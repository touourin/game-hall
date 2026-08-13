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
    {
        "key": "gomoku",
        "name": "五子棋",
        "players": "2 人",
        "description": "15 路棋盘，Swap2 与有禁手连珠",
    },
    {
        "key": "xiangqi",
        "name": "中国象棋",
        "players": "2 人",
        "description": "完整走子与重复局面限制",
    },
    {
        "key": "go",
        "name": "围棋",
        "players": "2 人",
        "description": "9/13/19 路中国规则，贴目可选",
    },
    {
        "key": "poker",
        "name": "德州扑克",
        "players": "2–8 人",
        "description": "大小盲、四轮下注与全押边池",
    },
    {
        "key": "doudizhu",
        "name": "斗地主",
        "players": "3 人",
        "description": "叫抢地主、三种玩法与倍数结算",
    },
    {
        "key": "junqi",
        "name": "军旗",
        "players": "2 人",
        "description": "暗军旗布阵与翻棋对战",
    },
    {
        "key": "reaction",
        "name": "反应挑战",
        "players": "1 人",
        "description": "三轮高精度反应测试",
    },
    {
        "key": "deep_shaft",
        "name": "百层深井",
        "players": "1 人",
        "description": "左右控制落点，在危险平台间深入一百层",
    },
    {
        "key": "schulte",
        "name": "舒尔特方格",
        "players": "1 人",
        "description": "按顺序寻找 1–25，训练专注与视觉搜索",
    },
    {
        "key": "survive_three_seconds",
        "name": "坚持三秒",
        "players": "1 人",
        "description": "在铺天盖地的弹幕中躲避三秒",
    },
    {
        "key": "minesweeper",
        "name": "扫雷",
        "players": "1 人",
        "description": "三种经典难度，首次点击安全",
    },
    {
        "key": "hanoi",
        "name": "汉诺塔",
        "players": "1 人",
        "description": "3–8 层经典益智挑战，争取最少步数",
    },
    {
        "key": "tetris",
        "name": "落块挑战",
        "players": "1 人",
        "description": "排列七种方块，连续消行挑战高分",
    },
    {
        "key": "monopoly",
        "name": "大富翁",
        "players": "2–4 人",
        "description": "掷骰环游城市，买地升级并收取租金",
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
