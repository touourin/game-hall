from __future__ import annotations

from backend.app.games.chess.definition import CHESS_GAME
from backend.app.games.deep_shaft.definition import DEEP_SHAFT_GAME
from backend.app.games.definition import GameDefinition
from backend.app.games.doudizhu.definition import DOUDIZHU_GAME
from backend.app.games.go.definition import GO_GAME
from backend.app.games.gomoku.definition import GOMOKU_GAME
from backend.app.games.hanoi.definition import HANOI_GAME
from backend.app.games.junqi.definition import JUNQI_GAME
from backend.app.games.minesweeper.definition import MINESWEEPER_GAME
from backend.app.games.monopoly.definition import MONOPOLY_GAME
from backend.app.games.poker.definition import POKER_GAME
from backend.app.games.reaction.definition import REACTION_GAME
from backend.app.games.schulte.definition import SCHULTE_GAME
from backend.app.games.survive_three_seconds.definition import SURVIVE_THREE_SECONDS_GAME
from backend.app.games.tetris.definition import TETRIS_GAME
from backend.app.games.xiangqi.definition import XIANGQI_GAME


BUILTIN_GAME_DEFINITIONS: tuple[GameDefinition, ...] = (
    GOMOKU_GAME,
    XIANGQI_GAME,
    CHESS_GAME,
    GO_GAME,
    POKER_GAME,
    DOUDIZHU_GAME,
    JUNQI_GAME,
    REACTION_GAME,
    DEEP_SHAFT_GAME,
    SCHULTE_GAME,
    SURVIVE_THREE_SECONDS_GAME,
    MINESWEEPER_GAME,
    HANOI_GAME,
    TETRIS_GAME,
    MONOPOLY_GAME,
)
BUILTIN_GAME_DEFINITION_BY_KEY = {
    definition.key: definition for definition in BUILTIN_GAME_DEFINITIONS
}

if len(BUILTIN_GAME_DEFINITION_BY_KEY) != len(BUILTIN_GAME_DEFINITIONS):
    raise ValueError("官方游戏模块存在重复 key")


def builtin_game_definition(game_key: str) -> GameDefinition | None:
    return BUILTIN_GAME_DEFINITION_BY_KEY.get(game_key)
