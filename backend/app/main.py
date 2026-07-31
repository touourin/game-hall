from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import socketio
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .access import access_password, access_token, verify_access_token, verify_password
from .realtime import sio


@asynccontextmanager
async def lifespan(_: FastAPI):
    access_password()
    yield


api = FastAPI(title="Avalon LAN", version="0.1.0", lifespan=lifespan)


class AccessRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


def bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


@api.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


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
