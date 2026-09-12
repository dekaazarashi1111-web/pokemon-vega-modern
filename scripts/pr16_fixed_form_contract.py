#!/usr/bin/env python3
"""Build the finite P03 fixed-form physical acceptance contract.

This is a read-only bridge between the pinned four-route owner inventory and a
future mGBA acceptance runner.  It deliberately does not claim native
acceptance, mutate a ROM/save, or close P03.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import pr16_p03_form_gap_inventory as inventory

SCHEMA = "pr16_fixed_form_contract.v1"
STATUS = "PASS_FIXED_FORM_CONTRACT_NATIVE_PENDING"
MODEL = Path("content/collection_supply_v1/canonical_model.json")
EXPECTED_TARGETS: dict[int, dict[str, Any]] = {
    1260: {
        "species_key": "SPECIES_KEY_NECROZMA_DUSK_MANE",
        "base_species": 1198,
        "base_species_key": "SPECIES_KEY_NECROZMA",
        "family": "necrozma_fixed_transition",
    },
    1261: {
        "species_key": "SPECIES_KEY_NECROZMA_DAWN_WINGS",
        "base_species": 1198,
        "base_species_key": "SPECIES_KEY_NECROZMA",
        "family": "necrozma_fixed_transition",
    },
    1386: {
        "species_key": "SPECIES_KEY_ZACIAN_CROWNED",
        "base_species": 1361,
        "base_species_key": "SPECIES_KEY_ZACIAN",
        "family": "crowned_battle_transition",
    },
    1387: {
        "species_key": "SPECIES_KEY_ZAMAZENTA_CROWNED",
        "base_species": 1362,
        "base_species_key": "SPECIES_KEY_ZAMAZENTA",
        "family": "crowned_battle_transition",
    },
}
EXPECTED_TARGET_ORDER = tuple(EXPECTED_TARGETS)

CASE_MATRIX = (
    {
        "id": "necrozma-dusk-mane-four-slot-roundtrip",
        "targets": [1260],
        "required_witnesses": [
            "native_transition_entry",
            "transition_owned_move_resolution",
            "four_slot_boundary",
            "identity_preserved",
            "native_reversion",
            "normal_save",
            "fresh_continue",
        ],
    },
    {
        "id": "necrozma-dawn-wings-four-slot-roundtrip",
        "targets": [1261],
        "required_witnesses": [
            "native_transition_entry",
            "transition_owned_move_resolution",
            "four_slot_boundary",
            "identity_preserved",
            "native_reversion",
            "normal_save",
            "fresh_continue",
        ],
    },
    {
        "id": "necrozma-decline-unchanged",
        "targets": [1260, 1261],
        "required_witnesses": [
            "native_transition_entry",
            "native_decline_or_ineligible_control",
            "party_bytes_unchanged",
            "save_counter_unchanged",
        ],
    },
    {
        "id": "zacian-crowned-battle-roundtrip",
        "targets": [1386],
        "required_witnesses": [
            "native_held_item_or_battle_entry",
            "battle_form_and_move",
            "battle_exit_restoration",
            "held_item_removal_boundary",
            "no_invalid_saved_form_move_pair",
        ],
    },
    {
        "id": "zamazenta-crowned-battle-roundtrip",
        "targets": [1387],
        "required_witnesses": [
            "native_held_item_or_battle_entry",
            "battle_form_and_move",
            "battle_exit_restoration",
            "held_item_removal_boundary",
            "no_invalid_saved_form_move_pair",
        ],
    },
)


class ContractError(ValueError):
    """Raised when the fixed-form owner contract stops being finite/exact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def stable(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _index_model(model: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    forms = model.get("forms")
    service_indices = model.get("service_form_indices")
    require(isinstance(forms, list), "canonical forms must be a list")
    require(isinstance(service_indices, list), "service_form_indices must be a list")
    indexed: dict[int, dict[str, Any]] = {}
    for index in service_indices:
        require(type(index) is int and 0 <= index < len(forms), "invalid service form index")
        row = forms[index]
        require(isinstance(row, dict), "canonical service form row must be an object")
        target = row.get("target_species")
        require(type(target) is int and target not in indexed, "duplicate/invalid service target")
        indexed[target] = {"service_index": index, **row}
    return indexed


def validate(owner: Mapping[str, Any], model: Mapping[str, Any]) -> list[dict[str, Any]]:
    require(owner.get("route_count") == 4, "fixed transition route count must remain four")
    require(owner.get("species_count") == 4, "fixed transition species count must remain four")
    require(tuple(owner.get("species", ())) == EXPECTED_TARGET_ORDER, "fixed target ordering changed")
    rows = owner.get("rows")
    require(isinstance(rows, list) and len(rows) == 4, "fixed owner rows must contain four entries")
    by_target: dict[int, dict[str, Any]] = {}
    for row in rows:
        require(isinstance(row, dict), "fixed owner row must be an object")
        target = row.get("target_species_id")
        require(type(target) is int and target in EXPECTED_TARGETS, "unknown fixed transition target")
        require(target not in by_target, "duplicate fixed transition target")
        source = row.get("source_route")
        require(isinstance(source, dict), "fixed transition source_route must be an object")
        require(source.get("route_kind") == "direct", "fixed transition must retain direct ownership")
        move = source.get("project_move_id")
        require(type(move) is int and 1 <= move <= 1062, "fixed transition move id is invalid")
        by_target[target] = row
    require(tuple(sorted(by_target)) == EXPECTED_TARGET_ORDER, "fixed owner target set changed")

    service = _index_model(model)
    plans: list[dict[str, Any]] = []
    for target in EXPECTED_TARGET_ORDER:
        expected = EXPECTED_TARGETS[target]
        canonical = service.get(target)
        require(canonical is not None, f"fixed target {target} left the authored FORM service")
        for key in ("species_key", "base_species", "base_species_key"):
            require(canonical.get(key) == expected[key], f"fixed target {target} {key} changed")
        require(canonical.get("method") == "FORM_CHANGE_SERVICE", "fixed canonical method changed")
        require(canonical.get("method_id") == 4, "fixed canonical method id changed")
        require(canonical.get("unlock") == "FINAL_LEAGUE_CLEARED", "fixed unlock changed")
        require(canonical.get("unlock_id") == 15, "fixed unlock id changed")
        require(canonical.get("distributable") is True, "fixed target became nondistributable")
        source = by_target[target]["source_route"]
        plans.append(
            {
                "target_species": target,
                "target_species_key": expected["species_key"],
                "base_species": expected["base_species"],
                "base_species_key": expected["base_species_key"],
                "family": expected["family"],
                "service_index": canonical["service_index"],
                "project_move_id": source["project_move_id"],
                "official_move_id": source.get("official_move_id"),
                "source_method": source.get("method"),
                "route_id": source.get("route_id"),
                "reference_id": by_target[target].get("reference_id"),
                "native_acceptance_required": True,
            }
        )
    return plans


def build_contract(root: Path, learnsets_zip: Path) -> dict[str, Any]:
    root = root.resolve()
    source_inventory = inventory.build_inventory(root, learnsets_zip)
    owner = source_inventory["owners"]["fixed_transition"]
    model_path = root / MODEL
    require(model_path.is_file() and not model_path.is_symlink(), "canonical model missing")
    model_raw = model_path.read_bytes()
    model = json.loads(model_raw)
    plans = validate(owner, model)
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "scope": "READ_ONLY_FIXED_FORM_ACCEPTANCE_CONTRACT",
        "source_inventory": {
            "status": source_inventory["status"],
            "learnsets_zip": source_inventory["learnsets_zip"],
            "fixed_rows_sha256": owner["rows_sha256"],
            "route_count": owner["route_count"],
            "species_count": owner["species_count"],
        },
        "canonical_model": {
            "path": str(MODEL),
            "size": len(model_raw),
            "sha256": sha256(model_raw),
        },
        "targets": plans,
        "case_matrix": list(CASE_MATRIX),
        "required_native_processes_minimum": len(CASE_MATRIX),
        "native_acceptance_claimed": False,
        "p03_fixed_form_gap_closed": False,
        "p03_umbrella_closed": False,
        "rom_or_save_modified": False,
        "release_ready": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--learnsets-zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.learnsets_zip is None:
        config = json.loads(
            (root / "config/modernization_p03_stage73_consumers.json").read_text(
                encoding="utf-8"
            )
        )
        learnsets_zip = root / config["inputs"]["learnsets_zip"]["path"]
    else:
        learnsets_zip = args.learnsets_zip
        if not learnsets_zip.is_absolute():
            learnsets_zip = root / learnsets_zip
    try:
        result = build_contract(root, learnsets_zip)
        rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output is not None:
            output = args.output if args.output.is_absolute() else root / args.output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (ContractError, inventory.InventoryError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
