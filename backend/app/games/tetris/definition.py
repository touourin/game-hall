from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameDefinition,
)

from .engine import TetrisEngine


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
)
