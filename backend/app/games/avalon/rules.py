from __future__ import annotations

from .models import AvalonMode, Role


GOOD_EVIL_COUNTS: dict[int, tuple[int, int]] = {
    5: (3, 2),
    6: (4, 2),
    7: (4, 3),
    8: (5, 3),
    9: (6, 3),
    10: (6, 4),
}

MISSION_TEAM_SIZES: dict[int, tuple[int, int, int, int, int]] = {
    5: (2, 3, 2, 3, 3),
    6: (2, 3, 4, 3, 4),
    7: (2, 3, 3, 4, 4),
    8: (3, 4, 4, 5, 5),
    9: (3, 4, 4, 5, 5),
    10: (3, 4, 4, 5, 5),
}


def mission_team_size(player_count: int, mission_index: int) -> int:
    return MISSION_TEAM_SIZES[player_count][mission_index]


def mission_fail_threshold(player_count: int, mission_index: int) -> int:
    if player_count >= 7 and mission_index == 3:
        return 2
    return 1


def roles_for_player_count(
    player_count: int,
    mode: AvalonMode = AvalonMode.STANDARD,
) -> list[Role]:
    """Return a balanced, familiar role preset for 5–10 players."""
    good_count, evil_count = GOOD_EVIL_COUNTS[player_count]

    good_roles = [Role.MERLIN, Role.PERCIVAL]
    good_roles.extend([Role.LOYAL_SERVANT] * (good_count - len(good_roles)))
    if mode == AvalonMode.COURT_UNDERCURRENT:
        good_roles[good_roles.index(Role.LOYAL_SERVANT)] = (
            Role.DISSENTING_COURTIER
        )

    if player_count <= 6:
        evil_roles = [Role.ASSASSIN, Role.MORGANA]
    elif player_count == 7:
        evil_roles = [Role.ASSASSIN, Role.MORGANA, Role.OBERON]
    elif player_count == 8:
        evil_roles = [Role.ASSASSIN, Role.MORGANA, Role.MINION]
    elif player_count == 9:
        evil_roles = [Role.ASSASSIN, Role.MORGANA, Role.MORDRED]
    else:
        evil_roles = [Role.ASSASSIN, Role.MORGANA, Role.MORDRED, Role.OBERON]

    evil_roles.extend([Role.MINION] * (evil_count - len(evil_roles)))
    return good_roles + evil_roles
