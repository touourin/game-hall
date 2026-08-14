from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameDefinition,
    GameRecords,
)

from .engine import MinesweeperEngine


def minesweeper_match_mode(details: Mapping[str, Any]) -> str:
    state = details.get("state")
    if isinstance(state, dict):
        difficulty = state.get("difficulty")
        if isinstance(difficulty, str) and difficulty:
            return difficulty
    return "standard"


MINESWEEPER_GAME = GameDefinition(
    key="minesweeper",
    engine_factory=MinesweeperEngine,
    catalog=GameCatalogMetadata(
        order=140,
        name="扫雷",
        min_players=1,
        max_players=1,
        description="三种经典难度，首次点击安全",
    ),
    capabilities=GameCapabilities(
        guests=False,
        spectators=True,
        first_player=False,
    ),
    records=GameRecords(
        score_kind="time_trial",
        match_mode=minesweeper_match_mode,
    ),
)
