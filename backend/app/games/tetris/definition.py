from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameDefinition,
    GameRecords,
)

from .engine import TetrisEngine


def tetris_match_mode(details: Mapping[str, Any]) -> str:
    options = details.get("options")
    if isinstance(options, dict) and options.get("challengeMode") == "timed":
        duration = options.get("durationSeconds")
        if duration in {60, 180, 300}:
            return f"timed_{duration}"
    return "standard"


TETRIS_GAME = GameDefinition(
    key="tetris",
    engine_factory=TetrisEngine,
    catalog=GameCatalogMetadata(
        order=160,
        name="落块挑战",
        min_players=1,
        max_players=1,
        description="排列七种方块，连续消行挑战高分",
    ),
    capabilities=GameCapabilities(
        guests=False,
        spectators=False,
        first_player=False,
    ),
    records=GameRecords(
        score_kind="high_score",
        match_mode=tetris_match_mode,
        query_modes=frozenset(
            {"standard", "timed_60", "timed_180", "timed_300"}
        ),
    ),
)
