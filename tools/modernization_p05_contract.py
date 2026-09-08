#!/usr/bin/env python3
"""工程5: 採用済みの技差分と新規Move/Abilityだけを固定する契約builder。

このmoduleはROMや既存manifestを変更しない。受領ZIP、P03/P04契約、現行の
canonical manifest/runtime modelを相互照合し、後続実装が必要な差分だけを
機械可読にする。履歴資料やreview-only候補を暗黙採用しないことが主目的である。
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn, Sequence

from tools.modernization_identity import CheckedArchive, load_manifests


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P05"

LEARNSETS_ZIP = (
    "userfile/imports/modernization_p01/"
    "Pokemon_Vega_Stage61_技習得品質改善版_v1.3.0_20260905.zip"
)
RESTORATION_ZIP = (
    "userfile/imports/modernization_p01/"
    "Vega_Stage61_ID固定_原作復元監査資料.zip"
)

P03_RUNTIME_PATH = "content/modernization/p03_runtime_handoff.json"

NEW_MOVE_MEMBER = "implementation/new_move_definitions.json"
MOVE_AUDIT_MEMBER = "10_既存技806件比較_表現世代差4件.csv"
RESTORATION_REVIEW_MEMBER = "11_ID固定_内容更新候補_未適用.json"

EXPECTED_MEMBER_SHA256 = {
    NEW_MOVE_MEMBER: "d5e87b2e07e6094f23780f82684812d5362eb67be7b077e731e320ba1415a696",
    MOVE_AUDIT_MEMBER: "252fdb300f960b85f71d4ed294fe1d3463bda94c17d6d4035d6de02cb5e30a84",
    RESTORATION_REVIEW_MEMBER: "262b7e437565abb860f1f4c49e041283cf6d238c2e52d642acd5eb32f706fd0a",
}

# P04が提出した場合にだけ選択できる新規Ability名前空間。ここへ無いkeyを
# 「それらしい」名前で補完することをvalidatorで拒否する。
P04_ALLOWED_NEW_ABILITY_KEYS = frozenset(
    {
        "ABILITY_KEY_PIERCINGDRILL",
        "ABILITY_KEY_DRAGONIZE",
        "ABILITY_KEY_EELEVATE",
        "ABILITY_KEY_MEGASOL",
        "ABILITY_KEY_FIREMANE",
        "ABILITY_KEY_SPICYSPRAY",
    }
)

UPSTREAM_ABILITY_SYMBOLS = {
    "ABILITY_KEY_PIERCINGDRILL": "ABILITY_PIERCING_DRILL",
    "ABILITY_KEY_DRAGONIZE": "ABILITY_DRAGONIZE",
    "ABILITY_KEY_EELEVATE": "ABILITY_EELEVATE",
    "ABILITY_KEY_MEGASOL": "ABILITY_MEGA_SOL",
    "ABILITY_KEY_FIREMANE": "ABILITY_FIRE_MANE",
    "ABILITY_KEY_SPICYSPRAY": "ABILITY_SPICY_SPRAY",
}

EXPECTED_PRESERVE_DIFFS = {
    762: ("accuracy", 0, 100, "SELF_TARGET_ACCURACY_SENTINEL"),
    779: ("accuracy", 0, 100, "SELF_TARGET_ACCURACY_SENTINEL"),
    837: ("pp", 15, 10, "FROZEN_SHOWDOWN_REFERENCE_SUPPORTS_CURRENT_PP"),
    1058: ("power", 1, 0, "VARIABLE_POWER_SENTINEL_REQUIRES_EFFECT_AUDIT"),
}

TECHNICAL_SOURCE_COMMIT = "cafe0221cefb2a991cc0ece429174ade877d037d"
TECHNICAL_SOURCE_ROOT = ".local/modernization_sources/pokeemerald-expansion"
TECHNICAL_SOURCE_REPOSITORY = "https://github.com/rh-hideout/pokeemerald-expansion"
TECHNICAL_ID_PATH = "include/constants/abilities.h"
TECHNICAL_TEXT_PATH = "src/data/abilities.h"

EXPECTED_P04_FILES = {
    "content/modernization/p04_candidate_manifest.json":
        "64e9ffbc80a4344eef82726c191da25b008c6f7d87312c2bf8186c00a36c5644",
    "content/modernization/p04_official_sources.json":
        "eadd2eea75b5a3d4c7aacf9315b3025e0e7ece945354970ac9c372eb59548fcd",
    "content/modernization/p04_asset_sources.json":
        "133c6b8dd56dc0afdb80acbb943c2e5b3ed1b72247bcc07350c78933e93e0636",
}


class ModernizationP05Error(ValueError):
    """工程5契約の入力または整合性違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP05Error(message)


def stable_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _regular_file(path: Path, label: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        _fail(f"{label}が通常ファイルではありません: {path}")
    return path.read_bytes()


def _json_bytes(raw: bytes, label: str) -> Any:
    try:
        return json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{label}がUTF-8 JSONではありません: {error}")


def _json_file(path: Path, label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = _regular_file(path, label)
    value = _json_bytes(raw, label)
    if not isinstance(value, dict):
        _fail(f"{label}のrootがobjectではありません")
    return value, {"path": path.as_posix(), "size": len(raw), "sha256": _sha256(raw)}


def _member_identity(name: str, raw: bytes) -> dict[str, Any]:
    return {
        "path": name,
        "size": len(raw),
        "sha256": _sha256(raw),
    }


def _require_fields(row: Mapping[str, Any], fields: Iterable[str], label: str) -> None:
    missing = sorted(field for field in fields if field not in row)
    if missing:
        _fail(f"{label}の必須fieldがありません: {missing}")


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}が整数ではありません: {value!r}")
    try:
        result = int(value)
    except (TypeError, ValueError):
        _fail(f"{label}が整数ではありません: {value!r}")
    if str(result) != str(value) and not isinstance(value, int):
        _fail(f"{label}が正規10進整数ではありません: {value!r}")
    return result


def _load_p03_runtime(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """現行tracked worktreeのP03 handoffだけを読む。古いfallbackは禁止する。"""

    workspace = root.resolve()
    path = workspace
    for component in Path(P03_RUNTIME_PATH).parts:
        path = path / component
        if path.is_symlink():
            _fail(f"現行P03 runtime契約pathのsymlinkは禁止です: {P03_RUNTIME_PATH}")
    raw = _regular_file(path, "現行P03 runtime契約")
    completed = subprocess.run(
        ["git", "-C", str(workspace), "ls-files", "--error-unmatch", "--", P03_RUNTIME_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0 \
            or completed.stdout.strip().splitlines() != [P03_RUNTIME_PATH]:
        _fail(
            "現行P03 runtime契約がGit tracked worktree fileではありません: "
            f"{P03_RUNTIME_PATH}"
        )
    value = _json_bytes(raw, "P03 runtime契約")
    if not isinstance(value, dict):
        _fail("P03 runtime契約のrootがobjectではありません")
    return value, {
        "path": P03_RUNTIME_PATH,
        "content_sha256": _sha256(raw),
        "resolution": "CURRENT_TRACKED_WORKTREE_REQUIRED_NO_HISTORICAL_FALLBACK",
    }


def _validate_p03_side_change(
    p03: Mapping[str, Any], definition: Mapping[str, Any]
) -> Mapping[str, Any]:
    side = p03.get("side_change_1063")
    if not isinstance(side, dict):
        _fail("P03 runtime契約にside_change_1063がありません")
    expected = {
        "official_move_id": definition.get("official_move_id"),
        "project_move_id": definition.get("project_move_id"),
        "project_move_key": definition.get("project_move_key"),
    }
    for field, value in expected.items():
        if side.get(field) != value:
            _fail(f"P03/受領ZIPのSide Change {field}が不一致です")
    if side.get("definition") != {
        field: definition.get(field)
        for field in ("accuracy", "damage_class_id", "power", "pp", "priority", "type_id")
    }:
        _fail("P03/受領ZIPのSide Change battle定義が不一致です")
    routes = side.get("routes_by_consumer")
    if not isinstance(routes, dict) or sum(_integer(v, "P03 route count") for v in routes.values()) != side.get("adopted_route_count"):
        _fail("P03 Side Change経路集計が不一致です")
    if side.get("status") != "BLOCKING_RUNTIME_DEPENDENCY_NOT_IMPLEMENTED":
        _fail("P03 Side Changeを実装済みと誤認する状態です")
    return side


def _load_move_model(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = root / "generated/engine/moves/move_port.json"
    model, identity = _json_file(path, "現行Move runtime model")
    moves = model.get("moves")
    summary = model.get("summary")
    if not isinstance(moves, list) or not isinstance(summary, dict):
        _fail("現行Move runtime modelのschemaが不正です")
    count = _integer(summary.get("move_count"), "Move count")
    if count != len(moves) or summary.get("last_id") != count - 1:
        _fail("現行Move runtime modelのcount/last IDが不一致です")
    for expected_id, row in enumerate(moves):
        if not isinstance(row, dict) or row.get("id") != expected_id:
            _fail(f"現行Move runtime modelのID順が不正です: {expected_id}")
    identity["path"] = "generated/engine/moves/move_port.json"
    return model, identity


def _load_battle_core(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config, identity = _json_file(root / "config/battle_core.json", "battle core config")
    tables = config.get("runtime_tables")
    if not isinstance(tables, dict):
        _fail("battle core configにruntime_tablesがありません")
    expected = {
        "move_data": ("gBattleMoves", 12),
        "move_names": ("gMoveNames", 16),
        "move_descriptions": ("gMoveDescriptions", 4),
        "move_animations": ("gMoveAnimations", 4),
        "ability_names": ("gAbilityNames", 17),
        "ability_descriptions": ("gAbilityDescriptions", 4),
    }
    for key, (symbol, stride) in expected.items():
        row = tables.get(key)
        if not isinstance(row, dict) or row.get("symbol") != symbol or row.get("stride") != stride:
            _fail(f"battle core runtime table契約が変化しました: {key}")
    identity["path"] = "config/battle_core.json"
    return config, identity


def _parse_move_audit(
    raw: bytes,
    moves_manifest: Any,
    move_model: Mapping[str, Any],
) -> list[dict[str, Any]]:
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    except UnicodeDecodeError as error:
        _fail(f"既存技監査CSVがUTF-8ではありません: {error}")
    expected_header = [
        "技プロジェクトID", "技名", "原作参照ID_直接代入不可", "CSV比較差分", "判断", "参照",
    ]
    if reader.fieldnames != expected_header:
        _fail(f"既存技監査CSV headerが変化しました: {reader.fieldnames}")
    rows = list(reader)
    if {int(row["技プロジェクトID"]) for row in rows} != set(EXPECTED_PRESERVE_DIFFS):
        _fail("既存技監査の4差分集合が変化しました")

    runtime_moves = move_model["moves"]
    output: list[dict[str, Any]] = []
    for source in rows:
        move_id = _integer(source["技プロジェクトID"], "既存技監査:project ID")
        field, current, reference, reason_code = EXPECTED_PRESERVE_DIFFS[move_id]
        manifest = moves_manifest.by_id.get(move_id)
        if manifest is None or manifest["display_name"] != source["技名"]:
            _fail(f"既存技監査がMove manifest identityと不一致です: {move_id}")
        runtime = runtime_moves[move_id]
        if runtime.get("move_key") != manifest["move_key"] or runtime.get("display_name") != source["技名"]:
            _fail(f"既存技監査がMove runtime identityと不一致です: {move_id}")
        try:
            delta = json.loads(source["CSV比較差分"])
        except json.JSONDecodeError as error:
            _fail(f"既存技監査の差分JSONが不正です: {move_id}: {error}")
        if delta != {field: [current, reference]}:
            _fail(f"既存技監査の差分値が想定外です: {move_id}: {delta}")
        battle = runtime.get("battle")
        if not isinstance(battle, dict) or battle.get(field) != current:
            _fail(f"既存技監査の現行値がruntimeと不一致です: {move_id}:{field}")
        before = {
            key: battle.get(key)
            for key in (
                "type", "split", "power", "accuracy", "pp", "priority",
                "target", "effect", "secondary", "flags", "z_move_effect", "z_move_power",
            )
        }
        output.append(
            {
                "move_key": manifest["move_key"],
                "canonical_id": move_id,
                "display_name_ja": source["技名"],
                "source_reference_id_not_project_id": _integer(
                    source["原作参照ID_直接代入不可"], "既存技監査:reference ID"
                ),
                "reference_delta": delta,
                "before": before,
                "after": dict(before),
                "description": runtime.get("description"),
                "animation": runtime.get("animation"),
                "effect_binding": runtime.get("effect_map"),
                "decision": "PRESERVE_CURRENT_NO_PATCH",
                "data_only_patch_eligible": False,
                "reason_code": reason_code,
                "source_decision_ja": source["判断"],
                "source_url": source["参照"],
            }
        )
    return sorted(output, key=lambda row: row["canonical_id"])


def _build_new_move_requirement(
    definition: Mapping[str, Any],
    side: Mapping[str, Any],
    manifests: Mapping[str, Any],
    move_model: Mapping[str, Any],
) -> dict[str, Any]:
    _require_fields(
        definition,
        (
            "official_move_id", "official_identifier", "move_name_ja", "move_name_en",
            "existing_vega_move_id", "project_move_id", "project_move_key",
            "mapping_basis", "implementation_status", "type_id", "damage_class_id",
            "power", "pp", "accuracy", "priority", "source_url",
        ),
        "Side Change definition",
    )
    key = str(definition["project_move_key"])
    requested_id = _integer(definition["project_move_id"], "Side Change project ID")
    current_count = len(move_model["moves"])
    if key != "MOVE_KEY_ALLYSWITCH" or requested_id != current_count:
        _fail("提出済みSide Changeがcurrent manifestへの連続appendではありません")
    if key in manifests["moves"].by_key or requested_id in manifests["moves"].by_id:
        _fail("Side Change 1063は未実装契約なのにmanifestへ既に存在します")
    if definition["existing_vega_move_id"] is not None:
        _fail("Side Changeが既存Vega Move IDへ誤対応されています")
    type_id = _integer(definition["type_id"], "Side Change type ID")
    type_row = manifests["types"].by_id.get(type_id)
    if type_row is None:
        _fail("Side Change type IDがType manifestにありません")

    return {
        "selection_status": "ADOPTED_BY_P03_DISTRIBUTION_CONTRACT",
        "runtime_status": "BLOCKED_SPECIFICATION_AND_CAPACITY_INCOMPLETE",
        "move_key": key,
        "canonical_id": None,
        "requested_project_id": requested_id,
        "id_status": "PROPOSED_NEXT_ID_NOT_IN_CANONICAL_MANIFEST",
        "official": {
            "move_id": definition["official_move_id"],
            "identifier": definition["official_identifier"],
            "source_url": definition["source_url"],
        },
        "identity": {
            "name_ja": definition["move_name_ja"],
            "name_en": definition["move_name_en"],
            "mapping_basis": definition["mapping_basis"],
            "current_manifest_count": current_count,
            "required_manifest_count": current_count + 1,
            "current_last_id": current_count - 1,
        },
        "before": None,
        "submitted_after": {
            "type_id": type_id,
            "type_key": type_row["type_key"],
            "damage_class_id": definition["damage_class_id"],
            "runtime_split": None,
            "power": definition["power"],
            "accuracy": definition["accuracy"],
            "pp": definition["pp"],
            "priority": definition["priority"],
            "target": None,
            "effect": None,
            "secondary_chance": None,
            "flags": None,
            "description_ja": None,
            "animation": None,
        },
        "missing_specification_fields": [
            "runtime_split", "target", "effect", "secondary_chance", "flags",
            "description_ja", "animation",
        ],
        "effect_policy": {
            "effect_mapping": None,
            "reuse_existing_effect": False,
            "guard": "DO_NOT_MAP_TO_EFFECT_HIT_OR_ANOTHER_APPROXIMATION",
        },
        "p03_routes": {
            "target_count": side["adopted_target_count"],
            "route_count": side["adopted_route_count"],
            "by_consumer": side["routes_by_consumer"],
            "serialization_gate": "DO_NOT_SERIALIZE_UNTIL_RUNTIME_IMPLEMENTED",
        },
        "implementation_surfaces": {
            "identity_and_fixed_counts": "REQUIRED",
            "move_data": "BLOCKED_MISSING_RUNTIME_FIELDS",
            "effect_and_battle_script": "REQUIRED_NO_COMPATIBLE_MAPPING_SELECTED",
            "description_ja": "REQUIRED_NOT_SUBMITTED",
            "ai_single_and_double": "REQUIRED",
            "ui_all_move_consumers": "REQUIRED",
            "animation": "REQUIRED_NOT_SUBMITTED",
            "save_roundtrip": "ABI_COMPATIBLE_IN_PRINCIPLE_RUNTIME_TEST_REQUIRED",
        },
        "required_runtime_work": side["required_runtime_work"],
    }


def _normalize_repository_url(value: str) -> str:
    return value.strip().rstrip("/").removesuffix(".git")


def _verify_technical_checkout(
    source_root: Path,
    *,
    expected_commit: str = TECHNICAL_SOURCE_COMMIT,
    expected_repository: str = TECHNICAL_SOURCE_REPOSITORY,
) -> dict[str, Any]:
    if source_root.is_symlink() or not source_root.is_dir():
        _fail(f"P04固定technical source checkoutがありません: {source_root}")

    def git_output(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=source_root, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as error:
            _fail(f"P04 technical source git identityを確認できません: {error}")

    commit = git_output("rev-parse", "HEAD")
    if commit != expected_commit:
        _fail(f"P04 technical source commitが固定値と不一致です: {commit}")
    repository = git_output("remote", "get-url", "origin")
    if _normalize_repository_url(repository) != _normalize_repository_url(
        expected_repository
    ):
        _fail(f"P04 technical source repositoryが固定値と不一致です: {repository}")
    dirty = git_output("status", "--porcelain", "--untracked-files=all")
    if dirty:
        _fail("P04 technical source checkoutがdirtyです")
    return {
        "repository": _normalize_repository_url(repository),
        "commit": commit,
        "checkout_clean_observed": True,
        "checkout_clean_required": True,
    }


def _parse_technical_ability_source(
    root: Path, selected_keys: Sequence[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    source_root = root / TECHNICAL_SOURCE_ROOT
    checkout = _verify_technical_checkout(source_root)

    id_path = source_root / TECHNICAL_ID_PATH
    text_path = source_root / TECHNICAL_TEXT_PATH
    id_raw = _regular_file(id_path, "upstream ability constants")
    text_raw = _regular_file(text_path, "upstream ability text")
    id_text = id_raw.decode("utf-8")
    ability_text = text_raw.decode("utf-8")

    all_source_files = sorted(
        path for base in (source_root / "include", source_root / "src")
        for path in base.rglob("*")
        if path.is_file() and not path.is_symlink() and path.suffix in {".c", ".h"}
    )
    refs: dict[str, dict[str, Any]] = {}
    evidence_files: dict[str, dict[str, Any]] = {}
    for key in selected_keys:
        symbol = UPSTREAM_ABILITY_SYMBOLS[key]
        id_match = re.search(rf"\b{re.escape(symbol)}\s*=\s*([0-9]+)\s*,", id_text)
        block_match = re.search(
            rf"\[{re.escape(symbol)}\]\s*=\s*\{{(.*?)\n\s*\}},",
            ability_text,
            flags=re.DOTALL,
        )
        if id_match is None or block_match is None:
            _fail(f"upstream technical sourceにAbility定義がありません: {symbol}")
        block = block_match.group(1)
        name_match = re.search(r'\.name\s*=\s*_\("([^"]+)"\)', block)
        description_match = re.search(
            r'\.description\s*=\s*COMPOUND_STRING\("([^"]+)"\)', block
        )
        if name_match is None or description_match is None:
            _fail(f"upstream Ability name/descriptionを抽出できません: {symbol}")
        occurrences: list[dict[str, Any]] = []
        token = symbol.encode("ascii")
        for path in all_source_files:
            raw = path.read_bytes()
            count = raw.count(token)
            if not count:
                continue
            relative = path.relative_to(source_root).as_posix()
            if relative.startswith("src/data/pokemon/"):
                surface = "SPECIES_ASSIGNMENT_REFERENCE"
            elif "battle_ai" in relative or relative == "src/battle_dome.c":
                surface = "AI_REFERENCE"
            elif relative in {TECHNICAL_ID_PATH, TECHNICAL_TEXT_PATH}:
                surface = "IDENTITY_OR_TEXT_REFERENCE"
            else:
                surface = "EFFECT_REFERENCE"
            occurrences.append(
                {"path": relative, "surface": surface, "occurrences": count}
            )
            evidence_files.setdefault(
                relative,
                {"path": relative, "size": len(raw), "sha256": _sha256(raw)},
            )
        if not any(row["surface"] == "EFFECT_REFERENCE" for row in occurrences):
            _fail(f"upstream Ability effect参照がありません: {symbol}")
        refs[key] = {
            "source_symbol": symbol,
            "source_numeric_id_not_canonical": int(id_match.group(1)),
            "name_en_technical": name_match.group(1),
            "description_en_technical": description_match.group(1),
            "name_ja": None,
            "description_ja": None,
            "occurrences": occurrences,
            "status": "PINNED_TECHNICAL_REFERENCE_PORT_REQUIRED",
        }
    if _verify_technical_checkout(source_root) != checkout:
        _fail("P04 technical source identityが走査中に変化しました")
    return refs, {
        **checkout,
        "local_checkout": TECHNICAL_SOURCE_ROOT,
        "authority": "TECHNICAL_REFERENCE_NOT_OFFICIAL_SPECIFICATION",
        "files": sorted(evidence_files.values(), key=lambda row: row["path"]),
    }


def _build_p04_ability_contract(
    records: Sequence[Mapping[str, Any]],
    abilities_manifest: Any,
    technical_refs: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    required = (
        "record_key", "identity_species_key", "identity_form_key", "proposed_species_key",
        "classification", "implementation_scope", "ability_key", "ability_status",
        "ability_replacement_key", "ability_provenance_key", "official_confirmation_date",
        "official_url",
    )
    seen_records: set[str] = set()
    seen_replacement: set[str] = set()
    assignments: list[dict[str, Any]] = []
    held: list[dict[str, Any]] = []
    new_subjects: dict[str, list[str]] = defaultdict(list)

    for position, source in enumerate(records):
        if not isinstance(source, Mapping):
            _fail(f"P04 candidate recordがobjectではありません: row={position}")
        _require_fields(source, required, f"P04 candidate row {position}")
        record_key = str(source["record_key"])
        if record_key in seen_records:
            _fail(f"P04 record_keyが重複しています: {record_key}")
        seen_records.add(record_key)
        scope = source["implementation_scope"]
        status = source["ability_status"]
        ability_key = str(source["ability_key"])
        replacement = source["ability_replacement_key"]

        if scope == "HOLD_CLASSIFICATION":
            manifest = abilities_manifest.by_key.get(ability_key)
            if status != "TEMPORARY_REPLACEABLE" or manifest is None:
                _fail(f"P04 HOLD行の仮Abilityが現行manifestへ解決しません: {record_key}")
            if not isinstance(replacement, str) or not replacement.startswith("REPLACEMENT_KEY_ABILITY_"):
                _fail(f"P04 HOLD行の将来差替keyが不正です: {record_key}")
            if replacement in seen_replacement or replacement in abilities_manifest.by_key:
                _fail(f"P04 HOLD行の将来差替keyが重複/誤解決しています: {replacement}")
            seen_replacement.add(replacement)
            held.append(
                {
                    "record_key": record_key,
                    "classification": source["classification"],
                    "ability_key": ability_key,
                    "canonical_id": int(manifest["id"]),
                    "temporary_replaceable": True,
                    "replacement_trigger_key": replacement,
                    "reason": "P04_CLASSIFICATION_HOLD_NOT_P05_ADOPTED_CONTENT",
                }
            )
            continue
        if scope != "ADOPT_CANDIDATE":
            _fail(f"P04 implementation_scopeが未対応です: {record_key}:{scope}")
        manifest = abilities_manifest.by_key.get(ability_key)
        if status == "TEMPORARY_REPLACEABLE":
            if manifest is None:
                _fail(f"仮Abilityが現行manifestにありません: {record_key}:{ability_key}")
            if not isinstance(replacement, str) or not replacement.startswith("REPLACEMENT_KEY_ABILITY_"):
                _fail(f"仮Abilityの将来差替keyが不正です: {record_key}")
            if replacement in seen_replacement:
                _fail(f"仮Abilityの将来差替keyが重複しています: {replacement}")
            if replacement in abilities_manifest.by_key:
                _fail(f"将来差替keyを現行Abilityと誤認しています: {replacement}")
            seen_replacement.add(replacement)
            resolution = "EXISTING_TEMPORARY_REPLACEABLE"
            canonical_id: int | None = int(manifest["id"])
            official = False
        elif status == "OFFICIAL_CONFIRMED":
            if replacement is not None:
                _fail(f"公式確定Abilityにreplacement keyがあります: {record_key}")
            official = True
            if manifest is None:
                if ability_key not in P04_ALLOWED_NEW_ABILITY_KEYS:
                    _fail(f"P04未提出の新Abilityを補完できません: {record_key}:{ability_key}")
                resolution = "NEW_CANONICAL_ID_UNASSIGNED"
                canonical_id = None
                new_subjects[ability_key].append(record_key)
            else:
                resolution = "EXISTING_CANONICAL"
                canonical_id = int(manifest["id"])
        else:
            _fail(f"P04 ability_statusが未対応です: {record_key}:{status}")

        assignments.append(
            {
                "record_key": record_key,
                "identity_species_key": source["identity_species_key"],
                "identity_form_key": source["identity_form_key"],
                "proposed_species_key": source["proposed_species_key"],
                "ability_key": ability_key,
                "canonical_id": canonical_id,
                "resolution": resolution,
                "official_confirmed": official,
                "temporary_replaceable": status == "TEMPORARY_REPLACEABLE",
                "replacement_trigger_key": replacement,
                "ability_provenance_key": source["ability_provenance_key"],
                "official_confirmation_date": source["official_confirmation_date"],
                "official_url": source["official_url"],
                "presentation_guard": (
                    "MUST_LABEL_TEMPORARY_NOT_OFFICIAL"
                    if status == "TEMPORARY_REPLACEABLE" else "OFFICIAL_CONFIRMED_BY_P04"
                ),
            }
        )

    selected_new = set(new_subjects)
    if selected_new != P04_ALLOWED_NEW_ABILITY_KEYS:
        _fail(
            "P04の未割当公式Ability集合が固定候補と不一致です: "
            f"{sorted(selected_new)}"
        )
    requirements: list[dict[str, Any]] = []
    for key in sorted(selected_new):
        ref = technical_refs.get(key)
        if ref is None:
            _fail(f"新Abilityのtechnical referenceがありません: {key}")
        requirements.append(
            {
                "ability_key": key,
                "canonical_id": None,
                "id_status": "UNASSIGNED_APPEND_ALLOCATION_REQUIRED",
                "do_not_copy_source_numeric_id": ref["source_numeric_id_not_canonical"],
                "subjects": sorted(new_subjects[key]),
                "official_status": "OFFICIAL_CONFIRMED_BY_P04",
                "technical_reference": ref,
                "implementation_surfaces": {
                    "manifest_and_fixed_counts": "REQUIRED_ID_DECISION_PENDING",
                    "effect": "REFERENCE_AVAILABLE_PORT_AND_SEMANTIC_REVIEW_REQUIRED",
                    "name_ja": "REQUIRED_NOT_SUBMITTED",
                    "description_ja": "REQUIRED_NOT_SUBMITTED",
                    "ai": "REFERENCE_MAY_BE_PARTIAL_PORT_AND_TEST_REQUIRED",
                    "ui": "REQUIRED_TABLE_APPEND_AND_WIDTH_CHECK",
                    "animation": "NOT_APPLICABLE_ABILITY",
                    "save": "SLOT_DERIVED_NO_RAW_ABILITY_ID_MIGRATION_EXPECTED_TEST_REQUIRED",
                },
            }
        )
    return {
        "assignments": sorted(assignments, key=lambda row: row["record_key"]),
        "new_ability_requirements": requirements,
        "held_records": sorted(held, key=lambda row: row["record_key"]),
        "temporary_policy": {
            "replacement_is_keyed": True,
            "identity_key_must_not_change_on_replacement": True,
            "temporary_values_must_not_be_presented_as_official": True,
        },
        "summary": {
            "adopt_candidate_assignments": len(assignments),
            "official_existing_assignments": sum(
                row["resolution"] == "EXISTING_CANONICAL" for row in assignments
            ),
            "temporary_existing_assignments": sum(
                row["temporary_replaceable"] for row in assignments
            ),
            "temporary_declared_records_including_hold": (
                sum(row["temporary_replaceable"] for row in assignments)
                + sum(row["temporary_replaceable"] for row in held)
            ),
            "new_ability_count": len(requirements),
            "classification_hold_count": len(held),
        },
    }


def _build_p02_existing_move_dependencies(
    root: Path, manifests: Mapping[str, Any], move_model: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    document, identity = _json_file(
        root / "content/modernization/p02_evolution_contract.json", "P02 evolution契約"
    )
    section = document.get("p03_dependencies")
    if not isinstance(section, dict) or not isinstance(section.get("dependencies"), list):
        _fail("P02 evolution契約にp03_dependenciesがありません")
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in section["dependencies"]:
        if not isinstance(row, Mapping):
            _fail("P02 p03 dependency rowがobjectではありません")
        grouped[str(row.get("required_move_key"))].append(row)
    if set(grouped) != {"MOVE_KEY_HYPERDRILL", "MOVE_KEY_TWINBEAM"}:
        _fail(f"P02 trigger Move集合が想定外です: {sorted(grouped)}")
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        manifest = manifests["moves"].by_key.get(key)
        if manifest is None:
            _fail(f"P02 trigger Moveがmanifestにありません: {key}")
        move_id = int(manifest["id"])
        runtime = move_model["moves"][move_id]
        if runtime.get("move_key") != key:
            _fail(f"P02 trigger Moveがruntimeと不一致です: {key}")
        for dependency in grouped[key]:
            if dependency.get("required_move_id") != move_id:
                _fail(f"P02 trigger Move IDがkey解決結果と不一致です: {key}")
        output.append(
            {
                "move_key": key,
                "canonical_id": move_id,
                "display_name_ja": manifest["display_name"],
                "definition_status": "EXISTING_RUNTIME_NOT_A_NEW_P05_MOVE",
                "distribution_dependency_count": len(grouped[key]),
                "distribution_status": "P03_ROUTE_COMPILATION_REQUIRED",
            }
        )
    identity["path"] = "content/modernization/p02_evolution_contract.json"
    return output, identity


def _save_abi_contract(root: Path) -> dict[str, Any]:
    pokemon_h = root / "vendor/upstream/CFRU-JP/include/pokemon.h"
    build_pokemon_c = root / "vendor/upstream/CFRU-JP/src/build_pokemon.c"
    raw_h = _regular_file(pokemon_h, "Pokemon save ABI header")
    raw_c = _regular_file(build_pokemon_c, "GetMonAbility source")
    text_h = raw_h.decode("utf-8")
    text_c = raw_c.decode("utf-8")
    for snippet in ("u16 moves[4];", "u8 pp[4];", "u8 ppBonuses;", "u32 abilityNum:1;"):
        if snippet not in text_h:
            _fail(f"Pokemon save ABI snippetが見つかりません: {snippet}")
    if "u16 GetMonAbility(const struct Pokemon* mon)" not in text_c:
        _fail("GetMonAbilityのu16 table-derived ABIを確認できません")
    return {
        "evidence": [
            {
                "path": pokemon_h.relative_to(root).as_posix(),
                "size": len(raw_h),
                "sha256": _sha256(raw_h),
                "assertions": [
                    "stored_move_slots_are_u16",
                    "stored_current_pp_is_u8_per_slot",
                    "stored_pp_up_is_two_bits_per_slot_in_ppBonuses",
                    "stored_ability_is_selection_bits_not_canonical_ability_id",
                ],
            },
            {
                "path": build_pokemon_c.relative_to(root).as_posix(),
                "size": len(raw_c),
                "sha256": _sha256(raw_c),
                "assertions": ["GetMonAbility_returns_u16_derived_from_species_tables"],
            },
        ],
        "moves": {
            "numeric_capacity": "U16_SUFFICIENT_FOR_1063",
            "legacy_save_migration": "NOT_REQUIRED_FOR_NEW_MOVE_LEGACY_SAVES_CANNOT_CONTAIN_1063",
            "pp_change_migration": "NOT_REQUIRED_NO_ADOPTED_PP_CHANGE",
            "required_verification": [
                "save_load_roundtrip_move_1063",
                "pp_and_pp_up_calculation",
                "healing_and_move_relearner_display",
                "battle_entry_exit_and_facility_resume_where_supported",
            ],
        },
        "abilities": {
            "storage_model": "ABILITY_SLOT_BITS_PLUS_SPECIES_TABLE_DERIVATION",
            "legacy_save_migration": "NO_RAW_ABILITY_ID_REWRITE_EXPECTED",
            "required_verification": [
                "legacy_mon_ability_slot_roundtrip",
                "mega_form_runtime_ability_selection",
                "hidden_and_secondary_ability_selection",
                "u16_battle_ability_path_for_ids_above_255",
            ],
        },
    }


def build_p05_contract(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifests = load_manifests(root)
    move_model, move_model_identity = _load_move_model(root)
    battle_core, battle_core_identity = _load_battle_core(root)

    with CheckedArchive(root / LEARNSETS_ZIP, "learnsets") as archive:
        new_move_name, new_move_raw = archive.read(NEW_MOVE_MEMBER)
        learnsets_archive_identity = archive.identity()
    if _sha256(new_move_raw) != EXPECTED_MEMBER_SHA256[NEW_MOVE_MEMBER]:
        _fail("Side Change定義member hashが固定値と不一致です")
    new_move_doc = _json_bytes(new_move_raw, "Side Change定義")
    if (
        not isinstance(new_move_doc, dict)
        or new_move_doc.get("status") != "SPECIFICATION_ONLY"
        or new_move_doc.get("existing_rom_modified") is not False
        or not isinstance(new_move_doc.get("moves"), list)
        or len(new_move_doc["moves"]) != 1
    ):
        _fail("Side Change定義は未実装1件でなければなりません")

    with CheckedArchive(root / RESTORATION_ZIP, "restoration_audit") as archive:
        move_audit_name, move_audit_raw = archive.read(MOVE_AUDIT_MEMBER)
        review_name, review_raw = archive.read(RESTORATION_REVIEW_MEMBER)
        restoration_archive_identity = archive.identity()
    for suffix, raw in (
        (MOVE_AUDIT_MEMBER, move_audit_raw),
        (RESTORATION_REVIEW_MEMBER, review_raw),
    ):
        if _sha256(raw) != EXPECTED_MEMBER_SHA256[suffix]:
            _fail(f"復元監査member hashが固定値と不一致です: {suffix}")
    review_doc = _json_bytes(review_raw, "復元review-only候補")
    if (
        not isinstance(review_doc, dict)
        or review_doc.get("status") != "REVIEW_ONLY_NOT_APPLIED"
        or not isinstance(review_doc.get("candidates"), list)
    ):
        _fail("復元候補をreview-onlyとして確認できません")

    p03, p03_identity = _load_p03_runtime(root)
    side = _validate_p03_side_change(p03, new_move_doc["moves"][0])

    p04_documents: dict[str, dict[str, Any]] = {}
    p04_identities: dict[str, dict[str, Any]] = {}
    for relative, expected_hash in EXPECTED_P04_FILES.items():
        document, identity = _json_file(root / relative, f"P04 output {relative}")
        identity["path"] = relative
        if identity["sha256"] != expected_hash:
            _fail(
                f"P04 output hashが固定成果と不一致です: {relative}: "
                f"{identity['sha256']} != {expected_hash}"
            )
        p04_documents[relative] = document
        p04_identities[relative] = identity
    p04 = p04_documents["content/modernization/p04_candidate_manifest.json"]
    p04_identity = p04_identities["content/modernization/p04_candidate_manifest.json"]
    p04_records = p04.get("records")
    if p04.get("task") != "USER-MODERNIZATION-P04" or not isinstance(p04_records, list):
        _fail("P04 candidate manifestのschemaが不正です")
    submitted_move_fields = sum(
        field in record
        for record in p04_records if isinstance(record, Mapping)
        for field in ("move_key", "new_move_key", "proposed_move_key")
    )
    if submitted_move_fields:
        _fail("P04 candidate manifestに未契約のMove fieldがあります")
    official_doc = p04_documents["content/modernization/p04_official_sources.json"]
    official_sources = official_doc.get("sources")
    if not isinstance(official_sources, list):
        _fail("P04 official source一覧がありません")
    official_source_keys = {
        row.get("source_key") for row in official_sources
        if isinstance(row, Mapping)
    }
    candidate_provenance_keys = {
        row.get("ability_provenance_key") for row in p04_records
        if isinstance(row, Mapping) and row.get("implementation_scope") == "ADOPT_CANDIDATE"
    }
    if not candidate_provenance_keys <= official_source_keys:
        _fail(
            "P04 ability provenanceがofficial sourceへ解決しません: "
            f"{sorted(candidate_provenance_keys - official_source_keys)}"
        )
    asset_doc = p04_documents["content/modernization/p04_asset_sources.json"]
    asset_sources = asset_doc.get("sources")
    if not isinstance(asset_sources, list):
        _fail("P04 asset source一覧がありません")
    selected_asset = next(
        (
            row for row in asset_sources
            if isinstance(row, Mapping)
            and row.get("source_key") == asset_doc.get("selected_source_key")
        ),
        None,
    )
    if selected_asset is None or selected_asset.get("commit") != TECHNICAL_SOURCE_COMMIT:
        _fail("P04 selected technical source commitが工程5固定値と不一致です")
    technical_refs, technical_source = _parse_technical_ability_source(
        root, sorted(P04_ALLOWED_NEW_ABILITY_KEYS)
    )

    preserved = _parse_move_audit(
        move_audit_raw, manifests["moves"], move_model
    )
    new_move = _build_new_move_requirement(
        new_move_doc["moves"][0], side, manifests, move_model
    )
    p04_abilities = _build_p04_ability_contract(
        p04_records, manifests["abilities"], technical_refs
    )
    p02_moves, p02_identity = _build_p02_existing_move_dependencies(
        root, manifests, move_model
    )

    runtime_tables = battle_core["runtime_tables"]
    if runtime_tables["move_data"]["count"] != len(move_model["moves"]):
        _fail("Move runtime table countがmove modelと不一致です")
    if runtime_tables["ability_names"]["count"] != len(manifests["abilities"].rows):
        _fail("Ability runtime table countがmanifestと不一致です")

    contract = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "status": "CONTRACT_READY_RUNTIME_IMPLEMENTATION_REMAINS",
        "policy": {
            "selection": "ONLY_EXPLICIT_P03_P04_AND_RECEIVED_ARCHIVE_SUBMISSIONS",
            "historical_v3": "PROVENANCE_ALREADY_IN_BASELINE_NOT_A_P05_DELTA",
            "restoration_candidates": "REVIEW_ONLY_NOT_APPLIED",
            "unknown_effect": "BLOCK_DO_NOT_MAP_TO_APPROXIMATE_EXISTING_EFFECT",
            "numeric_identity": "KEY_FIRST_MANIFEST_ID_ONLY_NO_SOURCE_ID_COPY",
            "za_unconfirmed_ability": "EXISTING_TEMPORARY_VALUE_WITH_UNIQUE_REPLACEMENT_TRIGGER",
            "unsubmitted_move_or_ability": "DO_NOT_CREATE",
        },
        "inputs": {
            "learnsets_archive": {
                **learnsets_archive_identity,
                "path": LEARNSETS_ZIP,
                "selected_member": _member_identity(new_move_name, new_move_raw),
            },
            "restoration_archive": {
                **restoration_archive_identity,
                "path": RESTORATION_ZIP,
                "selected_members": [
                    _member_identity(move_audit_name, move_audit_raw),
                    _member_identity(review_name, review_raw),
                ],
            },
            "p03_runtime": p03_identity,
            "p04": {
                "candidate_manifest": p04_identity,
                "official_sources": p04_identities[
                    "content/modernization/p04_official_sources.json"
                ],
                "asset_sources": p04_identities[
                    "content/modernization/p04_asset_sources.json"
                ],
            },
            "p02_evolution": p02_identity,
            "move_runtime_model": move_model_identity,
            "battle_core": battle_core_identity,
            "manifests": {
                name: {
                    "path": index.spec.relative_path,
                    "count": len(index.rows),
                    "last_id": len(index.rows) - 1,
                    "sha256": index.sha256,
                }
                for name, index in sorted(manifests.items())
            },
            "ability_technical_source": technical_source,
        },
        "baseline": {
            "move_count": len(move_model["moves"]),
            "last_move_id": len(move_model["moves"]) - 1,
            "ability_count": len(manifests["abilities"].rows),
            "last_ability_id": len(manifests["abilities"].rows) - 1,
            "v3": {
                "modern_effect_rows": move_model["summary"]["v3_modern_count"],
                "vega_exclusive_rows": move_model["summary"]["v3_exclusive_count"],
                "numeric_override_rows": move_model["summary"]["v3_numeric_override_count"],
                "selected_as_new_p05_delta": 0,
            },
            "runtime_tables": {
                key: runtime_tables[key]
                for key in (
                    "move_data", "move_names", "move_descriptions", "move_animations",
                    "ability_names", "ability_descriptions",
                )
            },
        },
        "move_content": {
            "adopted_performance_adjustments": [],
            "preserved_reference_differences": preserved,
            "new_move_requirements": [new_move],
            "p04_new_move_requests": [],
            "p04_move_inference_guard": {
                "submitted_move_fields": submitted_move_fields,
                "mega_sol_is_ability_name_not_a_move_submission": True,
                "invented_move_keys": [],
            },
            "existing_evolution_trigger_moves": p02_moves,
        },
        "ability_content": p04_abilities,
        "save_compatibility": _save_abi_contract(root),
        "data_only_patch_plan": {
            "confirmed_patches": [],
            "confirmed_patch_count": 0,
            "preserve_without_patch_move_ids": [row["canonical_id"] for row in preserved],
            "reason": "受領監査の4差分はいずれも表現/世代/専用計算差で自動変更不要。採用済み性能変更は別提出されていない。",
        },
        "release_gates": [
            {
                "gate": "SIDE_CHANGE_1063_FULL_RUNTIME",
                "status": "BLOCKED",
                "requires": [
                    "manifest_id_1063_and_all_counts", "complete_move_record", "effect_script",
                    "description_ja", "ai", "ui", "animation", "save_and_route_rom_tests",
                ],
            },
            {
                "gate": "P04_NEW_ABILITIES",
                "status": "BLOCKED",
                "requires": [
                    "canonical_id_allocation", "effect_semantic_port", "name_description_ja",
                    "ai", "ui_tables", "species_form_binding", "save_runtime_tests",
                ],
            },
            {
                "gate": "P04_TEMPORARY_ABILITIES",
                "status": "CONTRACT_READY",
                "requires": [
                    "temporary_label_in_reports", "replacement_trigger_preservation",
                    "identity_stable_replacement_test",
                ],
            },
        ],
        "summary": {
            "adopted_performance_adjustment_count": 0,
            "preserved_reference_difference_count": len(preserved),
            "new_move_requirement_count": 1,
            "new_ability_requirement_count": len(p04_abilities["new_ability_requirements"]),
            "temporary_ability_assignment_count": p04_abilities["summary"]["temporary_existing_assignments"],
            "temporary_ability_record_count_including_hold": p04_abilities["summary"]["temporary_declared_records_including_hold"],
            "existing_official_ability_assignment_count": p04_abilities["summary"]["official_existing_assignments"],
            "held_candidate_count": p04_abilities["summary"]["classification_hold_count"],
            "confirmed_data_only_patch_count": 0,
            "runtime_blocker_count": 2,
        },
    }
    validate_p05_contract(contract)
    return contract


def validate_p05_contract(contract: Mapping[str, Any]) -> None:
    """生成後にも実行できる、誤採用・誤ID割当中心のfail-closed validator。"""

    if contract.get("schema_version") != SCHEMA_VERSION or contract.get("task") != TASK:
        _fail("P05 contract identityが不正です")
    moves = contract.get("move_content")
    abilities = contract.get("ability_content")
    summary = contract.get("summary")
    if not isinstance(moves, Mapping) or not isinstance(abilities, Mapping) or not isinstance(summary, Mapping):
        _fail("P05 contractの主要sectionがありません")
    if moves.get("adopted_performance_adjustments") != []:
        _fail("未提出の技性能変更がP05へ混入しています")
    new_moves = moves.get("new_move_requirements")
    if not isinstance(new_moves, list) or len(new_moves) != 1:
        _fail("P05新規Moveは提出済みSide Change 1件だけです")
    side = new_moves[0]
    if (
        side.get("move_key") != "MOVE_KEY_ALLYSWITCH"
        or side.get("requested_project_id") != 1063
        or side.get("canonical_id") is not None
        or side.get("effect_policy", {}).get("effect_mapping") is not None
    ):
        _fail("Side Changeの未割当/未実装guardが破られています")
    if moves.get("p04_new_move_requests") != []:
        _fail("P04から未提出Moveを推測しています")
    requirements = abilities.get("new_ability_requirements")
    if not isinstance(requirements, list):
        _fail("P05 new ability requirementsがlistではありません")
    if any(not isinstance(row, Mapping) for row in requirements):
        _fail("P05 new ability requirement rowがobjectではありません")
    raw_keys = [row.get("ability_key") for row in requirements]
    if any(not isinstance(key, str) for key in raw_keys):
        _fail("P05 new ability requirement keyが文字列ではありません")
    keys = set(raw_keys)
    if keys != P04_ALLOWED_NEW_ABILITY_KEYS:
        _fail(f"P05新Ability集合がP04提出集合と不一致です: {sorted(keys)}")
    if any(row.get("canonical_id") is not None for row in requirements):
        _fail("未割当Abilityへcanonical IDを創作しています")
    assignments = abilities.get("assignments")
    if not isinstance(assignments, list):
        _fail("P05 ability assignmentsがlistではありません")
    for row in assignments:
        if not isinstance(row, Mapping):
            _fail("P05 ability assignment rowがobjectではありません")
        if row.get("temporary_replaceable"):
            if row.get("official_confirmed") or row.get("canonical_id") is None:
                _fail("仮Abilityが公式扱いまたは未解決です")
            trigger = row.get("replacement_trigger_key")
            if not isinstance(trigger, str) or not trigger.startswith("REPLACEMENT_KEY_ABILITY_"):
                _fail("仮Abilityのreplacement triggerがありません")
    patch = contract.get("data_only_patch_plan")
    if not isinstance(patch, Mapping) or patch.get("confirmed_patches") != []:
        _fail("確定していないdata-only patchが混入しています")
    if summary.get("new_move_requirement_count") != 1 or summary.get("new_ability_requirement_count") != 6:
        _fail("P05 summary countが固定内容と不一致です")


__all__ = [
    "ModernizationP05Error",
    "P04_ALLOWED_NEW_ABILITY_KEYS",
    "build_p05_contract",
    "stable_json",
    "validate_p05_contract",
]
