from __future__ import annotations

from backend.app.games.definition import (
    GameCatalogMetadata,
    GameRegistration,
    social_table_capabilities,
)

from .engine import DepartedSuspicionEngine


DEPARTED_SUSPICION_GAME = GameRegistration(
    key="departed_suspicion",
    engine_factory=DepartedSuspicionEngine,
    catalog=GameCatalogMetadata(
        order=10,
        name="无间疑云",
        min_players=4,
        max_players=8,
        description="调查底细、装备应变并找出敌方领袖",
    ),
    capabilities=social_table_capabilities(),
)
