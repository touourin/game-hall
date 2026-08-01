from __future__ import annotations

from backend.app.games.base import GameEngine
from backend.app.games.doudizhu import DoudizhuEngine
from backend.app.games.go import GoEngine
from backend.app.games.gomoku import GomokuEngine
from backend.app.games.hanoi import HanoiEngine
from backend.app.games.junqi import JunqiEngine
from backend.app.games.minesweeper import MinesweeperEngine
from backend.app.games.poker import PokerEngine
from backend.app.games.reaction import ReactionEngine
from backend.app.games.schulte import SchulteEngine
from backend.app.games.xiangqi import XiangqiEngine


def build_engine_registry() -> dict[str, GameEngine]:
    engines: list[GameEngine] = [
        GomokuEngine(),
        XiangqiEngine(),
        GoEngine(),
        PokerEngine(),
        DoudizhuEngine(),
        JunqiEngine(),
        ReactionEngine(),
        SchulteEngine(),
        MinesweeperEngine(),
        HanoiEngine(),
    ]
    return {engine.key: engine for engine in engines}


GAME_CATALOG = [
    {
        "key": "avalon",
        "name": "阿瓦隆",
        "players": "5–10 人",
        "description": "身份推理与团队博弈",
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
        "key": "schulte",
        "name": "舒尔特方格",
        "players": "1 人",
        "description": "按顺序寻找 1–25，训练专注与视觉搜索",
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
]
