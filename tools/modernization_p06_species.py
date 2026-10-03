#!/usr/bin/env python3
"""工程6の未採用候補を隔離し、採用済み種族差分だけを監査する。"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


class P06SpeciesError(RuntimeError):
    """入力固定、候補区分、stable identity、consumer ABIの違反。"""


STAT_KEYS = ("hp", "attack", "defense", "sp_attack", "sp_defense", "speed")
RUNTIME_STAT_OFFSETS = {"hp": 0, "attack": 1, "defense": 2, "speed": 3, "sp_attack": 4, "sp_defense": 5}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise P06SpeciesError(message)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise P06SpeciesError(f"入力を読めません: {path}: {exc}") from exc
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise P06SpeciesError(f"JSONを読めません: {path}: {exc}") from exc
    _require(isinstance(data, dict), f"JSON rootはobject必須です: {path}")
    return data


def _fixed_file(root: Path, entry: Mapping[str, Any]) -> Path:
    path = root / str(entry.get("path") or entry.get("logical_path") or "")
    _require(path.is_file(), f"固定入力がありません: {path}")
    if "size" in entry:
        _require(path.stat().st_size == entry["size"], f"固定入力size不一致: {path}")
    _require(_sha256_file(path) == entry["sha256"], f"固定入力SHA-256不一致: {path}")
    return path


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise P06SpeciesError(f"CSVを読めません: {path}: {exc}") from exc
    _require(bool(rows), f"CSVが空です: {path}")
    return rows


def _read_review_member(archive: Path, source: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    try:
        with zipfile.ZipFile(archive) as handle:
            suffix = str(source["review_member_suffix"])
            matches = [name for name in handle.namelist() if name.endswith(suffix)]
            _require(len(matches) == 1, f"復元監査memberの一致数が不正です: {matches}")
            info = handle.getinfo(matches[0])
            _require(info.file_size == source["review_member_size"], "復元監査member size不一致")
            raw = handle.read(matches[0])
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise P06SpeciesError(f"復元監査ZIPを読めません: {archive}: {exc}") from exc
    digest = _sha256_bytes(raw)
    _require(digest == source["review_member_sha256"], "復元監査member SHA-256不一致")
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise P06SpeciesError(f"復元監査member JSON不正: {exc}") from exc
    _require(isinstance(data, dict), "復元監査member rootはobject必須です")
    return data, matches[0]


def _manifest_maps(root: Path) -> dict[str, Any]:
    species_rows = _read_csv(root / "manifests/species_ids.csv")
    type_rows = _read_csv(root / "manifests/type_ids.csv")
    ability_rows = _read_csv(root / "manifests/ability_ids.csv")
    species_by_key = {row["species_key"]: row for row in species_rows}
    species_by_id = {int(row["id"]): row for row in species_rows}
    type_by_id = {int(row["id"]): row for row in type_rows}
    ability_by_id = {int(row["id"]): row for row in ability_rows}
    _require(len(species_by_key) == len(species_rows) == len(species_by_id), "species manifest重複")
    _require(len(type_by_id) == len(type_rows), "type manifest ID重複")
    _require(len(ability_by_id) == len(ability_rows), "ability manifest ID重複")
    return {
        "species_rows": species_rows,
        "species_by_key": species_by_key,
        "species_by_id": species_by_id,
        "type_by_id": type_by_id,
        "ability_by_id": ability_by_id,
    }


def _parse_runtime_row(raw: bytes, maps: Mapping[str, Any]) -> dict[str, Any]:
    _require(len(raw) == 32, "BaseStats rowは32 bytes必須です")
    stats = {key: raw[offset] for key, offset in RUNTIME_STAT_OFFSETS.items()}
    type_ids = [raw[6], raw[7]]
    logical_type_ids = type_ids[:1] if type_ids[0] == type_ids[1] else type_ids
    ability_ids = [int.from_bytes(raw[offset:offset + 2], "little") for offset in (22, 26, 28)]
    for type_id in type_ids:
        _require(type_id in maps["type_by_id"], f"runtime type ID未解決: {type_id}")
    for ability_id in ability_ids:
        _require(ability_id in maps["ability_by_id"], f"runtime ability ID未解決: {ability_id}")
    return {
        "base_stats": stats,
        "base_stat_total": sum(stats.values()),
        "runtime_type_ids": type_ids,
        "logical_type_ids": logical_type_ids,
        "logical_type_keys": [maps["type_by_id"][value]["type_key"] for value in logical_type_ids],
        "ability_ids": ability_ids,
        "ability_keys": [maps["ability_by_id"][value]["ability_key"] for value in ability_ids],
    }


def _name_matches_ability(source_name: str, ability_id: int, maps: Mapping[str, Any]) -> bool:
    if source_name == "":
        return ability_id == 0
    return source_name == maps["ability_by_id"][ability_id]["display_name"]


def _name_matches_type(source_name: str, type_id: int, maps: Mapping[str, Any]) -> bool:
    return source_name == maps["type_by_id"][type_id]["display_name"]


def _normalise_candidate(
    candidate: Mapping[str, Any],
    runtime: bytes,
    maps: Mapping[str, Any],
) -> dict[str, Any]:
    species_id = candidate.get("existing_project_id")
    species_key = candidate.get("assert_species_key")
    _require(isinstance(species_id, int) and species_id in maps["species_by_id"], f"候補species ID不正: {species_id}")
    manifest = maps["species_by_id"][species_id]
    _require(species_key == manifest["species_key"], f"候補stable key不一致: {species_id}: {species_key}")
    _require(manifest.get("form_key", "") == "", f"復元候補にbase以外のformが混入: {species_key}")
    _require(candidate.get("name") == manifest["display_name"], f"候補表示名不一致: {species_key}")
    parsed = _parse_runtime_row(runtime[species_id * 32:(species_id + 1) * 32], maps)
    changes = candidate.get("changes")
    _require(isinstance(changes, dict) and changes, f"候補changes不正: {species_key}")
    _require(set(changes) <= {"base_stats", "types", "abilities"}, f"未許可field候補: {species_key}: {sorted(changes)}")
    fields: dict[str, Any] = {}

    if "base_stats" in changes:
        source = changes["base_stats"]
        before = source.get("before")
        target = source.get("target")
        _require(isinstance(before, dict) and set(before) == set(STAT_KEYS), f"base_stats before不正: {species_key}")
        _require(isinstance(target, dict) and set(target) == set(STAT_KEYS), f"base_stats target不正: {species_key}")
        _require(before == parsed["base_stats"], f"current base_statsが候補beforeと不一致: {species_key}")
        _require(all(isinstance(target[key], int) and 1 <= target[key] <= 255 for key in STAT_KEYS), f"target base_stats範囲外: {species_key}")
        classification = (
            "CONFIRMED_TRANSCRIPTION_OR_ID_BUG_REVIEW_ONLY"
            if species_key == "SPECIES_KEY_SCYTHER"
            else "ORIGINAL_RESTORATION_REVIEW_ONLY"
        )
        fields["base_stats"] = {
            "classification": classification,
            "adoption_status": "NOT_ADOPTED",
            "before": before,
            "before_total": sum(before.values()),
            "target": target,
            "target_total": sum(target.values()),
        }

    if "types" in changes:
        source = changes["types"]
        before_names = source.get("before_names")
        target_ids = source.get("target_project_ids")
        _require(isinstance(before_names, list) and len(before_names) == len(parsed["logical_type_ids"]), f"type before slot数不一致: {species_key}")
        _require(all(_name_matches_type(name, value, maps) for name, value in zip(before_names, parsed["logical_type_ids"])), f"current typeが候補beforeと不一致: {species_key}")
        _require(isinstance(target_ids, list) and 1 <= len(target_ids) <= 2, f"target type slot不正: {species_key}")
        _require(all(isinstance(value, int) and value in maps["type_by_id"] for value in target_ids), f"target type ID未解決: {species_key}")
        fields["types"] = {
            "classification": "ORIGINAL_RESTORATION_REVIEW_ONLY",
            "adoption_status": "NOT_ADOPTED",
            "before_ids": parsed["logical_type_ids"],
            "before_keys": parsed["logical_type_keys"],
            "target_ids": target_ids,
            "target_keys": [maps["type_by_id"][value]["type_key"] for value in target_ids],
        }

    if "abilities" in changes:
        source = changes["abilities"]
        before_names = source.get("before_names")
        target_ids = source.get("target_project_ids")
        _require(isinstance(before_names, list) and len(before_names) == 3, f"ability before slot数不一致: {species_key}")
        _require(all(_name_matches_ability(name, value, maps) for name, value in zip(before_names, parsed["ability_ids"])), f"current abilityが候補beforeと不一致: {species_key}")
        _require(isinstance(target_ids, list) and len(target_ids) == 3, f"target ability slot数不一致: {species_key}")
        _require(all(isinstance(value, int) and value in maps["ability_by_id"] for value in target_ids), f"target ability ID未解決: {species_key}")
        fields["abilities"] = {
            "classification": "ORIGINAL_RESTORATION_REVIEW_ONLY",
            "adoption_status": "NOT_ADOPTED",
            "before_ids": parsed["ability_ids"],
            "before_keys": parsed["ability_keys"],
            "target_ids": target_ids,
            "target_keys": [maps["ability_by_id"][value]["ability_key"] for value in target_ids],
            "slot_order": ["normal_1", "normal_2", "hidden"],
        }

    return {
        "record_key": f"P06_REVIEW_{species_key.removeprefix('SPECIES_KEY_')}",
        "species_key": species_key,
        "form_key": "FORM_KEY_BASE",
        "existing_project_id": species_id,
        "display_name": candidate["name"],
        "record_status": "REVIEW_ONLY_NOT_ADOPTED",
        "fields": fields,
    }


def render_review_projection(root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    """固定ZIPと現行tableから、未採用候補の正規化projectionを生成する。"""
    root = root.resolve()
    sources = contract["sources"]
    restoration_archive = _fixed_file(root, sources["restoration_archive"])
    _fixed_file(root, sources["learnset_archive"])
    for key in ("current_species_manifest", "current_type_manifest", "current_ability_manifest", "current_base_stats"):
        _fixed_file(root, sources[key])
    review, member_name = _read_review_member(restoration_archive, sources["restoration_archive"])
    _require(review.get("status") == "REVIEW_ONLY_NOT_APPLIED", "復元監査sourceが未採用ではありません")
    maps = _manifest_maps(root)
    runtime_path = root / sources["current_base_stats"]["path"]
    runtime = runtime_path.read_bytes()
    expected_size = sources["current_base_stats"]["species_count"] * sources["current_base_stats"]["stride"]
    _require(len(runtime) == expected_size, "current BaseStats table size不一致")
    records = [_normalise_candidate(item, runtime, maps) for item in review.get("candidates", [])]
    records.sort(key=lambda row: row["existing_project_id"])
    _require(len(records) == len({row["record_key"] for row in records}), "review record key重複")
    field_counts = Counter(field for row in records for field in row["fields"])
    return {
        "schema_version": 1,
        "task": "USER-MODERNIZATION-P06",
        "status": "REVIEW_PROJECTION_ONLY_NOT_ADOPTED",
        "source": {
            "archive_sha256": sources["restoration_archive"]["sha256"],
            "member": member_name,
            "member_sha256": sources["restoration_archive"]["review_member_sha256"],
            "source_status": review["status"],
            "baseline": review.get("baseline"),
        },
        "current_surface": {
            "base_stats_sha256": sources["current_base_stats"]["sha256"],
            "species_manifest_sha256": sources["current_species_manifest"]["sha256"],
            "type_manifest_sha256": sources["current_type_manifest"]["sha256"],
            "ability_manifest_sha256": sources["current_ability_manifest"]["sha256"],
        },
        "partition": {
            "adopted_delta_count": 0,
            "review_record_count": len(records),
            "field_candidate_counts": dict(sorted(field_counts.items())),
            "confirmed_transcription_or_id_bug_field_count": sum(
                field["classification"] == "CONFIRMED_TRANSCRIPTION_OR_ID_BUG_REVIEW_ONLY"
                for row in records for field in row["fields"].values()
            ),
            "original_restoration_review_field_count": sum(
                field["classification"] == "ORIGINAL_RESTORATION_REVIEW_ONLY"
                for row in records for field in row["fields"].values()
            ),
            "vega_custom_submitted_delta_count": 0,
        },
        "records": records,
    }


def calculate_stat(
    base: int,
    *,
    level: int,
    iv: int,
    ev: int,
    is_hp: bool,
    nature_numerator: int = 10,
    nature_denominator: int = 10,
) -> int:
    """Gen 3以降の通常能力計算を整数演算で再現する。"""
    _require(1 <= base <= 255, "base stat範囲外")
    _require(1 <= level <= 100, "level範囲外")
    _require(0 <= iv <= 31, "IV範囲外")
    _require(0 <= ev <= 255, "EV範囲外")
    common = ((2 * base + iv + ev // 4) * level) // 100
    if is_hp:
        return common + level + 10
    _require((nature_numerator, nature_denominator) in {(9, 10), (10, 10), (11, 10)}, "nature補正不正")
    return ((common + 5) * nature_numerator) // nature_denominator


def _validate_projection(contract: Mapping[str, Any], projection: Mapping[str, Any]) -> None:
    _require(contract["status"] == "CHECKPOINT_ADOPTED_DELTA_EMPTY", "P06 checkpoint status不正")
    adoption = contract["adoption"]
    _require(adoption["adopted_delta_count"] == 0 and adoption["adopted_delta_records"] == [], "未承認deltaがadoptedへ混入")
    _require(adoption["runtime_patch_authorized"] is False, "採用差分0でruntime patchが許可されています")
    _require(projection["status"] == "REVIEW_PROJECTION_ONLY_NOT_ADOPTED", "projection status不正")
    expected = contract["review_partition"]
    partition = projection["partition"]
    _require(partition["review_record_count"] == expected["source_record_count"], "review record count不一致")
    _require(partition["field_candidate_counts"] == expected["field_candidate_counts"], "field candidate count不一致")
    _require(partition["confirmed_transcription_or_id_bug_field_count"] == 1, "確認済み転記不整合の分離数不正")
    _require(partition["original_restoration_review_field_count"] == 217, "原作復元review field数不正")
    confirmed = [
        (row, field_name, field)
        for row in projection["records"]
        for field_name, field in row["fields"].items()
        if field["classification"] == "CONFIRMED_TRANSCRIPTION_OR_ID_BUG_REVIEW_ONLY"
    ]
    _require(len(confirmed) == 1, "確認済み転記不整合fieldが一意ではありません")
    row, field_name, field = confirmed[0]
    _require((row["species_key"], row["form_key"], field_name) == ("SPECIES_KEY_SCYTHER", "FORM_KEY_BASE", "base_stats"), "確認済み転記不整合対象が想定外です")
    _require(field["adoption_status"] == "NOT_ADOPTED", "確認済み候補を無断採用しています")
    custom = expected["vega_custom_candidates"]
    _require(all(item["submitted_delta"] is None and item["status"] == "SPEC_NOT_SUBMITTED_NOT_ADOPTED" for item in custom), "未提出Vega独自案にdeltaが作成されています")


def _audit_runtime_consumer(root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    source = contract["sources"]
    abi = contract["runtime_consumer_contract"]
    table_path = _fixed_file(root, source["current_base_stats"])
    table = table_path.read_bytes()
    metadata = _read_json(root / abi["repoint_metadata_path"])
    base_stats = metadata.get("base_stats", {})
    _require(base_stats.get("count") == source["current_base_stats"]["species_count"], "consumer metadata species count不一致")
    _require(base_stats.get("stride") == abi["base_stats_stride"], "consumer metadata stride不一致")
    _require(base_stats.get("address") == abi["base_stats_address"], "consumer metadata address不一致")
    sites = base_stats.get("repoint_sites", [])
    _require(len(sites) == abi["expected_repoint_count"], "consumer repoint count不一致")
    rom_path = _fixed_file(root, source["cumulative_rom"])
    rom = rom_path.read_bytes()
    encoded_address = int(abi["base_stats_address"]).to_bytes(4, "little")
    bad_sites = [site for site in sites if rom[site:site + 4] != encoded_address]
    _require(not bad_sites, f"cumulative ROMのBaseStats consumer root不一致: {bad_sites[:10]}")
    offset = abi["base_stats_rom_offset"]
    _require(rom[offset:offset + len(table)] == table, "cumulative ROMのBaseStats tableがcurrent surfaceと不一致")
    ability_limit = len(_read_csv(root / "manifests/ability_ids.csv"))
    type_limit = len(_read_csv(root / "manifests/type_ids.csv"))
    max_ability = 0
    max_type = 0
    for start in range(0, len(table), 32):
        row = table[start:start + 32]
        max_type = max(max_type, row[6], row[7])
        max_ability = max(max_ability, *(int.from_bytes(row[index:index + 2], "little") for index in (22, 26, 28)))
    _require(max_type < type_limit, "BaseStats consumerに未解決type IDがあります")
    _require(max_ability < ability_limit, "BaseStats consumerに未解決ability IDがあります")
    return {
        "status": "PASS",
        "rom_path": source["cumulative_rom"]["path"],
        "rom_sha256": source["cumulative_rom"]["sha256"],
        "table_sha256": source["current_base_stats"]["sha256"],
        "species_count": source["current_base_stats"]["species_count"],
        "stride": abi["base_stats_stride"],
        "root_address": f"0x{abi['base_stats_address']:08X}",
        "repoint_count": len(sites),
        "type_offsets": abi["type_offsets"],
        "ability_u16_offsets": abi["ability_u16_offsets"],
        "max_type_id_used": max_type,
        "max_ability_id_used": max_ability,
    }


def audit_p06(root: Path, *, compare_archive: bool = True) -> dict[str, Any]:
    """採用差分0、候補隔離、入力hash、現行consumerを副作用なしで検査する。"""
    root = root.resolve()
    contract_path = root / "content/modernization/p06_species_adjustment_contract.json"
    projection_path = root / "content/modernization/p06_review_projection.json"
    contract = _read_json(contract_path)
    projection = _read_json(projection_path)
    _validate_projection(contract, projection)
    projection_hash = _sha256_file(projection_path)
    expected_projection_hash = contract["review_partition"].get("projection_sha256")
    _require(expected_projection_hash == projection_hash, "review projection SHA-256不一致")

    archive_comparison = "NOT_REQUESTED"
    if compare_archive:
        rebuilt = render_review_projection(root, contract)
        expected_bytes = (json.dumps(rebuilt, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        actual_bytes = projection_path.read_bytes()
        _require(actual_bytes == expected_bytes, "固定ZIPからのreview projection再生成結果が不一致")
        archive_comparison = "PASS"

    dependencies: dict[str, Any] = {}
    for key, entry in contract["cumulative_dependencies"].items():
        path = root / entry["path"]
        if not path.is_file():
            _require(entry["required"] is False, f"必須累積dependencyがありません: {path}")
            dependencies[key] = {"present": False, "required": False}
            continue
        data = _read_json(path)
        row = {
            "present": True,
            "required": entry["required"],
            "path": entry["path"],
            "sha256": _sha256_file(path),
            "status": data.get("status"),
            "species_adjustment_import": entry["species_adjustment_import"],
        }
        if key == "p05":
            summary = data.get("summary", {})
            count = summary.get(entry["expected_summary_field"])
            _require(count == 0, f"P05に採用済み性能差分があります。P06 contract更新が必要: {count}")
            row["adopted_performance_adjustment_count"] = count
        dependencies[key] = row

    consumer = _audit_runtime_consumer(root, contract)
    return {
        "schema_version": 1,
        "task": "USER-MODERNIZATION-P06",
        "status": "PASS",
        "completion_state": "CHECKPOINT_NOT_P06_DONE",
        "implementation_ready": False,
        "side_effects": "NONE",
        "rom_modified": False,
        "adopted_delta_count": 0,
        "runtime_patch_authorized": False,
        "inputs": {
            "restoration_archive": {
                "path": contract["sources"]["restoration_archive"]["logical_path"],
                "size": contract["sources"]["restoration_archive"]["size"],
                "sha256": contract["sources"]["restoration_archive"]["sha256"],
                "member_sha256": contract["sources"]["restoration_archive"]["review_member_sha256"],
                "declared_status": contract["sources"]["restoration_archive"]["declared_status"],
            },
            "learnset_archive": {
                "path": contract["sources"]["learnset_archive"]["logical_path"],
                "size": contract["sources"]["learnset_archive"]["size"],
                "sha256": contract["sources"]["learnset_archive"]["sha256"],
                "species_adjustment_role": "NONE",
            },
        },
        "review_projection": {
            "sha256": projection_hash,
            "archive_rebuild": archive_comparison,
            **projection["partition"],
        },
        "runtime_consumer": consumer,
        "dependencies": dependencies,
        "blockers": [
            {
                "blocker_key": "BLOCKER_ADOPTED_SPEC_NOT_SUBMITTED",
                "detail_ja": "ユーザー採用済みの種族調整表がなく、runtimeへ適用できるdeltaは0件。"
            },
            {
                "blocker_key": "BLOCKER_RESTORATION_REVIEW_NOT_APPROVAL",
                "detail_ja": "復元監査194 recordsはREVIEW_ONLY_NOT_APPLIED。転記不整合候補1 fieldを含め一括採用しない。"
            },
            {
                "blocker_key": "BLOCKER_VEGA_CUSTOM_SPEC_MISSING",
                "detail_ja": "ジバクン特性差替えとカモナイツA45は具体delta未提出。意味や数値を推測しない。"
            }
        ],
    }


__all__ = ["P06SpeciesError", "audit_p06", "calculate_stat", "render_review_projection"]
