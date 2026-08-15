from __future__ import annotations

from backend.app.games.definition import (
    GameCatalogMetadata,
    GameRegistration,
    social_table_capabilities,
)

from .engine import MonopolyEngine


MONOPOLY_GAME = GameRegistration(
    key="monopoly",
    engine_factory=MonopolyEngine,
    catalog=GameCatalogMetadata(
        order=170,
        name="大富翁",
        min_players=2,
        max_players=4,
        description="掷骰环游城市，买地升级并收取租金",
    ),
    capabilities=social_table_capabilities(),
)
