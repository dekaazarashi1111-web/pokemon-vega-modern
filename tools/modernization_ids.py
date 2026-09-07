"""P01: 数値だけの結合を禁止する、副作用のないcanonical identity処理。"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
import re
from typing import Any


class IdentityError(ValueError):
    """原本の行本文ではなく、失敗した契約名だけを伝える。"""


def integer(value: Any) -> int:
    if isinstance(value, bool) or not re.fullmatch(r"0|[1-9][0-9]*", str(value)):
        raise IdentityError("NON_CANONICAL_INTEGER")
    return int(value)


def boolean(value: Any) -> bool:
    if value is True or value in ("true", "True"):
        return True
    if value is False or value in ("false", "False"):
        return False
    raise IdentityError("NON_CANONICAL_BOOLEAN")


class CanonicalIndex:
    """namespace、key、IDの全単射を検証する。表示名はidentityに使わない。"""

    def __init__(self, rows: Iterable[Mapping[str, Any]], namespace: str,
                 *, count: int | None = None) -> None:
        self.namespace = namespace
        self.key_field = namespace.lower() + "_key"
        self.by_key: dict[str, dict[str, Any]] = {}
        self.by_id: dict[int, dict[str, Any]] = {}
        forms: set[str] = set()
        pattern = re.compile(re.escape(namespace.upper() + "_KEY_") + r"[A-Z0-9_]+")
        for source in rows:
            row = deepcopy(dict(source))
            key = row.get(self.key_field)
            if not isinstance(key, str) or not pattern.fullmatch(key):
                raise IdentityError("INVALID_KEY_NAMESPACE")
            ident = integer(row.get("id"))
            if ident >= (count if count is not None else 65536):
                raise IdentityError("CANONICAL_ID_OUT_OF_RANGE")
            if key in self.by_key:
                raise IdentityError("DUPLICATE_CANONICAL_KEY")
            if ident in self.by_id:
                raise IdentityError("DUPLICATE_CANONICAL_ID")
            if namespace == "species":
                form = row.get("form_key", "")
                if row.get("classification") == "DPE_FORM_APPEND" and not form:
                    raise IdentityError("FORM_KEY_MISSING")
                if form:
                    if not re.fullmatch(r"FORM_KEY_[A-Z0-9_]+", form) or form in forms:
                        raise IdentityError("DUPLICATE_OR_INVALID_FORM_KEY")
                    forms.add(form)
            row["id"] = ident
            self.by_key[key] = row
            self.by_id[ident] = row
        if not self.by_key:
            raise IdentityError("EMPTY_CANONICAL_MANIFEST")
        if count is not None and set(self.by_id) != set(range(count)):
            raise IdentityError("CANONICAL_ID_SET_MISMATCH")

    def require(self, key: Any, ident: Any | None = None) -> dict[str, Any]:
        if not isinstance(key, str) or key not in self.by_key:
            raise IdentityError("UNKNOWN_CANONICAL_KEY")
        row = self.by_key[key]
        if ident is not None and integer(ident) != row["id"]:
            raise IdentityError("KEY_ID_MEANING_MISMATCH")
        return deepcopy(row)


def normalize_rows(index: CanonicalIndex, rows: Iterable[Mapping[str, Any]], *,
                   key_field: str, id_field: str, require_all: bool = True,
                   legacy: Mapping[str, int] | None = None,
                   semantic_fields: Mapping[str, str] | None = None
                   ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """既知の旧IDだけを訂正し、入力の順序・非ID列を保存する。"""
    legacy = {} if legacy is None else legacy
    semantic_fields = {} if semantic_fields is None else semantic_fields
    for key, old in legacy.items():
        index.require(key)
        if integer(old) not in index.by_id:
            raise IdentityError("LEGACY_ID_OUT_OF_RANGE")
    output: list[dict[str, Any]] = []
    corrections: list[dict[str, Any]] = []
    keys: set[str] = set()
    old_ids: set[int] = set()
    for source in rows:
        row = deepcopy(dict(source))
        key = row.get(key_field)
        canonical = index.require(key)
        old = integer(row.get(id_field))
        if old not in index.by_id:
            raise IdentityError("SOURCE_ID_OUT_OF_RANGE")
        if key in keys:
            raise IdentityError("DUPLICATE_SOURCE_KEY")
        if old in old_ids:
            raise IdentityError("DUPLICATE_SOURCE_ID")
        keys.add(key)
        old_ids.add(old)
        for field, canonical_field in semantic_fields.items():
            left, right = row.get(field, ""), canonical.get(canonical_field, "")
            if canonical_field == "canonical_national_dex":
                left, right = integer(left or 0), integer(right or 0)
            if left != right:
                raise IdentityError("SEMANTIC_FIELD_MISMATCH:" + field)
        if old != canonical["id"]:
            if legacy.get(key) != old:
                raise IdentityError("UNAPPROVED_STALE_ID")
            corrections.append({"key": key, "old_id": old, "current_id": canonical["id"]})
        row[id_field] = canonical["id"]
        output.append(row)
    if require_all and keys != set(index.by_key):
        raise IdentityError("SOURCE_KEY_SET_MISMATCH")
    return output, corrections


def validate_registry(index: CanonicalIndex, rows: list[dict[str, Any]]) -> None:
    """内部枠、通常基本種、フォームの意味を検査。収集bitは変更しない。"""
    collection_keys: set[str] = set()
    by_key = {row["species_key"]: row for row in rows}
    if len(by_key) != len(rows) or set(by_key) != set(index.by_key):
        raise IdentityError("REGISTRY_KEY_SET_MISMATCH")
    for row in rows:
        canonical = index.require(row["species_key"], row["canonical_id"])
        key = row.get("collection_key")
        if not isinstance(key, str) or not key or key in collection_keys:
            raise IdentityError("DUPLICATE_OR_EMPTY_COLLECTION_KEY")
        collection_keys.add(key)
        if row.get("form_key", "") != canonical.get("form_key", ""):
            raise IdentityError("REGISTRY_FORM_MISMATCH")
        if integer(row.get("national_no") or 0) != integer(canonical.get("canonical_national_dex") or 0):
            raise IdentityError("REGISTRY_NATIONAL_DEX_MISMATCH")
        if boolean(row["is_official"]) != boolean(canonical["is_official"]):
            raise IdentityError("REGISTRY_OFFICIAL_IDENTITY_MISMATCH")
        if canonical.get("form_key") and row.get("base_or_form") != "FORM":
            raise IdentityError("FORM_ADOPTED_AS_BASE")
    for key in ("SPECIES_KEY_NONE", "SPECIES_KEY_EGG"):
        row = by_key[key]
        if (row["target_status"] != "INTERNAL_EXCLUDED"
                or integer(row["completion_weight"]) != 0 or row["route_required"] != "no"):
            raise IdentityError("INTERNAL_SLOT_ADOPTED")
    caterpie = by_key["SPECIES_KEY_CATERPIE"]
    if (caterpie["target_status"] != "REQUIRED_BASE" or caterpie["base_or_form"] != "BASE"
            or integer(caterpie["completion_weight"]) != 1 or caterpie["route_required"] != "yes"):
        raise IdentityError("CATERPIE_NOT_REQUIRED_BASE")


def normalize_decisions(index: CanonicalIndex, registry: list[dict[str, Any]],
                        rows: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """P01の対象メタデータ訂正のみ。技表やROMを適用しない。"""
    validate_registry(index, registry)
    output, id_changes = normalize_rows(index, rows, key_field="stage61_key", id_field="vega_species_id",
                                        semantic_fields={"form_key": "form_key", "national_no": "canonical_national_dex"})
    if id_changes:
        raise IdentityError("DECISION_ID_CHANGED")
    registry_by_key = {row["species_key"]: row for row in registry}
    changes: list[dict[str, Any]] = []
    permitted_statuses = {
        "SPECIES_KEY_CATERPIE": ("INTERNAL_EXCLUDED", "REQUIRED_BASE"),
        "SPECIES_KEY_EGG": ("REQUIRED_BASE", "INTERNAL_EXCLUDED"),
    }
    for row in output:
        key = row["stage61_key"]
        apply = boolean(row["apply"])
        expected = registry_by_key[key]["target_status"]
        before = {"target_status": row["target_status"], "apply": apply}
        if row["target_status"] != expected:
            if permitted_statuses.get(key) != (row["target_status"], expected):
                raise IdentityError("UNAPPROVED_TARGET_CLASSIFICATION_CHANGE")
            row["target_status"] = expected
        if key == "SPECIES_KEY_CATERPIE":
            if not row.get("reference_id") or integer(row["national_no"]) != 10 or row.get("form_key"):
                raise IdentityError("CATERPIE_REFERENCE_MISSING_OR_WRONG_FORM")
            apply = True
        if key in ("SPECIES_KEY_NONE", "SPECIES_KEY_EGG") and apply:
            raise IdentityError("INTERNAL_LEARNSET_ADOPTED")
        row["apply"] = apply
        after = {"target_status": row["target_status"], "apply": apply}
        if before != after:
            changes.append({"key": key, "before": before, "after": after})
    return output, changes


def validate_forms(index: CanonicalIndex, rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    seen: set[str] = set()
    excluded = 0
    for row in rows:
        target = index.require(row["species_key"], row["target_species"])
        base = index.require(row["base_species_key"], row["base_species"])
        if row["species_key"] in seen:
            raise IdentityError("DUPLICATE_FORM_TARGET")
        seen.add(row["species_key"])
        if not target.get("form_key") or not base.get("canonical_national_dex"):
            raise IdentityError("INVALID_FORM_TARGET_OR_BASE")
        if integer(target["canonical_national_dex"]) != integer(base["canonical_national_dex"]):
            raise IdentityError("FORM_FAMILY_MISMATCH")
        if row["method"] in ("DO_NOT_DISTRIBUTE", "BATTLE_TRANSFORM_ONLY", "GMAX_FACTOR_ONLY"):
            excluded += 1
            if boolean(row["distributable"]):
                raise IdentityError("EXCLUDED_FORM_DISTRIBUTED")
    return {"checked": len(seen), "excluded_methods": excluded}
