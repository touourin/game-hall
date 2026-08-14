from __future__ import annotations

from backend.app.games.definition import (
    GameCatalogMetadata,
    GameDefinition,
    social_table_capabilities,
)

from .engine import PokerEngine


POKER_GAME = GameDefinition(
    key="poker",
    engine_factory=PokerEngine,
    catalog=GameCatalogMetadata(
        order=70,
        name="德州扑克",
        min_players=2,
        max_players=8,
        description="大小盲、四轮下注与全押边池",
    ),
    capabilities=social_table_capabilities(first_player=False),
)
