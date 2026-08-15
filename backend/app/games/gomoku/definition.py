from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameRegistration,
)

from .engine import GomokuEngine


GOMOKU_GAME = GameRegistration(
    key="gomoku",
    engine_factory=GomokuEngine,
    catalog=GameCatalogMetadata(
        order=30,
        name="五子棋",
        min_players=2,
        max_players=2,
        description="15 路棋盘，Swap2 与有禁手连珠",
    ),
    capabilities=GameCapabilities(
        undo_actions=frozenset({"place", "pass"}),
        draw_requests=True,
        guests=True,
        spectators=True,
        first_player=True,
        replay=False,
        ai=False,
    ),
)
