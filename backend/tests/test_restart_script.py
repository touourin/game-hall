from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import pytest


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
    deploy_application = Mock()

    monkeypatch.setattr(
        restart,
        "parse_args",
        lambda: type(
            "Args",
            (),
            {
                "no_pull": True,
                "timeout": 120,
            },
        )(),
    )
    monkeypatch.setattr(restart, "validate_environment", lambda: None)
    monkeypatch.setattr(restart, "update_sources", update_sources)
    monkeypatch.setattr(restart, "deploy_application", deploy_application)
    monkeypatch.setattr(restart, "wait_until_healthy", lambda _timeout: None)
    monkeypatch.setattr(restart, "log", lambda _message: None)

    assert restart.main() == 0
    update_sources.assert_not_called()
    deploy_application.assert_called_once_with()


def test_deployment_builds_validates_then_restarts(monkeypatch) -> None:
    restart = load_restart_script()
    commands: list[list[str]] = []

    monkeypatch.setattr(restart, "log", lambda _message: None)
    monkeypatch.setattr(
        restart,
        "run",
        lambda command, **_kwargs: commands.append(command),
    )

    restart.deploy_application()

    assert commands == [
        ["docker", "compose", "config", "--quiet"],
        ["docker", "compose", "build", "app"],
        [
            "docker",
            "compose",
            "run",
            "--rm",
            "--no-deps",
            "app",
            "python",
            "-m",
            "backend.app.games.validate_plugins",
        ],
        ["docker", "compose", "up", "-d", "--no-build", "app"],
    ]


def test_failed_plugin_validation_keeps_current_application_running(
    monkeypatch,
) -> None:
    restart = load_restart_script()
    commands: list[list[str]] = []

    monkeypatch.setattr(restart, "log", lambda _message: None)

    def run(command: list[str], **_kwargs) -> None:
        commands.append(command)
        if "backend.app.games.validate_plugins" in command:
            raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(restart, "run", run)

    with pytest.raises(subprocess.CalledProcessError):
        restart.deploy_application()

    assert ["docker", "compose", "up", "-d", "--no-build", "app"] not in commands
