import random
from collections import Counter

import pytest

from backend.app.arcade.rooms import ArcadeRoomError, ArcadeRoomManager
from backend.app.games.base import GameRuleError
from backend.app.games.avalon.arcade import AvalonEngine
from backend.app.games.avalon.engine import GameEngine as AvalonRulesEngine
from backend.app.games.avalon.models import (
    Alignment,
    MissionRecord,
    Phase,
    Role,
)

from .test_engine import confirm_all_roles, make_room


def unified_avalon(player_count: int = 5):
    engine = AvalonEngine(AvalonRulesEngine(random.Random(42)))
    manager = ArcadeRoomManager({"avalon": engine}, random.Random(7))
    room, host, _ = manager.create_room(
        "avalon", "玩家0", "account-0"
    )
    for index in range(1, player_count):
        manager.join_room(
            room.code,
            "avalon",
            f"玩家{index}",
            f"account-{index}",
        )
    return manager, engine, room, host


def test_arcade_adapter_preserves_standard_avalon_rule_transitions() -> None:
    direct_room = make_room(5)
    direct_rules = AvalonRulesEngine(random.Random(42))
    manager, adapter, room, host = unified_avalon(5)

    direct_rules.start_game(direct_room, direct_room.host_id)
    manager.start(room, host.id)
    domain = room.state

    assert domain.phase == direct_room.phase == Phase.ROLE_REVEAL
    assert domain.leader_index == direct_room.leader_index
    assert [player.role for player in domain.players] == [
        player.role for player in direct_room.players
    ]
    assert domain.lady_holder_id == domain.players[
        (domain.leader_index - 1) % 5
    ].id

    confirm_all_roles(direct_rules, direct_room)
    for player in room.players:
        manager.act(room, player.id, "confirm_role", {})
    assert domain.phase == direct_room.phase == Phase.TEAM_BUILDING

    direct_team = [player.id for player in direct_room.players[:2]]
    unified_team = [player.id for player in room.players[:2]]
    direct_rules.propose_team(direct_room, direct_room.leader.id, direct_team)
    manager.act(
        room,
        domain.leader.id,
        "propose_team",
        {"team_ids": unified_team},
    )
    for index in range(5):
        approve = index < 3
        direct_rules.vote_team(direct_room, direct_room.players[index].id, approve)
        manager.act(room, room.players[index].id, "vote_team", {"approve": approve})

    assert domain.phase == direct_room.phase == Phase.MISSION_VOTING
    assert domain.proposal_history[-1].accepted is True
    for direct_id, unified_id in zip(direct_team, unified_team, strict=True):
        direct_rules.vote_mission(direct_room, direct_id, True)
        manager.act(room, unified_id, "vote_mission", {"success": True})

    assert domain.phase == direct_room.phase == Phase.ROUND_RESULT
    assert domain.mission_history[-1].success is True
    assert domain.mission_history[-1].fail_count == 0
    assert adapter.view(room, host)["game"]["successCount"] == 1


def test_court_undercurrent_keeps_its_original_fixed_rule_constraints() -> None:
    manager, _, room, host = unified_avalon(5)

    manager.update_options(
        room,
        host.id,
        {
            "mode": "court_undercurrent",
            "ladyEnabled": True,
            "listed": False,
            "earlyAssassinationEnabled": True,
        },
    )

    assert room.options == {
        "allowGuests": True,
        "mode": "court_undercurrent",
        "shadowMerlinEnabled": False,
        "ladyEnabled": False,
        "listed": False,
        "earlyAssassinationEnabled": False,
    }
    assert room.listed is False
    manager.start(room, host.id)
    domain = room.state
    assert domain.settings.lady_enabled is False
    assert domain.settings.early_assassination_enabled is False

    with pytest.raises(ArcadeRoomError, match="等待房间"):
        manager.update_options(room, host.id, {"mode": "standard"})


def test_shadow_merlin_is_a_six_player_court_only_extension() -> None:
    manager, adapter, room, host = unified_avalon(5)
    manager.update_options(
        room,
        host.id,
        {
            "mode": "court_undercurrent",
            "shadowMerlinEnabled": True,
        },
    )

    assert room.options["shadowMerlinEnabled"] is True
    assert adapter.view(room, host)["actions"]["canStart"] is False
    with pytest.raises(GameRuleError, match="至少需要 6"):
        manager.start(room, host.id)

    manager.update_options(
        room,
        host.id,
        {"mode": "standard", "shadowMerlinEnabled": True},
    )
    assert room.options["shadowMerlinEnabled"] is False


def test_council_assassination_accepts_new_and_open_browser_action_names() -> None:
    manager, adapter, room, host = unified_avalon(6)
    manager.start(room, host.id)
    domain = room.state
    domain.phase = Phase.EXILE_COUNCIL_ASSASSINATION_DECISION
    adapter._sync_outer(room, domain)

    adapter.act(
        room,
        room.players[0],
        "exile_council_assassination_decision",
        {"assassinate": False},
    )
    adapter.act(
        room,
        room.players[1],
        "council_assassination_decision",
        {"assassinate": False},
    )

    assert domain.exile_council_assassination_decisions == {
        room.players[0].id: False,
        room.players[1].id: False,
    }


def finish_ten_player_shadow_scenario(
    adapter: AvalonEngine,
    room,
    scenario: str,
) -> None:
    domain = room.state
    rules = adapter.rules
    shadow = next(
        player for player in domain.players if player.role == Role.SHADOW_MERLIN
    )
    merlin = next(
        player for player in domain.players if player.role == Role.MERLIN
    )
    percival = next(
        player for player in domain.players if player.role == Role.PERCIVAL
    )
    assassin = next(
        player for player in domain.players if player.role == Role.ASSASSIN
    )
    dissenting = next(
        player
        for player in domain.players
        if player.role == Role.DISSENTING_COURTIER
    )

    if scenario == "missions":
        domain.mission_index = 2
        domain.mission_history = [
            MissionRecord(number, [], False, 1)
            for number in range(1, 4)
        ]
        domain.phase = Phase.ROUND_RESULT
        rules.continue_after_mission(domain, domain.host_id)
        return

    if scenario in {"correct_exile", "wrong_exile", "tied_exile"}:
        valid_voters = [
            player
            for player in domain.players
            if player.role
            in {
                Role.MERLIN,
                Role.PERCIVAL,
                Role.LOYAL_SERVANT,
                Role.DISSENTING_COURTIER,
            }
        ]
        if scenario == "correct_exile":
            targets = [shadow.id] * len(valid_voters)
        elif scenario == "wrong_exile":
            targets = [merlin.id] * len(valid_voters)
        else:
            targets = [
                shadow.id,
                shadow.id,
                merlin.id,
                merlin.id,
                percival.id,
            ]
        domain.exile_council_target_votes = {
            player.id: target
            for player, target in zip(valid_voters, targets, strict=True)
        }
        domain.phase = Phase.EXILE_COUNCIL_ASSASSINATION_DECISION
        for player in domain.players:
            rules.submit_exile_council_assassination_decision(
                domain, player.id, False
            )
        return

    if scenario in {"assassin_hit", "assassin_miss"}:
        domain.phase = Phase.EXILE_COUNCIL_ASSASSINATION_DECISION
        for player in domain.players:
            rules.submit_exile_council_assassination_decision(
                domain,
                player.id,
                player.id == assassin.id,
            )
        assassin_target = merlin if scenario == "assassin_hit" else percival
        for player in domain.players:
            target = (
                assassin_target
                if player.id == assassin.id
                else next(
                    candidate
                    for candidate in domain.players
                    if candidate.id != player.id
                )
            )
            rules.submit_exile_council_assassination_target(
                domain, player.id, target.id
            )
        return

    domain.mission_index = 2
    domain.mission_history = [
        MissionRecord(number, [], True, 0)
        for number in range(1, 4)
    ]
    domain.phase = Phase.ROUND_RESULT
    rules.continue_after_mission(domain, domain.host_id)
    if scenario == "dagger_miss":
        wrong_target_id = next(
            target_id
            for target_id in domain.dagger_candidate_ids
            if target_id != dissenting.id
        )
        rules.grant_dagger(domain, assassin.id, wrong_target_id)
        return

    rules.grant_dagger(domain, assassin.id, dissenting.id)
    dissenting_target = (
        merlin
        if scenario == "dissenting_hit"
        else next(
            domain.player(target_id)
            for target_id in rules.eligible_dissenting_targets(domain)
            if domain.player(target_id).role != Role.MERLIN
        )
    )
    rules.dissenting_assassinate(
        domain, dissenting.id, dissenting_target.id
    )


@pytest.mark.parametrize(
    ("scenario", "winning_roles", "shadow_alignment", "dissenting_alignment"),
    [
        (
            "missions",
            [
                Role.ASSASSIN,
                Role.MORGANA,
                Role.MORDRED,
                Role.OBERON,
                Role.SHADOW_MERLIN,
            ],
            Alignment.EVIL,
            Alignment.GOOD,
        ),
        (
            "wrong_exile",
            [
                Role.ASSASSIN,
                Role.MORGANA,
                Role.MORDRED,
                Role.OBERON,
                Role.SHADOW_MERLIN,
            ],
            Alignment.EVIL,
            Alignment.GOOD,
        ),
        (
            "tied_exile",
            [
                Role.ASSASSIN,
                Role.MORGANA,
                Role.MORDRED,
                Role.OBERON,
                Role.SHADOW_MERLIN,
            ],
            Alignment.EVIL,
            Alignment.GOOD,
        ),
        (
            "correct_exile",
            [
                Role.MERLIN,
                Role.PERCIVAL,
                Role.LOYAL_SERVANT,
                Role.LOYAL_SERVANT,
                Role.DISSENTING_COURTIER,
            ],
            Alignment.EVIL,
            Alignment.GOOD,
        ),
        (
            "dagger_miss",
            [
                Role.MERLIN,
                Role.PERCIVAL,
                Role.LOYAL_SERVANT,
                Role.LOYAL_SERVANT,
                Role.DISSENTING_COURTIER,
            ],
            Alignment.EVIL,
            Alignment.GOOD,
        ),
        (
            "assassin_hit",
            [Role.ASSASSIN, Role.MORGANA, Role.MORDRED, Role.OBERON],
            Alignment.GOOD,
            Alignment.GOOD,
        ),
        (
            "assassin_miss",
            [
                Role.MERLIN,
                Role.PERCIVAL,
                Role.LOYAL_SERVANT,
                Role.LOYAL_SERVANT,
                Role.DISSENTING_COURTIER,
                Role.SHADOW_MERLIN,
            ],
            Alignment.GOOD,
            Alignment.GOOD,
        ),
        (
            "dissenting_hit",
            [
                Role.ASSASSIN,
                Role.MORGANA,
                Role.MORDRED,
                Role.OBERON,
                Role.DISSENTING_COURTIER,
            ],
            Alignment.GOOD,
            Alignment.EVIL,
        ),
        (
            "dissenting_miss",
            [
                Role.MERLIN,
                Role.PERCIVAL,
                Role.LOYAL_SERVANT,
                Role.LOYAL_SERVANT,
                Role.SHADOW_MERLIN,
            ],
            Alignment.GOOD,
            Alignment.EVIL,
        ),
    ],
)
def test_ten_player_shadow_role_outcomes_match_the_rule_table(
    scenario: str,
    winning_roles: list[Role],
    shadow_alignment: Alignment,
    dissenting_alignment: Alignment,
) -> None:
    manager, adapter, room, host = unified_avalon(10)
    manager.update_options(
        room,
        host.id,
        {
            "mode": "court_undercurrent",
            "shadowMerlinEnabled": True,
        },
    )
    manager.start(room, host.id)

    finish_ten_player_shadow_scenario(adapter, room, scenario)
    adapter._sync_outer(room, room.state)

    results = {
        player.id: adapter.player_result(room, player)
        for player in room.players
    }
    actual_winning_roles = Counter(
        Role(role)
        for role, _, won in results.values()
        if won
    )
    assert actual_winning_roles == Counter(winning_roles)
    assert set(room.winner_player_ids) == {
        player_id
        for player_id, (_, _, won) in results.items()
        if won
    }
    role_alignments = {
        Role(role): Alignment(alignment)
        for role, alignment, _ in results.values()
        if Role(role) in {Role.SHADOW_MERLIN, Role.DISSENTING_COURTIER}
    }
    assert role_alignments[Role.SHADOW_MERLIN] == shadow_alignment
    assert role_alignments[Role.DISSENTING_COURTIER] == dissenting_alignment


def test_avalon_ai_and_finished_room_lifecycle_remain_unchanged() -> None:
    engine = AvalonEngine(AvalonRulesEngine(random.Random(42)))
    manager = ArcadeRoomManager({"avalon": engine})
    room, host, _ = manager.create_room(
        "avalon", "房主", "account-host"
    )
    for _ in range(4):
        manager.act(room, host.id, "add_ai", {})
    assert len(room.players) == 5
    assert sum(player.is_bot for player in room.players) == 4

    manager.start(room, host.id)
    domain = room.state
    assert domain.phase == Phase.ROLE_REVEAL
    assert len(domain.role_confirmed_ids) == 4

    domain.winner = Alignment.GOOD
    domain.win_reason = "测试终局"
    domain.phase = Phase.GAME_OVER
    engine._sync_outer(room, domain)
    manager.leave(room, host.id)
    assert room.code not in manager.rooms
