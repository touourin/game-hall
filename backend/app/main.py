from __future__ import annotations

import asyncio
import logging
import secrets
import time
from contextlib import suppress
from contextlib import asynccontextmanager
from pathlib import Path

import socketio
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from .access import access_signing_secret, access_token, verify_access_token
from .accounts import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    AccountError,
    account_store,
)
from .avatars import (
    MAX_AVATAR_UPLOAD_BYTES,
    AvatarValidationError,
    process_avatar_upload,
)
from .games.registry import GAME_CATALOG
from .games.builtin import builtin_game_definition
from .games.definition import GameRecordQueryError, GameRecords
from .guests import GuestSessionError, guest_for_token, issue_guest_session
from .infrastructure import redis_status
from .logging_config import (
    bind_request_context,
    configure_logging,
    reset_request_context,
)
from .realtime import (
    close_game_engines,
    close_room_state_store,
    maintain_game_rooms,
    persist_room_state,
    replace_account_session_connections,
    resume_bot_turns,
    restore_room_state,
    sio,
    warm_game_engines,
)


logger = logging.getLogger(__name__)
GAME_NAMES = {item["key"]: item["name"] for item in GAME_CATALOG}
DEFAULT_GAME_RECORDS = GameRecords()


def validate_record_query(
    game: str | None,
    mode: str | None,
    variant: str | None,
) -> None:
    definition = builtin_game_definition(game) if game is not None else None
    records = definition.records if definition else DEFAULT_GAME_RECORDS
    try:
        records.validate_query(mode, variant)
    except GameRecordQueryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@asynccontextmanager
async def lifespan(_: FastAPI):
    log_dir = configure_logging()
    cleanup_task: asyncio.Task[None] | None = None
    warmup_task: asyncio.Task[None] | None = None
    try:
        logger.info(
            "Game hall is starting",
            extra={
                "event": "application.starting",
                "log_dir": str(log_dir),
            },
        )
        access_signing_secret()
        account_store().initialize()
        await restore_room_state()
        warmup_task = asyncio.create_task(
            warm_game_engines(),
            name="game-engine-warmup",
        )
        await resume_bot_turns()
        cleanup_task = asyncio.create_task(maintain_game_rooms())
        logger.info(
            "Game hall is ready",
            extra={"event": "application.ready"},
        )
        yield
    except Exception:
        logger.exception(
            "Application lifecycle failed",
            extra={"event": "application.failed"},
        )
        raise
    finally:
        if warmup_task is not None:
            warmup_task.cancel()
            with suppress(asyncio.CancelledError):
                await warmup_task
        if cleanup_task is not None:
            cleanup_task.cancel()
            with suppress(asyncio.CancelledError):
                await cleanup_task
        await close_game_engines()
        await persist_room_state()
        await close_room_state_store()
        logger.info(
            "Game hall stopped",
            extra={"event": "application.stopped"},
        )


api = FastAPI(title="Game Hall", version="0.2.0", lifespan=lifespan)


@api.middleware("http")
async def log_http_request(request: Request, call_next):
    request_id = secrets.token_hex(8)
    raw_path = request.url.path
    path = (
        "/api/avatars/:token"
        if raw_path.startswith("/api/avatars/")
        else raw_path
    )
    tokens = bind_request_context(request_id, request.method, path)
    started_at = time.perf_counter()
    client_ip = request.client.host if request.client else None
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.exception(
            "Unhandled HTTP request failure",
            extra={
                "client_ip": client_ip,
                "duration_ms": duration_ms,
                "event": "http.failed",
                "method": request.method,
                "path": path,
                "status_code": 500,
            },
        )
        raise
    else:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        log_level = (
            logging.ERROR
            if response.status_code >= 500
            else logging.WARNING
            if response.status_code >= 400
            else logging.DEBUG
            if path == "/api/health"
            else logging.INFO
        )
        logger.log(
            log_level,
            "HTTP request completed",
            extra={
                "client_ip": client_ip,
                "duration_ms": duration_ms,
                "event": "http.completed",
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
            },
        )
        return response
    finally:
        reset_request_context(tokens)


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
    )
    player_name: str = Field(min_length=1, max_length=12)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
    )
    password: str = Field(min_length=6, max_length=128)


class GuestRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=12)


class RenamePlayerRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=12)


class AvatarPresetRequest(BaseModel):
    preset: str = Field(min_length=2, max_length=32)


def bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def require_front_door(access_header: str | None) -> None:
    if not verify_access_token(access_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="访问凭证无效",
        )


def game_hall_access_header(
    x_game_hall_access: str | None = Header(
        default=None, alias="X-Game-Hall-Access"
    ),
    x_avalon_access: str | None = Header(
        default=None, alias="X-Avalon-Access"
    ),
) -> str | None:
    """Prefer the game-hall header while accepting old deployed clients."""
    return x_game_hall_access or x_avalon_access


def require_account_session(
    authorization: str | None, access_header: str | None
):
    require_front_door(access_header)
    account = account_store().account_for_token(bearer_token(authorization))
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效",
        )
    return account


def require_identity_session(
    authorization: str | None, access_header: str | None
):
    require_front_door(access_header)
    token = bearer_token(authorization)
    identity = account_store().account_for_token(token) or guest_for_token(token)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效",
        )
    return identity


@api.get("/api/health")
def health() -> dict[str, str]:
    try:
        account_store().ping()
        cache_status = redis_status()
    except Exception as error:
        logger.exception(
            "Infrastructure health check failed",
            extra={"event": "health.failed"},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="基础服务暂不可用",
        ) from error
    return {
        "status": "ok",
        "database": "ok",
        "redis": cache_status,
    }


@api.post("/api/access/session")
async def create_access_session() -> dict[str, str | bool]:
    """Issue the internal transport token without a user-facing password gate."""
    return {"ok": True, "token": access_token()}


@api.get("/api/access/status")
async def access_status(
    authorization: str | None = Header(default=None),
) -> dict[str, bool]:
    if not verify_access_token(bearer_token(authorization)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="访问凭证无效",
        )
    return {"ok": True}


@api.post("/api/auth/register")
def register_account(
    payload: RegisterRequest,
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    require_front_door(game_hall_access)
    try:
        account, token = account_store().register(
            payload.username, payload.password, payload.player_name
        )
    except AccountError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    return {"ok": True, "token": token, "account": account.as_dict()}


@api.post("/api/auth/login")
async def login_account(
    payload: LoginRequest,
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    require_front_door(game_hall_access)
    try:
        account, token = await run_in_threadpool(
            account_store().login,
            payload.username,
            payload.password,
        )
    except AccountError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error
    try:
        await replace_account_session_connections(account.id)
    except Exception:
        # The database token has already been replaced, so stale sockets will
        # still be rejected by per-event validation. A transient notification
        # failure must not hide the new valid token from the player.
        logger.exception(
            "Failed to notify previous account login connections",
            extra={
                "account_id": account.id,
                "event": "account.session_notification_failed",
            },
        )
    return {"ok": True, "token": token, "account": account.as_dict()}


@api.post("/api/auth/guest")
def create_guest_session(
    payload: GuestRequest,
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    require_front_door(game_hall_access)
    try:
        guest, token = issue_guest_session(payload.player_name)
    except GuestSessionError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    logger.info(
        "Guest session created",
        extra={"account_id": guest.id, "event": "guest.created"},
    )
    return {"ok": True, "token": token, "account": guest.as_dict()}


@api.get("/api/auth/me")
def current_account(
    authorization: str | None = Header(default=None),
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    identity = require_identity_session(authorization, game_hall_access)
    return {"ok": True, "account": identity.as_dict()}


@api.patch("/api/auth/me")
def rename_current_account(
    payload: RenamePlayerRequest,
    authorization: str | None = Header(default=None),
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    account = require_account_session(authorization, game_hall_access)
    try:
        renamed = account_store().rename_player(
            account.id, payload.player_name
        )
    except AccountError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    return {"ok": True, "account": renamed.as_dict()}


@api.patch("/api/auth/me/avatar")
def select_current_avatar_preset(
    payload: AvatarPresetRequest,
    authorization: str | None = Header(default=None),
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    account = require_account_session(authorization, game_hall_access)
    try:
        updated = account_store().set_avatar_preset(
            account.id,
            payload.preset,
        )
    except AccountError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    logger.info(
        "Account avatar preset changed",
        extra={
            "account_id": account.id,
            "avatar_preset": payload.preset,
            "event": "account.avatar.preset_changed",
        },
    )
    return {"ok": True, "account": updated.as_dict()}


@api.put("/api/auth/me/avatar")
async def upload_current_avatar(
    request: Request,
    authorization: str | None = Header(default=None),
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    account = require_account_session(authorization, game_hall_access)
    declared_length = request.headers.get("content-length")
    if declared_length is not None:
        try:
            if int(declared_length) > MAX_AVATAR_UPLOAD_BYTES:
                raise AvatarValidationError(
                    "头像图片不能超过 8 MB",
                    reason="too_large",
                )
        except AvatarValidationError as error:
            logger.warning(
                "Account avatar upload rejected",
                extra={
                    "account_id": account.id,
                    "event": "account.avatar.upload_rejected",
                    "reason": error.reason,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=str(error),
            ) from error
        except ValueError:
            pass

    payload = await request.body()
    try:
        avatar_data, mime_type = process_avatar_upload(payload)
    except AvatarValidationError as error:
        logger.warning(
            "Account avatar upload rejected",
            extra={
                "account_id": account.id,
                "event": "account.avatar.upload_rejected",
                "reason": error.reason,
                "upload_bytes": len(payload),
            },
        )
        raise HTTPException(
            status_code=(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                if error.reason == "too_large"
                else status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error

    try:
        updated = account_store().set_custom_avatar(
            account.id,
            avatar_data,
            mime_type,
        )
    except AccountError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    logger.info(
        "Account avatar uploaded",
        extra={
            "account_id": account.id,
            "event": "account.avatar.uploaded",
            "mime_type": mime_type,
            "stored_bytes": len(avatar_data),
            "upload_bytes": len(payload),
        },
    )
    return {"ok": True, "account": updated.as_dict()}


@api.get("/api/avatars/{avatar_token}")
def custom_avatar(avatar_token: str) -> Response:
    avatar = account_store().custom_avatar(avatar_token)
    if avatar is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="头像不存在",
        )
    data, mime_type = avatar
    return Response(
        content=data,
        media_type=mime_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
        },
    )


@api.post("/api/auth/logout")
def logout_account(
    authorization: str | None = Header(default=None),
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict[str, bool]:
    require_front_door(game_hall_access)
    account_store().logout(bearer_token(authorization))
    return {"ok": True}


@api.get("/api/stats/me")
def personal_stats(
    game: str | None = None,
    mode: str | None = None,
    variant: str | None = None,
    authorization: str | None = Header(default=None),
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    account = require_account_session(authorization, game_hall_access)
    if game is not None and game not in GAME_NAMES:
        raise HTTPException(status_code=404, detail="没有找到这个游戏")
    validate_record_query(game, mode, variant)
    return {
        "ok": True,
        "summary": account_store().summary_for_account(
            account.id,
            game_key=game,
            game_mode=mode,
            game_variant=variant,
        ),
        "history": account_store().history_for_account(
            account.id,
            game_key=game,
            game_mode=mode,
            game_variant=variant,
        ),
    }


@api.get("/api/games/avalon/role-skins/me")
def avalon_role_skin_progress(
    authorization: str | None = Header(default=None),
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    account = require_account_session(authorization, game_hall_access)
    return {
        "ok": True,
        "progress": account_store().avalon_role_skin_progress(account.id),
    }


@api.get("/api/leaderboard")
def leaderboard(
    game: str,
    mode: str | None = None,
    variant: str | None = None,
    authorization: str | None = Header(default=None),
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    require_identity_session(authorization, game_hall_access)
    if game not in GAME_NAMES:
        raise HTTPException(status_code=404, detail="没有找到这个游戏")
    validate_record_query(game, mode, variant)
    return {
        "ok": True,
        "players": account_store().leaderboard(
            game_key=game,
            game_mode=mode,
            game_variant=variant,
        ),
    }


@api.get("/api/games")
def game_catalog(
    authorization: str | None = Header(default=None),
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    require_identity_session(authorization, game_hall_access)
    return {"ok": True, "games": GAME_CATALOG}


@api.get("/api/matches/{match_id}")
def match_detail(
    match_id: str,
    authorization: str | None = Header(default=None),
    game_hall_access: str | None = Depends(game_hall_access_header),
) -> dict:
    account = require_account_session(authorization, game_hall_access)
    match = account_store().match_for_account(match_id, account.id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到这场战绩",
        )
    return {"ok": True, "match": match}


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
assets_dir = frontend_dist / "assets"

if assets_dir.exists():
    api.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@api.get("/{path:path}", include_in_schema=False)
async def serve_spa(path: str):
    requested_file = frontend_dist / path
    if path and requested_file.is_file():
        return FileResponse(requested_file)
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "前端尚未构建，请在开发模式打开 Vite 地址，或先执行前端构建。"
    }


app = socketio.ASGIApp(sio, other_asgi_app=api)
