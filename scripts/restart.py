#!/usr/bin/env python3

from __future__ import annotations

import argparse
import fcntl
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from pathlib import Path

from ingress import (
    APPLICATION_CONTAINER,
    APPLICATION_SERVICE,
    CADDYFILE_PATH,
    HTTP_INGRESS,
    HTTPS_COMPOSE_LAYOUT,
    HTTPS_CONTAINER,
    HTTPS_SERVICE,
    IngressConfig,
    compose_command,
    compose_environment,
    container_environment,
    container_is_running,
    https_responds,
    load_ingress_config,
    normalize_public_domain,
    parse_container_inspection,
    published_app_binding as parse_published_app_binding,
)


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_HEALTH_TIMEOUT = 120
DEFAULT_BUILD_TIMEOUT = 30 * 60
BUILD_HEARTBEAT_INTERVAL = 30
LOW_MEMORY_BUILD_THRESHOLD_BYTES = 2 * 1024**3
MINIMUM_LOW_MEMORY_SWAP_BYTES = 1024**3
DEPLOY_BRANCH = "main"
PLUGIN_VALIDATION_MODULE = "backend.app.games.validate_plugins"
DEPLOYMENT_LOCK_PATH = Path(tempfile.gettempdir()) / (
    "game-hall-deploy-"
    f"{hashlib.sha256(str(PROJECT_DIR).encode()).hexdigest()[:12]}.lock"
)
MEMINFO_PATH = Path("/proc/meminfo")


@dataclass(frozen=True)
class BuildProfile:
    name: str
    force_serial_stages: bool
    validate_frontend: bool
    suspend_runtime_services: bool


VERIFIED_BUILD_PROFILE = BuildProfile(
    name="verified",
    force_serial_stages=False,
    validate_frontend=True,
    suspend_runtime_services=False,
)
LOW_MEMORY_BUILD_PROFILE = BuildProfile(
    name="low-memory",
    force_serial_stages=True,
    validate_frontend=False,
    suspend_runtime_services=True,
)


@dataclass(frozen=True)
class MemoryInfo:
    total_bytes: int
    available_bytes: int
    swap_total_bytes: int
    swap_free_bytes: int


def positive_integer(raw_value: str) -> int:
    try:
        value = int(raw_value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deploy or restart the game hall with Docker Compose.",
    )
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument(
        "--no-pull",
        action="store_true",
        help="skip Git updates and rebuild the currently checked-out code",
    )
    operation.add_argument(
        "--restart-only",
        action="store_true",
        help="restart the existing application container without pulling or building",
    )
    parser.add_argument(
        "--build-timeout",
        type=positive_integer,
        default=DEFAULT_BUILD_TIMEOUT,
        metavar="SECONDS",
        help=f"image-build timeout (default: {DEFAULT_BUILD_TIMEOUT})",
    )
    parser.add_argument(
        "--timeout",
        type=positive_integer,
        default=DEFAULT_HEALTH_TIMEOUT,
        metavar="SECONDS",
        help=f"health-check timeout (default: {DEFAULT_HEALTH_TIMEOUT})",
    )
    return parser.parse_args(argv)


def log(message: str) -> None:
    print(f"\n==> {message}", flush=True)


def fail(message: str) -> None:
    raise RuntimeError(message)


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, remaining_seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {remaining_seconds:.0f}s"


def format_memory(size_bytes: int) -> str:
    return f"{size_bytes / 1024**3:.1f} GiB"


def read_memory_info() -> MemoryInfo | None:
    try:
        lines = MEMINFO_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    values: dict[str, int] = {}
    for line in lines:
        key, separator, raw_value = line.partition(":")
        if not separator:
            continue
        fields = raw_value.split()
        if not fields or not fields[0].isdigit():
            continue
        values[key] = int(fields[0]) * 1024

    total_bytes = values.get("MemTotal")
    if total_bytes is None:
        return None
    return MemoryInfo(
        total_bytes=total_bytes,
        available_bytes=values.get("MemAvailable", 0),
        swap_total_bytes=values.get("SwapTotal", 0),
        swap_free_bytes=values.get("SwapFree", 0),
    )


def low_memory_build_required(memory: MemoryInfo | None) -> bool:
    return (
        memory is not None
        and memory.total_bytes < LOW_MEMORY_BUILD_THRESHOLD_BYTES
    )


def validate_build_memory(memory: MemoryInfo | None) -> None:
    if (
        low_memory_build_required(memory)
        and memory is not None
        and memory.swap_free_bytes < MINIMUM_LOW_MEMORY_SWAP_BYTES
    ):
        raise RuntimeError(
            "Low-memory deployments require at least "
            f"{format_memory(MINIMUM_LOW_MEMORY_SWAP_BYTES)} of free swap; "
            f"detected {format_memory(memory.total_bytes)} RAM and "
            f"{format_memory(memory.available_bytes)} available memory with "
            f"{format_memory(memory.swap_free_bytes)} free swap. Add swap before "
            "running a full deployment; --restart-only remains available."
        )


@contextmanager
def timed_phase(message: str) -> Iterator[None]:
    log(message)
    started_at = time.monotonic()
    try:
        yield
    except BaseException:
        elapsed = format_duration(time.monotonic() - started_at)
        print(f"    failed after {elapsed}", flush=True)
        raise
    elapsed = format_duration(time.monotonic() - started_at)
    print(f"    completed in {elapsed}", flush=True)


@contextmanager
def progress_heartbeat(
    message: str,
    *,
    interval: int = BUILD_HEARTBEAT_INTERVAL,
) -> Iterator[None]:
    stopped = threading.Event()
    started_at = time.monotonic()

    def report_progress() -> None:
        while not stopped.wait(interval):
            elapsed = format_duration(time.monotonic() - started_at)
            print(f"    {message} ({elapsed} elapsed)", flush=True)

    reporter = threading.Thread(target=report_progress, daemon=True)
    reporter.start()
    try:
        yield
    finally:
        stopped.set()
        reporter.join()


@contextmanager
def deployment_lock() -> Iterator[None]:
    with DEPLOYMENT_LOCK_PATH.open("a+", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            lock_file.seek(0)
            owner_pid = lock_file.read().strip()
            owner = f" (process {owner_pid})" if owner_pid else ""
            raise RuntimeError(
                "Another game hall deployment or restart is already running"
                f"{owner}"
            ) from error
        lock_file.seek(0)
        lock_file.truncate()
        lock_file.write(f"{os.getpid()}\n")
        lock_file.flush()
        yield


def run(
    command: list[str],
    *,
    capture_output: bool = False,
    check: bool = True,
    env: Mapping[str, str] | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_DIR,
        check=check,
        capture_output=capture_output,
        env=env,
        text=True,
        timeout=timeout,
    )


def run_compose(
    ingress: IngressConfig,
    *arguments: str,
    capture_output: bool = False,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return run(
        compose_command(ingress, *arguments),
        capture_output=capture_output,
        check=check,
        env=compose_environment(ingress),
        timeout=timeout,
    )


def require_command(command: str, message: str) -> None:
    if shutil.which(command) is None:
        fail(message)


def validate_environment() -> None:
    require_command("docker", "Docker is not installed or is not in PATH")

    if not (PROJECT_DIR / ".env").is_file():
        fail(".env was not found; copy .env.example to .env and configure it first")

    try:
        run(["docker", "compose", "version"], capture_output=True)
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Docker Compose v2 is unavailable") from error

    try:
        run(["docker", "info"], capture_output=True)
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "Docker daemon is not running or is not accessible"
        ) from error


def validate_ingress_environment(ingress: IngressConfig) -> None:
    for compose_file in ingress.compose_files:
        if not compose_file.is_file():
            fail(f"{compose_file.name} was not found in {PROJECT_DIR}")
    if ingress.https_enabled and not CADDYFILE_PATH.is_file():
        fail("Caddyfile is required when HTTPS_ENABLED=1")


def validate_source_checkout() -> None:
    require_command("git", "Git is not installed or is not in PATH")
    checkout = run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        check=False,
    )
    if checkout.returncode != 0 or checkout.stdout.strip() != "true":
        fail(f"{PROJECT_DIR} is not a Git checkout")

    status = run(
        [
            "git",
            "status",
            "--porcelain",
            "--untracked-files=no",
            "--ignore-submodules=all",
        ],
        capture_output=True,
    ).stdout
    if status.strip():
        fail("Git working tree is not clean; commit or stash tracked changes first")

    branch = run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
    ).stdout.strip()
    if branch != DEPLOY_BRANCH:
        fail(
            f"restart deployments must run from branch {DEPLOY_BRANCH!r}; "
            f"current branch is {branch!r}"
        )


def pull_main_branch() -> None:
    with timed_phase(f"Updating the main repository from origin/{DEPLOY_BRANCH}"):
        run(
            [
                "git",
                "pull",
                "--ff-only",
                "--no-recurse-submodules",
                "origin",
                DEPLOY_BRANCH,
            ]
        )


def repository_revision() -> str:
    return run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
    ).stdout.strip()


def update_submodules_from_remotes() -> None:
    if not (PROJECT_DIR / ".gitmodules").is_file():
        return
    log("Updating Git submodules from their configured remote branches")
    run(["git", "submodule", "sync", "--recursive"])
    run(
        [
            "git",
            "submodule",
            "update",
            "--init",
            "--remote",
            "--recursive",
            "--checkout",
        ]
    )


def update_sources() -> bool:
    validate_source_checkout()
    previous_revision = repository_revision()
    pull_main_branch()
    update_submodules_from_remotes()
    return repository_revision() != previous_revision


def reexec_updated_entrypoint(args: argparse.Namespace) -> None:
    entrypoint = Path(sys.argv[0]).resolve()
    log("Restarting the deployment command with the updated source code")
    os.execv(
        sys.executable,
        [
            sys.executable,
            str(entrypoint),
            "--no-pull",
            "--build-timeout",
            str(args.build_timeout),
            "--timeout",
            str(args.timeout),
        ],
    )


def build_application_image(
    timeout: int,
    *,
    build_profile: BuildProfile = VERIFIED_BUILD_PROFILE,
    ingress: IngressConfig = HTTP_INGRESS,
) -> None:
    memory = read_memory_info()
    validate_build_memory(memory)
    low_memory_build = (
        build_profile.force_serial_stages
        or low_memory_build_required(memory)
    )
    arguments = [
        "--progress",
        "plain",
        "build",
    ]
    if low_memory_build:
        if memory is None:
            memory_summary = "memory information unavailable"
        else:
            memory_summary = (
                f"{format_memory(memory.total_bytes)} RAM, "
                f"{format_memory(memory.available_bytes)} available, "
                f"{format_memory(memory.swap_total_bytes)} swap"
            )
        log(
            f"Serial low-memory image build enabled ({memory_summary})"
        )
        arguments.extend(["--build-arg", "LOW_MEMORY_BUILD=1"])
    if not build_profile.validate_frontend:
        log(
            "Runtime frontend build enabled; full type, icon, and theme "
            "validation remains available through the standard build"
        )
        arguments.extend(
            ["--build-arg", "FRONTEND_BUILD_VALIDATION=0"]
        )
    arguments.append(APPLICATION_SERVICE)

    with timed_phase("Building the game hall application image"):
        try:
            with progress_heartbeat("Docker image build is still running"):
                run_compose(ingress, *arguments, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(
                "Application image build exceeded "
                f"{format_duration(timeout)}; the current application container "
                "was not replaced"
            ) from error


def validate_application_image(ingress: IngressConfig = HTTP_INGRESS) -> None:
    with timed_phase(
        "Validating the community game release registry and published plugins"
    ):
        run_compose(
            ingress,
            "run",
            "--rm",
            "--no-deps",
            APPLICATION_SERVICE,
            "python",
            "-m",
            PLUGIN_VALIDATION_MODULE,
        )


def remove_https_proxy() -> None:
    run_compose(
        HTTPS_COMPOSE_LAYOUT,
        "rm",
        "--stop",
        "--force",
        HTTPS_SERVICE,
        check=False,
    )


def inspect_container(container: str) -> dict[str, object] | None:
    result = run(
        ["docker", "inspect", container],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return parse_container_inspection(result.stdout)


def published_app_binding() -> tuple[str, int] | None:
    return parse_published_app_binding(inspect_container(APPLICATION_CONTAINER))


def detect_running_ingress(target: IngressConfig) -> IngressConfig:
    binding = published_app_binding()
    bind_host, app_host_port = binding or (
        target.bind_host,
        target.app_host_port,
    )
    caddy = inspect_container(HTTPS_CONTAINER)
    if not container_is_running(caddy):
        return IngressConfig(
            https_enabled=False,
            app_host_port=app_host_port,
            bind_host=bind_host,
        )

    environment = container_environment(caddy)
    domain = environment.get("HTTPS_DOMAIN") or target.domain
    if domain is None:
        fail("Cannot determine the domain used by the running HTTPS proxy")
    return IngressConfig(
        https_enabled=True,
        app_host_port=app_host_port,
        bind_host="127.0.0.1",
        domain=normalize_public_domain(domain),
    )


def prepare_ingress(ingress: IngressConfig) -> None:
    validate_ingress_environment(ingress)
    with timed_phase("Validating the selected HTTP/HTTPS ingress"):
        run_compose(ingress, "config", "--quiet")
        if ingress.https_enabled:
            run_compose(
                ingress,
                "run",
                "--rm",
                "--no-deps",
                "--entrypoint",
                "caddy",
                HTTPS_SERVICE,
                "validate",
                "--config",
                "/etc/caddy/Caddyfile",
            )


def activate_runtime(ingress: IngressConfig, *, restart_only: bool) -> None:
    if not ingress.https_enabled:
        remove_https_proxy()

    if restart_only:
        run_compose(
            ingress,
            "up",
            "-d",
            "--no-build",
            "--no-deps",
            "--force-recreate",
            APPLICATION_SERVICE,
        )
        if ingress.https_enabled:
            run_compose(
                ingress,
                "up",
                "-d",
                "--no-build",
                "--no-deps",
                "--force-recreate",
                HTTPS_SERVICE,
            )
        return

    run_compose(
        ingress,
        "up",
        "-d",
        "--no-build",
        *ingress.services,
    )


def replace_runtime(
    ingress: IngressConfig,
    *,
    timeout: int,
    restart_only: bool,
    previous_ingress: IngressConfig | None = None,
) -> None:
    previous = previous_ingress or detect_running_ingress(ingress)
    try:
        with timed_phase("Applying the selected HTTP/HTTPS ingress"):
            activate_runtime(ingress, restart_only=restart_only)
        wait_until_healthy(timeout, ingress)
    except BaseException:
        if previous != ingress:
            log("Restoring the previous ingress after the failed switch")
            try:
                activate_runtime(previous, restart_only=True)
                wait_until_healthy(DEFAULT_HEALTH_TIMEOUT, previous)
                print("Previous ingress restored successfully.", flush=True)
            except BaseException as rollback_error:
                print(
                    f"Warning: automatic ingress rollback failed: {rollback_error}",
                    file=sys.stderr,
                    flush=True,
                )
        raise


def restart_application(ingress: IngressConfig, *, timeout: int) -> None:
    prepare_ingress(ingress)
    replace_runtime(
        ingress,
        timeout=timeout,
        restart_only=True,
    )


@contextmanager
def suspended_runtime_services(
    ingress: IngressConfig = HTTP_INGRESS,
) -> Iterator[None]:
    services = [*ingress.services[::-1], "mysql", "redis"]
    log("Stopping runtime services during the low-memory build")
    try:
        run_compose(
            ingress,
            "stop",
            "--timeout",
            "30",
            *services,
        )
        yield
    except BaseException:
        log("Restoring the previous application services after deployment failure")
        run_compose(
            ingress,
            "start",
            "mysql",
            "redis",
            *ingress.services,
            check=False,
        )
        raise


def deploy_application(
    build_timeout: int,
    *,
    health_timeout: int = DEFAULT_HEALTH_TIMEOUT,
    build_profile: BuildProfile = VERIFIED_BUILD_PROFILE,
    ingress: IngressConfig = HTTP_INGRESS,
) -> None:
    prepare_ingress(ingress)
    previous_ingress = detect_running_ingress(ingress)
    runtime_context = (
        suspended_runtime_services(previous_ingress)
        if build_profile.suspend_runtime_services
        else nullcontext()
    )
    with runtime_context:
        build_application_image(
            build_timeout,
            build_profile=build_profile,
            ingress=ingress,
        )
        validate_application_image(ingress)
        replace_runtime(
            ingress,
            timeout=health_timeout,
            restart_only=False,
            previous_ingress=previous_ingress,
        )


def container_status(
    service: str = APPLICATION_SERVICE,
    ingress: IngressConfig = HTTP_INGRESS,
) -> str:
    container_result = run_compose(
        ingress,
        "ps",
        "--all",
        "--quiet",
        service,
        capture_output=True,
        check=False,
    )
    container_id = container_result.stdout.strip()
    if container_result.returncode != 0 or not container_id:
        return ""

    inspect_result = run(
        [
            "docker",
            "inspect",
            "--format",
            "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}",
            container_id,
        ],
        capture_output=True,
        check=False,
    )
    if inspect_result.returncode != 0:
        return ""
    return inspect_result.stdout.strip()


def show_recent_logs(ingress: IngressConfig = HTTP_INGRESS) -> None:
    run_compose(
        ingress,
        "logs",
        "--tail",
        "100",
        *ingress.services,
        check=False,
    )


def wait_until_healthy(
    timeout: int,
    ingress: IngressConfig = HTTP_INGRESS,
) -> None:
    if ingress.https_enabled:
        log("Waiting for the application and HTTPS endpoint to become healthy")
    else:
        log("Waiting for the game hall container to become healthy")
    deadline = time.monotonic() + timeout
    last_statuses = {service: "unknown" for service in ingress.services}
    tls_ready = not ingress.https_enabled

    while time.monotonic() < deadline:
        for service in ingress.services:
            current_status = container_status(service, ingress)
            if current_status:
                last_statuses[service] = current_status

        failed_services = {
            service: status
            for service, status in last_statuses.items()
            if status in {"unhealthy", "exited", "dead"}
        }
        if failed_services:
            show_recent_logs(ingress)
            fail(f"Game hall services failed: {failed_services}")

        containers_ready = all(
            status in {"healthy", "running"}
            for status in last_statuses.values()
        )
        if containers_ready:
            tls_ready = https_responds(ingress)
        if containers_ready and tls_ready:
            run_compose(ingress, "ps")
            if ingress.https_enabled:
                print(
                    f"\nGame hall restarted successfully at "
                    f"https://{ingress.domain}."
                )
            else:
                print("\nGame hall restarted successfully.")
            return

        time.sleep(2)

    show_recent_logs(ingress)
    fail(
        f"Game hall did not become healthy within {timeout} seconds "
        f"(services: {last_statuses}, HTTPS ready: {tls_ready})"
    )


def main(
    *,
    build_profile: BuildProfile = VERIFIED_BUILD_PROFILE,
) -> int:
    args = parse_args()
    with deployment_lock():
        validate_environment()
        ingress = load_ingress_config()
        if ingress.https_enabled:
            log(f"HTTPS ingress enabled for {ingress.domain}")

        if args.restart_only:
            restart_application(ingress, timeout=args.timeout)
        else:
            if args.no_pull:
                log("Skipping Git updates because --no-pull was specified")
            elif update_sources():
                reexec_updated_entrypoint(args)
                return 0

            deploy_application(
                args.build_timeout,
                health_timeout=args.timeout,
                build_profile=build_profile,
                ingress=ingress,
            )
    return 0


def run_cli(
    *,
    build_profile: BuildProfile = VERIFIED_BUILD_PROFILE,
) -> int:
    try:
        return main(build_profile=build_profile)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run_cli())
