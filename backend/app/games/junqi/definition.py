from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameRegistration,
)

from .engine import JunqiEngine


JUNQI_GAME = GameRegistration(
    key="junqi",
    engine_factory=JunqiEngine,
    catalog=GameCatalogMetadata(
        order=90,
        name="军旗",
        min_players=2,
        max_players=2,
        description="暗军旗秘密布阵与翻棋对战",
    ),
    capabilities=GameCapabilities(
        guests=True,
        spectators=True,
        first_player=True,
        replay=False,
        ai=False,
    ),
)
