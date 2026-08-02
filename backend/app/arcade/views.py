from __future__ import annotations

from typing import Any

from backend.app.games.base import GameEngine

from .models import ArcadePlayer, ArcadeRoom
from .rooms import (
    ACTIVE_GAME_PHASES,
    DISCONNECT_FORFEIT_GRACE,
    DRAW_GAMES,
    HOST_TRANSFER_GRACE,
    MAX_CHAT_LENGTH,
    UNDO_GAMES,
)


def build_lobby_view(
    rooms: list[ArcadeRoom], engines: dict[str, GameEngine]
) -> list[dict[str, Any]]:
    return [
        {
            "roomCode": room.code,
            "gameKey": room.game_key,
            "gameName": engines[room.game_key].name,
            "hostName": room.host.name,
            "hostAvatarUrl": getattr(room.host, "avatar_url", None),
            "playerCount": len(room.players),
            "maxPlayers": engines[room.game_key].max_players,
            "options": room.options,
            "phase": room.phase,
            "cleanupAvailable": room.cleanup_ready,
            "allHumansOffline": room.all_humans_offline_since is not None,
        }
        for room in rooms
        if room.cleanup_ready or (room.listed and room.phase == "lobby")
    ]


def build_room_view(
    room: ArcadeRoom,
    viewer: ArcadePlayer,
    engine: GameEngine,
) -> dict[str, Any]:
    pending_request = room.pending_request
    requester = (
        room.player(pending_request.requester_id)
        if pending_request is not None
        else None
    )
    active_phase_checker = getattr(engine, "is_active_phase", None)
    is_active_phase = (
        bool(active_phase_checker(room.phase))
        if active_phase_checker is not None
        else room.phase in ACTIVE_GAME_PHASES
    )
    restart_checker = getattr(engine, "can_restart", None)
    can_restart = (
        bool(restart_checker(room, viewer))
        if restart_checker is not None
        else room.phase == "finished"
        and viewer.id not in room.rematch_ready_ids
    )
    return {
        "revision": room.revision,
        "roomCode": room.code,
        "gameKey": room.game_key,
        "gameName": engine.name,
        "options": room.options,
        "phase": room.phase,
        "hostTransferAt": (
            (room.host_offline_since + HOST_TRANSFER_GRACE).isoformat()
            if room.host_offline_since is not None
            else None
        ),
        "hostId": room.host_id,
        "self": {
            "id": viewer.id,
            "accountId": viewer.account_id,
            "name": viewer.name,
            "seat": viewer.seat,
            "avatarUrl": getattr(viewer, "avatar_url", None),
        },
        "players": [
            {
                "id": player.id,
                "name": player.name,
                "avatarUrl": getattr(player, "avatar_url", None),
                "isBot": player.is_bot,
                "seat": player.seat,
                "connected": player.connected,
                "disconnectForfeitAt": (
                    (
                        player.disconnected_at + DISCONNECT_FORFEIT_GRACE
                    ).isoformat()
                    if is_active_phase
                    and room.all_humans_offline_since is None
                    and not player.connected
                    and not player.disconnect_forfeited
                    and player.disconnected_at is not None
                    else None
                ),
                "disconnectForfeited": player.disconnect_forfeited,
                "isHost": player.id == room.host_id,
            }
            for player in room.players
        ],
        "requiredPlayers": engine.max_players,
        "minimumPlayers": engine.min_players,
        "roundNumber": room.round_number,
        "winner": room.winner,
        "winnerPlayerIds": room.winner_player_ids,
        "winReason": room.win_reason,
        "actions": {
            "canStart": (
                room.phase == "lobby"
                and viewer.id == room.host_id
                and engine.min_players <= len(room.players) <= engine.max_players
            ),
            "canRestart": can_restart,
            "canAct": is_active_phase,
            "canKickPlayers": room.phase == "lobby" and viewer.id == room.host_id,
            "canDissolve": room.phase == "lobby" and viewer.id == room.host_id,
            "canEditRules": (
                room.phase in {"lobby", "finished"}
                and viewer.id == room.host_id
            ),
            "canRequestUndo": (
                room.phase == "playing"
                and room.game_key in UNDO_GAMES
                and room.options.get("allowUndo", True)
                and bool(room.undo_history)
                and pending_request is None
            ),
            "canRequestDraw": (
                room.phase == "playing"
                and room.game_key in DRAW_GAMES
                and room.options.get("allowDraw", True)
                and pending_request is None
            ),
            "canResolveRequest": (
                pending_request is not None
                and pending_request.requester_id != viewer.id
            ),
        },
        "rematchReadyPlayerIds": sorted(room.rematch_ready_ids),
        "request": (
            {
                "kind": pending_request.kind,
                "requesterId": pending_request.requester_id,
                "requesterName": requester.name,
                "isMine": pending_request.requester_id == viewer.id,
            }
            if pending_request is not None and requester is not None
            else None
        ),
        "chat": {
            "maxLength": MAX_CHAT_LENGTH,
            "messages": [
                {
                    "id": message.id,
                    "senderId": message.sender_id,
                    "senderName": message.sender_name,
                    "senderAvatarUrl": _player_avatar_url(
                        room, message.sender_id
                    ),
                    "content": message.content,
                    "createdAt": message.created_at,
                }
                for message in room.chat_messages
            ],
        },
        "game": engine.view(room, viewer),
    }


def _player_avatar_url(room: ArcadeRoom, player_id: str) -> str | None:
    player = next((item for item in room.players if item.id == player_id), None)
    return getattr(player, "avatar_url", None)
