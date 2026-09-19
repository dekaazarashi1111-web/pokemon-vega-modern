#!/usr/bin/env python3
"""Stage68 Mega Stone BP shopの独立exact-ROM mGBA gateを実行／照合する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn


ROOT = Path(__file__).resolve().parents[1]
TASK = "USER-MODERNIZATION-MEGA-STONE-BP-SHOP-MGBA-GATE"
STAGE_TASK = "USER-MODERNIZATION-MEGA-STONE-BP-SHOP"
STAGE = 68
ROM = Path("build/stages/68_modernization_mega_shop.gba")
METADATA = Path("build/stages/68_modernization_mega_shop.json")
SYMBOLS = Path("generated/runtime/modernization_mega_shop_symbols.json")
CHECKPOINT = Path("content/modernization/mega_shop_checkpoint.json")
RUNNER = Path("tools/mgba_modernization_mega_shop_smoke.c")
OUTPUT = Path("content/modernization/mega_shop_mgba_runtime_gate.json")

DIAGNOSTIC_HISTORY = {
    "failed_process_runs_before_pass": 5,
    "passing_process_runs": 1,
    "failed_evidence_files_written": 0,
    "last_failure_observation": {
        "load_game_data": 2,
        "ensure_save": 1,
        "balance_bp_from_sector31": 52,
        "mega_ring_visible_before_bag_pointer_setup": False,
    },
    "save_file_read_only_audit": {
        "size_with_mgba_rtc_footer": 131088,
        "standard_slots_complete": True,
        "sector_signatures_and_checksums_valid": True,
    },
    "root_cause": "FRESH_CORE_SAVE_BLOCK_POINTERS_NOT_INITIALIZED",
    "resolution": [
        "SetSaveBlocksPointers when fresh EWRAM owner pointers are invalid",
        "Save_LoadGameData",
        "SetBagPocketsPointers before bag queries",
    ],
    "rom_defect": False,
}


class ModernizationMegaShopMgbaError(RuntimeError):
    """Stage68 identity、実ROM結果、または公開証跡が不正。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationMegaShopMgbaError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _path(relative: Path, label: str) -> Path:
    path = ROOT / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(ROOT.resolve())
    except (OSError, ValueError) as error:
        _fail(f"{label}がworkspace内の通常ファイルではありません: {error}")
    if path.is_symlink() or not resolved.is_file():
        _fail(f"{label}がworkspace内の通常ファイルではありません")
    return resolved


def _identity(relative: Path, label: str) -> dict[str, Any]:
    raw = _path(relative, label).read_bytes()
    return {"path": relative.as_posix(), "size": len(raw), "sha256": _sha(raw)}


def _json(relative: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(_path(relative, label).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{label}を読めません: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} rootはobject必須です")
    return value


def _validate_stage_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    metadata = _json(METADATA, "Stage68 metadata")
    symbols = _json(SYMBOLS, "Stage68 symbols")
    checkpoint = _json(CHECKPOINT, "Stage68 checkpoint")
    rom_identity = _identity(ROM, "Stage68 ROM")
    if (
        metadata.get("schema_version") != 1
        or metadata.get("task") != STAGE_TASK
        or metadata.get("stage") != STAGE
        or metadata.get("status") != "PASS_HOST_STATIC_EXACT_ROM_PENDING"
        or metadata.get("validation", {}).get("exact_rom_runtime_smoke") != "PENDING"
        or metadata.get("output") != rom_identity
    ):
        _fail("Stage68 metadata/output/PENDING境界が一致しません")
    catalog = metadata.get("catalog", {})
    if (
        catalog.get("entry_count") != 45
        or catalog.get("item_ids") != list(range(999, 1044))
        or catalog.get("prices_bp") != [16]
        or catalog.get("claim_flags") != list(range(0x14A0, 0x14CD))
        or catalog.get("key_stone_item_id") != 580
    ):
        _fail("Stage68 45石/16BP/Mega Ring/claim flag契約が不一致です")
    map_contract = metadata.get("map", {})
    if (
        map_contract.get("group_id") != 96
        or map_contract.get("map_id") != 5
        or map_contract.get("object_count_after") != 14
        or map_contract.get("shop_object", {}).get("local_id") != 14
        or map_contract.get("shop_object", {}).get("x") != 24
        or map_contract.get("shop_object", {}).get("y") != 19
    ):
        _fail("Stage68 physical shop map契約が不一致です")
    if (
        symbols.get("schema_version") != 1
        or symbols.get("task") != STAGE_TASK
        or symbols.get("entrypoints") != metadata.get("entrypoints")
        or symbols.get("map") != metadata.get("map")
        or symbols.get("scripts") != metadata.get("scripts")
    ):
        _fail("Stage68 symbolsとmetadataが一致しません")
    if (
        checkpoint.get("schema_version") != 1
        or checkpoint.get("task") != STAGE_TASK
        or checkpoint.get("stage") != STAGE
        or checkpoint.get("status") != "PASS_HOST_STATIC_EXACT_ROM_PENDING"
        or checkpoint.get("rom") != rom_identity
        or checkpoint.get("validation", {}).get("exact_rom_runtime_smoke")
        != "PENDING"
    ):
        _fail("Stage68 checkpoint/PENDING境界が一致しません")
    return metadata, symbols, checkpoint


EXPECTED_CHECKS = {
    "physical_npc_script_graph_to_entrypoint",
    "item_consumer_boundaries_999_1023_1024_1043_1044",
    "name_hold_effect_and_is_mega_stone_consumers",
    "probe_and_save_init",
    "mega_ring_580_gate",
    "insufficient_bp_no_mutation",
    "bag_full_no_mutation",
    "index_0_item_999_price_16",
    "index_22_item_1021_price_16",
    "index_44_item_1043_price_16",
    "claim_flags_14a0_14b6_14cc",
    "fresh_core_normal_save_reload",
    "fresh_core_once_rejected",
}


def _validate_runner_result(result: Mapping[str, Any]) -> None:
    checks = result.get("checks")
    if (
        result.get("schema_version") != 1
        or result.get("stage") != STAGE
        or result.get("status") != "PASS"
        or result.get("warnings_errors") != 0
        or not isinstance(checks, dict)
        or set(checks) != EXPECTED_CHECKS
        or not all(value is True for value in checks.values())
        or result.get("representative_indices") != [0, 22, 44]
        or result.get("representative_item_ids") != [999, 1021, 1043]
        or result.get("representative_claim_flags") != [5280, 5302, 5324]
        or result.get("accepted_item_boundary_ids") != [999, 1023, 1024, 1043]
        or result.get("first_rejected_item_id") != 1044
        or result.get("hold_effect") != 73
        or result.get("price_bp") != 16
        or result.get("initial_bp") != 100
        or result.get("final_bp") != 52
        or result.get("core_instances") != 2
        or result.get("process_runs") != 1
        or result.get("state_fixture") != "PRODUCTION_ROM_FUNCTIONS_ONLY"
        or result.get("retained_artifacts") != []
        or not isinstance(result.get("bag_full_capacity"), int)
        or result["bag_full_capacity"] <= 0
    ):
        _fail("mGBA runner result契約が不一致です")


def _run_command(command: list[str], label: str, *, timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        _fail(f"{label}を実行できません: {error}")
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label}失敗({completed.returncode}): {detail}")
    return completed


def run_gate() -> dict[str, Any]:
    metadata, symbols, _checkpoint = _validate_stage_inputs()
    before_rom = _identity(ROM, "Stage68 ROM")
    compiler = os.environ.get("CC", "cc")
    with tempfile.TemporaryDirectory(prefix="vega-stage68-mega-shop-mgba-") as raw_temp:
        temporary = Path(raw_temp)
        executable = temporary / "mgba-modernization-mega-shop-smoke"
        save = temporary / "stage68-mega-shop.sav"
        compile_result = _run_command(
            [
                compiler,
                "-std=c11",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(RUNNER),
                "-o",
                str(executable),
                "-lmgba",
            ],
            "Stage68 mGBA runner compile",
            timeout=60,
        )
        entry = symbols["entrypoints"]
        map_contract = symbols["map"]
        script = symbols["scripts"]
        command = [
            str(executable),
            str(ROM),
            str(save),
            hex(entry["MegaShop_Probe"]),
            hex(entry["MegaShop_EnsureSave"]),
            hex(entry["MegaShop_GetBalance"]),
            hex(entry["MegaShop_IsUnlocked"]),
            hex(entry["MegaShop_IsClaimed"]),
            hex(entry["MegaShop_PurchaseByIndex"]),
            hex(entry["MegaShop_Open"]),
            hex(script["npc_address"]),
            hex(map_contract["events_after_address"]),
            hex(map_contract["old_scripts_pointer"]),
            hex(symbols["item_tables"]["item_data"]["new_address"]),
        ]
        completed = _run_command(command, "Stage68 exact-ROM mGBA gate", timeout=150)
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            _fail(f"mGBA stdoutがJSONではありません: {error}: {completed.stdout!r}")
        if not isinstance(result, dict):
            _fail("mGBA stdout rootはobject必須です")
        _validate_runner_result(result)
        compiler_identity = {
            "command": compiler,
            "flags": ["-std=c11", "-Wall", "-Wextra", "-Werror", "-lmgba"],
            "stdout": compile_result.stdout.strip(),
            "stderr": compile_result.stderr.strip(),
        }
    after_rom = _identity(ROM, "Stage68 ROM")
    if after_rom != before_rom:
        _fail("mGBA gateがStage68 ROMを変更しました")
    return {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "classification": "EXACT_ROM_STATEFUL_NORMAL_FUNCTION_FRESH_CORE",
        "inputs": {
            "rom": before_rom,
            "metadata": _identity(METADATA, "Stage68 metadata"),
            "symbols": _identity(SYMBOLS, "Stage68 symbols"),
            "checkpoint": _identity(CHECKPOINT, "Stage68 checkpoint"),
        },
        "runtime": {
            "runner_source": _identity(RUNNER, "mGBA runner source"),
            "compiler": compiler_identity,
            "process_runs": 1,
            "core_instances": 2,
            "fresh_core": True,
            "host_test_overlay": False,
            "retained_artifacts": [],
        },
        "runtime_result": result,
        "diagnostic_history": DIAGNOSTIC_HISTORY,
        "claims": {
            "exact_stage68_rom": True,
            "physical_npc_script_graph_to_entrypoint": True,
            "mega_ring_580_gate": True,
            "three_representative_16_bp_purchases": True,
            "representative_bag_items_and_claim_flags": True,
            "item_consumer_boundaries_and_mega_semantics": True,
            "insufficient_and_bag_full_no_mutation": True,
            "normal_save_fresh_core_once_rejection": True,
            "warnings_errors_zero": True,
            "all_45_runtime_purchases": False,
            "physical_menu_input_e2e": False,
        },
        "stage68_metadata_validation_state_at_run":
            metadata["validation"]["exact_rom_runtime_smoke"],
        "artifacts_written": [OUTPUT.as_posix()],
    }


def check_gate() -> dict[str, Any]:
    evidence = _json(OUTPUT, "Stage68 mGBA evidence")
    _validate_stage_inputs()
    if (
        evidence.get("schema_version") != 1
        or evidence.get("task") != TASK
        or evidence.get("stage") != STAGE
        or evidence.get("status") != "PASS"
        or evidence.get("classification")
        != "EXACT_ROM_STATEFUL_NORMAL_FUNCTION_FRESH_CORE"
        or evidence.get("inputs", {}).get("rom") != _identity(ROM, "Stage68 ROM")
        or evidence.get("inputs", {}).get("metadata")
        != _identity(METADATA, "Stage68 metadata")
        or evidence.get("inputs", {}).get("symbols")
        != _identity(SYMBOLS, "Stage68 symbols")
        or evidence.get("inputs", {}).get("checkpoint")
        != _identity(CHECKPOINT, "Stage68 checkpoint")
        or evidence.get("runtime", {}).get("runner_source")
        != _identity(RUNNER, "mGBA runner source")
        or evidence.get("runtime", {}).get("process_runs") != 1
        or evidence.get("runtime", {}).get("core_instances") != 2
        or evidence.get("runtime", {}).get("fresh_core") is not True
        or evidence.get("runtime", {}).get("host_test_overlay") is not False
        or evidence.get("stage68_metadata_validation_state_at_run") != "PENDING"
        or evidence.get("diagnostic_history") != DIAGNOSTIC_HISTORY
    ):
        _fail("Stage68 mGBA evidenceのidentity/境界が不一致です")
    claims = evidence.get("claims", {})
    if (
        not all(
            claims.get(key) is True
            for key in (
                "exact_stage68_rom",
                "physical_npc_script_graph_to_entrypoint",
                "mega_ring_580_gate",
                "three_representative_16_bp_purchases",
                "representative_bag_items_and_claim_flags",
                "item_consumer_boundaries_and_mega_semantics",
                "insufficient_and_bag_full_no_mutation",
                "normal_save_fresh_core_once_rejection",
                "warnings_errors_zero",
            )
        )
        or claims.get("all_45_runtime_purchases") is not False
        or claims.get("physical_menu_input_e2e") is not False
    ):
        _fail("Stage68 mGBA evidenceのclaim境界が不一致です")
    result = evidence.get("runtime_result")
    if not isinstance(result, dict):
        _fail("Stage68 mGBA evidenceにruntime_resultがありません")
    _validate_runner_result(result)
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "check"))
    arguments = parser.parse_args(argv)
    try:
        if arguments.action == "run":
            evidence = run_gate()
            output = ROOT / OUTPUT
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(_stable(evidence))
            print("MODERNIZATION_MEGA_SHOP_MGBA_RUN=PASS")
        else:
            check_gate()
            print("MODERNIZATION_MEGA_SHOP_MGBA_CHECK=PASS")
    except ModernizationMegaShopMgbaError as error:
        print(f"MODERNIZATION_MEGA_SHOP_MGBA_{arguments.action.upper()}=FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
