from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameDefinition,
)

from .engine import SurviveThreeSecondsEngine


SURVIVE_THREE_SECONDS_GAME = GameDefinition(
    key="survive_three_seconds",
    engine_factory=SurviveThreeSecondsEngine,
    catalog=GameCatalogMetadata(
        order=130,
        name="坚持三秒",
        min_players=1,
        max_players=1,
        description="在铺天盖地的弹幕中躲避三秒",
    ),
    capabilities=GameCapabilities(
        guests=False,
        spectators=False,
        first_player=False,
    ),
)
