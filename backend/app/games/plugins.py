from __future__ import annotations

import importlib.util
import json
import logging
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Literal, cast

from backend.app.games.base import GameEngine
from backend.app.games.definition import (
    GameCapabilities,
    GameCatalogMetadata,
    GameRegistration,
    GamePluginMetadata,
    GameRecords,
)


logger = logging.getLogger(__name__)
PLUGIN_MANIFEST_API_VERSION = 1
PLUGIN_REGISTRY_API_VERSION = 1
PLUGIN_KEY_PATTERN = re.compile(r"^plugin-[a-z0-9][a-z0-9-]{0,24}$")
PLUGIN_TONE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,23}$")
PLUGIN_VERSION_PATTERN = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?$"
)
PLUGIN_ACTION_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
PLUGIN_ROOM_LAYOUTS = frozenset({"standard", "wide", "immersive"})
PLUGIN_REGISTRY_STATUSES = frozenset({"enabled", "deprecated", "disabled"})
PLUGIN_SCORE_KINDS = frozenset({"outcome", "time_trial", "high_score"})
PLUGIN_MANIFEST_FIELDS = frozenset(
    {
        "$schema",
        "apiVersion",
        "version",
        "author",
        "license",
        "id",
        "name",
        "description",
        "category",
        "tone",
        "roomLayout",
        "players",
        "capabilities",
        "records",
        "defaultOptions",
        "ruleLabels",
    }
)
PLUGIN_PLAYER_FIELDS = frozenset({"min", "max", "label"})
PLUGIN_CAPABILITY_FIELDS = frozenset(
    {
        "guests",
        "spectators",
        "spectatorFrames",
        "firstPlayer",
        "undoActions",
        "drawRequests",
        "replay",
        "ai",
    }
)
PLUGIN_RECORD_FIELDS = frozenset({"scoreKind"})
PLUGIN_REGISTRY_FIELDS = frozenset({"$schema", "apiVersion", "plugins"})
PLUGIN_REGISTRY_ENTRY_FIELDS = frozenset({"id", "path", "status", "order"})
PLUGIN_REQUIRED_FILES = (
    "README.md",
    "backend/plugin.py",
    "frontend/GameView.vue",
)
PluginRegistryStatus = Literal["enabled", "deprecated", "disabled"]


@dataclass(frozen=True)
class PluginRegistryEntry:
    id: str
    directory: Path
    status: PluginRegistryStatus
    order: int


@dataclass(frozen=True)
class GamePlugin:
    directory: Path
    manifest: dict[str, Any]
    registration: GameRegistration

    @property
    def engine(self) -> GameEngine:
        """Compatibility helper for callers that need a fresh engine instance."""

        return self.registration.create_engine()

    @property
    def catalog_entry(self) -> dict[str, str]:
        return self.registration.catalog_entry


class GamePluginValidationError(ValueError):
    def __init__(self, issues: list[str]) -> None:
        self.issues = tuple(issues)
        super().__init__(
            "社区游戏插件校验失败：\n- " + "\n- ".join(self.issues)
        )


def community_games_root() -> Path:
    return Path(__file__).resolve().parents[3] / "game-hall-community-games"


def discover_game_plugins(root: Path | None = None) -> list[GamePlugin]:
    """Best-effort discovery used by development tooling."""

    return _collect_game_plugins(root, fail_on_error=False)


def validate_game_plugins(root: Path | None = None) -> list[GamePlugin]:
    """Load every published plugin and reject the release on any error."""

    return _collect_game_plugins(root, fail_on_error=True)


def _collect_game_plugins(
    root: Path | None,
    *,
    fail_on_error: bool,
) -> list[GamePlugin]:
    plugin_root = root or community_games_root()
    try:
        if not _plugin_repository_available(plugin_root):
            return []
        entries = _read_registry(plugin_root)
    except Exception as error:
        if fail_on_error:
            raise GamePluginValidationError(
                [f"registry.json: {_error_reason(error)}"]
            ) from error
        logger.exception(
            "Community game registry was disabled",
            extra={"event": "game_plugin.registry_disabled"},
        )
        return []

    plugins: list[GamePlugin] = []
    issues: list[str] = []
    for entry in entries:
        if entry.status == "disabled":
            continue
        try:
            manifest_path = entry.directory / "manifest.json"
            manifest = _read_manifest(manifest_path)
            if manifest["id"] != entry.id:
                raise ValueError("registry id 必须与 manifest id 完全一致")
            _validate_required_files(entry.directory)
            engine_factory = _load_engine_factory(entry.directory, entry.id)
            engine = engine_factory()
            _validate_engine(engine, manifest)
            registration = _build_registration(
                entry,
                manifest,
                engine_factory,
            )
            registration.create_engine()
            plugins.append(GamePlugin(entry.directory, manifest, registration))
        except Exception as error:
            issue = f"{entry.id}: {_error_reason(error)}"
            if fail_on_error:
                issues.append(issue)
                continue
            logger.exception(
                "Community game plugin was disabled",
                extra={
                    "event": "game_plugin.disabled",
                    "plugin_id": entry.id,
                    "plugin_path": str(entry.directory),
                },
            )
    if issues:
        raise GamePluginValidationError(issues)
    return plugins


def _plugin_repository_available(root: Path) -> bool:
    """Return false only for an absent or uninitialized plugin repository."""

    if not root.exists():
        return False
    if not root.is_dir():
        raise ValueError("社区游戏路径必须是目录")
    if (root / "registry.json").is_file():
        return True
    if any(root.iterdir()):
        raise ValueError("缺少 registry.json")
    return False


def _read_registry(root: Path) -> list[PluginRegistryEntry]:
    path = root / "registry.json"
    if not path.is_file():
        raise ValueError("缺少 registry.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("registry.json 必须是对象")
    _reject_unknown_fields(payload, PLUGIN_REGISTRY_FIELDS, "registry.json")
    schema = payload.get("$schema")
    if schema is not None and not isinstance(schema, str):
        raise ValueError("registry.json 的 $schema 必须是字符串")
    if payload.get("apiVersion") != PLUGIN_REGISTRY_API_VERSION:
        raise ValueError(
            f"registry API 版本必须为 {PLUGIN_REGISTRY_API_VERSION}"
        )
    raw_entries = payload.get("plugins")
    if not isinstance(raw_entries, list):
        raise ValueError("registry.json 的 plugins 必须是数组")

    entries: list[PluginRegistryEntry] = []
    seen_ids: set[str] = set()
    seen_paths: set[Path] = set()
    seen_orders: set[int] = set()
    root_resolved = root.resolve()
    for index, candidate in enumerate(raw_entries):
        label = f"registry.plugins[{index}]"
        if not isinstance(candidate, dict):
            raise ValueError(f"{label} 必须是对象")
        _reject_unknown_fields(candidate, PLUGIN_REGISTRY_ENTRY_FIELDS, label)
        plugin_id = candidate.get("id")
        relative_path = candidate.get("path")
        status = candidate.get("status")
        order = candidate.get("order")
        if not isinstance(plugin_id, str) or not PLUGIN_KEY_PATTERN.fullmatch(
            plugin_id
        ):
            raise ValueError(f"{label}.id 不是有效的插件 ID")
        if not isinstance(relative_path, str):
            raise ValueError(f"{label}.path 必须是相对目录")
        pure_path = PurePosixPath(relative_path)
        if (
            pure_path.is_absolute()
            or not pure_path.parts
            or any(part in {"", ".", ".."} for part in pure_path.parts)
        ):
            raise ValueError(f"{label}.path 必须是安全的相对目录")
        directory = root.joinpath(*pure_path.parts).resolve()
        if not directory.is_relative_to(root_resolved):
            raise ValueError(f"{label}.path 不能离开社区仓库")
        if status not in PLUGIN_REGISTRY_STATUSES:
            raise ValueError(
                f"{label}.status 只能是 enabled、deprecated 或 disabled"
            )
        if (
            not isinstance(order, int)
            or isinstance(order, bool)
            or not 1 <= order <= 9999
        ):
            raise ValueError(f"{label}.order 必须是 1–9999 的整数")
        if plugin_id in seen_ids:
            raise ValueError(f"registry.json 存在重复 id：{plugin_id}")
        if directory in seen_paths:
            raise ValueError(f"registry.json 存在重复 path：{relative_path}")
        if order in seen_orders:
            raise ValueError(f"registry.json 存在重复 order：{order}")
        seen_ids.add(plugin_id)
        seen_paths.add(directory)
        seen_orders.add(order)
        entries.append(
            PluginRegistryEntry(
                id=plugin_id,
                directory=directory,
                status=cast(PluginRegistryStatus, status),
                order=order,
            )
        )
    return sorted(entries, key=lambda entry: entry.order)


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("缺少 manifest.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest.json 必须是对象")
    _reject_unknown_fields(payload, PLUGIN_MANIFEST_FIELDS, "manifest.json")
    schema = payload.get("$schema")
    if schema is not None and not isinstance(schema, str):
        raise ValueError("manifest.json 的 $schema 必须是字符串")
    if payload.get("apiVersion") != PLUGIN_MANIFEST_API_VERSION:
        raise ValueError(
            f"插件 API 版本必须为 {PLUGIN_MANIFEST_API_VERSION}"
        )

    string_limits = {
        "id": 32,
        "name": 24,
        "description": 80,
        "category": 16,
        "tone": 24,
        "version": 48,
        "author": 80,
        "license": 32,
    }
    for field, maximum in string_limits.items():
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"manifest.json 缺少有效字段：{field}")
        if len(value) > maximum:
            raise ValueError(f"manifest.json 字段过长：{field}")
    if not PLUGIN_KEY_PATTERN.fullmatch(payload["id"]):
        raise ValueError(
            "插件 id 必须以 plugin- 开头、最长 32 位，并只包含小写字母、数字和连字符"
        )
    if not PLUGIN_TONE_PATTERN.fullmatch(payload["tone"]):
        raise ValueError("tone 只能包含小写字母、数字和连字符")
    if not PLUGIN_VERSION_PATTERN.fullmatch(payload["version"]):
        raise ValueError("version 必须是语义化版本号，例如 1.0.0")

    room_layout = payload.get("roomLayout")
    if room_layout is not None and room_layout not in PLUGIN_ROOM_LAYOUTS:
        raise ValueError("roomLayout 只能是 standard、wide 或 immersive")
    players = _validate_players(payload.get("players"))
    capabilities = _validate_capabilities(payload.get("capabilities"))
    records = _validate_records(payload.get("records"))
    payload["players"] = players
    payload["capabilities"] = capabilities
    payload["records"] = records

    default_options = payload.get("defaultOptions")
    if default_options is not None and (
        not isinstance(default_options, dict)
    ):
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


def _validate_players(candidate: Any) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("manifest.json 缺少 players 配置")
    _reject_unknown_fields(candidate, PLUGIN_PLAYER_FIELDS, "players")
    minimum = candidate.get("min")
    maximum = candidate.get("max")
    if (
        not isinstance(minimum, int)
        or isinstance(minimum, bool)
        or not isinstance(maximum, int)
        or isinstance(maximum, bool)
        or not 1 <= minimum <= maximum <= 20
    ):
        raise ValueError("players.min/max 必须是 1–20 之间的有效人数范围")
    label = candidate.get("label")
    if label is not None and (
        not isinstance(label, str) or not label.strip() or len(label) > 16
    ):
        raise ValueError("players.label 必须是 1–16 位字符串")
    return candidate


def _validate_capabilities(candidate: Any) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("manifest.json 缺少 capabilities 配置")
    _reject_unknown_fields(candidate, PLUGIN_CAPABILITY_FIELDS, "capabilities")
    missing = PLUGIN_CAPABILITY_FIELDS - set(candidate)
    if missing:
        raise ValueError(
            "capabilities 缺少字段：" + "、".join(sorted(missing))
        )
    for field in PLUGIN_CAPABILITY_FIELDS - {"undoActions"}:
        if not isinstance(candidate[field], bool):
            raise ValueError(f"capabilities.{field} 必须是布尔值")
    undo_actions = candidate["undoActions"]
    if (
        not isinstance(undo_actions, list)
        or len(undo_actions) > 12
        or len(set(undo_actions)) != len(undo_actions)
        or any(
            not isinstance(action, str)
            or len(action) > 32
            or not PLUGIN_ACTION_PATTERN.fullmatch(action)
            for action in undo_actions
        )
    ):
        raise ValueError("capabilities.undoActions 包含无效动作")
    if candidate["spectatorFrames"] and not candidate["spectators"]:
        raise ValueError("spectatorFrames 依赖 spectators 能力")
    return candidate


def _validate_records(candidate: Any) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("manifest.json 缺少 records 配置")
    _reject_unknown_fields(candidate, PLUGIN_RECORD_FIELDS, "records")
    if candidate.get("scoreKind") not in PLUGIN_SCORE_KINDS:
        raise ValueError(
            "records.scoreKind 只能是 outcome、time_trial 或 high_score"
        )
    return candidate


def _build_registration(
    entry: PluginRegistryEntry,
    manifest: dict[str, Any],
    engine_factory: Callable[[], GameEngine],
) -> GameRegistration:
    players = manifest["players"]
    capabilities = manifest["capabilities"]
    return GameRegistration(
        key=manifest["id"],
        engine_factory=engine_factory,
        catalog=GameCatalogMetadata(
            order=entry.order,
            name=manifest["name"],
            min_players=players["min"],
            max_players=players["max"],
            description=manifest["description"],
            players_label=players.get("label"),
        ),
        capabilities=GameCapabilities(
            undo_actions=frozenset(capabilities["undoActions"]),
            draw_requests=capabilities["drawRequests"],
            guests=capabilities["guests"],
            spectators=capabilities["spectators"],
            spectator_frames=capabilities["spectatorFrames"],
            first_player=capabilities["firstPlayer"],
            replay=capabilities["replay"],
            ai=capabilities["ai"],
        ),
        records=GameRecords(score_kind=manifest["records"]["scoreKind"]),
        source="community",
        availability=(
            "deprecated" if entry.status == "deprecated" else "enabled"
        ),
        plugin=GamePluginMetadata(
            version=manifest["version"],
            author=manifest["author"],
            license=manifest["license"],
            directory=str(entry.directory),
        ),
    )


def _validate_required_files(directory: Path) -> None:
    missing = [
        relative
        for relative in PLUGIN_REQUIRED_FILES
        if not (directory / relative).is_file()
    ]
    if missing:
        raise ValueError(f"缺少必需文件：{'、'.join(missing)}")


def _load_engine_factory(
    directory: Path,
    plugin_key: str,
) -> Callable[[], GameEngine]:
    backend_directory = directory / "backend"
    entry = backend_directory / "plugin.py"
    package_name = f"game_hall_plugin_{plugin_key.replace('-', '_')}"
    backend_package_name = f"{package_name}.backend"
    module_name = f"{backend_package_name}.plugin"
    _remove_plugin_modules(package_name)

    package = ModuleType(package_name)
    package.__package__ = package_name
    package.__path__ = [str(directory)]  # type: ignore[attr-defined]
    backend_package = ModuleType(backend_package_name)
    backend_package.__package__ = backend_package_name
    backend_package.__path__ = [str(backend_directory)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package
    sys.modules[backend_package_name] = backend_package

    spec = importlib.util.spec_from_file_location(module_name, entry)
    if spec is None or spec.loader is None:
        _remove_plugin_modules(package_name)
        raise ValueError("无法加载插件后端入口")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        _execute_module(spec.loader, module)
    except Exception:
        _remove_plugin_modules(package_name)
        raise
    factory = getattr(module, "create_engine", None)
    if not callable(factory):
        _remove_plugin_modules(package_name)
        raise ValueError("backend/plugin.py 必须导出 create_engine()")
    return cast(Callable[[], GameEngine], factory)


def _remove_plugin_modules(package_name: str) -> None:
    for module_name in tuple(sys.modules):
        if module_name == package_name or module_name.startswith(
            f"{package_name}."
        ):
            sys.modules.pop(module_name, None)


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
    if (
        manifest["records"]["scoreKind"] != "outcome"
        and not callable(getattr(engine, "player_score", None))
    ):
        raise ValueError(
            "计时或高分插件引擎必须实现 player_score()"
        )


def _reject_unknown_fields(
    payload: dict[str, Any],
    allowed: frozenset[str],
    label: str,
) -> None:
    unexpected = set(payload) - allowed
    if unexpected:
        raise ValueError(
            f"{label} 包含未知字段：{'、'.join(sorted(unexpected))}"
        )


def _error_reason(error: Exception) -> str:
    return str(error).strip() or type(error).__name__
