#!/usr/bin/env python3
"""Fail-closed cross-reference and reachability validator for acquisition content."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Iterable

INTERNAL_SPECIES_IDS = {252, 253, 254, 256, 282} | set(range(257, 277))
REQUIRED_TARGET_STATUSES = {"REQUIRED_BASE", "REQUIRED_VEGA_ORIGINAL"}
REQUIRED_ROUTE_STATUSES = REQUIRED_TARGET_STATUSES | {"REQUIRED_ENABLING_FORM"}


class ValidationError(ValueError):
    pass


def rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValidationError(f"missing file: {path}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def unique(items: Iterable[str], label: str) -> set[str]:
    values = list(items)
    require(len(values) == len(set(values)), f"duplicate {label}")
    return set(values)


def validate_unlocks(unlocks: list[dict[str, str]]) -> set[str]:
    by_key = {row["unlock_key"]: row for row in unlocks}
    require(len(by_key) == len(unlocks), "duplicate unlock_key")
    require("UNLOCK_NEW_GAME" in by_key, "UNLOCK_NEW_GAME missing")
    for row in unlocks:
        operator = row["operator"]
        require(operator in {"ROOT", "AND", "OR"}, f"bad unlock operator: {row}")
        prereqs = [value for value in row["prerequisite_keys"].split("|") if value]
        if operator == "ROOT":
            require(not prereqs, f"root has prerequisites: {row['unlock_key']}")
        for key in prereqs:
            require(key in by_key, f"unknown unlock prerequisite {key}")

    # Cycle detection over all declared prerequisite edges.
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(key: str) -> None:
        if key in visited:
            return
        require(key not in visiting, f"unlock cycle at {key}")
        visiting.add(key)
        for prereq in by_key[key]["prerequisite_keys"].split("|"):
            if prereq:
                visit(prereq)
        visiting.remove(key)
        visited.add(key)
    for key in by_key:
        visit(key)

    reachable = {key for key, row in by_key.items() if row["operator"] == "ROOT"}
    changed = True
    while changed:
        changed = False
        for key, row in by_key.items():
            if key in reachable:
                continue
            prereqs = [value for value in row["prerequisite_keys"].split("|") if value]
            good = all(value in reachable for value in prereqs) if row["operator"] == "AND" else any(value in reachable for value in prereqs)
            if good:
                reachable.add(key)
                changed = True
    require(reachable == set(by_key), f"unreachable unlocks: {sorted(set(by_key) - reachable)}")
    return reachable


def validate(package: Path) -> dict[str, object]:
    content = package / "content"
    manifests = package / "manifests"
    registry = rows(content / "collectible_species_registry.csv")
    routes = rows(content / "species_acquisition_routes.csv")
    events = rows(content / "acquisition_events.csv")
    hosts = rows(content / "acquisition_physical_hosts.csv")
    arcs = rows(content / "event_arcs.csv")
    unlocks = rows(content / "unlocks.csv")
    dialogues = rows(content / "acquisition_event_dialogue.csv")
    states = rows(content / "acquisition_event_states.csv")
    specials = rows(content / "special_event_catalog_125.csv")
    starters = rows(content / "starter_lab_catalog_24.csv")
    fossils = rows(content / "fossil_restoration_catalog_16.csv")
    trades = rows(content / "trade_alternative_catalog_30.csv")
    evolutions = rows(content / "evolution_requirements_553.csv")
    vega = rows(content / "vega_original_target_decisions_206.csv")
    release_events = rows(manifests / "release_ready_events.csv")
    allocation_requests = rows(manifests / "allocation_requests.csv")
    save_layout = rows(manifests / "save_layout.csv")
    current_audit = rows(content / "current_acquisition_audit_1216.csv")
    wild_corrections = rows(content / "wild_source_corrections.csv")
    vertical_slices = rows(package / "tests/representative_vertical_slices.csv")
    exact_cases = rows(package / "tests/exact_rom_acceptance_cases.csv")

    require(len(registry) == 1621, f"registry count {len(registry)} != 1621")
    require(len(routes) == 1621, f"route count {len(routes)} != 1621")
    require(len(specials) == 125, f"special count {len(specials)} != 125")
    require(len(starters) == 24, f"starter count {len(starters)} != 24")
    require(len(fossils) == 16, f"fossil count {len(fossils)} != 16")
    require(len(trades) == 30, f"trade count {len(trades)} != 30")
    require(len(evolutions) == 553, f"evolution count {len(evolutions)} != 553")
    require(len(vega) == 206, f"Vega review count {len(vega)} != 206")
    require(len(current_audit) == 1216, f"current audit count {len(current_audit)} != 1216")
    require(len(save_layout) == 8, f"save layout row count {len(save_layout)} != 8")
    require(len(wild_corrections) == 2, f"wild correction count {len(wild_corrections)} != 2")

    species_keys = unique((row["species_key"] for row in registry), "species_key")
    canonical_ids = unique((row["canonical_id"] for row in registry), "canonical_id")
    require(canonical_ids == {str(index) for index in range(1621)}, "canonical IDs must be 0..1620")
    registry_by_key = {row["species_key"]: row for row in registry}
    route_keys = unique((row["species_key"] for row in routes), "route species_key")
    require(route_keys == species_keys, "route/registry species sets differ")
    route_by_species = {row["species_key"]: row for row in routes}

    required = [row for row in registry if row["target_status"] in REQUIRED_TARGET_STATUSES]
    require(len(required) == 1206, f"completion target {len(required)} != 1206")
    require(sum(row["target_status"] == "REQUIRED_BASE" for row in registry) == 1025, "base target != 1025")
    require(sum(row["target_status"] == "REQUIRED_VEGA_ORIGINAL" for row in registry) == 181, "Vega target != 181")
    require(sum(row["target_status"] == "REQUIRED_ENABLING_FORM" for row in registry) == 10, "enabling forms != 10")
    require(sum(int(row["completion_weight"]) for row in registry) == 1206, "completion weight sum != 1206")

    required_route_species = {row["species_key"] for row in registry if row["target_status"] in REQUIRED_ROUTE_STATUSES}
    current_audit_keys = unique((row["species_key"] for row in current_audit), "current audit species_key")
    require(current_audit_keys == required_route_species, "current audit/required route species sets differ")
    audit_class_counts = Counter(row["current_audit_class"] for row in current_audit)
    require(audit_class_counts == {
        "EXISTING_ROM_WILD_OR_ECOLOGY": 581,
        "EXISTING_ROM_EVOLUTION_EDGE_TRIGGER_AUDIT": 451,
        "EVENT_GIFT_OR_ROUTE_AUDIT_REQUIRED": 184,
    }, f"current audit class counts differ: {dict(audit_class_counts)}")
    current_method_counts = Counter(row["current_method"] for row in current_audit)
    require(current_method_counts == {
        "ROM_WILD_TABLE": 567,
        "CONNECTED_ECOLOGY_RUNTIME": 14,
        "EXACT_EVOLUTION_TABLE_EDGE": 451,
        "NO_VERIFIED_WILD_OR_EVOLUTION_ENTRY": 184,
    }, f"current audit method counts differ: {dict(current_method_counts)}")
    for row in current_audit:
        method = row["current_method"]
        evidence = row["current_evidence"]
        if method == "ROM_WILD_TABLE":
            require("ROM_WILD:" in evidence, f"ROM wild audit evidence missing {row['species_key']}")
        elif method == "CONNECTED_ECOLOGY_RUNTIME":
            require("TOHOKU_ECOLOGY:" in evidence and "ROM_WILD:" not in evidence,
                    f"ecology-only audit evidence differs {row['species_key']}")
        elif method == "EXACT_EVOLUTION_TABLE_EDGE":
            require("analysis/CURRENT_ACQUISITION_COVERAGE_1231.csv" in evidence and "0x09F79290" in evidence,
                    f"evolution-edge audit evidence missing {row['species_key']}")
        else:
            require(method == "NO_VERIFIED_WILD_OR_EVOLUTION_ENTRY" and
                    "analysis/CURRENT_ACQUISITION_COVERAGE_1231.csv" in evidence,
                    f"no-entry audit evidence differs {row['species_key']}")

    expected_save_layout = {
        "ACQ_SAVE_HEADER": (0, 12, 4),
        "ACQ_COLLECTION_LEDGER_BITS": (12, 152, 1),
        "ACQ_EVENT_CLAIM_BITS": (164, 22, 1),
        "ACQ_BOUNDED_CLAIM_COUNTERS": (186, 1, 1),
        "ACQ_ALIGNMENT_PADDING": (187, 1, 1),
        "ACQ_EVOLUTION_COUNTERS": (188, 32, 4),
        "ACQ_PENDING_TRANSACTION": (220, 20, 4),
        "ACQ_SAVE_BLOCK_TOTAL": (0, 240, 4),
    }
    save_layout_keys = unique((row["field_key"] for row in save_layout), "save layout field_key")
    require(save_layout_keys == set(expected_save_layout), "save layout field set differs")
    for row in save_layout:
        observed = (int(row["offset_bytes"]), int(row["size_bytes"]), int(row["alignment"]))
        require(observed == expected_save_layout[row["field_key"]],
                f"save layout differs for {row['field_key']}: {observed}")

    for row in registry:
        required_route = row["target_status"] in REQUIRED_ROUTE_STATUSES
        route = route_by_species[row["species_key"]]
        require((row["route_required"] == "yes") == required_route,
                f"route_required mismatch {row['species_key']}")
        if required_route:
            require(route["method"] not in {"", "MISSING", "EXCLUDED"}, f"missing required route {row['species_key']}")
            require(route["runtime_status"] not in {"", "MISSING", "NOT_IN_COLLECTION_TARGET"}, f"bad runtime status {row['species_key']}")
        if int(row["canonical_id"]) in INTERNAL_SPECIES_IDS:
            require(not required_route, f"internal species is required {row['species_key']}")

    event_keys = unique((row["event_key"] for row in events), "event_key")
    host_keys = unique((row["host_key"] for row in hosts), "host_key")
    arc_keys = unique((row["event_arc"] for row in arcs), "event_arc")
    unlock_keys = validate_unlocks(unlocks)
    host_by_key = {row["host_key"]: row for row in hosts}
    for row in events:
        require(row["event_arc"] in arc_keys, f"unknown event arc {row['event_arc']}")
        require(row["host_key"] in host_keys, f"unknown event host {row['host_key']}")
        require(row["unlock_key"] in unlock_keys, f"unknown event unlock {row['unlock_key']}")
        require(row["battle_or_gift"] in {"CAPTURE", "GIFT", "EGG", "FOSSIL", "EVOLUTION_SUPPORT", "TRADE_EMULATOR", "SERVICE"}, f"bad event mode {row['event_key']}")
        for species_key in [value for value in row["target_species_keys"].split("|") if value]:
            require(species_key in species_keys, f"unknown event species {species_key}")
            require(int(registry_by_key[species_key]["canonical_id"]) not in INTERNAL_SPECIES_IDS,
                    f"internal species leaked into event {row['event_key']}")

    for host in hosts:
        if host["status"] == "READY_TO_SERIALIZE":
            require(host["event_kind"] == "OBJECT_REUSE", f"release host is not object reuse {host['host_key']}")
            require(host["physical_map_key"].startswith("KANTO_"), f"non-Kanto release host {host['host_key']}")
            require(int(host["object_count_before"]) == int(host["object_count_after"]), f"object count changed {host['host_key']}")
            require(int(host["object_count_before"]) <= 15, f"object+player would exceed 16 {host['host_key']}")
            require(int(host["object_delta"]) == 0, f"object delta not zero {host['host_key']}")
        elif host["status"] == "PHYSICAL_COORD_AUDIT_REQUIRED":
            require(host["x"] == host["y"] == "", "audit-required Tohoku coordinates must stay blank")

    release_event_keys = unique((row["event_key"] for row in release_events), "release event_key")
    expected_release_event_keys = {row["event_key"] for row in events if host_by_key[row["host_key"]]["status"] == "READY_TO_SERIALIZE" and row["runtime_status"] != "DESIGN_ONLY"}
    require(release_event_keys == expected_release_event_keys, "release manifest differs from ready-host event set")
    for row in release_events:
        require(host_by_key[row["host_key"]]["status"] == "READY_TO_SERIALIZE",
                f"non-ready host in release manifest {row['event_key']}")
    ready_host_keys = {row["host_key"] for row in hosts if row["status"] == "READY_TO_SERIALIZE"}
    require(all(any(event["host_key"] == host_key for event in events) for host_key in ready_host_keys),
            "READY_TO_SERIALIZE host has no event")

    slice_keys = unique((row["slice_key"] for row in vertical_slices), "vertical slice_key")
    require(len(slice_keys) == 7, f"vertical slice count {len(slice_keys)} != 7")
    for row in vertical_slices:
        require(row["event_key"] in event_keys, f"vertical slice references unknown event {row['event_key']}")
    exact_case_keys = unique((row["case_key"] for row in exact_cases), "exact acceptance case_key")
    require(exact_case_keys, "exact acceptance case catalog is empty")
    require({row["event_key"] for row in exact_cases} == event_keys, "exact acceptance cases do not cover every event")

    dialogue_counts = Counter(row["event_key"] for row in dialogues)
    state_counts = Counter(row["event_key"] for row in states)
    require(set(dialogue_counts) == event_keys, "dialogue event set differs")
    require(set(state_counts) == event_keys, "state event set differs")
    require(all(value == 9 for value in dialogue_counts.values()), "every event needs 9 dialogue states")
    require(all(value == 9 for value in state_counts.values()), "every event needs 9 FSM states")

    require(all(not row["address"] for row in allocation_requests), "raw allocation addresses must remain blank")
    require({row["allocation_name"] for row in allocation_requests} == {"acquisition_runtime", "acquisition_map_scripts"}, "named allocations differ")

    # New-game graph reachability.  Route availability is resolved by fixed point over
    # unlocks and species prerequisites.  Hosts are already validated separately.
    reachable_species: set[str] = set()
    changed = True
    while changed:
        changed = False
        for species_key, route in route_by_species.items():
            if species_key in reachable_species or registry_by_key[species_key]["target_status"] not in REQUIRED_ROUTE_STATUSES:
                continue
            if route["unlock_key"] and route["unlock_key"] not in unlock_keys:
                continue
            predecessor = route["prerequisite_species_key"]
            if predecessor and predecessor not in reachable_species:
                continue
            if route["method"] in {"MISSING", "EXCLUDED", "OPTIONAL_FORM_TRANSFORMATION"}:
                continue
            reachable_species.add(species_key)
            changed = True
    required_species = {row["species_key"] for row in registry if row["target_status"] in REQUIRED_ROUTE_STATUSES}
    require(reachable_species == required_species,
            f"new-game route graph unreachable: {sorted(required_species - reachable_species)[:30]}")

    # Known regression: internal Scyther ID 282 must not be a wild/event target.
    require(registry_by_key["SPECIES_KEY_SCYTHER"]["canonical_id"] == "255", "official Scyther canonical ID changed")
    internal_282 = next(row for row in registry if row["canonical_id"] == "282")
    require(internal_282["target_status"].startswith("INTERNAL_EXCLUDED"), "internal Scyther 282 not excluded")
    correction_keys = unique((row["correction_key"] for row in wild_corrections), "wild correction_key")
    require(correction_keys == {"WILD_FIX_SCYTHER_01_064_LAND", "WILD_FIX_SCYTHER_01_111_LAND"}, "wild correction keys differ")
    for row in wild_corrections:
        require(row["from_species_key"] == "SPECIES_KEY_VEGA_282", "wild correction source must be internal Scyther")
        require(row["to_species_key"] == "SPECIES_KEY_SCYTHER", "wild correction target must be official Scyther")
        require(row["from_canonical_id"] == "282" and row["to_canonical_id"] == "255", "wild correction IDs differ")
        require(row["encounter_kind"] == "LAND" and row["status"] == "REQUIRED_BEFORE_RELEASE", "wild correction policy differs")

    report = {
        "status": "PASS",
        "registry_rows": len(registry),
        "completion_target": len(required),
        "enabling_forms": 10,
        "events": len(events),
        "release_events": len(release_events),
        "release_hosts": sum(row["status"] == "READY_TO_SERIALIZE" for row in hosts),
        "specials": len(specials),
        "starters": len(starters),
        "fossils": len(fossils),
        "trade_edges": len(trades),
        "evolution_edges": len(evolutions),
        "reachable_required_or_enabling": len(reachable_species),
        "wild_source_corrections": len(wild_corrections),
        "current_audit_rows": len(current_audit),
        "strict_direct_rom_wild": current_method_counts["ROM_WILD_TABLE"],
        "strict_direct_ecology_only": current_method_counts["CONNECTED_ECOLOGY_RUNTIME"],
        "exact_edge_trigger_audit": current_method_counts["EXACT_EVOLUTION_TABLE_EDGE"],
        "event_integration_or_route_audit": current_method_counts["NO_VERIFIED_WILD_OR_EVOLUTION_ENTRY"],
        "save_block_bytes": expected_save_layout["ACQ_SAVE_BLOCK_TOTAL"][1],
        "exact_acceptance_cases": len(exact_cases),
        "vertical_slices": len(vertical_slices),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = validate(args.package.resolve())
    except (ValidationError, KeyError, ValueError) as error:
        print(f"acquisition validation failed: {error}", file=sys.stderr)
        return 1
    text = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
