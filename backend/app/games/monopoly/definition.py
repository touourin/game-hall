from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameDefinition,
)

from .engine import MonopolyEngine


MONOPOLY_GAME = GameDefinition(
    key="monopoly",
    engine_factory=MonopolyEngine,
    catalog=GameCatalogMetadata(
        order=170,
        name="大富翁",
        min_players=2,
        max_players=4,
        description="掷骰环游城市，买地升级并收取租金",
    ),
    capabilities=GameCapabilities(
        guests=True,
        spectators=True,
        first_player=True,
    ),
)
