#!/usr/bin/env python3
"""全収集・道具供給・フォーム・Raid設計をChatGPT Proへ渡すZIPを生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from textwrap import dedent
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
PACKET_NAME = "Pokemon-Vega_CHATGPT-PRO_COLLECTION-SUPPLY-V1_INPUT_20260825"
OUTPUT_ZIP_NAME = "Pokemon-Vega_COLLECTION-SUPPLY-V1_IMPLEMENTATION-READY.zip"
FIXED_ZIP_TIME = (2026, 8, 25, 0, 0, 0)
VALIDATOR = Path("templates/chatgpt_pro_design_packets/tools/validate_submission.py")


class PacketError(RuntimeError):
    pass


def _default_windows_downloads() -> Path:
    return Path("/mnt/c/Users") / Path.home().name / "Downloads"


def _stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise PacketError(f"必須CSVがありません: {path}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path) -> Any:
    if not path.is_file():
        raise PacketError(f"必須JSONがありません: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(
    path: Path,
    header: Sequence[str],
    rows: Iterable[Mapping[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(header), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in header})


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_stable_json(value))


def _copy(root: Path, packet: Path, source: Path, target: Path) -> None:
    source_path = root / source
    if not source_path.is_file():
        raise PacketError(f"必須入力がありません: {source}")
    target_path = packet / target
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)


def _form_category(canonical_id: int, form_key: str, target_status: str) -> str:
    if 1201 <= canonical_id <= 1220:
        return "REGIONAL_ALOLA"
    if 1393 <= canonical_id <= 1414:
        return "REGIONAL_GALAR"
    if 1415 <= canonical_id <= 1431:
        return "REGIONAL_HISUI"
    if 1590 <= canonical_id <= 1593:
        return "REGIONAL_PALDEA"
    if "_GIGA" in form_key:
        return "GIGANTAMAX_BATTLE_FORM"
    if "_MEGA" in form_key:
        return "MEGA_BATTLE_FORM"
    if "TERASTAL" in form_key or "STELLAR" in form_key:
        return "TERASTAL_BATTLE_FORM"
    if target_status == "BATTLE_ONLY_EXCLUDED":
        return "OTHER_BATTLE_FORM"
    if target_status == "UNOBTAINABLE_EVENT_FORM_EXCLUDED":
        return "UNOBTAINABLE_EVENT_FORM"
    return "OTHER_PERSISTENT_OR_COSMETIC_FORM"


def _form_attention(target_status: str, category: str) -> str:
    if target_status == "REQUIRED_ENABLING_FORM":
        return "KEEP_STAGE26_ROUTE_AND_REGRESS"
    if category == "GIGANTAMAX_BATTLE_FORM":
        return "DESIGN_GMAX_FACTOR_NOT_DIRECT_FORM"
    if target_status == "OPTIONAL_FORM":
        return "DESIGN_ROUTE_OR_EXPLICIT_HELPER_EXCLUSION"
    if target_status == "UNOBTAINABLE_EVENT_FORM_EXCLUDED":
        return "KEEP_CANON_EXCLUDED"
    return "KEEP_BATTLE_ONLY_EXCLUDED"


def _build_form_catalog(root: Path, packet: Path) -> dict[str, int]:
    registry = _read_csv(root / "vendor/vega_acquisition/content/collectible_species_registry.csv")
    routes = {
        row["species_key"]: row
        for row in _read_csv(
            root / "vendor/vega_acquisition/content/species_acquisition_routes.csv"
        )
    }
    bases = {
        row["national_no"]: row
        for row in registry
        if row["national_no"] and not row["form_key"]
        and row["target_status"] == "REQUIRED_BASE"
    }
    forms = [row for row in registry if row["form_key"]]
    if len(registry) != 1621 or len(forms) != 388:
        raise PacketError(
            f"Species/form件数が変化しました: registry={len(registry)} forms={len(forms)}"
        )
    counts = Counter(row["target_status"] for row in forms)
    if counts != Counter({
        "OPTIONAL_FORM": 272,
        "BATTLE_ONLY_EXCLUDED": 105,
        "REQUIRED_ENABLING_FORM": 10,
        "UNOBTAINABLE_EVENT_FORM_EXCLUDED": 1,
    }):
        raise PacketError(f"form target_status件数が変化しました: {dict(counts)}")

    output = []
    giga = []
    for row in forms:
        canonical_id = int(row["canonical_id"])
        base = bases.get(row["national_no"])
        if base is None:
            raise PacketError(f"formのbaseがありません: {row['species_key']}")
        route = routes[row["species_key"]]
        category = _form_category(canonical_id, row["form_key"], row["target_status"])
        record = {
            "form_record_key": f"FORM_RECORD_{canonical_id:04d}",
            "species_key": row["species_key"],
            "base_species_key": base["species_key"],
            "canonical_id": canonical_id,
            "national_no": row["national_no"],
            "display_name": row["display_name"],
            "form_key": row["form_key"],
            "form_category": category,
            "current_target_status": row["target_status"],
            "completion_weight": row["completion_weight"],
            "current_route_method": route["method"],
            "current_runtime_status": route["runtime_status"],
            "current_physical_status": route["physical_status"],
            "current_exclusion_reason": row["exclusion_reason"],
            "design_attention": _form_attention(row["target_status"], category),
        }
        output.append(record)
        if category == "GIGANTAMAX_BATTLE_FORM":
            giga.append({
                "form_record_key": record["form_record_key"],
                "gmax_species_key": row["species_key"],
                "base_species_key": base["species_key"],
                "national_no": row["national_no"],
                "display_name": row["display_name"],
                "form_key": row["form_key"],
                "current_factor_supply": "ITEM_KEY_DYNAMAX_CANDY_HAS_NO_EXPLICIT_SOURCE",
                "engine_behavior": "MAX_POWDER_CALLBACK_TOGGLES_GMAX_BIT",
                "storage_behavior": "BOXPOKEMON_RAW80_AND_VAULT_PRESERVE_BIT",
            })
    if len(giga) != 34:
        raise PacketError(f"Gigantamax form件数が34ではありません: {len(giga)}")

    _write_csv(packet / "catalogs/form_availability_baseline.csv", [
        "form_record_key", "species_key", "base_species_key", "canonical_id",
        "national_no", "display_name", "form_key", "form_category",
        "current_target_status", "completion_weight", "current_route_method",
        "current_runtime_status", "current_physical_status", "current_exclusion_reason",
        "design_attention",
    ], output)
    _write_csv(packet / "catalogs/gmax_factor_baseline.csv", [
        "form_record_key", "gmax_species_key", "base_species_key", "national_no",
        "display_name", "form_key", "current_factor_supply", "engine_behavior",
        "storage_behavior",
    ], giga)
    category_counts = Counter(row["form_category"] for row in output)
    return {
        "canonical_species_rows": len(registry),
        "form_rows": len(forms),
        "optional_form_rows": counts["OPTIONAL_FORM"],
        "required_enabling_form_rows": counts["REQUIRED_ENABLING_FORM"],
        "gigantamax_form_rows": len(giga),
        "regional_alola_rows": category_counts["REGIONAL_ALOLA"],
        "regional_galar_rows": category_counts["REGIONAL_GALAR"],
        "regional_hisui_rows": category_counts["REGIONAL_HISUI"],
        "regional_paldea_rows": category_counts["REGIONAL_PALDEA"],
        "mega_battle_form_rows": category_counts["MEGA_BATTLE_FORM"],
        "terastal_battle_form_rows": category_counts["TERASTAL_BATTLE_FORM"],
        "other_battle_form_rows": category_counts["OTHER_BATTLE_FORM"],
        "other_persistent_or_cosmetic_form_rows": category_counts[
            "OTHER_PERSISTENT_OR_COSMETIC_FORM"
        ],
        "unobtainable_event_form_rows": category_counts["UNOBTAINABLE_EVENT_FORM"],
    }


def _active_csv_sources(root: Path) -> defaultdict[str, list[str]]:
    sources: defaultdict[str, list[str]] = defaultdict(list)
    models = (
        ("manifests/kanto_items.csv", "item_key", "KANTO_PLACEMENT", True),
        ("manifests/tohoku_items.csv", "item_key", "TOHOKU_PLACEMENT", True),
        ("manifests/qol_rewards.csv", "item_key", "QOL_REWARD", True),
        ("manifests/facility_rewards.csv", "item_key", "FACILITY_REWARD", True),
        ("config/qol_production_supply_catalog.csv", "item_key", "QOL_PRODUCTION_SHOP", False),
    )
    for relative, key, source, has_status in models:
        for row in _read_csv(root / relative):
            if has_status and row.get("status") != "ACTIVE":
                continue
            item = row.get(key, "")
            if item and item not in {"NONE", "ITEM_KEY_NONE"}:
                sources[item].append(source)

    json_models = (
        ("content/research_economy_v1/canonical_model.json", "shop", "item_key", "RESEARCH_SHOP"),
        ("content/research_economy_v1/canonical_model.json", "ranks", "reward_item_key", "RESEARCH_RANK"),
        ("content/factory_high_modes_v2/canonical_model.json", "rewards", "item_key", "FACTORY_HIGH_REWARD"),
    )
    for relative, section, key, source in json_models:
        for row in _read_json(root / relative)[section]:
            item = row.get(key, "")
            if item and item not in {"NONE", "ITEM_KEY_NONE"}:
                sources[item].append(source)
    return sources


def _item_scope(row: Mapping[str, str]) -> str:
    if row["item_key"] == "ITEM_KEY_NONE" or row["status"] == "RESERVED":
        return "INTERNAL_OR_RESERVED_REVIEW"
    if set(row["display_name"]) <= {"？"}:
        return "UNKNOWN_VEGA_SLOT_REVIEW"
    if row["role"] == "KEY_ITEM":
        return "STORY_OR_SYSTEM_KEY_REVIEW"
    return "FUNCTIONAL_COLLECTIBLE_REVIEW"


def _item_evidence(row: Mapping[str, str], source_list: Sequence[str]) -> str:
    if source_list:
        return "EXPLICIT_PRODUCTION_SOURCE"
    if row["supply_key"] == "SUPPLY_VEGA_EXISTING":
        return "LEGACY_SUPPLY_DECLARED_EXACT_ROUTE_NOT_IN_PACKET"
    if "PENDING" in row["supply_key"]:
        return "DESIGN_PENDING_NO_EXPLICIT_SOURCE"
    return "DECLARED_SUPPLY_NO_EXPLICIT_SOURCE"


def _build_item_catalog(root: Path, packet: Path) -> dict[str, int]:
    items = _read_csv(root / "manifests/item_ids.csv")
    if len(items) != 999 or {int(row["id"]) for row in items} != set(range(999)):
        raise PacketError("Item ID 0..998の999行契約が変化しました")
    sources = _active_csv_sources(root)
    output = []
    evidence_counts: Counter[str] = Counter()
    scope_counts: Counter[str] = Counter()
    for row in items:
        source_list = sorted(set(sources.get(row["item_key"], [])))
        evidence = _item_evidence(row, source_list)
        evidence_counts[evidence] += 1
        design_scope = _item_scope(row)
        scope_counts[design_scope] += 1
        output.append({
            "item_key": row["item_key"],
            "item_id": row["id"],
            "display_name": row["display_name"],
            "classification": row["classification"],
            "status": row["status"],
            "pocket": row["pocket"],
            "role": row["role"],
            "importance": row["importance"],
            "consume_policy": row["consume_policy"],
            "target_policy": row["target_policy"],
            "field_use_callback_key": row["field_use_callback_key"],
            "battle_use_callback_key": row["battle_use_callback_key"],
            "supply_key": row["supply_key"],
            "runtime_binding": row["runtime_binding"],
            "explicit_source_count": len(source_list),
            "explicit_source_kinds": "|".join(source_list) or "NONE",
            "current_evidence_class": evidence,
            "design_scope_seed": design_scope,
        })
    expected = Counter({
        "EXPLICIT_PRODUCTION_SOURCE": 109,
        "LEGACY_SUPPLY_DECLARED_EXACT_ROUTE_NOT_IN_PACKET": 362,
        "DESIGN_PENDING_NO_EXPLICIT_SOURCE": 528,
    })
    if evidence_counts != expected:
        raise PacketError(f"Item供給監査件数が変化しました: {dict(evidence_counts)}")
    _write_csv(packet / "catalogs/item_availability_baseline.csv", [
        "item_key", "item_id", "display_name", "classification", "status", "pocket",
        "role", "importance", "consume_policy", "target_policy",
        "field_use_callback_key", "battle_use_callback_key", "supply_key",
        "runtime_binding", "explicit_source_count", "explicit_source_kinds",
        "current_evidence_class", "design_scope_seed",
    ], output)
    return {
        "item_rows": len(items),
        "item_explicit_source_rows": evidence_counts["EXPLICIT_PRODUCTION_SOURCE"],
        "item_legacy_declared_rows": evidence_counts[
            "LEGACY_SUPPLY_DECLARED_EXACT_ROUTE_NOT_IN_PACKET"
        ],
        "item_design_pending_rows": evidence_counts["DESIGN_PENDING_NO_EXPLICIT_SOURCE"],
        "item_functional_review_rows": scope_counts["FUNCTIONAL_COLLECTIBLE_REVIEW"],
        "item_story_or_system_key_review_rows": scope_counts["STORY_OR_SYSTEM_KEY_REVIEW"],
        "item_unknown_vega_slot_review_rows": scope_counts["UNKNOWN_VEGA_SLOT_REVIEW"],
        "item_internal_or_reserved_review_rows": scope_counts["INTERNAL_OR_RESERVED_REVIEW"],
        "item_unknown_display_name_rows": sum(
            set(row["display_name"]) <= {"？"} for row in items
        ),
    }


def _build_species_catalog(root: Path, packet: Path) -> dict[str, int]:
    species = _read_csv(root / "manifests/species_ids.csv")
    if len(species) != 1621:
        raise PacketError(f"Species manifest件数が1621ではありません: {len(species)}")
    _write_csv(packet / "catalogs/species_keys.csv", [
        "species_key", "id", "display_name", "form_key", "is_official",
        "canonical_national_dex", "classification", "status",
    ], species)
    return {"species_key_rows": len(species)}


def _build_raid_catalog(root: Path, packet: Path) -> dict[str, int]:
    raids = _read_csv(root / "manifests/raid_encounters.csv")
    if len(raids) != 256:
        raise PacketError(f"Raid manifest件数が256ではありません: {len(raids)}")
    output = []
    for row in raids:
        low = row["raid_key"].startswith("RAID_KEY_LOW_")
        output.append({
            **row,
            "current_physical_binding_status": (
                "MANIFEST_ACTIVE_BUT_STAGE50_PHYSICAL_HOST_WITHDRAWN"
                if low else "PHYSICAL_ACCESS_REAUDIT_AFTER_WORLD_FIX"
            ),
            "current_gmax_factor_guarantee": "NOT_EXPLICIT",
            "design_attention": (
                "REPLACE_WITH_SAFE_ROTATING_HOST"
                if low else "DISTRIBUTE_POOL_ACROSS_SAFE_HOSTS"
            ),
        })
    header = list(raids[0]) + [
        "current_physical_binding_status", "current_gmax_factor_guarantee",
        "design_attention",
    ]
    _write_csv(packet / "catalogs/raid_availability_baseline.csv", header, output)
    return {
        "raid_manifest_rows": len(raids),
        "raid_low_rows_withdrawn": sum(
            row["raid_key"].startswith("RAID_KEY_LOW_") for row in raids
        ),
        "raid_shared_capture_keys": len({
            row["shared_capture_key"] for row in raids
            if row["shared_capture_key"] not in {"", "NONE"}
        }),
    }


def _build_npc_candidates(root: Path, packet: Path) -> dict[str, int]:
    ledger = _read_json(root / "reports/generated/world_runtime_owner_ledger.json")
    candidate_roles = {
        "VEGA_RECOVERED_FINITE_DIALOGUE",
        "SOURCE_RECOVERED_FINITE_DIALOGUE",
        "EXISTING_INVALID_RECOVERED_FINITE_DIALOGUE",
    }
    rows = [row for row in ledger["owner_rows"] if row["role"] in candidate_roles]
    if len(rows) != 118:
        raise PacketError(f"finite dialogue候補が118件ではありません: {len(rows)}")
    output = []
    for row in rows:
        group = int(row["group"])
        map_id = int(row["map"])
        index = int(row["index"])
        output.append({
            "candidate_key": f"NPC_CANDIDATE_{group:03d}_{map_id:03d}_{index:03d}",
            "group_id": group,
            "map_id": map_id,
            "object_index": index,
            "local_id": row.get("local_id", ""),
            "graphics_id": row.get("graphics_id", ""),
            "x": row.get("x", ""),
            "y": row.get("y", ""),
            "elevation": row.get("elevation", ""),
            "current_role": row["role"],
            "candidate_status": "CANDIDATE_ONLY_DO_NOT_BIND_IN_PRO_OUTPUT",
            "required_reaudit": "ORIGINAL_VEGA_SEMANTIC_AND_LIVE_A_INPUT_AFTER_WORLD_FIX",
            "notes": "会話だけに見えても原作eventの可能性がある。Codexが使用前に個別確認する。",
        })
    _write_csv(packet / "catalogs/message_only_npc_candidates.csv", [
        "candidate_key", "group_id", "map_id", "object_index", "local_id",
        "graphics_id", "x", "y", "elevation", "current_role", "candidate_status",
        "required_reaudit", "notes",
    ], output)
    return {
        "message_only_npc_candidate_rows": len(rows),
        "message_only_vega_rows": sum(
            row["role"] == "VEGA_RECOVERED_FINITE_DIALOGUE" for row in rows
        ),
        "message_only_source_rows": sum(
            row["role"] == "SOURCE_RECOVERED_FINITE_DIALOGUE" for row in rows
        ),
        "message_only_invalid_rows": sum(
            row["role"] == "EXISTING_INVALID_RECOVERED_FINITE_DIALOGUE" for row in rows
        ),
    }


def _collect_unlocks(value: Any, result: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "unlock_key" and isinstance(child, str) and child:
                result.add(child)
            _collect_unlocks(child, result)
    elif isinstance(value, list):
        for child in value:
            _collect_unlocks(child, result)


def _build_unlock_catalog(root: Path, packet: Path) -> dict[str, int]:
    values = {"NONE"}
    for relative in (
        "content/maps.csv", "content/qol_supply.csv", "manifests/kanto_items.csv",
        "manifests/tohoku_items.csv", "manifests/qol_rewards.csv",
        "manifests/raid_encounters.csv", "manifests/reward_encounters.csv",
        "manifests/facility_rewards.csv", "content/kanto_progression.csv",
    ):
        for row in _read_csv(root / relative):
            unlock = row.get("unlock_key", "")
            if unlock:
                values.add(unlock)
    for relative in (
        "content/research_economy_v1/canonical_model.json",
        "content/factory_high_modes_v2/canonical_model.json",
        "content/reward_encounters_v2/canonical_model.json",
    ):
        _collect_unlocks(_read_json(root / relative), values)
    _write_csv(packet / "catalogs/unlock_keys.csv", ["unlock_key"], (
        {"unlock_key": value} for value in sorted(values)
    ))
    return {"unlock_key_rows": len(values)}


def _build_system_catalog(packet: Path) -> dict[str, int]:
    rows = [
        {
            "system_key": "SYSTEM_STAGE26_ACQUISITION",
            "current_state": "DESIGNED_IMPLEMENTED_STAGE26",
            "capacity_or_count": "1206_BASE_PLUS_10_ENABLING_FORMS",
            "reuse_policy": "PRESERVE_AND_REGRESS_AFTER_WORLD_FIX",
            "notes": "通常図鑑完成用の既存経路を全置換しない。",
        },
        {
            "system_key": "SYSTEM_OPTIONAL_FORM_COLLECTION",
            "current_state": "NOT_DESIGNED",
            "capacity_or_count": "272_OPTIONAL_FORMS",
            "reuse_policy": "DESIGN_PERSISTENT_FORMS_WITHOUT_CHANGING_NATIONAL_DEX_COUNT",
            "notes": "フォーム別図鑑台帳は現状ない。",
        },
        {
            "system_key": "SYSTEM_GMAX_FACTOR",
            "current_state": "ENGINE_CALLBACK_PRESENT_SUPPLY_MISSING",
            "capacity_or_count": "34_GMAX_FORM_ROWS",
            "reuse_policy": "SUPPLY_ITEM_KEY_DYNAMAX_CANDY_AND_RAID_FACTOR",
            "notes": "G-Max形態をPC個体として直接配布しない。",
        },
        {
            "system_key": "SYSTEM_BOX14_VAULT",
            "current_state": "STAGE47_IPAD_ROUNDTRIP_VERIFIED",
            "capacity_or_count": "30_PER_BATCH_FILESYSTEM_CAPACITY",
            "reuse_policy": "NO_IN_ROM_PC_EXPANSION",
            "notes": "raw80でform、G-Max bit、Tera、持ち物を保持。mail個体は拒否。",
        },
        {
            "system_key": "SYSTEM_BP_SHOP",
            "current_state": "PRODUCTION_CONNECTED",
            "capacity_or_count": "EXISTING_MENU_AND_TRANSACTION",
            "reuse_policy": "GROUP_COMPETITIVE_AND_TRAINING_ITEMS",
            "notes": "高価な反復供給向け。",
        },
        {
            "system_key": "SYSTEM_RESEARCH_SHOP",
            "current_state": "PRODUCTION_CONNECTED",
            "capacity_or_count": "23_CURRENT_ROWS",
            "reuse_policy": "EXTEND_FORM_AND_RARE_UTILITY_SUPPLY",
            "notes": "研究ポイントはBP等と独立。",
        },
        {
            "system_key": "SYSTEM_FACTORY_REWARDS",
            "current_state": "PRODUCTION_CONNECTED",
            "capacity_or_count": "24_MODES_16_REWARD_ROWS",
            "reuse_policy": "MILESTONE_AND_HIGH_VALUE_ITEMS",
            "notes": "通常RaidやMirageのstateと共有しない。",
        },
        {
            "system_key": "SYSTEM_REWARD_ENCOUNTERS",
            "current_state": "PRODUCTION_CONNECTED",
            "capacity_or_count": "4_TIERS_24_POOL_ROWS",
            "reuse_policy": "KEEP_SPECIES_SERVICE_SEPARATE_FROM_RAID_REWARDS",
            "notes": "pending同一個体再戦と支払いtransactionを維持。",
        },
        {
            "system_key": "SYSTEM_RAID",
            "current_state": "DATA_DESIGNED_PHYSICAL_ACCESS_UNRELIABLE",
            "capacity_or_count": "256_ROWS_125_SHARED_CAPTURES_6_WITHDRAWN_LOW_ROWS",
            "reuse_policy": "ROTATING_POOLS_ACROSS_12_TO_24_SAFE_HOSTS",
            "notes": "専用map/UIを増やさずSIMPLE_EVENTを使う。",
        },
        {
            "system_key": "SYSTEM_MESSAGE_ONLY_NPCS",
            "current_state": "118_CANDIDATES_NOT_APPROVED",
            "capacity_or_count": "84_VEGA_24_SOURCE_10_INVALID_RECOVERED",
            "reuse_policy": "POST_WORLD_FIX_EXACT_REAUDIT_BEFORE_BINDING",
            "notes": "ProはIDを選ばず必要な役割と地域だけを設計する。",
        },
        {
            "system_key": "SYSTEM_FORM_DEX",
            "current_state": "NATIONAL_DEX_NUMBER_SHARED",
            "capacity_or_count": "NO_SEPARATE_FORM_LEDGER",
            "reuse_policy": "DO_NOT_REQUIRE_NEW_LEDGER_FOR_THIS_SCOPE",
            "notes": "一度捕獲した全国図鑑フラグは外部バンク預入後も残る。",
        },
        {
            "system_key": "SYSTEM_WORLD_RUNTIME",
            "current_state": "STAGE53_REOPEN_IN_PROGRESS_NOT_RELEASE",
            "capacity_or_count": "PHYSICAL_IDS_UNSTABLE",
            "reuse_policy": "DESIGN_SYMBOLIC_NOW_BIND_AFTER_BUG_FIX",
            "notes": "知恵の洞窟と博士風NPCの誤同定が再調査中。",
        },
    ]
    _write_csv(packet / "catalogs/system_capacity_catalog.csv", [
        "system_key", "current_state", "capacity_or_count", "reuse_policy", "notes",
    ], rows)
    return {"system_catalog_rows": len(rows)}


def _csv_output(
    header: Sequence[str],
    *,
    min_rows: int,
    max_rows: int | None = None,
    unique: Sequence[Sequence[str]] = (),
    required: Sequence[str] = (),
    symbolic: Sequence[str] = (),
    allowed: Mapping[str, Sequence[str]] | None = None,
    integer_ranges: Mapping[str, Sequence[int]] | None = None,
    references: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "kind": "csv", "header": list(header), "min_rows": min_rows,
        "unique": [list(value) for value in unique],
        "required_nonempty": list(required), "symbolic_fields": list(symbolic),
    }
    if max_rows is not None:
        result["max_rows"] = max_rows
    if allowed:
        result["allowed"] = {key: list(value) for key, value in allowed.items()}
    if integer_ranges:
        result["integer_ranges"] = {
            key: list(value) for key, value in integer_ranges.items()
        }
    if references:
        result["references"] = dict(references)
    return result


def _packet_spec() -> dict[str, Any]:
    form_header = [
        "form_record_key", "species_key", "base_species_key", "form_category",
        "current_target_status", "collection_policy", "acquisition_method",
        "source_system", "unlock_key", "repeatability", "tracking_policy",
        "implementation_action", "verification", "notes",
    ]
    gmax_header = [
        "form_record_key", "gmax_species_key", "base_species_key", "item_key",
        "primary_supply_system", "unlock_key", "repeatability",
        "raid_capture_sets_factor", "remove_factor_supported",
        "vault_preservation_test", "direct_gmax_species_distribution",
        "implementation_action", "notes",
    ]
    item_header = [
        "item_key", "item_role", "current_evidence_class", "target_policy",
        "primary_source_system", "secondary_source_system", "unlock_key",
        "repeatability", "currency_key", "price_or_weight", "quantity",
        "implementation_action", "verification", "reason",
    ]
    raid_host_header = [
        "raid_host_key", "region", "progression_band", "preferred_area",
        "placement_kind", "reuse_priority", "pool_key", "reward_pool_key",
        "unlock_key", "repeatability", "physical_binding_policy", "status", "notes",
    ]
    raid_pool_header = [
        "pool_entry_key", "source_raid_key", "pool_key", "tier", "biome", "species_key",
        "gmax_factor_chance", "level_min", "level_max", "weight",
        "capture_policy", "unlock_key", "status", "notes",
    ]
    raid_reward_header = [
        "reward_entry_key", "reward_pool_key", "tier", "item_key",
        "quantity_min", "quantity_max", "weight", "first_clear_guarantee",
        "unlock_key", "repeatability", "status", "notes",
    ]
    host_header = [
        "requirement_key", "service_kind", "region", "progression_band",
        "preferred_area", "reuse_priority", "menu_policy", "required_capacity",
        "post_world_fix_audit", "status", "notes",
    ]
    batch_header = [
        "batch_key", "priority", "depends_on", "owned_outputs",
        "implementation_scope", "rollback_boundary", "verify_cases", "status", "notes",
    ]
    outputs: dict[str, Any] = {
        "DESIGN_BIBLE_JA.md": {"kind": "markdown", "min_bytes": 3000},
        "form_acquisition_plan.csv": _csv_output(
            form_header, min_rows=388, max_rows=388,
            unique=(("form_record_key",), ("species_key",)),
            required=form_header[:-1],
            symbolic=("form_record_key", "species_key", "base_species_key", "unlock_key"),
            allowed={
                "collection_policy": (
                    "REQUIRED_ENABLING", "OPTIONAL_PERSISTENT_COLLECTIBLE",
                    "OPTIONAL_COSMETIC", "INTERNAL_HELPER_EXCLUDED",
                    "BATTLE_ONLY_EXCLUDED", "UNOBTAINABLE_CANON_EXCLUDED",
                ),
                "acquisition_method": (
                    "KEEP_STAGE26_ROUTE", "WILD_OVERLAY", "RESEARCH_EGG",
                    "BREEDING_FORM_INHERIT", "EVOLUTION", "FORM_CHANGE_SERVICE",
                    "FIXED_GIFT", "RAID_CAPTURE", "GMAX_FACTOR_ONLY",
                    "BATTLE_TRANSFORM_ONLY", "DO_NOT_DISTRIBUTE",
                ),
                "source_system": (
                    "STAGE26_ACQUISITION", "RESEARCH", "RAID", "BREEDING",
                    "EVOLUTION", "FORM_SERVICE", "EXCLUDED",
                ),
                "repeatability": ("ONCE", "REPEATABLE", "LIMITED_REPEATABLE", "NOT_APPLICABLE"),
                "tracking_policy": ("NATIONAL_DEX_SHARED", "NO_DEX_ENTRY", "EXISTING_CAUGHT_STATE"),
                "implementation_action": (
                    "NO_CHANGE", "DATA_ONLY", "EXISTING_SERVICE_EXTENSION",
                    "NEW_SIMPLE_EVENT", "EXCLUDED",
                ),
            },
            references={
                "form_record_key": {"catalog": "forms"},
                "species_key": {"catalog": "species"},
                "base_species_key": {"catalog": "species"},
                "unlock_key": {"catalog": "unlocks"},
            },
        ),
        "gmax_factor_plan.csv": _csv_output(
            gmax_header, min_rows=34, max_rows=34,
            unique=(("form_record_key",),), required=gmax_header[:-1],
            symbolic=(
                "form_record_key", "gmax_species_key", "base_species_key",
                "item_key", "unlock_key",
            ),
            allowed={
                "primary_supply_system": ("RAID_REWARD", "RESEARCH_SHOP", "BP_SHOP"),
                "repeatability": ("REPEATABLE", "LIMITED_REPEATABLE"),
                "raid_capture_sets_factor": ("true", "false"),
                "remove_factor_supported": ("true",),
                "vault_preservation_test": ("REQUIRED",),
                "direct_gmax_species_distribution": ("false",),
                "implementation_action": ("DATA_ONLY", "EXISTING_SERVICE_EXTENSION"),
            },
            references={
                "form_record_key": {"catalog": "gmax_forms"},
                "gmax_species_key": {"catalog": "species"},
                "base_species_key": {"catalog": "species"},
                "item_key": {"catalog": "items"},
                "unlock_key": {"catalog": "unlocks"},
            },
        ),
        "item_availability_plan.csv": _csv_output(
            item_header, min_rows=999, max_rows=999,
            unique=(("item_key",),), required=item_header[:-1],
            symbolic=("item_key", "unlock_key"),
            allowed={
                "target_policy": (
                    "OBTAINABLE_REPEATABLE", "OBTAINABLE_LIMITED_REPEATABLE",
                    "OBTAINABLE_FINITE", "STORY_KEY_EXISTING",
                    "FUNCTIONAL_SERVICE_ONLY", "INTERNAL_UNUSED_EXCLUDED",
                    "UNSAFE_DISABLED_EXCLUDED",
                ),
                "primary_source_system": (
                    "VEGA_EXISTING", "MONEY_SHOP", "BP_SHOP", "RESEARCH_SHOP",
                    "ARCADE_PRIZE", "RAID_REWARD", "FACTORY_REWARD", "FIELD_ITEM",
                    "NPC_GIFT", "WILD_HELD_ITEM", "FORM_SERVICE", "STORY_EVENT",
                    "EXCLUDED",
                ),
                "secondary_source_system": (
                    "NONE", "MONEY_SHOP", "BP_SHOP", "RESEARCH_SHOP", "ARCADE_PRIZE",
                    "RAID_REWARD", "FACTORY_REWARD", "FIELD_ITEM", "NPC_GIFT",
                    "WILD_HELD_ITEM", "FORM_SERVICE",
                ),
                "repeatability": (
                    "ONCE", "REPEATABLE", "LIMITED_REPEATABLE", "STORY_BOUND",
                    "NOT_APPLICABLE",
                ),
                "currency_key": (
                    "NONE", "MONEY", "BP", "RESEARCH_POINT", "ARCADE_COIN", "RAID_DROP",
                ),
                "implementation_action": (
                    "NO_CHANGE", "VERIFY_EXISTING", "ADD_TO_EXISTING_SHOP",
                    "ADD_TO_REWARD_POOL", "ADD_SIMPLE_EVENT", "EXCLUDED",
                ),
                "verification": ("EXACT_ROM_REQUIRED", "STATIC_AND_RUNTIME_REQUIRED", "NOT_APPLICABLE"),
            },
            integer_ranges={"price_or_weight": (0, 999999), "quantity": (0, 99)},
            references={
                "item_key": {"catalog": "items"},
                "unlock_key": {"catalog": "unlocks"},
            },
        ),
        "raid_host_plan.csv": _csv_output(
            raid_host_header, min_rows=12, max_rows=24,
            unique=(("raid_host_key",),), required=raid_host_header[:-1],
            symbolic=("raid_host_key", "pool_key", "reward_pool_key", "unlock_key"),
            allowed={
                "region": ("TOHOKU", "KANTO"),
                "placement_kind": ("MESSAGE_NPC_REUSE", "TERMINAL_REUSE", "BG_EVENT_REPOINT", "FIELD_SPARKLE"),
                "reuse_priority": ("MESSAGE_ONLY_FIRST", "EXISTING_SERVICE_FIRST", "NO_NEW_OBJECT"),
                "repeatability": ("REPEATABLE", "ROTATING_REPEATABLE", "SHARED_ONCE_CAPTURE"),
                "physical_binding_policy": ("POST_WORLD_FIX_EXACT_REAUDIT",),
                "status": ("READY_FOR_POST_FIX_BINDING",),
            },
            references={"unlock_key": {"catalog": "unlocks"}},
        ),
        "raid_pool_entries.csv": _csv_output(
            raid_pool_header, min_rows=256,
            unique=(("pool_entry_key",),), required=raid_pool_header[:-1],
            symbolic=(
                "pool_entry_key", "source_raid_key", "pool_key", "species_key",
                "unlock_key",
            ),
            allowed={
                "tier": ("LOW", "MID", "HIGH", "MASTER", "SPECIAL"),
                "capture_policy": ("REPEATABLE_NORMAL", "SHARED_ONCE", "NO_CAPTURE"),
                "status": ("ACTIVE",),
            },
            integer_ranges={
                "gmax_factor_chance": (0, 100), "level_min": (1, 100),
                "level_max": (1, 100), "weight": (1, 1000),
            },
            references={
                "source_raid_key": {"catalog": "raids", "allow": ["NONE"]},
                "species_key": {"catalog": "species"},
                "unlock_key": {"catalog": "unlocks"},
            },
        ),
        "raid_reward_entries.csv": _csv_output(
            raid_reward_header, min_rows=32,
            unique=(("reward_entry_key",),), required=raid_reward_header[:-1],
            symbolic=("reward_entry_key", "reward_pool_key", "item_key", "unlock_key"),
            allowed={
                "tier": ("LOW", "MID", "HIGH", "MASTER", "SPECIAL"),
                "first_clear_guarantee": ("true", "false"),
                "repeatability": ("ONCE", "REPEATABLE", "LIMITED_REPEATABLE"),
                "status": ("ACTIVE",),
            },
            integer_ranges={
                "quantity_min": (1, 99), "quantity_max": (1, 99), "weight": (1, 1000),
            },
            references={
                "item_key": {"catalog": "items"},
                "unlock_key": {"catalog": "unlocks"},
            },
        ),
        "host_requirements.csv": _csv_output(
            host_header, min_rows=4, max_rows=16,
            unique=(("requirement_key",),), required=host_header[:-1],
            symbolic=("requirement_key",),
            allowed={
                "service_kind": ("FORM_SERVICE", "ITEM_SHOP", "RAID_HOST", "RAID_REWARD", "GMAX_SERVICE"),
                "region": ("TOHOKU", "KANTO", "BOTH"),
                "reuse_priority": ("MESSAGE_ONLY_FIRST", "EXISTING_SERVICE_FIRST", "NO_NEW_OBJECT"),
                "menu_policy": ("STANDARD_MESSAGE", "STANDARD_LIST", "YES_NO", "EXISTING_SHOP_MENU"),
                "post_world_fix_audit": ("REQUIRED",),
                "status": ("READY",),
            },
            integer_ranges={"required_capacity": (1, 999)},
        ),
        "implementation_batches.csv": _csv_output(
            batch_header, min_rows=5, max_rows=12,
            unique=(("batch_key",),), required=batch_header[:-1],
            symbolic=("batch_key",),
            allowed={"priority": ("P0", "P1", "P2"), "status": ("READY",)},
        ),
        "OPEN_QUESTIONS.md": {"kind": "markdown", "min_bytes": 40},
    }
    return {
        "schema_version": 1,
        "packet_type": "COLLECTION_SUPPLY",
        "output_zip_name": OUTPUT_ZIP_NAME,
        "catalog_sets": {
            "species": {"path": "catalogs/species_keys.csv", "field": "species_key"},
            "forms": {"path": "catalogs/form_availability_baseline.csv", "field": "form_record_key"},
            "gmax_forms": {"path": "catalogs/gmax_factor_baseline.csv", "field": "form_record_key"},
            "items": {"path": "catalogs/item_availability_baseline.csv", "field": "item_key"},
            "raids": {"path": "catalogs/raid_availability_baseline.csv", "field": "raid_key"},
            "unlocks": {"path": "catalogs/unlock_keys.csv", "field": "unlock_key"},
        },
        "outputs": outputs,
        "coverage": [
            {"output": "form_acquisition_plan.csv", "output_field": "form_record_key", "catalog": "forms", "exact": True},
            {"output": "gmax_factor_plan.csv", "output_field": "form_record_key", "catalog": "gmax_forms", "exact": True},
            {"output": "item_availability_plan.csv", "output_field": "item_key", "catalog": "items", "exact": True},
            {"output": "raid_pool_entries.csv", "output_field": "source_raid_key", "catalog": "raids", "exact": False},
        ],
    }


def _start_text() -> str:
    return dedent(f"""
        # 最初に読む

        このパケットは、Pokémon Vega Modernのバグ修正完了後にCodexが短い実装batchへ
        変換できるよう、全収集・道具供給・恒常フォーム・G-Max個体・Raid配置を確定する
        ChatGPT Pro向け入力です。

        ## 作業順

        1. `01_CHATGPT_PRO_PROMPT_JA.txt`を新しいChatGPT Pro会話へ貼る。
        2. `02_CURRENT_STATE_AND_GAPS_JA.md`から`05_IMPLEMENTATION_BOUNDARIES_JA.md`まで読む。
        3. `catalogs/`を機械的正本として分析する。
        4. `submission_template/`を`submission/`へ複製し、全ファイルを完成させる。
        5. `python tools/validate_submission.py submission --packet-root .`をPASSさせる。
        6. `submission/`直下だけを`{OUTPUT_ZIP_NAME}`へ格納して返す。

        ## 重要

        - 現行Stage 53はworld runtime再調査中で、配布候補ではない。
        - Proはmap group/map/local ID、ROM address、NPC IDを確定しない。
        - 会話だけのNPC 118件は候補であり、原作意味とA入力をCodexがバグ修正後に再監査する。
        - 既存の1,206種＋進化入口フォーム10件のStage 26取得設計は保持する。
        - ZIPをChatGPTが直接展開できない場合は、Windowsで展開して中のファイルをアップロードする。
    """)


def _prompt_text() -> str:
    return dedent(f"""
        役割:
        あなたはPokémon Vega Modernの収集・経済・イベント配置を担当するシステムデザイナー兼、
        Codex実装用データ作者です。

        目標:
        添付ZIPを唯一のプロジェクト技術正本として読み、未設計の恒常フォーム272件、
        G-Max可能個体34フォーム分、全999 Item行の供給方針、現行world修正後に安全に配置する
        Raidと既存NPC再利用要件を一つの実装可能仕様へ確定してください。既存Raid 256行は
        すべてrotation poolへ割り当て、必要なら`source_raid_key=NONE`で新規行を追加してください。

        必須判断:
        - Stage 26の1,206種＋進化入口フォーム10件の経路は再設計せず、回帰対象として保持する。
        - 全388 form行を分類する。正当な恒常・リージョン・外見フォームには入手または生成経路を
          与え、DPE内部補助、戦闘中変身、Mega、G-Max表示形態、Tera形態は直接配布しない。
        - G-Maxは34の巨大化Speciesを配る方式にせず、base個体のG-Max bitを使う。
          既存`ITEM_KEY_DYNAMAX_CANDY`の反復可能な供給とRaid捕獲時bit付与を確定する。
        - 全999 Item行を一行ずつ判定し、機能する可視道具は少なくとも一つの供給へ接続する。
          NONE、予約、用途不明、危険な内部道具は理由付きで除外する。単に全999個を店へ並べない。
        - BP、研究ポイント、通常店、Factory、Raid報酬、既存field item、NPC giftを役割分担し、
          必須消耗品を一度限りfield itemだけにしない。
        - Raidは専用map、ロビー、full-screen UIを増やさず、12〜24のSIMPLE_EVENT入口と
          rotation poolで分散する。既存256 rowを一度ずつ割り当て、種族・capture policy・
          unlockと125共有捕獲stateを壊さない。G-Max可能な全base種をchance>0で含める。
        - 物理NPC IDは選ばず、必要な地域・役割・menu・容量を`host_requirements.csv`へ書く。
          Codexがworld runtime修正後に118候補を原作Vegaと実入力で監査して束縛する。
        - フォーム別図鑑完成ledgerを新設しない。全国図鑑番号共有とBox 14外部vaultを利用する。

        品質:
        - catalogs内のsymbolic keyだけを使い、数値Species/Item/Map/NPC IDを発明しない。
        - `OPEN_QUESTIONS.md`を「なし」にし、TODO、TBD、未定、要検討を残さない。
        - 実装batchはP0〜P2、所有output、rollback境界、exact-ROM testを明記する。
        - validatorをPASSさせるまで修正する。

        出力:
        `submission/`直下だけを`{OUTPUT_ZIP_NAME}`に梱包して添付し、最終回答には
        `VALIDATION=PASS`、主要行数、open_questions=0だけを簡潔に表示してください。
    """)


def _current_state_text(counts: Mapping[str, int]) -> str:
    return dedent(f"""
        # 現状と未設計範囲

        ## 既にあるもの

        - 全国図鑑1〜1025のbase種とVega独立181種、合計1,206種の取得設計・Stage 26実装。
        - 別全国種への進化に必要なリージョンフォーム10件の研究タマゴ。
        - 201取得イベント、24 host、捕獲／gift／egg／化石／進化／交換代替／serviceのtransaction。
        - BP shop、研究ポイントshop 23品、Factory 24 mode、報酬遭遇24 pool。
        - Box 14と外部filesystem個体庫のraw80往復。ゲーム内PC拡張は不要。

        ## 数値で確認した穴

        - canonical Species: {counts['canonical_species_rows']}行。
        - form: {counts['form_rows']}行。このうちoptional form {counts['optional_form_rows']}行は
          完成数から外しただけで、取得経路は設計されていない。
          リージョン範囲はAlola {counts['regional_alola_rows']}、Galar {counts['regional_galar_rows']}、
          Hisui {counts['regional_hisui_rows']}、Paldea {counts['regional_paldea_rows']}行。DPE内部補助や
          Galarヒヒダルマの戦闘形態を外見だけで恒常配布しないよう個別判定が必要。
        - その他のformは恒常／外見候補{counts['other_persistent_or_cosmetic_form_rows']}、
          Mega {counts['mega_battle_form_rows']}、Tera {counts['terastal_battle_form_rows']}、
          その他戦闘形態{counts['other_battle_form_rows']}、未配信event形態
          {counts['unobtainable_event_form_rows']}行。
        - G-Max battle form: {counts['gigantamax_form_rows']}行。base個体のbitを使うengineはあるが、
          `ITEM_KEY_DYNAMAX_CANDY`に明示供給がない。
        - Item: {counts['item_rows']}行。明示production sourceあり
          {counts['item_explicit_source_rows']}、Vega既存供給という宣言だけ
          {counts['item_legacy_declared_rows']}、明示供給なし
          {counts['item_design_pending_rows']}。これは即「入手不可」を意味せず、物理経路監査の強さを表す。
          機能する通常候補{counts['item_functional_review_rows']}、story／system key候補
          {counts['item_story_or_system_key_review_rows']}、用途不明Vega slot
          {counts['item_unknown_vega_slot_review_rows']}、NONE／予約候補
          {counts['item_internal_or_reserved_review_rows']}行として、一律店売りにせず分類する。
        - Raid manifest: {counts['raid_manifest_rows']}行、共有捕獲key
          {counts['raid_shared_capture_keys']}。低レベル{counts['raid_low_rows_withdrawn']}入口は
          Stage 50で停止回避のため物理配置を撤回した。
        - 会話だけに見えるNPC候補: {counts['message_only_npc_candidate_rows']}件。
          すべて使用前の原作意味・実入力再監査が必要。

        ## 現行ROMについての禁止表現

        Stage 53は本物の「ちえのどうくつ」と博士風NPCを誤同定したため再調査中です。
        この設計作業だけで「現行ROMですべて入手可能」「全Raid入口が動く」と主張しません。
        返却物はsymbolic designを完成させ、物理bindingと実ROM合格はバグ修正後のCodexへ残します。
    """)


def _design_principles_text() -> str:
    return dedent("""
        # 設計原則

        ## 収集の定義を分ける

        1. 図鑑完成: 1,206種。全国図鑑はformを同じ番号へ集約する。
        2. 恒常フォーム収集: optional。正当な保存可能formへ入手／生成経路を用意する。
        3. 戦闘フォーム: Mega、G-Max表示形態、Tera、一時変身は個体として配らない。
        4. G-Max可否: base個体のbit。ダイマックスアメまたはG-Max Raid捕獲で付与する。
        5. Item completion: 機能する可視Itemを対象とし、内部予約や危険なdebug相当は除外する。

        ## 実装量を抑える配置

        - 通常消耗品: money shop。
        - 育成・対戦品: BP shop。
        - form変更、珍しい進化品、図鑑支援: research shop/service。
        - 高価値品、G-Max、Tera、Ability品: Raid reward。
        - 一度限りの鍵・Mega Stone・Z Crystal等: 既存story、短いNPC gift、field item。
        - Berry、ball等: 店＋Raid／wild held itemの補助供給。低確率盗難を唯一経路にしない。

        ## Raid

        - 一体ごとにNPCを置かず、地域・進行・biome別のrotation poolへまとめる。
        - 入口は12〜24件。トーホクとカントー双方へ分散し、早期・中盤・後半・endgameを作る。
        - special 125共有捕獲keyは同じ個体を二地方で重複取得させない。
        - `source_raid_key`で現行256行を一度ずつpoolへ移し、元のspecies、capture policy、unlockを保持する。
        - 追加枠は`source_raid_key=NONE`とし、既存行のsymbolic keyを捏造しない。
        - 捕獲と報酬のrepeatabilityを分離する。
        - G-Max対象のRaid捕獲はbase Speciesへ戻したうえでG-Max bitを保持する。

        ## NPC再利用

        Proは物理IDを選ばない。まず必要serviceと地域だけを設計し、実装時にCodexが次の順で探す。

        1. 原作意味が本当に不要と実証された会話のみNPC。
        2. 既存shop／研究員／Factory受付へのmenu拡張。
        3. 既存sign／terminalのrepoint。
        4. object追加なしのBG eventまたは足元調査。

        原作NPC、item、trainer、field object、取得イベントを見た目だけで上書きしない。
    """)


def _output_contract_text(spec: Mapping[str, Any]) -> str:
    lines = [
        "# 出力契約", "", f"返却ZIP名: `{OUTPUT_ZIP_NAME}`", "",
        "`submission/`直下には次の成果だけを置きます。", "",
    ]
    for name, model in spec["outputs"].items():
        suffix = ""
        if model["kind"] == "csv":
            maximum = model.get("max_rows")
            suffix = f"（{model['min_rows']}行以上"
            if maximum is not None:
                suffix += f"、最大{maximum}行"
            suffix += "）"
        lines.append(f"- `{name}`{suffix}")
    lines.extend([
        "- `VALIDATION_REPORT.json`（validator生成）",
        "- `SUBMISSION_MANIFEST.json`（validator生成）", "",
        "## CSV header", "",
    ])
    for name, model in spec["outputs"].items():
        if model["kind"] != "csv":
            continue
        lines.extend([f"### {name}", "", "```text", ",".join(model["header"]), "```", ""])
    lines.extend([
        "## 検証", "", "```bash",
        "python tools/validate_submission.py submission --packet-root .",
        "```", "", "PASS後にsubmission直下だけをZIPへ格納します。",
    ])
    return "\n".join(lines)


def _implementation_boundaries_text() -> str:
    return dedent("""
        # 実装境界と受入条件

        ## Proが決める

        - 全form／Item行の採否、供給system、unlock、repeatability、価格帯。
        - Raid hostの地域・進行帯・役割とrotation pool、reward pool。
        - G-Max bit取得とダイマックスアメ供給。
        - 実装batch、rollback境界、代表test。

        ## Codexがバグ修正後に決める

        - exact map group/map/local ID、script root、ROM address、free object slot。
        - 118候補NPCが本当に不要な会話だけかの原作ROM／A入力監査。
        - 既存flag、var、save owner、allocator、event object上限への物理binding。
        - 現行Stageでのbuild、mGBA、iPad実プレイ、通常save／Continue。

        ## 受入条件

        - Stage 26の1,206＋10経路を失わない。
        - 全388 formと全999 Itemが返却CSVで一度ずつ分類される。
        - 正当な保存可能リージョンフォームが、直接・進化・孵化・form serviceのいずれかを持つ。
        - 34 G-Max formは直接配布せず、base個体bitの取得経路を持つ。
        - ダイマックスアメが反復または限定反復で供給される。
        - Raid入口12〜24、既存256 Raid行のpool割当100%、reward 32件以上。
        - G-Max可能な34 base種がRaid poolにも含まれ、捕獲時bit付与が指定される。
        - 必須進化・form変更消耗品は一度限り／低確率だけに依存しない。
        - 物理IDはすべてpost-world-fix exact audit待ちとして残す。
        - Box 14 vaultでリージョンform、G-Max bit、持ち物の往復testを指定する。
    """)


def _submission_template(packet: Path, spec: Mapping[str, Any]) -> None:
    target = packet / "submission_template"
    target.mkdir(parents=True, exist_ok=True)
    for name, model in spec["outputs"].items():
        path = target / name
        if model["kind"] == "csv":
            _write_csv(path, model["header"], [])
        elif name == "OPEN_QUESTIONS.md":
            _write_text(path, "# Open questions\n\n完成版では質問を0件に確定してください。")
        else:
            _write_text(path, f"# {name}\n\n完成版の設計正本へ置換してください。")


def _privacy_scan(packet: Path) -> dict[str, int]:
    forbidden_strings = (b"BEGIN PRIVATE KEY", b"AKIA", b"sk-proj-")
    private_path_patterns = (
        re.compile(rb"/home/[^/\x00\r\n]+"),
        re.compile(rb"/mnt/[a-z]/Users/[^/\x00\r\n]+", re.IGNORECASE),
        re.compile(rb"[a-z]:\\Users\\[^\\\x00\r\n]+", re.IGNORECASE),
    )
    forbidden_suffixes = {
        ".gba", ".sav", ".sa1", ".sa2", ".sgm", ".ips", ".ups", ".bps",
        ".exe", ".dll", ".so", ".dylib", ".7z", ".rar",
    }
    files = bytes_total = 0
    for path in packet.rglob("*"):
        if not path.is_file():
            continue
        files += 1
        bytes_total += path.stat().st_size
        if path.suffix.lower() in forbidden_suffixes:
            raise PacketError(f"禁止binaryが混入しました: {path.relative_to(packet)}")
        raw = path.read_bytes()
        for marker in forbidden_strings:
            if marker in raw:
                raise PacketError(f"private markerが混入しました: {path.relative_to(packet)}")
        for pattern in private_path_patterns:
            if pattern.search(raw):
                raise PacketError(f"private pathが混入しました: {path.relative_to(packet)}")
    return {"files_scanned": files, "bytes_scanned": bytes_total}


def _write_manifest(packet: Path, counts: Mapping[str, int], privacy: Mapping[str, int]) -> None:
    files = []
    for path in sorted(packet.rglob("*")):
        if path.is_file() and path.name not in {"PACKET_MANIFEST.json", "SHA256SUMS.txt"}:
            files.append({
                "path": path.relative_to(packet).as_posix(),
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            })
    _write_json(packet / "PACKET_MANIFEST.json", {
        "schema_version": 1,
        "packet_name": PACKET_NAME,
        "packet_type": "COLLECTION_SUPPLY",
        "expected_output_zip": OUTPUT_ZIP_NAME,
        "baseline": {
            "world_runtime": "STAGE53_REOPEN_IN_PROGRESS_NOT_RELEASE",
            "physical_binding_policy": "POST_WORLD_FIX_EXACT_REAUDIT",
        },
        "privacy": {
            "rom_included": False, "save_included": False, "patch_included": False,
            "private_input_included": False, **privacy,
        },
        "catalog_counts": dict(sorted(counts.items())),
        "files": files,
    })
    checksum_paths = [
        path for path in sorted(packet.rglob("*"))
        if path.is_file() and path.name != "SHA256SUMS.txt"
    ]
    _write_text(packet / "SHA256SUMS.txt", "".join(
        f"{_sha256(path)}  {path.relative_to(packet).as_posix()}\n"
        for path in checksum_paths
    ))


def _verify_manifest(packet: Path) -> None:
    manifest = _read_json(packet / "PACKET_MANIFEST.json")
    expected = {row["path"]: row for row in manifest["files"]}
    actual = {
        path.relative_to(packet).as_posix(): path
        for path in packet.rglob("*")
        if path.is_file() and path.name not in {"PACKET_MANIFEST.json", "SHA256SUMS.txt"}
    }
    if set(expected) != set(actual):
        raise PacketError("PACKET_MANIFEST file set不一致")
    for name, row in expected.items():
        path = actual[name]
        if path.stat().st_size != row["size"] or _sha256(path) != row["sha256"]:
            raise PacketError(f"PACKET_MANIFEST mismatch: {name}")
    for line in (packet / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if not (packet / name).is_file() or _sha256(packet / name) != digest:
            raise PacketError(f"SHA256SUMS mismatch: {name}")


def _deterministic_zip(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(
                f"{source.name}/{path.relative_to(source).as_posix()}",
                date_time=FIXED_ZIP_TIME,
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o644 & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)


def _verify_zip(zip_path: Path, expected_digest: str) -> None:
    with tempfile.TemporaryDirectory(prefix="vega-collection-supply-verify-") as temporary:
        destination = Path(temporary)
        with zipfile.ZipFile(zip_path) as archive:
            bad = archive.testzip()
            if bad:
                raise PacketError(f"ZIP CRC失敗: {bad}")
            prefix = f"{PACKET_NAME}/"
            names = archive.namelist()
            if not names or any(
                not name.startswith(prefix) or ".." in Path(name).parts for name in names
            ):
                raise PacketError("ZIP root/path traversal契約違反")
            archive.extractall(destination)
        extracted = destination / PACKET_NAME
        _verify_manifest(extracted)
        run = subprocess.run(
            [sys.executable, str(extracted / "tools/validate_submission.py"),
             "--packet-root", str(extracted), "--self-test"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if run.returncode or "VALIDATION=PASS" not in run.stdout:
            raise PacketError(f"展開後validator self-test失敗:\n{run.stdout}\n{run.stderr}")
        repacked = destination / "repacked.zip"
        _deterministic_zip(extracted, repacked)
        if _sha256(repacked) != expected_digest:
            raise PacketError("ZIPがbyte deterministicではありません")


def build(
    root: Path,
    output_parent: Path,
    zip_parent: Path,
    windows_downloads: Path | None,
) -> dict[str, Any]:
    packet = output_parent / PACKET_NAME
    if packet.exists():
        shutil.rmtree(packet)
    packet.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    counts.update(_build_species_catalog(root, packet))
    counts.update(_build_form_catalog(root, packet))
    counts.update(_build_item_catalog(root, packet))
    counts.update(_build_raid_catalog(root, packet))
    counts.update(_build_npc_candidates(root, packet))
    counts.update(_build_unlock_catalog(root, packet))
    counts.update(_build_system_catalog(packet))

    spec = _packet_spec()
    _write_json(packet / "PACKET_SPEC.json", spec)
    _copy(root, packet, VALIDATOR, Path("tools/validate_submission.py"))
    _write_text(packet / "00_START_HERE_JA.md", _start_text())
    _write_text(packet / "01_CHATGPT_PRO_PROMPT_JA.txt", _prompt_text())
    _write_text(packet / "02_CURRENT_STATE_AND_GAPS_JA.md", _current_state_text(counts))
    _write_text(packet / "03_DESIGN_PRINCIPLES_JA.md", _design_principles_text())
    _write_text(packet / "04_OUTPUT_CONTRACT_JA.md", _output_contract_text(spec))
    _write_text(packet / "05_IMPLEMENTATION_BOUNDARIES_JA.md", _implementation_boundaries_text())
    _submission_template(packet, spec)

    self_test = subprocess.run(
        [sys.executable, str(packet / "tools/validate_submission.py"),
         "--packet-root", str(packet), "--self-test"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if self_test.returncode or "VALIDATION=PASS" not in self_test.stdout:
        raise PacketError(f"validator self-test失敗:\n{self_test.stdout}\n{self_test.stderr}")
    privacy = _privacy_scan(packet)
    _write_manifest(packet, counts, privacy)
    _verify_manifest(packet)

    zip_path = zip_parent / f"{PACKET_NAME}.zip"
    _deterministic_zip(packet, zip_path)
    digest = _sha256(zip_path)
    _verify_zip(zip_path, digest)

    windows_path = None
    if windows_downloads is not None:
        if not windows_downloads.is_dir():
            raise PacketError(f"Windows Downloadsがありません: {windows_downloads}")
        windows_path = windows_downloads / zip_path.name
        shutil.copy2(zip_path, windows_path)
        if _sha256(windows_path) != digest:
            raise PacketError("Windows Downloads copy hash不一致")

    return {
        "schema_version": 1,
        "status": "PASS",
        "packet_name": PACKET_NAME,
        "packet_dir": str(packet),
        "zip": str(zip_path),
        "windows_download": str(windows_path) if windows_path else None,
        "zip_size": zip_path.stat().st_size,
        "zip_sha256": digest,
        "catalog_counts": dict(sorted(counts.items())),
        "verification": {
            "validator_self_test": "PASS",
            "manifest": "PASS",
            "sha256s": "PASS",
            "privacy": "PASS",
            "zip_crc": "PASS",
            "path_guard": "PASS",
            "repack_determinism": "PASS",
            "windows_copy": "PASS" if windows_path else "SKIP",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output-parent", type=Path,
        default=Path("userfile/chatgpt_pro_design_packets/unpacked"),
    )
    parser.add_argument(
        "--zip-parent", type=Path, default=Path("userfile/chatgpt_pro_design_packets"),
    )
    parser.add_argument(
        "--windows-downloads", type=Path, default=_default_windows_downloads(),
    )
    parser.add_argument("--no-windows-copy", action="store_true")
    parser.add_argument(
        "--report", type=Path,
        default=Path("build/chatgpt_pro_collection_supply_packet.json"),
    )
    args = parser.parse_args()
    root = args.root.resolve()

    def resolved(value: Path) -> Path:
        return value if value.is_absolute() else root / value

    try:
        result = build(
            root,
            resolved(args.output_parent).resolve(),
            resolved(args.zip_parent).resolve(),
            None if args.no_windows_copy else args.windows_downloads.resolve(),
        )
    except (PacketError, OSError, ValueError, KeyError, json.JSONDecodeError,
            subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        result = {"schema_version": 1, "status": "FAIL", "error": str(exc)}
    report = resolved(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_bytes(_stable_json(result))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
