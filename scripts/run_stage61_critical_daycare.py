#!/usr/bin/env python3
"""Stage61 candidateで2系統の育て屋deposit/payment/withdrawを実走する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_stage61_mgba_validation as RUNNER  # noqa: E402
from tools.stage61_interaction_oracle import (  # noqa: E402
    _daycare_scenario_payload,
)


TASK = "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT"
STAGE = 61
REQUIRED_RUNS = 2
DEFAULT_ROM = Path("build/stages/61_critical_release_candidate.gba")
DEFAULT_METADATA = Path("build/stages/61_critical_release_candidate.json")
DEFAULT_OUTPUT = Path(
    "reports/generated/stage61_critical_release_daycare.json"
)
DEFAULT_WORK_DIR = Path(".local/stage61-critical/daycare")
SCENARIOS = ("empty_deposit", "route5_empty_deposit")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class CriticalDaycareError(RuntimeError):
    """critical daycare runnerの入力または実走証跡が不正。"""


def _fail(message: str) -> NoReturn:
    raise CriticalDaycareError(message)


def _path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write_atomic(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=path.name + ".", suffix=".tmp",
            dir=path.parent, delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        temporary = None
    finally:
        if temporary is not None and temporary.is_file():
            temporary.unlink()


def _daycare_external(
    reference: str, fixture: Mapping[str, Any], scenario_id: str,
) -> dict[str, Any]:
    route5 = scenario_id.startswith("route5_")
    return {
        "kind": "DAYCARE_TRANSACTION_STATE",
        "id": 1 if route5 else 0,
        "source_ids": (
            [131, 132, 133, 186, 188, 197, 198,
             374, 375, 376, 377, 378]
            if route5 else
            [131, 132, 133, 182, 186, 187, 188,
             189, 190, 191, 192, 197, 198]
        ),
        "read_addresses": ["0x08127F00"],
        "candidate_values": list(
            RUNNER._ROUTE5_DAYCARE_TRANSACTION_SCENARIO_IDS
            if route5 else RUNNER._DAYCARE_TRANSACTION_SCENARIO_IDS
        ),
        "relations": [{
            "operator": (
                RUNNER._ROUTE5_DAYCARE_TRANSACTION_RELATION
                if route5 else RUNNER._DAYCARE_TRANSACTION_RELATION
            ),
            "state_owners": list(
                RUNNER._ROUTE5_DAYCARE_TRANSACTION_STATE_OWNERS
                if route5 else RUNNER._DAYCARE_TRANSACTION_STATE_OWNERS
            ),
        }],
        "required_value_in_matrix_case": {
            "scenario_id": scenario_id,
            "layout_ref": reference,
            "party_count": fixture["party_count"],
            "money": fixture["money"],
            "party_sha256": _sha(bytes.fromhex(fixture["party_raw_hex"])),
            "daycare_sha256": _sha(
                bytes.fromhex(fixture["daycare_raw_hex"])
            ),
        },
        "requirement_basis": (
            "CRITICAL_RELEASE_ROUTE5_DAYCARE_TRANSACTION"
            if route5 else
            "CRITICAL_RELEASE_FOUR_ISLAND_DAYCARE_TRANSACTION"
        ),
    }


def _prepare_controls(
    fixture_dir: Path,
) -> tuple[dict[str, Mapping[str, Any]], dict[str, str]]:
    raw_registry = {
        RUNNER._runner_fixture_key(_daycare_scenario_payload(scenario)):
            _daycare_scenario_payload(scenario)
        for scenario in SCENARIOS
    }
    registry = RUNNER._normalize_control_fixture_registry(raw_registry)
    RUNNER.write_control_fixture_files(fixture_dir, registry)
    state = {name: [] for name in ("flags", "vars", "items", "trainers")}
    controls: dict[str, str] = {}
    for reference, fixture in registry.items():
        scenario = str(fixture["scenario_id"])
        normalized = RUNNER._normalize_external_controls(
            [_daycare_external(reference, fixture, scenario)],
            state, registry, f"critical-daycare-{scenario}",
        )
        if len(normalized) != 1:
            _fail(f"{scenario} external controlが一意ではありません")
        controls[scenario] = RUNNER._encode_external_control(normalized[0])
    if set(controls) != set(SCENARIOS):
        _fail("critical daycare control closure不一致")
    return registry, controls


def _validate_result(value: Any, scenario: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{scenario} result rootはobjectではありません")
    expected = {
        "schema_version": 1,
        "status": "PASS",
        "case": "critical_daycare_transaction",
        "scenario_id": scenario,
        "family": "ROUTE5" if scenario.startswith("route5_")
            else "FOUR_ISLAND",
        "deposit_via_script_context": True,
        "party_compaction_exact": True,
        "cost": 100,
        "enough": 1,
        "money_after": 400,
        "withdraw_result_species": 3,
        "party_restored_exact": True,
        "daycare_storage_cleared": True,
        "pc_storage_unchanged": True,
        "modern_queue_unchanged": True,
        "field_input_recovered": True,
        "failed": 0,
        "untested": 0,
        "warnings": 0,
        "artifacts": [],
        "framebuffer_artifacts": [],
    }
    normalized = deepcopy(dict(value))
    if normalized != expected:
        differing = sorted(
            key for key in set(normalized) | set(expected)
            if normalized.get(key) != expected.get(key)
        )
        _fail(f"{scenario} result不一致: {differing}")
    return normalized


def run(
    *, rom: Path, metadata: Path, output: Path, work_dir: Path,
    expected_rom_sha256: str, runs: int = REQUIRED_RUNS,
) -> dict[str, Any]:
    if runs != REQUIRED_RUNS or isinstance(runs, bool):
        _fail(f"--runsはexact {REQUIRED_RUNS}です")
    if _SHA256.fullmatch(expected_rom_sha256) is None:
        _fail("--expected-rom-sha256は64桁lowercase SHA-256です")
    rom_path, metadata_path = _path(rom), _path(metadata)
    rom_raw, metadata_document, digest = RUNNER._read_identity(
        rom_path, metadata_path,
    )
    metadata_sha256 = _sha(metadata_path.read_bytes())
    if digest != expected_rom_sha256:
        _fail("candidate ROM SHA-256が明示pinと不一致です")
    if metadata_document.get("release_profile") != "CRITICAL_RELEASE" \
            or metadata_document.get("candidate_status") != "CANDIDATE" \
            or metadata_document.get("strict_audit_status") \
                != "DEFERRED_AUDIT":
        _fail("critical-release candidate metadata契約不一致")

    work = _path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    fixture_dir = work / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    if any(fixture_dir.iterdir()):
        _fail("critical daycare fixture directoryが空ではありません")
    registry, controls = _prepare_controls(fixture_dir)
    executable = work / "toolchain" / "stage61-critical-daycare"
    executable.parent.mkdir(parents=True, exist_ok=True)
    compile_info = RUNNER._compile(executable)
    source_path = ROOT / RUNNER.SOURCE
    source_sha256 = _sha(source_path.read_bytes())
    orchestrator_path = Path(__file__).resolve()
    orchestrator_sha256 = _sha(orchestrator_path.read_bytes())
    fixture_document = RUNNER.validate_fixture_document(
        deepcopy(RUNNER.DEFAULT_FIXTURE_DOCUMENT)
    )
    base_environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith("S61_")
    }
    base_environment.update(RUNNER.fixture_environment(fixture_document))
    base_environment["S61_CONTROL_FIXTURE_DIR"] = str(
        fixture_dir.resolve()
    )

    scenario_reports: dict[str, Any] = {}
    for scenario in SCENARIOS:
        run_reports: list[dict[str, Any]] = []
        for run_index in range(1, runs + 1):
            case_dir = work / f"{scenario}-run-{run_index:02d}"
            case_dir.mkdir(parents=True, exist_ok=False)
            environment = dict(base_environment)
            environment["S61_DAYCARE_TRANSACTION_CONTROL"] = controls[
                scenario
            ]
            completed = subprocess.run(
                [str(executable), str(rom_path.resolve()),
                 str(case_dir.resolve()), "critical_daycare_transaction"],
                cwd=ROOT, env=environment, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=1800, check=False,
            )
            _write_atomic(case_dir / "process.stdout", completed.stdout)
            _write_atomic(case_dir / "process.stderr", completed.stderr)
            if completed.returncode != 0 or completed.stderr:
                detail = (completed.stderr or completed.stdout).decode(
                    "utf-8", errors="replace",
                )
                _fail(
                    f"{scenario} run{run_index} mGBA失敗 "
                    f"exit={completed.returncode}: {detail[-8000:]}"
                )
            try:
                result = json.loads(completed.stdout)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                _fail(f"{scenario} run{run_index} JSON不正: {error}")
            normalized = _validate_result(result, scenario)
            run_reports.append({
                "run_index": run_index,
                "status": "PASS",
                "normalized_sha256": _sha(_stable(normalized)),
                "stdout_sha256": _sha(completed.stdout),
                "stderr_sha256": _sha(completed.stderr),
                "result": normalized,
            })
        if run_reports[0]["normalized_sha256"] \
                != run_reports[1]["normalized_sha256"]:
            _fail(f"{scenario} independent run result hash不一致")
        scenario_reports[scenario] = {
            "status": "PASS",
            "runs": runs,
            "normalized_sha256": run_reports[0]["normalized_sha256"],
            "normalized_hashes_match": True,
            "records": run_reports,
        }

    if _sha(rom_path.read_bytes()) != digest \
            or _sha(metadata_path.read_bytes()) \
                != metadata_sha256 \
            or _sha(source_path.read_bytes()) != source_sha256 \
            or _sha(orchestrator_path.read_bytes()) != orchestrator_sha256:
        _fail("critical daycare実走中に入力identityが変化しました")
    report = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "release_profile": "CRITICAL_RELEASE",
        "rom_sha256": digest,
        "metadata_sha256": metadata_sha256,
        "runner_source_sha256": source_sha256,
        "orchestrator_sha256": orchestrator_sha256,
        "compile": compile_info,
        "runs_per_scenario": runs,
        "scenario_count": len(SCENARIOS),
        "scenarios": scenario_reports,
        "fixture_registry": {
            "count": len(registry),
            "keys": sorted(registry),
        },
        "coverage": {
            "four_island_daycare": True,
            "route5_daycare": True,
            "deposit_via_script_context": True,
            "party_compaction": True,
            "exact_cost_and_money_transaction": True,
            "withdraw_via_script_context": True,
            "party_restoration": True,
            "daycare_storage_clear": True,
            "pc_storage_unchanged": True,
            "modern_egg_queue_unchanged": True,
            "field_input_recovered": True,
            "independent_runs_exact_2": True,
        },
        "failed": 0,
        "untested": 0,
        "warnings": 0,
    }
    _write_atomic(_path(output), _stable(report))
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--expected-rom-sha256", required=True)
    parser.add_argument("--runs", type=int, default=REQUIRED_RUNS)
    args = parser.parse_args(argv)
    report = run(
        rom=args.rom, metadata=args.metadata, output=args.output,
        work_dir=args.work_dir,
        expected_rom_sha256=args.expected_rom_sha256, runs=args.runs,
    )
    print(json.dumps({
        "status": report["status"],
        "rom_sha256": report["rom_sha256"],
        "scenario_count": report["scenario_count"],
        "runs_per_scenario": report["runs_per_scenario"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CriticalDaycareError, RUNNER.Stage61MgbaError) as error:
        print(f"stage61-critical-daycare: {error}", file=sys.stderr)
        raise SystemExit(1)
