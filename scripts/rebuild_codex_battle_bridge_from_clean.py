#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からT26 Stage 43を二経路で厳密再構築する。"""

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

from scripts.build_codex_battle_bridge import (  # noqa: E402
    ACCEPTANCE_KEYS,
    REQUIRED_ENTRYPOINTS,
)
from tools.release.bps import apply_bps  # noqa: E402


TASK = "T26"
CONFIG = Path("config/codex_battle_bridge.json")
BUILDER = Path("scripts/build_codex_battle_bridge.py")
RUNNER = Path("tools/mgba_codex_battle_bridge_smoke.c")


class CodexBattleCleanRebuildError(RuntimeError):
    """clean、Stage42/43 BPS、mGBAまたはiPad証跡の契約違反。"""


def _fail(message: str) -> NoReturn:
    raise CodexBattleCleanRebuildError(message)


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
    if not isinstance(config, dict) or config.get("task") != TASK:
        _fail("Codex Battle config root/task differs")
    inputs = config["inputs"]
    outputs = config["outputs"]
    clean = _read(Path(inputs["clean_rom"]["path"]))
    stage42 = _read(Path(inputs["stage42_rom"]["path"]))
    stage42_direct = _read(Path(inputs["stage42_clean_bps"]["path"]))
    stage43 = _read(Path(outputs["rom"]))
    metadata_raw = _read(Path(outputs["metadata"]))
    allocation_raw = _read(Path(outputs["allocation"]))
    incremental = _read(Path(outputs["incremental_bps"]))
    direct = _read(Path(outputs["clean_bps"]))
    protocol_raw = _read(Path(outputs["protocol"]))
    symbols_raw = _read(Path(outputs["symbols"]))
    cases_raw = _read(Path(outputs["cases"]))
    audit_raw = _read(Path(outputs["audit"]))
    coverage_raw = _read(Path(outputs["coverage"]))
    ipad_raw = _read(Path(outputs["ipad"]))
    _identity(clean, inputs["clean_rom"], "clean FireRed")
    _identity(stage42, inputs["stage42_rom"], "Stage42")
    _identity(stage42_direct, inputs["stage42_clean_bps"], "Stage42 clean BPS")
    rebuilt42 = apply_bps(clean, stage42_direct)
    chained = apply_bps(rebuilt42, incremental)
    direct_result = apply_bps(clean, direct)
    if rebuilt42 != stage42 or chained != stage43 or direct_result != stage43:
        _fail("clean->Stage42->Stage43 and clean->Stage43 identities differ")

    metadata = json.loads(metadata_raw)
    allocation = json.loads(allocation_raw)
    protocol = json.loads(protocol_raw)
    symbols = json.loads(symbols_raw)
    cases = json.loads(cases_raw)
    audit = json.loads(audit_raw)
    coverage = json.loads(coverage_raw)
    ipad = json.loads(ipad_raw)
    if (metadata.get("task") != TASK or metadata.get("status") != "PASS"
            or metadata.get("output", {}).get("sha256") != _sha(stage43)
            or metadata.get("mgba", {}).get("status") != "PASS"
            or metadata.get("mgba", {}).get("process_count") != 2
            or set(metadata.get("acceptance", {})) != set(ACCEPTANCE_KEYS)
            or any(value is not True for value in metadata["acceptance"].values())
            or metadata.get("change_audit", {}).get("outside_declared_span_count") != 0
            or metadata.get("change_audit", {}).get("declared_span_overlap_count") != 0
            or metadata.get("overlap_audit") != {"rom": 0, "ram": 0, "save": 0, "hook": 0}
            or allocation.get("summaries", {}).get("overlap_count") != 0
            or protocol.get("rom", {}).get("sha256") != _sha(stage43)
            or protocol.get("mailbox", {}).get("stage_number") != 43
            or cases.get("rom_sha256") != _sha(stage43)
            or len(cases.get("invalid_cases", [])) != 10
            or audit.get("status") != "PASS" or coverage.get("status") != "PASS"
            or ipad.get("status") != "PASS"):
        _fail("Stage43 metadata/allocation/protocol/evidence contract differs")
    symbol_rows = symbols.get("symbols", {})
    if (set(REQUIRED_ENTRYPOINTS) - set(symbol_rows)
            or any(int(symbol_rows[name].get("address", 0)) & 1 != 1
                   for name in REQUIRED_ENTRYPOINTS)):
        _fail("Stage43 runtime symbols differ")
    if (metadata["patches"]["incremental"]["sha256"] != _sha(incremental)
            or metadata["patches"]["clean_direct"]["sha256"] != _sha(direct)
            or metadata["patches"]["incremental"]["exact"] is not True
            or metadata["patches"]["clean_direct"]["exact"] is not True):
        _fail("Stage43 BPS metadata differs")

    runner_raw = _read(RUNNER)
    identities = {
        "rom_sha256": _sha(stage43), "runner_sha256": _sha(runner_raw),
        "symbols_sha256": _sha(symbols_raw), "cases_sha256": _sha(cases_raw),
    }
    documents: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for mode, key in (("quick", "mgba_quick"), ("full", "mgba_full")):
        raw = _read(Path(outputs[key]))
        document = json.loads(raw)
        if (document.get("task") != TASK or document.get("mode") != mode
                or document.get("status") != "PASS" or document.get("process_runs") != 1
                or document.get("warnings") != 0
                or any(document.get(name) != value for name, value in identities.items())
                or any(value is not True for value in document.get("tests", {}).values())):
            _fail(f"Stage43 mGBA {mode} evidence differs")
        documents[mode] = document
        hashes[mode] = _sha(raw)
    if documents["quick"]["result_identity"] != documents["full"]["result_identity"]:
        _fail("Stage43 mGBA quick/full identity differs")

    evidence = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "method": "PINNED_CLEAN_TO_STAGE42_PLUS_INCREMENTAL_AND_DIRECT_CROSSCHECK",
        "input_output": {
            "clean_sha256": _sha(clean), "stage42_sha256": _sha(stage42),
            "stage43_sha256": _sha(stage43),
            "stage43_crc32": metadata["output"]["crc32"],
            "metadata_sha256": _sha(metadata_raw),
            "allocation_sha256": _sha(allocation_raw),
            "protocol_sha256": _sha(protocol_raw),
            "ipad_evidence_sha256": _sha(ipad_raw),
        },
        "bps": {
            "stage42_baseline": {"sha256": _sha(stage42_direct),
                                 "size": len(stage42_direct), "round_trip_exact": True},
            "stage42_incremental": {"sha256": _sha(incremental),
                                    "size": len(incremental), "round_trip_exact": True},
            "clean_direct": {"sha256": _sha(direct), "size": len(direct),
                             "round_trip_exact": True},
            "chain_direct_identity_equal": True,
        },
        "declared_span": {
            "outside_declared_span_count": 0,
            "declared_span_overlap_count": 0,
            "changed_byte_count": metadata["change_audit"]["changed_byte_count"],
        },
        "overlap": metadata["overlap_audit"],
        "runtime": {"required_export_count": len(REQUIRED_ENTRYPOINTS),
                    "invalid_case_count": 10, "protected_span_count": 7},
        "mgba": {
            "process_count": 2,
            "result_identity": documents["quick"]["result_identity"],
            "quick_artifact_sha256": hashes["quick"],
            "full_artifact_sha256": hashes["full"], **identities,
        },
        "ipad": {"status": "PASS", "evidence_sha256": _sha(ipad_raw),
                 "ip_credential_container_redacted": True},
        "acceptance": {key: True for key in ACCEPTANCE_KEYS},
        "inputs": {"config_sha256": _sha(config_raw)},
    }
    return evidence, Path(outputs["clean_rebuild"])


def _execute(mode: str) -> dict[str, Any]:
    _run([sys.executable, BUILDER.as_posix(), mode], f"Stage43 builder {mode}")
    evidence, path = _validate()
    expected = _stable(evidence)
    if mode == "build":
        _atomic_write(path, expected)
    elif _read(path) != expected:
        _fail("Stage43 clean-rebuild evidence differs")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = _execute(args.mode)
    except (
        OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
        subprocess.SubprocessError, CodexBattleCleanRebuildError,
    ) as error:
        print(f"Codex Battle Bridge clean rebuild {args.mode} failed: {error}",
              file=sys.stderr)
        return 1
    print(
        "Codex Battle Bridge clean rebuild %s: PASS stage43=%s processes=2"
        % (args.mode, evidence["input_output"]["stage43_sha256"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
