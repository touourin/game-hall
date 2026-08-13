from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameDefinition,
)

from .engine import DeepShaftEngine


DEEP_SHAFT_GAME = GameDefinition(
    key="deep_shaft",
    engine_factory=DeepShaftEngine,
    catalog=GameCatalogMetadata(
        order=110,
        name="百层深井",
        min_players=1,
        max_players=1,
        description="左右控制落点，在危险平台间深入一百层",
    ),
    capabilities=GameCapabilities(
        guests=False,
        spectators=False,
        first_player=False,
    ),
)
