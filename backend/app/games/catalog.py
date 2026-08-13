from __future__ import annotations

from backend.app.games.builtin import BUILTIN_GAME_DEFINITIONS


_catalog_orders = [
    definition.catalog.order for definition in BUILTIN_GAME_DEFINITIONS
]
if len(set(_catalog_orders)) != len(_catalog_orders):
    raise ValueError("官方游戏目录存在重复排序")

BUILTIN_GAME_CATALOG: tuple[dict[str, str], ...] = tuple(
    definition.catalog_entry
    for definition in sorted(
        BUILTIN_GAME_DEFINITIONS,
        key=lambda item: item.catalog.order,
    )
)

BUILTIN_GAME_NAMES = {
    game["key"]: game["name"] for game in BUILTIN_GAME_CATALOG
}
