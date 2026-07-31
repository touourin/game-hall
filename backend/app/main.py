from __future__ import annotations

from pathlib import Path

import socketio
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .realtime import sio


api = FastAPI(title="Avalon LAN", version="0.1.0")


@api.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


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

