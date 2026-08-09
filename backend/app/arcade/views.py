from __future__ import annotations

from typing import Any

from backend.app.games.base import GameEngine

from .bots import ArcadeBotService
from .models import ArcadePlayer, ArcadeRoom, ArcadeSpectator
from .rooms import (
    ACTIVE_GAME_PHASES,
    DISCONNECT_FORFEIT_GRACE,
    DRAW_GAMES,
    HOST_TRANSFER_GRACE,
    MAX_CHAT_LENGTH,
    UNDO_GAMES,
    request_voter_ids,
)


def build_lobby_view(
    rooms: list[ArcadeRoom],
    engines: dict[str, GameEngine],
    spectator_counts: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    return [
        build_lobby_room_view(
            room,
            engines[room.game_key],
            spectator_count=(spectator_counts or {}).get(room.code, 0),
        )
        for room in rooms
        if room.cleanup_ready
        or (
            room.listed
            and (
                room.phase == "lobby"
                or (
                    room.phase != "finished"
                    and room.options.get("allowSpectators", True)
                )
            )
        )
    ]


def build_lobby_room_view(
    room: ArcadeRoom,
    engine: GameEngine,
    *,
    spectator_count: int = 0,
) -> dict[str, Any]:
    watchable = (
        room.phase not in {"lobby", "finished"}
        and room.options.get("allowSpectators", True)
    )
    return {
        "roomCode": room.code,
        "roomName": room.name,
        "gameKey": room.game_key,
        "gameName": engine.name,
        "hostName": room.host.name,
        "hostAvatarUrl": getattr(room.host, "avatar_url", None),
        "playerCount": len(room.players),
        "maxPlayers": engine.max_players,
        "players": [
            {
                "id": player.id,
                "name": player.name,
                "avatarUrl": getattr(player, "avatar_url", None),
                "seat": player.seat,
                "connected": player.connected,
                "leftRoom": player.left_room,
            }
            for player in room.players
            if not player.left_room
        ],
        "options": room.options,
        "allowsGuests": room.options.get("allowGuests", True),
        "statsEligible": room.stats_eligible,
        "phase": room.phase,
        "watchable": watchable,
        "spectatorCount": spectator_count,
        "cleanupAvailable": room.cleanup_ready,
        "allHumansOffline": room.all_humans_offline_since is not None,
    }


def build_room_view(
    room: ArcadeRoom,
    viewer: ArcadePlayer,
    engine: GameEngine,
    spectators: list[ArcadeSpectator] | None = None,
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
    start_checker = getattr(engine, "can_start", None)
    can_start = (
        room.phase == "lobby"
        and viewer.id == room.host_id
        and engine.min_players <= len(room.players) <= engine.max_players
        and (
            bool(start_checker(room, viewer))
            if start_checker is not None
            else True
        )
    )
    voter_ids = request_voter_ids(
        room,
        engine,
        pending_request.kind if pending_request is not None else "",
    )
    request_approved_ids = (
        pending_request.approved_player_ids & voter_ids
        if pending_request is not None
        else set()
    )
    end_table_voter_ids = request_voter_ids(room, engine, "end_table")
    bot_difficulties = (
        ArcadeBotService.difficulties(engine)
        if ArcadeBotService.supports(engine)
        else ()
    )
    difficulty_labels = {
        "easy": "简单",
        "normal": "普通",
        "hard": "困难",
    }
    return {
        "revision": room.revision,
        "roomCode": room.code,
        "roomName": room.name,
        "gameKey": room.game_key,
        "gameName": engine.name,
        "options": room.options,
        "phase": room.phase,
        "statsEligible": room.stats_eligible,
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
            "isGuest": viewer.is_guest,
        },
        "viewer": {
            "mode": "player",
            "id": viewer.id,
            "accountId": viewer.account_id,
            "name": viewer.name,
            "avatarUrl": getattr(viewer, "avatar_url", None),
            "isGuest": viewer.is_guest,
            "targetPlayerId": viewer.id,
        },
        "players": [
            {
                "id": player.id,
                "name": player.name,
                "avatarUrl": getattr(player, "avatar_url", None),
                "isBot": player.is_bot,
                "botDifficulty": getattr(player, "bot_difficulty", None),
                "isGuest": player.is_guest,
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
                "leftRoom": player.left_room,
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
        "ai": (
            {
                "difficulties": [
                    {
                        "key": difficulty,
                        "label": difficulty_labels.get(
                            difficulty, difficulty
                        ),
                    }
                    for difficulty in bot_difficulties
                ],
                "defaultDifficulty": getattr(
                    engine,
                    "default_bot_difficulty",
                    bot_difficulties[0],
                ),
            }
            if bot_difficulties
            else None
        ),
        "actions": {
            "canStart": can_start,
            "canRestart": can_restart,
            "canAct": is_active_phase,
            "canAddAiPlayer": (
                room.phase == "lobby"
                and viewer.id == room.host_id
                and len(room.players) < engine.max_players
                and ArcadeBotService.supports(engine)
            ),
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
            "canRequestEndTable": (
                is_active_phase
                and engine.max_players > 1
                and viewer.id in end_table_voter_ids
                and pending_request is None
            ),
            "canResolveRequest": (
                pending_request is not None
                and pending_request.requester_id != viewer.id
                and viewer.id not in request_approved_ids
            ),
        },
        "rematchReadyPlayerIds": sorted(room.rematch_ready_ids),
        "request": (
            {
                "kind": pending_request.kind,
                "requesterId": pending_request.requester_id,
                "requesterName": requester.name,
                "isMine": pending_request.requester_id == viewer.id,
                "hasApproved": viewer.id in request_approved_ids,
                "canRespond": (
                    viewer.id in voter_ids
                    and viewer.id != pending_request.requester_id
                    and viewer.id not in request_approved_ids
                ),
                "approvedPlayerIds": sorted(request_approved_ids),
                "approvalCount": len(request_approved_ids),
                "requiredApprovalCount": len(voter_ids),
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
        "spectators": _spectator_views(room, spectators or []),
        "game": engine.view(room, viewer),
    }


def build_spectator_room_view(
    room: ArcadeRoom,
    target: ArcadePlayer,
    spectator: ArcadeSpectator,
    engine: GameEngine,
    spectators: list[ArcadeSpectator] | None = None,
) -> dict[str, Any]:
    view = build_room_view(room, target, engine, spectators)
    view["self"].pop("accountId", None)
    view["viewer"] = {
        "mode": "spectator",
        "id": spectator.id,
        "accountId": spectator.account_id,
        "name": spectator.name,
        "avatarUrl": spectator.avatar_url,
        "isGuest": spectator.is_guest,
        "targetPlayerId": target.id,
    }
    view["actions"] = {
        action: False for action in view["actions"]
    }
    if view["request"] is not None:
        view["request"] = {
            **view["request"],
            "isMine": False,
            "hasApproved": False,
            "canRespond": False,
        }
    return view


def _spectator_views(
    room: ArcadeRoom,
    spectators: list[ArcadeSpectator],
) -> list[dict[str, Any]]:
    player_names = {player.id: player.name for player in room.players}
    return [
        {
            "id": spectator.id,
            "name": spectator.name,
            "avatarUrl": spectator.avatar_url,
            "isGuest": spectator.is_guest,
            "targetPlayerId": spectator.target_player_id,
            "targetPlayerName": player_names.get(
                spectator.target_player_id, "已离场玩家"
            ),
        }
        for spectator in sorted(
            spectators,
            key=lambda item: (item.name.casefold(), item.id),
        )
    ]


def _player_avatar_url(room: ArcadeRoom, player_id: str) -> str | None:
    player = next((item for item in room.players if item.id == player_id), None)
    return getattr(player, "avatar_url", None)
