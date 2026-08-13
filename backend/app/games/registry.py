from __future__ import annotations

from backend.app.games.base import GameEngine
from backend.app.games.builtin import BUILTIN_GAME_DEFINITIONS
from backend.app.games.catalog import BUILTIN_GAME_CATALOG
from backend.app.games.avalon.arcade import AvalonEngine
from backend.app.games.departed_suspicion import DepartedSuspicionEngine
from backend.app.games.one_night_werewolf import OneNightWerewolfEngine
from backend.app.games.plugins import discover_game_plugins, plugin_catalog


def build_engine_registry() -> dict[str, GameEngine]:
    engines: list[GameEngine] = [
        AvalonEngine(),
        DepartedSuspicionEngine(),
        OneNightWerewolfEngine(),
    ]
    engines.extend(
        definition.create_engine()
        for definition in BUILTIN_GAME_DEFINITIONS
    )
    registry = {engine.key: engine for engine in engines}
    if len(registry) != len(engines):
        raise ValueError("官方游戏引擎存在重复 key")
    for plugin in discover_game_plugins():
        if plugin.engine.key in registry:
            raise ValueError(f"游戏标识重复：{plugin.engine.key}")
        registry[plugin.engine.key] = plugin.engine
    return registry


GAME_CATALOG = [*BUILTIN_GAME_CATALOG, *plugin_catalog()]
