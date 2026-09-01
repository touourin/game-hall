#!/usr/bin/env python3

from __future__ import annotations

from restart import LOW_MEMORY_BUILD_PROFILE, run_cli


if __name__ == "__main__":
    raise SystemExit(run_cli(build_profile=LOW_MEMORY_BUILD_PROFILE))
