from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .engine import EARLY_ASSASSINATION_PHASES, GameEngine
from .models import Alignment, Phase, Player, Role, Room
from .rules import (
    GOOD_EVIL_COUNTS,
    mission_fail_threshold,
    mission_team_size,
    roles_for_player_count,
)
from .rooms import HOST_TRANSFER_GRACE


ROLE_LABELS = {
    Role.MERLIN: "梅林",
    Role.PERCIVAL: "派西维尔",
    Role.LOYAL_SERVANT: "亚瑟的忠臣",
    Role.ASSASSIN: "刺客",
    Role.MORGANA: "莫甘娜",
    Role.MORDRED: "莫德雷德",
    Role.OBERON: "奥伯伦",
    Role.MINION: "莫德雷德的爪牙",
}

ROLE_DESCRIPTIONS = {
    Role.MERLIN: "你知道多数邪恶势力是谁，但必须隐藏自己的身份。",
    Role.PERCIVAL: "你能看到梅林与莫甘娜，但不知道两人各自的身份。",
    Role.LOYAL_SERVANT: "你没有额外信息，请通过发言和投票找出邪恶势力。",
    Role.ASSASSIN: "邪恶阵营。若好人完成三次任务，你可以刺杀梅林翻盘。",
    Role.MORGANA: "邪恶阵营。你会在派西维尔眼中伪装成梅林。",
    Role.MORDRED: "邪恶阵营。梅林无法看到你。",
    Role.OBERON: "邪恶阵营。你与其他邪恶玩家互相不可见。",
    Role.MINION: "邪恶阵营。隐藏身份并破坏三次任务。",
}


def build_lobby_view(all_rooms: Iterable[Room]) -> list[dict[str, Any]]:
    visible_rooms = [
        room
        for room in all_rooms
        if room.cleanup_ready
        or (
            room.phase == Phase.LOBBY
            and room.settings.listed
            and len(room.players) < 10
            and any(
                not player.is_bot and player.connected
                for player in room.players
            )
        )
    ]
    return [
        {
            "roomCode": room.code,
            "hostName": room.player(room.host_id).name,
            "playerCount": len(room.players),
            "maxPlayers": 10,
            "ladyEnabled": room.settings.lady_enabled,
            "phase": room.phase.value,
            "cleanupAvailable": room.cleanup_ready,
            "allHumansOffline": room.all_humans_offline_since is not None,
        }
        for room in reversed(visible_rooms)
    ]


def build_player_view(
    room: Room, viewer: Player, engine: GameEngine
) -> dict[str, Any]:
    player_count = len(room.players)
    current_mission_number = min(room.mission_index + 1, 5)
    required_team_size = (
        mission_team_size(player_count, room.mission_index)
        if player_count in GOOD_EVIL_COUNTS and room.mission_index < 5
        else None
    )
    current_fail_threshold = (
        mission_fail_threshold(player_count, room.mission_index)
        if player_count in GOOD_EVIL_COUNTS and room.mission_index < 5
        else 1
    )

    players = []
    for player in room.players:
        item: dict[str, Any] = {
            "id": player.id,
            "name": player.name,
            "seat": player.seat,
            "connected": player.connected,
            "isBot": player.is_bot,
            "isHost": player.id == room.host_id,
            "isLeader": room.phase != Phase.LOBBY
            and player.id == room.leader.id,
            "isSelected": player.id in room.selected_team_ids,
        }
        if room.phase in (Phase.ASSASSINATION, Phase.GAME_OVER):
            item["alignment"] = player.alignment.value
        if room.phase == Phase.GAME_OVER and player.role is not None:
            item["role"] = player.role.value
            item["roleLabel"] = ROLE_LABELS[player.role]
        players.append(item)

    private_role = None
    if room.phase != Phase.LOBBY and viewer.role is not None:
        role_description = ROLE_DESCRIPTIONS[viewer.role]
        if (
            viewer.role == Role.ASSASSIN
            and room.settings.early_assassination_enabled
        ):
            role_description += (
                " 本房已开启提前刺杀：任务进行期间可豪赌梅林，"
                "刺错则好人立即获胜。"
            )
        private_role = {
            "code": viewer.role.value,
            "label": ROLE_LABELS[viewer.role],
            "alignment": viewer.alignment.value,
            "description": role_description,
            "knowledge": _knowledge_for_player(room, viewer),
        }

    my_lady_checks = [
        {
            "targetId": check.target_id,
            "targetName": room.player(check.target_id).name,
            "alignment": check.alignment.value,
            "missionNumber": check.mission_number,
        }
        for check in room.lady_checks
        if check.inspector_id == viewer.id
    ]

    latest_lady_check = room.lady_checks[-1] if room.lady_checks else None
    public_lady_history = [
        {
            "inspectorId": check.inspector_id,
            "inspectorName": room.player(check.inspector_id).name,
            "targetId": check.target_id,
            "targetName": room.player(check.target_id).name,
            "missionNumber": check.mission_number,
        }
        for check in room.lady_checks
    ]

    role_preset = []
    if player_count in GOOD_EVIL_COUNTS:
        role_preset = [
            {"code": role.value, "label": ROLE_LABELS[role]}
            for role in roles_for_player_count(player_count)
        ]

    actions = {
        "canStart": room.phase == Phase.LOBBY
        and viewer.id == room.host_id
        and player_count in GOOD_EVIL_COUNTS,
        "canUpdateSettings": room.phase == Phase.LOBBY
        and viewer.id == room.host_id,
        "canDissolve": room.phase == Phase.LOBBY
        and viewer.id == room.host_id,
        "canLeave": True,
        "canConfirmRole": room.phase == Phase.ROLE_REVEAL
        and viewer.id not in room.role_confirmed_ids,
        "canProposeTeam": room.phase == Phase.TEAM_BUILDING
        and viewer.id == room.leader.id,
        "canVoteTeam": room.phase == Phase.TEAM_VOTING
        and viewer.id not in room.team_votes,
        "canVoteMission": room.phase == Phase.MISSION_VOTING
        and viewer.id in room.selected_team_ids
        and viewer.id not in room.mission_votes,
        "canMissionFail": viewer.alignment == Alignment.EVIL,
        "canContinueRound": room.phase == Phase.ROUND_RESULT,
        "canUseLady": room.phase == Phase.LADY_SELECT
        and viewer.id == room.lady_holder_id,
        "canAcknowledgeLady": room.phase == Phase.LADY_REVEAL
        and viewer.id == room.lady_pending_inspector_id,
        "canAssassinate": room.phase == Phase.ASSASSINATION
        and viewer.role == Role.ASSASSIN,
        "canEarlyAssassinate": room.settings.early_assassination_enabled
        and room.phase in EARLY_ASSASSINATION_PHASES
        and viewer.role == Role.ASSASSIN,
        "canAddAiPlayer": room.phase == Phase.LOBBY
        and viewer.id == room.host_id
        and player_count < 10,
        "canRestart": room.phase == Phase.GAME_OVER
        and viewer.id == room.host_id,
    }

    return {
        "roomCode": room.code,
        "revision": room.revision,
        "phase": room.phase.value,
        "hostTransferAt": (
            (room.host_offline_since + HOST_TRANSFER_GRACE).isoformat()
            if room.host_offline_since is not None
            else None
        ),
        "self": {
            "id": viewer.id,
            "name": viewer.name,
            "isHost": viewer.id == room.host_id,
            "role": private_role,
        },
        "players": players,
        "settings": {
            "ladyEnabled": room.settings.lady_enabled,
            "ladyRecommended": player_count >= 7,
            "listed": room.settings.listed,
            "earlyAssassinationEnabled": (
                room.settings.early_assassination_enabled
            ),
            "rolePreset": role_preset,
        },
        "game": {
            "missionNumber": current_mission_number,
            "requiredTeamSize": required_team_size,
            "failThreshold": current_fail_threshold,
            "leaderId": room.leader.id if room.phase != Phase.LOBBY else None,
            "proposalAttempt": room.proposal_attempt,
            "selectedTeamIds": list(room.selected_team_ids),
            "teamVotesSubmitted": len(room.team_votes),
            "myTeamVoteSubmitted": viewer.id in room.team_votes,
            "lastTeamVotes": [
                {"playerId": player_id, "approve": approve}
                for player_id, approve in room.last_team_votes.items()
            ],
            "missionVotesSubmitted": len(room.mission_votes),
            "myMissionVoteSubmitted": viewer.id in room.mission_votes,
            "roleConfirmedCount": len(room.role_confirmed_ids),
            "missionHistory": [
                {
                    "number": record.number,
                    "teamIds": record.team_ids,
                    "success": record.success,
                    "failCount": record.fail_count,
                }
                for record in room.mission_history
            ],
            "proposalHistory": [
                {
                    "missionNumber": record.mission_number,
                    "attempt": record.attempt,
                    "leaderId": record.leader_id,
                    "teamIds": record.team_ids,
                    "votes": [
                        {
                            "playerId": player.id,
                            "approve": record.votes[player.id],
                        }
                        for player in room.players
                    ],
                    "accepted": record.accepted,
                }
                for record in room.proposal_history
            ],
            "successCount": room.success_count,
            "failCount": room.fail_count,
        },
        "lady": {
            "enabled": room.settings.lady_enabled,
            "holderId": room.lady_holder_id,
            "usedByIds": list(room.lady_used_by_ids),
            "eligibleTargetIds": (
                engine.eligible_lady_targets(room)
                if actions["canUseLady"]
                else []
            ),
            "pendingInspectorId": room.lady_pending_inspector_id,
            "pendingTargetId": room.lady_pending_target_id,
            "history": public_lady_history,
            "myChecks": my_lady_checks,
            "currentResult": (
                {
                    "targetId": latest_lady_check.target_id,
                    "targetName": room.player(latest_lady_check.target_id).name,
                    "alignment": latest_lady_check.alignment.value,
                }
                if latest_lady_check
                and room.phase == Phase.LADY_REVEAL
                and room.lady_pending_inspector_id == viewer.id
                else None
            ),
        },
        "result": {
            "winner": room.winner.value if room.winner else None,
            "reason": room.win_reason,
            "assassinTargetId": room.assassin_target_id,
            "assassinationWasEarly": room.assassination_was_early,
        },
        "chat": {
            "maxLength": 300,
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
        "actions": actions,
    }


def _knowledge_for_player(room: Room, viewer: Player) -> list[dict[str, str]]:
    knowledge: list[dict[str, str]] = []
    if viewer.role == Role.MERLIN:
        for player in room.players:
            if player.alignment == Alignment.EVIL and player.role != Role.MORDRED:
                knowledge.append(
                    {
                        "playerId": player.id,
                        "playerName": player.name,
                        "kind": "evil",
                        "label": "你看到的邪恶势力",
                    }
                )
    elif viewer.role == Role.PERCIVAL:
        for player in room.players:
            if player.role in (Role.MERLIN, Role.MORGANA):
                knowledge.append(
                    {
                        "playerId": player.id,
                        "playerName": player.name,
                        "kind": "merlin_candidate",
                        "label": "梅林或莫甘娜",
                    }
                )
    elif viewer.alignment == Alignment.EVIL and viewer.role != Role.OBERON:
        for player in room.players:
            if (
                player.id != viewer.id
                and player.alignment == Alignment.EVIL
                and player.role != Role.OBERON
            ):
                knowledge.append(
                    {
                        "playerId": player.id,
                        "playerName": player.name,
                        "kind": "evil_ally",
                        "label": "邪恶同伴",
                    }
                )
    return knowledge
