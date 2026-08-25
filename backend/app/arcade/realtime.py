from __future__ import annotations

import asyncio
import copy
import inspect
import json
import logging
import secrets
from collections import defaultdict, deque
from dataclasses import asdict, is_dataclass
from functools import wraps
from typing import Any

import socketio
from pydantic import BaseModel, Field, ValidationError

from backend.app.accounts import account_store
from backend.app.games.registry import build_engine_registry, game_registration
from backend.app.logging_config import bind_game_context, reset_game_context

from .models import ArcadeGameRequestKind, ArcadeRoom, ArcadeSpectator
from .rooms import (
    ACTION_ERRORS,
    ActiveRoomError,
    ArcadeRoomError,
    ArcadeRoomManager,
)
from .views import (
    build_lobby_room_view,
    build_lobby_view,
    build_room_view,
    build_spectator_room_view,
)


logger = logging.getLogger(__name__)
INFO_SOCKET_EVENTS = {
    "arcade:abandon",
    "arcade:active",
    "arcade:cleanup",
    "arcade:create",
    "arcade:detach",
    "arcade:dissolve",
    "arcade:join",
    "arcade:kick",
    "arcade:leave",
    "arcade:restart",
    "arcade:resume",
    "arcade:rules:update",
    "arcade:start",
    "arcade:unwatch",
    "arcade:watch",
}
MAX_SPECTATOR_FRAME_BYTES = 64 * 1024
MAX_SPECTATOR_FRAMES_PER_SECOND = 20


class CreatePayload(BaseModel):
    game_key: str = Field(min_length=1, max_length=32)
    room_name: str | None = Field(default=None, max_length=64)
    options: dict[str, Any] = Field(default_factory=dict)


class JoinPayload(CreatePayload):
    room_code: str = Field(min_length=4, max_length=8)


class ResumePayload(BaseModel):
    room_code: str = Field(min_length=4, max_length=8)
    token: str = Field(min_length=16, max_length=128)


class RoomCodePayload(BaseModel):
    room_code: str = Field(min_length=4, max_length=8)


class WatchInspectPayload(RoomCodePayload):
    game_key: str = Field(min_length=1, max_length=32)


class WatchPayload(WatchInspectPayload):
    target_id: str = Field(min_length=1, max_length=64)


class ActionPayload(BaseModel):
    # Keep enough room for legacy game actions that shipped before individual
    # games standardized on shorter wire names. Existing browser tabs may keep
    # sending those names during a rolling deployment.
    action: str = Field(min_length=1, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class RealtimeInputPayload(BaseModel):
    sequence: int = Field(ge=0, le=2_147_483_647)
    input_mask: int = Field(ge=0, le=2_147_483_647)


class SpectatorFramePayload(BaseModel):
    sequence: int = Field(ge=0, le=2_147_483_647)
    state: dict[str, Any] = Field(default_factory=dict)


class TargetPayload(BaseModel):
    target_id: str = Field(min_length=1, max_length=64)


class ChatPayload(BaseModel):
    content: str = Field(min_length=1, max_length=300)


class GameRequestPayload(BaseModel):
    kind: ArcadeGameRequestKind


class ResolveRequestPayload(BaseModel):
    accept: bool


class RulesPayload(BaseModel):
    options: dict[str, Any] = Field(default_factory=dict)


def error_response(error: Exception) -> dict[str, Any]:
    detail = (
        "validation error"
        if isinstance(error, ValidationError)
        else str(error)
    )
    logger.warning(
        "Arcade realtime request rejected: %s",
        detail,
        extra={
            "error_type": type(error).__name__,
            "event": "socket.rejected",
        },
    )
    if isinstance(error, ValidationError):
        return {"ok": False, "error": "提交的数据格式不正确"}
    if isinstance(error, ActiveRoomError):
        return {
            "ok": False,
            "error": str(error),
            "roomCode": error.room_code,
            "gameKey": error.game_key,
            "activeRoom": True,
        }
    return {"ok": False, "error": str(error)}


class ArcadeRealtime:
    def __init__(self) -> None:
        self.engines = build_engine_registry()
        self.rooms = ArcadeRoomManager(self.engines)
        self.active_sids: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.spectator_sids: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.spectators: dict[tuple[str, str], ArcadeSpectator] = {}
        self.watch_target_locks: dict[tuple[str, int, str], str] = {}
        self.account_sids: dict[str, set[str]] = defaultdict(set)
        self.sid_accounts: dict[str, str] = {}
        self.sio: socketio.AsyncServer | None = None
        self.logger = logger
        self.bot_tasks: dict[str, asyncio.Task[None]] = {}
        self.bot_rerun_requested: set[str] = set()
        self.realtime_tasks: dict[str, asyncio.Task[None]] = {}
        self.realtime_input_times: dict[
            tuple[str, str], deque[float]
        ] = defaultdict(deque)
        self.spectator_frame_times: dict[
            tuple[str, str], deque[float]
        ] = defaultdict(deque)
        self.closing = False

    def bind(self, sio: socketio.AsyncServer) -> None:
        self.sio = sio
        self._bind_event(sio, "arcade:create", self.create_room)
        self._bind_event(sio, "arcade:join", self.join_room)
        self._bind_event(sio, "arcade:active", self.active_room)
        self._bind_event(sio, "arcade:resume", self.resume_room)
        self._bind_event(sio, "arcade:watch:inspect", self.inspect_watch_room)
        self._bind_event(sio, "arcade:watch", self.watch_room)
        self._bind_event(sio, "arcade:unwatch", self.unwatch_room)
        self._bind_event(sio, "arcade:detach", self.detach_room)
        self._bind_event(sio, "arcade:leave", self.leave_room)
        self._bind_event(sio, "arcade:abandon", self.abandon_room)
        self._bind_event(sio, "arcade:start", self.start_game)
        self._bind_event(sio, "arcade:action", self.game_action)
        self._bind_event(sio, "arcade:input", self.realtime_input)
        self._bind_event(
            sio, "arcade:spectator:frame", self.spectator_frame
        )
        self._bind_event(sio, "arcade:restart", self.restart_game)
        self._bind_event(sio, "arcade:kick", self.kick_player)
        self._bind_event(sio, "arcade:dissolve", self.dissolve_room)
        self._bind_event(sio, "arcade:cleanup", self.cleanup_room)
        self._bind_event(sio, "arcade:chat", self.send_chat)
        self._bind_event(
            sio, "arcade:request", self.request_game_action
        )
        self._bind_event(
            sio, "arcade:request:resolve", self.resolve_game_request
        )
        self._bind_event(
            sio, "arcade:rules:update", self.update_rules
        )
        self._bind_event(sio, "arcade:list", self.list_rooms)

    def _bind_event(self, sio, event_name: str, handler) -> None:
        @wraps(handler)
        async def logged_handler(sid: str, *args):
            raw_data = args[0] if args else None
            context = await self._event_log_context(sid, raw_data)
            tokens = bind_game_context(
                game_key=context["game_key"],
                room_code=context["room_code"],
                socket_event=event_name,
                player_id=context["player_id"],
                account_id=context["account_id"],
                action=context["action"],
            )
            try:
                if not await self._session_is_current(sid):
                    return await self._reject_stale_session(sid)
                response = await handler(sid, *args)
                if isinstance(response, dict) and response.get("ok"):
                    room_code = response.get("roomCode") or context[
                        "room_code"
                    ]
                    self.logger.log(
                        logging.INFO
                        if event_name in INFO_SOCKET_EVENTS
                        else logging.DEBUG,
                        "Arcade socket event completed",
                        extra={
                            "event": "socket.completed",
                            "game_key": context["game_key"],
                            "player_id": response.get("playerId")
                            or context["player_id"],
                            "room_code": room_code,
                            "socket_event": event_name,
                        },
                    )
                return response
            except Exception:
                self.logger.exception(
                    "Unhandled arcade socket event",
                    extra={"event": "socket.unhandled"},
                )
                raise
            finally:
                reset_game_context(tokens)

        sio.on(event_name)(logged_handler)

    async def _event_log_context(
        self, sid: str, raw_data: Any
    ) -> dict[str, str | None]:
        data = raw_data if isinstance(raw_data, dict) else {}
        game_key = data.get("game_key")
        room_code = data.get("room_code")
        action = data.get("action")
        player_id = None
        account_id = None
        try:
            session = await self._server.get_session(sid)
            room_code = session.get("arcade_room_code") or room_code
            player_id = session.get("arcade_player_id") or session.get(
                "arcade_spectator_id"
            )
            account_id = session.get("account_id")
        except (KeyError, TypeError):
            pass
        normalized_code = (
            str(room_code).strip().upper() if room_code else None
        )
        room = self.rooms.rooms.get(normalized_code or "")
        if room is not None:
            game_key = room.game_key
            normalized_code = room.code
        return {
            "game_key": str(game_key) if game_key else None,
            "room_code": normalized_code,
            "player_id": str(player_id) if player_id else None,
            "account_id": str(account_id) if account_id else None,
            "action": str(action) if action else None,
        }

    async def on_connect(self, sid: str, account_id: str) -> None:
        self.account_sids[account_id].add(sid)
        self.sid_accounts[sid] = account_id
        await self._server.emit("arcade:lobby", self.lobby_view(), to=sid)

    async def replace_account_session(self, account_id: str) -> int:
        """Invalidate every socket from the account's previous login."""
        target_sids = list(self.account_sids.get(account_id, set()))
        if not target_sids:
            return 0
        payload = {
            "message": "账号已在其他设备登录，请重新登录",
        }
        for target_sid in target_sids:
            await self._server.emit(
                "account:replaced",
                payload,
                to=target_sid,
            )
        for target_sid in target_sids:
            await self._server.disconnect(target_sid)
        self.logger.info(
            "Previous account socket session disconnected",
            extra={
                "account_id": account_id,
                "connection_count": len(target_sids),
                "event": "account.session_connections_revoked",
            },
        )
        return len(target_sids)

    async def on_disconnect(self, sid: str) -> None:
        account_id = self.sid_accounts.pop(sid, None)
        if account_id is not None:
            self.account_sids[account_id].discard(sid)
            if not self.account_sids[account_id]:
                self.account_sids.pop(account_id, None)
        try:
            session = await self._server.get_session(sid)
        except KeyError:
            return
        if session.get("arcade_role") == "spectator":
            await self._disconnect_spectator(sid, session)
            return
        try:
            room, player = await self._context(sid)
        except (ArcadeRoomError, KeyError, TypeError):
            return
        key = (room.code, player.id)
        self.active_sids[key].discard(sid)
        if not self.active_sids[key]:
            self.active_sids.pop(key, None)
            player.connected = False
            room.revision += 1
            self.rooms.update_presence(room)
            await self.broadcast_room(room)

    async def active_room(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        try:
            identity = await self._identity(sid)
            active = self.rooms.active_room_for_account(identity["id"])
            if active is None:
                return {"ok": True, "activeRoom": False}
            room, player = active
            async with room.lock:
                player.name = identity["player_name"]
                player.avatar_url = identity["avatar_url"]
                player.is_guest = identity["is_guest"]
                player.connected = True
                await self._bind_session(sid, room, player.id)
            await self.broadcast_room(room)
            return {
                "ok": True,
                "activeRoom": True,
                "roomCode": room.code,
                "gameKey": room.game_key,
                "playerId": player.id,
            }
        except ACTION_ERRORS as error:
            return error_response(error)

    async def create_room(self, sid: str, raw_data: Any) -> dict[str, Any]:
        try:
            payload = CreatePayload.model_validate(raw_data or {})
            identity = await self._identity(sid)
            self._ensure_not_spectating(identity["id"])
            room, player, token = self.rooms.create_room(
                payload.game_key,
                identity["player_name"],
                identity["id"],
                payload.options,
                identity["avatar_url"],
                is_guest=identity["is_guest"],
                room_name=payload.room_name,
            )
            await self._bind_session(sid, room, player.id)
            await self.broadcast_room(room)
            await self.broadcast_lobby()
            return self._join_response(room.code, player.id, token)
        except (ValidationError, *ACTION_ERRORS) as error:
            return error_response(error)

    async def join_room(self, sid: str, raw_data: Any) -> dict[str, Any]:
        try:
            payload = JoinPayload.model_validate(raw_data or {})
            identity = await self._identity(sid)
            self._ensure_not_spectating(identity["id"])
            room, player, token = self.rooms.join_room(
                payload.room_code,
                payload.game_key,
                identity["player_name"],
                identity["id"],
                identity["avatar_url"],
                is_guest=identity["is_guest"],
            )
            await self._bind_session(sid, room, player.id)
            await self.broadcast_room(room)
            await self.broadcast_lobby()
            return self._join_response(room.code, player.id, token)
        except (ValidationError, ArcadeRoomError, KeyError) as error:
            return error_response(error)

    async def resume_room(self, sid: str, raw_data: Any) -> dict[str, Any]:
        try:
            payload = ResumePayload.model_validate(raw_data or {})
            identity = await self._identity(sid)
            self._ensure_not_spectating(identity["id"])
            room = self.rooms.get_room(payload.room_code)
            async with room.lock:
                room, player = self.rooms.resume(
                    payload.room_code, payload.token, identity["id"]
                )
                player.name = identity["player_name"]
                player.avatar_url = identity["avatar_url"]
                player.is_guest = identity["is_guest"]
            await self._bind_session(sid, room, player.id)
            await self.broadcast_room(room)
            return {
                "ok": True,
                "roomCode": room.code,
                "gameKey": room.game_key,
                "playerId": player.id,
            }
        except (ValidationError, ArcadeRoomError, KeyError) as error:
            return error_response(error)

    async def inspect_watch_room(
        self, sid: str, raw_data: Any
    ) -> dict[str, Any]:
        try:
            payload = WatchInspectPayload.model_validate(raw_data or {})
            identity = await self._identity(sid)
            room = self._watchable_room(payload, identity)
            return {
                "ok": True,
                "room": build_lobby_room_view(
                    room,
                    self.engines[room.game_key],
                    spectator_count=len(self._room_spectators(room.code)),
                ),
            }
        except (ValidationError, *ACTION_ERRORS) as error:
            return error_response(error)

    async def watch_room(
        self, sid: str, raw_data: Any
    ) -> dict[str, Any]:
        try:
            payload = WatchPayload.model_validate(raw_data or {})
            identity = await self._identity(sid)
            room = self._watchable_room(payload, identity)
            target = room.player(payload.target_id)
            if target.left_room:
                raise ArcadeRoomError("这名玩家已经离开对局")
            lock_key = (room.code, room.round_number, identity["id"])
            locked_target_id = self.watch_target_locks.get(lock_key)
            if locked_target_id is not None and locked_target_id != target.id:
                locked_target = room.player(locked_target_id)
                raise ArcadeRoomError(
                    f"本局已固定观看{locked_target.name}，不能切换视角"
                )
            existing = self.spectators.get((room.code, identity["id"]))
            if existing is not None and existing.target_player_id != target.id:
                raise ArcadeRoomError("请先退出当前观战")
            is_new = existing is None
            spectator = existing or ArcadeSpectator(
                id=secrets.token_urlsafe(10),
                account_id=identity["id"],
                name=identity["player_name"],
                avatar_url=identity["avatar_url"],
                is_guest=identity["is_guest"],
                target_player_id=target.id,
            )
            self.watch_target_locks[lock_key] = target.id
            self.spectators[(room.code, spectator.account_id)] = spectator
            await self._bind_watch_session(sid, room, spectator)
            if is_new:
                room.revision += 1
            await self.broadcast_room(room)
            await self.broadcast_lobby()
            return {
                "ok": True,
                "roomCode": room.code,
                "gameKey": room.game_key,
                "spectatorId": spectator.id,
                "targetPlayerId": target.id,
            }
        except (ValidationError, *ACTION_ERRORS) as error:
            return error_response(error)

    async def unwatch_room(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        try:
            room, spectator = await self._watch_context(sid)
        except (ArcadeRoomError, KeyError, TypeError):
            await self._clear_room_session(sid)
            return {"ok": True}
        await self._server.leave_room(
            sid, self._spectator_channel(room.code, spectator.account_id)
        )
        key = (room.code, spectator.account_id)
        self.spectator_sids[key].discard(sid)
        removed = False
        if not self.spectator_sids[key]:
            self.spectator_sids.pop(key, None)
            self.spectators.pop(key, None)
            removed = True
        await self._clear_room_session(sid)
        if removed and room.code in self.rooms.rooms:
            room.revision += 1
            await self.broadcast_room(room)
            await self.broadcast_lobby()
        return {"ok": True}

    async def cleanup_room(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        try:
            payload = RoomCodePayload.model_validate(raw_data or {})
            await self._identity(sid)
            room = self.rooms.get_room(payload.room_code)
            async with room.lock:
                self.rooms.cleanup_room(room.code)
            await self._eject_room_spectators(
                room.code, "房间已被清理，观战已经结束"
            )
            await self.broadcast_lobby()
            return {"ok": True}
        except (ValidationError, ArcadeRoomError, KeyError) as error:
            return error_response(error)

    async def detach_room(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        if await self._is_spectator_session(sid):
            return await self.unwatch_room(sid)
        try:
            room, player = await self._context(sid)
        except (ArcadeRoomError, KeyError, TypeError):
            await self._clear_room_session(sid)
            return {"ok": True, "seatPreserved": True}
        key = (room.code, player.id)
        await self._server.leave_room(sid, self._channel(room.code, player.id))
        self.active_sids[key].discard(sid)
        if not self.active_sids[key]:
            self.active_sids.pop(key, None)
        async with room.lock:
            player.connected = bool(self.active_sids.get(key))
            room.revision += 1
            self.rooms.update_presence(room)
        await self._clear_room_session(sid)
        await self.broadcast_room(room)
        await self.broadcast_lobby()
        return {"ok": True, "seatPreserved": True}

    async def leave_room(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        if await self._is_spectator_session(sid):
            return await self.unwatch_room(sid)
        try:
            room, player = await self._context(sid)
        except (ArcadeRoomError, KeyError, TypeError):
            await self._clear_room_session(sid)
            return {"ok": True, "seatPreserved": False}
        try:
            async with room.lock:
                self.rooms.leave(room, player.id)
            await self._eject_player(
                room.code,
                player.id,
                account_id=player.account_id,
                event="arcade:left",
                message="你已退出房间",
                silent=True,
            )
            if room.code in self.rooms.rooms:
                await self.broadcast_room(room)
            else:
                await self._eject_room_spectators(
                    room.code, "房间已经关闭，观战已经结束"
                )
            await self.broadcast_lobby()
            return {"ok": True, "seatPreserved": False}
        except ACTION_ERRORS as error:
            return error_response(error)

    async def abandon_room(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        if await self._is_spectator_session(sid):
            return await self.unwatch_room(sid)
        try:
            room, player = await self._context(sid)
        except (ArcadeRoomError, KeyError, TypeError):
            await self._clear_room_session(sid)
            return {"ok": True, "seatPreserved": False}
        try:
            async with room.lock:
                self.rooms.abandon(room, player.id)
                if room.phase == "finished":
                    self._record_room(room)
            await self._eject_player(
                room.code,
                player.id,
                account_id=player.account_id,
                event="arcade:left",
                message="你已退出房间",
                silent=True,
            )
            if room.code in self.rooms.rooms:
                await self.broadcast_room(room)
            else:
                await self._eject_room_spectators(
                    room.code, "房间已经关闭，观战已经结束"
                )
            await self.broadcast_lobby()
            return {"ok": True, "seatPreserved": False}
        except ACTION_ERRORS as error:
            return error_response(error)

    async def start_game(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        try:
            room, player = await self._context(sid)
            async with room.lock:
                self.rooms.start(room, player.id)
            await self.broadcast_room(room)
            await self.broadcast_lobby()
            self.schedule_bot_turns(room)
            self.schedule_realtime_game(room)
            return {"ok": True}
        except ACTION_ERRORS as error:
            return error_response(error)

    async def game_action(self, sid: str, raw_data: Any) -> dict[str, Any]:
        try:
            payload = ActionPayload.model_validate(raw_data or {})
            room, player = await self._context(sid)
            async with room.lock:
                self.rooms.act(room, player.id, payload.action, payload.payload)
                if room.phase == "finished":
                    self._record_room(room)
            await self.broadcast_room(room)
            self.schedule_bot_turns(room)
            return {"ok": True}
        except (ValidationError, *ACTION_ERRORS) as error:
            return error_response(error)

    async def realtime_input(
        self, sid: str, raw_data: Any
    ) -> dict[str, Any]:
        try:
            payload = RealtimeInputPayload.model_validate(raw_data or {})
            room, player = await self._context(sid)
            engine = self.engines[room.game_key]
            input_handler = getattr(engine, "apply_input", None)
            if not callable(input_handler):
                raise ArcadeRoomError("这个游戏不接收实时移动输入")
            self._check_realtime_input_rate(room.code, player.id)
            async with room.lock:
                accepted = bool(
                    input_handler(
                        room,
                        player,
                        payload.sequence,
                        payload.input_mask,
                    )
                )
            return {
                "ok": True,
                "accepted": accepted,
                "sequence": payload.sequence,
            }
        except (ValidationError, *ACTION_ERRORS) as error:
            return error_response(error)

    async def spectator_frame(
        self, sid: str, raw_data: Any
    ) -> dict[str, Any]:
        try:
            payload = SpectatorFramePayload.model_validate(raw_data or {})
            room, player = await self._context(sid)
            registration = game_registration(room.game_key)
            if not (
                registration
                and registration.capabilities.spectator_frames
            ):
                raise ArcadeRoomError("这个游戏不接收观战画面同步")
            if room.phase != "playing":
                raise ArcadeRoomError("当前对局不接收观战画面同步")
            if len(
                json.dumps(
                    payload.state,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            ) > MAX_SPECTATOR_FRAME_BYTES:
                raise ArcadeRoomError("观战画面数据过大")
            self._check_spectator_frame_rate(room.code, player.id)
            frame = {
                "roomCode": room.code,
                "gameKey": room.game_key,
                "roundNumber": room.round_number,
                "targetPlayerId": player.id,
                "sequence": payload.sequence,
                "state": payload.state,
            }
            for spectator in self._room_spectators(room.code):
                if spectator.target_player_id != player.id:
                    continue
                await self._server.emit(
                    "arcade:spectator:frame",
                    frame,
                    room=self._spectator_channel(
                        room.code, spectator.account_id
                    ),
                )
            return {"ok": True, "sequence": payload.sequence}
        except (ValidationError, *ACTION_ERRORS) as error:
            return error_response(error)

    async def restart_game(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        try:
            room, player = await self._context(sid)
            async with room.lock:
                self.rooms.restart(room, player.id)
            await self.broadcast_room(room)
            await self.broadcast_lobby()
            self.schedule_bot_turns(room)
            self.schedule_realtime_game(room)
            return {"ok": True}
        except ACTION_ERRORS as error:
            return error_response(error)

    async def kick_player(self, sid: str, raw_data: Any) -> dict[str, Any]:
        try:
            payload = TargetPayload.model_validate(raw_data or {})
            room, player = await self._context(sid)
            target = room.player(payload.target_id)
            async with room.lock:
                self.rooms.kick(room, player.id, target.id)
            await self._eject_player(
                room.code,
                target.id,
                account_id=target.account_id,
                event="arcade:kicked",
                message="你已被房主移出房间",
            )
            await self.broadcast_room(room)
            await self.broadcast_lobby()
            return {"ok": True}
        except (ValidationError, *ACTION_ERRORS) as error:
            return error_response(error)

    async def dissolve_room(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        try:
            room, player = await self._context(sid)
            players = [
                (member.id, member.account_id) for member in room.players
            ]
            async with room.lock:
                self.rooms.dissolve(room, player.id)
            for player_id, account_id in players:
                await self._eject_player(
                    room.code,
                    player_id,
                    account_id=account_id,
                    event="arcade:closed",
                    message="房主已解散房间",
                    silent=player_id == player.id,
                )
            await self._eject_room_spectators(
                room.code, "房主已解散房间，观战已经结束"
            )
            await self.broadcast_lobby()
            return {"ok": True}
        except ACTION_ERRORS as error:
            return error_response(error)

    async def send_chat(self, sid: str, raw_data: Any) -> dict[str, Any]:
        try:
            payload = ChatPayload.model_validate(raw_data or {})
            room, player = await self._context(sid)
            async with room.lock:
                self.rooms.send_chat(room, player.id, payload.content)
            await self.broadcast_room(room)
            return {"ok": True}
        except (ValidationError, *ACTION_ERRORS) as error:
            return error_response(error)

    async def request_game_action(
        self, sid: str, raw_data: Any
    ) -> dict[str, Any]:
        try:
            payload = GameRequestPayload.model_validate(raw_data or {})
            room, player = await self._context(sid)
            async with room.lock:
                returned_to_lobby = self.rooms.request_game_action(
                    room, player.id, payload.kind
                )
            await self.broadcast_room(room)
            if room.phase == "scoring":
                self.schedule_bot_turns(room)
            if returned_to_lobby:
                await self.broadcast_lobby()
            return {"ok": True}
        except (ValidationError, *ACTION_ERRORS) as error:
            return error_response(error)

    async def resolve_game_request(
        self, sid: str, raw_data: Any
    ) -> dict[str, Any]:
        try:
            payload = ResolveRequestPayload.model_validate(raw_data or {})
            room, player = await self._context(sid)
            async with room.lock:
                returned_to_lobby = self.rooms.resolve_game_request(
                    room,
                    player.id,
                    payload.accept,
                )
                if room.phase == "finished":
                    self._record_room(room)
            await self.broadcast_room(room)
            if room.phase == "scoring":
                self.schedule_bot_turns(room)
            if returned_to_lobby:
                await self.broadcast_lobby()
            return {"ok": True}
        except (ValidationError, *ACTION_ERRORS) as error:
            return error_response(error)

    async def update_rules(self, sid: str, raw_data: Any) -> dict[str, Any]:
        try:
            payload = RulesPayload.model_validate(raw_data or {})
            room, player = await self._context(sid)
            async with room.lock:
                self.rooms.update_options(room, player.id, payload.options)
            await self.broadcast_room(room)
            await self.broadcast_lobby()
            return {"ok": True}
        except (ValidationError, *ACTION_ERRORS) as error:
            return error_response(error)

    async def list_rooms(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        return {"ok": True, "rooms": self.lobby_view()}

    async def maintain(self) -> None:
        changed_rooms = self.rooms.maintain()
        if changed_rooms:
            for room in changed_rooms:
                if room.phase == "finished":
                    self._record_room(room)
                await self.broadcast_room(room)
            await self.broadcast_lobby()

    def schedule_bot_turns(self, room: ArcadeRoom) -> None:
        """Ensure at most one background AI driver is active per room."""
        if self.closing:
            return
        current = self.bot_tasks.get(room.code)
        if current is not None and not current.done():
            self.bot_rerun_requested.add(room.code)
            return
        task = asyncio.create_task(
            self._run_bot_turns(room),
            name=f"arcade-bot-{room.code}",
        )
        self.bot_tasks[room.code] = task
        task.add_done_callback(
            lambda completed, room_code=room.code: self._bot_task_done(
                room_code, completed
            )
        )

    async def resume_bot_turns(self) -> None:
        for room in self.rooms.rooms.values():
            self.schedule_bot_turns(room)

    async def resume_realtime_games(self) -> None:
        for room in self.rooms.rooms.values():
            self.schedule_realtime_game(room)

    async def warm_up(self) -> None:
        """Warm optional external engines without blocking application startup."""
        for game_key, engine in self.engines.items():
            warmer = getattr(engine, "warm_up", None)
            if not callable(warmer):
                continue
            try:
                result = warmer()
                if inspect.isawaitable(result):
                    await result
            except Exception:
                self.logger.warning(
                    "Game engine warm-up failed; lazy startup remains available",
                    exc_info=True,
                    extra={
                        "event": "engine.warmup_failed",
                        "game_key": game_key,
                    },
                )

    async def close(self) -> None:
        self.closing = True
        self.bot_rerun_requested.clear()
        tasks = [*self.bot_tasks.values(), *self.realtime_tasks.values()]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self.bot_tasks.clear()
        self.realtime_tasks.clear()
        self.realtime_input_times.clear()
        for engine in self.engines.values():
            closer = getattr(engine, "close", None)
            if callable(closer):
                result = closer()
                if inspect.isawaitable(result):
                    await result

    async def _run_bot_turns(self, room: ArcadeRoom) -> None:
        engine = self.engines[room.game_key]
        loop = asyncio.get_running_loop()
        action_interval = self.rooms.bots.action_interval_seconds(engine)
        next_action_at = loop.time() + action_interval
        for _ in range(self.rooms.bots.max_automatic_actions):
            async with room.lock:
                if self.rooms.rooms.get(room.code) is not room:
                    return
                revision = room.revision
                snapshot = copy.deepcopy(room)

            selected = await self.rooms.bots.select_action(snapshot, engine)
            if selected is None:
                return

            delay = next_action_at - loop.time()
            if delay > 0:
                await asyncio.sleep(delay)

            async with room.lock:
                if self.rooms.rooms.get(room.code) is not room:
                    return
                if room.revision != revision:
                    next_action_at = loop.time() + action_interval
                    continue
                self.rooms.apply_bot_action(room, selected)
                if room.phase == "finished":
                    self._record_room(room)
                next_action_at = loop.time() + action_interval
            await self.broadcast_room(room)
            if room.phase == "finished":
                await self.broadcast_lobby()
        raise RuntimeError("AI 自动行动超过安全上限")

    def _bot_task_done(
        self,
        room_code: str,
        task: asyncio.Task[None],
    ) -> None:
        if self.bot_tasks.get(room_code) is task:
            self.bot_tasks.pop(room_code, None)
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            self.logger.error(
                "AI room driver failed",
                exc_info=(type(error), error, error.__traceback__),
                extra={"event": "bot.driver_failed", "room_code": room_code},
            )
        if (
            not self.closing
            and room_code in self.bot_rerun_requested
            and (room := self.rooms.rooms.get(room_code)) is not None
        ):
            self.bot_rerun_requested.discard(room_code)
            self.schedule_bot_turns(room)

    def schedule_realtime_game(self, room: ArcadeRoom) -> None:
        if self.closing or room.phase != "playing":
            return
        engine = self.engines[room.game_key]
        if not callable(getattr(engine, "tick", None)):
            return
        current = self.realtime_tasks.get(room.code)
        if current is not None and not current.done():
            return
        task = asyncio.create_task(
            self._run_realtime_game(room),
            name=f"arcade-realtime-{room.code}",
        )
        self.realtime_tasks[room.code] = task
        task.add_done_callback(
            lambda completed, room_code=room.code: self._realtime_task_done(
                room_code,
                completed,
            )
        )

    async def _run_realtime_game(self, room: ArcadeRoom) -> None:
        engine = self.engines[room.game_key]
        tick_handler = getattr(engine, "tick")
        tick_rate = int(getattr(engine, "realtime_tick_rate", 30))
        snapshot_rate = int(getattr(engine, "realtime_snapshot_rate", 15))
        if not 1 <= tick_rate <= 60 or not 1 <= snapshot_rate <= tick_rate:
            raise RuntimeError("实时游戏 tick 或快照频率不正确")
        frame_interval = max(1, round(tick_rate / snapshot_rate))
        tick_interval = 1 / tick_rate
        loop = asyncio.get_running_loop()
        deadline = loop.time()
        ticks_since_frame = 0

        while not self.closing:
            deadline += tick_interval
            await asyncio.sleep(max(0, deadline - loop.time()))
            if loop.time() - deadline > tick_interval * 4:
                deadline = loop.time()

            should_send_frame = False
            should_send_snapshot = False
            finished = False
            changed = False
            async with room.lock:
                if self.rooms.rooms.get(room.code) is not room:
                    return
                if room.phase != "playing":
                    return
                state = room.state
                previous_boundary = (
                    getattr(state, "stage", None),
                    getattr(state, "round_number", None),
                )
                changed = bool(tick_handler(room))
                current_boundary = (
                    getattr(room.state, "stage", None),
                    getattr(room.state, "round_number", None),
                )
                if changed:
                    room.revision += 1
                    ticks_since_frame += 1
                    should_send_frame = ticks_since_frame >= frame_interval
                    if should_send_frame:
                        ticks_since_frame = 0
                should_send_snapshot = previous_boundary != current_boundary
                finished = room.phase == "finished"
                if finished:
                    self._record_room(room)

            if should_send_frame or finished:
                await self.broadcast_realtime_frame(room)
            if should_send_snapshot or finished:
                await self.broadcast_room(room)
            if finished:
                await self.broadcast_lobby()
                return

    def _realtime_task_done(
        self,
        room_code: str,
        task: asyncio.Task[None],
    ) -> None:
        owned_task = self.realtime_tasks.get(room_code) is task
        if owned_task:
            self.realtime_tasks.pop(room_code, None)
        for key in tuple(self.realtime_input_times):
            if key[0] == room_code:
                self.realtime_input_times.pop(key, None)
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            self.logger.error(
                "Realtime room driver failed",
                exc_info=(type(error), error, error.__traceback__),
                extra={
                    "event": "realtime.driver_failed",
                    "room_code": room_code,
                },
            )
            return
        # A rematch can enter ``playing`` while the previous room driver is
        # returning but before its done callback runs. Start the replacement
        # here so an immediate restart never loses the simulation clock.
        room = self.rooms.rooms.get(room_code)
        if owned_task and not self.closing and room is not None:
            self.schedule_realtime_game(room)

    def _check_realtime_input_rate(
        self,
        room_code: str,
        player_id: str,
    ) -> None:
        now = asyncio.get_running_loop().time()
        timestamps = self.realtime_input_times[(room_code, player_id)]
        while timestamps and now - timestamps[0] >= 1:
            timestamps.popleft()
        if len(timestamps) >= 90:
            raise ArcadeRoomError("操作过于频繁，请稍后再试")
        timestamps.append(now)

    def _check_spectator_frame_rate(
        self,
        room_code: str,
        player_id: str,
    ) -> None:
        now = asyncio.get_running_loop().time()
        timestamps = self.spectator_frame_times[(room_code, player_id)]
        while timestamps and now - timestamps[0] >= 1:
            timestamps.popleft()
        if len(timestamps) >= MAX_SPECTATOR_FRAMES_PER_SECOND:
            raise ArcadeRoomError("观战画面同步过于频繁")
        timestamps.append(now)

    def lobby_view(self) -> list[dict[str, Any]]:
        spectator_counts = {
            room_code: len(self._room_spectators(room_code))
            for room_code in self.rooms.rooms
        }
        return build_lobby_view(
            list(self.rooms.rooms.values()),
            self.engines,
            spectator_counts,
        )

    async def broadcast_lobby(self) -> None:
        await self._server.emit("arcade:lobby", self.lobby_view())

    async def broadcast_room(self, room: ArcadeRoom) -> None:
        engine = self.engines[room.game_key]
        if (
            room.phase == "lobby"
            or not room.options.get("allowSpectators", True)
        ):
            await self._eject_room_spectators(
                room.code,
                "房间已回到等待阶段，观战已经结束",
            )
        else:
            active_player_ids = {
                player.id for player in room.players if not player.left_room
            }
            for spectator in list(self._room_spectators(room.code)):
                if spectator.target_player_id not in active_player_ids:
                    await self._eject_spectator(
                        room.code,
                        spectator.account_id,
                        "被观战玩家已经离开，对局观战结束",
                    )
        spectators = self._room_spectators(room.code)
        for player in room.players:
            await self._server.emit(
                "arcade:snapshot",
                build_room_view(room, player, engine, spectators),
                room=self._channel(room.code, player.id),
            )
        for spectator in spectators:
            target = room.player(spectator.target_player_id)
            await self._server.emit(
                "arcade:snapshot",
                build_spectator_room_view(
                    room,
                    target,
                    spectator,
                    engine,
                    spectators,
                ),
                room=self._spectator_channel(
                    room.code, spectator.account_id
                ),
            )

    async def broadcast_realtime_frame(self, room: ArcadeRoom) -> None:
        engine = self.engines[room.game_key]
        frame_builder = getattr(engine, "realtime_frame", None)
        if not callable(frame_builder):
            return
        spectators = self._room_spectators(room.code)
        for player in room.players:
            await self._server.emit(
                "arcade:frame",
                frame_builder(room, player),
                room=self._channel(room.code, player.id),
            )
        for spectator in spectators:
            target = room.player(spectator.target_player_id)
            await self._server.emit(
                "arcade:frame",
                frame_builder(room, target),
                room=self._spectator_channel(
                    room.code,
                    spectator.account_id,
                ),
            )

    async def _bind_session(
        self, sid: str, room: ArcadeRoom, player_id: str
    ) -> None:
        try:
            session = await self._server.get_session(sid)
        except KeyError:
            session = {}
        session.update(
            {
                "arcade_room_code": room.code,
                "arcade_player_id": player_id,
                "arcade_role": "player",
            }
        )
        session.pop("arcade_spectator_id", None)
        session.pop("arcade_watch_target_id", None)
        await self._server.save_session(sid, session)
        await self._server.enter_room(sid, self._channel(room.code, player_id))
        self.active_sids[(room.code, player_id)].add(sid)
        room.player(player_id).connected = True
        self.rooms.update_presence(room)

    async def _bind_watch_session(
        self,
        sid: str,
        room: ArcadeRoom,
        spectator: ArcadeSpectator,
    ) -> None:
        try:
            session = await self._server.get_session(sid)
        except KeyError:
            session = {}
        session.update(
            {
                "arcade_room_code": room.code,
                "arcade_role": "spectator",
                "arcade_spectator_id": spectator.id,
                "arcade_watch_target_id": spectator.target_player_id,
            }
        )
        session.pop("arcade_player_id", None)
        await self._server.save_session(sid, session)
        await self._server.enter_room(
            sid,
            self._spectator_channel(room.code, spectator.account_id),
        )
        self.spectator_sids[(room.code, spectator.account_id)].add(sid)

    async def _clear_room_session(self, sid: str) -> None:
        try:
            session = await self._server.get_session(sid)
        except KeyError:
            return
        session.pop("arcade_room_code", None)
        session.pop("arcade_player_id", None)
        session.pop("arcade_role", None)
        session.pop("arcade_spectator_id", None)
        session.pop("arcade_watch_target_id", None)
        await self._server.save_session(sid, session)

    async def _eject_player(
        self,
        room_code: str,
        player_id: str,
        *,
        account_id: str,
        event: str,
        message: str,
        silent: bool = False,
    ) -> None:
        key = (room_code, player_id)
        target_sids = list(self.active_sids.pop(key, set()))
        notification_sids = list(
            self.account_sids.get(account_id) or set(target_sids)
        )
        payload = {
            "roomCode": room_code,
            "message": message,
            "silent": silent,
        }
        for target_sid in notification_sids:
            await self._server.emit(
                event,
                payload,
                to=target_sid,
            )
        for target_sid in target_sids:
            await self._server.leave_room(
                target_sid,
                self._channel(room_code, player_id),
            )
            await self._clear_room_session(target_sid)

    async def _disconnect_spectator(
        self, sid: str, session: dict[str, Any]
    ) -> None:
        room_code = session.get("arcade_room_code")
        account_id = session.get("account_id")
        if not isinstance(room_code, str) or not isinstance(account_id, str):
            return
        key = (room_code, account_id)
        self.spectator_sids[key].discard(sid)
        if self.spectator_sids[key]:
            return
        self.spectator_sids.pop(key, None)
        removed = self.spectators.pop(key, None)
        room = self.rooms.rooms.get(room_code)
        if removed is not None and room is not None:
            room.revision += 1
            await self.broadcast_room(room)
            await self.broadcast_lobby()

    async def _eject_room_spectators(
        self, room_code: str, message: str
    ) -> None:
        for spectator in list(self._room_spectators(room_code)):
            await self._eject_spectator(
                room_code, spectator.account_id, message
            )
        self._clear_watch_target_locks(room_code)

    async def _eject_spectator(
        self,
        room_code: str,
        account_id: str,
        message: str,
    ) -> None:
        key = (room_code, account_id)
        spectator = self.spectators.pop(key, None)
        target_sids = list(self.spectator_sids.pop(key, set()))
        if spectator is None and not target_sids:
            return
        payload = {"roomCode": room_code, "message": message}
        for target_sid in target_sids:
            await self._server.emit(
                "arcade:watch:ended", payload, to=target_sid
            )
            await self._server.leave_room(
                target_sid,
                self._spectator_channel(room_code, account_id),
            )
            await self._clear_room_session(target_sid)

    def _watchable_room(
        self,
        payload: WatchInspectPayload,
        identity: dict[str, Any],
    ) -> ArcadeRoom:
        room = self.rooms.get_room(payload.room_code)
        if room.game_key != payload.game_key:
            raise ArcadeRoomError("房间所属游戏不正确")
        if room.phase == "lobby":
            raise ArcadeRoomError("游戏尚未开始，请直接加入房间")
        if room.phase == "finished":
            raise ArcadeRoomError("本局已经结束，暂时不能加入观战")
        if not room.options.get("allowSpectators", True):
            raise ArcadeRoomError("房主没有开启观战")
        if identity["is_guest"] and not room.options.get(
            "allowGuests", True
        ):
            raise ArcadeRoomError("这个房间不允许游客观战")
        if any(
            not player.is_bot and player.account_id == identity["id"]
            for player in room.players
        ):
            raise ArcadeRoomError("你已经是这局游戏的玩家")
        active = self.rooms.active_room_for_account(identity["id"])
        if active is not None:
            raise ActiveRoomError(active[0])
        current_watch = self._spectator_for_account(identity["id"])
        if current_watch is not None and current_watch[0] != room.code:
            raise ArcadeRoomError("请先退出当前观战")
        return room

    def _ensure_not_spectating(self, account_id: str) -> None:
        if self._spectator_for_account(account_id) is not None:
            raise ArcadeRoomError("请先退出当前观战")

    def _spectator_for_account(
        self, account_id: str
    ) -> tuple[str, ArcadeSpectator] | None:
        return next(
            (
                (room_code, spectator)
                for (room_code, spectator_account_id), spectator
                in self.spectators.items()
                if spectator_account_id == account_id
            ),
            None,
        )

    def _room_spectators(self, room_code: str) -> list[ArcadeSpectator]:
        return [
            spectator
            for (spectator_room_code, _), spectator
            in self.spectators.items()
            if spectator_room_code == room_code
        ]

    def _clear_watch_target_locks(self, room_code: str) -> None:
        for key in tuple(self.watch_target_locks):
            if key[0] == room_code:
                self.watch_target_locks.pop(key, None)

    async def _is_spectator_session(self, sid: str) -> bool:
        try:
            session = await self._server.get_session(sid)
        except KeyError:
            return False
        return session.get("arcade_role") == "spectator"

    async def _session_is_current(self, sid: str) -> bool:
        try:
            session = await self._server.get_session(sid)
        except KeyError:
            return False
        if bool(session.get("is_guest", False)):
            return True
        account_id = session.get("account_id")
        token_hash = session.get("account_session_hash")
        if not isinstance(account_id, str) or not isinstance(token_hash, str):
            return False
        return account_store().session_is_active(account_id, token_hash)

    async def _reject_stale_session(self, sid: str) -> dict[str, Any]:
        account_id = self.sid_accounts.get(sid)
        self.logger.warning(
            "Stale account socket session rejected",
            extra={
                "account_id": account_id,
                "event": "account.stale_session_rejected",
            },
        )
        await self._server.emit(
            "account:replaced",
            {"message": "账号登录状态已失效，请重新登录"},
            to=sid,
        )
        await self._server.disconnect(sid)
        return {
            "ok": False,
            "error": "账号登录状态已失效，请重新登录",
            "sessionReplaced": True,
        }

    async def _context(self, sid: str):
        try:
            session = await self._server.get_session(sid)
            if session.get("arcade_role") == "spectator":
                raise KeyError("spectator")
            room = self.rooms.get_room(session["arcade_room_code"])
            player = room.player(session["arcade_player_id"])
            return room, player
        except (KeyError, TypeError) as exc:
            raise ArcadeRoomError("连接还没有加入这个游戏房间") from exc

    async def _watch_context(
        self, sid: str
    ) -> tuple[ArcadeRoom, ArcadeSpectator]:
        try:
            session = await self._server.get_session(sid)
            if session.get("arcade_role") != "spectator":
                raise KeyError("player")
            room = self.rooms.get_room(session["arcade_room_code"])
            account_id = str(session["account_id"])
            spectator = self.spectators[(room.code, account_id)]
            return room, spectator
        except (KeyError, TypeError) as exc:
            raise ArcadeRoomError("连接当前没有在观战") from exc

    async def _identity(self, sid: str) -> dict[str, Any]:
        try:
            session = await self._server.get_session(sid)
            identity_id = str(session["account_id"])
            player_name = session.get("player_name")
            avatar_url = session.get("avatar_url")
            is_guest = bool(session.get("is_guest", False))
            if isinstance(player_name, str) and player_name:
                return {
                    "id": identity_id,
                    "player_name": player_name,
                    "avatar_url": (
                        str(avatar_url) if avatar_url is not None else None
                    ),
                    "is_guest": is_guest,
                }
            account = account_store().account_for_id(identity_id)
            if account is None:
                raise KeyError(identity_id)
            return {
                "id": account.id,
                "player_name": account.player_name,
                "avatar_url": account.avatar_url,
                "is_guest": False,
            }
        except (KeyError, TypeError) as exc:
            raise ArcadeRoomError("登录状态无效，请重新登录") from exc

    def _record_room(self, room: ArcadeRoom) -> None:
        if (
            room.recorded
            or room.game_id is None
            or room.started_at is None
            or room.ended_at is None
            or room.winner is None
            or room.win_reason is None
        ):
            return
        if not room.stats_eligible:
            room.recorded = True
            self.logger.info(
                "Arcade match skipped because the round included a guest",
                extra={
                    "event": "match.skipped_guest",
                    "game_id": room.game_id,
                    "game_key": room.game_key,
                    "room_code": room.code,
                },
            )
            return
        engine = self.engines[room.game_key]
        match_persister = getattr(engine, "persist_match", None)
        if match_persister is not None:
            try:
                room.recorded = bool(match_persister(room, account_store()))
                if room.recorded:
                    self.logger.info(
                        "Arcade match persisted",
                        extra={
                            "event": "match.persisted",
                            "game_id": room.game_id,
                            "game_key": room.game_key,
                            "room_code": room.code,
                        },
                    )
            except Exception:
                self.logger.exception(
                    "Failed to persist %s match", room.game_key
                )
            return
        players = []
        score_reader = getattr(engine, "player_score", None)
        for player in room.players:
            role, alignment, won = engine.player_result(room, player)
            players.append(
                {
                    "accountId": player.account_id,
                    "playerName": player.name,
                    "seat": player.seat,
                    "role": role,
                    "alignment": alignment,
                    "won": won,
                    "isHost": player.id == room.host_id,
                    "isBot": player.is_bot,
                    "scoreValue": (
                        score_reader(room, player)
                        if score_reader is not None
                        else None
                    ),
                }
            )
        record_state = getattr(engine, "record_state", None)
        state = (
            record_state(room)
            if record_state is not None
            else asdict(room.state)
            if is_dataclass(room.state)
            else room.state
        )
        try:
            stored = account_store().record_game_match(
                game_key=room.game_key,
                game_name=engine.name,
                match_id=room.game_id,
                room_code=room.code,
                winner=room.winner,
                reason=room.win_reason,
                started_at=room.started_at,
                ended_at=room.ended_at,
                details={
                    "options": room.options,
                    "players": [
                        {
                            "id": player.id,
                            "name": player.name,
                            "seat": player.seat,
                            "role": players[index]["role"],
                            "alignment": players[index]["alignment"],
                            "isBot": player.is_bot,
                        }
                        for index, player in enumerate(room.players)
                    ],
                    "state": state,
                },
                players=[
                    result for result in players if not result["isBot"]
                ],
                participant_count=len(room.players),
                ranked=not any(player.is_bot for player in room.players),
            )
            room.recorded = stored
            if stored:
                self.logger.info(
                    "Arcade match persisted",
                    extra={
                        "event": "match.persisted",
                        "game_id": room.game_id,
                        "game_key": room.game_key,
                        "room_code": room.code,
                    },
                )
        except Exception:
            self.logger.exception("Failed to persist %s match", room.game_key)

    @property
    def _server(self) -> socketio.AsyncServer:
        if self.sio is None:
            raise RuntimeError("ArcadeRealtime has not been bound")
        return self.sio

    @staticmethod
    def _channel(room_code: str, player_id: str) -> str:
        return f"arcade-player:{room_code}:{player_id}"

    @staticmethod
    def _spectator_channel(room_code: str, account_id: str) -> str:
        return f"arcade-spectator:{room_code}:{account_id}"

    @staticmethod
    def _join_response(
        room_code: str, player_id: str, token: str
    ) -> dict[str, Any]:
        return {
            "ok": True,
            "roomCode": room_code,
            "playerId": player_id,
            "resumeToken": token,
        }


arcade_realtime = ArcadeRealtime()
