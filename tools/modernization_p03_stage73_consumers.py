"""P03 Stage73候補consumer群の読取専用preflight。

ROMを変更せず、固定P03 ZIPを1回streamして専用5群を再計数する。
Stage72 identityが未確定の間はROM工程をfail-closedとする。
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn

from tools.modernization_learnsets import iter_compiled_p03_routes


TASK = "USER-MODERNIZATION-P03-STAGE73-CONSUMER-PREFLIGHT"
CONSUMERS = ("egg", "shared_egg", "pre_evolution_carry", "reminder", "form_change")
SIDE_CHANGE_MOVE_ID = 1063
EGG_ALIAS_SPECIES = {203, 324}
EGG_INCENSE_SPECIES = {364, 608, 719, 724, 727}
ROTOM_FORM_SPECIES = {894, 895, 896, 897, 898}
FIXED_FORM_SPECIES = {1260, 1261, 1386, 1387}


class ModernizationP03Stage73ConsumersError(ValueError):
    """Stage73 preflightのidentity・件数・境界違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP03Stage73ConsumersError(message)


def stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


class FramedDigest:
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


def _fixed_bytes(root: Path, contract: Mapping[str, Any], label: str) -> bytes:
    path = root / str(contract.get("path", ""))
    if path.is_symlink() or not path.is_file():
        _fail(f"{label}が固定通常ファイルではありません: {path}")
    raw = path.read_bytes()
    if len(raw) != contract.get("size"):
        _fail(f"{label} size不一致")
    if hashlib.sha256(raw).hexdigest() != contract.get("sha256"):
        _fail(f"{label} SHA-256不一致")
    return raw


def read_config(root: Path, relative: Path | str) -> dict[str, Any]:
    path = Path(relative)
    if not path.is_absolute():
        path = root / path
    if path.is_symlink() or not path.is_file():
        _fail(f"configが通常ファイルではありません: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"configを読めません: {error}")
    if not isinstance(value, dict):
        _fail("config rootがobjectではありません")
    if (value.get("schema_version"), value.get("task"), value.get("stage")) != (1, TASK, 73):
        _fail("config schema/task/stage不一致")
    parent = value.get("parent_identity", {})
    if (parent.get("stage71_commit")
            != "ee8062094f84fff42f529793cb95f09d2078ae33"
            or parent.get("policy")
            != "FAIL_CLOSED_UNTIL_ALL_STAGE72_FIELDS_ARE_PINNED"):
        _fail("親identity policy不一致")
    return value


def require_pinned_parent(config: Mapping[str, Any]) -> None:
    parent = config.get("parent_identity", {})
    pending = [name for name in ("stage72_commit", "stage72_rom_path", "stage72_rom_size", "stage72_rom_sha256")
               if parent.get(name) == "PENDING"]
    if pending:
        _fail("Stage72 identity未確定のためROM工程を拒否: " + ", ".join(pending))


def _counter(value: Counter[str]) -> dict[str, int]:
    return dict(sorted(value.items()))


def _assert_expected(actual: Mapping[str, Any], expected: Mapping[str, Any], label: str) -> None:
    for key, expected_value in expected.items():
        if actual.get(key) != expected_value:
            _fail(f"{label}.{key}不一致: {actual.get(key)!r} != {expected_value!r}")


def build_preflight(root: Path, config_path: Path | str = Path("config/modernization_p03_stage73_consumers.json")) -> dict[str, Any]:
    root = root.resolve()
    config = read_config(root, config_path)
    inputs = config.get("inputs", {})
    contract = json.loads(_fixed_bytes(root, inputs["p03_contract"], "P03 contract"))
    zip_contract = inputs["learnsets_zip"]
    learnsets_zip = root / zip_contract["path"]
    _fixed_bytes(root, zip_contract, "P03 learnsets ZIP")

    source_counts: Counter[str] = Counter()
    selected_counts: Counter[str] = Counter()
    excluded_counts: Counter[str] = Counter()
    source_digests = {name: FramedDigest() for name in CONSUMERS}
    selected_digests = {name: FramedDigest() for name in CONSUMERS}
    level_pairs: set[tuple[int, int]] = set()
    egg_pairs: set[tuple[int, int]] = set()
    reminder_pairs: set[tuple[int, int]] = set()
    shared_pairs: set[tuple[int, int]] = set()
    carry_pairs: set[tuple[int, int]] = set()
    form_pairs: set[tuple[int, int]] = set()
    targets = {name: set() for name in CONSUMERS}
    egg_boundary: Counter[str] = Counter()
    shared_games: Counter[str] = Counter()
    shared_basis: Counter[str] = Counter()
    shared_resolution: Counter[str] = Counter()
    carry_methods: Counter[str] = Counter()
    form_methods: Counter[str] = Counter()
    form_kinds: Counter[str] = Counter()
    global_routes = 0
    global_excluded = 0

    for row in iter_compiled_p03_routes(root, learnsets_zip):
        global_routes += 1
        consumer = str(row["consumer"])
        source = row["source_route"]
        move = int(source["project_move_id"])
        species = int(row["target_species_id"])
        pair = (species, move)
        if consumer in CONSUMERS:
            source_counts[consumer] += 1
            source_digests[consumer].add(row)
        if move == SIDE_CHANGE_MOVE_ID:
            global_excluded += 1
            if consumer in CONSUMERS:
                excluded_counts[consumer] += 1
            continue
        if row.get("runtime_move_ready") is not True or not 1 <= move <= 1062:
            _fail(f"選択routeのruntime move境界不一致: {consumer}/{species}/{move}")
        if consumer == "level_up":
            level_pairs.add(pair)
            continue
        if consumer not in CONSUMERS:
            continue
        selected_counts[consumer] += 1
        targets[consumer].add(species)
        selected_digests[consumer].add({**row, "selection_status": "ADOPTED_FOR_RUNTIME"})
        method = str(source["method"])
        if consumer == "egg":
            if method == "special_breeding":
                if pair != (24, 344):
                    _fail("未知のspecial breeding route")
                egg_boundary["special_breeding_existing_owner"] += 1
            else:
                egg_pairs.add(pair)
                if species in EGG_ALIAS_SPECIES:
                    egg_boundary["legacy_alias_conflict"] += 1
                elif species in EGG_INCENSE_SPECIES:
                    egg_boundary["incense_union_conflict"] += 1
        elif consumer == "reminder":
            reminder_pairs.add(pair)
        elif consumer == "shared_egg":
            shared_pairs.add(pair)
            shared_games[str(source["source_game"])] += 1
            shared_basis[str(source["shared_egg_receiver_basis"])] += 1
            shared_resolution[str(source["shared_egg_resolution"])] += 1
        elif consumer == "pre_evolution_carry":
            carry_pairs.add(pair)
            carry_methods[method] += 1
        elif consumer == "form_change":
            form_pairs.add(pair)
            form_methods[method] += 1
            form_kinds[str(source["route_kind"])] += 1
            if source["route_kind"] == "direct" and species not in ROTOM_FORM_SPECIES | FIXED_FORM_SPECIES:
                _fail(f"未知の直接form transition owner: {species}")

    expected_groups = config["consumer_groups"]
    contract_source = contract["corrected_adoption"]["consumers"]
    contract_selected = contract["runtime_selection"]["consumers"]
    groups: dict[str, Any] = {}
    for name in CONSUMERS:
        source_hash = source_digests[name].hexdigest()
        selected_hash = selected_digests[name].hexdigest()
        actual = {
            "source_count": source_counts[name], "source_group_sha256": source_hash,
            "selected_count": selected_counts[name], "selected_group_sha256": selected_hash,
        }
        _assert_expected(
            actual,
            {key: expected_groups[name][key] for key in actual},
            name,
        )
        if contract_source[name] != {"count": source_counts[name], "content_sha256": source_hash}:
            _fail(f"{name} source group hashがP03正本と不一致")
        if contract_selected[name] != {"count": selected_counts[name], "content_sha256": selected_hash}:
            _fail(f"{name} selected group hashがP03正本と不一致")
        groups[name] = actual

    egg_actual = {
        **groups["egg"], "stage73_scope_count": sum(egg_boundary.values()),
        **_counter(egg_boundary), "exact_override_pending_runtime_hook":
        egg_boundary["legacy_alias_conflict"] + egg_boundary["incense_union_conflict"],
    }
    shared_actual = {
        **groups["shared_egg"], "target_count": len(targets["shared_egg"]),
        "unique_species_move_pairs": len(shared_pairs),
        "direct_egg_overlap": len(shared_pairs & egg_pairs),
        "shared_only": len(shared_pairs - egg_pairs), "source_games": _counter(shared_games),
        "receiver_basis": _counter(shared_basis), "resolution": _counter(shared_resolution),
    }
    carry_supply = sum(carry_methods[name] for name in ("tm", "tr", "tutor"))
    carry_actual = {
        **groups["pre_evolution_carry"], "target_count": len(targets["pre_evolution_carry"]),
        "unique_species_move_pairs": len(carry_pairs),
        "duplicate_route_paths": selected_counts["pre_evolution_carry"] - len(carry_pairs),
        "methods": _counter(carry_methods),
        "existing_generic_move_slot_persistence_semantics": selected_counts["pre_evolution_carry"],
        "machine_tutor_upstream_supply_dependency": carry_supply,
        "other_source_owner_dependency": selected_counts["pre_evolution_carry"] - carry_supply,
        "new_runtime_materialized_count": 0,
    }
    reminder_actual = {
        **groups["reminder"], "target_count": len(targets["reminder"]),
        "unique_species_move_pairs": len(reminder_pairs),
        "direct_level_up_overlap": len(reminder_pairs & level_pairs),
        "pending_dedicated_runtime_table": selected_counts["reminder"],
    }
    form_actual = {
        **groups["form_change"], "target_count": len(targets["form_change"]),
        "unique_species_move_pairs": len(form_pairs),
        "duplicate_route_paths": selected_counts["form_change"] - len(form_pairs),
        "route_kinds": _counter(form_kinds), "methods": _counter(form_methods),
        "existing_generic_carry_owner": form_kinds["form_change"],
        "existing_fixed_transition_owner": 4, "rotom_transition_owner_missing": 5,
        "machine_upstream_supply_dependency": form_methods["tm"],
        "new_runtime_materialized_count": 0,
    }
    for name, actual in (("egg", egg_actual), ("shared_egg", shared_actual),
                         ("pre_evolution_carry", carry_actual), ("reminder", reminder_actual),
                         ("form_change", form_actual)):
        _assert_expected(actual, expected_groups[name], name)

    boundary_actual = {
        "five_group_source_count": sum(source_counts.values()),
        # egg全selected 2,563のうちStage67で安全に接続済みの2,522は対象外。
        "five_group_selected_count": (
            egg_actual["stage73_scope_count"]
            + selected_counts["shared_egg"]
            + selected_counts["pre_evolution_carry"]
            + selected_counts["reminder"]
            + selected_counts["form_change"]
        ),
        "side_change_project_move_id": SIDE_CHANGE_MOVE_ID,
        "side_change_global_excluded_count": global_excluded,
        "side_change_five_group_excluded_count": sum(excluded_counts.values()),
        "browt_pombon_gecqua_adopted_count": 0,
    }
    _assert_expected(boundary_actual, config["selection_boundary"], "selection_boundary")
    if global_routes != 118528:
        _fail(f"全P03 route件数不一致: {global_routes}")
    if any(config["prohibited_coercions"].values()):
        _fail("禁止されたconsumer偽装転記がconfigにあります")
    if config["claim_policy"] != {
        "preflight_new_runtime_materialized": 0,
        "existing_owner_semantics_are_not_new_materialization": True,
        "upstream_supply_dependencies_are_not_materialized": True,
        "stage73_completion_claim_allowed": False,
    }:
        _fail("実装済みclaim分離policy不一致")
    return {
        "schema_version": 1, "task": TASK, "status": "PASS_PREFLIGHT_PARENT_PENDING",
        "source_route_count": global_routes, "consumer_groups": {
            "egg": egg_actual, "shared_egg": shared_actual,
            "pre_evolution_carry": carry_actual, "reminder": reminder_actual,
            "form_change": form_actual,
        },
        "selection_boundary": boundary_actual,
        "claims": config["claim_policy"],
        "prohibited_coercions": config["prohibited_coercions"],
        "parent_identity": config["parent_identity"],
    }
