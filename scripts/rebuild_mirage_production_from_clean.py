#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からT21 Stage38を厳密再構築する。

固定Stage37をclean直接BPSで再構築し、Stage37→38 incremental BPSと
clean→Stage38直接BPSが同じ32 MiB ROMになることを検証する。さらに
metadata、allocator、mGBA quick/full独立processの証跡を固定する。
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

from tools.release.bps import apply_bps  # noqa: E402


TASK = "T21"
ROM_SIZE = 32 * 1024 * 1024
CLEAN = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
STAGE37 = Path("build/stages/37_event_design.gba")
STAGE37_META = Path("build/stages/37_event_design.json")
STAGE37_ALLOC = Path("build/stages/37_allocation.json")
STAGE37_CLEAN_PATCH = Path(
    "build/patches/firered-jpn-rev0-to-event-design-stage37.bps"
)
BUILDER = Path("scripts/build_mirage_production.py")
STAGE38 = Path("build/stages/38_mirage_production.gba")
STAGE38_META = Path("build/stages/38_mirage_production.json")
STAGE38_ALLOC = Path("build/stages/38_allocation.json")
INCREMENTAL = Path(
    "build/patches/event-design-stage37-to-mirage-production-stage38.bps"
)
DIRECT = Path(
    "build/patches/firered-jpn-rev0-to-mirage-production-stage38.bps"
)
MGBA_QUICK = Path("build/stages/38_mgba_mirage_production_quick.json")
MGBA_FULL = Path("build/stages/38_mgba_mirage_production_full.json")
SYMBOLS = Path("generated/runtime/mirage_production_symbols.json")
EVIDENCE = Path("build/stages/38_clean_rebuild.json")
REPORT = Path("reports/generated/mirage_production_clean_rebuild.md")

REQUIRED_ENTRYPOINTS = {
    "MirageProduction_Probe",
    "MirageProduction_FieldEnter",
    "MirageProduction_CommitSelection",
    "MirageProduction_CommitRound4Mechanic",
    "MirageProduction_PrepareBattle",
    "MirageProduction_FinalizeBattleCopy",
    "MirageProduction_AfterBattle",
    "MirageProduction_Complete",
    "MirageProduction_Abort",
    "MirageProduction_Recover",
    "MirageProduction_MapTransitionRecover",
    "MirageProduction_SaveLoadAdapter",
    "MirageProduction_BuildTrainerPartyAdapter",
    "MirageProduction_LoadProperAbilityBattleDataAdapter",
    "MirageProduction_TestWarpToReception",
    "MirageProduction_TestInjectPersistenceFault",
}
ABILITY_ROOT_ADDRESS = 0x090973FC
ABILITY_ROOT_EXPECTED = bytes.fromhex("6bf298fd")

CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
STAGE37_SHA256 = "76d4f6a4005a815e6faf33f2ae24c18c2a7b4a1fe6f1f313e6f1837ecaf5cb7c"
STAGE37_META_SHA256 = "712ecdcd15b7fd7ac3003771eca45fd6ffd6e4dcb410436e3204e0862f1d9873"
STAGE37_ALLOC_SHA256 = "a7d2fc5dbcc4b31920fe05f45ccde49abf211db03ca0b459efa3512e9ac8660c"
STAGE37_CLEAN_PATCH_SHA256 = (
    "bb7a417791b2a944a3663cc6d5c69d3b360d5c40f1c01b7bc2b09547826669ce"
)


class MirageProductionCleanRebuildError(RuntimeError):
    """固定入力、BPS chain、mGBAまたは再構築証跡の契約違反。"""


def _fail(message: str) -> NoReturn:
    raise MirageProductionCleanRebuildError(message)


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
    try:
        value = json.loads(_read(path))
    except json.JSONDecodeError as exc:
        _fail(f"JSON artifact is invalid: {path}: {exc}")
    if not isinstance(value, dict):
        _fail(f"JSON artifact root is not an object: {path}")
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
    actual = _sha(raw)
    if len(raw) != size or actual != digest:
        _fail(
            f"{label} identity differs: size={len(raw)}/{size} "
            f"sha256={actual}/{digest}"
        )


def _patch_record(metadata: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    """T19/T20のrelease_patchesとT21のpatches表記を厳密値で受ける。"""
    for owner in ("patches", "release_patches"):
        records = metadata.get(owner)
        if isinstance(records, Mapping):
            record = records.get(key)
            if isinstance(record, Mapping):
                return record
    _fail(f"Stage38 patch metadata is unavailable: {key}")


def _mgba(path: Path, mode: str, rom_sha256: str) -> dict[str, Any]:
    value = _json(path)
    checks = value.get("checks")
    acceptance = value.get("acceptance_checks")
    if (
        value.get("status") != "PASS"
        or value.get("mode") != mode
        or value.get("rom_sha256") != rom_sha256
        or value.get("warnings_errors") != 0
        or value.get("process_runs") != 1
        or not isinstance(checks, Mapping)
        or not checks
        or any(result is not True for result in checks.values())
        or not isinstance(acceptance, Mapping)
        or len(acceptance) != 15
        or any(result is not True for result in acceptance.values())
    ):
        _fail(f"mGBA {mode} evidence is not exact all-PASS")
    identity = value.get("result_identity")
    if not isinstance(identity, str) or not identity:
        _fail(f"mGBA {mode} result identity is unavailable")
    return value


def _validate() -> tuple[dict[str, Any], bytes]:
    clean = _read(CLEAN)
    stage37 = _read(STAGE37)
    stage38 = _read(STAGE38)
    _identity(clean, 16 * 1024 * 1024, CLEAN_SHA256, "clean FireRed")
    _identity(stage37, ROM_SIZE, STAGE37_SHA256, "Stage37")
    if _sha(_read(STAGE37_META)) != STAGE37_META_SHA256:
        _fail("Stage37 metadata identity differs")
    if _sha(_read(STAGE37_ALLOC)) != STAGE37_ALLOC_SHA256:
        _fail("Stage37 allocation identity differs")
    stage37_clean_patch = _read(STAGE37_CLEAN_PATCH)
    if _sha(stage37_clean_patch) != STAGE37_CLEAN_PATCH_SHA256:
        _fail("clean->Stage37 BPS identity differs")
    stage37_from_clean = apply_bps(clean, stage37_clean_patch)
    if stage37_from_clean != stage37:
        _fail("clean->Stage37 direct BPS round trip differs")

    metadata = _json(STAGE38_META)
    allocation = _json(STAGE38_ALLOC)
    symbols = _json(SYMBOLS)
    output = metadata.get("output")
    output_sha256 = output.get("sha256") if isinstance(output, Mapping) else None
    if not isinstance(output_sha256, str) or len(output_sha256) != 64:
        _fail("Stage38 output identity is unavailable")
    _identity(stage38, ROM_SIZE, output_sha256, "Stage38")
    change_audit = metadata.get("change_audit")
    summaries = allocation.get("summaries")
    runtime_ram = metadata.get("runtime_ram")
    if (
        metadata.get("status") != "PASS"
        or not isinstance(metadata.get("input"), Mapping)
        or metadata["input"].get("sha256") != STAGE37_SHA256
        or not isinstance(metadata.get("clean_input"), Mapping)
        or metadata["clean_input"].get("sha256") != CLEAN_SHA256
        or not isinstance(change_audit, Mapping)
        or change_audit.get("outside_declared_span_count") != 0
        or change_audit.get("declared_span_overlap_count") != 0
        or not isinstance(summaries, Mapping)
        or summaries.get("overlap_count") != 0
        or not isinstance(runtime_ram, Mapping)
        or runtime_ram.get("address") != 0x0203EE00
        or runtime_ram.get("end_exclusive") != 0x0203F098
        or runtime_ram.get("size") != 664
        or runtime_ram.get("end_exclusive", 0) > 0x0203F101
    ):
        _fail("Stage38 metadata/allocation contract differs")

    entrypoints = symbols.get("entrypoints")
    physical = metadata.get("physical_bindings")
    root_patches = physical.get("root_patches") if isinstance(physical, Mapping) else None
    if (
        not isinstance(entrypoints, Mapping)
        or set(entrypoints) != REQUIRED_ENTRYPOINTS
        or not isinstance(root_patches, list)
        or physical.get("root_patch_count") != 7
        or len(root_patches) != 7
    ):
        _fail("Stage38 16-export/7-root runtime contract differs")
    ability_roots = [
        row for row in root_patches
        if isinstance(row, Mapping) and row.get("name") == "MIRAGE_ABILITY_LOAD_CHAIN"
    ]
    if len(ability_roots) != 1:
        _fail("Stage38 authored-ability rooted binding is unavailable")
    ability_root = ability_roots[0]
    ability_offset = ABILITY_ROOT_ADDRESS - 0x08000000
    replacement = bytes.fromhex(str(ability_root.get("replacement_hex", "")))
    if (
        ability_root.get("address") != ABILITY_ROOT_ADDRESS
        or ability_root.get("expected_hex") != ABILITY_ROOT_EXPECTED.hex()
        or ability_root.get("target_symbol")
            != "native::MirageProduction_LoadProperAbilityBattleDataAdapter"
        or ability_root.get("target")
            != entrypoints["MirageProduction_LoadProperAbilityBattleDataAdapter"]
        or stage37[ability_offset:ability_offset + 4] != ABILITY_ROOT_EXPECTED
        or stage38[ability_offset:ability_offset + len(replacement)] != replacement
    ):
        _fail("Stage38 authored-ability expected-byte binding differs")

    scripts = symbols.get("scripts")
    trainerbattle_rows = scripts.get("trainerbattle_rows") \
        if isinstance(scripts, Mapping) else None
    if (
        not isinstance(scripts, Mapping)
        or scripts.get("trainerbattle_command") != 0x5C
        or scripts.get("trainerbattle_mode") != 3
        or scripts.get("trainerbattle_mode_name") != "SINGLE_NO_INTRO"
        or scripts.get("trainerbattle_local_id") != 1
        or scripts.get("trainerbattle_live_flags") != 0x0C
        or scripts.get("trainerbattle_required_flags")
            != {"IS_MASTER": 0x04, "TRAINER": 0x08}
        or scripts.get("trainerbattle_authored_flags") != ["TRAINER"]
        or scripts.get("trainerbattle_engine_owned_flags") != ["IS_MASTER"]
        or scripts.get("trainerbattle_forbidden_flags")
            != ["DOUBLE", "LINK", "MULTI", "FRONTIER"]
        or scripts.get("trainerbattle_forbidden_flags_zero") is not True
        or scripts.get("trainerbattle_launch_count") != 28
        or scripts.get("direct_bare_battlebegin_count") != 0
        or scripts.get("map_script_installed") is not True
        or scripts.get("map_script_type") != 3
        or not isinstance(scripts.get("map_transition_recovery"), Mapping)
        or scripts["map_transition_recovery"].get("entrypoint")
            != "MirageProduction_MapTransitionRecover"
        or scripts["map_transition_recovery"].get("direct_recover_call")
            is not False
        or scripts["map_transition_recovery"].get("active_challenge")
            != "SKIP_KEEP_JOURNAL_STATUS_OK"
        or scripts["map_transition_recovery"].get("inactive_challenge")
            != "RECOVER_STALE_STATE"
        or scripts.get("first_trainerbattle_script")
            != "script::mirage_battle_01_after"
        or not isinstance(trainerbattle_rows, list)
        or len(trainerbattle_rows) != 28
        or any(
            not isinstance(row, Mapping)
            or row.get("opcode") != 0x5C
            or row.get("mode") != 3
            or row.get("local_id") != 1
            or row.get("continuation") != "MirageProduction_AfterBattle"
            for row in trainerbattle_rows
        )
    ):
        _fail("Stage38 canonical trainerbattle field graph differs")

    incremental = _read(INCREMENTAL)
    chained = apply_bps(stage37_from_clean, incremental)
    direct = _read(DIRECT)
    directly_rebuilt = apply_bps(clean, direct)
    if chained != stage38 or directly_rebuilt != stage38 or chained != directly_rebuilt:
        _fail("clean->Stage37->Stage38/direct Stage38 identity differs")
    incremental_record = _patch_record(metadata, "incremental")
    direct_record = _patch_record(metadata, "clean_direct")
    if (
        incremental_record.get("sha256") != _sha(incremental)
        or incremental_record.get("exact") is not True
        or direct_record.get("sha256") != _sha(direct)
        or direct_record.get("exact") is not True
    ):
        _fail("Stage38 release patch metadata differs")

    quick = _mgba(MGBA_QUICK, "quick", output_sha256)
    full = _mgba(MGBA_FULL, "full", output_sha256)
    for key in ("result_identity", "runner_sha256", "symbols_sha256", "cases_sha256"):
        if quick.get(key) != full.get(key):
            _fail(f"mGBA quick/full {key} differs")

    evidence = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "method": "PINNED_CLEAN_TO_STAGE37_BPS_PLUS_STAGE38_SERIALIZER_AND_DIRECT_CROSSCHECK",
        "input_output": {
            "clean_sha256": _sha(clean),
            "stage37_sha256": _sha(stage37),
            "stage38_sha256": _sha(stage38),
            "stage37_metadata_sha256": _sha(_read(STAGE37_META)),
            "stage37_allocation_sha256": _sha(_read(STAGE37_ALLOC)),
            "stage38_metadata_sha256": _sha(_read(STAGE38_META)),
            "stage38_allocation_sha256": _sha(_read(STAGE38_ALLOC)),
        },
        "chain": [
            {"artifact": CLEAN.as_posix(), "sha256": _sha(clean), "size": len(clean)},
            {
                "artifact": STAGE37_CLEAN_PATCH.as_posix(),
                "sha256": _sha(stage37_clean_patch),
                "size": len(stage37_clean_patch),
            },
            {"artifact": STAGE37.as_posix(), "sha256": _sha(stage37), "size": len(stage37)},
            {"artifact": BUILDER.as_posix(), "sha256": _sha(_read(BUILDER))},
            {
                "artifact": INCREMENTAL.as_posix(),
                "sha256": _sha(incremental),
                "size": len(incremental),
            },
            {"artifact": STAGE38.as_posix(), "sha256": _sha(stage38), "size": len(stage38)},
        ],
        "bps": {
            "stage37_incremental": {
                "sha256": _sha(incremental), "round_trip_exact": True,
            },
            "clean_direct": {
                "sha256": _sha(direct), "size": len(direct),
                "round_trip_exact": True,
            },
            "chain_direct_identity_equal": True,
        },
        "declared_span": {
            "changed_byte_count": change_audit.get("changed_byte_count"),
            "outside_declared_span_count": 0,
            "declared_span_overlap_count": 0,
        },
        "allocator_overlap_count": 0,
        "runtime_contract": {
            "required_export_count": 16,
            "root_patch_count": 7,
            "ability_root_address": f"0x{ABILITY_ROOT_ADDRESS:08X}",
            "ability_root_expected_hex": ABILITY_ROOT_EXPECTED.hex(),
            "ability_adapter":
                "MirageProduction_LoadProperAbilityBattleDataAdapter",
            "trainerbattle_command": 0x5C,
            "trainerbattle_mode": 3,
            "trainerbattle_launch_count": 28,
            "direct_bare_battlebegin_count": 0,
            "runtime_state_address": "0x0203EE00",
            "runtime_state_end_exclusive": "0x0203F098",
            "runtime_state_size": 664,
            "ui_help_video_state_address": "0x0203F101",
        },
        "mgba": {
            "process_count": 2,
            "result_identity": quick["result_identity"],
            "quick_artifact_sha256": _sha(_read(MGBA_QUICK)),
            "full_artifact_sha256": _sha(_read(MGBA_FULL)),
            "warnings_errors": 0,
        },
    }
    report = f"""# T21 Mirage production clean rebuild

## 結論

- clean FireRed日本版Rev.0→Stage37→Stage38 chainとclean→Stage38直接BPSが同一ROMになった。
- Stage37→38 incremental BPS、clean直接BPSを完全往復した。
- allocator/declared-span overlap 0、declared span外変更0。
    - production runtimeはrequired export 16件、expected-byte root 7件（active-safe map transitionとauthored ability chainを含む）。
    - field実戦はcanonical trainerbattle 0x5C/mode3を28件持ち、bare 0x5D直行は0件。
- mGBA quick/full独立2 processはwarnings/errors 0、result identity一致。

## Identity

- clean SHA-256: `{evidence['input_output']['clean_sha256']}`
- Stage37 SHA-256: `{evidence['input_output']['stage37_sha256']}`
- Stage38 SHA-256: `{evidence['input_output']['stage38_sha256']}`
- result identity: `{evidence['mgba']['result_identity']}`
""".encode("utf-8")
    return evidence, report


def _execute(mode: str) -> dict[str, Any]:
    _run([sys.executable, BUILDER.as_posix(), mode], f"Stage38 serializer/mGBA {mode}")
    evidence, report = _validate()
    expected = _stable(evidence)
    if mode == "build":
        _atomic_write(EVIDENCE, expected)
        _atomic_write(REPORT, report)
    else:
        if _read(EVIDENCE) != expected:
            _fail("Stage38 clean rebuild evidence differs")
        if _read(REPORT) != report:
            _fail("Stage38 clean rebuild report differs")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = _execute(args.mode)
    except (
        OSError, ValueError, KeyError, json.JSONDecodeError,
        MirageProductionCleanRebuildError,
    ) as exc:
        print(f"Mirage production clean rebuild {args.mode}: FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "Mirage production clean rebuild %s: PASS rom=%s identity=%s"
        % (
            args.mode,
            evidence["input_output"]["stage38_sha256"],
            evidence["mgba"]["result_identity"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
