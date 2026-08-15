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
DEPLOY_BRANCH = "main"
APPLICATION_SERVICE = "app"
PLUGIN_VALIDATION_MODULE = "backend.app.games.validate_plugins"


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
        "--no-pull",
        action="store_true",
        help="skip Git updates and rebuild the currently checked-out code",
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


def reset_submodules_to_recorded_commits() -> None:
    if not (PROJECT_DIR / ".gitmodules").is_file():
        return
    log("Preparing Git submodules for the main-branch update")
    run(["git", "submodule", "sync", "--recursive"])
    run(["git", "submodule", "update", "--init", "--recursive", "--checkout"])


def pull_main_branch() -> None:
    log(f"Updating the main repository from origin/{DEPLOY_BRANCH}")
    run(["git", "pull", "--ff-only", "origin", DEPLOY_BRANCH])


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
    # A previous deployment may have advanced a submodule beyond the commit
    # recorded by the parent repository. Put it back first so the parent can
    # fast-forward cleanly, then advance it to its configured remote branch.
    reset_submodules_to_recorded_commits()
    pull_main_branch()
    update_submodules_from_remotes()


def build_application_image() -> None:
    log("Building the game hall application image")
    run(["docker", "compose", "build", APPLICATION_SERVICE])


def validate_application_image() -> None:
    log("Validating the third-party release registry and published plugins")
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
    log("Restarting the game hall with the validated image")
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


def deploy_application() -> None:
    run(["docker", "compose", "config", "--quiet"])
    build_application_image()
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
    validate_environment()
    if args.no_pull:
        log("Skipping Git updates because --no-pull was specified")
    else:
        update_sources()

    deploy_application()
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
