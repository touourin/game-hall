from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameRegistration,
    GameRecords,
)

from .engine import ReactionEngine


REACTION_GAME = GameRegistration(
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
        spectator_frames=True,
        first_player=False,
    ),
    records=GameRecords(score_kind="time_trial"),
)
