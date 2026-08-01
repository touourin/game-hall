from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from functools import wraps
from typing import Any, Literal

import socketio
from pydantic import BaseModel, Field, ValidationError

from backend.app.accounts import account_store
from backend.app.games.registry import build_engine_registry
from backend.app.logging_config import bind_game_context, reset_game_context

from .models import ArcadeRoom
from .rooms import ACTION_ERRORS, ArcadeRoomError, ArcadeRoomManager
from .views import build_lobby_view, build_room_view


logger = logging.getLogger(__name__)
INFO_SOCKET_EVENTS = {
    "arcade:cleanup",
    "arcade:create",
    "arcade:dissolve",
    "arcade:join",
    "arcade:kick",
    "arcade:leave",
    "arcade:restart",
    "arcade:resume",
    "arcade:rules:update",
    "arcade:start",
}


class CreatePayload(BaseModel):
    game_key: str = Field(min_length=1, max_length=32)
    options: dict[str, Any] = Field(default_factory=dict)


class JoinPayload(CreatePayload):
    room_code: str = Field(min_length=4, max_length=8)


class ResumePayload(BaseModel):
    room_code: str = Field(min_length=4, max_length=8)
    token: str = Field(min_length=16, max_length=128)


class RoomCodePayload(BaseModel):
    room_code: str = Field(min_length=4, max_length=8)


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
    return {"ok": False, "error": str(error)}


class ArcadeRealtime:
    def __init__(self) -> None:
        self.engines = build_engine_registry()
        self.rooms = ArcadeRoomManager(self.engines)
        self.active_sids: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.sio: socketio.AsyncServer | None = None
        self.logger = logger

    def bind(self, sio: socketio.AsyncServer) -> None:
        self.sio = sio
        self._bind_event(sio, "arcade:create", self.create_room)
        self._bind_event(sio, "arcade:join", self.join_room)
        self._bind_event(sio, "arcade:resume", self.resume_room)
        self._bind_event(sio, "arcade:leave", self.leave_room)
        self._bind_event(sio, "arcade:start", self.start_game)
        self._bind_event(sio, "arcade:action", self.game_action)
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
            player_id = session.get("arcade_player_id")
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
        except (ValidationError, *ACTION_ERRORS) as error:
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
            room = self.rooms.get_room(payload.room_code)
            async with room.lock:
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

    async def cleanup_room(
        self, sid: str, raw_data: Any = None
    ) -> dict[str, Any]:
        try:
            payload = RoomCodePayload.model_validate(raw_data or {})
            await self._account_id(sid)
            room = self.rooms.get_room(payload.room_code)
            async with room.lock:
                self.rooms.cleanup_room(room.code)
            await self.broadcast_lobby()
            return {"ok": True}
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

    async def maintain(self) -> None:
        changed_rooms = self.rooms.maintain()
        if changed_rooms:
            for room in changed_rooms:
                if room.phase == "finished":
                    self._record_room(room)
                await self.broadcast_room(room)
            await self.broadcast_lobby()

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
        self.rooms.update_presence(room)

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
