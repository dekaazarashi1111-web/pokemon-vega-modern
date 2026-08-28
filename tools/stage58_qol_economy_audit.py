#!/usr/bin/env python3
"""Stage57のQOL道具・通貨・供給ownerをStage58向けに決定論監査する。

この監査は「manifestに存在する」「購入できる」だけを実使用PASSにしない。
Stage36/40/56のproduction証跡、Stage57 exact ROMまたはidentityをmetadataで固定した
post-Stage57 ROMのitem callbackと供給table、通常売値を突き合わせ、
取得→効果→取消/失敗→通常save再読込の証明深度を返す。
ROMは読み取り専用で、修正はexpected/replacement byteを持つpatch planとして返す。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
STAGE57_ROM = Path("build/stages/57_comprehensive_debug_repair.gba")
STAGE57_SHA256 = "546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d"
STAGE57_SIZE = 32 * 1024 * 1024
ROM_BASE = 0x08000000

# T06 canonical item table and the two production supply tables are rooted in
# Stage57.  Addresses are revalidated against row contents before reporting.
ITEM_TABLE = 0x0904D108
ITEM_STRIDE = 40
ITEM_FIELD_CALLBACK_OFFSET = 24
QOL_SUPPLY_TABLE = 0x09381412
QOL_SUPPLY_STRIDE = 8
COLLECTION_REWARD_TABLE = 0x09408486
COLLECTION_REWARD_STRIDE = 10
COLLECTION_ITEM_TABLE = 0x0940B088
COLLECTION_ITEM_STRIDE = 12

COLLECTION_SOURCE_MONEY = 0
COLLECTION_SOURCE_BP = 1
COLLECTION_SOURCE_EXISTING = 8
COLLECTION_UNLOCK_PRE_ENTRY = 1
COLLECTION_UNLOCK_KANTO_EARLY = 5

EXPECTED_EFFECT_CALLBACKS = {
    "EXP_CANDY": 0x093777C9,
    "EV_RESET": 0x093777C9,
    "ABILITY": 0x09123731,
    "MINT": 0x091238A1,
    "HYPER_SERVICE_ITEM": 0x080A34F9,
}

EXP_CANDIES = (
    "ITEM_KEY_EXP_CANDY_XS", "ITEM_KEY_EXP_CANDY_S",
    "ITEM_KEY_EXP_CANDY_M", "ITEM_KEY_EXP_CANDY_L",
    "ITEM_KEY_EXP_CANDY_XL",
)
ABILITY_ITEMS = ("ITEM_KEY_ABILITY_CAPSULE", "ITEM_KEY_ABILITY_PATCH")
HYPER_ITEMS = ("ITEM_KEY_BOTTLE_CAP", "ITEM_KEY_GOLD_BOTTLE_CAP")
EV_RESET_ITEMS = (
    "ITEM_KEY_EV_RESET_HP", "ITEM_KEY_EV_RESET_ATK",
    "ITEM_KEY_EV_RESET_DEF", "ITEM_KEY_EV_RESET_SPEED",
    "ITEM_KEY_EV_RESET_SPATK", "ITEM_KEY_EV_RESET_SPDEF",
)

REQUIRED_STAGE58_VERIFICATION_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "QOL_EFFECTS_36",
        "domain": "qol_items",
        "tests": ["cancel_no_consume_36", "effect_and_consume_36",
                  "ineligible_no_consume_36"],
    },
    {
        "id": "QOL_NORMAL_BAG_UI_5_FAMILIES",
        "domain": "qol_items",
        "tests": ["normal_bag_ui_family_paths"],
    },
    {
        "id": "QOL_EFFECT_FRESH_RELOAD_36",
        "domain": "qol_items",
        "tests": ["fresh_core_effect_records_36", "fresh_core_bag_counts_36"],
    },
    {
        "id": "T19_ABILITY_PATCH_TRANSACTION",
        "domain": "economy",
        "tests": ["normal_menu_cancel_no_mutation", "bag_full_no_debit",
                  "insufficient_no_mutation", "cross_store_fault_rollback",
                  "limited_repeatable_reopen"],
    },
    {
        "id": "LOW_RAID_XS_UNLOCK_RUNTIME",
        "domain": "economy",
        "tests": ["low_raid_xs_unlock_runtime"],
    },
    {
        "id": "COLLECTION_QOL_OWNER_47_RUNTIME",
        "domain": "economy",
        "tests": ["collection_qol_owner_47_runtime"],
    },
    {
        "id": "HONEY_NO_ARBITRAGE_RUNTIME",
        "domain": "economy",
        "tests": ["honey_buy_sell_no_profit_runtime"],
    },
    {
        "id": "RESEARCH_RATE_71_RUNTIME",
        "domain": "economy",
        "tests": ["research_rate_71_runtime"],
    },
    {
        "id": "ACTUAL_TRAINER_FACTORY_EARN_PURCHASE_RELOAD",
        "domain": "economy",
        "tests": [
            "normal_trainer_victory_prize_honey_normal_save_phase1",
            "factory_prepare_real_battles_bp_patch_normal_save_phase1",
            "fresh_process_trainer_prize_honey_reload",
            "fresh_process_factory_reward_ability_patch_reload",
        ],
    },
    {
        "id": "CODEX_MART_BAG_FULL_NO_DEBIT",
        "domain": "convenience",
        "tests": ["mart_bag_full_no_charge"],
    },
)


class AuditError(RuntimeError):
    """入力identityまたはtable契約が壊れている。"""


@dataclass(frozen=True)
class PatchSpec:
    key: str
    address: int
    expected: bytes
    replacement: bytes
    priority: str
    reason: str
    projected_result: str

    def as_dict(self, state: str) -> dict[str, Any]:
        return {
            "key": self.key,
            "address": f"0x{self.address:08X}",
            "end_exclusive": f"0x{self.address + len(self.expected):08X}",
            "expected_hex": self.expected.hex(),
            "replacement_hex": self.replacement.hex(),
            "priority": self.priority,
            "reason": self.reason,
            "projected_result": self.projected_result,
            "state": state,
        }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AuditError(f"JSON root must be object: {path}")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rom_offset(address: int, size: int, rom_size: int) -> int:
    offset = address - ROM_BASE
    if offset < 0 or offset + size > rom_size:
        raise AuditError(f"ROM address out of range: 0x{address:08X}+{size}")
    return offset


def _slice(rom: bytes, address: int, size: int) -> bytes:
    offset = _rom_offset(address, size, len(rom))
    return rom[offset:offset + size]


def _item_id_rows(root: Path) -> tuple[dict[str, dict[str, str]], dict[int, dict[str, str]]]:
    rows = _read_csv(root / "manifests/item_ids.csv")
    by_key = {row["item_key"]: row for row in rows}
    by_id = {int(row["id"]): row for row in rows}
    if len(by_key) != 999 or len(by_id) != 999:
        raise AuditError("item manifest must contain 999 unique rows")
    return by_key, by_id


def _mint_keys(items: Mapping[str, Mapping[str, str]]) -> tuple[str, ...]:
    values = sorted(
        key for key, row in items.items()
        if row["item_type_key"] == "ITEM_TYPE_MINT"
    )
    if len(values) != 21:
        raise AuditError(f"nature mint count differs: {len(values)}")
    return tuple(values)


def _effect_kind(key: str, mint_keys: Sequence[str]) -> str:
    if key in EXP_CANDIES:
        return "EXP_CANDY"
    if key in EV_RESET_ITEMS:
        return "EV_RESET"
    if key in ABILITY_ITEMS:
        return "ABILITY"
    if key in mint_keys:
        return "MINT"
    if key in HYPER_ITEMS:
        return "HYPER_SERVICE_ITEM"
    raise AuditError(f"unknown effect item: {key}")


def _patch_state(rom: bytes, spec: PatchSpec) -> str:
    current = _slice(rom, spec.address, len(spec.expected))
    if current == spec.expected:
        return "PENDING"
    if current == spec.replacement:
        return "APPLIED"
    raise AuditError(
        f"patch site drift {spec.key} at 0x{spec.address:08X}: "
        f"{current.hex()} not {spec.expected.hex()}/{spec.replacement.hex()}"
    )


def _assert_non_overlapping(specs: Sequence[PatchSpec]) -> None:
    spans = sorted((s.address, s.address + len(s.expected), s.key) for s in specs)
    for left, right in zip(spans, spans[1:]):
        if left[1] > right[0]:
            raise AuditError(f"patch overlap: {left[2]} / {right[2]}")


def _price_summary(values: Sequence[int]) -> dict[str, int | float]:
    if not values:
        raise AuditError("price summary input is empty")
    ordered = sorted(values)
    middle = len(ordered) // 2
    median: int | float
    if len(ordered) % 2:
        median = ordered[middle]
    else:
        median = (ordered[middle - 1] + ordered[middle]) / 2
    return {
        "count": len(ordered), "minimum": ordered[0],
        "median": median, "maximum": ordered[-1], "total": sum(ordered),
    }


def _maximum_money_for_budget(
    rows: Iterable[tuple[int, int]], budget: int,
) -> int:
    """反復購入可能な(price, sell yield)でbudget内の最大換金額を返す。"""
    entries = tuple(rows)
    best = [0] * (budget + 1)
    for spent in range(1, budget + 1):
        best[spent] = max(
            (best[spent - price] + yield_money
             for price, yield_money in entries if price <= spent),
            default=0,
        )
    return best[budget]


def _source_registry(
    root: Path,
    item_rows: Mapping[str, Mapping[str, str]],
    collection: Mapping[str, Any],
    collection_live: Mapping[int, Mapping[str, int]],
) -> dict[str, list[dict[str, Any]]]:
    sources: dict[str, list[dict[str, Any]]] = {key: [] for key in item_rows}

    for row in _read_csv(root / "config/qol_production_supply_catalog.csv"):
        sources[row["item_key"]].append({
            "owner": "T19_QOL_BP_SHOP", "currency": "BP",
            "price": int(row["price_bp"]), "quantity": 1,
            "unlock": row["unlock_feature"],
            "repeatability": row["repeatability"],
        })
    for row in _read_csv(root / "manifests/qol_rewards.csv"):
        if row["status"] != "ACTIVE" or row["item_key"] == "ITEM_KEY_NONE":
            continue
        sources[row["item_key"]].append({
            "owner": "QOL_REWARD_MANIFEST", "currency": row["currency_key"],
            "price": int(row["price"]), "quantity": int(row["quantity"]),
            "unlock": row["unlock_key"], "repeatability": row["repeatability"],
        })
    for row in _read_csv(root / "manifests/facility_rewards.csv"):
        if row["status"] != "ACTIVE" or row["item_key"] == "ITEM_KEY_NONE":
            continue
        sources[row["item_key"]].append({
            "owner": "FACTORY_REWARD_OR_BP_SHOP",
            "currency": row["currency_key"],
            "price": -int(row["amount"]) if int(row["amount"]) < 0 else 0,
            "quantity": int(row["quantity"]), "unlock": row["unlock_key"],
            "repeatability": row["repeatability"],
            "trigger": row["trigger_kind"],
        })
    research = _read_json(root / "generated/runtime/research_economy_v1_mgba_cases.json")
    by_id = {int(row["id"]): key for key, row in item_rows.items()}
    for row in research["shop"]:
        key = by_id[int(row["item_id"])]
        sources[key].append({
            "owner": "T23_RESEARCH_SHOP", "currency": "RESEARCH",
            "price": int(row["price"]), "quantity": int(row["quantity"]),
            "unlock": row["unlock_key"],
            "repeatability": "DAILY_LIMITED" if int(row["daily_limit"]) else "REPEATABLE",
            "daily_limit": int(row["daily_limit"]),
        })
    for row in collection["items"]:
        item_id = int(row["item_id"])
        live = collection_live[item_id]
        if live["source"] in (COLLECTION_SOURCE_MONEY, COLLECTION_SOURCE_BP):
            sources[row["item_key"]].append({
                "owner": "STAGE56_COLLECTION_PRIMARY",
                "currency": "MONEY" if live["source"] == 0 else "BP",
                "price": live["price"], "quantity": live["quantity"],
                "unlock": row["unlock"], "repeatability": row["repeatability"],
            })
    for row in collection["reward_entries"]:
        sources[row["item_key"]].append({
            "owner": "STAGE56_COLLECTION_RAID", "currency": "RAID_CLEAR",
            "price": 0, "quantity": [int(row["quantity_min"]), int(row["quantity_max"])],
            "unlock": row["unlock"], "repeatability": "REPEATABLE",
            "weight": int(row["weight"]), "pool": row["reward_pool_key"],
        })
    for row in _read_csv(root / "manifests/kanto_items.csv"):
        if row["status"] != "ACTIVE":
            continue
        sources[row["item_key"]].append({
            "owner": "T16_KANTO_FIELD_ITEM", "currency": "EXPLORATION",
            "price": 0, "quantity": int(row["quantity"]),
            "unlock": row["unlock_key"], "repeatability": row["repeatability"],
        })
    return sources


def _existing_validation(root: Path) -> dict[str, Any]:
    paths = {
        "stage36_quick": "build/stages/36_mgba_qol_production_quick.json",
        "stage36_full": "build/stages/36_mgba_qol_production_full.json",
        "stage40": "build/stages/40_research_economy_v1.json",
        "stage40_full": "build/stages/40_mgba_research_economy_v1_full.json",
        "stage56": "build/stages/56_collection_supply_v1.json",
        "stage56_full": "build/stages/56_mgba_collection_supply_v1_full.json",
        "stage57": "build/stages/57_comprehensive_debug_repair.json",
    }
    result: dict[str, Any] = {}
    for key, relative in paths.items():
        value = _read_json(root / relative)
        if value.get("status") != "PASS":
            raise AuditError(f"upstream evidence is not PASS: {relative}")
        result[key] = {
            "path": relative,
            "status": value["status"],
            "mgba_status": value.get("mgba", {}).get("status", value.get("status")),
        }
    q36 = _read_json(root / paths["stage36_quick"])
    f36 = _read_json(root / paths["stage36_full"])
    required = {
        "supply_once_repeat", "quantity_consumers", "training_atomic",
        "cross_store_fault_injection", "fresh_core_save_reload",
    }
    for value, name in ((q36, "quick"), (f36, "full")):
        missing = sorted(k for k in required if value["checks"].get(k) is not True)
        if missing:
            raise AuditError(f"Stage36 {name} evidence missing: {missing}")
    result["stage36_scope_limit"] = (
        "fresh_core_save_reloadはQOL ledger/設定の保存を証明するが、"
        "道具使用後のparty能力/経験値/EV/nature mutation再読込との同一caseではない"
    )
    research_full = _read_json(root / paths["stage40_full"])
    collection_full = _read_json(root / paths["stage56_full"])
    required_research = {
        "activity_day_caps", "shop_23_atomic_stock", "pending_fault_recovery",
    }
    required_collection = {
        "money_bp_research_and_relic_transactions",
        "owner_crc_and_sector31_restore", "raid_rotation_capture_reward_and_retry",
    }
    missing_research = sorted(
        key for key in required_research if research_full["tests"].get(key) is not True
    )
    missing_collection = sorted(
        key for key in required_collection
        if collection_full["tests"].get(key) is not True
    )
    if missing_research or missing_collection:
        raise AuditError(
            f"transaction evidence missing: research={missing_research}, "
            f"collection={missing_collection}"
        )
    return result


def build_audit(
    root: Path = ROOT,
    rom_path: Path | None = None,
    *,
    require_stage57_identity: bool = True,
    rom_bytes: bytes | None = None,
    hyper_service_item_callback: int | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    rom_file = (root / STAGE57_ROM) if rom_path is None else rom_path.resolve()
    if rom_bytes is not None and rom_path is not None:
        raise AuditError("rom_pathとrom_bytesは同時指定できません")
    rom = rom_file.read_bytes() if rom_bytes is None else bytes(rom_bytes)
    rom_sha = _sha256(rom)
    if len(rom) != STAGE57_SIZE:
        raise AuditError(f"Stage57 ROM size differs: {len(rom)}")
    if require_stage57_identity and rom_sha != STAGE57_SHA256:
        raise AuditError(f"Stage57 ROM SHA-256 differs: {rom_sha}")
    if hyper_service_item_callback is not None:
        if require_stage57_identity:
            raise AuditError(
                "Stage57 identity監査ではhyper service callback overrideを許可しません"
            )
        if (
            hyper_service_item_callback & 1 == 0
            or not ROM_BASE <= (hyper_service_item_callback & ~1)
            < ROM_BASE + len(rom)
        ):
            raise AuditError(
                "hyper service callback override must be a Thumb ROM pointer"
            )

    item_rows, by_id = _item_id_rows(root)
    mint_keys = _mint_keys(item_rows)
    effect_keys = EXP_CANDIES + ABILITY_ITEMS + mint_keys + EV_RESET_ITEMS + HYPER_ITEMS
    if len(effect_keys) != 36 or len(set(effect_keys)) != 36:
        raise AuditError("effect item set must contain 36 unique rows")

    collection = _read_json(root / "content/collection_supply_v1/canonical_model.json")
    if collection.get("counts", {}).get("items") != 999:
        raise AuditError("Collection item model differs from 999 rows")
    collection_by_id = {int(row["item_id"]): row for row in collection["items"]}
    if len(collection_by_id) != 999:
        raise AuditError("Collection item rows must be ID-complete")

    collection_live: dict[int, dict[str, int]] = {}
    for item_id in range(999):
        address = COLLECTION_ITEM_TABLE + item_id * COLLECTION_ITEM_STRIDE
        raw = _slice(rom, address, COLLECTION_ITEM_STRIDE)
        live_id, price, quantity, source, unlock, repeatability, _name = struct.unpack(
            "<HHBBBBI", raw
        )
        if live_id != item_id:
            raise AuditError(f"Collection item row ID drift at {item_id}: {live_id}")
        model = collection_by_id[item_id]
        if quantity != int(model["quantity"]) or unlock != int(model["unlock_id"]):
            raise AuditError(f"Collection item ABI drift at {item_id}")
        collection_live[item_id] = {
            "address": address, "price": price, "quantity": quantity,
            "source": source, "unlock": unlock, "repeatability": repeatability,
        }

    qol_catalog = _read_csv(root / "config/qol_production_supply_catalog.csv")
    if len(qol_catalog) != 49:
        raise AuditError("QOL production catalog differs from 49 rows")
    qol_catalog_by_key = {row["item_key"]: row for row in qol_catalog}
    if len(qol_catalog_by_key) != 49:
        raise AuditError("QOL production catalog contains duplicate item keys")
    research_cases = _read_json(
        root / "generated/runtime/research_economy_v1_mgba_cases.json"
    )
    research_shop = research_cases["shop"]
    research_daily_cap = sum(
        int(row["daily_cap"]) for row in research_cases["activities"]
    )

    patch_specs: list[PatchSpec] = []
    duplicate_keys: list[str] = []
    for row in qol_catalog:
        item = item_rows[row["item_key"]]
        item_id = int(item["id"])
        live = collection_live[item_id]
        # canonical Stage56でBP_SHOPだった行をowner移行対象として固定する。
        # live byteだけで選ぶとpatch後の再監査でAPPLIED行が消えるため不可。
        if int(collection_by_id[item_id]["source_id"]) != COLLECTION_SOURCE_BP:
            continue
        duplicate_keys.append(row["item_key"])
        patch_specs.append(PatchSpec(
            key=f"COLLECTION_QOL_OWNER_{row['item_key']}",
            address=live["address"] + 5,
            expected=bytes((COLLECTION_SOURCE_BP,)),
            replacement=bytes((COLLECTION_SOURCE_EXISTING,)),
            priority="P0",
            reason=(
                "T19 QOL BP shopがproduction ownerのため、Collection側の重複BP入口を"
                "非表示にして価格・解禁・repeatabilityを一元化する"
            ),
            projected_result="QOL BP供給はT19に一本化され、入手不能にはならない",
        ))

    # T23 Research shop内の最も高い通常売却換金率を既存の上限契約とする。
    # 逆交換はないが、Collectionの8 RP→9500円は同通貨ownerの上限を9倍超え、
    # active-play day 116ptごとに通常moneyを134750円生成できるため補正する。
    research_reference_rates: list[float] = []
    for row in research_shop:
        item = by_id[int(row["item_id"])]
        sell_yield = int(item["price"]) // 2 * int(row["quantity"])
        research_reference_rates.append(sell_yield / int(row["price"]))
    research_money_ceiling = max(research_reference_rates)
    if research_money_ceiling != 125:
        raise AuditError(
            f"T23 research→money reference ceiling differs: {research_money_ceiling}"
        )
    research_reprices: list[dict[str, Any]] = []
    for item_id, model in collection_by_id.items():
        if int(model["source_id"]) != 2:
            continue
        item = by_id[item_id]
        sell_yield = int(item["price"]) // 2 * int(model["quantity"])
        old_price = int(model["price"])
        new_price = max(old_price, math.ceil(sell_yield / research_money_ceiling))
        if new_price == old_price:
            continue
        live = collection_live[item_id]
        research_reprices.append({
            "item_key": item["item_key"], "item_id": item_id,
            "sell_money": sell_yield, "old_research": old_price,
            "new_research": new_price,
            "old_money_per_research": sell_yield / old_price,
            "new_money_per_research": sell_yield / new_price,
        })
        patch_specs.append(PatchSpec(
            key=f"COLLECTION_RESEARCH_PRICE_{item['item_key']}",
            address=live["address"] + 2,
            expected=struct.pack("<H", old_price),
            replacement=struct.pack("<H", new_price),
            priority="P1",
            reason=(
                f"通常売却{sell_yield}円/Collection価格{old_price} RP="
                f"{sell_yield / old_price:.3f}円/RPがT23既存上限125円/RPを超える"
            ),
            projected_result=(
                f"価格{new_price} RP、通常売却換金率"
                f"{sell_yield / new_price:.3f}円/RP以下"
            ),
        ))

    honey_id = int(item_rows["ITEM_KEY_HONEY"]["id"])
    honey = collection_live[honey_id]
    honey_sell = int(item_rows["ITEM_KEY_HONEY"]["price"]) // 2
    patch_specs.append(PatchSpec(
        key="COLLECTION_HONEY_MONEY_ARBITRAGE",
        address=honey["address"] + 2,
        expected=struct.pack("<H", 300),
        replacement=struct.pack("<H", int(item_rows["ITEM_KEY_HONEY"]["price"])),
        priority="P0",
        reason=f"Collection買値300円が通常売値{honey_sell}円を下回り無限利益になる",
        projected_result="買値900円・売値450円となり1往復の純利益は-450円",
    ))

    reward_index = next(
        index for index, row in enumerate(collection["reward_entries"])
        if row["entry_key"] == "REWARD_ENTRY_0004"
    )
    reward_address = COLLECTION_REWARD_TABLE + reward_index * COLLECTION_REWARD_STRIDE
    reward_raw = _slice(rom, reward_address, COLLECTION_REWARD_STRIDE)
    expected_reward = struct.pack("<HHBBBBBB", 988, 90, 0, 1, 2, 0, 1, 0)
    if reward_raw not in (expected_reward, expected_reward[:8] + bytes((5, 0))):
        raise AuditError(f"low Raid EXP Candy XS row drift: {reward_raw.hex()}")
    patch_specs.append(PatchSpec(
        key="LOW_RAID_EXP_CANDY_XS_UNLOCK",
        address=reward_address + 8,
        expected=bytes((COLLECTION_UNLOCK_PRE_ENTRY,)),
        replacement=bytes((COLLECTION_UNLOCK_KANTO_EARLY,)),
        priority="P0",
        reason="序盤RaidのXS反復報酬がVEGA_PRE_ENTRYでT19のD.H.解禁より前に漏出する",
        projected_result="シオウclear+D.H.clearまたはKanto渡航後だけXSが抽選対象になる",
    ))

    ability_index = next(
        index for index, row in enumerate(qol_catalog)
        if row["item_key"] == "ITEM_KEY_ABILITY_PATCH"
    )
    ability_supply_address = QOL_SUPPLY_TABLE + ability_index * QOL_SUPPLY_STRIDE
    ability_row = _slice(rom, ability_supply_address, QOL_SUPPLY_STRIDE)
    expected_ability_row = struct.pack("<HHBBBB", 943, 64, 23, 1, 0xFF, 0)
    replacement_ability_row = struct.pack("<HHBBBB", 943, 64, 23, 2, 2, 0)
    if ability_row not in (expected_ability_row, replacement_ability_row):
        raise AuditError(f"QOL Ability Patch row drift: {ability_row.hex()}")
    patch_specs.append(PatchSpec(
        key="QOL_ABILITY_PATCH_REACQUISITION",
        address=ability_supply_address + 5,
        expected=bytes((1, 0xFF)),
        replacement=bytes((2, 2)),
        priority="P0",
        reason=(
            "永続一回claimは売却/使用後に再購入できず、"
            "qol_rewardsのLIMITED_REPEATABLE契約とも不一致"
        ),
        projected_result="1回のshop openにつき1個、再open後は64 BPで再購入可能",
    ))

    _assert_non_overlapping(patch_specs)
    patch_states = {spec.key: _patch_state(rom, spec) for spec in patch_specs}
    pending = [key for key, state in patch_states.items() if state == "PENDING"]

    # Money-only buy/sell cycles are the only direct currency cycle.  BP and
    # research points have no shop-side money conversion, so they are reported
    # as alternate prices rather than false-positive infinite profit.
    arbitrage: list[dict[str, Any]] = []
    for item_id, live in collection_live.items():
        if live["source"] != COLLECTION_SOURCE_MONEY:
            continue
        manifest = by_id[item_id]
        sale = int(manifest["price"]) // 2 * live["quantity"]
        if live["price"] < sale:
            arbitrage.append({
                "item_key": manifest["item_key"], "item_id": item_id,
                "buy_money": live["price"], "sell_money": sale,
                "profit_per_cycle": sale - live["price"],
                "repeatability": collection_by_id[item_id]["repeatability"],
            })

    reward_pool_zero = [
        row for row in collection["reward_entries"]
        if int(row["pool_id"]) == 0 and int(row["unlock_id"]) == 1
    ]
    low_total = sum(int(row["weight"]) for row in reward_pool_zero)
    xs_low = next(row for row in reward_pool_zero if row["item_key"] == "ITEM_KEY_EXP_CANDY_XS")
    xs_probability = int(xs_low["weight"]) / low_total

    sources = _source_registry(root, item_rows, collection, collection_live)
    effect_rows: list[dict[str, Any]] = []
    effect_unproven: list[str] = []
    reload_unproven: list[str] = []
    for key in effect_keys:
        item = item_rows[key]
        item_id = int(item["id"])
        kind = _effect_kind(key, mint_keys)
        callback_address = ITEM_TABLE + item_id * ITEM_STRIDE + ITEM_FIELD_CALLBACK_OFFSET
        callback = struct.unpack("<I", _slice(rom, callback_address, 4))[0]
        expected_callback = (
            hyper_service_item_callback
            if kind == "HYPER_SERVICE_ITEM"
            and hyper_service_item_callback is not None
            else EXPECTED_EFFECT_CALLBACKS[kind]
        )
        if callback != expected_callback:
            raise AuditError(
                f"field callback drift {key}: 0x{callback:08X} != 0x{expected_callback:08X}"
            )
        proven = kind in {"EXP_CANDY", "EV_RESET", "HYPER_SERVICE_ITEM"}
        route = (
            "BAG_FIELD_CALLBACK_ADAPTER_TO_SERVICE_17"
            if kind == "HYPER_SERVICE_ITEM"
            and hyper_service_item_callback is not None
            else "START_SELECT_HYPER_TRAIN_SERVICE"
            if kind == "HYPER_SERVICE_ITEM"
            else "BAG_FIELD_CALLBACK"
        )
        if not proven:
            effect_unproven.append(key)
        reload_unproven.append(key)
        repeat_sources = [
            row for row in sources[key]
            if row["repeatability"] not in {"ONCE", "LIMITED", "STORY_BOUND"}
        ]
        effect_rows.append({
            "item_key": key,
            "item_id": item_id,
            "display_name": item["display_name"],
            "effect_kind": kind,
            "field_effect_key": item["field_effect_key"],
            "manifest_runtime_binding": item["runtime_binding"],
            "entry_route": route,
            "callback_site": f"0x{callback_address:08X}",
            "callback": f"0x{callback:08X}",
            "callback_bound": True,
            "effect_execution_evidence": (
                "STAGE36_MGBA_EFFECT_AND_CONSUME"
                if proven else "PURCHASE_AND_CALLBACK_ONLY_EFFECT_UNPROVEN"
            ),
            "cancel_or_no_effect_evidence": (
                "PROVEN" if kind in {"EXP_CANDY", "HYPER_SERVICE_ITEM"}
                else "PARTIAL" if kind == "EV_RESET" else "UNPROVEN"
            ),
            "effect_then_fresh_core_reload": "UNPROVEN",
            "source_count": len(sources[key]),
            "repeatable_source_count": len(repeat_sources),
            "sellable": int(item["importance"]) == 0 and int(item["price"]) > 0,
            "sources": sources[key],
        })

    missable = [
        row["item_key"] for row in effect_rows
        if row["sellable"] and row["repeatable_source_count"] == 0
    ]

    # QOL catalog rows duplicated by the live Collection BP table are a single
    # owner violation even when a later unlock/discount could be intentional.
    live_duplicate_keys = [
        row["item_key"] for row in qol_catalog
        if collection_live[int(item_rows[row["item_key"]]["id"])]["source"]
        == COLLECTION_SOURCE_BP
    ]
    price_mismatches = []
    for key in live_duplicate_keys:
        live = collection_live[int(item_rows[key]["id"])]
        canonical = int(qol_catalog_by_key[key]["price_bp"])
        if live["price"] != canonical:
            price_mismatches.append({
                "item_key": key, "qol_owner_bp": canonical,
                "collection_bp": live["price"],
                "delta": live["price"] - canonical,
            })
    if len(duplicate_keys) != 47 or len(research_reprices) != 71:
        raise AuditError(
            "Stage58 balance target count drift: "
            f"QOL owner={len(duplicate_keys)}, research reprices={len(research_reprices)}"
        )

    def sale_yield(item_id: int, quantity: int = 1) -> int:
        return int(by_id[item_id]["price"]) // 2 * quantity

    qol_bp_prices = [int(row["price_bp"]) for row in qol_catalog]
    qol_bp_rates = [
        sale_yield(int(item_rows[row["item_key"]]["id"])) / int(row["price_bp"])
        for row in qol_catalog
    ]
    collection_bp_current = [
        (live["price"], sale_yield(item_id, live["quantity"]), by_id[item_id]["item_key"])
        for item_id, live in collection_live.items()
        if live["source"] == COLLECTION_SOURCE_BP and live["price"] > 0
    ]
    duplicate_set = set(duplicate_keys)
    collection_bp_projected = [
        row for row in collection_bp_current if row[2] not in duplicate_set
    ]
    research_new_price = {
        row["item_id"]: row["new_research"] for row in research_reprices
    }
    collection_research_current = [
        (live["price"], sale_yield(item_id, live["quantity"]),
         by_id[item_id]["item_key"])
        for item_id, live in collection_live.items()
        if live["source"] == 2 and live["price"] > 0
    ]
    collection_research_projected = [
        (research_new_price.get(item_id, int(model["price"])),
         sale_yield(item_id, int(model["quantity"])), by_id[item_id]["item_key"])
        for item_id, model in collection_by_id.items()
        if int(model["source_id"]) == 2 and int(model["price"]) > 0
    ]
    research_shop_prices = [int(row["price"]) for row in research_shop]
    research_shop_rates = [
        sale_yield(int(row["item_id"]), int(row["quantity"])) / int(row["price"])
        for row in research_shop
    ]
    collection_research_daily_money = _maximum_money_for_budget(
        ((price, money) for price, money, _key in collection_research_current),
        research_daily_cap,
    )
    projected_collection_research_daily_money = _maximum_money_for_budget(
        ((price, money) for price, money, _key in collection_research_projected),
        research_daily_cap,
    )

    validation = _existing_validation(root)
    runtime_symbols = _read_json(root / "generated/runtime/qol_production_symbols.json")["entrypoints"]
    required_symbols = (
        "VegaQolProduction_PurchaseSupply",
        "VegaQolProduction_FieldUseCommonQuantityAdapter",
        "VegaQolProduction_ApplyExpCandyQuantityAdapter",
        "VegaQolProduction_Dispatch",
    )
    symbol_rows = []
    for symbol in required_symbols:
        address = int(runtime_symbols[symbol]) & ~1
        first = _slice(rom, address, 4)
        if first == b"\xFF" * 4 or first == b"\x00" * 4:
            raise AuditError(f"QOL runtime symbol is blank: {symbol}")
        symbol_rows.append({
            "symbol": symbol, "address": f"0x{int(runtime_symbols[symbol]):08X}",
            "first_word_hex": first.hex(), "rooted_in_stage57": True,
        })

    projected_arbitrage = [row for row in arbitrage if row["item_key"] != "ITEM_KEY_HONEY"]
    status = "REPAIR_REQUIRED" if pending else "EFFECT_RUNTIME_PROOF_REQUIRED"
    report = {
        "schema_version": 1,
        "task": "USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG",
        "stage": 57,
        "status": status,
        "input": {
            "rom": (
                "<memory>" if rom_bytes is not None else
                str(rom_file.relative_to(root) if rom_file.is_relative_to(root) else rom_file)
            ),
            "size": len(rom), "sha256": rom_sha,
            "stage57_exact": rom_sha == STAGE57_SHA256,
        },
        "existing_validation": validation,
        "runtime_symbols": symbol_rows,
        "transaction_evidence": {
            "currency_acquisition": {
                "MONEY": (
                    "既存Vega通常獲得を継承。Stage36/40/56 smokeは残高注入であり、"
                    "trainer/rematch→通常save→別core reloadは未証明"
                ),
                "BP": (
                    "Factory ledger ownerはrooted。Stage36/56 smokeは残高注入であり、"
                    "実戦BP award→shop→通常save→別core reloadの一連caseは未証明"
                ),
                "RESEARCH": (
                    "Stage40 activity_day_capsで6活動・116pt/day・hook/root・"
                    "pending recoveryを実行証明済み"
                ),
            },
            "purchase_routes": {
                "T19_QOL_BP": {
                    "success": True, "insufficient": True,
                    "cancel_no_mutation": False, "bag_full_no_mutation": False,
                    "purchase_persist_failure_rollback": False,
                    "fresh_core_reload_after_purchase": False,
                    "scope_note": (
                        "Stage36 cross_store fault/reloadは別service・rewardを証明するが、"
                        "supply_purchase_rawと同一caseではない"
                    ),
                },
                "T23_RESEARCH": {
                    "success_all_23": True, "cancel_no_mutation_all_23": True,
                    "insufficient_all_23": True, "bag_full_no_mutation_all_23": True,
                    "purchase_persist_failure_recovery": True,
                    "fresh_core_reload_after_pending_purchase": True,
                },
                "STAGE56_COLLECTION_MONEY_BP_RESEARCH": {
                    "success_each_currency": True, "insufficient_each_currency": True,
                    "persist_failure_rollback_each_currency": True,
                    "cancel_no_mutation": False, "bag_full_purchase_no_mutation": False,
                    "fresh_core_reload_after_purchase": False,
                    "scope_note": (
                        "Raid報酬のbag-full retryとowner sector restoreは別caseでPASS"
                    ),
                },
            },
        },
        "qol_effect_items": {
            "count": len(effect_rows),
            "callback_bound_count": sum(row["callback_bound"] for row in effect_rows),
            "effect_execution_proven_count": len(effect_rows) - len(effect_unproven),
            "effect_execution_unproven_count": len(effect_unproven),
            "effect_execution_unproven": effect_unproven,
            "effect_then_fresh_core_reload_proven_count": 0,
            "effect_then_fresh_core_reload_unproven_count": len(reload_unproven),
            "missable_after_sale_count": len(missable),
            "missable_after_sale": missable,
            "rows": effect_rows,
        },
        "economy": {
            "currencies": ["MONEY", "BP", "RESEARCH"],
            "collection_money_rows": sum(
                row["source"] == COLLECTION_SOURCE_MONEY for row in collection_live.values()
            ),
            "money_buy_sell_arbitrage_count": len(arbitrage),
            "money_buy_sell_arbitrage": arbitrage,
            "projected_money_buy_sell_arbitrage_count": len(projected_arbitrage),
            "qol_catalog_count": len(qol_catalog),
            "collection_qol_bp_duplicate_count": len(live_duplicate_keys),
            "collection_qol_bp_duplicate_keys": live_duplicate_keys,
            "qol_collection_bp_price_mismatch_count": len(price_mismatches),
            "qol_collection_bp_price_mismatches": price_mismatches,
            "projected_collection_qol_bp_duplicate_count": 0,
            "qol_bp_price_summary": _price_summary(qol_bp_prices),
            "research_shop_price_summary": _price_summary(research_shop_prices),
            "research_daily_point_cap": research_daily_cap,
            "t19_bp_money_per_point_ceiling": max(qol_bp_rates),
            "collection_bp_money_per_point_ceiling": max(
                money / price for price, money, _key in collection_bp_current
            ),
            "projected_collection_bp_money_per_point_ceiling": max(
                money / price for price, money, _key in collection_bp_projected
            ),
            "t23_research_money_per_point_ceiling": max(research_shop_rates),
            "collection_research_money_per_point_ceiling": max(
                money / price
                for price, money, _key in collection_research_current
            ),
            "projected_collection_research_money_per_point_ceiling": max(
                money / price
                for price, money, _key in collection_research_projected
            ),
            "collection_research_reprice_count": len(research_reprices),
            "collection_research_reprices": research_reprices,
            "collection_research_daily_money_conversion_max":
                collection_research_daily_money,
            "projected_collection_research_daily_money_conversion_max":
                projected_collection_research_daily_money,
            "same_currency_infinite_profit_cycle_count": len(arbitrage),
            "currency_conversion_cycle_count": len(arbitrage),
            "bp_research_to_money_direct_conversion": True,
            "money_to_bp_research_reverse_conversion": False,
            "conversion_policy": (
                "片道売却換金は維持するが、BP/RPごとの通常money価値は各正本shopの"
                "既存最大値（T19=1250円/BP、T23=125円/RP）を超えさせない"
            ),
        },
        "raid_rewards": {
            "low_pool_pre_entry_total_weight": low_total,
            "exp_candy_xs_pre_entry_weight": int(xs_low["weight"]),
            "exp_candy_xs_pre_entry_probability": xs_probability,
            "exp_candy_xs_quantity": [int(xs_low["quantity_min"]), int(xs_low["quantity_max"])],
            "exp_candy_xs_repeatable": True,
            "pre_unlock_leak_count": 1 if patch_states["LOW_RAID_EXP_CANDY_XS_UNLOCK"] == "PENDING" else 0,
            "projected_pre_unlock_leak_count": 0,
            "ability_patch_special_pool_weight": 18,
            "ability_patch_secondary_source_policy": (
                "UB_PARADOX後のRaid副供給は維持。T19をLIMITED_REPEATABLEへ合わせ、"
                "Collectionの重複BP販売だけを除去する"
            ),
        },
        "patch_plan": {
            "count": len(patch_specs),
            "pending_count": len(pending),
            "applied_count": len(patch_specs) - len(pending),
            "overlap_count": 0,
            "rows": [spec.as_dict(patch_states[spec.key]) for spec in patch_specs],
        },
        "required_stage58_verification_cases": [
            {**row, "required": True, "verification": "EXACT_ROM_MGBA"}
            for row in REQUIRED_STAGE58_VERIFICATION_CASES
        ],
        "decision": {
            "qol_items_are_really_usable": (
                "経験アメ、EV reset、おうかんserviceは効果実行済み。"
                "特性カプセル/パッチと全21ミントはcallback接続のみで、Stage57証跡は購入成功まで"
            ),
            "root_fix": (
                "QOL 47品のBP供給ownerをT19へ一本化し、Ability Patchを64 BPの"
                "LIMITED_REPEATABLEへ統一する。Collection Research高換金71品は"
                "T23既存上限125円/RPへ価格floor補正し、Raid副供給は終盤報酬として維持する"
            ),
            "completion_gate": (
                "patch 121件適用だけでは完了にせず、stable ID付き必須10 caseを"
                "Stage58 exact ROMのmGBA証跡へ全件対応させ、未証明23品の実効果、"
                "36品のfresh-core reload、通常money/BPの実獲得をPASSさせる"
            ),
        },
    }
    return report


def apply_patch_plan(rom: bytes, report: Mapping[str, Any]) -> bytes:
    """監査reportのPENDING patchをmemory上だけへ適用する（test/builder用）。"""
    output = bytearray(rom)
    for row in report["patch_plan"]["rows"]:
        address = int(row["address"], 0)
        expected = bytes.fromhex(row["expected_hex"])
        replacement = bytes.fromhex(row["replacement_hex"])
        offset = _rom_offset(address, len(expected), len(output))
        current = bytes(output[offset:offset + len(expected)])
        if current == replacement:
            continue
        if current != expected:
            raise AuditError(f"apply patch drift: {row['key']}={current.hex()}")
        output[offset:offset + len(expected)] = replacement
    return bytes(output)


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--rom", type=Path)
    parser.add_argument(
        "--metadata", type=Path,
        help=(
            "post-Stage57 ROMを監査する場合のbuild metadata。output SHA-256と"
            "Bottle Cap callbackをROMと照合し、identity固定を解除する"
        ),
    )
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--require-fixed", action="store_true",
        help="patch残件または実効果証明残件があれば終了1",
    )
    args = parser.parse_args(argv)
    if args.metadata is None:
        report = build_audit(args.root, args.rom)
    else:
        if args.rom is None:
            parser.error("--metadataには--romが必要です")
        metadata_path = args.metadata.resolve()
        metadata = _read_json(metadata_path)
        rom_path = args.rom.resolve()
        rom_sha = _sha256(rom_path.read_bytes())
        expected_sha = str(metadata.get("output", {}).get("sha256", ""))
        if rom_sha != expected_sha:
            raise AuditError(
                "metadata output SHA-256 differs: "
                f"rom={rom_sha} metadata={expected_sha or '<missing>'}"
            )
        callback = metadata.get("qol_item_bag_adapter", {}).get(
            "replacement_callback"
        )
        if not isinstance(callback, int):
            raise AuditError(
                "metadataにqol_item_bag_adapter.replacement_callbackがありません"
            )
        report = build_audit(
            args.root, rom_path, require_stage57_identity=False,
            hyper_service_item_callback=callback,
        )
    print(json.dumps(
        report, ensure_ascii=False, indent=2 if args.pretty else None,
        sort_keys=True,
    ))
    if args.require_fixed and report["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
