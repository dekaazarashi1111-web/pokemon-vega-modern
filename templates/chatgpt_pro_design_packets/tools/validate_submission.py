#!/usr/bin/env python3
"""ChatGPT Pro設計パケット共通submission validator。

パケット内のPACKET_SPEC.jsonを正本として、返却物のファイル集合、CSV schema、
symbolic reference、coverage、個別機能契約を検証する。外部packageは不要。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


KEY_RE = re.compile(r"^(?:[A-Z][A-Z0-9_]*|NONE)$")
PLACEHOLDER_RE = re.compile(
    r"(?:\bTODO\b|\bTBD\b|\bPLACEHOLDER\b|未定(?:$|[、。\s])|要検討|仮置き|あとで決め)",
    re.IGNORECASE,
)
OPEN_QUESTIONS_TEXT = "# Open questions\n\nなし。実装に必要な判断はすべて確定済み。\n"
GENERATED_FILES = {"VALIDATION_REPORT.json", "SUBMISSION_MANIFEST.json"}
FORBIDDEN_SUFFIXES = {
    ".gba", ".sav", ".sa1", ".sa2", ".sgm", ".ips", ".ups", ".bps",
    ".exe", ".dll", ".so", ".dylib", ".7z", ".rar",
}


class ValidationError(RuntimeError):
    pass


def _stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _fingerprint(paths: Iterable[Path], base: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(base).as_posix()):
        digest.update(path.relative_to(base).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _read_csv(path: Path, expected: list[str], errors: list[str]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            actual = list(reader.fieldnames or [])
            rows = list(reader)
    except OSError as exc:
        errors.append(f"{path.name}: read failed: {exc}")
        return []
    if actual != expected:
        errors.append(f"{path.name}: header drift: {actual!r} != {expected!r}")
    return rows


def _split_refs(value: str, separator: str | None) -> list[str]:
    if separator:
        return [part for part in value.split(separator) if part]
    return [value]


def _catalog_sets(packet: Path, spec: dict[str, Any], errors: list[str]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for name, model in spec.get("catalog_sets", {}).items():
        path = packet / model["path"]
        try:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
        except OSError as exc:
            errors.append(f"catalog {name}: read failed: {exc}")
            result[name] = set()
            continue
        field = model["field"]
        values = {row.get(field, "") for row in rows}
        values.discard("")
        if not values:
            errors.append(f"catalog {name}: empty field {field}")
        result[name] = values
    return result


def _check_text(path: Path, errors: list[str], *, min_bytes: int = 1) -> None:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"{path.name}: UTF-8 read failed: {exc}")
        return
    if len(raw) < min_bytes:
        errors.append(f"{path.name}: too small ({len(raw)} < {min_bytes})")
    match = PLACEHOLDER_RE.search(text)
    if match:
        errors.append(f"{path.name}: placeholder remains: {match.group(0)!r}")


def _validate_csv(
    path: Path,
    model: dict[str, Any],
    catalogs: dict[str, set[str]],
    errors: list[str],
) -> list[dict[str, str]]:
    rows = _read_csv(path, model["header"], errors)
    minimum = int(model.get("min_rows", 0))
    maximum = model.get("max_rows")
    if len(rows) < minimum:
        errors.append(f"{path.name}: rows {len(rows)} < {minimum}")
    if maximum is not None and len(rows) > int(maximum):
        errors.append(f"{path.name}: rows {len(rows)} > {maximum}")

    for fields in model.get("unique", []):
        values = [tuple(row.get(field, "") for field in fields) for row in rows]
        duplicates = [value for value, count in Counter(values).items() if count > 1]
        if duplicates:
            errors.append(f"{path.name}: duplicate {fields}: {duplicates[:8]}")

    allowed = model.get("allowed", {})
    integer_ranges = model.get("integer_ranges", {})
    references = model.get("references", {})
    required_nonempty = set(model.get("required_nonempty", []))
    symbolic_fields = set(model.get("symbolic_fields", []))
    for line, row in enumerate(rows, 2):
        for field in required_nonempty:
            if not row.get(field, "").strip():
                errors.append(f"{path.name}:{line}: {field} is empty")
        for field in symbolic_fields:
            value = row.get(field, "")
            if value and not KEY_RE.fullmatch(value):
                errors.append(f"{path.name}:{line}: invalid symbolic key {field}={value!r}")
        for field, options in allowed.items():
            if row.get(field, "") not in options:
                errors.append(
                    f"{path.name}:{line}: {field}={row.get(field)!r} not in {options}"
                )
        for field, bounds in integer_ranges.items():
            try:
                value = int(row.get(field, ""))
            except ValueError:
                errors.append(f"{path.name}:{line}: {field} is not integer")
                continue
            low, high = int(bounds[0]), int(bounds[1])
            if not low <= value <= high:
                errors.append(f"{path.name}:{line}: {field} {value} outside {low}..{high}")
        for field, ref in references.items():
            separator = ref.get("separator")
            allow = set(ref.get("allow", []))
            known = catalogs.get(ref["catalog"], set()) | allow
            for value in _split_refs(row.get(field, ""), separator):
                if value not in known:
                    errors.append(f"{path.name}:{line}: unresolved {field}={value!r}")
        match = PLACEHOLDER_RE.search(" ".join(row.values()))
        if match:
            errors.append(f"{path.name}:{line}: placeholder remains: {match.group(0)!r}")
    return rows


def _validate_json(path: Path, model: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.name}: JSON read failed: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.name}: root must be object")
        return {}
    for field in model.get("required_top_level", []):
        if field not in value:
            errors.append(f"{path.name}: missing top-level {field}")
    if model.get("implementation_ready"):
        if value.get("design_status") != "IMPLEMENTATION_READY":
            errors.append(f"{path.name}: design_status must be IMPLEMENTATION_READY")
        if value.get("open_questions") != []:
            errors.append(f"{path.name}: open_questions must be []")
    text = json.dumps(value, ensure_ascii=False)
    match = PLACEHOLDER_RE.search(text)
    if match:
        errors.append(f"{path.name}: placeholder remains: {match.group(0)!r}")
    return value


def _coverage_checks(
    spec: dict[str, Any],
    rows_by_file: dict[str, list[dict[str, str]]],
    catalogs: dict[str, set[str]],
    errors: list[str],
) -> None:
    for model in spec.get("coverage", []):
        rows = rows_by_file.get(model["output"], [])
        actual = {row.get(model["output_field"], "") for row in rows}
        actual.discard("")
        expected = catalogs.get(model["catalog"], set())
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing:
            errors.append(
                f"{model['output']}: coverage missing {model['catalog']}: {missing[:16]}"
            )
        if model.get("exact", True) and extra:
            errors.append(
                f"{model['output']}: coverage extra for {model['catalog']}: {extra[:16]}"
            )


def _load_catalog_rows(packet: Path, relative: str) -> list[dict[str, str]]:
    with (packet / relative).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _check_dialogue(
    packet: Path,
    rows: list[dict[str, str]],
    errors: list[str],
) -> None:
    path = packet / "catalogs/game_charmap.json"
    if not path.is_file():
        return
    charmap = json.loads(path.read_text(encoding="utf-8"))
    mapping = charmap.get("mapping", {})
    tokens = sorted(
        (token for token in mapping if token and token not in {"$", "\\n", "\\p"}),
        key=lambda token: (-len(token), token),
    )
    for index, row in enumerate(rows, 2):
        text = row.get("text", "")
        if "\n" in text or "\r" in text:
            errors.append(f"dialogue.csv:{index}: physical newline is forbidden")
            continue
        lines = text.split("\\n")
        if len(lines) > 2:
            errors.append(f"dialogue.csv:{index}: more than two lines")
        for line_no, line in enumerate(lines, 1):
            cursor = 0
            width = 0
            while cursor < len(line):
                token = next((item for item in tokens if line.startswith(item, cursor)), None)
                if token is None:
                    errors.append(
                        f"dialogue.csv:{index}: unencodable at line {line_no}: {line[cursor:]!r}"
                    )
                    break
                cursor += len(token)
                width += 1
            if width > 18:
                errors.append(f"dialogue.csv:{index}: line {line_no} width {width} > 18")


def _custom_move(
    packet: Path,
    rows: dict[str, list[dict[str, str]]],
    catalogs: dict[str, set[str]],
    errors: list[str],
) -> None:
    level_rows = rows.get("level_up_final.csv", [])
    by_species: dict[str, list[int]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for row in level_rows:
        species = row.get("species_key", "")
        try:
            order = int(row.get("order", ""))
        except ValueError:
            continue
        by_species[species].append(order)
        key = (species, row.get("level", ""), row.get("move_key", ""))
        if key in seen:
            errors.append(f"level_up_final.csv: duplicate species/level/move {key}")
        seen.add(key)
    for species, orders in by_species.items():
        if sorted(orders) != list(range(1, len(orders) + 1)):
            errors.append(f"level_up_final.csv: non-contiguous order for {species}")

    slot_rows = _load_catalog_rows(packet, "catalogs/tm_tutor_slots.csv")
    slots = {row["slot_key"]: row for row in slot_rows}
    for line, row in enumerate(rows.get("tm_tutor_changes.csv", []), 2):
        slot = slots.get(row.get("slot_key", ""))
        if slot and row.get("move_key") != slot.get("move_key"):
            errors.append(
                f"tm_tutor_changes.csv:{line}: move_key differs from slot {row.get('slot_key')}"
            )

    for line, row in enumerate(rows.get("wild_initial_moves_final.csv", []), 2):
        values = [row.get(f"move{index}_key", "") for index in range(1, 5)]
        if len(set(values)) != 4:
            errors.append(f"wild_initial_moves_final.csv:{line}: four moves must be unique")

    for line, row in enumerate(rows.get("form_policy_final.csv", []), 2):
        action = row.get("implementation_action")
        canonical = row.get("canonical_species_key")
        if action == "NO_CANONICAL_ROW" and canonical != "NONE":
            errors.append(f"form_policy_final.csv:{line}: NO_CANONICAL_ROW requires NONE")
        if action != "NO_CANONICAL_ROW" and canonical not in catalogs.get("species", set()):
            errors.append(f"form_policy_final.csv:{line}: canonical species is required")


def _custom_factory(
    rows: dict[str, list[dict[str, str]]],
    spec: dict[str, Any],
    errors: list[str],
) -> None:
    modes = rows.get("mode_matrix.csv", [])
    slots: list[int] = []
    for row in modes:
        try:
            slots.append(int(row.get("save_streak_slot", "")))
        except ValueError:
            continue
        try:
            round_count = int(row.get("round_battle_count", ""))
            milestone = int(row.get("max_milestone", ""))
        except ValueError:
            continue
        if milestone < round_count or milestone % round_count:
            errors.append(
                f"mode_matrix.csv: {row.get('mode_key')} milestone must be a round multiple"
            )
    if len(slots) != len(set(slots)):
        errors.append("mode_matrix.csv: save_streak_slot must be unique")
    mode_keys = {row.get("mode_key") for row in modes}
    for line, row in enumerate(rows.get("mode_coverage.csv", []), 2):
        if row.get("mode_key") not in mode_keys:
            errors.append(
                f"mode_coverage.csv:{line}: unresolved mode_key={row.get('mode_key')!r}"
            )

    minimums = spec.get("custom", {}).get("minimum_rentals_by_tier", {})
    rental_counts = Counter(row.get("tier") for row in rows.get("rental_sets.csv", []))
    for tier, minimum in minimums.items():
        if rental_counts[tier] < int(minimum):
            errors.append(f"rental_sets.csv: {tier} {rental_counts[tier]} < {minimum}")
    for line, row in enumerate(rows.get("rental_sets.csv", []), 2):
        moves = [row.get(f"move{index}_key", "") for index in range(1, 5)]
        if "NONE" in moves or len(set(moves)) != 4:
            errors.append(f"rental_sets.csv:{line}: four non-NONE unique moves required")

    minimum_profiles = spec.get("custom", {}).get("minimum_profiles_by_tier", {})
    profile_counts = Counter(row.get("tier") for row in rows.get("opponent_profiles.csv", []))
    for tier, minimum in minimum_profiles.items():
        if profile_counts[tier] < int(minimum):
            errors.append(f"opponent_profiles.csv: {tier} {profile_counts[tier]} < {minimum}")


def _custom_reward(
    rows: dict[str, list[dict[str, str]]],
    spec: dict[str, Any],
    catalogs: dict[str, set[str]],
    errors: list[str],
) -> None:
    expected_prices = spec.get("custom", {}).get("bp_prices", {})
    services = rows.get("encounter_services.csv", [])
    expected_tiers = Counter({tier: 1 for tier in expected_prices})
    if Counter(row.get("tier") for row in services) != expected_tiers:
        errors.append("encounter_services.csv: exactly one service for each tier is required")
    for row in services:
        if row.get("credit_cost") != "1":
            errors.append(f"encounter_services.csv: {row.get('tier')} credit_cost must be 1")
        if row.get("bp_direct_price") != str(expected_prices.get(row.get("tier"))):
            errors.append(f"encounter_services.csv: {row.get('tier')} BP price drift")
    pools = rows.get("encounter_pool_entries.csv", [])
    expected = Counter({tier: 6 for tier in expected_prices})
    if Counter(row.get("tier") for row in pools) != expected:
        errors.append("encounter_pool_entries.csv: exactly six entries per tier are required")
    species = [row.get("species_key") for row in pools]
    if len(species) != len(set(species)):
        errors.append("encounter_pool_entries.csv: species must be unique across four pools")
    forbidden = catalogs.get("forbidden_reward_species", set())
    used_forbidden = sorted(set(species) & forbidden)
    if used_forbidden:
        errors.append(
            f"encounter_pool_entries.csv: forbidden raid/special species: {used_forbidden[:16]}"
        )


def _custom_research(
    rows: dict[str, list[dict[str, str]]],
    spec: dict[str, Any],
    errors: list[str],
) -> None:
    expected = set(spec.get("custom", {}).get("activities", []))
    actual = {row.get("activity") for row in rows.get("activity_contracts.csv", [])}
    if actual != expected:
        errors.append(f"activity_contracts.csv: coverage differs: missing={sorted(expected-actual)}")
    if any(row.get("implementation_mode") == "DEFER" for row in rows.get("activity_contracts.csv", [])):
        errors.append("activity_contracts.csv: DEFER is forbidden")
    ranks = rows.get("rank_progression.csv", [])
    try:
        thresholds = [int(row["threshold_points"]) for row in sorted(ranks, key=lambda r: int(r["rank_no"]))]
    except (ValueError, KeyError):
        thresholds = []
    if thresholds and thresholds != sorted(set(thresholds)):
        errors.append("rank_progression.csv: thresholds must be unique and increasing")


def _custom_collection_supply(
    packet: Path,
    rows: dict[str, list[dict[str, str]]],
    errors: list[str],
) -> None:
    def baseline(relative: str, key: str) -> dict[str, dict[str, str]]:
        path = packet / relative
        try:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                values = list(csv.DictReader(stream))
        except OSError as exc:
            errors.append(f"{relative}: baseline read failed: {exc}")
            return {}
        return {row.get(key, ""): row for row in values if row.get(key, "")}

    form_baseline = baseline(
        "catalogs/form_availability_baseline.csv", "form_record_key"
    )
    gmax_baseline = baseline("catalogs/gmax_factor_baseline.csv", "form_record_key")
    item_baseline = baseline("catalogs/item_availability_baseline.csv", "item_key")
    raid_baseline = baseline("catalogs/raid_availability_baseline.csv", "raid_key")

    form_rows = rows.get("form_acquisition_plan.csv", [])
    form_by_key = {row.get("form_record_key", ""): row for row in form_rows}
    for line, row in enumerate(form_rows, 2):
        source = form_baseline.get(row.get("form_record_key", ""), {})
        for field in (
            "species_key", "base_species_key", "form_category", "current_target_status",
        ):
            if source and row.get(field) != source.get(field):
                errors.append(
                    f"form_acquisition_plan.csv:{line}: baseline drift {field}="
                    f"{row.get(field)!r} != {source.get(field)!r}"
                )
        status = row.get("current_target_status")
        category = row.get("form_category")
        policy = row.get("collection_policy")
        method = row.get("acquisition_method")
        system = row.get("source_system")
        if status == "REQUIRED_ENABLING_FORM" and (
            policy != "REQUIRED_ENABLING"
            or method != "KEEP_STAGE26_ROUTE"
            or system != "STAGE26_ACQUISITION"
        ):
            errors.append(
                f"form_acquisition_plan.csv:{line}: Stage26 enabling route must be preserved"
            )
        elif status == "BATTLE_ONLY_EXCLUDED":
            expected_method = (
                "GMAX_FACTOR_ONLY"
                if category == "GIGANTAMAX_BATTLE_FORM"
                else None
            )
            if policy != "BATTLE_ONLY_EXCLUDED" or (
                expected_method is not None and method != expected_method
            ) or (
                expected_method is None
                and method not in {"BATTLE_TRANSFORM_ONLY", "DO_NOT_DISTRIBUTE"}
            ):
                errors.append(
                    f"form_acquisition_plan.csv:{line}: battle-only form distribution is invalid"
                )
        elif status == "UNOBTAINABLE_EVENT_FORM_EXCLUDED" and (
            policy != "UNOBTAINABLE_CANON_EXCLUDED" or method != "DO_NOT_DISTRIBUTE"
        ):
            errors.append(
                f"form_acquisition_plan.csv:{line}: unavailable canon form must remain excluded"
            )
        elif status == "OPTIONAL_FORM":
            if policy in {"BATTLE_ONLY_EXCLUDED", "UNOBTAINABLE_CANON_EXCLUDED"}:
                errors.append(
                    f"form_acquisition_plan.csv:{line}: optional form has invalid policy"
                )
            if policy == "INTERNAL_HELPER_EXCLUDED":
                if method != "DO_NOT_DISTRIBUTE" or system != "EXCLUDED":
                    errors.append(
                        f"form_acquisition_plan.csv:{line}: helper exclusion must not distribute"
                    )
            elif method == "DO_NOT_DISTRIBUTE" or system == "EXCLUDED":
                errors.append(
                    f"form_acquisition_plan.csv:{line}: persistent form needs an acquisition route"
                )

    for row in rows.get("gmax_factor_plan.csv", []):
        form = form_by_key.get(row.get("form_record_key", ""))
        if form and form.get("acquisition_method") != "GMAX_FACTOR_ONLY":
            errors.append(
                "form_acquisition_plan.csv: Gigantamax rows must use GMAX_FACTOR_ONLY"
            )
        if row.get("item_key") != "ITEM_KEY_DYNAMAX_CANDY":
            errors.append("gmax_factor_plan.csv: item_key must be ITEM_KEY_DYNAMAX_CANDY")
        if row.get("direct_gmax_species_distribution") != "false":
            errors.append(
                "gmax_factor_plan.csv: direct Gigantamax species distribution is forbidden"
            )
        source = gmax_baseline.get(row.get("form_record_key", ""), {})
        for field in ("gmax_species_key", "base_species_key"):
            if source and row.get(field) != source.get(field):
                errors.append(f"gmax_factor_plan.csv: baseline drift {field}")
        if row.get("raid_capture_sets_factor") != "true":
            errors.append("gmax_factor_plan.csv: every G-Max raid capture must set the factor")

    item_by_key = {
        row.get("item_key", ""): row
        for row in rows.get("item_availability_plan.csv", [])
    }
    for line, row in enumerate(rows.get("item_availability_plan.csv", []), 2):
        source = item_baseline.get(row.get("item_key", ""), {})
        if source and row.get("item_role") != source.get("role"):
            errors.append(f"item_availability_plan.csv:{line}: item_role baseline drift")
        if source and row.get("current_evidence_class") != source.get(
            "current_evidence_class"
        ):
            errors.append(
                f"item_availability_plan.csv:{line}: current_evidence_class baseline drift"
            )
    none_item = item_by_key.get("ITEM_KEY_NONE")
    if none_item and none_item.get("target_policy") != "INTERNAL_UNUSED_EXCLUDED":
        errors.append("item_availability_plan.csv: ITEM_KEY_NONE must remain excluded")
    dynamax_candy = item_by_key.get("ITEM_KEY_DYNAMAX_CANDY")
    if dynamax_candy and dynamax_candy.get("target_policy") not in {
        "OBTAINABLE_REPEATABLE", "OBTAINABLE_LIMITED_REPEATABLE"
    }:
        errors.append(
            "item_availability_plan.csv: Dynamax Candy must have a renewable supply"
        )

    for line, row in enumerate(rows.get("raid_host_plan.csv", []), 2):
        if row.get("physical_binding_policy") != "POST_WORLD_FIX_EXACT_REAUDIT":
            errors.append(
                f"raid_host_plan.csv:{line}: physical binding must wait for exact re-audit"
            )
        combined = " ".join(row.values())
        if re.search(r"(?:group|map|local|object)[ _-]*id\s*[:=]?\s*(?:0x)?[0-9]", combined,
                     re.IGNORECASE):
            errors.append(
                f"raid_host_plan.csv:{line}: raw physical IDs are forbidden in Pro design"
            )

    host_pools = {
        row.get("pool_key", "") for row in rows.get("raid_host_plan.csv", [])
    }
    host_reward_pools = {
        row.get("reward_pool_key", "") for row in rows.get("raid_host_plan.csv", [])
    }
    pool_rows = rows.get("raid_pool_entries.csv", [])
    source_raid_counts: Counter[str] = Counter()
    gmax_bases = {
        row.get("base_species_key", "")
        for row in rows.get("gmax_factor_plan.csv", [])
    }
    gmax_pool_bases: set[str] = set()
    for line, row in enumerate(pool_rows, 2):
        source_key = row.get("source_raid_key", "")
        if source_key != "NONE":
            source_raid_counts[source_key] += 1
            source = raid_baseline.get(source_key, {})
            for field in ("species_key", "capture_policy", "unlock_key"):
                if source and row.get(field) != source.get(field):
                    errors.append(
                        f"raid_pool_entries.csv:{line}: source raid baseline drift {field}"
                    )
        if row.get("pool_key") not in host_pools:
            errors.append(f"raid_pool_entries.csv:{line}: pool has no physical host plan")
        try:
            gmax_chance = int(row.get("gmax_factor_chance", "0"))
            level_min = int(row.get("level_min", "0"))
            level_max = int(row.get("level_max", "0"))
        except ValueError:
            continue
        if level_min > level_max:
            errors.append(f"raid_pool_entries.csv:{line}: level_min exceeds level_max")
        if gmax_chance:
            if row.get("species_key") not in gmax_bases:
                errors.append(
                    f"raid_pool_entries.csv:{line}: G-Max chance used by non-G-Max base"
                )
            else:
                gmax_pool_bases.add(row.get("species_key", ""))
    duplicate_sources = sorted(
        key for key, count in source_raid_counts.items() if count != 1
    )
    if duplicate_sources:
        errors.append(
            f"raid_pool_entries.csv: source raid must appear once: {duplicate_sources[:16]}"
        )
    missing_gmax = sorted(gmax_bases - gmax_pool_bases)
    if missing_gmax:
        errors.append(
            f"raid_pool_entries.csv: G-Max-capable bases missing from Raid pools: {missing_gmax[:16]}"
        )
    used_pools = {row.get("pool_key", "") for row in pool_rows}
    empty_host_pools = sorted(host_pools - used_pools)
    if empty_host_pools:
        errors.append(f"raid_host_plan.csv: pools without entries: {empty_host_pools[:16]}")

    reward_rows = rows.get("raid_reward_entries.csv", [])
    used_reward_pools = set()
    for line, row in enumerate(reward_rows, 2):
        pool = row.get("reward_pool_key", "")
        used_reward_pools.add(pool)
        if pool not in host_reward_pools:
            errors.append(
                f"raid_reward_entries.csv:{line}: reward pool has no physical host plan"
            )
        try:
            if int(row.get("quantity_min", "0")) > int(row.get("quantity_max", "0")):
                errors.append(
                    f"raid_reward_entries.csv:{line}: quantity_min exceeds quantity_max"
                )
        except ValueError:
            pass
    empty_reward_pools = sorted(host_reward_pools - used_reward_pools)
    if empty_reward_pools:
        errors.append(
            f"raid_host_plan.csv: reward pools without entries: {empty_reward_pools[:16]}"
        )

    for line, row in enumerate(rows.get("host_requirements.csv", []), 2):
        if row.get("post_world_fix_audit") != "REQUIRED":
            errors.append(
                f"host_requirements.csv:{line}: post-world-fix audit must be REQUIRED"
            )


def _custom_checks(
    packet: Path,
    spec: dict[str, Any],
    rows: dict[str, list[dict[str, str]]],
    jsons: dict[str, dict[str, Any]],
    catalogs: dict[str, set[str]],
    errors: list[str],
) -> None:
    packet_type = spec.get("packet_type")
    if packet_type == "MOVE_DISTRIBUTION":
        _custom_move(packet, rows, catalogs, errors)
    elif packet_type == "FACTORY_HIGH_MODES":
        _custom_factory(rows, spec, errors)
    elif packet_type == "REWARD_ENCOUNTERS":
        _custom_reward(rows, spec, catalogs, errors)
    elif packet_type == "RESEARCH_ECONOMY":
        _custom_research(rows, spec, errors)
    elif packet_type == "COLLECTION_SUPPLY":
        _custom_collection_supply(packet, rows, errors)
    else:
        errors.append(f"unknown packet_type: {packet_type!r}")

    for name, value in jsons.items():
        if not value:
            continue
        states = value.get("states")
        transitions = value.get("transitions")
        if states is not None and (not isinstance(states, list) or not states):
            errors.append(f"{name}: states must be a non-empty list")
        if transitions is not None and (not isinstance(transitions, list) or not transitions):
            errors.append(f"{name}: transitions must be a non-empty list")


def _validate_packet_self(packet: Path, spec: dict[str, Any], errors: list[str]) -> None:
    for name, model in spec.get("catalog_sets", {}).items():
        path = packet / model["path"]
        if not path.is_file():
            errors.append(f"catalog {name}: missing {model['path']}")
    for path in packet.rglob("*"):
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"packet contains forbidden binary: {path.relative_to(packet)}")
    if not spec.get("output_zip_name", "").endswith(".zip"):
        errors.append("PACKET_SPEC.json: output_zip_name must end with .zip")


def _write_generated(
    submission: Path,
    spec: dict[str, Any],
    rows: dict[str, list[dict[str, str]]],
    content_files: list[Path],
) -> tuple[dict[str, Any], dict[str, Any]]:
    fingerprint = _fingerprint(content_files, submission)
    report = {
        "schema_version": 1,
        "status": "PASS",
        "packet_type": spec["packet_type"],
        "output_zip_name": spec["output_zip_name"],
        "errors": [],
        "warnings": [],
        "row_counts": {name: len(value) for name, value in sorted(rows.items())},
        "open_questions": 0,
        "submission_fingerprint": fingerprint,
    }
    report_path = submission / "VALIDATION_REPORT.json"
    report_path.write_bytes(_stable_json(report))
    files = []
    for path in sorted(
        [*content_files, report_path], key=lambda item: item.relative_to(submission).as_posix()
    ):
        files.append({
            "path": path.relative_to(submission).as_posix(),
            "size": path.stat().st_size,
            "sha256": _sha256(path),
        })
    manifest = {
        "schema_version": 1,
        "design_status": "IMPLEMENTATION_READY",
        "packet_type": spec["packet_type"],
        "submission_fingerprint": fingerprint,
        "files": files,
    }
    (submission / "SUBMISSION_MANIFEST.json").write_bytes(_stable_json(manifest))
    return report, manifest


def validate(packet: Path, submission: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    try:
        spec = json.loads((packet / "PACKET_SPEC.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"PACKET_SPEC.json read failed: {exc}"], {}
    catalogs = _catalog_sets(packet, spec, errors)
    output_models = spec.get("outputs", {})
    expected_content = set(output_models)
    actual = {
        path.relative_to(submission).as_posix()
        for path in submission.rglob("*") if path.is_file()
    }
    allowed = expected_content | GENERATED_FILES
    extra = sorted(actual - allowed)
    missing = sorted(expected_content - actual)
    if extra:
        errors.append(f"unexpected output files: {extra}")
    if missing:
        errors.append(f"missing output files: {missing}")

    rows_by_file: dict[str, list[dict[str, str]]] = {}
    json_by_file: dict[str, dict[str, Any]] = {}
    for name, model in output_models.items():
        path = submission / name
        if not path.is_file():
            continue
        kind = model["kind"]
        if kind == "csv":
            rows_by_file[name] = _validate_csv(path, model, catalogs, errors)
        elif kind == "json":
            json_by_file[name] = _validate_json(path, model, errors)
        elif kind == "markdown":
            _check_text(path, errors, min_bytes=int(model.get("min_bytes", 1)))
        else:
            errors.append(f"{name}: unknown output kind {kind}")

    questions = submission / "OPEN_QUESTIONS.md"
    if questions.is_file() and questions.read_text(encoding="utf-8") != OPEN_QUESTIONS_TEXT:
        errors.append("OPEN_QUESTIONS.md must contain the canonical no-questions text")
    _coverage_checks(spec, rows_by_file, catalogs, errors)
    if "dialogue.csv" in rows_by_file:
        _check_dialogue(packet, rows_by_file["dialogue.csv"], errors)
    _custom_checks(packet, spec, rows_by_file, json_by_file, catalogs, errors)
    return errors, {"spec": spec, "rows": rows_by_file, "jsons": json_by_file}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("submission", nargs="?", type=Path)
    parser.add_argument("--packet-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    packet = args.packet_root.resolve()
    try:
        spec = json.loads((packet / "PACKET_SPEC.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"VALIDATION=FAIL PACKET_SPEC={exc}", file=sys.stderr)
        return 1

    if args.self_test:
        errors: list[str] = []
        _validate_packet_self(packet, spec, errors)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            print(f"VALIDATION=FAIL errors={len(errors)}")
            return 1
        print(f"VALIDATION=PASS packet_type={spec['packet_type']} self_test=PASS")
        return 0

    if args.submission is None:
        parser.error("submission is required unless --self-test is used")
    submission = args.submission.resolve()
    errors, context = validate(packet, submission)
    if errors:
        report = {
            "schema_version": 1,
            "status": "FAIL",
            "packet_type": spec.get("packet_type"),
            "errors": errors,
            "warnings": [],
            "open_questions": None,
        }
        report_path = args.report or submission / "VALIDATION_REPORT.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_bytes(_stable_json(report))
        for error in errors:
            print(f"ERROR: {error}")
        print(f"VALIDATION=FAIL errors={len(errors)}")
        return 1

    content_files = [submission / name for name in sorted(spec["outputs"])]
    report, manifest = _write_generated(
        submission, spec, context["rows"], content_files
    )
    if args.report and args.report.resolve() != (submission / "VALIDATION_REPORT.json").resolve():
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_bytes(_stable_json(report))
    print(
        f"VALIDATION=PASS packet_type={spec['packet_type']} "
        f"files={len(manifest['files']) + 1} open_questions=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
