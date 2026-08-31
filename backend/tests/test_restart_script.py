from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.app.ai.douzero_models import require_model_paths


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
        lambda: SimpleNamespace(
            no_pull=True,
            restart_only=False,
            timeout=120,
        ),
    )
    monkeypatch.setattr(restart, "validate_environment", lambda: None)
    monkeypatch.setattr(restart, "update_sources", update_sources)
    monkeypatch.setattr(restart, "deploy_application", deploy_application)
    monkeypatch.setattr(restart, "wait_until_healthy", lambda _timeout: None)
    monkeypatch.setattr(restart, "log", lambda _message: None)

    assert restart.main() == 0
    update_sources.assert_not_called()
    deploy_application.assert_called_once_with()


def test_restart_only_skips_source_updates_and_deployment(monkeypatch) -> None:
    restart = load_restart_script()
    update_sources = Mock()
    deploy_application = Mock()
    restart_existing_application = Mock()
    wait_until_healthy = Mock()

    monkeypatch.setattr(
        restart,
        "parse_args",
        lambda: SimpleNamespace(
            no_pull=False,
            restart_only=True,
            timeout=45,
        ),
    )
    monkeypatch.setattr(restart, "validate_environment", lambda: None)
    monkeypatch.setattr(restart, "update_sources", update_sources)
    monkeypatch.setattr(restart, "deploy_application", deploy_application)
    monkeypatch.setattr(
        restart,
        "restart_existing_application",
        restart_existing_application,
    )
    monkeypatch.setattr(restart, "wait_until_healthy", wait_until_healthy)

    assert restart.main() == 0
    update_sources.assert_not_called()
    deploy_application.assert_not_called()
    restart_existing_application.assert_called_once_with()
    wait_until_healthy.assert_called_once_with(45)


def test_restart_only_and_no_pull_are_mutually_exclusive() -> None:
    restart = load_restart_script()

    with pytest.raises(SystemExit):
        restart.parse_args(["--restart-only", "--no-pull"])


def test_restart_only_restarts_the_application_service(monkeypatch) -> None:
    restart = load_restart_script()
    commands: list[list[str]] = []

    monkeypatch.setattr(restart, "log", lambda _message: None)
    monkeypatch.setattr(
        restart,
        "run",
        lambda command, **_kwargs: commands.append(command),
    )

    restart.restart_existing_application()

    assert commands == [
        ["docker", "compose", "restart", "--no-deps", "app"],
    ]


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


def test_ai_engines_use_uniform_optional_build_bundles() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
    compose = (PROJECT_ROOT / "compose.yaml").read_text(encoding="utf-8")
    environment_example = (PROJECT_ROOT / ".env.example").read_text(
        encoding="utf-8"
    )
    model_paths = require_model_paths(PROJECT_ROOT / "ai" / "douzero")

    assert {path.name for path in model_paths.values()} == {
        "landlord.ckpt",
        "landlord_up.ckpt",
        "landlord_down.ckpt",
    }
    for engine in ("PIKAFISH", "KATAGO", "DOUZERO"):
        setting = f"ENABLE_{engine}_AI"
        assert f"ARG {setting}=1" in dockerfile
        assert f"{setting}: ${{{setting}:-1}}" in compose
        assert f"{setting}=1" in environment_example
    assert "FROM pikafish-bundle-${ENABLE_PIKAFISH_AI}" in dockerfile
    assert "FROM katago-bundle-${ENABLE_KATAGO_AI}" in dockerfile
    assert "FROM douzero-runtime-${ENABLE_DOUZERO_AI} AS runtime" in dockerfile
    assert "COPY --from=pikafish-bundle /bundle/ /" in dockerfile
    assert "COPY --from=katago-bundle /bundle/ /" in dockerfile
    assert "/tmp/douzero-models --output /bundle" in dockerfile
    assert "COPY --from=douzero-model-bundle" in dockerfile
    assert "/bundle/ /opt/game-hall/ai/douzero/" in dockerfile
    assert "--model-dir /opt/game-hall/ai/douzero --threads 1 --check" in dockerfile
    assert "INSTALL_DOUZERO_AI" not in dockerfile + compose + environment_example
    assert "DOUZERO_MODEL_HOST_DIR" not in compose
