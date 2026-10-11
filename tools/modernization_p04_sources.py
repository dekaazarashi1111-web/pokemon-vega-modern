#!/usr/bin/env python3
"""工程4の公式候補と外部GBA素材sourceを読み取り専用で監査する。"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import struct
import subprocess
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


class P04SourceError(RuntimeError):
    """工程4の入力が不完全または相互矛盾している場合に送出する。"""


OFFICIAL_HOSTS = {
    "www.pokemon.com",
    "pokemon.com",
    "legends.pokemon.com",
    "windswaves.pokemon.com",
    "www.pokemon.co.jp",
}
KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]+$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise P04SourceError(message)


def _load_json(path: Path) -> dict[str, Any]:
    _require(path.is_file(), f"必須JSONがありません: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise P04SourceError(f"JSONを読めません: {path}: {exc}") from exc
    _require(isinstance(value, dict), f"JSON rootはobject必須です: {path}")
    return value


def _load_csv_keys(path: Path, key_field: str) -> tuple[set[str], list[int]]:
    _require(path.is_file(), f"必須manifestがありません: {path}")
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise P04SourceError(f"manifestを読めません: {path}: {exc}") from exc
    _require(rows, f"manifestが空です: {path}")
    _require(key_field in rows[0], f"manifestに{key_field}列がありません: {path}")
    keys: set[str] = set()
    ids: list[int] = []
    for line, row in enumerate(rows, start=2):
        key = row.get(key_field, "")
        _require(bool(key), f"{path}:{line}: {key_field}が空です")
        _require(key not in keys, f"{path}:{line}: key重複: {key}")
        keys.add(key)
        try:
            ids.append(int(row["id"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise P04SourceError(f"{path}:{line}: idが整数ではありません") from exc
    return keys, ids


def _capacity(ids: list[int]) -> dict[str, Any]:
    _require(ids, "ID表が空です")
    _require(len(ids) == len(set(ids)), "ID表に重複があります")
    highest = max(ids)
    holes = sorted(set(range(highest + 1)) - set(ids))
    return {
        "declared_rows": len(ids),
        "lowest_id": min(ids),
        "highest_id": highest,
        "holes_below_highest": holes,
        "free_slots_below_highest": len(holes),
    }


def _validate_https_url(url: str, *, official: bool, context: str) -> None:
    parsed = urlparse(url)
    _require(parsed.scheme == "https" and bool(parsed.netloc), f"{context}: HTTPS URL必須: {url}")
    if official:
        _require(parsed.hostname in OFFICIAL_HOSTS, f"{context}: 公式hostではありません: {url}")


def _date_on_or_before(value: str, cutoff: date, context: str) -> None:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise P04SourceError(f"{context}: ISO日付ではありません: {value}") from exc
    _require(parsed <= cutoff, f"{context}: 調査締切後の日付です: {value}")


def _validate_official_sources(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cutoff = date.fromisoformat(data.get("research_cutoff_date", ""))
    _require(data.get("policy", {}).get("authority") == "OFFICIAL_PRIMARY_ONLY", "公式一次情報限定policyがありません")
    _require(data.get("policy", {}).get("exclude_rumors_leaks_and_inference") is True, "噂・リーク除外policyがありません")
    result: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(data.get("sources", [])):
        context = f"official_sources[{index}]"
        key = source.get("source_key")
        _require(isinstance(key, str) and KEY_RE.fullmatch(key) is not None, f"{context}: source_key不正")
        _require(key not in result, f"{context}: source_key重複: {key}")
        is_official = source.get("official", True) is not False
        _validate_https_url(source.get("url", ""), official=is_official, context=context)
        _date_on_or_before(source.get("publication_date", ""), cutoff, context)
        if not is_official:
            _require(source.get("kind") == "TECHNICAL_REFERENCE_NOT_OFFICIAL", f"{context}: 非公式sourceの区分が不正です")
        result[key] = source
    _require(result, "公式source一覧が空です")
    return result


def _validate_asset_sources(data: dict[str, Any], cutoff: date) -> dict[str, dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(data.get("sources", [])):
        context = f"asset_sources[{index}]"
        key = source.get("source_key")
        _require(isinstance(key, str) and KEY_RE.fullmatch(key) is not None, f"{context}: source_key不正")
        _require(key not in sources, f"{context}: source_key重複: {key}")
        _validate_https_url(source.get("repository_url", ""), official=False, context=context)
        _validate_https_url(source.get("commit_url", ""), official=False, context=context)
        commit = source.get("commit", "")
        _require(HEX40_RE.fullmatch(commit) is not None, f"{context}: commit SHA不正")
        try:
            commit_date = datetime.fromisoformat(source.get("commit_date", "").replace("Z", "+00:00")).date()
        except (TypeError, ValueError) as exc:
            raise P04SourceError(f"{context}: commit_date不正") from exc
        _require(commit_date <= cutoff, f"{context}: 締切後のcommitです")
        _require(source.get("redistribution_allowed") is False, f"{context}: 権利確認前の再配布許可は禁止です")
        _require(bool(source.get("license_status")), f"{context}: license_statusがありません")
        sources[key] = source
    selected = data.get("selected_source_key")
    _require(selected in sources, "selected_source_keyがsource一覧にありません")
    selected_source = sources[selected]
    _require(selected_source.get("technical_fit") == "SELECTED", "選定sourceのtechnical_fitが不正です")
    _require(data.get("selection_policy", {}).get("asset_import_requires_license_review") is True, "素材権利review gateがありません")
    return sources


def _validate_candidate_contract(
    data: dict[str, Any],
    official_sources: dict[str, dict[str, Any]],
    species_keys: set[str],
    item_keys: set[str],
    ability_keys: set[str],
) -> dict[str, Any]:
    cutoff = date.fromisoformat(data.get("research_cutoff_date", ""))
    non_adopted_policy = data.get("non_adopted_policy", {})
    _require(
        non_adopted_policy
        == {
            "implementation_scope": "NON_ADOPTED_USER_SCOPE",
            "id_assignment": "NOT_APPLICABLE_NON_ADOPTED",
            "asset_requirement": "NOT_REQUIRED",
            "preserve_provenance": True,
            "future_readoption": "EXPLICIT_USER_DECISION_AND_FULL_CAPACITY_ASSET_REVALIDATION_REQUIRED",
            "notes_ja": non_adopted_policy.get("notes_ja"),
        }
        and isinstance(non_adopted_policy.get("notes_ja"), str)
        and bool(non_adopted_policy["notes_ja"]),
        "NON_ADOPTED_USER_SCOPE policyが不完全です",
    )
    profiles = data.get("provenance_profiles", {})
    _require(isinstance(profiles, dict) and profiles, "provenance_profilesがありません")
    required_profile_properties = {"identity", "types", "stats", "learnset", "change_condition"}
    for key, profile in profiles.items():
        _require(KEY_RE.fullmatch(key) is not None, f"provenance profile key不正: {key}")
        _require(required_profile_properties <= set(profile), f"{key}: property provenance不足")
        for prop in required_profile_properties:
            source_key = profile[prop]
            _require(source_key in official_sources, f"{key}.{prop}: source未解決: {source_key}")

    records = data.get("records", [])
    _require(isinstance(records, list) and records, "候補recordsがありません")
    required_fields = {
        "record_key", "identity_species_key", "identity_form_key", "proposed_species_key",
        "source_species_key", "classification", "identity_group_key", "name_en", "type_keys",
        "work", "version", "implementation_scope", "id_assignment", "mega_stone_key",
        "stone_asset_stem", "ability_key", "ability_status", "ability_replacement_key",
        "ability_provenance_key", "provenance_profile_key", "official_confirmation_date",
        "official_url", "asset_dir", "upstream_species_symbol",
    }
    record_keys: set[str] = set()
    identity_pairs: set[tuple[str, str]] = set()
    declared_proposed_keys: set[str] = set()
    adopted_proposed_keys: set[str] = set()
    replacement_keys: set[str] = set()
    resolved_records: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        context = f"records[{index}]"
        missing = required_fields - set(record)
        _require(not missing, f"{context}: 必須field不足: {sorted(missing)}")
        for field in ("record_key", "identity_species_key", "identity_form_key", "identity_group_key"):
            _require(isinstance(record[field], str) and KEY_RE.fullmatch(record[field]) is not None, f"{context}: {field}不正")
        _require(record["record_key"] not in record_keys, f"{context}: record_key重複")
        record_keys.add(record["record_key"])
        pair = (record["identity_species_key"], record["identity_form_key"])
        _require(pair not in identity_pairs, f"{context}: stable species/form key重複: {pair}")
        identity_pairs.add(pair)
        profile_key = record["provenance_profile_key"]
        _require(profile_key in profiles, f"{context}: provenance profile未解決: {profile_key}")
        ability_source_key = record["ability_provenance_key"]
        _require(ability_source_key in official_sources, f"{context}: ability provenance未解決")
        _date_on_or_before(record["official_confirmation_date"], cutoff, context)
        _validate_https_url(record["official_url"], official=True, context=context)
        _require(isinstance(record["type_keys"], list) and 1 <= len(record["type_keys"]) <= 2, f"{context}: type_keys不正")
        _require(all(isinstance(x, str) and x.startswith("TYPE_KEY_") for x in record["type_keys"]), f"{context}: type key不正")

        classification = record["classification"]
        _require(classification in {"BATTLE_ONLY_MEGA", "NEW_SPECIES", "APPEARANCE_CLASSIFICATION_PENDING"}, f"{context}: classification不正")
        implementation_scope = record["implementation_scope"]
        _require(
            implementation_scope in {"ADOPT_CANDIDATE", "NON_ADOPTED_USER_SCOPE", "HOLD_CLASSIFICATION"},
            f"{context}: implementation_scope不正",
        )
        if classification == "APPEARANCE_CLASSIFICATION_PENDING":
            _require(implementation_scope == "HOLD_CLASSIFICATION", f"{context}: 分類未確定外観はHOLD必須")
            _require(record["proposed_species_key"] is None, f"{context}: 分類未確定外観へspecies keyを割当てています")
            _require(record["id_assignment"] == "NOT_APPLICABLE_HELD", f"{context}: 分類保留のID状態が不正です")
        else:
            proposed = record["proposed_species_key"]
            _require(isinstance(proposed, str) and proposed.startswith("SPECIES_KEY_"), f"{context}: proposed_species_key不正")
            _require(proposed not in declared_proposed_keys, f"{context}: proposed species key重複")
            _require(proposed not in species_keys, f"{context}: proposed species keyが現行IDを上書きします: {proposed}")
            declared_proposed_keys.add(proposed)
            if implementation_scope == "ADOPT_CANDIDATE":
                adopted_proposed_keys.add(proposed)
                _require(record["id_assignment"] == "BLOCKED_PENDING_CAPACITY_EXPANSION", f"{context}: 容量拡張前のID割当は禁止です")
            elif implementation_scope == "NON_ADOPTED_USER_SCOPE":
                _require(classification == "NEW_SPECIES", f"{context}: 現行非採用scopeはWinds/Waves新種だけに限定します")
                _require(record["id_assignment"] == "NOT_APPLICABLE_NON_ADOPTED", f"{context}: 非採用候補へIDを予約しています")
            else:
                raise P04SourceError(f"{context}: 確定分類をHOLD scopeへ置けません")

        if classification == "BATTLE_ONLY_MEGA":
            _require(implementation_scope == "ADOPT_CANDIDATE", f"{context}: Mega候補は現行採用scope必須です")
        elif classification == "NEW_SPECIES":
            _require(implementation_scope == "NON_ADOPTED_USER_SCOPE", f"{context}: Winds/Waves新種は現行非採用scope必須です")

        source_species_key = record["source_species_key"]
        if source_species_key is not None:
            _require(source_species_key in species_keys, f"{context}: source species key未解決: {source_species_key}")
        elif classification != "NEW_SPECIES":
            raise P04SourceError(f"{context}: source species keyがありません")

        if classification == "BATTLE_ONLY_MEGA":
            _require(record["mega_stone_key"].startswith("ITEM_KEY_"), f"{context}: Mega Stone key不正")
            _require(record["mega_stone_key"] not in item_keys, f"{context}: Mega Stone keyが現行IDと衝突")
            _require(bool(record["stone_asset_stem"]), f"{context}: stone asset stemがありません")
            _require(bool(record["asset_dir"]) and bool(record["upstream_species_symbol"]), f"{context}: Mega素材参照がありません")
            _require(profiles[profile_key].get("stone") in official_sources, f"{context}: stone provenance未解決")
        else:
            _require(record["mega_stone_key"] is None and record["stone_asset_stem"] is None, f"{context}: Mega以外にstoneが設定されています")

        ability_status = record["ability_status"]
        _require(ability_status in {"OFFICIAL_CONFIRMED", "TEMPORARY_REPLACEABLE"}, f"{context}: ability_status不正")
        replacement_key = record["ability_replacement_key"]
        if ability_status == "TEMPORARY_REPLACEABLE":
            _require(isinstance(replacement_key, str) and replacement_key.startswith("REPLACEMENT_KEY_ABILITY_"), f"{context}: replacement key必須")
            _require(replacement_key not in replacement_keys, f"{context}: replacement key重複")
            replacement_keys.add(replacement_key)
            _require(official_sources[ability_source_key].get("official", True) is False, f"{context}: 仮特性provenanceは非公式技術参照である必要があります")
            _require(record["ability_key"] in ability_keys, f"{context}: 仮特性keyが現行manifestにありません")
        else:
            _require(replacement_key is None, f"{context}: 公式確定特性にreplacement keyがあります")
            _require(official_sources[ability_source_key].get("official", True) is not False, f"{context}: 公式確定特性に非公式provenanceを使用しています")

        resolved = dict(record)
        resolved["property_provenance"] = dict(profiles[profile_key])
        resolved_records.append(resolved)

    expected = data.get("expected_counts", {})
    adopted = [x for x in records if x["implementation_scope"] == "ADOPT_CANDIDATE"]
    mega = [x for x in adopted if x["classification"] == "BATTLE_ONLY_MEGA"]
    new_species = [x for x in records if x["classification"] == "NEW_SPECIES"]
    holds = [x for x in records if x["classification"] == "APPEARANCE_CLASSIFICATION_PENDING"]
    non_adopted = [x for x in records if x["implementation_scope"] == "NON_ADOPTED_USER_SCOPE"]
    adopted_new_species = [x for x in adopted if x["classification"] == "NEW_SPECIES"]
    actual_counts = {
        "all_records": len(records),
        "adoption_candidate_records": len(adopted),
        "classification_hold_records": len(holds),
        "non_adopted_user_scope_records": len(non_adopted),
        "mega_runtime_records": len(mega),
        "mega_identity_groups": len({x["identity_group_key"] for x in mega}),
        "unique_mega_stones": len({x["mega_stone_key"] for x in mega}),
        "new_species_records": len(new_species),
        "adopted_new_species_records": len(adopted_new_species),
    }
    for key, value in actual_counts.items():
        _require(expected.get(key) == value, f"expected_counts.{key}={expected.get(key)!r}, 実測={value}")

    official_missing_abilities = sorted({x["ability_key"] for x in adopted if x["ability_status"] == "OFFICIAL_CONFIRMED"} - ability_keys)
    current_manifest_abilities = sorted({x["ability_key"] for x in records if x["ability_key"] in ability_keys})
    _require(
        official_missing_abilities
        == sorted({
            "ABILITY_KEY_DRAGONIZE", "ABILITY_KEY_EELEVATE", "ABILITY_KEY_FIREMANE",
            "ABILITY_KEY_MEGASOL", "ABILITY_KEY_PIERCINGDRILL", "ABILITY_KEY_SPICYSPRAY",
        }),
        f"工程5依存となる新特性集合が想定外です: {official_missing_abilities}",
    )
    return {
        "records": resolved_records,
        "counts": actual_counts,
        "proposed_species_keys": sorted(adopted_proposed_keys),
        "non_adopted_proposed_species_keys": sorted(declared_proposed_keys - adopted_proposed_keys),
        "proposed_item_keys": sorted({x["mega_stone_key"] for x in mega}),
        "official_missing_ability_keys": official_missing_abilities,
        "current_manifest_ability_keys_used": current_manifest_abilities,
        "temporary_ability_records": sorted(x["record_key"] for x in records if x["ability_status"] == "TEMPORARY_REPLACEABLE"),
        "classification_hold_records": sorted(x["record_key"] for x in holds),
        "non_adopted_user_scope_records": sorted(x["record_key"] for x in non_adopted),
    }


def _run_git(checkout: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(checkout), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise P04SourceError(f"git監査に失敗しました: {checkout}: {detail.strip()}") from exc
    return completed.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise P04SourceError(f"hash対象を読めません: {path}: {exc}") from exc
    return digest.hexdigest()


def _parse_png(path: Path) -> dict[str, int]:
    try:
        data = path.read_bytes()[:33]
    except OSError as exc:
        raise P04SourceError(f"PNGを読めません: {path}: {exc}") from exc
    _require(len(data) >= 33 and data[:8] == PNG_SIGNATURE, f"PNG signature不正: {path}")
    _require(data[12:16] == b"IHDR", f"PNG IHDR不正: {path}")
    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    return {"width": width, "height": height, "bit_depth": bit_depth, "color_type": color_type}


def _parse_jasc_palette(path: Path) -> dict[str, int]:
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise P04SourceError(f"paletteを読めません: {path}: {exc}") from exc
    _require(len(lines) >= 3 and lines[0] == "JASC-PAL" and lines[1] == "0100", f"JASC-PAL header不正: {path}")
    try:
        declared = int(lines[2])
        colors = [tuple(int(part) for part in line.split()) for line in lines[3:] if line.strip()]
    except ValueError as exc:
        raise P04SourceError(f"palette値不正: {path}") from exc
    _require(1 <= declared <= 16 and len(colors) == declared, f"GBA 4bpp範囲のpaletteではありません: {path}")
    _require(all(len(rgb) == 3 and all(0 <= value <= 255 for value in rgb) for rgb in colors), f"palette RGB値不正: {path}")
    return {"declared_colors": declared, "actual_colors": len(colors)}


def _aggregate_hash(paths: Iterable[Path], base: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(set(paths), key=lambda item: item.relative_to(base).as_posix()):
        relative = path.relative_to(base).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _validate_checkout(
    checkout: Path,
    selected_source: dict[str, Any],
    candidate_result: dict[str, Any],
    expected_counts: dict[str, Any],
) -> dict[str, Any]:
    _require(checkout.is_dir(), f"固定source checkoutがありません: {checkout}")
    expected_commit = selected_source["commit"]
    actual_commit = _run_git(checkout, "rev-parse", "HEAD")
    _require(actual_commit == expected_commit, f"source HEAD不一致: expected={expected_commit}, actual={actual_commit}")
    actual_origin = _run_git(checkout, "remote", "get-url", "origin")
    accepted_origins = {selected_source["clone_url"], selected_source["repository_url"], selected_source["repository_url"] + ".git"}
    _require(actual_origin in accepted_origins, f"source origin不一致: {actual_origin}")
    dirty = _run_git(checkout, "status", "--porcelain", "--untracked-files=all")
    _require(not dirty, f"source checkoutに変更があります: {dirty[:300]}")

    for relative, expected_hash in selected_source.get("evidence_sha256", {}).items():
        _require(SHA256_RE.fullmatch(expected_hash) is not None, f"evidence SHA-256不正: {relative}")
        actual_hash = _sha256(checkout / relative)
        _require(actual_hash == expected_hash, f"evidence hash不一致: {relative}")

    mega_records = [
        x for x in candidate_result["records"]
        if x["classification"] == "BATTLE_ONLY_MEGA"
        and x["implementation_scope"] == "ADOPT_CANDIDATE"
    ]
    species_constants = (checkout / "include/constants/species.h").read_text(encoding="utf-8")
    item_constants = (checkout / "include/constants/items.h").read_text(encoding="utf-8")
    audited_files: list[Path] = []
    asset_dirs: set[str] = set()
    for record in mega_records:
        context = record["record_key"]
        _require(re.search(rf"\b{re.escape(record['upstream_species_symbol'])}\b", species_constants) is not None, f"{context}: upstream species symbol未解決")
        item_symbol = record["mega_stone_key"].replace("ITEM_KEY_", "ITEM_", 1)
        _require(re.search(rf"\b{re.escape(item_symbol)}\b", item_constants) is not None, f"{context}: upstream stone symbol未解決")
        asset_dirs.add(record["asset_dir"])
        base = checkout / "graphics/pokemon" / record["asset_dir"]
        required = {
            "front.png": (64, 64),
            "back.png": (64, 64),
            "icon.png": (32, 64),
        }
        for filename, dimensions in required.items():
            path = base / filename
            _require(path.is_file(), f"{context}: sprite不足: {path}")
            metadata = _parse_png(path)
            _require((metadata["width"], metadata["height"]) == dimensions, f"{context}: sprite寸法不正: {filename}")
            _require(metadata["color_type"] == 3, f"{context}: indexed PNGではありません: {filename}")
            audited_files.append(path)
        palette_override = selected_source["asset_layout"].get("palette_overrides", {}).get(record["asset_dir"])
        palette_base = checkout / palette_override if palette_override else base
        for filename in ("normal.pal", "shiny.pal"):
            path = palette_base / filename
            _require(path.is_file(), f"{context}: palette不足: {path}")
            _parse_jasc_palette(path)
            audited_files.append(path)

    stones = {x["mega_stone_key"]: x["stone_asset_stem"] for x in mega_records}
    for key, stem in stones.items():
        icon = checkout / "graphics/items/icons" / f"{stem}.png"
        palette = checkout / "graphics/items/icon_palettes" / f"{stem}.pal"
        _require(icon.is_file(), f"{key}: stone icon不足: {icon}")
        metadata = _parse_png(icon)
        _require((metadata["width"], metadata["height"], metadata["color_type"]) == (24, 24, 3), f"{key}: stone icon contract不一致")
        _require(palette.is_file(), f"{key}: stone palette不足: {palette}")
        _parse_jasc_palette(palette)
        audited_files.extend((icon, palette))

    coverage = {
        "mega_runtime_records": {"covered": len(mega_records), "required": len(mega_records)},
        "unique_mega_asset_directories": {"covered": len(asset_dirs), "required": len(asset_dirs)},
        "mega_stones": {"covered": len(stones), "required": len(stones)},
        "winds_waves_new_species": {"covered": 0, "required": 0},
    }
    _require(len(mega_records) == expected_counts["selected_source_mega_asset_records"], "Mega asset record期待数不一致")
    _require(len(asset_dirs) == expected_counts["selected_source_unique_mega_asset_directories"], "Mega asset directory期待数不一致")
    _require(len(stones) == expected_counts["selected_source_stone_asset_records"], "stone asset期待数不一致")
    _require(expected_counts["selected_source_new_species_asset_records"] == 0, "非採用新種へsource asset要件があります")
    return {
        "checkout": str(checkout),
        "origin": actual_origin,
        "commit": actual_commit,
        "clean": True,
        "license_status": selected_source["license_status"],
        "redistribution_allowed": selected_source["redistribution_allowed"],
        "coverage": coverage,
        "audited_file_count": len(set(audited_files)),
        "asset_set_sha256": _aggregate_hash(audited_files, checkout),
    }


def audit_p04_sources(
    root: Path,
    *,
    source_root: Path | None = None,
    require_checkout: bool = True,
) -> dict[str, Any]:
    """工程4の正本候補、現行manifest、固定checkoutを変更せず監査する。"""
    root = root.resolve()
    content_root = root / "content/modernization"
    official_data = _load_json(content_root / "p04_official_sources.json")
    asset_data = _load_json(content_root / "p04_asset_sources.json")
    candidate_data = _load_json(content_root / "p04_candidate_manifest.json")
    cutoff_values = {
        official_data.get("research_cutoff_date"),
        asset_data.get("research_cutoff_date"),
        candidate_data.get("research_cutoff_date"),
    }
    _require(cutoff_values == {"2026-09-08"}, f"調査締切が一致しません: {sorted(str(x) for x in cutoff_values)}")
    cutoff = date(2026, 9, 8)
    official_sources = _validate_official_sources(official_data)
    asset_sources = _validate_asset_sources(asset_data, cutoff)
    selected_source = asset_sources[asset_data["selected_source_key"]]

    species_keys, species_ids = _load_csv_keys(root / "manifests/species_ids.csv", "species_key")
    item_keys, item_ids = _load_csv_keys(root / "manifests/item_ids.csv", "item_key")
    ability_keys, ability_ids = _load_csv_keys(root / "manifests/ability_ids.csv", "ability_key")
    candidate_result = _validate_candidate_contract(
        candidate_data,
        official_sources,
        species_keys,
        item_keys,
        ability_keys,
    )

    capacities = {
        "species": _capacity(species_ids),
        "items": _capacity(item_ids),
        "abilities": _capacity(ability_ids),
    }
    for kind, expected_free in candidate_data["baseline"]["expected_free_slots"].items():
        _require(capacities[kind]["free_slots_below_highest"] == expected_free, f"{kind}: 現行空きID実測が契約と不一致")

    if source_root is None:
        source_root = root / selected_source["local_checkout"]
    checkout_result: dict[str, Any] | None = None
    if source_root.is_dir():
        checkout_result = _validate_checkout(
            source_root.resolve(),
            selected_source,
            candidate_result,
            candidate_data["expected_counts"],
        )
    elif require_checkout:
        raise P04SourceError(f"固定asset sourceがありません: {source_root}")

    temp_count = len(candidate_result["temporary_ability_records"])
    blockers = [
        {
            "blocker_key": "BLOCKER_ID_CAPACITY",
            "detail_ja": "現行species/item/ability ID表は最高ID以下に空きがなく、追加前に宣言容量とconsumerの拡張が必要。",
        },
        {
            "blocker_key": "BLOCKER_ASSET_RIGHTS",
            "detail_ja": "選定sourceにLICENSEファイルがなく、画像・palette・stoneのtracked取込は権利とcreditsの手動確認まで禁止。",
        },
        {
            "blocker_key": "BLOCKER_TEMPORARY_ABILITIES",
            "detail_ja": f"締切時点で公式ターン制仕様を固定できない{temp_count}行はTEMPORARY_REPLACEABLE。各replacement keyで後日差替が必要。",
        },
        {
            "blocker_key": "BLOCKER_PRIMARY_GAMEPLAY_EXTRACTION",
            "detail_ja": "全候補の種族値・習得・ターン制変化条件は一次情報抽出と移植仕様の固定が未完了。アクション作品値を機械転記しない。",
        },
        {
            "blocker_key": "BLOCKER_PIKACHU_CLASSIFICATION",
            "detail_ja": "Mr. Windychu/Ms. Wavychuは公式が新外観とのみ説明しており、恒常フォームと推定せずHOLD。",
        },
    ]
    return {
        "schema_version": 1,
        "task": "USER-MODERNIZATION-P04",
        "status": "PASS",
        "audit_scope": "RESEARCH_AND_SOURCE_CHECKPOINT",
        "implementation_ready": False,
        "research_cutoff_date": "2026-09-08",
        "side_effects": "NONE",
        "rom_modified": False,
        "official_sources": {
            "count": len(official_sources),
            "official_primary_count": sum(x.get("official", True) is not False for x in official_sources.values()),
            "technical_reference_count": sum(x.get("official", True) is False for x in official_sources.values()),
            "urls": [x["url"] for x in official_sources.values()],
        },
        "asset_source_comparison": {
            "count": len(asset_sources),
            "selected_source_key": asset_data["selected_source_key"],
            "selected_commit": selected_source["commit"],
            "selected_license_status": selected_source["license_status"],
            "selected_redistribution_allowed": selected_source["redistribution_allowed"],
        },
        "candidate_counts": candidate_result["counts"],
        "manifest_capacity": capacities,
        "manifest_diff": {
            "new_species_or_form_keys": candidate_result["proposed_species_keys"],
            "new_species_or_form_key_count": len(candidate_result["proposed_species_keys"]),
            "new_item_keys": candidate_result["proposed_item_keys"],
            "new_item_key_count": len(candidate_result["proposed_item_keys"]),
            "new_ability_dependency_keys": candidate_result["official_missing_ability_keys"],
            "new_ability_dependency_key_count": len(candidate_result["official_missing_ability_keys"]),
        },
        "temporary_ability_records": candidate_result["temporary_ability_records"],
        "classification_hold_records": candidate_result["classification_hold_records"],
        "non_adopted_user_scope": {
            "records": candidate_result["non_adopted_user_scope_records"],
            "preserved_candidate_species_keys": candidate_result["non_adopted_proposed_species_keys"],
            "id_reservation_count": 0,
            "asset_requirement_count": 0,
            "future_readoption": "EXPLICIT_USER_DECISION_AND_FULL_CAPACITY_ASSET_REVALIDATION_REQUIRED",
        },
        "source_checkout": checkout_result,
        "blockers": blockers,
        "records": candidate_result["records"],
    }


__all__ = [
    "P04SourceError",
    "audit_p04_sources",
]
