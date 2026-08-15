from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameRegistration,
)

from .engine import GoEngine


GO_GAME = GameRegistration(
    key="go",
    engine_factory=GoEngine,
    catalog=GameCatalogMetadata(
        order=60,
        name="围棋",
        min_players=2,
        max_players=2,
        description="9/13/19 路中国规则，贴目与让子可选",
    ),
    capabilities=GameCapabilities(
        undo_actions=frozenset({"place", "pass"}),
        draw_requests=True,
        guests=True,
        spectators=True,
        first_player=True,
        replay=False,
        ai=True,
    ),
)
