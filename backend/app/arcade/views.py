from __future__ import annotations

from typing import Any

from backend.app.games.base import GameEngine

from .models import ArcadePlayer, ArcadeRoom


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
        }
        for room in rooms
        if room.listed and room.phase == "lobby"
    ]


def build_room_view(
    room: ArcadeRoom,
    viewer: ArcadePlayer,
    engine: GameEngine,
) -> dict[str, Any]:
    return {
        "revision": room.revision,
        "roomCode": room.code,
        "gameKey": room.game_key,
        "gameName": engine.name,
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
        "winner": room.winner,
        "winnerPlayerIds": room.winner_player_ids,
        "winReason": room.win_reason,
        "actions": {
            "canStart": (
                room.phase == "lobby"
                and viewer.id == room.host_id
                and engine.min_players <= len(room.players) <= engine.max_players
            ),
            "canRestart": room.phase == "finished" and viewer.id == room.host_id,
            "canAct": room.phase in {"playing", "bidding"},
        },
        "game": engine.view(room, viewer),
    }
