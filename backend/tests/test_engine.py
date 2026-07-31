from __future__ import annotations

import random

import pytest

from backend.app.games.avalon.engine import GameEngine, GameRuleError
from backend.app.games.avalon.models import (
    Alignment,
    GameSettings,
    MissionRecord,
    Phase,
    Player,
    Role,
    Room,
)


def make_room(player_count: int, lady_enabled: bool = True) -> Room:
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
        settings=GameSettings(lady_enabled=lady_enabled),
    )


def start_room(player_count: int = 5, lady_enabled: bool = True):
    room = make_room(player_count, lady_enabled)
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


def test_five_rejected_teams_give_evil_the_win():
    engine, room = start_room()
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

    assert room.phase == Phase.GAME_OVER
    assert room.winner == Alignment.EVIL
    assert "五次" in room.win_reason
    assert len(room.proposal_history) == 5
    assert all(not record.accepted for record in room.proposal_history)


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


def test_final_assassination_rejects_evil_target():
    engine, room = start_room(7)
    assassin = next(player for player in room.players if player.role == Role.ASSASSIN)
    evil_target = next(
        player
        for player in room.players
        if player.alignment == Alignment.EVIL and player.id != assassin.id
    )
    room.phase = Phase.ASSASSINATION

    with pytest.raises(GameRuleError, match="只能选择好人阵营"):
        engine.assassinate(room, assassin.id, evil_target.id)


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
        player
        for player in room.players
        if player.id != assassin.id and player.role != Role.MERLIN
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
