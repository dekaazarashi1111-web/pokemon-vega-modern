#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からT27 Stage 44を二経路で厳密再構築する。"""

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

from scripts.build_codex_battle_runtime import (  # noqa: E402
    ACCEPTANCE_KEYS,
    MGBA_TESTS,
    REQUIRED_ENTRYPOINTS,
)
from tools.release.bps import apply_bps  # noqa: E402


TASK = "T27"
CONFIG = Path("config/codex_battle_runtime.json")
BUILDER = Path("scripts/build_codex_battle_runtime.py")
RUNNER = Path("tools/mgba_codex_battle_runtime_smoke.c")


class CodexBattleRuntimeCleanError(RuntimeError):
    """Stage 44 clean/BPS/mGBA/iPad契約違反。"""


def _fail(message: str) -> NoReturn:
    raise CodexBattleRuntimeCleanError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def _read(path: Path) -> bytes:
    try:
        return (ROOT / path).read_bytes()
    except OSError as error:
        _fail(f"required artifact unavailable: {path}: {error}")


def _identity(raw: bytes, contract: Mapping[str, Any], label: str) -> None:
    if contract.get("size") is not None and len(raw) != int(contract["size"]):
        _fail(f"{label} size differs")
    if _sha(raw) != str(contract["sha256"]):
        _fail(f"{label} SHA-256 differs")


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


def _validate() -> tuple[dict[str, Any], Path]:
    config_raw = _read(CONFIG)
    config = json.loads(config_raw)
    if config.get("task") != TASK or config.get("stage") != 44:
        _fail("Codex Battle runtime config differs")
    inputs = config["inputs"]
    outputs = config["outputs"]
    clean = _read(Path(inputs["clean_rom"]["path"]))
    stage43 = _read(Path(inputs["stage43_rom"]["path"]))
    stage43_direct = _read(Path(inputs["stage43_clean_bps"]["path"]))
    stage44 = _read(Path(outputs["rom"]))
    incremental = _read(Path(outputs["incremental_bps"]))
    direct = _read(Path(outputs["clean_bps"]))
    _identity(clean, inputs["clean_rom"], "clean FireRed")
    _identity(stage43, inputs["stage43_rom"], "Stage43")
    _identity(stage43_direct, inputs["stage43_clean_bps"], "Stage43 clean BPS")
    if (apply_bps(clean, stage43_direct) != stage43
            or apply_bps(stage43, incremental) != stage44
            or apply_bps(clean, direct) != stage44):
        _fail("clean->Stage43->Stage44 and clean->Stage44 identities differ")

    metadata_raw = _read(Path(outputs["metadata"]))
    allocation_raw = _read(Path(outputs["allocation"]))
    protocol_raw = _read(Path(outputs["protocol"]))
    symbols_raw = _read(Path(outputs["symbols"]))
    cases_raw = _read(Path(outputs["cases"]))
    audit_raw = _read(Path(outputs["audit"]))
    coverage_raw = _read(Path(outputs["coverage"]))
    matrix_raw = _read(Path(outputs["matrix"]))
    catalog_report_raw = _read(Path(outputs["catalog_report"]))
    privacy_raw = _read(Path(outputs["privacy"]))
    gimmick_raw = _read(Path(outputs["gimmick"]))
    ipad_raw = _read(Path(outputs["ipad"]))
    catalog_raw = _read(Path(config["catalog"]["path"]))
    metadata = json.loads(metadata_raw)
    allocation = json.loads(allocation_raw)
    protocol = json.loads(protocol_raw)
    symbols = json.loads(symbols_raw)
    cases = json.loads(cases_raw)
    audit = json.loads(audit_raw)
    coverage = json.loads(coverage_raw)
    matrix = json.loads(matrix_raw)
    catalog_report = json.loads(catalog_report_raw)
    privacy = json.loads(privacy_raw)
    gimmick = json.loads(gimmick_raw)
    ipad = json.loads(ipad_raw)
    if (metadata.get("task") != TASK or metadata.get("status") != "PASS"
            or metadata.get("output", {}).get("sha256") != _sha(stage44)
            or metadata.get("mgba", {}).get("status") != "PASS"
            or metadata.get("mgba", {}).get("process_count") != 2
            or set(metadata.get("acceptance", {})) != set(ACCEPTANCE_KEYS)
            or any(value is not True for value in metadata["acceptance"].values())
            or metadata.get("change_audit", {}).get("outside_declared_span_count") != 0
            or metadata.get("change_audit", {}).get("declared_span_overlap_count") != 0
            or any(metadata.get("overlap_audit", {}).values())
            or allocation.get("summaries", {}).get("overlap_count") != 0
            or protocol.get("rom", {}).get("sha256") != _sha(stage44)
            or protocol.get("mailbox", {}).get("stage_number") != 44
            or cases.get("rom_sha256") != _sha(stage44)
            or cases.get("expected_tests") != list(MGBA_TESTS)
            or len(cases.get("invalid_cases", [])) != 13
            or audit.get("status") != "PASS"
            or coverage.get("status") != "PASS"
            or matrix.get("status") != "PASS"
            or catalog_report.get("status") != "PASS"
            or privacy.get("status") != "PASS"
            or gimmick.get("status") != "PASS"
            or ipad.get("status") != "PASS"):
        _fail("Stage44 metadata/evidence contract differs")
    symbol_rows = symbols.get("symbols", {})
    if (set(REQUIRED_ENTRYPOINTS) - set(symbol_rows)
            or any(int(symbol_rows[name]["address"]) & 1 != 1
                   for name in REQUIRED_ENTRYPOINTS)):
        _fail("Stage44 runtime exports differ")

    runner_raw = _read(RUNNER)
    source_identities = {
        "rom_sha256": _sha(stage44),
        "runner_source_sha256": _sha(runner_raw),
        "symbols_sha256": _sha(symbols_raw),
        "cases_sha256": _sha(cases_raw),
    }
    mgba_documents: dict[str, dict[str, Any]] = {}
    mgba_hashes: dict[str, str] = {}
    for mode, key in (("quick", "mgba_quick"), ("full", "mgba_full")):
        raw = _read(Path(outputs[key]))
        document = json.loads(raw)
        if (document.get("task") != TASK or document.get("mode") != mode
                or document.get("status") != "PASS"
                or document.get("process_runs") != 1
                or document.get("warnings") != 0
                or document.get("turn_cycles", 0) < 3
                or any(document.get(name) != value
                       for name, value in source_identities.items())
                or set(document.get("tests", {})) != set(MGBA_TESTS)
                or any(value is not True for value in document["tests"].values())):
            _fail(f"Stage44 mGBA {mode} evidence differs")
        mgba_documents[mode] = document
        mgba_hashes[mode] = _sha(raw)
    if (mgba_documents["quick"]["result_identity"]
            != mgba_documents["full"]["result_identity"]):
        _fail("Stage44 mGBA quick/full identity differs")

    evidence = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "method": "PINNED_CLEAN_TO_STAGE43_PLUS_INCREMENTAL_AND_DIRECT_CROSSCHECK",
        "input_output": {
            "clean_sha256": _sha(clean), "stage43_sha256": _sha(stage43),
            "stage44_sha256": _sha(stage44),
            "stage44_crc32": metadata["output"]["crc32"],
            "metadata_sha256": _sha(metadata_raw),
            "allocation_sha256": _sha(allocation_raw),
            "protocol_sha256": _sha(protocol_raw),
            "catalog_sha256": _sha(catalog_raw),
            "ipad_evidence_sha256": _sha(ipad_raw),
        },
        "bps": {
            "stage43_baseline": {"sha256": _sha(stage43_direct),
                                 "size": len(stage43_direct), "round_trip_exact": True},
            "stage43_incremental": {"sha256": _sha(incremental),
                                    "size": len(incremental), "round_trip_exact": True},
            "clean_direct": {"sha256": _sha(direct), "size": len(direct),
                             "round_trip_exact": True},
            "chain_direct_identity_equal": True,
        },
        "declared_span": metadata["change_audit"],
        "overlap": metadata["overlap_audit"],
        "runtime": {"required_export_count": len(REQUIRED_ENTRYPOINTS),
                    "invalid_case_count": 13, "state_size": 1536},
        "mgba": {
            "process_count": 2,
            "result_identity": mgba_documents["quick"]["result_identity"],
            "quick_artifact_sha256": mgba_hashes["quick"],
            "full_artifact_sha256": mgba_hashes["full"], **source_identities,
        },
        "ipad": {"status": "PASS", "evidence_sha256": _sha(ipad_raw),
                 "multi_turn": ipad["turn_cycles"], "secrets_redacted": True},
        "acceptance": {key: True for key in ACCEPTANCE_KEYS},
        "inputs": {"config_sha256": _sha(config_raw)},
    }
    return evidence, Path(outputs["clean_rebuild"])


def _execute(mode: str) -> dict[str, Any]:
    _run([sys.executable, BUILDER.as_posix(), mode], f"Stage44 builder {mode}")
    evidence, path = _validate()
    expected = _stable(evidence)
    if mode == "build":
        _atomic_write(path, expected)
    elif _read(path) != expected:
        _fail("Stage44 clean-rebuild evidence differs")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = _execute(args.mode)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, CodexBattleRuntimeCleanError) as error:
        print(f"Codex Battle Runtime clean rebuild {args.mode} failed: {error}",
              file=sys.stderr)
        return 1
    print("Codex Battle Runtime clean rebuild %s: PASS stage44=%s processes=2"
          % (args.mode, evidence["input_output"]["stage44_sha256"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
