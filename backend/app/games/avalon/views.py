from __future__ import annotations

from typing import Any

from backend.app.arcade.rooms import (
    DISCONNECT_FORFEIT_GRACE,
    HOST_TRANSFER_GRACE,
)

from .engine import (
    EARLY_ASSASSINATION_PHASES,
    EXILE_COUNCIL_VOTING_ROLES,
    GameEngine,
)
from .models import Alignment, AvalonMode, Phase, Player, Role, Room
from .rules import (
    GOOD_EVIL_COUNTS,
    mission_fail_threshold,
    mission_team_size,
    roles_for_player_count,
)


ROLE_LABELS = {
    Role.MERLIN: "梅林",
    Role.PERCIVAL: "派西维尔",
    Role.LOYAL_SERVANT: "亚瑟的忠臣",
    Role.DISSENTING_COURTIER: "心怀异念之臣",
    Role.SHADOW_MERLIN: "暗影梅林",
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
    Role.DISSENTING_COURTIER: (
        "你开局属于好人且只能支持任务成功。你知道刺客是谁，"
        "可以选择隐藏身份，也可以通过发言争取被授刃。"
    ),
    Role.SHADOW_MERLIN: (
        "你开局潜伏于邪恶阵营，叠加梅林、派西维尔与心怀异念之臣"
        "的视野，能够准确看见梅林及除莫德雷德外所有邪恶角色，但"
        "无法提交任务失败票。任何刺杀开始后，你会立刻转为好人阵营；"
        "若梅林被刺中，你也会失败。"
    ),
    Role.ASSASSIN: "邪恶阵营。若好人完成三次任务，你可以刺杀梅林翻盘。",
    Role.MORGANA: "邪恶阵营。你会在派西维尔眼中伪装成梅林。",
    Role.MORDRED: "邪恶阵营。梅林无法看到你。",
    Role.OBERON: "邪恶阵营。你与其他邪恶玩家互相不可见。",
    Role.MINION: "邪恶阵营。隐藏身份并破坏三次任务。",
}

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
            "avatarUrl": getattr(player, "avatar_url", None),
            "seat": player.seat,
            "connected": player.connected,
            "disconnectForfeitAt": (
                (
                    player.disconnected_at + DISCONNECT_FORFEIT_GRACE
                ).isoformat()
                if room.phase not in {Phase.LOBBY, Phase.GAME_OVER}
                and room.all_humans_offline_since is None
                and not player.is_bot
                and not player.connected
                and not player.disconnect_forfeited
                and player.disconnected_at is not None
                else None
            ),
            "disconnectForfeited": player.disconnect_forfeited,
            "isBot": player.is_bot,
            "isHost": player.id == room.host_id,
            "isLeader": room.phase != Phase.LOBBY
            and player.id == room.leader.id,
            "isSelected": player.id in room.selected_team_ids,
        }
        if room.phase == Phase.GAME_OVER or (
            room.phase == Phase.ASSASSINATION
            and player.alignment == Alignment.EVIL
            and player.role != Role.OBERON
        ):
            item["alignment"] = player.alignment.value
        if room.phase == Phase.GAME_OVER and player.role is not None:
            item["role"] = player.role.value
            item["roleLabel"] = ROLE_LABELS[player.role]
        players.append(item)

    private_role = None
    if room.phase != Phase.LOBBY and viewer.role is not None:
        role_description = ROLE_DESCRIPTIONS[viewer.role]
        if (
            room.settings.mode == AvalonMode.COURT_UNDERCURRENT
            and viewer.role == Role.ASSASSIN
        ):
            role_description = (
                "邪恶阵营。你知道场上存在心怀异念之臣，但不知道是谁。"
                "好人完成三次任务后，你必须从私密候选中向他授刃。"
            )
            if room.settings.shadow_merlin_enabled:
                role_description += (
                    " 邪恶累计两次任务失败后会触发暗刃议影提案；"
                    "议影若开启，你可以选择发动一次刺杀或放弃刺杀并"
                    "结算裁影。只有你可以发动刺杀并选择刺杀目标。"
                )
        if (
            viewer.role == Role.DISSENTING_COURTIER
            and room.transformed_player_id == viewer.id
        ):
            role_description = (
                "你已被黑誓之刃强制转化为邪恶阵营。"
                "利用最后议事判断梅林，并由你亲自完成刺杀。"
            )
        if (
            viewer.role == Role.SHADOW_MERLIN
            and room.shadow_merlin_transformed
        ):
            role_description = (
                "刺杀已经开始，你已转为好人阵营。保护梅林不被刺中；"
                "若梅林死亡，你也会一同失败。"
            )
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
    if player_count in GOOD_EVIL_COUNTS and (
        not room.settings.shadow_merlin_enabled or player_count >= 6
    ):
        role_preset = [
            {"code": role.value, "label": ROLE_LABELS[role]}
            for role in roles_for_player_count(
                player_count,
                room.settings.mode,
                shadow_merlin_enabled=(
                    room.settings.shadow_merlin_enabled
                ),
            )
        ]

    actions = {
        "canStart": room.phase == Phase.LOBBY
        and viewer.id == room.host_id
        and player_count in GOOD_EVIL_COUNTS
        and (
            not room.settings.shadow_merlin_enabled or player_count >= 6
        ),
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
        "canMissionFail": viewer.alignment == Alignment.EVIL
        and viewer.role != Role.SHADOW_MERLIN,
        "canContinueRound": room.phase == Phase.ROUND_RESULT,
        "canSubmitExileCouncilBallot": (
            room.phase == Phase.EXILE_COUNCIL_BALLOT
            and viewer.id not in room.exile_council_open_votes
        ),
        "canSubmitExileCouncilAssassinationDecision": (
            room.phase == Phase.EXILE_COUNCIL_ASSASSINATION_DECISION
            and viewer.id
            not in room.exile_council_assassination_decisions
        ),
        "canSubmitExileCouncilAssassinationTarget": (
            room.phase == Phase.EXILE_COUNCIL_ASSASSINATION_TARGET
            and viewer.role == Role.ASSASSIN
            and viewer.id not in room.exile_council_assassination_targets
        ),
        "canUseLady": room.phase == Phase.LADY_SELECT
        and viewer.id == room.lady_holder_id,
        "canAcknowledgeLady": room.phase == Phase.LADY_REVEAL
        and viewer.id == room.lady_pending_inspector_id,
        "canAssassinate": room.phase == Phase.ASSASSINATION
        and viewer.role == Role.ASSASSIN,
        "canGrantDagger": room.phase == Phase.DAGGER_GRANT
        and viewer.role == Role.ASSASSIN,
        "canDissentingAssassinate": room.phase == Phase.FINAL_COUNCIL
        and room.transformed_player_id == viewer.id,
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
            "avatarUrl": getattr(viewer, "avatar_url", None),
            "isHost": viewer.id == room.host_id,
            "role": private_role,
        },
        "players": players,
        "settings": {
            "mode": room.settings.mode.value,
            "shadowMerlinEnabled": room.settings.shadow_merlin_enabled,
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
                    "failedByRejections": getattr(
                        record, "failed_by_rejections", False
                    ),
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
            "endingRoute": room.ending_route,
            "assassinTargetId": room.assassin_target_id,
            "assassinationWasEarly": room.assassination_was_early,
            "eligibleTargetIds": (
                engine.eligible_assassination_targets(room)
                if actions["canAssassinate"]
                or actions["canEarlyAssassinate"]
                else []
            ),
        },
        "courtUndercurrent": {
            "enabled": (
                room.settings.mode == AvalonMode.COURT_UNDERCURRENT
            ),
            "daggerCandidateIds": (
                list(room.dagger_candidate_ids)
                if actions["canGrantDagger"]
                or room.phase == Phase.GAME_OVER
                else []
            ),
            "daggerTargetId": (
                room.dagger_target_id
                if room.phase in {Phase.FINAL_COUNCIL, Phase.GAME_OVER}
                or viewer.role == Role.ASSASSIN
                or viewer.id == room.transformed_player_id
                else None
            ),
            "daggerHit": (
                room.dagger_hit
                if room.phase in {Phase.FINAL_COUNCIL, Phase.GAME_OVER}
                else None
            ),
            "transformedPlayerId": (
                room.transformed_player_id
                if room.phase in {Phase.FINAL_COUNCIL, Phase.GAME_OVER}
                else None
            ),
            "eligibleTargetIds": (
                engine.eligible_dissenting_targets(room)
                if actions["canDissentingAssassinate"]
                or room.phase == Phase.GAME_OVER
                else []
            ),
            "assassinationTargetId": (
                room.dissenting_assassination_target_id
                if room.phase == Phase.GAME_OVER
                else None
            ),
        },
        "shadowMerlin": {
            "enabled": room.settings.shadow_merlin_enabled,
            "transformed": room.shadow_merlin_transformed,
            "councilTriggered": room.exile_council_triggered,
            "councilOpened": room.exile_council_opened,
            "ballotsSubmitted": len(room.exile_council_open_votes),
            "myBallotSubmitted": (
                viewer.id in room.exile_council_open_votes
            ),
            "eligibleExileTargetIds": (
                [player.id for player in room.players]
                if actions["canSubmitExileCouncilBallot"]
                else []
            ),
            "assassinationDecisionsSubmitted": len(
                room.exile_council_assassination_decisions
            ),
            "myAssassinationDecisionSubmitted": (
                viewer.id in room.exile_council_assassination_decisions
            ),
            "assassinationChosen": (
                room.exile_council_assassination_chosen
            ),
            "assassinationTargetsSubmitted": len(
                room.exile_council_assassination_targets
            ),
            "myAssassinationTargetSubmitted": (
                viewer.id in room.exile_council_assassination_targets
            ),
            "eligibleAssassinationTargetIds": (
                engine.eligible_assassination_targets(room)
                if actions[
                    "canSubmitExileCouncilAssassinationTarget"
                ]
                else []
            ),
            "assassinationTargetId": (
                room.exile_council_assassination_target_id
                if room.phase == Phase.GAME_OVER
                else None
            ),
            "exileTargetId": (
                room.exile_council_exile_target_id
                if room.phase == Phase.GAME_OVER
                else None
            ),
            "exileSuccess": (
                room.exile_council_exile_success
                if room.phase == Phase.GAME_OVER
                else None
            ),
            "openVotes": (
                [
                    {
                        "playerId": player.id,
                        "openCouncil": (
                            room.exile_council_open_votes[player.id]
                        ),
                        "effective": (
                            player.role in EXILE_COUNCIL_VOTING_ROLES
                        ),
                    }
                    for player in room.players
                    if player.id in room.exile_council_open_votes
                ]
                if room.phase == Phase.GAME_OVER
                else []
            ),
            "targetVotes": (
                [
                    {
                        "playerId": player.id,
                        "targetId": (
                            room.exile_council_target_votes[player.id]
                        ),
                        "effective": (
                            player.role in EXILE_COUNCIL_VOTING_ROLES
                        ),
                    }
                    for player in room.players
                    if player.id in room.exile_council_target_votes
                ]
                if room.phase == Phase.GAME_OVER
                else []
            ),
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
            if (
                player.alignment == Alignment.EVIL
                and player.role
                not in {
                    Role.MORDRED,
                    Role.DISSENTING_COURTIER,
                    Role.SHADOW_MERLIN,
                }
            ):
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
    elif viewer.role == Role.SHADOW_MERLIN:
        for player in room.players:
            if player.role in {
                Role.MERLIN,
                Role.ASSASSIN,
                Role.MORGANA,
                Role.OBERON,
                Role.MINION,
            }:
                knowledge.append(
                    {
                        "playerId": player.id,
                        "playerName": player.name,
                        "kind": "special_identity",
                        "label": ROLE_LABELS[player.role],
                    }
                )
    elif viewer.role == Role.DISSENTING_COURTIER:
        for player in room.players:
            if player.role == Role.ASSASSIN:
                knowledge.append(
                    {
                        "playerId": player.id,
                        "playerName": player.name,
                        "kind": "assassin",
                        "label": "你认出的刺客",
                    }
                )
            elif (
                room.transformed_player_id == viewer.id
                and player.id != viewer.id
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
    elif viewer.alignment == Alignment.EVIL and viewer.role not in {
        Role.OBERON,
        Role.SHADOW_MERLIN,
    }:
        for player in room.players:
            if (
                player.id != viewer.id
                and player.alignment == Alignment.EVIL
                and player.role not in {
                    Role.OBERON,
                    Role.SHADOW_MERLIN,
                }
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
