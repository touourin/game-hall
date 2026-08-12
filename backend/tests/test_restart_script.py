from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_restart_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "restart_script",
        PROJECT_ROOT / "scripts" / "restart.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_update_sources_updates_main_then_remote_submodules(monkeypatch) -> None:
    restart = load_restart_script()
    calls: list[str] = []

    monkeypatch.setattr(
        restart, "validate_source_checkout", lambda: calls.append("validate")
    )
    monkeypatch.setattr(
        restart,
        "reset_submodules_to_recorded_commits",
        lambda: calls.append("reset-submodules"),
    )
    monkeypatch.setattr(restart, "pull_main_branch", lambda: calls.append("pull-main"))
    monkeypatch.setattr(
        restart,
        "update_submodules_from_remotes",
        lambda: calls.append("update-submodules"),
    )

    restart.update_sources()

    assert calls == [
        "validate",
        "reset-submodules",
        "pull-main",
        "update-submodules",
    ]


def test_remote_submodule_update_tracks_configured_branches(monkeypatch) -> None:
    restart = load_restart_script()
    commands: list[list[str]] = []

    monkeypatch.setattr(restart, "log", lambda _message: None)
    monkeypatch.setattr(
        restart,
        "run",
        lambda command, **_kwargs: commands.append(command),
    )

    restart.update_submodules_from_remotes()

    assert commands[-1] == [
        "git",
        "submodule",
        "update",
        "--init",
        "--remote",
        "--recursive",
        "--checkout",
    ]


def test_main_skips_git_updates_with_no_pull(monkeypatch) -> None:
    restart = load_restart_script()
    update_sources = Mock()

    monkeypatch.setattr(restart, "parse_args", lambda: type("Args", (), {
        "no_pull": True,
        "timeout": 120,
    })())
    monkeypatch.setattr(restart, "validate_environment", lambda: None)
    monkeypatch.setattr(restart, "update_sources", update_sources)
    monkeypatch.setattr(restart, "run", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(restart, "wait_until_healthy", lambda _timeout: None)
    monkeypatch.setattr(restart, "log", lambda _message: None)

    assert restart.main() == 0
    update_sources.assert_not_called()
