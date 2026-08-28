#!/usr/bin/env python3
"""Stage58 exact ROMを継承7 domainと新規QOL/Codex domainでmGBA検証する。"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_stage57_mgba_validation import (  # noqa: E402
    _route505_domain,
    _species_domain,
    _story_domain,
    _without_timing,
    _world_domain,
)
from tools.stage58_debug_suite import full_audit  # noqa: E402


TASK = "USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG"
STAGE = 58
DEFAULT_ROM = Path("build/stages/58_qol_world_convenience_debug.gba")
DEFAULT_METADATA = Path("build/stages/58_qol_world_convenience_debug.json")
DEFAULT_CASES = Path("generated/runtime/stage58_qol_world_convenience_debug_cases.json")
DEFAULT_OUTPUT = Path("build/stages/58_mgba_qol_world_convenience_debug.json")
COLLECTION_SYMBOLS = Path("generated/runtime/collection_supply_v1_symbols.json")
STAGE57_SYMBOLS = Path("generated/runtime/stage57_comprehensive_debug_repair_symbols.json")
COLLECTION_CASES = Path("generated/runtime/collection_supply_v1_mgba_cases.json")
QOL_METADATA = Path("build/stages/36_qol_production.json")
INHERITED_DOMAINS = (
    "static", "story", "menu", "route505", "species", "collection", "world",
)
NEW_DOMAINS = ("qol_items", "economy", "convenience")
ALL_DOMAINS = (*INHERITED_DOMAINS, *NEW_DOMAINS)
VALIDATION_CONTRACT_ROOT_FILES = (
    Path("config/ram_layout.csv"),
    Path("config/save_layout.csv"),
    COLLECTION_SYMBOLS,
    STAGE57_SYMBOLS,
    COLLECTION_CASES,
    QOL_METADATA,
    Path("scripts/run_stage58_mgba_validation.py"),
    Path("scripts/build_stage58_qol_world_convenience_debug.py"),
    Path("tools/mgba_stage57_menu_smoke.c"),
    Path("tools/mgba_stage57_route505_smoke.c"),
    Path("tools/mgba_stage57_collection_smoke.c"),
    Path("tools/mgba_species_runtime_smoke.c"),
    Path("tools/mgba_world_runtime_input_e2e.c"),
    Path("tools/mgba_stage58_qol_item_effects_smoke.c"),
    Path("tools/mgba_stage58_economy_smoke.c"),
    Path("tools/mgba_stage58_convenience_smoke.c"),
)


class Stage58MgbaError(RuntimeError):
    """Stage58 exact identity、runner、独立processまたはcoverage契約違反。"""


def _fail(message: str) -> NoReturn:
    raise Stage58MgbaError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _validation_contract_files() -> tuple[Path, ...]:
    """Resolve local Python imports and quoted C includes from QA roots."""
    pending = list(VALIDATION_CONTRACT_ROOT_FILES)
    resolved: set[Path] = set()
    include_pattern = re.compile(r'^\s*#\s*include\s+"([^"]+)"', re.MULTILINE)
    while pending:
        path = pending.pop()
        if path in resolved:
            continue
        absolute = ROOT / path
        if not absolute.is_file():
            _fail(f"validation contract source不在: {path}")
        resolved.add(path)
        if path.suffix == ".c" or path.suffix == ".h":
            text_source = absolute.read_text(encoding="utf-8")
            for include in include_pattern.findall(text_source):
                candidate = (path.parent / include)
                if (ROOT / candidate).is_file():
                    pending.append(candidate)
            continue
        if path.suffix != ".py":
            continue
        tree = ast.parse(absolute.read_text(encoding="utf-8"), filename=str(path))
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 \
                    and node.module is not None:
                modules.add(node.module)
        for module in modules:
            candidate = Path(*module.split(".")).with_suffix(".py")
            if (ROOT / candidate).is_file():
                pending.append(candidate)
    return tuple(sorted(resolved, key=lambda item: item.as_posix()))


def validation_contract(cases_path: Path = DEFAULT_CASES) -> dict[str, Any]:
    """Bind evidence to the exact cases and every executable QA source."""
    sources = {
        path.as_posix(): _sha((ROOT / path).read_bytes())
        for path in _validation_contract_files()
    }
    cases_absolute = cases_path if cases_path.is_absolute() else ROOT / cases_path
    cases_digest = _sha(cases_absolute.read_bytes())
    joined = (
        "".join(
            f"{path}\0{digest}\n" for path, digest in sorted(sources.items())
        ) + f"cases\0{cases_digest}\n"
    ).encode("utf-8")
    return {
        "schema_version": 1,
        "cases_path": str(cases_path.relative_to(ROOT)
                          if cases_path.is_absolute() else cases_path),
        "cases_sha256": cases_digest,
        "sources_sha256": sources,
        "contract_sha256": _sha(joined),
    }


def _read_identity(
    rom_path: Path, metadata_path: Path, cases_path: Path,
) -> tuple[bytes, dict[str, Any], dict[str, Any], str]:
    raw = rom_path.read_bytes()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    digest = _sha(raw)
    if len(raw) != 32 * 1024 * 1024:
        _fail(f"Stage58 ROM size不一致: {len(raw)}")
    if (metadata.get("task"), metadata.get("stage"),
            metadata.get("output", {}).get("sha256")) != (TASK, STAGE, digest):
        _fail("Stage58 ROM/metadata identity不一致")
    if (cases.get("task"), cases.get("stage"), cases.get("rom_sha256")) \
            != (TASK, STAGE, digest):
        _fail("Stage58 ROM/cases identity不一致")
    return raw, metadata, cases, digest


def _compile(source: Path, executable: Path,
             definitions: Mapping[str, str] | None = None) -> None:
    compiler = shutil.which("cc")
    if compiler is None or not source.is_file():
        _fail(f"mGBA compile前提不足: {source}")
    define_args = [
        f'-D{key}="{value}"' for key, value in sorted((definitions or {}).items())
    ]
    completed = subprocess.run(
        [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
         "-pedantic", *define_args, str(source), "-o", str(executable), "-lmgba"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=180, check=False,
    )
    if completed.returncode or completed.stdout or completed.stderr:
        _fail(
            f"mGBA runner compile失敗 {source.name}: "
            + (completed.stderr or completed.stdout or str(completed.returncode))[-6000:]
        )


def _run_json(command: Sequence[str], *, timeout: int,
              label: str) -> dict[str, Any]:
    completed = subprocess.run(
        list(command), cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=timeout, check=False,
    )
    if completed.returncode or completed.stderr:
        _fail(
            f"{label}失敗 exit={completed.returncode}: "
            + (completed.stderr or completed.stdout or str(completed.returncode))[-8000:]
        )
    try:
        document = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        _fail(f"{label} JSON不正: {error}")
    if not isinstance(document, dict) or document.get("status") != "PASS":
        _fail(f"{label} PASS契約不一致: {document}")
    return _without_timing(document)


def _repeat(runs: int, function: Callable[[int], dict[str, Any]],
            label: str) -> dict[str, Any]:
    documents = [function(index) for index in range(runs)]
    if any(document != documents[0] for document in documents[1:]):
        _fail(f"{label}の独立{runs} process結果が非決定的です")
    return {
        "status": "PASS", "process_runs": runs,
        "identical_results": True, "result": documents[0],
    }


def _validate_rom(document: Mapping[str, Any], digest: str, label: str) -> None:
    if document.get("rom_sha256") not in (None, digest):
        _fail(f"{label} ROM SHA-256不一致")


def _static_domain(raw: bytes, metadata: Mapping[str, Any],
                   cases: Mapping[str, Any], digest: str) -> dict[str, Any]:
    first = _without_timing(full_audit(raw, metadata, cases))
    second = _without_timing(full_audit(raw, metadata, cases))
    if first != second or first.get("rom_sha256") != digest:
        _fail("Stage58 full static audit反復不一致")
    return {
        "status": "PASS", "process_runs": 2,
        "identical_results": True, "result": first,
    }


def _menu_domain(rom: Path, digest: str, directory: Path,
                 runs: int) -> dict[str, Any]:
    executable = directory / "menu-runner"
    _compile(
        ROOT / "tools/mgba_stage57_menu_smoke.c", executable,
        {"S57_EXPECTED_ROM_SHA256": digest},
    )

    def run(index: int) -> dict[str, Any]:
        document = _run_json(
            [str(executable), str(rom), str(directory / f"menu-{index + 1}")],
            timeout=1200, label=f"menu process {index + 1}",
        )
        _validate_rom(document, digest, "menu")
        return document

    return _repeat(runs, run, "menu")


def _collection_domain(rom: Path, digest: str, directory: Path,
                       runs: int, mode: str) -> dict[str, Any]:
    executable = directory / "collection-runner"
    _compile(
        ROOT / "tools/mgba_stage57_collection_smoke.c", executable,
        {"S57_COLLECTION_EXPECTED_ROM_SHA256": digest},
    )

    def run(index: int) -> dict[str, Any]:
        document = _run_json([
            str(executable), str(rom), str(ROOT / COLLECTION_SYMBOLS),
            str(ROOT / STAGE57_SYMBOLS), str(ROOT / COLLECTION_CASES), mode,
            str(directory / f"collection-{index + 1}.sav"),
        ], timeout=1800, label=f"Collection {mode} process {index + 1}")
        _validate_rom(document, digest, "Collection")
        if document.get("warnings") != 0 \
                or not all(document.get("tests", {}).values()):
            _fail("Collection test/warning契約不一致")
        return document

    result = _repeat(runs, run, f"Collection {mode}")
    result["mode"] = mode
    return result


def _qol_items_domain(rom: Path, digest: str, directory: Path,
                      chains: int) -> dict[str, Any]:
    executable = directory / "qol-items-runner"
    _compile(ROOT / "tools/mgba_stage58_qol_item_effects_smoke.c", executable)
    metadata = json.loads((ROOT / QOL_METADATA).read_text(encoding="utf-8"))
    entry = metadata["runtime"]["entrypoints"]
    required = ("VegaQolProduction_Probe", "VegaQolProduction_Dispatch")
    if any(name not in entry for name in required):
        _fail("QOL item effect entrypoint inventory不一致")

    def run(index: int) -> dict[str, Any]:
        save = directory / f"qol-items-{index + 1}.sav"
        arguments = [
            str(executable), str(rom), str(save), digest,
            "phase1", hex(int(entry[required[0]])), hex(int(entry[required[1]])),
        ]
        phase1 = _run_json(
            arguments, timeout=3600,
            label=f"QOL item effects phase1 chain {index + 1}",
        )
        arguments[4] = "reload"
        reload = _run_json(
            arguments, timeout=1200,
            label=f"QOL item effects reload chain {index + 1}",
        )
        for phase, document in (("phase1", phase1), ("reload", reload)):
            _validate_rom(document, digest, f"QOL items {phase}")
            if document.get("phase") != phase \
                    or document.get("warnings_errors") != 0 \
                    or not document.get("tests") \
                    or not all(document["tests"].values()) \
                    or document.get("coverage", {}).get("effect_items") != 36:
                _fail(f"QOL item effects {phase} coverage契約不一致")
        phase_counts = phase1.get("counts", {})
        reload_counts = reload.get("counts", {})
        if any(int(phase_counts.get(key, -1)) != 36 for key in (
                "cancelled", "successful", "effectless")) \
                or any(int(reload_counts.get(key, -1)) != 36 for key in (
                    "reload_records", "reload_bags")):
            _fail("QOL item effects 36品count契約不一致")
        return {"phase1": phase1, "reload": reload}

    result = _repeat(chains, run, "QOL item effects two-phase")
    result["process_runs"] = chains * 2
    result["chains"] = chains
    result["effect_item_count"] = 36
    return result


def _convenience_domain(rom: Path, digest: str, cases: Path,
                        directory: Path, chains: int) -> dict[str, Any]:
    executable = directory / "convenience-runner"
    _compile(ROOT / "tools/mgba_stage58_convenience_smoke.c", executable)
    phase1_tests = {
        "hub_exact_graph", "thin_events_exact_graph", "wild_exact_slots",
        "codex_result_win_loss_draw_table_exact",
        "kanto_wild_runtime_land_rate_species_level_field_return",
        "kanto_wild_runtime_water_rate_species_level_field_return",
        "kanto_wild_runtime_rock_rate_species_level_field_return",
        "kanto_wild_runtime_fishing_rate_species_level_field_return",
        "kanto_wild_fishing_old_good_super_rng_boundaries",
        "thin_events_initial_pickup", "thin_events_repeat_no_duplicate",
        "thin_events_blockdata_walkable_non_event_adjacent",
        "thin_events_bag_full_retry_all_6",
        "thin_events_native_flag_neighbor_bits_stable",
        "thin_events_quest_log_normal_save_recorded",
        "thin_events_quest_log_reload_next_input_flag_stable",
        "thin_events_quantities_preserved_across_normal_saves",
        "pc_object_storage_callback_field_return", "pc_normal_ui_deposit",
        "healer_object_hp_pp_status", "healer_zero_party_field_return",
        "healer_egg_hp_pp_status", "healer_fainted_hp_pp_status",
        "healer_normal_hp_pp_status",
        "mart_object_open_navigate_cancel_unchanged", "mart_money_purchase",
        "mart_bag_full_no_charge", "mart_normal_ui_sell_ball",
        "mart_normal_ui_sell_item",
        "codex_npc_normal_a_battle_start_finish_field_return",
        "codex_reward_closed_open_closed",
        "codex_transaction_request_owned",
        "codex_natural_readkeys_all_11_requests",
        "codex_forfeit_result_kind_4",
        "codex_disconnect_cpu_controller_uninstalled",
        "codex_disconnect_cpu_win_result_kind_1",
        "codex_cpu_win_thin_quantities_preserved",
        "codex_forfeit_thin_quantities_preserved",
        "codex_cpu_win_save_layout_restored",
        "codex_forfeit_save_layout_restored",
        "codex_disconnect_cpu_normal_input_field_reward_return",
        "codex_external_capabilities_7fff_preserved",
        "codex_request_window_not_cleared",
        "thin_codex_owner_hash_unchanged",
        "hub_codex_boundaries_valid", "save_after_normal_ui_mutation",
    }
    reload_tests = {
        "hub_exact_graph", "thin_events_exact_graph", "wild_exact_slots",
        "codex_result_win_loss_draw_table_exact",
        "pc_normal_ui_deposit_persisted", "mart_money_purchase_persisted",
        "mart_normal_ui_sales_persisted",
        "codex_post_battle_closed_reset_boundary",
        "codex_external_mailbox_volatile_reset",
        "thin_events_pickups_persisted", "reload_box",
        "reload_party_healed", "reload_field_codex_boundaries",
    }

    def run(index: int) -> dict[str, Any]:
        save = directory / f"convenience-{index + 1}.sav"
        phase1 = _run_json(
            [str(executable), str(rom), str(cases), str(save), "phase1"],
            timeout=1800, label=f"convenience phase1 chain {index + 1}",
        )
        reload = _run_json(
            [str(executable), str(rom), str(cases), str(save), "reload"],
            timeout=900, label=f"convenience reload chain {index + 1}",
        )
        _validate_rom(phase1, digest, "convenience phase1")
        _validate_rom(reload, digest, "convenience reload")
        for phase, document, required in (
            ("phase1", phase1, phase1_tests),
            ("reload", reload, reload_tests),
        ):
            coverage = document.get("coverage", {})
            if (document.get("schema_version"), document.get("task"),
                    document.get("stage"), document.get("phase"),
                    document.get("warnings"),
                    document.get("warnings_errors")) \
                    != (1, TASK, STAGE, phase, 0, 0) \
                    or set(document.get("tests", {})) != required \
                    or not all(document["tests"].values()) \
                    or coverage.get("hub_objects") != 4 \
                    or coverage.get("thin_events") != 6 \
                    or coverage.get("thin_retry") != 6 \
                    or coverage.get("wild_modes") != 4 \
                    or coverage.get("codex_result_routes_exact") != 3 \
                    or (phase == "phase1" and (
                        coverage.get("codex_battle_paths") != 2
                        or coverage.get("wild_runtime_modes") != 4
                        or coverage.get("fishing_tiers") != 3
                        or coverage.get("fishing_rng_samples") != 300
                    )) \
                    or int(coverage.get("wild_slots", 0)) <= 0:
                _fail(f"convenience {phase} coverage契約不一致")
        cpu_battle = phase1.get("evidence", {}).get("cpu_battle", {})
        if (
            int(cpu_battle.get("outcome", -1)) != 1
            or int(cpu_battle.get("result_kind", -1)) != 1
        ):
            _fail("convenience CPU勝利/result-kind証跡不一致")
        save_layout = phase1.get("evidence", {}).get(
            "codex_save_layout", {}
        )
        for owner in ("seen", "personality", "owned"):
            try:
                before = int(str(save_layout[f"{owner}_before"]), 16)
                after_cpu = int(str(save_layout[f"{owner}_after_cpu"]), 16)
                after_forfeit = int(
                    str(save_layout[f"{owner}_after_forfeit"]), 16
                )
            except (KeyError, TypeError, ValueError):
                _fail(f"convenience Codex {owner} hash証跡不正")
            if before == 0 or (before, after_cpu, after_forfeit) \
                    != (before, before, before):
                _fail(f"convenience Codex {owner} restore証跡不一致")
        return {"phase1": phase1, "reload": reload}

    result = _repeat(chains, run, "Codex convenience two-phase")
    result["process_runs"] = chains * 2
    result["chains"] = chains
    return result


def _economy_domain(rom: Path, digest: str, directory: Path,
                    chains: int) -> dict[str, Any]:
    executable = directory / "economy-runner"
    _compile(ROOT / "tools/mgba_stage58_economy_smoke.c", executable)
    metadata = json.loads((ROOT / QOL_METADATA).read_text(encoding="utf-8"))
    entry = metadata["runtime"]["entrypoints"]
    names = (
        "VegaQolProduction_Probe",
        "VegaQolProduction_Dispatch",
        "VegaQolProduction_FeatureUnlocked",
        "VegaQolProduction_PurchaseSupply",
        "VegaQolProduction_OpenSupplyShop",
        "VegaQolProduction_TestInjectPersistenceFault",
    )
    if any(name not in entry for name in names):
        _fail("Stage58 economy entrypoint inventory不一致")
    addresses = [hex(int(entry[name])) for name in names]
    phase1_tests = {
        "normal_menu_cancel_no_mutation", "bag_full_no_debit",
        "insufficient_no_mutation", "cross_store_fault_rollback",
        "limited_repeatable_reopen",
        "currency_owner_api_integration_boundary",
        "low_raid_xs_unlock_runtime",
        "collection_qol_owner_47_runtime",
        "honey_buy_sell_no_profit_runtime",
        "research_rate_71_runtime",
        "normal_trainer_victory_prize_honey_normal_save_phase1",
        "factory_prepare_real_battles_bp_patch_normal_save_phase1",
    }
    reload_tests = {
        "fresh_process_trainer_prize_honey_reload",
        "fresh_process_factory_reward_ability_patch_reload",
    }
    phase_boundaries = {
        "phase1": {
            "normal_trainer_victory_to_prize_honey_normal_save": True,
            "factory_prepare_to_real_battle_to_bp_reward": True,
            "factory_reward_to_patch_normal_save": True,
            "fresh_process_earned_purchases_reload": False,
            "factory_physical_npc_and_selection_ui": False,
            "factory_unmodified_battle_fixture": False,
            "low_raid_field_battle": False,
            "honey_sell_ui": False,
            "synthetic_currency_owner_api_is_actual_earn": False,
        },
        "reload": {
            "normal_trainer_victory_to_prize_honey_normal_save": False,
            "factory_prepare_to_real_battle_to_bp_reward": False,
            "factory_reward_to_patch_normal_save": False,
            "fresh_process_earned_purchases_reload": True,
            "factory_physical_npc_and_selection_ui": False,
            "factory_unmodified_battle_fixture": False,
            "low_raid_field_battle": False,
            "honey_sell_ui": False,
            "synthetic_currency_owner_api_is_actual_earn": False,
        },
    }
    phase_claims = {
        "phase1": "ACTUAL_TRAINER_AND_FACTORY_EARN_PURCHASE_NORMAL_SAVE",
        "reload": (
            "ACTUAL_TRAINER_AND_FACTORY_EARN_PURCHASE_NORMAL_SAVE_"
            "FRESH_PROCESS_RELOAD"
        ),
    }

    def run(index: int) -> dict[str, Any]:
        save = directory / f"economy-{index + 1}.sav"
        arguments = [
            str(executable), str(rom), str(save), digest,
            "phase1", *addresses,
        ]
        phase1 = _run_json(
            arguments, timeout=3600,
            label=f"economy phase1 chain {index + 1}",
        )
        arguments[4] = "reload"
        reload = _run_json(
            arguments, timeout=1200,
            label=f"economy reload chain {index + 1}",
        )
        for phase, document, required in (
            ("phase1", phase1, phase1_tests),
            ("reload", reload, reload_tests),
        ):
            _validate_rom(document, digest, f"economy {phase}")
            tests = document.get("tests", {})
            ability = document.get("ability_patch", {})
            if (document.get("schema_version"), document.get("task"),
                    document.get("stage"), document.get("phase"),
                    document.get("warnings_errors")) \
                    != (1, TASK, STAGE, phase, 0) \
                    or set(tests) != required or not all(tests.values()) \
                    or (ability.get("catalog_index"), ability.get("item_id"),
                        ability.get("price_bp"), ability.get("bag_capacity"),
                        ability.get("bag_capacity_observed_phase1")) \
                    != (35, 943, 64, 999, 999 if phase == "phase1" else 0):
                _fail(f"economy {phase} coverage契約不一致")
            if document.get("e2e_boundaries") != phase_boundaries[phase] \
                    or document.get("completion_claim") != phase_claims[phase]:
                _fail(f"economy {phase}証明境界不一致")
        trainer = phase1.get("trainer_evidence", {})
        factory = phase1.get("factory_evidence", {})
        counts = phase1.get("evidence_counts", {})
        if (trainer.get("observed_in_phase1"), trainer.get("trainer_id"),
                trainer.get("script"), trainer.get("money_before"),
                trainer.get("money_after"), trainer.get("prize_delta"),
                trainer.get("money_after_honey"), trainer.get("outcome"),
                trainer.get("enemy_fainted"), trainer.get("runtime_cleaned")) \
                != (True, 89, "0x09376713", 3000, 3128, 128, 2228,
                    1, True, True):
            _fail("economy trainer実賞金/Honey証跡不一致")
        if (factory.get("observed_in_phase1"), factory.get("outcomes"),
                factory.get("payload_starts"), factory.get("bp_before"),
                factory.get("bp_after_reward"), factory.get("bp_delta"),
                factory.get("bp_after_purchase"),
                factory.get("purchase_raw_result"),
                factory.get("purchase_special_result")) \
                != (True, [1, 1, 1], 3, 55, 64, 9, 0, 0, 0):
            _fail("economy Factory実戦/BP/Ability Patch証跡不一致")
        save_hashes: list[int] = []
        for owner, evidence in (("trainer", trainer), ("factory", factory)):
            encoded_hash = evidence.get("normal_save_hash")
            if not isinstance(encoded_hash, str) \
                    or re.fullmatch(r"0x[0-9a-f]{16}", encoded_hash) is None:
                _fail(f"economy {owner} normal save hash形式不正")
            try:
                save_hash = int(encoded_hash, 16)
            except (KeyError, TypeError, ValueError):
                _fail(f"economy {owner} normal save hash証跡不正")
            if save_hash == 0:
                _fail(f"economy {owner} normal save hashがゼロです")
            save_hashes.append(save_hash)
        if len(set(save_hashes)) != 2:
            _fail("economy trainer/Factory normal save hashが未遷移です")
        routes = phase1.get("test_routes", {})
        if routes.get("normal_trainer_fixture_scope") \
                != "AUTHORED_TRAINER89_SCRIPT_COPY_AND_ENEMY_HP1_NO_OUTCOME_OR_PRIZE_WRITE" \
                or routes.get("factory_fixture_scope") \
                != "HOST_SELECTED_ORDER_HP_MAXHP_SPEED_MOVE_PP_ACTION_AND_MOVE_CURSORS_NO_OUTCOME_OR_REWARD_WRITE":
            _fail("economy deterministic fixture scope証跡不一致")
        if (counts.get("phase1_transaction_boundaries_contract"),
                counts.get("transaction_boundaries_observed_this_phase"),
                counts.get("low_pre_xs_hits"),
                counts.get("collection_owner_rows"),
                counts.get("research_reprice_rows")) != (5, 5, 0, 47, 71) \
                or int(counts.get("low_post_xs_hits", 0)) <= 0:
            _fail("economy取引/供給表coverage証跡不一致")
        reload_evidence = reload.get("reload_evidence", {})
        reload_counts = reload.get("evidence_counts", {})
        if (reload_evidence.get("observed_in_fresh_process"),
                reload_evidence.get("money"), reload_evidence.get("honey"),
                reload_evidence.get("bp"),
                reload_evidence.get("ability_patch")) \
                != (True, 2228, 1, 0, 1) \
                or reload_counts.get(
                    "phase1_transaction_boundaries_contract") != 5 \
                or reload_counts.get(
                    "transaction_boundaries_observed_this_phase") != 0:
            _fail("economy別process再読込証跡不一致")
        if int(phase1["ability_patch"].get("bag_capacity", 0)) < 999:
            _fail("economy bag-full容量境界不足")
        return {"phase1": phase1, "reload": reload}

    result = _repeat(chains, run, "Stage58 economy two-phase")
    result["process_runs"] = chains * 2
    result["chains"] = chains
    result["transaction_cases"] = 5
    result["economy_test_cases"] = len(phase1_tests | reload_tests)
    return result


def run_validation(
    rom_path: Path,
    metadata_path: Path,
    cases_path: Path,
    selected: Sequence[str],
    *,
    runs: int,
    jobs: int,
    collection_mode: str,
) -> dict[str, Any]:
    raw, metadata, cases, digest = _read_identity(
        rom_path, metadata_path, cases_path,
    )
    requested = set(ALL_DOMAINS if "all" in selected else selected)
    if not requested or not requested <= set(ALL_DOMAINS):
        _fail(f"domain不正: {sorted(requested)}")
    if runs != 2:
        _fail("Stage58 acceptanceの独立process数は2固定です")
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stage58-mgba-", dir=local) as raw_dir:
        directory = Path(raw_dir)
        functions: dict[str, Callable[[], dict[str, Any]]] = {
            "static": lambda: _static_domain(raw, metadata, cases, digest),
            "story": lambda: _story_domain(raw, digest),
            "menu": lambda: _menu_domain(rom_path, digest, directory, runs),
            "route505": lambda: _route505_domain(
                rom_path, digest, directory, runs),
            "species": lambda: _species_domain(raw, digest, runs),
            "collection": lambda: _collection_domain(
                rom_path, digest, directory, runs, collection_mode),
            "world": lambda: _world_domain(raw, digest),
            "qol_items": lambda: _qol_items_domain(
                rom_path, digest, directory, runs),
            "economy": lambda: _economy_domain(
                rom_path, digest, directory, runs),
            "convenience": lambda: _convenience_domain(
                rom_path, digest, cases_path, directory, runs),
        }
        results: dict[str, Any] = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(max(1, jobs), len(requested)),
        ) as executor:
            pending = {
                executor.submit(functions[name]): name for name in sorted(requested)
            }
            for future in concurrent.futures.as_completed(pending):
                name = pending[future]
                results[name] = future.result()
    warnings = sum(
        int(result.get("result", result).get("warnings", 0))
        + int(result.get("result", result).get("warnings_errors", 0))
        for result in results.values()
    )
    if warnings:
        _fail(f"mGBA warning/error残存: {warnings}")
    dynamic = sum(
        int(result.get("process_runs", 0))
        for name, result in results.items() if name not in {"static", "story"}
    )
    return {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "tool": "run_stage58_mgba_validation", "status": "PASS",
        "profile": "all" if requested == set(ALL_DOMAINS) else "custom",
        "rom": str(rom_path), "rom_sha256": digest,
        "collection_mode": collection_mode,
        "selected_domains": sorted(results), "domain_count": len(results),
        "inherited_domain_count": len(set(results) & set(INHERITED_DOMAINS)),
        "full_coverage": requested == set(ALL_DOMAINS),
        "dynamic_process_runs": dynamic, "warnings": 0,
        "validation_contract": validation_contract(cases_path),
        "domains": {name: results[name] for name in sorted(results)},
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument(
        "--domain", action="append", choices=("all", *ALL_DOMAINS), default=[],
    )
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument(
        "--collection-mode", choices=("quick", "full"), default="full",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    try:
        document = run_validation(
            args.rom, args.metadata, args.cases, args.domain or ["all"],
            runs=args.runs, jobs=args.jobs,
            collection_mode=args.collection_mode,
        )
        output = args.output
        if output is None and document["profile"] == "all" and not args.no_write:
            output = DEFAULT_OUTPUT
        rendered = _stable(document)
        if output is not None and not args.no_write:
            output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=output.parent, delete=False, mode="w", encoding="utf-8",
            ) as stream:
                stream.write(rendered)
                temporary = Path(stream.name)
            os.replace(temporary, output)
        print(rendered, end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, Stage58MgbaError) as error:
        print(f"Stage58 mGBA validation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
