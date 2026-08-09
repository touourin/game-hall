from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import socketio

from .access import verify_access_token
from .accounts import account_store
from .arcade.models import ArcadeRoom
from .arcade.realtime import arcade_realtime
from .games.avalon.arcade import AvalonEngine
from .games.avalon.models import AvalonMode, Room
from .guests import guest_for_token
from .infrastructure import redis_url
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
room_state_store = RedisRoomStateStore(redis_connection_url)


def _repair_avalon_domain(room: Room) -> None:
    if not hasattr(room.settings, "mode"):
        room.settings.mode = AvalonMode.STANDARD
    room.ending_route = getattr(room, "ending_route", None)
    room.dagger_candidate_ids = getattr(room, "dagger_candidate_ids", [])
    room.dagger_target_id = getattr(room, "dagger_target_id", None)
    room.dagger_hit = getattr(room, "dagger_hit", None)
    room.transformed_player_id = getattr(room, "transformed_player_id", None)
    room.dissenting_assassination_target_id = getattr(
        room, "dissenting_assassination_target_id", None
    )
    room.lock = asyncio.Lock()
    for player in room.players:
        player.alignment_override = getattr(player, "alignment_override", None)
        player.disconnect_forfeited = getattr(
            player, "disconnect_forfeited", False
        )


async def restore_room_state() -> None:
    state = await room_state_store.load()
    if state is None:
        return

    restored: dict[str, ArcadeRoom] = {}
    saved_arcade_rooms = state.get("arcade")
    if isinstance(saved_arcade_rooms, dict):
        restored.update(
            {
                code: room
                for code, room in saved_arcade_rooms.items()
                if isinstance(code, str) and isinstance(room, ArcadeRoom)
            }
        )

    # One-time migration for rooms persisted before Avalon joined Arcade.
    saved_avalon_rooms = state.get("avalon")
    if isinstance(saved_avalon_rooms, dict):
        for code, legacy_room in saved_avalon_rooms.items():
            if (
                not isinstance(code, str)
                or not isinstance(legacy_room, Room)
                or code in restored
            ):
                continue
            _repair_avalon_domain(legacy_room)
            restored[code] = AvalonEngine.migrate_legacy_room(legacy_room)

    arcade_realtime.rooms.rooms = restored
    restored_at = datetime.now(timezone.utc)
    for room in restored.values():
        room.lock = asyncio.Lock()
        room.cleanup_ready = getattr(room, "cleanup_ready", False)
        room.stats_eligible = getattr(room, "stats_eligible", True)
        room.host_offline_since = None
        if room.game_key == "avalon" and isinstance(room.state, Room):
            _repair_avalon_domain(room.state)
        engine = arcade_realtime.engines.get(room.game_key)
        repair_restored_room = getattr(engine, "repair_restored_room", None)
        if callable(repair_restored_room):
            repair_restored_room(room)

        had_connected_human = any(
            player.connected and not getattr(player, "is_bot", False)
            for player in room.players
        )
        for player in room.players:
            player.is_bot = getattr(player, "is_bot", False)
            player.bot_difficulty = getattr(
                player,
                "bot_difficulty",
                "normal" if player.is_bot else None,
            )
            player.is_guest = getattr(player, "is_guest", False)
            player.left_room = getattr(player, "left_room", False)
            player.disconnected_at = None
            player.disconnect_timeout_handled = getattr(
                player, "disconnect_timeout_handled", False
            )
            player.disconnect_forfeited = getattr(
                player, "disconnect_forfeited", False
            )
            player.connected = player.is_bot
        if any(player.is_guest for player in room.players):
            room.stats_eligible = False
        if had_connected_human:
            room.all_humans_offline_since = restored_at
            room.cleanup_ready = False
        arcade_realtime.rooms.update_presence(room, now=restored_at)


async def persist_room_state() -> None:
    await room_state_store.save({"arcade": arcade_realtime.rooms.rooms})


async def close_room_state_store() -> None:
    await room_state_store.close()


async def resume_bot_turns() -> None:
    await arcade_realtime.resume_bot_turns()


async def warm_game_engines() -> None:
    await arcade_realtime.warm_up()


async def close_game_engines() -> None:
    await arcade_realtime.close()


async def maintain_game_rooms() -> None:
    while True:
        await asyncio.sleep(1)
        try:
            await arcade_realtime.maintain()
            await persist_room_state()
        except Exception:
            logger.exception(
                "Room maintenance iteration failed",
                extra={"event": "maintenance.failed"},
            )


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
    identity = account_store().account_for_token(account_token)
    is_guest = False
    if identity is None:
        identity = guest_for_token(account_token)
        is_guest = identity is not None
    if identity is None:
        logger.warning(
            "Socket connection rejected by account verification",
            extra={"event": "socket.connect_rejected"},
        )
        return False
    await sio.save_session(
        sid,
        {
            "account_id": identity.id,
            "account_session_hash": (
                None
                if is_guest
                else account_store().session_fingerprint(str(account_token))
            ),
            "player_name": identity.player_name,
            "avatar_url": identity.avatar_url,
            "is_guest": is_guest,
        },
    )
    logger.debug(
        "Socket connected",
        extra={"account_id": identity.id, "event": "socket.connected"},
    )
    await arcade_realtime.on_connect(sid, identity.id)
    return None


@sio.event
async def disconnect(sid: str, reason: str) -> None:
    await arcade_realtime.on_disconnect(sid)


async def replace_account_session_connections(account_id: str) -> int:
    return await arcade_realtime.replace_account_session(account_id)
