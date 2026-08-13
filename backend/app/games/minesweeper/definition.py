from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameDefinition,
)

from .engine import MinesweeperEngine


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
)
