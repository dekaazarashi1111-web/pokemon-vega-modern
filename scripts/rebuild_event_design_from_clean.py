#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からT20 Stage37を厳密再構築する。"""

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

from tools.release.bps import apply_bps  # noqa: E402


TASK = "T20"
ROM_SIZE = 32 * 1024 * 1024
CLEAN = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
STAGE36 = Path("build/stages/36_qol_production.gba")
STAGE36_META = Path("build/stages/36_qol_production.json")
STAGE36_CLEAN_PATCH = Path("build/patches/firered-jpn-rev0-to-qol-production-stage36.bps")
BUILDER = Path("scripts/build_event_design_stage.py")
STAGE37 = Path("build/stages/37_event_design.gba")
STAGE37_META = Path("build/stages/37_event_design.json")
STAGE37_ALLOC = Path("build/stages/37_allocation.json")
INCREMENTAL = Path("build/patches/qol-production-stage36-to-event-design-stage37.bps")
DIRECT = Path("build/patches/firered-jpn-rev0-to-event-design-stage37.bps")
MGBA_QUICK = Path("build/stages/37_mgba_event_design_quick.json")
MGBA_FULL = Path("build/stages/37_mgba_event_design_full.json")
EVIDENCE = Path("build/stages/37_clean_rebuild.json")
REPORT = Path("reports/generated/event_design_clean_rebuild.md")

CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
STAGE36_SHA256 = "c262fbb121957950f890c7b28ab64b19f9bc8fdf541b543747c39ab1f7c381dd"
STAGE36_META_SHA256 = "f901673fb0eef34ac9fdad6585697007f1077e16d42f84a36dbcb79433a34bce"


class EventDesignCleanRebuildError(RuntimeError):
    """固定入力、BPS chain、mGBAまたは再構築証跡の違反。"""


def _fail(message: str) -> NoReturn:
    raise EventDesignCleanRebuildError(message)


def _read(path: Path) -> bytes:
    try:
        return (ROOT / path).read_bytes()
    except OSError as exc:
        _fail(f"required artifact is unavailable: {path}: {exc}")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(_read(path))
    if not isinstance(value, dict):
        _fail(f"JSON root is not an object: {path}")
    return value


def _run(command: Sequence[str], label: str) -> None:
    completed = subprocess.run(
        list(command), cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-8000:]}")


def _atomic_write(path: Path, raw: bytes) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        stream.write(raw)
        temporary = Path(stream.name)
    os.replace(temporary, target)


def _identity(raw: bytes, size: int, digest: str, label: str) -> None:
    if len(raw) != size or _sha(raw) != digest:
        _fail(f"{label} identity differs: size={len(raw)} sha256={_sha(raw)}")


def _mgba(path: Path, mode: str, rom_sha256: str) -> dict[str, Any]:
    value = _json(path)
    checks = value.get("checks")
    if (
        value.get("status") != "PASS" or value.get("mode") != mode
        or value.get("rom_sha256") != rom_sha256
        or value.get("warnings_errors") != 0
        or value.get("process_runs") != 1
        or not isinstance(checks, dict) or any(result is not True for result in checks.values())
    ):
        _fail(f"mGBA {mode} evidence is not exact all-PASS")
    return value


def _validate() -> tuple[dict[str, Any], bytes]:
    clean = _read(CLEAN)
    stage36 = _read(STAGE36)
    stage37 = _read(STAGE37)
    _identity(clean, 16 * 1024 * 1024, CLEAN_SHA256, "clean FireRed")
    _identity(stage36, ROM_SIZE, STAGE36_SHA256, "Stage36")
    if _sha(_read(STAGE36_META)) != STAGE36_META_SHA256:
        _fail("Stage36 metadata identity differs")
    metadata = _json(STAGE37_META)
    output_sha256 = metadata.get("output", {}).get("sha256")
    if not isinstance(output_sha256, str) or len(output_sha256) != 64:
        _fail("Stage37 output identity is unavailable")
    _identity(stage37, ROM_SIZE, output_sha256, "Stage37")
    if (
        metadata.get("status") != "PASS"
        or metadata.get("input", {}).get("sha256") != STAGE36_SHA256
        or metadata.get("clean_input", {}).get("sha256") != CLEAN_SHA256
        or metadata.get("change_audit", {}).get("outside_declared_span_count") != 0
        or metadata.get("change_audit", {}).get("declared_span_overlap_count") != 0
        or _json(STAGE37_ALLOC).get("summaries", {}).get("overlap_count") != 0
    ):
        _fail("Stage37 metadata/allocation contract differs")

    stage36_from_clean = apply_bps(clean, _read(STAGE36_CLEAN_PATCH))
    if stage36_from_clean != stage36:
        _fail("clean->Stage36 direct BPS round trip differs")
    incremental = _read(INCREMENTAL)
    chained = apply_bps(stage36_from_clean, incremental)
    direct = _read(DIRECT)
    directly_rebuilt = apply_bps(clean, direct)
    if chained != stage37 or directly_rebuilt != stage37 or chained != directly_rebuilt:
        _fail("clean->Stage36->Stage37/direct Stage37 identity differs")
    patches = metadata.get("release_patches", {})
    if (
        patches.get("incremental", {}).get("sha256") != _sha(incremental)
        or patches.get("incremental", {}).get("exact") is not True
        or patches.get("clean_direct", {}).get("sha256") != _sha(direct)
        or patches.get("clean_direct", {}).get("exact") is not True
    ):
        _fail("Stage37 release patch metadata differs")

    quick = _mgba(MGBA_QUICK, "quick", output_sha256)
    full = _mgba(MGBA_FULL, "full", output_sha256)
    if (
        quick.get("result_identity") != full.get("result_identity")
        or quick.get("runner_sha256") != full.get("runner_sha256")
        or quick.get("cases_sha256") != full.get("cases_sha256")
    ):
        _fail("mGBA quick/full result or fixture identity differs")
    evidence = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "method": "CLEAN_TO_STAGE36_DIRECT_PLUS_STAGE37_SERIALIZER_AND_DIRECT_CROSSCHECK",
        "input_output": {
            "clean_sha256": _sha(clean), "stage36_sha256": _sha(stage36),
            "stage37_sha256": _sha(stage37),
            "stage37_metadata_sha256": _sha(_read(STAGE37_META)),
            "stage37_allocation_sha256": _sha(_read(STAGE37_ALLOC)),
        },
        "chain": [
            {"artifact": CLEAN.as_posix(), "sha256": _sha(clean), "size": len(clean)},
            {"artifact": STAGE36_CLEAN_PATCH.as_posix(),
             "sha256": _sha(_read(STAGE36_CLEAN_PATCH)),
             "size": len(_read(STAGE36_CLEAN_PATCH))},
            {"artifact": STAGE36.as_posix(), "sha256": _sha(stage36), "size": len(stage36)},
            {"artifact": BUILDER.as_posix(), "sha256": _sha(_read(BUILDER))},
            {"artifact": INCREMENTAL.as_posix(), "sha256": _sha(incremental),
             "size": len(incremental)},
            {"artifact": STAGE37.as_posix(), "sha256": _sha(stage37), "size": len(stage37)},
        ],
        "bps": {
            "stage36_incremental": {"sha256": _sha(incremental), "round_trip_exact": True},
            "clean_direct": {"sha256": _sha(direct), "size": len(direct),
                             "round_trip_exact": True},
            "chain_direct_identity_equal": True,
        },
        "declared_span": {
            "changed_byte_count": metadata["change_audit"]["changed_byte_count"],
            "outside_declared_span_count": 0, "declared_span_overlap_count": 0,
        },
        "allocator_overlap_count": 0,
        "mgba": {
            "process_count": 2, "result_identity": quick["result_identity"],
            "quick_artifact_sha256": _sha(_read(MGBA_QUICK)),
            "full_artifact_sha256": _sha(_read(MGBA_FULL)),
            "warnings_errors": 0,
        },
    }
    report = f"""# T20 Event design clean rebuild

## 結論

- clean FireRed日本版Rev.0→Stage36→Stage37 chainとclean→Stage37直接BPSが同一ROMになった。
- Stage36→37 incremental BPS、clean直接BPSを完全往復した。
- allocator/declared-span overlap 0、declared span外変更0。
- mGBA quick/full独立2 processはwarnings/errors 0、result identity一致。

## Identity

- clean SHA-256: `{evidence['input_output']['clean_sha256']}`
- Stage36 SHA-256: `{evidence['input_output']['stage36_sha256']}`
- Stage37 SHA-256: `{evidence['input_output']['stage37_sha256']}`
- result identity: `{evidence['mgba']['result_identity']}`
""".encode("utf-8")
    return evidence, report


def _execute(mode: str) -> dict[str, Any]:
    _run([sys.executable, BUILDER.as_posix(), mode], f"Stage37 serializer/mGBA {mode}")
    evidence, report = _validate()
    expected = _stable(evidence)
    if mode == "build":
        _atomic_write(EVIDENCE, expected)
        _atomic_write(REPORT, report)
    else:
        if _read(EVIDENCE) != expected:
            _fail("Stage37 clean rebuild evidence differs")
        if _read(REPORT) != report:
            _fail("Stage37 clean rebuild report differs")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = _execute(args.mode)
    except (OSError, ValueError, KeyError, json.JSONDecodeError,
            EventDesignCleanRebuildError) as exc:
        print(f"Event design clean rebuild {args.mode}: FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "Event design clean rebuild %s: PASS rom=%s identity=%s"
        % (args.mode, evidence["input_output"]["stage37_sha256"],
           evidence["mgba"]["result_identity"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
