from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
from functools import wraps
from typing import Any

import socketio
from pydantic import BaseModel, Field, ValidationError

from .access import verify_access_token
from .accounts import account_store
from .arcade.models import ArcadeRoom
from .arcade.realtime import arcade_realtime
from .games.avalon.bots import advance_ai_players
from .games.avalon.engine import GameEngine, GameRuleError
from .games.avalon.models import Phase, Room
from .games.avalon.rooms import RoomError, RoomManager
from .games.avalon.schemas import (
    ChatPayload,
    EarlyAssassinationSettingPayload,
    JoinPayload,
    LadySettingPayload,
    ListedSettingPayload,
    MissionVotePayload,
    ResumePayload,
    TargetPayload,
    TeamPayload,
    TeamVotePayload,
)
from .games.avalon.views import build_lobby_view, build_player_view
from .infrastructure import redis_url
from .logging_config import bind_game_context, reset_game_context
from .room_state import RedisRoomStateStore


redis_connection_url = redis_url()
logger = logging.getLogger(__name__)
socketio_logger = logging.getLogger("game_hall.socketio")
engineio_logger = logging.getLogger("game_hall.engineio")
socket_manager = (
    socketio.AsyncRedisManager(redis_connection_url, channel="game-hall")
    if redis_connection_url is not None
    else None
)
sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=socket_manager,
    logger=socketio_logger,
    engineio_logger=engineio_logger,
)
arcade_realtime.bind(sio)
rooms = RoomManager()
engine = GameEngine()
active_sids: dict[tuple[str, str], set[str]] = defaultdict(set)
room_state_store = RedisRoomStateStore(redis_connection_url)
INFO_SOCKET_EVENTS = {
    "game:restart",
    "game:start",
    "room:cleanup",
    "room:create",
    "room:join",
    "room:kick",
    "room:leave",
    "room:resume",
    "room:set-early-assassination",
    "room:set-lady",
    "room:set-listed",
}


class RoomCodePayload(BaseModel):
    room_code: str = Field(min_length=4, max_length=8)


async def restore_room_state() -> None:
    state = await room_state_store.load()
    if state is None:
        return
    avalon_rooms = state.get("avalon")
    arcade_rooms = state.get("arcade")
    if isinstance(avalon_rooms, dict):
        rooms.rooms = {
            code: room
            for code, room in avalon_rooms.items()
            if isinstance(code, str) and isinstance(room, Room)
        }
    if isinstance(arcade_rooms, dict):
        arcade_realtime.rooms.rooms = {
            code: room
            for code, room in arcade_rooms.items()
            if isinstance(code, str) and isinstance(room, ArcadeRoom)
        }

    restored_at = datetime.now(timezone.utc)
    for room in rooms.rooms.values():
        had_connected_human = any(
            not player.is_bot and player.connected for player in room.players
        )
        room.lock = asyncio.Lock()
        room.cleanup_ready = getattr(room, "cleanup_ready", False)
        room.host_offline_since = None
        for player in room.players:
            if not player.is_bot:
                player.connected = False
        if had_connected_human:
            room.all_humans_offline_since = restored_at
            room.cleanup_ready = False
        rooms.update_human_presence(room, now=restored_at)

    for room in arcade_realtime.rooms.rooms.values():
        had_connected_player = any(player.connected for player in room.players)
        room.lock = asyncio.Lock()
        room.cleanup_ready = getattr(room, "cleanup_ready", False)
        room.host_offline_since = None
        for player in room.players:
            player.connected = False
        if had_connected_player:
            room.all_humans_offline_since = restored_at
            room.cleanup_ready = False
        arcade_realtime.rooms.update_presence(room, now=restored_at)


async def persist_room_state() -> None:
    await room_state_store.save(
        {
            "avalon": rooms.rooms,
            "arcade": arcade_realtime.rooms.rooms,
        }
    )


async def close_room_state_store() -> None:
    await room_state_store.close()


def player_channel(room_code: str, player_id: str) -> str:
    return f"player:{room_code}:{player_id}"


async def broadcast_room(room: Room) -> None:
    for player in room.players:
        await sio.emit(
            "room:snapshot",
            build_player_view(room, player, engine),
            room=player_channel(room.code, player.id),
        )


async def broadcast_lobby() -> None:
    await sio.emit("lobby:rooms", build_lobby_view(rooms.rooms.values()))


async def cleanup_abandoned_rooms() -> None:
    while True:
        await asyncio.sleep(1)
        try:
            await arcade_realtime.tick()
            changed_rooms = rooms.maintain()
            if changed_rooms:
                for room in changed_rooms:
                    await broadcast_room(room)
                await broadcast_lobby()
            await arcade_realtime.maintain()
            await persist_room_state()
        except Exception:
            # Keep the shared maintenance task alive after a transient room,
            # Redis, or broadcast failure. The full traceback is persisted.
            logger.exception(
                "Room maintenance iteration failed",
                extra={"event": "maintenance.failed"},
            )


async def bind_session(
    sid: str, room: Room, player_id: str
) -> None:
    try:
        session = await sio.get_session(sid)
    except KeyError:
        session = {}
    session.update({"room_code": room.code, "player_id": player_id})
    await sio.save_session(sid, session)
    await sio.enter_room(sid, player_channel(room.code, player_id))
    active_sids[(room.code, player_id)].add(sid)
    room.player(player_id).connected = True
    rooms.update_human_presence(room)


async def clear_room_session(sid: str) -> None:
    try:
        session = await sio.get_session(sid)
    except KeyError:
        return
    session.pop("room_code", None)
    session.pop("player_id", None)
    await sio.save_session(sid, session)


async def context_for_sid(sid: str) -> tuple[Room, str]:
    try:
        session = await sio.get_session(sid)
        room = rooms.get_room(session["room_code"])
        player_id = session["player_id"]
        room.player(player_id)
    except (KeyError, TypeError) as exc:
        raise RoomError("连接还没有加入房间") from exc
    return room, player_id


async def account_id_for_sid(sid: str) -> str:
    try:
        session = await sio.get_session(sid)
        return session["account_id"]
    except (KeyError, TypeError) as exc:
        raise RoomError("登录状态无效，请重新登录") from exc


def error_response(error: Exception) -> dict[str, Any]:
    detail = (
        "validation error"
        if isinstance(error, ValidationError)
        else str(error)
    )
    logger.warning(
        "Realtime request rejected: %s",
        detail,
        extra={
            "error_type": type(error).__name__,
            "event": "socket.rejected",
        },
    )
    if isinstance(error, ValidationError):
        return {"ok": False, "error": "提交的数据格式不正确"}
    return {"ok": False, "error": str(error)}


async def avalon_event_log_context(
    sid: str, raw_data: Any
) -> dict[str, str | None]:
    data = raw_data if isinstance(raw_data, dict) else {}
    room_code = data.get("room_code")
    player_id = None
    account_id = None
    try:
        session = await sio.get_session(sid)
        room_code = session.get("room_code") or room_code
        player_id = session.get("player_id")
        account_id = session.get("account_id")
    except (KeyError, TypeError):
        pass
    normalized_code = (
        str(room_code).strip().upper() if room_code else None
    )
    room = rooms.rooms.get(normalized_code or "")
    if room is not None:
        normalized_code = room.code
    return {
        "room_code": normalized_code,
        "player_id": str(player_id) if player_id else None,
        "account_id": str(account_id) if account_id else None,
    }


def logged_socket_event(event_name: str):
    def register(handler):
        @wraps(handler)
        async def logged_handler(sid: str, *args):
            raw_data = args[0] if args else None
            context = await avalon_event_log_context(sid, raw_data)
            tokens = bind_game_context(
                game_key="avalon",
                room_code=context["room_code"],
                socket_event=event_name,
                player_id=context["player_id"],
                account_id=context["account_id"],
            )
            try:
                response = await handler(sid, *args)
                if isinstance(response, dict) and response.get("ok"):
                    logger.log(
                        logging.INFO
                        if event_name in INFO_SOCKET_EVENTS
                        else logging.DEBUG,
                        "Avalon socket event completed",
                        extra={
                            "event": "socket.completed",
                            "game_key": "avalon",
                            "player_id": response.get("playerId")
                            or context["player_id"],
                            "room_code": response.get("roomCode")
                            or context["room_code"],
                            "socket_event": event_name,
                        },
                    )
                return response
            except Exception:
                logger.exception(
                    "Unhandled Avalon socket event",
                    extra={"event": "socket.unhandled"},
                )
                raise
            finally:
                reset_game_context(tokens)

        sio.on(event_name)(logged_handler)
        return logged_handler

    return register


async def execute_action(
    sid: str,
    raw_data: Any,
    schema: type[BaseModel] | None,
    action: Callable[..., None],
) -> dict[str, Any]:
    try:
        payload = schema.model_validate(raw_data or {}) if schema else None
        room, player_id = await context_for_sid(sid)
        async with room.lock:
            if payload is None:
                action(room, player_id)
            else:
                action(room, player_id, payload)
            advance_ai_players(room, engine)
            if room.phase == Phase.GAME_OVER:
                try:
                    recorded = account_store().record_match(room)
                    if recorded:
                        logger.info(
                            "Avalon match persisted",
                            extra={
                                "event": "match.persisted",
                                "game_id": room.game_id,
                                "game_key": "avalon",
                                "room_code": room.code,
                            },
                        )
                except Exception:
                    # A storage failure must not prevent the completed game
                    # state from reaching connected players.
                    logger.exception(
                        "Failed to persist completed match %s", room.game_id
                    )
        await broadcast_room(room)
        return {"ok": True}
    except (ValidationError, RoomError, GameRuleError, KeyError) as error:
        return error_response(error)


async def execute_lobby_action(
    sid: str,
    raw_data: Any,
    schema: type[BaseModel] | None,
    action: Callable[..., None],
) -> dict[str, Any]:
    response = await execute_action(sid, raw_data, schema, action)
    if response.get("ok"):
        await broadcast_lobby()
    return response


@sio.event
async def connect(sid: str, environ: dict, auth: Any) -> bool | None:
    token = auth.get("token") if isinstance(auth, dict) else None
    if not verify_access_token(token):
        logger.warning(
            "Socket connection rejected by access verification",
            extra={"event": "socket.connect_rejected"},
        )
        return False
    account_token = (
        auth.get("accountToken") if isinstance(auth, dict) else None
    )
    account = account_store().account_for_token(account_token)
    if account is None:
        logger.warning(
            "Socket connection rejected by account verification",
            extra={"event": "socket.connect_rejected"},
        )
        return False
    await sio.save_session(sid, {"account_id": account.id})
    logger.debug(
        "Socket connected",
        extra={"account_id": account.id, "event": "socket.connected"},
    )
    await sio.emit(
        "lobby:rooms",
        build_lobby_view(rooms.rooms.values()),
        to=sid,
    )
    await arcade_realtime.on_connect(sid)
    return None


@sio.event
async def disconnect(sid: str, reason: str) -> None:
    await arcade_realtime.on_disconnect(sid)
    try:
        room, player_id = await context_for_sid(sid)
    except (RoomError, KeyError):
        return
    key = (room.code, player_id)
    active_sids[key].discard(sid)
    if not active_sids[key]:
        room.player(player_id).connected = False
        room.revision += 1
        active_sids.pop(key, None)
        rooms.update_human_presence(room)
        await broadcast_room(room)


@logged_socket_event("room:create")
async def create_room(sid: str, raw_data: Any) -> dict[str, Any]:
    try:
        account_id = await account_id_for_sid(sid)
        account = account_store().account_for_id(account_id)
        if account is None:
            raise RoomError("登录状态无效，请重新登录")
        room, player, token = rooms.create_room(
            account.player_name, account_id
        )
        await bind_session(sid, room, player.id)
        await broadcast_room(room)
        await broadcast_lobby()
        return {
            "ok": True,
            "roomCode": room.code,
            "playerId": player.id,
            "resumeToken": token,
        }
    except (ValidationError, RoomError) as error:
        return error_response(error)


@logged_socket_event("room:join")
async def join_room(sid: str, raw_data: Any) -> dict[str, Any]:
    try:
        payload = JoinPayload.model_validate(raw_data or {})
        account_id = await account_id_for_sid(sid)
        account = account_store().account_for_id(account_id)
        if account is None:
            raise RoomError("登录状态无效，请重新登录")
        room, player, token = rooms.join_room(
            payload.room_code, account.player_name, account_id
        )
        await bind_session(sid, room, player.id)
        await broadcast_room(room)
        await broadcast_lobby()
        return {
            "ok": True,
            "roomCode": room.code,
            "playerId": player.id,
            "resumeToken": token,
        }
    except (ValidationError, RoomError) as error:
        return error_response(error)


@logged_socket_event("room:resume")
async def resume_room(sid: str, raw_data: Any) -> dict[str, Any]:
    try:
        payload = ResumePayload.model_validate(raw_data or {})
        account_id = await account_id_for_sid(sid)
        room = rooms.get_room(payload.room_code)
        async with room.lock:
            room, player = rooms.resume(
                payload.room_code, payload.token, account_id
            )
        await bind_session(sid, room, player.id)
        await broadcast_room(room)
        return {
            "ok": True,
            "roomCode": room.code,
            "playerId": player.id,
        }
    except (ValidationError, RoomError) as error:
        return error_response(error)


@logged_socket_event("room:cleanup")
async def cleanup_room(sid: str, raw_data: Any) -> dict[str, Any]:
    try:
        payload = RoomCodePayload.model_validate(raw_data or {})
        await account_id_for_sid(sid)
        room = rooms.get_room(payload.room_code)
        async with room.lock:
            rooms.cleanup_room(room.code)
        await broadcast_lobby()
        await persist_room_state()
        return {"ok": True}
    except (ValidationError, RoomError, KeyError) as error:
        return error_response(error)


@logged_socket_event("room:leave")
async def leave_room(sid: str, raw_data: Any = None) -> dict[str, Any]:
    try:
        room, player_id = await context_for_sid(sid)
    except (RoomError, KeyError):
        # Leaving is idempotent. A reconnect after a server restart can leave
        # the browser showing a stale room even though the socket no longer
        # has room context; in that state the user's intent is already met.
        await clear_room_session(sid)
        return {"ok": True, "seatPreserved": False}

    try:
        seat_preserved = room.phase != Phase.LOBBY
        async with room.lock:
            if not seat_preserved:
                rooms.leave_lobby(room, player_id)
        await sio.leave_room(sid, player_channel(room.code, player_id))
        active_key = (room.code, player_id)
        active_sids[active_key].discard(sid)
        if not active_sids[active_key]:
            active_sids.pop(active_key, None)
            if seat_preserved:
                room.player(player_id).connected = False
                room.revision += 1
                rooms.update_human_presence(room)
        await clear_room_session(sid)
        if room.code in rooms.rooms:
            await broadcast_room(room)
        await broadcast_lobby()
        return {"ok": True, "seatPreserved": seat_preserved}
    except (RoomError, GameRuleError, KeyError) as error:
        return error_response(error)


@logged_socket_event("room:set-lady")
async def set_lady(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_lobby_action(
        sid,
        raw_data,
        LadySettingPayload,
        lambda room, player_id, payload: rooms.set_lady_enabled(
            room, player_id, payload.enabled
        ),
    )


@logged_socket_event("room:add-ai-player")
async def add_ai_player(
    sid: str, raw_data: Any = None
) -> dict[str, Any]:
    return await execute_lobby_action(
        sid, raw_data, None, rooms.add_ai_player
    )


@logged_socket_event("room:set-listed")
async def set_listed(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_lobby_action(
        sid,
        raw_data,
        ListedSettingPayload,
        lambda room, player_id, payload: rooms.set_listed(
            room, player_id, payload.listed
        ),
    )


@logged_socket_event("room:set-early-assassination")
async def set_early_assassination(
    sid: str, raw_data: Any
) -> dict[str, Any]:
    return await execute_lobby_action(
        sid,
        raw_data,
        EarlyAssassinationSettingPayload,
        lambda room, player_id, payload: (
            rooms.set_early_assassination_enabled(
                room, player_id, payload.enabled
            )
        ),
    )


@logged_socket_event("room:kick")
async def kick_player(sid: str, raw_data: Any) -> dict[str, Any]:
    try:
        payload = TargetPayload.model_validate(raw_data or {})
        room, player_id = await context_for_sid(sid)
        target_channel = player_channel(room.code, payload.target_id)
        async with room.lock:
            rooms.kick_player(room, player_id, payload.target_id)
        await sio.emit(
            "room:kicked",
            {"message": "你已被房主移出房间"},
            room=target_channel,
        )
        target_key = (room.code, payload.target_id)
        target_sids = list(active_sids.pop(target_key, set()))
        for target_sid in target_sids:
            await sio.disconnect(target_sid)
        await broadcast_room(room)
        await broadcast_lobby()
        return {"ok": True}
    except (ValidationError, RoomError, GameRuleError, KeyError) as error:
        return error_response(error)


@logged_socket_event("game:start")
async def start_game(sid: str, raw_data: Any = None) -> dict[str, Any]:
    return await execute_lobby_action(
        sid, raw_data, None, engine.start_game
    )


@logged_socket_event("game:confirm-role")
async def confirm_role(sid: str, raw_data: Any = None) -> dict[str, Any]:
    return await execute_action(sid, raw_data, None, engine.confirm_role)


@logged_socket_event("game:propose-team")
async def propose_team(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        TeamPayload,
        lambda room, player_id, payload: engine.propose_team(
            room, player_id, payload.team_ids
        ),
    )


@logged_socket_event("game:vote-team")
async def vote_team(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        TeamVotePayload,
        lambda room, player_id, payload: engine.vote_team(
            room, player_id, payload.approve
        ),
    )


@logged_socket_event("game:vote-mission")
async def vote_mission(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        MissionVotePayload,
        lambda room, player_id, payload: engine.vote_mission(
            room, player_id, payload.success
        ),
    )


@logged_socket_event("game:continue")
async def continue_game(sid: str, raw_data: Any = None) -> dict[str, Any]:
    return await execute_action(
        sid, raw_data, None, engine.continue_after_mission
    )


@logged_socket_event("game:lady-inspect")
async def lady_inspect(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        TargetPayload,
        lambda room, player_id, payload: engine.inspect_with_lady(
            room, player_id, payload.target_id
        ),
    )


@logged_socket_event("game:lady-acknowledge")
async def lady_acknowledge(
    sid: str, raw_data: Any = None
) -> dict[str, Any]:
    return await execute_action(sid, raw_data, None, engine.acknowledge_lady)


@logged_socket_event("game:assassinate")
async def assassinate(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        TargetPayload,
        lambda room, player_id, payload: engine.assassinate(
            room, player_id, payload.target_id
        ),
    )


@logged_socket_event("game:early-assassinate")
async def early_assassinate(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        TargetPayload,
        lambda room, player_id, payload: engine.early_assassinate(
            room, player_id, payload.target_id
        ),
    )


@logged_socket_event("game:restart")
async def restart(sid: str, raw_data: Any = None) -> dict[str, Any]:
    return await execute_lobby_action(sid, raw_data, None, engine.restart)


@logged_socket_event("chat:send")
async def send_chat(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        ChatPayload,
        lambda room, player_id, payload: rooms.send_chat(
            room, player_id, payload.content
        ),
    )


@logged_socket_event("lobby:list")
async def list_lobby_rooms(
    sid: str, raw_data: Any = None
) -> dict[str, Any]:
    return {
        "ok": True,
        "rooms": build_lobby_view(rooms.rooms.values()),
    }
