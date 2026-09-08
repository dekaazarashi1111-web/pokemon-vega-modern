#!/usr/bin/env python3
"""Modernization P03の不変learnset原本を訂正レイヤー経由でcompileする。

巨大なJSONLをtracked領域へ複製せず、固定ZIPから1レコードずつ読み、P01の
canonical identityと照合する。公開する成果は全内容を覆うframed SHA-256 index
とruntime引渡し契約である。
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, NoReturn, Sequence

from tools.modernization_identity import CheckedArchive, load_manifests, stable_json


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P03"
ARCHIVE_ROOT = "Pokemon_Vega_Stage61_Learnsets_v1_3_20260905"
IDENTITY_CONTRACT = Path("content/modernization/identity_contract.json")

EXPECTED_MEMBER_IDENTITIES: Mapping[str, tuple[int, str]] = {
    "README_JA.md": (7097, "2a33bc7a2499c75134e8f7b543fff49b4dc3664dfb0838db3fe3c488afdbaeb3"),
    "SCHEMA_JA.md": (8067, "7f873ab9aa3853d9d926d3d6fb8ea4b9fbc3e8396f3717d2cb301f6c8951ef80"),
    "config/policy.json": (9289, "d6de9587d4ae92714354f1427c0b32098e625f0ff7687c3bf0234e058622b724"),
    "config/stage61_form_map.json": (413818, "0736718e5add10c7368cc425fa3bfe4ba3d39b6ad9a96262c3b18c6aab7e4108"),
    "data/stage61_record_decisions.csv": (332961, "64ba8ef9e39187056d267d385595daf8f529d9a83164f79b2a42c870186dff48"),
    "data/reference_learnsets.jsonl": (193768661, "af3ac5a4dda8a3c51642b47f68cf86f47159ad3ff8f82a3e9154591c21fedbe1"),
    "data/adopted_stage61_learnsets.jsonl": (182887565, "09734339048c7dbf9d18725b2657161012939594291fc2b9f2bce755d753e9ab"),
    "data/move_id_crosswalk.csv": (189708, "17bded79b9df09bbf7b040ecfced62631757d3b4b27e55782aaca614fb1f2475"),
    "data/base_species_1025.csv": (235503, "633705e41565c267e3d4d651461de020bc0f8496a4aa920839a011fc0950b598"),
    "implementation/README_JA.md": (1384, "f2fed1010ae7ca1aa155324c169723168fa5a9fe1b2c73dad85372555fee8aa7"),
    "implementation/adopted_project_move_ids.csv": (633505, "5d630a3c220e3c45c1cfe892d13e411031681c003b77a86aa7a6aeb6421da8d4"),
    "implementation/existing_runtime_slot_projection.csv": (1783431, "3d62e1039a6f58c0f485ab88b978f5f9c946daa81f5dd63d688588d82d17a766"),
    "implementation/moves_without_existing_slot.csv": (3614622, "62d3c9cdd829a1dab12f0b67abf5903748259e39a39addaebac920367096e72b"),
    "implementation/new_move_definitions.json": (771, "d5e87b2e07e6094f23780f82684812d5362eb67be7b077e731e320ba1415a696"),
    "scripts/validate_v13.py": (20969, "2db54dfa4c210951ae671e9e27fb3263d9db2683c156b99be0c6a2e6cfe27bcb"),
    "scripts/learning_rules_v13.py": (6655, "e89919b3d4f334df628cc862bcf0ab4a3b81f671b5d1b16d9c309e3a58772100"),
    "validation/acceptance_v13.json": (7670, "742bbbbb6e9351571d29477f28b20dce361a5a3926fd730dfbe209db3191e112"),
}

EXPECTED_REFERENCE_ROUTE_COUNTS = {
    "direct": 83_950,
    "shared_egg": 5_140,
    "pre_evolution": 36_225,
    "form_change": 431,
}
EXPECTED_COMPILED_COUNTS = {
    "level_up": 18_530,
    "evolution": 341,
    "reminder": 298,
    "machine": 55_380,
    "tutor": 1_113,
    "egg": 2_572,
    "shared_egg": 5_041,
    "pre_evolution_carry": 35_183,
    "form_change": 70,
}
CONSUMERS = tuple(EXPECTED_COMPILED_COUNTS)
ADOPTED_FIELDS = {
    "all_move_ids", "all_official_move_ids", "evidence", "id_namespace",
    "new_engine_move_ids_required", "reference_id", "routes", "schema_version",
    "stage61_key", "vega_species_id",
}
REQUIRED_ROUTE_FIELDS = {
    "route_id", "route_kind", "method", "official_move_id", "project_move_id",
    "existing_vega_move_id", "machine_item", "level", "target_learning_level",
    "donor_learning_level", "learning_species_key", "learning_form_index",
    "source_key", "source_game", "source_file", "source_line", "source_raw_token",
    "source_condition_ja", "acquisition_condition_ja", "carry_condition_ja",
    "form_change_condition_ja", "shared_egg_source_key", "display_path_ja",
}


class ModernizationLearnsetError(ValueError):
    """P03入力、訂正集合、経路、供給、またはruntime契約が不正である。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationLearnsetError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _object_sha(value: Any) -> str:
    return _sha(stable_json(value))


class _FramedDigest:
    """境界衝突を避けて順序付きobject列をhashする。"""

    def __init__(self) -> None:
        self._digest = hashlib.sha256()
        self.count = 0

    def add(self, value: Any) -> None:
        raw = stable_json(value)
        self._digest.update(len(raw).to_bytes(8, "big"))
        self._digest.update(raw)
        self.count += 1

    def hexdigest(self) -> str:
        return self._digest.hexdigest()


def _set_sha(values: Iterable[str]) -> str:
    digest = _FramedDigest()
    for value in sorted(values):
        digest.add(value)
    return digest.hexdigest()


def _strict_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or re.fullmatch(r"0|[1-9][0-9]*", str(value)) is None:
        _fail(f"{label}が非負10進整数ではありません: {value!r}")
    return int(value)


def _strict_csv(raw: bytes, label: str) -> list[dict[str, str]]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        _fail(f"{label}がUTF-8 CSVではありません: {error}")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        _fail(f"{label}のheaderがないか重複しています")
    rows = list(reader)
    if any(None in row for row in rows):
        _fail(f"{label}にheader外の列があります")
    return rows


def _member_suffix(relative: str) -> str:
    return f"{ARCHIVE_ROOT}/{relative}"


def _check_member_identity(relative: str, raw: bytes) -> None:
    expected_size, expected_sha = EXPECTED_MEMBER_IDENTITIES[relative]
    if len(raw) != expected_size or _sha(raw) != expected_sha:
        _fail(
            f"learnset member identity不一致: {relative} "
            f"size={len(raw)} sha256={_sha(raw)}"
        )


def _read_member(archive: CheckedArchive, relative: str) -> bytes:
    name, raw = archive.read(_member_suffix(relative))
    if name != _member_suffix(relative):
        _fail(f"learnset member pathが固定root外です: {name}")
    _check_member_identity(relative, raw)
    return raw


def _json_member(archive: CheckedArchive, relative: str) -> Any:
    raw = _read_member(archive, relative)
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{relative}をJSONとして読めません: {error}")


def _csv_member(archive: CheckedArchive, relative: str) -> list[dict[str, str]]:
    return _strict_csv(_read_member(archive, relative), relative)


def _iter_jsonl_member(
    archive: CheckedArchive, relative: str,
) -> Iterator[dict[str, Any]]:
    """memberを展開せず逐次decodeし、完全走査後にsize/hashを検証する。"""

    expected_size, expected_sha = EXPECTED_MEMBER_IDENTITIES[relative]
    name, stream = archive.lines(_member_suffix(relative))
    if name != _member_suffix(relative):
        stream.close()
        _fail(f"learnset member pathが固定root外です: {name}")
    digest = hashlib.sha256()
    size = 0
    with stream:
        for line_no, raw in enumerate(stream, 1):
            digest.update(raw)
            size += len(raw)
            if not raw.strip():
                _fail(f"{relative}:{line_no}に空行があります")
            try:
                value = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                _fail(f"{relative}:{line_no}がJSON objectではありません: {error}")
            if not isinstance(value, dict):
                _fail(f"{relative}:{line_no}のrootがobjectではありません")
            yield value
    actual_sha = digest.hexdigest()
    if size != expected_size or actual_sha != expected_sha:
        _fail(
            f"learnset JSONL identity不一致: {relative} "
            f"size={size} sha256={actual_sha}"
        )


def _file_identity(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"runtime接続正本が通常ファイルではありません: {relative}")
    raw = path.read_bytes()
    return {"path": relative, "size": len(raw), "sha256": _sha(raw)}


def _load_identity(
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    path = root / IDENTITY_CONTRACT
    if path.is_symlink() or not path.is_file():
        _fail(f"P01 identity契約が通常ファイルではありません: {IDENTITY_CONTRACT}")
    raw = path.read_bytes()
    try:
        identity = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"P01 identity契約を読めません: {error}")
    if raw != stable_json(identity) or identity.get("status") != "PASS":
        _fail("P01 identity契約が決定的PASS成果ではありません")
    manifests = load_manifests(root)
    for name, manifest in manifests.items():
        declared = identity.get("manifests", {}).get(name, {})
        if declared.get("sha256") != manifest.sha256:
            _fail(f"P01 identityと{name} manifestのhashが一致しません")

    records = identity.get("target_normalization", {}).get("records")
    if not isinstance(records, list) or len(records) != 1621:
        _fail("P01 normalized targetが1621件ではありません")
    targets: dict[str, dict[str, Any]] = {}
    for record in records:
        key = str(record.get("species_key", ""))
        manifest = manifests["species"].by_key.get(key)
        if manifest is None or int(manifest["id"]) != record.get("canonical_id"):
            _fail(f"P01 targetのcanonical key/idが不正です: {key}")
        if manifest.get("form_key", "") != record.get("form_key", ""):
            _fail(f"P01 targetのform identityが不正です: {key}")
        if key in targets:
            _fail(f"P01 target keyが重複しています: {key}")
        targets[key] = record
    if set(targets) != set(manifests["species"].by_key):
        _fail("P01 target集合がSpecies manifestと一致しません")
    source = {key for key, row in targets.items() if row["input"]["apply"]}
    corrected = {key for key, row in targets.items() if row["normalized"]["apply"]}
    if len(source) != 1299 or len(corrected) != 1300 \
            or corrected - source != {"SPECIES_KEY_CATERPIE"} \
            or source - corrected:
        _fail("P03で許可された採用訂正がキャタピー1件だけではありません")
    caterpie = targets["SPECIES_KEY_CATERPIE"]
    egg = targets["SPECIES_KEY_EGG"]
    if caterpie["canonical_id"] != 649 or caterpie["reference_id"] != "swordshield:0010.00":
        _fail("キャタピーidentityがID649/swordshield:0010.00ではありません")
    if egg["canonical_id"] != 412 or egg["normalized"]["apply"]:
        _fail("内部タマゴidentityがID412/除外ではありません")
    return identity, targets, manifests


def consumer_for_route(route: Mapping[str, Any]) -> str:
    """経路の意味を壊さず9つのruntime consumerへ一意に振り分ける。"""

    kind = route.get("route_kind")
    method = route.get("method")
    if kind == "pre_evolution":
        return "pre_evolution_carry"
    if kind == "form_change":
        return "form_change"
    if kind == "shared_egg":
        if method != "shared_egg":
            _fail(f"shared_egg経路のmethodが不正です: {method!r}")
        return "shared_egg"
    if kind != "direct":
        _fail(f"未知のroute_kindです: {kind!r}")
    mapping = {
        "level_up": "level_up",
        "evolution": "evolution",
        "reminder": "reminder",
        "tm": "machine",
        "tr": "machine",
        "tutor": "tutor",
        "egg": "egg",
        "special_breeding": "egg",
        # 恒久表へ混ぜず、姿・戦闘状態consumerのsubmodeとして保持する。
        "form_move": "form_change",
        "battle_transform": "form_change",
    }
    try:
        return mapping[str(method)]
    except KeyError:
        _fail(f"direct経路の未知methodです: {method!r}")


@dataclass(frozen=True)
class _ReferenceMeta:
    reference_id: str
    record_sha256: str
    routes_sha256: str
    route_count: int
    all_official_move_ids: tuple[int, ...]
    all_project_move_ids: tuple[int, ...]
    unimplemented_official_move_ids: tuple[int, ...]


@dataclass(frozen=True)
class P03Artifacts:
    contract: dict[str, Any]
    compiled_index: dict[str, Any]
    runtime_handoff: dict[str, Any]

    def output_documents(self) -> Mapping[str, dict[str, Any]]:
        return {
            "content/modernization/p03_learnset_contract.json": self.contract,
            "content/modernization/p03_compiled_index.json": self.compiled_index,
            "content/modernization/p03_runtime_handoff.json": self.runtime_handoff,
        }


def _validate_policy(policy: Any) -> dict[str, Any]:
    if not isinstance(policy, dict) or policy.get("schema_version") != 2:
        _fail("learnset policy schemaがv2ではありません")
    if policy.get("policy_version") != "stage61-native-no-remakes-v1.3":
        _fail("固定採用作品policyがv1.3ではありません")
    extensions = policy.get("extension_moves")
    expected = [{
        "official_move_id": 502,
        "proposed_project_move_id": 1063,
        "proposed_key": "MOVE_KEY_ALLYSWITCH",
        "name_ja": "サイドチェンジ",
        "status": "SPEC_ONLY_REQUIRES_ENGINE_IMPLEMENTATION",
    }]
    if extensions != expected:
        _fail("Side Change ID1063 reservationが固定仕様と異なります")
    return policy


def _load_crosswalk(
    rows: Sequence[Mapping[str, str]], moves: Any,
) -> dict[int, dict[str, Any]]:
    by_official: dict[int, dict[str, Any]] = {}
    for row in rows:
        official = _strict_int(row.get("official_move_id"), "crosswalk official_move_id")
        project = _strict_int(row.get("project_move_id"), f"move {official}:project_move_id")
        if official in by_official:
            _fail(f"official Move対応が重複しています: {official}")
        normalized = dict(row)
        normalized["official_move_id"] = official
        normalized["project_move_id"] = project
        normalized["existing_vega_move_id"] = (
            _strict_int(row["existing_vega_move_id"], f"move {official}:existing")
            if row.get("existing_vega_move_id", "") else None
        )
        key = row.get("project_move_key", "")
        if project == 1063:
            if key != "MOVE_KEY_ALLYSWITCH" or row.get("implementation_status") \
                    != "SPEC_ONLY_REQUIRES_ENGINE_IMPLEMENTATION":
                _fail("Move 1063をruntime実装済みとして扱えません")
            if project in moves.by_id:
                _fail("Move 1063は現行manifestの外でなければなりません")
        else:
            manifest = moves.by_id.get(project)
            if manifest is None or manifest["move_key"] != key:
                _fail(f"Move crosswalkがmanifestと一致しません: {official}->{project}")
        by_official[official] = normalized
    if len(by_official) != 807:
        _fail(f"Move crosswalk件数が807ではありません: {len(by_official)}")
    if [row["project_move_id"] for row in by_official.values()].count(1063) != 1:
        _fail("Side Changeのcrosswalkが一意ではありません")
    return by_official


def _validate_route(
    route: Mapping[str, Any], crosswalk: Mapping[int, Mapping[str, Any]],
) -> str:
    missing = sorted(REQUIRED_ROUTE_FIELDS - set(route))
    if missing:
        _fail(f"route必須fieldがありません: {missing}")
    route_id = str(route["route_id"])
    if re.fullmatch(r"[0-9a-f]{24}", route_id) is None:
        _fail(f"route_idが24桁hexではありません: {route_id!r}")
    official = _strict_int(route["official_move_id"], f"route {route_id}:official_move_id")
    project = _strict_int(route["project_move_id"], f"route {route_id}:project_move_id")
    mapping = crosswalk.get(official)
    if mapping is None or mapping["project_move_id"] != project:
        _fail(f"routeのMove対応がcrosswalkと一致しません: {route_id}")
    if route["existing_vega_move_id"] != mapping["existing_vega_move_id"]:
        _fail(f"routeのexisting Move assertionが一致しません: {route_id}")
    consumer = consumer_for_route(route)
    kind = route["route_kind"]
    if kind == "pre_evolution" and route.get("target_learning_level") is not None:
        _fail(f"進化前持ち越しを対象自身のlevelへ転記しています: {route_id}")
    if kind == "form_change" and not route.get("form_change_condition_ja"):
        _fail(f"姿変更経路の条件がありません: {route_id}")
    if kind == "shared_egg" and not route.get("acquisition_condition_ja"):
        _fail(f"共有タマゴ経路の手順がありません: {route_id}")
    return consumer


def _compile_route_row(
    target: Mapping[str, Any], route: Mapping[str, Any],
    crosswalk: Mapping[int, Mapping[str, Any]],
    catalog: Mapping[tuple[str, int], int],
) -> dict[str, Any]:
    """1経路をlosslessに注釈し、元のroute objectを変更せず返す。"""

    consumer = _validate_route(route, crosswalk)
    mapping = crosswalk[route["official_move_id"]]
    compiled: dict[str, Any] = {
        "target_species_key": target["species_key"],
        "target_species_id": target["canonical_id"],
        "target_form_key": target["form_key"],
        "reference_id": target["reference_id"],
        "consumer": consumer,
        "move_key": mapping["project_move_key"],
        "runtime_move_ready": route["project_move_id"] != 1063,
        "source_route": dict(route),
    }
    if route["route_kind"] == "direct" and route["method"] in {"tm", "tr", "tutor"}:
        family = "tutor" if route["method"] == "tutor" else "machine"
        slot = catalog.get((family, route["project_move_id"]))
        compiled["runtime_supply"] = {
            "family": family,
            "source_machine_item": route["machine_item"],
            "source_machine_namespace": "ORIGINAL_GAME_NOT_RUNTIME_SLOT",
            "status": "EXISTING_RUNTIME_SLOT" if slot is not None else "SUPPLY_REQUIRED",
            "runtime_slot_zero_based": slot,
        }
    elif route["route_kind"] in {"pre_evolution", "form_change"}:
        compiled["runtime_supply"] = {
            "status": "CARRY_ONLY_NO_TARGET_DIRECT_BIT",
            "source_machine_item": route["machine_item"],
        }
    return compiled


def _make_adopted_record(
    reference: Mapping[str, Any], target: Mapping[str, Any],
    crosswalk: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    required_new = [
        crosswalk[official]["project_move_id"]
        for official in reference["unimplemented_official_move_ids"]
    ]
    return {
        "all_move_ids": reference["all_project_move_ids"],
        "all_official_move_ids": reference["all_official_move_ids"],
        "evidence": "OFFICIAL_GAME_REFERENCE_SPEC_NOT_ROM",
        "id_namespace": (
            "project_move_id (existing Vega IDs + explicitly declared spec extensions)"
        ),
        "new_engine_move_ids_required": required_new,
        "reference_id": reference["reference_id"],
        "routes": reference["routes"],
        "schema_version": 2,
        "stage61_key": target["species_key"],
        "vega_species_id": target["canonical_id"],
    }


def _validate_adopted_record(
    record: Mapping[str, Any], target: Mapping[str, Any], meta: _ReferenceMeta,
    crosswalk: Mapping[int, Mapping[str, Any]],
) -> None:
    if set(record) != ADOPTED_FIELDS:
        _fail(f"adopted record field契約が不正です: {target['species_key']}")
    expected_top = {
        "all_move_ids": list(meta.all_project_move_ids),
        "all_official_move_ids": list(meta.all_official_move_ids),
        "evidence": "OFFICIAL_GAME_REFERENCE_SPEC_NOT_ROM",
        "id_namespace": (
            "project_move_id (existing Vega IDs + explicitly declared spec extensions)"
        ),
        "new_engine_move_ids_required": [
            crosswalk[value]["project_move_id"]
            for value in meta.unimplemented_official_move_ids
        ],
        "reference_id": meta.reference_id,
        "schema_version": 2,
        "stage61_key": target["species_key"],
        "vega_species_id": target["canonical_id"],
    }
    actual_top = {key: value for key, value in record.items() if key != "routes"}
    if actual_top != expected_top:
        _fail(f"adopted record上位fieldが参考表と一致しません: {target['species_key']}")
    routes = record.get("routes")
    if not isinstance(routes, list) or len(routes) != meta.route_count \
            or _object_sha(routes) != meta.routes_sha256:
        _fail(f"adopted route全内容が参考表と一致しません: {target['species_key']}")


def _validate_decisions(
    rows: Sequence[Mapping[str, str]], targets: Mapping[str, Mapping[str, Any]],
) -> None:
    if len(rows) != 1621:
        _fail(f"record decisionsが1621件ではありません: {len(rows)}")
    seen: set[str] = set()
    for row in rows:
        key = row.get("stage61_key", "")
        target = targets.get(key)
        if target is None or key in seen:
            _fail(f"record decision keyが未知または重複です: {key}")
        seen.add(key)
        if _strict_int(row.get("vega_species_id"), f"{key}:vega_species_id") \
                != target["canonical_id"]:
            _fail(f"record decisionの数値ID assertionが不正です: {key}")
        source_apply = row.get("apply") == "True"
        if row.get("apply") not in {"True", "False"} \
                or source_apply != target["input"]["apply"] \
                or row.get("reference_id", "") != target["reference_id"]:
            _fail(f"record decisionがP01 identity入力と一致しません: {key}")
    if seen != set(targets):
        _fail("record decision集合がP01 target集合と一致しません")


def _validate_base_species(
    rows: Sequence[Mapping[str, str]], references: Mapping[str, _ReferenceMeta],
) -> dict[str, Any]:
    numbers = [_strict_int(row.get("national_no"), "base national_no") for row in rows]
    refs = [row.get("reference_id", "") for row in rows]
    if numbers != list(range(1, 1026)) or len(set(refs)) != 1025:
        _fail("原作基本1025種の集合・順序が不正です")
    missing = sorted(set(refs) - set(references))
    if missing:
        _fail(f"基本種のreferenceがありません: {missing[:8]}")
    return {
        "rows": 1025,
        "national_no_min": 1,
        "national_no_max": 1025,
        "reference_id_set_sha256": _set_sha(refs),
    }


def _load_runtime_supply(
    projection_rows: Sequence[Mapping[str, str]],
    missing_rows: Sequence[Mapping[str, str]],
    targets: Mapping[str, Mapping[str, Any]],
    species_manifest: Any,
) -> tuple[
    dict[tuple[str, int], int], set[tuple[int, str, int]], set[tuple[int, str, int]],
]:
    targets_by_id = {row["canonical_id"]: row for row in targets.values()}
    catalog: dict[tuple[str, int], int] = {}
    projection: set[tuple[int, str, int]] = set()
    for row in projection_rows:
        species = _strict_int(row.get("vega_species_id"), "projection species")
        family = row.get("runtime_family", "")
        move = _strict_int(row.get("project_move_id"), "projection move")
        slot = _strict_int(row.get("slot_zero_based"), "projection slot")
        target = targets_by_id.get(species)
        manifest = species_manifest.by_id.get(species)
        if target is None or manifest is None \
                or row.get("name_ja") != manifest["display_name"] \
                or row.get("form_key", "") != target["form_key"] \
                or row.get("selected_game", "") != target["selected_game"]:
            _fail(f"projection SpeciesのID/名前/form/game意味が一致しません: {species}")
        if family not in {"machine", "tutor"} \
                or (family == "machine" and not 0 <= slot < 128) \
                or (family == "tutor" and not 0 <= slot < 64) \
                or row.get("projection_only") != "True":
            _fail(f"runtime slot projection rowが不正です: {row}")
        key = (family, move)
        previous = catalog.setdefault(key, slot)
        if previous != slot:
            _fail(f"同じMoveが複数runtime slotへ対応しています: {key}")
        value = (species, family, move)
        if value in projection:
            _fail(f"runtime projectionが重複しています: {value}")
        projection.add(value)

    missing: set[tuple[int, str, int]] = set()
    for row in missing_rows:
        species = _strict_int(row.get("vega_species_id"), "missing supply species")
        family = row.get("family", "")
        move = _strict_int(row.get("project_move_id"), "missing supply move")
        manifest = species_manifest.by_id.get(species)
        if species not in targets_by_id or manifest is None \
                or row.get("name_ja") != manifest["display_name"] \
                or family not in {"machine", "tutor"}:
            _fail(f"未配置Move rowが不正です: {row}")
        value = (species, family, move)
        if value in missing or value in projection:
            _fail(f"供給projection/missingが重複しています: {value}")
        if (family, move) in catalog:
            _fail(f"既存slotのあるMoveをmissingへ分類しています: {value}")
        missing.add(value)
    if len(projection) != 29_772 or len(missing) != 26_720:
        _fail("原本runtime projection/missing件数が固定値と異なります")
    return catalog, projection, missing


def iter_compiled_p03_routes(
    root: Path, learnsets_zip: Path, *, consumer: str | None = None,
) -> Iterator[dict[str, Any]]:
    """訂正後118,528経路をcanonical ID順に逐次返す。

    `consumer`を指定しても全入力を検証しながら対象経路だけをyieldする。呼出側は
    generatorを最後まで消費して、末尾の集合・件数検査も必ず実行させること。
    """

    if consumer is not None and consumer not in CONSUMERS:
        _fail(f"未知のP03 consumerです: {consumer}")
    root = root.resolve()
    _, targets, manifests = _load_identity(root)
    input_true = {key for key, row in targets.items() if row["input"]["apply"]}
    normalized_true = {key for key, row in targets.items() if row["normalized"]["apply"]}
    with CheckedArchive(learnsets_zip, "learnsets") as archive:
        crosswalk = _load_crosswalk(
            _csv_member(archive, "data/move_id_crosswalk.csv"), manifests["moves"],
        )
        catalog, _, _ = _load_runtime_supply(
            _csv_member(archive, "implementation/existing_runtime_slot_projection.csv"),
            _csv_member(archive, "implementation/moves_without_existing_slot.csv"),
            targets, manifests["species"],
        )
        caterpie_reference: dict[str, Any] | None = None
        for reference in _iter_jsonl_member(archive, "data/reference_learnsets.jsonl"):
            if reference.get("reference_id") == "swordshield:0010.00":
                caterpie_reference = reference
        if caterpie_reference is None:
            _fail("キャタピー参考表がありません")
        caterpie_record = _make_adopted_record(
            caterpie_reference, targets["SPECIES_KEY_CATERPIE"], crosswalk,
        )

        seen_source: set[str] = set()
        seen_corrected: set[str] = set()
        seen_routes: set[str] = set()
        counts: Counter[str] = Counter()

        def rows_for(record: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
            key = str(record.get("stage61_key", ""))
            target = targets.get(key)
            if target is None or key in seen_corrected:
                _fail(f"訂正後import targetが未知または重複です: {key}")
            if record.get("vega_species_id") != target["canonical_id"] \
                    or record.get("reference_id") != target["reference_id"]:
                _fail(f"訂正後importのkey/ID/reference assertionが不正です: {key}")
            seen_corrected.add(key)
            for route in record.get("routes", []):
                compiled = _compile_route_row(target, route, crosswalk, catalog)
                route_key = f"{key}:{route['route_id']}"
                if route_key in seen_routes:
                    _fail(f"訂正後import routeが重複しています: {route_key}")
                seen_routes.add(route_key)
                counts[compiled["consumer"]] += 1
                if consumer is None or compiled["consumer"] == consumer:
                    yield compiled

        previous_id = -1
        inserted = False
        for record in _iter_jsonl_member(archive, "data/adopted_stage61_learnsets.jsonl"):
            key = str(record.get("stage61_key", ""))
            target = targets.get(key)
            if target is None or key not in input_true or key in seen_source:
                _fail(f"原本adopted import targetが未知・除外・重複です: {key}")
            canonical_id = target["canonical_id"]
            if canonical_id <= previous_id:
                _fail(f"原本adopted import orderが不正です: {key}")
            previous_id = canonical_id
            if not inserted and canonical_id > 649:
                yield from rows_for(caterpie_record)
                inserted = True
            yield from rows_for(record)
            seen_source.add(key)
        if not inserted:
            yield from rows_for(caterpie_record)
        if seen_source != input_true or seen_corrected != normalized_true \
                or len(seen_routes) != 118_528 or dict(counts) != EXPECTED_COMPILED_COUNTS:
            _fail(
                "P03 streaming importの採用集合または9経路分割が固定契約と一致しません"
            )


def _runtime_connection_contract(root: Path) -> dict[str, Any]:
    config_path = root / "config/move_distribution_v4.json"
    hotfix_path = root / "config/stage61_runtime_hotfix.json"
    consumer_path = root / "content/move_distribution_v4/consumer_contract.json"
    try:
        config = json.loads(config_path.read_bytes())
        hotfix = json.loads(hotfix_path.read_bytes())
        consumers = json.loads(consumer_path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"現行learnset runtime契約を読めません: {error}")
    counts = config.get("counts", {})
    if counts.get("species") != 1621 or counts.get("moves") != 1063 \
            or counts.get("tm_slots") != 120 or counts.get("tutor_slots") != 64 \
            or counts.get("compatibility_stride") != 16:
        _fail("現行Move Distribution runtime容量契約が想定外です")
    if consumers.get("canonical_owner") != "MOVE_DISTRIBUTION_V4_STAGE39_TABLES":
        _fail("現行learnset consumer ownerが想定外です")
    runtime = hotfix.get("rom_contract", {})
    return {
        "source_files": [
            _file_identity(root, value) for value in (
                "scripts/build_species_surface.py",
                "scripts/build_move_distribution_v4.py",
                "scripts/build_move_memory.py",
                "scripts/build_stage61_runtime_hotfix.py",
                "config/move_distribution_v4.json",
                "config/stage61_runtime_hotfix.json",
                "content/move_distribution_v4/consumer_contract.json",
            )
        ],
        "current_abi": {
            "species_count": 1621,
            "implemented_move_ids": "0..1062",
            "move_count": 1063,
            "level_up": {
                "root_sites": config["stage38_roots"]["level_up"],
                "runtime_literal_site": config["stage38_roots"]["level_up_runtime_literal"],
                "row": "U16_PROJECT_MOVE_ID + U8_LEVEL",
                "terminator": "0000FF",
            },
            "egg": {
                "root_site": config["stage38_roots"]["egg"],
                "row": "U16; 20000+species marker / project Move ID / FFFF terminator",
            },
            "machine_compatibility": {
                "root_site": hotfix["rom_contract"]["stage61_tmhm_root_site"],
                "stride": 16,
                "tm_slots": 120,
                "hm_runtime_indices": "120..127",
                "catalog_root_site": runtime["tmhm_moves_root_site"],
            },
            "tutor_compatibility": {
                "root_site": config["stage38_roots"]["tutor"],
                "stride": 16,
                "slots": 64,
                "catalog_root_site": runtime["tutor_moves_root_site"],
            },
        },
        "current_consumers": consumers["consumers"],
        "integration_rule": (
            "parent ROMのpointer siteを再解決し、metadata/allocationを継承して新表へrepointする。"
            "Stage38のexpected addressを後続Stageへ固定流用しない。"
        ),
    }


def build_p03_artifacts(root: Path, learnsets_zip: Path) -> P03Artifacts:
    """固定原本を一回ずつstreamし、訂正・compile・compact契約を生成する。"""

    root = root.resolve()
    identity, targets, manifests = _load_identity(root)
    identity_raw = (root / IDENTITY_CONTRACT).read_bytes()
    input_true = {key for key, row in targets.items() if row["input"]["apply"]}
    normalized_true = {key for key, row in targets.items() if row["normalized"]["apply"]}

    with CheckedArchive(learnsets_zip, "learnsets") as archive:
        if archive.identity()["archive_root"] != ARCHIVE_ROOT:
            _fail("learnset ZIP rootが固定値と異なります")

        # 説明・rules・validatorも固定入力として読み、hashを検査する。
        for relative in (
            "README_JA.md", "SCHEMA_JA.md", "implementation/README_JA.md",
            "scripts/validate_v13.py", "scripts/learning_rules_v13.py",
        ):
            _read_member(archive, relative)
        policy = _validate_policy(_json_member(archive, "config/policy.json"))
        acceptance = _json_member(archive, "validation/acceptance_v13.json")
        if acceptance.get("status") != "PASS" or acceptance.get("passed") != 26 \
                or acceptance.get("route_counts") != EXPECTED_REFERENCE_ROUTE_COUNTS:
            _fail("v1.3原本validator acceptanceが固定PASS結果ではありません")
        form_map = _json_member(archive, "config/stage61_form_map.json")
        if not isinstance(form_map, list) or len(form_map) != 1413:
            _fail("Stage61 form mapが1413件ではありません")

        decision_rows = _csv_member(archive, "data/stage61_record_decisions.csv")
        _validate_decisions(decision_rows, targets)
        crosswalk = _load_crosswalk(
            _csv_member(archive, "data/move_id_crosswalk.csv"), manifests["moves"],
        )
        base_rows = _csv_member(archive, "data/base_species_1025.csv")
        adopted_move_rows = _csv_member(
            archive, "implementation/adopted_project_move_ids.csv",
        )
        projection_rows = _csv_member(
            archive, "implementation/existing_runtime_slot_projection.csv",
        )
        missing_rows = _csv_member(
            archive, "implementation/moves_without_existing_slot.csv",
        )
        new_moves = _json_member(archive, "implementation/new_move_definitions.json")
        expected_new = policy["extension_moves"][0]
        if new_moves.get("status") != "SPECIFICATION_ONLY" \
                or new_moves.get("existing_rom_modified") is not False \
                or len(new_moves.get("moves", [])) != 1:
            _fail("new Move定義をruntime実装済みとして扱えません")
        new_move = new_moves["moves"][0]
        if any(new_move.get(key) != value for key, value in {
            "official_move_id": expected_new["official_move_id"],
            "project_move_id": expected_new["proposed_project_move_id"],
            "project_move_key": expected_new["proposed_key"],
            "move_name_ja": expected_new["name_ja"],
            "implementation_status": expected_new["status"],
        }.items()):
            _fail("new Move 1063定義がpolicy reservationと一致しません")

        catalog, source_projection, source_missing = _load_runtime_supply(
            projection_rows, missing_rows, targets, manifests["species"],
        )

        references: dict[str, _ReferenceMeta] = {}
        reference_route_ids: set[str] = set()
        reference_kinds: Counter[str] = Counter()
        reference_methods: Counter[str] = Counter()
        caterpie_reference: dict[str, Any] | None = None
        reference_records_digest = _FramedDigest()
        for reference in _iter_jsonl_member(archive, "data/reference_learnsets.jsonl"):
            reference_id = str(reference.get("reference_id", ""))
            if not reference_id or reference_id in references:
                _fail(f"reference_idが空または重複です: {reference_id!r}")
            routes = reference.get("routes")
            if not isinstance(routes, list):
                _fail(f"reference routesがarrayではありません: {reference_id}")
            local_ids: set[str] = set()
            for route in routes:
                consumer_for_route(route)
                _validate_route(route, crosswalk)
                route_id = route["route_id"]
                if route_id in local_ids or route_id in reference_route_ids:
                    _fail(f"reference route_idが重複しています: {route_id}")
                local_ids.add(route_id)
                reference_route_ids.add(route_id)
                reference_kinds[route["route_kind"]] += 1
                reference_methods[route["method"]] += 1
            meta = _ReferenceMeta(
                reference_id=reference_id,
                record_sha256=_object_sha(reference),
                routes_sha256=_object_sha(routes),
                route_count=len(routes),
                all_official_move_ids=tuple(reference.get("all_official_move_ids", [])),
                all_project_move_ids=tuple(reference.get("all_project_move_ids", [])),
                unimplemented_official_move_ids=tuple(
                    reference.get("unimplemented_official_move_ids", [])
                ),
            )
            references[reference_id] = meta
            reference_records_digest.add(reference)
            if reference_id == "swordshield:0010.00":
                caterpie_reference = reference
        if len(references) != 1377 \
                or dict(reference_kinds) != EXPECTED_REFERENCE_ROUTE_COUNTS \
                or len(reference_route_ids) != 125_746:
            _fail(
                "reference全経路集合が固定仕様と一致しません: "
                f"records={len(references)} routes={len(reference_route_ids)} "
                f"kinds={dict(reference_kinds)}"
            )
        if caterpie_reference is None:
            _fail("キャタピー参考表がありません")
        base_contract = _validate_base_species(base_rows, references)

        source_move_rows_by_id: dict[int, Mapping[str, str]] = {}
        for row in adopted_move_rows:
            species = _strict_int(row.get("vega_species_id"), "adopted move species")
            if species in source_move_rows_by_id:
                _fail(f"adopted move handoff Speciesが重複しています: {species}")
            source_move_rows_by_id[species] = row
        if len(source_move_rows_by_id) != 1299:
            _fail("adopted move handoffが1299件ではありません")

        caterpie_record = _make_adopted_record(
            caterpie_reference, targets["SPECIES_KEY_CATERPIE"], crosswalk,
        )
        compiled_counts: Counter[str] = Counter()
        compiled_digests = {name: _FramedDigest() for name in CONSUMERS}
        corrected_route_keys: set[str] = set()
        corrected_records_digest = _FramedDigest()
        corrected_routes_digest = _FramedDigest()
        compiled_index_rows: list[dict[str, Any]] = []
        corrected_supply_pairs: set[tuple[int, str, int]] = set()
        source_supply_pairs: set[tuple[int, str, int]] = set()
        side_targets: set[str] = set()
        side_counts: Counter[str] = Counter()
        caterpie_fixture: list[dict[str, Any]] = []
        carry_fixture: dict[str, Any] | None = None
        form_fixture: dict[str, Any] | None = None
        corrected_seen_keys: set[str] = set()

        def compile_record(record: dict[str, Any], origin: str) -> None:
            nonlocal carry_fixture, form_fixture
            key = record["stage61_key"]
            target = targets[key]
            meta = references[target["reference_id"]]
            if key in corrected_seen_keys:
                _fail(f"訂正後採用keyが重複しています: {key}")
            corrected_seen_keys.add(key)
            if origin == "ADD_CATERPIE_FROM_REFERENCE":
                _validate_adopted_record(record, target, meta, crosswalk)
            corrected_records_digest.add(record)
            per_counts: Counter[str] = Counter()
            per_digests = {name: _FramedDigest() for name in CONSUMERS}
            per_route_ids: set[str] = set()
            for route in record["routes"]:
                compiled = _compile_route_row(target, route, crosswalk, catalog)
                consumer = compiled["consumer"]
                route_id = route["route_id"]
                route_key = f"{key}:{route_id}"
                if route_key in corrected_route_keys or route_id in per_route_ids:
                    _fail(f"訂正後target+route identityが重複しています: {route_key}")
                per_route_ids.add(route_id)
                corrected_route_keys.add(route_key)
                if route["route_kind"] == "direct" and route["method"] in {"tm", "tr", "tutor"}:
                    family = "tutor" if route["method"] == "tutor" else "machine"
                    pair = (target["canonical_id"], family, route["project_move_id"])
                    corrected_supply_pairs.add(pair)
                    if origin == "PRESERVE_SOURCE_ADOPTED":
                        source_supply_pairs.add(pair)
                per_counts[consumer] += 1
                compiled_counts[consumer] += 1
                per_digests[consumer].add(compiled)
                compiled_digests[consumer].add(compiled)
                corrected_routes_digest.add(compiled)
                if route["project_move_id"] == 1063:
                    side_targets.add(key)
                    side_counts[consumer] += 1
                if key == "SPECIES_KEY_CATERPIE":
                    caterpie_fixture.append({
                        "route_id": route_id,
                        "consumer": consumer,
                        "method": route["method"],
                        "project_move_id": route["project_move_id"],
                        "source_machine_item": route["machine_item"],
                        "runtime_slot_zero_based": (
                            compiled.get("runtime_supply", {}).get("runtime_slot_zero_based")
                        ),
                    })
                if consumer == "pre_evolution_carry" and carry_fixture is None:
                    carry_fixture = {
                        "target_species_key": key, "route_id": route_id,
                        "route_kind": route["route_kind"], "method": route["method"],
                        "target_learning_level": route["target_learning_level"],
                        "donor_learning_level": route["donor_learning_level"],
                        "runtime_supply_status": compiled["runtime_supply"]["status"],
                    }
                if consumer == "form_change" and form_fixture is None:
                    form_fixture = {
                        "target_species_key": key, "route_id": route_id,
                        "route_kind": route["route_kind"], "method": route["method"],
                        "form_change_condition_ja": route["form_change_condition_ja"],
                    }
            compiled_index_rows.append({
                "species_key": key,
                "canonical_id": target["canonical_id"],
                "form_key": target["form_key"],
                "reference_id": target["reference_id"],
                "origin": origin,
                "record_content_sha256": _object_sha(record),
                "reference_content_sha256": meta.record_sha256,
                "route_count": len(record["routes"]),
                "route_id_set_sha256": _set_sha(per_route_ids),
                "consumer_counts": dict(sorted(per_counts.items())),
                "consumer_content_sha256": {
                    name: per_digests[name].hexdigest()
                    for name in CONSUMERS if per_digests[name].count
                },
            })

        # 182 MBの原本をlist化せず、canonical ID順にCaterpieだけを挿入して逐次compileする。
        source_seen: set[str] = set()
        previous_id = -1
        caterpie_inserted = False
        for record in _iter_jsonl_member(archive, "data/adopted_stage61_learnsets.jsonl"):
            key = str(record.get("stage61_key", ""))
            target = targets.get(key)
            if target is None or key not in input_true or key in source_seen:
                _fail(f"原本adopted targetが未知・除外・重複です: {key}")
            canonical_id = target["canonical_id"]
            if record.get("vega_species_id") != canonical_id or canonical_id <= previous_id:
                _fail(f"原本adoptedのcanonical ID assertion/orderが不正です: {key}")
            previous_id = canonical_id
            meta = references.get(target["reference_id"])
            if meta is None:
                _fail(f"採用targetのreferenceがありません: {key}")
            _validate_adopted_record(record, target, meta, crosswalk)
            handoff = source_move_rows_by_id.get(canonical_id)
            if handoff is None \
                    or json.loads(handoff["all_official_move_ids"]) != record["all_official_move_ids"] \
                    or json.loads(handoff["all_project_move_ids"]) != record["all_move_ids"] \
                    or json.loads(handoff["required_new_official_move_ids"]) \
                    != list(meta.unimplemented_official_move_ids):
                _fail(f"adopted move handoffがJSONL正本と一致しません: {key}")
            if not caterpie_inserted and canonical_id > 649:
                compile_record(caterpie_record, "ADD_CATERPIE_FROM_REFERENCE")
                caterpie_inserted = True
            compile_record(record, "PRESERVE_SOURCE_ADOPTED")
            source_seen.add(key)
        if not caterpie_inserted:
            compile_record(caterpie_record, "ADD_CATERPIE_FROM_REFERENCE")
        if source_seen != input_true or len(compiled_index_rows) != 1300:
            _fail("原本1299件または訂正後1300件の採用集合が一致しません")
        if corrected_seen_keys != normalized_true \
                or corrected_seen_keys - source_seen != {"SPECIES_KEY_CATERPIE"}:
            _fail("訂正後集合がP01 normalized apply集合と一致しません")

        if len(corrected_route_keys) != 118_528 \
                or dict(compiled_counts) != EXPECTED_COMPILED_COUNTS \
                or sum(compiled_counts.values()) != len(corrected_route_keys):
            _fail(
                "訂正後経路の9分割が固定仕様と一致しません: "
                f"routes={len(corrected_route_keys)} counts={dict(compiled_counts)}"
            )
        if source_supply_pairs != source_projection | source_missing \
                or source_projection & source_missing:
            _fail("原本のdirect TM/TR/tutor集合がprojection+missingと一致しません")
        corrected_projection = {
            pair for pair in corrected_supply_pairs if (pair[1], pair[2]) in catalog
        }
        corrected_missing = corrected_supply_pairs - corrected_projection
        if len(corrected_projection) != 29_773 or len(corrected_missing) != 26_720 \
                or corrected_projection - source_projection \
                != {(649, "machine", 489)} \
                or corrected_missing != source_missing:
            _fail("キャタピー訂正後のruntime供給集合が期待値と一致しません")
        if sorted((row["consumer"], row["method"], row["project_move_id"])
                  for row in caterpie_fixture) != [
            ("level_up", "level_up", 33),
            ("level_up", "level_up", 81),
            ("level_up", "level_up", 535),
            ("machine", "tm", 489),
        ]:
            _fail("キャタピーの4経路内容が固定参考表と一致しません")
        caterpie_machine = next(row for row in caterpie_fixture if row["consumer"] == "machine")
        if caterpie_machine["source_machine_item"] != "TM82" \
                or caterpie_machine["runtime_slot_zero_based"] != 116:
            _fail("原作TM82と現runtime slot 116を混同しています")

        archive_identity = archive.identity()

    missing_by_family: dict[str, set[int]] = defaultdict(set)
    for _, family, move in corrected_missing:
        missing_by_family[family].add(move)
    projected_by_family = Counter(family for _, family, _ in corrected_projection)
    missing_rows_by_family = Counter(family for _, family, _ in corrected_missing)
    route_contract = {
        name: {
            "count": compiled_counts[name],
            "content_sha256": compiled_digests[name].hexdigest(),
        }
        for name in CONSUMERS
    }
    contract = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": "PASS",
        "policy": {
            "source_archive": "IMMUTABLE_STREAM_ONLY",
            "adoption": "REPLACE_NORMAL_TARGET_WITH_FIXED_REFERENCE_NOT_UNION",
            "identity_join": "SPECIES_KEY_THEN_ASSERT_CANONICAL_ID",
            "route_partition": "EXACTLY_ONE_OF_NINE_CONSUMERS",
            "carry_to_direct_conversion": "FORBIDDEN",
            "original_machine_number_as_runtime_slot": "FORBIDDEN",
            "missing_runtime_slot_as_cannot_learn": "FORBIDDEN",
            "existing_party_box_save_rewrite": "FORBIDDEN",
            "trainer_facility_explicit_parties": "OUTSIDE_P03_AND_PRESERVED",
        },
        "inputs": {
            "learnsets": {
                **archive_identity,
                "authoritative_members": {
                    relative: {"size": size, "sha256": digest}
                    for relative, (size, digest) in sorted(EXPECTED_MEMBER_IDENTITIES.items())
                },
            },
            "identity_contract": {
                "path": IDENTITY_CONTRACT.as_posix(),
                "size": len(identity_raw),
                "sha256": _sha(identity_raw),
            },
            "fixed_policy_version": policy["policy_version"],
            "upstream_validation": {
                "status": acceptance["status"],
                "passed": acceptance["passed"],
                "failed": acceptance["failed"],
            },
        },
        "correction": {
            "source_adopted_records": 1299,
            "corrected_adopted_records": 1300,
            "added_keys": ["SPECIES_KEY_CATERPIE"],
            "removed_keys": [],
            "protected_false_targets": len(targets) - len(normalized_true),
            "caterpie": {
                "species_key": "SPECIES_KEY_CATERPIE",
                "canonical_id": 649,
                "reference_id": "swordshield:0010.00",
                "route_count": 4,
                "compiled_routes": caterpie_fixture,
            },
            "egg": {
                "species_key": "SPECIES_KEY_EGG",
                "canonical_id": 412,
                "apply": False,
            },
        },
        "source_reference": {
            "base_species": base_contract,
            "reference_records": len(references),
            "routes": len(reference_route_ids),
            "route_kind_counts": dict(sorted(reference_kinds.items())),
            "method_counts": dict(sorted(reference_methods.items())),
            "record_content_sha256": reference_records_digest.hexdigest(),
            "route_id_set_sha256": _set_sha(reference_route_ids),
        },
        "corrected_adoption": {
            "records": len(compiled_index_rows),
            "routes": len(corrected_route_keys),
            "record_content_sha256": corrected_records_digest.hexdigest(),
            "compiled_route_content_sha256": corrected_routes_digest.hexdigest(),
            "target_route_key_set_sha256": _set_sha(corrected_route_keys),
            "consumers": route_contract,
        },
        "runtime_supply": {
            "direct_machine_tutor_pairs": len(corrected_supply_pairs),
            "existing_slot_projection_rows": len(corrected_projection),
            "supply_required_rows": len(corrected_missing),
            "projected_rows_by_family": dict(sorted(projected_by_family.items())),
            "supply_required_rows_by_family": dict(sorted(missing_rows_by_family.items())),
            "supply_required_distinct_moves_by_family": {
                family: len(values) for family, values in sorted(missing_by_family.items())
            },
            "projection_set_sha256": _set_sha(
                f"{species}:{family}:{move}:{catalog[(family, move)]}"
                for species, family, move in corrected_projection
            ),
            "supply_required_set_sha256": _set_sha(
                f"{species}:{family}:{move}" for species, family, move in corrected_missing
            ),
            "resolution": (
                "既存slotはruntime zero-based indexへ投影。未配置は削除せず、"
                "catalog/compatibility拡張または別供給経路が実装されるまで依存として保持。"
            ),
        },
    }
    compiled_index = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": "PASS",
        "materialization": (
            "COMPACT_HASH_INDEX_ONLY; full routes remain solely in immutable source ZIP"
        ),
        "ordering": "canonical Species ID ascending; source route order preserved",
        "record_count": len(compiled_index_rows),
        "route_count": len(corrected_route_keys),
        "records": compiled_index_rows,
    }
    runtime_connection = _runtime_connection_contract(root)
    runtime_handoff = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": "DATA_CONTRACT_READY_RUNTIME_WORK_REMAINS",
        "consumer_compilation": {
            "level_up": "direct/level_upだけをlevel-up表へserialize",
            "evolution": "direct/evolutionを進化時consumerへ別serialize",
            "reminder": "direct/reminderを思い出しconsumerへ別serialize",
            "machine": "direct/tm|trだけ。machine_itemは原作番号、runtime_slotはprojectionから解決",
            "tutor": "direct/tutorだけ。runtime slot projectionと供給不足を分離",
            "egg": "direct/egg|special_breeding。特殊条件を通常eggへ無条件化しない",
            "shared_egg": "shared_egg routeだけ。共有手順・受け手・作品条件を保持",
            "pre_evolution_carry": "全pre_evolution route。対象の直接表/compatibility bitへ書かない",
            "form_change": "form_change routeとdirect form_move/battle_transform。恒久技化しない",
        },
        "connection_points": runtime_connection,
        "preservation": {
            "new_normal_mon_generation": "同一正本のlevel-up consumerを使用して初期4枠を決定",
            "wild_generation": "新規生成時だけ照合。既存party/box/saveロード時は変更しない",
            "move_memory": "level/evolution/reminder/egg/shared/carry/formの条件付きqueryを統合",
            "trainer_facility": "明示手持ちは別正本として保持し、自動置換しない",
        },
        "unresolved_supply": contract["runtime_supply"],
        "side_change_1063": {
            "status": "BLOCKING_RUNTIME_DEPENDENCY_NOT_IMPLEMENTED",
            "project_move_id": 1063,
            "project_move_key": "MOVE_KEY_ALLYSWITCH",
            "official_move_id": 502,
            "definition": {
                "type_id": new_move["type_id"],
                "damage_class_id": new_move["damage_class_id"],
                "power": new_move["power"],
                "pp": new_move["pp"],
                "accuracy": new_move["accuracy"],
                "priority": new_move["priority"],
            },
            "adopted_target_count": len(side_targets),
            "adopted_route_count": sum(side_counts.values()),
            "routes_by_consumer": dict(sorted(side_counts.items())),
            "required_runtime_work": {
                "identity_and_tables": [
                    "Move manifest/capacityをID 1063を含む1064件へ拡張",
                    "gBattleMoves、name、description、animation、全fixed-count guardを同じidentityへ更新",
                ],
                "effect": [
                    "ダブル時の味方との位置交換effect、対象/失敗条件、battle scriptを実装",
                    "シングル・味方不在・交換不能時を安全に失敗させ、優先度+2を適用",
                ],
                "ai": [
                    "使用可能な味方位置と失敗条件を判定",
                    "無効局面で選ばず、位置交換の戦術価値をdouble battle AIへ接続",
                ],
                "ui": [
                    "日本語名・説明・エスパー/変化・PP15・優先度情報を表示tableへ追加",
                    "習得・思い出し・共有・機械/教え技画面で未知ID表示を起こさない",
                ],
                "verification": [
                    "effect/AI/UI、single失敗、double成功、save往復、各習得経路を実ROMで検証",
                    "実装完了まで1063を既存runtime slotまたは実装済みMoveとしてserializeしない",
                ],
            },
        },
        "fixtures": {
            "caterpie": caterpie_fixture,
            "pre_evolution_carry": carry_fixture,
            "form_change": form_fixture,
        },
    }
    return P03Artifacts(contract, compiled_index, runtime_handoff)
