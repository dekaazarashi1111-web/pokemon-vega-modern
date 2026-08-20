#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からT19 Stage36を厳密再構築する。

Stage35の既存clean rebuildを前段として再利用し、Stage36 serializerを実行する。
さらにStage35 incremental BPSとclean直接BPSの完全往復、metadata、allocator、
mGBA quick/full、および全入力・出力identityを機械可読証跡へ固定する。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.bps import apply_bps, create_bps  # noqa: E402


TASK = "T19"
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
STAGE35_REBUILD = Path("scripts/rebuild_trainer_changekit_final_from_clean.py")
STAGE35_ROM = Path("build/stages/35_trainer_changekit_final.gba")
STAGE35_META = Path("build/stages/35_trainer_changekit_final.json")
STAGE35_ALLOC = Path("build/stages/35_allocation.json")
STAGE35_CLEAN_PATCH = Path(
    "build/patches/firered-jpn-rev0-to-trainer-changekit-final-stage35.bps"
)

STAGE36_BUILDER = Path("scripts/build_qol_production.py")
STAGE36_ROM = Path("build/stages/36_qol_production.gba")
STAGE36_META = Path("build/stages/36_qol_production.json")
STAGE36_ALLOC = Path("build/stages/36_allocation.json")
STAGE36_INCREMENTAL = Path(
    "build/patches/trainer-stage35-to-qol-production-stage36.bps"
)
STAGE36_DIRECT_PATCH = Path(
    "build/patches/firered-jpn-rev0-to-qol-production-stage36.bps"
)
MGBA_QUICK = Path("build/stages/36_mgba_qol_production_quick.json")
MGBA_FULL = Path("build/stages/36_mgba_qol_production_full.json")
EVIDENCE = Path("build/stages/36_clean_rebuild.json")
REPORT = Path("reports/generated/qol_production_clean_rebuild.md")

CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
STAGE35_SHA256 = "2ff8d61d7e17d120eaf60a81863dc29f6666d84c48a245e1be3d8dfa2447d180"
STAGE35_META_SHA256 = "d452395c0282a3fe6973f73fecd6e015828a87dfed443b59c6bb2af2ff812cf1"
STAGE35_ALLOC_SHA256 = "df7ac6d5274cbf8d5abeb0492437e7d387319c5e3fd764d7c23c3b13f734fc2d"
ROM_SIZE = 32 * 1024 * 1024


class CleanRebuildError(RuntimeError):
    """固定入力、patch chain、生成物、または証跡の契約違反。"""


def _fail(message: str) -> NoReturn:
    raise CleanRebuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read(path: Path) -> bytes:
    try:
        return (ROOT / path).read_bytes()
    except OSError as exc:
        _fail(f"required artifact is unavailable: {path}: {exc}")


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(_read(path))
    except json.JSONDecodeError as exc:
        _fail(f"JSON artifact is invalid: {path}: {exc}")
    if not isinstance(value, dict):
        _fail(f"JSON artifact root is not an object: {path}")
    return value


def _atomic_write(path: Path, raw: bytes) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        stream.write(raw)
        temporary = Path(stream.name)
    os.replace(temporary, target)


def _expect(raw: bytes, expected_sha256: str, expected_size: int, label: str) -> None:
    actual = _sha(raw)
    if len(raw) != expected_size or actual != expected_sha256:
        _fail(
            f"{label} identity differs: size={len(raw)}/{expected_size} "
            f"sha256={actual}/{expected_sha256}"
        )


def _run(command: Sequence[str], label: str) -> None:
    completed = subprocess.run(
        list(command), cwd=ROOT, text=True, capture_output=True, check=False
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-8000:]}")


def _validate_stage35(*, mode: str) -> tuple[bytes, bytes]:
    _run(
        [sys.executable, STAGE35_REBUILD.as_posix(), mode],
        f"Stage35 clean rebuild {mode}",
    )
    clean = _read(CLEAN_ROM)
    _expect(clean, CLEAN_SHA256, 16 * 1024 * 1024, "clean FireRed")
    stage35 = _read(STAGE35_ROM)
    _expect(stage35, STAGE35_SHA256, ROM_SIZE, "Stage35")
    if _sha(_read(STAGE35_META)) != STAGE35_META_SHA256:
        _fail("Stage35 metadata hash differs")
    if _sha(_read(STAGE35_ALLOC)) != STAGE35_ALLOC_SHA256:
        _fail("Stage35 allocation hash differs")
    direct = _read(STAGE35_CLEAN_PATCH)
    if apply_bps(clean, direct) != stage35:
        _fail("clean->Stage35 direct BPS round trip differs")
    return clean, stage35


def _direct_patch_metadata(stage36_sha256: str) -> bytes:
    return _stable({
        "format": "BPS1",
        "task": TASK,
        "source_sha256": CLEAN_SHA256,
        "target_sha256": stage36_sha256,
    })


def _validate_mgba(path: Path, mode: str, rom_sha256: str) -> dict[str, Any]:
    value = _json(path)
    if (
        value.get("status") != "PASS"
        or value.get("mode") != mode
        or value.get("rom_sha256") != rom_sha256
        or value.get("warnings_errors") != 0
        or value.get("process_runs") != 1
        or not value.get("checks")
        or not all(value["checks"].values())
    ):
        _fail(f"mGBA {mode} evidence is not exact all-PASS")
    return value


def _validate_stage36(
    clean: bytes, stage35: bytes
) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any], dict[str, Any]]:
    final = _read(STAGE36_ROM)
    metadata = _json(STAGE36_META)
    allocation = _json(STAGE36_ALLOC)
    expected_sha256 = metadata.get("output", {}).get("sha256")
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        _fail("Stage36 metadata output hash is unavailable")
    _expect(final, expected_sha256, ROM_SIZE, "Stage36")
    if metadata.get("input", {}).get("sha256") != STAGE35_SHA256:
        _fail("Stage36 metadata input is not the pinned Stage35")
    if metadata.get("clean_input", {}).get("sha256") != CLEAN_SHA256:
        _fail("Stage36 metadata clean input is not the pinned FireRed Rev.0")
    if metadata.get("status") != "PASS":
        _fail("Stage36 metadata status is not PASS")
    if metadata.get("change_audit", {}).get("outside_declared_span_count") != 0:
        _fail("Stage36 contains changes outside declared spans")
    if allocation.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage36 allocation contains an overlap")

    incremental = _read(STAGE36_INCREMENTAL)
    if apply_bps(stage35, incremental) != final:
        _fail("Stage35->Stage36 incremental BPS round trip differs")
    recorded_incremental = metadata.get("release_patches", {}).get("incremental", {})
    if (
        recorded_incremental.get("sha256") != _sha(incremental)
        or recorded_incremental.get("exact") is not True
    ):
        _fail("Stage36 incremental BPS metadata differs")

    direct = create_bps(clean, final, metadata=_direct_patch_metadata(expected_sha256))
    if apply_bps(clean, direct) != final:
        _fail("clean->Stage36 direct BPS round trip differs")
    quick = _validate_mgba(MGBA_QUICK, "quick", expected_sha256)
    full = _validate_mgba(MGBA_FULL, "full", expected_sha256)
    if (
        quick.get("runner_sha256") != full.get("runner_sha256")
        or quick.get("cases_sha256") != full.get("cases_sha256")
    ):
        _fail("mGBA quick/full runner or case identity differs")
    return final, direct, metadata, quick, full


def _expected_evidence(
    clean: bytes,
    stage35: bytes,
    final: bytes,
    direct: bytes,
    metadata: Mapping[str, Any],
    quick: Mapping[str, Any],
    full: Mapping[str, Any],
) -> dict[str, Any]:
    incremental = _read(STAGE36_INCREMENTAL)
    return {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "method": "PINNED_STAGE35_CLEAN_REBUILD_PLUS_STAGE36_SERIALIZER",
        "chain": [
            {
                "artifact": CLEAN_ROM.as_posix(),
                "sha256": _sha(clean),
                "size": len(clean),
            },
            {
                "artifact": STAGE35_CLEAN_PATCH.as_posix(),
                "sha256": _sha(_read(STAGE35_CLEAN_PATCH)),
                "size": len(_read(STAGE35_CLEAN_PATCH)),
            },
            {
                "artifact": STAGE35_ROM.as_posix(),
                "sha256": _sha(stage35),
                "size": len(stage35),
            },
            {
                "artifact": STAGE36_BUILDER.as_posix(),
                "sha256": _sha(_read(STAGE36_BUILDER)),
            },
            {
                "artifact": STAGE36_INCREMENTAL.as_posix(),
                "sha256": _sha(incremental),
                "size": len(incremental),
            },
            {
                "artifact": STAGE36_ROM.as_posix(),
                "sha256": _sha(final),
                "size": len(final),
            },
        ],
        "input_output": {
            "clean_sha256": _sha(clean),
            "stage35_sha256": _sha(stage35),
            "stage36_sha256": _sha(final),
            "stage36_metadata_sha256": _sha(_read(STAGE36_META)),
            "stage36_allocation_sha256": _sha(_read(STAGE36_ALLOC)),
        },
        "bps": {
            "stage35_incremental": {
                "artifact": STAGE36_INCREMENTAL.as_posix(),
                "sha256": _sha(incremental),
                "round_trip_exact": True,
            },
            "direct_clean": {
                "artifact": STAGE36_DIRECT_PATCH.as_posix(),
                "sha256": _sha(direct),
                "size": len(direct),
                "round_trip_exact": True,
            },
        },
        "declared_span": {
            "changed_byte_count": metadata["change_audit"]["changed_byte_count"],
            "outside_declared_span_count": metadata["change_audit"][
                "outside_declared_span_count"
            ],
        },
        "allocator_overlap_count": _json(STAGE36_ALLOC)["summaries"][
            "overlap_count"
        ],
        "mgba": {
            "quick": {
                "artifact_sha256": _sha(_read(MGBA_QUICK)),
                "status": quick["status"],
                "checks": quick["checks"],
                "warnings_errors": quick["warnings_errors"],
                "process_runs": quick["process_runs"],
            },
            "full": {
                "artifact_sha256": _sha(_read(MGBA_FULL)),
                "status": full["status"],
                "checks": full["checks"],
                "warnings_errors": full["warnings_errors"],
                "process_runs": full["process_runs"],
            },
        },
    }


def _report(evidence: Mapping[str, Any]) -> bytes:
    bps = evidence["bps"]
    declared = evidence["declared_span"]
    output = evidence["input_output"]
    return f"""# T19 QOL production clean rebuild

## 結論

- clean FireRed日本版Rev.0からStage35既存clean rebuildとStage36 serializerを順に実行した。
- Stage35→Stage36 incremental BPSとclean→Stage36直接BPSをexact round-tripした。
- mGBA quick/fullを独立processで実行し、全check PASS、warning/error 0を確認した。
- allocator overlap {evidence['allocator_overlap_count']}、declared span外変更 {declared['outside_declared_span_count']}。

## Identity

- clean SHA-256: `{output['clean_sha256']}`
- Stage35 SHA-256: `{output['stage35_sha256']}`
- Stage36 SHA-256: `{output['stage36_sha256']}`
- Stage35 incremental BPS SHA-256: `{bps['stage35_incremental']['sha256']}`
- clean直接BPS SHA-256: `{bps['direct_clean']['sha256']}`
""".encode("utf-8")


def _finalize(clean: bytes, stage35: bytes, *, write: bool) -> dict[str, Any]:
    final, direct, metadata, quick, full = _validate_stage36(clean, stage35)
    evidence = _expected_evidence(
        clean, stage35, final, direct, metadata, quick, full
    )
    report = _report(evidence)
    if write:
        _atomic_write(STAGE36_DIRECT_PATCH, direct)
        _atomic_write(EVIDENCE, _stable(evidence))
        _atomic_write(REPORT, report)
    else:
        if _read(STAGE36_DIRECT_PATCH) != direct:
            _fail("published clean direct Stage36 BPS differs")
        if _read(EVIDENCE) != _stable(evidence):
            _fail("Stage36 clean rebuild evidence differs")
        if _read(REPORT) != report:
            _fail("Stage36 clean rebuild report differs")
    return evidence


def build() -> dict[str, Any]:
    clean, stage35 = _validate_stage35(mode="build")
    _run(
        [sys.executable, STAGE36_BUILDER.as_posix(), "build"],
        "Stage36 serializer/mGBA build",
    )
    return _finalize(clean, stage35, write=True)


def check() -> dict[str, Any]:
    clean, stage35 = _validate_stage35(mode="check")
    _run(
        [sys.executable, STAGE36_BUILDER.as_posix(), "check"],
        "Stage36 serializer/mGBA check",
    )
    return _finalize(clean, stage35, write=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = build() if args.mode == "build" else check()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CleanRebuildError) as exc:
        print(f"QOL production clean rebuild {args.mode}: FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "QOL production clean rebuild %s: PASS rom=%s direct_bps=%s"
        % (
            args.mode,
            evidence["input_output"]["stage36_sha256"],
            evidence["bps"]["direct_clean"]["sha256"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
