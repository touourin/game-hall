from backend.app.games.avalon.bots import advance_ai_players
from backend.app.games.avalon.models import (
    Alignment,
    AvalonMode,
    MissionRecord,
    Phase,
    Role,
)

from .test_engine import start_room


def test_ai_players_confirm_roles_propose_a_team_and_vote():
    engine, room = start_room(5)
    for player in room.players[1:]:
        player.is_bot = True
    room.leader_index = 1

    advance_ai_players(room, engine)

    assert room.phase == Phase.ROLE_REVEAL
    assert room.role_confirmed_ids == {
        player.id for player in room.players[1:]
    }

    engine.confirm_role(room, room.host_id)
    advance_ai_players(room, engine)

    assert room.phase == Phase.TEAM_VOTING
    assert len(room.selected_team_ids) == 2
    assert set(room.team_votes) == {
        player.id for player in room.players[1:]
    }
    assert room.host_id not in room.team_votes


def test_ai_mission_vote_respects_good_alignment():
    engine, room = start_room(5)
    good_ai = next(
        player
        for player in room.players[1:]
        if player.alignment == Alignment.GOOD
    )
    good_ai.is_bot = True
    room.phase = Phase.MISSION_VOTING
    room.selected_team_ids = [room.host_id, good_ai.id]

    advance_ai_players(room, engine)

    assert room.phase == Phase.MISSION_VOTING
    assert room.mission_votes == {good_ai.id: True}


def test_ai_lady_holder_inspects_and_acknowledges_automatically():
    engine, room = start_room(7)
    room.leader_index = 0
    inspector = room.players[2]
    inspector.is_bot = True
    room.lady_holder_id = inspector.id
    room.mission_index = 1
    room.mission_history = [
        MissionRecord(1, ["p0", "p1"], True, 0),
        MissionRecord(2, ["p0", "p1", "p2"], True, 0),
    ]
    room.phase = Phase.LADY_SELECT

    advance_ai_players(room, engine)

    assert len(room.lady_checks) == 1
    assert room.lady_checks[0].inspector_id == inspector.id
    assert room.lady_pending_inspector_id is None
    assert room.phase == Phase.TEAM_BUILDING
    assert room.mission_index == 2


def test_ai_assassin_resolves_final_assassination_but_not_early():
    engine, room = start_room(5)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    assassin.is_bot = True
    room.phase = Phase.ASSASSINATION

    advance_ai_players(room, engine)

    assert room.phase == Phase.GAME_OVER
    assert room.assassin_target_id in engine.eligible_assassination_targets(
        room
    )
    assert room.player(room.assassin_target_id).role not in {
        Role.ASSASSIN,
        Role.MORGANA,
        Role.MORDRED,
        Role.MINION,
    }
    assert room.assassination_was_early is False


def test_ai_randomly_resolves_dagger_grant_and_courtier_stab():
    engine, room = start_room(7, mode=AvalonMode.COURT_UNDERCURRENT)
    assassin = next(
        player for player in room.players if player.role == Role.ASSASSIN
    )
    dissenting = next(
        player
        for player in room.players
        if player.role == Role.DISSENTING_COURTIER
    )
    decoy = next(
        player
        for player in room.players
        if player.alignment == Alignment.GOOD and player.id != dissenting.id
    )
    assassin.is_bot = True
    dissenting.is_bot = True
    room.dagger_candidate_ids = [dissenting.id, decoy.id]
    room.phase = Phase.DAGGER_GRANT

    advance_ai_players(room, engine)

    assert room.phase == Phase.GAME_OVER
    assert room.dagger_target_id in room.dagger_candidate_ids
    if room.dagger_hit:
        assert room.dissenting_assassination_target_id is not None
