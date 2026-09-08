"""P01: 受領済みの限定ID契約を現行の対象consumerへ接続する。

原本の集合digestは訂正前を表す。意味を固定した2件以外は変更しない。
このmoduleはROM、save、歴史的Wiki、取得bitへ書き込まない。
"""
from __future__ import annotations

from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from tools.modernization_ids import CanonicalIndex, IdentityError, integer, validate_forms, validate_registry

CONTRACT_PATH = "content/modernization/identity_contract.json"
CATERPIE = "SPECIES_KEY_CATERPIE"
EGG = "SPECIES_KEY_EGG"
ELIGIBLE = frozenset(("REQUIRED_BASE", "REQUIRED_ENABLING_FORM", "OPTIONAL_FORM"))


def projection_digest(value: Any) -> str:
    """UTF-8 / ensure_ascii=False / sort_keys / compact separators / 終端改行なし。"""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def require_set_pin(keys: list[str], pin: dict[str, Any], label: str) -> None:
    if len(set(keys)) != len(keys):
        raise IdentityError(label + "_DUPLICATE_KEY")
    if len(keys) != integer(pin["count"]) or projection_digest(sorted(keys)) != pin["sha256"]:
        raise IdentityError(label + "_KEY_SET_MISMATCH")


def resolve_targets(indexes: dict[str, CanonicalIndex], registry: list[dict],
                    forms: list[dict], contract: dict) -> dict:
    """原本のidentityと集合を照合した後だけ、現行対象表を返す。"""
    if contract["schema_version"] != 1 or contract["task"] != "USER-MODERNIZATION-P01":
        raise IdentityError("REFERENCE_CONTRACT_SCHEMA_MISMATCH")
    species = indexes["species"]
    validate_registry(species, registry)
    spec = contract["species"]
    identities = [[key, row["id"], integer(row.get("canonical_national_dex") or 0), row.get("form_key", "")]
                  for key, row in sorted(species.by_key.items())]
    if len(identities) != integer(spec["count"]) or projection_digest(identities) != spec["identity_projection_sha256"]:
        raise IdentityError("REFERENCE_SPECIES_IDENTITY_MISMATCH")
    by_key = {row["species_key"]: row for row in registry}
    archived_sets: dict[str, list[str]] = defaultdict(list)
    current_sets: dict[str, list[str]] = defaultdict(list)
    for key, row in sorted(by_key.items()):
        status = row["target_status"]
        current_sets[status].append(key)
        # 台帳原本の誤区分へ戻した集合との比較。現行出力へ旧区分は出さない。
        archived_status = "INTERNAL_EXCLUDED" if key == CATERPIE else "REQUIRED_BASE" if key == EGG else status
        archived_sets[archived_status].append(key)
    if set(archived_sets) != set(spec["target_sets"]):
        raise IdentityError("TARGET_STATUS_SET_MISMATCH")
    for status, keys in archived_sets.items():
        require_set_pin(keys, spec["target_sets"][status], "ARCHIVED_TARGET_" + status)
    excluded = spec["preserved_optional_exclusions"]
    if len(excluded) != len(set(excluded)) or any(key not in by_key or by_key[key]["target_status"] != "OPTIONAL_FORM" for key in excluded):
        raise IdentityError("OPTIONAL_EXCLUSION_CONTRACT_MISMATCH")
    apply_keys = sorted(key for key, row in by_key.items() if row["target_status"] in ELIGIBLE and key not in excluded)
    require_set_pin(apply_keys, spec["corrected_apply"], "CORRECTED_APPLY")
    require_set_pin([key for key in apply_keys if key != CATERPIE], spec["source_apply"], "SOURCE_APPLY")
    if CATERPIE not in apply_keys or EGG in apply_keys or "SPECIES_KEY_NONE" in apply_keys:
        raise IdentityError("INTERNAL_OR_CATERPIE_ADOPTION_MISMATCH")
    expected_forms = {key for key, row in species.by_key.items() if row.get("form_key")}
    actual_forms = [row["species_key"] for row in forms]
    if len(actual_forms) != len(set(actual_forms)) or set(actual_forms) != expected_forms:
        raise IdentityError("FORM_TARGET_KEY_SET_MISMATCH")
    form_audit = validate_forms(species, forms)
    moves = indexes["move"]
    mids = [integer(value) for value in contract["moves"]["existing_ids"]]
    if len(mids) != integer(contract["moves"]["existing_count"]) or len(mids) != len(set(mids)):
        raise IdentityError("MOVE_REFERENCE_SET_MISMATCH")
    if any(mid not in moves.by_id for mid in mids):
        raise IdentityError("MOVE_REFERENCE_OUT_OF_RANGE")
    move_pairs = sorted([[moves.by_id[mid]["move_key"], mid] for mid in mids])
    if projection_digest(move_pairs) != contract["moves"]["identity_projection_sha256"]:
        raise IdentityError("MOVE_REFERENCE_KEY_ID_MISMATCH")
    pending = contract["moves"]["pending"]
    pending_keys: set[str] = set()
    pending_ids: set[int] = set()
    for row in pending:
        ident = integer(row["proposal_id"])
        if (row["key"] in moves.by_key or ident in moves.by_id or row["key"] in pending_keys
                or ident in pending_ids or row["status"] != "SPEC_ONLY_REQUIRES_ENGINE_IMPLEMENTATION"):
            raise IdentityError("UNIMPLEMENTED_MOVE_ADOPTED_OR_DUPLICATED")
        pending_keys.add(row["key"])
        pending_ids.add(ident)
    abilities = indexes["ability"]
    ability_refs = []
    seen_abilities: set[int] = set()
    for ident_raw, name in contract["restoration"]["ability_numeric_name_references"]:
        ident = integer(ident_raw)
        if ident in seen_abilities:
            raise IdentityError("DUPLICATE_ABILITY_REFERENCE")
        seen_abilities.add(ident)
        canonical = abilities.by_id.get(ident)
        alias_none = ident == 0 and name == "なし" and canonical is not None and canonical["ability_key"] == "ABILITY_KEY_NONE"
        matches = canonical is not None and (name == canonical["display_name"] or alias_none)
        ability_refs.append({"reference_id": ident, "reference_name": name,
                             "canonical_key": canonical["ability_key"] if canonical else None,
                             "name_id_match": matches, "adoption_authorized": False})
    if contract["restoration"]["adopted"] is not False:
        raise IdentityError("RESTORATION_PROPOSALS_NOT_APPROVED")
    apply_set = set(apply_keys)
    targets = [{"species_key": key, "id": row["id"], "national_no": integer(row.get("canonical_national_dex") or 0),
                "form_key": row.get("form_key", ""), "name": row["display_name"],
                "target_status": by_key[key]["target_status"], "collection_key": by_key[key]["collection_key"],
                "apply": key in apply_set}
               for key, row in sorted(species.by_key.items(), key=lambda pair: pair[1]["id"])]
    return {"schema_version": 1, "task": "USER-MODERNIZATION-P01", "evidence": "SOURCE_TARGET_IDENTITY_NOT_ROM_APPLICATION",
            "rom_applied": False, "save_bit_reindex": False, "species": targets,
            "target_sets": dict(sorted(current_sets.items())), "apply_keys": apply_keys,
            "newly_enabled_keys": [CATERPIE], "preserved_optional_exclusions": excluded,
            "caterpie_reference_id": spec["caterpie_reference_id"],
            "move_key_id_pairs": move_pairs, "unimplemented_moves": pending,
            "form_audit": form_audit, "ability_reference_audit": ability_refs,
            "ability_reference_mismatches": [row for row in ability_refs if not row["name_id_match"]],
            "restoration_adopted": False}


def load_targets(root: Path, current: dict) -> dict:
    inputs = json.loads((root / "config/modernization_inputs.json").read_text(encoding="utf-8"))
    pin = inputs["normalized_projection"]
    if pin["path"] != CONTRACT_PATH:
        raise IdentityError("REFERENCE_CONTRACT_PATH_MISMATCH")
    path = root / CONTRACT_PATH
    if path.is_symlink():
        raise IdentityError("REFERENCE_CONTRACT_SYMLINK")
    raw = path.read_bytes()
    if len(raw) != integer(pin["size"]) or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
        raise IdentityError("REFERENCE_CONTRACT_HASH_MISMATCH")
    indexes = {}
    for kind in ("species", "move", "ability"):
        with (root / f"manifests/{kind}_ids.csv").open(encoding="utf-8-sig", newline="") as stream:
            indexes[kind] = CanonicalIndex(csv.DictReader(stream), kind, count=current["counts"][kind])
    supply = json.loads((root / "content/collection_supply_v1/canonical_model.json").read_text(encoding="utf-8"))
    result = resolve_targets(indexes, [row["registry"] for row in current["species"]], supply["forms"], json.loads(raw))
    result["input_contract_sha256"] = pin["sha256"]
    return result
