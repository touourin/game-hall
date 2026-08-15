from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameRegistration,
)

from .engine import XiangqiEngine


XIANGQI_GAME = GameRegistration(
    key="xiangqi",
    engine_factory=XiangqiEngine,
    catalog=GameCatalogMetadata(
        order=40,
        name="中国象棋",
        min_players=2,
        max_players=2,
        description="完整走子、让子与重复局面限制",
    ),
    capabilities=GameCapabilities(
        undo_actions=frozenset({"move"}),
        draw_requests=True,
        guests=True,
        spectators=True,
        first_player=True,
        replay=True,
        ai=True,
    ),
)
