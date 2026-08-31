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
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_HEALTH_TIMEOUT = 120
DEFAULT_BUILD_TIMEOUT = 30 * 60
BUILD_HEARTBEAT_INTERVAL = 30
LOW_MEMORY_BUILD_THRESHOLD_BYTES = 2 * 1024**3
MINIMUM_LOW_MEMORY_SWAP_BYTES = 1024**3
DEPLOY_BRANCH = "main"
APPLICATION_SERVICE = "app"
PLUGIN_VALIDATION_MODULE = "backend.app.games.validate_plugins"
DEPLOYMENT_LOCK_PATH = Path(tempfile.gettempdir()) / (
    "game-hall-deploy-"
    f"{hashlib.sha256(str(PROJECT_DIR).encode()).hexdigest()[:12]}.lock"
)
MEMINFO_PATH = Path("/proc/meminfo")


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
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_DIR,
        check=check,
        capture_output=capture_output,
        text=True,
        timeout=timeout,
    )


def require_command(command: str, message: str) -> None:
    if shutil.which(command) is None:
        fail(message)


def validate_environment() -> None:
    require_command("docker", "Docker is not installed or is not in PATH")

    if not (PROJECT_DIR / "compose.yaml").is_file():
        fail(f"compose.yaml was not found in {PROJECT_DIR}")
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


def update_sources() -> None:
    validate_source_checkout()
    pull_main_branch()
    update_submodules_from_remotes()


def build_application_image(timeout: int) -> None:
    memory = read_memory_info()
    validate_build_memory(memory)
    low_memory_build = low_memory_build_required(memory)
    command = [
        "docker",
        "compose",
        "--progress",
        "plain",
        "build",
    ]
    if low_memory_build:
        assert memory is not None
        log(
            "Low-memory host detected "
            f"({format_memory(memory.total_bytes)} RAM, "
            f"{format_memory(memory.available_bytes)} available, "
            f"{format_memory(memory.swap_total_bytes)} swap); "
            "serializing Python and frontend build stages"
        )
        command.extend(["--build-arg", "LOW_MEMORY_BUILD=1"])
    command.append(APPLICATION_SERVICE)

    with timed_phase("Building the game hall application image"):
        try:
            with progress_heartbeat("Docker image build is still running"):
                run(command, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(
                "Application image build exceeded "
                f"{format_duration(timeout)}; the current application container "
                "was not replaced"
            ) from error


def validate_application_image() -> None:
    with timed_phase(
        "Validating the community game release registry and published plugins"
    ):
        run(
            [
                "docker",
                "compose",
                "run",
                "--rm",
                "--no-deps",
                APPLICATION_SERVICE,
                "python",
                "-m",
                PLUGIN_VALIDATION_MODULE,
            ]
        )


def start_application() -> None:
    with timed_phase("Restarting the game hall with the validated image"):
        run(
            [
                "docker",
                "compose",
                "up",
                "-d",
                "--no-build",
                APPLICATION_SERVICE,
            ]
        )


def restart_existing_application() -> None:
    with timed_phase("Restarting the existing game hall application container"):
        run(
            [
                "docker",
                "compose",
                "restart",
                "--no-deps",
                APPLICATION_SERVICE,
            ]
        )


def deploy_application(build_timeout: int) -> None:
    run(["docker", "compose", "config", "--quiet"])
    build_application_image(build_timeout)
    validate_application_image()
    start_application()


def container_status() -> str:
    container_result = run(
        ["docker", "compose", "ps", "-q", "app"],
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


def show_recent_logs() -> None:
    run(
        ["docker", "compose", "logs", "--tail", "100", "app"],
        check=False,
    )


def wait_until_healthy(timeout: int) -> None:
    log("Waiting for the game hall container to become healthy")
    deadline = time.monotonic() + timeout
    last_status = "unknown"

    while time.monotonic() < deadline:
        current_status = container_status()
        if current_status:
            last_status = current_status

        if current_status in {"healthy", "running"}:
            run(["docker", "compose", "ps"])
            print("\nGame hall restarted successfully.")
            return

        if current_status in {"unhealthy", "exited", "dead"}:
            show_recent_logs()
            fail(f"Game hall container entered state: {current_status}")

        time.sleep(2)

    show_recent_logs()
    fail(
        f"Game hall did not become healthy within {timeout} seconds "
        f"(last state: {last_status})"
    )


def main() -> int:
    args = parse_args()
    with deployment_lock():
        validate_environment()

        if args.restart_only:
            restart_existing_application()
        else:
            if args.no_pull:
                log("Skipping Git updates because --no-pull was specified")
            else:
                update_sources()

            deploy_application(args.build_timeout)

        wait_until_healthy(args.timeout)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise SystemExit(130)
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
