from __future__ import annotations

import json
from pathlib import Path

import pytest

import backend.app.accounts as accounts_module
from backend.app.accounts import AccountStore
from backend.app.games.plugins import (
    GamePluginValidationError,
    discover_game_plugins,
    validate_game_plugins,
)


def write_plugin(
    root: Path,
    *,
    plugin_id: str,
    status: str = "enabled",
    room_layout: str | None = None,
) -> Path:
    directory = root / plugin_id
    backend = directory / "backend"
    backend.mkdir(parents=True)
    manifest = {
        "apiVersion": 1,
        "version": "1.0.0",
        "author": "Test Author",
        "license": "UNLICENSED",
        "id": plugin_id,
        "name": "测试插件",
        "description": "测试自动注册",
        "category": "插件游戏",
        "tone": "test",
        "players": {"min": 1, "max": 1},
        "capabilities": {
            "guests": False,
            "spectators": True,
            "spectatorFrames": False,
            "firstPlayer": False,
            "undoActions": [],
            "drawRequests": False,
            "replay": False,
            "ai": False,
        },
        "records": {"scoreKind": "outcome"},
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
    (directory / "README.md").write_text("# 测试插件\n", encoding="utf-8")
    plugin_source = """
class Engine:
    key = __PLUGIN_KEY__
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
""".replace("__PLUGIN_KEY__", repr(plugin_id)).strip()
    (backend / "plugin.py").write_text(
        plugin_source,
        encoding="utf-8",
    )
    frontend = directory / "frontend"
    frontend.mkdir()
    (frontend / "GameView.vue").write_text(
        "<template><main>测试插件</main></template>\n",
        encoding="utf-8",
    )
    registry_path = root / "registry.json"
    registry = (
        json.loads(registry_path.read_text(encoding="utf-8"))
        if registry_path.is_file()
        else {"apiVersion": 1, "plugins": []}
    )
    registry["plugins"].append(
        {
            "id": plugin_id,
            "path": plugin_id,
            "status": status,
            "order": len(registry["plugins"]) + 1,
        }
    )
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False),
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
    assert plugins[0].registration.source == "community"
    assert plugins[0].registration.capabilities.spectators is True
    assert plugins[0].registration.records.score_kind == "outcome"


def test_absent_or_empty_plugin_repository_loads_no_plugins(tmp_path) -> None:
    missing = tmp_path / "missing"
    empty = tmp_path / "empty"
    empty.mkdir()

    assert validate_game_plugins(missing) == []
    assert validate_game_plugins(empty) == []


def test_nonempty_plugin_repository_requires_a_registry(tmp_path) -> None:
    (tmp_path / "README.md").write_text("# 插件仓库\n", encoding="utf-8")

    with pytest.raises(GamePluginValidationError) as error:
        validate_game_plugins(tmp_path)

    assert error.value.issues == ("registry.json: 缺少 registry.json",)


def test_plugin_with_invalid_room_layout_is_rejected(tmp_path) -> None:
    write_plugin(
        tmp_path,
        plugin_id="plugin-test-game",
        room_layout="fullscreen",
    )

    assert discover_game_plugins(tmp_path) == []


def test_plugin_with_fields_outside_the_manifest_schema_is_rejected(tmp_path) -> None:
    directory = write_plugin(tmp_path, plugin_id="plugin-test-game")
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["installScript"] = "unsafe"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(GamePluginValidationError) as error:
        validate_game_plugins(tmp_path)

    assert error.value.issues == (
        "plugin-test-game: manifest.json 包含未知字段：installScript",
    )


@pytest.mark.parametrize("score_kind", ("time_trial", "high_score", "ranking"))
def test_scored_plugin_must_expose_player_score(tmp_path, score_kind) -> None:
    directory = write_plugin(tmp_path, plugin_id="plugin-test-game")
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["records"]["scoreKind"] = score_kind
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(GamePluginValidationError) as error:
        validate_game_plugins(tmp_path)

    assert error.value.issues == (
        "plugin-test-game: 计时、高分或排名积分插件引擎必须实现 player_score()",
    )


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
    write_plugin(tmp_path, plugin_id="plugin-disabled", status="disabled")
    broken = tmp_path / "plugin-broken"
    broken.mkdir()
    (broken / "manifest.json").write_text("{}", encoding="utf-8")

    plugins = discover_game_plugins(tmp_path)

    assert [plugin.engine.key for plugin in plugins] == ["plugin-test-game"]


def test_release_validation_reports_every_invalid_plugin(tmp_path) -> None:
    missing_view = write_plugin(tmp_path, plugin_id="plugin-test-game")
    (missing_view / "frontend" / "GameView.vue").unlink()
    missing_readme = write_plugin(tmp_path, plugin_id="plugin-second-game")
    (missing_readme / "README.md").unlink()

    with pytest.raises(GamePluginValidationError) as error:
        validate_game_plugins(tmp_path)

    assert error.value.issues == (
        "plugin-test-game: 缺少必需文件：frontend/GameView.vue",
        "plugin-second-game: 缺少必需文件：README.md",
    )


def test_plugin_match_is_registered_and_visible_in_stats(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin_root = tmp_path / "plugins"
    write_plugin(plugin_root, plugin_id="plugin-test-game")
    registration = validate_game_plugins(plugin_root)[0].registration
    monkeypatch.setattr(
        accounts_module,
        "GAME_NAMES",
        {registration.key: registration.catalog.name},
    )
    monkeypatch.setattr(
        accounts_module,
        "game_registration",
        lambda game_key: registration if game_key == registration.key else None,
    )
    monkeypatch.setattr(accounts_module, "SCORED_GAME_KEYS", frozenset())

    store = AccountStore(tmp_path / "plugin-stats.sqlite3")
    first, _ = store.register("plugin_one", "secret123", "插件玩家一")
    second, _ = store.register("plugin_two", "secret123", "插件玩家二")

    stored = store.record_game_match(
        game_key=registration.key,
        game_name=registration.catalog.name,
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
        first.id, game_key=registration.key
    )["wins"] == 1
    history = store.history_for_account(
        first.id, game_key=registration.key
    )
    assert history[0]["gameName"] == registration.catalog.name
