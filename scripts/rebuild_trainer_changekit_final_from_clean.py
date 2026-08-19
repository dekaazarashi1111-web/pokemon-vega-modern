#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からTrainer ChangeKit最終ROMを厳密再構築する。

固定済みv1.4.0 release BPS、Stage34累積BPS、Stage35 serializerを順に使い、
各境界のSHA-256とBPS往復を検証する。元ROMや入力ZIPは変更しない。
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
from typing import Any, Mapping, NoReturn


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.bps import apply_bps, create_bps  # noqa: E402


TASK = "USER-20260819-TRAINER-CHANGEKIT-FINAL-INTEGRATION"
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
BASE_PATCH = Path("build/patches/firered-jpn-rev0-to-vega-modern-kanto-v1.4.0.bps")
BASE_ROM = Path("build/final/vega-modern-kanto-v1.4.0.gba")
STAGE34_PATCH = Path("build/patches/vega-modern-kanto-v1.4.0-to-trainer-v5-stage34.bps")
STAGE34_ROM = Path("build/stages/34_trainer_v5_tohoku_batch03.gba")
STAGE34_META = Path("build/stages/34_trainer_v5_tohoku_batch03.json")
STAGE34_ALLOC = Path("build/stages/34_allocation.json")
STAGE35_ROM = Path("build/stages/35_trainer_changekit_final.gba")
STAGE35_META = Path("build/stages/35_trainer_changekit_final.json")
STAGE35_INCREMENTAL = Path("build/patches/trainer-stage34-to-changekit-final-stage35.bps")
STAGE35_BASE_PATCH = Path("build/patches/vega-modern-kanto-v1.4.0-to-trainer-changekit-final-stage35.bps")
STAGE35_CLEAN_PATCH = Path("build/patches/firered-jpn-rev0-to-trainer-changekit-final-stage35.bps")
MGBA_QUICK = Path("build/stages/35_mgba_trainer_changekit_quick.json")
MGBA_FULL = Path("build/stages/35_mgba_trainer_changekit_full.json")
EVIDENCE = Path("build/stages/35_clean_rebuild.json")
REPORT = Path("reports/generated/trainer_changekit_clean_rebuild.md")

CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
BASE_PATCH_SHA256 = "0b69b5de39e29168929f36750049c29f2064f290215112384449f1e4b38f418e"
BASE_SHA256 = "30f19ee3ebab856379393a572bfde33c2ccfdac7351e73ff3a7f3e231f3f553e"
STAGE34_PATCH_SHA256 = "49c9e27b422e3d4bf78dcd6790b155c266e40d9ed100636034b47bf3333a5fab"
STAGE34_SHA256 = "84395df49b5cee3fa83b501714828fa03db29bc24b1ed0f1a9cb292e1437946f"
STAGE35_SHA256 = "2ff8d61d7e17d120eaf60a81863dc29f6666d84c48a245e1be3d8dfa2447d180"


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


def _rebuild_prefix(*, write: bool) -> tuple[bytes, bytes, bytes]:
    clean = _read(CLEAN_ROM)
    base_patch = _read(BASE_PATCH)
    stage34_patch = _read(STAGE34_PATCH)
    _expect(clean, CLEAN_SHA256, 16 * 1024 * 1024, "clean FireRed")
    if _sha(base_patch) != BASE_PATCH_SHA256:
        _fail("v1.4.0 clean release BPS hash differs")
    if _sha(stage34_patch) != STAGE34_PATCH_SHA256:
        _fail("Stage34 cumulative BPS hash differs")

    base = apply_bps(clean, base_patch)
    _expect(base, BASE_SHA256, 32 * 1024 * 1024, "v1.4.0 base")
    stage34 = apply_bps(base, stage34_patch)
    _expect(stage34, STAGE34_SHA256, 32 * 1024 * 1024, "Stage34")
    if write:
        _atomic_write(BASE_ROM, base)
        _atomic_write(STAGE34_ROM, stage34)
    else:
        if _read(BASE_ROM) != base:
            _fail("published v1.4.0 base differs from clean reconstruction")
        if _read(STAGE34_ROM) != stage34:
            _fail("published Stage34 differs from clean reconstruction")

    metadata = _json(STAGE34_META)
    allocation = _json(STAGE34_ALLOC)
    if metadata.get("output", {}).get("sha256") != STAGE34_SHA256:
        _fail("Stage34 metadata target hash differs")
    if allocation.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage34 allocation contains an overlap")
    return clean, base, stage34


def _direct_patch_metadata() -> bytes:
    return _stable({
        "format": "BPS1",
        "task": TASK,
        "source_sha256": CLEAN_SHA256,
        "target_sha256": STAGE35_SHA256,
    })


def _validate_mgba(path: Path, mode: str) -> dict[str, Any]:
    value = _json(path)
    if (
        value.get("status") != "PASS"
        or value.get("mode") != mode
        or value.get("rom_sha256") != STAGE35_SHA256
        or value.get("warnings_errors") != 0
        or not value.get("checks")
        or not all(value["checks"].values())
    ):
        _fail(f"mGBA {mode} evidence is not exact all-PASS")
    return value


def _expected_evidence(
    clean: bytes,
    base: bytes,
    stage34: bytes,
    final: bytes,
    direct_patch: bytes,
    quick: Mapping[str, Any],
    full: Mapping[str, Any],
) -> dict[str, Any]:
    metadata = _json(STAGE35_META)
    return {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "method": "PINNED_EXACT_BPS_CHAIN_PLUS_STAGE35_SERIALIZER",
        "chain": [
            {"artifact": CLEAN_ROM.as_posix(), "sha256": _sha(clean), "size": len(clean)},
            {"artifact": BASE_PATCH.as_posix(), "sha256": _sha(_read(BASE_PATCH))},
            {"artifact": BASE_ROM.as_posix(), "sha256": _sha(base), "size": len(base)},
            {"artifact": STAGE34_PATCH.as_posix(), "sha256": _sha(_read(STAGE34_PATCH))},
            {"artifact": STAGE34_ROM.as_posix(), "sha256": _sha(stage34), "size": len(stage34)},
            {"artifact": STAGE35_INCREMENTAL.as_posix(),
             "sha256": _sha(_read(STAGE35_INCREMENTAL))},
            {"artifact": STAGE35_ROM.as_posix(), "sha256": _sha(final), "size": len(final)},
        ],
        "direct_clean_patch": {
            "artifact": STAGE35_CLEAN_PATCH.as_posix(),
            "sha256": _sha(direct_patch),
            "size": len(direct_patch),
            "round_trip_exact": True,
        },
        "coverage": metadata["coverage"],
        "runtime_ram": metadata["runtime_ram"],
        "allocator_overlap_count": metadata["allocation"]["overlap_count"],
        "changed_outside_declared_span_count": metadata["change_audit"][
            "outside_declared_span_count"
        ],
        "mgba": {
            "quick": {"status": quick["status"], "checks": quick["checks"],
                      "warnings_errors": quick["warnings_errors"]},
            "full": {"status": full["status"], "checks": full["checks"],
                     "warnings_errors": full["warnings_errors"],
                     "coverage": full["coverage"]},
        },
    }


def _report(evidence: Mapping[str, Any]) -> bytes:
    coverage = evidence["coverage"]
    full = evidence["mgba"]["full"]["coverage"]
    return f"""# Trainer ChangeKit clean rebuild

## 結論

- clean FireRed日本版Rev.0から固定v1.4.0 BPS、Stage34累積BPS、Stage35 serializerを順に適用し、各境界をSHA-256で照合した。
- cleanからStage35への直接BPSも再生成し、32 MiB最終ROMへのexact round-tripを確認した。
- 全{coverage['encounter_count']}戦・{coverage['member_count']}体、SINGLE {coverage['battle_format_counts']['SINGLE']} / DOUBLE {coverage['battle_format_counts']['DOUBLE']}をserializeした。
- mGBA quick/fullは全check PASS、warning/error 0。fullはrematch {full['rematches']}、kind8 {full['kind8']}、Mega {full['mega']}、Zワザ {full['z_move']}、ダイマックス {full['dynamax']}、テラスタル {full['terastal']}を観測した。
- allocator overlap 0、declared span外変更0、runtime EWRAM overlap 0。

## 最終identity

- ROM SHA-256: `{STAGE35_SHA256}`
- clean直接BPS SHA-256: `{evidence['direct_clean_patch']['sha256']}`
- clean直接BPS size: {evidence['direct_clean_patch']['size']} bytes
""".encode("utf-8")


def _finalize(clean: bytes, base: bytes, stage34: bytes, *, write: bool) -> dict[str, Any]:
    final = _read(STAGE35_ROM)
    _expect(final, STAGE35_SHA256, 32 * 1024 * 1024, "Stage35")
    if apply_bps(stage34, _read(STAGE35_INCREMENTAL)) != final:
        _fail("Stage34 incremental BPS round trip differs")
    if apply_bps(base, _read(STAGE35_BASE_PATCH)) != final:
        _fail("v1.4.0 cumulative Stage35 BPS round trip differs")
    direct_patch = create_bps(clean, final, metadata=_direct_patch_metadata())
    if apply_bps(clean, direct_patch) != final:
        _fail("clean direct Stage35 BPS round trip differs")
    if write:
        _atomic_write(STAGE35_CLEAN_PATCH, direct_patch)
    elif _read(STAGE35_CLEAN_PATCH) != direct_patch:
        _fail("published clean direct Stage35 BPS differs")
    quick = _validate_mgba(MGBA_QUICK, "quick")
    full = _validate_mgba(MGBA_FULL, "full")
    evidence = _expected_evidence(
        clean, base, stage34, final, direct_patch, quick, full
    )
    report = _report(evidence)
    if write:
        _atomic_write(EVIDENCE, _stable(evidence))
        _atomic_write(REPORT, report)
    else:
        if _read(EVIDENCE) != _stable(evidence):
            _fail("clean rebuild evidence differs")
        if _read(REPORT) != report:
            _fail("clean rebuild report differs")
    return evidence


def build() -> dict[str, Any]:
    clean, base, stage34 = _rebuild_prefix(write=True)
    completed = subprocess.run(
        [sys.executable, "scripts/build_trainer_changekit_final.py", "build"],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode:
        _fail(f"Stage35 serializer/mGBA build failed ({completed.returncode})")
    return _finalize(clean, base, stage34, write=True)


def check() -> dict[str, Any]:
    clean, base, stage34 = _rebuild_prefix(write=False)
    return _finalize(clean, base, stage34, write=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = build() if args.mode == "build" else check()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, CleanRebuildError) as exc:
        print(f"Trainer ChangeKit clean rebuild {args.mode}: FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        f"Trainer ChangeKit clean rebuild {args.mode}: PASS "
        f"rom={STAGE35_SHA256} direct_bps={evidence['direct_clean_patch']['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
