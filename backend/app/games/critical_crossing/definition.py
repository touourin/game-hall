from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameRegistration,
    GameRecords,
)

from .engine import CriticalCrossingEngine, DEFAULT_DIFFICULTY, DIFFICULTIES


def critical_crossing_match_mode(details: Mapping[str, Any]) -> str:
    state = details.get("state")
    if isinstance(state, dict):
        difficulty = state.get("difficulty")
        if isinstance(difficulty, str) and difficulty in DIFFICULTIES:
            return difficulty
    return DEFAULT_DIFFICULTY


CRITICAL_CROSSING_GAME = GameRegistration(
    key="critical_crossing",
    engine_factory=CriticalCrossingEngine,
    catalog=GameCatalogMetadata(
        order=130,
        name="临界穿越",
        min_players=1,
        max_players=1,
        description="识别脉冲缺口，穿越不断收紧的临界场",
    ),
    capabilities=GameCapabilities(
        guests=False,
        spectators=True,
        spectator_frames=True,
        first_player=False,
    ),
    records=GameRecords(
        score_kind="outcome",
        match_mode=critical_crossing_match_mode,
        query_modes=frozenset(DIFFICULTIES),
    ),
)
