#!/usr/bin/env python3
"""Modernization入力をcanonical keyで照合し、対象区分を安全に正規化する。"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import stat
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, NoReturn, Sequence


SCHEMA_VERSION = 1
EXPECTED_ARCHIVES = {
    "learnsets": {
        "sha256": "80b678320c08203e7b39236e5c123f5c2f2f0c729e7f4e5101bed88c84158adb",
        "size": 82_683_251,
    },
    "restoration_audit": {
        "sha256": "448608de12a431bef8eaaaf2dc3024743bfd77ad7925e5fb6ae01b6086cfac08",
        "size": 67_698,
    },
}


class ModernizationIdentityError(ValueError):
    """manifestまたは入力資料がidentity契約に違反した。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationIdentityError(message)


@dataclass(frozen=True)
class ManifestSpec:
    name: str
    relative_path: str
    key_field: str
    key_prefix: str
    expected_count: int


MANIFEST_SPECS = (
    ManifestSpec("species", "manifests/species_ids.csv", "species_key", "SPECIES_KEY_", 1621),
    ManifestSpec("moves", "manifests/move_ids.csv", "move_key", "MOVE_KEY_", 1063),
    ManifestSpec("abilities", "manifests/ability_ids.csv", "ability_key", "ABILITY_KEY_", 312),
    ManifestSpec("items", "manifests/item_ids.csv", "item_key", "ITEM_KEY_", 999),
    ManifestSpec("types", "manifests/type_ids.csv", "type_key", "TYPE_KEY_", 25),
)


@dataclass(frozen=True)
class ManifestIndex:
    spec: ManifestSpec
    rows: tuple[dict[str, str], ...]
    by_key: Mapping[str, dict[str, str]]
    by_id: Mapping[int, dict[str, str]]
    sha256: str


def stable_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _decimal(value: Any, label: str) -> int:
    raw = str(value)
    if re.fullmatch(r"0|[1-9][0-9]*", raw) is None:
        _fail(f"{label}が非負10進整数ではありません: {raw!r}")
    return int(raw)


def _boolean(value: Any, label: str) -> bool:
    if value is True or value == "True":
        return True
    if value is False or value == "False":
        return False
    _fail(f"{label}が厳密なTrue/Falseではありません: {value!r}")


def _csv_rows(raw: bytes, label: str) -> list[dict[str, str]]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        _fail(f"{label}がUTF-8 CSVではありません: {error}")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None:
        _fail(f"{label}にCSV headerがありません")
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        _fail(f"{label}のCSV headerが重複しています")
    rows = list(reader)
    if any(None in row for row in rows):
        _fail(f"{label}にheader外の列があります")
    return rows


def validate_manifest_rows(
    spec: ManifestSpec,
    rows: Sequence[Mapping[str, Any]],
    *,
    sha256: str = "TEST_FIXTURE",
) -> ManifestIndex:
    """1 manifestを重複・欠落・範囲外を許さず読み込む。"""

    if len(rows) != spec.expected_count:
        _fail(
            f"{spec.name} manifest件数が契約外です: "
            f"{len(rows)} != {spec.expected_count}"
        )
    required = {"id", spec.key_field, "display_name"}
    by_key: dict[str, dict[str, str]] = {}
    by_id: dict[int, dict[str, str]] = {}
    normalized: list[dict[str, str]] = []
    for position, source in enumerate(rows):
        row = {str(key): str(value) for key, value in source.items()}
        missing = sorted(field for field in required if field not in row)
        if missing:
            _fail(f"{spec.name} manifest必須列がありません: {missing}")
        key = row[spec.key_field]
        if not key.startswith(spec.key_prefix) or key == spec.key_prefix:
            _fail(f"{spec.name} keyが名前空間外です: {key!r}")
        canonical_id = _decimal(row["id"], f"{spec.name}:{key}:id")
        if canonical_id != position:
            _fail(
                f"{spec.name} IDが欠落・範囲外・順序不正です: "
                f"row={position} id={canonical_id}"
            )
        if key in by_key:
            _fail(f"{spec.name} keyが重複しています: {key}")
        if canonical_id in by_id:
            _fail(f"{spec.name} IDが重複しています: {canonical_id}")
        by_key[key] = row
        by_id[canonical_id] = row
        normalized.append(row)

    if spec.name == "species":
        form_keys: set[str] = set()
        national_forms: set[tuple[str, str]] = set()
        for row in normalized:
            form_key = row.get("form_key", "")
            if form_key:
                if not form_key.startswith("FORM_KEY_"):
                    _fail(f"Species form keyが名前空間外です: {form_key}")
                if form_key in form_keys:
                    _fail(f"Species form keyが重複しています: {form_key}")
                form_keys.add(form_key)
                pair = (row.get("canonical_national_dex", ""), form_key)
                if pair in national_forms:
                    _fail(f"Species national/form identityが重複しています: {pair}")
                national_forms.add(pair)

    return ManifestIndex(
        spec=spec,
        rows=tuple(normalized),
        by_key=by_key,
        by_id=by_id,
        sha256=sha256,
    )


def load_manifests(root: Path) -> dict[str, ManifestIndex]:
    result: dict[str, ManifestIndex] = {}
    for spec in MANIFEST_SPECS:
        path = root / spec.relative_path
        if path.is_symlink() or not path.is_file():
            _fail(f"canonical manifestが通常ファイルではありません: {spec.relative_path}")
        raw = path.read_bytes()
        rows = _csv_rows(raw, spec.relative_path)
        result[spec.name] = validate_manifest_rows(
            spec, rows, sha256=_sha256_bytes(raw),
        )
    return result


class CheckedArchive:
    """path traversal・重複member・symlinkを拒否するZIP reader。"""

    def __init__(self, path: Path, role: str):
        expected = EXPECTED_ARCHIVES[role]
        if path.is_symlink() or not path.is_file():
            _fail(f"{role} ZIPが通常ファイルではありません: {path}")
        size = path.stat().st_size
        digest = _sha256_file(path)
        if size != expected["size"] or digest != expected["sha256"]:
            _fail(
                f"{role} ZIP identity不一致: size={size} sha256={digest}"
            )
        try:
            self._zip = zipfile.ZipFile(path)
        except (OSError, zipfile.BadZipFile) as error:
            _fail(f"{role} ZIPを開けません: {error}")
        self.path = path
        self.role = role
        self.size = size
        self.sha256 = digest
        self._members: dict[str, zipfile.ZipInfo] = {}
        for info in self._zip.infolist():
            name = info.filename
            logical = PurePosixPath(name)
            mode = info.external_attr >> 16
            if (
                not name
                or name.startswith("/")
                or "\\" in name
                or any(part in {"", ".", ".."} for part in logical.parts)
            ):
                self.close()
                _fail(f"{role} ZIP member pathが不正です: {name!r}")
            if name in self._members:
                self.close()
                _fail(f"{role} ZIP memberが重複しています: {name}")
            if stat.S_ISLNK(mode):
                self.close()
                _fail(f"{role} ZIPにsymlinkがあります: {name}")
            self._members[name] = info

    def close(self) -> None:
        self._zip.close()

    def __enter__(self) -> "CheckedArchive":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def member(self, suffix: str) -> str:
        matches = sorted(
            name for name, info in self._members.items()
            if not info.is_dir() and name.endswith(suffix)
        )
        if len(matches) != 1:
            _fail(
                f"{self.role} ZIPのmemberが一意ではありません: "
                f"suffix={suffix!r} matches={matches[:5]}"
            )
        return matches[0]

    def read(self, suffix: str) -> tuple[str, bytes]:
        name = self.member(suffix)
        try:
            return name, self._zip.read(name)
        except (OSError, RuntimeError, zipfile.BadZipFile) as error:
            _fail(f"{self.role} ZIP memberを読めません: {name}: {error}")

    def lines(self, suffix: str) -> tuple[str, Iterable[bytes]]:
        name = self.member(suffix)
        return name, self._zip.open(name)

    def identity(self) -> dict[str, Any]:
        roots = {PurePosixPath(name).parts[0] for name in self._members}
        if len(roots) != 1:
            _fail(f"{self.role} ZIPのrootが一意ではありません: {sorted(roots)}")
        return {
            "role": self.role,
            "size": self.size,
            "sha256": self.sha256,
            "archive_root": next(iter(roots)),
            "member_count": len(self._members),
        }


def _member_identity(name: str, raw: bytes) -> dict[str, Any]:
    parts = PurePosixPath(name).parts
    return {
        "path_below_archive_root": PurePosixPath(*parts[1:]).as_posix(),
        "size": len(raw),
        "sha256": _sha256_bytes(raw),
    }


def _require_fields(row: Mapping[str, Any], fields: Iterable[str], label: str) -> None:
    missing = sorted(field for field in fields if field not in row)
    if missing:
        _fail(f"{label}の必須fieldがありません: {missing}")


def normalize_target_rows(
    rows: Sequence[Mapping[str, Any]],
    species: ManifestIndex,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Stage61対象区分をkey joinし、許可された2件だけ訂正する。"""

    required = {
        "vega_species_id", "stage61_key", "name_ja", "national_no",
        "form_key", "target_status", "apply", "reference_id", "source_form",
        "selected_game", "decision", "mapping_basis", "note_ja",
    }
    seen_keys: set[str] = set()
    seen_ids: set[int] = set()
    output: list[dict[str, Any]] = []
    for source in rows:
        _require_fields(source, required, "stage61 target row")
        key = str(source["stage61_key"])
        source_id = _decimal(source["vega_species_id"], f"{key}:vega_species_id")
        if key in seen_keys:
            _fail(f"Stage61対象keyが重複しています: {key}")
        manifest = species.by_key.get(key)
        if manifest is None:
            _fail(f"Stage61対象keyがSpecies manifestにありません: {key}")
        canonical_id = int(manifest["id"])
        if source_id != canonical_id:
            _fail(
                f"旧Species IDまたは誤結合を検出しました: "
                f"{key} source={source_id} canonical={canonical_id}"
            )
        if source_id in seen_ids:
            _fail(f"Stage61対象IDが重複しています: {source_id}")
        seen_keys.add(key)
        seen_ids.add(source_id)
        if str(source.get("form_key", "")) != manifest.get("form_key", ""):
            _fail(
                f"Species formを混同しています: {key} "
                f"source={source.get('form_key', '')!r} "
                f"canonical={manifest.get('form_key', '')!r}"
            )
        if str(source.get("name_ja", "")) != manifest["display_name"]:
            _fail(f"Species key/name意味が一致しません: {key}")

        input_apply = _boolean(source["apply"], f"{key}:apply")
        input_status = str(source["target_status"])
        input_decision = str(source["decision"])
        normalized_apply = input_apply
        normalized_status = input_status
        normalized_decision = input_decision
        override = "NONE"
        if key == "SPECIES_KEY_CATERPIE":
            normalized_apply = True
            normalized_status = "REQUIRED_BASE"
            normalized_decision = "REFERENCE"
            override = "FIX_LEGACY_TARGET_SWAP_KEEP_ID_649"
        elif key == "SPECIES_KEY_EGG":
            normalized_apply = False
            normalized_status = "INTERNAL_EXCLUDED"
            normalized_decision = "PRESERVE_VEGA_OR_INTERNAL"
            override = "KEEP_INTERNAL_EGG_EXCLUDED_AT_ID_412"

        output.append({
            "species_key": key,
            "canonical_id": canonical_id,
            "form_key": manifest.get("form_key", ""),
            "national_no": _decimal(
                manifest.get("canonical_national_dex", "0") or "0",
                f"{key}:canonical_national_dex",
            ),
            "reference_id": str(source.get("reference_id", "")),
            "selected_game": str(source.get("selected_game", "")),
            "source_form": (
                _decimal(source["source_form"], f"{key}:source_form")
                if str(source.get("source_form", "")) else None
            ),
            "input": {
                "apply": input_apply,
                "target_status": input_status,
                "decision": input_decision,
            },
            "normalized": {
                "apply": normalized_apply,
                "target_status": normalized_status,
                "decision": normalized_decision,
            },
            "override": override,
        })

    expected_keys = set(species.by_key)
    if seen_keys != expected_keys:
        _fail(
            "Stage61対象集合がSpecies manifestと一致しません: "
            f"missing={sorted(expected_keys - seen_keys)[:8]} "
            f"extra={sorted(seen_keys - expected_keys)[:8]}"
        )
    if seen_ids != set(species.by_id):
        _fail("Stage61対象ID集合がSpecies manifestと一致しません")

    by_key = {row["species_key"]: row for row in output}
    caterpie = by_key.get("SPECIES_KEY_CATERPIE")
    egg = by_key.get("SPECIES_KEY_EGG")
    if caterpie is None or caterpie["canonical_id"] != 649 \
            or caterpie["form_key"] or caterpie["national_no"] != 10:
        _fail("キャタピーcanonical identityが649/base/national 10ではありません")
    if egg is None or egg["canonical_id"] != 412 \
            or egg["form_key"] or egg["national_no"] != 0:
        _fail("内部タマゴcanonical identityが412/base/national 0ではありません")
    if not caterpie["reference_id"]:
        _fail("キャタピーの原作習得referenceがありません")

    enabled_other_false = [
        row["species_key"] for row in output
        if not row["input"]["apply"] and row["normalized"]["apply"]
        and row["species_key"] != "SPECIES_KEY_CATERPIE"
    ]
    if enabled_other_false:
        _fail(f"許可なくapply=false対象を有効化しました: {enabled_other_false[:8]}")
    changes = [
        row for row in output if row["input"] != row["normalized"]
    ]
    if {row["species_key"] for row in changes} != {
        "SPECIES_KEY_CATERPIE", "SPECIES_KEY_EGG",
    }:
        _fail(
            "対象区分の訂正集合が許可された2件ではありません: "
            f"{[row['species_key'] for row in changes]}"
        )
    summary = {
        "source_rows": len(rows),
        "normalized_rows": len(output),
        "input_apply_true": sum(row["input"]["apply"] for row in output),
        "normalized_apply_true": sum(
            row["normalized"]["apply"] for row in output
        ),
        "protected_input_false_rows": sum(
            not row["input"]["apply"] and row["species_key"] != "SPECIES_KEY_CATERPIE"
            for row in output
        ),
        "unauthorized_false_to_true": len(enabled_other_false),
        "changed_keys": [row["species_key"] for row in changes],
    }
    return output, summary


def normalize_form_map_rows(
    rows: Sequence[Mapping[str, Any]],
    species: ManifestIndex,
    targets: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """form mapもSpecies key/form keyで再解決し、Caterpieだけを有効化する。"""

    required = {
        "vega_species_id", "stage61_key", "form_key", "decision", "apply",
        "source_form",
    }
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for source in rows:
        _require_fields(source, required, "stage61 form map row")
        key = str(source["stage61_key"])
        if key in seen:
            _fail(f"form map Species keyが重複しています: {key}")
        seen.add(key)
        manifest = species.by_key.get(key)
        if manifest is None or key not in targets:
            _fail(f"form map Species keyがcanonical対象にありません: {key}")
        source_id = _decimal(source["vega_species_id"], f"form map:{key}:id")
        canonical_id = int(manifest["id"])
        if source_id != canonical_id:
            _fail(
                f"form mapで旧Species IDを検出しました: "
                f"{key} source={source_id} canonical={canonical_id}"
            )
        form_key = str(source.get("form_key", ""))
        if form_key != manifest.get("form_key", ""):
            _fail(f"form mapで別姿を混同しています: {key}")
        input_apply = _boolean(source["apply"], f"form map:{key}:apply")
        normalized_apply = input_apply or key == "SPECIES_KEY_CATERPIE"
        input_decision = str(source["decision"])
        normalized_decision = (
            "REFERENCE" if key == "SPECIES_KEY_CATERPIE" else input_decision
        )
        target = targets[key]
        if input_apply != target["input"]["apply"]:
            _fail(f"form mapと対象表のinput applyが一致しません: {key}")
        if normalized_apply != target["normalized"]["apply"]:
            _fail(f"form mapと対象表のnormalized applyが一致しません: {key}")
        output.append({
            "species_key": key,
            "canonical_id": canonical_id,
            "form_key": form_key,
            "reference_id": str(target.get("reference_id", "")),
            "source_form": (
                _decimal(source["source_form"], f"form map:{key}:source_form")
                if source.get("source_form") is not None else None
            ),
            "input_apply": input_apply,
            "normalized_apply": normalized_apply,
            "input_decision": input_decision,
            "normalized_decision": normalized_decision,
            "override": (
                "FIX_CATERPIE_REFERENCE_APPLICATION"
                if key == "SPECIES_KEY_CATERPIE" else "NONE"
            ),
        })

    unauthorized = [
        row["species_key"] for row in output
        if not row["input_apply"] and row["normalized_apply"]
        and row["species_key"] != "SPECIES_KEY_CATERPIE"
    ]
    if unauthorized:
        _fail(f"form mapの除外対象を許可なく有効化しました: {unauthorized[:8]}")
    if "SPECIES_KEY_EGG" in seen:
        _fail("内部タマゴを公式reference form mapへ混入させています")
    if "SPECIES_KEY_CATERPIE" not in seen:
        _fail("キャタピーがform mapにありません")
    return output, {
        "source_rows": len(rows),
        "normalized_rows": len(output),
        "input_apply_true": sum(row["input_apply"] for row in output),
        "normalized_apply_true": sum(row["normalized_apply"] for row in output),
        "protected_input_false_rows": sum(
            not row["input_apply"] and row["species_key"] != "SPECIES_KEY_CATERPIE"
            for row in output
        ),
        "unauthorized_false_to_true": len(unauthorized),
        "changed_keys": [
            row["species_key"] for row in output
            if row["input_apply"] != row["normalized_apply"]
            or row["input_decision"] != row["normalized_decision"]
        ],
    }


def validate_move_crosswalk_rows(
    rows: Sequence[Mapping[str, Any]],
    moves: ManifestIndex,
) -> dict[str, Any]:
    required = {
        "official_move_id", "official_identifier", "move_name_ja",
        "existing_vega_move_id", "project_move_id", "project_move_key",
        "mapping_basis", "implementation_status",
    }
    seen_official: set[int] = set()
    seen_project: set[int] = set()
    seen_keys: set[str] = set()
    unresolved: list[dict[str, Any]] = []
    for source in rows:
        _require_fields(source, required, "move crosswalk row")
        official_id = _decimal(source["official_move_id"], "official_move_id")
        project_id = _decimal(source["project_move_id"], "project_move_id")
        key = str(source["project_move_key"])
        if official_id in seen_official:
            _fail(f"official Move IDが重複しています: {official_id}")
        if project_id in seen_project:
            _fail(f"project Move IDが重複しています: {project_id}")
        if key in seen_keys:
            _fail(f"project Move keyが重複しています: {key}")
        seen_official.add(official_id)
        seen_project.add(project_id)
        seen_keys.add(key)
        manifest = moves.by_id.get(project_id)
        if manifest is not None:
            if manifest[moves.spec.key_field] != key:
                _fail(
                    f"Move key/ID意味が一致しません: "
                    f"id={project_id} source={key} "
                    f"canonical={manifest[moves.spec.key_field]}"
                )
            existing = str(source.get("existing_vega_move_id", ""))
            if not existing or _decimal(existing, f"{key}:existing_vega_move_id") != project_id:
                _fail(f"既存MoveのVega ID assertionが一致しません: {key}")
            if source["implementation_status"] != "EXISTING_VEGA_MOVE":
                _fail(f"既存Moveの実装状態が不正です: {key}")
            continue

        unresolved.append({
            "official_move_id": official_id,
            "project_move_id": project_id,
            "project_move_key": key,
            "implementation_status": str(source["implementation_status"]),
            "mapping_basis": str(source["mapping_basis"]),
        })

    expected_unresolved = [{
        "official_move_id": 502,
        "project_move_id": 1063,
        "project_move_key": "MOVE_KEY_ALLYSWITCH",
        "implementation_status": "SPEC_ONLY_REQUIRES_ENGINE_IMPLEMENTATION",
        "mapping_basis": "EXPLICIT_NEW_SPEC_ID_NOT_ROM_ID",
    }]
    if unresolved != expected_unresolved:
        _fail(
            "未実装Move集合が契約外です。ID 1063を実装済みとして扱えません: "
            f"{unresolved}"
        )
    return {
        "rows": len(rows),
        "implemented_rows": len(rows) - len(unresolved),
        "unimplemented_rows": unresolved,
    }


def _validate_entity_stream(
    archive: CheckedArchive,
    suffix: str,
    index: ManifestIndex,
    *,
    allow_unimplemented_move: bool = False,
) -> dict[str, Any]:
    name, raw_stream = archive.lines(suffix)
    count = 0
    unimplemented: list[dict[str, Any]] = []
    try:
        with raw_stream as stream:
            for line_number, raw in enumerate(stream, start=1):
                if not raw.strip():
                    _fail(f"{suffix}:{line_number}に空行があります")
                try:
                    row = json.loads(raw)
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    _fail(f"{suffix}:{line_number}がJSON objectではありません: {error}")
                if not isinstance(row, dict):
                    _fail(f"{suffix}:{line_number}がJSON objectではありません")
                _require_fields(row, ("id", "key", "name"), suffix)
                canonical_id = _decimal(row["id"], f"{suffix}:{line_number}:id")
                if canonical_id != count:
                    _fail(f"{suffix}のIDが欠落・重複・順序不正です: {canonical_id}")
                manifest = index.by_id.get(canonical_id)
                if manifest is None:
                    if allow_unimplemented_move and row == {
                        "accuracy": None,
                        "category": "変化",
                        "description": "味方と位置を入れ替える技。原作仕様に基づく新規定義案。連続使用制限などの世代差もゲーム実装時に扱う。",
                        "effect_id": None,
                        "evidence": "SPEC_ONLY_REQUIRES_ENGINE_IMPLEMENTATION",
                        "id": 1063,
                        "key": "MOVE_KEY_ALLYSWITCH",
                        "name": "サイドチェンジ",
                        "official_move_id": 502,
                        "power": 0,
                        "pp": 15,
                        "priority": 2,
                        "runtime_implemented": False,
                        "type": "エスパー",
                    }:
                        unimplemented.append({
                            "id": 1063,
                            "key": "MOVE_KEY_ALLYSWITCH",
                            "runtime_implemented": False,
                        })
                        count += 1
                        continue
                    _fail(f"{suffix}がmanifest範囲外IDを含みます: {canonical_id}")
                if row["key"] != manifest[index.spec.key_field]:
                    _fail(f"{suffix}のkey/ID意味が一致しません: {canonical_id}")
                if row["name"] != manifest["display_name"]:
                    _fail(f"{suffix}のkey/name意味が一致しません: {row['key']}")
                if index.spec.name == "species" \
                        and row.get("form_key", "") != manifest.get("form_key", ""):
                    _fail(f"{suffix}のSpecies formが一致しません: {row['key']}")
                count += 1
    except OSError as error:
        _fail(f"{suffix}を展開できません: {error}")
    expected = index.spec.expected_count + (1 if allow_unimplemented_move else 0)
    if count != expected:
        _fail(f"{suffix}件数が不正です: {count} != {expected}")
    if allow_unimplemented_move and unimplemented != [{
        "id": 1063,
        "key": "MOVE_KEY_ALLYSWITCH",
        "runtime_implemented": False,
    }]:
        _fail("Move 1063の未実装sentinelがありません")
    return {
        "path_below_archive_root": PurePosixPath(*PurePosixPath(name).parts[1:]).as_posix(),
        "rows": count,
        "canonical_rows": index.spec.expected_count,
        "unimplemented_rows": unimplemented,
    }


def _validate_species_snapshot(
    archive: CheckedArchive,
    manifests: Mapping[str, ManifestIndex],
    source_targets: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    suffix = "docs/wiki/stage61/data/species.jsonl"
    name, raw_stream = archive.lines(suffix)
    count = 0
    type_references = 0
    ability_references = 0
    item_references = 0
    move_references = 0
    unimplemented_reference_count = 0
    with raw_stream as stream:
        for line_number, raw in enumerate(stream, start=1):
            try:
                row = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                _fail(f"{suffix}:{line_number}が不正です: {error}")
            _require_fields(
                row,
                ("id", "key", "name", "form_key", "target_status", "types",
                 "abilities", "held_items", "learnsets", "learnsets_selection"),
                suffix,
            )
            canonical_id = _decimal(row["id"], f"{suffix}:{line_number}:id")
            if canonical_id != count:
                _fail(f"Species snapshot IDが連続していません: {canonical_id}")
            manifest = manifests["species"].by_id.get(canonical_id)
            if manifest is None or row["key"] != manifest["species_key"]:
                _fail(f"Species snapshot key/ID意味が一致しません: {canonical_id}")
            if row["name"] != manifest["display_name"] \
                    or row["form_key"] != manifest.get("form_key", ""):
                _fail(f"Species snapshot name/form意味が一致しません: {row['key']}")
            target = source_targets.get(row["key"])
            if target is None or row["target_status"] != target["input"]["target_status"]:
                _fail(f"Species snapshot対象区分がsource決定表と一致しません: {row['key']}")
            selection = row["learnsets_selection"]
            if not isinstance(selection, dict):
                _fail(f"Species learnsets_selectionがobjectではありません: {row['key']}")
            if (
                _boolean(selection.get("apply"), f"snapshot:{row['key']}:apply")
                != target["input"]["apply"]
                or selection.get("decision") != target["input"]["decision"]
                or (selection.get("reference_id") or "") != target["reference_id"]
            ):
                _fail(f"Species snapshotとsource決定表が一致しません: {row['key']}")

            for value in row["types"]:
                if not isinstance(value, dict) or "id" not in value or "name" not in value:
                    _fail(f"Species type参照が不正です: {row['key']}")
                ref = _decimal(value["id"], f"{row['key']}:type")
                target_type = manifests["types"].by_id.get(ref)
                if target_type is None or value["name"] != target_type["display_name"]:
                    _fail(f"Species type key意味が一致しません: {row['key']}:{ref}")
                type_references += 1
            for value in row["abilities"]:
                if not isinstance(value, dict) or "id" not in value or "name" not in value:
                    _fail(f"Species Ability参照が不正です: {row['key']}")
                ref = _decimal(value["id"], f"{row['key']}:ability")
                ability = manifests["abilities"].by_id.get(ref)
                if ability is None or value["name"] != ability["display_name"]:
                    _fail(f"Species Ability key意味が一致しません: {row['key']}:{ref}")
                ability_references += 1
            for value in row["held_items"]:
                if not isinstance(value, dict) or "id" not in value:
                    _fail(f"Species Item参照が不正です: {row['key']}")
                ref = _decimal(value["id"], f"{row['key']}:item")
                if ref not in manifests["items"].by_id:
                    _fail(f"Species Item参照が範囲外です: {row['key']}:{ref}")
                item_references += 1
            learnsets = row["learnsets"]
            if not isinstance(learnsets, dict):
                _fail(f"Species learnsetsがobjectではありません: {row['key']}")
            runtime_learnsets = row.get("learnsets_runtime_snapshot", learnsets)
            if not isinstance(runtime_learnsets, dict):
                _fail(f"Species runtime learnsetsがobjectではありません: {row['key']}")
            for values in runtime_learnsets.values():
                if not isinstance(values, list):
                    _fail(f"Species runtime learnset経路がlistではありません: {row['key']}")
                for value in values:
                    ref = value.get("move_id") if isinstance(value, dict) else value
                    move_id = _decimal(ref, f"{row['key']}:move")
                    if move_id not in manifests["moves"].by_id:
                        _fail(f"実ROM習得表が未実装Moveを参照しています: {row['key']}:{move_id}")
                    move_references += 1
            specification = row.get("learnsets_reference", learnsets)
            if specification is not runtime_learnsets:
                if not isinstance(specification, dict):
                    _fail(f"learnsets specificationがobjectではありません: {row['key']}")
                for move_id in specification.get("all_move_ids", []):
                    parsed = _decimal(move_id, f"{row['key']}:reference move")
                    if parsed not in manifests["moves"].by_id:
                        if parsed != 1063:
                            _fail(f"原作習得参照が未知Moveを参照しています: {row['key']}:{parsed}")
                        unimplemented_reference_count += 1
            count += 1
    if count != manifests["species"].spec.expected_count:
        _fail(f"Species snapshot件数が不正です: {count}")
    return {
        "path_below_archive_root": PurePosixPath(*PurePosixPath(name).parts[1:]).as_posix(),
        "rows": count,
        "type_references": type_references,
        "ability_references": ability_references,
        "item_references": item_references,
        "runtime_move_references": move_references,
        "unimplemented_move_1063_reference_sets": unimplemented_reference_count,
    }


def _validate_restoration_candidates(
    document: Any,
    manifests: Mapping[str, ManifestIndex],
) -> dict[str, Any]:
    if not isinstance(document, dict) or document.get("status") != "REVIEW_ONLY_NOT_APPLIED":
        _fail("原作復元資料を採用済みデータとして扱えません")
    candidates = document.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 194:
        _fail("原作復元review candidate件数が契約外です")
    seen_keys: set[str] = set()
    seen_ids: set[int] = set()
    counts: Counter[str] = Counter()
    ability_refs = 0
    type_refs = 0
    for candidate in candidates:
        if not isinstance(candidate, dict):
            _fail("原作復元candidateがobjectではありません")
        _require_fields(candidate, ("existing_project_id", "assert_species_key", "changes"), "restoration candidate")
        key = str(candidate["assert_species_key"])
        canonical_id = _decimal(candidate["existing_project_id"], f"{key}:existing_project_id")
        if key in seen_keys or canonical_id in seen_ids:
            _fail(f"原作復元candidateのkey/IDが重複しています: {key}/{canonical_id}")
        seen_keys.add(key)
        seen_ids.add(canonical_id)
        species = manifests["species"].by_key.get(key)
        if species is None or int(species["id"]) != canonical_id:
            _fail(
                f"原作復元candidateで旧Species IDを検出しました: "
                f"{key}/{canonical_id}"
            )
        changes = candidate["changes"]
        if not isinstance(changes, dict) or not changes:
            _fail(f"原作復元candidate changesが空です: {key}")
        unknown = set(changes) - {"base_stats", "abilities", "types"}
        if unknown:
            _fail(f"原作復元candidateに未監査fieldがあります: {key}:{sorted(unknown)}")
        counts.update(changes.keys())
        ability_change = changes.get("abilities")
        if ability_change is not None:
            for ability_id in ability_change.get("target_project_ids", []):
                parsed = _decimal(ability_id, f"{key}:target ability")
                if parsed not in manifests["abilities"].by_id:
                    _fail(f"原作復元candidate Abilityが範囲外です: {key}:{parsed}")
                ability_refs += 1
        type_change = changes.get("types")
        if type_change is not None:
            type_ids = type_change.get("target_project_ids", [])
            type_names = type_change.get("target_names", [])
            if len(type_ids) != len(type_names):
                _fail(f"原作復元candidate Type ID/name数が一致しません: {key}")
            for type_id, name in zip(type_ids, type_names):
                parsed = _decimal(type_id, f"{key}:target type")
                target = manifests["types"].by_id.get(parsed)
                if target is None or target["display_name"] != name:
                    _fail(f"原作復元candidate Type key意味が一致しません: {key}:{parsed}")
                type_refs += 1
    if counts != Counter({"abilities": 190, "base_stats": 21, "types": 7}):
        _fail(f"原作復元candidate区分件数が契約外です: {dict(counts)}")
    return {
        "status": "REVIEW_ONLY_NOT_APPLIED",
        "candidate_rows": len(candidates),
        "candidate_change_counts": dict(sorted(counts.items())),
        "species_key_id_assertions": len(seen_keys),
        "ability_references": ability_refs,
        "type_references": type_refs,
        "automatically_adopted_rows": 0,
    }


def build_identity_contract(
    root: Path,
    learnsets_zip: Path,
    restoration_zip: Path,
) -> dict[str, Any]:
    manifests = load_manifests(root)
    with CheckedArchive(learnsets_zip, "learnsets") as archive:
        decisions_name, decisions_raw = archive.read("data/stage61_record_decisions.csv")
        form_name, form_raw = archive.read("config/stage61_form_map.json")
        crosswalk_name, crosswalk_raw = archive.read("data/move_id_crosswalk.csv")
        target_rows, target_summary = normalize_target_rows(
            _csv_rows(decisions_raw, decisions_name), manifests["species"],
        )
        targets = {row["species_key"]: row for row in target_rows}
        try:
            form_source = json.loads(form_raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            _fail(f"{form_name}を読めません: {error}")
        if not isinstance(form_source, list):
            _fail("stage61_form_map.json rootがarrayではありません")
        form_rows, form_summary = normalize_form_map_rows(
            form_source, manifests["species"], targets,
        )
        move_crosswalk = validate_move_crosswalk_rows(
            _csv_rows(crosswalk_raw, crosswalk_name), manifests["moves"],
        )
        entity_audit = {
            "species": _validate_species_snapshot(archive, manifests, targets),
            "moves": _validate_entity_stream(
                archive, "docs/wiki/stage61/data/moves.jsonl",
                manifests["moves"], allow_unimplemented_move=True,
            ),
            "abilities": _validate_entity_stream(
                archive, "docs/wiki/stage61/data/abilities.jsonl",
                manifests["abilities"],
            ),
            "items": _validate_entity_stream(
                archive, "docs/wiki/stage61/data/items.jsonl", manifests["items"],
            ),
        }
        learnsets_identity = archive.identity()
        learnsets_members = {
            "stage61_record_decisions": _member_identity(decisions_name, decisions_raw),
            "stage61_form_map": _member_identity(form_name, form_raw),
            "move_id_crosswalk": _member_identity(crosswalk_name, crosswalk_raw),
        }

    with CheckedArchive(restoration_zip, "restoration_audit") as archive:
        audit_name, audit_raw = archive.read("11_ID固定_内容更新候補_未適用.json")
        try:
            audit_document = json.loads(audit_raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            _fail(f"{audit_name}を読めません: {error}")
        restoration = _validate_restoration_candidates(audit_document, manifests)
        restoration_identity = archive.identity()
        restoration_member = _member_identity(audit_name, audit_raw)

    manifest_contract = {
        name: {
            "path": index.spec.relative_path,
            "key_field": index.spec.key_field,
            "key_prefix": index.spec.key_prefix,
            "rows": len(index.rows),
            "id_min": 0,
            "id_max": len(index.rows) - 1,
            "ids_contiguous_and_ordered": True,
            "sha256": index.sha256,
        }
        for name, index in sorted(manifests.items())
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "policy": {
            "identity_join": "CANONICAL_KEY_THEN_ASSERT_NUMERIC_ID",
            "numeric_id_only_join": "FORBIDDEN",
            "manifest_ids_changed": False,
            "form_identity": "SPECIES_KEY_AND_FORM_KEY_EXACT",
            "restoration_candidates": "REVIEW_ONLY_NOT_AUTOMATICALLY_APPLIED",
            "other_apply_false_rows": "PRESERVED",
            "unimplemented_move_1063": "SPEC_ONLY_NOT_ROM_RUNTIME",
        },
        "inputs": {
            "learnsets": {
                **learnsets_identity,
                "authoritative_members": learnsets_members,
            },
            "restoration_audit": {
                **restoration_identity,
                "authoritative_member": restoration_member,
            },
        },
        "manifests": manifest_contract,
        "target_normalization": {
            "summary": target_summary,
            "records": target_rows,
        },
        "form_map_normalization": {
            "summary": form_summary,
            "records": form_rows,
        },
        "move_crosswalk": move_crosswalk,
        "zip_entity_identity_audit": entity_audit,
        "restoration_review_audit": restoration,
    }
