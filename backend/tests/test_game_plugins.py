from __future__ import annotations

import json
from pathlib import Path

from backend.app.accounts import AccountStore
from backend.app.games.plugins import discover_game_plugins, third_party_games_root


def write_plugin(
    root: Path,
    *,
    plugin_id: str,
    enabled: bool = True,
    room_layout: str | None = None,
) -> Path:
    directory = root / plugin_id
    backend = directory / "backend"
    backend.mkdir(parents=True)
    manifest = {
        "apiVersion": 1,
        "enabled": enabled,
        "id": plugin_id,
        "name": "测试插件",
        "description": "测试自动注册",
        "category": "插件游戏",
        "tone": "test",
        "players": {"min": 1, "max": 1},
    }
    if room_layout is not None:
        manifest["roomLayout"] = room_layout
    (directory / "manifest.json").write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (backend / "plugin.py").write_text(
        """
class Engine:
    key = 'plugin-test-game'
    name = '测试插件'
    min_players = 1
    max_players = 1
    def initial_state(self): return {}
    def start(self, room): room.phase = 'playing'
    def act(self, room, player, action, payload): return None
    def view(self, room, viewer): return {}
    def player_result(self, room, player): return ('player', 'solo', False)

def create_engine():
    return Engine()
""".strip(),
        encoding="utf-8",
    )
    return directory


def test_enabled_plugin_is_discovered_from_its_own_directory(tmp_path) -> None:
    write_plugin(
        tmp_path,
        plugin_id="plugin-test-game",
        room_layout="immersive",
    )

    plugins = discover_game_plugins(tmp_path)

    assert [plugin.engine.key for plugin in plugins] == ["plugin-test-game"]
    assert plugins[0].catalog_entry["players"] == "1 人"
    assert plugins[0].manifest["roomLayout"] == "immersive"


def test_plugin_with_invalid_room_layout_is_rejected(tmp_path) -> None:
    write_plugin(
        tmp_path,
        plugin_id="plugin-test-game",
        room_layout="fullscreen",
    )

    assert discover_game_plugins(tmp_path) == []


def test_plugin_backend_can_keep_existing_logic_in_local_modules(tmp_path) -> None:
    directory = write_plugin(tmp_path, plugin_id="plugin-test-game")
    backend = directory / "backend"
    (backend / "engine.py").write_text(
        """
class ExistingGameEngine:
    key = 'plugin-test-game'
    name = '测试插件'
    min_players = 1
    max_players = 1
    def initial_state(self): return {'source': 'local-module'}
    def start(self, room): room.phase = 'playing'
    def act(self, room, player, action, payload): return None
    def view(self, room, viewer): return room.state
    def player_result(self, room, player): return ('player', 'solo', False)
""".strip(),
        encoding="utf-8",
    )
    (backend / "plugin.py").write_text(
        """
from .engine import ExistingGameEngine

def create_engine():
    return ExistingGameEngine()
""".strip(),
        encoding="utf-8",
    )

    plugins = discover_game_plugins(tmp_path)

    assert plugins[0].engine.initial_state() == {"source": "local-module"}


def test_disabled_or_broken_plugin_does_not_block_other_plugins(tmp_path) -> None:
    write_plugin(tmp_path, plugin_id="plugin-test-game")
    write_plugin(tmp_path, plugin_id="plugin-disabled", enabled=False)
    broken = tmp_path / "plugin-broken"
    broken.mkdir()
    (broken / "manifest.json").write_text("{}", encoding="utf-8")

    plugins = discover_game_plugins(tmp_path)

    assert [plugin.engine.key for plugin in plugins] == ["plugin-test-game"]


def test_repository_includes_a_safe_disabled_template() -> None:
    root = third_party_games_root()
    manifest = json.loads(
        (root / "plugin-counter-demo" / "manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["enabled"] is False
    assert (root / "README.md").is_file()
    assert (root / "plugin.schema.json").is_file()


def test_plugin_match_is_registered_and_visible_in_stats(tmp_path) -> None:
    store = AccountStore(tmp_path / "plugin-stats.sqlite3")
    first, _ = store.register("plugin_one", "secret123", "插件玩家一")
    second, _ = store.register("plugin_two", "secret123", "插件玩家二")

    stored = store.record_game_match(
        game_key="plugin-counter-demo",
        game_name="计数竞速",
        match_id="plugin-match-1",
        room_code="PLUG",
        winner="player",
        reason="插件玩家一率先达到 10 分",
        started_at="2026-08-04T10:00:00+00:00",
        ended_at="2026-08-04T10:05:00+00:00",
        details={"options": {}, "state": {"targetScore": 10}},
        players=[
            {
                "accountId": first.id,
                "playerName": first.player_name,
                "seat": 1,
                "role": "counter",
                "alignment": "solo",
                "won": True,
                "isHost": True,
            },
            {
                "accountId": second.id,
                "playerName": second.player_name,
                "seat": 2,
                "role": "counter",
                "alignment": "solo",
                "won": False,
                "isHost": False,
            },
        ],
    )

    assert stored is True
    assert store.summary_for_account(
        first.id, game_key="plugin-counter-demo"
    )["wins"] == 1
    history = store.history_for_account(
        first.id, game_key="plugin-counter-demo"
    )
    assert history[0]["gameName"] == "计数竞速"
