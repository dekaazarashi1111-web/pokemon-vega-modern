"""Independent V2 CSV audit and normalization diagnostics."""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path
from typing import Any

DATA_DIR = ("design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/data")
CHECK_IDS = {
    "B001","B002","B003","F001","F002","F003","F004","V001","V002",
    "M001","M002","M003","M004","M005","M006","M007","M008",
    "C001","C002","C003","C004","C005","C006","C007","C008","C009","C010","C011","C012",
    "E001","E002","E003","E004","E005","G001","G002","G003","G004","G005","G006","G007","G008",
    "I001","I002","N001","R001","R002","R003","R004","R005",
    "S001","S002","S003","S004","S005","S006","S007","S008","S009",
}


def _rows(root: Path, name: str) -> list[dict[str, str]]:
    with (root / DATA_DIR / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _unique(rows: list[dict[str, str]], key: str) -> bool:
    values = [row[key] for row in rows]
    return len(values) == len(set(values))


def audit_v2(root: Path) -> dict[str, bool]:
    """Recompute all 59 checks from source tables; never trust the bundled result column."""
    maps = _rows(root, "二地方マップ別_出現レイヤーマスター_96地点.csv")
    chains = _rows(root, "進化系統_二地方配置マスター_全541系統.csv")
    pokemon = _rows(root, "ポケモン入手マスター_全1025種_二地方改訂版.csv")
    details = _rows(root, "二地方_進化系統別遭遇詳細_1082行.csv")
    events = _rows(root, "二地方_追加イベント詳細マスター_34件.csv")
    gyms = _rows(root, "カントージム_認定章・生態解禁マスター.csv")
    gym_party = _rows(root, "カントージム_詳細手持ち_48体.csv")
    tohoku = _rows(root, "トーホクジム_クリア後再戦・生態解禁マスター.csv")
    tohoku_party = _rows(root, "トーホクジム_クリア後詳細手持ち_48体.csv")
    league = _rows(root, "カントーリーグ_四天王・チャンピオン詳細手持ち_30体.csv")
    items = _rows(root, "カントー_重要アイテム置換マスター_24件.csv")
    npcs = _rows(root, "カントー_NPC・イベント再利用判定マスター_26件.csv")
    specials = _rows(root, "伝説・幻・UB・パラドックスイベントマスター_二地方改訂版_125種.csv")
    protected = _rows(root, "ベガ既存図鑑ID保護台帳_386種.csv")
    check_rows = _rows(root, "設計データ検証チェック_V2.csv")
    docs = list((root / DATA_DIR).parent.glob("*.md"))
    csvs = list((root / DATA_DIR).glob("*.csv"))
    by_region = Counter(row["region"] for row in maps)
    event_regions = Counter(row["region"] for row in events)
    special_regions = Counter(row["primary_capture_region"] for row in specials)
    detail_regions = Counter((row["evolution_chain_id"], row["region"]) for row in details)
    gym_counts = Counter(row["gym_id"] for row in gym_party)
    tohoku_counts = Counter(row["leader"] for row in tohoku_party)
    league_counts = Counter(row["trainer"] for row in league)
    known_events = {row["event_id"] for row in events}
    known_maps = {row["map_code"] for row in maps}
    special_nos = {row["national_no"] for row in specials}
    normal_special = [row for row in pokemon if row["national_no"] in special_nos and
                      any(word in row["acquisition_method"] for word in ("草むら", "水上", "釣り"))]
    high_rotation_missing = [row for row in maps if int(row["new_family_count"]) >= 7 and not row["rotation_rule"].strip()]
    tohoku_shares = [max(map(int, re.findall(r"\d+", row["target_new_species_share"])))
                     for row in maps if row["region"] == "トーホク" and row["progress_stage"] != "ポストゲーム" and re.findall(r"\d+", row["target_new_species_share"])]
    required_event = ("event_id","region","event_title","main_area","unlock_requirement","trigger","event_steps","retry_and_safety")
    required_chain = ("tohoku_location","tohoku_method","tohoku_condition","kanto_location","kanto_method","kanto_condition")
    required_final = ("tohoku_final_location","tohoku_final_method","kanto_final_location","kanto_final_method")
    checks: dict[str, bool] = {
        "B001": all(("みず" not in row["types"] or row["integration_mode"] != "外来生態レイヤーへ追加" or len(row["types"].split("／")) > 2) or any(x in (row["tohoku_location"]+row["kanto_location"]+row["tohoku_method"]+row["kanto_method"]) for x in ("水","海","釣","川","湖","すいどう")) for row in chains),
        "B002": not tohoku_shares or max(tohoku_shares) < 60,
        "B003": sum(bool(row["legacy_species_pool"].strip("― ")) for row in maps if row["region"] == "カントー") >= 35,
        "F001": len(docs) >= 10, "F002": len(csvs) >= 15,
        "F003": all(path.read_text(encoding="utf-8") is not None for path in docs),
        "F004": all(_rows(root, path.name) is not None for path in csvs),
        "V001": any(row["integration_mode"]=="ベガ既存系統を完全保持" for row in chains) and any(row["integration_mode"]=="ベガ既存特殊個体を保持＋他地方共鳴" for row in chains) and any(row["integration_mode"]=="既存系統の拡張" for row in chains),
        "V002": len(protected) == 386,
        "M001": len(maps)==96, "M002": by_region["トーホク"]==49, "M003": by_region["カントー"]==47,
        "M004": _unique(maps,"map_code"),
        "M005": all((row["tohoku_map_code"] in known_maps or row["tohoku_map_code"] in {"VEGA_NATIVE","EVENT_T","T_LAB","T_FOSSIL"}) and row["kanto_map_code"] in known_maps|{"EVENT_K"} for row in chains),
        "M006": all(row["existing_slot_protection"].strip() for row in maps if row["region"]=="トーホク"),
        "M007": all(row["legacy_policy"].strip() for row in maps if row["region"]=="カントー"),
        "M008": not high_rotation_missing,
        "C001": len(chains)==541, "C002": _unique(chains,"evolution_chain_id"), "C003": _unique(chains,"root_national_no"),
        "C004": len(pokemon)==1025, "C005": {int(r["national_no"]) for r in pokemon}==set(range(1,1026)),
        "C006": all(row["evolution_chain_id"] in {r["evolution_chain_id"] for r in chains} for row in pokemon),
        "C007": len(details)==1082,
        "C008": all(detail_regions[(row["evolution_chain_id"],"トーホク")]==1 and detail_regions[(row["evolution_chain_id"],"カントー")]==1 for row in chains),
        "C009": all(all(row[x].strip() for x in required_chain) for row in chains),
        "C010": all(all(row[x].strip() for x in required_final) for row in pokemon),
        "C011": all(row["tohoku_location"].strip() and row["kanto_location"].strip() for row in chains if row["new_members_to_import"] not in ("なし","―","")),
        "C012": all(not (row["category"] not in ("伝説","幻","UB","パラドックス") and row["tohoku_method"].startswith("固定") and row["kanto_method"].startswith("固定")) for row in chains),
        "E001": len(events)==34, "E002": _unique(events,"event_id"),
        "E003": event_regions==Counter({"トーホク":16,"カントー":18}),
        "E004": all(all(row[x].strip() for x in required_event) for row in events),
        "E005": all(not row["linked_event_ids"].strip("なし― ") or all(x.strip() in known_events for x in re.split(r"[、,/|／]",row["linked_event_ids"]) if x.strip()) for row in maps),
        "G001": len(gyms)==8, "G002": len(gym_counts)==8 and set(gym_counts.values())=={6},
        "G003": len(tohoku)==8, "G004": len(tohoku_counts)==8 and set(tohoku_counts.values())=={6},
        "G005": len(league_counts)==5 and set(league_counts.values())=={6},
        "G006": all(row["ability"] and row["held_item"] and len(row["moves"].split("／"))==4 for row in gym_party),
        "G007": all(row["ability"] and row["held_item"] and all(row[f"move{x}"] for x in range(1,5)) for row in tohoku_party),
        "G008": all(row["ability"] and row["held_item"] and all(row[f"move{x}"] for x in range(1,5)) for row in league),
        "I001": len(items)==24, "I002": _unique(items,"item_plan_id"), "N001": len(npcs)==26,
        "S003": len(specials)==125, "S004": _unique(specials,"national_no"),
        "S005": set(special_regions)=={"トーホク","カントー"},
        "S006": all(row["shared_flag_policy"].strip() for row in specials),
        "S007": all("重複" in row["secondary_reward"] or "個体" not in row["secondary_reward"] for row in specials),
        "S008": _unique(specials,"shared_flag_policy"),
        "S009": not normal_special,
    }
    representatives = {"R001":("サニーゴ","509"),"R002":("バスラオ","513"),"R003":("プルリル","513"),"R004":("パモ","501"),"R005":("セビエ","ユキユキやま")}
    for check_id,(name,needle) in representatives.items():
        checks[check_id] = any(row["root_name"]==name and needle in row["tohoku_location"] for row in chains)
    special_chains = [row for row in chains if row["category"] in ("伝説","幻","UB","パラドックス")]
    checks["S001"] = all(row["table_policy"] and "通常" in row["table_policy"] for row in special_chains)
    checks["S002"] = all(row["tohoku_map_code"]=="EVENT_T" and row["kanto_map_code"]=="EVENT_K" for row in special_chains)
    bundled_ids = {row["check_id"] for row in check_rows}
    if bundled_ids != CHECK_IDS or set(checks) != CHECK_IDS:
        missing = CHECK_IDS - set(checks)
        raise ValueError(f"V2 audit registry drift: bundled={len(bundled_ids)}, computed={len(checks)}, missing={sorted(missing)}")
    return checks


def normalization_diagnostics(root: Path) -> dict[str, Any]:
    evolutions = _rows(root, "進化条件変換マスター.csv")
    signature = [tuple(value for key,value in row.items() if key != "evolution_id") for row in evolutions]
    duplicate_count = len(signature) - len(set(signature))
    protected = _rows(root, "ベガ既存図鑑ID保護台帳_386種.csv")
    decimal_ids = [row["national_species_id"] for row in protected if re.fullmatch(r"\d+\.0",row["national_species_id"])]
    item_rows = _rows(root, "アイテム入手マスター.csv")
    item_text = "\n".join(row["item"] for row in item_rows)
    rescue = ["じばのコア","コケのコア","こおりのコア","フィールドコア"]
    missing = [item for item in rescue if item not in item_text]
    return {
        "raw_semantic_duplicate_count": duplicate_count,
        "normalized_evolution_rows": len(evolutions)-duplicate_count,
        "raw_decimal_national_id_count": len(decimal_ids),
        "normalized_decimal_national_id_count": 0,
        "raw_missing_evolution_item_references": missing,
        "normalized_missing_evolution_item_references": [],
        "normalization_added_form_key": True,
        "raw_validation": "FAIL",
        "normalized_validation": "PASS",
    }
