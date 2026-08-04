from __future__ import annotations

import random
import secrets
from collections import Counter
from collections.abc import Sequence
from datetime import datetime, timezone

from .models import (
    Alignment,
    AvalonMode,
    LadyCheck,
    MissionRecord,
    Phase,
    Player,
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

KNOWN_EVIL_ROLES = {
    Role.ASSASSIN,
    Role.MORGANA,
    Role.MORDRED,
    Role.MINION,
}

EXILE_COUNCIL_VOTING_ROLES = {
    Role.MERLIN,
    Role.PERCIVAL,
    Role.LOYAL_SERVANT,
    Role.DISSENTING_COURTIER,
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

        if room.settings.mode == AvalonMode.COURT_UNDERCURRENT:
            room.settings.lady_enabled = False
            room.settings.early_assassination_enabled = False
        if room.settings.shadow_merlin_enabled:
            if room.settings.mode != AvalonMode.COURT_UNDERCURRENT:
                raise GameRuleError("暗影梅林扩展必须先开启王庭暗流")
            if player_count < 6:
                raise GameRuleError("暗影梅林扩展至少需要 6 名玩家")

        roles = roles_for_player_count(
            player_count,
            room.settings.mode,
            shadow_merlin_enabled=room.settings.shadow_merlin_enabled,
        )
        self.rng.shuffle(roles)
        for player, role in zip(room.players, roles, strict=True):
            player.role = role
            player.alignment_override = None
            player.disconnected_at = None
            player.disconnect_forfeited = False

        room.game_id = secrets.token_urlsafe(12)
        room.game_started_at = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )
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
        room.ending_route = None
        room.dagger_candidate_ids.clear()
        room.dagger_target_id = None
        room.dagger_hit = None
        room.transformed_player_id = None
        room.dissenting_assassination_target_id = None
        room.shadow_merlin_transformed = False
        room.exile_council_triggered = False
        room.exile_council_open_votes.clear()
        room.exile_council_target_votes.clear()
        room.exile_council_opened = None
        room.exile_council_assassination_decisions.clear()
        room.exile_council_assassination_chosen = None
        room.exile_council_assassination_targets.clear()
        room.exile_council_assassination_target_id = None
        room.exile_council_exile_target_id = None
        room.exile_council_exile_success = None
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
                    room.mission_history.append(
                        MissionRecord(
                            number=room.mission_index + 1,
                            team_ids=[],
                            success=False,
                            fail_count=0,
                            failed_by_rejections=True,
                        )
                    )
                    room.selected_team_ids.clear()
                    room.mission_votes.clear()
                    room.phase = Phase.ROUND_RESULT
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
        if (
            player.alignment == Alignment.GOOD
            or player.role == Role.SHADOW_MERLIN
        ) and not success:
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
            self._finish(
                room,
                Alignment.EVIL,
                "坏人阵营破坏了三次任务",
                ending_route="missions",
            )
        elif (
            room.settings.shadow_merlin_enabled
            and room.fail_count >= 2
            and not room.exile_council_triggered
        ):
            self._start_exile_council(room)
        elif room.success_count >= 3:
            if room.settings.mode == AvalonMode.COURT_UNDERCURRENT:
                self._start_dagger_grant(room)
            else:
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

    def submit_exile_council_ballot(
        self,
        room: Room,
        actor_id: str,
        *,
        open_council: bool,
        target_id: str,
    ) -> None:
        self._require_phase(room, Phase.EXILE_COUNCIL_BALLOT)
        self._require_player(room, actor_id)
        self._require_player(room, target_id)
        if actor_id in room.exile_council_open_votes:
            raise GameRuleError("你已经提交过驱逐议会选票")

        room.exile_council_open_votes[actor_id] = open_council
        room.exile_council_target_votes[actor_id] = target_id
        if len(room.exile_council_open_votes) == len(room.players):
            valid_voters = [
                player
                for player in room.players
                if player.role in EXILE_COUNCIL_VOTING_ROLES
            ]
            approvals = sum(
                room.exile_council_open_votes[player.id]
                for player in valid_voters
            )
            rejections = len(valid_voters) - approvals
            room.exile_council_opened = approvals >= rejections
            if room.exile_council_opened:
                room.phase = Phase.EXILE_COUNCIL_ASSASSINATION_DECISION
            else:
                self._advance_to_next_mission(room)
        self._touch(room)

    def submit_exile_council_assassination_decision(
        self, room: Room, actor_id: str, assassinate: bool
    ) -> None:
        self._require_phase(
            room, Phase.EXILE_COUNCIL_ASSASSINATION_DECISION
        )
        self._require_player(room, actor_id)
        if actor_id in room.exile_council_assassination_decisions:
            raise GameRuleError("你已经提交过刺杀选择")

        room.exile_council_assassination_decisions[actor_id] = assassinate
        if len(room.exile_council_assassination_decisions) == len(
            room.players
        ):
            assassin = self._role_player(room, Role.ASSASSIN)
            chosen = room.exile_council_assassination_decisions[assassin.id]
            room.exile_council_assassination_chosen = chosen
            if chosen:
                self._transform_shadow_merlin(room)
                room.phase = Phase.EXILE_COUNCIL_ASSASSINATION_TARGET
            else:
                self._resolve_exile_council_vote(room)
        self._touch(room)

    def submit_exile_council_assassination_target(
        self, room: Room, actor_id: str, target_id: str
    ) -> None:
        self._require_phase(
            room, Phase.EXILE_COUNCIL_ASSASSINATION_TARGET
        )
        actor = self._require_player(room, actor_id)
        if actor.role != Role.ASSASSIN:
            raise GameRuleError("只有刺客可以选择刺杀目标")
        target = self._require_player(room, target_id)
        if actor_id in room.exile_council_assassination_targets:
            raise GameRuleError("你已经提交过刺杀目标")
        if target_id == actor_id:
            raise GameRuleError("不能选择自己作为刺杀目标")
        if target_id not in self.eligible_assassination_targets(room):
            raise GameRuleError("刺客不能选择已知的邪恶同伴")

        room.exile_council_assassination_targets[actor_id] = target_id
        self._resolve_exile_council_assassination(room, target)
        self._touch(room)

    def resolve_restored_exile_council_assassination(
        self, room: Room
    ) -> bool:
        """Finish a legacy in-progress vote once the assassin already chose."""
        if room.phase != Phase.EXILE_COUNCIL_ASSASSINATION_TARGET:
            return False
        assassin = self._role_player(room, Role.ASSASSIN)
        target_id = room.exile_council_assassination_targets.get(assassin.id)
        if target_id is None:
            return False
        target = self._require_player(room, target_id)
        self._resolve_exile_council_assassination(room, target)
        self._touch(room)
        return True

    def _resolve_exile_council_assassination(
        self, room: Room, target: Player
    ) -> None:
        room.exile_council_assassination_target_id = target.id
        room.assassin_target_id = target.id
        room.assassination_was_early = False
        if target.role == Role.MERLIN:
            self._finish(
                room,
                Alignment.EVIL,
                "驱逐议会中，刺客成功刺杀了梅林",
                ending_route="exile_council_assassination",
            )
        else:
            self._finish(
                room,
                Alignment.GOOD,
                "驱逐议会中，刺客未能找出梅林",
                ending_route="exile_council_assassination",
            )

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

    def grant_dagger(
        self, room: Room, actor_id: str, target_id: str
    ) -> None:
        self._require_phase(room, Phase.DAGGER_GRANT)
        assassin = self._require_player(room, actor_id)
        if assassin.role != Role.ASSASSIN:
            raise GameRuleError("只有刺客可以选择授刃目标")
        if target_id not in room.dagger_candidate_ids:
            raise GameRuleError("授刃目标不在候选名单中")

        target = self._require_player(room, target_id)
        room.dagger_target_id = target_id
        room.dagger_hit = target.role == Role.DISSENTING_COURTIER
        if not room.dagger_hit:
            self._finish(
                room,
                Alignment.GOOD,
                "刺客未能找出心怀异念之臣，授刃失败",
                ending_route="dagger_miss",
            )
        else:
            target.alignment_override = Alignment.EVIL
            room.transformed_player_id = target.id
            if room.settings.shadow_merlin_enabled:
                self._transform_shadow_merlin(room)
            room.phase = Phase.FINAL_COUNCIL
        self._touch(room)

    def dissenting_assassinate(
        self, room: Room, actor_id: str, target_id: str
    ) -> None:
        self._require_phase(room, Phase.FINAL_COUNCIL)
        actor = self._require_player(room, actor_id)
        if (
            actor.role != Role.DISSENTING_COURTIER
            or room.transformed_player_id != actor.id
            or actor.alignment != Alignment.EVIL
        ):
            raise GameRuleError("只有转化后的心怀异念之臣可以执行刺杀")
        if target_id not in self.eligible_dissenting_targets(room):
            raise GameRuleError("该玩家不能成为心怀异念之臣的刺杀目标")

        target = self._require_player(room, target_id)
        room.dissenting_assassination_target_id = target.id
        if target.role == Role.MERLIN:
            self._finish(
                room,
                Alignment.EVIL,
                "心怀异念之臣成功刺杀了梅林",
                ending_route="dissenting_assassination",
            )
        else:
            self._finish(
                room,
                Alignment.GOOD,
                "心怀异念之臣未能找出梅林",
                ending_route="dissenting_assassination",
            )
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
        if target.id not in self.eligible_assassination_targets(room):
            raise GameRuleError("刺客不能选择已知的邪恶同伴")

        room.assassin_target_id = target_id
        room.assassination_was_early = early
        if target.role == Role.MERLIN:
            reason = (
                "刺客提前刺杀并成功找出了梅林"
                if early
                else "刺客成功找出了梅林"
            )
            self._finish(
                room,
                Alignment.EVIL,
                reason,
                ending_route="standard_assassination",
            )
        else:
            reason = (
                "刺客提前刺杀错误，好人阵营直接获胜"
                if early
                else "刺客未能找出梅林"
            )
            self._finish(
                room,
                Alignment.GOOD,
                reason,
                ending_route="standard_assassination",
            )

    def restart(self, room: Room, actor_id: str) -> None:
        self._require_phase(room, Phase.GAME_OVER)
        self._require_host(room, actor_id)
        for player in room.players:
            player.role = None
            player.alignment_override = None
            player.disconnected_at = None
            player.disconnect_forfeited = False
        room.phase = Phase.LOBBY
        room.game_id = None
        room.game_started_at = None
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
        room.ending_route = None
        room.dagger_candidate_ids.clear()
        room.dagger_target_id = None
        room.dagger_hit = None
        room.transformed_player_id = None
        room.dissenting_assassination_target_id = None
        room.shadow_merlin_transformed = False
        room.exile_council_triggered = False
        room.exile_council_open_votes.clear()
        room.exile_council_target_votes.clear()
        room.exile_council_opened = None
        room.exile_council_assassination_decisions.clear()
        room.exile_council_assassination_chosen = None
        room.exile_council_assassination_targets.clear()
        room.exile_council_assassination_target_id = None
        room.exile_council_exile_target_id = None
        room.exile_council_exile_success = None
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

    def eligible_assassination_targets(self, room: Room) -> list[str]:
        return [
            player.id
            for player in room.players
            if player.role not in KNOWN_EVIL_ROLES
        ]

    def eligible_dissenting_targets(self, room: Room) -> list[str]:
        if room.transformed_player_id is None:
            return []
        return [
            player.id
            for player in room.players
            if player.id != room.transformed_player_id
            and player.role not in KNOWN_EVIL_ROLES
        ]

    def _start_dagger_grant(self, room: Room) -> None:
        dissenting = next(
            (
                player
                for player in room.players
                if player.role == Role.DISSENTING_COURTIER
            ),
            None,
        )
        if dissenting is None:
            raise GameRuleError("王庭暗流缺少心怀异念之臣")
        decoys = [
            player
            for player in room.players
            if player.id != dissenting.id
            and player.role not in KNOWN_EVIL_ROLES
        ]
        candidate_count = 3 if len(room.players) == 10 else 2
        candidates = [
            dissenting,
            *self.rng.sample(decoys, candidate_count - 1),
        ]
        self.rng.shuffle(candidates)
        room.dagger_candidate_ids = [player.id for player in candidates]
        room.phase = Phase.DAGGER_GRANT

    def _start_exile_council(self, room: Room) -> None:
        room.exile_council_triggered = True
        room.exile_council_open_votes.clear()
        room.exile_council_target_votes.clear()
        room.exile_council_opened = None
        room.exile_council_assassination_decisions.clear()
        room.exile_council_assassination_chosen = None
        room.exile_council_assassination_targets.clear()
        room.exile_council_assassination_target_id = None
        room.exile_council_exile_target_id = None
        room.exile_council_exile_success = None
        room.phase = Phase.EXILE_COUNCIL_BALLOT

    def _resolve_exile_council_vote(self, room: Room) -> None:
        valid_votes = [
            room.exile_council_target_votes[player.id]
            for player in room.players
            if player.role in EXILE_COUNCIL_VOTING_ROLES
        ]
        counts = Counter(valid_votes)
        highest = max(counts.values(), default=0)
        leaders = [
            player_id
            for player_id, count in counts.items()
            if count == highest
        ]
        unique_target_id = leaders[0] if len(leaders) == 1 else None
        shadow_merlin = self._role_player(room, Role.SHADOW_MERLIN)
        success = unique_target_id == shadow_merlin.id
        room.exile_council_exile_target_id = unique_target_id
        room.exile_council_exile_success = success
        if success:
            self._finish(
                room,
                Alignment.GOOD,
                "驱逐议会正确驱逐了暗影梅林",
                ending_route="exile_council_exile",
            )
        else:
            reason = (
                "驱逐议会最高票并列，好人阵营驱逐失败"
                if unique_target_id is None
                else "驱逐议会驱逐错误，好人阵营失败"
            )
            self._finish(
                room,
                Alignment.EVIL,
                reason,
                ending_route="exile_council_exile",
            )

    def _transform_shadow_merlin(self, room: Room) -> None:
        shadow_merlin = self._role_player(room, Role.SHADOW_MERLIN)
        shadow_merlin.alignment_override = Alignment.GOOD
        room.shadow_merlin_transformed = True

    def _advance_to_next_mission(self, room: Room) -> None:
        room.mission_index += 1
        room.proposal_attempt = 1
        room.selected_team_ids.clear()
        room.team_votes.clear()
        room.mission_votes.clear()
        self._rotate_leader(room)
        room.phase = Phase.TEAM_BUILDING

    def _finish(
        self,
        room: Room,
        winner: Alignment,
        reason: str,
        *,
        ending_route: str | None = None,
    ) -> None:
        room.winner = winner
        room.win_reason = reason
        room.ending_route = ending_route
        room.phase = Phase.GAME_OVER

    @staticmethod
    def _role_player(room: Room, role: Role) -> Player:
        player = next(
            (candidate for candidate in room.players if candidate.role == role),
            None,
        )
        if player is None:
            raise GameRuleError(f"本局缺少{role.value}身份")
        return player

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
