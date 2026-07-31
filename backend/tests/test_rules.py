from backend.app.games.avalon.models import Role
from backend.app.games.avalon.rules import (
    GOOD_EVIL_COUNTS,
    MISSION_TEAM_SIZES,
    mission_fail_threshold,
    roles_for_player_count,
)


def test_role_presets_match_required_alignment_counts():
    good_roles = {Role.MERLIN, Role.PERCIVAL, Role.LOYAL_SERVANT}
    for player_count, (good_count, evil_count) in GOOD_EVIL_COUNTS.items():
        roles = roles_for_player_count(player_count)
        assert len(roles) == player_count
        assert sum(role in good_roles for role in roles) == good_count
        assert sum(role not in good_roles for role in roles) == evil_count
        assert roles.count(Role.MERLIN) == 1
        assert roles.count(Role.ASSASSIN) == 1


def test_mission_team_size_table_matches_standard_game():
    assert MISSION_TEAM_SIZES[5] == (2, 3, 2, 3, 3)
    assert MISSION_TEAM_SIZES[7] == (2, 3, 3, 4, 4)
    assert MISSION_TEAM_SIZES[10] == (3, 4, 4, 5, 5)


def test_fourth_mission_needs_two_fails_for_seven_or_more_players():
    assert mission_fail_threshold(6, 3) == 1
    assert mission_fail_threshold(7, 3) == 2
    assert mission_fail_threshold(10, 3) == 2
    assert mission_fail_threshold(10, 2) == 1
