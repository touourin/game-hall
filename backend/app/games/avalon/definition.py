from __future__ import annotations

from backend.app.games.definition import (
    GameCatalogMetadata,
    GameDefinition,
    GameRecords,
    social_table_capabilities,
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
    capabilities=social_table_capabilities(
        first_player=False,
        replay=True,
        ai=True,
    ),
    records=GameRecords(
        query_modes=frozenset({"standard", "court_undercurrent"}),
        query_variants={
            "court_undercurrent": frozenset({"classic", "shadow_merlin"}),
        },
        invalid_variant_message="王庭暗流统计分组不正确",
    ),
)
