#!/usr/bin/env python3
"""clean FireRed日本版Rev.0からT28 Stage 45を二経路で厳密再構築する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_codex_battle_rewards import ACCEPTANCE_KEYS, MGBA_TESTS  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


TASK = "T28"
CONFIG = Path("config/codex_battle_rewards.json")
BUILDER = Path("scripts/build_codex_battle_rewards.py")


class CodexBattleRewardsCleanError(RuntimeError):
    """Stage 45 clean/BPS/mGBA/iPad契約違反。"""


def _fail(message: str) -> NoReturn:
    raise CodexBattleRewardsCleanError(message)


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
    if len(raw) != int(contract["size"]):
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
    if config.get("task") != TASK or config.get("stage") != 45:
        _fail("Codex Battle rewards config differs")
    inputs = config["inputs"]
    outputs = config["outputs"]
    clean = _read(Path(inputs["clean_rom"]["path"]))
    stage44 = _read(Path(inputs["stage44_rom"]["path"]))
    stage44_bps = _read(Path(inputs["stage44_clean_bps"]["path"]))
    stage45 = _read(Path(outputs["rom"]))
    incremental = _read(Path(outputs["incremental_bps"]))
    direct = _read(Path(outputs["clean_bps"]))
    _identity(clean, inputs["clean_rom"], "clean FireRed")
    _identity(stage44, inputs["stage44_rom"], "Stage44")
    _identity(stage44_bps, inputs["stage44_clean_bps"], "Stage44 clean BPS")
    if (apply_bps(clean, stage44_bps) != stage44
            or apply_bps(stage44, incremental) != stage45
            or apply_bps(clean, direct) != stage45):
        _fail("clean->Stage44->Stage45 and clean->Stage45 identities differ")

    metadata_raw = _read(Path(outputs["metadata"]))
    allocation_raw = _read(Path(outputs["allocation"]))
    protocol_raw = _read(Path(outputs["protocol"]))
    symbols_raw = _read(Path(outputs["symbols"]))
    cases_raw = _read(Path(outputs["cases"]))
    audit_raw = _read(Path(outputs["audit"]))
    coverage_raw = _read(Path(outputs["coverage"]))
    transactions_raw = _read(Path(outputs["transactions"]))
    ipad_raw = _read(Path(outputs["ipad"]))
    metadata = json.loads(metadata_raw)
    allocation = json.loads(allocation_raw)
    protocol = json.loads(protocol_raw)
    cases = json.loads(cases_raw)
    audit = json.loads(audit_raw)
    coverage = json.loads(coverage_raw)
    transactions = json.loads(transactions_raw)
    ipad = json.loads(ipad_raw)
    if (metadata.get("task") != TASK or metadata.get("status") != "PASS"
            or metadata.get("output", {}).get("sha256") != _sha(stage45)
            or metadata.get("mgba", {}).get("status") != "PASS"
            or metadata.get("mgba", {}).get("process_count") != 4
            or set(metadata.get("acceptance", {})) != set(ACCEPTANCE_KEYS)
            or any(value is not True for value in metadata["acceptance"].values())
            or metadata.get("change_audit", {}).get("outside_declared_span_count") != 0
            or metadata.get("change_audit", {}).get("declared_span_overlap_count") != 0
            or any(metadata.get("overlap_audit", {}).values())
            or allocation.get("summaries", {}).get("overlap_count") != 0
            or protocol.get("task") != TASK or protocol.get("stage") != 45
            or protocol.get("rom", {}).get("sha256") != _sha(stage45)
            or cases.get("rom_sha256") != _sha(stage45)
            or cases.get("expected_tests") != list(MGBA_TESTS)
            or audit.get("status") != "PASS"
            or coverage.get("status") != "PASS"
            or transactions.get("status") != "PASS"
            or ipad.get("status") != "PASS"):
        _fail("Stage45 metadata/evidence contract differs")

    mgba_hashes: dict[str, str] = {}
    result_identity: str | None = None
    for mode, key in (("quick", "mgba_quick"), ("full", "mgba_full")):
        raw = _read(Path(outputs[key]))
        document = json.loads(raw)
        if (document.get("task") != TASK or document.get("stage") != 45
                or document.get("mode") != mode
                or document.get("status") != "PASS"
                or document.get("process_runs") != 2
                or document.get("warnings") != 0
                or set(document.get("tests", {})) != set(MGBA_TESTS)
                or any(value is not True for value in document["tests"].values())):
            _fail(f"Stage45 mGBA {mode} evidence differs")
        if result_identity is None:
            result_identity = document["result_identity"]
        elif document["result_identity"] != result_identity:
            _fail("Stage45 mGBA quick/full identity differs")
        mgba_hashes[mode] = _sha(raw)

    evidence = {
        "schema_version": 1, "task": TASK, "stage": 45, "status": "PASS",
        "method": "PINNED_CLEAN_TO_STAGE44_PLUS_INCREMENTAL_AND_DIRECT_CROSSCHECK",
        "input_output": {
            "clean_sha256": _sha(clean), "stage44_sha256": _sha(stage44),
            "stage45_sha256": _sha(stage45),
            "stage45_crc32": f"{zlib.crc32(stage45) & 0xFFFFFFFF:08X}",
            "metadata_sha256": _sha(metadata_raw),
            "allocation_sha256": _sha(allocation_raw),
            "protocol_sha256": _sha(protocol_raw),
            "symbols_sha256": _sha(symbols_raw),
            "cases_sha256": _sha(cases_raw),
            "ipad_evidence_sha256": _sha(ipad_raw),
        },
        "bps": {
            "clean_to_stage44": {"sha256": _sha(stage44_bps),
                                   "size": len(stage44_bps), "round_trip_exact": True},
            "stage44_to_stage45": {"sha256": _sha(incremental),
                                     "size": len(incremental), "round_trip_exact": True},
            "clean_to_stage45": {"sha256": _sha(direct),
                                   "size": len(direct), "round_trip_exact": True},
            "chain_direct_identity_equal": True,
        },
        "declared_span": metadata["change_audit"],
        "overlap": metadata["overlap_audit"],
        "mgba": {"process_count": 4, "result_identity": result_identity,
                 "quick_artifact_sha256": mgba_hashes["quick"],
                 "full_artifact_sha256": mgba_hashes["full"]},
        "ipad": {"status": "PASS", "evidence_sha256": _sha(ipad_raw),
                 "secrets_redacted": True, "existing_files_overwritten": False},
        "acceptance": {key: True for key in ACCEPTANCE_KEYS},
        "inputs": {"config_sha256": _sha(config_raw)},
    }
    return evidence, Path(outputs["clean_rebuild"])


def _execute(mode: str) -> dict[str, Any]:
    _run([sys.executable, BUILDER.as_posix(), mode], f"Stage45 builder {mode}")
    evidence, path = _validate()
    expected = _stable(evidence)
    if mode == "build":
        _atomic_write(path, expected)
    elif _read(path) != expected:
        _fail("Stage45 clean-rebuild evidence differs")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        evidence = _execute(args.mode)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, CodexBattleRewardsCleanError) as error:
        print(f"Codex Battle Rewards clean rebuild {args.mode} failed: {error}",
              file=sys.stderr)
        return 1
    print("Codex Battle Rewards clean rebuild %s: PASS stage45=%s processes=4"
          % (args.mode, evidence["input_output"]["stage45_sha256"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
