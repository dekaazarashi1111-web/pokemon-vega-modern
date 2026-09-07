#!/usr/bin/env python3
"""明示採用済みの現行プレイ基準ROMを検証して解決する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zlib
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config/active_play_baseline.json"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
CRC32_RE = re.compile(r"[0-9A-F]{8}")


class ActivePlayBaselineError(ValueError):
    """現行プレイ基準が安全に解決できない。"""


def _require_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ActivePlayBaselineError(f"{label}がobjectではありません")
    return value


def _rom_identity(path: Path) -> tuple[int, str, str]:
    digest = hashlib.sha256()
    crc = 0
    size = 0
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                size += len(chunk)
                digest.update(chunk)
                crc = zlib.crc32(chunk, crc)
    except OSError as error:
        raise ActivePlayBaselineError(f"現行ROMを読めません: {path}") from error
    return size, digest.hexdigest(), f"{crc & 0xFFFFFFFF:08X}"


def load_active_play_baseline(
    manifest_path: Path = DEFAULT_MANIFEST,
    workspace: Path = ROOT,
    *,
    verify_rom: bool = True,
) -> dict[str, Any]:
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise ActivePlayBaselineError("現行プレイ基準manifestを読めません") from error
    manifest = _require_mapping(document, "manifest")
    if manifest.get("schema_version") != 1:
        raise ActivePlayBaselineError("schema_versionが1ではありません")
    if manifest.get("policy") != "LATEST_EXPLICITLY_ADOPTED":
        raise ActivePlayBaselineError("自動的な最大Stage選択は許可されていません")
    if manifest.get("status") != "ACTIVE":
        raise ActivePlayBaselineError("現行プレイ基準がACTIVEではありません")

    stage = manifest.get("stage")
    if type(stage) is not int or stage < 47:
        raise ActivePlayBaselineError("stageは47以上の整数で指定してください")
    label = manifest.get("label")
    if not isinstance(label, str) or not label.strip():
        raise ActivePlayBaselineError("labelがありません")

    rom = _require_mapping(manifest.get("rom"), "rom")
    relative = rom.get("path")
    if not isinstance(relative, str) or not relative or "\t" in relative or "\n" in relative:
        raise ActivePlayBaselineError("ROM pathが不正です")
    parsed = PurePosixPath(relative)
    if parsed.is_absolute() or ".." in parsed.parts or parsed.suffix.lower() != ".gba":
        raise ActivePlayBaselineError("ROM pathはworkspace内の相対GBA pathにしてください")
    workspace_resolved = workspace.resolve()
    resolved = (workspace_resolved / Path(*parsed.parts)).resolve()
    try:
        resolved.relative_to(workspace_resolved)
    except ValueError as error:
        raise ActivePlayBaselineError("ROM pathがworkspace外を指しています") from error

    expected_size = rom.get("size")
    expected_sha256 = rom.get("sha256")
    expected_crc32 = rom.get("crc32")
    if type(expected_size) is not int or expected_size <= 0:
        raise ActivePlayBaselineError("ROM sizeが正の整数ではありません")
    if not isinstance(expected_sha256, str) or SHA256_RE.fullmatch(expected_sha256) is None:
        raise ActivePlayBaselineError("ROM SHA-256が小文字hex 64桁ではありません")
    if not isinstance(expected_crc32, str) or CRC32_RE.fullmatch(expected_crc32) is None:
        raise ActivePlayBaselineError("ROM CRC32が大文字hex 8桁ではありません")

    if verify_rom:
        actual = _rom_identity(resolved)
        expected = (expected_size, expected_sha256, expected_crc32)
        if actual != expected:
            raise ActivePlayBaselineError(
                "現行ROM identityがmanifestと一致しません: "
                f"size={actual[0]} sha256={actual[1]} crc32={actual[2]}"
            )

    return {
        "schema_version": 1,
        "policy": manifest["policy"],
        "status": manifest["status"],
        "stage": stage,
        "label": label,
        "adopted_on": manifest.get("adopted_on"),
        "rom": {
            "path": relative,
            "resolved_path": str(resolved),
            "size": expected_size,
            "sha256": expected_sha256,
            "crc32": expected_crc32,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("check", "resolve"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--workspace", type=Path, default=ROOT)
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        baseline = load_active_play_baseline(
            args.manifest,
            args.workspace,
            verify_rom=not args.metadata_only,
        )
    except ActivePlayBaselineError as error:
        print(f"active-play-baseline: FAIL: {error}", file=sys.stderr)
        return 1

    if args.command == "resolve":
        print(f"{baseline['rom']['resolved_path']}\t{baseline['stage']}")
    elif args.json:
        print(json.dumps({"status": "PASS", **baseline}, ensure_ascii=False, sort_keys=True))
    else:
        print(
            "active-play-baseline: PASS: "
            f"stage={baseline['stage']} sha256={baseline['rom']['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
