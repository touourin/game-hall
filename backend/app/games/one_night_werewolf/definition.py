from __future__ import annotations

from backend.app.games.definition import (
    GameCatalogMetadata,
    GameDefinition,
    social_table_capabilities,
)

from .engine import OneNightWerewolfEngine


ONE_NIGHT_WEREWOLF_GAME = GameDefinition(
    key="one_night_werewolf",
    engine_factory=OneNightWerewolfEngine,
    catalog=GameCatalogMetadata(
        order=20,
        name="一夜狼人",
        min_players=3,
        max_players=10,
        description="一晚行动、晨间推理与一次终局投票",
    ),
    capabilities=social_table_capabilities(
        first_player=False,
    ),
)
