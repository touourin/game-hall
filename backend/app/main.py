from __future__ import annotations

import asyncio
from contextlib import suppress
from contextlib import asynccontextmanager
from pathlib import Path

import socketio
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .access import access_password, access_token, verify_access_token, verify_password
from .accounts import AccountError, GAME_NAMES, account_store
from .games.registry import GAME_CATALOG
from .infrastructure import redis_status
from .realtime import cleanup_abandoned_rooms, sio


@asynccontextmanager
async def lifespan(_: FastAPI):
    access_password()
    account_store().initialize()
    cleanup_task = asyncio.create_task(cleanup_abandoned_rooms())
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


api = FastAPI(title="Private Game Hall", version="0.2.0", lifespan=lifespan)


class AccessRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=20)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=12)


class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=20)
    password: str = Field(min_length=6, max_length=128)


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


@api.get("/api/health")
def health() -> dict[str, str]:
    try:
        account_store().ping()
        cache_status = redis_status()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="基础服务暂不可用",
        ) from error
    return {
        "status": "ok",
        "database": "ok",
        "redis": cache_status,
    }


@api.post("/api/access/unlock")
async def unlock_access(payload: AccessRequest) -> dict[str, str | bool]:
    if not verify_password(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="访问密码错误",
        )
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
    x_avalon_access: str | None = Header(default=None),
) -> dict:
    require_front_door(x_avalon_access)
    try:
        account, token = account_store().register(
            payload.username, payload.password, payload.display_name
        )
    except AccountError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    return {"ok": True, "token": token, "account": account.as_dict()}


@api.post("/api/auth/login")
def login_account(
    payload: LoginRequest,
    x_avalon_access: str | None = Header(default=None),
) -> dict:
    require_front_door(x_avalon_access)
    try:
        account, token = account_store().login(payload.username, payload.password)
    except AccountError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error
    return {"ok": True, "token": token, "account": account.as_dict()}


@api.get("/api/auth/me")
def current_account(
    authorization: str | None = Header(default=None),
    x_avalon_access: str | None = Header(default=None),
) -> dict:
    account = require_account_session(authorization, x_avalon_access)
    return {"ok": True, "account": account.as_dict()}


@api.post("/api/auth/logout")
def logout_account(
    authorization: str | None = Header(default=None),
    x_avalon_access: str | None = Header(default=None),
) -> dict[str, bool]:
    require_front_door(x_avalon_access)
    account_store().logout(bearer_token(authorization))
    return {"ok": True}


@api.get("/api/stats/me")
def personal_stats(
    game: str | None = None,
    authorization: str | None = Header(default=None),
    x_avalon_access: str | None = Header(default=None),
) -> dict:
    account = require_account_session(authorization, x_avalon_access)
    if game is not None and game not in GAME_NAMES:
        raise HTTPException(status_code=404, detail="没有找到这个游戏")
    return {
        "ok": True,
        "summary": account_store().summary_for_account(
            account.id, game_key=game
        ),
        "history": account_store().history_for_account(
            account.id, game_key=game
        ),
    }


@api.get("/api/leaderboard")
def leaderboard(
    game: str,
    authorization: str | None = Header(default=None),
    x_avalon_access: str | None = Header(default=None),
) -> dict:
    require_account_session(authorization, x_avalon_access)
    if game not in GAME_NAMES:
        raise HTTPException(status_code=404, detail="没有找到这个游戏")
    return {
        "ok": True,
        "players": account_store().leaderboard(game_key=game),
    }


@api.get("/api/games")
def game_catalog(
    authorization: str | None = Header(default=None),
    x_avalon_access: str | None = Header(default=None),
) -> dict:
    require_account_session(authorization, x_avalon_access)
    return {"ok": True, "games": GAME_CATALOG}


@api.get("/api/matches/{match_id}")
def match_detail(
    match_id: str,
    authorization: str | None = Header(default=None),
    x_avalon_access: str | None = Header(default=None),
) -> dict:
    account = require_account_session(authorization, x_avalon_access)
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
