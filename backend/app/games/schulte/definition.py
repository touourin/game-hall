from __future__ import annotations

from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameRegistration,
    GameRecords,
)

from .engine import SchulteEngine


SCHULTE_GAME = GameRegistration(
    key="schulte",
    engine_factory=SchulteEngine,
    catalog=GameCatalogMetadata(
        order=120,
        name="舒尔特方格",
        min_players=1,
        max_players=1,
        description="按顺序寻找 1–25，训练专注与视觉搜索",
    ),
    capabilities=GameCapabilities(
        guests=False,
        spectators=True,
        first_player=False,
    ),
    records=GameRecords(score_kind="time_trial"),
)
