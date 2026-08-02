from backend.app.games.avalon.models import AvalonMode, Role
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


def test_role_presets_match_the_standard_special_role_lineup():
    expected_evil_roles = {
        5: [Role.ASSASSIN, Role.MORGANA],
        6: [Role.ASSASSIN, Role.MORGANA],
        7: [Role.ASSASSIN, Role.MORGANA, Role.OBERON],
        8: [Role.ASSASSIN, Role.MORGANA, Role.MINION],
        9: [Role.ASSASSIN, Role.MORGANA, Role.MORDRED],
        10: [Role.ASSASSIN, Role.MORGANA, Role.MORDRED, Role.OBERON],
    }
    expected_loyal_servants = {5: 1, 6: 2, 7: 2, 8: 3, 9: 4, 10: 4}

    for player_count in range(5, 11):
        roles = roles_for_player_count(player_count)
        assert roles.count(Role.LOYAL_SERVANT) == expected_loyal_servants[player_count]
        assert roles[-len(expected_evil_roles[player_count]) :] == expected_evil_roles[
            player_count
        ]


def test_mission_team_size_table_matches_standard_game():
    assert MISSION_TEAM_SIZES[5] == (2, 3, 2, 3, 3)
    assert MISSION_TEAM_SIZES[7] == (2, 3, 3, 4, 4)
    assert MISSION_TEAM_SIZES[10] == (3, 4, 4, 5, 5)


def test_fourth_mission_needs_two_fails_for_seven_or_more_players():
    assert mission_fail_threshold(6, 3) == 1
    assert mission_fail_threshold(7, 3) == 2
    assert mission_fail_threshold(10, 3) == 2
    assert mission_fail_threshold(10, 2) == 1


def test_court_undercurrent_replaces_exactly_one_loyal_servant():
    for player_count in range(5, 11):
        standard = roles_for_player_count(player_count)
        variant = roles_for_player_count(
            player_count, AvalonMode.COURT_UNDERCURRENT
        )

        assert variant.count(Role.DISSENTING_COURTIER) == 1
        assert variant.count(Role.LOYAL_SERVANT) == (
            standard.count(Role.LOYAL_SERVANT) - 1
        )
        for role in Role:
            if role not in {
                Role.LOYAL_SERVANT,
                Role.DISSENTING_COURTIER,
            }:
                assert variant.count(role) == standard.count(role)
