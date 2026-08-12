from __future__ import annotations

from backend.app.games.base import GameEngine
from backend.app.games.catalog import BUILTIN_GAME_CATALOG
from backend.app.games.avalon.arcade import AvalonEngine
from backend.app.games.departed_suspicion import DepartedSuspicionEngine
from backend.app.games.doudizhu import DoudizhuEngine
from backend.app.games.go import GoEngine
from backend.app.games.gomoku import GomokuEngine
from backend.app.games.hanoi import HanoiEngine
from backend.app.games.junqi import JunqiEngine
from backend.app.games.minesweeper import MinesweeperEngine
from backend.app.games.monopoly import MonopolyEngine
from backend.app.games.poker import PokerEngine
from backend.app.games.reaction import ReactionEngine
from backend.app.games.schulte import SchulteEngine
from backend.app.games.tetris import TetrisEngine
from backend.app.games.xiangqi import XiangqiEngine
from backend.app.games.plugins import discover_game_plugins, plugin_catalog


def build_engine_registry() -> dict[str, GameEngine]:
    engines: list[GameEngine] = [
        AvalonEngine(),
        DepartedSuspicionEngine(),
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
        TetrisEngine(),
        MonopolyEngine(),
    ]
    registry = {engine.key: engine for engine in engines}
    for plugin in discover_game_plugins():
        if plugin.engine.key in registry:
            raise ValueError(f"游戏标识重复：{plugin.engine.key}")
        registry[plugin.engine.key] = plugin.engine
    return registry


GAME_CATALOG = [*BUILTIN_GAME_CATALOG, *plugin_catalog()]
