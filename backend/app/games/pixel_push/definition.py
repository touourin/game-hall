from __future__ import annotations

from backend.app.games.definition import (
    GameCatalogMetadata,
    GameDefinition,
    social_table_capabilities,
)

from .engine import PixelPushEngine


PIXEL_PUSH_GAME = GameDefinition(
    key="pixel_push",
    engine_factory=PixelPushEngine,
    catalog=GameCatalogMetadata(
        order=95,
        name="像素推推王",
        min_players=2,
        max_players=4,
        description="冲刺、稳住与失衡击退的像素擂台乱斗",
    ),
    capabilities=social_table_capabilities(first_player=False),
)
