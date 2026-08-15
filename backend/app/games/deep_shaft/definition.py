from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameRegistration,
    GameRecords,
)

from .engine import DeepShaftEngine


DEEP_SHAFT_GAME = GameRegistration(
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
        spectators=True,
        spectator_frames=True,
        first_player=False,
    ),
    records=GameRecords(score_kind="high_score"),
)
