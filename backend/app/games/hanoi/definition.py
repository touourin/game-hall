from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameDefinition,
)

from .engine import HanoiEngine


HANOI_GAME = GameDefinition(
    key="hanoi",
    engine_factory=HanoiEngine,
    catalog=GameCatalogMetadata(
        order=150,
        name="汉诺塔",
        min_players=1,
        max_players=1,
        description="3–8 层经典益智挑战，争取最少步数",
    ),
    capabilities=GameCapabilities(
        guests=False,
        spectators=True,
        first_player=False,
    ),
)
