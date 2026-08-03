from __future__ import annotations

import random

import pytest

from backend.app.games.avalon.engine import GameEngine, GameRuleError
from backend.app.games.avalon.models import (
    Alignment,
    AvalonMode,
    GameSettings,
    MissionRecord,
    Phase,
    Player,
    Role,
    Room,
)


def make_room(
    player_count: int,
    lady_enabled: bool = True,
    mode: AvalonMode = AvalonMode.STANDARD,
) -> Room:
    players = [
        Player(
            id=f"p{index}",
            name=f"玩家{index}",
            token_hash=f"token-{index}",
            seat=index,
        )
        for index in range(player_count)
    ]
    return Room(
        code="TEST",
        host_id=players[0].id,
        players=players,
        settings=GameSettings(mode=mode, lady_enabled=lady_enabled),
    )


def start_room(
    player_count: int = 5,
    lady_enabled: bool = True,
    mode: AvalonMode = AvalonMode.STANDARD,
):
    room = make_room(player_count, lady_enabled, mode)
    engine = GameEngine(random.Random(42))
    engine.start_game(room, room.host_id)
    return engine, room


def confirm_all_roles(engine: GameEngine, room: Room) -> None:
    for player in room.players:
        engine.confirm_role(room, player.id)


def test_game_starts_with_private_roles_and_random_leader():
    engine, room = start_room(7)
    assert room.phase == Phase.ROLE_REVEAL
    assert all(player.role is not None for player in room.players)
    assert room.lady_holder_id == room.players[(room.leader_index - 1) % 7].id

    confirm_all_roles(engine, room)
    assert room.phase == Phase.TEAM_BUILDING


def test_good_player_cannot_sabotage_mission():
    engine, room = start_room()
    good_player = next(
        player for player in room.players if player.alignment == Alignment.GOOD
    )
    room.phase = Phase.MISSION_VOTING
    room.selected_team_ids = [good_player.id, room.players[1].id]

    with pytest.raises(GameRuleError, match="好人阵营只能支持任务成功"):
        engine.vote_mission(room, good_player.id, success=False)


@pytest.mark.parametrize(
    "mode",
    [AvalonMode.STANDARD, AvalonMode.COURT_UNDERCURRENT],
)
def test_five_rejected_teams_fail_only_the_current_mission(mode):
    engine, room = start_room(mode=mode)
    confirm_all_roles(engine, room)

    for _ in range(5):
        required = 2
        engine.propose_team(
            room,
            room.leader.id,
            [player.id for player in room.players[:required]],
        )
        for player in room.players:
            engine.vote_team(room, player.id, approve=False)

    assert room.phase == Phase.ROUND_RESULT
    assert room.winner is None
    assert room.fail_count == 1
    assert room.mission_history == [
        MissionRecord(
            number=1,
            team_ids=[],
            success=False,
            fail_count=0,
            failed_by_rejections=True,
        )
    ]
    assert len(room.proposal_history) == 5
    assert all(not record.accepted for record in room.proposal_history)

    engine.continue_after_mission(room, room.host_id)

    assert room.phase == Phase.TEAM_BUILDING
    assert room.mission_index == 1
    assert room.proposal_attempt == 1


def test_fifth_rejection_on_third_failed_mission_gives_evil_the_win():
    engine, room = start_room()
    confirm_all_roles(engine, room)
    room.mission_history = [
        MissionRecord(1, ["p0", "p1"], False, 1),
        MissionRecord(2, ["p0", "p1", "p2"], False, 1),
    ]
    room.mission_index = 2

    for _ in range(5):
        required = 2
        engine.propose_team(
            room,
            room.leader.id,
            [player.id for player in room.players[:required]],
        )
        for player in room.players:
            engine.vote_team(room, player.id, approve=False)

    assert room.phase == Phase.ROUND_RESULT
    assert room.fail_count == 3
    assert room.winner is None

    engine.continue_after_mission(room, room.host_id)

    assert room.phase == Phase.GAME_OVER
    assert room.winner == Alignment.EVIL
    assert room.ending_route == "missions"


def test_completed_team_vote_is_recorded_for_replay():
    engine, room = start_room()
    confirm_all_roles(engine, room)
    leader_id = room.leader.id
    team_ids = [player.id for player in room.players[:2]]

    engine.propose_team(room, leader_id, team_ids)
    votes = {
        room.players[0].id: True,
        room.players[1].id: False,
        room.players[2].id: True,
        room.players[3].id: False,
        room.players[4].id: True,
    }
    for player_id, approve in votes.items():
        engine.vote_team(room, player_id, approve)

    record = room.proposal_history[-1]
    assert record.mission_number == 1
    assert record.attempt == 1
    assert record.leader_id == leader_id
    assert record.team_ids == team_ids
    assert record.votes == votes
    assert record.accepted is True
    assert room.phase == Phase.MISSION_VOTING


def test_fourth_mission_with_one_fail_still_succeeds_for_seven_players():
    engine, room = start_room(7)
    room.mission_index = 3
    room.phase = Phase.MISSION_VOTING

    evil = next(
        player for player in room.players if player.alignment == Alignment.EVIL
    )
    good_players = [
        player for player in room.players if player.alignment == Alignment.GOOD
    ][:3]
    team = [evil, *good_players]
    room.selected_team_ids = [player.id for player in team]

    engine.vote_mission(room, evil.id, success=False)
    for player in good_players:
        engine.vote_mission(room, player.id, success=True)

    assert room.mission_history[-1].success is True
    assert room.mission_history[-1].fail_count == 1


def test_lady_of_lake_is_private_and_moves_to_examined_player():
    engine, room = start_room(7)
    room.mission_index = 1
    room.mission_history = [
        MissionRecord(1, ["p0", "p1"], True, 0),
        MissionRecord(2, ["p0", "p1", "p2"], False, 1),
    ]
    room.phase = Phase.ROUND_RESULT

    engine.continue_after_mission(room, room.host_id)
    assert room.phase == Phase.LADY_SELECT

    inspector_id = room.lady_holder_id
    target_id = next(
        player_id
        for player_id in engine.eligible_lady_targets(room)
        if player_id != inspector_id
    )
    target_alignment = room.player(target_id).alignment

    engine.inspect_with_lady(room, inspector_id, target_id)
    assert room.phase == Phase.LADY_REVEAL
    assert room.lady_checks[-1].alignment == target_alignment
    assert room.lady_holder_id == target_id
    assert inspector_id in room.lady_used_by_ids

    engine.acknowledge_lady(room, inspector_id)
    assert room.phase == Phase.TEAM_BUILDING
    assert room.mission_index == 2


def test_assassin_only_wins_when_target_is_merlin():
    engine, room = start_room()
    assassin = next(player for player in room.players if player.role == Role.ASSASSIN)
    merlin = next(player for player in room.players if player.role == Role.MERLIN)
    room.phase = Phase.ASSASSINATION

    engine.assassinate(room, assassin.id, merlin.id)

    assert room.phase == Phase.GAME_OVER
    assert room.winner == Alignment.EVIL
    assert room.assassin_target_id == merlin.id
    assert room.assassination_was_early is False


def test_final_assassination_can_miss_by_targeting_hidden_oberon():
    engine, room = start_room(7)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    oberon = next(
        player for player in room.players if player.role == Role.OBERON
    )
    room.phase = Phase.ASSASSINATION

    assert oberon.id in engine.eligible_assassination_targets(room)
    engine.assassinate(room, assassin.id, oberon.id)

    assert room.phase == Phase.GAME_OVER
    assert room.winner == Alignment.GOOD
    assert room.assassin_target_id == oberon.id
    assert room.assassination_was_early is False


@pytest.mark.parametrize(
    ("player_count", "known_evil_role"),
    [
        (5, Role.MORGANA),
        (8, Role.MINION),
        (9, Role.MORDRED),
    ],
)
def test_assassin_cannot_target_a_known_evil_teammate(
    player_count: int, known_evil_role: Role
):
    engine, room = start_room(player_count)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    teammate = next(
        player for player in room.players if player.role == known_evil_role
    )
    room.phase = Phase.ASSASSINATION

    assert teammate.id not in engine.eligible_assassination_targets(room)
    with pytest.raises(GameRuleError, match="已知的邪恶同伴"):
        engine.assassinate(room, assassin.id, teammate.id)

    assert room.phase == Phase.ASSASSINATION
    assert room.assassin_target_id is None


def test_assassin_can_win_with_enabled_early_assassination():
    engine, room = start_room()
    confirm_all_roles(engine, room)
    room.settings.early_assassination_enabled = True
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    merlin = next(player for player in room.players if player.role == Role.MERLIN)

    engine.early_assassinate(room, assassin.id, merlin.id)

    assert room.phase == Phase.GAME_OVER
    assert room.winner == Alignment.EVIL
    assert room.assassin_target_id == merlin.id
    assert room.assassination_was_early is True
    assert "提前刺杀" in room.win_reason


def test_wrong_early_assassination_immediately_gives_good_the_win():
    engine, room = start_room()
    confirm_all_roles(engine, room)
    room.settings.early_assassination_enabled = True
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    non_merlin = next(
        room.player(player_id)
        for player_id in engine.eligible_assassination_targets(room)
        if room.player(player_id).role != Role.MERLIN
    )

    engine.early_assassinate(room, assassin.id, non_merlin.id)

    assert room.phase == Phase.GAME_OVER
    assert room.winner == Alignment.GOOD
    assert room.assassin_target_id == non_merlin.id
    assert room.assassination_was_early is True


def test_early_assassination_requires_enabled_house_rule():
    engine, room = start_room()
    confirm_all_roles(engine, room)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    target = next(player for player in room.players if player.id != assassin.id)

    with pytest.raises(GameRuleError, match="没有开启"):
        engine.early_assassinate(room, assassin.id, target.id)


def test_early_assassination_is_not_available_during_role_reveal():
    engine, room = start_room()
    room.settings.early_assassination_enabled = True
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    target = next(player for player in room.players if player.id != assassin.id)

    with pytest.raises(GameRuleError, match="当前阶段不能发动提前刺杀"):
        engine.early_assassinate(room, assassin.id, target.id)


def complete_three_successes(room: Room) -> None:
    room.mission_index = 2
    room.mission_history = [
        MissionRecord(1, ["p0", "p1"], True, 0),
        MissionRecord(2, ["p0", "p1", "p2"], True, 0),
        MissionRecord(3, ["p0", "p1"], True, 0),
    ]
    room.phase = Phase.ROUND_RESULT


@pytest.mark.parametrize(
    ("player_count", "candidate_count"),
    [(5, 2), (6, 2), (7, 2), (8, 2), (9, 2), (10, 3)],
)
def test_court_undercurrent_starts_dagger_grant_with_balanced_candidates(
    player_count: int, candidate_count: int
):
    engine, room = start_room(
        player_count,
        lady_enabled=True,
        mode=AvalonMode.COURT_UNDERCURRENT,
    )
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )
    complete_three_successes(room)

    engine.continue_after_mission(room, room.host_id)

    assert room.phase == Phase.DAGGER_GRANT
    assert len(room.dagger_candidate_ids) == candidate_count
    assert dissenting.id in room.dagger_candidate_ids
    assert all(
        room.player(player_id).role
        not in {Role.ASSASSIN, Role.MORGANA, Role.MORDRED, Role.MINION}
        for player_id in room.dagger_candidate_ids
    )
    assert room.settings.lady_enabled is False
    assert room.settings.early_assassination_enabled is False


@pytest.mark.parametrize(
    ("player_count", "grant_seed"),
    [(7, 5), (10, 4)],
)
def test_oberon_can_be_random_dagger_decoy_without_being_forced(
    player_count: int, grant_seed: int
):
    engine, room = start_room(
        player_count, mode=AvalonMode.COURT_UNDERCURRENT
    )
    engine.rng = random.Random(grant_seed)
    complete_three_successes(room)

    engine.continue_after_mission(room, room.host_id)

    candidate_roles = {
        room.player(player_id).role
        for player_id in room.dagger_candidate_ids
    }
    assert Role.DISSENTING_COURTIER in candidate_roles
    assert Role.OBERON in candidate_roles


@pytest.mark.parametrize("player_count", [7, 10])
def test_oberon_is_not_a_required_dagger_candidate(player_count: int):
    engine, room = start_room(
        player_count, mode=AvalonMode.COURT_UNDERCURRENT
    )
    engine.rng = random.Random(0)
    complete_three_successes(room)

    engine.continue_after_mission(room, room.host_id)

    candidate_roles = {
        room.player(player_id).role
        for player_id in room.dagger_candidate_ids
    }
    assert Role.DISSENTING_COURTIER in candidate_roles
    assert Role.OBERON not in candidate_roles


def test_selecting_oberon_is_a_generic_dagger_miss():
    engine, room = start_room(7, mode=AvalonMode.COURT_UNDERCURRENT)
    engine.rng = random.Random(5)
    complete_three_successes(room)
    engine.continue_after_mission(room, room.host_id)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    oberon = next(
        player for player in room.players if player.role == Role.OBERON
    )

    engine.grant_dagger(room, assassin.id, oberon.id)

    assert room.phase == Phase.GAME_OVER
    assert room.winner == Alignment.GOOD
    assert room.dagger_hit is False
    assert room.ending_route == "dagger_miss"
    assert "奥伯伦" not in (room.win_reason or "")


def test_wrong_dagger_target_gives_good_the_win_without_assassination():
    engine, room = start_room(mode=AvalonMode.COURT_UNDERCURRENT)
    complete_three_successes(room)
    engine.continue_after_mission(room, room.host_id)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    decoy_id = next(
        player_id
        for player_id in room.dagger_candidate_ids
        if room.player(player_id).role != Role.DISSENTING_COURTIER
    )

    engine.grant_dagger(room, assassin.id, decoy_id)

    assert room.phase == Phase.GAME_OVER
    assert room.winner == Alignment.GOOD
    assert room.dagger_hit is False
    assert room.ending_route == "dagger_miss"
    assert room.assassin_target_id is None


def test_correct_dagger_target_forces_transformation_and_transfers_stab():
    engine, room = start_room(7, mode=AvalonMode.COURT_UNDERCURRENT)
    complete_three_successes(room)
    engine.continue_after_mission(room, room.host_id)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )

    engine.grant_dagger(room, assassin.id, dissenting.id)

    assert room.phase == Phase.FINAL_COUNCIL
    assert room.dagger_hit is True
    assert room.transformed_player_id == dissenting.id
    assert dissenting.alignment == Alignment.EVIL
    assert assassin.id not in engine.eligible_dissenting_targets(room)
    oberon = next(
        player for player in room.players if player.role == Role.OBERON
    )
    assert oberon.id in engine.eligible_dissenting_targets(room)
    assert len(engine.eligible_dissenting_targets(room)) == 4


@pytest.mark.parametrize(
    ("player_count", "target_count"),
    [(5, 2), (6, 3), (7, 4), (8, 4), (9, 5), (10, 6)],
)
def test_dissenting_assassination_uses_the_natural_target_range(
    player_count: int, target_count: int
):
    engine, room = start_room(
        player_count, mode=AvalonMode.COURT_UNDERCURRENT
    )
    complete_three_successes(room)
    engine.continue_after_mission(room, room.host_id)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )

    engine.grant_dagger(room, assassin.id, dissenting.id)

    targets = [
        room.player(player_id)
        for player_id in engine.eligible_dissenting_targets(room)
    ]
    assert len(targets) == target_count
    assert dissenting not in targets
    assert all(
        player.role
        not in {Role.ASSASSIN, Role.MORGANA, Role.MORDRED, Role.MINION}
        for player in targets
    )
    if player_count in {7, 10}:
        assert any(player.role == Role.OBERON for player in targets)


def test_transformed_dissenting_courtier_wins_only_by_stabbing_merlin():
    engine, room = start_room(mode=AvalonMode.COURT_UNDERCURRENT)
    complete_three_successes(room)
    engine.continue_after_mission(room, room.host_id)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )
    merlin = next(player for player in room.players if player.role == Role.MERLIN)
    engine.grant_dagger(room, assassin.id, dissenting.id)

    engine.dissenting_assassinate(room, dissenting.id, merlin.id)

    assert room.phase == Phase.GAME_OVER
    assert room.winner == Alignment.EVIL
    assert room.dissenting_assassination_target_id == merlin.id
    assert room.ending_route == "dissenting_assassination"


def test_transformed_dissenting_courtier_loses_after_stabbing_wrong_target():
    engine, room = start_room(6, mode=AvalonMode.COURT_UNDERCURRENT)
    complete_three_successes(room)
    engine.continue_after_mission(room, room.host_id)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )
    engine.grant_dagger(room, assassin.id, dissenting.id)
    wrong_target = next(
        room.player(player_id)
        for player_id in engine.eligible_dissenting_targets(room)
        if room.player(player_id).role != Role.MERLIN
    )

    engine.dissenting_assassinate(room, dissenting.id, wrong_target.id)

    assert room.phase == Phase.GAME_OVER
    assert room.winner == Alignment.GOOD
    assert room.dissenting_assassination_target_id == wrong_target.id
    assert room.ending_route == "dissenting_assassination"
