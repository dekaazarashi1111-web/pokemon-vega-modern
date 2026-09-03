#!/usr/bin/env python3
"""現行Stage61 ROMから、プレイ質問向けの決定的Wikiを生成・検査する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import struct
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/wiki/stage61"
REPORT = ROOT / "reports/generated/stage61_wiki.json"
ROM_REL = "build/stages/61_critical_release_candidate.gba"
ROM_SHA256 = "44e951e20e7985b6f4480a04ff997cc77e6305dd0945eb90cfed7e3c6d85ae4e"
ROM_SIZE = 33_554_432
SPECIES_COUNT = 1_621
MOVE_COUNT = 1_063
ABILITY_COUNT = 312
ITEM_COUNT = 999
BASE_STATS_OFFSET = 0x01600000
MOVE_TABLE_OFFSET = 0x010421F4
ECOLOGY_OFFSET = 0x0121D98C
ECOLOGY_COUNT = 95
ECOLOGY_ROW_SIZE = 104
PTR_BASE = 0x08000000

SOURCE_PATHS = (
    "design/active_play_baseline.md",
    "manifests/species_ids.csv",
    "manifests/move_ids.csv",
    "manifests/ability_ids.csv",
    "manifests/item_ids.csv",
    "generated/engine/ids/id_spaces.json",
    "generated/engine/moves/move_port.json",
    "vendor/vega_acquisition/content/species_acquisition_routes.csv",
    "vendor/vega_acquisition/content/evolution_requirements_553.csv",
    "vendor/vega_acquisition/content/acquisition_events.csv",
    "content/collection_supply_v1/canonical_model.json",
    "reports/generated/stage58_qol_economy_audit.json",
    "reports/generated/stage61_critical_release_map_display_catalog.json",
    "config/stage61_runtime_hotfix.json",
    "manifests/kanto_items.csv",
    "manifests/tohoku_items.csv",
    "manifests/qol_rewards.csv",
    "manifests/facility_rewards.csv",
)

TYPE_NAMES = {
    0: "ノーマル", 1: "かくとう", 2: "ひこう", 3: "どく", 4: "じめん",
    5: "いわ", 6: "むし", 7: "ゴースト", 8: "はがね", 9: "？？？",
    10: "ほのお", 11: "みず", 12: "くさ", 13: "でんき", 14: "エスパー",
    15: "こおり", 16: "ドラゴン", 17: "あく", 23: "フェアリー", 24: "ステラ",
}
GROWTH_NAMES = {0: "中", 1: "不規則", 2: "変動", 3: "やや遅い", 4: "早い", 5: "遅い"}
EGG_GROUP_NAMES = {
    0: "なし", 1: "怪獣", 2: "水中1", 3: "虫", 4: "飛行", 5: "陸上",
    6: "妖精", 7: "植物", 8: "人型", 9: "水中3", 10: "鉱物", 11: "不定形",
    12: "水中2", 13: "メタモン", 14: "ドラゴン", 15: "未発見",
}
MOVE_SPLITS = {0: "物理", 1: "特殊", 2: "変化"}
WILD_MODE_NAMES = {"land": "草むら", "water": "水上", "rock": "いわくだき", "fishing": "釣り"}
AREA_NAMES = {0: "草むら", 1: "水上", 2: "いわくだき", 3: "釣り", 4: "隠し遭遇"}
LAYER_NAMES = {0: "通常", 1: "昼", 2: "夜", 3: "大量発生", 4: "釣り", 5: "隠し遭遇"}
METHOD_NAMES = {
    "WILD_TABLE": "通常野生", "ECOLOGY_OVERLAY": "生態オーバーレイ", "EVOLUTION": "進化",
    "EVOLUTION_SUPPORT": "進化補助", "FIXED_CAPTURE": "固定シンボル捕獲", "RESEARCH_EGG": "研究タマゴ",
    "BREEDING_OR_RESEARCH_EGG": "孵化または研究タマゴ", "GIFT": "ギフト", "FOSSIL_RESTORE": "化石復元",
    "EXCLUDED": "入手対象外", "WILD_OVERLAY": "野生フォーム置換", "FORM_CHANGE_SERVICE": "フォーム変更サービス",
    "RAID_CAPTURE": "Raid捕獲", "FIXED_GIFT": "固定ギフト", "DO_NOT_DISTRIBUTE": "配布対象外",
    "BATTLE_TRANSFORM_ONLY": "戦闘中のみ変化", "GMAX_FACTOR_ONLY": "キョダイマックス因子のみ",
    "OPTIONAL_FORM_TRANSFORMATION": "任意フォーム変化",
}
SOURCE_NAMES = {
    "BP_SHOP": "BPショップ", "RESEARCH_SHOP": "研究ショップ", "MONEY_SHOP": "通常ショップ",
    "NPC_GIFT": "NPCギフト", "VEGA_EXISTING": "Vega従来入手", "EXCLUDED": "入手対象外",
    "RAID_REWARD": "Raid報酬", "STORY_EVENT": "ストーリーイベント", "FACTORY_REWARD": "Factory報酬",
    "FORM_SERVICE": "フォーム変更サービス",
}
REPEAT_NAMES = {
    "REPEATABLE": "繰り返し可", "REPEATABLE_WILD": "野生で繰り返し可", "LIMITED_REPEATABLE": "条件付き再入手可",
    "ONCE": "1回", "STORY_BOUND": "ストーリー条件", "NOT_APPLICABLE": "対象外", "NOT_REQUIRED": "不要",
    "REPEATABLE_WHILE_SOURCE_AVAILABLE": "入手元が利用可能な間は繰り返し可",
    "ONE_CAPTURE; defeat/escape/cancel/reset retryable": "1回捕獲（敗北・逃走・キャンセル・reset時は再試行可）",
    "ONCE_PER_SPECIES; cancel/reset/full retryable": "種族ごとに1回（キャンセル・reset・満杯時は再試行可）",
    "ONE_REGISTRATION; failure retryable; Kanto rescue once": "登録1回（失敗時再試行、カントー救済は1回）",
    "ONCE_PER_FORM; registration-safe retry": "フォームごとに1回（登録前失敗は再試行可）",
    "REPEATABLE; first registration protected": "繰り返し可（初回登録を保護）",
}
UNLOCK_NAMES = {
    "": "条件なし", "NONE": "条件なし", "UNLOCK_EXISTING_MAP_PROGRESSION": "Vega従来マップの進行条件",
    "UNLOCK_EVOLUTION_GLOBAL": "進化機能解禁", "UNLOCK_FOSSIL_SERVICE": "化石復元サービス解禁",
    "UNLOCK_HALL_OF_FAME": "殿堂入り", "UNLOCK_KANTO_EARLY_ACCESS": "カントー早期渡航解禁",
    "UNLOCK_MOVE_CONDITION_TUTOR": "指定技条件を満たせる技教え解禁", "UNLOCK_PARADOX_RESEARCH": "パラドックス研究解禁",
    "UNLOCK_REGIONAL_NURSERY": "地方育て屋解禁", "UNLOCK_RESEARCH_RANK_4": "研究ランク4",
    "UNLOCK_RESEARCH_RANK_5": "研究ランク5", "UNLOCK_SPECIAL_ARCHIVE": "特別アーカイブ解禁",
    "UNLOCK_SPHERE_RUINS_CLEAR": "スフィア遺跡クリア", "UNLOCK_TERA_ORB": "テラオーブ解禁",
    "RESEARCH_PROFILE_UNLOCKED": "研究プロフィール解禁", "COMPETITIVE_SUPPLY_UNLOCKED": "対戦用供給解禁",
    "FACTORY_STANDARD": "Factory Standard解禁", "FACTORY_FULL": "Factory Full解禁", "FACTORY_MASTER": "Factory Master解禁",
    "FINAL_LEAGUE_CLEARED": "最終リーグクリア", "LEAGUE_I_CLEARED": "第1リーグクリア",
    "LEAGUE_II_CLEARED": "第2リーグクリア", "HIDDEN_ABILITY_DEXNAV_UNLOCKED": "隠れ特性DexNav解禁",
    "RAID_HIGH_UNLOCKED": "高難度Raid解禁", "TM_LICENSE_UNLOCKED": "TMライセンス解禁",
    "UB_PARADOX_UNLOCKED": "UB・パラドックス解禁", "KANTO_EARLY_ACCESS": "カントー早期渡航解禁",
    "VEGA_PRE_ENTRY": "Vega序盤から", "VEGA_BADGE_1": "Vegaバッジ1個", "VEGA_BADGE_2": "Vegaバッジ2個",
    "VEGA_BADGE_5": "Vegaバッジ5個", "VEGA_BADGE_6": "Vegaバッジ6個", "VEGA_BADGE_7": "Vegaバッジ7個",
    "VEGA_BADGE_8": "Vegaバッジ8個", "VEGA_HALL_OF_FAME": "Vega殿堂入り",
    "VEGA_SHIOU_BADGE_3": "シオウのバッジ3個", "KANTO_LEAGUE": "カントーリーグ解禁",
    "UNLOCK_BEAST_BALL": "ウルトラボール系供給解禁", "VEGA_DH_CLEAR": "D・Hビル初回攻略後",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    return ("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for row in rows) + "\n").encode()


def _md(value: Any) -> str:
    if value in (None, "", []):
        return "—"
    return str(value).replace("|", "\\|").replace("\r", "").replace("\\n", "<br>").replace("\n", "<br>")


def _named(raw: str, names: dict[str, str]) -> str:
    return f"{names.get(raw, raw or '条件なし')} (`{raw or 'NONE'}`)"


def _unlock(raw: str) -> str:
    if raw.startswith("KANTO_CERT_"):
        return f"カントー認定章{raw.rsplit('_', 1)[-1]} (`{raw}`)"
    return _named(raw, UNLOCK_NAMES)


def _unlock_desc(raw: str) -> str:
    if raw.startswith("KANTO_CERT_"):
        return f"カントー認定章{raw.rsplit('_', 1)[-1]}"
    return UNLOCK_NAMES.get(raw, "正本keyを参照（未翻訳）")


def _gender_label(value: int) -> str:
    if value == 0:
        return "オスのみ（code 0）"
    if value == 254:
        return "メスのみ（code 254）"
    if value == 255:
        return "性別不明（code 255）"
    female = value / 254 * 100
    return f"オス約{100 - female:.1f}% / メス約{female:.1f}%（code {value}）"


def _ptr(raw: bytes, site: int) -> int:
    value = struct.unpack_from("<I", raw, site)[0]
    if not PTR_BASE <= value < PTR_BASE + len(raw):
        raise ValueError(f"ROM pointer範囲外: site=0x{site:08X} value=0x{value:08X}")
    return value - PTR_BASE


def _require_contiguous(rows: list[dict[str, str]], field: str, count: int, label: str) -> None:
    ids = sorted(int(row[field]) for row in rows)
    if ids != list(range(count)):
        raise ValueError(f"{label} IDが0..{count - 1}で連続していません")


def _identity(raw: bytes) -> dict[str, Any]:
    digest = _sha(raw)
    if len(raw) != ROM_SIZE or digest != ROM_SHA256:
        raise ValueError(f"active Stage61 ROM不一致: size={len(raw)} sha256={digest}")
    baseline = (ROOT / "design/active_play_baseline.md").read_text(encoding="utf-8")
    if ROM_REL not in baseline or ROM_SHA256 not in baseline or "DEFERRED_AUDIT" not in baseline:
        raise ValueError("design/active_play_baseline.mdが固定したStage61 identityと一致しません")
    return {
        "path": ROM_REL,
        "size": len(raw),
        "sha256": digest,
        "candidate_status": "CANDIDATE",
        "strict_audit": "DEFERRED_AUDIT",
    }


def _load_wild(raw: bytes) -> dict[str, Any]:
    path = ROOT / "scripts/validate_stage60_wild_species_root_repair.py"
    spec = importlib.util.spec_from_file_location("stage61_wild_reader", path)
    if spec is None or spec.loader is None:
        raise ValueError("野生テーブルreaderを読み込めません")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = module.enumerate_wild(raw)
    if data["rom_sha256"] != ROM_SHA256 or data["header_count"] != 265 or data["slot_count"] != 2733:
        raise ValueError("Stage61通常野生テーブルshape不一致")
    return data


def _load_ecology(raw: bytes) -> list[dict[str, Any]]:
    blob = raw[ECOLOGY_OFFSET:ECOLOGY_OFFSET + ECOLOGY_COUNT * ECOLOGY_ROW_SIZE]
    expected = "da77542c7070098485aa98d268101b6c88ef50df2842485cfae40d2964a5d4f5"
    if _sha(blob) != expected:
        raise ValueError("Stage61 ecology overlay table hash不一致")
    result = []
    for index in range(ECOLOGY_COUNT):
        row = blob[index * ECOLOGY_ROW_SIZE:(index + 1) * ECOLOGY_ROW_SIZE]
        group, map_id, area, layer, threshold, count, rate, reserved = row[:8]
        species = list(struct.unpack_from("<12H", row, 8))[:count]
        result.append({
            "index": index,
            "group": group,
            "map": map_id,
            "area": AREA_NAMES.get(area, f"area-{area}"),
            "layer": LAYER_NAMES.get(layer, f"layer-{layer}"),
            "threshold": threshold,
            "candidate_count": count,
            "rate_percent": rate,
            "species": species,
            "pre_levels": [[row[32 + i], row[44 + i]] for i in range(count)],
            "post_levels": [[row[56 + i], row[68 + i]] for i in range(count)],
            "min_badges": list(row[80:80 + count]),
            "min_rods": list(row[92:92 + count]),
            "reserved": reserved,
        })
    return result


def _load_level_moves(raw: bytes) -> list[list[dict[str, int]]]:
    root = _ptr(raw, 0x4346C)
    rows: list[list[dict[str, int]]] = []
    for species_id in range(SPECIES_COUNT):
        offset = _ptr(raw, root + species_id * 4)
        moves = []
        for _ in range(256):
            move_id, level = struct.unpack_from("<HB", raw, offset)
            offset += 3
            if move_id == 0 and level == 0xFF:
                break
            if move_id >= MOVE_COUNT:
                raise ValueError(f"レベル技ID範囲外: species={species_id} move={move_id}")
            if move_id:
                moves.append({"level": level, "move_id": move_id})
        else:
            raise ValueError(f"レベル技終端なし: species={species_id}")
        rows.append(moves)
    if sum(map(len, rows)) != 28_859:
        raise ValueError("Stage61レベル技件数不一致")
    return rows


def _load_egg_moves(raw: bytes) -> list[list[int]]:
    offset = _ptr(raw, 0x45214)
    rows: list[list[int]] = [[] for _ in range(SPECIES_COUNT)]
    current: int | None = None
    marker_count = 0
    while True:
        value = struct.unpack_from("<H", raw, offset)[0]
        offset += 2
        if value == 0xFFFF:
            break
        if value >= 20_000:
            current = value - 20_000
            if not 0 <= current < SPECIES_COUNT:
                raise ValueError(f"タマゴ技species marker範囲外: {current}")
            marker_count += 1
        else:
            if current is None or value >= MOVE_COUNT:
                raise ValueError("タマゴ技stream不正")
            rows[current].append(value)
    if marker_count != 1_388 or sum(map(len, rows)) != 8_831:
        raise ValueError("Stage61タマゴ技件数不一致")
    return rows


def _load_compatibility(raw: bytes, root_site: int, moves_site: int, slot_count: int) -> tuple[list[int], list[list[int]]]:
    table = _ptr(raw, root_site)
    moves_root = _ptr(raw, moves_site)
    move_ids = list(struct.unpack_from(f"<{slot_count}H", raw, moves_root))
    if any(not 0 < move_id < MOVE_COUNT for move_id in move_ids):
        raise ValueError("実行時TM/教え技move tableに範囲外IDがあります")
    rows = []
    for species_id in range(SPECIES_COUNT):
        bits = raw[table + species_id * 16:table + (species_id + 1) * 16]
        rows.append([move_ids[slot] for slot in range(slot_count) if bits[slot // 8] & (1 << (slot % 8))])
    return move_ids, rows


def _load_evolutions(raw: bytes, species_by_key: dict[str, dict[str, Any]], item_by_id: dict[int, dict[str, Any]], move_by_id: dict[int, dict[str, Any]]) -> tuple[list[list[dict[str, Any]]], int]:
    root = _ptr(raw, 0x4265C)
    requirements = _read_csv("vendor/vega_acquisition/content/evolution_requirements_553.csv")
    human = {(row["from_species_key"], row["to_species_key"]): row["integrated_condition"] for row in requirements}
    species_key_by_id = {int(row["id"]): row["species_key"] for row in species_by_key.values()}
    method_names = {
        1: "なつき度", 2: "なつき度（昼）", 3: "なつき度（夜）", 4: "レベル",
        5: "通信交換", 6: "道具を持たせて通信交換", 7: "道具使用",
        8: "レベル（攻撃>防御）", 9: "レベル（攻撃=防御）", 10: "レベル（攻撃<防御）",
        11: "カラサリス分岐", 12: "マユルド分岐", 13: "テッカニン分岐", 14: "ヌケニン分岐",
        15: "うつくしさ", 16: "雨/霧", 17: "指定タイプの技", 18: "手持ちの指定タイプ＋レベル",
        19: "指定場所", 20: "オス＋レベル", 21: "メス＋レベル", 22: "夜＋レベル",
        23: "昼＋レベル", 24: "夜＋持ち物", 25: "昼＋持ち物", 26: "指定技を覚えてレベル",
        27: "指定種族を手持ちに入れてレベル", 28: "指定時間帯", 29: "指定フラグ",
        30: "急所3回", 31: "性格値上位", 32: "性格値下位", 33: "被ダメージ＋場所",
        34: "指定場所で道具使用", 35: "道具を持たせてレベル", 36: "道具を持たせて道具使用",
        37: "指定技＋オス", 38: "指定技＋メス", 39: "夜に道具使用",
        40: "イッカネズミ分岐", 41: "ノココッチ分岐", 252: "テラスタル", 253: "キョダイマックス", 254: "メガシンカ",
    }
    result: list[list[dict[str, Any]]] = [[] for _ in range(SPECIES_COUNT)]
    total = 0
    for source_id in range(SPECIES_COUNT):
        for slot in range(16):
            method, param, target, extra = struct.unpack_from("<HHHH", raw, root + source_id * 128 + slot * 8)
            if method == 0:
                break
            if target >= SPECIES_COUNT:
                raise ValueError(f"進化先ID範囲外: {source_id}->{target}")
            source_key = species_key_by_id[source_id]
            target_key = species_key_by_id[target]
            condition = human.get((source_key, target_key))
            if not condition:
                label = method_names.get(method, f"method {method}")
                if method in {4, 8, 9, 10, 20, 21, 22, 23}:
                    condition = f"{label} Lv.{param}"
                elif method in {6, 7, 24, 25, 34, 35, 36, 39} and param in item_by_id:
                    condition = f"{label}: {item_by_id[param]['display_name']}"
                elif method in {17, 26, 37, 38} and param in move_by_id:
                    condition = f"{label}: {move_by_id[param]['display_name']}"
                elif method == 27 and param in species_key_by_id:
                    condition = f"{label}: {species_by_key[species_key_by_id[param]]['display_name']}"
                else:
                    condition = f"{label}（parameter={param}）"
            result[source_id].append({
                "slot": slot,
                "method_id": method,
                "parameter": param,
                "extra": extra,
                "target_id": target,
                "condition": condition,
                "evidence": "EXACT_ROM",
            })
            total += 1
    if total != 856:
        raise ValueError(f"Stage61進化件数不一致: {total}")
    return result, total


def _species_page(record: dict[str, Any], move_names: dict[int, str]) -> bytes:
    sid = record["id"]
    types = " / ".join(dict.fromkeys(t["name"] for t in record["types"]))
    stats = record["base_stats"]
    abilities = []
    for ability in record["abilities"]:
        if ability["id"]:
            abilities.append(f"- {ability['slot']}: **{ability['name']}** — {ability['description']}")
        else:
            abilities.append(f"- {ability['slot']}: なし")
    acquisitions = []
    route = record["acquisition"]["catalog_route"]
    host = ""
    if route["host_kind"] or route["x"] is not None:
        coordinates = f"座標 ({route['x']},{route['y']})" if route["x"] is not None else "座標—"
        host = f" / host {route['host_kind'] or '—'} `{route['host_key'] or '—'}` {coordinates}"
    acquisitions.append(
        f"- 基本経路（Stage26/56継承）: {_named(route['method'], METHOD_NAMES)} / {route['detail']} / "
        f"{route['location']} / {route['level_or_egg']} / 解禁 {_unlock(route['unlock'])} / "
        f"{_named(route['repeatability'], REPEAT_NAMES)}{host}"
    )
    for wild in record["acquisition"]["live_wild"]:
        acquisitions.append(
            f"- 通常野生（現ROM）: {wild['location']} `{wild['group']}/{wild['map']}`、{wild['mode']}、"
            f"出現率値 {wild['rate']}、Lv.{wild['level_min']}-{wild['level_max']}、slot {','.join(map(str, wild['slots']))}"
        )
    for ecology in record["acquisition"]["live_ecology"]:
        acquisitions.append(
            f"- 生態オーバーレイ（現ROM）: {ecology['location']} `{ecology['group']}/{ecology['map']}`、"
            f"{ecology['area']}・{ecology['layer']}、置換率 {ecology['rate_percent']}%、"
            f"Lv.{ecology['pre_level'][0]}-{ecology['pre_level'][1]} → Lv.{ecology['post_level'][0]}-{ecology['post_level'][1]}、"
            f"必要バッジ {ecology['min_badges']}、竿条件 {ecology['min_rod']}"
        )
    for raid in record["acquisition"]["raids"]:
        acquisitions.append(
            f"- Raid（Stage56継承）: {raid['location']}、{raid['pool']}、Lv.{raid['level_min']}-{raid['level_max']}、"
            f"weight {raid['weight']}、解禁 `{raid['unlock']}`、{raid['capture_policy']}"
        )
    for form in record["acquisition"]["form_supply"]:
        acquisitions.append(
            f"- フォーム供給（Stage56継承）: {_named(form['method'], METHOD_NAMES)}、基準種 "
            f"[{form['base_name']}](../pokemon/{form['base_species']:04d}.md)、解禁 {_unlock(form['unlock'])}、"
            f"{_named(form['repeatability'], REPEAT_NAMES)}、"
            f"配布対象={'はい' if form['distributable'] else 'いいえ'}"
        )
    pre_evolution_lines = [
        f"- ← [{edge['source_name']}](../pokemon/{edge['source_id']:04d}.md) (ID {edge['source_id']}): {edge['condition']}"
        for edge in record["pre_evolutions"]
    ] or ["- 進化元なし"]
    evolution_lines = [
        f"- → [{edge['target_name']}](../pokemon/{edge['target_id']:04d}.md) (ID {edge['target_id']}): {edge['condition']}"
        for edge in record["evolutions"]
    ] or ["- 進化先なし"]

    def move_list(rows: list[dict[str, Any]] | list[int], level: bool = False) -> str:
        if not rows:
            return "なし"
        if level:
            return "、".join(f"Lv.{row['level']} {move_names[row['move_id']]}" for row in rows)  # type: ignore[index]
        return "、".join(move_names[int(move_id)] for move_id in rows)

    lines = [
        "---",
        "wiki_schema_version: 1",
        "kind: pokemon",
        "stage: 61",
        f"active_rom_sha256: {ROM_SHA256}",
        f"canonical_id: {sid}",
        f"species_key: {record['key']}",
        "generated_by: scripts/build_stage61_wiki.py",
        "---",
        f'<a id="species-{sid:04d}"></a>',
        f"# {record['name']} — ID {sid}",
        "",
        f"[ポケモン索引へ](../POKEMON_INDEX.md) / [Wiki入口へ](../README.md)",
        "",
        "## 基本情報",
        "",
        f"- 種族キー: `{record['key']}`",
        f"- 全国図鑑番号: {record['national_no'] or '—'}",
        f"- フォームキー: `{record['form_key']}`" if record["form_key"] else "- フォームキー: —",
        f"- 区分: `{record['classification']}` / `{record['target_status']}`",
        f"- タイプ: **{types}**",
        f"- 捕獲率: {record['capture_rate']} / 基礎経験値: {record['exp_yield']}",
        f"- 初期なつき度: {record['friendship']} / タマゴ歩数係数: {record['egg_cycles']} / 成長: {record['growth']}",
        f"- タマゴグループ: {' / '.join(record['egg_groups'])}",
        f"- 性別比: {_gender_label(record['gender_ratio'])}",
        f"- 野生所持品: {record['held_items'][0]['name']} / {record['held_items'][1]['name']}",
        "",
        "## 種族値",
        "",
        "| HP | 攻撃 | 防御 | 特攻 | 特防 | 素早さ | 合計 |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        f"| {stats['hp']} | {stats['attack']} | {stats['defense']} | {stats['sp_attack']} | {stats['sp_defense']} | {stats['speed']} | {stats['total']} |",
        "",
        f"努力値: HP {record['ev_yield']['hp']} / 攻撃 {record['ev_yield']['attack']} / 防御 {record['ev_yield']['defense']} / 特攻 {record['ev_yield']['sp_attack']} / 特防 {record['ev_yield']['sp_defense']} / 素早さ {record['ev_yield']['speed']}",
        "",
        "## 特性",
        "",
        *(abilities or ["- なし"]),
        "",
        "## 入手方法",
        "",
        *acquisitions,
        "",
        "> 通常野生・生態オーバーレイは現行Stage61 ROMから直接抽出。基本経路・Raid・フォーム供給はStage26/56の統合済み正本をStage61が継承。全経路の現SHA実機走破監査は未完了です。",
        "",
        "## 進化",
        "",
        "### 進化元",
        "",
        *pre_evolution_lines,
        "",
        "### 進化先",
        "",
        *evolution_lines,
        "",
        "## 覚える技",
        "",
        f"- レベル技（現ROM）: {move_list(record['learnsets']['level_up'], True)}",
        f"- タマゴ技（現ROM）: {move_list(record['learnsets']['egg'])}",
        f"- TM/HM互換（実行時128枠：TM120＋HM8）: {move_list(record['learnsets']['machine_runtime'])}",
        f"- 教え技互換（実行時64枠）: {move_list(record['learnsets']['tutor_runtime'])}",
        "",
        "> TM01–120、HM01–08、教え技01–64は現行ROMの実行時tableと互換bitsetを直接読み取って表示しています。接続修正の詳細は [実行時の状態](../RUNTIME_LIMITATIONS.md)。",
        "",
        "## 証拠区分",
        "",
        "- 種族値・タイプ・特性・習得技・進化: `EXACT_ROM`",
        "- 通常野生・生態オーバーレイ: `EXACT_ROM`",
        "- 基本取得経路・Raid・フォーム供給: `INHERITED_INTEGRATED`",
        "",
    ]
    return "\n".join(lines).encode()


def _item_sources(item: dict[str, Any]) -> str:
    sources = []
    primary = item["supply"]
    source = primary["source"]
    value = primary["price"]
    if source == "MONEY_SHOP":
        cost = f"{value}円"
    elif source == "BP_SHOP":
        cost = f"{value} BP"
    elif source == "RESEARCH_SHOP":
        cost = f"{value}研究ポイント"
    elif source in {"RAID_REWARD", "FACTORY_REWARD"}:
        cost = f"weight/段階値 {value}"
    else:
        cost = "価格なし" if not value else f"設定値 {value}"
    sources.append(
        f"{_named(source, SOURCE_NAMES)}（解禁 {_unlock(primary['unlock'])}、"
        f"{_named(primary['repeatability'], REPEAT_NAMES)}、数量 {primary['quantity']}、{cost}）"
    )
    for source in item["current_qol_sources"]:
        quantity = source.get("quantity", 1)
        sources.append(
            f"{source.get('owner', 'QOL')} / {source.get('currency', 'NONE')} {source.get('price', 0)} / "
            f"数量 {quantity} / {_named(source.get('repeatability', ''), REPEAT_NAMES)} / 解禁 {_unlock(source.get('unlock', ''))}"
        )
    for placement in item["placements"]:
        sources.append(
            f"{placement['location']} `{placement['map_key']}` / {placement['placement_type']} / 数量 {placement['quantity']} / "
            f"解禁 {_unlock(placement['unlock'])} / {_named(placement['repeatability'], REPEAT_NAMES)}"
        )
    return "<br>".join(_md(source) for source in sources)


def _build() -> tuple[dict[str, bytes], dict[str, Any]]:
    raw = (ROOT / ROM_REL).read_bytes()
    identity = _identity(raw)
    species_manifest = _read_csv("manifests/species_ids.csv")
    move_manifest = _read_csv("manifests/move_ids.csv")
    ability_manifest = _read_csv("manifests/ability_ids.csv")
    item_manifest = _read_csv("manifests/item_ids.csv")
    _require_contiguous(species_manifest, "id", SPECIES_COUNT, "Species")
    _require_contiguous(move_manifest, "id", MOVE_COUNT, "Move")
    _require_contiguous(ability_manifest, "id", ABILITY_COUNT, "Ability")
    _require_contiguous(item_manifest, "id", ITEM_COUNT, "Item")

    ids = _read_json("generated/engine/ids/id_spaces.json")
    move_port = _read_json("generated/engine/moves/move_port.json")
    supply = _read_json("content/collection_supply_v1/canonical_model.json")
    route_rows = _read_csv("vendor/vega_acquisition/content/species_acquisition_routes.csv")
    map_catalog = _read_json("reports/generated/stage61_critical_release_map_display_catalog.json")
    if map_catalog["stage"] != 61 or map_catalog["status"] != "PASS" or len(map_catalog["maps"]) != 678:
        raise ValueError("Stage61 map display catalog不正")
    map_names = {(row["group"], row["map"]): row["actual_name"] for row in map_catalog["maps"]}

    species_by_id = {int(row["id"]): row for row in species_manifest}
    species_by_key = {row["species_key"]: row for row in species_manifest}
    move_by_id = {int(row["id"]): row for row in move_manifest}
    ability_by_id = {row["id"]: row for row in ids["abilities"]}
    item_by_id = {row["id"]: row for row in ids["items"]}
    item_manifest_by_id = {int(row["id"]): row for row in item_manifest}
    route_by_id = {int(row["canonical_id"]): row for row in route_rows}
    if set(route_by_id) != set(range(SPECIES_COUNT)):
        raise ValueError("全Speciesの取得経路が揃っていません")

    move_records = []
    live_move_blob = raw[MOVE_TABLE_OFFSET:MOVE_TABLE_OFFSET + MOVE_COUNT * 12]
    if _sha(live_move_blob) != "3093301fa53069b82c34ed37b2359628d38aa7fbd661e956cc8d1a9d35be5c4a":
        raise ValueError("Stage61 move table hash不一致")
    for move in move_port["moves"]:
        mid = move["id"]
        effect, power, type_id, accuracy, pp, secondary, target, priority, flags, z_power, split, z_effect = struct.unpack_from("<BBBBBBBBBBBB", live_move_blob, mid * 12)
        battle = move["battle"]
        live = {"effect": effect, "power": power, "type": type_id, "accuracy": accuracy, "pp": pp, "secondary": secondary, "target": target, "priority": priority if priority < 128 else priority - 256, "flags": flags, "split": split, "z_move_power": z_power, "z_move_effect": z_effect}
        # Vega固有技39件のeffectだけは移植metadataが0のため、現ROM値を正とする。
        if any(live[key] != battle[key] for key in live if key != "effect"):
            raise ValueError(f"Move {mid} metadataと現ROMが不一致")
        move_records.append({
            "id": mid,
            "key": move["move_key"],
            "name": move["display_name"],
            "type": {"id": type_id, "name": TYPE_NAMES.get(type_id, f"type-{type_id}")},
            "category": MOVE_SPLITS.get(split, f"split-{split}"),
            "power": power,
            "accuracy": accuracy,
            "pp": pp,
            "priority": live["priority"],
            "effect_id": effect,
            "secondary_percent": secondary,
            "target_id": target,
            "flags": flags,
            "description": move["description"]["text"].rstrip(),
            "evidence": "EXACT_ROM",
        })
    move_record_by_id = {row["id"]: row for row in move_records}
    move_names = {row["id"]: row["name"] for row in move_records}

    base_blob = raw[BASE_STATS_OFFSET:BASE_STATS_OFFSET + SPECIES_COUNT * 32]
    if _sha(base_blob) != "913bbbc26e1ead40416af5a3a28907ce82d44b4d1d90b1c400779b86eecbc00a":
        raise ValueError("Stage61 BaseStats hash不一致")
    level_moves = _load_level_moves(raw)
    egg_moves = _load_egg_moves(raw)
    machine_move_ids, machine_rows = _load_compatibility(raw, 0x432B4, 0x1263D8, 128)
    tutor_move_ids, tutor_rows = _load_compatibility(raw, 0x121420, 0x1213D4, 64)
    evolutions, evolution_count = _load_evolutions(raw, species_by_key, item_by_id, move_by_id)
    wild = _load_wild(raw)
    ecology = _load_ecology(raw)

    wild_by_species: dict[int, list[dict[str, Any]]] = defaultdict(list)
    wild_rows = []
    for header in wild["headers"]:
        group, map_id = header["group"], header["map"]
        location = map_names.get((group, map_id), f"map {group}/{map_id}")
        for mode, table in header["modes"].items():
            if not table:
                continue
            species_slots: dict[int, list[dict[str, int]]] = defaultdict(list)
            for slot in table["slots"]:
                species_slots[slot["species"]].append(slot)
            for species_id, slots in species_slots.items():
                entry = {
                    "group": group, "map": map_id, "location": location,
                    "mode": WILD_MODE_NAMES[mode], "rate": table["rate"],
                    "level_min": min(row["low"] for row in slots),
                    "level_max": max(row["high"] for row in slots),
                    "slots": [row["slot"] for row in slots], "evidence": "EXACT_ROM",
                }
                wild_by_species[species_id].append(entry)
                wild_rows.append({"species_id": species_id, **entry})

    ecology_by_species: dict[int, list[dict[str, Any]]] = defaultdict(list)
    ecology_rows = []
    for row in ecology:
        location = map_names.get((row["group"], row["map"]), f"map {row['group']}/{row['map']}")
        for slot, species_id in enumerate(row["species"]):
            entry = {
                "table_index": row["index"], "candidate_slot": slot,
                "group": row["group"], "map": row["map"], "location": location,
                "area": row["area"], "layer": row["layer"], "rate_percent": row["rate_percent"],
                "threshold": row["threshold"], "pre_level": row["pre_levels"][slot],
                "post_level": row["post_levels"][slot], "min_badges": row["min_badges"][slot],
                "min_rod": row["min_rods"][slot], "evidence": "EXACT_ROM",
            }
            ecology_by_species[species_id].append(entry)
            ecology_rows.append({"species_id": species_id, **entry})

    host_by_pool = {row["pool_id"]: row for row in supply["hosts"]}
    raids_by_species: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in supply["pool_entries"]:
        host = host_by_pool[row["pool_id"]]
        physical = host["physical"]
        raids_by_species[row["species"]].append({
            "pool": row["pool_key"], "host": host["host_key"],
            "location": map_names.get((physical["map_group"], physical["map_num"]), f"map {physical['map_group']}/{physical['map_num']}"),
            "group": physical["map_group"], "map": physical["map_num"],
            "level_min": row["level_min"], "level_max": row["level_max"],
            "weight": row["weight"], "unlock": row["unlock"], "capture_policy": row["capture_policy"],
            "evidence": "INHERITED_INTEGRATED",
        })
    forms_by_species: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in supply["forms"]:
        if row["target_species"] not in species_by_id or row["base_species"] not in species_by_id:
            raise ValueError("form supplyのSpecies参照が範囲外です")
        forms_by_species[row["target_species"]].append({
            "base_species": row["base_species"], "base_name": species_by_id[row["base_species"]]["display_name"],
            "method": row["method"], "unlock": row["unlock"],
            "repeatability": row["repeatability"], "distributable": row["distributable"],
            "collection_policy": row["collection_policy"], "evidence": "INHERITED_INTEGRATED",
        })

    item_placements: dict[str, list[dict[str, Any]]] = defaultdict(list)
    bindings: dict[str, tuple[int, int]] = {}
    for path in ("content/map_bindings.csv", "manifests/map_ids.csv"):
        for row in _read_csv(path):
            if row.get("group_id") and row.get("map_id"):
                bindings[row["map_key"]] = (int(row["group_id"]), int(row["map_id"]))
                if row.get("physical_map_key"):
                    bindings[row["physical_map_key"]] = (int(row["group_id"]), int(row["map_id"]))
    for path in ("manifests/kanto_items.csv", "manifests/tohoku_items.csv"):
        for row in _read_csv(path):
            pair = bindings.get(row["map_key"])
            location = map_names.get(pair, row["logical_location_key"]) if pair else row["logical_location_key"]
            item_placements[row["item_key"]].append({
                "map_key": row["map_key"], "location": location, "placement_type": row["placement_type"],
                "quantity": int(row["quantity"]), "unlock": row["unlock_key"], "repeatability": row["repeatability"],
                "evidence": "INHERITED_INTEGRATED",
            })
    qol_audit = _read_json("reports/generated/stage58_qol_economy_audit.json")
    if qol_audit["stage"] != 58 or qol_audit["status"] != "PASS":
        raise ValueError("Stage58 QOL economy audit不正")
    qol_by_key = {row["item_key"]: row for row in qol_audit["after"]["qol_effect_items"]["rows"]}

    item_records = []
    for item_id in range(ITEM_COUNT):
        info = item_by_id[item_id]
        manifest = item_manifest_by_id[item_id]
        source = supply["items"][item_id]
        if source["item_id"] != item_id or source["item_key"] != info["item_key"]:
            raise ValueError(f"item供給表のID/key順序不一致: {item_id}")
        qol = qol_by_key.get(info["item_key"], {})
        item_records.append({
            "id": item_id, "key": info["item_key"], "name": info["display_name"],
            "description": info["description"].rstrip(), "classification": info["classification"],
            "pocket": info["pocket"], "role": info["role"], "importance": info["importance"],
            "price": info["price"], "ball_kind": info["ball_kind"],
            "is_evolution_stone": info["is_evolution_stone"], "is_evolution_item": info["is_evolution_item"],
            "hold_effect": info["hold_effect_key"], "field_effect": info["field_effect_key"],
            "battle_effect": info["battle_effect_key"], "consume_policy": info["consume_policy"],
            "supply": source, "placements": item_placements.get(info["item_key"], []),
            "current_qol_sources": qol.get("sources", []),
            "effect_execution_evidence": qol.get("effect_execution_evidence"),
            "manifest_notes": manifest["notes"],
        })

    ability_records = [{
        "id": row["id"], "key": row["ability_key"], "name": row["display_name"],
        "description": row["description"].rstrip(), "rating": row["rating"], "effect_key": row["effect_key"],
    } for row in ids["abilities"]]
    ability_names = {row["id"]: row["name"] for row in ability_records}
    item_names = {row["id"]: row["name"] for row in item_records}
    item_names[0] = "なし"

    species_records = []
    incoming_by_species: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for source_id, edges in enumerate(evolutions):
        for edge in edges:
            incoming_by_species[edge["target_id"]].append({
                "source_id": source_id,
                "source_key": species_by_id[source_id]["species_key"],
                "source_name": species_by_id[source_id]["display_name"],
                "condition": edge["condition"],
                "evidence": "EXACT_ROM",
            })
    for species_id in range(SPECIES_COUNT):
        manifest = species_by_id[species_id]
        data = base_blob[species_id * 32:(species_id + 1) * 32]
        hp, attack, defense, speed, sp_attack, sp_defense, type1, type2, capture_rate, _pad = struct.unpack_from("<10B", data)
        ev_bits = struct.unpack_from("<H", data, 10)[0]
        held1, held2 = struct.unpack_from("<HH", data, 12)
        gender, egg_cycles, friendship, growth, egg1, egg2 = struct.unpack_from("<6B", data, 16)
        ability1 = struct.unpack_from("<H", data, 22)[0]
        ability2 = struct.unpack_from("<H", data, 26)[0]
        hidden = struct.unpack_from("<H", data, 28)[0]
        exp_yield = struct.unpack_from("<H", data, 30)[0]
        for ref, label, limit in ((type1, "type", 25), (type2, "type", 25), (ability1, "ability", ABILITY_COUNT), (ability2, "ability", ABILITY_COUNT), (hidden, "ability", ABILITY_COUNT), (held1, "item", ITEM_COUNT), (held2, "item", ITEM_COUNT)):
            if ref >= limit:
                raise ValueError(f"Species {species_id} {label}参照範囲外: {ref}")
        route = route_by_id[species_id]
        group = int(route["group_id"]) if route["group_id"] else None
        map_id = int(route["map_id"]) if route["map_id"] else None
        location = map_names.get((group, map_id), route["logical_location_key"] or route["physical_map_key"] or "—") if group is not None else (route["logical_location_key"] or "—")
        base_stats = {"hp": hp, "attack": attack, "defense": defense, "sp_attack": sp_attack, "sp_defense": sp_defense, "speed": speed}
        base_stats["total"] = sum(base_stats.values())
        edge_rows = []
        for edge in evolutions[species_id]:
            target = species_by_id[edge["target_id"]]
            edge_rows.append({**edge, "target_key": target["species_key"], "target_name": target["display_name"]})
        species_records.append({
            "id": species_id, "key": manifest["species_key"], "name": manifest["display_name"],
            "national_no": int(manifest["canonical_national_dex"] or 0), "form_key": manifest["form_key"],
            "classification": manifest["classification"], "target_status": route["target_status"],
            "types": [{"id": type1, "name": TYPE_NAMES.get(type1, f"type-{type1}")}, {"id": type2, "name": TYPE_NAMES.get(type2, f"type-{type2}")}],
            "base_stats": base_stats, "capture_rate": capture_rate,
            "ev_yield": {"hp": (ev_bits >> 0) & 3, "attack": (ev_bits >> 2) & 3, "defense": (ev_bits >> 4) & 3, "speed": (ev_bits >> 6) & 3, "sp_attack": (ev_bits >> 8) & 3, "sp_defense": (ev_bits >> 10) & 3},
            "held_items": [{"id": held1, "name": item_names[held1]}, {"id": held2, "name": item_names[held2]}],
            "gender_ratio": gender, "egg_cycles": egg_cycles, "friendship": friendship,
            "growth": GROWTH_NAMES.get(growth, f"growth-{growth}"),
            "egg_groups": [EGG_GROUP_NAMES.get(egg1, f"group-{egg1}"), EGG_GROUP_NAMES.get(egg2, f"group-{egg2}")],
            "abilities": [
                {"slot": "通常1", "id": ability1, "name": ability_names[ability1], "description": ability_by_id[ability1]["description"].rstrip()},
                {"slot": "通常2", "id": ability2, "name": ability_names[ability2], "description": ability_by_id[ability2]["description"].rstrip()},
                {"slot": "隠れ", "id": hidden, "name": ability_names[hidden], "description": ability_by_id[hidden]["description"].rstrip()},
            ],
            "exp_yield": exp_yield,
            "acquisition": {
                "catalog_route": {
                    "method": route["method"], "detail": route["method_detail"], "region": route["region"],
                    "location": location, "group": group, "map": map_id, "unlock": route["unlock_key"],
                    "level_or_egg": route["level_or_egg"], "repeatability": route["repeatability"],
                    "host_kind": route["host_kind"], "host_key": route["host_key"],
                    "host_local_id": route["host_local_id_or_bg_index"],
                    "x": int(route["x"]) if route["x"] else None, "y": int(route["y"]) if route["y"] else None,
                    "elevation": int(route["elevation"]) if route["elevation"] else None,
                    "evidence": "INHERITED_INTEGRATED",
                },
                "live_wild": wild_by_species.get(species_id, []), "live_ecology": ecology_by_species.get(species_id, []),
                "raids": raids_by_species.get(species_id, []), "form_supply": forms_by_species.get(species_id, []),
            },
            "pre_evolutions": incoming_by_species.get(species_id, []), "evolutions": edge_rows,
            "learnsets": {"level_up": level_moves[species_id], "egg": egg_moves[species_id], "machine_runtime": machine_rows[species_id], "tutor_runtime": tutor_rows[species_id]},
            "page": f"pokemon/{species_id:04d}.md",
        })

    files: dict[str, bytes] = {}
    source_hashes = {path: _sha((ROOT / path).read_bytes()) for path in SOURCE_PATHS}
    files["data/species.jsonl"] = _jsonl_bytes(species_records)
    files["data/moves.jsonl"] = _jsonl_bytes(move_records)
    files["data/abilities.jsonl"] = _jsonl_bytes(ability_records)
    files["data/items.jsonl"] = _jsonl_bytes(item_records)
    files["data/wild_encounters.jsonl"] = _jsonl_bytes(wild_rows)
    files["data/ecology_encounters.jsonl"] = _jsonl_bytes(ecology_rows)

    search_rows = []
    for record in species_records:
        search_rows.append({"kind": "species", "id": record["id"], "name": record["name"], "aliases": [record["key"], record["form_key"]], "page": record["page"], "anchor": f"species-{record['id']:04d}"})
    for kind, records, page in (("move", move_records, "MOVE_INDEX.md"), ("ability", ability_records, "ABILITY_INDEX.md"), ("item", item_records, "ITEM_INDEX.md")):
        for record in records:
            search_rows.append({"kind": kind, "id": record["id"], "name": record["name"], "aliases": [record["key"]], "page": page, "anchor": f"{kind}-{record['id']:04d}"})
    files["data/search_index.jsonl"] = _jsonl_bytes(search_rows)

    for record in species_records:
        files[record["page"]] = _species_page(record, move_names)

    pokemon_index = [
        "# Stage61 ポケモン索引", "", "[Wiki入口へ](README.md)", "",
        "名前が重複するフォームがあるため、IDまたはspecies keyでも検索してください。ID 0と内部・戦闘専用フォームも完全性のため収録しています。", "",
        "| ID | 全国No. | 名前 | フォーム | タイプ | 基本入手経路 | 詳細 |", "|---:|---:|---|---|---|---|---|",
    ]
    for record in species_records:
        route = record["acquisition"]["catalog_route"]
        type_label = "/".join(dict.fromkeys(t["name"] for t in record["types"]))
        pokemon_index.append(f"| {record['id']} | {record['national_no'] or '—'} | {_md(record['name'])} | {_md(record['form_key'])} | {type_label} | {_md(route['method'])}: {_md(route['location'])} | [開く]({record['page']}) |")
    pokemon_index.append("")
    files["POKEMON_INDEX.md"] = "\n".join(pokemon_index).encode()

    move_index = ["# Stage61 技索引", "", "[Wiki入口へ](README.md)", "", "全1,063 ID。性能値は現ROMの12-byte move tableから照合済みです。", "", "| ID | 技 | タイプ | 分類 | 威力 | 命中 | PP | 優先度 | 説明 |", "|---:|---|---|---|---:|---:|---:|---:|---|"]
    for move in move_records:
        move_index.append(f'| <a id="move-{move["id"]:04d}"></a>{move["id"]} | {_md(move["name"])} | {move["type"]["name"]} | {move["category"]} | {move["power"]} | {move["accuracy"]} | {move["pp"]} | {move["priority"]} | {_md(move["description"])} |')
    files["MOVE_INDEX.md"] = ("\n".join(move_index) + "\n").encode()

    ability_index = ["# Stage61 特性索引", "", "[Wiki入口へ](README.md)", "", "全312 ID。", "", "| ID | 特性 | 説明 | 評価値 |", "|---:|---|---|---:|"]
    for ability in ability_records:
        ability_index.append(f'| <a id="ability-{ability["id"]:04d}"></a>{ability["id"]} | {_md(ability["name"])} | {_md(ability["description"])} | {ability["rating"]} |')
    files["ABILITY_INDEX.md"] = ("\n".join(ability_index) + "\n").encode()

    major_ids = {
        row["id"] for row in item_records
        if row["importance"] or row["role"] in {"KEY_ITEM", "BALL", "TM_HM"}
        or row["is_evolution_item"] or row["is_evolution_stone"] or row["current_qol_sources"]
        or row["id"] >= 988
    }
    item_guide = [
        "# Stage61 アイテム入手ガイド", "", "[Wiki入口へ](README.md)", "",
        f"主要アイテム {len(major_ids)}件を掲載。主要判定はkey item・Ball・TM/HM・進化道具・QOL効果品・追加ID 988以降です。全999件は `data/items.jsonl` で検索できます。", "",
        "供給欄の先頭はStage56の全item供給正本です。QOL効果品はStage58の実効供給を続けて表示します。`VEGA_EXISTING` は従来入手を意味し、精密座標が未抽出のものは推測していません。", "",
        "| ID | アイテム | 役割 | 説明 | 入手・供給 |", "|---:|---|---|---|---|",
    ]
    for item in item_records:
        if item["id"] not in major_ids:
            continue
        item_guide.append(f'| <a id="item-{item["id"]:04d}"></a>{item["id"]} | {_md(item["name"])} | {_md(item["role"])} | {_md(item["description"])} | {_item_sources(item)} |')
    files["ITEM_GUIDE.md"] = ("\n".join(item_guide) + "\n").encode()

    item_index = [
        "# Stage61 全アイテム索引", "", "[Wiki入口へ](README.md) / [主要アイテム入手ガイドへ](ITEM_GUIDE.md)", "",
        "全999 ID。供給はStage56の全item供給正本を表示し、主要アイテムの複数経路は入手ガイドへ分離しています。", "",
        "| ID | アイテム | 役割 | pocket | 説明 | 主供給 | 解禁 | 反復性 | 詳細 |", "|---:|---|---|---|---|---|---|---|---|",
    ]
    for item in item_records:
        detail = f"[主要経路](ITEM_GUIDE.md#item-{item['id']:04d})" if item["id"] in major_ids else "—"
        item_index.append(
            f'| <a id="item-{item["id"]:04d}"></a>{item["id"]} | {_md(item["name"])} | {_md(item["role"])} | {_md(item["pocket"])} | '
            f'{_md(item["description"])} | {_md(item["supply"]["source"])} | `{_md(item["supply"]["unlock"])}` | {_md(item["supply"]["repeatability"])} | {detail} |'
        )
    files["ITEM_INDEX.md"] = ("\n".join(item_index) + "\n").encode()

    unlock_keys = {record["acquisition"]["catalog_route"]["unlock"] or "NONE" for record in species_records}
    unlock_keys.update(form["unlock"] for record in species_records for form in record["acquisition"]["form_supply"])
    unlock_keys.update(raid["unlock"] for record in species_records for raid in record["acquisition"]["raids"])
    unlock_keys.update(item["supply"]["unlock"] for item in item_records)
    unlock_keys.update(placement["unlock"] for item in item_records for placement in item["placements"])
    unlock_keys.update(source.get("unlock", "NONE") or "NONE" for item in item_records for source in item["current_qol_sources"])
    glossary = [
        "# Stage61 Wiki 用語集", "", "[Wiki入口へ](README.md)", "",
        "## 入手方法", "", "| 正本key | 表示 |", "|---|---|",
        *[f"| `{key}` | {_md(value)} |" for key, value in sorted(METHOD_NAMES.items())],
        "", "## アイテム供給", "", "| 正本key | 表示 |", "|---|---|",
        *[f"| `{key}` | {_md(value)} |" for key, value in sorted(SOURCE_NAMES.items())],
        "", "## 再入手性", "", "| 正本key | 表示 |", "|---|---|",
        *[f"| `{key}` | {_md(value)} |" for key, value in sorted(REPEAT_NAMES.items())],
        "", "## 解禁条件", "", "| 正本key | 意味 |", "|---|---|",
        *[f"| `{key or 'NONE'}` | {_md(_unlock_desc(key))} |" for key in sorted(unlock_keys)],
        "",
        "未翻訳の解禁keyは意味を推測せず、そのまま残しています。バッジ・認定章の数字は必要個数または段階です。",
        "",
    ]
    files["GLOSSARY.md"] = "\n".join(glossary).encode()

    wild_page = ["# Stage61 野生遭遇一覧", "", "[Wiki入口へ](README.md)", "", f"現行ROMから直接抽出: 通常野生 {wild['header_count']} header / {wild['slot_count']} slot、生態オーバーレイ {len(ecology)} table / {len(ecology_rows)} candidate assignment。", "", "## 通常野生", "", "| map | 場所 | 方法 | 種族 | Lv. | rate値 | slots |", "|---|---|---|---|---:|---:|---|"]
    for row in wild_rows:
        species = species_by_id[row["species_id"]]
        wild_page.append(f"| `{row['group']}/{row['map']}` | {_md(row['location'])} | {row['mode']} | [{_md(species['display_name'])}](pokemon/{row['species_id']:04d}.md) | {row['level_min']}-{row['level_max']} | {row['rate']} | {','.join(map(str,row['slots']))} |")
    wild_page += ["", "## 生態オーバーレイ", "", "| table | map | 場所 | 層 | 種族 | 置換率 | 変更前Lv. | 変更後Lv. | 条件 |", "|---:|---|---|---|---|---:|---:|---:|---|"]
    for row in ecology_rows:
        species = species_by_id[row["species_id"]]
        wild_page.append(f"| {row['table_index']} | `{row['group']}/{row['map']}` | {_md(row['location'])} | {row['area']}・{row['layer']} | [{_md(species['display_name'])}](pokemon/{row['species_id']:04d}.md) | {row['rate_percent']}% | {row['pre_level'][0]}-{row['pre_level'][1]} | {row['post_level'][0]}-{row['post_level'][1]} | badge {row['min_badges']} / rod {row['min_rod']} |")
    files["WILD_ENCOUNTERS.md"] = ("\n".join(wild_page) + "\n").encode()

    type_rows = [row for row in ids["types"] if row["id"] in TYPE_NAMES]
    type_page = ["# Stage61 タイプ相性", "", "[Wiki入口へ](README.md)", "", "行が攻撃側、列が防御側です。`0`=無効、`0.5`=半減、`1`=等倍、`2`=弱点。", "", "|攻撃\\防御|" + "|".join(TYPE_NAMES[row["id"]] for row in type_rows) + "|", "|---|" + "|".join("---:" for _ in type_rows) + "|"]
    for attacker in type_rows:
        values = []
        for defender in type_rows:
            raw_value = attacker["effectiveness"][defender["id"]]
            values.append("0" if raw_value == 1 else str(raw_value / 1000).rstrip("0").rstrip("."))
        type_page.append(f"|{TYPE_NAMES[attacker['id']]}|" + "|".join(values) + "|")
    files["TYPE_CHART.md"] = ("\n".join(type_page) + "\n").encode()

    files["RUNTIME_LIMITATIONS.md"] = f"""# Stage61 実行時の既知制約

[Wiki入口へ](README.md)

## ROM候補の状態

- SHA-256: `{ROM_SHA256}`
- `candidate_status=CANDIDATE`
- strict全件監査: `DEFERRED_AUDIT`
- 通常野生、ecology、種族値、技性能、習得表、進化表は現ROMから直接抽出しています。
- 取得イベント、Raid、フォーム供給、item供給は統合済みのStage26/56/58正本を継承していますが、現SHAで全経路を手動走破したという意味ではありません。

## TM/HMと教え技（接続修正済み）

`gTMHMMoves` は128件（TM01–120＋HM01–08）へ再配置し、TM51–58と旧HM slotの衝突を解消しました。HM互換は実行時index 121–128へ移し、V4のTM51–58互換は設計入力から再構築しています。

`gTutorMoves` はV4の64件を全件接続し、通常教え技consumerの上限をslot 01–64へ修正しました。16件目以降が終端や隣接dataをMove IDとして誤読する状態はありません。

このWikiの各ポケモンページは、現ROMの実行時tableと互換bitsetからTM/HM 128件・教え技64件を直接抽出して掲載します。
ここで示すのは互換判定の接続状態であり、NPC配置・価格・解禁経路の一覧ではありません。
""".encode()

    files["CODEX_INDEX.md"] = f"""# Codex用 Stage61 Wiki索引

プレイ中の質問では、原則としてスクリプトやgeneratorを調べる前にこのWikiを使います。

1. 名前・key・IDを `docs/wiki/stage61/data/search_index.jsonl` で検索する。
2. `page` で示されたMarkdownだけを読む。
3. 精密な再検証が必要な場合だけ `data/*.jsonl` と [証拠・制約](RUNTIME_LIMITATIONS.md) を確認する。

```bash
rg 'リープン|SPECIES_KEY_VEGA_001' docs/wiki/stage61/data/search_index.jsonl
rg 'マスターボール|ITEM_KEY_MASTER_BALL' docs/wiki/stage61/data/search_index.jsonl
```

現行ROM SHA-256: `{ROM_SHA256}`。ROMが変わった場合は `make stage61-wiki` で再生成し、`make stage61-wiki-check` を通すまで旧Wikiを現行扱いしません。
""".encode()

    files["README.md"] = f"""# Pokémon Vega Stage61 プレイWiki

現行Stage61 ROMに固定した、プレイヤー向け・Codex向けの参照資料です。

- ROM: `{ROM_REL}`
- SHA-256: `{ROM_SHA256}`
- ポケモン: {SPECIES_COUNT} ID（内部・フォームを含む）
- 技: {MOVE_COUNT} ID
- 特性: {ABILITY_COUNT} ID
- アイテム: {ITEM_COUNT} ID

## 読む順番

- Codexの検索手順: [CODEX_INDEX.md](CODEX_INDEX.md)
- ポケモンの入手・能力・特性・全習得技: [POKEMON_INDEX.md](POKEMON_INDEX.md)
- 主要アイテムの入手: [ITEM_GUIDE.md](ITEM_GUIDE.md)
- 全アイテム索引: [ITEM_INDEX.md](ITEM_INDEX.md)
- 全技: [MOVE_INDEX.md](MOVE_INDEX.md)
- 全特性: [ABILITY_INDEX.md](ABILITY_INDEX.md)
- タイプ相性: [TYPE_CHART.md](TYPE_CHART.md)
- 通常野生・生態オーバーレイ: [WILD_ENCOUNTERS.md](WILD_ENCOUNTERS.md)
- 入手方法・解禁条件の用語集: [GLOSSARY.md](GLOSSARY.md)
- 証拠レベルと既知制約: [RUNTIME_LIMITATIONS.md](RUNTIME_LIMITATIONS.md)

## 情報の信頼度

- `EXACT_ROM`: 現行ROMから直接抽出・参照整合を検査。
- `INHERITED_INTEGRATED`: 以前のstageで統合・検証済みの正本をStage61が継承。
- `DEFERRED_AUDIT`: 現行候補ROMでの全経路手動走破は未完了。

取得場所が複数ある場合、各ポケモンページは現ROMの通常野生・生態オーバーレイ、Raid、基本取得経路を併記します。`VEGA_EXISTING` itemなど精密場所が未抽出の情報は、推測で補いません。

## 再生成・検査

```bash
make stage61-wiki
make stage61-wiki-check
```

生成物は時刻を含まず、同じ入力から同じbyteになります。機械可読の完全データは `data/*.jsonl` です。
""".encode()

    index = {
        "schema_version": 1, "stage": 61, "active_rom": identity,
        "counts": {
            "species": len(species_records), "moves": len(move_records), "abilities": len(ability_records), "items": len(item_records),
            "level_move_records_raw": 28_874, "level_moves": sum(len(row) for row in level_moves), "egg_moves": sum(len(row) for row in egg_moves),
            "machine_runtime_slots": len(machine_move_ids), "machine_runtime_compatibilities": sum(map(len, machine_rows)),
            "tutor_runtime_slots": len(tutor_move_ids), "tutor_runtime_compatibilities": sum(map(len, tutor_rows)),
            "evolutions": evolution_count, "wild_headers": wild["header_count"], "wild_slots": wild["slot_count"],
            "ecology_tables": len(ecology), "ecology_assignments": len(ecology_rows), "major_items": len(major_ids),
        },
        "runtime_move_slots": {"machine": machine_move_ids, "tutor": tutor_move_ids},
        "source_hashes": source_hashes,
        "evidence_levels": {
            "EXACT_ROM": "現行Stage61 ROMから直接抽出またはbyte照合",
            "INHERITED_INTEGRATED": "過去stageで統合済みのtracked正本をStage61が継承",
            "DEFERRED_AUDIT": "現行候補ROMでの全経路実機走破は未完了",
        },
        "build": "python3 scripts/build_stage61_wiki.py build",
        "check": "python3 scripts/build_stage61_wiki.py check",
    }
    files["data/index.json"] = _json_bytes(index)
    return files, index


def _report(files: dict[str, bytes], index: dict[str, Any]) -> bytes:
    return _json_bytes({
        "schema_version": 1, "task": "USER-20260903-STAGE61-WIKI", "stage": 61, "status": "PASS",
        "active_rom": index["active_rom"], "counts": index["counts"],
        "wiki_root": "docs/wiki/stage61", "file_count": len(files),
        "files": [{"path": path, "size": len(data), "sha256": _sha(data)} for path, data in sorted(files.items())],
    })


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(data)
        temp = Path(handle.name)
    os.replace(temp, path)


def build() -> None:
    files, index = _build()
    expected = {OUT / relative for relative in files}
    if OUT.exists():
        for path in sorted((p for p in OUT.rglob("*") if p.is_file()), reverse=True):
            if path not in expected:
                path.unlink()
    for relative, data in files.items():
        _atomic_write(OUT / relative, data)
    _atomic_write(REPORT, _report(files, index))
    print(f"Stage61 Wiki生成完了: files={len(files)} species={index['counts']['species']} sha256={ROM_SHA256}")


def check() -> None:
    files, index = _build()
    expected_paths = {OUT / relative for relative in files}
    actual_paths = {path for path in OUT.rglob("*") if path.is_file()} if OUT.exists() else set()
    errors = []
    for relative, expected in files.items():
        path = OUT / relative
        if not path.exists():
            errors.append(f"missing: {path.relative_to(ROOT)}")
        elif path.read_bytes() != expected:
            errors.append(f"drift: {path.relative_to(ROOT)}")
    for path in sorted(actual_paths - expected_paths):
        errors.append(f"unexpected: {path.relative_to(ROOT)}")
    expected_report = _report(files, index)
    if not REPORT.exists():
        errors.append(f"missing: {REPORT.relative_to(ROOT)}")
    elif REPORT.read_bytes() != expected_report:
        errors.append(f"drift: {REPORT.relative_to(ROOT)}")
    if errors:
        raise SystemExit("Stage61 Wiki check FAIL\n" + "\n".join(errors[:40]))
    print(f"Stage61 Wiki check PASS: files={len(files)} species={index['counts']['species']} sha256={ROM_SHA256}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "check"))
    args = parser.parse_args()
    build() if args.command == "build" else check()


if __name__ == "__main__":
    main()
