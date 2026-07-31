from __future__ import annotations

from backend.app.games.base import GameEngine
from backend.app.games.doudizhu import DoudizhuEngine
from backend.app.games.go import GoEngine
from backend.app.games.gomoku import GomokuEngine
from backend.app.games.xiangqi import XiangqiEngine


def build_engine_registry() -> dict[str, GameEngine]:
    engines: list[GameEngine] = [
        GomokuEngine(),
        XiangqiEngine(),
        GoEngine(),
        DoudizhuEngine(),
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
        "description": "15 路棋盘，率先连成五子",
    },
    {
        "key": "xiangqi",
        "name": "中国象棋",
        "players": "2 人",
        "description": "完整走子、将军与将死校验",
    },
    {
        "key": "go",
        "name": "围棋",
        "players": "2 人",
        "description": "19 路中国规则，支持提子与打劫",
    },
    {
        "key": "doudizhu",
        "name": "斗地主",
        "players": "3 人",
        "description": "叫地主、完整牌型与联网对战",
    },
]
