from __future__ import annotations

from backend.app.games.chess.definition import CHESS_GAME
from backend.app.games.definition import GameDefinition
from backend.app.games.go.definition import GO_GAME
from backend.app.games.gomoku.definition import GOMOKU_GAME
from backend.app.games.junqi.definition import JUNQI_GAME
from backend.app.games.xiangqi.definition import XIANGQI_GAME


BUILTIN_GAME_DEFINITIONS: tuple[GameDefinition, ...] = (
    GOMOKU_GAME,
    XIANGQI_GAME,
    CHESS_GAME,
    GO_GAME,
    JUNQI_GAME,
)
BUILTIN_GAME_DEFINITION_BY_KEY = {
    definition.key: definition for definition in BUILTIN_GAME_DEFINITIONS
}

if len(BUILTIN_GAME_DEFINITION_BY_KEY) != len(BUILTIN_GAME_DEFINITIONS):
    raise ValueError("官方游戏模块存在重复 key")


def builtin_game_definition(game_key: str) -> GameDefinition | None:
    return BUILTIN_GAME_DEFINITION_BY_KEY.get(game_key)
