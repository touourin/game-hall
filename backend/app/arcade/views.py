from __future__ import annotations

from typing import Any

from backend.app.games.base import GameEngine

from .models import ArcadePlayer, ArcadeRoom
from .rooms import DRAW_GAMES, MAX_CHAT_LENGTH, UNDO_GAMES


def build_lobby_view(
    rooms: list[ArcadeRoom], engines: dict[str, GameEngine]
) -> list[dict[str, Any]]:
    return [
        {
            "roomCode": room.code,
            "gameKey": room.game_key,
            "gameName": engines[room.game_key].name,
            "hostName": room.host.name,
            "playerCount": len(room.players),
            "maxPlayers": engines[room.game_key].max_players,
            "options": room.options,
        }
        for room in rooms
        if room.listed and room.phase == "lobby"
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
    return {
        "revision": room.revision,
        "roomCode": room.code,
        "gameKey": room.game_key,
        "gameName": engine.name,
        "options": room.options,
        "phase": room.phase,
        "hostId": room.host_id,
        "self": {
            "id": viewer.id,
            "name": viewer.name,
            "seat": viewer.seat,
        },
        "players": [
            {
                "id": player.id,
                "name": player.name,
                "seat": player.seat,
                "connected": player.connected,
                "isHost": player.id == room.host_id,
            }
            for player in room.players
        ],
        "requiredPlayers": engine.max_players,
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
            "canRestart": (
                room.phase == "finished"
                and viewer.id not in room.rematch_ready_ids
            ),
            "canAct": room.phase in {"setup", "playing", "bidding", "scoring"},
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
                    "content": message.content,
                    "createdAt": message.created_at,
                }
                for message in room.chat_messages
            ],
        },
        "game": engine.view(room, viewer),
    }
