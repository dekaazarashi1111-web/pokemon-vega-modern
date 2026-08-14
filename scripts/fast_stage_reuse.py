#!/usr/bin/env python3
"""開発用差分ビルドで、直前stageの実体とmetadataを相互検証する。"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


FAST_REUSE_ENV = "VEGA_FAST_STAGE_REUSE"


def enabled() -> bool:
    return os.environ.get(FAST_REUSE_ENV) == "1"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _metadata(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"stage metadata must be an object: {path}")
    return value


def trusted_stage_sha(
    root: Path,
    rom_relative: Path,
    metadata_relative: Path,
    task: str,
    pinned_sha256: str,
) -> str:
    """通常は固定hash、差分modeではPASS metadataと一致する実ROM hashを返す。"""

    if not enabled():
        return pinned_sha256
    rom = root / rom_relative
    metadata_path = root / metadata_relative
    if not rom.is_file() or rom.is_symlink() or not metadata_path.is_file():
        raise ValueError(f"fast reuse prerequisite is missing: {rom_relative}")
    metadata = _metadata(metadata_path)
    output = metadata.get("output")
    if (
        metadata.get("task") != task
        or metadata.get("status") != "PASS"
        or not isinstance(output, dict)
        or output.get("size") != rom.stat().st_size
        or output.get("sha256") != _sha(rom)
        or rom.stat().st_size != 32 * 1024 * 1024
    ):
        raise ValueError(f"fast reuse stage/metadata identity differs: {rom_relative}")
    invariants = metadata.get("invariants")
    if isinstance(invariants, dict) and invariants and not all(
        value is True for value in invariants.values()
    ):
        raise ValueError(f"fast reuse stage invariants failed: {rom_relative}")
    return str(output["sha256"])


def trusted_t06_fingerprint(
    root: Path, metadata_relative: Path, pinned_fingerprint: str
) -> str:
    """差分modeでは、published T06 metadata自身が証明するfingerprintを使う。"""

    if not enabled():
        return pinned_fingerprint
    metadata = _metadata(root / metadata_relative)
    fingerprint = metadata.get("fingerprint")
    runs = metadata.get("upstream_runs")
    if (
        metadata.get("task") != "T06"
        or metadata.get("status") != "PASS"
        or not isinstance(fingerprint, str)
        or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None
        or not isinstance(runs, list)
        or len(runs) != 2
    ):
        raise ValueError("fast reuse T06 fingerprint evidence differs")
    return fingerprint


def generated_input_may_follow_stage(path: str) -> bool:
    """差分modeでmetadata連鎖から再検証する生成入力だけを識別する。"""

    return enabled() and path.startswith(("build/", "generated/", "reports/generated/"))
