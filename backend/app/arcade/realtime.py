from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from typing import Any, Literal

import socketio
from pydantic import BaseModel, Field, ValidationError

from backend.app.accounts import account_store
from backend.app.games.registry import build_engine_registry

from .models import ArcadeRoom
from .rooms import ACTION_ERRORS, ArcadeRoomError, ArcadeRoomManager
from .views import build_lobby_view, build_room_view


class CreatePayload(BaseModel):
    game_key: str = Field(min_length=1, max_length=32)
    options: dict[str, Any] = Field(default_factory=dict)


class JoinPayload(CreatePayload):
    room_code: str = Field(min_length=4, max_length=8)


class ResumePayload(BaseModel):
    room_code: str = Field(min_length=4, max_length=8)
    token: str = Field(min_length=16, max_length=128)


class ActionPayload(BaseModel):
    action: str = Field(min_length=1, max_length=32)
    payload: dict[str, Any] = Field(default_factory=dict)


class TargetPayload(BaseModel):
    target_id: str = Field(min_length=1, max_length=64)


class ChatPayload(BaseModel):
    content: str = Field(min_length=1, max_length=300)


class GameRequestPayload(BaseModel):
    kind: Literal["undo", "draw"]


class ResolveRequestPayload(BaseModel):
    accept: bool


class RulesPayload(BaseModel):
    options: dict[str, Any] = Field(default_factory=dict)


def error_response(error: Exception) -> dict[str, Any]:
    if isinstance(error, ValidationError):
        return {"ok": False, "error": "提交的数据格式不正确"}
    return {"ok": False, "error": str(error)}


class ArcadeRealtime:
    def __init__(self) -> None:
        self.engines = build_engine_registry()
        self.rooms = ArcadeRoomManager(self.engines)
        self.active_sids: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.sio: socketio.AsyncServer | None = None
        self.logger = logging.getLogger(__name__)

    def bind(self, sio: socketio.AsyncServer) -> None:
        self.sio = sio
        sio.on("arcade:create")(self.create_room)
        sio.on("arcade:join")(self.join_room)
        sio.on("arcade:resume")(self.resume_room)
        sio.on("arcade:leave")(self.leave_room)
        sio.on("arcade:start")(self.start_game)
        sio.on("arcade:action")(self.game_action)
        sio.on("arcade:restart")(self.restart_game)
        sio.on("arcade:kick")(self.kick_player)
        sio.on("arcade:dissolve")(self.dissolve_room)
        sio.on("arcade:chat")(self.send_chat)
        sio.on("arcade:request")(self.request_game_action)
        sio.on("arcade:request:resolve")(self.resolve_game_request)
        sio.on("arcade:rules:update")(self.update_rules)
        sio.on("arcade:list")(self.list_rooms)

    async def on_connect(self, sid: str) -> None:
        await self._server.emit("arcade:lobby", self.lobby_view(), to=sid)

    async def on_disconnect(self, sid: str) -> None:
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

    async def create_room(self, sid: str, raw_data: Any) -> dict[str, Any]:
        try:
            payload = CreatePayload.model_validate(raw_data or {})
            account_id = await self._account_id(sid)
            account = account_store().account_for_id(account_id)
            if account is None:
                raise ArcadeRoomError("登录状态无效，请重新登录")
            room, player, token = self.rooms.create_room(
                payload.game_key,
                account.player_name,
                account_id,
                payload.options,
            )
            await self._bind_session(sid, room, player.id)
            await self.broadcast_room(room)
            await self.broadcast_lobby()
            return self._join_response(room.code, player.id, token)
        except (ValidationError, ArcadeRoomError, KeyError) as error:
            return error_response(error)

    async def join_room(self, sid: str, raw_data: Any) -> dict[str, Any]:
        try:
            payload = JoinPayload.model_validate(raw_data or {})
            account_id = await self._account_id(sid)
            account = account_store().account_for_id(account_id)
            if account is None:
                raise ArcadeRoomError("登录状态无效，请重新登录")
            room, player, token = self.rooms.join_room(
                payload.room_code,
                payload.game_key,
                account.player_name,
                account_id,
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
            account_id = await self._account_id(sid)
            room, player = self.rooms.resume(
                payload.room_code, payload.token, account_id
            )
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

    async def leave_room(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        try:
            room, player = await self._context(sid)
            async with room.lock:
                seat_preserved = self.rooms.leave(room, player.id)
            await self._server.leave_room(sid, self._channel(room.code, player.id))
            key = (room.code, player.id)
            self.active_sids[key].discard(sid)
            if not self.active_sids[key]:
                self.active_sids.pop(key, None)
            await self._clear_room_session(sid)
            if room.code in self.rooms.rooms:
                await self.broadcast_room(room)
            await self.broadcast_lobby()
            return {"ok": True, "seatPreserved": seat_preserved}
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
            return {"ok": True}
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
            player_ids = [member.id for member in room.players]
            async with room.lock:
                self.rooms.dissolve(room, player.id)
            for player_id in player_ids:
                await self._eject_player(
                    room.code,
                    player_id,
                    event="arcade:closed",
                    message="房主已解散房间",
                    silent=player_id == player.id,
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
                self.rooms.request_game_action(room, player.id, payload.kind)
            await self.broadcast_room(room)
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
                self.rooms.resolve_game_request(
                    room,
                    player.id,
                    payload.accept,
                )
                if room.phase == "finished":
                    self._record_room(room)
            await self.broadcast_room(room)
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

    async def cleanup(self) -> None:
        if self.rooms.cleanup_abandoned():
            await self.broadcast_lobby()

    async def tick(self) -> None:
        for room in list(self.rooms.rooms.values()):
            if room.phase != "playing":
                continue
            try:
                expire_timeout = getattr(
                    self.engines[room.game_key],
                    "expire_timeout",
                    None,
                )
                if expire_timeout is None:
                    continue
                async with room.lock:
                    expired = expire_timeout(room)
                    if expired:
                        self._record_room(room)
                if expired:
                    await self.broadcast_room(room)
            except Exception:
                # A broken room must not stop clock handling for every other
                # active game or terminate the shared maintenance task.
                self.logger.exception(
                    "Failed to process clock tick for room %s",
                    room.code,
                )

    def lobby_view(self) -> list[dict[str, Any]]:
        return build_lobby_view(list(self.rooms.rooms.values()), self.engines)

    async def broadcast_lobby(self) -> None:
        await self._server.emit("arcade:lobby", self.lobby_view())

    async def broadcast_room(self, room: ArcadeRoom) -> None:
        engine = self.engines[room.game_key]
        for player in room.players:
            await self._server.emit(
                "arcade:snapshot",
                build_room_view(room, player, engine),
                room=self._channel(room.code, player.id),
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
            }
        )
        await self._server.save_session(sid, session)
        await self._server.enter_room(sid, self._channel(room.code, player_id))
        self.active_sids[(room.code, player_id)].add(sid)
        room.player(player_id).connected = True
        room.all_humans_offline_since = None

    async def _clear_room_session(self, sid: str) -> None:
        try:
            session = await self._server.get_session(sid)
        except KeyError:
            return
        session.pop("arcade_room_code", None)
        session.pop("arcade_player_id", None)
        await self._server.save_session(sid, session)

    async def _eject_player(
        self,
        room_code: str,
        player_id: str,
        *,
        event: str,
        message: str,
        silent: bool = False,
    ) -> None:
        key = (room_code, player_id)
        target_sids = list(self.active_sids.pop(key, set()))
        for target_sid in target_sids:
            await self._server.emit(
                event,
                {"message": message, "silent": silent},
                to=target_sid,
            )
            await self._server.leave_room(
                target_sid,
                self._channel(room_code, player_id),
            )
            await self._clear_room_session(target_sid)

    async def _context(self, sid: str):
        try:
            session = await self._server.get_session(sid)
            room = self.rooms.get_room(session["arcade_room_code"])
            player = room.player(session["arcade_player_id"])
            return room, player
        except (KeyError, TypeError) as exc:
            raise ArcadeRoomError("连接还没有加入这个游戏房间") from exc

    async def _account_id(self, sid: str) -> str:
        try:
            session = await self._server.get_session(sid)
            return session["account_id"]
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
        engine = self.engines[room.game_key]
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
                    "scoreMs": (
                        score_reader(room, player)
                        if score_reader is not None
                        else None
                    ),
                }
            )
        state = asdict(room.state) if is_dataclass(room.state) else room.state
        try:
            stored = account_store().record_game_match(
                game_key=room.game_key,
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
                        }
                        for index, player in enumerate(room.players)
                    ],
                    "state": state,
                },
                players=players,
            )
            room.recorded = stored
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
