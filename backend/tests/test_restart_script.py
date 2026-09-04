from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from backend.app.ai.douzero_models import require_model_paths


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


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


def ingress_module(restart: ModuleType) -> ModuleType:
    return sys.modules[restart.https_responds.__module__]


def test_update_sources_updates_main_then_remote_submodules(monkeypatch) -> None:
    restart = load_restart_script()
    calls: list[str] = []
    revisions = iter(["before", "after"])

    monkeypatch.setattr(
        restart, "validate_source_checkout", lambda: calls.append("validate")
    )
    monkeypatch.setattr(restart, "pull_main_branch", lambda: calls.append("pull-main"))
    monkeypatch.setattr(
        restart,
        "update_submodules_from_remotes",
        lambda: calls.append("update-submodules"),
    )
    monkeypatch.setattr(restart, "repository_revision", lambda: next(revisions))

    assert restart.update_sources() is True

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


def test_updated_main_restarts_the_same_entrypoint_without_pulling_again(
    monkeypatch,
) -> None:
    restart = load_restart_script()
    execv = Mock()
    args = SimpleNamespace(build_timeout=1800, timeout=90)
    entrypoint = str((PROJECT_ROOT / "scripts" / "deploy_low_memory.py").resolve())
    monkeypatch.setattr(restart.sys, "argv", [entrypoint])
    monkeypatch.setattr(restart.os, "execv", execv)
    monkeypatch.setattr(restart, "log", lambda _message: None)

    restart.reexec_updated_entrypoint(args)

    execv.assert_called_once_with(
        restart.sys.executable,
        [
            restart.sys.executable,
            entrypoint,
            "--no-pull",
            "--build-timeout",
            "1800",
            "--timeout",
            "90",
        ],
    )


def test_main_reexecs_updated_code_before_deployment(monkeypatch) -> None:
    restart = load_restart_script()
    deploy_application = Mock()
    reexec_updated_entrypoint = Mock()
    args = SimpleNamespace(
        no_pull=False,
        restart_only=False,
        build_timeout=900,
        timeout=120,
    )
    monkeypatch.setattr(restart, "parse_args", lambda: args)
    monkeypatch.setattr(restart, "validate_environment", lambda: None)
    monkeypatch.setattr(restart, "load_ingress_config", lambda: restart.HTTP_INGRESS)
    monkeypatch.setattr(restart, "validate_ingress_environment", lambda _config: None)
    monkeypatch.setattr(restart, "update_sources", lambda: True)
    monkeypatch.setattr(restart, "reexec_updated_entrypoint", reexec_updated_entrypoint)
    monkeypatch.setattr(restart, "deploy_application", deploy_application)

    assert restart.main() == 0
    reexec_updated_entrypoint.assert_called_once_with(args)
    deploy_application.assert_not_called()


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
    monkeypatch.setattr(restart, "load_ingress_config", lambda: restart.HTTP_INGRESS)
    monkeypatch.setattr(restart, "validate_ingress_environment", lambda _config: None)
    monkeypatch.setattr(restart, "update_sources", update_sources)
    monkeypatch.setattr(restart, "deploy_application", deploy_application)
    monkeypatch.setattr(
        restart,
        "wait_until_healthy",
        lambda _timeout, _ingress: None,
    )
    monkeypatch.setattr(restart, "log", lambda _message: None)

    assert restart.main() == 0
    update_sources.assert_not_called()
    deploy_application.assert_called_once_with(
        900,
        health_timeout=120,
        build_profile=restart.VERIFIED_BUILD_PROFILE,
        ingress=restart.HTTP_INGRESS,
    )


def test_restart_only_skips_source_updates_and_deployment(monkeypatch) -> None:
    restart = load_restart_script()
    update_sources = Mock()
    deploy_application = Mock()
    restart_application = Mock()

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
    monkeypatch.setattr(restart, "load_ingress_config", lambda: restart.HTTP_INGRESS)
    monkeypatch.setattr(restart, "validate_ingress_environment", lambda _config: None)
    monkeypatch.setattr(restart, "update_sources", update_sources)
    monkeypatch.setattr(restart, "deploy_application", deploy_application)
    monkeypatch.setattr(
        restart,
        "restart_application",
        restart_application,
    )

    assert restart.main() == 0
    update_sources.assert_not_called()
    deploy_application.assert_not_called()
    restart_application.assert_called_once_with(
        restart.HTTP_INGRESS,
        timeout=45,
    )


def test_restart_only_and_no_pull_are_mutually_exclusive() -> None:
    restart = load_restart_script()

    with pytest.raises(SystemExit):
        restart.parse_args(["--restart-only", "--no-pull"])


def test_http_activation_removes_https_then_recreates_app(monkeypatch) -> None:
    restart = load_restart_script()
    commands: list[list[str]] = []

    monkeypatch.setattr(restart, "log", lambda _message: None)
    monkeypatch.setattr(
        restart,
        "run",
        lambda command, **_kwargs: commands.append(command),
    )

    restart.activate_runtime(restart.HTTP_INGRESS, restart_only=True)

    assert commands == [
        restart.compose_command(
            restart.HTTPS_COMPOSE_LAYOUT,
            "rm",
            "--stop",
            "--force",
            "caddy",
        ),
        restart.compose_command(
            restart.HTTP_INGRESS,
            "up",
            "-d",
            "--no-build",
            "--no-deps",
            "--force-recreate",
            "app",
        ),
    ]


def test_https_ingress_config_is_loaded_from_dotenv(monkeypatch, tmp_path) -> None:
    restart = load_restart_script()
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "HTTPS_ENABLED=1\n"
        "HTTPS_DOMAIN=DepartedSpirit.com.\n"
        "HTTPS_BACKEND_PORT=12000\n",
        encoding="utf-8",
    )
    for setting in (
        "AVALON_PORT",
        "GAME_HALL_BIND_HOST",
        "GAME_HALL_PORT",
        "HTTPS_ENABLED",
        "HTTPS_DOMAIN",
        "HTTPS_BACKEND_PORT",
    ):
        monkeypatch.delenv(setting, raising=False)

    assert restart.load_ingress_config(dotenv) == restart.IngressConfig(
        https_enabled=True,
        app_host_port=12000,
        bind_host="127.0.0.1",
        domain="departedspirit.com",
    )


def test_http_ingress_preserves_the_direct_bind_address(monkeypatch, tmp_path) -> None:
    restart = load_restart_script()
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "HTTPS_ENABLED=0\n"
        "GAME_HALL_BIND_HOST=127.0.0.1\n"
        "GAME_HALL_PORT=8080\n",
        encoding="utf-8",
    )
    for setting in (
        "AVALON_PORT",
        "GAME_HALL_BIND_HOST",
        "GAME_HALL_PORT",
        "HTTPS_ENABLED",
    ):
        monkeypatch.delenv(setting, raising=False)

    assert restart.load_ingress_config(dotenv) == restart.IngressConfig(
        https_enabled=False,
        app_host_port=8080,
        bind_host="127.0.0.1",
    )


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("HTTPS_ENABLED=yes\n", "HTTPS_ENABLED must be 0 or 1"),
        (
            "HTTPS_ENABLED=1\nHTTPS_DOMAIN=https://example.com\n",
            "without a scheme",
        ),
        (
            "HTTPS_ENABLED=1\nHTTPS_DOMAIN=127.0.0.1\n",
            "not an IP address",
        ),
        (
            "HTTPS_ENABLED=1\nHTTPS_DOMAIN=example.com\nHTTPS_BACKEND_PORT=443\n",
            "cannot be 80 or 443",
        ),
    ],
)
def test_invalid_https_ingress_config_fails(
    monkeypatch,
    tmp_path,
    contents: str,
    message: str,
) -> None:
    restart = load_restart_script()
    dotenv = tmp_path / ".env"
    dotenv.write_text(contents, encoding="utf-8")
    for setting in (
        "AVALON_PORT",
        "GAME_HALL_BIND_HOST",
        "GAME_HALL_PORT",
        "HTTPS_ENABLED",
        "HTTPS_DOMAIN",
        "HTTPS_BACKEND_PORT",
    ):
        monkeypatch.delenv(setting, raising=False)

    with pytest.raises(RuntimeError, match=message):
        restart.load_ingress_config(dotenv)


def test_https_restart_recreates_private_app_then_caddy(monkeypatch) -> None:
    restart = load_restart_script()
    calls: list[tuple[list[str], dict[str, object]]] = []
    ingress = restart.IngressConfig(
        https_enabled=True,
        app_host_port=10618,
        bind_host="127.0.0.1",
        domain="departedspirit.com",
    )

    monkeypatch.setattr(restart, "log", lambda _message: None)
    monkeypatch.setattr(
        restart,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    restart.activate_runtime(ingress, restart_only=True)

    assert [call[0][-1] for call in calls] == ["app", "caddy"]
    for command, options in calls:
        prefix = restart.compose_command(ingress)
        assert command[: len(prefix)] == prefix
        assert command[len(prefix) :] == [
            "up",
            "-d",
            "--no-build",
            "--no-deps",
            "--force-recreate",
            command[-1],
        ]
        environment = options["env"]
        assert isinstance(environment, dict)
        assert environment["HTTPS_BACKEND_PORT"] == "10618"
        assert environment["HTTPS_DOMAIN"] == "departedspirit.com"


def test_https_preflight_validates_caddy_before_runtime_switch(monkeypatch) -> None:
    restart = load_restart_script()
    ingress = restart.IngressConfig(
        https_enabled=True,
        app_host_port=10618,
        bind_host="127.0.0.1",
        domain="departedspirit.com",
    )
    commands: list[list[str]] = []
    monkeypatch.setattr(restart, "validate_ingress_environment", lambda _config: None)
    monkeypatch.setattr(restart, "log", lambda _message: None)
    monkeypatch.setattr(
        restart,
        "run",
        lambda command, **_kwargs: commands.append(command),
    )

    restart.prepare_ingress(ingress)

    assert commands == [
        restart.compose_command(ingress, "config", "--quiet"),
        restart.compose_command(
            ingress,
            "run",
            "--rm",
            "--no-deps",
            "--entrypoint",
            "caddy",
            "caddy",
            "validate",
            "--config",
            "/etc/caddy/Caddyfile",
        ),
    ]


def test_failed_https_switch_restores_previous_http_ingress(monkeypatch) -> None:
    restart = load_restart_script()
    target = restart.IngressConfig(
        https_enabled=True,
        app_host_port=10618,
        bind_host="127.0.0.1",
        domain="departedspirit.com",
    )
    previous = restart.IngressConfig(
        https_enabled=False,
        app_host_port=80,
        bind_host="0.0.0.0",
    )
    activations: list[tuple[object, bool]] = []
    health_checks: list[object] = []

    monkeypatch.setattr(restart, "log", lambda _message: None)
    monkeypatch.setattr(
        restart,
        "activate_runtime",
        lambda ingress, *, restart_only: activations.append(
            (ingress, restart_only)
        ),
    )

    def wait_until_healthy(_timeout, ingress) -> None:
        health_checks.append(ingress)
        if ingress == target:
            raise RuntimeError("TLS endpoint failed")

    monkeypatch.setattr(restart, "wait_until_healthy", wait_until_healthy)

    with pytest.raises(RuntimeError, match="TLS endpoint failed"):
        restart.replace_runtime(
            target,
            timeout=30,
            restart_only=True,
            previous_ingress=previous,
        )

    assert activations == [(target, True), (previous, True)]
    assert health_checks == [target, previous]


def test_running_https_snapshot_uses_actual_domain_and_backend_port(
    monkeypatch,
) -> None:
    restart = load_restart_script()
    inspections = {
        restart.APPLICATION_CONTAINER: {
            "NetworkSettings": {
                "Ports": {
                    "8000/tcp": [
                        {"HostIp": "127.0.0.1", "HostPort": "12000"}
                    ]
                }
            }
        },
        restart.HTTPS_CONTAINER: {
            "State": {"Running": True},
            "Config": {"Env": ["HTTPS_DOMAIN=DepartedSpirit.com."]},
        },
    }
    monkeypatch.setattr(
        restart,
        "inspect_container",
        lambda container: inspections.get(container),
    )

    assert restart.detect_running_ingress(restart.HTTP_INGRESS) == (
        restart.IngressConfig(
            https_enabled=True,
            app_host_port=12000,
            bind_host="127.0.0.1",
            domain="departedspirit.com",
        )
    )


def test_https_compose_service_persists_certificates() -> None:
    compose = (PROJECT_ROOT / "compose.yaml").read_text(encoding="utf-8")
    http = (PROJECT_ROOT / "compose.override.yaml").read_text(encoding="utf-8")
    https = (PROJECT_ROOT / "compose.https.yaml").read_text(encoding="utf-8")
    caddyfile = (PROJECT_ROOT / "Caddyfile").read_text(encoding="utf-8")

    assert "caddy:" not in compose
    assert "ports:" not in compose.split("  app:", 1)[1]
    assert '${GAME_HALL_BIND_HOST:-0.0.0.0}' in http
    assert "caddy:2.11.4-alpine" in https
    assert "127.0.0.1:${HTTPS_BACKEND_PORT:-10618}:8000" in https
    assert "./Caddyfile:/etc/caddy/Caddyfile:ro" in https
    assert "caddy-data:/data" in https
    assert "caddy-config:/config" in https
    assert "{$HTTPS_DOMAIN}" in caddyfile
    assert "reverse_proxy app:8000" in caddyfile


def test_https_probe_validates_tls_and_proxy_response(monkeypatch) -> None:
    restart = load_restart_script()
    ingress_runtime = ingress_module(restart)
    config = restart.IngressConfig(
        https_enabled=True,
        domain="departedspirit.com",
    )
    raw_socket = MagicMock()
    raw_socket.__enter__.return_value = raw_socket
    secure_socket = MagicMock()
    secure_socket.__enter__.return_value = secure_socket
    response = MagicMock()
    response.__enter__.return_value = response
    response.readline.return_value = b"HTTP/1.1 200 OK\r\n"
    secure_socket.makefile.return_value = response
    tls_context = MagicMock()
    tls_context.wrap_socket.return_value = secure_socket

    monkeypatch.setattr(
        ingress_runtime.socket,
        "create_connection",
        lambda address, timeout: raw_socket,
    )
    monkeypatch.setattr(
        ingress_runtime.ssl,
        "create_default_context",
        lambda: tls_context,
    )

    assert restart.https_responds(config) is True
    tls_context.wrap_socket.assert_called_once_with(
        raw_socket,
        server_hostname="departedspirit.com",
    )
    secure_socket.sendall.assert_called_once()


def test_https_probe_retries_certificate_failures(monkeypatch) -> None:
    restart = load_restart_script()
    ingress_runtime = ingress_module(restart)
    config = restart.IngressConfig(
        https_enabled=True,
        domain="departedspirit.com",
    )

    def fail_connection(_address, timeout):
        assert timeout == 3
        raise OSError("certificate endpoint is not ready")

    monkeypatch.setattr(
        ingress_runtime.socket,
        "create_connection",
        fail_connection,
    )

    assert restart.https_responds(config) is False


def test_deployment_lock_rejects_overlapping_runs(monkeypatch, tmp_path) -> None:
    restart = load_restart_script()
    monkeypatch.setattr(restart, "DEPLOYMENT_LOCK_PATH", tmp_path / "deploy.lock")

    with restart.deployment_lock():
        with pytest.raises(RuntimeError, match="already running"):
            with restart.deployment_lock():
                pytest.fail("overlapping deployment unexpectedly acquired the lock")


def test_deployment_builds_validates_then_restarts(monkeypatch) -> None:
    restart = load_restart_script()
    calls: list[str] = []
    monkeypatch.setattr(
        restart,
        "prepare_ingress",
        lambda _ingress: calls.append("prepare"),
    )
    monkeypatch.setattr(
        restart,
        "detect_running_ingress",
        lambda _ingress: calls.append("detect") or restart.HTTP_INGRESS,
    )
    monkeypatch.setattr(
        restart,
        "build_application_image",
        lambda *_args, **_kwargs: calls.append("build"),
    )
    monkeypatch.setattr(
        restart,
        "validate_application_image",
        lambda _ingress: calls.append("validate"),
    )
    monkeypatch.setattr(
        restart,
        "replace_runtime",
        lambda *_args, **_kwargs: calls.append("replace"),
    )

    restart.deploy_application(900)

    assert calls == ["prepare", "detect", "build", "validate", "replace"]


def test_low_memory_deployment_suspends_runtime_services(monkeypatch) -> None:
    restart = load_restart_script()
    commands: list[list[str]] = []

    monkeypatch.setattr(restart, "log", lambda _message: None)
    monkeypatch.setattr(restart, "prepare_ingress", lambda _ingress: None)
    monkeypatch.setattr(
        restart,
        "detect_running_ingress",
        lambda _ingress: restart.HTTP_INGRESS,
    )
    monkeypatch.setattr(restart, "build_application_image", lambda *_a, **_k: None)
    monkeypatch.setattr(restart, "validate_application_image", lambda _ingress: None)
    monkeypatch.setattr(restart, "replace_runtime", lambda *_a, **_k: None)
    monkeypatch.setattr(
        restart,
        "run",
        lambda command, **_kwargs: commands.append(command),
    )

    restart.deploy_application(
        900,
        build_profile=restart.LOW_MEMORY_BUILD_PROFILE,
    )

    assert commands == [
        restart.compose_command(
            restart.HTTP_INGRESS,
            "stop",
            "--timeout",
            "30",
            "app",
            "mysql",
            "redis",
        )
    ]


def test_low_memory_deployment_restores_services_after_failure(monkeypatch) -> None:
    restart = load_restart_script()
    commands: list[list[str]] = []

    monkeypatch.setattr(restart, "log", lambda _message: None)
    monkeypatch.setattr(restart, "prepare_ingress", lambda _ingress: None)
    monkeypatch.setattr(
        restart,
        "detect_running_ingress",
        lambda _ingress: restart.HTTP_INGRESS,
    )
    monkeypatch.setattr(
        restart,
        "build_application_image",
        Mock(side_effect=subprocess.CalledProcessError(1, ["build"])),
    )

    def run(command: list[str], **_kwargs) -> None:
        commands.append(command)

    monkeypatch.setattr(restart, "run", run)

    with pytest.raises(subprocess.CalledProcessError):
        restart.deploy_application(
            900,
            build_profile=restart.LOW_MEMORY_BUILD_PROFILE,
        )

    assert commands[-1] == restart.compose_command(
        restart.HTTP_INGRESS,
        "start",
        "mysql",
        "redis",
        "app",
    )
    assert not any("up" in command for command in commands)


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

    assert len(calls) == 1
    command, options = calls[0]
    assert command == restart.compose_command(
        restart.HTTP_INGRESS,
        "--progress",
        "plain",
        "build",
        "--build-arg",
        "LOW_MEMORY_BUILD=1",
        "app",
    )
    assert options["timeout"] == 900
    assert any("1.6 GiB RAM" in message for message in messages)


def test_low_memory_profile_builds_runtime_assets_with_a_smaller_heap(
    monkeypatch,
) -> None:
    restart = load_restart_script()
    calls: list[tuple[list[str], dict[str, object]]] = []
    messages: list[str] = []

    monkeypatch.setattr(restart, "read_memory_info", lambda: None)
    monkeypatch.setattr(restart, "log", messages.append)
    monkeypatch.setattr(
        restart,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    restart.build_application_image(
        900,
        build_profile=restart.LOW_MEMORY_BUILD_PROFILE,
    )

    assert len(calls) == 1
    command, options = calls[0]
    assert command == restart.compose_command(
        restart.HTTP_INGRESS,
        "--progress",
        "plain",
        "build",
        "--build-arg",
        "LOW_MEMORY_BUILD=1",
        "--build-arg",
        "FRONTEND_BUILD_VALIDATION=0",
        "app",
    )
    assert options["timeout"] == 900
    assert any("Runtime frontend build enabled" in message for message in messages)


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
    replace_runtime = Mock()
    monkeypatch.setattr(restart, "prepare_ingress", lambda _ingress: None)
    monkeypatch.setattr(
        restart,
        "detect_running_ingress",
        lambda _ingress: restart.HTTP_INGRESS,
    )
    monkeypatch.setattr(restart, "build_application_image", lambda *_a, **_k: None)
    monkeypatch.setattr(
        restart,
        "validate_application_image",
        Mock(side_effect=subprocess.CalledProcessError(1, ["validate"])),
    )
    monkeypatch.setattr(restart, "replace_runtime", replace_runtime)

    with pytest.raises(subprocess.CalledProcessError):
        restart.deploy_application(900)

    replace_runtime.assert_not_called()


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
    assert "ARG FRONTEND_BUILD_VALIDATION=1" in dockerfile
    assert "NODE_OPTIONS=--max-old-space-size=256" in dockerfile
    assert "frontend_build=build:assets" in dockerfile
    assert "INSTALL_DOUZERO_AI" not in dockerfile + compose + environment_example
    assert "DOUZERO_MODEL_HOST_DIR" not in compose


def test_docker_build_context_excludes_runtime_data_and_secrets() -> None:
    dockerignore = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8")
    ignored_paths = set(dockerignore.splitlines())

    assert {".env", ".env.*", "backups", "logs"} <= ignored_paths
    assert "!.env.example" in ignored_paths


def test_low_memory_entrypoint_reuses_the_restart_deployer() -> None:
    entrypoint = (PROJECT_ROOT / "scripts" / "deploy_low_memory.py").read_text(
        encoding="utf-8"
    )
    frontend_package = (PROJECT_ROOT / "frontend" / "package.json").read_text(
        encoding="utf-8"
    )

    assert "LOW_MEMORY_BUILD_PROFILE" in entrypoint
    assert "run_cli(build_profile=LOW_MEMORY_BUILD_PROFILE)" in entrypoint
    assert '"build:assets": "npm run plugins:sync && vite build"' in frontend_package
