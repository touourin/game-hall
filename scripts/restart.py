#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_HEALTH_TIMEOUT = 120


def positive_integer(raw_value: str) -> int:
    try:
        value = int(raw_value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild and restart the game hall with Docker Compose.",
    )
    parser.add_argument(
        "--pull",
        action="store_true",
        help="pull the current Git branch with --ff-only first",
    )
    parser.add_argument(
        "--timeout",
        type=positive_integer,
        default=DEFAULT_HEALTH_TIMEOUT,
        metavar="SECONDS",
        help=f"health-check timeout (default: {DEFAULT_HEALTH_TIMEOUT})",
    )
    return parser.parse_args()


def log(message: str) -> None:
    print(f"\n==> {message}", flush=True)


def fail(message: str) -> None:
    raise RuntimeError(message)


def run(
    command: list[str],
    *,
    capture_output: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_DIR,
        check=check,
        capture_output=capture_output,
        text=True,
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


def pull_current_branch() -> None:
    require_command("git", "Git is not installed or is not in PATH")
    if not (PROJECT_DIR / ".git").is_dir():
        fail(f"{PROJECT_DIR} is not a Git checkout")

    status = run(["git", "status", "--porcelain"], capture_output=True).stdout
    if status.strip():
        fail("Git working tree is not clean; commit or stash changes before --pull")

    branch = run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
    ).stdout.strip()
    if branch == "HEAD":
        fail("cannot pull while Git is in detached HEAD state")

    log(f"Pulling Git branch {branch}")
    run(["git", "pull", "--ff-only"])


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
    validate_environment()

    if args.pull:
        pull_current_branch()

    run(["docker", "compose", "config", "--quiet"])

    log("Building and restarting the game hall")
    run(["docker", "compose", "up", "-d", "--build", "app"])
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
