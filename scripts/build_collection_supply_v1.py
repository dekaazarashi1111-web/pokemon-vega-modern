#!/usr/bin/env python3
"""検証済みCollection Supply V1をStage 55へ結合しStage 56を生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import stat
import struct
import subprocess
import sys
import tempfile
import zipfile
import zlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import (  # noqa: E402
    _arm_tool,
    _host_cc,
    _sparse_bps,
)
from tools.regression.rom_runtime import _charmap, _encode_text  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import build_allocation_report_from_csv  # noqa: E402
from tools.trainer_final.kanto_events import (  # noqa: E402
    _map_header_offset,
    _object_fields,
    _stage_map_state,
)


TASK = "USER-20260827-COLLECTION-SUPPLY-V1-IMPLEMENTATION"
STAGE = 56
GBA_ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "collection_supply_v1_stage56_payload"
DEFAULT_CONFIG = Path("config/collection_supply_v1.json")

EXPECTED_ZIP_ENTRIES = (
    "DESIGN_BIBLE_JA.md",
    "form_acquisition_plan.csv",
    "gmax_factor_plan.csv",
    "item_availability_plan.csv",
    "raid_host_plan.csv",
    "raid_pool_entries.csv",
    "raid_reward_entries.csv",
    "host_requirements.csv",
    "implementation_batches.csv",
    "OPEN_QUESTIONS.md",
    "VALIDATION_REPORT.json",
    "SUBMISSION_MANIFEST.json",
)

REQUIRED_ENTRYPOINTS = {
    "CollectionSupply_Probe",
    "CollectionSupply_FieldHost",
    "CollectionSupply_ApplySelectedForm",
    "CollectionSupply_ApplySelectedGmax",
    "CollectionSupply_StartSelectedRaid",
    "CollectionSupply_SaveLoadAdapter",
    "CollectionSupply_ReadKeysAdapter",
    "CollectionSupply_TryGenerateWildMonAdapter",
    "CollectionSupply_EndWildBattleAdapter",
    "CollectionSupply_EndWildBattleCommitInternal",
    "CollectionSupply_TestInitialize",
    "CollectionSupply_TestPurchase",
    "CollectionSupply_TestApplyForm",
    "CollectionSupply_TestToggleGmax",
    "CollectionSupply_TestPrepareRaid",
    "CollectionSupply_TestCompleteRaid",
    "CollectionSupply_TestGift",
    "CollectionSupply_TestClaimRelic",
    "CollectionSupply_TestOwnerField",
    "CollectionSupply_TestBalance",
    "CollectionSupply_TestSectorRoundTrip",
    "CollectionSupply_TestSetFault",
    "CollectionSupply_TestSetBalances",
    "CollectionSupply_TestSetBag",
    "CollectionSupply_TestSeedParty",
    "CollectionSupply_TestPartyField",
    "CollectionSupply_TestBagCount",
    "CollectionSupply_TestBagItem",
    "CollectionSupply_TestGiftField",
    "CollectionSupply_TestRaidField",
}

EXPECTED_TESTS = (
    "probe_and_canonical_counts",
    "owner_crc_and_sector31_restore",
    "money_bp_research_and_relic_transactions",
    "form_service_gift_egg_and_wild_overlay",
    "gmax_toggle_capture_and_raw80_vault",
    "raid_rotation_capture_reward_and_retry",
    "fourteen_world_hosts_normal_a_input",
    "stage55_world_regression",
    "warnings_zero",
)

UNLOCK_IDS = {
    "NONE": 0,
    "VEGA_PRE_ENTRY": 1,
    "VEGA_BADGE_1": 2,
    "VEGA_BADGE_2": 3,
    "VEGA_BADGE_5": 4,
    "KANTO_EARLY_ACCESS": 5,
    "RESEARCH_PROFILE_UNLOCKED": 6,
    "RAID_HIGH_UNLOCKED": 7,
    "TM_LICENSE_UNLOCKED": 8,
    "HIDDEN_ABILITY_DEXNAV_UNLOCKED": 9,
    "LEAGUE_I_CLEARED": 10,
    "FACTORY_STANDARD": 11,
    "LEAGUE_II_CLEARED": 12,
    "COMPETITIVE_SUPPLY_UNLOCKED": 13,
    "FACTORY_FULL": 14,
    "FINAL_LEAGUE_CLEARED": 15,
    "KANTO_LEAGUE_CLEAR": 16,
    "UB_PARADOX_UNLOCKED": 17,
    "FACTORY_MASTER": 18,
}

UNLOCK_MACROS = {
    "NONE": "NONE",
    "VEGA_PRE_ENTRY": "VEGA_PRE_ENTRY",
    "VEGA_BADGE_1": "VEGA_BADGE_1",
    "VEGA_BADGE_2": "VEGA_BADGE_2",
    "VEGA_BADGE_5": "VEGA_BADGE_5",
    "KANTO_EARLY_ACCESS": "KANTO_EARLY_ACCESS",
    "RESEARCH_PROFILE_UNLOCKED": "RESEARCH_PROFILE",
    "RAID_HIGH_UNLOCKED": "RAID_HIGH",
    "TM_LICENSE_UNLOCKED": "TM_LICENSE",
    "HIDDEN_ABILITY_DEXNAV_UNLOCKED": "HIDDEN_ABILITY",
    "LEAGUE_I_CLEARED": "LEAGUE_I",
    "FACTORY_STANDARD": "FACTORY_STANDARD",
    "LEAGUE_II_CLEARED": "LEAGUE_II",
    "COMPETITIVE_SUPPLY_UNLOCKED": "COMPETITIVE",
    "FACTORY_FULL": "FACTORY_FULL",
    "FINAL_LEAGUE_CLEARED": "FINAL_LEAGUE",
    "KANTO_LEAGUE_CLEAR": "KANTO_LEAGUE",
    "UB_PARADOX_UNLOCKED": "UB_PARADOX",
    "FACTORY_MASTER": "FACTORY_MASTER",
}

METHOD_IDS = {
    "WILD_OVERLAY": 0,
    "EVOLUTION": 1,
    "BREEDING_FORM_INHERIT": 2,
    "BATTLE_TRANSFORM_ONLY": 3,
    "FORM_CHANGE_SERVICE": 4,
    "DO_NOT_DISTRIBUTE": 5,
    "RESEARCH_EGG": 6,
    "FIXED_GIFT": 7,
    "KEEP_STAGE26_ROUTE": 8,
    "RAID_CAPTURE": 9,
    "GMAX_FACTOR_ONLY": 10,
}

SOURCE_IDS = {
    "MONEY_SHOP": 0,
    "BP_SHOP": 1,
    "RESEARCH_SHOP": 2,
    "FACTORY_REWARD": 3,
    "RAID_REWARD": 4,
    "NPC_GIFT": 5,
    "FORM_SERVICE": 6,
    "STORY_EVENT": 7,
    "VEGA_EXISTING": 8,
    "EXCLUDED": 9,
}

REPEAT_IDS = {
    "NOT_APPLICABLE": 0,
    "REPEATABLE": 1,
    "LIMITED_REPEATABLE": 2,
    "ONCE": 3,
    "STORY_BOUND": 4,
}

SERVICE_IDS = {
    "MONEY": 0,
    "BP": 1,
    "RESEARCH": 2,
    "FORM": 3,
    "RELIC": 4,
    "GIFT": 5,
    "GMAX": 6,
}

TIER_IDS = {"LOW": 0, "MID": 1, "HIGH": 2, "MASTER": 3, "SPECIAL": 4}


class CollectionSupplyBuildError(RuntimeError):
    """入力、canonical解決、ROM配線または検証契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise CollectionSupplyBuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def _integer(value: Any, label: str) -> int:
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as error:
        _fail(f"{label}が整数ではありません: {value!r}: {error}")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"JSONを読めません: {path}: {error}")
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _identity(contract: Mapping[str, Any], label: str) -> bytes:
    path = ROOT / str(contract["path"])
    try:
        raw = path.read_bytes()
    except OSError as error:
        _fail(f"{label}を読めません: {error}")
    if "size" in contract and len(raw) != int(contract["size"]):
        _fail(f"{label} size不一致: {len(raw)} != {contract['size']}")
    if _sha(raw) != str(contract["sha256"]):
        _fail(f"{label} SHA-256不一致: {path}")
    return raw


def _csv_raw(raw: bytes, label: str) -> list[dict[str, str]]:
    try:
        return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error) as error:
        _fail(f"{label} CSVを読めません: {error}")


def _csv_path(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    except (OSError, csv.Error) as error:
        _fail(f"CSVを読めません: {path}: {error}")


def _run(command: Sequence[str], label: str, timeout: int = 360) -> str:
    completed = subprocess.run(
        list(command), cwd=ROOT, capture_output=True, text=True,
        timeout=timeout, check=False,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label}失敗 ({completed.returncode}): {detail[-6000:]}")
    if completed.stderr.strip():
        _fail(f"{label}がstderrを出力しました: {completed.stderr[-3000:]}")
    return completed.stdout.strip()


def _verify_packet_manifest(config: Mapping[str, Any]) -> dict[str, Any]:
    raw = _identity(config["inputs"]["packet_manifest"], "設計packet manifest")
    manifest = json.loads(raw)
    packet = ROOT / str(config["inputs"]["packet_root"])
    if manifest.get("packet_type") != "COLLECTION_SUPPLY":
        _fail("設計packet typeがCOLLECTION_SUPPLYではありません")
    for row in manifest.get("files", []):
        path = packet / str(row["path"])
        if not path.is_file():
            _fail(f"設計packet fileがありません: {row['path']}")
        body = path.read_bytes()
        if len(body) != int(row["size"]) or _sha(body) != row["sha256"]:
            _fail(f"設計packet file identity不一致: {row['path']}")
    return manifest


def _submission(config: Mapping[str, Any]) -> dict[str, Any]:
    contract = config["inputs"]["submission_zip"]
    raw = _identity(contract, "Collection Supply返却ZIP")
    path = ROOT / str(contract["path"])
    if path.stat().st_mode & 0o222:
        _fail("返却ZIP原本がread-onlyではありません")
    source_bytes: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if names != list(EXPECTED_ZIP_ENTRIES):
                _fail(f"返却ZIP entry inventory不一致: {names}")
            if len(infos) != int(contract["entry_count"]):
                _fail("返却ZIP entry count不一致")
            for info in infos:
                member = Path(info.filename)
                mode = (info.external_attr >> 16) & 0o170000
                if (member.is_absolute() or len(member.parts) != 1
                        or ".." in member.parts or stat.S_ISLNK(mode)
                        or info.is_dir()):
                    _fail(f"返却ZIP unsafe entry: {info.filename!r}")
                source_bytes[info.filename] = archive.read(info)
    except (OSError, zipfile.BadZipFile, RuntimeError) as error:
        _fail(f"返却ZIPを安全に読めません: {error}")

    local = ROOT / ".local"
    local.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="collection-supply-validate-", dir=local) as raw_dir:
        submission = Path(raw_dir)
        for name, body in source_bytes.items():
            (submission / name).write_bytes(body)
        validator = ROOT / str(config["inputs"]["validator"])
        if _sha(validator.read_bytes()) != config["inputs"]["validator_sha256"]:
            _fail("共通submission validator identity不一致")
        stdout = _run([
            sys.executable, str(validator), "--packet-root",
            str(ROOT / str(config["inputs"]["packet_root"])), str(submission),
        ], "Collection Supply返却validator")
        report = json.loads((submission / "VALIDATION_REPORT.json").read_text("utf-8"))
        manifest = json.loads((submission / "SUBMISSION_MANIFEST.json").read_text("utf-8"))
        if report.get("status") != "PASS" or report.get("errors") \
                or report.get("warnings") or report.get("open_questions") != 0:
            _fail(f"返却validator結果不一致: {report}")
        if report.get("submission_fingerprint") != contract["fingerprint"]:
            _fail("返却submission fingerprint不一致")
        for name in ("VALIDATION_REPORT.json", "SUBMISSION_MANIFEST.json"):
            if (submission / name).read_bytes() != source_bytes[name]:
                _fail(f"返却ZIPの生成済みvalidator証跡drift: {name}")
    return {
        "bytes": source_bytes,
        "rows": {
            name: _csv_raw(source_bytes[name], name)
            for name in EXPECTED_ZIP_ENTRIES if name.endswith(".csv")
        },
        "validation": report,
        "manifest": manifest,
        "validator_stdout": stdout,
        "zip_sha256": _sha(raw),
        "zip_size": len(raw),
    }


def _index(rows: Sequence[Mapping[str, str]], key: str, label: str) \
        -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            _fail(f"{label}の{key}が空または重複: {value!r}")
        result[value] = row
    return result


def _resolve_model(config: Mapping[str, Any], submission: Mapping[str, Any]) \
        -> dict[str, Any]:
    inputs = config["inputs"]
    packet = ROOT / str(inputs["packet_root"])
    rows = submission["rows"]
    species_manifest = _index(
        _csv_raw(_identity(inputs["species_manifest"], "species manifest"),
                 "species manifest"), "species_key", "species manifest",
    )
    item_manifest = _index(
        _csv_raw(_identity(inputs["item_manifest"], "item manifest"),
                 "item manifest"), "item_key", "item manifest",
    )
    packet_species = _index(
        _csv_path(packet / "catalogs/species_keys.csv"), "species_key", "packet species",
    )
    item_baseline = _index(
        _csv_path(packet / "catalogs/item_availability_baseline.csv"),
        "item_key", "packet item baseline",
    )
    raid_baseline = _index(
        _csv_path(packet / "catalogs/raid_availability_baseline.csv"),
        "raid_key", "packet raid baseline",
    )
    shared_rows = _csv_raw(
        _identity(inputs["shared_captures"], "shared capture manifest"),
        "shared capture manifest",
    )
    shared_index = {row["shared_capture_key"]: index
                    for index, row in enumerate(shared_rows)}
    if len(shared_index) != int(config["counts"]["shared_captures"]):
        _fail("共有捕獲state count不一致")

    def species(key: str) -> tuple[int, str]:
        if key not in species_manifest or key not in packet_species:
            _fail(f"species key未解決: {key}")
        current = species_manifest[key]
        packet_row = packet_species[key]
        if current["id"] != packet_row["id"]:
            _fail(f"species ID drift: {key}")
        return int(current["id"]), current["display_name"]

    def item(key: str) -> tuple[int, str]:
        if key not in item_manifest or key not in item_baseline:
            _fail(f"item key未解決: {key}")
        current = item_manifest[key]
        baseline = item_baseline[key]
        if current["id"] != baseline["item_id"]:
            _fail(f"item ID drift: {key}")
        return int(current["id"]), current["display_name"]

    form_rows: list[dict[str, Any]] = []
    method_counts: Counter[str] = Counter()
    for source in rows["form_acquisition_plan.csv"]:
        target_id, display = species(source["species_key"])
        base_id, _ = species(source["base_species_key"])
        method = source["acquisition_method"]
        unlock = source["unlock_key"]
        if method not in METHOD_IDS or unlock not in UNLOCK_IDS:
            _fail(f"form enum未解決: {method}/{unlock}")
        distributable = method not in {
            "BATTLE_TRANSFORM_ONLY", "DO_NOT_DISTRIBUTE", "GMAX_FACTOR_ONLY",
        }
        form_rows.append({
            "record_key": source["form_record_key"],
            "species_key": source["species_key"],
            "target_species": target_id,
            "base_species_key": source["base_species_key"],
            "base_species": base_id,
            "display_name": display,
            "method": method,
            "method_id": METHOD_IDS[method],
            "unlock": unlock,
            "unlock_id": UNLOCK_IDS[unlock],
            "distributable": distributable,
            "repeatability": source["repeatability"],
            "collection_policy": source["collection_policy"],
            "status": source["current_target_status"],
        })
        method_counts[method] += 1
    form_index = {row["record_key"]: index for index, row in enumerate(form_rows)}
    if len(form_index) != len(form_rows):
        _fail("form record keyが重複しています")

    gmax_rows: list[dict[str, Any]] = []
    for source in rows["gmax_factor_plan.csv"]:
        if source["form_record_key"] not in form_index:
            _fail(f"G-Max form record未解決: {source['form_record_key']}")
        form = form_rows[form_index[source["form_record_key"]]]
        base_id, base_name = species(source["base_species_key"])
        form_id, _ = species(source["gmax_species_key"])
        if (form["method"] != "GMAX_FACTOR_ONLY"
                or form["target_species"] != form_id or form["base_species"] != base_id):
            _fail(f"G-Max form解決不一致: {source['form_record_key']}")
        gmax_rows.append({
            "record_key": source["form_record_key"],
            "base_species_key": source["base_species_key"],
            "base_species": base_id,
            "form_species": form_id,
            "display_name": base_name,
            "item_key": source["item_key"],
        })

    item_rows: list[dict[str, Any]] = []
    source_counts: Counter[str] = Counter()
    excluded_keys: list[str] = []
    for source in rows["item_availability_plan.csv"]:
        item_id, display = item(source["item_key"])
        supply = source["primary_source_system"]
        unlock = source["unlock_key"]
        repeat = source["repeatability"]
        if supply not in SOURCE_IDS or unlock not in UNLOCK_IDS or repeat not in REPEAT_IDS:
            _fail(f"item enum未解決: {supply}/{unlock}/{repeat}")
        row = {
            "item_key": source["item_key"], "item_id": item_id,
            "display_name": display, "source": supply,
            "source_id": SOURCE_IDS[supply], "unlock": unlock,
            "unlock_id": UNLOCK_IDS[unlock], "repeatability": repeat,
            "repeatability_id": REPEAT_IDS[repeat],
            "price": int(source["price_or_weight"]),
            "quantity": int(source["quantity"]),
            "target_policy": source["target_policy"],
            "secondary_source": source["secondary_source_system"],
        }
        if not 0 <= item_id < int(config["counts"]["items"]):
            _fail(f"item ID範囲外: {source['item_key']}={item_id}")
        if supply == "EXCLUDED":
            excluded_keys.append(source["item_key"])
        item_rows.append(row)
        source_counts[supply] += 1
    item_by_key = {row["item_key"]: row for row in item_rows}
    if len(item_by_key) != len(item_rows):
        _fail("item keyが重複しています")
    dynamax = item_by_key.get("ITEM_KEY_DYNAMAX_CANDY")
    if dynamax is None or dynamax["repeatability"] not in {
        "REPEATABLE", "LIMITED_REPEATABLE",
    }:
        _fail("Dynamax Candyの反復供給がありません")

    service_form_indices = [index for index, row in enumerate(form_rows)
                            if row["method"] == "FORM_CHANGE_SERVICE"]
    wild_form_indices = [index for index, row in enumerate(form_rows)
                         if row["method"] == "WILD_OVERLAY"]
    relic_item_indices = [index for index, row in enumerate(item_rows)
                          if row["source"] == "NPC_GIFT"]
    gifts: list[dict[str, Any]] = []
    fixed_bit = 0
    for index, row in enumerate(form_rows):
        if row["method"] not in {"FIXED_GIFT", "RESEARCH_EGG"}:
            continue
        fixed = row["method"] == "FIXED_GIFT"
        gifts.append({
            "form_index": index, "kind": "FIXED" if fixed else "RESEARCH_EGG",
            "kind_id": 0 if fixed else 1,
            "claim_bit": fixed_bit if fixed else 0,
            "unlock": row["unlock"], "unlock_id": row["unlock_id"],
            "display_name": row["display_name"],
        })
        if fixed:
            fixed_bit += 1

    host_sources = rows["raid_host_plan.csv"]
    configured_hosts = config["physical_hosts"]
    if [row["raid_host_key"] for row in host_sources] \
            != [row["host_key"] for row in configured_hosts]:
        _fail("symbolic host順とphysical host順が一致しません")
    pool_keys = [row["pool_key"] for row in host_sources]
    if len(set(pool_keys)) != len(pool_keys):
        _fail("raid pool keyがhost間で重複しています")
    pool_ids = {key: index for index, key in enumerate(pool_keys)}
    reward_keys = list(dict.fromkeys(row["reward_pool_key"] for row in host_sources))
    reward_ids = {key: index for index, key in enumerate(reward_keys)}

    raid_form_indices = [index for index, row in enumerate(form_rows)
                         if row["method"] == "RAID_CAPTURE"]
    raid_form_capture = {
        form_rows[index]["species_key"]: capture_index
        for capture_index, index in enumerate(raid_form_indices)
    }
    pool_rows: list[dict[str, Any]] = []
    source_raids: list[str] = []
    for source in rows["raid_pool_entries.csv"]:
        species_id, _ = species(source["species_key"])
        source_key = source["source_raid_key"]
        if source["pool_key"] not in pool_ids or source["unlock_key"] not in UNLOCK_IDS:
            _fail(f"raid pool enum未解決: {source['pool_entry_key']}")
        capture_kind = "REPEATABLE"
        capture_index = 0
        reward_once = False
        if source_key != "NONE":
            if source_key not in raid_baseline:
                _fail(f"source raid未解決: {source_key}")
            baseline = raid_baseline[source_key]
            for field in ("species_key", "capture_policy", "unlock_key"):
                if source[field] != baseline[field]:
                    _fail(f"source raid意味契約drift: {source_key}/{field}")
            if int(source["level_min"]) != int(baseline["level"]) \
                    or int(source["level_max"]) != int(baseline["level"]):
                _fail(f"source raid level drift: {source_key}")
            source_raids.append(source_key)
            if baseline["capture_policy"] == "SHARED_ONCE":
                shared_key = baseline["shared_capture_key"]
                if shared_key not in shared_index:
                    _fail(f"shared capture未解決: {shared_key}")
                capture_kind = "SHARED"
                capture_index = shared_index[shared_key]
            reward_once = baseline["reward_repeatability"] == "ONCE"
        elif source["species_key"] in raid_form_capture:
            capture_kind = "FORM"
            capture_index = raid_form_capture[source["species_key"]]
        pool_rows.append({
            "entry_key": source["pool_entry_key"], "source_raid_key": source_key,
            "pool_key": source["pool_key"], "pool_id": pool_ids[source["pool_key"]],
            "tier": source["tier"], "tier_id": TIER_IDS[source["tier"]],
            "species_key": source["species_key"], "species": species_id,
            "gmax_chance": int(source["gmax_factor_chance"]),
            "level_min": int(source["level_min"]),
            "level_max": int(source["level_max"]), "weight": int(source["weight"]),
            "capture_policy": source["capture_policy"],
            "capture_kind": capture_kind,
            "capture_kind_id": {"REPEATABLE": 0, "SHARED": 1, "FORM": 2}[capture_kind],
            "capture_index": capture_index, "reward_once": reward_once,
            "unlock": source["unlock_key"],
            "unlock_id": UNLOCK_IDS[source["unlock_key"]],
        })
    if len(source_raids) != len(set(source_raids)) \
            or set(source_raids) != set(raid_baseline):
        _fail("既存Raid 256行の一意coverageが一致しません")

    reward_rows: list[dict[str, Any]] = []
    for source in rows["raid_reward_entries.csv"]:
        item_id, _ = item(source["item_key"])
        if source["reward_pool_key"] not in reward_ids \
                or source["unlock_key"] not in UNLOCK_IDS:
            _fail(f"raid reward enum未解決: {source['reward_entry_key']}")
        if source["item_key"] in excluded_keys:
            _fail(f"除外itemがRaid報酬へ混入: {source['item_key']}")
        reward_rows.append({
            "entry_key": source["reward_entry_key"],
            "reward_pool_key": source["reward_pool_key"],
            "pool_id": reward_ids[source["reward_pool_key"]],
            "item_key": source["item_key"], "item_id": item_id,
            "quantity_min": int(source["quantity_min"]),
            "quantity_max": int(source["quantity_max"]),
            "weight": int(source["weight"]),
            "first_clear": source["first_clear_guarantee"] == "true",
            "unlock": source["unlock_key"],
            "unlock_id": UNLOCK_IDS[source["unlock_key"]],
        })

    host_rows: list[dict[str, Any]] = []
    for source, physical in zip(host_sources, configured_hosts):
        unlock = source["unlock_key"]
        service = physical["service"]
        if unlock not in UNLOCK_IDS or service not in SERVICE_IDS:
            _fail(f"host enum未解決: {source['raid_host_key']}")
        host_rows.append({
            "host_key": source["raid_host_key"],
            "pool_key": source["pool_key"], "pool_id": pool_ids[source["pool_key"]],
            "reward_pool_key": source["reward_pool_key"],
            "reward_pool_id": reward_ids[source["reward_pool_key"]],
            "unlock": unlock, "unlock_id": UNLOCK_IDS[unlock],
            "service": service, "service_id": SERVICE_IDS[service],
            "high_raid": source["progression_band"] not in {"EARLY", "MID"},
            "physical": dict(physical),
        })

    expected_counts = config["counts"]
    actual_counts = {
        "forms": len(form_rows), "gmax": len(gmax_rows), "items": len(item_rows),
        "hosts": len(host_rows), "pool_entries": len(pool_rows),
        "reward_entries": len(reward_rows),
        "host_requirements": len(rows["host_requirements.csv"]),
        "batches": len(rows["implementation_batches.csv"]),
        "source_raids": len(source_raids),
        "added_gmax_raids": sum(
            row["source_raid_key"] == "NONE" and row["capture_kind"] == "REPEATABLE"
            for row in pool_rows
        ),
        "added_form_raids": sum(row["capture_kind"] == "FORM" for row in pool_rows),
        "shared_captures": len(shared_index),
    }
    if actual_counts != {key: int(value) for key, value in expected_counts.items()}:
        _fail(f"canonical count不一致: {actual_counts} != {expected_counts}")
    expected_methods = {
        "WILD_OVERLAY": 78, "EVOLUTION": 65, "BREEDING_FORM_INHERIT": 3,
        "BATTLE_TRANSFORM_ONLY": 71, "FORM_CHANGE_SERVICE": 95,
        "DO_NOT_DISTRIBUTE": 10, "RESEARCH_EGG": 15, "FIXED_GIFT": 3,
        "KEEP_STAGE26_ROUTE": 10, "RAID_CAPTURE": 4, "GMAX_FACTOR_ONLY": 34,
    }
    if dict(method_counts) != expected_methods:
        _fail(f"form method coverage不一致: {dict(method_counts)}")
    expected_sources = {
        "EXCLUDED": 69, "FACTORY_REWARD": 20, "MONEY_SHOP": 86,
        "RESEARCH_SHOP": 207, "RAID_REWARD": 64, "VEGA_EXISTING": 69,
        "BP_SHOP": 354, "STORY_EVENT": 30, "FORM_SERVICE": 18,
        "NPC_GIFT": 82,
    }
    if dict(source_counts) != expected_sources:
        _fail(f"item source coverage不一致: {dict(source_counts)}")
    gmax_bases = {row["base_species_key"] for row in gmax_rows}
    pool_gmax_bases = {row["species_key"] for row in pool_rows if row["gmax_chance"] > 0}
    if gmax_bases != pool_gmax_bases:
        _fail("全34 G-Max baseのRaid factor chance coverageが一致しません")
    reward_items = {row["item_key"] for row in reward_rows}
    factory_items = {row["item_key"] for row in item_rows
                     if row["source"] == "FACTORY_REWARD"}
    if not factory_items <= reward_items:
        _fail("Factory 20品の補助Raid供給が不足しています")
    if len(service_form_indices) != 95 or len(wild_form_indices) != 78 \
            or len(relic_item_indices) != 82 or len(gifts) != 18:
        _fail("service/gift/wild/relic index coverage不一致")

    return {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "submission_fingerprint": submission["validation"]["submission_fingerprint"],
        "counts": actual_counts,
        "form_method_counts": dict(sorted(method_counts.items())),
        "item_source_counts": dict(sorted(source_counts.items())),
        "enums": {
            "unlocks": UNLOCK_IDS, "methods": METHOD_IDS, "sources": SOURCE_IDS,
            "services": SERVICE_IDS, "tiers": TIER_IDS,
        },
        "forms": form_rows, "gmax": gmax_rows, "items": item_rows,
        "gifts": gifts, "service_form_indices": service_form_indices,
        "wild_form_indices": wild_form_indices,
        "relic_item_indices": relic_item_indices,
        "raid_form_indices": raid_form_indices,
        "hosts": host_rows, "pool_entries": pool_rows,
        "reward_entries": reward_rows,
        "excluded_item_keys": excluded_keys,
        "dynamax_candy_item_id": dynamax["item_id"],
        "coverage": {
            "stage26_completion_target": 1206,
            "stage26_enabling_forms": 10,
            "factory_primary_items_with_raid_supply": len(factory_items),
            "gmax_bases_with_positive_raid_chance": len(pool_gmax_bases),
            "direct_gmax_species_distribution": 0,
            "excluded_items_in_runtime_supply": 0,
        },
    }


def _c_bytes(name: str, raw: bytes) -> str:
    values = ", ".join(f"0x{value:02X}u" for value in raw)
    return f"static const u8 {name}[] = {{{values}}};"


def _menu_text(prefix: str, display: str, mapping: Mapping[str, int],
               tokens: Sequence[str], maximum: int = 23) -> bytes:
    candidate = f"{prefix} {display}"
    while True:
        try:
            encoded = _encode_text(candidate, mapping, tokens)
        except Exception as error:  # RuntimeBuildErrorはprivate helper側の型。
            _fail(f"game textをencodeできません: {candidate!r}: {error}")
        if len(encoded) <= maximum:
            return encoded
        if not display:
            _fail(f"menu textを{maximum} byte以内へ短縮できません: {prefix}")
        display = display[:-1]
        candidate = f"{prefix} {display}"


def _generated_header(config: Mapping[str, Any], model: Mapping[str, Any]) -> bytes:
    mapping, tokens = _charmap(ROOT)
    qol = json.loads(_identity(config["inputs"]["qol_symbols"], "QOL symbols"))
    research = json.loads(_identity(
        config["inputs"]["research_symbols"], "Research symbols",
    ))
    try_save = int(qol["entrypoints"]["VegaQolProduction_OriginalTrySavingData"])
    research_finalize = int(
        research["symbols"]["ResearchEconomy_SaveFinalize"]["address"]
    )
    if try_save != 0x093789E5 or research_finalize != 0x093BDD7D:
        _fail("downstream save symbol identityが期待値と一致しません")

    lines = [
        "#ifndef VEGA_COLLECTION_SUPPLY_V1_GENERATED_H",
        "#define VEGA_COLLECTION_SUPPLY_V1_GENERATED_H",
        "",
    ]
    for name, value in sorted(config["engine"].items()):
        lines.append(
            f"#define COLLECTION_ENGINE_{name.upper()} 0x{_integer(value, name):08X}u"
        )
    for name, hook in sorted(config["hooks"].items()):
        lines.append(
            f"#define COLLECTION_DELEGATE_{name.upper()} "
            f"0x{_integer(hook['delegate'], name + ' delegate'):08X}u"
        )
    lines.extend([
        f"#define COLLECTION_TRY_SAVING_DATA 0x{try_save:08X}u",
        f"#define COLLECTION_RESEARCH_SAVE_FINALIZE 0x{research_finalize:08X}u",
        f"#define COLLECTION_FORM_COUNT {len(model['forms'])}u",
        f"#define COLLECTION_GMAX_COUNT {len(model['gmax'])}u",
        f"#define COLLECTION_ITEM_COUNT {len(model['items'])}u",
        f"#define COLLECTION_HOST_COUNT {len(model['hosts'])}u",
        f"#define COLLECTION_POOL_COUNT {len(model['pool_entries'])}u",
        f"#define COLLECTION_REWARD_COUNT {len(model['reward_entries'])}u",
        f"#define COLLECTION_GIFT_COUNT {len(model['gifts'])}u",
        f"#define COLLECTION_SERVICE_FORM_COUNT {len(model['service_form_indices'])}u",
        f"#define COLLECTION_WILD_FORM_COUNT {len(model['wild_form_indices'])}u",
        f"#define COLLECTION_RELIC_COUNT {len(model['relic_item_indices'])}u",
        f"#define COLLECTION_DYNAMAX_CANDY_ITEM_ID "
        f"{int(model['dynamax_candy_item_id'])}u",
        "",
    ])
    for key, value in UNLOCK_IDS.items():
        lines.append(f"#define COLLECTION_UNLOCK_{UNLOCK_MACROS[key]} {value}u")
    for key, value in METHOD_IDS.items():
        lines.append(f"#define COLLECTION_METHOD_{key} {value}u")
    lines.extend([
        "#define COLLECTION_METHOD_FORM_SERVICE COLLECTION_METHOD_FORM_CHANGE_SERVICE",
        "",
    ])

    text_values = {
        "gCollectionTextRaid": "レイド",
        "gCollectionTextMoney": "ショップ",
        "gCollectionTextBp": "バトルポイント",
        "gCollectionTextResearch": "けんきゅう",
        "gCollectionTextForm": "フォルム",
        "gCollectionTextRelic": "メガ ゼット",
        "gCollectionTextGift": "おくりもの",
        "gCollectionTextGmax": "キョダイマックス",
        "gCollectionTextNext": "つぎ",
        "gCollectionTextCancel": "やめる",
    }
    for name, text in text_values.items():
        lines.append(_c_bytes(name, _encode_text(text, mapping, tokens)))
    lines.append("")

    for index, row in enumerate(model["items"]):
        encoded = _menu_text(f"{int(row['item_id']):03d}", str(row["display_name"]),
                             mapping, tokens)
        lines.append(_c_bytes(f"gCollectionItemName_{index:04d}", encoded))
    for index, row in enumerate(model["forms"]):
        encoded = _menu_text(f"{int(row['target_species']):04d}",
                             str(row["display_name"]), mapping, tokens)
        lines.append(_c_bytes(f"gCollectionFormName_{index:04d}", encoded))
    for index, row in enumerate(model["gifts"]):
        encoded = _menu_text(f"{index + 1:02d}", str(row["display_name"]),
                             mapping, tokens)
        lines.append(_c_bytes(f"gCollectionGiftName_{index:02d}", encoded))

    lines.extend(["", "static const CollectionItemRow gCollectionItemRows[] = {"])
    for index, row in enumerate(model["items"]):
        lines.append(
            "    {%du, %du, %du, %du, %du, %du, gCollectionItemName_%04d},"
            % (row["item_id"], row["price"], row["quantity"], row["source_id"],
               row["unlock_id"], row["repeatability_id"], index)
        )
    lines.extend(["};", "", "static const CollectionFormRow gCollectionFormRows[] = {"])
    for index, row in enumerate(model["forms"]):
        lines.append(
            "    {%du, %du, %du, %du, %du, 0u, gCollectionFormName_%04d},"
            % (row["target_species"], row["base_species"], row["method_id"],
               row["unlock_id"], int(bool(row["distributable"])), index)
        )
    lines.extend(["};", "", "static const CollectionGmaxRow gCollectionGmaxRows[] = {"])
    for row in model["gmax"]:
        lines.append("    {%du, %du}," % (row["base_species"], row["form_species"]))
    lines.extend(["};", "", "static const CollectionGiftRow gCollectionGiftRows[] = {"])
    for index, row in enumerate(model["gifts"]):
        lines.append(
            "    {%du, %du, %du, %du, 0u, gCollectionGiftName_%02d},"
            % (row["form_index"], row["kind_id"], row["claim_bit"],
               row["unlock_id"], index)
        )
    lines.extend(["};", "", "static const CollectionPoolRow gCollectionPoolRows[] = {"])
    for row in model["pool_entries"]:
        lines.append(
            "    {%du, %du, %du, %du, %du, %du, %du, %du, %du, %du, %du, 0u},"
            % (row["species"], row["weight"], row["pool_id"], row["tier_id"],
               row["level_min"], row["level_max"], row["gmax_chance"],
               row["capture_kind_id"], row["capture_index"],
               int(bool(row["reward_once"])), row["unlock_id"])
        )
    lines.extend(["};", "", "static const CollectionRewardRow gCollectionRewardRows[] = {"])
    for row in model["reward_entries"]:
        lines.append(
            "    {%du, %du, %du, %du, %du, %du, %du, 0u},"
            % (row["item_id"], row["weight"], row["pool_id"],
               row["quantity_min"], row["quantity_max"],
               int(bool(row["first_clear"])), row["unlock_id"])
        )
    lines.extend(["};", "", "static const CollectionHostRow gCollectionHostRows[] = {"])
    for row in model["hosts"]:
        lines.append(
            "    {%du, %du, %du, %du, %du, {0u, 0u, 0u}},"
            % (row["pool_id"], row["reward_pool_id"], row["unlock_id"],
               row["service_id"], int(bool(row["high_raid"])))
        )

    def index_array(name: str, values: Sequence[int]) -> None:
        lines.extend(["};", "", f"static const u16 {name}[] = {{"])
        for start in range(0, len(values), 16):
            lines.append("    " + ", ".join(
                f"{int(value)}u" for value in values[start:start + 16]
            ) + ",")

    index_array("gCollectionServiceFormIndices", model["service_form_indices"])
    index_array("gCollectionWildFormIndices", model["wild_form_indices"])
    index_array("gCollectionRelicItemIndices", model["relic_item_indices"])
    lines.extend(["};", "", "#endif", ""])
    return "\n".join(lines).encode("ascii")


def _compile_runtime(load_address: int, header: bytes) \
        -> tuple[bytes, dict[str, int], dict[str, int]]:
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    sources = (
        ROOT / "overlays/collection_supply_v1/collection_supply_v1.c",
        ROOT / "overlays/save_migration/save_migration.c",
        ROOT / "overlays/collection_supply_v1/collection_supply_v1_libc.c",
    )
    if any(not source.is_file() for source in sources):
        _fail("Collection Supply runtime sourceが不足しています")
    with tempfile.TemporaryDirectory(prefix="collection-supply-runtime-",
                                     dir=ROOT / ".local") as raw:
        directory = Path(raw)
        (directory / "collection_supply_v1_generated.h").write_bytes(header)
        objects: list[Path] = []
        for source in sources:
            obj = directory / (source.stem + ".o")
            _run([
                compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os",
                "-std=c11", "-Wall", "-Wextra", "-Werror",
                "-Wno-address-of-packed-member", "-ffreestanding", "-fno-builtin",
                "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
                "-fdata-sections", "-ffunction-sections", "-fno-common",
                "-DVEGA_SAVE_ROM_RUNTIME=1", f"-I{directory}", f"-I{ROOT}",
                "-c", str(source), "-o", str(obj),
            ], f"Collection Supply runtime compile {source.name}")
            objects.append(obj)
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.CollectionSupply_*)) *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "collection_supply_v1.elf"
        binary = directory / "collection_supply_v1.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,CollectionSupply_Probe", f"-Wl,-T,{linker}",
            *(str(path) for path in objects), "-lgcc", "-o", str(elf),
        ], "Collection Supply runtime link")
        undefined = _run([nm, "-u", str(elf)], "Collection Supply undefined audit")
        if undefined:
            _fail(f"Collection Supply undefined symbols: {undefined}")
        symbols: dict[str, int] = {}
        sizes: dict[str, int] = {}
        mutable: list[str] = []
        for line in _run(
            [nm, "-n", "-S", "--defined-only", str(elf)],
            "Collection Supply nm",
        ).splitlines():
            fields = line.split()
            if len(fields) < 4:
                continue
            try:
                address, size = int(fields[0], 16), int(fields[1], 16)
            except ValueError:
                continue
            kind, name = fields[2], fields[3]
            symbols[name], sizes[name] = address, size
            if kind in {"B", "b", "C", "c", "D", "d", "G", "g", "S", "s"}:
                mutable.append(name)
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing or mutable:
            _fail(f"runtime symbol audit不一致: missing={missing}, mutable={mutable}")
        _run([objcopy, "-O", "binary", str(elf), str(binary)],
             "Collection Supply objcopy")
        code = binary.read_bytes()
        if not code or len(code) > 512 * 1024:
            _fail(f"Collection Supply runtime size不正: {len(code)}")
        return code, symbols, sizes


@dataclass(frozen=True)
class _Fixup:
    offset: int
    label: str
    thumb: bool = False


class _Blob:
    def __init__(self) -> None:
        self.data = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[_Fixup] = []

    def align(self, alignment: int = 4, fill: int = 0xFF) -> None:
        if alignment <= 0 or alignment & (alignment - 1):
            _fail("payload alignmentは2の冪でなければなりません")
        while len(self.data) % alignment:
            self.data.append(fill)

    def add(self, label: str, raw: bytes, alignment: int = 4) -> int:
        if label in self.labels:
            _fail(f"payload label重複: {label}")
        self.align(alignment)
        offset = len(self.data)
        self.labels[label] = offset
        self.data.extend(raw)
        return offset

    def pointer(self, offset: int, label: str, *, thumb: bool = False) -> None:
        self.fixups.append(_Fixup(offset, label, thumb))

    def finish(self, payload_offset: int) -> bytes:
        result = bytearray(self.data)
        for fixup in self.fixups:
            if fixup.label not in self.labels:
                _fail(f"payload label未解決: {fixup.label}")
            address = GBA_ROM_BASE + payload_offset + self.labels[fixup.label]
            if fixup.thumb:
                address |= 1
            if fixup.offset < 0 or fixup.offset + 4 > len(result):
                _fail(f"payload pointer fixup範囲外: {fixup.offset:#x}")
            struct.pack_into("<I", result, fixup.offset, address)
        return bytes(result)


@dataclass
class _Script:
    data: bytearray
    fixups: list[tuple[int, str, bool]]
    operations: list[str]

    def __init__(self) -> None:
        self.data = bytearray()
        self.fixups = []
        self.operations = []

    def emit(self, *values: int, operation: str | None = None) -> "_Script":
        self.data.extend(values)
        if operation:
            self.operations.append(operation)
        return self

    def half(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<H", value))
        return self

    def word(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<I", value))
        return self

    def pointer(self, label: str) -> "_Script":
        self.fixups.append((len(self.data), label, False))
        self.data.extend(bytes(4))
        return self

    def setvar(self, variable: int, value: int) -> "_Script":
        self.operations.append(f"setvar:0x{variable:04X}:{value}")
        return self.emit(0x16).half(variable).half(value)

    def callnative(self, address: int, name: str) -> "_Script":
        self.operations.append(f"callnative:{name}")
        return self.emit(0x23).word(address | 1)

    def compare(self, variable: int, value: int) -> "_Script":
        self.operations.append(f"compare:0x{variable:04X}:{value}")
        return self.emit(0x21).half(variable).half(value)

    def compare_result(self, value: int) -> "_Script":
        return self.compare(0x800D, value)

    def branch(self, condition: int, label: str) -> "_Script":
        self.operations.append(f"branch:{condition}:{label}")
        return self.emit(0x06, condition).pointer(label)

    def if_equal(self, label: str) -> "_Script":
        return self.branch(1, label)

    def if_at_least(self, label: str) -> "_Script":
        return self.branch(4, label)

    def goto(self, label: str) -> "_Script":
        self.operations.append(f"goto:{label}")
        return self.emit(0x05).pointer(label)

    def special(self, value: int) -> "_Script":
        self.operations.append(f"special:0x{value:04X}")
        return self.emit(0x25).half(value)

    def waitstate(self) -> "_Script":
        return self.emit(0x27, operation="waitstate")


def _add_script(blob: _Blob, label: str, script: _Script,
                audit: list[dict[str, Any]]) -> None:
    offset = blob.add(label, bytes(script.data), 4)
    for relative, target, thumb in script.fixups:
        blob.pointer(offset + relative, target, thumb=thumb)
    audit.append({
        "label": label, "offset": offset, "size": len(script.data),
        "operations": script.operations,
    })


def _host_scripts(blob: _Blob, symbols: Mapping[str, int], host_count: int) \
        -> list[dict[str, Any]]:
    audit: list[dict[str, Any]] = []
    for host in range(host_count):
        root = f"script::collection_host::{host:02d}"
        wait = root + "::wait"
        form = root + "::form"
        gmax = root + "::gmax"
        raid = root + "::raid"
        battle_wait = root + "::battle_wait"
        finish = root + "::finish"
        _add_script(
            blob, root,
            _Script().emit(0x6A, operation="lock")
            .setvar(0x8004, host)
            .callnative(symbols["CollectionSupply_FieldHost"],
                        "CollectionSupply_FieldHost")
            .compare_result(9).if_equal(wait).goto(finish), audit,
        )
        _add_script(
            blob, wait,
            _Script().waitstate()
            .compare_result(20).if_equal(form)
            .compare_result(21).if_equal(gmax)
            .compare_result(22).if_equal(raid)
            .goto(finish), audit,
        )
        _add_script(
            blob, form,
            _Script().special(0x009F).waitstate()
            .compare(0x8004, 6).if_at_least(finish)
            .callnative(symbols["CollectionSupply_ApplySelectedForm"],
                        "CollectionSupply_ApplySelectedForm")
            .goto(finish), audit,
        )
        _add_script(
            blob, gmax,
            _Script().special(0x009F).waitstate()
            .compare(0x8004, 6).if_at_least(finish)
            .callnative(symbols["CollectionSupply_ApplySelectedGmax"],
                        "CollectionSupply_ApplySelectedGmax")
            .goto(finish), audit,
        )
        _add_script(
            blob, raid,
            _Script().callnative(symbols["CollectionSupply_StartSelectedRaid"],
                                 "CollectionSupply_StartSelectedRaid")
            .compare_result(23).if_equal(battle_wait).goto(finish), audit,
        )
        _add_script(blob, battle_wait, _Script().waitstate().goto(finish), audit)
        _add_script(
            blob, finish,
            _Script().emit(0x6C, 0x02, operation="release_end"), audit,
        )
    return audit


def _map_cell(stage: bytes, group: int, number: int, x: int, y: int) \
        -> dict[str, int]:
    _, header = _map_header_offset(stage, group, number)
    layout = struct.unpack_from("<I", stage, header)[0] - GBA_ROM_BASE
    width, height = struct.unpack_from("<II", stage, layout)
    if not 0 <= x < width or not 0 <= y < height:
        _fail(f"host座標がmap外です: {group}/{number} ({x},{y})")
    blockdata = struct.unpack_from("<I", stage, layout + 12)[0] - GBA_ROM_BASE

    def value_at(px: int, py: int) -> int:
        return struct.unpack_from("<H", stage, blockdata + 2 * (py * width + px))[0]

    value = value_at(x, y)
    adjacent = sum(
        0 <= px < width and 0 <= py < height
        and ((value_at(px, py) >> 10) & 3) == 0
        for px, py in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
    )
    return {
        "width": width, "height": height, "metatile": value & 0x3FF,
        "collision": (value >> 10) & 3, "elevation": (value >> 12) & 0xF,
        "walkable_adjacent_cells": adjacent,
    }


def _host_collision(state: Mapping[str, Any], x: int, y: int) \
        -> list[dict[str, int | str]]:
    result: list[dict[str, int | str]] = []
    for index, raw in enumerate(state["objects"]):
        fields = _object_fields(raw)
        if (int(fields["x"]), int(fields["y"])) == (x, y):
            result.append({"kind": "object", "index": index})
    for kind, size, key in (
        ("warp", 8, "warps_hex"), ("coord", 16, "coords_hex"),
        ("bg", 12, "bg_hex"),
    ):
        raw = bytes.fromhex(str(state[key]))
        for offset in range(0, len(raw), size):
            if struct.unpack_from("<HH", raw, offset) == (x, y):
                result.append({"kind": kind, "index": offset // size})
    return result


def _build_payload(stage: bytes, model: Mapping[str, Any], code: bytes,
                   symbols: Mapping[str, int], payload_offset: int) \
        -> tuple[bytes, dict[str, Any], list[dict[str, Any]]]:
    blob = _Blob()
    if blob.add("payload_header", b"\xFF" * PAYLOAD_HEADER_SIZE, 16) != 0:
        _fail("payload header offset不一致")
    if blob.add("runtime_code", code, 4) != PAYLOAD_HEADER_SIZE:
        _fail("runtime code offset不一致")
    scripts = _host_scripts(blob, symbols, len(model["hosts"]))
    patches: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    seen_maps: set[tuple[int, int]] = set()
    for host_index, host in enumerate(model["hosts"]):
        physical = host["physical"]
        group = int(physical["map_group"])
        number = int(physical["map_num"])
        coordinate = (group, number)
        if coordinate in seen_maps:
            _fail(f"複数hostが同じphysical mapを複製しようとしました: {coordinate}")
        seen_maps.add(coordinate)
        x, y = int(physical["x"]), int(physical["y"])
        state = _stage_map_state(stage, group, number)
        collision = _host_collision(state, x, y)
        cell = _map_cell(stage, group, number, x, y)
        if collision or cell["collision"] != 0 or cell["walkable_adjacent_cells"] < 2:
            _fail(
                f"physical host安全監査不一致: {host['host_key']} "
                f"collision={collision} cell={cell}"
            )
        counts = state["counts"]
        if int(counts["bg"]) >= 255:
            _fail(f"BG event上限超過: {group}/{number}")
        prefix = f"map::{group:02d}::{number:03d}"
        arrays = {
            "objects": b"".join(state["objects"]),
            "warps": bytes.fromhex(str(state["warps_hex"])),
            "coords": bytes.fromhex(str(state["coords_hex"])),
            "bg": bytes.fromhex(str(state["bg_hex"])),
        }
        bg_record = struct.pack("<HHBBHI", x, y, int(physical["elevation"]), 0, 0, 0)
        arrays["bg"] += bg_record
        array_offsets: dict[str, int] = {}
        for name in ("objects", "warps", "coords", "bg"):
            if arrays[name]:
                array_offsets[name] = blob.add(prefix + "::" + name, arrays[name], 4)
        root_label = f"script::collection_host::{host_index:02d}"
        blob.pointer(array_offsets["bg"] + len(arrays["bg"]) - 4, root_label)
        event_raw = struct.pack(
            "<4B4I", int(counts["objects"]), int(counts["warps"]),
            int(counts["coords"]), int(counts["bg"]) + 1, 0, 0, 0, 0,
        )
        event_label = prefix + "::events"
        event_offset = blob.add(event_label, event_raw, 4)
        for pointer_index, name in enumerate(("objects", "warps", "coords", "bg")):
            if name in array_offsets:
                blob.pointer(event_offset + 4 + pointer_index * 4, prefix + "::" + name)
        _, header_offset = _map_header_offset(stage, group, number)
        patches.append({
            "kind": "map_event_header", "host_key": host["host_key"],
            "site": header_offset + 4, "expected": int(state["event_header_address"]),
            "label": event_label, "group": group, "map": number,
        })
        bindings.append({
            "host_index": host_index, "host_key": host["host_key"],
            "region": "TOHOKU" if host_index < 7 else "KANTO",
            "map_group": group, "map_num": number, "x": x, "y": y,
            "elevation": int(physical["elevation"]), "service": host["service"],
            "pool_key": host["pool_key"], "reward_pool_key": host["reward_pool_key"],
            "event_header_before": int(state["event_header_address"]),
            "bg_count_before": int(counts["bg"]),
            "bg_count_after": int(counts["bg"]) + 1,
            "existing_event_collision_count": len(collision),
            "cell": cell, "input_contract": "NORMAL_FIELD_A_ON_BG_EVENT",
            "new_object_count": 0,
        })
    payload = bytearray(blob.finish(payload_offset))
    struct.pack_into(
        "<8s15I", payload, 0, b"VEGACS56", 1, len(payload),
        PAYLOAD_HEADER_SIZE, len(code), len(model["forms"]), len(model["gmax"]),
        len(model["items"]), len(model["hosts"]), len(model["pool_entries"]),
        len(model["reward_entries"]),
        _integer(model["dynamax_candy_item_id"], "Dynamax Candy"),
        _integer(0x0203D900, "owner"), 512, _integer(0x0203F720, "state"), 224,
    )
    base = GBA_ROM_BASE + payload_offset
    for row in scripts:
        row["address"] = base + int(row["offset"])
    for row in bindings:
        event_label = f"map::{row['map_group']:02d}::{row['map_num']:03d}::events"
        row["event_header_after"] = base + blob.labels[event_label]
        row["script_address"] = base + blob.labels[
            f"script::collection_host::{row['host_index']:02d}"
        ]
    return bytes(payload), {
        "labels": {name: base + offset for name, offset in blob.labels.items()},
        "scripts": scripts, "bindings": bindings,
    }, patches


def _previous_requests(previous: Mapping[str, Any]) -> list[dict[str, Any]]:
    if previous.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage55 allocation reportにoverlapがあります")
    return [{
        key: row[key]
        for key in ("name", "region", "size", "alignment", "owner", "purpose",
                    "content_sha256")
    } for row in previous["allocations"]]


def _allocation(previous: Mapping[str, Any], size: int, digest: str) \
        -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME, "region": "integration_modules",
        "size": size, "alignment": 16, "owner": TASK,
        "purpose": "388 form・34 G-Max・999 Item・14 Raid hostのStage56 production runtime",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage56 allocator overlap")
    matches = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage56 payload allocationが一意ではありません")
    return matches[0], report


def _jump_stub(target: int) -> bytes:
    return struct.pack("<HHI", 0x4B00, 0x4718, target | 1)


def _apply_patch(output: bytearray, baseline: bytes, declared: list[dict[str, Any]],
                 site: int, expected: bytes, replacement: bytes,
                 kind: str) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"patch長不一致: {kind}")
    if baseline[site:site + len(expected)] != expected \
            or output[site:site + len(expected)] != expected:
        _fail(f"patch expected bytes不一致: {kind}@0x{site:08X}")
    output[site:site + len(replacement)] = replacement
    row = {
        "kind": kind, "start": site, "end_exclusive": site + len(replacement),
        "expected_hex": expected.hex(), "replacement_hex": replacement.hex(),
    }
    declared.append(row)
    return row


def _layout_audit(config: Mapping[str, Any]) -> dict[str, Any]:
    targets = {
        ("ram", "gCollectionSupplyOwner"),
        ("ram", "gCollectionSupplyVolatileState"),
        ("save", "collection_supply_owner"),
    }
    rows_by_kind = {
        "ram": _csv_path(ROOT / "config/ram_layout.csv"),
        "save": _csv_path(ROOT / "config/save_layout.csv"),
    }
    found: dict[tuple[str, str], Mapping[str, str]] = {}
    overlaps: list[dict[str, Any]] = []
    for kind, rows in rows_by_kind.items():
        for row in rows:
            symbol = row.get("symbol", "")
            key = (kind, symbol)
            if key not in targets:
                continue
            if key in found:
                _fail(f"layout target重複: {key}")
            found[key] = row
            start, end = int(row["start"], 0), int(row["end_exclusive"], 0)
            if end - start != int(row["size"]):
                _fail(f"layout size不一致: {key}")
            for other in rows:
                if other is row or other.get("status") != "LIVE" \
                        or other.get("address_space") != row.get("address_space") \
                        or not other.get("start") or not other.get("end_exclusive"):
                    continue
                other_start = int(other["start"], 0)
                other_end = int(other["end_exclusive"], 0)
                if max(start, other_start) < min(end, other_end):
                    overlaps.append({
                        "target": symbol, "other": other.get("symbol"),
                        "start": max(start, other_start),
                        "end_exclusive": min(end, other_end),
                    })
    if set(found) != targets or overlaps:
        _fail(f"RAM/save owner台帳不一致: found={set(found)} overlaps={overlaps}")
    save = config["save_owner"]
    owner_address = _integer(save["address"], "owner address")
    parasite_offset = _integer(save["parasite_offset"], "parasite offset")
    if (owner_address != 0x0203B0E8 + parasite_offset
            or owner_address - _integer(save["sector_image_address"], "sector image")
            != 0x964):
        _fail("Collection ownerのparasite/sector image対応が不一致")
    return {
        "status": "PASS", "ram_owner_count": 2, "save_owner_count": 1,
        "ram_overlap_count": 0, "save_overlap_count": 0,
        "owner_address": owner_address, "owner_size": int(save["size"]),
        "parasite_offset": parasite_offset, "sector": int(save["sector"]),
        "sector_read_offset": 0x964,
    }


def _stage26_audit(config: Mapping[str, Any], stage55: bytes, output: bytes) \
        -> dict[str, Any]:
    inputs = config["inputs"]
    stage26 = _identity(inputs["stage26_rom"], "Stage26 acquisition ROM")
    metadata = json.loads(_identity(inputs["stage26_metadata"], "Stage26 metadata"))
    allocation = json.loads(_identity(inputs["stage26_allocation"], "Stage26 allocation"))
    package = metadata.get("package_validation", {})
    if package.get("completion_target") != 1206 or package.get("enabling_forms") != 10:
        _fail("Stage26 1,206種＋進化入口10件契約が一致しません")
    names = ("acquisition_runtime", "acquisition_map_scripts")
    spans: list[dict[str, Any]] = []
    for name in names:
        matches = [row for row in allocation["allocations"] if row["name"] == name]
        if len(matches) != 1:
            _fail(f"Stage26 allocationが一意ではありません: {name}")
        row = matches[0]
        start, end = int(row["start"]), int(row["end_exclusive"])
        reference = stage26[start:end]
        current = stage55[start:end]
        if output[start:end] != current or _sha(reference) != row["content_sha256"]:
            _fail(f"Stage26取得runtimeのStage55→56回帰があります: {name}")
        inherited_changes = sum(left != right for left, right in zip(reference, current))
        spans.append({
            "name": name, "start": start, "end_exclusive": end,
            "size": len(reference), "stage26_sha256": _sha(reference),
            "stage55_sha256": _sha(current), "stage56_sha256": _sha(output[start:end]),
            "inherited_post_stage26_changed_bytes": inherited_changes,
            "stage55_to_stage56_changed_bytes": 0,
        })
    return {
        "status": "PASS", "completion_target": 1206, "enabling_forms": 10,
        "stage26_rom_sha256": _sha(stage26), "preserved_spans": spans,
        "preserved_span_count": len(spans), "stage55_to_stage56_changed_bytes": 0,
    }


def _declared_change_audit(before: bytes, after: bytes,
                           spans: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = sorted(
        ({"kind": row["kind"], "start": int(row["start"]),
          "end_exclusive": int(row["end_exclusive"])} for row in spans),
        key=lambda row: (row["start"], row["end_exclusive"]),
    )
    overlap = [
        (left, right) for left, right in zip(ordered, ordered[1:])
        if left["end_exclusive"] > right["start"]
    ]
    if overlap:
        _fail(f"declared ROM span overlap: {overlap[:4]}")
    changed = 0
    outside: list[int] = []
    span_index = 0
    for index, (old, new) in enumerate(zip(before, after)):
        if old == new:
            continue
        changed += 1
        while (span_index < len(ordered)
               and index >= ordered[span_index]["end_exclusive"]):
            span_index += 1
        if (span_index >= len(ordered)
                or index < ordered[span_index]["start"]):
            outside.append(index)
            if len(outside) >= 8:
                break
    if outside:
        _fail("宣言外ROM変更: " + ", ".join(hex(value) for value in outside))
    return {
        "status": "PASS", "changed_byte_count": changed,
        "declared_spans": ordered, "declared_span_count": len(ordered),
        "declared_span_overlap_count": 0, "outside_declared_span_count": 0,
    }


def _static_outputs(config_path: Path) -> dict[str, bytes]:
    config = _read_json(config_path)
    if (config.get("schema_version"), config.get("task"), config.get("stage")) \
            != (1, TASK, STAGE):
        _fail("Collection Supply config root/task/stage不一致")
    _verify_packet_manifest(config)
    submission = _submission(config)
    model = _resolve_model(config, submission)
    header = _generated_header(config, model)
    inputs = config["inputs"]
    stage55 = _identity(inputs["stage55_rom"], "Stage55 ROM")
    metadata55 = json.loads(_identity(inputs["stage55_metadata"], "Stage55 metadata"))
    previous = json.loads(_identity(inputs["stage55_allocation"], "Stage55 allocation"))
    owner_ledger = json.loads(_identity(
        inputs["stage55_owner_ledger"], "Stage55 world owner ledger",
    ))
    clean = _identity(inputs["clean_rom"], "clean FireRed JPN Rev0")
    if len(stage55) != ROM_SIZE or metadata55.get("output", {}).get("sha256") != _sha(stage55):
        _fail("Stage55 metadata/output identity不一致")
    if owner_ledger.get("status") != "PASS" \
            or owner_ledger.get("rom_sha256") != _sha(stage55) \
            or owner_ledger.get("physical_maps") != 678:
        _fail("Stage55 world owner ledger完了identity不一致")

    provisional_code, provisional_symbols, _ = _compile_runtime(
        GBA_ROM_BASE + PAYLOAD_HEADER_SIZE, header,
    )
    provisional_payload, _, _ = _build_payload(
        stage55, model, provisional_code, provisional_symbols, 0,
    )
    allocation, _ = _allocation(previous, len(provisional_payload), "0" * 64)
    payload_offset = int(allocation["start"])
    load_address = GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE
    code, symbols, symbol_sizes = _compile_runtime(load_address, header)
    payload, world, map_patches = _build_payload(
        stage55, model, code, symbols, payload_offset,
    )
    if len(payload) != len(provisional_payload) or len(code) != len(provisional_code):
        _fail("runtime/payload sizeが配置addressで変化しました")
    allocation, allocation_report = _allocation(previous, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("payload hash確定後にallocationが移動しました")
    payload_end = payload_offset + len(payload)
    if stage55[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage56 payload destinationがerased FFではありません")

    output = bytearray(stage55)
    output[payload_offset:payload_end] = payload
    declared: list[dict[str, Any]] = [{
        "kind": "payload::collection_supply_v1",
        "start": payload_offset, "end_exclusive": payload_end,
    }]
    applied_map_patches: list[dict[str, Any]] = []
    for patch in map_patches:
        expected = struct.pack("<I", int(patch["expected"]))
        replacement_address = int(world["labels"][str(patch["label"])])
        applied = _apply_patch(
            output, stage55, declared, int(patch["site"]), expected,
            struct.pack("<I", replacement_address),
            f"map_event_header::{patch['host_key']}",
        )
        applied.update({
            "mode": "ROM_POINTER", "target": replacement_address,
            "host_key": patch["host_key"], "map_group": patch["group"],
            "map_num": patch["map"],
        })
        applied_map_patches.append(applied)

    hook_patches: list[dict[str, Any]] = []
    for name, hook in config["hooks"].items():
        site = _integer(hook["address"], name + " address") - GBA_ROM_BASE
        expected = bytes.fromhex(str(hook["expected_hex"]))
        target_symbol = str(hook["target"])
        target = symbols[target_symbol] | 1
        mode = str(hook["mode"])
        if mode == "THUMB_POINTER":
            replacement = struct.pack("<I", target)
        elif mode == "THUMB_JUMP":
            replacement = _jump_stub(target)
        else:
            _fail(f"hook mode未対応: {name}/{mode}")
        applied = _apply_patch(
            output, stage55, declared, site, expected, replacement,
            f"hook::{name}",
        )
        applied.update({
            "name": name, "mode": mode, "address": site + GBA_ROM_BASE,
            "target_symbol": target_symbol, "target": target,
            "delegate": _integer(hook["delegate"], name + " delegate"),
        })
        hook_patches.append(applied)
    output_raw = bytes(output)
    change_audit = _declared_change_audit(stage55, output_raw, declared)
    layout_audit = _layout_audit(config)
    stage26_audit = _stage26_audit(config, stage55, output_raw)

    downstream = json.loads(_identity(
        inputs["downstream_symbols"], "Windows Box14 vault symbols",
    ))
    downstream_spans = [
        (int(row["address"]) - GBA_ROM_BASE,
         int(row["address"]) - GBA_ROM_BASE
         + len(bytes.fromhex(str(row["replacement_hex"]))))
        for row in downstream.get("patches", [])
    ]
    collection_spans = [(row["start"], row["end_exclusive"])
                        for row in hook_patches]
    hook_overlap = sum(
        max(left[0], right[0]) < min(left[1], right[1])
        for left in collection_spans for right in downstream_spans
    )
    if downstream.get("task") != "T30" or downstream.get("stage") != 47 \
            or hook_overlap != 2:
        _fail("Box14 vault ABI/hook回帰監査不一致")

    incremental = _sparse_bps(stage55, output_raw)
    direct = create_bps(
        clean, output_raw,
        metadata=b"Clean FireRed JPN Rev0 to Stage56 Collection Supply V1",
    )
    if apply_bps(stage55, incremental) != output_raw \
            or apply_bps(clean, direct) != output_raw:
        _fail("Stage56 BPS round-trip不一致")

    runtime = {
        "payload": {
            "offset": payload_offset, "address": GBA_ROM_BASE + payload_offset,
            "size": len(payload), "sha256": _sha(payload),
        },
        "code": {
            "offset": payload_offset + PAYLOAD_HEADER_SIZE,
            "address": load_address, "size": len(code), "sha256": _sha(code),
        },
        "entrypoints": {name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)},
        "symbol_sizes": {name: symbol_sizes[name] for name in sorted(REQUIRED_ENTRYPOINTS)},
        "mutable_symbol_count": 0,
    }
    output_identity = {
        "path": config["outputs"]["rom"], "size": len(output_raw),
        "sha256": _sha(output_raw),
        "crc32": f"{zlib.crc32(output_raw) & 0xFFFFFFFF:08X}",
    }
    validation = {
        "status": "PASS", "zip_sha256": submission["zip_sha256"],
        "zip_size": submission["zip_size"],
        "entry_count": len(submission["bytes"]),
        "submission_fingerprint": model["submission_fingerprint"],
        "open_questions": 0, "warnings": 0, "errors": 0,
        "validator_stdout": submission["validator_stdout"],
    }
    overlap_audit = {
        "status": "PASS", "rom": 0, "ram": 0, "save": 0,
        "hook": 0, "map_host": 0,
    }
    audit = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "PASS_STATIC_MGBA_PENDING",
        "input": {
            "stage55": {"path": inputs["stage55_rom"]["path"],
                        "size": len(stage55), "sha256": _sha(stage55)},
            "submission": validation,
        },
        "output": output_identity, "runtime": runtime,
        "canonical_counts": model["counts"],
        "change_audit": change_audit, "layout_audit": layout_audit,
        "overlap_audit": overlap_audit, "stage26_regression": stage26_audit,
        "world_binding": {
            "status": "PASS", "host_count": len(world["bindings"]),
            "new_object_count": 0, "normal_a_input_count": len(world["bindings"]),
            "existing_event_collision_count": 0,
        },
        "vault_regression": {
            "status": "PASS_STATIC_MGBA_PENDING", "box_count": 14,
            "box14_raw_size": 80, "party_raw_size": 100,
            "vault_runtime_rebound": False,
            "intentional_shared_adapter_chain_count": hook_overlap,
            "conflicting_hook_overlap_count": 0,
            "mail_rejection_owner": "T30", "form_factor_tera_item_bytes_preserved": True,
        },
        "bps": {
            "incremental": {"path": config["outputs"]["incremental_bps"],
                            "size": len(incremental), "sha256": _sha(incremental),
                            "round_trip": True},
            "clean": {"path": config["outputs"]["clean_bps"],
                      "size": len(direct), "sha256": _sha(direct),
                      "round_trip": True},
        },
    }
    coverage = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "PASS_STATIC_MGBA_PENDING", "counts": model["counts"],
        "form_method_counts": model["form_method_counts"],
        "item_source_counts": model["item_source_counts"],
        "coverage": model["coverage"],
        "service_form_rows": len(model["service_form_indices"]),
        "wild_overlay_rows": len(model["wild_form_indices"]),
        "gift_rows": len(model["gifts"]),
        "relic_claim_rows": len(model["relic_item_indices"]),
        "excluded_item_keys": model["excluded_item_keys"],
        "runtime_tables_connected": True,
        "expected_tests": {name: "PENDING" for name in EXPECTED_TESTS},
    }
    world_binding = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": "PASS",
        "rom_sha256": _sha(output_raw), "host_count": len(world["bindings"]),
        "bindings": world["bindings"], "scripts": world["scripts"],
        "map_pointer_patches": applied_map_patches,
        "invariants": {
            "new_maps": 0, "new_objects": 0, "new_full_screen_ui": 0,
            "existing_arrays_preserved_by_copy": True,
            "ordinary_a_input": True, "collision_count": 0,
        },
    }
    symbols_document = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "runtime": runtime["code"], "payload": runtime["payload"],
        "symbols": {
            name: {"address": symbols[name] | 1, "size": symbol_sizes[name]}
            for name in sorted(REQUIRED_ENTRYPOINTS)
        },
        "hooks": hook_patches, "map_patches": applied_map_patches,
        "upstream_vault": downstream,
    }
    money_index = next(index for index, row in enumerate(model["items"])
                       if row["source"] == "MONEY_SHOP")
    bp_index = next(index for index, row in enumerate(model["items"])
                    if row["source"] == "BP_SHOP")
    research_index = next(index for index, row in enumerate(model["items"])
                          if row["source"] == "RESEARCH_SHOP")
    relic_index = model["relic_item_indices"][0]
    form_index = model["service_form_indices"][0]
    fixed_gift_index = next(
        index for index, row in enumerate(model["gifts"])
        if row["kind"] == "FIXED"
    )
    research_egg_index = next(
        index for index, row in enumerate(model["gifts"])
        if row["kind"] == "RESEARCH_EGG"
    )
    selected = {
        "money_index": money_index,
        "money_item": model["items"][money_index]["item_id"],
        "money_price": model["items"][money_index]["price"],
        "money_quantity": model["items"][money_index]["quantity"],
        "bp_index": bp_index,
        "bp_item": model["items"][bp_index]["item_id"],
        "bp_price": model["items"][bp_index]["price"],
        "bp_quantity": model["items"][bp_index]["quantity"],
        "research_index": research_index,
        "research_item": model["items"][research_index]["item_id"],
        "research_price": model["items"][research_index]["price"],
        "research_quantity": model["items"][research_index]["quantity"],
        "relic_index": relic_index,
        "relic_item": model["items"][relic_index]["item_id"],
        "form_index": form_index,
        "form_base": model["forms"][form_index]["base_species"],
        "form_target": model["forms"][form_index]["target_species"],
        "fixed_gift_index": fixed_gift_index,
        "fixed_gift_species": model["forms"][
            model["gifts"][fixed_gift_index]["form_index"]
        ]["target_species"],
        "research_egg_index": research_egg_index,
        "research_egg_species": model["forms"][
            model["gifts"][research_egg_index]["form_index"]
        ]["target_species"],
        "gmax_base": model["gmax"][0]["base_species"],
        "dynamax_candy_item": model["dynamax_candy_item_id"],
        "gmax_host": 6,
        "raid_retry_host": 1,
    }
    world_fixture: dict[str, int] = {}
    for index, (binding, patch) in enumerate(zip(
            world["bindings"], applied_map_patches, strict=True)):
        prefix = f"map_{index:02d}_"
        world_fixture[prefix + "site"] = GBA_ROM_BASE + int(patch["start"])
        world_fixture[prefix + "target"] = int(patch["target"])
        world_fixture[prefix + "bg_count"] = int(binding["bg_count_after"])
        world_fixture[prefix + "x"] = int(binding["x"])
        world_fixture[prefix + "y"] = int(binding["y"])
        world_fixture[prefix + "elevation"] = int(binding["elevation"])
    cases = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "rom_sha256": _sha(output_raw), "runtime": runtime,
        "owner": config["save_owner"], "ram": config["ram"],
        "canonical_counts": model["counts"],
        "selected_fixtures": selected,
        "world_fixtures": world_fixture,
        "stage55_world_fixture_count": 22,
        "stage55_world_process_count": 2,
        "expected_tests": list(coverage["expected_tests"]),
        "quick_iterations": 1, "full_iterations": 8,
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "PASS_STATIC_MGBA_PENDING",
        "input": audit["input"], "output": output_identity,
        "runtime": runtime, "allocation": allocation,
        "hooks": hook_patches, "map_patches": applied_map_patches,
        "change_audit": change_audit, "overlap_audit": overlap_audit,
        "canonical_counts": model["counts"],
        "mgba": {"status": "PENDING", "process_count": 0},
    }
    outputs = config["outputs"]
    return {
        outputs["rom"]: output_raw,
        outputs["metadata"]: _stable(metadata),
        outputs["allocation"]: _stable(allocation_report),
        outputs["incremental_bps"]: incremental,
        outputs["clean_bps"]: direct,
        outputs["model"]: _stable(model),
        outputs["generated_header"]: header,
        outputs["runtime"]: code,
        outputs["symbols"]: _stable(symbols_document),
        outputs["cases"]: _stable(cases),
        outputs["audit"]: _stable(audit),
        outputs["coverage"]: _stable(coverage),
        outputs["world_binding"]: _stable(world_binding),
    }


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _validate_mgba_document(
    document: Mapping[str, Any], mode: str, identities: Mapping[str, str],
) -> None:
    tests = document.get("tests")
    coverage = document.get("coverage")
    expected_coverage = {
        "forms": 388, "gmax": 34, "items": 999, "hosts": 14,
        "pool_entries": 292, "reward_entries": 217,
        "vault_batch": 30, "raw_record_bytes": 80,
    }
    if (
        document.get("schema_version") != 1
        or document.get("task") != TASK
        or document.get("stage") != STAGE
        or document.get("mode") != mode
        or document.get("status") != "PASS"
        or document.get("result_identity")
            != "CSV56:388:34:999:14:292:217:raw80x30"
        or any(document.get(key) != value
               for key, value in identities.items())
        or not isinstance(tests, dict)
        or tuple(tests) != EXPECTED_TESTS
        or any(value is not True for value in tests.values())
        or document.get("total") != len(EXPECTED_TESTS)
        or document.get("warnings") != 0
        or document.get("warnings_errors") != 0
        or coverage != expected_coverage
    ):
        _fail(f"Collection Supply mGBA {mode} exact all-PASS不一致")


def _finalize_outputs(
    config_path: Path, static: Mapping[str, bytes],
) -> dict[str, bytes]:
    """Stage56 exact ROMをquick/fullとStage55自然入力回帰で確定する。"""
    config = _read_json(config_path)
    paths = config["outputs"]
    runner = ROOT / "tools/mgba_collection_supply_v1_smoke.c"
    if not runner.is_file():
        _fail("Collection Supply mGBA runnerがありません")
    source_identities = {
        "rom_sha256": _sha(static[paths["rom"]]),
        "runner_sha256": _sha(runner.read_bytes()),
        "symbols_sha256": _sha(static[paths["symbols"]]),
        "cases_sha256": _sha(static[paths["cases"]]),
    }
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    documents: dict[str, dict[str, Any]] = {}
    finalized = dict(static)
    with tempfile.TemporaryDirectory(
        prefix="vega-collection-supply-v1-mgba-", dir=local,
    ) as raw:
        directory = Path(raw)
        executable = directory / "mgba-collection-supply-v1"
        rom = directory / "stage56.gba"
        symbols = directory / "symbols.json"
        cases = directory / "cases.json"
        rom.write_bytes(static[paths["rom"]])
        symbols.write_bytes(static[paths["symbols"]])
        cases.write_bytes(static[paths["cases"]])
        _run([
            _host_cc(ROOT), "-std=c11", "-O2", "-Wall", "-Wextra",
            "-Werror", str(runner), "-o", str(executable), "-lmgba",
        ], "Collection Supply libmGBA compile", timeout=120)
        executable_identities = {
            **source_identities,
            "runner_sha256": _sha(executable.read_bytes()),
        }
        for mode, output_key, timeout in (
            ("quick", "mgba_quick", 600),
            ("full", "mgba_full", 1200),
        ):
            save = directory / f"{mode}.sav"
            stdout = _run([
                str(executable), str(rom), str(symbols), str(cases), mode,
                str(save),
            ], f"Collection Supply mGBA {mode}", timeout=timeout)
            try:
                document = json.loads(stdout)
            except json.JSONDecodeError as error:
                _fail(f"Collection Supply mGBA {mode} JSON不正: {error}")
            if not isinstance(document, dict):
                _fail(f"Collection Supply mGBA {mode} root不一致")
            _validate_mgba_document(document, mode, executable_identities)
            document["runner_sha256"] = source_identities["runner_sha256"]
            document["process_runs"] = 1
            document["fixture"] = "collection_supply_v1_stage56_exact_rom"
            documents[mode] = document
            finalized[paths[output_key]] = _stable(document)
    quick, full = documents["quick"], documents["full"]
    for key in (
        "result_identity", "rom_sha256", "runner_sha256",
        "symbols_sha256", "cases_sha256", "tests", "coverage",
    ):
        if quick[key] != full[key]:
            _fail(f"Collection Supply mGBA quick/full {key}不一致")

    from scripts.build_world_runtime_e2e_repair import (  # noqa: PLC0415
        _world_input_e2e,
    )
    world_input = _world_input_e2e(static[paths["rom"]])
    if (world_input.get("status") != "PASS"
            or world_input.get("process_runs") != 2
            or world_input.get("fixture_count") != 22
            or world_input.get("warnings") != 0):
        _fail("Stage56上のStage55 world自然入力回帰不一致")
    mgba = {
        "status": "PASS", "process_count": 2,
        "result_identity": quick["result_identity"],
        "identity_checks": {
            "independent_processes": True,
            "quick_full_equal": True,
            "warnings_zero": True,
        },
        "quick": {"path": paths["mgba_quick"],
                  "tests": quick["tests"], "coverage": quick["coverage"]},
        "full": {"path": paths["mgba_full"],
                 "tests": full["tests"], "coverage": full["coverage"]},
    }
    for output_key in ("metadata", "audit", "coverage"):
        document = json.loads(static[paths[output_key]])
        document["status"] = "PASS"
        document["mgba"] = mgba
        document["world_input_e2e"] = world_input
        if output_key == "audit":
            document["vault_regression"]["status"] = "PASS"
            document["vault_regression"].update({
                "batch_size": 30,
                "round_trip_and_reload": True,
                "mail_rejection": True,
                "raw80_exact": True,
            })
        if output_key == "coverage":
            document["expected_tests"] = {
                name: "PASS" for name in EXPECTED_TESTS
            }
        finalized[paths[output_key]] = _stable(document)
    return finalized


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    drift = [relative for relative, raw in outputs.items()
             if not (ROOT / relative).is_file()
             or (ROOT / relative).read_bytes() != raw]
    if drift:
        _fail("Stage56生成物drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    try:
        static = _static_outputs(args.config)
        second = _static_outputs(args.config)
        if static != second:
            _fail("Stage56 static buildがbyte deterministicではありません")
        outputs = static if args.static_only else _finalize_outputs(
            args.config, static,
        )
        if args.mode == "build":
            _write_outputs(outputs)
        else:
            _check_outputs(outputs)
    except (OSError, ValueError, KeyError, TypeError, struct.error,
            json.JSONDecodeError, subprocess.SubprocessError,
            CollectionSupplyBuildError) as error:
        print(f"Collection Supply Stage56 {args.mode} failed: {error}", file=sys.stderr)
        return 1
    config = _read_json(args.config)
    metadata = json.loads(outputs[config["outputs"]["metadata"]])
    print(
        "Collection Supply Stage56 %s: %s sha256=%s crc32=%s artifacts=%d"
        % (args.mode, metadata["status"], metadata["output"]["sha256"],
           metadata["output"]["crc32"], len(outputs))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
