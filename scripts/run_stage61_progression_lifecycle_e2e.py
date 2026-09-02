#!/usr/bin/env python3
"""Stage61 League/Seafoamの完結した実mGBA進行lifecycleを検証する。

C側の自己申告だけでは合格にしない。独立OS processを2回起動し、通常入力SAVEを
distinct mCoreでcold Continueした後のraw SRM/framebufferとprocess出力をatomic保持する。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("tools/mgba_stage61_progression_lifecycle_e2e.c")
EMBEDDED = Path("tools/mgba_stage61_display_npc_event_e2e.c")
RFU_SOURCE = Path("tools/mgba_stage61_rfu_peripheral.c")
RFU_HEADER = Path("tools/mgba_stage61_rfu_peripheral.h")
DEFAULT_ROM = Path("build/stages/61_display_npc_event_audit.gba")
DEFAULT_METADATA = Path("build/stages/61_display_npc_event_audit.json")
SAVE_SIZE = 131072
PPM_HEADER = b"P6\n240 160\n255\n"
PPM_PIXEL_SIZE = 240 * 160 * 3
TASK = "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT"
ARTIFACT_STEMS = {
    "league": ("league_full_chain", "league_blackout_retry"),
    "seafoam": ("seafoam_active_current", "seafoam_stopped_current"),
}
PROCESS_ARTIFACT_NAMES = {
    "stdout": "process.stdout.raw",
    "stderr": "process.stderr.raw",
    "case_result": "case-result.canonical.json",
}
ARTIFACT_DESCRIPTOR_KEYS = {
    "path", "name", "role", "format", "case_id", "size", "sha256",
    "raw_re_read", "atomic_retain",
}
REQUIRED_RUNS = 2
REPORT_SCHEMA_VERSION = 3
RESULT_SCHEMA_VERSION = 3
CHECKPOINT_EXPECTATIONS: dict[str, dict[str, dict[str, Any]]] = {
    "league": {
        "league_full_chain": {
            "map": {"group": 97, "number": 80},
            "flags": {
                "0x1407": True,
                "0x1408": True,
                "0x1409": True,
                "0x140A": True,
                "0x140B": True,
                "0x140C": True,
            },
            "vars": {"0x516C": 5},
        },
        "league_blackout_retry": {
            "map": {"group": 97, "number": 76},
            "flags": {
                "0x1407": True,
                "0x1408": True,
                "0x1409": False,
                "0x140A": False,
                "0x140B": False,
                "0x140C": False,
            },
            "vars": {"0x516C": 2},
        },
    },
    "seafoam": {
        "seafoam_active_current": {
            "map": {"group": 97, "number": 87},
            "flags": {
                "0x0805": False,
                "0x162D": False,
                "0x162E": False,
                "0x162F": True,
                "0x1630": True,
                "0x1631": True,
                "0x1632": True,
                "0x1633": True,
                "0x1634": True,
                "0x1635": True,
                "0x1636": False,
                "0x1637": False,
                "0x1638": False,
                "0x1639": False,
                "0x163A": True,
                "0x163D": False,
                "0x163E": False,
            },
            "vars": {"0x5167": 0},
        },
        "seafoam_stopped_current": {
            "map": {"group": 97, "number": 87},
            "flags": {
                "0x0805": False,
                "0x162D": True,
                "0x162E": True,
                "0x162F": True,
                "0x1630": True,
                "0x1631": True,
                "0x1632": True,
                "0x1633": False,
                "0x1634": False,
                "0x1635": True,
                "0x1636": False,
                "0x1637": True,
                "0x1638": False,
                "0x1639": False,
                "0x163A": False,
                "0x163D": True,
                "0x163E": True,
            },
            "vars": {"0x5167": 0},
        },
    },
}
_MAIN = "\nint main(int argc, char **argv)\n{"
_RENAMED = "\nint s61_embedded_progression_main(int argc, char **argv)\n{"
_FNV1A64 = re.compile(r"[0-9A-F]{16}")


class ProgressionLifecycleError(RuntimeError):
    pass


def _fail(message: str) -> NoReturn:
    raise ProgressionLifecycleError(message)


def _path(value: Path) -> Path:
    return value if value.is_absolute() else ROOT / value


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fnv1a64(data: bytes) -> int:
    value = 14695981039346656037
    for byte in data:
        value ^= byte
        value = (value * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return value


def _read_json(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"{label}を読めません: {error}")
    if not isinstance(value, Mapping):
        _fail(f"{label} rootはobjectではありません")
    return value


def _u32(raw: bytes, offset: int, label: str) -> int:
    if not 0 <= offset <= len(raw) - 4:
        _fail(f"{label}がROM範囲外です")
    return int.from_bytes(raw[offset:offset + 4], "little")


def _rom_offset(pointer: int, label: str) -> int:
    if not 0x08000000 <= pointer < 0x0A000000:
        _fail(f"{label} pointerがROM範囲外です: {pointer:#x}")
    return pointer - 0x08000000


def _script_tags(raw: bytes, table_pointer: int, label: str) -> tuple[int, ...]:
    offset = _rom_offset(table_pointer, label)
    result: list[int] = []
    for _ in range(12):
        if offset >= len(raw):
            _fail(f"{label} tableがROM終端を越えます")
        tag = raw[offset]
        if tag == 0:
            return tuple(result)
        pointer = _u32(raw, offset + 1, label + " entry")
        _rom_offset(pointer, label + " script")
        result.append(tag)
        offset += 5
    _fail(f"{label} table終端がありません")


def verify_rom_roots(raw: bytes) -> dict[str, Any]:
    """Map-group root→header→script-tableをROMから直接再解決する。"""
    root = _rom_offset(_u32(raw, 0x54B0C, "gMapGroups"), "gMapGroups")

    def table(group: int, number: int, expected: tuple[int, ...]) -> dict[str, Any]:
        group_table = _rom_offset(_u32(raw, root + group * 4, "map group"), "map group")
        header = _rom_offset(_u32(raw, group_table + number * 4, "map header"), "map header")
        script = _u32(raw, header + 8, "map script table")
        tags = _script_tags(raw, script, f"{group:03d}/{number:03d}")
        if tags != expected:
            _fail(f"{group:03d}/{number:03d} script tag root不一致: {tags} != {expected}")
        return {"map": f"{group:03d}/{number:03d}",
                "header": f"0x{header + 0x08000000:08X}",
                "script_table": f"0x{script:08X}", "tags": list(tags)}

    league = [table(97, number, expected) for number, expected in (
        (75, (5, 1, 4, 2)), (76, (5, 1, 4, 2)),
        (77, (5, 1, 4, 2)), (78, (5, 1, 4, 2)),
        (79, (4, 2)), (80, (3,)),
    )]
    seafoam = [table(97, number, expected) for number, expected in (
        (83, ()), (84, ()), (85, ()), (86, (3, 2)), (87, (3, 1, 4, 2)),
    )]
    return {"map_groups_pointer": "0x08054B0C", "league": league, "seafoam": seafoam}


def read_identity(rom_path: Path, metadata_path: Path) -> dict[str, Any]:
    rom = _path(rom_path)
    raw = rom.read_bytes()
    if len(raw) != 32 * 1024 * 1024:
        _fail(f"Stage61 ROM size不一致: {len(raw)}")
    digest = _sha(raw)
    roots = verify_rom_roots(raw)
    metadata_file = _path(metadata_path)
    metadata = _read_json(metadata_file, "Stage61 metadata")
    output = metadata.get("output")
    if metadata.get("schema_version") != 1 or metadata.get("stage") != 61 \
            or metadata.get("task") != TASK or metadata.get("status") != "PASS" \
            or not isinstance(output, Mapping) or output.get("size") != len(raw) \
            or output.get("sha256") != digest:
        _fail("Stage61 ROM/metadata identity不一致")
    return {"rom": str(rom.resolve()), "rom_sha256": digest,
            "metadata": str(metadata_file.resolve()),
            "metadata_sha256": _sha(metadata_file.read_bytes()), "roots": roots}


def _verify_identity_unchanged(identity: Mapping[str, Any]) -> None:
    if _sha(Path(identity["rom"]).read_bytes()) != identity["rom_sha256"]:
        _fail("実走中にStage61 ROM identityが変化しました")
    if _sha(Path(identity["metadata"]).read_bytes()) \
            != identity["metadata_sha256"]:
        _fail("実走中にStage61 metadata identityが変化しました")


def _verify_compiled_sources_unchanged(compile_info: Mapping[str, Any]) -> None:
    sources = compile_info["sources"]
    for label in ("runner_c", "orchestrator", "rfu_source", "rfu_header"):
        source = sources[label]
        if _sha(Path(source["path"]).read_bytes()) != source["sha256"]:
            _fail(f"実走中に{label} source identityが変化しました")


def _build_embedded(destination: Path) -> dict[str, Any]:
    source = ROOT / EMBEDDED
    text = source.read_text(encoding="utf-8")
    if text.count(_MAIN) != 1:
        _fail("embedded runner main定義が一意ではありません")
    transformed = text.replace(_MAIN, _RENAMED, 1)
    destination.write_text(transformed, encoding="utf-8", newline="\n")
    return {"source": str(EMBEDDED), "source_sha256": _sha(text.encode()),
            "transformed_sha256": _sha(transformed.encode()), "main_renamed": True}


def compile_runner(executable: Path) -> dict[str, Any]:
    compiler = shutil.which("cc")
    rfu_source = ROOT / RFU_SOURCE
    rfu_header = ROOT / RFU_HEADER
    missing = [
        str(path) for path in (rfu_source, rfu_header) if not path.is_file()
    ]
    if compiler is None or missing:
        _fail(f"compile前提不足: cc={compiler}, missing={missing}")
    executable.parent.mkdir(parents=True, exist_ok=True)
    embedded = executable.parent / "stage61-progression-embedded.c"
    identity = _build_embedded(embedded)
    command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-pedantic", f"-I{ROOT / 'tools'}",
               f'-DS61_PROGRESSION_EMBEDDED_HARNESS="{embedded}"',
               str(ROOT / SOURCE), str(rfu_source),
               "-o", str(executable), "-lmgba"]
    completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=180, check=False)
    if completed.returncode or completed.stdout or completed.stderr:
        _fail("progression lifecycle C compile失敗: "
              + (completed.stderr or completed.stdout or str(completed.returncode))[-6000:])
    c_source = ROOT / SOURCE
    orchestrator = Path(__file__).resolve()
    return {"status": "PASS", "embedded": identity,
            "sources": {
                "runner_c": {"path": str(c_source.resolve()),
                             "sha256": _sha(c_source.read_bytes())},
                "orchestrator": {"path": str(orchestrator),
                                 "sha256": _sha(orchestrator.read_bytes())},
                "rfu_source": {"path": str(rfu_source.resolve()),
                               "sha256": _sha(rfu_source.read_bytes())},
                "rfu_header": {"path": str(rfu_header.resolve()),
                               "sha256": _sha(rfu_header.read_bytes())},
            },
            "command": "cc -std=c11 -O2 -Wall -Wextra -Werror -pedantic ... -lmgba"}


def _require_map(value: Any, keys: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        _fail(f"{label} keys不一致")
    return value


def _positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        _fail(f"{label}は正の整数ではありません")
    return value


def _remove_exact_generated_path(path: Path, label: str) -> None:
    """再実走時のstale PASSを排除する。指定した単一生成物以外は触らない。"""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        _fail(f"{label} pathが通常fileではありません: {path}")


def _prepare_output(output: Path | None, identity: Mapping[str, Any]) -> Path | None:
    if output is None:
        return None
    destination = _path(output).absolute()
    protected = {
        Path(identity["rom"]).absolute(),
        Path(identity["metadata"]).absolute(),
        (ROOT / SOURCE).absolute(),
        Path(__file__).absolute(),
    }
    if destination in protected:
        _fail("report outputがROM/metadata/sourceと同一pathです")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _remove_exact_generated_path(destination, "report output")
    return destination


def _runtime_artifact_names(mode: str) -> set[str]:
    names = set(PROCESS_ARTIFACT_NAMES.values())
    for stem in ARTIFACT_STEMS[mode]:
        names.add(f"{stem}.srm")
        names.add(f"{stem}.ppm")
    return names


def _prepare_run_directory(work: Path, mode: str) -> int:
    """既知の生成物だけをpreclearし、process起動前の空dirを保証する。"""
    if work.is_symlink() or (work.exists() and not work.is_dir()):
        _fail(f"run directoryが通常directoryではありません: {work}")
    work.mkdir(parents=True, exist_ok=True)
    expected = _runtime_artifact_names(mode)
    unknown = sorted(path.name for path in work.iterdir()
                     if path.name not in expected)
    if unknown:
        _fail(f"run directoryに未知の既存entryがあります: {unknown}")
    removed = 0
    for name in sorted(expected):
        path = work / name
        if path.exists() or path.is_symlink():
            _remove_exact_generated_path(path, "runtime artifact")
            removed += 1
    if any(work.iterdir()):
        _fail("run directoryをprocess起動前に空にできません")
    return removed


def _prepare_runtime_artifacts(work: Path, mode: str) -> None:
    """後方互換のtest helper。単一run directoryを完全preclearする。"""
    _prepare_run_directory(work, mode)


def _write_bytes_atomic(destination: Path, raw: bytes) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=destination.name + ".", suffix=".tmp",
            dir=destination.parent, delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(raw)
            temporary.flush()
            os.fsync(temporary.fileno())
        temporary_path.replace(destination)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _write_json_atomic(destination: Path, value: Mapping[str, Any]) -> None:
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
           + "\n").encode("utf-8")
    _write_bytes_atomic(destination, raw)


def _artifact_descriptor(path: Path, expected: bytes, *, role: str,
                         format_name: str, case_id: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        _fail(f"retained artifactが通常fileではありません: {path.name}")
    actual = path.read_bytes()
    if actual != expected:
        _fail(f"retained artifact atomic再読不一致: {path.name}")
    return {
        "path": str(path.resolve()),
        "name": path.name,
        "role": role,
        "format": format_name,
        "case_id": case_id,
        "size": len(actual),
        "sha256": _sha(actual),
        "raw_re_read": True,
        "atomic_retain": True,
    }


def _retain_bytes(path: Path, raw: bytes, *, role: str,
                  format_name: str, case_id: str) -> dict[str, Any]:
    _write_bytes_atomic(path, raw)
    return _artifact_descriptor(
        path, raw, role=role, format_name=format_name, case_id=case_id
    )


def _validate_srm(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        _fail(f"必須SRMが通常fileではありません: {path.name}")
    raw = path.read_bytes()
    if len(raw) != SAVE_SIZE:
        _fail(f"SRM size不一致: {path.name}: {len(raw)}")
    if len(set(raw)) < 2:
        _fail(f"SRM内容が一様で実SAVE証跡ではありません: {path.name}")
    _write_bytes_atomic(path, raw)
    return _artifact_descriptor(
        path, raw, role="cold_continue_srm", format_name="flash1m-srm",
        case_id=path.stem,
    )


def _validate_ppm(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        _fail(f"必須framebuffer PPMが通常fileではありません: {path.name}")
    raw = path.read_bytes()
    expected_size = len(PPM_HEADER) + PPM_PIXEL_SIZE
    if len(raw) != expected_size or not raw.startswith(PPM_HEADER):
        _fail(f"framebuffer PPM形式/size不一致: {path.name}")
    pixels = raw[len(PPM_HEADER):]
    if len(set(pixels)) < 2:
        _fail(f"framebuffer PPMが一様画面です: {path.name}")
    _write_bytes_atomic(path, raw)
    return _artifact_descriptor(
        path, raw, role="cold_continue_framebuffer",
        format_name="ppm-p6-240x160", case_id=path.stem,
    )


def _validate_checkpoint_positions(value: Any, mode: str) -> None:
    checkpoints = _require_map(
        value, set(ARTIFACT_STEMS[mode]), f"{mode} checkpoint_positions"
    )
    for stem in ARTIFACT_STEMS[mode]:
        checkpoint = _require_map(
            checkpoints[stem], {"save_before", "cold_continue"},
            f"{stem} checkpoint",
        )
        positions: list[Mapping[str, Any]] = []
        for phase in ("save_before", "cold_continue"):
            position = _require_map(
                checkpoint[phase], {"x", "y", "warp_id"},
                f"{stem} {phase}",
            )
            for coordinate in ("x", "y"):
                item = position[coordinate]
                if (isinstance(item, bool) or not isinstance(item, int)
                        or not 0 <= item <= 0xFFFF):
                    _fail(f"{stem} {phase} {coordinate}がu16ではありません")
            warp_id = position["warp_id"]
            if (isinstance(warp_id, bool) or not isinstance(warp_id, int)
                    or not 0 <= warp_id <= 0xFF):
                _fail(f"{stem} {phase} warp_idがu8ではありません")
            positions.append(position)
        if positions[0] != positions[1]:
            _fail(f"{stem} save直前とcold Continue後の位置が不一致です")


def _validate_checkpoint_framebuffer_hashes(
        value: Any, mode: str, work_dir: Path) -> None:
    hashes = _require_map(
        value, set(ARTIFACT_STEMS[mode]),
        f"{mode} checkpoint_framebuffer_fnv1a64",
    )
    for stem in ARTIFACT_STEMS[mode]:
        expected = hashes[stem]
        if not isinstance(expected, str) or _FNV1A64.fullmatch(expected) is None:
            _fail(f"{stem} checkpoint framebuffer FNV-1a64形式不一致")
        ppm = (work_dir / f"{stem}.ppm").read_bytes()
        if not ppm.startswith(PPM_HEADER):
            _fail(f"{stem} checkpoint framebuffer PPM header不一致")
        actual = f"{_fnv1a64(ppm[len(PPM_HEADER):]):016X}"
        if actual != expected:
            _fail(f"{stem} checkpoint framebuffer FNV-1a64不一致")


def validate_result(value: Any, work_dir: Path, mode: str) -> dict[str, Any]:
    if mode == "league":
        keys = {"schema_version", "status", "case", "room_order", "scene_var",
                "scene_sequence_exact", "completion_sequence_exact",
                "trainer_battle_wins", "trainer_battle_losses", "blackout_exercised",
                "last_heal_match", "blackout_field_recovered",
                "blackout_scene_high_water_preserved", "completion_absent_after_loss",
                "actual_reentry_after_blackout", "retry_win_committed",
                "physical_room_warp_transitions", "actual_walk_steps",
                "face_a_battle_cases", "owner_pc_cases", "owner_pc_hits",
                "battle_resume_instruction_trace_cases",
                "elite_completion_adapter_cases",
                "champion_no_geometry_negative_control",
                "field_recovery_cases", "hall_of_fame_tag3_field_terminal",
                "checkpoint_positions", "checkpoint_framebuffer_fnv1a64",
                "start_save_cases", "fresh_continue_cases",
                "bootstrap_stock_warp_calls",
                "direct_owner_or_script_calls", "failed", "untested", "warnings"}
        result = _require_map(value, keys, "league result")
        required = {
            "schema_version": RESULT_SCHEMA_VERSION, "status": "PASS",
            "case": "league_progression_lifecycle_complete",
            "room_order": ["097/075", "097/076", "097/077", "097/078",
                           "097/079", "097/080"], "scene_var": "0x516C",
            "scene_sequence_exact": [1, 2, 3, 4, 5, 5],
            "completion_sequence_exact": ["0x1408", "0x1409", "0x140A",
                                          "0x140B", "0x140C"],
            "trainer_battle_wins": 6, "trainer_battle_losses": 1,
            "blackout_exercised": True, "last_heal_match": True,
            "blackout_field_recovered": True,
            "blackout_scene_high_water_preserved": True,
            "completion_absent_after_loss": True,
            "actual_reentry_after_blackout": True, "retry_win_committed": True,
            "physical_room_warp_transitions": 6, "face_a_battle_cases": 7,
            "owner_pc_cases": 7, "field_recovery_cases": 6,
            "battle_resume_instruction_trace_cases": 6,
            "elite_completion_adapter_cases": 5,
            "champion_no_geometry_negative_control": True,
            "hall_of_fame_tag3_field_terminal": True,
            "start_save_cases": 2, "fresh_continue_cases": 2,
            "bootstrap_stock_warp_calls": 3, "direct_owner_or_script_calls": 0,
            "failed": 0, "untested": 0, "warnings": 0,
        }
        assets = ARTIFACT_STEMS["league"]
    else:
        keys = {"schema_version", "status", "case", "static_maps_83_through_87",
                "runtime_maps_b3_b4", "flag_state_variants",
                "runtime_maps_1f_through_b4", "route20_reset_owner_cases",
                "route20_reset_owner_pc_hits",
                "upper_b3_physical_chain_cases",
                "distinct_b3_b4_physical_chain_cases",
                "active_current_control_chain_cases",
                "actual_strength_prompt_cases", "strength_zero_to_one_transition_cases",
                "native_strength_clear_after_fall_cases",
                "actual_boulder_push_cases", "actual_boulder_push_steps",
                "actual_hole_fall_cases", "fall_owner_pc_cases", "fall_owner_pc_hits",
                "push_owner_pc_cases", "push_owner_pc_hits",
                "strength_owner_pc_cases", "strength_owner_pc_hits",
                "topology_hide_arrival_transition_cases", "surf_observed_cases",
                "active_current_motion_cases", "active_current_motion_observed",
                "b3_current_stop_observed", "b4_current_stop_observed",
                "stopped_current_flag_observed", "non_producer_obstacle_controls",
                "topology_direct_flag_writes",
                "active_stopped_layouts_distinct", "physical_exit_reentry_cases",
                "checkpoint_positions", "checkpoint_framebuffer_fnv1a64",
                "start_save_cases", "fresh_continue_cases",
                "field_callback_chain_cases",
                "actual_walk_steps", "bootstrap_stock_warp_calls",
                "direct_owner_or_script_calls", "failed", "untested", "warnings"}
        result = _require_map(value, keys, "seafoam result")
        required = {
            "schema_version": RESULT_SCHEMA_VERSION, "status": "PASS",
            "case": "seafoam_progression_lifecycle_complete",
            "static_maps_83_through_87": 5, "runtime_maps_b3_b4": 2,
            "flag_state_variants": 2, "runtime_maps_1f_through_b4": 5,
            "route20_reset_owner_cases": 2,
            "upper_b3_physical_chain_cases": 2,
            "distinct_b3_b4_physical_chain_cases": 2,
            "active_current_control_chain_cases": 1,
            "actual_strength_prompt_cases": 9,
            "strength_zero_to_one_transition_cases": 9,
            "native_strength_clear_after_fall_cases": 9,
            "actual_boulder_push_cases": 9, "actual_boulder_push_steps": 23,
            "actual_hole_fall_cases": 9,
            "topology_hide_arrival_transition_cases": 9,
            "fall_owner_pc_cases": 9, "push_owner_pc_cases": 9,
            "strength_owner_pc_cases": 9, "surf_observed_cases": 4,
            "active_current_motion_cases": 3,
            "active_current_motion_observed": True,
            "b3_current_stop_observed": True,
            "b4_current_stop_observed": True,
            "stopped_current_flag_observed": True,
            "non_producer_obstacle_controls": 2,
            "topology_direct_flag_writes": 0,
            "active_stopped_layouts_distinct": True,
            "physical_exit_reentry_cases": 2, "start_save_cases": 2,
            "fresh_continue_cases": 2, "field_callback_chain_cases": 2,
            "bootstrap_stock_warp_calls": 5, "direct_owner_or_script_calls": 0,
            "failed": 0, "untested": 0, "warnings": 0,
        }
        assets = ARTIFACT_STEMS["seafoam"]
    for key, expected in required.items():
        if result.get(key) != expected:
            _fail(f"mGBA result {key}不一致: {result.get(key)!r} != {expected!r}")
    _validate_checkpoint_positions(result.get("checkpoint_positions"), mode)
    _positive_int(result.get("actual_walk_steps"), "actual_walk_steps")
    if mode == "league":
        if _positive_int(result.get("owner_pc_hits"), "owner_pc_hits") \
                < result["owner_pc_cases"]:
            _fail("trainer owner PC hit数がcase数未満です")
    else:
        if _positive_int(result.get("fall_owner_pc_hits"), "fall_owner_pc_hits") \
                < result["fall_owner_pc_cases"]:
            _fail("fall owner PC hit数がcase数未満です")
        if _positive_int(result.get("strength_owner_pc_hits"), "strength_owner_pc_hits") \
                < result["strength_owner_pc_cases"]:
            _fail("Strength owner PC hit数がcase数未満です")
        if _positive_int(result.get("push_owner_pc_hits"), "push_owner_pc_hits") \
                < result["push_owner_pc_cases"]:
            _fail("push owner PC hit数がcase数未満です")
        if _positive_int(
                result.get("route20_reset_owner_pc_hits"),
                "route20_reset_owner_pc_hits") \
                < result["route20_reset_owner_cases"]:
            _fail("Route20 reset owner PC hit数がcase数未満です")
    artifacts: dict[str, dict[str, Any]] = {}
    for stem in assets:
        artifacts[f"{stem}_srm"] = _validate_srm(work_dir / f"{stem}.srm")
        artifacts[f"{stem}_framebuffer"] = _validate_ppm(
            work_dir / f"{stem}.ppm"
        )
    _validate_checkpoint_framebuffer_hashes(
        result.get("checkpoint_framebuffer_fnv1a64"), mode, work_dir
    )
    return {"mode": mode, "result": dict(result), "artifacts": artifacts,
            "artifact_sha_re_read_by_orchestrator": True,
            "natural_input_owner_and_callback_validated": True,
            "distinct_mcore_cold_continue_validated": True,
            "checkpoint_expectations": CHECKPOINT_EXPECTATIONS[mode],
            "complete": True,
            "remaining": None}


def _canonical_result_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _parse_process_stdout(raw: bytes) -> Mapping[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        _fail(f"mGBA lifecycle stdoutがUTF-8ではありません: {error}")
    if not text.endswith("\n") or text.count("\n") != 1 or not text[:-1]:
        _fail("mGBA lifecycle JSON stdoutがexact 1行ではありません")
    try:
        value = json.loads(text[:-1])
    except json.JSONDecodeError as error:
        _fail(f"mGBA lifecycle JSON不正: {error}")
    if not isinstance(value, Mapping):
        _fail("mGBA lifecycle JSON rootはobjectではありません")
    return value


def _run_once(mode: str, executable: Path, rom: str, run_dir: Path,
              run_index: int,
    precleared: int) -> tuple[dict[str, Any], dict[str, Any]]:
    command = [str(executable), rom, str(run_dir), mode]
    process_environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith("S61_")
    }
    completed = subprocess.run(
        command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=7200, check=False, env=process_environment,
    )
    artifacts = {
        "process_stdout": _retain_bytes(
            run_dir / PROCESS_ARTIFACT_NAMES["stdout"], completed.stdout,
            role="mGBA_process_stdout", format_name="raw-utf8-json-line",
            case_id=mode,
        ),
        "process_stderr": _retain_bytes(
            run_dir / PROCESS_ARTIFACT_NAMES["stderr"], completed.stderr,
            role="mGBA_process_stderr", format_name="raw-bytes",
            case_id=mode,
        ),
    }
    if completed.returncode != 0 or completed.stderr:
        diagnostic = (completed.stderr or completed.stdout).decode(
            "utf-8", errors="replace"
        )
        _fail("mGBA lifecycle probe失敗: " + diagnostic[-6000:])
    raw_result = _parse_process_stdout(completed.stdout)
    canonical = _canonical_result_bytes(raw_result)
    artifacts["canonical_case_result"] = _retain_bytes(
        run_dir / PROCESS_ARTIFACT_NAMES["case_result"], canonical,
        role="canonical_case_result", format_name="canonical-json",
        case_id=mode,
    )
    if json.loads((run_dir / PROCESS_ARTIFACT_NAMES["stdout"])
                  .read_text(encoding="utf-8")) != raw_result:
        _fail("retained stdoutとparsed case-resultが一致しません")
    if json.loads((run_dir / PROCESS_ARTIFACT_NAMES["case_result"])
                  .read_text(encoding="utf-8")) != raw_result:
        _fail("canonical case-resultのatomic再読が一致しません")
    normalized = validate_result(raw_result, run_dir, mode)
    artifacts.update(normalized.pop("artifacts"))
    expected_names = _runtime_artifact_names(mode)
    actual_names = {path.name for path in run_dir.iterdir()}
    if actual_names != expected_names or len(artifacts) != 7:
        _fail("run retained artifact集合がexact 7件ではありません")
    result_sha = _sha(canonical)
    record = {
        "run_index": run_index,
        "directory": str(run_dir.resolve()),
        "directory_empty_before_launch": True,
        "stale_artifacts_precleared": precleared,
        "process": {
            "command": command,
            "returncode": completed.returncode,
            "stdout_case_result_exact_match": True,
            "stderr_empty": completed.stderr == b"",
            "normalized_result_sha256": result_sha,
        },
        "artifacts": artifacts,
    }
    return record, normalized


def _require_runs(runs: int) -> None:
    if isinstance(runs, bool) or runs != REQUIRED_RUNS:
        _fail(f"--runsはexact {REQUIRED_RUNS}でなければなりません")


def _path_independent_artifact_descriptors(
        record: Mapping[str, Any], run_index: int) -> dict[str, dict[str, Any]]:
    """Retained leafを再読し、run directoryだけを差し引いて比較可能にする。"""
    artifacts = record.get("artifacts")
    if not isinstance(artifacts, Mapping):
        _fail(f"run-{run_index} artifact descriptor rootがobjectではありません")
    normalized: dict[str, dict[str, Any]] = {}
    paths: set[Path] = set()
    for key, value in artifacts.items():
        if not isinstance(key, str) or not isinstance(value, Mapping) \
                or set(value) != ARTIFACT_DESCRIPTOR_KEYS:
            _fail(f"run-{run_index} artifact descriptor schema不一致: {key!r}")
        path_value = value.get("path")
        if not isinstance(path_value, str):
            _fail(f"run-{run_index} artifact pathが文字列ではありません: {key}")
        path = Path(path_value)
        if not path.is_absolute() or path.is_symlink() or not path.is_file() \
                or path in paths:
            _fail(f"run-{run_index} artifact pathが一意な通常fileではありません: {key}")
        paths.add(path)
        raw = path.read_bytes()
        size = value.get("size")
        digest = value.get("sha256")
        if isinstance(size, bool) or not isinstance(size, int) \
                or size != len(raw) or digest != _sha(raw) \
                or value.get("name") != path.name \
                or value.get("raw_re_read") is not True \
                or value.get("atomic_retain") is not True:
            _fail(f"run-{run_index} artifact descriptor/file再読不一致: {key}")
        normalized[key] = {
            descriptor_key: descriptor_value
            for descriptor_key, descriptor_value in value.items()
            if descriptor_key != "path"
        }
    return normalized


def _require_replay_match(run_records: list[Mapping[str, Any]],
                          validations: list[Mapping[str, Any]]) -> str:
    if len(run_records) != REQUIRED_RUNS or len(validations) != REQUIRED_RUNS:
        _fail("independent OS run数がexact 2ではありません")
    artifact_descriptors = [
        _path_independent_artifact_descriptors(record, index)
        for index, record in enumerate(run_records, start=1)
    ]
    if artifact_descriptors[0] != artifact_descriptors[1]:
        _fail(
            "2 independent OS runのpath除外artifact descriptorが"
            "exact一致しません"
        )
    result_hashes = [record["process"]["normalized_result_sha256"]
                     for record in run_records]
    if len(set(result_hashes)) != 1 or validations[0] != validations[1]:
        _fail("2 independent OS runのnormalized resultが一致しません")
    return str(result_hashes[0])


def run(mode: str, rom: Path, metadata: Path, output: Path | None,
        work_dir: Path | None, runs: int = REQUIRED_RUNS) -> dict[str, Any]:
    _require_runs(runs)
    identity = read_identity(rom, metadata)
    destination = _prepare_output(output, identity)
    if work_dir is None:
        work = Path(tempfile.mkdtemp(prefix=f"stage61-{mode}-lifecycle-"))
    else:
        work = _path(work_dir)
        if work.is_symlink() or (work.exists() and not work.is_dir()):
            _fail(f"work directoryが通常directoryではありません: {work}")
        work.mkdir(parents=True, exist_ok=True)
    work = work.resolve()
    run_dirs = [work / f"run-{index:02d}"
                for index in range(1, REQUIRED_RUNS + 1)]
    if destination is not None and any(
            destination == run_dir or run_dir in destination.parents
            for run_dir in run_dirs):
        _fail("report outputをruntime run directory内には置けません")
    executable = work / "stage61-progression-lifecycle"
    compile_info = compile_runner(executable)
    preclear_counts = [
        _prepare_run_directory(run_dir, mode) for run_dir in run_dirs
    ]
    run_records: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    for index in range(1, REQUIRED_RUNS + 1):
        _verify_identity_unchanged(identity)
        _verify_compiled_sources_unchanged(compile_info)
        record, normalized = _run_once(
            mode, executable, identity["rom"], run_dirs[index - 1], index,
            preclear_counts[index - 1],
        )
        run_records.append(record)
        validations.append(normalized)
    _verify_identity_unchanged(identity)
    _verify_compiled_sources_unchanged(compile_info)
    result_hash = _require_replay_match(run_records, validations)
    normalized = dict(validations[0])
    normalized["independent_os_subprocess_replay_validated"] = True
    report = {
        "schema_version": REPORT_SCHEMA_VERSION, "status": "PASS",
        "case": "stage61_progression_lifecycle_e2e", "mode": mode,
        "runs": REQUIRED_RUNS,
        "failed": 0, "untested": 0, "warnings": 0,
        "identity": identity, "compile": compile_info,
        "execution": {
            "backend": "libmGBA", "os_subprocess_runs": REQUIRED_RUNS,
            "distinct_mcore_instances_per_run": 6,
            "cold_boot_continue_instances_per_run": 2,
            "real_gba_key_input": True, "host_direct_owner_or_script_calls": 0,
            "stale_runtime_artifacts_precleared": True,
            "run_directories_empty_before_launch": True,
            "retained_artifacts_per_run": 7,
            "retained_artifacts_total": 14,
            "all_retained_artifacts_atomic": True,
            "stdout_case_result_exact_match": True,
            "independent_run_normalized_result_sha256_equal": True,
            "normalized_result_sha256": result_hash,
            "work_directory": str(work),
            "run_directories": [record["directory"] for record in run_records],
            "stderr_empty": True,
        },
        "validation": normalized,
        "run_records": run_records,
    }
    if destination is not None:
        _write_json_atomic(destination, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("league", "seafoam"))
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--runs", type=int, default=REQUIRED_RUNS)
    parser.add_argument("--compile-only", action="store_true")
    args = parser.parse_args()
    _require_runs(args.runs)
    if args.compile_only:
        with tempfile.TemporaryDirectory(prefix="stage61-progression-compile-") as temporary:
            print(json.dumps(compile_runner(Path(temporary) / "runner"), ensure_ascii=False))
        return 0
    print(json.dumps(run(args.mode, args.rom, args.metadata, args.output,
                         args.work_dir, args.runs), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
