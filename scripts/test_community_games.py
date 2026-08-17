#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = PROJECT_ROOT / "game-hall-community-games"


def plugin_test_directories() -> list[Path]:
    if not PLUGIN_ROOT.is_dir():
        return []
    return [
        tests_directory
        for tests_directory in sorted(PLUGIN_ROOT.glob("plugin-*/tests"))
        if any(tests_directory.rglob("test_*.py"))
    ]


def main() -> int:
    test_directories = plugin_test_directories()
    if not test_directories:
        print("No community game Python tests found.")
        return 0
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--import-mode=importlib",
            *(str(path) for path in test_directories),
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
