from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameDefinition,
)

from .arcade import AvalonEngine


AVALON_GAME = GameDefinition(
    key="avalon",
    engine_factory=AvalonEngine,
    catalog=GameCatalogMetadata(
        order=0,
        name="阿瓦隆",
        min_players=5,
        max_players=10,
        description="身份推理与团队博弈",
    ),
    capabilities=GameCapabilities(
        guests=True,
        spectators=True,
        first_player=False,
        replay=True,
        ai=True,
    ),
)
