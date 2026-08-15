from __future__ import annotations

from backend.app.games.avalon.definition import AVALON_GAME
from backend.app.games.chess.definition import CHESS_GAME
from backend.app.games.critical_crossing.definition import CRITICAL_CROSSING_GAME
from backend.app.games.deep_shaft.definition import DEEP_SHAFT_GAME
from backend.app.games.departed_suspicion.definition import (
    DEPARTED_SUSPICION_GAME,
)
from backend.app.games.definition import GameRegistration
from backend.app.games.doudizhu.definition import DOUDIZHU_GAME
from backend.app.games.go.definition import GO_GAME
from backend.app.games.gomoku.definition import GOMOKU_GAME
from backend.app.games.hanoi.definition import HANOI_GAME
from backend.app.games.junqi.definition import JUNQI_GAME
from backend.app.games.minesweeper.definition import MINESWEEPER_GAME
from backend.app.games.monopoly.definition import MONOPOLY_GAME
from backend.app.games.one_night_werewolf.definition import (
    ONE_NIGHT_WEREWOLF_GAME,
)
from backend.app.games.poker.definition import POKER_GAME
from backend.app.games.pixel_push.definition import PIXEL_PUSH_GAME
from backend.app.games.reaction.definition import REACTION_GAME
from backend.app.games.schulte.definition import SCHULTE_GAME
from backend.app.games.tetris.definition import TETRIS_GAME
from backend.app.games.xiangqi.definition import XIANGQI_GAME


BUILTIN_GAME_REGISTRATIONS: tuple[GameRegistration, ...] = (
    AVALON_GAME,
    DEPARTED_SUSPICION_GAME,
    ONE_NIGHT_WEREWOLF_GAME,
    GOMOKU_GAME,
    XIANGQI_GAME,
    CHESS_GAME,
    GO_GAME,
    POKER_GAME,
    DOUDIZHU_GAME,
    JUNQI_GAME,
    PIXEL_PUSH_GAME,
    REACTION_GAME,
    DEEP_SHAFT_GAME,
    SCHULTE_GAME,
    CRITICAL_CROSSING_GAME,
    MINESWEEPER_GAME,
    HANOI_GAME,
    TETRIS_GAME,
    MONOPOLY_GAME,
)
if len({definition.key for definition in BUILTIN_GAME_REGISTRATIONS}) != len(
    BUILTIN_GAME_REGISTRATIONS
):
    raise ValueError("官方游戏模块存在重复 key")

_catalog_orders = [
    definition.catalog.order for definition in BUILTIN_GAME_REGISTRATIONS
]
if len(set(_catalog_orders)) != len(_catalog_orders):
    raise ValueError("官方游戏目录存在重复排序")
