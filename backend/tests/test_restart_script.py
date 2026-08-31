from __future__ import annotations

import importlib.util
import subprocess
import sys
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
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_update_sources_updates_main_then_remote_submodules(monkeypatch) -> None:
    restart = load_restart_script()
    calls: list[str] = []

    monkeypatch.setattr(
        restart, "validate_source_checkout", lambda: calls.append("validate")
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
        "pull-main",
        "update-submodules",
    ]


def test_main_pull_does_not_duplicate_submodule_updates(monkeypatch) -> None:
    restart = load_restart_script()
    commands: list[list[str]] = []
    monkeypatch.setattr(
        restart,
        "run",
        lambda command, **_kwargs: commands.append(command),
    )

    restart.pull_main_branch()

    assert commands == [
        [
            "git",
            "pull",
            "--ff-only",
            "--no-recurse-submodules",
            "origin",
            "main",
        ]
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
            build_timeout=900,
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
    deploy_application.assert_called_once_with(900)


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
            build_timeout=900,
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


def test_deployment_lock_rejects_overlapping_runs(monkeypatch, tmp_path) -> None:
    restart = load_restart_script()
    monkeypatch.setattr(restart, "DEPLOYMENT_LOCK_PATH", tmp_path / "deploy.lock")

    with restart.deployment_lock():
        with pytest.raises(RuntimeError, match="already running"):
            with restart.deployment_lock():
                pytest.fail("overlapping deployment unexpectedly acquired the lock")


def test_deployment_builds_validates_then_restarts(monkeypatch) -> None:
    restart = load_restart_script()
    calls: list[tuple[list[str], dict[str, object]]] = []

    monkeypatch.setattr(restart, "log", lambda _message: None)
    monkeypatch.setattr(restart, "read_memory_info", lambda: None)
    monkeypatch.setattr(
        restart,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    restart.deploy_application(900)

    assert calls == [
        (["docker", "compose", "config", "--quiet"], {}),
        (
            ["docker", "compose", "--progress", "plain", "build", "app"],
            {"timeout": 900},
        ),
        (
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
            {},
        ),
        (["docker", "compose", "up", "-d", "--no-build", "app"], {}),
    ]


def test_low_memory_build_serializes_heavy_stages(monkeypatch) -> None:
    restart = load_restart_script()
    calls: list[tuple[list[str], dict[str, object]]] = []
    messages: list[str] = []
    gibibyte = 1024**3

    monkeypatch.setattr(
        restart,
        "read_memory_info",
        lambda: restart.MemoryInfo(
            total_bytes=int(1.6 * gibibyte),
            available_bytes=400 * 1024**2,
            swap_total_bytes=2 * gibibyte,
            swap_free_bytes=2 * gibibyte,
        ),
    )
    monkeypatch.setattr(restart, "log", messages.append)
    monkeypatch.setattr(
        restart,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    restart.build_application_image(900)

    assert calls == [
        (
            [
                "docker",
                "compose",
                "--progress",
                "plain",
                "build",
                "--build-arg",
                "LOW_MEMORY_BUILD=1",
                "app",
            ],
            {"timeout": 900},
        )
    ]
    assert any("1.6 GiB RAM" in message for message in messages)


def test_memory_info_reads_linux_kibibytes(monkeypatch, tmp_path) -> None:
    restart = load_restart_script()
    meminfo = tmp_path / "meminfo"
    meminfo.write_text(
        "MemTotal:       1647000 kB\n"
        "MemAvailable:    420000 kB\n"
        "SwapTotal:            0 kB\n"
        "SwapFree:             0 kB\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(restart, "MEMINFO_PATH", meminfo)

    memory = restart.read_memory_info()

    assert memory == restart.MemoryInfo(
        total_bytes=1647000 * 1024,
        available_bytes=420000 * 1024,
        swap_total_bytes=0,
        swap_free_bytes=0,
    )
    assert restart.low_memory_build_required(memory) is True


def test_low_memory_build_without_swap_fails_before_docker(monkeypatch) -> None:
    restart = load_restart_script()
    run = Mock()
    gibibyte = 1024**3
    monkeypatch.setattr(
        restart,
        "read_memory_info",
        lambda: restart.MemoryInfo(
            total_bytes=int(1.6 * gibibyte),
            available_bytes=400 * 1024**2,
            swap_total_bytes=0,
            swap_free_bytes=0,
        ),
    )
    monkeypatch.setattr(restart, "run", run)

    with pytest.raises(RuntimeError, match="Add swap before"):
        restart.build_application_image(900)

    run.assert_not_called()


def test_build_timeout_keeps_current_application_image(monkeypatch) -> None:
    restart = load_restart_script()
    monkeypatch.setattr(restart, "read_memory_info", lambda: None)

    def run(command: list[str], **_kwargs) -> None:
        raise subprocess.TimeoutExpired(command, 900)

    monkeypatch.setattr(restart, "run", run)

    with pytest.raises(
        RuntimeError,
        match="current application container was not replaced",
    ):
        restart.build_application_image(900)


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
        restart.deploy_application(900)

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
    assert (
        "FROM douzero-runtime-${ENABLE_DOUZERO_AI} AS application-runtime"
        in dockerfile
    )
    assert "FROM application-runtime AS runtime" in dockerfile
    assert "COPY --from=pikafish-bundle /bundle/ /" in dockerfile
    assert "COPY --from=katago-bundle /bundle/ /" in dockerfile
    assert "python /tmp/douzero_models.py" in dockerfile
    assert "/tmp/douzero-models --output /bundle" in dockerfile
    assert "COPY --from=douzero-model-bundle" in dockerfile
    assert "/bundle/ /opt/game-hall/ai/douzero/" in dockerfile
    assert "--model-dir /opt/game-hall/ai/douzero --threads 1 --check" in dockerfile
    dependency_manifest = dockerfile.index("COPY backend/pyproject.toml")
    heavy_dependency_install = dockerfile.index("'torch>=2.6,<3'")
    application_source = dockerfile.index(
        "COPY backend/ ./backend/",
        heavy_dependency_install,
    )
    assert dependency_manifest < heavy_dependency_install < application_source
    assert dockerfile.count("COPY backend/ ./backend/") == 1
    assert "ARG LOW_MEMORY_BUILD=0" in dockerfile
    assert "FROM application-runtime AS web-build-gate-1" in dockerfile
    assert "FROM web-build-gate-${LOW_MEMORY_BUILD} AS web-build-gate" in dockerfile
    assert "COPY --from=web-build-gate /build-gate" in dockerfile
    assert "NODE_OPTIONS=--max-old-space-size=768" in dockerfile
    assert "INSTALL_DOUZERO_AI" not in dockerfile + compose + environment_example
    assert "DOUZERO_MODEL_HOST_DIR" not in compose


def test_docker_build_context_excludes_runtime_data_and_secrets() -> None:
    dockerignore = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8")
    ignored_paths = set(dockerignore.splitlines())

    assert {".env", ".env.*", "backups", "logs"} <= ignored_paths
    assert "!.env.example" in ignored_paths
