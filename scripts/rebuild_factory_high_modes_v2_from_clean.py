#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からT25 Stage42を二経路で厳密再構築する。"""

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

from scripts.build_factory_high_modes_v2 import (  # noqa: E402
    ACCEPTANCE_KEYS,
    REQUIRED_ENTRYPOINTS,
)
from tools.release.bps import apply_bps  # noqa: E402


TASK = "T25"
CONFIG = Path("config/factory_high_modes_v2.json")
BUILDER = Path("scripts/build_factory_high_modes_v2.py")
RUNNER = Path("tools/mgba_factory_high_modes_v2_smoke.c")
SYMBOLS = Path("generated/runtime/factory_high_modes_v2_symbols.json")
CASES = Path("generated/runtime/factory_high_modes_v2_mgba_cases.json")
AUDIT = Path("reports/generated/factory_high_modes_v2_audit.json")
COVERAGE = Path("reports/generated/factory_high_modes_v2_coverage.json")
REPORT = Path("reports/generated/factory_high_modes_v2_clean_rebuild.md")


class FactoryHighCleanRebuildError(RuntimeError):
    """clean、Stage41/42 BPSまたはmGBA証跡の契約違反。"""


def _fail(message: str) -> NoReturn:
    raise FactoryHighCleanRebuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


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


def _identity(raw: bytes, contract: Mapping[str, Any], label: str) -> None:
    if contract.get("size") is not None and len(raw) != int(contract["size"]):
        _fail(f"{label} size differs")
    if _sha(raw) != str(contract["sha256"]):
        _fail(f"{label} SHA-256 differs")


def _validate() -> tuple[dict[str, Any], bytes, Path]:
    config_raw = _read(CONFIG)
    config = json.loads(config_raw)
    if not isinstance(config, dict) or config.get("task") != TASK:
        _fail("Factory High config root/task differs")
    inputs = config["inputs"]
    outputs = config["outputs"]
    clean = _read(Path(inputs["clean_rom"]["path"]))
    stage41 = _read(Path(inputs["stage41_rom"]["path"]))
    stage41_meta_raw = _read(Path(inputs["stage41_metadata"]["path"]))
    stage41_alloc_raw = _read(Path(inputs["stage41_allocation"]["path"]))
    stage41_direct = _read(Path(inputs["stage41_clean_bps"]["path"]))
    submission = _read(Path(inputs["submission_zip"]["path"]))
    stage42 = _read(Path(outputs["rom"]))
    metadata_raw = _read(Path(outputs["metadata"]))
    allocation_raw = _read(Path(outputs["allocation"]))
    incremental = _read(Path(outputs["incremental_bps"]))
    direct = _read(Path(outputs["clean_bps"]))
    matrix_raw = _read(Path(outputs["mode_matrix"]))
    _identity(clean, inputs["clean_rom"], "clean FireRed")
    _identity(stage41, inputs["stage41_rom"], "Stage41")
    _identity(submission, inputs["submission_zip"], "private submission ZIP")
    if (_sha(stage41_meta_raw) != inputs["stage41_metadata"]["sha256"]
            or _sha(stage41_alloc_raw) != inputs["stage41_allocation"]["sha256"]
            or _sha(stage41_direct) != inputs["stage41_clean_bps"]["sha256"]):
        _fail("Stage41 pinned evidence identity differs")
    rebuilt_stage41 = apply_bps(clean, stage41_direct)
    if rebuilt_stage41 != stage41:
        _fail("clean->Stage41 pinned BPS does not reproduce Stage41")
    chained = apply_bps(rebuilt_stage41, incremental)
    direct_result = apply_bps(clean, direct)
    if chained != stage42 or direct_result != stage42 or chained != direct_result:
        _fail("clean->Stage41->Stage42 and clean->Stage42 identities differ")

    metadata = json.loads(metadata_raw)
    allocation = json.loads(allocation_raw)
    matrix = json.loads(matrix_raw)
    if (metadata.get("task") != TASK or metadata.get("status") != "PASS"
            or metadata.get("input", {}).get("sha256") != _sha(stage41)
            or metadata.get("output", {}).get("sha256") != _sha(stage42)
            or metadata.get("output", {}).get("size") != len(stage42)
            or metadata.get("mgba", {}).get("status") != "PASS"
            or metadata.get("mgba", {}).get("process_count") != 2
            or any(value is not True
                   for value in metadata.get("static_acceptance", {}).values())
            or metadata.get("change_audit", {}).get("outside_declared_span_count") != 0
            or metadata.get("change_audit", {}).get("declared_span_overlap_count") != 0
            or metadata.get("overlap_audit")
                != {"rom": 0, "ram": 0, "save": 0, "ui": 0, "hook": 0}
            or allocation.get("summaries", {}).get("overlap_count") != 0
            or matrix.get("status") != "PASS" or matrix.get("row_count") != 7440
            or matrix.get("mgba", {}).get("status") != "PASS"
            or any(value is not True for value in matrix.get("checks", {}).values())):
        _fail("Stage42 metadata/allocation/matrix contract differs")
    if (metadata["patches"]["incremental"]["sha256"] != _sha(incremental)
            or metadata["patches"]["clean_direct"]["sha256"] != _sha(direct)
            or metadata["patches"]["incremental"]["exact"] is not True
            or metadata["patches"]["clean_direct"]["exact"] is not True):
        _fail("Stage42 BPS metadata differs")

    symbols_raw = _read(SYMBOLS)
    cases_raw = _read(CASES)
    runner_raw = _read(RUNNER)
    symbols = json.loads(symbols_raw)
    cases = json.loads(cases_raw)
    symbol_rows = symbols.get("symbols", {})
    if (set(REQUIRED_ENTRYPOINTS) - set(symbol_rows)
            or any(int(symbol_rows[name].get("address", 0)) & 1 != 1
                   for name in REQUIRED_ENTRYPOINTS)
            or tuple(cases.get("acceptance_keys", [])) != ACCEPTANCE_KEYS
            or cases.get("rom_sha256") != _sha(stage42)):
        _fail("Stage42 runtime symbol/case contract differs")
    identities = {
        "rom_sha256": _sha(stage42), "runner_sha256": _sha(runner_raw),
        "symbols_sha256": _sha(symbols_raw), "cases_sha256": _sha(cases_raw),
    }
    mgba_documents: dict[str, dict[str, Any]] = {}
    mgba_hashes: dict[str, str] = {}
    for mode, key in (("quick", "mgba_quick"), ("full", "mgba_full")):
        raw = _read(Path(outputs[key]))
        document = json.loads(raw)
        if (document.get("task") != TASK or document.get("mode") != mode
                or document.get("status") != "PASS" or document.get("process_runs") != 1
                or document.get("warnings") != 0 or document.get("warnings_errors") != 0
                or any(document.get(name) != value for name, value in identities.items())
                or any(value is not True for value in document.get("tests", {}).values())
                or set(document.get("acceptance_checks", {})) != set(ACCEPTANCE_KEYS)
                or any(value is not True
                       for value in document.get("acceptance_checks", {}).values())):
            _fail(f"Stage42 mGBA {mode} evidence differs")
        mgba_documents[mode] = document
        mgba_hashes[mode] = _sha(raw)
    if mgba_documents["quick"]["result_identity"] != mgba_documents["full"]["result_identity"]:
        _fail("Stage42 mGBA quick/full identity differs")
    audit_raw = _read(AUDIT)
    coverage_raw = _read(COVERAGE)
    audit = json.loads(audit_raw)
    coverage = json.loads(coverage_raw)
    if (audit.get("status") != "PASS" or coverage.get("status") != "PASS"
            or set(coverage.get("acceptance", {})) != set(ACCEPTANCE_KEYS)
            or any(row.get("status") != "PASS"
                   or not all(row.get("evidence", {}).values())
                   for row in coverage.get("acceptance", {}).values())):
        _fail("Stage42 acceptance evidence differs")
    evidence = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "method": "PINNED_CLEAN_TO_STAGE41_PLUS_INCREMENTAL_AND_DIRECT_CROSSCHECK",
        "input_output": {
            "clean_sha256": _sha(clean), "stage41_sha256": _sha(stage41),
            "stage42_sha256": _sha(stage42),
            "stage42_metadata_sha256": _sha(metadata_raw),
            "stage42_allocation_sha256": _sha(allocation_raw),
            "mode_matrix_sha256": _sha(matrix_raw),
            "audit_sha256": _sha(audit_raw), "coverage_sha256": _sha(coverage_raw),
        },
        "bps": {
            "stage41_baseline": {"sha256": _sha(stage41_direct),
                                 "size": len(stage41_direct), "round_trip_exact": True},
            "stage41_incremental": {"sha256": _sha(incremental),
                                    "size": len(incremental), "round_trip_exact": True},
            "clean_direct": {"sha256": _sha(direct), "size": len(direct),
                             "round_trip_exact": True},
            "chain_direct_identity_equal": True,
        },
        "declared_span": {"outside_declared_span_count": 0,
                          "declared_span_overlap_count": 0,
                          "changed_byte_count": metadata["change_audit"]["changed_byte_count"]},
        "overlap": metadata["overlap_audit"],
        "host_matrix": {"row_count": 7440, "identity": matrix["identity"],
                        "finite_bounds": matrix["finite_bounds"]},
        "runtime": {"required_export_count": len(REQUIRED_ENTRYPOINTS),
                    "symbols_sha256": _sha(symbols_raw), "cases_sha256": _sha(cases_raw)},
        "mgba": {"process_count": 2,
                 "result_identity": mgba_documents["quick"]["result_identity"],
                 "quick_artifact_sha256": mgba_hashes["quick"],
                 "full_artifact_sha256": mgba_hashes["full"], **identities},
        "acceptance": {key: True for key in ACCEPTANCE_KEYS},
        "private_submission_unchanged": _sha(submission) == inputs["submission_zip"]["sha256"],
        "inputs": {"config_sha256": _sha(config_raw),
                   "stage41_metadata_sha256": _sha(stage41_meta_raw),
                   "stage41_allocation_sha256": _sha(stage41_alloc_raw)},
    }
    report = f"""# T25 Factory High Modes V2 clean rebuild

- clean FireRed日本版Rev.0→Stage41→Stage42 chainとclean→Stage42直接BPSが同一ROMになった。
- 7,440-row host matrix、mGBA quick/full独立2 process、全11 acceptanceを再照合した。
- allocator/ROM/RAM/save/UI/hook overlap 0、declared span外変更0。

- Stage41 SHA-256: `{evidence['input_output']['stage41_sha256']}`
- Stage42 SHA-256: `{evidence['input_output']['stage42_sha256']}`
- result identity: `{evidence['mgba']['result_identity']}`
""".encode("utf-8")
    return evidence, report, Path(outputs["clean_rebuild"])


def _execute(mode: str) -> dict[str, Any]:
    _run([sys.executable, BUILDER.as_posix(), mode],
         f"Stage42 serializer/mGBA {mode}")
    evidence, report, evidence_path = _validate()
    expected = _stable(evidence)
    if mode == "build":
        _atomic_write(evidence_path, expected)
        _atomic_write(REPORT, report)
    elif _read(evidence_path) != expected or _read(REPORT) != report:
        _fail("Stage42 clean-rebuild evidence differs")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = _execute(args.mode)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, FactoryHighCleanRebuildError) as error:
        print(f"Factory High Modes V2 clean rebuild {args.mode} failed: {error}",
              file=sys.stderr)
        return 1
    print("Factory High Modes V2 clean rebuild %s: PASS stage42=%s processes=2"
          % (args.mode, evidence["input_output"]["stage42_sha256"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
