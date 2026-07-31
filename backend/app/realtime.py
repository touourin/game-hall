from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

import socketio
from pydantic import BaseModel, ValidationError

from .game.engine import GameEngine, GameRuleError
from .game.models import Room
from .rooms import RoomError, RoomManager
from .schemas import (
    ChatPayload,
    EarlyAssassinationSettingPayload,
    JoinPayload,
    LadySettingPayload,
    ListedSettingPayload,
    MissionVotePayload,
    NamePayload,
    RenamePlayerPayload,
    ResumePayload,
    TargetPayload,
    TeamPayload,
    TeamVotePayload,
)
from .views import build_lobby_view, build_player_view


sio = socketio.AsyncServer(
    async_mode="asgi",
    logger=False,
    engineio_logger=False,
)
rooms = RoomManager()
engine = GameEngine()
active_sids: dict[tuple[str, str], set[str]] = defaultdict(set)


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


async def bind_session(
    sid: str, room: Room, player_id: str
) -> None:
    await sio.save_session(
        sid, {"room_code": room.code, "player_id": player_id}
    )
    await sio.enter_room(sid, player_channel(room.code, player_id))
    active_sids[(room.code, player_id)].add(sid)
    room.player(player_id).connected = True


async def context_for_sid(sid: str) -> tuple[Room, str]:
    try:
        session = await sio.get_session(sid)
    except KeyError as exc:
        raise RoomError("连接还没有加入房间") from exc
    room = rooms.get_room(session["room_code"])
    player_id = session["player_id"]
    room.player(player_id)
    return room, player_id


def error_response(error: Exception) -> dict[str, Any]:
    if isinstance(error, ValidationError):
        return {"ok": False, "error": "提交的数据格式不正确"}
    return {"ok": False, "error": str(error)}


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
async def connect(sid: str, environ: dict, auth: Any) -> None:
    await sio.emit(
        "lobby:rooms",
        build_lobby_view(rooms.rooms.values()),
        to=sid,
    )


@sio.event
async def disconnect(sid: str, reason: str) -> None:
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
        await broadcast_room(room)


@sio.on("room:create")
async def create_room(sid: str, raw_data: Any) -> dict[str, Any]:
    try:
        payload = NamePayload.model_validate(raw_data or {})
        room, player, token = rooms.create_room(payload.name)
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


@sio.on("room:join")
async def join_room(sid: str, raw_data: Any) -> dict[str, Any]:
    try:
        payload = JoinPayload.model_validate(raw_data or {})
        room, player, token = rooms.join_room(
            payload.room_code, payload.name
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


@sio.on("room:resume")
async def resume_room(sid: str, raw_data: Any) -> dict[str, Any]:
    try:
        payload = ResumePayload.model_validate(raw_data or {})
        room, player = rooms.resume(payload.room_code, payload.token)
        await bind_session(sid, room, player.id)
        await broadcast_room(room)
        return {
            "ok": True,
            "roomCode": room.code,
            "playerId": player.id,
        }
    except (ValidationError, RoomError) as error:
        return error_response(error)


@sio.on("room:leave")
async def leave_room(sid: str, raw_data: Any = None) -> dict[str, Any]:
    try:
        room, player_id = await context_for_sid(sid)
        async with room.lock:
            rooms.leave_lobby(room, player_id)
        await sio.leave_room(sid, player_channel(room.code, player_id))
        active_sids[(room.code, player_id)].discard(sid)
        await sio.save_session(sid, {})
        if room.code in rooms.rooms:
            await broadcast_room(room)
        await broadcast_lobby()
        return {"ok": True}
    except (RoomError, GameRuleError, KeyError) as error:
        return error_response(error)


@sio.on("room:set-lady")
async def set_lady(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_lobby_action(
        sid,
        raw_data,
        LadySettingPayload,
        lambda room, player_id, payload: rooms.set_lady_enabled(
            room, player_id, payload.enabled
        ),
    )


@sio.on("room:set-listed")
async def set_listed(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_lobby_action(
        sid,
        raw_data,
        ListedSettingPayload,
        lambda room, player_id, payload: rooms.set_listed(
            room, player_id, payload.listed
        ),
    )


@sio.on("room:set-early-assassination")
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


@sio.on("room:kick")
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


@sio.on("room:rename-player")
async def rename_player(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        RenamePlayerPayload,
        lambda room, player_id, payload: rooms.rename_player(
            room, player_id, payload.target_id, payload.name
        ),
    )


@sio.on("game:start")
async def start_game(sid: str, raw_data: Any = None) -> dict[str, Any]:
    return await execute_lobby_action(
        sid, raw_data, None, engine.start_game
    )


@sio.on("game:confirm-role")
async def confirm_role(sid: str, raw_data: Any = None) -> dict[str, Any]:
    return await execute_action(sid, raw_data, None, engine.confirm_role)


@sio.on("game:propose-team")
async def propose_team(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        TeamPayload,
        lambda room, player_id, payload: engine.propose_team(
            room, player_id, payload.team_ids
        ),
    )


@sio.on("game:vote-team")
async def vote_team(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        TeamVotePayload,
        lambda room, player_id, payload: engine.vote_team(
            room, player_id, payload.approve
        ),
    )


@sio.on("game:vote-mission")
async def vote_mission(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        MissionVotePayload,
        lambda room, player_id, payload: engine.vote_mission(
            room, player_id, payload.success
        ),
    )


@sio.on("game:continue")
async def continue_game(sid: str, raw_data: Any = None) -> dict[str, Any]:
    return await execute_action(
        sid, raw_data, None, engine.continue_after_mission
    )


@sio.on("game:lady-inspect")
async def lady_inspect(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        TargetPayload,
        lambda room, player_id, payload: engine.inspect_with_lady(
            room, player_id, payload.target_id
        ),
    )


@sio.on("game:lady-acknowledge")
async def lady_acknowledge(
    sid: str, raw_data: Any = None
) -> dict[str, Any]:
    return await execute_action(sid, raw_data, None, engine.acknowledge_lady)


@sio.on("game:assassinate")
async def assassinate(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        TargetPayload,
        lambda room, player_id, payload: engine.assassinate(
            room, player_id, payload.target_id
        ),
    )


@sio.on("game:early-assassinate")
async def early_assassinate(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        TargetPayload,
        lambda room, player_id, payload: engine.early_assassinate(
            room, player_id, payload.target_id
        ),
    )


@sio.on("game:restart")
async def restart(sid: str, raw_data: Any = None) -> dict[str, Any]:
    return await execute_lobby_action(sid, raw_data, None, engine.restart)


@sio.on("chat:send")
async def send_chat(sid: str, raw_data: Any) -> dict[str, Any]:
    return await execute_action(
        sid,
        raw_data,
        ChatPayload,
        lambda room, player_id, payload: rooms.send_chat(
            room, player_id, payload.content
        ),
    )


@sio.on("lobby:list")
async def list_lobby_rooms(
    sid: str, raw_data: Any = None
) -> dict[str, Any]:
    return {
        "ok": True,
        "rooms": build_lobby_view(rooms.rooms.values()),
    }
