from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameDefinition,
)

from .engine import DoudizhuEngine


DOUDIZHU_GAME = GameDefinition(
    key="doudizhu",
    engine_factory=DoudizhuEngine,
    catalog=GameCatalogMetadata(
        order=80,
        name="斗地主",
        min_players=3,
        max_players=3,
        description="叫抢地主、三种玩法与倍数结算",
    ),
    capabilities=GameCapabilities(
        guests=True,
        spectators=True,
        first_player=True,
    ),
)
