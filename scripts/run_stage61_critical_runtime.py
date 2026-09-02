#!/usr/bin/env python3
"""Stage61 candidateの主要進行を対象別mGBA実走で検証する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_stage61_mgba_validation as RUNNER  # noqa: E402


TASK = "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT"
STAGE = 61
REQUIRED_RUNS = 2
DEFAULT_ROM = Path("build/stages/61_critical_release_candidate.gba")
DEFAULT_METADATA = Path("build/stages/61_critical_release_candidate.json")
DEFAULT_OUTPUT = Path(
    "reports/generated/stage61_critical_release_runtime.json"
)
DEFAULT_WORK_DIR = Path(".local/stage61-critical/runtime")
CASES = (
    "critical_fixed_encounter_save",
    "snorlax_missing_flute",
    "fuji_before_after",
    "fly_normal_menu",
    "connection_transition_lifecycle",
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_FNV64 = re.compile(r"[0-9A-F]{16}")
_ROLE = re.compile(r"[A-Z0-9_]+")
_PPM_HEADER = b"P6\n240 160\n255\n"
_PPM_SIZE = len(_PPM_HEADER) + 240 * 160 * 3


class CriticalRuntimeError(RuntimeError):
    """critical runtime入力または実走証跡が不正。"""


def _fail(message: str) -> NoReturn:
    raise CriticalRuntimeError(message)


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


def _fnv1a64(raw: bytes) -> str:
    value = 14695981039346656037
    for byte in raw:
        value ^= byte
        value = (value * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016X}"


def _require_true(value: Mapping[str, Any], names: Sequence[str],
                  label: str) -> None:
    bad = [name for name in names if value.get(name) is not True]
    if bad:
        _fail(f"{label} true anchor不一致: {bad}")


def _validate_capture(value: Any, label: str,
                      *, require_messages: bool) -> None:
    if not isinstance(value, Mapping):
        _fail(f"{label} captureはobjectではありません")
    execution = value.get("execution")
    if not isinstance(execution, Mapping) \
            or execution.get("invalid_control_flow") is not False:
        _fail(f"{label} invalid control flowを検出")
    messages = value.get("messages")
    if not isinstance(messages, list) \
            or (require_messages and not messages):
        _fail(f"{label} visible message証跡不足")
    for index, message in enumerate(messages):
        if not isinstance(message, Mapping) \
                or not isinstance(message.get("raw_hex"), str) \
                or not message["raw_hex"].endswith("FF") \
                or _FNV64.fullmatch(
                    str(message.get("framebuffer_fnv1a64", ""))
                ) is None:
            _fail(f"{label} message[{index}] raw/framebuffer不正")


def _validate_field_roundtrip(value: Any, label: str) -> None:
    if not isinstance(value, Mapping):
        _fail(f"{label} field roundtripはobjectではありません")
    _require_true(value, (
        "controls_released", "running_state_released",
        "tile_transition_released", "start_pressed",
        "start_menu_opened", "back_pressed", "callback_ordered",
        "map_preserved", "field_input_recovered",
    ), label)


def _validate_core(value: Mapping[str, Any]) -> None:
    _require_true(value, (
        "producer_via_normal_dialogue", "stock_warp_then_fresh_continue",
        "no_branch_preserved", "yes_branch_battle_started",
        "battle_completed_via_normal_fight_input",
        "post_battle_field_input_recovered",
        "fresh_continue_after_normal_save",
        "save_raw_128k_exact_after_continue", "flute_item_persisted",
        "snorlax_hidden_flag_persisted",
    ), "critical fixed encounter")
    if value.get("fresh_core_continue_count") != 3 \
            or value.get("normal_start_menu_save_generations") != 2 \
            or value.get("actual_walk_steps") != 2 \
            or value.get("battle_species") != 491 \
            or value.get("battle_outcome_last_sample") not in (0, 1):
        _fail("critical fixed encounter count/species anchor不一致")
    hashes = [
        value.get("pre_battle_save_fnv1a64"),
        value.get("saved_fnv1a64"), value.get("reloaded_fnv1a64"),
    ]
    if any(_FNV64.fullmatch(str(item)) is None for item in hashes) \
            or hashes[1] != hashes[2] or hashes[0] == hashes[1]:
        _fail("critical fixed encounter save raw hash不一致")
    captures = value.get("captures")
    if not isinstance(captures, Mapping) or set(captures) != {
        "producer", "no", "yes",
    }:
        _fail("critical fixed encounter capture集合不一致")
    for name, capture in captures.items():
        _validate_capture(
            capture, f"critical fixed encounter/{name}",
            require_messages=True,
        )
    _validate_field_roundtrip(
        value.get("post_battle_field_roundtrip"), "post battle",
    )
    _validate_field_roundtrip(
        value.get("reload_field_roundtrip"), "after reload",
    )


def _validate_missing(value: Mapping[str, Any]) -> None:
    _require_true(value, (
        "natural_continue", "stock_warp_save", "direction_plus_a",
        "object_visible_before", "object_visible_after",
    ), "missing flute")
    if value.get("actual_walk_steps") != 1 \
            or value.get("flute_flag") != 0 \
            or value.get("hidden_flag") != 0 \
            or value.get("battle_started") is not False:
        _fail("missing flute fail-closed branch不一致")
    _validate_capture(
        value.get("capture"), "missing flute", require_messages=True,
    )


def _validate_fuji(value: Mapping[str, Any]) -> None:
    _require_true(value, (
        "producer_via_normal_dialogue", "dialogue_distinct",
    ), "Fuji before/after")
    if value.get("before_flute_flag") != 0 \
            or value.get("after_flute_flag") != 1 \
            or not isinstance(value.get("actual_walk_steps"), int) \
            or value["actual_walk_steps"] < 2:
        _fail("Fuji before/after story state不一致")
    captures = value.get("captures")
    if not isinstance(captures, Mapping) or set(captures) != {
        "before", "after",
    }:
        _fail("Fuji before/after capture集合不一致")
    for name, capture in captures.items():
        _validate_capture(
            capture, f"Fuji/{name}", require_messages=True,
        )


def _validate_fly(value: Mapping[str, Any]) -> None:
    _require_true(value, (
        "preparation_only_host_writes", "start_party_town_map_via_keys",
        "town_map_visible", "landing_overworld",
        "landing_script_released", "landing_controls_unlocked",
        "start_pressed", "start_menu_opened", "back_pressed",
        "field_input_recovered",
    ), "Fly")
    if value.get("origin") != "96/23" \
            or value.get("destination") != "96/4" \
            or value.get("landing") != [6, 6] \
            or not isinstance(value.get("sequence_steps"), int) \
            or value["sequence_steps"] <= 0:
        _fail("Fly destination/input sequence不一致")
    _validate_capture(value.get("capture"), "Fly", require_messages=False)


def _validate_connection(value: Mapping[str, Any]) -> None:
    _require_true(value, (
        "stock_warp_setup_only", "direct_boundary_transition_exact",
        "resume_start_back_callback_ordered",
        "all_current_owner_pointers_reresolved",
    ), "connection transition")
    rows = value.get("results")
    if value.get("direct_destination_teleport") is not False \
            or value.get("variant_count") != 2 \
            or not isinstance(rows, list) or len(rows) != 2:
        _fail("connection transition root不一致")
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            _fail("connection transition rowはobjectではありません")
        _require_true(row, (
            "save_generated", "fresh_title_continue",
            "stock_warp_source_setup", "source_predecessor_exact",
            "arrival_transform_exact", "root_absent_before_boundary_step",
            "root_call_sequence_exact", "first_root_identity_exact",
            "field_released_after_transition", "field_input_recovered",
        ), f"connection row{index}")
        if row.get("actual_boundary_walk_steps") != 1 \
                or row.get("direct_destination_teleport") is not False \
                or row.get("destination_map") != [3, 0] \
                or row.get("arrival") != [34, 15] \
                or row.get("invalid_control_flow") is not False:
            _fail(f"connection row{index} transition不一致")
        resume = index == 1
        if row.get("start_menu_opened") is not resume \
                or row.get("back_pressed") is not resume \
                or row.get("callback_ordered") is not resume:
            _fail(f"connection row{index} resume callback不一致")
        _validate_capture(
            row.get("capture"), f"connection row{index}",
            require_messages=False,
        )


_VALIDATORS = {
    "critical_fixed_encounter_save": _validate_core,
    "snorlax_missing_flute": _validate_missing,
    "fuji_before_after": _validate_fuji,
    "fly_normal_menu": _validate_fly,
    "connection_transition_lifecycle": _validate_connection,
}


def _validate_result(value: Any, case: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{case} result rootはobjectではありません")
    result = dict(value)
    if result.get("status") != "PASS" or result.get("case") != case \
            or result.get("warnings") != 0 \
            or result.get("failed", 0) != 0 \
            or result.get("untested", 0) != 0:
        _fail(f"{case} status/count不一致")
    _VALIDATORS[case](result)
    return result


def _validate_framebuffers(
    value: Mapping[str, Any], case_dir: Path, case: str,
) -> list[dict[str, Any]]:
    rows = value.get("framebuffer_artifacts")
    if not isinstance(rows, list):
        _fail(f"{case} framebuffer registryがありません")
    expected_minimum = {
        "critical_fixed_encounter_save": 9,
        "snorlax_missing_flute": 1,
        "fuji_before_after": 2,
        "fly_normal_menu": 2,
        "connection_transition_lifecycle": 4,
    }[case]
    if len(rows) < expected_minimum:
        _fail(
            f"{case} framebuffer不足: "
            f"minimum={expected_minimum} actual={len(rows)}"
        )
    paths: set[str] = set()
    validated: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            _fail(f"{case} framebuffer[{index}]はobjectではありません")
        relative = row.get("path")
        role = row.get("framebuffer_role")
        if not isinstance(relative, str) or not relative.endswith(".ppm") \
                or "\\" in relative:
            _fail(f"{case} framebuffer path不正")
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts \
                or relative in paths \
                or _ROLE.fullmatch(str(role)) is None:
            _fail(f"{case} framebuffer path/role不正: {relative}")
        paths.add(relative)
        path = case_dir / Path(*pure.parts)
        raw = path.read_bytes() if path.is_file() else b""
        if len(raw) != _PPM_SIZE or not raw.startswith(_PPM_HEADER):
            _fail(f"{case} framebuffer file不正: {relative}")
        rgb_hash = _fnv1a64(raw[len(_PPM_HEADER):])
        if row.get("rgb_fnv1a64") != rgb_hash:
            _fail(f"{case} framebuffer RGB hash不一致: {relative}")
        validated.append({
            "path": relative,
            "size": len(raw),
            "sha256": _sha(raw),
            "rgb_fnv1a64": rgb_hash,
            "framebuffer_role": role,
        })
    actual = {
        path.relative_to(case_dir).as_posix()
        for path in case_dir.rglob("*.ppm")
    }
    if actual != paths:
        _fail(f"{case} framebuffer registry/file集合不一致")
    return validated


def run(
    *, rom: Path, metadata: Path, output: Path, work_dir: Path,
    expected_rom_sha256: str, runs: int = REQUIRED_RUNS,
) -> dict[str, Any]:
    if runs != REQUIRED_RUNS or isinstance(runs, bool):
        _fail(f"--runsはexact {REQUIRED_RUNS}です")
    if _SHA256.fullmatch(expected_rom_sha256) is None:
        _fail("--expected-rom-sha256は64桁lowercase SHA-256です")
    rom_path, metadata_path = _path(rom), _path(metadata)
    _rom_raw, metadata_document, digest = RUNNER._read_identity(
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
    if any(work.iterdir()):
        _fail("critical runtime work directoryが空ではありません")
    executable = work / "toolchain" / "stage61-critical-runtime"
    executable.parent.mkdir(parents=True, exist_ok=False)
    compile_info = RUNNER._compile(executable)
    source_path = ROOT / RUNNER.SOURCE
    source_sha256 = _sha(source_path.read_bytes())
    orchestrator_path = Path(__file__).resolve()
    orchestrator_sha256 = _sha(orchestrator_path.read_bytes())

    fixture_document = RUNNER.validate_fixture_document(
        json.loads(json.dumps(RUNNER.DEFAULT_FIXTURE_DOCUMENT))
    )
    environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith("S61_")
    }
    environment.update(RUNNER.fixture_environment(fixture_document))

    case_reports: dict[str, Any] = {}
    for case in CASES:
        records: list[dict[str, Any]] = []
        for run_index in range(1, runs + 1):
            case_dir = work / f"{case}-run-{run_index:02d}"
            case_dir.mkdir(parents=True, exist_ok=False)
            completed = subprocess.run(
                [str(executable), str(rom_path.resolve()),
                 str(case_dir.resolve()), case],
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
                    f"{case} run{run_index} mGBA失敗 "
                    f"exit={completed.returncode}: {detail[-12000:]}"
                )
            try:
                raw_result = json.loads(completed.stdout)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                _fail(f"{case} run{run_index} JSON不正: {error}")
            result = _validate_result(raw_result, case)
            framebuffers = _validate_framebuffers(result, case_dir, case)
            save_rows = [
                {
                    "path": path.relative_to(case_dir).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": _sha(path.read_bytes()),
                }
                for path in sorted(case_dir.rglob("*.srm"))
            ]
            if case == "critical_fixed_encounter_save" \
                    and (len(save_rows) != 1
                         or save_rows[0]["size"] != 131072):
                _fail("critical normal save artifactはexact 128 KiBではありません")
            normalized_sha256 = _sha(_stable(result))
            records.append({
                "run_index": run_index,
                "status": "PASS",
                "normalized_sha256": normalized_sha256,
                "stdout_sha256": _sha(completed.stdout),
                "stderr_sha256": _sha(completed.stderr),
                "framebuffers": framebuffers,
                "save_artifacts": save_rows,
                "result": result,
            })
        hashes = [record["normalized_sha256"] for record in records]
        if len(set(hashes)) != 1:
            _fail(f"{case} independent run result hash不一致: {hashes}")
        case_reports[case] = {
            "status": "PASS",
            "runs": runs,
            "normalized_sha256": hashes[0],
            "normalized_hashes_match": True,
            "records": records,
        }

    if _sha(rom_path.read_bytes()) != digest \
            or _sha(metadata_path.read_bytes()) != metadata_sha256 \
            or _sha(source_path.read_bytes()) != source_sha256 \
            or _sha(orchestrator_path.read_bytes()) != orchestrator_sha256:
        _fail("critical runtime実走中に入力identityが変化しました")
    report = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "status_scope": "CURATED_CRITICAL_RUNTIME_ONLY",
        "release_profile": "CRITICAL_RELEASE",
        "rom_sha256": digest,
        "metadata_sha256": metadata_sha256,
        "runner_source_sha256": source_sha256,
        "orchestrator_sha256": orchestrator_sha256,
        "fixture_sha256": _sha(_stable(fixture_document)),
        "compile": compile_info,
        "runs_per_case": runs,
        "case_count": len(CASES),
        "cases": case_reports,
        "coverage": {
            "boot_and_fresh_core_continue": True,
            "normal_start_menu_save_two_generations": True,
            "exact_128k_save_and_fresh_continue_readback": True,
            "actual_player_movement": True,
            "stock_connection_boundary_transition": True,
            "normal_party_menu_fly_warp": True,
            "visible_dialogue": True,
            "story_key_item_acquisition_and_persistence": True,
            "major_progression_no_yes_branches": True,
            "canonical_fixed_encounter_species": True,
            "battle_completed_via_normal_input": True,
            "post_battle_field_input_recovered": True,
            "crash_zero": True,
            "softlock_zero": True,
            "save_corruption_zero": True,
            "progression_blockage_zero": True,
            "curated_cases_independent_runs_exact_2": True,
        },
        "deferred_scope": [
            "ALL_678_MAPS_ALL_OWNER_ALL_BRANCH_RUNS_2",
            "UNUSED_STATE_ENUMERATION",
            "EXACT_TRACE_ORDINAL_ALL_OWNERS",
            "COMPLETE_COVERAGE_ZERO_OMISSION",
        ],
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
        "case_count": report["case_count"],
        "runs_per_case": report["runs_per_case"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CriticalRuntimeError, RUNNER.Stage61MgbaError) as error:
        print(f"stage61-critical-runtime: {error}", file=sys.stderr)
        raise SystemExit(1)
