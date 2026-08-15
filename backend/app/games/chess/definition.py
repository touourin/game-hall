from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameRegistration,
)

from .engine import ChessEngine


CHESS_GAME = GameRegistration(
    key="chess",
    engine_factory=ChessEngine,
    catalog=GameCatalogMetadata(
        order=50,
        name="国际象棋",
        min_players=2,
        max_players=2,
        description="标准规则、升变与完整和棋判定",
    ),
    capabilities=GameCapabilities(
        undo_actions=frozenset({"move"}),
        draw_requests=True,
        guests=True,
        spectators=True,
        first_player=True,
        replay=True,
        ai=False,
    ),
)
