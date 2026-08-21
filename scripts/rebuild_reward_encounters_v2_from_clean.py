#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からT24 Stage41を二経路で厳密再構築する。"""

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

from scripts.build_reward_encounters_v2 import (  # noqa: E402
    ACCEPTANCE_KEYS,
    REQUIRED_ENTRYPOINTS,
)
from tools.release.bps import apply_bps  # noqa: E402


TASK = "T24"
CONFIG = Path("config/reward_encounters_v2.json")
BUILDER = Path("scripts/build_reward_encounters_v2.py")
RUNNER = Path("tools/mgba_reward_encounters_v2_smoke.c")
SYMBOLS = Path("generated/runtime/reward_encounters_v2_symbols.json")
CASES = Path("generated/runtime/reward_encounters_v2_mgba_cases.json")
AUDIT = Path("reports/generated/reward_encounters_v2_audit.json")
COVERAGE = Path("reports/generated/reward_encounters_v2_coverage.json")
REPORT = Path("reports/generated/reward_encounters_v2_clean_rebuild.md")


class RewardEncountersCleanRebuildError(RuntimeError):
    """clean、Stage40/41 BPSまたはmGBA証跡の契約違反。"""


def _fail(message: str) -> NoReturn:
    raise RewardEncountersCleanRebuildError(message)


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
    coverage = document.get("coverage")
    if (
        document.get("schema_version") != 1
        or document.get("task") != TASK
        or document.get("mode") != mode
        or document.get("status") != "PASS"
        or document.get("process_runs") != 1
        or document.get("warnings") != 0
        or document.get("warnings_errors") != 0
        or any(document.get(key) != value for key, value in identities.items())
        or not isinstance(tests, dict) or not tests
        or any(value is not True for value in tests.values())
        or document.get("total") != len(tests)
        or not isinstance(acceptance, dict)
        or set(acceptance) != set(ACCEPTANCE_KEYS)
        or any(value is not True for value in acceptance.values())
        or not isinstance(coverage, dict)
        or coverage.get("transaction_rows") != 32
    ):
        _fail(f"Stage41 mGBA {mode} evidence differs")


def _validate() -> tuple[dict[str, Any], bytes, Path]:
    config_raw = _read(CONFIG)
    config = json.loads(config_raw)
    if not isinstance(config, dict) or config.get("task") != TASK:
        _fail("Reward Encounters config root/task differs")
    inputs = config["inputs"]
    outputs = config["outputs"]
    clean_path = Path(inputs["clean_rom"]["path"])
    stage40_path = Path(inputs["stage40_rom"]["path"])
    stage40_metadata_path = Path(inputs["stage40_metadata"]["path"])
    stage40_allocation_path = Path(inputs["stage40_allocation"]["path"])
    stage40_direct_path = Path(inputs["stage40_clean_bps"]["path"])
    submission_path = Path(inputs["submission_zip"]["path"])
    stage41_path = Path(outputs["rom"])
    metadata_path = Path(outputs["metadata"])
    allocation_path = Path(outputs["allocation"])
    incremental_path = Path(outputs["incremental_bps"])
    direct_path = Path(outputs["clean_bps"])
    matrix_path = Path(outputs["transaction_matrix"])
    evidence_path = Path(outputs["clean_rebuild"])

    clean = _read(clean_path)
    stage40 = _read(stage40_path)
    stage40_metadata_raw = _read(stage40_metadata_path)
    stage40_allocation_raw = _read(stage40_allocation_path)
    stage40_direct = _read(stage40_direct_path)
    submission = _read(submission_path)
    stage41 = _read(stage41_path)
    metadata_raw = _read(metadata_path)
    allocation_raw = _read(allocation_path)
    incremental = _read(incremental_path)
    direct = _read(direct_path)
    matrix_raw = _read(matrix_path)

    _identity(clean, inputs["clean_rom"], "clean FireRed")
    _identity(stage40, inputs["stage40_rom"], "Stage40")
    _identity(submission, inputs["submission_zip"], "private submission ZIP")
    if _sha(stage40_metadata_raw) != inputs["stage40_metadata"]["sha256"]:
        _fail("Stage40 metadata identity differs")
    if _sha(stage40_allocation_raw) != inputs["stage40_allocation"]["sha256"]:
        _fail("Stage40 allocation identity differs")
    if _sha(stage40_direct) != inputs["stage40_clean_bps"]["sha256"]:
        _fail("pinned clean->Stage40 BPS identity differs")
    rebuilt_stage40 = apply_bps(clean, stage40_direct)
    if rebuilt_stage40 != stage40:
        _fail("clean->Stage40 pinned BPS does not reproduce Stage40")

    metadata = json.loads(metadata_raw)
    allocation = json.loads(allocation_raw)
    matrix = json.loads(matrix_raw)
    if not all(isinstance(value, dict) for value in (metadata, allocation, matrix)):
        _fail("Stage41 metadata/allocation/matrix root differs")
    if (
        metadata.get("status") != "PASS"
        or metadata.get("task") != TASK
        or metadata.get("input", {}).get("sha256") != _sha(stage40)
        or metadata.get("output", {}).get("sha256") != _sha(stage41)
        or metadata.get("output", {}).get("size") != len(stage41)
        or metadata.get("content") != config["counts"]
        or metadata.get("mgba", {}).get("status") != "PASS"
        or metadata.get("mgba", {}).get("process_count") != 2
        or metadata.get("change_audit", {}).get("outside_declared_span_count") != 0
        or metadata.get("change_audit", {}).get("declared_span_overlap_count") != 0
        or metadata.get("overlap_audit")
        != {"rom": 0, "ram": 0, "save": 0, "map": 0, "hook": 0}
        or allocation.get("summaries", {}).get("overlap_count") != 0
        or any(value is not True for value in metadata.get("static_acceptance", {}).values())
    ):
        _fail("Stage41 metadata/allocation contract differs")

    chained = apply_bps(rebuilt_stage40, incremental)
    direct_result = apply_bps(clean, direct)
    if chained != stage41 or direct_result != stage41 or chained != direct_result:
        _fail("clean->Stage40->Stage41 and clean->Stage41 identities differ")
    if (
        metadata.get("patches", {}).get("incremental", {}).get("sha256")
        != _sha(incremental)
        or metadata["patches"]["clean_direct"].get("sha256") != _sha(direct)
        or metadata["patches"]["incremental"].get("exact") is not True
        or metadata["patches"]["clean_direct"].get("exact") is not True
    ):
        _fail("Stage41 BPS metadata differs")

    symbols_raw = _read(SYMBOLS)
    cases_raw = _read(CASES)
    runner_raw = _read(RUNNER)
    symbols = json.loads(symbols_raw)
    cases = json.loads(cases_raw)
    symbol_rows = symbols.get("symbols", {})
    runtime = symbols.get("runtime", {})
    if (
        not isinstance(symbol_rows, dict)
        or set(REQUIRED_ENTRYPOINTS) - set(symbol_rows)
        or any(int(symbol_rows[name].get("address", 0)) & 1 != 1
               for name in REQUIRED_ENTRYPOINTS)
        or runtime.get("sha256") != metadata["runtime"]["code"]["sha256"]
        or runtime.get("address") != metadata["runtime"]["code"]["address"]
        or runtime.get("size") != metadata["runtime"]["code"]["size"]
        or tuple(cases.get("acceptance_keys", [])) != ACCEPTANCE_KEYS
        or cases.get("rom_sha256") != _sha(stage41)
    ):
        _fail("Stage41 runtime symbol/case contract differs")

    mgba_identities = {
        "rom_sha256": _sha(stage41),
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
    _validate_mgba(quick, "quick", mgba_identities)
    _validate_mgba(full, "full", mgba_identities)
    for key in (*mgba_identities, "result_identity"):
        if quick.get(key) != full.get(key):
            _fail(f"Stage41 mGBA quick/full {key} differs")

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
            or not all(row.get("evidence", {}).values())
            for row in coverage.get("acceptance", {}).values()
        )
        or matrix.get("status") != "PASS"
        or matrix.get("row_count") != 32
        or matrix.get("rom_sha256") != _sha(stage41)
        or any(value is not True for value in matrix.get("checks", {}).values())
    ):
        _fail("Stage41 acceptance/transaction evidence differs")

    physical = metadata.get("physical_binding", {})
    factory = metadata.get("factory_inheritance", {})
    upstream = metadata.get("upstream_regression", {})
    if (
        physical.get("objects_before") != 4
        or physical.get("objects_after") != 5
        or physical.get("scientist_local_id") != 5
        or physical.get("reachable_adjacent") is not True
        or physical.get("warps_preserved") is not True
        or physical.get("coords_preserved") is not True
        or physical.get("backgrounds_preserved") is not True
        or factory.get("bytes_unchanged") is not True
        or upstream.get("stage40_status") != "PASS"
        or upstream.get("stage40_mgba_status") != "PASS"
        or upstream.get("previous_allocations_changed_outside_roots") != 0
    ):
        _fail("Stage41 rooted/upstream contract differs")

    evidence = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "method": "PINNED_CLEAN_TO_STAGE40_BPS_PLUS_STAGE41_SERIALIZER_AND_DIRECT_CROSSCHECK",
        "input_output": {
            "clean_sha256": _sha(clean),
            "stage40_sha256": _sha(stage40),
            "stage41_sha256": _sha(stage41),
            "stage41_metadata_sha256": _sha(metadata_raw),
            "stage41_allocation_sha256": _sha(allocation_raw),
            "audit_sha256": _sha(audit_raw),
            "coverage_sha256": _sha(coverage_raw),
            "transaction_matrix_sha256": _sha(matrix_raw),
        },
        "bps": {
            "stage40_baseline": {"sha256": _sha(stage40_direct), "size": len(stage40_direct), "round_trip_exact": True},
            "stage40_incremental": {"sha256": _sha(incremental), "size": len(incremental), "round_trip_exact": True},
            "clean_direct": {"sha256": _sha(direct), "size": len(direct), "round_trip_exact": True},
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
        "transaction_contract": {
            "row_count": 32,
            "checks": matrix["checks"],
        },
        "physical_contract": {
            "objects_before": 4,
            "objects_after": 5,
            "scientist_local_id": 5,
            "reachable_adjacent": True,
            "preserved_arrays": True,
        },
        "mgba": {
            "process_count": 2,
            "result_identity": quick["result_identity"],
            "quick_artifact_sha256": _sha(quick_raw),
            "full_artifact_sha256": _sha(full_raw),
            "warnings": 0,
            "warnings_errors": 0,
            **mgba_identities,
        },
        "acceptance": {
            key: coverage["acceptance"][key]["status"] == "PASS"
            for key in ACCEPTANCE_KEYS
        },
        "inputs": {
            "config_sha256": _sha(config_raw),
            "submission_sha256": _sha(submission),
            "stage40_metadata_sha256": _sha(stage40_metadata_raw),
            "stage40_allocation_sha256": _sha(stage40_allocation_raw),
        },
    }
    if any(value is not True for value in evidence["acceptance"].values()):
        _fail("Stage41 acceptance evidence is incomplete")
    report = f"""# T24 Reward Encounters V2 clean rebuild

- clean FireRed日本版Rev.0→Stage40→Stage41 chainとclean→Stage41直接BPSが同一ROMになった。
- Stage40 baseline、Stage40→41 incremental、clean直接BPSを完全往復した。
- allocator/declared-span overlap 0、declared span外変更0。
- Scientist field root、32 transaction row、T23 wild-end delegateを再照合した。
- mGBA quick/full独立2 processと全11 acceptanceをPASSした。

- Stage40 SHA-256: `{evidence['input_output']['stage40_sha256']}`
- Stage41 SHA-256: `{evidence['input_output']['stage41_sha256']}`
- result identity: `{evidence['mgba']['result_identity']}`
""".encode("utf-8")
    return evidence, report, evidence_path


def _execute(mode: str) -> dict[str, Any]:
    _run([sys.executable, BUILDER.as_posix(), mode], f"Stage41 serializer/mGBA {mode}")
    evidence, report, evidence_path = _validate()
    expected = _stable(evidence)
    if mode == "build":
        _atomic_write(evidence_path, expected)
        _atomic_write(REPORT, report)
    elif _read(evidence_path) != expected or _read(REPORT) != report:
        _fail("Stage41 clean-rebuild evidence differs")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = _execute(args.mode)
    except (
        OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
        subprocess.SubprocessError, RewardEncountersCleanRebuildError,
    ) as error:
        print(f"Reward Encounters V2 clean rebuild {args.mode} failed: {error}", file=sys.stderr)
        return 1
    print(
        "Reward Encounters V2 clean rebuild %s: PASS stage41=%s processes=2"
        % (args.mode, evidence["input_output"]["stage41_sha256"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
