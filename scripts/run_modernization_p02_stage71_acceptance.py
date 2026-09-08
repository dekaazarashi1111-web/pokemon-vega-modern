#!/usr/bin/env python3
"""Stage71累積ROMでP02の残runtime acceptanceを一度だけ閉じるgate。

Stage71 identity確定前はC harnessのcompile、固定CFRU ABI、既存P02証跡、
6種の進化rowをpreflightするだけで、runtime PASSを生成しない。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path("config/modernization_p02_stage71_acceptance_gate.json")
TASK = "USER-MODERNIZATION-P02-STAGE71-ACCEPTANCE"
ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
PENDING = "PENDING_STAGE71_FINAL_IDENTITY"


class ModernizationP02Stage71AcceptanceError(RuntimeError):
    """Stage71 identity、runtime、またはP02 acceptance契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP02Stage71AcceptanceError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _workspace_file(relative: str, label: str) -> Path:
    path = ROOT / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(ROOT.resolve())
    except (OSError, ValueError) as error:
        _fail(f"{label}がworkspace内の通常fileではありません: {relative}: {error}")
    if path.is_symlink() or not resolved.is_file():
        _fail(f"{label}がworkspace内の通常fileではありません: {relative}")
    return resolved


def _read_json(path: Path, label: str) -> dict[str, Any]:
    absolute = path if path.is_absolute() else ROOT / path
    try:
        value = json.loads(absolute.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(f"{label}をJSONとして読めません: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} rootがobjectではありません")
    return value


def _fixed(contract: Mapping[str, Any], label: str) -> bytes:
    expected = contract.get("sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        _fail(f"{label} SHA-256 pinが未確定です")
    path = _workspace_file(str(contract.get("path", "")), label)
    raw = path.read_bytes()
    size = contract.get("size")
    if size is not None and len(raw) != int(size):
        _fail(f"{label} size不一致: {len(raw)} != {size}")
    if _sha(raw) != expected:
        _fail(f"{label} SHA-256不一致")
    return raw


def _identity(relative: str, label: str = "source") -> dict[str, Any]:
    raw = _workspace_file(relative, label).read_bytes()
    return {"path": relative, "size": len(raw), "sha256": _sha(raw)}


def _config_relative(config_path: Path) -> str:
    absolute = config_path if config_path.is_absolute() else ROOT / config_path
    try:
        return absolute.resolve(strict=True).relative_to(ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        _fail("P02 Stage71 configはworkspace内の通常fileでなければなりません")


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}がboolです")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    _fail(f"{label}が整数ではありません: {value!r}")


def _validate_config(config: Mapping[str, Any]) -> None:
    if (config.get("schema_version"), config.get("task")) != (1, TASK):
        _fail("P02 Stage71 config schema/task不一致")
    status = config.get("status")
    if status not in {
        "WAITING_STAGE71_FINAL_IDENTITY",
        "STAGE71_FINAL_IDENTITY_PINNED",
    }:
        _fail("P02 Stage71 config status不一致")
    stage_inputs = (
        config.get("inputs", {}).get("stage71_rom", {}),
        config.get("inputs", {}).get("stage71_metadata", {}),
        config.get("inputs", {}).get("stage71_allocation", {}),
    )
    if status == "WAITING_STAGE71_FINAL_IDENTITY":
        if any(row.get("sha256") != PENDING for row in stage_inputs):
            _fail("waiting configに部分的なStage71 identity pinがあります")
    else:
        if any(
            not isinstance(row.get("sha256"), str)
            or len(row["sha256"]) != 64
            for row in stage_inputs
        ):
            _fail("final configのStage71 identityが未固定です")
    continue_save = config.get("inputs", {}).get("known_good_continue_save", {})
    if continue_save != {
        "path": ".local/60_wild_species_root_repair.srm",
        "size": 131072,
        "sha256": "f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb",
    }:
        _fail("既知正常Continue save identity契約不一致")

    table = config.get("evolution_table", {})
    repairs = table.get("level_held_item_repairs")
    if (
        _integer(table.get("address"), "evolution_table.address") != 0x094FE8E0
        or table.get("count") != 1670
        or table.get("stride") != 128
        or table.get("entry_size") != 8
        or not isinstance(repairs, list)
        or len(repairs) != 6
        or [row.get("species_id") for row in repairs]
        != [499, 759, 861, 993, 1001, 1121]
    ):
        _fail("P02 level+held-item 6種row契約不一致")
    for row in repairs:
        regular = row.get("regular_entry")
        conditional = row.get("conditional_entry")
        if (
            not isinstance(regular, list)
            or not isinstance(conditional, list)
            or len(regular) != 4
            or len(conditional) != 4
            or regular[0] != 4
            or conditional[0] != 35
            or regular[1] != conditional[1]
        ):
            _fail(f"P02 repair row ABI不一致: species={row.get('species_id')}")

    runtime = config.get("runtime", {})
    boot = runtime.get("boot_fixture", {})
    if (
        runtime.get("process_runs") != 2
        or not isinstance(runtime.get("timeout_seconds"), int)
        or runtime["timeout_seconds"] < 60
        or set(runtime.get("symbols", {}))
        != {
            "BeginEvolutionScene",
            "GetEvolutionTargetSpecies",
            "ItemEvolutionRemoval",
            "GetMonAbility",
            "CalculateMonStats",
            "ItemUseCB_EvolutionStone",
            "TrySavingData",
            "Save_LoadGameData",
        }
        or boot != {
            "policy":
                "PINNED_KNOWN_GOOD_SAVE_NORMAL_TITLE_CONTINUE_THEN_RAM_FIXTURE_REPLACEMENT",
            "per_process_seed_copy": True,
            "source_save_never_mutated": True,
            "stable_field_callback": "0x08055E75",
            "map_group": 96,
            "map_num": 5,
            "x": 20,
            "y": 20,
            "quest_log_state": 0,
            "quest_log_playback_state": 0,
            "field_lock": 0,
            "fixture_mutation_boundary":
                "AFTER_NORMAL_CONTINUE_INPUT_READY_FIELD_ONLY",
            "forbidden_synthetic_post_trace_call": "QOL_B_RETURN_WARP",
            "rejected_reset_callback": {
                "address": "0x080ED8D1",
                "symbol": "CB2_Intro",
                "classification": "SOFT_RESET_INTRO_NOT_FIELD",
            },
        }
    ):
        _fail("P02 Stage71 runtime契約不一致")
    required = config.get("acceptance", {}).get("required_routes")
    if not isinstance(required, list) or len(required) != 11 or len(set(required)) != 11:
        _fail("P02 Stage71 required acceptance route不一致")
    acceptance = config["acceptance"]
    if (
        acceptance.get("normal_cancel") != {
            "source_species_id": 1,
            "source_species_key": "SPECIES_KEY_VEGA_001",
            "source_display_name_ja": "リープン",
            "target_species_id": 2,
            "target_species_key": "SPECIES_KEY_VEGA_002",
            "target_display_name_ja": "リーティン",
            "start_level": 15,
            "trigger_item_id": 68,
        }
        or acceptance.get("bag_item") != {
            "source_species_id": 19,
            "source_species_key": "SPECIES_KEY_TOGETIC",
            "target_species_id": 20,
            "target_species_key": "SPECIES_KEY_TOGEKISS",
            "item_id": 93,
            "item_key": "ITEM_KEY_SUN_STONE",
            "stage71_evolution_row": [7, 93, 20, 0],
        }
        or acceptance.get("retained_moves") != [246, 33, 45, 52]
    ):
        _fail("P02 Stage71 representative identity契約不一致")


def _validate_historical(config: Mapping[str, Any]) -> dict[str, Any]:
    acceptance_raw = _fixed(
        config["inputs"]["historical_acceptance_checkpoint"],
        "historical P02 acceptance checkpoint",
    )
    rayquaza_raw = _fixed(
        config["inputs"]["historical_rayquaza_gate"],
        "historical P02 Rayquaza gate",
    )
    try:
        acceptance = json.loads(acceptance_raw)
        rayquaza = json.loads(rayquaza_raw)
    except (UnicodeError, json.JSONDecodeError) as error:
        _fail(f"historical P02 evidenceがJSONではありません: {error}")
    claims = acceptance.get("claims", {})
    result = acceptance.get("runtime_result", {})
    hidden = result.get("hidden_ability_readback", {})
    if (
        acceptance.get("status") != "CHECKPOINT_NOT_DONE"
        or claims.get("level_held_item_slot_priority_root_fixed") is not True
        or claims.get("correct_condition_item_only_consumed") is not True
        or claims.get("target_application_rom_consumers_executed") is not True
        or claims.get("hidden_ability_bit_readback_verified") is not True
        or claims.get("full_evolution_acceptance") is not False
        or result.get("classification") != "DIRECT_REAL_CONSUMER_CHECKPOINT"
        or result.get("level_item_priority_repair", {}).get("repaired_species_count") != 6
        or hidden.get("all_observed_preserved") is not True
    ):
        _fail("historical P02 partial acceptanceを継承できません")
    ray_claims = rayquaza.get("claims", {})
    if (
        rayquaza.get("status") != "PASS"
        or ray_claims.get("dragon_ascent_630_selects_mega_rayquaza_1092") is not True
        or ray_claims.get("historical_773_does_not_select_wish_mega") is not True
        or ray_claims.get("full_evolution_acceptance") is not False
    ):
        _fail("historical Rayquaza gateを継承できません")
    return {
        "acceptance_checkpoint": config["inputs"]["historical_acceptance_checkpoint"],
        "rayquaza_gate": config["inputs"]["historical_rayquaza_gate"],
        "six_level_held_item_cases": True,
        "hidden_ability_readback": True,
        "rayquaza_wish_mega": True,
        "historical_full_acceptance": False,
    }


def _validate_symbols(rom: bytes, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for name, contract in config["runtime"]["symbols"].items():
        address = _integer(contract.get("address"), f"symbol.{name}.address")
        offset = address - ROM_BASE
        try:
            expected = bytes.fromhex(str(contract.get("entry_bytes", "")))
        except ValueError:
            _fail(f"symbol.{name}.entry_bytesがhexではありません")
        if address & 1 or len(expected) != 8 or not 0 <= offset <= len(rom) - 8:
            _fail(f"symbol.{name} ABI契約不一致")
        actual = rom[offset:offset + 8]
        if actual != expected:
            _fail(f"symbol.{name} entry bytes不一致")
        evidence.append({
            "name": name,
            "address": f"0x{address:08X}",
            "thumb_entry": f"0x{address | 1:08X}",
            "entry_bytes": actual.hex(),
        })
    return evidence


def _validate_repair_rows(rom: bytes, config: Mapping[str, Any]) -> dict[str, Any]:
    table = config["evolution_table"]
    root = _integer(table["address"], "evolution table") - ROM_BASE
    count = int(table["count"])
    stride = int(table["stride"])
    entry_size = int(table["entry_size"])
    if root < 0 or root + count * stride > len(rom):
        _fail("Stage71 evolution tableがROM範囲外です")
    representatives = {
        1: [4, 16, 2, 0],
        19: [7, 93, 20, 0],
    }
    for species, values in representatives.items():
        expected = struct.pack("<HHHH", *values)
        offset = root + species * stride
        if rom[offset:offset + entry_size] != expected:
            _fail(f"Stage71 representative evolution row不一致: species={species}")
    rows: list[dict[str, Any]] = []
    for row in table["level_held_item_repairs"]:
        species = int(row["species_id"])
        offset = root + species * stride
        expected = struct.pack(
            "<HHHHHHHH",
            *[int(value) for value in row["regular_entry"]],
            *[int(value) for value in row["conditional_entry"]],
        )
        if rom[offset:offset + 2 * entry_size] != expected:
            _fail(f"Stage71 P02 repaired row不一致: species={species}")
        rows.append({
            "species_id": species,
            "source": row["source"],
            "rom_offset": offset,
            "entry_hex": expected.hex(),
        })
    return {
        "status": "PASS",
        "table_address": f"0x{root + ROM_BASE:08X}",
        "table_extent_inside_rom": True,
        "species_count": len(rows),
        "representative_rows": {
            "SPECIES_KEY_VEGA_001": representatives[1],
            "SPECIES_KEY_TOGETIC": representatives[19],
        },
        "rows": rows,
    }


def _validate_libmgba(config: Mapping[str, Any]) -> dict[str, Any]:
    contract = config["runtime"]["libmgba"]
    path = Path(str(contract.get("path", "")))
    if path.is_symlink() or not path.is_file():
        _fail("固定libmGBAが通常fileではありません")
    raw = path.read_bytes()
    if _sha(raw) != contract.get("sha256"):
        _fail("固定libmGBA SHA-256不一致")
    return {"path": str(path), "size": len(raw), "sha256": _sha(raw)}


def _compile_harness(
    config: Mapping[str, Any], directory: Path,
) -> tuple[Path, dict[str, Any]]:
    runtime = config["runtime"]
    compiler = shutil.which(str(runtime["compiler"]))
    if compiler is None:
        _fail("C compilerがありません")
    version = subprocess.run(
        [compiler, "--version"], cwd=ROOT, capture_output=True, text=True,
        check=False,
    )
    if version.returncode or not version.stdout.splitlines():
        _fail("C compiler versionを取得できません")
    executable = directory / "p02-stage71-acceptance-smoke"
    command = [
        compiler,
        *map(str, runtime["compile_flags"]),
        str(ROOT / runtime["runner_source"]),
        "-o",
        str(executable),
        *map(str, runtime["link_flags"]),
    ]
    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True,
        timeout=int(runtime["timeout_seconds"]), check=False,
    )
    if completed.returncode:
        _fail(f"P02 Stage71 harness compile失敗: {completed.stdout}{completed.stderr}")
    if completed.stdout or completed.stderr:
        _fail("P02 Stage71 harness compileが予期しない出力を生成しました")
    return executable, {
        "compiler": compiler,
        "compiler_version": version.stdout.splitlines()[0],
        "compile_flags": runtime["compile_flags"],
        "link_flags": runtime["link_flags"],
        "status": "PASS",
    }


def build_preflight(
    config_path: Path = DEFAULT_CONFIG,
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = _read_json(config_path, "P02 Stage71 config")
    _validate_config(config)
    reference = _fixed(config["inputs"]["preflight_reference_rom"], "Stage70 reference ROM")
    continue_save = _fixed(
        config["inputs"]["known_good_continue_save"],
        "known-good normal-Continue save",
    )
    if len(reference) != ROM_SIZE:
        _fail("Stage70 reference ROM size不一致")
    historical = _validate_historical(config)
    sources = [
        _identity(_config_relative(config_path), "config"),
        _identity(config["runtime"]["gate_script"]),
        _identity(config["runtime"]["runner_source"]),
        *[_identity(path) for path in config["runtime"]["transitive_sources"]],
    ]
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p02-stage71-compile-", dir=local) as raw:
        _executable, compilation = _compile_harness(config, Path(raw))
    preflight = {
        "config": sources[0],
        "reference_rom": config["inputs"]["preflight_reference_rom"],
        "known_good_continue_save": {
            **config["inputs"]["known_good_continue_save"],
            "identity_verified": True,
            "source_save_never_mutated": True,
            "validated_size": len(continue_save),
        },
        "historical": historical,
        "symbols": _validate_symbols(reference, config),
        "repaired_rows": _validate_repair_rows(reference, config),
        "sources": sources[1:],
        "libmgba": _validate_libmgba(config),
        "compilation": compilation,
        "stage71_identity_status": config["status"],
    }
    return config, preflight


def _waiting_evidence(config: Mapping[str, Any], preflight: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task": TASK,
        "status": "WAITING_STAGE71_FINAL_IDENTITY",
        "classification": "COMPILED_FAIL_CLOSED_PREFLIGHT_NO_RUNTIME_EXECUTION",
        "preflight": preflight,
        "stage71": {
            "rom": config["inputs"]["stage71_rom"],
            "metadata": config["inputs"]["stage71_metadata"],
            "allocation": config["inputs"]["stage71_allocation"],
            "identity_pinned": False,
        },
        "completed_acceptance": [
            "historical 6種level+held-item direct consumer証跡のhash継承",
            "Stage70参照ROMで6種rowとproduction symbol ABIを再確認",
            "Stage71用normal-input/fresh-core harnessの警告0 compile",
        ],
        "remaining_acceptance": list(config["acceptance"]["required_routes"]),
        "claims": {
            "harness_compiled": True,
            "stage71_identity_pinned": False,
            "stage71_exact_rom_executed": False,
            "normal_input_evolution_scene": False,
            "normal_input_cancel": False,
            "normal_bag_item_use": False,
            "post_scene_identity": False,
            "stock_save_fresh_core_reload": False,
            "full_evolution_acceptance": False,
        },
        "release_ready": False,
        "artifacts_written": [config["output"]],
    }


def _validate_stage71_inputs(
    config: Mapping[str, Any], rom: bytes, metadata_raw: bytes, allocation_raw: bytes,
) -> dict[str, Any]:
    try:
        metadata = json.loads(metadata_raw)
        allocation = json.loads(allocation_raw)
    except (UnicodeError, json.JSONDecodeError) as error:
        _fail(f"Stage71 metadata/allocationがJSONではありません: {error}")
    output = metadata.get("output", metadata.get("output_rom", {}))
    if (
        metadata.get("stage") != 71
        or not isinstance(output, dict)
        or output.get("size") != len(rom)
        or output.get("sha256") != _sha(rom)
        or metadata.get("allocation", {}).get("output_sha256")
            != _sha(allocation_raw)
    ):
        _fail("Stage71 metadata output identity不一致")
    allocations = allocation.get("allocations")
    if not isinstance(allocations, list) or len(allocations) != 74:
        _fail("Stage71 allocation ledgerが不正です")
    names: set[str] = set()
    intervals: list[tuple[int, int, str]] = []
    target = None
    for index, row in enumerate(allocations):
        if not isinstance(row, dict):
            _fail("Stage71 allocation rowがobjectではありません")
        start = row.get("start")
        end = row.get("end_exclusive")
        digest = row.get("content_sha256")
        name = row.get("name")
        if (
            not isinstance(start, int)
            or not isinstance(end, int)
            or not 0 <= start < end <= len(rom)
            or not isinstance(digest, str)
            or len(digest) != 64
            or not isinstance(name, str)
            or not name
            or name in names
            or row.get("sequence") != index
        ):
            _fail(f"Stage71 allocation row契約不一致: {name}")
        names.add(name)
        intervals.append((start, end, name))
        if name == "modernization_p04_species_runtime_stage70_payload":
            target = row
    for index, (start, end, name) in enumerate(sorted(intervals)):
        if index and start < sorted(intervals)[index - 1][1]:
            _fail(f"Stage71 allocation overlap: {name}")
    audit = metadata.get("allocation", {}).get("audit", {})
    if (
        target is None
        or audit.get("status") != "PASS"
        or audit.get("target_name") != target["name"]
        or audit.get("target_sequence") != target["sequence"]
        or audit.get("overlap_count") != 0
        or audit.get("non_target_rom_slices_unchanged") is not True
        or audit.get("full_target_allocation_slice_verified") is not True
        or _sha(rom[target["start"]:target["end_exclusive"]])
            != target["content_sha256"]
        or audit.get("output_full_slice_sha256") != target["content_sha256"]
    ):
        _fail("Stage71 target allocation audit不一致")
    return {
        "identity_pinned": True,
        "rom": config["inputs"]["stage71_rom"],
        "metadata": config["inputs"]["stage71_metadata"],
        "allocation": config["inputs"]["stage71_allocation"],
        "rom_sha256": _sha(rom),
        "metadata_output_bound": True,
        "allocation_row_count_structural": len(allocations),
        "allocation_overlap_count": 0,
        "stage71_target_allocation_content_hash_verified": True,
        "historical_allocation_content_hashes_not_reinterpreted_as_final_rom": True,
    }


def _validate_runtime_result(result: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    direct = result.get("direct_conditions", {})
    six = direct.get("level_held_item_six", {})
    cancel = result.get("normal_evolution_cancel", {})
    normal = result.get("normal_evolution_success", {})
    form = result.get("conditional_form_success", {})
    bag = result.get("bag_item_use", {})
    missing = result.get("bag_item_missing", {})
    reload = result.get("save_reload", {})
    expected_sha = config["inputs"]["stage71_rom"]["sha256"]
    if (
        result.get("schema_version") != 1
        or result.get("status") != "PASS"
        or result.get("classification")
        != "STAGE71_EXACT_ROM_NORMAL_INPUT_AND_FRESH_CORE"
        or result.get("rom_sha256") != expected_sha
        or result.get("known_good_seed_sha256")
            != config["inputs"]["known_good_continue_save"]["sha256"]
        or result.get("boot_route")
            != "NORMAL_TITLE_CONTINUE_PINNED_SAVE"
        or result.get("initial_normal_continue_field") is not True
        or result.get("fixture_replacement_after_field") is not True
        or result.get("warnings_errors") != 0
        or result.get("temporary_save_only") is not True
    ):
        _fail("P02 Stage71 runtime top-level contract不一致")
    if (
        direct.get("level") is not True
        or direct.get("friendship") is not True
        or direct.get("known_move") is not True
        or direct.get("trade") is not True
        or direct.get("night_form") is not True
        or six != {
            "species_count": 6,
            "conditional_selected": 6,
            "conditional_item_consumed": 6,
            "below_level_rejected": 6,
            "wrong_or_missing_item_regular": 12,
            "hidden_ability_preserved": 24,
            "payload_pc_seen": True,
        }
    ):
        _fail("P02 Stage71 condition/6種runtime matrix不一致")
    required_true = {
        "normal_evolution_cancel": (
            cancel,
            ("normal_bag_party_input", "scene_callbacks_seen", "physical_b_cancel",
             "source_retained", "four_moves_retained", "ability_slot_retained"),
        ),
        "normal_evolution_success": (
            normal,
            ("normal_bag_party_input", "scene_callbacks_seen", "target_applied",
             "four_moves_retained", "ability_slot_retained", "ability_matches_slot"),
        ),
        "conditional_form_success": (
            form,
            ("normal_bag_party_input", "scene_callbacks_seen", "exact_form_applied",
             "condition_item_consumed", "four_moves_retained",
             "hidden_ability_preserved", "ability_matches_hidden"),
        ),
        "bag_item_use": (
            bag,
            ("normal_start_bag_party_input", "scene_callbacks_seen", "target_applied",
             "bag_item_consumed", "four_moves_retained"),
        ),
        "bag_item_missing": (
            missing,
            ("normal_start_bag_input_attempted", "item_absent", "party_not_opened_for_item",
             "species_unchanged"),
        ),
        "save_reload": (
            reload,
            ("stock_save_twice", "original_core_destroyed", "fresh_core_created",
             "stock_load_succeeded", "normal_continue_load_succeeded",
             "exact_form_reloaded", "four_moves_reloaded",
             "condition_item_still_consumed", "hidden_ability_reloaded",
             "ability_matches_hidden"),
        ),
    }
    for label, (section, keys) in required_true.items():
        if any(section.get(key) is not True for key in keys):
            _fail(f"P02 Stage71 {label} contract不一致")


def _stopped_evidence(
    config: Mapping[str, Any], preflight: Mapping[str, Any],
) -> dict[str, Any]:
    rom = _fixed(config["inputs"]["stage71_rom"], "Stage71 final ROM")
    metadata = _fixed(config["inputs"]["stage71_metadata"], "Stage71 metadata")
    allocation = _fixed(config["inputs"]["stage71_allocation"], "Stage71 allocation")
    stage71 = _validate_stage71_inputs(config, rom, metadata, allocation)
    stage71["symbols"] = _validate_symbols(rom, config)
    stage71["repaired_rows"] = _validate_repair_rows(rom, config)
    completed = [
        "six_level_held_item_runtime_matrix",
        "condition_method_representatives",
    ]
    remaining = [
        route for route in config["acceptance"]["required_routes"]
        if route not in completed
    ]
    return {
        "schema_version": 1,
        "task": TASK,
        "status": "STOPPED_EXACT_UI_PENDING",
        "classification":
            "STAGE71_EXACT_ROM_TWO_HARNESS_FAILURES_PRODUCTION_RUNTIME_UNJUDGED",
        "failure_scope": "HARNESS_UI_NAVIGATION_UNRESOLVED_NOT_ROM_DEFECT",
        "preflight": preflight,
        "stage71": stage71,
        "execution": {
            "attempt_sets": [
                {
                    "attempt_set": 1,
                    "process_runs_started": 2,
                    "status": "FAIL",
                    "classification":
                        "HARNESS_SYNTHETIC_POST_TRACE_WARP_SOFT_RESET",
                    "error":
                        "field baseline cb=080ed8d1 save=0202548c x=0 y=0 party=0 script=0 logs=0",
                    "diagnosis":
                        "0x080ED8D1 is CB2_Intro after the fixture-only QOL_B_RETURN_WARP",
                },
                {
                    "attempt_set": 2,
                    "process_runs_started": 2,
                    "status": "FAIL",
                    "classification": "HARNESS_NORMAL_BAG_PARTY_ENTRY_FAILED",
                    "error":
                        "normal Start/Bag/party input did not reach party menu",
                    "natural_field_trace_passed_before_failure": True,
                    "direct_condition_matrix_passed_before_failure": True,
                    "second_process_terminated_after_first_failure": True,
                },
            ],
            "total_attempt_sets_for_stage71_identity": 2,
            "additional_mgba_execution_permitted": False,
            "structured_runtime_result_emitted": False,
            "p02_production_runtime_judgment": "UNJUDGED",
        },
        "next_cumulative_run_preparation": {
            "status": "STATIC_AND_COMPILE_READY_NOT_EXECUTED",
            "known_good_continue_save":
                config["inputs"]["known_good_continue_save"],
            "per_process_private_copy": True,
            "original_seed_never_mutated": True,
            "initial_route": [
                "attach_private_seed_copy",
                "ordinary_title_start_and_continue_input",
                "dismiss_quest_log_recap_by_ordinary_input",
                "require_120_input_ready_field_frames_at_96/5/20,20",
                "replace_only_party_and_item_test_fixture_after_field_ready",
            ],
            "fresh_core_reload_route": [
                "stock_TrySavingData_twice",
                "destroy_original_core",
                "attach_saved_private_copy_to_fresh_core",
                "ordinary_title_continue_load",
                "verify_persisted_species_form_moves_item_and_ability",
            ],
            "stage_diagnostics": [
                "initial_normal_continue",
                "fixture_replacement",
                "rare_candy_cancel_entry",
                "rare_candy_success_entry",
                "sun_stone_success_entry",
                "bag_item_missing_entry",
                "conditional_form_success_entry",
                "fresh_core_normal_continue",
            ],
        },
        "completed_acceptance": completed,
        "remaining_acceptance": remaining,
        "claims": {
            "harness_compiled": True,
            "stage71_identity_pinned": True,
            "stage71_exact_rom_executed": True,
            "condition_method_representatives_reached": True,
            "six_level_held_item_matrix_reached": True,
            "normal_input_evolution_scene": False,
            "normal_input_cancel": False,
            "normal_bag_item_use": False,
            "post_scene_identity": False,
            "stock_save_fresh_core_reload": False,
            "p02_production_runtime_judged": False,
            "full_evolution_acceptance": False,
        },
        "release_ready": False,
        "release_boundary":
            "P02_EXACT_UI_ACCEPTANCE_PENDING_OTHER_MODERNIZATION_WORK_CONTINUES",
        "artifacts_written": [config["output"]],
    }


def _run_processes(
    executable: Path, rom_path: Path, expected_sha: str,
    seed_save_path: Path, expected_seed_sha: str,
    directory: Path, count: int, timeout: int,
) -> list[dict[str, Any]]:
    processes: list[subprocess.Popen[str]] = []
    seed_raw = seed_save_path.read_bytes()
    if _sha(seed_raw) != expected_seed_sha:
        _fail("process seed save SHA-256が起動直前に変化しました")
    results: list[dict[str, Any]] = []
    try:
        for index in range(count):
            save = directory / f"process-{index}.sav"
            shutil.copyfile(seed_save_path, save)
            copied = save.read_bytes()
            if copied != seed_raw or _sha(copied) != expected_seed_sha:
                _fail(f"process-{index} private seed copy不一致")
            processes.append(subprocess.Popen(
                [str(executable), str(rom_path), str(save), expected_sha,
                 expected_seed_sha],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True,
            ))
        if len({process.pid for process in processes}) != count:
            _fail("独立mGBA process IDが重複しました")
        for process in processes:
            stdout, stderr = process.communicate(timeout=timeout)
            if process.returncode:
                _fail(f"P02 Stage71 mGBA runner失敗: {stderr.strip()}")
            if stderr:
                _fail(f"P02 Stage71 mGBA runnerがstderrを出力しました: {stderr.strip()}")
            try:
                value = json.loads(stdout)
            except json.JSONDecodeError as error:
                _fail(f"P02 Stage71 mGBA出力がJSONではありません: {error}")
            if not isinstance(value, dict):
                _fail("P02 Stage71 mGBA JSON rootがobjectではありません")
            results.append(value)
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()
    if seed_save_path.read_bytes() != seed_raw:
        _fail("known-good source saveがruntime中に変更されました")
    if not results or any(result != results[0] for result in results[1:]):
        _fail("独立P02 Stage71 mGBA process結果が一致しません")
    return results


def run_gate(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config, preflight = build_preflight(config_path)
    if config["status"] != "STAGE71_FINAL_IDENTITY_PINNED":
        _fail("Stage71 final identity未確定のため重いruntime gateを拒否します")
    rom = _fixed(config["inputs"]["stage71_rom"], "Stage71 final ROM")
    metadata_raw = _fixed(config["inputs"]["stage71_metadata"], "Stage71 metadata")
    allocation_raw = _fixed(config["inputs"]["stage71_allocation"], "Stage71 allocation")
    if len(rom) != ROM_SIZE:
        _fail("Stage71 final ROM size不一致")
    stage71 = _validate_stage71_inputs(config, rom, metadata_raw, allocation_raw)
    stage71["symbols"] = _validate_symbols(rom, config)
    stage71["repaired_rows"] = _validate_repair_rows(rom, config)

    runtime = config["runtime"]
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p02-stage71-runtime-", dir=local) as raw:
        temporary = Path(raw)
        executable, compilation = _compile_harness(config, temporary)
        results = _run_processes(
            executable,
            _workspace_file(config["inputs"]["stage71_rom"]["path"], "Stage71 ROM"),
            _sha(rom),
            _workspace_file(
                config["inputs"]["known_good_continue_save"]["path"],
                "known-good normal-Continue save",
            ),
            config["inputs"]["known_good_continue_save"]["sha256"],
            temporary,
            int(runtime["process_runs"]),
            int(runtime["timeout_seconds"]),
        )
    for result in results:
        _validate_runtime_result(result, config)
    runtime_result = results[0]
    return {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "classification": "EXACT_STAGE71_FULL_P02_RUNTIME_ACCEPTANCE",
        "preflight": preflight,
        "stage71": stage71,
        "execution": {
            **compilation,
            "process_runs": int(runtime["process_runs"]),
            "independent_processes": True,
            "identical_results": True,
            "runner_result_sha256": _sha(_stable(runtime_result)),
            "successful_attempt_sets_with_current_harness": 1,
            "failed_predecessor_attempt_sets": 2,
            "total_attempt_sets_for_stage71_identity": 3,
            "predecessor_failure_classifications": [
                "HARNESS_SYNTHETIC_POST_TRACE_WARP_SOFT_RESET",
                "HARNESS_NORMAL_BAG_PARTY_ENTRY_FAILED",
            ],
        },
        "runtime_result": runtime_result,
        "completed_acceptance": list(config["acceptance"]["required_routes"]),
        "remaining_acceptance": [],
        "claims": {
            "harness_compiled": True,
            "stage71_identity_pinned": True,
            "stage71_exact_rom_executed": True,
            "normal_input_evolution_scene": True,
            "normal_input_cancel": True,
            "normal_bag_item_use": True,
            "post_scene_identity": True,
            "stock_save_fresh_core_reload": True,
            "full_evolution_acceptance": True,
        },
        "release_ready": False,
        "release_boundary": "P02_ACCEPTED_BUT_P03_TO_P08_AND_FINAL_RELEASE_GATES_REMAIN",
        "artifacts_written": [config["output"]],
    }


def _validate_waiting(
    evidence: Mapping[str, Any], config: Mapping[str, Any], preflight: Mapping[str, Any],
) -> None:
    claims = evidence.get("claims", {})
    if (
        evidence.get("schema_version") != 1
        or evidence.get("task") != TASK
        or evidence.get("status") != "WAITING_STAGE71_FINAL_IDENTITY"
        or evidence.get("classification")
        != "COMPILED_FAIL_CLOSED_PREFLIGHT_NO_RUNTIME_EXECUTION"
        or evidence.get("preflight") != preflight
        or evidence.get("remaining_acceptance")
        != list(config["acceptance"]["required_routes"])
        or claims.get("harness_compiled") is not True
        or claims.get("stage71_exact_rom_executed") is not False
        or claims.get("full_evolution_acceptance") is not False
        or evidence.get("release_ready") is not False
        or "runtime_result" in evidence
    ):
        _fail("公開済みP02 Stage71 waiting checkpoint不一致")


def _validate_pass(
    evidence: Mapping[str, Any], config: Mapping[str, Any], preflight: Mapping[str, Any],
) -> None:
    claims = evidence.get("claims", {})
    if (
        evidence.get("schema_version") != 1
        or evidence.get("task") != TASK
        or evidence.get("status") != "PASS"
        or evidence.get("classification") != "EXACT_STAGE71_FULL_P02_RUNTIME_ACCEPTANCE"
        or evidence.get("preflight") != preflight
        or evidence.get("remaining_acceptance") != []
        or claims.get("stage71_exact_rom_executed") is not True
        or claims.get("full_evolution_acceptance") is not True
        or evidence.get("release_ready") is not False
        or evidence.get("execution", {}).get("process_runs") != 2
        or evidence.get("execution", {}).get(
            "successful_attempt_sets_with_current_harness") != 1
        or evidence.get("execution", {}).get("failed_predecessor_attempt_sets") != 2
        or evidence.get("execution", {}).get(
            "total_attempt_sets_for_stage71_identity") != 3
        or evidence.get("execution", {}).get(
            "predecessor_failure_classifications") != [
                "HARNESS_SYNTHETIC_POST_TRACE_WARP_SOFT_RESET",
                "HARNESS_NORMAL_BAG_PARTY_ENTRY_FAILED",
            ]
    ):
        _fail("公開済みP02 Stage71 PASS checkpoint不一致")
    _validate_runtime_result(evidence.get("runtime_result", {}), config)
    if evidence["execution"].get("runner_result_sha256") != _sha(
        _stable(evidence["runtime_result"])
    ):
        _fail("公開済みP02 Stage71 runner result hash不一致")


def _validate_stopped(
    evidence: Mapping[str, Any], config: Mapping[str, Any], preflight: Mapping[str, Any],
) -> None:
    execution = evidence.get("execution", {})
    claims = evidence.get("claims", {})
    completed = [
        "six_level_held_item_runtime_matrix",
        "condition_method_representatives",
    ]
    remaining = [
        route for route in config["acceptance"]["required_routes"]
        if route not in completed
    ]
    attempts = execution.get("attempt_sets")
    preparation = evidence.get("next_cumulative_run_preparation", {})
    if (
        evidence.get("schema_version") != 1
        or evidence.get("task") != TASK
        or evidence.get("status") != "STOPPED_EXACT_UI_PENDING"
        or evidence.get("classification")
            != "STAGE71_EXACT_ROM_TWO_HARNESS_FAILURES_PRODUCTION_RUNTIME_UNJUDGED"
        or evidence.get("failure_scope")
            != "HARNESS_UI_NAVIGATION_UNRESOLVED_NOT_ROM_DEFECT"
        or evidence.get("preflight") != preflight
        or evidence.get("completed_acceptance") != completed
        or evidence.get("remaining_acceptance") != remaining
        or execution.get("total_attempt_sets_for_stage71_identity") != 2
        or execution.get("additional_mgba_execution_permitted") is not False
        or execution.get("structured_runtime_result_emitted") is not False
        or execution.get("p02_production_runtime_judgment") != "UNJUDGED"
        or not isinstance(attempts, list)
        or len(attempts) != 2
        or attempts[0].get("status") != "FAIL"
        or attempts[0].get("classification")
            != "HARNESS_SYNTHETIC_POST_TRACE_WARP_SOFT_RESET"
        or attempts[1].get("status") != "FAIL"
        or attempts[1].get("classification")
            != "HARNESS_NORMAL_BAG_PARTY_ENTRY_FAILED"
        or attempts[1].get("direct_condition_matrix_passed_before_failure")
            is not True
        or attempts[1].get("second_process_terminated_after_first_failure")
            is not True
        or claims.get("stage71_exact_rom_executed") is not True
        or claims.get("normal_input_evolution_scene") is not False
        or claims.get("stock_save_fresh_core_reload") is not False
        or claims.get("p02_production_runtime_judged") is not False
        or claims.get("full_evolution_acceptance") is not False
        or preparation.get("status")
            != "STATIC_AND_COMPILE_READY_NOT_EXECUTED"
        or preparation.get("known_good_continue_save")
            != config["inputs"]["known_good_continue_save"]
        or preparation.get("per_process_private_copy") is not True
        or preparation.get("original_seed_never_mutated") is not True
        or preparation.get("stage_diagnostics") != [
            "initial_normal_continue",
            "fixture_replacement",
            "rare_candy_cancel_entry",
            "rare_candy_success_entry",
            "sun_stone_success_entry",
            "bag_item_missing_entry",
            "conditional_form_success_entry",
            "fresh_core_normal_continue",
        ]
        or evidence.get("release_boundary")
            != "P02_EXACT_UI_ACCEPTANCE_PENDING_OTHER_MODERNIZATION_WORK_CONTINUES"
        or evidence.get("release_ready") is not False
        or "runtime_result" in evidence
    ):
        _fail("公開済みP02 Stage71 stopped/pending checkpoint不一致")


def validate_published(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config, preflight = build_preflight(config_path)
    evidence = _read_json(Path(config["output"]), "P02 Stage71 checkpoint")
    if config["status"] == "WAITING_STAGE71_FINAL_IDENTITY":
        _validate_waiting(evidence, config, preflight)
    else:
        rom = _fixed(config["inputs"]["stage71_rom"], "Stage71 final ROM")
        metadata = _fixed(config["inputs"]["stage71_metadata"], "Stage71 metadata")
        allocation = _fixed(config["inputs"]["stage71_allocation"], "Stage71 allocation")
        _validate_stage71_inputs(config, rom, metadata, allocation)
        if evidence.get("status") == "STOPPED_EXACT_UI_PENDING":
            _validate_stopped(evidence, config, preflight)
        else:
            _validate_pass(evidence, config, preflight)
    return evidence


def _atomic_write(path: Path, raw: bytes) -> None:
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("prepare", "compile-check", "run", "record-stopped", "check"),
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    try:
        if args.mode == "prepare":
            config, preflight = build_preflight(args.config)
            evidence = _waiting_evidence(config, preflight)
            _atomic_write(Path(config["output"]), _stable(evidence))
        elif args.mode == "compile-check":
            config, _preflight = build_preflight(args.config)
            evidence = {
                "status": "PASS",
                "claims": {"full_evolution_acceptance": False},
                "stage71": {"identity_pinned": config["status"].endswith("PINNED")},
            }
        elif args.mode == "run":
            config = _read_json(args.config, "P02 Stage71 config")
            evidence = run_gate(args.config)
            _atomic_write(Path(config["output"]), _stable(evidence))
        elif args.mode == "record-stopped":
            config, preflight = build_preflight(args.config)
            if config["status"] != "STAGE71_FINAL_IDENTITY_PINNED":
                _fail("stopped runtime evidenceにはStage71 final identityが必要です")
            evidence = _stopped_evidence(config, preflight)
            _atomic_write(Path(config["output"]), _stable(evidence))
        else:
            evidence = validate_published(args.config)
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        struct.error,
        subprocess.SubprocessError,
        ModernizationP02Stage71AcceptanceError,
    ) as error:
        print(f"MODERNIZATION_P02_STAGE71_{args.mode.upper()}=FAIL", file=sys.stderr)
        print(str(error), file=sys.stderr)
        return 1
    print(
        f"MODERNIZATION_P02_STAGE71_{args.mode.upper()}=PASS "
        f"status={evidence['status']} "
        f"identity_pinned={evidence['stage71']['identity_pinned']} "
        f"full_acceptance={evidence['claims']['full_evolution_acceptance']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
