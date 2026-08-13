from __future__ import annotations

from backend.app.games.builtin import BUILTIN_GAME_DEFINITIONS


BUILTIN_GAME_ORDER: tuple[str, ...] = (
    "avalon",
    "departed_suspicion",
    "one_night_werewolf",
    "gomoku",
    "xiangqi",
    "chess",
    "go",
    "poker",
    "doudizhu",
    "junqi",
    "reaction",
    "deep_shaft",
    "schulte",
    "survive_three_seconds",
    "minesweeper",
    "hanoi",
    "tetris",
    "monopoly",
)

LEGACY_BUILTIN_GAME_CATALOG: tuple[dict[str, str], ...] = (
    {
        "key": "avalon",
        "name": "阿瓦隆",
        "players": "5–10 人",
        "description": "身份推理与团队博弈",
    },
    {
        "key": "departed_suspicion",
        "name": "无间疑云",
        "players": "4–8 人",
        "description": "调查底细、装备应变并找出敌方领袖",
    },
    {
        "key": "one_night_werewolf",
        "name": "一夜狼人",
        "players": "3–10 人",
        "description": "一晚行动、晨间推理与一次终局投票",
    },
)

_LEGACY_CATALOG_ORDER = {
    key: index * 10 for index, key in enumerate(BUILTIN_GAME_ORDER)
}

_definition_keys = {definition.key for definition in BUILTIN_GAME_DEFINITIONS}
_legacy_keys = {game["key"] for game in LEGACY_BUILTIN_GAME_CATALOG}
if _definition_keys & _legacy_keys:
    raise ValueError("官方游戏同时存在于模块注册表和旧目录")
if _definition_keys | _legacy_keys != set(BUILTIN_GAME_ORDER):
    raise ValueError("官方游戏目录与排序表不一致")

BUILTIN_GAME_CATALOG: tuple[dict[str, str], ...] = tuple(
    entry
    for _, entry in sorted(
        [
            *(
                (_LEGACY_CATALOG_ORDER[game["key"]], game)
                for game in LEGACY_BUILTIN_GAME_CATALOG
            ),
            *(
                (definition.catalog.order, definition.catalog_entry)
                for definition in BUILTIN_GAME_DEFINITIONS
            ),
        ],
        key=lambda item: item[0],
    )
)

BUILTIN_GAME_NAMES = {
    game["key"]: game["name"] for game in BUILTIN_GAME_CATALOG
}
