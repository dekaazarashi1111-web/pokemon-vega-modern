#!/usr/bin/env python3
"""Stage35 event authoring submission validator.

The packet is intentionally self-contained.  The validator uses only the
Python standard library; jsonschema is used when available, while all project
cross-reference and implementation constraints are checked here regardless.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


KEY_RE = re.compile(r"^(?:[A-Z][A-Z0-9_]*|NONE)$")
PLACEHOLDER_RE = re.compile(r"(?:\bTODO\b|\bTBD\b|PLACEHOLDER|未定|仮置き|要検討|あとで)", re.I)

OUTPUT_FILES = {
    "EVENT_BIBLE_JA.md",
    "event_plan.json",
    "dialogue.csv",
    "coverage.csv",
    "OPEN_QUESTIONS.md",
    "VALIDATION_REPORT.json",
}
DIALOGUE_HEADER = [
    "dialogue_key", "event_key", "speaker_actor_key", "usage", "text",
    "next_step_key", "notes",
]
COVERAGE_HEADER = [
    "coverage_key", "subject_kind", "subject_key", "coverage_status",
    "event_keys", "rationale",
]
DIALOGUE_USAGE = {
    "INTRO", "PROMPT", "ACCEPT", "DECLINE", "LOCKED", "ACTIVE",
    "COMPLETE", "FAILURE", "REVISIT", "FLAVOR", "SHOP", "SYSTEM",
}
COVERAGE_STATUS = {
    "NEW_EVENT", "EXISTING_CONTENT", "AUTO_UNLOCK", "NO_EVENT_JUSTIFIED",
}
REQUIRED_TEST_CATEGORIES = {
    "UNLOCK_BOUNDARY", "HAPPY_PATH", "REVISIT", "SAVE_RELOAD",
}
BRANCH_OPS = {"CHECK_CONDITION", "YES_NO"}
TERMINAL = {"END", "NONE"}


class ValidationFailure(RuntimeError):
    pass


def _csv(path: Path, expected: list[str], errors: list[str]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            header = list(reader.fieldnames or [])
            rows = list(reader)
    except OSError as exc:
        errors.append(f"{path.name}: read failed: {exc}")
        return []
    if header != expected:
        errors.append(f"{path.name}: header drift: {header!r}")
    return rows


def _catalog(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _split(value: str) -> list[str]:
    return [part for part in value.split("|") if part and part != "NONE"]


def _unique(rows: Iterable[dict[str, Any]], field: str, label: str,
            errors: list[str]) -> set[str]:
    values = [str(row.get(field, "")) for row in rows]
    duplicate = sorted(key for key, count in Counter(values).items() if count > 1)
    if "" in values:
        errors.append(f"{label}: missing {field}")
    if duplicate:
        errors.append(f"{label}: duplicate {field}: {duplicate[:12]}")
    return set(values)


def _require_key(value: object, label: str, errors: list[str]) -> str:
    text = str(value)
    if not KEY_RE.fullmatch(text):
        errors.append(f"{label}: invalid symbolic key {text!r}")
    return text


def _stable_hash(paths: Iterable[Path], base: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.as_posix()):
        digest.update(path.relative_to(base).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_catalogs(packet: Path) -> dict[str, Any]:
    catalogs = packet / "catalogs"
    maps = _catalog(catalogs / "maps.csv")
    progression = _catalog(catalogs / "progression.csv")
    qol = _catalog(catalogs / "qol_features.csv")
    trainers = _catalog(catalogs / "existing_kanto_trainers.csv")
    acquisition = _catalog(catalogs / "acquisition_hosts.csv")
    rewards = _catalog(catalogs / "reward_catalog.csv")
    services = _catalog(catalogs / "service_profiles.csv")
    graphics = _catalog(catalogs / "object_graphics_catalog.csv")
    object_hosts = _catalog(catalogs / "source_object_hosts.csv")
    bg_hosts = _catalog(catalogs / "bg_event_hosts.csv")
    coord_hosts = _catalog(catalogs / "coord_event_hosts.csv")
    states = _catalog(catalogs / "existing_state_keys.csv")
    charmap = json.loads((catalogs / "game_charmap.json").read_text(encoding="utf-8"))
    return {
        "maps": {row["map_key"]: row for row in maps},
        "logical_codes": {row["logical_code"] for row in maps},
        "unlocks": {row["unlock_key"]: row for row in progression},
        "safe_routes": {row["safe_route_key"] for row in progression},
        "required_gates": {
            row["unlock_key"] for row in progression
            if row.get("event_coverage_required") == "true"
        },
        "qol": {row["feature_key"]: row for row in qol},
        "trainers": {row["encounter_key"] for row in trainers},
        "acquisition": {row["host_key"] for row in acquisition},
        "rewards": {row["catalog_reward_key"]: row for row in rewards},
        "services": {row["service_profile_key"] for row in services},
        "graphics": {row["graphics_id"] for row in graphics},
        "object_hosts": {row["host_ref"]: row for row in object_hosts},
        "bg_hosts": {row["host_ref"]: row for row in bg_hosts},
        "coord_hosts": {row["host_ref"]: row for row in coord_hosts},
        "existing_states": {row["state_key"] for row in states},
        "charmap": charmap,
    }


def _validate_json_schema(plan: dict[str, Any], schema_path: Path,
                          errors: list[str], warnings: list[str]) -> None:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        warnings.append("jsonschema package unavailable; project-specific structural checks used")
        return
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(schema)
        for error in sorted(validator.iter_errors(plan), key=lambda item: list(item.path)):
            location = ".".join(str(value) for value in error.path) or "root"
            errors.append(f"event_plan.schema:{location}: {error.message}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"event_plan.schema: setup failed: {exc}")


def _token_width(text: str, charmap: dict[str, Any], label: str,
                 errors: list[str], *, max_lines: int, max_width: int) -> None:
    if "\n" in text or "\r" in text:
        errors.append(f"{label}: physical newline is forbidden; use literal \\n")
        return
    lines = text.split("\\n")
    if len(lines) > max_lines:
        errors.append(f"{label}: {len(lines)} lines exceeds {max_lines}")
    mapping = charmap.get("mapping", {})
    tokens = sorted((token for token in mapping if token and token not in {"$", "\\n", "\\p"}),
                    key=lambda token: (-len(token), token))
    for line_number, line in enumerate(lines, 1):
        cursor = 0
        width = 0
        while cursor < len(line):
            token = next((candidate for candidate in tokens if line.startswith(candidate, cursor)), None)
            if token is None:
                errors.append(f"{label}: unencodable text at line {line_number}: {line[cursor:]!r}")
                break
            width += 1
            cursor += len(token)
        if width > max_width:
            errors.append(f"{label}: line {line_number} width {width} exceeds {max_width}")


def _validate_placements(plan: dict[str, Any], catalogs: dict[str, Any],
                         errors: list[str]) -> set[str]:
    placements = plan.get("placements", [])
    keys = _unique(placements, "placement_key", "placements", errors)
    object_costs: dict[str, int] = defaultdict(int)
    claimed_hosts: dict[str, str] = {}
    allowed_policies = {
        "RESTORE_SOURCE_OBJECT", "REPOINT_SOURCE_BG", "REPOINT_SOURCE_COORD",
        "ALLOCATE_SAFE_TILE", "NO_PHYSICAL_HOST",
    }
    for row in placements:
        key = _require_key(row.get("placement_key"), "placement", errors)
        map_key = str(row.get("map_key"))
        if map_key not in catalogs["maps"]:
            errors.append(f"{key}: unresolved map {map_key}")
            continue
        policy = str(row.get("allocation_policy"))
        host_ref = str(row.get("host_ref"))
        try:
            cost = int(row.get("object_cost", -1))
        except (TypeError, ValueError):
            cost = -1
        if policy not in allowed_policies:
            errors.append(f"{key}: unsupported allocation policy {policy}")
            continue
        if policy == "RESTORE_SOURCE_OBJECT":
            host = catalogs["object_hosts"].get(host_ref)
            if not host or host.get("status") != "AVAILABLE_RESTORE":
                errors.append(f"{key}: object host unavailable: {host_ref}")
            else:
                if host.get("map_key") != map_key:
                    errors.append(f"{key}: object host belongs to {host.get('map_key')}")
                if row.get("graphics_id") != host.get("graphics_id"):
                    errors.append(f"{key}: restored graphics must equal host graphics")
                if row.get("movement_type") != host.get("movement_type"):
                    errors.append(f"{key}: restored movement must equal host movement")
            if cost != 1:
                errors.append(f"{key}: restored object cost must be 1")
        elif policy == "REPOINT_SOURCE_BG":
            host = catalogs["bg_hosts"].get(host_ref)
            if not host or host.get("status") != "AVAILABLE_REPOINT":
                errors.append(f"{key}: bg host unavailable: {host_ref}")
            elif host.get("map_key") != map_key:
                errors.append(f"{key}: bg host belongs to {host.get('map_key')}")
            if cost != 0 or row.get("graphics_id") != "NONE":
                errors.append(f"{key}: bg repoint must cost 0 and have graphics NONE")
        elif policy == "REPOINT_SOURCE_COORD":
            host = catalogs["coord_hosts"].get(host_ref)
            if not host or host.get("status") != "AVAILABLE_WITH_AUDIT":
                errors.append(f"{key}: coord host unavailable: {host_ref}")
            elif host.get("map_key") != map_key:
                errors.append(f"{key}: coord host belongs to {host.get('map_key')}")
            if cost != 0 or not row.get("collision_audit_required"):
                errors.append(f"{key}: coord repoint requires cost 0 and collision audit")
        elif policy == "ALLOCATE_SAFE_TILE":
            if host_ref != "ALLOCATE_SAFE" or cost != 1 or not row.get("collision_audit_required"):
                errors.append(f"{key}: safe allocation contract drift")
            if row.get("graphics_id") not in catalogs["graphics"]:
                errors.append(f"{key}: unknown graphics {row.get('graphics_id')}")
        else:
            if host_ref != "NONE" or cost != 0 or row.get("graphics_id") != "NONE" \
                    or row.get("movement_type") != "NONE":
                errors.append(f"{key}: no-physical-host fields must be NONE/0")
        if policy in {"RESTORE_SOURCE_OBJECT", "REPOINT_SOURCE_BG", "REPOINT_SOURCE_COORD"}:
            if host_ref in claimed_hosts:
                errors.append(f"{key}: host already claimed by {claimed_hosts[host_ref]}: {host_ref}")
            else:
                claimed_hosts[host_ref] = key
        if cost > 0:
            object_costs[map_key] += cost
    for map_key, cost in object_costs.items():
        free = int(catalogs["maps"][map_key]["free_object_slots"])
        if cost > free:
            errors.append(f"{map_key}: planned object cost {cost} exceeds free slots {free}")
    return keys


def _validate_conditions(plan: dict[str, Any], catalogs: dict[str, Any],
                         state_keys: set[str], errors: list[str]) -> set[str]:
    rows = plan.get("conditions", [])
    keys = _unique(rows, "condition_key", "conditions", errors)
    known_states = state_keys | catalogs["existing_states"]
    for row in rows:
        key = _require_key(row.get("condition_key"), "condition", errors)
        if not any(row.get(field) for field in ("all_of", "any_of", "none_of")):
            errors.append(f"{key}: empty condition")
        for field in ("all_of", "any_of", "none_of"):
            for term in row.get(field, []):
                kind = term.get("kind")
                ref = str(term.get("key"))
                if kind == "UNLOCK" and ref not in catalogs["unlocks"]:
                    errors.append(f"{key}: unknown unlock term {ref}")
                elif kind == "STATE" and ref not in known_states:
                    errors.append(f"{key}: unknown state term {ref}")
                elif kind == "QOL_FEATURE" and ref not in catalogs["qol"]:
                    errors.append(f"{key}: unknown QOL term {ref}")
                elif kind == "TRAINER_DEFEATED" and ref not in catalogs["trainers"]:
                    errors.append(f"{key}: unknown trainer term {ref}")
                elif kind == "ACQUISITION_CLAIMED" and ref not in catalogs["acquisition"]:
                    errors.append(f"{key}: unknown acquisition term {ref}")
                elif kind == "ITEM" and ref not in {
                    item.get("resource_key") for item in catalogs["rewards"].values()
                }:
                    errors.append(f"{key}: item term is outside reward catalog: {ref}")
                elif kind in {"PARTY_SIZE", "CAPTURE_COUNT"} and ref != "NONE":
                    errors.append(f"{key}: {kind} term key must be NONE")
    return keys


def _graph_can_end(start: str, edges: dict[str, list[str]]) -> bool:
    pending = [start]
    seen: set[str] = set()
    while pending:
        value = pending.pop()
        if value in TERMINAL:
            return True
        if value in seen:
            continue
        seen.add(value)
        pending.extend(edges.get(value, []))
    return False


def _validate_events(plan: dict[str, Any], catalogs: dict[str, Any],
                     refs: dict[str, set[str]], dialogue_keys: set[str],
                     dialogue_owner: dict[str, str], errors: list[str]) -> set[str]:
    events = plan.get("events", [])
    event_keys = _unique(events, "event_key", "events", errors)
    all_test_keys: list[str] = []
    referenced_dialogues: set[str] = set()
    for event in events:
        key = _require_key(event.get("event_key"), "event", errors)
        map_key = str(event.get("map_key"))
        map_row = catalogs["maps"].get(map_key)
        if not map_row:
            errors.append(f"{key}: unresolved map {map_key}")
        elif event.get("logical_code") != map_row.get("logical_code"):
            errors.append(f"{key}: logical_code does not match map catalog")
        for field, domain in (
            ("arc_key", refs["arcs"]), ("batch_key", refs["batches"]),
            ("placement_key", refs["placements"]), ("unlock_key", set(catalogs["unlocks"])),
        ):
            if event.get(field) not in domain:
                errors.append(f"{key}: unresolved {field} {event.get(field)}")
        if event.get("condition_key") != "NONE" and event.get("condition_key") not in refs["conditions"]:
            errors.append(f"{key}: unresolved condition {event.get('condition_key')}")
        if event.get("completion_state_key") != "NONE" and event.get("completion_state_key") not in refs["states"]:
            errors.append(f"{key}: unresolved completion state")
        if event.get("reward_key") != "NONE" and event.get("reward_key") not in refs["rewards"]:
            errors.append(f"{key}: unresolved reward")

        steps = event.get("steps", [])
        step_keys = _unique(steps, "step_key", f"{key}.steps", errors)
        edges: dict[str, list[str]] = {}
        operations = {str(row.get("op")) for row in steps}
        for step in steps:
            step_key = _require_key(step.get("step_key"), f"{key}.step", errors)
            op = str(step.get("op"))
            arg = str(step.get("arg_key"))
            next_key = str(step.get("next_step_key"))
            alt_key = str(step.get("alt_step_key"))
            if op == "SHOW_DIALOGUE" or op == "YES_NO":
                if arg not in dialogue_keys:
                    errors.append(f"{key}.{step_key}: unresolved dialogue {arg}")
                elif dialogue_owner.get(arg) != key:
                    errors.append(f"{key}.{step_key}: dialogue {arg} belongs to {dialogue_owner.get(arg)}")
                referenced_dialogues.add(arg)
            elif op == "CHECK_CONDITION" and arg not in refs["conditions"]:
                errors.append(f"{key}.{step_key}: unresolved condition {arg}")
            elif op == "SET_STATE" and arg not in refs["states"]:
                errors.append(f"{key}.{step_key}: unresolved state {arg}")
            elif op == "GIVE_REWARD" and arg not in refs["rewards"]:
                errors.append(f"{key}.{step_key}: unresolved reward {arg}")
            elif op == "START_TRAINER_BATTLE" and arg not in catalogs["trainers"]:
                errors.append(f"{key}.{step_key}: unresolved trainer encounter {arg}")
            elif op == "CALL_ACQUISITION_HOST" and arg not in catalogs["acquisition"]:
                errors.append(f"{key}.{step_key}: unresolved acquisition host {arg}")
            elif op == "OPEN_SERVICE" and arg not in catalogs["services"]:
                errors.append(f"{key}.{step_key}: unresolved service profile {arg}")
            elif op == "WARP_SAFE" and arg not in catalogs["safe_routes"]:
                errors.append(f"{key}.{step_key}: unresolved safe route {arg}")
            elif op in {"HEAL_PARTY", "END"} and arg != "NONE":
                errors.append(f"{key}.{step_key}: {op} arg must be NONE")
            if op == "END" and (next_key != "NONE" or alt_key != "NONE"):
                errors.append(f"{key}.{step_key}: END targets must be NONE")
            outgoing = ["END"] if op == "END" else [next_key]
            if op in BRANCH_OPS:
                if next_key == "NONE" or alt_key == "NONE" or next_key == alt_key:
                    errors.append(f"{key}.{step_key}: branch requires two distinct targets")
                outgoing.append(alt_key)
            elif alt_key != "NONE":
                errors.append(f"{key}.{step_key}: alt target only valid for branch op")
            for target in outgoing:
                if target not in step_keys | TERMINAL:
                    errors.append(f"{key}.{step_key}: unresolved step target {target}")
            edges[step_key] = outgoing
        if steps:
            start = str(steps[0].get("step_key"))
            reachable: set[str] = set()
            pending = deque([start])
            while pending:
                current = pending.popleft()
                if current in reachable or current in TERMINAL:
                    continue
                reachable.add(current)
                pending.extend(edges.get(current, []))
            unreachable = sorted(step_keys - reachable)
            if unreachable:
                errors.append(f"{key}: unreachable steps {unreachable}")
            if not _graph_can_end(start, edges):
                errors.append(f"{key}: step graph has no reachable END")
        categories = {row.get("category") for row in event.get("acceptance_tests", [])}
        all_test_keys.extend(str(row.get("test_key", "")) for row in event.get("acceptance_tests", []))
        missing = sorted(REQUIRED_TEST_CATEGORIES - categories)
        if missing:
            errors.append(f"{key}: missing acceptance categories {missing}")
        if "GIVE_REWARD" in operations and "BAG_FULL" not in categories:
            errors.append(f"{key}: reward event requires BAG_FULL acceptance test")
        if "START_TRAINER_BATTLE" in operations and "BATTLE_LOSS" not in categories:
            errors.append(f"{key}: battle event requires BATTLE_LOSS acceptance test")
        if "CALL_ACQUISITION_HOST" in operations and "PARTY_PC_FULL" not in categories:
            errors.append(f"{key}: acquisition event requires PARTY_PC_FULL acceptance test")
        if "YES_NO" in operations and "DECLINE" not in categories:
            errors.append(f"{key}: choice event requires DECLINE acceptance test")
        if operations & {"SET_STATE", "GIVE_REWARD", "START_TRAINER_BATTLE",
                         "CALL_ACQUISITION_HOST"} and "RESET" not in categories:
            errors.append(f"{key}: stateful event requires RESET acceptance test")
        if event.get("result_policy") == "NO_BATTLE" and operations & {
            "START_TRAINER_BATTLE", "CALL_ACQUISITION_HOST"
        }:
            errors.append(f"{key}: NO_BATTLE conflicts with battle/acquisition step")
        if event.get("result_policy") == "WIN_REQUIRED" and "START_TRAINER_BATTLE" not in operations:
            errors.append(f"{key}: WIN_REQUIRED requires START_TRAINER_BATTLE")
        if event.get("result_policy") == "ACQUISITION_TRANSACTION" \
                and "CALL_ACQUISITION_HOST" not in operations:
            errors.append(f"{key}: ACQUISITION_TRANSACTION requires CALL_ACQUISITION_HOST")
        if event.get("repeatability") in {"ONCE", "STATEFUL"} \
                and event.get("completion_state_key") == "NONE":
            errors.append(f"{key}: one-time/stateful event requires completion state")
        has_reward = event.get("reward_key") != "NONE"
        if has_reward != ("GIVE_REWARD" in operations):
            errors.append(f"{key}: reward_key and GIVE_REWARD step must agree")
        if event.get("completion_state_key") != "NONE" \
                and event.get("completion_state_key") not in {
                    str(step.get("arg_key")) for step in steps if step.get("op") == "SET_STATE"
                }:
            errors.append(f"{key}: completion state is never written")
    duplicates = sorted(key for key, count in Counter(all_test_keys).items() if count > 1)
    if "" in all_test_keys:
        errors.append("acceptance tests: missing test_key")
    if duplicates:
        errors.append(f"acceptance tests: duplicate test_key: {duplicates[:12]}")
    unused_dialogues = sorted(dialogue_keys - referenced_dialogues)
    if unused_dialogues:
        errors.append(f"dialogue: rows not referenced by event steps: {unused_dialogues[:12]}")
    return event_keys


def validate(packet: Path, submission: Path, *, allow_template: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        catalogs = _load_catalogs(packet)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        return {"schema_version": 1, "status": "FAIL", "errors": [f"catalog load failed: {exc}"],
                "warnings": [], "counts": {}}

    if not submission.is_dir():
        errors.append(f"submission directory not found: {submission}")
        files: set[str] = set()
    else:
        files = {path.name for path in submission.iterdir() if path.is_file()}
        directories = [path.name for path in submission.iterdir() if path.is_dir()]
        if directories:
            errors.append(f"submission contains subdirectories: {directories}")
    missing = sorted((OUTPUT_FILES - {"VALIDATION_REPORT.json"}) - files)
    extra = sorted(files - OUTPUT_FILES)
    if missing:
        errors.append(f"submission missing files: {missing}")
    if extra:
        errors.append(f"submission has extra files: {extra}")

    try:
        plan = json.loads((submission / "event_plan.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        plan = {}
        errors.append(f"event_plan.json: {exc}")
    _validate_json_schema(plan, packet / "schemas/event_plan.schema.json", errors, warnings)

    dialogues = _csv(submission / "dialogue.csv", DIALOGUE_HEADER, errors)
    coverage = _csv(submission / "coverage.csv", COVERAGE_HEADER, errors)
    dialogue_keys = _unique(dialogues, "dialogue_key", "dialogue", errors)
    coverage_keys = _unique(coverage, "coverage_key", "coverage", errors)
    del coverage_keys

    states = plan.get("states", []) if isinstance(plan, dict) else []
    state_keys = _unique(states, "state_key", "states", errors)
    for row in states:
        key = _require_key(row.get("state_key"), "state", errors)
        if key != "NONE" and not key.startswith("STATE_KEY_EVENT_"):
            errors.append(f"{key}: new state must start STATE_KEY_EVENT_")
        if row.get("storage_policy") == "DERIVED" and row.get("write_policy") != "DERIVED_ONLY":
            errors.append(f"{key}: derived state must use DERIVED_ONLY")
        if row.get("storage_policy") != "DERIVED" and not row.get("save_reload_required"):
            errors.append(f"{key}: persisted state must require save/reload coverage")
        try:
            if int(row.get("initial_value", 0)) > int(row.get("max_value", 0)):
                errors.append(f"{key}: initial_value exceeds max_value")
        except (TypeError, ValueError):
            errors.append(f"{key}: state values must be integers")

    arc_keys = _unique(plan.get("arcs", []), "arc_key", "arcs", errors)
    batch_keys = _unique(plan.get("batches", []), "batch_key", "batches", errors)
    placement_keys = _validate_placements(plan, catalogs, errors)
    condition_keys = _validate_conditions(plan, catalogs, state_keys, errors)
    reward_rows = plan.get("rewards", [])
    reward_keys = _unique(reward_rows, "reward_key", "rewards", errors)
    for row in reward_rows:
        key = _require_key(row.get("reward_key"), "reward", errors)
        catalog_key = str(row.get("catalog_reward_key"))
        catalog_row = catalogs["rewards"].get(catalog_key)
        if not catalog_row or catalog_row.get("use_policy") != "GRANT_ALLOWED":
            errors.append(f"{key}: reward catalog entry is not grant-allowed: {catalog_key}")
        elif (
            str(row.get("quantity")) != str(catalog_row.get("quantity"))
            or row.get("unlock_key") != catalog_row.get("unlock_key")
        ):
            errors.append(f"{key}: quantity/unlock must equal reward catalog entry")
        if row.get("unlock_key") not in catalogs["unlocks"]:
            errors.append(f"{key}: unresolved unlock {row.get('unlock_key')}")
        if row.get("repeatability") in {"ONCE", "LIMITED_REPEATABLE"}:
            if row.get("claim_state_key") not in state_keys:
                errors.append(f"{key}: one-time reward requires a new claim state")
        elif row.get("claim_state_key") != "NONE":
            errors.append(f"{key}: repeatable/none reward must not have a claim state")

    actor_rows = plan.get("actors", [])
    actor_keys = _unique(actor_rows, "actor_key", "actors", errors)
    for row in actor_rows:
        key = _require_key(row.get("actor_key"), "actor", errors)
        if key != "NONE" and not key.startswith("ACTOR_KEY_EVENT_"):
            errors.append(f"{key}: new actor must start ACTOR_KEY_EVENT_")
        if row.get("graphics_id") not in catalogs["graphics"] | {"NONE"}:
            errors.append(f"{key}: unresolved graphics {row.get('graphics_id')}")
        placement = row.get("placement_key")
        if placement != "NONE" and placement not in placement_keys:
            errors.append(f"{key}: unresolved placement {placement}")
        if row.get("home_map_key") != "NONE" and row.get("home_map_key") not in catalogs["maps"]:
            errors.append(f"{key}: unresolved home map")
        _token_width(str(row.get("display_name_game", "")), catalogs["charmap"],
                     f"{key}.display_name_game", errors, max_lines=1, max_width=10)

    dialogue_owner: dict[str, str] = {}
    event_steps = {
        str(event.get("event_key")): {
            str(step.get("step_key")) for step in event.get("steps", [])
        }
        for event in plan.get("events", [])
    }
    for row in dialogues:
        key = _require_key(row.get("dialogue_key"), "dialogue", errors)
        event_key = str(row.get("event_key"))
        dialogue_owner[key] = event_key
        if event_key not in {str(item.get("event_key")) for item in plan.get("events", [])}:
            errors.append(f"{key}: unresolved event {event_key}")
        if row.get("speaker_actor_key") not in actor_keys | {"ACTOR_KEY_NARRATION", "ACTOR_KEY_SYSTEM"}:
            errors.append(f"{key}: unresolved speaker {row.get('speaker_actor_key')}")
        if row.get("usage") not in DIALOGUE_USAGE:
            errors.append(f"{key}: invalid usage {row.get('usage')}")
        _token_width(row.get("text", ""), catalogs["charmap"], key, errors,
                     max_lines=int(catalogs["charmap"].get("max_message_lines", 2)),
                     max_width=int(catalogs["charmap"].get("max_line_glyphs", 18)))
        target = str(row.get("next_step_key"))
        if target not in event_steps.get(event_key, set()) | TERMINAL:
            errors.append(f"{key}: unresolved next_step_key {target}")

    refs = {
        "arcs": arc_keys,
        "batches": batch_keys,
        "placements": placement_keys,
        "conditions": condition_keys,
        "states": state_keys,
        "rewards": reward_keys,
    }
    event_keys = _validate_events(
        plan, catalogs, refs, dialogue_keys, dialogue_owner, errors
    )

    for arc in plan.get("arcs", []):
        key = str(arc.get("arc_key"))
        listed = set(arc.get("event_keys", []))
        actual = {event["event_key"] for event in plan.get("events", []) if event.get("arc_key") == key}
        if listed != actual:
            errors.append(f"{key}: arc event_keys differ from event assignments")
        completion = arc.get("completion_state_key")
        if completion != "NONE" and completion not in state_keys:
            errors.append(f"{key}: unresolved completion state")
        if arc.get("start_unlock_key") not in catalogs["unlocks"]:
            errors.append(f"{key}: unresolved start unlock")

    batch_graph: dict[str, list[str]] = {}
    for batch in plan.get("batches", []):
        key = str(batch.get("batch_key"))
        listed = set(batch.get("event_keys", []))
        actual = {event["event_key"] for event in plan.get("events", []) if event.get("batch_key") == key}
        if listed != actual:
            errors.append(f"{key}: batch event_keys differ from event assignments")
        if not allow_template and not 5 <= len(listed) <= 15:
            errors.append(f"{key}: batch must contain 5..15 events")
        if not set(batch.get("map_keys", [])) >= {
            event["map_key"] for event in plan.get("events", []) if event.get("batch_key") == key
        }:
            errors.append(f"{key}: batch map_keys incomplete")
        dependencies = list(batch.get("depends_on", []))
        if any(value not in batch_keys for value in dependencies):
            errors.append(f"{key}: unresolved batch dependency")
        batch_graph[key] = dependencies
    visiting: set[str] = set()
    done: set[str] = set()
    def visit(value: str) -> None:
        if value in visiting:
            errors.append(f"batch dependency cycle at {value}")
            return
        if value in done:
            return
        visiting.add(value)
        for parent in batch_graph.get(value, []):
            visit(parent)
        visiting.remove(value)
        done.add(value)
    for value in batch_graph:
        visit(value)
    if not allow_template:
        pilot = next((row for row in plan.get("batches", [])
                      if row.get("batch_key") == "BATCH_KEY_PILOT_VERMILION"), None)
        if not pilot or not 5 <= len(pilot.get("event_keys", [])) <= 10 or pilot.get("depends_on"):
            errors.append("BATCH_KEY_PILOT_VERMILION must be an independent 5..10-event first batch")
        categories = Counter(str(row.get("category")) for row in plan.get("arcs", []))
        if categories["MAIN"] < 1:
            errors.append("design quality: at least one MAIN arc is required")
        if categories["CERTIFICATION"] < 8:
            errors.append("design quality: eight CERTIFICATION arcs are required")
        if not 8 <= categories["SIDEQUEST"] <= 12:
            errors.append("design quality: SIDEQUEST arcs must be 8..12")
        if len(plan.get("events", [])) < 32:
            errors.append("design quality: at least 32 implementation events are required")
        if len(plan.get("batches", [])) < 3:
            errors.append("design quality: at least three implementation batches are required")

    required_coverage = (
        {("LOGICAL_LOCATION", f"K{value:02d}") for value in range(1, 48)}
        | {("QOL_FEATURE", key) for key in catalogs["qol"]}
        | {("PROGRESSION_GATE", key) for key in catalogs["required_gates"]}
    )
    seen_coverage: set[tuple[str, str]] = set()
    for row in coverage:
        subject = (row.get("subject_kind", ""), row.get("subject_key", ""))
        if subject in seen_coverage:
            errors.append(f"coverage duplicate subject: {subject}")
        seen_coverage.add(subject)
        status = row.get("coverage_status")
        if allow_template and status == "TEMPLATE_TODO":
            continue
        if status not in COVERAGE_STATUS:
            errors.append(f"coverage {subject}: invalid status {status}")
        keys = set(_split(row.get("event_keys", "")))
        if not keys <= event_keys:
            errors.append(f"coverage {subject}: unresolved event keys {sorted(keys - event_keys)}")
        if status == "NEW_EVENT" and not keys:
            errors.append(f"coverage {subject}: NEW_EVENT requires event_keys")
        if not row.get("rationale", "").strip():
            errors.append(f"coverage {subject}: rationale required")
        if not allow_template and subject[0] == "QOL_FEATURE":
            requirement = catalogs["qol"].get(subject[1], {}).get("event_design_requirement")
            if requirement == "REQUIRED_SIMPLE_EVENT" and status not in {
                "NEW_EVENT", "EXISTING_CONTENT"
            }:
                errors.append(f"coverage {subject}: SIMPLE_EVENT cannot be {status}")
        if not allow_template and subject[0] == "PROGRESSION_GATE" \
                and status not in {"NEW_EVENT", "EXISTING_CONTENT"}:
            errors.append(f"coverage {subject}: required gate needs event/content ownership")
    if required_coverage != seen_coverage:
        errors.append(
            f"coverage subjects mismatch: missing={sorted(required_coverage-seen_coverage)[:12]} "
            f"extra={sorted(seen_coverage-required_coverage)[:12]}"
        )

    try:
        bible = (submission / "EVENT_BIBLE_JA.md").read_text(encoding="utf-8")
        questions = (submission / "OPEN_QUESTIONS.md").read_text(encoding="utf-8")
    except OSError as exc:
        bible, questions = "", ""
        errors.append(f"markdown output read failed: {exc}")
    if not allow_template:
        if plan.get("design_status") != "IMPLEMENTATION_READY":
            errors.append("design_status must be IMPLEMENTATION_READY")
        if plan.get("open_questions"):
            errors.append("event_plan.open_questions must be empty")
        expected_questions = "# Open questions\n\nなし。実装に必要な判断はevent_plan.jsonのassumptionsへ記録済み。\n"
        if questions.replace("\r\n", "\n") != expected_questions:
            errors.append("OPEN_QUESTIONS.md must contain the exact no-open-questions statement")
        for key in sorted(arc_keys | batch_keys):
            if key not in bible:
                errors.append(f"EVENT_BIBLE_JA.md does not mention {key}")
        for path in [submission / name for name in OUTPUT_FILES - {"VALIDATION_REPORT.json"}]:
            if path.is_file() and PLACEHOLDER_RE.search(path.read_text(encoding="utf-8")):
                errors.append(f"{path.name}: placeholder text remains")

    input_files = [submission / name for name in OUTPUT_FILES - {"VALIDATION_REPORT.json"}
                   if (submission / name).is_file()]
    counts = {
        "arcs": len(plan.get("arcs", [])),
        "states": len(states),
        "actors": len(actor_rows),
        "placements": len(plan.get("placements", [])),
        "conditions": len(plan.get("conditions", [])),
        "rewards": len(reward_rows),
        "events": len(plan.get("events", [])),
        "dialogues": len(dialogues),
        "batches": len(plan.get("batches", [])),
        "coverage_rows": len(coverage),
        "open_questions": len(plan.get("open_questions", [])) if isinstance(plan, dict) else -1,
    }
    return {
        "schema_version": 1,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "counts": counts,
        "submission_sha256": _stable_hash(input_files, submission) if input_files else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("submission", type=Path)
    parser.add_argument("--packet-root", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-template", action="store_true")
    args = parser.parse_args()
    packet = (args.packet_root or Path(__file__).resolve().parents[1]).resolve()
    submission = args.submission.resolve()
    report = validate(packet, submission, allow_template=args.allow_template)
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_bytes(raw)
    sys.stdout.buffer.write(raw)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
