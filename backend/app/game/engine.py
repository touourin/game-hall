from __future__ import annotations

import random
import secrets
from collections.abc import Sequence

from .models import (
    Alignment,
    LadyCheck,
    MissionRecord,
    Phase,
    ProposalRecord,
    Role,
    Room,
)
from .rules import (
    GOOD_EVIL_COUNTS,
    mission_fail_threshold,
    mission_team_size,
    roles_for_player_count,
)


class GameRuleError(ValueError):
    pass


EARLY_ASSASSINATION_PHASES = {
    Phase.TEAM_BUILDING,
    Phase.TEAM_VOTING,
    Phase.MISSION_VOTING,
    Phase.ROUND_RESULT,
    Phase.LADY_SELECT,
    Phase.LADY_REVEAL,
}


class GameEngine:
    def __init__(self, rng: random.Random | random.SystemRandom | None = None):
        self.rng = rng or secrets.SystemRandom()

    def start_game(self, room: Room, actor_id: str) -> None:
        self._require_phase(room, Phase.LOBBY)
        self._require_host(room, actor_id)
        player_count = len(room.players)
        if player_count not in GOOD_EVIL_COUNTS:
            raise GameRuleError("需要 5–10 名玩家才能开始")

        roles = roles_for_player_count(player_count)
        self.rng.shuffle(roles)
        for player, role in zip(room.players, roles, strict=True):
            player.role = role

        room.leader_index = self.rng.randrange(player_count)
        room.mission_index = 0
        room.proposal_attempt = 1
        room.selected_team_ids.clear()
        room.team_votes.clear()
        room.last_team_votes.clear()
        room.mission_votes.clear()
        room.mission_history.clear()
        room.proposal_history.clear()
        room.role_confirmed_ids.clear()
        room.winner = None
        room.win_reason = None
        room.assassin_target_id = None
        room.assassination_was_early = False
        room.lady_used_by_ids.clear()
        room.lady_checks.clear()
        room.lady_pending_inspector_id = None
        room.lady_pending_target_id = None
        room.lady_holder_id = (
            room.players[(room.leader_index - 1) % player_count].id
            if room.settings.lady_enabled
            else None
        )
        room.phase = Phase.ROLE_REVEAL
        self._touch(room)

    def confirm_role(self, room: Room, actor_id: str) -> None:
        self._require_phase(room, Phase.ROLE_REVEAL)
        self._require_player(room, actor_id)
        room.role_confirmed_ids.add(actor_id)
        if len(room.role_confirmed_ids) == len(room.players):
            room.phase = Phase.TEAM_BUILDING
        self._touch(room)

    def propose_team(
        self, room: Room, actor_id: str, team_ids: Sequence[str]
    ) -> None:
        self._require_phase(room, Phase.TEAM_BUILDING)
        if room.leader.id != actor_id:
            raise GameRuleError("只有当前队长可以选择任务队伍")
        required_size = mission_team_size(len(room.players), room.mission_index)
        if len(team_ids) != required_size or len(set(team_ids)) != required_size:
            raise GameRuleError(f"本轮必须选择 {required_size} 名不同的玩家")
        player_ids = {player.id for player in room.players}
        if not set(team_ids).issubset(player_ids):
            raise GameRuleError("任务队伍包含不存在的玩家")

        room.selected_team_ids = list(team_ids)
        room.team_votes.clear()
        room.phase = Phase.TEAM_VOTING
        self._touch(room)

    def vote_team(self, room: Room, actor_id: str, approve: bool) -> None:
        self._require_phase(room, Phase.TEAM_VOTING)
        self._require_player(room, actor_id)
        if actor_id in room.team_votes:
            raise GameRuleError("你已经提交过组队投票")

        room.team_votes[actor_id] = approve
        if len(room.team_votes) == len(room.players):
            room.last_team_votes = dict(room.team_votes)
            approvals = sum(room.team_votes.values())
            accepted = approvals > len(room.players) / 2
            room.proposal_history.append(
                ProposalRecord(
                    mission_number=room.mission_index + 1,
                    attempt=room.proposal_attempt,
                    leader_id=room.leader.id,
                    team_ids=list(room.selected_team_ids),
                    votes=dict(room.team_votes),
                    accepted=accepted,
                )
            )
            room.team_votes.clear()
            if accepted:
                room.mission_votes.clear()
                room.phase = Phase.MISSION_VOTING
            else:
                if room.proposal_attempt >= 5:
                    self._finish(
                        room,
                        Alignment.EVIL,
                        "同一任务连续五次组队被否决",
                    )
                else:
                    room.proposal_attempt += 1
                    self._rotate_leader(room)
                    room.selected_team_ids.clear()
                    room.phase = Phase.TEAM_BUILDING
        self._touch(room)

    def vote_mission(self, room: Room, actor_id: str, success: bool) -> None:
        self._require_phase(room, Phase.MISSION_VOTING)
        player = self._require_player(room, actor_id)
        if actor_id not in room.selected_team_ids:
            raise GameRuleError("你不在本次任务队伍中")
        if actor_id in room.mission_votes:
            raise GameRuleError("你已经提交过任务票")
        if player.alignment == Alignment.GOOD and not success:
            raise GameRuleError("好人阵营只能支持任务成功")

        room.mission_votes[actor_id] = success
        if len(room.mission_votes) == len(room.selected_team_ids):
            fail_count = sum(not vote for vote in room.mission_votes.values())
            threshold = mission_fail_threshold(
                len(room.players), room.mission_index
            )
            record = MissionRecord(
                number=room.mission_index + 1,
                team_ids=list(room.selected_team_ids),
                success=fail_count < threshold,
                fail_count=fail_count,
            )
            room.mission_history.append(record)
            room.mission_votes.clear()
            room.phase = Phase.ROUND_RESULT
        self._touch(room)

    def continue_after_mission(self, room: Room, actor_id: str) -> None:
        self._require_phase(room, Phase.ROUND_RESULT)
        self._require_player(room, actor_id)
        last_mission_number = room.mission_history[-1].number

        if room.fail_count >= 3:
            self._finish(room, Alignment.EVIL, "坏人阵营破坏了三次任务")
        elif room.success_count >= 3:
            room.phase = Phase.ASSASSINATION
        elif (
            room.settings.lady_enabled
            and last_mission_number in (2, 3, 4)
            and self.eligible_lady_targets(room)
        ):
            room.phase = Phase.LADY_SELECT
        else:
            self._advance_to_next_mission(room)
        self._touch(room)

    def inspect_with_lady(
        self, room: Room, actor_id: str, target_id: str
    ) -> None:
        self._require_phase(room, Phase.LADY_SELECT)
        if room.lady_holder_id != actor_id:
            raise GameRuleError("只有湖中仙女持有者可以查验")
        if target_id not in self.eligible_lady_targets(room):
            raise GameRuleError("该玩家不能被湖中仙女查验")

        target = self._require_player(room, target_id)
        assert target.alignment is not None
        room.lady_checks.append(
            LadyCheck(
                inspector_id=actor_id,
                target_id=target_id,
                alignment=target.alignment,
                mission_number=room.mission_history[-1].number,
            )
        )
        room.lady_used_by_ids.add(actor_id)
        room.lady_pending_inspector_id = actor_id
        room.lady_pending_target_id = target_id
        room.lady_holder_id = target_id
        room.phase = Phase.LADY_REVEAL
        self._touch(room)

    def acknowledge_lady(self, room: Room, actor_id: str) -> None:
        self._require_phase(room, Phase.LADY_REVEAL)
        if room.lady_pending_inspector_id != actor_id:
            raise GameRuleError("只有本次查验者可以确认结果")
        room.lady_pending_inspector_id = None
        room.lady_pending_target_id = None
        self._advance_to_next_mission(room)
        self._touch(room)

    def assassinate(self, room: Room, actor_id: str, target_id: str) -> None:
        self._require_phase(room, Phase.ASSASSINATION)
        self._resolve_assassination(room, actor_id, target_id, early=False)
        self._touch(room)

    def early_assassinate(
        self, room: Room, actor_id: str, target_id: str
    ) -> None:
        if not room.settings.early_assassination_enabled:
            raise GameRuleError("本房间没有开启提前刺杀")
        if room.phase not in EARLY_ASSASSINATION_PHASES:
            raise GameRuleError("当前阶段不能发动提前刺杀")
        self._resolve_assassination(room, actor_id, target_id, early=True)
        self._touch(room)

    def _resolve_assassination(
        self, room: Room, actor_id: str, target_id: str, *, early: bool
    ) -> None:
        assassin = self._require_player(room, actor_id)
        if assassin.role != Role.ASSASSIN:
            raise GameRuleError("只有刺客可以执行刺杀")
        target = self._require_player(room, target_id)
        if target.id == assassin.id:
            raise GameRuleError("刺客不能选择自己")

        room.assassin_target_id = target_id
        room.assassination_was_early = early
        if target.role == Role.MERLIN:
            reason = (
                "刺客提前刺杀并成功找出了梅林"
                if early
                else "刺客成功找出了梅林"
            )
            self._finish(room, Alignment.EVIL, reason)
        else:
            reason = (
                "刺客提前刺杀错误，好人阵营直接获胜"
                if early
                else "刺客未能找出梅林"
            )
            self._finish(room, Alignment.GOOD, reason)

    def restart(self, room: Room, actor_id: str) -> None:
        self._require_phase(room, Phase.GAME_OVER)
        self._require_host(room, actor_id)
        for player in room.players:
            player.role = None
        room.phase = Phase.LOBBY
        room.mission_index = 0
        room.proposal_attempt = 1
        room.selected_team_ids.clear()
        room.team_votes.clear()
        room.last_team_votes.clear()
        room.mission_votes.clear()
        room.mission_history.clear()
        room.proposal_history.clear()
        room.role_confirmed_ids.clear()
        room.winner = None
        room.win_reason = None
        room.assassin_target_id = None
        room.assassination_was_early = False
        room.lady_holder_id = None
        room.lady_used_by_ids.clear()
        room.lady_checks.clear()
        room.lady_pending_inspector_id = None
        room.lady_pending_target_id = None
        self._touch(room)

    def eligible_lady_targets(self, room: Room) -> list[str]:
        if room.lady_holder_id is None:
            return []
        return [
            player.id
            for player in room.players
            if player.id != room.lady_holder_id
            and player.id not in room.lady_used_by_ids
        ]

    def _advance_to_next_mission(self, room: Room) -> None:
        room.mission_index += 1
        room.proposal_attempt = 1
        room.selected_team_ids.clear()
        room.team_votes.clear()
        room.mission_votes.clear()
        self._rotate_leader(room)
        room.phase = Phase.TEAM_BUILDING

    def _finish(
        self, room: Room, winner: Alignment, reason: str
    ) -> None:
        room.winner = winner
        room.win_reason = reason
        room.phase = Phase.GAME_OVER

    @staticmethod
    def _rotate_leader(room: Room) -> None:
        room.leader_index = (room.leader_index + 1) % len(room.players)

    @staticmethod
    def _require_phase(room: Room, phase: Phase) -> None:
        if room.phase != phase:
            raise GameRuleError("当前阶段不能执行这个操作")

    @staticmethod
    def _require_player(room: Room, player_id: str):
        try:
            return room.player(player_id)
        except KeyError as exc:
            raise GameRuleError("玩家不存在") from exc

    @staticmethod
    def _require_host(room: Room, actor_id: str) -> None:
        if room.host_id != actor_id:
            raise GameRuleError("只有房主可以执行这个操作")

    @staticmethod
    def _touch(room: Room) -> None:
        room.revision += 1
