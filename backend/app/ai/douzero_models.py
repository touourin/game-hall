from __future__ import annotations

import argparse
import hashlib
import hmac
import re
import shutil
from collections.abc import Mapping
from pathlib import Path


POSITIONS = ("landlord", "landlord_up", "landlord_down")
MODEL_FILENAMES = {
    "landlord": "landlord.ckpt",
    "landlord_up": "landlord_up.ckpt",
    "landlord_down": "landlord_down.ckpt",
}
CHECKSUMS_FILENAME = "SHA256SUMS"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class DouZeroModelError(ValueError):
    """Raised when a DouZero model bundle is incomplete or inconsistent."""


def find_model_paths(model_dir: str | Path | None) -> dict[str, Path] | None:
    """Return a complete, verified model set or ``None`` when unavailable."""
    if not model_dir:
        return None
    try:
        return require_model_paths(model_dir)
    except DouZeroModelError:
        return None


def require_model_paths(model_dir: str | Path) -> dict[str, Path]:
    """Resolve all role models and verify the checksum manifest when present."""
    directory = Path(model_dir).expanduser()
    paths = _require_model_files(directory)

    manifest = directory / CHECKSUMS_FILENAME
    if manifest.is_file():
        _verify_checksums(paths, manifest)
    return paths


def write_checksum_manifest(model_dir: str | Path) -> Path:
    """Persist deterministic checksums beside a complete set of weights."""
    directory = Path(model_dir).expanduser()
    paths = _require_model_files(directory)
    manifest = directory / CHECKSUMS_FILENAME
    manifest.write_text(
        "".join(
            f"{_sha256(paths[position])}  {paths[position].name}\n"
            for position in POSITIONS
        ),
        encoding="utf-8",
    )
    return manifest


def stage_model_bundle(source_dir: str | Path, output_dir: str | Path) -> Path:
    """Copy only verified model files and create a fresh checksum manifest."""
    source_paths = require_model_paths(source_dir)
    output = Path(output_dir).expanduser()
    output.mkdir(parents=True, exist_ok=True)
    for position in POSITIONS:
        shutil.copyfile(
            source_paths[position],
            output / MODEL_FILENAMES[position],
        )
    return write_checksum_manifest(output)


def _require_model_files(directory: Path) -> dict[str, Path]:
    paths = {
        position: directory / filename
        for position, filename in MODEL_FILENAMES.items()
    }
    missing = [
        path.name
        for path in paths.values()
        if not path.is_file() or path.stat().st_size == 0
    ]
    if missing:
        raise DouZeroModelError(
            "DouZero 模型缺失或为空：" + "、".join(missing)
        )
    return paths


def _verify_checksums(
    paths: Mapping[str, Path],
    manifest: Path,
) -> None:
    expected_filenames = set(MODEL_FILENAMES.values())
    expected_hashes: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        manifest.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise DouZeroModelError(
                f"{CHECKSUMS_FILENAME} 第 {line_number} 行格式不正确"
            )
        digest, filename = parts[0].lower(), parts[1].lstrip("*")
        if (
            _SHA256_PATTERN.fullmatch(digest) is None
            or filename not in expected_filenames
            or filename in expected_hashes
        ):
            raise DouZeroModelError(
                f"{CHECKSUMS_FILENAME} 第 {line_number} 行格式不正确"
            )
        expected_hashes[filename] = digest

    missing = expected_filenames - expected_hashes.keys()
    if missing:
        raise DouZeroModelError(
            f"{CHECKSUMS_FILENAME} 缺少校验值：" + "、".join(sorted(missing))
        )

    paths_by_filename = {path.name: path for path in paths.values()}
    mismatched = [
        filename
        for filename, expected in expected_hashes.items()
        if not hmac.compare_digest(_sha256(paths_by_filename[filename]), expected)
    ]
    if mismatched:
        raise DouZeroModelError(
            "DouZero 模型校验失败：" + "、".join(sorted(mismatched))
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as model_file:
        for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a DouZero model bundle and write its checksums.",
    )
    parser.add_argument("model_dir", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    manifest = (
        stage_model_bundle(args.model_dir, args.output)
        if args.output is not None
        else write_checksum_manifest(args.model_dir)
    )
    print(f"DouZero model checksums: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
