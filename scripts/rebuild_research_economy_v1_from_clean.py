#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からT23 Stage40を二経路で厳密再構築する。"""

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

from scripts.build_research_economy_v1 import (  # noqa: E402
    ACCEPTANCE_KEYS,
    REQUIRED_ENTRYPOINTS,
)
from tools.release.bps import apply_bps  # noqa: E402


TASK = "T23"
CONFIG = Path("config/research_economy_v1.json")
BUILDER = Path("scripts/build_research_economy_v1.py")
RUNNER = Path("tools/mgba_research_economy_v1_smoke.c")
SYMBOLS = Path("generated/runtime/research_economy_v1_symbols.json")
CASES = Path("generated/runtime/research_economy_v1_mgba_cases.json")
AUDIT = Path("reports/generated/research_economy_v1_audit.json")
COVERAGE = Path("reports/generated/research_economy_v1_coverage.json")
EVIDENCE = Path("build/stages/40_clean_rebuild.json")
REPORT = Path("reports/generated/research_economy_v1_clean_rebuild.md")


class ResearchEconomyCleanRebuildError(RuntimeError):
    """clean、Stage39/40 BPS、migrationまたはmGBA証跡の契約違反。"""


def _fail(message: str) -> NoReturn:
    raise ResearchEconomyCleanRebuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(
        value, ensure_ascii=False, sort_keys=True, indent=2,
    ) + "\n").encode("utf-8")


def _read(path: Path) -> bytes:
    try:
        return (ROOT / path).read_bytes()
    except OSError as exc:
        _fail(f"required artifact unavailable: {path}: {exc}")


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(_read(path))
    if not isinstance(value, dict):
        _fail(f"JSON root differs: {path}")
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


def _identity(raw: bytes, model: Mapping[str, Any], label: str) -> None:
    if model.get("size") is not None and len(raw) != int(model["size"]):
        _fail(f"{label} size differs")
    if _sha(raw) != str(model["sha256"]):
        _fail(f"{label} SHA-256 differs")


def _validate_mgba(
    document: Mapping[str, Any], mode: str, identities: Mapping[str, str],
) -> None:
    tests = document.get("tests")
    acceptance = document.get("acceptance_checks")
    if (
        document.get("schema_version") != 1
        or document.get("task") != TASK
        or document.get("mode") != mode
        or document.get("status") != "PASS"
        or document.get("process_runs") != 1
        or document.get("warnings") != 0
        or document.get("warnings_errors") != 0
        or not isinstance(document.get("result_identity"), str)
        or not document["result_identity"]
        or any(document.get(key) != value for key, value in identities.items())
        or not isinstance(tests, dict) or not tests
        or any(value is not True for value in tests.values())
        or document.get("total") != len(tests)
        or not isinstance(acceptance, dict)
        or set(acceptance) != set(ACCEPTANCE_KEYS)
        or any(value is not True for value in acceptance.values())
    ):
        _fail(f"Stage40 mGBA {mode} evidence differs")


def _validate() -> tuple[dict[str, Any], bytes]:
    config_raw = _read(CONFIG)
    config = json.loads(config_raw)
    if not isinstance(config, dict) or config.get("task") != TASK:
        _fail("Research Economy config root/task differs")
    inputs = config["inputs"]
    outputs = config["outputs"]
    clean_path = Path(inputs["clean_rom"]["path"])
    stage39_path = Path(inputs["stage39_rom"]["path"])
    stage39_metadata_path = Path(inputs["stage39_metadata"]["path"])
    stage39_allocation_path = Path(inputs["stage39_allocation"]["path"])
    stage39_direct_path = Path(inputs["stage39_clean_bps"]["path"])
    stage40_path = Path(outputs["rom"])
    metadata_path = Path(outputs["metadata"])
    allocation_path = Path(outputs["allocation"])
    incremental_path = Path(outputs["incremental_bps"])
    direct_path = Path(outputs["clean_bps"])
    migration_path = Path(outputs["migration"])

    clean = _read(clean_path)
    stage39 = _read(stage39_path)
    stage39_metadata_raw = _read(stage39_metadata_path)
    stage39_allocation_raw = _read(stage39_allocation_path)
    stage39_direct = _read(stage39_direct_path)
    stage40 = _read(stage40_path)
    metadata_raw = _read(metadata_path)
    allocation_raw = _read(allocation_path)
    incremental = _read(incremental_path)
    direct = _read(direct_path)
    migration_raw = _read(migration_path)

    _identity(clean, inputs["clean_rom"], "clean FireRed")
    _identity(stage39, inputs["stage39_rom"], "Stage39")
    if _sha(stage39_metadata_raw) != inputs["stage39_metadata"]["sha256"]:
        _fail("Stage39 metadata identity differs")
    if _sha(stage39_allocation_raw) != inputs["stage39_allocation"]["sha256"]:
        _fail("Stage39 allocation identity differs")
    if _sha(stage39_direct) != inputs["stage39_clean_bps"]["sha256"]:
        _fail("pinned clean->Stage39 BPS identity differs")
    rebuilt_stage39 = apply_bps(clean, stage39_direct)
    if rebuilt_stage39 != stage39:
        _fail("clean->Stage39 pinned BPS does not reproduce Stage39")

    metadata = json.loads(metadata_raw)
    allocation = json.loads(allocation_raw)
    migration = json.loads(migration_raw)
    if not all(isinstance(value, dict) for value in (metadata, allocation, migration)):
        _fail("Stage40 metadata/allocation/migration root differs")
    if (
        metadata.get("status") != "PASS"
        or metadata.get("task") != TASK
        or metadata.get("input", {}).get("sha256") != _sha(stage39)
        or metadata.get("output", {}).get("sha256") != _sha(stage40)
        or metadata.get("output", {}).get("size") != len(stage40)
        or metadata.get("mgba", {}).get("status") != "PASS"
        or metadata.get("mgba", {}).get("process_count") != 2
        or metadata.get("change_audit", {}).get("outside_declared_span_count") != 0
        or metadata.get("change_audit", {}).get("declared_span_overlap_count") != 0
        or metadata.get("overlap_audit")
        != {"rom": 0, "ram": 0, "save": 0, "map": 0, "hook": 0}
        or allocation.get("summaries", {}).get("overlap_count") != 0
    ):
        _fail("Stage40 metadata/allocation contract differs")

    chained = apply_bps(rebuilt_stage39, incremental)
    direct_result = apply_bps(clean, direct)
    if chained != stage40 or direct_result != stage40 or chained != direct_result:
        _fail("clean->Stage39->Stage40 and clean->Stage40 identities differ")
    if (
        metadata.get("patches", {}).get("incremental", {}).get("sha256")
        != _sha(incremental)
        or metadata["patches"]["clean_direct"].get("sha256") != _sha(direct)
        or metadata["patches"]["incremental"].get("exact") is not True
        or metadata["patches"]["clean_direct"].get("exact") is not True
    ):
        _fail("Stage40 BPS metadata differs")

    symbols_raw = _read(SYMBOLS)
    cases_raw = _read(CASES)
    runner_raw = _read(RUNNER)
    symbols = json.loads(symbols_raw)
    cases = json.loads(cases_raw)
    if not isinstance(symbols, dict) or not isinstance(cases, dict):
        _fail("runtime symbols/cases root differs")
    symbol_rows = symbols.get("symbols")
    runtime = symbols.get("runtime")
    if (
        not isinstance(symbol_rows, dict)
        or set(REQUIRED_ENTRYPOINTS) - set(symbol_rows)
        or any(
            not isinstance(symbol_rows[name], dict)
            or int(symbol_rows[name].get("address", 0)) & 1 != 1
            for name in REQUIRED_ENTRYPOINTS
        )
        or not isinstance(runtime, dict)
        or runtime.get("sha256") != metadata["runtime"]["code"]["sha256"]
        or runtime.get("address") != metadata["runtime"]["code"]["address"]
        or runtime.get("size") != metadata["runtime"]["code"]["size"]
        or tuple(cases.get("acceptance_keys", [])) != ACCEPTANCE_KEYS
        or cases.get("rom_sha256") != _sha(stage40)
    ):
        _fail("Stage40 runtime symbol/case contract differs")

    mgba_identities = {
        "rom_sha256": _sha(stage40),
        "runner_sha256": _sha(runner_raw),
        "symbols_sha256": _sha(symbols_raw),
        "cases_sha256": _sha(cases_raw),
    }
    quick_path = Path(outputs["mgba_quick"])
    full_path = Path(outputs["mgba_full"])
    quick_raw = _read(quick_path)
    full_raw = _read(full_path)
    quick = json.loads(quick_raw)
    full = json.loads(full_raw)
    if not isinstance(quick, dict) or not isinstance(full, dict):
        _fail("mGBA evidence root differs")
    _validate_mgba(quick, "quick", mgba_identities)
    _validate_mgba(full, "full", mgba_identities)
    for key in (*mgba_identities, "result_identity"):
        if quick.get(key) != full.get(key):
            _fail(f"Stage40 mGBA quick/full {key} differs")

    expected_migration_checks = {
        "new_save", "v1_to_v2", "non_owner_preserved", "outer_checksum",
        "bad_checksum_fallback", "pending_recovery",
    }
    if (
        migration.get("status") != "PASS"
        or migration.get("source_version") != 1
        or migration.get("target_version") != 2
        or migration.get("owner_offset") != 0x73F
        or migration.get("owner_size") != 64
        or set(migration.get("checks", {})) != expected_migration_checks
        or any(value is not True for value in migration["checks"].values())
        or migration.get("mgba", {}).get("status") != "PASS"
    ):
        _fail("Stage40 save migration evidence differs")

    physical = metadata.get("physical_bindings", {})
    consumers = metadata.get("consumer_bindings", {})
    dialogue = metadata.get("dialogue_reachability", {})
    field_contract = metadata.get("field_script_contract", {})
    save_v2_compatibility = metadata.get("save_v2_compatibility", {})
    if (
        physical.get("binding_count") != 9
        or physical.get("map_root_count") != 7
        or len(physical.get("rows", [])) != 9
        or consumers.get("hook_count") != 11
        or consumers.get("veneer_count") != 2
        or consumers.get("compatibility_patch_count") != 1
        or dialogue.get("dialogue_count") != 35
        or dialogue.get("unreachable_count") != 0
        or not field_contract.get("freeze_release")
        or save_v2_compatibility.get("patch_count") != 1
        or save_v2_compatibility.get("stage39_version_compare") != 1
        or save_v2_compatibility.get("stage40_version_compare") != 2
        or save_v2_compatibility.get("rows", [{}])[0].get("replacement_hex")
        != "022a"
    ):
        _fail("Stage40 physical/rooted field contract differs")

    audit_raw = _read(AUDIT)
    coverage_raw = _read(COVERAGE)
    audit = json.loads(audit_raw)
    coverage = json.loads(coverage_raw)
    if (
        not isinstance(audit, dict) or audit.get("status") != "PASS"
        or not isinstance(coverage, dict) or coverage.get("status") != "PASS"
        or set(coverage.get("acceptance", {})) != set(ACCEPTANCE_KEYS)
        or any(
            row.get("status") != "PASS"
            or not all(row.get("evidence", {}).get("checks", {}).values())
            for row in coverage.get("acceptance", {}).values()
        )
    ):
        _fail("Stage40 tracked audit/coverage evidence differs")

    evidence = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "method": (
            "PINNED_CLEAN_TO_STAGE39_BPS_PLUS_STAGE40_SERIALIZER_"
            "AND_DIRECT_CROSSCHECK"
        ),
        "input_output": {
            "clean_sha256": _sha(clean),
            "stage39_sha256": _sha(stage39),
            "stage40_sha256": _sha(stage40),
            "stage40_metadata_sha256": _sha(metadata_raw),
            "stage40_allocation_sha256": _sha(allocation_raw),
            "migration_sha256": _sha(migration_raw),
            "audit_sha256": _sha(audit_raw),
            "coverage_sha256": _sha(coverage_raw),
        },
        "chain": [
            {"artifact": clean_path.as_posix(), "sha256": _sha(clean), "size": len(clean)},
            {"artifact": stage39_direct_path.as_posix(), "sha256": _sha(stage39_direct), "size": len(stage39_direct)},
            {"artifact": stage39_path.as_posix(), "sha256": _sha(stage39), "size": len(stage39)},
            {"artifact": BUILDER.as_posix(), "sha256": _sha(_read(BUILDER))},
            {"artifact": incremental_path.as_posix(), "sha256": _sha(incremental), "size": len(incremental)},
            {"artifact": stage40_path.as_posix(), "sha256": _sha(stage40), "size": len(stage40)},
        ],
        "bps": {
            "stage39_baseline": {
                "sha256": _sha(stage39_direct), "size": len(stage39_direct),
                "round_trip_exact": True,
            },
            "stage39_incremental": {
                "sha256": _sha(incremental), "size": len(incremental),
                "round_trip_exact": True,
            },
            "clean_direct": {
                "sha256": _sha(direct), "size": len(direct),
                "round_trip_exact": True,
            },
            "chain_direct_identity_equal": True,
        },
        "declared_span": {
            "changed_byte_count": metadata["change_audit"]["changed_byte_count"],
            "outside_declared_span_count": 0,
            "declared_span_overlap_count": 0,
        },
        "allocator_overlap_count": 0,
        "runtime_contract": {
            "required_export_count": len(REQUIRED_ENTRYPOINTS),
            "runtime_address": runtime["address"],
            "runtime_size": runtime["size"],
            "runtime_sha256": runtime["sha256"],
            "symbols_sha256": _sha(symbols_raw),
            "cases_sha256": _sha(cases_raw),
            "deterministic_double_build": True,
        },
        "physical_contract": {
            "binding_count": 9, "map_root_count": 7,
            "hook_count": 11, "veneer_count": 2,
            "save_v2_compatibility_patch_count": 1,
            "dialogue_count": 35, "unreachable_dialogue_count": 0,
            "freeze_release_exact": True,
        },
        "save_migration": {
            "source_version": 1, "target_version": 2,
            "owner_offset": 0x73F, "owner_size": 64,
            "checks": migration["checks"],
        },
        "mgba": {
            "process_count": 2,
            "result_identity": quick["result_identity"],
            "quick_artifact_sha256": _sha(quick_raw),
            "full_artifact_sha256": _sha(full_raw),
            "warnings": 0, "warnings_errors": 0,
            **mgba_identities,
        },
        "acceptance": {
            key: coverage["acceptance"][key]["status"] == "PASS"
            for key in ACCEPTANCE_KEYS
        },
        "inputs": {
            "config_sha256": _sha(config_raw),
            "stage39_metadata_sha256": _sha(stage39_metadata_raw),
            "stage39_allocation_sha256": _sha(stage39_allocation_raw),
        },
    }
    if any(value is not True for value in evidence["acceptance"].values()):
        _fail("Stage40 acceptance evidence is incomplete")
    report = f"""# T23 Research Economy V1 clean rebuild

- clean FireRed日本版Rev.0→Stage39→Stage40 chainとclean→Stage40直接BPSが同一ROMになった。
- Stage39 baseline、Stage39→40 incremental、clean直接BPSを完全往復した。
- allocator/declared-span overlap 0、declared span外変更0。
- 9 physical host、7 map root、11 hook、2 veneer、35 dialogueを再照合した。
- save v1→v2 migrationとmGBA quick/full独立2 processをPASSした。

- Stage39 SHA-256: `{evidence['input_output']['stage39_sha256']}`
- Stage40 SHA-256: `{evidence['input_output']['stage40_sha256']}`
- result identity: `{evidence['mgba']['result_identity']}`
""".encode("utf-8")
    return evidence, report


def _execute(mode: str) -> dict[str, Any]:
    _run(
        [sys.executable, BUILDER.as_posix(), mode],
        f"Stage40 serializer/mGBA {mode}",
    )
    evidence, report = _validate()
    expected = _stable(evidence)
    if mode == "build":
        _atomic_write(EVIDENCE, expected)
        _atomic_write(REPORT, report)
    else:
        if _read(EVIDENCE) != expected or _read(REPORT) != report:
            _fail("Stage40 clean-rebuild evidence differs")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = _execute(args.mode)
    except (
        OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
        subprocess.SubprocessError, ResearchEconomyCleanRebuildError,
    ) as error:
        print(f"Research Economy V1 clean rebuild {args.mode} failed: {error}", file=sys.stderr)
        return 1
    print(
        "Research Economy V1 clean rebuild %s: PASS stage40=%s processes=2"
        % (args.mode, evidence["input_output"]["stage40_sha256"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
