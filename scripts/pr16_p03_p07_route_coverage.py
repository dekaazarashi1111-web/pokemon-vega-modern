#!/usr/bin/env python3
"""Validate and project the finite PR #16 P03/P07 route-coverage ledger.

This checkpoint deliberately separates three claims:
  * an implementation/consumer route has accepted evidence;
  * a P07-changed route is accepted on the 635fd890 parent candidate; and
  * that evidence has been transferred to the e630f7f1 successor candidate.

Only the last claim belongs to P08.  The script never relabels an old native run.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "pr16_p03_p07_route_coverage.v1"
P03_GAPS = [
    "P03_GENERIC_FORM_CHANGE_CARRY_PHYSICAL",
    "P03_FIXED_FORM_TRANSITION_PHYSICAL",
]
P07_PARENT = "635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e"
P08_SUCCESSOR = "e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CoverageError(ValueError):
    """Raised when the finite coverage ledger is internally inconsistent."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CoverageError(message)


def _route_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    routes = manifest["p03"]["route_groups"]
    index = {route["id"]: route for route in routes}
    _require(len(index) == len(routes), "duplicate P03 route-group id")
    return index


def _changed_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    changed = manifest["p07"]["change_surface"]["changed_by_p07"]
    index = {route["id"]: route for route in changed}
    _require(len(index) == len(changed), "duplicate P07 changed-path id")
    return index


def _walk_condition_objects(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if isinstance(value.get("id"), str):
            yield value
        for child in value.values():
            yield from _walk_condition_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_condition_objects(child)


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    _require(manifest.get("schema") == SCHEMA, f"schema must be {SCHEMA}")

    scope = manifest["candidate_scope"]
    _require(scope["p07_parent_candidate_sha256"] == P07_PARENT, "unexpected P07 parent candidate")
    _require(scope["latest_successor_candidate_sha256"] == P08_SUCCESSOR, "unexpected successor candidate")
    _require(scope["successor_transfer_condition_id"] == "FINAL_NATIVE_ACCEPTANCE", "P08 transfer owner changed")
    _require(scope["successor_transfer_is_route_gap"] is False, "successor transfer must not become a P03/P07 route gap")
    for name in ("p07_parent_candidate_sha256", "latest_successor_candidate_sha256"):
        _require(bool(SHA256_RE.fullmatch(scope[name])), f"invalid SHA-256: {name}")

    p03 = manifest["p03"]
    _require(p03["condition_id"] == "EVOLUTION_FORM_OTHER_EGG", "wrong P03 condition id")
    _require(p03["coverage_inventory_complete"] is True, "P03 inventory must be finite")
    _require(p03["physical_acceptance_complete"] is False, "P03 must stay open until two physical gaps pass")
    _require(p03["complete"] is False, "P03 must not be marked complete")
    _require(p03["remaining_physical_gap_ids"] == P03_GAPS, "P03 gap list must be exactly the two non-Rotom form owners")

    form = p03["form_inventory"]
    _require(form["generic_carry_routes"] + form["fixed_transition_routes"] + form["rotom_routes"] == form["routes"] == 70,
             "P03 form-route total must be 61 + 4 + 5 = 70")
    _require(form["species"] == 19, "P03 form species total must be 19")

    routes = _route_index(manifest)
    expected_routes = {
        "LEVEL_AND_EVOLUTION_LEARNING",
        "ORDINARY_DIRECT_EGG_DAYCARE",
        "SPECIAL_EGG_INHERITANCE",
        "NORMAL_AND_EGG_MOVE_MEMORY",
        "FORGETTING_AND_SAVE_VALIDATION",
        "MACHINE_AND_TUTOR_ARCHIVE",
        "SHARED_EGG_MOVE_MEMORY",
        "ROTOM_BESPOKE_FORM_TRANSITION",
        "GENERIC_FORM_CHANGE_CARRY",
        "FIXED_FORM_TRANSITION",
    }
    _require(set(routes) == expected_routes, "P03 route-group inventory changed")

    physical_gap_routes = [route for route in routes.values() if route["coverage"] == "PHYSICAL_GAP"]
    _require([route["gap_id"] for route in physical_gap_routes] == P03_GAPS,
             "only the generic and fixed non-Rotom form owners may remain as P03 physical gaps")
    for route in routes.values():
        if route["coverage"] != "PHYSICAL_GAP":
            _require("gap_id" not in route, f"accepted route unexpectedly has a gap id: {route['id']}")
            _require(bool(route.get("evidence")), f"accepted route lacks evidence: {route['id']}")

    ordinary = routes["ORDINARY_DIRECT_EGG_DAYCARE"]
    ordinary_evidence = ordinary["evidence"][0]
    _require(ordinary_evidence["run_id"] == 34434453733, "ordinary daycare must retain the accepted eight-case run")
    _require(ordinary_evidence["case_count"] == 8, "ordinary daycare evidence must retain all eight cases")
    for required_path in ("ordinary-deposit", "ordinary-claim", "native-hatch", "hatched-save-continue"):
        _require(required_path in ordinary_evidence["lifecycle"], f"ordinary daycare lifecycle missing {required_path}")

    shared = routes["SHARED_EGG_MOVE_MEMORY"]
    _require(shared["static_route_counts"] == {"receivers": 943, "rows": 5023, "shared_only_rows": 2751},
             "shared-egg static inventory changed")
    machine = routes["MACHINE_AND_TUTOR_ARCHIVE"]
    _require(machine["static_route_counts"]["machine"] + machine["static_route_counts"]["tutor"] == 26648,
             "machine/tutor route total changed")

    generic = routes["GENERIC_FORM_CHANGE_CARRY"]["form_inventory"]
    fixed = routes["FIXED_FORM_TRANSITION"]["form_inventory"]
    rotom = routes["ROTOM_BESPOKE_FORM_TRANSITION"]["form_inventory"]
    _require(generic["routes"] == 61 and generic["species"] == 10, "generic form inventory changed")
    _require(sum(generic["methods"].values()) == 61, "generic form method counts must sum to 61")
    _require(len(set(generic["species_keys"])) == 10, "generic form species list must contain 10 unique species")
    _require(fixed["routes"] == 4 and len(set(fixed["species_keys"])) == 4, "fixed transition inventory changed")
    _require(rotom["routes"] == 5 and rotom["species"] == 5, "Rotom route inventory changed")

    p07 = manifest["p07"]
    _require(p07["condition_id"] == "P07_REMAINING_ROUTE_ACCEPTANCE", "wrong P07 condition id")
    _require(p07["coverage_inventory_complete"] is True, "P07 inventory must be finite")
    _require(p07["physical_acceptance_complete_on_parent_candidate"] is True, "P07 changed paths must be accepted on parent")
    _require(p07["complete_on_parent_candidate"] is True, "P07 route acceptance must close on parent")
    _require(p07["successor_transfer_complete"] is False, "successor transfer must remain in P08")
    _require(p07["successor_transfer_owned_by"] == "P08:FINAL_NATIVE_ACCEPTANCE", "P07 transfer owner changed")
    _require(p07["remaining_physical_gap_ids"] == [], "P07 changed-path gap list must be empty")

    adopted = p07["static_reconciliation"]["adopted"]
    preserved = p07["static_reconciliation"]["preserved"]
    _require(adopted["level_up"] + adopted["egg"] + adopted["machine"] + adopted["tutor"] == adopted["total"] == 1073,
             "P07 adopted totals must be 450 + 254 + 179 + 190 = 1073")
    _require(preserved["level_up"] + preserved["egg"] == preserved["total"] == 499,
             "P07 preserved totals must be 310 + 189 = 499")
    _require(p07["static_reconciliation"]["missing_or_conflicting_rows"] == 0,
             "P07 reconciliation must have zero missing/conflicting rows")

    changed = _changed_index(manifest)
    _require(set(changed) == {"PRESERVED_LEVEL_ROWS", "PRESERVED_EGG_ROWS", "HAPPINY_COLLISION_ADAPTER"},
             "P07 changed surface must contain only preserved level, preserved egg, and Happiny adapter")
    _require(changed["PRESERVED_LEVEL_ROWS"]["rows"] == 310, "P07 preserved level count changed")
    _require(changed["PRESERVED_EGG_ROWS"]["rows"] == 189, "P07 preserved egg count changed")
    _require(changed["HAPPINY_COLLISION_ADAPTER"]["moves"] == [461, 464, 357], "Happiny adapter moves changed")
    for item in changed.values():
        _require(item["coverage"] == "ACCEPTED_NATIVE_ON_PARENT", f"P07 changed path is not accepted: {item['id']}")

    unchanged = p07["change_surface"]["unchanged_parent_content"]
    _require(sum(item["rows"] for item in unchanged) == 1073, "unchanged adopted rows must sum to 1073")
    _require(all(item["static_exact"] is True for item in unchanged), "every unchanged adopted family must remain statically exact")

    projection = manifest["remaining_projection"]
    _require(projection["EVOLUTION_FORM_OTHER_EGG"]["remaining_physical_gap_ids"] == P03_GAPS,
             "P03 remaining projection diverged from ledger")
    _require(projection["P07_REMAINING_ROUTE_ACCEPTANCE"]["remaining_physical_gap_ids"] == [],
             "P07 remaining projection must have no route gaps")
    _require(projection["P07_REMAINING_ROUTE_ACCEPTANCE"]["accepted_candidate_sha256"] == P07_PARENT,
             "P07 remaining projection points at wrong parent candidate")

    return {
        "status": "PASS",
        "schema": SCHEMA,
        "p03_remaining_physical_gap_ids": list(P03_GAPS),
        "p07_remaining_physical_gap_ids": [],
        "p07_parent_candidate_sha256": P07_PARENT,
        "p08_successor_candidate_sha256": P08_SUCCESSOR,
        "successor_transfer_owned_by": "P08:FINAL_NATIVE_ACCEPTANCE",
    }


def apply_remaining_projection(document: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Apply only the two condition projections, wherever their containing list lives."""
    projected = manifest["remaining_projection"]
    result = copy.deepcopy(document)
    seen: dict[str, int] = {key: 0 for key in projected}
    for condition in _walk_condition_objects(result):
        condition_id = condition.get("id")
        if condition_id in projected:
            condition.update(copy.deepcopy(projected[condition_id]))
            seen[condition_id] += 1
    _require(all(count == 1 for count in seen.values()), f"expected one matching condition for each projection, got {seen}")
    return result


def check_remaining_projection(document: dict[str, Any], manifest: dict[str, Any]) -> None:
    projected = manifest["remaining_projection"]
    found: dict[str, list[dict[str, Any]]] = {key: [] for key in projected}
    for condition in _walk_condition_objects(document):
        if condition.get("id") in found:
            found[condition["id"]].append(condition)
    _require(all(len(items) == 1 for items in found.values()),
             f"expected one matching condition for each projection, got { {key: len(items) for key, items in found.items()} }")
    for condition_id, fields in projected.items():
        condition = found[condition_id][0]
        for key, expected in fields.items():
            _require(condition.get(key) == expected, f"{condition_id}.{key} does not match finite coverage projection")


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    _require(isinstance(value, dict), f"JSON root must be an object: {path}")
    return value


def _dump(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("content/modernization/pr16_p03_p07_route_coverage.json"),
    )
    parser.add_argument("--check-remaining", type=Path)
    parser.add_argument("--apply-remaining", type=Path)
    parser.add_argument("--output", type=Path, help="optional JSON receipt path")
    args = parser.parse_args(argv)

    try:
        manifest = _load(args.manifest)
        receipt = validate_manifest(manifest)
        if args.check_remaining is not None:
            check_remaining_projection(_load(args.check_remaining), manifest)
            receipt["remaining_projection"] = "PASS"
        if args.apply_remaining is not None:
            remaining = _load(args.apply_remaining)
            updated = apply_remaining_projection(remaining, manifest)
            _dump(args.apply_remaining, updated)
            check_remaining_projection(updated, manifest)
            receipt["remaining_projection_applied"] = str(args.apply_remaining)
        if args.output is not None:
            _dump(args.output, receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0
    except (CoverageError, KeyError, TypeError, json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
