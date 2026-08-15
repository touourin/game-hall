from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameDefinition,
    GameRecords,
)

from .engine import ReactionEngine


REACTION_GAME = GameDefinition(
    key="reaction",
    engine_factory=ReactionEngine,
    catalog=GameCatalogMetadata(
        order=100,
        name="反应挑战",
        min_players=1,
        max_players=1,
        description="三轮高精度反应测试",
    ),
    capabilities=GameCapabilities(
        guests=False,
        spectators=True,
        first_player=False,
    ),
    records=GameRecords(score_kind="time_trial"),
)
