from __future__ import annotations

import importlib.util
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from backend.app.games.base import GameEngine


logger = logging.getLogger(__name__)
PLUGIN_API_VERSION = 1
PLUGIN_KEY_PATTERN = re.compile(r"^plugin-[a-z0-9][a-z0-9-]{0,24}$")
PLUGIN_TONE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,23}$")


@dataclass(frozen=True)
class GamePlugin:
    directory: Path
    manifest: dict[str, Any]
    engine: GameEngine

    @property
    def catalog_entry(self) -> dict[str, str]:
        players = self.manifest["players"]
        label = players.get("label") or (
            f"{players['min']} 人"
            if players["min"] == players["max"]
            else f"{players['min']}–{players['max']} 人"
        )
        return {
            "key": self.manifest["id"],
            "name": self.manifest["name"],
            "players": label,
            "description": self.manifest["description"],
        }


def third_party_games_root() -> Path:
    return Path(__file__).resolve().parents[3] / "third_party_games"


def discover_game_plugins(root: Path | None = None) -> list[GamePlugin]:
    plugin_root = root or third_party_games_root()
    if not plugin_root.is_dir():
        return []

    plugins: list[GamePlugin] = []
    seen_keys: set[str] = set()
    for manifest_path in sorted(plugin_root.glob("*/manifest.json")):
        try:
            manifest = _read_manifest(manifest_path)
            if not manifest["enabled"]:
                continue
            plugin_key = manifest["id"]
            if plugin_key in seen_keys:
                raise ValueError(f"插件游戏标识重复：{plugin_key}")
            engine = _load_engine(manifest_path.parent, plugin_key)
            _validate_engine(engine, manifest)
            plugins.append(GamePlugin(manifest_path.parent, manifest, engine))
            seen_keys.add(plugin_key)
        except Exception:
            logger.exception(
                "Third-party game plugin was disabled",
                extra={
                    "event": "game_plugin.disabled",
                    "plugin_path": str(manifest_path.parent),
                },
            )
    return plugins


def plugin_catalog(root: Path | None = None) -> list[dict[str, str]]:
    return [plugin.catalog_entry for plugin in discover_game_plugins(root)]


def _read_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest.json 必须是对象")
    string_limits = {
        "id": 32,
        "name": 24,
        "description": 80,
        "category": 16,
        "tone": 24,
    }
    for field, maximum in string_limits.items():
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise ValueError(f"manifest.json 缺少有效字段：{field}")
        if len(payload[field]) > maximum:
            raise ValueError(f"manifest.json 字段过长：{field}")
    if payload.get("apiVersion") != PLUGIN_API_VERSION:
        raise ValueError(
            f"插件 API 版本必须为 {PLUGIN_API_VERSION}"
        )
    if not isinstance(payload.get("enabled"), bool):
        raise ValueError("manifest.json 的 enabled 必须是布尔值")
    if not PLUGIN_KEY_PATTERN.fullmatch(payload["id"]):
        raise ValueError("插件 id 必须以 plugin- 开头、最长 32 位，并只包含小写字母、数字和连字符")
    if not PLUGIN_TONE_PATTERN.fullmatch(payload["tone"]):
        raise ValueError("tone 只能包含小写字母、数字和连字符")
    if path.parent.name != payload["id"]:
        raise ValueError("插件目录名必须与 manifest id 完全一致")
    players = payload.get("players")
    if not isinstance(players, dict):
        raise ValueError("manifest.json 缺少 players 配置")
    minimum = players.get("min")
    maximum = players.get("max")
    if (
        not isinstance(minimum, int)
        or isinstance(minimum, bool)
        or not isinstance(maximum, int)
        or isinstance(maximum, bool)
        or not 1 <= minimum <= maximum <= 20
    ):
        raise ValueError("players.min/max 必须是 1–20 之间的有效人数范围")
    label = players.get("label")
    if label is not None and (
        not isinstance(label, str) or not label.strip() or len(label) > 16
    ):
        raise ValueError("players.label 必须是 1–16 位字符串")
    default_options = payload.get("defaultOptions")
    if default_options is not None and not isinstance(default_options, dict):
        raise ValueError("defaultOptions 必须是对象")
    rule_labels = payload.get("ruleLabels")
    if rule_labels is not None and (
        not isinstance(rule_labels, list)
        or len(rule_labels) > 6
        or any(
            not isinstance(item, str)
            or not item.strip()
            or len(item) > 24
            for item in rule_labels
        )
    ):
        raise ValueError("ruleLabels 最多包含 6 个 1–24 位字符串")
    return payload


def _load_engine(directory: Path, plugin_key: str) -> GameEngine:
    entry = directory / "backend" / "plugin.py"
    if not entry.is_file():
        raise ValueError("缺少 backend/plugin.py")
    module_name = f"game_hall_plugin_{plugin_key.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, entry)
    if spec is None or spec.loader is None:
        raise ValueError("无法加载插件后端入口")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        _execute_module(spec.loader, module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    factory = getattr(module, "create_engine", None)
    if not callable(factory):
        raise ValueError("backend/plugin.py 必须导出 create_engine()")
    return factory()


def _execute_module(loader: Any, module: ModuleType) -> None:
    loader.exec_module(module)


def _validate_engine(engine: GameEngine, manifest: dict[str, Any]) -> None:
    players = manifest["players"]
    if getattr(engine, "key", None) != manifest["id"]:
        raise ValueError("引擎 key 必须与 manifest id 一致")
    if getattr(engine, "name", None) != manifest["name"]:
        raise ValueError("引擎 name 必须与 manifest name 一致")
    if getattr(engine, "min_players", None) != players["min"]:
        raise ValueError("引擎 min_players 必须与 manifest players.min 一致")
    if getattr(engine, "max_players", None) != players["max"]:
        raise ValueError("引擎 max_players 必须与 manifest players.max 一致")
    for method in ("initial_state", "start", "act", "view", "player_result"):
        if not callable(getattr(engine, method, None)):
            raise ValueError(f"插件引擎缺少方法：{method}")
