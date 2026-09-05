from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]

from tools.stage61_catalog_state_matrix import (  # noqa: E402
    ControlDomain,
    ControlKey,
    FACILITY_SESSION_KIND,
    MAX_FLAGS_PER_CASE,
    NATIONAL_DEX_ENABLED_VAR_VALUE,
    NATIONAL_DEX_FLAG_ID,
    NATIONAL_DEX_VAR_ID,
    RUNTIME_POSITION_EXPECTED_CONTROLS,
    RUNTIME_POSITION_EXPECTED_OWNERS,
    RUIN_SEAL_COMPLETION_FLAG,
    RUIN_SEAL_FLAGS,
    RUIN_SEAL_OBJECT_ROOT,
    RUIN_SEAL_PREFIX_KIND,
    Stage61CatalogStateMatrixError,
    TRAINER_TOWER_INIT_ADDRESS,
    TRAINER_TOWER_LOCAL_BLOB_ADDRESS,
    TRAINER_TOWER_LOCAL_BLOB_SIZE,
    TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION,
    TRAINER_TOWER_SETUP_ADDRESS,
    TRAINER_TOWER_SETUP_SIZE,
    TRAINER_TOWER_TRANSITION_ADDRESS,
    TRAINER_TOWER_VISIBLE_OBJECTS,
    _candidate_assignments,
    _merge_flags,
    _trainer_tower_local_fallback_lifecycle,
    _normalized_trainer_tower_runtime_map_lifecycle,
    _validate_trainer_tower_fixture_precondition,
    _validate_map_compact_controls,
    _validate_map_lifecycle_order,
    _validate_map_lifecycle_sequence,
    _normalize_runner_required_postconditions,
    _runtime_assignment_map,
    _runtime_position_state_contract,
    _runtime_control_value,
    attach_stage61_case_oracles,
    attach_stage61_event_owner_runtime_scope,
    bind_stage61_object_runtime_case_ids,
    build_stage61_event_owner_execution_scope,
    build_stage61_catalog_state_matrix,
    expand_stage61_runtime_control_matrix,
    runner_event_state_rows,
    runner_state_rows,
)
from tools.stage61_event_semantic_relocator import SemanticScriptGraph  # noqa: E402
from tools.stage61_interaction_oracle import (  # noqa: E402
    _dormant_common7_structural_evidence,
    _facility_scenario_keys,
    _materialize_control_requirement,
    _owner_trigger_contract,
    FACILITY_SESSION_RELATION,
    FACILITY_SHARED_ROOT,
    RUIN_SEAL_PREFIX_RELATION,
    RUIN_SEAL_SCENARIO_IDS,
)
from scripts.build_stage61_display_npc_event_audit import (  # noqa: E402
    BILL_SEVII_SOURCE_EVIDENCE_PATHS,
    BG_NUMERIC_ZERO_RETURN_BRANCH_ADDRESS,
    BG_NUMERIC_ZERO_RETURN_BRANCH_PREIMAGE,
    BG_NUMERIC_ZERO_RETURN_PATCH_ADDRESS,
    BG_NUMERIC_ZERO_RETURN_PATCH_PREIMAGE,
    BG_NUMERIC_ZERO_RETURN_PATCH_REPLACEMENT,
    EVENT_CONSUMER_SOURCE_CONTRACT,
    MGBA_REQUIRED_CASES,
    MGBA_REQUIRED_DOMAINS,
    MGBA_REQUIRED_STATE_PERSISTENCE_CASES,
    MGBA_ORCHESTRATOR_SOURCE,
    MGBA_RUNNER_SOURCE,
    Stage61BuildError,
    Stage61MgbaError,
    RUNTIME_POSITION_STATE_MAP_CONTRACTS,
    _compile_runtime,
    _apply_bg_numeric_zero_return_patch,
    _collision_zero,
    _diagnostic_walk_cycle,
    _engine_special_flag_owner_literal_contract,
    _engine_special_flag_lifecycle_fixture,
    _interaction_abi_pinned_inputs,
    _mgba_binding_sha256,
    _mgba_oracle_canonical_sha256,
    _mgba_effect_command_groups,
    _mgba_effect_case_partition,
    _mgba_effect_group_key,
    _mgba_effect_registry_missing_inventory,
    _mgba_effect_registry_source_binding,
    _mgba_effect_registry_structure,
    _mgba_effect_raw_watch,
    _mgba_effect_validator_projection,
    _mgba_expected_default_effect_observer,
    _mgba_validate_effect_signature_rebinding,
    _local_object_operation_evidence,
    _map_geometry,
    _map_geometry_from_layout_id,
    _normalized_mgba_matrix_sha256,
    _object_fields,
    _required_mgba_source_binding,
    _runtime_position_final_operation_evidence,
    _runtime_position_layout_variant_evidence,
    _runtime_position_root_binding_evidence,
    _stage_map_state,
    _validate_mgba_retained_artifact_manifest,
    _validate_required_mgba_document,
    _validate_runtime_toolchain_manifest,
)


STATEFUL_MENU_CONTRACTS_SHA256 = "9" * 64
SHADOW_OWNER_PAIRS = {
    "OBJECT:003/022:000": "OBJECT:096/015:007",
    "OBJECT:003/022:003": "OBJECT:096/015:008",
}


def _empty_required_postconditions() -> dict:
    return {
        "flags": [], "engine_special_flags": [], "vars": [],
        "items": [], "trainers": [], "objects": [], "warp": None,
        "battle": None, "money": None, "berry_powder": None,
        "coins": None, "party": None, "storage": None, "persistent": [],
    }


def _strict_walk_execution(object_position: list[int]) -> dict:
    """Build a schema-exact real-walk fixture around one pinned object tile."""

    object_x, object_y = map(int, object_position)
    if [object_x, object_y] == [6, 3]:
        # 2/34 runtime Dunsparce: the direct vertical approach is blocked by
        # the effective layout.  Start on the known passable west stance and
        # make a real left/right cycle before facing the object.
        stance = [5, 3]
        start = list(stance)
        walk_sequence = ["LEFT", "RIGHT"]
        action = "RIGHT"
    elif [object_x, object_y] == [23, 2]:
        # 2/34 static Dunsparce uses the alternate layout.  Its north stance
        # is passable; retain a non-empty physical walk without crossing the
        # object's occupied tile.
        stance = [23, 1]
        start = list(stance)
        walk_sequence = ["LEFT", "RIGHT"]
        action = "DOWN"
    elif object_x > 0:
        stance = [object_x - 1, object_y]
        start = [stance[0], stance[1] + 1]
        walk_sequence = ["UP"]
        action = "RIGHT"
    else:
        stance = [object_x + 1, object_y]
        start = [stance[0], stance[1] + 1]
        walk_sequence = ["UP"]
        action = "LEFT"
    return {
        "trigger": "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A",
        "start": start,
        "walk_sequence": walk_sequence,
        "stance": stance,
        "action": action,
        "interaction_distance": 1,
        "counter_tile": None,
        "actual_walk_required": True,
        "actual_walk_exception": None,
        "walk_path_basis": (
            "TEST_FIXTURE_PINNED_OBJECT_GEOMETRY_WITH_NONEMPTY_REAL_WALK"
        ),
        "direct_script_call_forbidden": True,
    }


def _runtime_position_state(
    control: dict, *, runtime: bool,
) -> dict[str, list[dict]]:
    value = bool(
        control["runtime_value"] if runtime else control["static_value"]
    )
    reason = (
        "MAP_TAG3_RUNTIME_POSITION_CONDITION_RUNTIME"
        if runtime else "MAP_TAG3_RUNTIME_POSITION_CONDITION_STATIC"
    )
    if control["kind"] == "FLAG":
        return {
            "flags": [{
                "id": int(control["id"]), "value": value,
                "reason": reason,
            }],
            "vars": [],
        }
    return {
        "flags": [{
            "id": NATIONAL_DEX_FLAG_ID, "value": value,
            "reason": reason,
        }],
        "vars": [{
            "id": NATIONAL_DEX_VAR_ID,
            "value": NATIONAL_DEX_ENABLED_VAR_VALUE if value else 0,
            "reason": reason,
        }],
    }


def _strict_legacy_catalog_fixture(
    legacy: dict, placement: dict, inventory: dict, stage61_rom: bytes,
) -> dict:
    """Upgrade the retained pre-contract catalog from independent ROM facts."""

    result = json.loads(json.dumps(legacy))
    placement_by_id = {
        str(row["npc_id"]): row for row in placement["objects"]
    }
    inventory_by_id = {
        str(row["owner_id"]): row for row in inventory["owners"]
        if row.get("owner_kind") == "OBJECT" and row.get("runtime_root") is True
    }
    conditioned: dict[tuple[int, int], set[int]] = {}
    for npc in result["npcs"]:
        owner = str(npc["npc_id"])
        placement_row = placement_by_id[owner]
        inventory_row = inventory_by_id[owner]
        record_offset = int(inventory_row["record_address"]) - 0x08000000
        template_raw = stage61_rom[record_offset:record_offset + 24]
        if len(template_raw) != 24:
            raise AssertionError(f"object template truncated: {owner}")
        template_object = [
            struct.unpack_from("<h", template_raw, 4)[0],
            struct.unpack_from("<h", template_raw, 6)[0],
        ]
        if template_object != [int(npc["x"]), int(npc["y"])]:
            raise AssertionError(f"legacy/template coordinate drift: {owner}")
        runtime_object = list(map(int, placement_row["object"]))
        npc["expected_template_raw_hex"] = template_raw.hex().upper()
        npc["interaction_object"] = runtime_object
        npc["interaction_execution"] = _strict_walk_execution(runtime_object)
        npc["non_product_shadow_alias"] = None
        if owner in SHADOW_OWNER_PAIRS:
            canonical_owner = SHADOW_OWNER_PAIRS[owner]
            common = {
                "classification": "CANONICAL_SHADOW_NON_PRODUCT_SOURCE",
                "source_owner_id": owner,
                "canonical_owner_id": canonical_owner,
            }
            npc["non_product_shadow_alias"] = {
                **common, "role": "NON_PRODUCT_SOURCE",
            }
            legacy_execution = placement_row["interaction_execution"]
            npc["interaction_execution"] = {
                "trigger": (
                    "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A"
                ),
                "start": list(legacy_execution["stance"]),
                "walk_sequence": [],
                "stance": list(legacy_execution["stance"]),
                "action": str(legacy_execution["action"]),
                "interaction_distance": int(
                    legacy_execution["interaction_distance"]
                ),
                "counter_tile": legacy_execution["counter_tile"],
                "actual_walk_required": False,
                "actual_walk_exception": {
                    "classification": (
                        "CANONICAL_SHADOW_NON_PRODUCT_SOURCE"
                    ),
                    "canonical_owner_id": canonical_owner,
                    "canonical_walk_required": True,
                    "source_teleport_face_a_required": True,
                    "direct_script_call_forbidden": True,
                },
                "walk_path_basis": (
                    "CANONICAL_SHADOW_NON_PRODUCT_SOURCE_DIAGNOSTIC_STANCE"
                ),
                "direct_script_call_forbidden": True,
            }
        elif owner in SHADOW_OWNER_PAIRS.values():
            source_owner = next(
                source for source, canonical in SHADOW_OWNER_PAIRS.items()
                if canonical == owner
            )
            npc["non_product_shadow_alias"] = {
                "classification": "CANONICAL_SHADOW_NON_PRODUCT_SOURCE",
                "source_owner_id": source_owner,
                "canonical_owner_id": owner,
                "role": "CANONICAL_PHYSICAL_OWNER",
            }
            npc["interaction_execution"]["walk_path_basis"] = (
                "CANONICAL_SHADOW_EXACT_STOCK_INCOMING_ARRIVAL_TO_STANCE"
            )
        npc["runtime_position_state_contract"] = None
        if runtime_object == template_object:
            continue

        map_key = (int(npc["group"]), int(npc["map"]))
        source = RUNTIME_POSITION_STATE_MAP_CONTRACTS.get(map_key)
        if source is None:
            raise AssertionError(f"unmanifested runtime position: {owner}")
        control = json.loads(json.dumps(source["control"]))
        local_id = int(npc["local_id"])
        command = bytes([0x63, local_id, 0]) + struct.pack(
            "<hh", *runtime_object,
        )
        command_offsets: list[int] = []
        cursor = 0
        while True:
            offset = stage61_rom.find(command, cursor)
            if offset < 0:
                break
            command_offsets.append(offset)
            cursor = offset + 1
        if len(command_offsets) != 1:
            raise AssertionError(
                f"setobjectxyperm command cardinality drift: {owner} "
                f"count={len(command_offsets)}"
            )
        static_execution = _strict_walk_execution(template_object)
        runtime_execution = _strict_walk_execution(runtime_object)
        baseline_variant = (
            "RUNTIME" if control["kind"] == "NATIONAL_DEX" else "STATIC"
        )
        npc["runtime_position_state_contract"] = {
            "kind": "CONDITIONAL_MAP_SCRIPT_RUNTIME_POSITION",
            "root": f"0x{int(source['root']):08X}",
            "map_script_tag": 3,
            "control": control,
            "variants": [
                {
                    "variant_id": "STATIC",
                    "object": template_object,
                    "state": _runtime_position_state(
                        control, runtime=False,
                    ),
                    "interaction_execution": static_execution,
                    "baseline": baseline_variant == "STATIC",
                },
                {
                    "variant_id": "RUNTIME",
                    "object": runtime_object,
                    "state": _runtime_position_state(
                        control, runtime=True,
                    ),
                    "interaction_execution": runtime_execution,
                    "baseline": baseline_variant == "RUNTIME",
                },
            ],
            "setobjectxyperm_instruction_addresses": [
                f"0x{0x08000000 + command_offsets[0]:08X}"
            ],
            "root_prefix_hex": str(source["root_prefix_hex"]),
            "assertions": {
                "map_script_tag3_exact": True,
                "root_preimage_exact": True,
                "static_and_runtime_positions_distinct": True,
                "setobjectxyperm_root_exact": True,
                "var_result_not_host_seeded": True,
            },
        }
        npc["interaction_execution"] = runtime_execution
        conditioned.setdefault(map_key, set()).add(int(npc["object_index"]))

    if {
        key: frozenset(value) for key, value in conditioned.items()
    } != RUNTIME_POSITION_EXPECTED_OWNERS:
        raise AssertionError(f"runtime position owner drift: {conditioned}")
    if {
        key: (
            int(value["root"]), str(value["control"]["kind"]),
            int(value["control"]["id"]),
        )
        for key, value in RUNTIME_POSITION_STATE_MAP_CONTRACTS.items()
    } != RUNTIME_POSITION_EXPECTED_CONTROLS:
        raise AssertionError("builder/matrix runtime position manifest drift")
    return result


class Stage61CatalogStateMatrixUnitTests(unittest.TestCase):
    def test_map_lifecycle_sequence_is_phase_ordered_and_strict(self) -> None:
        optional = {
            "outer_index": None, "outer_record_address": None,
            "selected_condition_index": None,
            "selected_condition_record_address": None,
            "root_field_address": None, "root_pc": None, "owner_id": None,
        }

        def attempt(
            ordinal: int, phase: str, tag: int | None, result: str,
            **payload: object,
        ) -> dict[str, object]:
            return {
                "attempt_ordinal": ordinal, "phase_marker": phase,
                "tag": tag, "result": result, **optional, **payload,
            }

        def lifecycle(
            producer_kind: str, *, include_field_return: bool,
        ) -> dict[str, object]:
            attempts = [
                attempt(0, "DESTINATION_TEMP_CLEAR", None, "ENGINE_TRANSFORM"),
                attempt(1, "INITIAL_TRANSITION", 3, "TAG_ABSENT"),
                attempt(2, "INITIAL_LOAD", 1, "TAG_ABSENT"),
                attempt(3, "INITIAL_RESUME", 5, "TAG_ABSENT"),
            ]
            if producer_kind != "CONNECTION":
                attempts.append(attempt(
                    len(attempts), "INITIAL_WARP_IN", 4, "TAG_ABSENT",
                ))
            dispatch_attempt = len(attempts)
            owner = "MAP:003/004:000:000"
            attempts.append(attempt(
                dispatch_attempt, "PRE_FIELD_INPUT_ON_FRAME", 2,
                "DISPATCH", outer_index=0,
                outer_record_address="0x08100000",
                selected_condition_index=0,
                selected_condition_record_address="0x08100010",
                root_field_address="0x08100014",
                root_pc="0x08100100", owner_id=owner,
            ))
            attempts.append(attempt(
                len(attempts), "PRE_FIELD_INPUT_ON_FRAME", 2,
                "TAG_ABSENT",
            ))
            if include_field_return:
                attempts.extend((
                    attempt(
                        len(attempts), "FIELD_RETURN_RESUME", 5,
                        "TAG_ABSENT",
                    ),
                    attempt(
                        len(attempts) + 1,
                        "FIELD_RETURN_RETURN_TO_FIELD", 7, "TAG_ABSENT",
                    ),
                ))
            dispatch = {
                "dispatch_ordinal": 0,
                "attempt_ordinal": dispatch_attempt,
                "phase_marker": "PRE_FIELD_INPUT_ON_FRAME", "tag": 2,
                "owner_id": owner, "root_pc": "0x08100100",
                "root_field_address": "0x08100014",
                "trace_start_index": 0, "trace_end_index": 0,
                "effect_start_index": 0, "effect_end_index": 0,
                "printer_start_index": 0, "printer_end_index": 0,
                "decision_start_index": 0, "decision_end_index": 0,
                "state_before_sha256": "1" * 64,
                "state_after_sha256": "2" * 64,
            }
            return {
                "schema_version": 1,
                "kind": "STAGE61_MAP_LIFECYCLE_SEQUENCE",
                "producer_ordinal": 0, "producer_kind": producer_kind,
                "control_variant_id": "unit-controls",
                "include_field_return": include_field_return,
                "attempt_cap": 256,
                "phase_controls": [{
                    "phase_marker": "PRE_TRANSITION",
                    "variables": [{"id": 0x4001, "value": 7}],
                    "flags": [{"id": 0x4002, "value": True}],
                }, {
                    "phase_marker": "PRE_FIELD_INPUT",
                    "variables": [{"id": 0x4003, "value": 9}],
                    "flags": [{"id": 0x0803, "value": False}],
                }],
                "engine_transforms": [{
                    "transform_ordinal": 0, "attempt_ordinal": 0,
                    "phase_marker": "DESTINATION_TEMP_CLEAR",
                    "kind": "STAGE61_MAP_ENGINE_TRANSFORM",
                    "operation": "CLEAR_TEMP_FIELD_EVENT_DATA",
                    "variable_writes": [
                        {"id": identifier, "value": 0}
                        for identifier in range(0x4000, 0x4010)
                    ],
                    "temporary_flag_writes": [
                        {"id": identifier, "value": False}
                        for identifier in range(0x20)
                    ],
                    "system_flag_writes": [
                        {"id": identifier, "value": False}
                        for identifier in (0x0803, 0x0804, 0x0805, 0x0807, 0x0842)
                    ],
                    "before_state_sha256": "3" * 64,
                    "after_state_sha256": "4" * 64,
                }],
                "ordered_attempts": attempts,
                "ordered_dispatches": [dispatch],
                "ordered_effect_instances": [],
                "dispatched_owner_ids": [owner],
                "attempt_count": len(attempts), "dispatch_count": 1,
            }

        stock = lifecycle("STOCK_WARP", include_field_return=True)
        _validate_map_lifecycle_sequence(stock, "stock")
        _validate_map_lifecycle_order(stock, "stock")
        connection = lifecycle("CONNECTION", include_field_return=False)
        _validate_map_lifecycle_sequence(connection, "connection")
        _validate_map_lifecycle_order(connection, "connection")
        self.assertNotIn(
            4, [row["tag"] for row in connection["ordered_attempts"]],
        )
        self.assertEqual(
            [row["tag"] for row in stock["ordered_attempts"][-2:]], [5, 7],
        )

        owner = stock["ordered_dispatches"][0]["owner_id"]

        def phase_relation(marker: str) -> list[dict[str, object]]:
            return [{
                "operator": "MAP_ENGINE_PHASE_CONTROL",
                "instruction_address": None,
                "source": {
                    "kind": "MAP_LIFECYCLE_PHASE_BOUNDARY",
                    "phase_marker": marker,
                },
                "abi_key": None,
            }]

        def compact(
            lifecycle_row: dict[str, object], *, include_position: bool,
        ) -> dict[str, object]:
            pre_transition = [{
                "kind": "VAR", "id": 0x4001, "value": 7,
                "owner_keys": [owner],
                "relation_evidence": phase_relation("PRE_TRANSITION"),
                "fixture_keys": [],
            }, {
                "kind": "ENGINE_SPECIAL_FLAG", "id": 0x4002,
                "value": True, "owner_keys": [owner],
                "relation_evidence": phase_relation("PRE_TRANSITION"),
                "fixture_keys": [],
            }]
            if include_position:
                pre_transition.append({
                    "kind": "PLAYER_POSITION", "id": 0,
                    "value": {
                        "x": 9, "y": 2, "group": 3, "map": 4,
                        "apply_relation":
                            "ACTUAL_STOCK_WARP_THEN_REAL_MOVEMENT",
                    },
                    "owner_keys": [owner],
                    "relation_evidence": [{
                        "operator":
                            "ACTUAL_PLAYER_COORDINATES_BEFORE_INTERACTION",
                    }],
                    "fixture_keys": [],
                })
            pre_transition.sort(key=lambda row: (row["kind"], row["id"]))
            return {
                "PRE_TRANSITION": {
                    "external": pre_transition, "internal": [],
                },
                "PRE_FIELD_INPUT": {
                    "external": [{
                        "kind": "FLAG", "id": 0x0803, "value": False,
                        "owner_keys": [owner],
                        "relation_evidence": phase_relation(
                            "PRE_FIELD_INPUT"
                        ),
                        "fixture_keys": [],
                    }, {
                        "kind": "VAR", "id": 0x4003, "value": 9,
                        "owner_keys": [owner],
                        "relation_evidence": phase_relation(
                            "PRE_FIELD_INPUT"
                        ),
                        "fixture_keys": [],
                    }],
                    "internal": [],
                },
            }

        positioned = deepcopy(stock)
        positioned["ordered_effect_instances"] = [{
            "effect_instance_ordinal": index, "dispatch_ordinal": 0,
            "owner_id": owner, "root_pc": "0x08100100",
            "effect": {
                "domain": "vars", "owner": f"VAR:0x800{4 + index:X}",
                "relation": f"COPY_CURRENT_PLAYER_{axis}",
                "instruction_address": "0x08100120",
                "execution_trace_index": 8, "opcode": "0x42",
                "abi_key": None, "group_member_ordinal": index,
            },
        } for index, axis in enumerate(("X", "Y"))]
        _validate_map_compact_controls(
            compact(positioned, include_position=True), positioned,
            "positioned", covered_owner_ids={owner},
        )
        for label, controls, lifecycle_row in (
            ("missing-position", compact(positioned, include_position=False),
             positioned),
            ("extra-position", compact(stock, include_position=True), stock),
            ("partial-position", compact(positioned, include_position=True),
             {**positioned, "ordered_effect_instances": positioned[
                 "ordered_effect_instances"
             ][:1]}),
        ):
            with self.subTest(label=label), self.assertRaises(
                Stage61CatalogStateMatrixError
            ):
                _validate_map_compact_controls(
                    controls, lifecycle_row, label,
                    covered_owner_ids={owner},
                )

        negatives = {
            "extra-nested": lambda row: row["phase_controls"][0][
                "variables"
            ][0].__setitem__("extra", True),
            "attempt-gap": lambda row: row["ordered_attempts"][2].__setitem__(
                "attempt_ordinal", 9,
            ),
            "tag2-no-quiescence": lambda row: row["ordered_attempts"][-3]
                .__setitem__("result", "DISPATCH"),
            "field-return-swap": lambda row: row["ordered_attempts"].__setitem__(
                slice(-2, None), list(reversed(row["ordered_attempts"][-2:])),
            ),
        }
        for label, mutation in negatives.items():
            broken = deepcopy(stock)
            mutation(broken)
            with self.subTest(label=label), self.assertRaises(
                Stage61CatalogStateMatrixError
            ):
                _validate_map_lifecycle_sequence(broken, label)
                _validate_map_lifecycle_order(broken, label)

        connection_with_tag4 = deepcopy(connection)
        connection_with_tag4["ordered_attempts"].insert(
            4, attempt(4, "INITIAL_WARP_IN", 4, "TAG_ABSENT"),
        )
        for ordinal, row in enumerate(connection_with_tag4["ordered_attempts"]):
            row["attempt_ordinal"] = ordinal
        connection_with_tag4["ordered_dispatches"][0]["attempt_ordinal"] += 1
        connection_with_tag4["attempt_count"] += 1
        _validate_map_lifecycle_sequence(connection_with_tag4, "connection-tag4")
        with self.assertRaises(Stage61CatalogStateMatrixError):
            _validate_map_lifecycle_order(connection_with_tag4, "connection-tag4")

    def test_dunsparce_layout_variants_use_passable_real_walk_cycles(
        self,
    ) -> None:
        runtime = _strict_walk_execution([6, 3])
        self.assertEqual(runtime["start"], [5, 3])
        self.assertEqual(runtime["walk_sequence"], ["LEFT", "RIGHT"])
        self.assertEqual(runtime["stance"], [5, 3])
        self.assertEqual(runtime["action"], "RIGHT")
        self.assertTrue(runtime["actual_walk_required"])

        static = _strict_walk_execution([23, 2])
        self.assertEqual(static["start"], [23, 1])
        self.assertEqual(static["walk_sequence"], ["LEFT", "RIGHT"])
        self.assertEqual(static["stance"], [23, 1])
        self.assertEqual(static["action"], "DOWN")
        self.assertTrue(static["actual_walk_required"])

    def test_runtime_position_root_binding_separates_coord_producer_aliases(
        self,
    ) -> None:
        rom = (
            ROOT / "build/stages/60_wild_species_root_repair.gba"
        ).read_bytes()
        state = _stage_map_state(rom, 1, 74)
        object_index = 3
        raw = state["objects"][object_index]
        fields = _object_fields(raw)
        operations = _local_object_operation_evidence(
            rom, 1, 74, state, object_index,
            int(fields["local_id"]), int.from_bytes(raw[16:20], "little"),
            int(fields["flag"]),
        )["operations"]
        position_rows = [
            row for row in operations
            if row["operation"] == "SET_OBJECT_XY_PERMANENT"
            and row.get("literal_position") == [20, 3]
        ]
        source = RUNTIME_POSITION_STATE_MAP_CONTRACTS[(1, 74)]
        evidence = _runtime_position_root_binding_evidence(
            rom, npc_id="OBJECT:001/074:003",
            canonical_root=int(source["root"]),
            control=source["control"],
            expected_aliases=source["producer_aliases"],
            position_rows=position_rows,
        )
        self.assertEqual(
            evidence["canonical_instruction_addresses"],
            ["0x087C9F45"],
        )
        self.assertEqual(
            [row["root_address"] for row in evidence["state_producer_aliases"]],
            ["0x087C9755", "0x087C9773"],
        )
        self.assertTrue(all(evidence["assertions"].values()))

        without_canonical = [
            row for row in position_rows
            if row["root_address"] != "0x087C9F20"
        ]
        with self.assertRaisesRegex(Stage61BuildError, "canonical tag3 root"):
            _runtime_position_root_binding_evidence(
                rom, npc_id="OBJECT:001/074:003",
                canonical_root=int(source["root"]), control=source["control"],
                expected_aliases=source["producer_aliases"],
                position_rows=without_canonical,
            )

        with self.assertRaisesRegex(Stage61BuildError, "alias exact"):
            _runtime_position_root_binding_evidence(
                rom, npc_id="OBJECT:001/074:003",
                canonical_root=int(source["root"]), control=source["control"],
                expected_aliases=source["producer_aliases"][:1],
                position_rows=position_rows,
            )

        wrong_flag_rom = bytearray(rom)
        wrong_flag_rom[0x087C9F0E - 0x08000000] = 0xC2
        with self.assertRaisesRegex(Stage61BuildError, "flag-before-body"):
            _runtime_position_root_binding_evidence(
                bytes(wrong_flag_rom), npc_id="OBJECT:001/074:003",
                canonical_root=int(source["root"]), control=source["control"],
                expected_aliases=source["producer_aliases"],
                position_rows=position_rows,
            )

        reversed_flag_rom = bytearray(rom)
        reversed_flag_rom[
            0x087C9F10 - 0x08000000:0x087C9F15 - 0x08000000
        ] = bytes.fromhex("2ac1110000")
        with self.assertRaisesRegex(Stage61BuildError, "flag-before-body"):
            _runtime_position_root_binding_evidence(
                bytes(reversed_flag_rom), npc_id="OBJECT:001/074:003",
                canonical_root=int(source["root"]), control=source["control"],
                expected_aliases=source["producer_aliases"],
                position_rows=position_rows,
            )

        power_state = _stage_map_state(rom, 1, 95)
        power_raw = power_state["objects"][21]
        power_fields = _object_fields(power_raw)
        power_npc = {
            "npc_id": "OBJECT:001/095:021",
            "group": 1, "map": 95, "object_index": 21,
            "local_id": int(power_fields["local_id"]),
            "script_pointer": int.from_bytes(power_raw[16:20], "little"),
            "flag": int(power_fields["flag"]),
        }
        patched_rom = bytearray(rom)
        patched_rom[
            0x0873E3FA - 0x08000000:0x0873E3FE - 0x08000000
        ] = bytes.fromhex("23000300")
        final_rows = _runtime_position_final_operation_evidence(
            bytes(patched_rom), power_npc,
        )
        self.assertEqual(
            {
                tuple(row["literal_position"])
                for row in final_rows
                if row["operation"] == "SET_OBJECT_XY_PERMANENT"
            },
            {(35, 3)},
        )

    def test_dunsparce_static_variant_uses_dug_out_layout_geometry(
        self,
    ) -> None:
        rom = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        base = _map_geometry(rom, 2, 34)
        dug_out = _map_geometry_from_layout_id(rom, 2, 34, 319)
        blockers = {(23, 2)}
        self.assertEqual(base["layout_id"], 318)
        self.assertFalse(_collision_zero(base, (23, 2)))
        self.assertFalse(_collision_zero(base, (23, 1)))
        self.assertIsNone(
            _diagnostic_walk_cycle(base, (23, 1), set(), blockers)
        )
        self.assertEqual(dug_out["layout_id"], 319)
        self.assertTrue(_collision_zero(dug_out, (23, 2)))
        self.assertTrue(_collision_zero(dug_out, (23, 1)))
        self.assertEqual(
            _diagnostic_walk_cycle(dug_out, (23, 1), set(), blockers),
            ["LEFT", "RIGHT"],
        )

    def test_dunsparce_layout_variant_binding_fails_closed(self) -> None:
        rom = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        source = RUNTIME_POSITION_STATE_MAP_CONTRACTS[(2, 34)]
        evidence = _runtime_position_layout_variant_evidence(
            rom, 2, 34, source,
        )
        self.assertIsNotNone(evidence)
        self.assertEqual(
            [row["layout_id"] for row in evidence["variants"]],
            [319, 318],
        )
        self.assertTrue(all(evidence["assertions"].values()))

        wrong_action = bytearray(rom)
        wrong_action[0x0816EB9F - 0x08000000] = 0x3E
        with self.assertRaisesRegex(Stage61BuildError, "layout action"):
            _runtime_position_layout_variant_evidence(
                bytes(wrong_action), 2, 34, source,
            )

        wrong_layout_entry = bytearray(rom)
        layouts_root = struct.unpack_from(
            "<I", wrong_layout_entry, 0x00054A54,
        )[0]
        entry_318 = layouts_root - 0x08000000 + (318 - 1) * 4
        entry_319 = layouts_root - 0x08000000 + (319 - 1) * 4
        wrong_layout_entry[entry_319:entry_319 + 4] = (
            wrong_layout_entry[entry_318:entry_318 + 4]
        )
        with self.assertRaisesRegex(Stage61BuildError, "pointer/hash drift"):
            _runtime_position_layout_variant_evidence(
                bytes(wrong_layout_entry), 2, 34, source,
            )

    def test_retained_artifact_manifest_rereads_exact_disk_tree(self) -> None:
        rom_sha = "a" * 64
        case_hashes = {
            case_id: hashlib.sha256(case_id.encode("ascii")).hexdigest()
            for case_id in MGBA_REQUIRED_CASES
        }
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            report = workspace / "reports" / "stage61.json"
            report.parent.mkdir(parents=True)
            report.write_text("{}", encoding="utf-8")
            retained = workspace / "retained"
            retained.mkdir()
            entries = []

            def add_entry(
                relative_path: str, raw: bytes, *, case_id: str | None,
                role: str,
            ) -> None:
                path = retained / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                body = {
                    "case_id": case_id, "role": role,
                    "relative_path": relative_path, "size": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "binding_sha256": rom_sha if case_id is None
                    else case_hashes[case_id],
                }
                entries.append({
                    "entry_id": "artifact-entry-"
                    + _mgba_binding_sha256(body), **body,
                })

            add_entry(
                "shared/runner_identity.bin", b"runner-identity",
                case_id=None, role="ROM_BOUND_RUNNER_IDENTITY",
            )
            for index, case_id in enumerate(MGBA_REQUIRED_CASES):
                add_entry(
                    f"cases/{index:02d}.json",
                    json.dumps({"case": case_id}, sort_keys=True).encode(),
                    case_id=case_id, role="CASE_RAW_RESULT",
                )
            entries.sort(key=lambda row: row["relative_path"])

            tree_sha = _mgba_binding_sha256(entries)
            manifest = {
                "schema_version": 1,
                "kind": "STAGE61_MGBA_RETAINED_ARTIFACT_MANIFEST_V1",
                "rom_sha256": rom_sha,
                "case_result_sha256s": case_hashes,
                "entries": entries, "tree_sha256": tree_sha,
            }
            manifest["manifest_sha256"] = _mgba_binding_sha256(manifest)
            raw = json.dumps(
                manifest, ensure_ascii=True, sort_keys=True,
                separators=(",", ":"),
            ).encode("ascii")
            manifest_path = retained / "artifact_manifest.json"
            manifest_path.write_bytes(raw)
            retention = {
                "schema_version": 1,
                "kind": "STAGE61_MGBA_ARTIFACT_RETENTION_V1",
                "root_relative_path": "retained",
                "manifest_relative_path": "artifact_manifest.json",
                "manifest_size": len(raw),
                "manifest_file_sha256": hashlib.sha256(raw).hexdigest(),
                "tree_sha256": tree_sha,
                "entry_count": len(entries),
                "entry_ids": [row["entry_id"] for row in entries],
            }
            validated = _validate_mgba_retained_artifact_manifest(
                retention, report_path=report, rom_sha256=rom_sha,
                case_result_sha256s=case_hashes,
                workspace_root=workspace,
            )
            self.assertEqual(validated["entry_count"], len(entries))
            self.assertTrue(validated["rom_bound"])

            leaf = retained / entries[0]["relative_path"]
            original = leaf.read_bytes()
            leaf.write_bytes(original + b"tamper")
            with self.assertRaisesRegex(Stage61BuildError, "leaf実体"):
                _validate_mgba_retained_artifact_manifest(
                    retention, report_path=report, rom_sha256=rom_sha,
                    case_result_sha256s=case_hashes,
                    workspace_root=workspace,
                )
            leaf.write_bytes(original)

            extra = retained / "unlisted.bin"
            extra.write_bytes(b"unlisted")
            with self.assertRaisesRegex(Stage61BuildError, "leaf集合"):
                _validate_mgba_retained_artifact_manifest(
                    retention, report_path=report, rom_sha256=rom_sha,
                    case_result_sha256s=case_hashes,
                    workspace_root=workspace,
                )
            extra.unlink()

            wrong_binding = dict(case_hashes)
            wrong_binding[MGBA_REQUIRED_CASES[0]] = "f" * 64
            with self.assertRaisesRegex(Stage61BuildError, "source binding"):
                _validate_mgba_retained_artifact_manifest(
                    retention, report_path=report, rom_sha256=rom_sha,
                    case_result_sha256s=wrong_binding,
                    workspace_root=workspace,
                )

    def test_runtime_toolchain_manifest_is_complete_and_abi_closed(self) -> None:
        implicit_cc1_output = ROOT / "<stdin>.s"
        self.assertFalse(
            implicit_cc1_output.exists(),
            "toolchain identity test must start without an implicit cc1 leaf",
        )
        _code, _symbols, _nm, manifest = _compile_runtime(
            Path(
                "overlays/stage61_display_npc_event_audit/"
                "stage61_display_npc_event_audit.c"
            ),
            0x09E00000,
            {
                "STAGE61_KANTO_NAME_TABLE": 0x09D00000,
                "STAGE61_TRAINER_REMATCH_ALIAS_TABLE": 0x09D01000,
                "STAGE61_TRAINER_REMATCH_ALIAS_COUNT": 1,
                "STAGE61_CHANGEKIT_GET_REMATCH": 0x09302DD9,
            },
        )
        self.assertFalse(
            implicit_cc1_output.exists(),
            "cc1 identity probing must not write into the workspace",
        )
        _validate_runtime_toolchain_manifest(manifest)
        self.assertFalse(
            implicit_cc1_output.exists(),
            "toolchain revalidation must remain workspace-side-effect-free",
        )
        self.assertEqual(
            set(manifest["tools"]),
            {"gcc", "nm", "objcopy", "objdump", "ld"},
        )
        self.assertEqual(
            set(manifest["internal_tools"]), {"as", "cc1", "collect2"},
        )
        for identity in [
            *manifest["tools"].values(),
            *manifest["internal_tools"].values(),
        ]:
            self.assertEqual(len(identity["binary_sha256"]), 64)
            self.assertEqual(len(identity["version"]["stdout_sha256"]), 64)
            self.assertTrue(Path(identity["resolved_realpath"]).is_absolute())
        self.assertEqual(len(manifest["libgcc"]["binary_sha256"]), 64)
        self.assertEqual(
            set(manifest["compiler_queries"]), {
                "assembler", "cc1", "collect2", "dumpmachine",
                "dumpspecs", "include_directory", "ld", "libgcc",
                "search_directories", "sysroot",
            },
        )
        self.assertEqual(
            set(manifest["post_link_argv_canonical"]), {
                "nm_undefined", "nm_symbols", "objcopy_text",
                "objdump_sections",
            },
        )
        self.assertTrue(all(
            row["mode"] in {
                "DYNAMIC_LDD_TRANSITIVE_CLOSURE",
                "STATIC_ASSERTED_BY_LDD",
            } and len(row["closure_sha256"]) == 64
            for row in manifest["dynamic_dependency_closures"].values()
        ))
        dependencies = manifest["preprocessor_dependency_manifest"]["files"]
        self.assertTrue(any(
            Path(row["resolved_realpath"]).name == "stdint.h"
            for row in dependencies
        ))
        self.assertNotIn(
            ".local/stage61-runtime-",
            json.dumps([
                manifest["compile_argv_canonical"],
                manifest["link_argv_canonical"],
                manifest["post_link_argv_canonical"],
            ]),
        )

        def resign(document: dict) -> None:
            unsigned = json.loads(json.dumps(document))
            unsigned.pop("manifest_sha256")
            document["manifest_sha256"] = _mgba_binding_sha256(unsigned)

        wrong_abi = json.loads(json.dumps(manifest))
        wrong_abi["target_abi"]["cpu"] = "cortex-m0"
        resign(wrong_abi)
        with self.assertRaises(Stage61BuildError):
            _validate_runtime_toolchain_manifest(wrong_abi)

        injected_flag = json.loads(json.dumps(manifest))
        injected_flag["compile_argv_canonical"].insert(1, "-march=armv7-a")
        resign(injected_flag)
        with self.assertRaises(Stage61BuildError):
            _validate_runtime_toolchain_manifest(injected_flag)

        changed_dependency = json.loads(json.dumps(manifest))
        first_closure = next(iter(
            changed_dependency["dynamic_dependency_closures"].values()
        ))
        first_closure["closure_sha256"] = "0" * 64
        resign(changed_dependency)
        with self.assertRaises(Stage61BuildError):
            _validate_runtime_toolchain_manifest(changed_dependency)

        with tempfile.TemporaryDirectory() as temporary:
            linker_path = Path(temporary) / "linker.ld"
            linker_path.write_bytes(
                manifest["linker_script"]["raw"].encode("ascii")
            )
            _validate_runtime_toolchain_manifest(
                manifest, actual_linker_path=linker_path,
            )
            linker_path.write_bytes(
                manifest["linker_script"]["raw"].encode("ascii") + b"\n"
            )
            with self.assertRaisesRegex(
                Stage61BuildError, "linker script実体",
            ):
                _validate_runtime_toolchain_manifest(
                    manifest, actual_linker_path=linker_path,
                )

    def test_effect_group_key_uses_only_dynamic_command_identity(self) -> None:
        effect = {
            "execution_trace_index": 7,
            "instruction_address": "0x08123456",
            "opcode": "0x23",
            "abi_key": "SPECIAL:0042",
            "domain": "flags", "owner": "FLAG:0x1234",
            "relation": "EXACT_FINAL", "after": True,
            "proof_mode": "TEST_PROOF_MODE",
            "observer_contract": {"test": "effect-specific"},
            "group_member_ordinal": 0,
        }
        payload = {
            "runtime_root": "0x08120000",
            "execution_trace_index": 7,
            "instruction_address": "0x08123456",
            "opcode": "0x23",
            "abi_key_or_empty": "SPECIAL:0042",
        }
        expected = "effect-group-" + hashlib.sha256(json.dumps(
            payload, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")).hexdigest()
        self.assertEqual(
            _mgba_effect_group_key("0x08120000", effect), expected,
        )
        self.assertEqual(len(expected), len("effect-group-") + 64)

        # Semantics, proof/watch implementation and member order must not
        # split multiple effects emitted by one SPECIAL/NATIVE occurrence.
        semantic_mutation = json.loads(json.dumps(effect))
        semantic_mutation.update({
            "domain": "storage", "owner": "SPECIES:1",
            "relation": "ADD_MON_EXACT", "after": {"slot": 1},
            "proof_mode": "ANOTHER_PROOF_MODE",
            "observer_contract": {"different": "watch"},
            "group_member_ordinal": 99,
        })
        self.assertEqual(
            _mgba_effect_group_key("0x08120000", semantic_mutation),
            expected,
        )
        for key, value in (
            ("execution_trace_index", 8),
            ("instruction_address", "0x08123458"),
            ("opcode", "0x24"),
            ("abi_key", "NATIVE:0042"),
        ):
            mutation = json.loads(json.dumps(effect))
            mutation[key] = value
            self.assertNotEqual(
                _mgba_effect_group_key("0x08120000", mutation), expected,
            )
        self.assertNotEqual(
            _mgba_effect_group_key("0x08120002", effect), expected,
        )

        non_abi = json.loads(json.dumps(effect))
        non_abi["abi_key"] = None
        empty_payload = {**payload, "abi_key_or_empty": ""}
        self.assertEqual(
            _mgba_effect_group_key("0x08120000", non_abi),
            "effect-group-" + hashlib.sha256(json.dumps(
                empty_payload, ensure_ascii=True, sort_keys=True,
                separators=(",", ":"),
            ).encode("ascii")).hexdigest(),
        )
        for key, value in (
            ("execution_trace_index", True),
            ("instruction_address", "0x0812345a"),
            ("opcode", "0x2a"),
            ("abi_key", ""),
        ):
            broken = json.loads(json.dumps(effect))
            broken[key] = value
            with self.assertRaises(Stage61BuildError):
                _mgba_effect_group_key("0x08120000", broken)

    def test_effect_command_groups_are_strict_then_unordered_exact(self) -> None:
        def effect(
            *, trace: int, pc: str, member: int, domain: str,
            template: str,
        ) -> dict:
            row = {
                "domain": domain, "owner": f"OWNER:{domain}",
                "relation": "EXACT", "instruction_address": pc,
                "execution_trace_index": trace, "opcode": "0x25",
                "abi_key": "SPECIAL:0001",
                "group_member_ordinal": member,
                "group_key": "", "template_id": template,
            }
            row["group_key"] = _mgba_effect_group_key(
                "0x08120000", row,
            )
            return row

        first_a = effect(
            trace=4, pc="0x08120020", member=0, domain="flags",
            template="template-a",
        )
        first_b = effect(
            trace=4, pc="0x08120020", member=1, domain="vars",
            template="template-b",
        )
        second = effect(
            trace=9, pc="0x08120040", member=0, domain="items",
            template="template-c",
        )
        forward = _mgba_effect_command_groups(
            "0x08120000", [first_a, first_b, second],
        )
        reversed_members = _mgba_effect_command_groups(
            "0x08120000", [first_b, first_a, second],
        )
        self.assertEqual(forward, reversed_members)
        self.assertEqual(
            [row["execution_trace_index"] for row in forward], [4, 9],
        )
        self.assertEqual([row["effect_count"] for row in forward], [2, 1])

        mutations = []
        wrong_group = json.loads(json.dumps(first_a))
        wrong_group["group_key"] = "effect-group-" + "0" * 64
        mutations.append([wrong_group])
        duplicate_member = json.loads(json.dumps(first_b))
        duplicate_member["group_member_ordinal"] = 0
        mutations.append([first_a, duplicate_member])
        generic_observer = json.loads(json.dumps(first_a))
        generic_observer["observer_contract"] = {"generic": True}
        mutations.append([generic_observer])
        mutations.append([second, first_a])
        mutations.append([first_a, second, first_b])
        for rows in mutations:
            with self.assertRaises(Stage61BuildError):
                _mgba_effect_command_groups("0x08120000", rows)

    def test_effect_missing_inventory_resolves_direct_opcode_template(
        self,
    ) -> None:
        effect = {
            "domain": "flags", "owner": "FLAG:0x0001",
            "relation": "EXACT_FINAL",
            "instruction_address": "0x08120020",
            "execution_trace_index": 4, "opcode": "0x29",
            "abi_key": None, "group_member_ordinal": 0,
            "group_key": "", "template_id": "template-direct",
        }
        effect["group_key"] = _mgba_effect_group_key(
            "0x08120000", effect,
        )
        runtime = {
            "effect_signatures": [{
                "signature_id": "effect-direct",
                "runtime_root": "0x08120000",
                "ordered_abi_dispatches": [],
                "ordered_effects": [effect],
                "terminal_kind": "FIELD_RELEASE",
            }],
            "effect_templates": [{
                "template_id": "template-direct",
                "abi_binding": {
                    "dispatch_kind": "SCRIPT_OPCODE", "opcode": "0x29",
                },
            }],
            "effect_instances": [], "effect_case_bindings": [],
        }
        inventory = _mgba_effect_registry_missing_inventory(runtime)
        self.assertIn("SCRIPT_OPCODE:0x29", inventory["required_abi_keys"])
        self.assertEqual(inventory["missing_abi_keys"], [])

    def test_effect_case_partition_uses_final_runner_cases(self) -> None:
        runtime = {"effect_signatures": [
            {
                "signature_id": "effect-dispatch",
                "ordered_effects": [{"effect": True}],
                "ordered_abi_dispatches": [],
            },
            {
                "signature_id": "effect-empty",
                "ordered_effects": [], "ordered_abi_dispatches": [],
            },
            {
                "signature_id": "effect-zero-abi",
                "ordered_effects": [],
                "ordered_abi_dispatches": [{"effect_member_count": 0}],
            },
        ]}
        object_rows = [
            {
                "case_id": "object-visible", "interaction_expected": True,
                "runtime_control_assignment": {
                    "effect_signature_ids": ["effect-dispatch"],
                },
            },
            {
                "case_id": "object-hidden", "interaction_expected": False,
                # A sibling root assignment may advertise a dispatch, but a
                # hidden matrix case has no A attempt and stays no-dispatch.
                "runtime_control_assignment": {
                    "effect_signature_ids": ["effect-dispatch"],
                },
            },
        ]
        event_rows = [
            {
                "case_id": "event-zero-abi",
                "effect_signature_ids": ["effect-zero-abi"],
            },
            {
                "case_id": "event-empty",
                "effect_signature_ids": ["effect-empty"],
            },
        ]
        result = _mgba_effect_case_partition(
            runtime, object_rows, event_rows,
        )
        self.assertEqual(result["case_signature_ids"], {
            "event-zero-abi": ["effect-zero-abi"],
            "object-visible": ["effect-dispatch"],
        })
        self.assertEqual(
            result["no_dispatch_case_ids"],
            ["event-empty", "object-hidden"],
        )
        self.assertEqual(result["counts"], {
            "runner_case_count": 4, "dispatched_case_count": 2,
            "no_dispatch_case_count": 2,
        })
        self.assertEqual(
            set(result["case_sources"]["object-visible"]),
            {
                "source_kind", "case_contract_sha256",
                "effect_signature_ids",
            },
        )
        self.assertEqual(
            result["case_sources"]["object-visible"][
                "case_contract_sha256"
            ],
            _mgba_binding_sha256(object_rows[0]),
        )

        mixed = json.loads(json.dumps(event_rows))
        mixed[0]["effect_signature_ids"] = [
            "effect-dispatch", "effect-empty",
        ]
        with self.assertRaisesRegex(Stage61BuildError, "\u6df7\u5728"):
            _mgba_effect_case_partition(runtime, object_rows, mixed)

        unknown = json.loads(json.dumps(event_rows))
        unknown[0]["effect_signature_ids"] = ["effect-unknown"]
        with self.assertRaises(Stage61BuildError):
            _mgba_effect_case_partition(runtime, object_rows, unknown)

    def test_effect_two_layer_registry_is_closed_and_result_independent(self) -> None:
        template_core = {
            "schema_version": 1,
            "kind": "STAGE61_ABI_EFFECT_TEMPLATE_V1",
            "abi_binding": {
                "abi_key": "SPECIAL:0001", "dispatch_kind": "SPECIAL",
                "opcode": "0x25",
            },
            "input_schema": [], "snapshot_schema": [],
            "selector": {"kind": "TOTAL_INPUT_PARTITION"},
            "transition_oracle": {"kind": "DECLARATIVE_V1"},
            "completion_boundary": "SYNC_RETURN",
        }
        template_id = "effect-template-" + _mgba_oracle_canonical_sha256(
            template_core
        )
        template = {
            **template_core, "template_id": template_id,
        }
        template["template_sha256"] = _mgba_oracle_canonical_sha256(
            template
        )
        effect = {
            "domain": "flags", "owner": "FLAG:0x0001",
            "relation": "EXACT_FINAL",
            "instruction_address": "0x08120020",
            "execution_trace_index": 4, "opcode": "0x25",
            "abi_key": "SPECIAL:0001", "group_member_ordinal": 0,
            "group_key": "", "template_id": template_id,
        }
        effect["group_key"] = _mgba_effect_group_key(
            "0x08120000", effect,
        )
        watch = _mgba_effect_raw_watch({
            "address_resolver": {
                "kind": "ABSOLUTE", "space": "EWRAM",
                "address": "0x02000010",
            },
            "length": 1, "hook_pc": None, "arg_capture": [],
            "completion_boundary": "SYNC_RETURN",
        })
        expected_contract = {
            "domain": effect["domain"], "owner": effect["owner"],
            "relation": effect["relation"],
            "proof_mode": "STATE_RANGE_EXACT",
            "observer_contract": {
                "completion_boundary": "SYNC_RETURN",
                "expected_result": {
                    "capture": {"kind": "NONE"}, "value": None,
                },
                "ranges": [{
                    "watch_id": watch["watch_id"], "space": "EWRAM",
                    "resolver": "ABSOLUTE", "address": "0x02000010",
                    "length": 1, "source_owner": "TEST",
                    "source_ref": "fixture", "canonicalization": "NONE",
                }],
                "transitions": [{
                    "watch_id": watch["watch_id"], "kind": "UNCHANGED",
                }],
            },
        }
        dispatch = {
            "execution_trace_index": 4,
            "instruction_address": "0x08120020", "opcode": "0x25",
            "abi_key": "SPECIAL:0001", "dispatch_kind": "SPECIAL",
            "entry_pc": "0x08128001",
            "result_capture": {"kind": "NONE", "value": None},
            "effect_member_count": 1, "group_key": effect["group_key"],
        }
        signature_payload = {
            "runtime_root": "0x08120000",
            "ordered_abi_dispatches": [dispatch],
            "ordered_effects": [effect], "terminal_kind": "FIELD_RELEASE",
        }
        signature_id = (
            "effect-" + _mgba_oracle_canonical_sha256(
                signature_payload
            )[:24]
        )
        instance_core = {
            "schema_version": 1,
            "kind": "STAGE61_EFFECT_INSTANCE_V1",
            "template_id": template_id, "case_id": "object-case-0",
            "occurrence_kind": "EFFECT_MEMBER",
            "signature_id": signature_id, "group_member_ordinal": 0,
            "group_key": effect["group_key"],
            "fixture_binding": {
                "case_id": "object-case-0",
                "case_contract_sha256": "1" * 64,
                "control_requirements_sha256": "2" * 64,
                "runner_fixture_refs": [],
                "input_sequence_sha256": "3" * 64,
            },
            "input_values": {}, "pre_images": [],
            "selected_selector_id": "selector-0",
            "expected_contract": expected_contract,
        }
        instance_id = "effect-instance-" + _mgba_oracle_canonical_sha256(
            instance_core
        )
        instance = {**instance_core, "instance_id": instance_id}
        instance["instance_sha256"] = _mgba_oracle_canonical_sha256(
            instance
        )
        binding = {
            "occurrence_kind": "EFFECT_MEMBER",
            "case_id": "object-case-0", "signature_id": signature_id,
            "group_key": effect["group_key"], "group_member_ordinal": 0,
            "template_id": template_id, "instance_id": instance_id,
        }
        runtime = {
            "effect_templates": [template], "effect_instances": [instance],
            "effect_case_bindings": [binding],
            "effect_signatures": [{
                "signature_id": signature_id, **signature_payload,
            }],
        }
        case_signatures = {"object-case-0": [signature_id]}
        structure = _mgba_effect_registry_structure(
            runtime, runnable_case_ids=set(case_signatures),
            case_signature_ids=case_signatures,
        )
        self.assertEqual(structure["template_ids"], [template_id])
        self.assertEqual(structure["instance_ids"], [instance_id])
        self.assertEqual(structure["instance_case_ids"], ["object-case-0"])
        self.assertEqual(
            structure["effect_signature_contracts"][0][
                "command_group_count"
            ],
            1,
        )

        missing = json.loads(json.dumps(runtime))
        missing.pop("effect_templates")
        missing["effect_signatures"][0]["ordered_effects"][0].pop(
            "template_id"
        )
        missing["effect_instances"] = []
        missing["effect_case_bindings"] = []
        inventory = _mgba_effect_registry_missing_inventory(
            missing,
            runnable_case_ids={"object-case-0", "object-case-1"},
            case_signature_ids={
                "object-case-0": [signature_id],
                "object-case-1": [signature_id],
            },
        )
        self.assertFalse(inventory["complete"])
        self.assertEqual(inventory["template_count"], 0)
        self.assertEqual(inventory["instance_count"], 0)
        self.assertEqual(
            inventory["missing_abi_keys"], ["SPECIAL:0001"],
        )
        self.assertEqual(
            inventory["missing_group_keys"], [effect["group_key"]],
        )
        self.assertEqual(
            inventory["missing_runnable_case_ids"],
            ["object-case-0", "object-case-1"],
        )
        self.assertEqual(
            len(inventory["missing_case_binding_occurrences"]), 2,
        )
        self.assertEqual(
            len(inventory["inventory_sha256"]), 64,
        )
        with self.assertRaisesRegex(
            Stage61BuildError, "EFFECT_OBSERVATION_CONTRACT_MISSING",
        ):
            _mgba_effect_registry_structure(
                missing,
                runnable_case_ids={"object-case-0", "object-case-1"},
                case_signature_ids={
                    "object-case-0": [signature_id],
                    "object-case-1": [signature_id],
                },
            )

        result_selected = json.loads(json.dumps(runtime))
        broken_instance = result_selected["effect_instances"][0]
        broken_instance["expected_contract"]["observer_contract"][
            "result_selector"
        ] = {"kind": "RETURN_R0"}
        broken_instance.pop("instance_id")
        broken_instance.pop("instance_sha256")
        broken_instance["instance_id"] = (
            "effect-instance-" + _mgba_oracle_canonical_sha256(
                broken_instance
            )
        )
        broken_instance["instance_sha256"] = _mgba_oracle_canonical_sha256(
            broken_instance
        )
        result_selected["effect_case_bindings"][0]["instance_id"] = (
            broken_instance["instance_id"]
        )
        with self.assertRaisesRegex(Stage61BuildError, "observed-result"):
            _mgba_effect_registry_structure(
                result_selected, runnable_case_ids=set(case_signatures),
                case_signature_ids=case_signatures,
            )

        unused = json.loads(json.dumps(runtime))
        unused["effect_instances"] = []
        with self.assertRaises(Stage61BuildError):
            _mgba_effect_registry_structure(
                unused, runnable_case_ids=set(case_signatures),
                case_signature_ids=case_signatures,
            )

        signature_instance_leak = json.loads(json.dumps(runtime))
        signature_instance_leak["effect_signatures"][0][
            "ordered_effects"
        ][0]["instance_id"] = instance_id
        with self.assertRaises(Stage61BuildError):
            _mgba_effect_registry_structure(
                signature_instance_leak,
                runnable_case_ids=set(case_signatures),
                case_signature_ids=case_signatures,
            )

        no_effect_sentinel = json.loads(json.dumps(runtime))
        no_effect_sentinel["effect_case_bindings"][0].update({
            "occurrence_kind": "ABI_DISPATCH_NO_EFFECT",
            "group_member_ordinal": 0,
        })
        with self.assertRaises(Stage61BuildError):
            _mgba_effect_registry_structure(
                no_effect_sentinel,
                runnable_case_ids=set(case_signatures),
                case_signature_ids=case_signatures,
            )

    def test_effect_zero_member_abi_dispatch_has_null_case_binding(self) -> None:
        template_core = {
            "schema_version": 1,
            "kind": "STAGE61_ABI_EFFECT_TEMPLATE_V1",
            "abi_binding": {
                "abi_key": "NATIVE:0x08128001",
                "dispatch_kind": "NATIVE", "opcode": "0x23",
            },
            "input_schema": [], "snapshot_schema": [],
            "selector": {"kind": "TOTAL_INPUT_PARTITION"},
            "transition_oracle": {"kind": "NO_EFFECT_STATIC_V1"},
            "completion_boundary": "SYNC_RETURN",
        }
        template_id = "effect-template-" + _mgba_oracle_canonical_sha256(
            template_core
        )
        template = {**template_core, "template_id": template_id}
        template["template_sha256"] = _mgba_oracle_canonical_sha256(
            template
        )
        dispatch_identity = {
            "execution_trace_index": 2,
            "instruction_address": "0x08120010", "opcode": "0x23",
            "abi_key": "NATIVE:0x08128001",
        }
        group_key = _mgba_effect_group_key(
            "0x08120000", dispatch_identity,
        )
        dispatch = {
            **dispatch_identity, "dispatch_kind": "NATIVE",
            "entry_pc": "0x08128001",
            "result_capture": {"kind": "NONE", "value": None},
            "effect_member_count": 0, "group_key": group_key,
        }
        signature_payload = {
            "runtime_root": "0x08120000",
            "ordered_abi_dispatches": [dispatch], "ordered_effects": [],
            "terminal_kind": "FIELD_RELEASE",
        }
        signature_id = (
            "effect-" + _mgba_oracle_canonical_sha256(
                signature_payload
            )[:24]
        )
        instance_core = {
            "schema_version": 1,
            "kind": "STAGE61_EFFECT_INSTANCE_V1",
            "template_id": template_id, "case_id": "event-case-0",
            "occurrence_kind": "ABI_DISPATCH_NO_EFFECT",
            "signature_id": signature_id, "group_member_ordinal": None,
            "group_key": group_key,
            "fixture_binding": {
                "case_id": "event-case-0",
                "case_contract_sha256": "1" * 64,
                "control_requirements_sha256": "2" * 64,
                "runner_fixture_refs": [],
                "input_sequence_sha256": "3" * 64,
            },
            "input_values": {}, "pre_images": [],
            "selected_selector_id": "selector-0",
            "expected_contract": {
                "proof_mode": "NO_EFFECT",
                "static_write_set_proof": {"test": True},
            },
        }
        instance_id = "effect-instance-" + _mgba_oracle_canonical_sha256(
            instance_core
        )
        instance = {**instance_core, "instance_id": instance_id}
        instance["instance_sha256"] = _mgba_oracle_canonical_sha256(
            instance
        )
        binding = {
            "occurrence_kind": "ABI_DISPATCH_NO_EFFECT",
            "case_id": "event-case-0", "signature_id": signature_id,
            "group_key": group_key, "group_member_ordinal": None,
            "template_id": template_id, "instance_id": instance_id,
        }
        runtime = {
            "effect_templates": [template], "effect_instances": [instance],
            "effect_case_bindings": [binding],
            "effect_signatures": [{
                "signature_id": signature_id, **signature_payload,
            }],
        }
        case_signatures = {"event-case-0": [signature_id]}
        result = _mgba_effect_registry_structure(
            runtime, runnable_case_ids=set(case_signatures),
            case_signature_ids=case_signatures,
        )
        self.assertEqual(
            result["effect_signature_contracts"][0][
                "command_groups"
            ][0]["effect_count"],
            0,
        )
        self.assertIsNone(
            result["effect_case_bindings"][0]["group_member_ordinal"]
        )

        for mutate in (
            lambda value: value["effect_case_bindings"][0].update({
                "group_member_ordinal": 0,
            }),
            lambda value: value.update({"effect_case_bindings": []}),
        ):
            broken = json.loads(json.dumps(runtime))
            mutate(broken)
            with self.assertRaises(Stage61BuildError):
                _mgba_effect_registry_structure(
                    broken, runnable_case_ids=set(case_signatures),
                    case_signature_ids=case_signatures,
                )

    def test_effect_raw_watch_is_semantics_free_and_full_hash_bound(self) -> None:
        range_body = {
            "address_resolver": {
                "kind": "ABSOLUTE", "space": "EWRAM",
                "address": "0x02000010",
            },
            "length": 4, "hook_pc": "0x08123456",
            "arg_capture": [], "completion_boundary": "SYNC_RETURN",
        }
        watch = _mgba_effect_raw_watch(range_body)
        canonical = json.dumps(
            range_body, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        self.assertEqual(
            watch["watch_id"],
            "effect-watch-" + hashlib.sha256(canonical).hexdigest(),
        )
        self.assertEqual(set(watch), {"watch_id", *range_body})
        self.assertEqual(len(watch["watch_id"]), len("effect-watch-") + 64)

        hook_body = {
            "address_resolver": {"kind": "NONE"},
            "length": 0, "hook_pc": "0x08123458",
            "arg_capture": [{
                "ordinal": 0, "phase": "ENTRY", "location": "R0",
                "width_bits": 32, "capture": "VALUE",
                "pointee_length": 0,
            }],
            "completion_boundary": "TASK_TERMINAL",
        }
        self.assertTrue(
            _mgba_effect_raw_watch(hook_body)["watch_id"].startswith(
                "effect-watch-"
            )
        )
        dynamic_hook_body = {
            "address_resolver": {
                "kind": "U32_CODE_POINTER_AT",
                "pointer_slot": "0x03007420",
                "target_thumb": True,
            },
            "length": 16, "hook_pc": None,
            "arg_capture": [{
                "ordinal": 0, "phase": "ENTRY", "location": "R0",
                "width_bits": 32, "capture": "VALUE",
                "pointee_length": 0,
            }],
            "completion_boundary": "FRESH_TITLE_CONTINUE",
        }
        self.assertTrue(
            _mgba_effect_raw_watch(dynamic_hook_body)["watch_id"].startswith(
                "effect-watch-"
            )
        )
        script_cursor_body = {
            "address_resolver": {
                "kind": "SCRIPT_CURSOR_DISPATCH",
                "script_context_address": "0x03000EA8",
                "script_cursor_offset": 8,
                "opcode_register": "R1",
                "cursor_register": "R2",
                "opcode_load_pc": "0x08069118",
                "opcode_load_raw_hex": "1178",
                "hook_raw_hex": "501c",
                "handler_table_start_offset": 92,
                "handler_table_end_offset": 96,
            },
            "length": 0, "hook_pc": "0x0806911A",
            "arg_capture": [{
                "ordinal": 0, "phase": "ENTRY", "location": "R1",
                "width_bits": 8, "capture": "VALUE",
                "pointee_length": 0,
            }, {
                "ordinal": 1, "phase": "ENTRY", "location": "R2",
                "width_bits": 32, "capture": "VALUE",
                "pointee_length": 0,
            }],
            "completion_boundary": "SCRIPT_CONTEXT_RESUME",
        }
        script_cursor_watch = _mgba_effect_raw_watch(script_cursor_body)
        self.assertTrue(
            script_cursor_watch["watch_id"].startswith("effect-watch-")
        )
        for mutation in (
            lambda row: row.update({"length": 0}),
            lambda row: row.update({"hook_pc": "0x0812345a"}),
            lambda row: row.update({"completion_boundary": "UNKNOWN"}),
            lambda row: row["address_resolver"].update({
                "domain": "flags",
            }),
            lambda row: row["arg_capture"].append({
                "expected_delta": 1,
            }),
        ):
            broken = json.loads(json.dumps(range_body))
            mutation(broken)
            with self.assertRaises(Stage61BuildError):
                _mgba_effect_raw_watch(broken)

        broken_hook = json.loads(json.dumps(hook_body))
        broken_hook["hook_pc"] = None
        with self.assertRaises(Stage61BuildError):
            _mgba_effect_raw_watch(broken_hook)
        for mutation in (
            lambda row: row["address_resolver"].update({
                "target_thumb": False,
            }),
            lambda row: row["address_resolver"].update({
                "pointer_slot": "0x04000000",
            }),
            lambda row: row.update({"hook_pc": "0x08123458"}),
            lambda row: row.update({"length": 0}),
        ):
            broken_dynamic = json.loads(json.dumps(dynamic_hook_body))
            mutation(broken_dynamic)
            with self.assertRaises(Stage61BuildError):
                _mgba_effect_raw_watch(broken_dynamic)
        for mutation in (
            lambda row: row.update({"hook_pc": None}),
            lambda row: row.update({"hook_pc": "0x08069118"}),
            lambda row: row.update({"length": 1}),
            lambda row: row["address_resolver"].update({
                "script_context_address": "0x03000EAC",
            }),
            lambda row: row["address_resolver"].update({
                "script_cursor_offset": 9,
            }),
            lambda row: row["address_resolver"].update({
                "opcode_register": "R2", "cursor_register": "R1",
            }),
            lambda row: row["address_resolver"].update({
                "opcode_load_raw_hex": "1078",
            }),
            lambda row: row["address_resolver"].update({
                "handler_table_end_offset": 100,
            }),
            lambda row: row["arg_capture"][0].update({"width_bits": 16}),
            lambda row: row["arg_capture"].reverse(),
        ):
            broken_cursor = json.loads(json.dumps(script_cursor_body))
            mutation(broken_cursor)
            with self.assertRaises(Stage61BuildError):
                _mgba_effect_raw_watch(broken_cursor)

    def test_effect_validator_projection_separates_expected_and_raw_payload(
        self,
    ) -> None:
        template = {"template_id": "effect-template-test"}
        instance = {
            "instance_id": "effect-instance-test",
            "case_id": "case-test",
        }
        watch = _mgba_effect_raw_watch({
            "address_resolver": {
                "kind": "ABSOLUTE", "space": "EWRAM",
                "address": "0x02000010",
            },
            "length": 4, "hook_pc": None, "arg_capture": [],
            "completion_boundary": "SYNC_RETURN",
        })
        unsigned_plan = {
            "schema_version": 1,
            "kind": "STAGE61_EFFECT_RAW_WATCH_PLAN_V1",
            "watches": [watch],
        }
        raw_plan = {
            **unsigned_plan,
            "plan_sha256": _mgba_oracle_canonical_sha256(unsigned_plan),
        }
        case_binding = {
            "occurrence_kind": "EFFECT_MEMBER",
            "case_id": "case-test", "signature_id": "effect-test",
            "group_key": "effect-group-" + "1" * 64,
            "group_member_ordinal": 0,
            "template_id": template["template_id"],
            "instance_id": instance["instance_id"],
        }
        partition = {
            "case_signature_ids": {"case-test": ["effect-test"]},
            "no_dispatch_case_ids": [],
        }
        validation = {
            "templates": [template], "instances": [instance],
            "effect_case_bindings": [case_binding],
            "no_dispatch_contracts": [],
            "instance_watch_bindings": [{
                "instance_id": instance["instance_id"],
                "watch_ids": [watch["watch_id"]],
            }],
            "no_dispatch_watch_bindings": [],
            "raw_watch_plan": raw_plan,
            "counts": {
                "template_count": 1, "instance_count": 1,
                "dispatched_case_count": 1,
                "no_dispatch_case_count": 0,
                "runner_case_count": 1, "occurrence_count": 1,
                "raw_watch_count": 1,
            },
        }
        (
            bindings, no_dispatch_contracts,
            no_dispatch_bindings, projected_plan,
        ) = _mgba_effect_validator_projection(
            validation,
            expected_templates=[template], expected_instances=[instance],
            expected_case_bindings=[case_binding],
            expected_case_partition=partition,
        )
        self.assertEqual(bindings, validation["instance_watch_bindings"])
        self.assertEqual(no_dispatch_contracts, [])
        self.assertEqual(no_dispatch_bindings, [])
        self.assertEqual(projected_plan, raw_plan)
        self.assertFalse(any(
            key in json.dumps(projected_plan, sort_keys=True)
            for key in (
                "domain", "owner", "relation", "template_id",
                "instance_id", "group_key", "expected",
            )
        ))

        for mutate in (
            lambda value: value["raw_watch_plan"]["watches"][0].update({
                "domain": "flags",
            }),
            lambda value: value["instance_watch_bindings"][0].update({
                "watch_ids": [],
            }),
            lambda value: value["counts"].update({"raw_watch_count": 2}),
        ):
            broken = json.loads(json.dumps(validation))
            mutate(broken)
            with self.assertRaises(Stage61BuildError):
                _mgba_effect_validator_projection(
                    broken,
                    expected_templates=[template],
                    expected_instances=[instance],
                    expected_case_bindings=[case_binding],
                    expected_case_partition=partition,
                )

    def test_effect_validator_projection_binds_no_dispatch_contract(
        self,
    ) -> None:
        watch = _mgba_effect_raw_watch({
            "address_resolver": {
                "kind": "ABSOLUTE", "space": "EWRAM",
                "address": "0x02000020",
            },
            "length": 4, "hook_pc": None, "arg_capture": [],
            "completion_boundary": "FIELD_RELEASE",
        })
        unsigned_plan = {
            "schema_version": 1,
            "kind": "STAGE61_EFFECT_RAW_WATCH_PLAN_V1",
            "watches": [watch],
        }
        contract = {
            "schema_version": 1,
            "kind": "STAGE61_NO_DISPATCH_CONTRACT_V1",
            "case_id": "hidden-case", "signature_ids": [],
            "fixture_binding": {"test": True},
            "completion_boundary": "FIELD_RELEASE",
            "owner_watch_ids": [watch["watch_id"]],
            "forbidden_hook_watch_ids": [],
            "expected_observation": {
                "all_owner_ranges_unchanged": True,
            },
        }
        contract["contract_sha256"] = _mgba_oracle_canonical_sha256(
            contract
        )
        no_dispatch_binding = {
            "case_id": "hidden-case",
            "contract_sha256": contract["contract_sha256"],
            "watch_ids": [watch["watch_id"]],
        }
        validation = {
            "templates": [], "instances": [], "effect_case_bindings": [],
            "no_dispatch_contracts": [contract],
            "instance_watch_bindings": [],
            "no_dispatch_watch_bindings": [no_dispatch_binding],
            "raw_watch_plan": {
                **unsigned_plan,
                "plan_sha256": _mgba_oracle_canonical_sha256(
                    unsigned_plan
                ),
            },
            "counts": {
                "template_count": 0, "instance_count": 0,
                "dispatched_case_count": 0,
                "no_dispatch_case_count": 1,
                "runner_case_count": 1, "occurrence_count": 0,
                "raw_watch_count": 1,
            },
        }
        partition = {
            "case_signature_ids": {},
            "no_dispatch_case_ids": ["hidden-case"],
        }
        projected = _mgba_effect_validator_projection(
            validation, expected_templates=[], expected_instances=[],
            expected_case_bindings=[], expected_case_partition=partition,
        )
        self.assertEqual(projected[1], [contract])
        self.assertEqual(projected[2], [no_dispatch_binding])

        for mutation in (
            lambda row: row["no_dispatch_contracts"][0].update({
                "contract_sha256": "0" * 64,
            }),
            lambda row: row.update({"no_dispatch_watch_bindings": []}),
            lambda row: row["counts"].update({
                "no_dispatch_case_count": 0,
            }),
        ):
            broken = json.loads(json.dumps(validation))
            mutation(broken)
            with self.assertRaises(Stage61BuildError):
                _mgba_effect_validator_projection(
                    broken, expected_templates=[], expected_instances=[],
                    expected_case_bindings=[],
                    expected_case_partition=partition,
                )

    def test_effect_registry_source_binding_recomputes_all_artifacts(
        self,
    ) -> None:
        signature_payload = {
            "runtime_root": "0x08120000",
            "ordered_abi_dispatches": [], "ordered_effects": [],
            "terminal_kind": "FIELD_RELEASE",
        }
        signature_id = (
            "effect-" + _mgba_oracle_canonical_sha256(
                signature_payload
            )[:24]
        )
        watch = _mgba_effect_raw_watch({
            "address_resolver": {
                "kind": "ABSOLUTE", "space": "EWRAM",
                "address": "0x02000020",
            },
            "length": 4, "hook_pc": None, "arg_capture": [],
            "completion_boundary": "FIELD_RELEASE",
        })
        contract = {
            "schema_version": 1,
            "kind": "STAGE61_NO_DISPATCH_CONTRACT_V1",
            "case_id": "hidden-case", "signature_ids": [],
            "fixture_binding": {"test": True},
            "completion_boundary": "FIELD_RELEASE",
            "owner_watch_ids": [watch["watch_id"]],
            "forbidden_hook_watch_ids": [],
            "expected_observation": {
                "all_owner_ranges_unchanged": True,
            },
        }
        contract["contract_sha256"] = _mgba_oracle_canonical_sha256(
            contract
        )
        no_dispatch_binding = {
            "case_id": "hidden-case",
            "contract_sha256": contract["contract_sha256"],
            "watch_ids": [watch["watch_id"]],
        }
        runtime = {
            "effect_signatures": [{
                "signature_id": signature_id, **signature_payload,
            }],
            "effect_templates": [], "effect_instances": [],
            "effect_case_bindings": [],
            "effect_instance_watch_bindings": [],
            "no_dispatch_contracts": [contract],
            "no_dispatch_watch_bindings": [no_dispatch_binding],
        }
        object_rows = [{
            "case_id": "hidden-case", "interaction_expected": False,
            "runtime_control_assignment": {
                "effect_signature_ids": [signature_id],
            },
        }]
        unsigned_plan = {
            "schema_version": 1,
            "kind": "STAGE61_EFFECT_RAW_WATCH_PLAN_V1",
            "watches": [watch],
        }
        raw_plan = {
            **unsigned_plan,
            "plan_sha256": _mgba_oracle_canonical_sha256(unsigned_plan),
        }
        binding = _mgba_effect_registry_source_binding(
            runtime, object_rows, [], raw_plan,
        )
        self.assertEqual(binding["dispatched_case_ids"], [])
        self.assertEqual(binding["no_dispatch_case_ids"], ["hidden-case"])
        self.assertEqual(binding["watch_ids"], [watch["watch_id"]])
        self.assertEqual(binding["counts"]["no_dispatch_case_count"], 1)
        unsigned_binding = json.loads(json.dumps(binding))
        declared = unsigned_binding.pop("binding_sha256")
        self.assertEqual(declared, _mgba_binding_sha256(unsigned_binding))

        for mutation in (
            lambda row: row["no_dispatch_watch_bindings"][0].update({
                "watch_ids": [],
            }),
            lambda row: row["no_dispatch_contracts"][0].update({
                "contract_sha256": "0" * 64,
            }),
        ):
            broken = json.loads(json.dumps(runtime))
            mutation(broken)
            with self.assertRaises(Stage61BuildError):
                _mgba_effect_registry_source_binding(
                    broken, object_rows, [], raw_plan,
                )
        broken_plan = json.loads(json.dumps(raw_plan))
        broken_plan["watches"][0]["length"] = 3
        with self.assertRaises(Stage61BuildError):
            _mgba_effect_registry_source_binding(
                runtime, object_rows, [], broken_plan,
            )
        already_projected = json.loads(json.dumps(object_rows[0]))
        already_projected["effect_source_key"] = {
            "source_case_id": "hidden-case", "sequence_id": None,
        }
        with self.assertRaisesRegex(
            Stage61BuildError, "既にexecution射影済み",
        ):
            _mgba_effect_registry_source_binding(
                runtime, [already_projected], [], raw_plan,
            )

    def test_effect_signature_rebind_preserves_explicit_observer_exactly(
        self,
    ) -> None:
        observer = {
            "completion_boundary": "SYNC_RETURN",
            "expected_result": {"capture": {"kind": "NONE"}, "value": None},
            "ranges": [], "transitions": [],
        }
        effect = {
            "domain": "flags", "owner": "FLAG:0x0001",
            "relation": "EXACT_FINAL",
            "instruction_address": "0x08120020",
            "execution_trace_index": 1, "opcode": "0x25",
            "abi_key": "SPECIAL:0001", "group_member_ordinal": 0,
            "group_key": "effect-group-" + "1" * 64,
            "source_observer_contract": {
                "proof_mode": "STATE_RANGE_EXACT",
                "observer_contract": observer,
            },
        }
        old = {
            "signature_id": "effect-old",
            "runtime_root": "0x08120000",
            "ordered_abi_dispatches": [],
            "ordered_effects": [effect],
            "terminal_kind": "FIELD_RELEASE",
        }
        public_effect = {
            key: deepcopy(value) for key, value in effect.items()
            if key != "source_observer_contract"
        }
        public_effect["template_id"] = "template-1"
        payload = {
            "runtime_root": old["runtime_root"],
            "ordered_abi_dispatches": [],
            "ordered_effects": [public_effect],
            "terminal_kind": old["terminal_kind"],
        }
        new_id = "effect-" + _mgba_oracle_canonical_sha256(payload)[:24]
        new = {"signature_id": new_id, **payload}
        source_effect = {
            key: deepcopy(value) for key, value in effect.items()
            if key != "source_observer_contract"
        }
        template = {
            "template_id": "template-1",
            "transition_oracle": {
                "effect_identity": {
                    "domain": effect["domain"], "owner": effect["owner"],
                    "relation": effect["relation"],
                    "proof_mode": "STATE_RANGE_EXACT",
                },
                "source_effect": {
                    "kind": "EFFECT_MEMBER", "effect": source_effect,
                    "observer_contract": deepcopy(observer),
                },
            },
        }
        rebindings = [{
            "old_signature_id": "effect-old", "new_signature_id": new_id,
        }]
        _mgba_validate_effect_signature_rebinding(
            [old], [new], rebindings, [template],
        )
        broken = deepcopy(template)
        broken["transition_oracle"]["source_effect"][
            "observer_contract"
        ]["completion_boundary"] = "FIELD_RELEASE"
        with self.assertRaises(Stage61BuildError):
            _mgba_validate_effect_signature_rebinding(
                [old], [new], rebindings, [broken],
            )

    def test_effect_signature_rebind_rederives_default_observer_exactly(
        self,
    ) -> None:
        rom = bytearray(0x200)
        rom[0x40] = 0x23
        rom[0x50] = 0x23
        rom[0x100:0x102] = b"\x00\x47"
        code_sha = hashlib.sha256(b"\x00\x47").hexdigest()
        abi_key = "NATIVE:0x08000101"
        group_key = "effect-group-" + "1" * 64
        effect = {
            "domain": "flags", "owner": "FLAG:0x0001",
            "relation": "EXACT_FINAL",
            "instruction_address": "0x08000040",
            "execution_trace_index": 1, "opcode": "0x23",
            "abi_key": abi_key, "group_member_ordinal": 0,
            "group_key": group_key, "after": True,
        }
        dispatch = {
            "execution_trace_index": 1,
            "instruction_address": "0x08000040",
            "opcode": "0x23", "abi_key": abi_key,
            "dispatch_kind": "NATIVE", "entry_pc": "0x08000100",
            "result_capture": {"kind": "NONE", "value": None},
            "effect_member_count": 1, "group_key": group_key,
        }
        old = {
            "signature_id": "effect-old-default",
            "runtime_root": "0x08000020",
            "ordered_abi_dispatches": [dispatch],
            "ordered_effects": [effect],
            "terminal_kind": "FIELD_RELEASE",
        }
        manifest = {
            "special_abis": [],
            "native_abis": [{
                "abi_key": abi_key, "execution": "SYNC",
            }],
        }
        template = {
            "template_id": "template-default",
            "abi_binding": {
                "abi_key": abi_key, "dispatch_kind": "NATIVE",
                "opcode": "0x23", "entry_pc": "0x08000100",
                "code_span": {
                    "start": "0x08000100", "length": 2,
                    "sha256": code_sha,
                },
                "source_provenance_sha256": "d" * 64,
            },
            "transition_oracle": {
                "effect_identity": {
                    "domain": effect["domain"], "owner": effect["owner"],
                    "relation": effect["relation"],
                    "proof_mode": "CALL_SINK_EXACT",
                },
                "source_effect": {
                    "kind": "EFFECT_MEMBER",
                    "effect": {
                        key: deepcopy(value) for key, value in effect.items()
                    },
                    "observer_contract": {},
                },
            },
        }
        template["transition_oracle"]["source_effect"]["observer_contract"] = (
            _mgba_expected_default_effect_observer(
                old, effect, template, stage61_rom=bytes(rom),
                interaction_abi_manifest=manifest,
            )
        )
        public_effect = {
            key: deepcopy(effect[key]) for key in (
                "domain", "owner", "relation", "instruction_address",
                "execution_trace_index", "opcode", "abi_key",
                "group_member_ordinal", "group_key",
            )
        }
        public_effect["template_id"] = template["template_id"]
        payload = {
            "runtime_root": old["runtime_root"],
            "ordered_abi_dispatches": [dispatch],
            "ordered_effects": [public_effect],
            "terminal_kind": old["terminal_kind"],
        }
        new_id = "effect-" + _mgba_oracle_canonical_sha256(payload)[:24]
        new = {"signature_id": new_id, **payload}
        rebindings = [{
            "old_signature_id": old["signature_id"],
            "new_signature_id": new_id,
        }]
        _mgba_validate_effect_signature_rebinding(
            [old], [new], rebindings, [template],
            stage61_rom=bytes(rom), interaction_abi_manifest=manifest,
        )

        broken = deepcopy(template)
        observer = broken["transition_oracle"]["source_effect"][
            "observer_contract"
        ]
        observer["sinks"][0]["caller_instruction_addresses"] = [
            "0x08000050"
        ]
        observer["expected_calls"][0][
            "caller_instruction_address"
        ] = "0x08000050"
        with self.assertRaisesRegex(
            Stage61BuildError, "default observer semantic drift",
        ):
            _mgba_validate_effect_signature_rebinding(
                [old], [new], rebindings, [broken],
                stage61_rom=bytes(rom),
                interaction_abi_manifest=manifest,
            )

        variable_result_cases = ({
            "kind": "GLOBAL_VAR_RESULT",
            "selector": {
                "kind": "GLOBAL_VAR_RESULT", "address": "0x02037004",
                "width_bits": 16,
            },
        }, {
            "kind": "SPECIALVAR_DEST",
            "selector": {
                "kind": "SPECIALVAR_DEST", "script_operand_offset": 1,
                "width_bits": 16,
            },
        })
        for result_case in variable_result_cases:
            with self.subTest(result_kind=result_case["kind"]):
                capture = {
                    "kind": result_case["kind"], "source_id": 0x8004,
                    "target_id": 0x4000, "value": 0x1234,
                }
                captured_old = deepcopy(old)
                captured_old["ordered_abi_dispatches"][0][
                    "result_capture"
                ] = capture
                captured_template = deepcopy(template)
                captured_observer = _mgba_expected_default_effect_observer(
                    captured_old, captured_old["ordered_effects"][0],
                    captured_template, stage61_rom=bytes(rom),
                    interaction_abi_manifest=manifest,
                )
                captured_template["transition_oracle"]["source_effect"][
                    "observer_contract"
                ] = captured_observer
                self.assertEqual(
                    captured_observer["expected_result"],
                    {
                        "capture": result_case["selector"],
                        "value": capture["value"],
                    },
                )
                captured_payload = {
                    "runtime_root": captured_old["runtime_root"],
                    "ordered_abi_dispatches": deepcopy(
                        captured_old["ordered_abi_dispatches"]
                    ),
                    "ordered_effects": [deepcopy(public_effect)],
                    "terminal_kind": captured_old["terminal_kind"],
                }
                captured_new_id = "effect-" + (
                    _mgba_oracle_canonical_sha256(captured_payload)[:24]
                )
                captured_new = {
                    "signature_id": captured_new_id, **captured_payload,
                }
                captured_rebindings = [{
                    "old_signature_id": captured_old["signature_id"],
                    "new_signature_id": captured_new_id,
                }]
                _mgba_validate_effect_signature_rebinding(
                    [captured_old], [captured_new], captured_rebindings,
                    [captured_template], stage61_rom=bytes(rom),
                    interaction_abi_manifest=manifest,
                )

                mismatched_template = deepcopy(captured_template)
                mismatched_template["transition_oracle"]["source_effect"][
                    "observer_contract"
                ]["expected_result"]["value"] ^= 1
                with self.assertRaisesRegex(
                    Stage61BuildError, "default observer semantic drift",
                ):
                    _mgba_validate_effect_signature_rebinding(
                        [captured_old], [captured_new], captured_rebindings,
                        [mismatched_template], stage61_rom=bytes(rom),
                        interaction_abi_manifest=manifest,
                    )

                invalid_captures = {
                    "missing": {
                        key: value for key, value in capture.items()
                        if key != "target_id"
                    },
                    "extra": {**capture, "unexpected": 0},
                    "type": {**capture, "source_id": True},
                }
                for invalid_kind, invalid_capture in invalid_captures.items():
                    with self.subTest(invalid=invalid_kind), \
                            self.assertRaisesRegex(
                                Stage61BuildError,
                                "variable result capture不正",
                            ):
                        invalid_old = deepcopy(captured_old)
                        invalid_old["ordered_abi_dispatches"][0][
                            "result_capture"
                        ] = invalid_capture
                        _mgba_expected_default_effect_observer(
                            invalid_old, invalid_old["ordered_effects"][0],
                            captured_template, stage61_rom=bytes(rom),
                            interaction_abi_manifest=manifest,
                        )

    def test_bill_sevii_guard_sources_are_runtime_pinned_blobs(self) -> None:
        source_blobs, _ = _interaction_abi_pinned_inputs()
        expected_paths = {
            path.as_posix() for path in BILL_SEVII_SOURCE_EVIDENCE_PATHS
        }
        self.assertTrue(expected_paths <= set(source_blobs))
        for relative in BILL_SEVII_SOURCE_EVIDENCE_PATHS:
            self.assertEqual(
                source_blobs[relative.as_posix()],
                (ROOT / relative).read_bytes(),
            )

    def test_bg_numeric_zero_consumer_returns_null_with_branch_preserved(
        self,
    ) -> None:
        stage60 = (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes()
        patch_offset = BG_NUMERIC_ZERO_RETURN_PATCH_ADDRESS - 0x08000000
        branch_offset = BG_NUMERIC_ZERO_RETURN_BRANCH_ADDRESS - 0x08000000
        self.assertEqual(
            stage60[patch_offset:patch_offset + 2],
            BG_NUMERIC_ZERO_RETURN_PATCH_PREIMAGE,
        )
        self.assertEqual(
            stage60[branch_offset:branch_offset + 2],
            BG_NUMERIC_ZERO_RETURN_BRANCH_PREIMAGE,
        )

        output = bytearray(stage60)
        declarations: list[dict] = []
        report = _apply_bg_numeric_zero_return_patch(
            stage60, output, declarations,
        )
        self.assertEqual(
            output[patch_offset:patch_offset + 2],
            BG_NUMERIC_ZERO_RETURN_PATCH_REPLACEMENT,
        )
        self.assertEqual(
            output[branch_offset:branch_offset + 2],
            BG_NUMERIC_ZERO_RETURN_BRANCH_PREIMAGE,
        )
        self.assertEqual(len(declarations), 1)
        self.assertEqual(declarations[0]["start"], patch_offset)
        self.assertEqual(declarations[0]["size"], 2)
        self.assertEqual(
            report["semantic_contract"], "NUMERIC_ZERO_BG_RETURNS_NULL",
        )
        self.assertEqual(
            report["source_provenance"]["project_policy"],
            EVENT_CONSUMER_SOURCE_CONTRACT["project_policy"],
        )
        self.assertTrue(all(report["assertions"].values()))

        fixture_size = branch_offset + 2
        valid_fixture = bytearray(fixture_size)
        valid_fixture[patch_offset:patch_offset + 2] = (
            BG_NUMERIC_ZERO_RETURN_PATCH_PREIMAGE
        )
        valid_fixture[branch_offset:branch_offset + 2] = (
            BG_NUMERIC_ZERO_RETURN_BRANCH_PREIMAGE
        )
        for mutation_offset in (patch_offset, branch_offset):
            mutated = bytearray(valid_fixture)
            mutated[mutation_offset] ^= 0x01
            with self.assertRaises(Stage61BuildError):
                _apply_bg_numeric_zero_return_patch(
                    bytes(mutated), bytearray(mutated), [],
                )

        premodified_output = bytearray(valid_fixture)
        premodified_output[patch_offset:patch_offset + 2] = (
            BG_NUMERIC_ZERO_RETURN_PATCH_REPLACEMENT
        )
        with self.assertRaises(Stage61BuildError):
            _apply_bg_numeric_zero_return_patch(
                bytes(valid_fixture), premodified_output, [],
            )

    def test_runtime_control_exact_party_rng_and_coin_domains(self) -> None:
        party_ref = "1" * 64
        storage_ref = "2" * 64
        self.assertEqual(
            _runtime_control_value({
                "kind": "PARTY_MOVE",
                "value": {
                    "move_id": 15, "expected_slot": 6,
                    "party_layout_ref": party_ref,
                },
            }, "party move"),
            {
                "move_id": 15, "expected_slot": 6,
                "party_layout_ref": party_ref,
            },
        )
        for result in (0, 1, 2):
            self.assertEqual(
                _runtime_control_value({
                    "kind": "PARTY_OR_STORAGE_CAPACITY",
                    "value": {
                        "expected_result": result,
                        "party_layout_ref": party_ref,
                        "storage_layout_ref": storage_ref,
                    },
                }, "give mon/egg")["expected_result"],
                result,
            )
        self.assertEqual(
            _runtime_control_value({
                "kind": "COINS",
                "value": {"vega": 9999, "cfru": 0xFFFFFFFF},
            }, "coins")["vega"],
            9999,
        )
        seed = 0
        maximum = 7
        modulo = (((seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF) >> 16) \
            % maximum
        self.assertEqual(
            _runtime_control_value({
                "kind": "RNG",
                "value": {
                    "state": seed, "maximum": maximum,
                    "expected_modulo": modulo,
                },
            }, "rng")["expected_modulo"],
            modulo,
        )
        pokedex = {
            "scenario_id": "kanto-complete-national-enabled",
            "national_enabled": True,
            "kanto_seen": 150, "kanto_caught": 150,
            "national_seen": 380, "national_caught": 380,
            "mew_caught": False, "has_all_required": True,
            "layout_ref": "3" * 64,
        }
        self.assertEqual(
            _runtime_control_value({
                "kind": "POKEDEX_STATE", "value": pokedex,
            }, "pokedex"),
            pokedex,
        )
        for bad in (
            {
                "kind": "PARTY_MOVE",
                "value": {
                    "move_id": 15, "expected_slot": 0x7F,
                    "party_layout_ref": party_ref,
                },
            },
            {
                "kind": "PARTY_OR_STORAGE_CAPACITY",
                "value": {
                    "expected_result": True,
                    "party_layout_ref": party_ref,
                    "storage_layout_ref": storage_ref,
                },
            },
            {
                "kind": "COINS", "value": {"vega": 10000, "cfru": 0},
            },
            {
                "kind": "POKEDEX_STATE",
                "value": {**pokedex, "national_caught": 379},
            },
            {
                "kind": "POKEDEX_STATE",
                "value": {**pokedex, "kanto_seen": True},
            },
        ):
            with self.assertRaises(Stage61CatalogStateMatrixError):
                _runtime_control_value(bad, "bad")

    def test_berry_powder_is_exact_physical_scalar_control(self) -> None:
        def row(value: object = 0) -> dict:
            return {
                "kind": "BERRY_POWDER", "id": 0, "value": value,
                "owner_keys": ["OBJECT:007/009:000"],
                "fixture_keys": [],
                "relation_evidence": [{
                    "operator": "EXACT_DECRYPTED_BERRY_POWDER",
                }],
            }

        for value in (0, 99999):
            with self.subTest(value=value):
                required = row(value)
                self.assertEqual(
                    _runtime_control_value(required, "berry-powder"),
                    value,
                )
                self.assertEqual(
                    _runtime_assignment_map(
                        {"required_values": [required]}, "berry-assignment",
                    ),
                    {("BERRY_POWDER", 0): required},
                )

        for label, mutate in {
            "missing-relation": lambda value: value.pop(
                "relation_evidence"
            ),
            "extra-relation": lambda value: value[
                "relation_evidence"
            ].append({"operator": "FORGED"}),
            "wrong-relation": lambda value: value.update({
                "relation_evidence": [{"operator": "FORGED"}],
            }),
            "wrong-id": lambda value: value.update({"id": 1}),
            "fixture-key": lambda value: value.update({
                "fixture_keys": ["0" * 64],
            }),
            "wrong-kind": lambda value: value.update({
                "kind": "BERRY_POWDERS",
            }),
        }.items():
            broken = row()
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                Stage61CatalogStateMatrixError,
            ):
                _runtime_assignment_map(
                    {"required_values": [broken]}, label,
                )

        for value in (True, "1", -1, 100000):
            with self.subTest(invalid_value=value), self.assertRaises(
                Stage61CatalogStateMatrixError,
            ):
                _runtime_control_value(row(value), "berry-powder-bad")

    def test_transaction_and_rfu_required_values_are_exact(self) -> None:
        fixture_ref = "1" * 64
        raw_100 = bytes(100)
        raw_80 = raw_100[:80]
        daycare = {
            "scenario_id": "egg_waiting", "layout_ref": fixture_ref,
            "party_count": 6, "money": 12345,
            "party_sha256": "2" * 64, "daycare_sha256": "3" * 64,
        }
        party_move = {
            "scenario_id": "relearner_teach_empty_slot",
            "layout_ref": fixture_ref, "family": "RELEARNER",
            "party_count": 1, "party_sha256": "4" * 64,
            "party_selection_sequence": [0], "selected_move_slot": None,
            "selected_relearn_move": 15, "teach_outcome": 1,
            "expected_relearnable_count": 1,
            "payment_policy": "FREE_OVERLAY_NO_MUSHROOM_CONSUMPTION",
            "expected_action": "TEACH_EMPTY_SLOT",
        }
        gift = {
            "scenario_id": "party_space", "layout_ref": fixture_ref,
            "executor_equivalence_class": "PARTY_SPACE",
            "party_count": 5, "party_sha256": "5" * 64,
            "storage_sha256": "6" * 64, "current_box": 0,
            "var_pc_box_to_send_mon": 0,
            "shown_box_was_full_message": False, "expected_result": 0,
            "expected_original_box": None, "expected_mon_box_id": None,
            "expected_mon_box_pos": None, "expected_var_pc_box_after": 0,
            "expected_shown_box_full_after_give": False,
            "fixed_rng_seed": 0x61E661E6,
            "expected_rng_after": 0x1BF2782A,
            "player_name_hex": "cebfcdceffffff", "player_gender": 0,
            "player_trainer_id": 0x12345678, "map_section_id": 92,
            "map_header_address": "0x0831543C",
            "generated_mon_100_raw_hex": raw_100.hex(),
            "generated_mon_80_raw_hex": raw_80.hex(),
            "generated_mon_100_sha256": hashlib.sha256(raw_100).hexdigest(),
            "generated_mon_80_sha256": hashlib.sha256(raw_80).hexdigest(),
            "national_dex_number": 18,
            "pokedex_preimage_sha256": {
                owner: "7" * 64
                for owner in ("owned", "seen", "seen1", "seen2")
            },
            "executor_representative_count": 4,
            "runner_exhaustive_layout_count": 30,
        }
        minigame = {
            "mode": 0, "eligible": True, "selected_slot": 5,
            "party_count": 6, "party_layout_ref": fixture_ref,
        }
        rfu = {
            "scenario_id": "mode1-leader-retry-result5",
            "endpoint_count": 3, "activity_mode": 1,
            "result_sequence": [8, 5], "fault_code": 2,
        }
        center_link = {
            "scenario_id": "group2-join-retry-result6",
            "link_group": 2, "activity": "multi-battle",
            "capacity_min": 4, "capacity_max": 4,
            "topology_policy": "EXACT_SOURCE_CAPACITY",
            "endpoint_count": 4, "result_sequence": [8, 6],
            "fault_code": 3,
        }
        fossil = {
            "scenario_id": "ready_amber", "layout_ref": fixture_ref,
            "revive_state": 2, "which_fossil": 3,
        }
        for kind, identifier, value in (
            ("DAYCARE_TRANSACTION_STATE", 0, daycare),
            ("PARTY_MOVE_TRANSACTION_STATE", 0, party_move),
            ("GIFT_STORAGE_TRANSACTION_STATE", 0, gift),
            ("PARTY_MINIGAME", 0, minigame),
            ("RFU_SESSION", 363, rfu),
            ("CENTER_LINK_SESSION", 364, center_link),
            ("FOSSIL_REVIVAL_STATE", 0, fossil),
        ):
            with self.subTest(kind=kind):
                row = {"kind": kind, "id": identifier, "value": value}
                if kind == "CENTER_LINK_SESSION":
                    row["relation_evidence"] = [{
                        "operator": (
                            "NATURAL_CENTER_LINK_GROUP_ROLE_RESULT_SEQUENCE"
                        ),
                    }]
                self.assertEqual(
                    _runtime_control_value(row, kind),
                    value,
                )

        invalid = (
            ("DAYCARE_TRANSACTION_STATE", 0, {
                **daycare, "scenario_id": "unknown",
            }),
            ("PARTY_MOVE_TRANSACTION_STATE", 0, {
                **party_move, "party_selection_sequence": [6],
            }),
            ("GIFT_STORAGE_TRANSACTION_STATE", 0, {
                **gift, "expected_mon_box_id": 0,
            }),
            ("PARTY_MINIGAME", 0, {
                **minigame, "eligible": False,
            }),
            ("RFU_SESSION", 363, {
                **rfu, "endpoint_count": 2,
            }),
            ("RFU_SESSION", 364, rfu),
            ("CENTER_LINK_SESSION", 364, {
                **center_link, "endpoint_count": 3,
            }),
            ("FOSSIL_REVIVAL_STATE", 0, {
                **fossil, "which_fossil": 1,
            }),
        )
        for kind, identifier, value in invalid:
            with self.subTest(kind=kind, value=value), self.assertRaises(
                Stage61CatalogStateMatrixError,
            ):
                row = {
                    "kind": kind, "id": identifier, "value": value,
                }
                if kind == "CENTER_LINK_SESSION":
                    row["relation_evidence"] = [{
                        "operator": (
                            "NATURAL_CENTER_LINK_GROUP_ROLE_RESULT_SEQUENCE"
                        ),
                    }]
                _runtime_control_value(row, f"bad-{kind}")

    def test_event_runner_projection_requires_phase3_oracle_binding(self) -> None:
        event_case = {
            "case_id": "event-bg-test", "owner_id": "BG:001/001:000",
            "input_sequence": {"sequence_id": "event-bg-test-seq-0000"},
        }
        document = {
            "event_runtime_cases": [event_case],
            "event_owner_runtime_scope": {
                "phase": "RUNTIME_CONTROL_EXPANDED",
                "oracle_phase": "ALL_EVENT_OWNER_RUNTIME_CASES_ORACLE_BOUND",
                "runtime_required_owner_count": 5416,
                "structural_nontrigger_owner_count": 1001,
                "runtime_owner_handoff_count": 5416,
                "untested_runtime_owner_handoff_count": 0,
                "event_runtime_case_count": 1,
                "event_runtime_sequence_count": 1,
                "map_lifecycle_composite_case_count": 0,
                "map_lifecycle_sequence_count": 0,
                "map_lifecycle_covered_physical_owner_count": 0,
                "map_lifecycle_dispatched_physical_owner_count": 0,
            },
        }
        self.assertEqual(runner_event_state_rows(document), [event_case])
        for key, value in (
            ("oracle_phase", "OBJECT_CASE_ORACLE_BINDING_REQUIRED"),
            ("untested_runtime_owner_handoff_count", 1),
        ):
            broken = json.loads(json.dumps(document))
            broken["event_owner_runtime_scope"][key] = value
            with self.assertRaises(Stage61CatalogStateMatrixError):
                runner_event_state_rows(broken)

    def test_phase3_oracle_attachment_promotes_both_phase_markers(self) -> None:
        case_id = "matrix-test-default-000"
        hidden_case_id = "matrix-test-collected-000"
        owner = "OBJECT:002/002:001"
        exact_effect = "effect-" + "1" * 24
        sibling_effect = "effect-" + "2" * 24
        exact_decision = "decision-" + "1" * 24
        sibling_decision = "decision-" + "2" * 24
        required = _empty_required_postconditions()
        text_oracle = {
            "visible_text_count": 0,
            "ordered_raw_sha256s": [],
            "allowed_ordered_raw_sha256_sequences": [[]],
        }
        document = {
            "schema_version": 1,
            "task": "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT",
            "stage": 61, "status": "PASS", "counts": {},
            "runner_projection": {"required_columns": []},
            "assertions": {"phase2": True},
            "cases": [
                {
                    "case_id": case_id, "owner_key": owner,
                    "interaction_expected": True,
                    "expected_object_visible": True,
                    "interaction": {
                        "group": 2, "map": 2, "object_index": 1,
                        "local_id": 2, "object": [4, 5],
                        "runtime_root": "0x08100000",
                    },
                    "runtime_map_lifecycle": {
                        "kind": "TRAINER_TOWER_ON_TRANSITION",
                    },
                    "runtime_control_assignment": {
                        "assignment_id": "tower-union",
                        "effect_signature_ids": [
                            exact_effect, sibling_effect,
                        ],
                        "ordered_decision_signature_ids": [
                            exact_decision, sibling_decision,
                        ],
                    },
                    "control_requirements": {"external": []},
                },
                {
                    "case_id": hidden_case_id, "owner_key": owner,
                    "interaction_expected": False,
                    "expected_object_visible": False,
                    "interaction": {
                        "group": 2, "map": 2, "object_index": 1,
                        "local_id": 2, "object": [4, 5],
                        "runtime_root": "0x08100000",
                    },
                    "control_requirements": {"external": []},
                },
            ],
            "event_runtime_cases": [],
            "event_owner_runtime_scope": {
                "phase": "RUNTIME_CONTROL_EXPANDED",
                "oracle_phase": "OBJECT_CASE_ORACLE_BINDING_REQUIRED",
                "runtime_required_owner_count": 5416,
                "runtime_owner_handoff_count": 5416,
                "untested_runtime_owner_handoff_count": 0,
            },
            "runtime_control_expansion": {
                "phase": "CONTROL_EXPANDED_ORACLE_CASE_BINDING_REQUIRED",
            },
            "dedicated_fixture_sweeps": {
                "GIFT_STORAGE_TRANSACTION_STATE": {"sentinel": True},
            },
        }
        sequence = {
            "sequence_id": f"{case_id}--seq-0000",
            "tokens": ["A"],
            "expected_static_branch_token": "NO_TEXT",
            "basis": {
                "kind": "PINNED_TEST_CFG",
                "effect_signature_id": exact_effect,
                "decision_signature_id": exact_decision,
            },
            "visible_text_expected": False,
            "silent_text_basis": {
                "kind": "STATIC_NO_TEXT_PATH",
                "source_instruction_addresses": ["0x08100000"],
                "reason": "PINNED_TEST_CFG_NO_PRINTER",
            },
            "text_oracle": text_oracle,
            "required_postconditions": required,
            "battle_start_required_postconditions": None,
            "post_battle_continuation": None,
        }
        catalog = {
            "schema_version": 1,
            "kind": "STAGE61_ALL_CASE_INDEPENDENT_INTERACTION_ORACLES",
            "status": "PASS", "unresolved_case_count": 0,
            "assertions": {"unresolved_zero": True},
            "cases": [
                {
                    "case_id": case_id, "owner_key": owner, "status": "PASS",
                    "stage61_root": "0x08100000",
                    "runner_contract": {
                        "input_sequences": [sequence],
                        "allowed_post_effect_families": [],
                        "allowed_post_effects": {},
                        "required_postconditions_by_sequence": {
                            sequence["sequence_id"]: required,
                        },
                        "battle_start_required_postconditions": {
                            sequence["sequence_id"]: None,
                        },
                        "control_requirements": {
                            "external": [], "internal": [],
                        },
                    },
                },
                {
                    "case_id": hidden_case_id, "owner_key": owner,
                    "status": "PASS", "stage61_root": "0x08100000",
                    "input_sequences": [],
                },
            ],
        }
        result = attach_stage61_case_oracles(document, catalog)
        self.assertEqual(
            result["event_owner_runtime_scope"]["phase"],
            "RUNTIME_CONTROL_EXPANDED",
        )
        self.assertEqual(
            result["event_owner_runtime_scope"]["oracle_phase"],
            "ALL_EVENT_OWNER_RUNTIME_CASES_ORACLE_BOUND",
        )
        self.assertEqual(
            result["runtime_control_expansion"]["phase"],
            "CONTROL_EXPANDED_AND_ORACLE_BOUND",
        )
        self.assertEqual(
            result["oracle"]["dedicated_fixture_sweeps"],
            document["dedicated_fixture_sweeps"],
        )
        self.assertEqual(
            result["cases"][1]["interaction"]["runtime_root"],
            "0x08100000",
        )
        projected_assignment = result["cases"][0][
            "runtime_control_assignment"
        ]
        self.assertEqual(
            projected_assignment["effect_signature_ids"], [exact_effect],
        )
        self.assertEqual(
            projected_assignment["ordered_decision_signature_ids"],
            [exact_decision],
        )
        self.assertEqual(
            projected_assignment["physical_context_signature_projection"]
            ["kind"],
            "TRAINER_TOWER_OWNER_EXACT",
        )
        self.assertTrue(all(result["assertions"].values()))

        unknown_signature = deepcopy(catalog)
        unknown_signature["cases"][0]["runner_contract"][
            "input_sequences"
        ][0]["basis"]["effect_signature_id"] = "effect-" + "f" * 24
        with self.assertRaisesRegex(
            Stage61CatalogStateMatrixError,
            "Trainer Tower physical context signature projection不一致",
        ):
            attach_stage61_case_oracles(document, unknown_signature)

        mutations = (
            ("oracle-root-bit", lambda matrix, oracle: oracle["cases"][0].update(
                {"stage61_root": "0x08100001"}
            )),
            ("case-root-missing", lambda matrix, oracle: matrix["cases"][0][
                "interaction"
            ].pop("runtime_root")),
            ("case-root-drift", lambda matrix, oracle: matrix["cases"][0][
                "interaction"
            ].update({"runtime_root": "0x08100002"})),
            ("hidden-oracle-root-missing", lambda matrix, oracle: oracle[
                "cases"
            ][1].pop("stage61_root")),
            ("hidden-case-root-drift", lambda matrix, oracle: matrix[
                "cases"
            ][1]["interaction"].update({"runtime_root": "0x08100002"})),
        )
        for label, mutate in mutations:
            broken_document = json.loads(json.dumps(document))
            broken_catalog = json.loads(json.dumps(catalog))
            mutate(broken_document, broken_catalog)
            with self.subTest(label=label), self.assertRaises(
                Stage61CatalogStateMatrixError,
            ):
                attach_stage61_case_oracles(
                    broken_document, broken_catalog,
                )

    def test_required_postconditions_are_strict_14_key_nested_schema(self) -> None:
        required = _empty_required_postconditions()
        self.assertEqual(
            _normalize_runner_required_postconditions(required, "unit"),
            required,
        )
        for berry_powder in (0, 99999):
            with self.subTest(berry_powder=berry_powder):
                changed = deepcopy(required)
                changed["berry_powder"] = berry_powder
                self.assertEqual(
                    _normalize_runner_required_postconditions(
                        changed, "berry-powder",
                    )["berry_powder"],
                    berry_powder,
                )
        transaction = deepcopy(required)
        transaction["party"] = {
            "count": 6, "raw_sha256": "1" * 64,
            "raw_byte_length": 600,
        }
        transaction["storage"] = {
            "raw_sha256": "2" * 64, "raw_byte_length": 0x83D0,
        }
        self.assertEqual(
            _normalize_runner_required_postconditions(
                transaction, "transaction",
            )["party"],
            transaction["party"],
        )
        mutations = {
            "top-extra": lambda value: value.update({"extra": []}),
            "berry-missing": lambda value: value.pop("berry_powder"),
            "berry-bool": lambda value: value.update({
                "berry_powder": True,
            }),
            "berry-negative": lambda value: value.update({
                "berry_powder": -1,
            }),
            "berry-overflow": lambda value: value.update({
                "berry_powder": 100000,
            }),
            "flag-extra": lambda value: value["flags"].append({
                "id": 1, "value": True, "extra": 0,
            }),
            "var-gap": lambda value: value["vars"].append({
                "id": 0x4100, "value": 1,
            }),
            "item-overflow": lambda value: value["items"].append({
                "id": 1, "count": 1000,
            }),
            "object-active": lambda value: value["objects"].append({
                "local_id": 1,
                "after": {
                    "active": True, "map": "1/1",
                    "invisible": False, "visible": True,
                    "current": [7, 7], "previous": [7, 7],
                },
            }),
            "battle-partial": lambda value: value.update({
                "battle": {"active": True},
            }),
            "storage-partial": lambda value: value.update({
                "storage": {"after_fnv1a64": "A" * 16},
            }),
            "legacy-party-fnv": lambda value: value.update({
                "party": {
                    "count": 1, "changed_slots": [0],
                    "after_fnv1a64": "A" * 16,
                },
            }),
            "party-size": lambda value: value.update({
                "party": {
                    "count": 1, "raw_sha256": "1" * 64,
                    "raw_byte_length": 599,
                },
            }),
            "storage-size": lambda value: value.update({
                "storage": {
                    "raw_sha256": "2" * 64,
                    "raw_byte_length": 0x83CF,
                },
            }),
        }
        for label, mutate in mutations.items():
            broken = deepcopy(required)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                Stage61CatalogStateMatrixError,
            ):
                _normalize_runner_required_postconditions(broken, label)

        object_case_id = "matrix-test-default-000"
        object_owner = "OBJECT:001/001:000"
        sequence_id = f"{object_case_id}--seq-0000"
        text_oracle = {
            "visible_text_count": 0,
            "ordered_raw_sha256s": [],
            "allowed_ordered_raw_sha256_sequences": [[]],
        }
        sequence = {
            "sequence_id": sequence_id, "tokens": ["A"],
            "expected_static_branch_token": "NO_TEXT",
            "basis": "PINNED_TEST_CFG", "visible_text_expected": False,
            "silent_text_basis": {
                "kind": "STATIC_NO_TEXT_PATH",
                "source_instruction_addresses": ["0x08100000"],
                "reason": "PINNED_TEST_CFG_NO_PRINTER",
            },
            "text_oracle": text_oracle,
            "required_postconditions": deepcopy(required),
            "battle_start_required_postconditions": None,
            "post_battle_continuation": None,
        }
        document = {
            "schema_version": 1,
            "task": "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT",
            "stage": 61, "status": "PASS", "counts": {},
            "runner_projection": {"required_columns": []},
            "assertions": {"phase2": True},
            "cases": [{
                "case_id": object_case_id, "owner_key": object_owner,
                "interaction_expected": True,
                "expected_object_visible": True,
                "interaction": {
                    "group": 1, "map": 1, "object_index": 0,
                    "local_id": 1, "object": [4, 5],
                    "runtime_root": "0x08100000",
                },
                "control_requirements": {"external": []},
            }],
            "event_runtime_cases": [],
            "event_owner_runtime_scope": {
                "phase": "RUNTIME_CONTROL_EXPANDED",
                "oracle_phase": "OBJECT_CASE_ORACLE_BINDING_REQUIRED",
                "runtime_owner_handoff_count": 5416,
                "untested_runtime_owner_handoff_count": 0,
            },
            "runtime_control_expansion": {
                "phase": "CONTROL_EXPANDED_ORACLE_CASE_BINDING_REQUIRED",
            },
        }
        catalog = {
            "schema_version": 1,
            "kind": "STAGE61_ALL_CASE_INDEPENDENT_INTERACTION_ORACLES",
            "status": "PASS", "unresolved_case_count": 0,
            "assertions": {"unresolved_zero": True},
            "cases": [{
                "case_id": object_case_id, "owner_key": object_owner,
                "status": "PASS", "stage61_root": "0x08100000",
                "runner_contract": {
                    "input_sequences": [sequence],
                    "allowed_post_effect_families": [],
                    "allowed_post_effects": {},
                    "required_postconditions_by_sequence": {
                        sequence_id: deepcopy(required),
                    },
                    "battle_start_required_postconditions": {
                        sequence_id: None,
                    },
                    "control_requirements": {"external": [], "internal": []},
                },
            }],
        }
        broken_catalog = deepcopy(catalog)
        broken_catalog["cases"][0]["runner_contract"]["input_sequences"][0][
            "required_postconditions"
        ]["battle"] = {"active": True}
        with self.assertRaises(Stage61CatalogStateMatrixError):
            attach_stage61_case_oracles(document, broken_catalog)

    @staticmethod
    def _complete_mgba_source_binding() -> dict:
        object_contracts = [
            {
                "case_id": "object-case-0", "base_case_id": "base-0",
                "owner_id": "OBJECT:001/001:000",
                "catalog_branch": "DEFAULT",
                "sequence_ids": ["object-seq-0a", "object-seq-0b"],
                "runtime_root": "0x08100000",
                "group": 1, "map": 1, "object_index": 0,
                "object": [0, 1],
                "runtime_map_lifecycle_source": None,
                "expected_live_current": [7, 8],
                "root_hit_sequence_ids": ["object-seq-0a", "object-seq-0b"],
                "hidden_root_zero": False,
            },
            {
                "case_id": "object-case-1", "base_case_id": "base-1",
                "owner_id": "OBJECT:001/001:001",
                "catalog_branch": "FLAG_CLEAR",
                "sequence_ids": ["object-seq-1a", "object-seq-1b"],
                "runtime_root": "0x08100010",
                "group": 1, "map": 1, "object_index": 1,
                "object": [1, 2],
                "runtime_map_lifecycle_source": None,
                "expected_live_current": [8, 9],
                "root_hit_sequence_ids": ["object-seq-1a", "object-seq-1b"],
                "hidden_root_zero": False,
            },
            {
                "case_id": "object-case-2", "base_case_id": "base-2",
                "owner_id": "OBJECT:001/001:002",
                "catalog_branch": "FLAG_SET",
                "sequence_ids": ["object-seq-2a"],
                "runtime_root": "0x08100020",
                "group": 1, "map": 1, "object_index": 2,
                "object": [2, 3],
                "runtime_map_lifecycle_source": None,
                "expected_live_current": [9, 10],
                "root_hit_sequence_ids": ["object-seq-2a"],
                "hidden_root_zero": False,
            },
        ]
        base_contracts = []
        for index, row in enumerate(object_contracts):
            branch_ids = [row["catalog_branch"]]
            base_contracts.append({
                "case_id": row["base_case_id"],
                "owner_key": row["owner_id"],
                "group": 1, "map": 1, "local_id": index + 1,
                "object": [index, index + 1],
                "branch_ids": branch_ids,
                "branches_sha256": _mgba_binding_sha256([
                    {"branch_id": branch_ids[0]},
                ]),
            })
        oracle_contracts = [
            {
                "case_id": row["case_id"], "owner_id": row["owner_id"],
                "oracle_sha256": hashlib.sha256(
                    row["case_id"].encode("utf-8")
                ).hexdigest(),
            }
            for row in object_contracts
        ]
        effect_ids = ["effect-test-a", "effect-test-b"]
        effect_contracts = [
            {
                "signature_id": signature_id,
                "runtime_root": f"0x{0x08100000 + index * 0x10:08X}",
                "terminal_kind": "FIELD_RELEASE",
                "ordered_effect_count": 0,
                "ordered_effects_sha256": _mgba_binding_sha256([]),
                "ordered_effects": [],
            }
            for index, signature_id in enumerate(effect_ids)
        ]
        map_source_case_id = (
            "map-lifecycle-001-001-0123456789abcdefabcd"
        )
        event_contracts = [
            {
                "case_id": "event-case-0",
                "source_case_id": "event-case-0",
                "case_kind": "EVENT_RUNTIME",
                "owner_id": "BG:001/001:000",
                "covered_owner_ids": ["BG:001/001:000"],
                "dispatched_owner_ids": None,
                "sequence_id": "event-seq-0",
                "effect_signature_ids": [effect_ids[0]],
                "producer_kind": None,
                "transition_mode": None,
            },
            {
                "case_id": f"{map_source_case_id}--run-0000",
                "source_case_id": map_source_case_id,
                "case_kind": "MAP_LIFECYCLE_COMPOSITE",
                "owner_id": "MAP_LIFECYCLE:001/001",
                "covered_owner_ids": [
                    "MAP:001/001:000", "MAP:001/001:001",
                ],
                "dispatched_owner_ids": ["MAP:001/001:001"],
                "sequence_id": "event-seq-1",
                "effect_signature_ids": [effect_ids[1]],
                "producer_kind": "STOCK_WARP",
                "transition_mode": "DIRECT",
            },
        ]
        object_owner_ids = sorted({
            row["owner_id"] for row in object_contracts
        })
        event_owner_ids = sorted({
            owner_id for row in event_contracts
            for owner_id in row["covered_owner_ids"]
        })
        runtime_owner_ids = sorted(object_owner_ids + event_owner_ids)
        structural_owner_ids = [
            "COMMON:007", "COORD:001/001:000",
        ]
        structural_evidence_sha256 = "3" * 64
        no_dispatch_case_ids = sorted(
            row["case_id"] for row in [*object_contracts, *event_contracts]
        )
        effect_registry_binding = {
            "schema_version": 1,
            "kind": "STAGE61_MGBA_EFFECT_REGISTRY_EXACT_BINDING_V1",
            "partition_sha256": "7" * 64,
            "case_sources_sha256": "8" * 64,
            "case_signature_ids_sha256": "9" * 64,
            "no_dispatch_case_ids_sha256": "a" * 64,
            "effect_signatures_sha256": "b" * 64,
            "effect_templates_sha256": "c" * 64,
            "effect_instances_sha256": "d" * 64,
            "effect_case_bindings_sha256": "e" * 64,
            "effect_instance_watch_bindings_sha256": "f" * 64,
            "no_dispatch_contracts_sha256": "0" * 64,
            "no_dispatch_watch_bindings_sha256": "1" * 64,
            "raw_watch_plan_sha256": "2" * 64,
            "raw_watch_plan_artifact_sha256": "3" * 64,
            "signature_ids": effect_ids,
            "template_ids": [], "instance_ids": [],
            "case_binding_instance_ids": [],
            "dispatched_case_ids": [],
            "no_dispatch_case_ids": no_dispatch_case_ids,
            "watch_ids": ["effect-watch-test"],
            "counts": {
                "template_count": 0, "instance_count": 0,
                "dispatched_case_count": 0,
                "no_dispatch_case_count": len(no_dispatch_case_ids),
                "runner_case_count": len(no_dispatch_case_ids),
                "occurrence_count": 0, "raw_watch_count": 1,
                "signature_count": len(effect_ids),
                "case_binding_count": 0,
                "instance_watch_binding_count": 0,
                "no_dispatch_contract_count": len(no_dispatch_case_ids),
                "no_dispatch_watch_binding_count":
                    len(no_dispatch_case_ids),
            },
        }
        effect_registry_binding["binding_sha256"] = _mgba_binding_sha256(
            effect_registry_binding
        )
        summary = {
            "base_contracts_sha256": _mgba_binding_sha256(base_contracts),
            "object_case_contracts_sha256":
                _mgba_binding_sha256(object_contracts),
            "oracle_case_contracts_sha256":
                _mgba_binding_sha256(oracle_contracts),
            "event_case_contracts_sha256":
                _mgba_binding_sha256(event_contracts),
            "runtime_owner_ids_sha256":
                _mgba_binding_sha256(runtime_owner_ids),
            "structural_owner_ids_sha256":
                _mgba_binding_sha256(structural_owner_ids),
            "structural_evidence_sha256": structural_evidence_sha256,
            "effect_signature_ids_sha256":
                _mgba_binding_sha256(effect_ids),
            "effect_signature_contracts_sha256":
                _mgba_binding_sha256(effect_contracts),
            "effect_registry_binding_sha256": effect_registry_binding[
                "binding_sha256"
            ],
            "base_object_count": len(base_contracts),
            "object_case_count": len(object_contracts),
            "event_case_count": len(event_contracts),
            "event_source_case_count": len({
                row["source_case_id"] for row in event_contracts
            }),
            "map_lifecycle_composite_case_count": 1,
            "map_lifecycle_execution_case_count": 1,
            "map_lifecycle_physical_owner_count": 2,
            "map_lifecycle_dispatched_owner_count": 1,
            "object_sequence_count": sum(
                len(row["sequence_ids"]) for row in object_contracts
            ),
            "event_sequence_count": len(event_contracts),
            "object_owner_count": len(object_owner_ids),
            "event_owner_count": len(event_owner_ids),
            "runtime_owner_count": len(runtime_owner_ids),
            "structural_owner_count": len(structural_owner_ids),
            "effect_signature_count": len(effect_ids),
        }
        return {
            "schema_version": 3,
            "kind": "STAGE61_MGBA_CURRENT_SOURCE_EXACT_BINDING_V3",
            "rom_sha256": "a" * 64,
            "normalized_matrix_sha256": "b" * 64,
            "normalized_catalog_sha256": "d" * 64,
            "normalized_legacy_catalog_sha256": "1" * 64,
            "interaction_oracle_catalog_sha256": "2" * 64,
            "runtime_control_contract_sha256": "4" * 64,
            "runtime_control_declared_sha256": "5" * 64,
            "runtime_control_bound_sha256": "6" * 64,
            "interaction_abi_manifest_sha256": "7" * 64,
            "interaction_abi_artifact_sha256": "8" * 64,
            "summary": summary,
            "base_contracts": base_contracts,
            "object_case_contracts": object_contracts,
            "oracle_case_contracts": oracle_contracts,
            "event_case_contracts": event_contracts,
            "object_owner_ids": object_owner_ids,
            "event_owner_ids": event_owner_ids,
            "runtime_owner_ids": runtime_owner_ids,
            "structural_owner_ids": structural_owner_ids,
            "structural_evidence_sha256": structural_evidence_sha256,
            "effect_signature_ids": effect_ids,
            "effect_signature_contracts": effect_contracts,
            "effect_registry_binding": effect_registry_binding,
        }

    @staticmethod
    def _mgba_catalog_result(object_index: int, row: dict) -> dict:
        local_id = object_index + 1
        position = list(row["object"])
        raw = bytearray(24)
        raw[0] = local_id
        raw[1] = 0x42
        struct.pack_into("<hh", raw, 4, *position)
        struct.pack_into("<I", raw, 16, int(row["runtime_root"], 0))
        raw_hex = bytes(raw).hex().upper()
        raw_fingerprint = hashlib.sha256(raw).hexdigest()[:16]
        identity = {
            "owner_object_index": object_index,
            "template_found": True,
            "template_index": object_index,
            "template_local_id": local_id,
            "template_graphics_id": 0x42,
            "template_kind": 0,
            "template_position": position,
            "template_elevation": 0,
            "template_movement_type": 0,
            "template_movement_range": [0, 0],
            "template_trainer_type": 0,
            "template_trainer_range_or_berry_tree_id": 0,
            "template_script": row["runtime_root"],
            "template_hide_flag": 0,
            "template_storage": "gMapHeader.events.objectEvents",
            "expected_raw_hex": raw_hex,
            "observed_raw_hex": raw_hex,
            "expected_raw_fnv1a64": raw_fingerprint,
            "observed_raw_fnv1a64": raw_fingerprint,
            "runtime_template_found": True,
            "runtime_template_index": object_index,
            "runtime_template_local_id": local_id,
            "runtime_template_position": position,
            "runtime_template_script": row["runtime_root"],
            "runtime_template_position_exact": True,
            "runtime_template_script_exact": True,
            "live_active": True,
            "live_visible": True,
            "live_current": list(row["expected_live_current"]),
            "map_lifecycle": None,
            "exact": True,
        }
        return {
            "case_id": row["case_id"],
            "base_case_id": row["base_case_id"],
            "owner_key": row["owner_id"],
            "catalog_branch": row["catalog_branch"],
            "map": "1/1",
            "local_id": local_id,
            "runtime_root": row["runtime_root"],
            "stance": [0, 0],
            "interaction_expected": True,
            "preinteraction_object_identity": identity,
            "root_probe": {
                "expected": row["runtime_root"],
                "armed_after_identity": True,
                "input_attempted": True,
                "hidden_idle_frames": 0,
                "hidden_hits": 0,
                "hidden_first": None,
            },
            "input_sequence_attempts": [
                {
                    "sequence_id": sequence_id,
                    "root_script_pointer_expected": row["runtime_root"],
                    "root_counter_armed_after_identity": True,
                    "root_script_pointer_hits": 1,
                    "first_root_script_pointer": row["runtime_root"],
                    "first_root_context": {
                        "map": "1/1", "player": [0, 0],
                    },
                    "preinteraction_object_identity": identity,
                }
                for sequence_id in row["sequence_ids"]
            ],
        }

    @staticmethod
    def _complete_mgba_document(
        source_binding: dict | None = None,
    ) -> dict:
        binding = source_binding or (
            Stage61CatalogStateMatrixUnitTests
            ._complete_mgba_source_binding()
        )
        digest = "a" * 64
        matrix_digest = "b" * 64
        runner_digest = "c" * 64
        case_results = {}
        for case_id in MGBA_REQUIRED_CASES:
            payload = {
                "schema_version": 1, "status": "PASS", "case": case_id,
                "evidence": {"actual_runtime_path": True},
                "failed": 0, "untested": 0,
                "unresolved": 0, "warnings": 0,
            }
            if case_id == "catalog_batch":
                payload.update({
                    "fixture_count": 3,
                    "results": [
                        Stage61CatalogStateMatrixUnitTests
                        ._mgba_catalog_result(object_index, row)
                        for object_index, row in enumerate(
                            binding["object_case_contracts"]
                        )
                    ],
                })
            elif case_id == "event_runtime_batch":
                event_rows = binding["event_case_contracts"]
                logical_owner_ids = sorted({
                    row["owner_id"] for row in event_rows
                })
                source_case_ids = sorted({
                    row["source_case_id"] for row in event_rows
                })
                map_rows = [
                    row for row in event_rows
                    if row["case_kind"] == "MAP_LIFECYCLE_COMPOSITE"
                ]
                map_source_case_ids = sorted({
                    row["source_case_id"] for row in map_rows
                })
                map_covered_owner_ids = sorted({
                    owner_id for row in map_rows
                    for owner_id in row["covered_owner_ids"]
                })
                payload.update({
                    "fixture_count": len(event_rows),
                    "owner_count": len(logical_owner_ids),
                    "source_owner_count":
                        binding["summary"]["event_owner_count"],
                    "executed_owner_count":
                        binding["summary"]["event_owner_count"],
                    "sequence_count": len(event_rows),
                    "results": [
                        {
                            "case_id": row["case_id"],
                            "source_case_id": row["source_case_id"],
                            "case_kind": row["case_kind"],
                            "owner_id": row["owner_id"],
                            "covered_owner_ids":
                                list(row["covered_owner_ids"]),
                            **({
                                "dispatched_owner_ids":
                                    list(row["dispatched_owner_ids"]),
                                "trigger_evidence": {
                                    "map_transition": {
                                        "contract": (
                                            "STOCK_WARP" if row[
                                                "transition_mode"
                                            ] == "DIRECT" else
                                            "STOCK_WARP_THEN_FIELD_RETURN"
                                        ),
                                        "seed_kind": (
                                            "stock_warp" if row[
                                                "transition_mode"
                                            ] == "DIRECT" else
                                            "resume_callback"
                                        ),
                                        "real_warp_step": True,
                                        "real_connection_step": False,
                                        "engine_teleport": False,
                                    },
                                },
                            } if row["case_kind"]
                                == "MAP_LIFECYCLE_COMPOSITE" else {}),
                            "input_sequence_attempt": {
                                "sequence_id": row["sequence_id"],
                            },
                            "effect_signature_ids":
                                list(row["effect_signature_ids"]),
                        }
                        for row in event_rows
                    ],
                    "executed_owner_ids":
                        list(binding["event_owner_ids"]),
                    "executed_logical_owner_count": len(logical_owner_ids),
                    "executed_logical_owner_ids": logical_owner_ids,
                    "executed_case_ids": sorted(
                        row["case_id"] for row in event_rows
                    ),
                    "source_case_count": len(source_case_ids),
                    "source_case_ids": source_case_ids,
                    "executed_source_case_ids": source_case_ids,
                    "executed_sequence_ids": sorted(
                        row["sequence_id"] for row in event_rows
                    ),
                    "map_transition_row_count": len(map_rows),
                    "map_transition_source_case_count":
                        len(map_source_case_ids),
                    "map_transition_source_case_ids": map_source_case_ids,
                    "map_transition_covered_owner_count":
                        len(map_covered_owner_ids),
                    "map_transition_covered_owner_ids":
                        map_covered_owner_ids,
                    "map_transition_seed_counts": {
                        "stock_warp": len(map_rows),
                        "stock_connection": 0,
                        "engine_teleport": 0,
                    },
                    "map_transition_producer_kind_counts": {
                        "STOCK_WARP": len(map_rows),
                        "CONNECTION": 0,
                        "ENGINE_TELEPORT": 0,
                    },
                    "map_transition_direct_seed_counts": {
                        "stock_warp": len(map_rows),
                        "stock_connection": 0,
                        "engine_teleport": 0,
                    },
                    "map_transition_resume_seed_counts": {
                        "stock_warp": 0,
                        "stock_connection": 0,
                        "engine_teleport": 0,
                    },
                    "map_transition_counts_source_derived": True,
                })
            elif case_id in {
                "catalog_state_persistence",
                "catalog_state_legacy_persistence",
            }:
                persistence_ids = [
                    selected_case_id for selected_case_id, _
                    in MGBA_REQUIRED_STATE_PERSISTENCE_CASES
                ]
                payload.update({
                    "fixture_count": len(persistence_ids),
                    "results": [
                        {
                            "case_id": selected_case_id,
                            "base_case_id": "cal-096-001-010",
                            "writer": {
                                "case_id": selected_case_id,
                                "phase": "WRITE",
                                "normal_save_generations": 2,
                                "save_via_start_menu_input": True,
                                "fresh_title_continue": True,
                                "expanded_flag_readback": True,
                                "expanded_var_readback": True,
                            },
                            "reader": {
                                "case_id": selected_case_id,
                                "phase": "READ",
                                "normal_save_generations": 0,
                                "save_via_start_menu_input": False,
                                "fresh_title_continue": True,
                                "expanded_flag_readback": True,
                                "expanded_var_readback": True,
                            },
                            "reader_save_image_unchanged": True,
                        }
                        for selected_case_id in persistence_ids
                    ],
                })
            elif case_id == "stateful_menu_loop_batch":
                payload.update({
                    "fixture_count": 56,
                    "vending_witness_count": 44,
                    "bill_witness_count": 12,
                    "direct_root_call_before": 0,
                    "direct_root_call_after": 0,
                })
            payload_sha256 = hashlib.sha256((json.dumps(
                payload, ensure_ascii=False, sort_keys=True, indent=2,
            ) + "\n").encode("utf-8")).hexdigest()
            case_results[case_id] = {
                "status": "PASS", "process_runs": 2,
                "process_shards": 1,
                "same_shard_boundaries_across_runs": True,
                "per_shard_identical_results": True,
                "per_shard_result_sha256": [payload_sha256],
                "per_run_merged_result_sha256": [
                    payload_sha256, payload_sha256,
                ],
                "per_run_per_shard_result_sha256": [
                    [payload_sha256], [payload_sha256],
                ],
                "identical_results": True,
                "result": payload,
            }
        summary = binding["summary"]
        trainer_tower_sectors = [
            {
                "physical_sector": physical,
                "offset": physical * 0x1000,
                "size": 0x1000,
                "first_u32_le": first,
                "first_u32_le_hex": f"0x{first:08X}",
                "sha256": ("3" if physical == 30 else "4") * 64,
                "special_sector_sentinel_absent": True,
            }
            for physical, first in ((30, 0xFFFFFFFF), (31, 0x00000000))
        ]
        trainer_tower_image = {
            "relative_path": "canonical.srm",
            "size": 0x20000,
            "sha256": "e" * 64,
            "sectors": trainer_tower_sectors,
        }
        trainer_tower_image["source_identity_sha256"] = (
            _mgba_binding_sha256(trainer_tower_image)
        )
        trainer_tower_cases = {}
        for case_id in MGBA_REQUIRED_CASES:
            trainer_tower_cases[case_id] = []
            for run_index in range(2):
                images = [deepcopy(trainer_tower_image)]
                trainer_tower_cases[case_id].append([{
                    "status": "PASS",
                    "process_identity": (
                        f"{case_id}/run-{run_index + 1}/shard-1"
                    ),
                    "canonical_source_srm_count": 1,
                    "canonical_source_srms": images,
                    "source_set_sha256": _mgba_binding_sha256(images),
                    "local_fallback_precondition": True,
                }])
        return {
            "schema_version": 1,
            "task": "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT",
            "stage": 61, "status": "PASS",
            "rom_sha256": digest,
            "expected_rom_sha256": digest,
            "metadata_sha256": digest,
            "fixture_sha256": digest,
            "interaction_abi_manifest_sha256": binding[
                "interaction_abi_manifest_sha256"
            ],
            "effect_registry_binding": binding[
                "effect_registry_binding"
            ],
            "effect_observer": {
                "runtime_control_path": "runtime.json",
                "raw_watch_plan_path": "effect-plan.json",
                "interaction_abi_path": "interaction-abi.json",
                "interaction_abi_sha256": binding[
                    "interaction_abi_manifest_sha256"
                ],
                "registry_binding": binding["effect_registry_binding"],
                "raw_watch_count": binding["effect_registry_binding"][
                    "counts"
                ]["raw_watch_count"],
                "runtime_control_declared_sha256": binding[
                    "runtime_control_declared_sha256"
                ],
                "runtime_control_artifact_sha256": binding[
                    "runtime_control_contract_sha256"
                ],
            },
            "trainer_tower_save_precondition": {
                "schema_version": 1,
                "status": "PASS",
                "contract": "CANONICAL_SAVE_LOCAL_FALLBACK_ONLY",
                "external_ereader_save_in_scope": False,
                "special_sector_sentinel": "0x0000B39D",
                "runtime_flash_gate": {
                    "status": "PROCESS_EXIT_GATED",
                    "entry": "world_generate_save_and_s61_open_fresh",
                    "timing": (
                        "BEFORE_INITIAL_STOCK_WARP_AND_"
                        "FRESH_CONTINUE_OWNER_EXECUTION"
                    ),
                    "flash_bank": 1,
                    "sector30_window_address": "0x0E00E000",
                    "sector31_window_address": "0x0E00F000",
                    "sector30_expected_first_u32_le": "0xFFFFFFFF",
                    "sector31_expected_first_u32_le": "0x00000000",
                    "generation_sector31_expected_first_u32_le": (
                        "0xFFFFFFFF"
                    ),
                    "failure_policy": "FAIL_CLOSED",
                },
                "cases": trainer_tower_cases,
            },
            "orchestrator": {
                "source": str(MGBA_ORCHESTRATOR_SOURCE),
                "source_sha256": "f" * 64,
                "status": "PASS",
            },
            "domains": list(MGBA_REQUIRED_DOMAINS),
            "cases": list(MGBA_REQUIRED_CASES),
            "process_runs": 2,
            "compile": {
                "status": "PASS",
                "source": MGBA_RUNNER_SOURCE.as_posix(),
                "source_sha256": runner_digest,
                "stdout_empty": True,
                "stderr_empty": True,
            },
            "results": case_results,
            "catalog": {
                "full_state_matrix": True,
                "normalized_sha256": "d" * 64,
                "base_fixture_count": summary["base_object_count"],
                "state_fixture_count": summary["object_case_count"],
                "source_state_fixture_count": summary["object_case_count"],
                "failed": 0, "untested": 0,
            },
            "calibration_source": {
                "normalized_sha256":
                    binding["normalized_legacy_catalog_sha256"],
                "script_object_count": summary["base_object_count"],
                "source_script_object_count": summary["base_object_count"],
                "branch_label_count": sum(
                    len(row["branch_ids"])
                    for row in binding["base_contracts"]
                ),
                "full_catalog": True,
                "failed": 0, "untested": 0,
            },
            "state_matrix": {
                "normalized_sha256": matrix_digest,
                "source_case_count": (
                    summary["object_case_count"]
                    + summary["event_case_count"]
                ),
                "source_object_case_count": summary["object_case_count"],
                "source_event_runtime_case_count":
                    summary["event_case_count"],
                "selected_case_count": (
                    summary["object_case_count"]
                    + summary["event_case_count"]
                ),
                "source_sequence_count": (
                    summary["object_sequence_count"]
                    + summary["event_sequence_count"]
                ),
                "selected_sequence_count": (
                    summary["object_sequence_count"]
                    + summary["event_sequence_count"]
                ),
                "executed_sequence_count": (
                    summary["object_sequence_count"]
                    + summary["event_sequence_count"]
                ),
                "full_matrix": True,
                "full_sequence_matrix": True,
                "all_reachable_input_options_enumerated": True,
                "control_abi_complete": True,
                "unknown_effect_count": 0,
                "empty_visible_text_count": 0,
                "softlock_count": 0,
                "event_owner_count": (
                    summary["runtime_owner_count"]
                    + summary["structural_owner_count"]
                ),
                "executed_runtime_owner_count":
                    summary["runtime_owner_count"],
                "structural_nontrigger_owner_count":
                    summary["structural_owner_count"],
                "untested_runtime_owner_count": 0,
                "event_owner_runtime_scope": {
                    "runtime_owner_ids":
                        list(binding["runtime_owner_ids"]),
                    "object_runtime_owner_ids":
                        list(binding["object_owner_ids"]),
                    "event_runtime_owner_ids":
                        list(binding["event_owner_ids"]),
                    "structural_nontrigger_owner_ids":
                        list(binding["structural_owner_ids"]),
                    "runtime_required_owner_count":
                        summary["runtime_owner_count"],
                    "object_runtime_owner_count":
                        summary["object_owner_count"],
                    "event_runtime_owner_count":
                        summary["event_owner_count"],
                    "structural_nontrigger_owner_count":
                        summary["structural_owner_count"],
                    "structural_nontrigger_evidence_sha256":
                        binding["structural_evidence_sha256"],
                    "all_1000_null_structural_zero_raw_proven": True,
                    "dormant_common7_table_abi_and_live_caller_zero_proven":
                        True,
                },
                "failed": 0, "untested": 0,
            },
            "state_persistence": {
                "selected_case_count": len(
                    MGBA_REQUIRED_STATE_PERSISTENCE_CASES
                ),
                "case_ids": [
                    case_id for case_id, _
                    in MGBA_REQUIRED_STATE_PERSISTENCE_CASES
                ],
                "modes": [
                    "catalog_state_legacy_persistence",
                    "catalog_state_persistence",
                ],
                "normal_rom_save": True,
                "save_via_start_menu_input": True,
                "separate_writer_reader_processes": True,
                "fresh_title_continue": True,
                "legacy_saveblock1_var_canaries": [
                    0x4000, 0x4040, 0x40FF,
                ],
                "legacy_source": {"sha256": "0" * 64},
                "failed": 0, "untested": 0,
            },
            "stateful_menu_loop_contracts": {
                "normalized_sha256": STATEFUL_MENU_CONTRACTS_SHA256,
                "contract_kind": "STATEFUL_MENU_LOOP_CONTRACT_V1",
                "contract_count": 4,
                "runtime_witness_count": 56,
                "failed": 0,
                "untested": 0,
            },
            "coverage": {
                key: True for key in (
                    "all_catalog_script_objects_and_flag_branches",
                    "catalog_untested_zero",
                    "catalog_all_control_domains_one_to_one_readback",
                    "catalog_hidden_without_interaction",
                    "pc_capacity_add_pc_item_savestate_four_synthetic_cases",
                    "product_map_scripts_stage60_negative_stage61_empty_table",
                    "product_coord_bg_08000000_to_null_actual_consumers",
                    "product_gym_bg_all_eight_type3_prepost_visible_text",
                    "all_5416_trigger_event_owners_executed",
                    "all_1001_structural_nontriggers_proven",
                    "stateful_menu_56_physical_repeated_choice_witnesses",
                )
            },
            "warnings": 0,
        }

    @patch(
        "scripts.build_stage61_display_npc_event_audit."
        "validate_final_mgba_case_result",
        side_effect=lambda _case_id, payload: payload,
    )
    def test_require_mgba_gate_binds_all_identity_case_and_sequence_counts(
        self, final_anchor,
    ) -> None:
        source_binding = self._complete_mgba_source_binding()
        document = self._complete_mgba_document(source_binding)
        evidence = _validate_required_mgba_document(
            document,
            rom_sha256="a" * 64,
            metadata_sha256="a" * 64,
            fixture_sha256="a" * 64,
            catalog_sha256="d" * 64,
            matrix_sha256="b" * 64,
            runner_source_sha256="c" * 64,
            orchestrator_source_sha256="f" * 64,
            stateful_menu_contracts_sha256=STATEFUL_MENU_CONTRACTS_SHA256,
            object_matrix_case_count=3,
            all_matrix_case_count=5,
            matrix_sequence_count=7,
            source_binding=source_binding,
        )
        self.assertEqual(evidence["status"], "PASS")
        self.assertEqual(evidence["domain_count"], 8)
        self.assertEqual(evidence["case_count"], len(MGBA_REQUIRED_CASES))
        self.assertEqual(evidence["object_owner_count"], 3)
        self.assertEqual(evidence["event_owner_count"], 3)
        self.assertEqual(evidence["runtime_owner_count"], 6)
        self.assertEqual(evidence["structural_owner_count"], 2)
        self.assertEqual(final_anchor.call_count, len(MGBA_REQUIRED_CASES))

        with self.assertRaisesRegex(Stage61BuildError, "stateful menu"):
            _validate_required_mgba_document(
                document,
                rom_sha256="a" * 64,
                metadata_sha256="a" * 64,
                fixture_sha256="a" * 64,
                catalog_sha256="d" * 64,
                matrix_sha256="b" * 64,
                runner_source_sha256="c" * 64,
                orchestrator_source_sha256="f" * 64,
                stateful_menu_contracts_sha256="8" * 64,
                object_matrix_case_count=3,
                all_matrix_case_count=5,
                matrix_sequence_count=7,
                source_binding=source_binding,
            )

        for mutation in (
            lambda row: row.update({"process_runs": 1}),
            lambda row: row.update({"process_runs": 3}),
            lambda row: row["state_matrix"].update(
                {"executed_sequence_count": 6}
            ),
            lambda row: row["results"][MGBA_REQUIRED_CASES[0]][
                "result"
            ].update({"unknown_effects": ["UNCLASSIFIED"]}),
        ):
            broken = json.loads(json.dumps(document))
            mutation(broken)
            with self.assertRaises(Stage61BuildError):
                _validate_required_mgba_document(
                    broken,
                    rom_sha256="a" * 64,
                    metadata_sha256="a" * 64,
                    fixture_sha256="a" * 64,
                    catalog_sha256="d" * 64,
                    matrix_sha256="b" * 64,
                    runner_source_sha256="c" * 64,
                    orchestrator_source_sha256="f" * 64,
                    stateful_menu_contracts_sha256=(
                        STATEFUL_MENU_CONTRACTS_SHA256
                    ),
                    object_matrix_case_count=3,
                    all_matrix_case_count=5,
                    matrix_sequence_count=7,
                    source_binding=source_binding,
                )

        for key in (
            "empty_text", "terminal_mismatches", "frame_diff_failures",
            "input_recovery_failures", "internal_control_failures",
        ):
            broken = json.loads(json.dumps(document))
            broken["results"][MGBA_REQUIRED_CASES[0]]["result"][key] = 1
            with self.assertRaises(Stage61BuildError):
                _validate_required_mgba_document(
                    broken,
                    rom_sha256="a" * 64,
                    metadata_sha256="a" * 64,
                    fixture_sha256="a" * 64,
                    catalog_sha256="d" * 64,
                    matrix_sha256="b" * 64,
                    runner_source_sha256="c" * 64,
                    orchestrator_source_sha256="f" * 64,
                    stateful_menu_contracts_sha256=(
                        STATEFUL_MENU_CONTRACTS_SHA256
                    ),
                    object_matrix_case_count=3,
                    all_matrix_case_count=5,
                    matrix_sequence_count=7,
                    source_binding=source_binding,
                )

        for mutation in (
            lambda row: row["results"][MGBA_REQUIRED_CASES[0]][
                "per_run_merged_result_sha256"
            ].__setitem__(1, "e" * 64),
            lambda row: row["results"][MGBA_REQUIRED_CASES[0]].update({
                "per_run_per_shard_result_sha256": [["f" * 64]],
            }),
            lambda row: row["results"][MGBA_REQUIRED_CASES[0]][
                "per_run_per_shard_result_sha256"
            ][1].__setitem__(0, "e" * 64),
            lambda row: row["results"][MGBA_REQUIRED_CASES[0]].update({
                "unbound_wrapper_field": True,
            }),
        ):
            broken = json.loads(json.dumps(document))
            mutation(broken)
            with self.assertRaises(Stage61BuildError):
                _validate_required_mgba_document(
                    broken,
                    rom_sha256="a" * 64,
                    metadata_sha256="a" * 64,
                    fixture_sha256="a" * 64,
                    catalog_sha256="d" * 64,
                    matrix_sha256="b" * 64,
                    runner_source_sha256="c" * 64,
                    orchestrator_source_sha256="f" * 64,
                    stateful_menu_contracts_sha256=(
                        STATEFUL_MENU_CONTRACTS_SHA256
                    ),
                    object_matrix_case_count=3,
                    all_matrix_case_count=5,
                    matrix_sequence_count=7,
                    source_binding=source_binding,
                )

        for target, key, value in (
            ("orchestrator", "source_sha256", "e" * 64),
            ("catalog", "normalized_sha256", "e" * 64),
            ("catalog", "state_fixture_count", 5),
            ("state_matrix", "source_object_case_count", 5),
            ("state_matrix", "source_event_runtime_case_count", 0),
        ):
            broken = json.loads(json.dumps(document))
            broken[target][key] = value
            with self.assertRaises(Stage61BuildError):
                _validate_required_mgba_document(
                    broken,
                    rom_sha256="a" * 64,
                    metadata_sha256="a" * 64,
                    fixture_sha256="a" * 64,
                    catalog_sha256="d" * 64,
                    matrix_sha256="b" * 64,
                    runner_source_sha256="c" * 64,
                    orchestrator_source_sha256="f" * 64,
                    stateful_menu_contracts_sha256=(
                        STATEFUL_MENU_CONTRACTS_SHA256
                    ),
                    object_matrix_case_count=3,
                    all_matrix_case_count=5,
                    matrix_sequence_count=7,
                    source_binding=source_binding,
                )

    @patch(
        "scripts.build_stage61_display_npc_event_audit."
        "validate_final_mgba_case_result",
        side_effect=lambda _case_id, payload: payload,
    )
    def test_require_mgba_gate_rejects_cross_document_set_tampering(
        self, _final_anchor,
    ) -> None:
        source_binding = self._complete_mgba_source_binding()
        document = self._complete_mgba_document(source_binding)

        def validate(
            candidate: dict, binding: dict = source_binding,
        ) -> dict:
            return _validate_required_mgba_document(
                candidate,
                rom_sha256="a" * 64,
                metadata_sha256="a" * 64,
                fixture_sha256="a" * 64,
                catalog_sha256="d" * 64,
                matrix_sha256="b" * 64,
                runner_source_sha256="c" * 64,
                orchestrator_source_sha256="f" * 64,
                stateful_menu_contracts_sha256=(
                    STATEFUL_MENU_CONTRACTS_SHA256
                ),
                object_matrix_case_count=3,
                all_matrix_case_count=5,
                matrix_sequence_count=7,
                source_binding=binding,
            )

        def rehash(candidate: dict, case_id: str) -> None:
            wrapper = candidate["results"][case_id]
            digest = hashlib.sha256((json.dumps(
                wrapper["result"], ensure_ascii=False,
                sort_keys=True, indent=2,
            ) + "\n").encode("utf-8")).hexdigest()
            wrapper["per_shard_result_sha256"] = [digest]
            wrapper["per_run_merged_result_sha256"] = [digest, digest]
            wrapper["per_run_per_shard_result_sha256"] = [
                [digest], [digest],
            ]

        def substitute_object_runtime_root(payload: dict) -> None:
            row = payload["results"][0]
            substituted = "0x08100030"
            row["runtime_root"] = substituted
            row["preinteraction_object_identity"][
                "template_script"
            ] = substituted
            row["root_probe"]["expected"] = substituted
            for attempt in row["input_sequence_attempts"]:
                attempt["root_script_pointer_expected"] = substituted
                attempt["first_root_script_pointer"] = substituted
                attempt["preinteraction_object_identity"][
                    "template_script"
                ] = substituted

        def substitute_object_xy(payload: dict) -> None:
            row = payload["results"][0]
            position = [12, 13]
            live_current = [19, 20]
            identity = row["preinteraction_object_identity"]
            identity["template_position"] = position
            identity["live_current"] = live_current
            for attempt in row["input_sequence_attempts"]:
                attempt_identity = attempt[
                    "preinteraction_object_identity"
                ]
                attempt_identity["template_position"] = position
                attempt_identity["live_current"] = live_current

        def inject_non_trainer_tower_lifecycle(payload: dict) -> None:
            row = payload["results"][0]
            lifecycle = {
                "kind": "TRAINER_TOWER_ON_TRANSITION",
                "root": "0x081A96EA",
                "map_script_tag": 2,
                "layout_id_expected": 298,
                "layout_id_observed": 298,
                "expected_object": [0, 1],
                "runtime_template_position": [0, 1],
                "expected_movement_type": 0,
                "runtime_template_movement_type": 0,
                "live_expected_visible": True,
                "live_active": True,
                "live_current": [7, 8],
                "exact": True,
            }
            row["preinteraction_object_identity"]["map_lifecycle"] = (
                deepcopy(lifecycle)
            )
            for attempt in row["input_sequence_attempts"]:
                attempt["preinteraction_object_identity"][
                    "map_lifecycle"
                ] = deepcopy(lifecycle)

        payload_mutations = (
            (
                "catalog_batch",
                lambda payload: payload["results"][0].update({
                    "case_id": "object-case-substituted",
                }),
            ),
            (
                "catalog_batch",
                lambda payload: payload["results"][0].update({
                    "owner_key": "OBJECT:999/999:999",
                }),
            ),
            (
                "catalog_batch",
                lambda payload: payload["results"][0].update({
                    "catalog_branch": "SUBSTITUTED",
                }),
            ),
            (
                "catalog_batch",
                lambda payload: payload["results"][0][
                    "input_sequence_attempts"
                ][0].update({"sequence_id": "object-seq-substituted"}),
            ),
            ("catalog_batch", substitute_object_runtime_root),
            ("catalog_batch", substitute_object_xy),
            ("catalog_batch", inject_non_trainer_tower_lifecycle),
            (
                "event_runtime_batch",
                lambda payload: payload["results"][0].update({
                    "case_id": "event-case-substituted",
                }),
            ),
            (
                "event_runtime_batch",
                lambda payload: payload["results"][0].update({
                    "owner_id": "BG:999/999:999",
                }),
            ),
            (
                "event_runtime_batch",
                lambda payload: payload["results"][0][
                    "input_sequence_attempt"
                ].update({"sequence_id": "event-seq-substituted"}),
            ),
            (
                "event_runtime_batch",
                lambda payload: payload["results"][0].update({
                    "effect_signature_ids": ["effect-test-b"],
                }),
            ),
            (
                "event_runtime_batch",
                lambda payload: payload["executed_owner_ids"].__setitem__(
                    0, "BG:999/999:999",
                ),
            ),
            (
                "event_runtime_batch",
                lambda payload: payload.update({
                    # 5416 is the OBJECT+non-OBJECT runtime union, not this
                    # non-OBJECT event batch's unique owner cardinality.
                    "owner_count": 5416,
                    "executed_owner_count": 5416,
                }),
            ),
        )
        for case_id, mutation in payload_mutations:
            broken = json.loads(json.dumps(document))
            mutation(broken["results"][case_id]["result"])
            rehash(broken, case_id)
            with self.subTest(case_id=case_id, mutation=mutation), \
                    self.assertRaises(Stage61BuildError):
                validate(broken)

        document_mutations = (
            lambda row: row.update({
                "interaction_abi_manifest_sha256": "0" * 64,
            }),
            lambda row: row["effect_observer"].update({
                "runtime_control_artifact_sha256": "0" * 64,
            }),
            lambda row: row["effect_registry_binding"]["watch_ids"].append(
                "effect-watch-substituted"
            ),
            lambda row: row["calibration_source"].update({
                "normalized_sha256": "7" * 64,
            }),
            lambda row: row["state_matrix"][
                "event_owner_runtime_scope"
            ]["event_runtime_owner_ids"].__setitem__(
                0, "BG:999/999:999",
            ),
            lambda row: row["state_matrix"][
                "event_owner_runtime_scope"
            ].update({
                "structural_nontrigger_evidence_sha256": "7" * 64,
            }),
            lambda row: row["trainer_tower_save_precondition"]["cases"][
                MGBA_REQUIRED_CASES[0]
            ][0][0]["canonical_source_srms"][0]["sectors"][0].update({
                "first_u32_le": 0x0000B39D,
            }),
            lambda row: row.pop("trainer_tower_save_precondition"),
        )
        for mutation in document_mutations:
            broken = json.loads(json.dumps(document))
            mutation(broken)
            with self.subTest(mutation=mutation), \
                    self.assertRaises(Stage61BuildError):
                validate(broken)

        coherent_binding_tamper = json.loads(json.dumps(source_binding))
        coherent_binding_tamper["event_case_contracts"][0][
            "effect_signature_ids"
        ] = ["effect-test-b"]
        coherent_binding_tamper["summary"][
            "event_case_contracts_sha256"
        ] = _mgba_binding_sha256(
            coherent_binding_tamper["event_case_contracts"]
        )
        with self.assertRaises(Stage61BuildError):
            validate(document, coherent_binding_tamper)

        coherent_structural_tamper = json.loads(json.dumps(source_binding))
        coherent_structural_tamper["structural_evidence_sha256"] = "7" * 64
        coherent_structural_tamper["summary"][
            "structural_evidence_sha256"
        ] = "7" * 64
        with self.assertRaises(Stage61BuildError):
            validate(document, coherent_structural_tamper)

    def test_current_source_binding_exact_joins_all_five_artifacts(
        self,
    ) -> None:
        rom_sha256 = "a" * 64
        owner_id = "OBJECT:001/001:000"
        event_owner_id = "BG:001/001:000"
        structural_owner_id = "COMMON:007"
        object_case_id = "object-case-0"
        event_case_id = "event-case-0"
        object_sequence_id = "object-seq-0"
        event_sequence_id = "event-seq-0"

        object_effect_payload = {
            "runtime_root": "0x08100000",
            "ordered_effects": [],
            "terminal_kind": "FIELD_RELEASE",
        }
        event_effect_payload = {
            "runtime_root": "0x08100010",
            "ordered_effects": [{
                "domain": "flags", "owner": "FLAG:0x0001",
                "relation": "EXACT_FINAL",
                "instruction_address": "0x08100012", "after": True,
            }],
            "terminal_kind": "FIELD_RELEASE",
        }

        def effect_row(payload: dict) -> dict:
            signature_id = (
                f"effect-{_mgba_oracle_canonical_sha256(payload)[:24]}"
            )
            return {"signature_id": signature_id, **payload}

        object_effect = effect_row(object_effect_payload)
        event_effect = effect_row(event_effect_payload)
        object_effect_id = object_effect["signature_id"]
        event_effect_id = event_effect["signature_id"]
        input_sequences = [{"sequence_id": object_sequence_id}]
        control_requirements = {"internal": [], "external": []}
        matrix_case = {
            "case_id": object_case_id,
            "base_case_id": "base-0",
            "owner_key": owner_id,
            "catalog_branch": "DEFAULT",
            "input_sequences": input_sequences,
            "interaction_expected": True,
            "allowed_post_effect_families": [],
            "allowed_post_effects": {},
            "control_requirements": control_requirements,
            "runtime_map_lifecycle": None,
        }
        projected_rows = {object_case_id: {
            "case_id": object_case_id,
            "base_case_id": "base-0",
            "owner_key": owner_id,
            "catalog_branch": "DEFAULT",
            "input_sequences": input_sequences,
            "interaction": {
                "group": 1, "map": 1, "object_index": 0,
                "runtime_root": 0x08100000,
                "object": [0, 1],
            },
            "expect_interaction": True,
        }}
        event_rows = {event_case_id: {
            "case_id": event_case_id,
            "owner_id": event_owner_id,
            "input_sequence": {"sequence_id": event_sequence_id},
            "effect_signature_ids": [event_effect_id],
        }}
        event_proof = {
            "runtime_owner_ids": sorted([owner_id, event_owner_id]),
            "object_runtime_owner_ids": [owner_id],
            "event_runtime_owner_ids": [event_owner_id],
            "structural_nontrigger_owner_ids": [structural_owner_id],
            "structural_nontrigger_evidence": [
                {"owner_id": structural_owner_id},
            ],
            "structural_nontrigger_evidence_sha256": "3" * 64,
        }
        strict = {"entries": [{
            "case_id": "base-0", "owner_key": owner_id,
            "group": 1, "map": 1, "local_id": 1,
            "object": [0, 1],
            "branches": [{"branch_id": "DEFAULT"}],
        }]}
        legacy = {"legacy": True}
        legacy_rows = {"base-0": {
            "case_id": "base-0", "owner_key": owner_id,
            "group": 1, "map": 1, "local_id": 1,
            "object": [0, 1], "branches": ["DEFAULT"],
        }}
        oracle_case = {
            "case_id": object_case_id,
            "owner_key": owner_id,
            "status": "PASS",
            "runner_contract": {
                "input_sequences": input_sequences,
                "allowed_post_effect_families": [],
                "allowed_post_effects": {},
                "control_requirements": control_requirements,
            },
        }
        oracle = {
            "schema_version": 1,
            "kind": "STAGE61_ALL_CASE_INDEPENDENT_INTERACTION_ORACLES",
            "status": "PASS",
            "cyclic_decision_contract_sha256": "c" * 64,
            "case_count": 1,
            "generated_case_count": 1, "unresolved_case_count": 0,
            "cases": [oracle_case], "unresolved": [],
            "decision_coverage": {},
            "assertions": {"complete": True},
        }
        oracle["audit_sha256"] = _mgba_oracle_canonical_sha256(oracle)

        runtime_event_case = {
            "case_id": event_case_id, "owner_id": event_owner_id,
            "root_assignment_id": "assignment-event",
            "trigger_path": {},
            "input_sequence": {"sequence_id": event_sequence_id},
            "control_requirements": control_requirements,
            "effect_signature_ids": [event_effect_id],
            "required_postconditions": {},
            "battle_start_required_postconditions": None,
            "text_oracle": {},
            "terminal_kind": "FIELD_RELEASE", "source_provenance": {},
        }
        interaction_abi = {
            "schema_version": 1,
            "kind": "STAGE61_INTERACTION_ABI_MANIFEST",
            "status": "PASS", "stage61_sha256": rom_sha256,
        }
        interaction_abi["manifest_sha256"] = _mgba_oracle_canonical_sha256(
            interaction_abi
        )
        stub_effect_binding = self._complete_mgba_source_binding()[
            "effect_registry_binding"
        ]
        runtime = {
            "schema_version": 1,
            "kind": "STAGE61_RUNTIME_CONTROL_EXPANSION_CONTRACT",
            "status": "PASS", "stage61_sha256": rom_sha256,
            "input_provenance": {
                "interaction_abi_manifest_sha256": interaction_abi[
                    "manifest_sha256"
                ],
                "cyclic_decision_contract_sha256": "c" * 64,
            },
            "counts": {
                "event_owner_count": 3,
                "runtime_required_owner_count": 2,
                "structural_nontrigger_owner_count": 1,
                "event_runtime_case_count": 1,
                "map_physical_owner_count": 0,
                "map_composite_case_count": 0,
                "map_composite_sequence_count": 0,
                "map_covered_owner_count": 0,
            },
            "roots": [{
                "candidate_assignments": [{
                    "effect_signature_ids": [
                        object_effect_id, event_effect_id,
                    ],
                }],
            }],
            "decision_signatures": [],
            "effect_signatures": [object_effect, event_effect],
            "effect_templates": [], "effect_instances": [],
            "effect_case_bindings": [],
            "effect_instance_watch_bindings": [],
            "no_dispatch_contracts": [],
            "no_dispatch_watch_bindings": [],
            "runner_fixtures": {},
            "event_owner_trigger_contracts": [
                {
                    "owner_id": owner_id, "owner_kind": "OBJECT",
                    "runtime_case_required": True,
                    "runtime_case_ids": [],
                },
                {
                    "owner_id": event_owner_id, "owner_kind": "BG",
                    "runtime_case_required": True,
                    "runtime_case_ids": [event_case_id],
                },
                {
                    "owner_id": structural_owner_id,
                    "owner_kind": "COMMON",
                    "runtime_case_required": False,
                    "runtime_case_ids": [],
                },
            ],
            "hidden_item_execution": {},
            "cyclic_decision_contract_integration": {
                "contract_sha256": "c" * 64,
            },
            "event_runtime_cases": [runtime_event_case],
            "unresolved": [], "unresolved_count": 0,
            "assertions": {"complete": True},
        }
        runtime["contract_sha256"] = _mgba_oracle_canonical_sha256(runtime)

        def bound_runtime_sha256(runtime_source: dict) -> str:
            bound = json.loads(json.dumps(runtime_source))
            bound["event_owner_trigger_contracts"][0][
                "runtime_case_ids"
            ] = [object_case_id]
            bound["object_matrix_case_binding"] = {
                "policy": (
                    "PHASE2_EXPANDED_MATRIX_IS_OBJECT_EXECUTION_REGISTRY"
                ),
                "object_owner_count": 1,
                "object_case_count": 1,
                "removed_pre_matrix_object_event_case_count": 0,
                "nonobject_event_case_count": 1,
                "map_lifecycle_composite_case_count": 0,
                "map_lifecycle_covered_physical_owner_count": 0,
                "assertions": {
                    "all_3108_object_owners_bound": False,
                    "object_and_nonobject_case_ids_disjoint": True,
                    "nonobject_event_cases_preserved_exact": True,
                    "all_map_owners_bound_to_exact_one_composite_case": True,
                },
            }
            bound.pop("contract_sha256")
            bound["contract_sha256"] = _mgba_oracle_canonical_sha256(bound)
            return _mgba_oracle_canonical_sha256(bound)

        oracle_sha256 = _mgba_oracle_canonical_sha256(oracle)
        self.assertNotEqual(_mgba_binding_sha256(oracle), oracle_sha256)
        matrix = {
            "cases": [matrix_case],
            "event_runtime_cases": [runtime_event_case],
            "oracle": {
                "catalog_sha256": oracle_sha256, "case_count": 1,
            },
            "runtime_control_expansion": {
                "oracle_catalog_sha256": oracle_sha256,
                "contract_sha256": bound_runtime_sha256(runtime),
            },
        }
        normalized_matrix = {"normalized": "matrix"}

        def invoke(
            *, matrix_source: dict = matrix,
            strict_normalized: dict = strict,
            legacy_normalized: dict = legacy,
            legacy_index: dict = legacy_rows,
            projected: dict = projected_rows,
            normalized_events: dict = event_rows,
            proof: dict = event_proof,
            oracle_source: dict = oracle,
            runtime_source: dict = runtime,
            identity_only: bool = True,
        ) -> dict:
            with patch(
                "scripts.build_stage61_display_npc_event_audit."
                "validate_mgba_state_matrix_document",
                return_value=(normalized_matrix, projected),
            ), patch(
                "scripts.build_stage61_display_npc_event_audit."
                "validate_mgba_catalog_document",
                return_value=(strict_normalized, {}),
            ), patch(
                "scripts.build_stage61_display_npc_event_audit."
                "validate_mgba_legacy_catalog_document",
                return_value=(legacy_normalized, legacy_index),
            ), patch(
                "scripts.build_stage61_display_npc_event_audit."
                "project_catalog_state_matrix",
                return_value=projected,
            ), patch(
                "scripts.build_stage61_display_npc_event_audit."
                "normalize_event_runtime_projection",
                return_value=(normalized_events, proof),
            ), patch(
                "scripts.build_stage61_display_npc_event_audit."
                "validate_mgba_identity_only_strict_catalog_contract",
                return_value=True,
                side_effect=(
                    None if identity_only else
                    Stage61MgbaError("LEGACY_EXPECTATION")
                ),
            ), patch(
                "scripts.build_stage61_display_npc_event_audit."
                "EVENT_RUNTIME_REQUIRED_OWNER_COUNT", 2,
            ), patch(
                "scripts.build_stage61_display_npc_event_audit."
                "EVENT_STRUCTURAL_NONTRIGGER_OWNER_COUNT", 1,
            ), patch(
                "scripts.build_stage61_display_npc_event_audit."
                "EVENT_OWNER_COUNT", 3,
            ), patch(
                "scripts.build_stage61_display_npc_event_audit."
                "_mgba_effect_registry_source_binding",
                return_value=stub_effect_binding,
            ):
                return _required_mgba_source_binding(
                    matrix_source, {}, {}, oracle_source, runtime_source,
                    interaction_abi, {},
                    rom_sha256=rom_sha256,
                )

        binding = invoke()
        self.assertEqual(binding["summary"]["base_object_count"], 1)
        self.assertEqual(binding["summary"]["event_owner_count"], 1)
        self.assertEqual(binding["summary"]["runtime_owner_count"], 2)
        self.assertEqual(binding["summary"]["effect_signature_count"], 2)

        with self.assertRaises(Stage61BuildError):
            invoke(identity_only=False)

        broken_legacy = json.loads(json.dumps(legacy_rows))
        broken_legacy["base-0"]["owner_key"] = "OBJECT:999/999:999"
        with self.assertRaises(Stage61BuildError):
            invoke(legacy_index=broken_legacy)

        broken_matrix = json.loads(json.dumps(matrix))
        broken_matrix["cases"][0]["input_sequences"][0][
            "sequence_id"
        ] = "object-seq-substituted"
        with self.assertRaises(Stage61BuildError):
            invoke(matrix_source=broken_matrix)

        broken_oracle = json.loads(json.dumps(oracle))
        broken_oracle["cases"][0]["owner_key"] = "OBJECT:999/999:999"
        unsigned_oracle = json.loads(json.dumps(broken_oracle))
        unsigned_oracle.pop("audit_sha256")
        broken_oracle["audit_sha256"] = _mgba_oracle_canonical_sha256(
            unsigned_oracle
        )
        with self.assertRaises(Stage61BuildError):
            invoke(oracle_source=broken_oracle)

        unused_effect_payload = {
            "runtime_root": "0x08100020",
            "ordered_effects": [], "terminal_kind": "BATTLE_START",
        }
        broken_runtime = json.loads(json.dumps(runtime))
        broken_runtime["effect_signatures"].append(
            effect_row(unused_effect_payload)
        )
        broken_runtime.pop("contract_sha256")
        broken_runtime["contract_sha256"] = _mgba_oracle_canonical_sha256(
            broken_runtime
        )
        with self.assertRaises(Stage61BuildError):
            invoke(runtime_source=broken_runtime)

        broken_events = json.loads(json.dumps(event_rows))
        broken_events[event_case_id]["owner_id"] = "BG:001/001:999"
        with self.assertRaises(Stage61BuildError):
            invoke(normalized_events=broken_events)

        broken_proof = json.loads(json.dumps(event_proof))
        broken_proof["event_runtime_owner_ids"] = []
        with self.assertRaises(Stage61BuildError):
            invoke(proof=broken_proof)

    def test_require_mgba_gate_rejects_case_specific_anchor_failure(
        self,
    ) -> None:
        source_binding = self._complete_mgba_source_binding()
        document = self._complete_mgba_document(source_binding)
        with patch(
            "scripts.build_stage61_display_npc_event_audit."
            "validate_final_mgba_case_result",
            side_effect=Stage61MgbaError("required anchor missing"),
        ), self.assertRaisesRegex(Stage61BuildError, "case固有"):
            _validate_required_mgba_document(
                document,
                rom_sha256="a" * 64,
                metadata_sha256="a" * 64,
                fixture_sha256="a" * 64,
                catalog_sha256="d" * 64,
                matrix_sha256="b" * 64,
                runner_source_sha256="c" * 64,
                orchestrator_source_sha256="f" * 64,
                stateful_menu_contracts_sha256=(
                    STATEFUL_MENU_CONTRACTS_SHA256
                ),
                object_matrix_case_count=3,
                all_matrix_case_count=5,
                matrix_sequence_count=7,
                source_binding=source_binding,
            )

    def test_runtime_control_contract_set_covers_decision_and_effect_signatures(self) -> None:
        base_case = {
            "case_id": "matrix-001-002-003-default-000",
            "base_case_id": "cal-001-002-003",
            "owner_key": "OBJECT:001/002:003",
            "catalog_branch": "DEFAULT",
            "owner_role": "DIALOGUE",
            "interaction": {
                "group": 1, "map": 2, "object_index": 3,
                "local_id": 4, "object": [5, 6],
                "runtime_root": "0x08100000",
            },
            "state": {"flags": [], "vars": [], "items": [], "trainers": []},
            "expected_object_visible": True,
            "interaction_expected": True,
            "choice_candidates": ["ADVANCE"],
            "expected_terminal": "FIELD_RELEASE",
            "reachability_basis": "TEST",
            "static_path_ids": [], "source_assignment": {}, "baseline": True,
        }
        document = {
            "schema_version": 1, "task": (
                "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT"
            ),
            "stage": 61, "status": "PASS", "rom_sha256": "0" * 64,
            "inputs": {}, "algorithm": {},
            "counts": {
                "matrix_case_count": 1, "interactive_case_count": 1,
                "hidden_assertion_count": 0, "max_flags_in_case": 0,
            },
            "runner_projection": {
                "mode": "EXTENDED_STATE_TSV_REQUIRED",
                "required_columns": [
                    "flags", "vars", "items", "trainers",
                    "expect_visible", "expect_interaction",
                ],
            },
            "assertions": {"base": True}, "semantic_roots": [],
            "cases": [base_case],
        }
        domain = {
            "kind": "FLAG", "id": 0x1234,
            "source_ids": [0x1234], "read_addresses": ["0x08100000"],
            "candidate_values": [False, True], "relations": [],
            "owner_keys": [base_case["owner_key"]],
        }

        def assignment(value: bool, ordinal: int) -> dict:
            return {
                "assignment_id": f"assignment-{ordinal}",
                "applicable_owner_ids": [base_case["owner_key"]],
                "physical_player_position_consumed": False,
                "compatible_catalog_branches": ["DEFAULT"],
                "required_values": [{
                    "kind": "FLAG", "id": 0x1234, "value": value,
                    "owner_keys": [base_case["owner_key"]],
                    "fixture_keys": [],
                    "relation_evidence": [],
                }],
                "reachable": True, "baseline": ordinal == 0,
                "baseline_basis": "FRESH_SAVE" if ordinal == 0 else "NOT_BASELINE",
                "ordered_decision_signature_ids": [f"decision-{ordinal}"],
                "effect_signature_ids": [f"effect-{ordinal}"],
                "terminal_kinds": ["FIELD_RELEASE"],
                "evidence": {
                    "cfg_path_instruction_addresses": ["0x08100000"],
                    "producer_abi_keys": [],
                },
            }

        contract = {
            "schema_version": 1,
            "kind": "STAGE61_RUNTIME_CONTROL_EXPANSION_CONTRACT",
            "status": "PASS", "stage61_sha256": "0" * 64,
            "unresolved": [], "unresolved_count": 0,
            "runner_fixtures": {},
            "roots": [{
                "runtime_root": "0x08100000",
                "owner_keys": [base_case["owner_key"]],
                "source_provenance": "SYNTHETIC_TEST",
                "external_domains": [domain], "internal_producers": [],
                "candidate_assignments": [assignment(False, 0), assignment(True, 1)],
            }],
            "decision_signatures": ["decision-0", "decision-1"],
            "effect_signatures": ["effect-0", "effect-1"],
            "assertions": {"unresolved_zero": True},
        }
        contract["contract_sha256"] = hashlib.sha256((
            json.dumps(
                contract, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"),
            ) + "\n"
        ).encode("utf-8")).hexdigest()
        result = expand_stage61_runtime_control_matrix(document, contract)
        self.assertEqual(result["counts"]["matrix_case_count"], 2)
        self.assertEqual(
            {
                row["state"]["flags"][0]["value"]
                for row in result["cases"]
            },
            {False, True},
        )
        self.assertTrue(all(result["assertions"].values()))
        self.assertEqual(
            result["runtime_control_expansion"]["root_reports"], [{
                "runtime_root": "0x08100000",
                "owner_keys": [base_case["owner_key"]],
                "source_provenance": "SYNTHETIC_TEST",
                "external_domain_count": 1,
                "internal_producer_count": 0,
                "candidate_assignment_count": 2,
                "baseline_assignment_id": "assignment-0",
                "compatible_catalog_branches": ["DEFAULT"],
            }],
        )

        # The four executor representatives belong to roots, but the 26
        # remaining box-number layouts are runner-only.  They must survive
        # expansion without being falsely rejected as unreferenced fixtures.
        runner_scenario_ids = (
            "party_space",
            *(f"pc_current_box_{box_id:02d}" for box_id in range(14)),
            *(f"pc_next_box_{box_id:02d}" for box_id in range(14)),
            "storage_full",
        )
        executor_scenario_ids = (
            "party_space", "pc_current_box_00", "pc_next_box_13",
            "storage_full",
        )
        registry = {}
        manifest_rows = []
        for scenario_id in runner_scenario_ids:
            current_box = 0
            target_box = None
            target_pos = None
            if scenario_id == "party_space":
                equivalence, expected_result, party_count = \
                    "PARTY_SPACE", 0, 5
            elif scenario_id.startswith("pc_current_box_"):
                current_box = int(scenario_id.rsplit("_", 1)[1])
                target_box, target_pos = current_box, 0
                equivalence, expected_result, party_count = \
                    "PC_CURRENT_BOX", 1, 6
            elif scenario_id.startswith("pc_next_box_"):
                current_box = int(scenario_id.rsplit("_", 1)[1])
                target_box, target_pos = (current_box + 1) % 14, 0
                equivalence = "PC_NEXT_BOX_WRAP" if current_box == 13 \
                    else "PC_NEXT_BOX"
                expected_result, party_count = 1, 6
            else:
                equivalence, expected_result, party_count = \
                    "STORAGE_FULL", 2, 6
            payload = {
                "fixture_kind": "GIFT_STORAGE_TRANSACTION_STATE",
                "scenario_id": scenario_id,
                "executor_equivalence_class": equivalence,
                "expected_result": expected_result,
                "current_box": current_box,
                "expected_mon_box_id": target_box,
                "expected_mon_box_pos": target_pos,
                "party_count": party_count,
                "expected_original_box": (
                    current_box if party_count == 6 else None
                ),
                "expected_var_pc_box_after": (
                    target_box if target_box is not None else current_box
                ),
                "var_pc_box_to_send_mon": current_box,
                "shown_box_was_full_message": False,
                "expected_shown_box_full_after_give": False,
                "map_section_id": 92,
                "map_section_source_root": "0x081859FA",
            }
            reference = hashlib.sha256((json.dumps(
                payload, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"),
            ) + "\n").encode("utf-8")).hexdigest()
            registry[reference] = payload
            manifest_rows.append({
                "scenario_id": scenario_id,
                "fixture_key": reference,
                "executor_representative": (
                    scenario_id in executor_scenario_ids
                ),
                "executor_equivalence_class": equivalence,
                "expected_result": expected_result,
                "current_box": current_box,
                "expected_mon_box_id": target_box,
                "expected_mon_box_pos": target_pos,
            })
        gift_contract = deepcopy(contract)
        gift_contract["runner_fixtures"] = registry
        gift_contract["dedicated_fixture_sweeps"] = {
            "GIFT_STORAGE_TRANSACTION_STATE": {
                "schema_version": 1,
                "fixture_kind": "GIFT_STORAGE_TRANSACTION_STATE",
                "relation": (
                    "GIVEMON_PARTY600_STORAGE83D0_SAVEBLOCK1_RAW_EXACT"
                ),
                "executor_representative_count": 4,
                "runner_exhaustive_layout_count": 30,
                "executor_representative_scenario_ids": list(
                    executor_scenario_ids
                ),
                "runner_exhaustive_scenario_ids": list(
                    runner_scenario_ids
                ),
                "runner_sweep_root": "0x081859FA",
                "runner_sweep_map_section_id": 92,
                "scenarios": manifest_rows,
                "assertions": {
                    "root_executor_uses_four_quotient_representatives": True,
                    "runner_registry_contains_all_thirty_layouts": True,
                    "runner_layout_fixture_keys_are_unique": True,
                    "c6_box_name_never_forks_independently": True,
                },
            },
        }
        gift_contract.pop("contract_sha256")
        gift_contract["contract_sha256"] = hashlib.sha256((json.dumps(
            gift_contract, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ) + "\n").encode("utf-8")).hexdigest()
        gift_result = expand_stage61_runtime_control_matrix(
            document, gift_contract,
        )
        self.assertEqual(
            gift_result["dedicated_fixture_sweeps"],
            gift_contract["dedicated_fixture_sweeps"],
        )
        self.assertEqual(
            gift_result["counts"]["runtime_dedicated_runner_fixture_count"],
            30,
        )
        self.assertEqual(
            gift_result["runtime_control_expansion"]
            ["root_referenced_fixture_count"],
            0,
        )
        self.assertTrue(
            gift_result["assertions"]
            ["runtime_fixture_registry_exact_and_fully_used"]
        )

        gift_mutations = (
            lambda row: row["dedicated_fixture_sweeps"]
                ["GIFT_STORAGE_TRANSACTION_STATE"]["scenarios"]
                [1].update({"expected_mon_box_id": 13}),
            lambda row: row["dedicated_fixture_sweeps"]
                ["GIFT_STORAGE_TRANSACTION_STATE"]["scenarios"]
                .__setitem__(1, deepcopy(row["dedicated_fixture_sweeps"]
                    ["GIFT_STORAGE_TRANSACTION_STATE"]["scenarios"][0])),
            lambda row: row["dedicated_fixture_sweeps"]
                ["GIFT_STORAGE_TRANSACTION_STATE"].update({
                    "runner_sweep_map_section_id": 93,
                }),
        )
        for mutate in gift_mutations:
            broken = deepcopy(gift_contract)
            mutate(broken)
            broken.pop("contract_sha256")
            broken["contract_sha256"] = hashlib.sha256((json.dumps(
                broken, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"),
            ) + "\n").encode("utf-8")).hexdigest()
            with self.assertRaises(Stage61CatalogStateMatrixError):
                expand_stage61_runtime_control_matrix(document, broken)

        for mutate in (
            lambda row: row["roots"][0]["candidate_assignments"][0][
                "required_values"
            ][0].pop("fixture_keys"),
            lambda row: row["roots"][0]["candidate_assignments"][0][
                "required_values"
            ][0].update({"fixture_keys": ["1" * 64]}),
            lambda row: row["roots"][0]["external_domains"].append({
                "kind": "VAR", "id": 0x4000,
                "owner_keys": [base_case["owner_key"]],
            }),
        ):
            broken = json.loads(json.dumps(contract))
            mutate(broken)
            with self.assertRaises(Stage61CatalogStateMatrixError):
                expand_stage61_runtime_control_matrix(document, broken)

    def test_player_position_assignment_is_bound_to_exact_physical_owner(
        self,
    ) -> None:
        owners = ["OBJECT:003/014:002", "OBJECT:003/014:003"]

        def base_case(owner: str, ordinal: int) -> dict:
            return {
                "case_id": f"matrix-003-014-{ordinal + 2:03d}-default-000",
                "base_case_id": f"cal-003-014-{ordinal + 2:03d}",
                "owner_key": owner, "catalog_branch": "DEFAULT",
                "owner_role": "DIALOGUE",
                "interaction": {
                    "group": 3, "map": 14, "object_index": ordinal + 2,
                    "local_id": ordinal + 3, "object": [9, 24],
                    "runtime_root": "0x08174475",
                },
                "interaction_execution": {
                    "trigger": (
                        "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A"
                    ),
                    "start": [9, 22], "walk_sequence": ["DOWN"],
                    "stance": [9, 23], "action": "DOWN",
                    "interaction_distance": 1, "counter_tile": None,
                    "actual_walk_required": True,
                    "actual_walk_exception": None,
                    "walk_path_basis": "SYNTHETIC_EXACT_STANCE",
                    "direct_script_call_forbidden": True,
                },
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "expected_object_visible": True,
                "interaction_expected": True,
                "choice_candidates": ["ADVANCE"],
                "expected_terminal": "FIELD_RELEASE",
                "reachability_basis": "TEST", "static_path_ids": [],
                "source_assignment": {}, "baseline": ordinal == 0,
            }

        cases = [base_case(owner, index) for index, owner in enumerate(owners)]
        document = {
            "schema_version": 1,
            "task": "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT",
            "stage": 61, "status": "PASS", "rom_sha256": "0" * 64,
            "inputs": {}, "algorithm": {},
            "counts": {
                "matrix_case_count": 2, "interactive_case_count": 2,
                "hidden_assertion_count": 0, "max_flags_in_case": 0,
            },
            "runner_projection": {
                "mode": "EXTENDED_STATE_TSV_REQUIRED",
                "required_columns": [
                    "flags", "vars", "items", "trainers",
                    "expect_visible", "expect_interaction",
                ],
            },
            "assertions": {"base": True}, "semantic_roots": [],
            "cases": cases,
        }
        position = {
            "x": 9, "y": 23, "group": 3, "map": 14,
            "apply_relation": "ACTUAL_STOCK_WARP_THEN_REAL_MOVEMENT",
        }
        domain = {
            "kind": "PLAYER_POSITION", "id": 0,
            "source_ids": [0], "read_addresses": ["0x081745FA"],
            "candidate_values": [position],
            "relations": [{
                "operator": "ACTUAL_PLAYER_COORDINATES_BEFORE_INTERACTION",
                "instruction_address": "0x081745FA",
                "source": None, "abi_key": None,
            }],
            "owner_keys": [owners[0]],
        }

        def assignment(owner: str, ordinal: int) -> dict:
            consumed = ordinal == 0
            required_values = []
            if consumed:
                required_values.append({
                    "kind": "PLAYER_POSITION", "id": 0,
                    "value": position, "owner_keys": [owner],
                    "fixture_keys": [],
                    "relation_evidence": [{
                        "operator":
                            "ACTUAL_PLAYER_COORDINATES_BEFORE_INTERACTION",
                    }],
                })
            return {
                "assignment_id": f"position-assignment-{ordinal}",
                "applicable_owner_ids": [owner],
                "physical_player_position_consumed": consumed,
                "compatible_catalog_branches": ["DEFAULT"],
                "required_values": required_values,
                "reachable": True, "baseline": ordinal == 0,
                "baseline_basis": (
                    "LOWEST_PINNED_REACHABLE_CONTROL_VECTOR"
                    if ordinal == 0 else "OWNER_PHYSICAL_STANCE"
                ),
                "ordered_decision_signature_ids": [f"decision-{ordinal}"],
                "effect_signature_ids": [f"effect-{ordinal}"],
                "terminal_kinds": ["FIELD_RELEASE"],
                "evidence": {
                    "cfg_path_instruction_addresses": [
                        "0x081745FA" if consumed else "0x08174482"
                    ],
                    "producer_abi_keys": [],
                    "physical_execution_owner_ids": [owner],
                },
            }

        contract = {
            "schema_version": 1,
            "kind": "STAGE61_RUNTIME_CONTROL_EXPANSION_CONTRACT",
            "status": "PASS", "stage61_sha256": "0" * 64,
            "unresolved": [], "unresolved_count": 0,
            "runner_fixtures": {},
            "roots": [{
                "runtime_root": "0x08174475", "owner_keys": owners,
                "source_provenance": "SYNTHETIC_TEST",
                "external_domains": [domain], "internal_producers": [],
                "candidate_assignments": [
                    assignment(owners[0], 0),
                    assignment(owners[0], 1),
                    assignment(owners[1], 2),
                ],
            }],
            "decision_signatures": [
                "decision-0", "decision-1", "decision-2",
            ],
            "effect_signatures": [
                "effect-0", "effect-1", "effect-2",
            ],
            "assertions": {"unresolved_zero": True},
        }

        def seal(value: dict) -> dict:
            value.pop("contract_sha256", None)
            value["contract_sha256"] = hashlib.sha256((
                json.dumps(
                    value, ensure_ascii=False, sort_keys=True,
                    separators=(",", ":"),
                ) + "\n"
            ).encode("utf-8")).hexdigest()
            return value

        result = expand_stage61_runtime_control_matrix(
            document, seal(contract),
        )
        self.assertEqual(
            [
                row["runtime_control_assignment"]["applicable_owner_ids"]
                for row in result["cases"]
            ],
            [[owners[0]], [owners[0]], [owners[1]]],
        )
        self.assertEqual(
            result["cases"][0]["control_requirements"]["external"][0][
                "required_value_in_matrix_case"
            ],
            position,
        )
        self.assertEqual(
            result["cases"][0]["control_requirements"]["external"][0][
                "relations"
            ],
            [{
                "operator":
                    "ACTUAL_PLAYER_COORDINATES_BEFORE_INTERACTION",
            }],
        )
        self.assertEqual(
            result["cases"][1]["control_requirements"]["external"],
            [],
        )
        self.assertEqual(
            result["cases"][2]["control_requirements"]["external"],
            [],
        )

        consumed_false_forgery = deepcopy(contract)
        consumed_false_forgery["roots"][0]["candidate_assignments"][0][
            "physical_player_position_consumed"
        ] = False
        with self.assertRaises(Stage61CatalogStateMatrixError):
            expand_stage61_runtime_control_matrix(
                document, seal(consumed_false_forgery),
            )

        missing_domain = deepcopy(contract)
        missing_domain["roots"][0]["external_domains"] = []
        with self.assertRaises(Stage61CatalogStateMatrixError):
            expand_stage61_runtime_control_matrix(
                document, seal(missing_domain),
            )

        missing_row = deepcopy(contract)
        missing_row["roots"][0]["candidate_assignments"][0][
            "required_values"
        ] = []
        with self.assertRaises(Stage61CatalogStateMatrixError):
            expand_stage61_runtime_control_matrix(
                document, seal(missing_row),
            )

        extra_row = deepcopy(contract)
        forged_row = deepcopy(
            extra_row["roots"][0]["candidate_assignments"][0][
                "required_values"
            ][0]
        )
        forged_row["owner_keys"] = [owners[0]]
        extra_row["roots"][0]["candidate_assignments"][1][
            "required_values"
        ] = [forged_row]
        with self.assertRaises(Stage61CatalogStateMatrixError):
            expand_stage61_runtime_control_matrix(
                document, seal(extra_row),
            )

        oversized_scope = deepcopy(contract)
        oversized_scope["roots"][0]["external_domains"][0][
            "owner_keys"
        ] = owners
        with self.assertRaises(Stage61CatalogStateMatrixError):
            expand_stage61_runtime_control_matrix(
                document, seal(oversized_scope),
            )

        nonzero_id = deepcopy(contract)
        nonzero_id["roots"][0]["external_domains"][0]["id"] = 1
        with self.assertRaises(Stage61CatalogStateMatrixError):
            expand_stage61_runtime_control_matrix(
                document, seal(nonzero_id),
            )

        duplicate_domain = deepcopy(contract)
        duplicate_domain["roots"][0]["external_domains"].append(
            deepcopy(duplicate_domain["roots"][0]["external_domains"][0])
        )
        with self.assertRaises(Stage61CatalogStateMatrixError):
            expand_stage61_runtime_control_matrix(
                document, seal(duplicate_domain),
            )

        empty_position_relation = deepcopy(contract)
        empty_position_relation["roots"][0]["candidate_assignments"][0][
            "required_values"
        ][0]["relation_evidence"] = []
        with self.assertRaises(Stage61CatalogStateMatrixError):
            expand_stage61_runtime_control_matrix(
                document, seal(empty_position_relation),
            )

        wrong_position = deepcopy(contract)
        wrong_position["roots"][0]["candidate_assignments"][0][
            "required_values"
        ][0]["value"] = {**position, "y": 24}
        with self.assertRaisesRegex(
            Stage61CatalogStateMatrixError,
            "PLAYER_POSITION/case stance不一致",
        ):
            expand_stage61_runtime_control_matrix(
                document, seal(wrong_position),
            )

    def test_large_domain_uses_bounded_pairwise_candidates(self) -> None:
        domains = tuple(
            ControlDomain(ControlKey("flag", index), (0, 1), index, ())
            for index in range(15)
        )
        candidates, mode, raw = _candidate_assignments(domains)
        self.assertEqual(mode, "BOUNDED_PAIRWISE_FALLBACK")
        self.assertEqual(raw, 32768)
        self.assertLess(len(candidates), raw)
        for left in range(len(domains)):
            for right in range(left + 1, len(domains)):
                self.assertEqual(
                    {(row[left], row[right]) for row in candidates},
                    {(0, 0), (0, 1), (1, 0), (1, 1)},
                )

    def test_visibility_conflict_is_not_silently_overwritten(self) -> None:
        rows, conflicts = _merge_flags((
            {"id": 0x1847, "value": True, "reason": "BRANCH"},
            {"id": 0x1847, "value": False, "reason": "VISIBILITY"},
        ))
        self.assertEqual(rows, [{
            "id": 0x1847,
            "value": True,
            "reasons": ["BRANCH", "VISIBILITY"],
        }])
        self.assertEqual(len(conflicts), 1)


class Stage61CatalogStateMatrixIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        retained_legacy = json.loads((
            ROOT / "reports/generated/stage61_npc_interaction_catalog_legacy.json"
        ).read_text(encoding="utf-8"))
        semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text(encoding="utf-8"))
        cls.semantic = semantic
        dependency = json.loads((
            ROOT / "reports/generated/stage61_event_dependency_graph.json"
        ).read_text(encoding="utf-8"))
        cls.stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        cls.stage60 = (
            ROOT / "build/stages/60_wild_species_root_repair.gba"
        ).read_bytes()
        cls.fixtures = json.loads((
            ROOT / "reports/generated/stage61_mgba_fixtures.json"
        ).read_text(encoding="utf-8"))
        cls.map_catalog = json.loads((
            ROOT / "reports/generated/stage61_map_display_catalog.json"
        ).read_text(encoding="utf-8"))
        cls.interaction_abi = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text(encoding="utf-8"))
        cls.repair_manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text(encoding="utf-8"))
        cls.event_owner_inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text(encoding="utf-8"))
        placement = json.loads((
            ROOT / "reports/generated/stage61_final_placement_audit.json"
        ).read_text(encoding="utf-8"))
        cls.legacy = _strict_legacy_catalog_fixture(
            retained_legacy, placement, cls.event_owner_inventory,
            cls.stage61,
        )
        cls.clean = (
            ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
        ).read_bytes()
        cls.document = build_stage61_catalog_state_matrix(
            cls.legacy, semantic, dependency,
            stage61_rom=cls.stage61,
            clean_rom=cls.clean,
            event_owner_inventory=cls.event_owner_inventory,
        )

    def test_additional_semantic_ranges_bind_final_post_placement_rom(self) -> None:
        ranges = self.semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]
        self.assertEqual(len(ranges), 2)
        for row in ranges:
            start = int(row["target_base"], 0) - 0x08000000
            raw = self.stage61[start:start + int(row["size"])]
            self.assertEqual(len(raw), int(row["size"]))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
        explicit = next(
            row for row in ranges
            if row["kind"] == "EXPLICIT_PROJECT_ADAPTERS_AND_TRACKED_TEXT"
        )
        self.assertEqual(len(explicit["text_relocations"]), 8)
        for row in explicit["text_relocations"]:
            contract = row["semantic_contract"]
            authored = bytes.fromhex(contract["authored_raw_hex"])
            self.assertEqual(len(authored), row["raw_size"])
            self.assertEqual(
                hashlib.sha256(authored).hexdigest(),
                contract["authored_raw_sha256"],
            )
            self.assertEqual(contract["authored_raw_sha256"], row["raw_sha256"])

    def test_all_live_special_and_native_abis_are_source_and_span_pinned(
        self,
    ) -> None:
        abi = self.interaction_abi
        self.assertEqual(abi["status"], "PASS")
        self.assertEqual(len(abi["special_abis"]), 175)
        self.assertEqual(len(abi["native_abis"]), 88)
        self.assertEqual(len(abi["effect_abis"]), 263)
        self.assertEqual(abi["registry_audit"]["site_count"], 2586)
        self.assertEqual(abi["registry_audit"]["unresolved_site_count"], 0)
        self.assertTrue(all(abi["assertions"].values()))
        self.assertEqual(
            self.repair_manifest["interaction_abi_manifest_sha256"],
            abi["manifest_sha256"],
        )
        self.assertEqual(self.repair_manifest["status"], "PASS")
        self.assertEqual(len(self.repair_manifest["special_abis"]), 175)
        self.assertEqual(len(self.repair_manifest["native_abis"]), 88)

    def test_popup_and_diglett_natural_fixtures_are_exact(self) -> None:
        popup = self.fixtures["map_popup_regressions"]
        self.assertEqual(popup["status"], "PASS")
        self.assertEqual(len(popup["cases"]), 7)
        self.assertEqual(
            {(row["group"], row["map"]) for row in popup["cases"]},
            {
                (97, 36), (97, 37), (97, 38),
                (1, 36), (1, 37), (1, 38), (1, 73),
            },
        )
        self.assertTrue(all(
            row["stock_warp"]["seed_basis"]
                == "EXACT_INCOMING_WARP_DESTINATION_ROW"
            and row["show_map_name"] is True
            and len(row["expected_name_raw_sha256"]) == 64
            for row in popup["cases"]
        ))
        diglett = self.fixtures["diglett_b1f_natural_interaction"]
        self.assertEqual(diglett["owner_id"], "OBJECT:097/037:000")
        self.assertEqual(diglett["local_id"], 1)
        self.assertGreater(diglett["walk_step_count"], 0)
        self.assertEqual(
            len(diglett["walk_key_sequence"]), diglett["walk_step_count"]
        )
        self.assertEqual(diglett["walk_tiles"][-1], diglett["stance"])
        self.assertTrue(diglett["press_a"])

    def test_all_non_kanto_map_names_are_pinned_to_stage60_bytes(self) -> None:
        catalog = self.map_catalog
        self.assertEqual(catalog["physical_map_count"], 678)
        self.assertEqual(catalog["non_kanto_map_count"], 425)
        self.assertEqual(catalog["failure_count"], 0)
        self.assertTrue(all(catalog["assertions"].values()))
        non_kanto = [
            row for row in catalog["maps"]
            if row["meaning_provenance"]
                == "PINNED_STAGE60_PHYSICAL_MAP_HEADER_AND_STOCK_NAME_BYTES"
        ]
        self.assertEqual(len(non_kanto), 425)
        self.assertTrue(all(
            row["namespace"] == "VEGA_STOCK_NAMESPACE"
            and row["actual_name_raw_sha256"]
                == row["expected_name_raw_sha256"]
            and row["stage60_baseline"]["decoded_utf8"]
                == row["actual_name"]
            for row in non_kanto
        ))
        wisdom = [
            row for row in non_kanto
            if row["group"] == 1 and row["map"] in {36, 37, 38, 73}
        ]
        self.assertEqual(len(wisdom), 4)
        self.assertEqual({row["actual_name"] for row in wisdom}, {"ちえのどうくつ"})

    def test_real_stage61_matrix_is_complete_and_bounded(self) -> None:
        document = self.document
        self.assertEqual(document["status"], "PASS")
        self.assertTrue(all(document["assertions"].values()))
        counts = document["counts"]
        self.assertEqual(counts["catalog_object_count"], 3108)
        self.assertEqual(counts["catalog_branch_count"], 4203)
        self.assertGreater(counts["matrix_case_count"], counts["catalog_branch_count"])
        self.assertLessEqual(counts["max_flags_in_case"], MAX_FLAGS_PER_CASE)
        self.assertEqual(counts["semantic_root_count"], 401)
        self.assertLess(
            counts["semantic_selected_state_total"],
            counts["semantic_raw_cartesian_total"],
        )
        self.assertEqual(
            counts["hidden_assertion_count"], 263 + 2 + 33,
        )

    def test_trainer_tower_local_fallback_natural_visibility_is_exact(self) -> None:
        contract = self.document[
            "trainer_tower_local_fallback_lifecycle_contract"
        ]
        self.assertEqual(
            contract["fixture_precondition"],
            TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION,
        )
        self.assertEqual(
            contract["scope_limit"],
            "ARBITRARY_EXTERNAL_EREADER_SAVE_OUT_OF_SCOPE",
        )
        self.assertFalse(contract["ereader_valid_sector_supported"])
        self.assertIsNone(contract["guessed_runtime_control"])
        self.assertEqual(contract["local_blob"]["num_floors"], 4)
        self.assertEqual(contract["local_blob"]["floor_stride"], 0x3D4)
        self.assertEqual(
            contract["local_blob"]["challenge_types"], [0, 1, 2, 0],
        )
        self.assertEqual(contract["counts"]["object_owner_count"], 40)
        self.assertEqual(contract["counts"]["visible_owner_count"], 7)
        self.assertEqual(contract["counts"]["hidden_owner_count"], 33)
        self.assertEqual(
            {row["layout_id"]: (row["width"], row["height"])
             for row in contract["selected_layout_geometry"]},
            {
                298: (18, 17), 301: (18, 17), 306: (18, 16),
                367: (18, 17), 376: (18, 17),
            },
        )
        visible = {
            "OBJECT:002/001:002",
            "OBJECT:002/002:001", "OBJECT:002/002:004",
            "OBJECT:002/003:001", "OBJECT:002/003:002",
            "OBJECT:002/003:003", "OBJECT:002/004:002",
        }
        self.assertEqual(set(contract["visible_owner_ids"]), visible)
        self.assertEqual(
            set(contract["visible_owner_ids"])
            | set(contract["hidden_owner_ids"]),
            {f"OBJECT:002/{floor:03d}:{index:03d}"
             for floor in range(1, 9) for index in range(5)},
        )
        cases = [
            row for row in self.document["cases"]
            if row["owner_key"].startswith("OBJECT:002/")
            and 1 <= int(row["owner_key"][11:14]) <= 8
        ]
        self.assertEqual(len(cases), 40)
        self.assertTrue(all(
            set(row["runtime_map_lifecycle"]) == {
                "kind", "root", "map_script_tag", "layout_id",
                "expected_object", "expected_movement_type",
                "local_fallback_precondition",
            }
            and row["runtime_map_lifecycle"]["kind"]
                == "TRAINER_TOWER_ON_TRANSITION"
            and row["runtime_map_lifecycle"]["root"] == "0x081A96EA"
            and row["runtime_map_lifecycle"]["map_script_tag"] == 2
            and row["runtime_position_variant"] is None
            and row["runtime_position_map_load_required"] is True
            for row in cases
        ))
        catalog = {row["npc_id"]: row for row in self.legacy["npcs"]}
        roof_cases = [
            row for row in cases
            if int(row["owner_key"][11:14]) >= 5
        ]
        self.assertEqual(len(roof_cases), 20)
        self.assertTrue(all(
            row["runtime_map_lifecycle"]["layout_id"] == 306
            and row["runtime_map_lifecycle"]["expected_object"]
                == list(catalog[row["owner_key"]]["interaction_object"])
            and row["runtime_map_lifecycle"]["expected_movement_type"]
                == int(catalog[row["owner_key"]]["movement_type"])
            for row in roof_cases
        ))
        self.assertEqual(
            {row["owner_key"] for row in cases if row["interaction_expected"]},
            visible,
        )
        self.assertTrue(all(
            row["expected_object_visible"]
            and row["choice_candidates"] != []
            for row in cases if row["owner_key"] in visible
        ))
        self.assertTrue(all(
            not row["expected_object_visible"]
            and not row["interaction_expected"]
            and row["choice_candidates"] == []
            and row["expected_terminal"] == "NO_INTERACTION_HIDDEN"
            for row in cases if row["owner_key"] not in visible
        ))
        self.assertEqual(self.document["counts"]["trainer_tower_object_case_count"], 40)
        self.assertEqual(
            self.document["counts"]["trainer_tower_interactive_case_count"], 7,
        )
        self.assertEqual(
            self.document["counts"]["trainer_tower_hidden_assertion_count"], 33,
        )
        self.assertEqual(
            self.document["counts"][
                "trainer_tower_runtime_map_lifecycle_case_count"
            ], 40,
        )
        expected_runtime = {
            "OBJECT:002/001:002": (298, [15, 13], 0x09, [14, 13], ["UP", "DOWN"], "RIGHT"),
            "OBJECT:002/002:001": (367, [10, 12], 0x08, [9, 12], ["LEFT", "RIGHT"], "RIGHT"),
            "OBJECT:002/002:004": (367, [11, 12], 0x08, [12, 12], ["RIGHT", "LEFT"], "LEFT"),
            "OBJECT:002/003:001": (376, [10, 10], 0x08, [11, 10], ["UP", "DOWN"], "LEFT"),
            "OBJECT:002/003:002": (376, [14, 13], 0x09, [13, 13], ["LEFT", "RIGHT"], "RIGHT"),
            "OBJECT:002/003:003": (376, [10, 16], 0x07, [10, 15], ["UP", "DOWN"], "DOWN"),
            "OBJECT:002/004:002": (301, [15, 13], 0x09, [14, 13], ["UP", "DOWN"], "RIGHT"),
        }
        for row in cases:
            if row["owner_key"] not in expected_runtime:
                continue
            layout, obj, movement, stance, walk, action = expected_runtime[
                row["owner_key"]
            ]
            lifecycle = row["runtime_map_lifecycle"]
            self.assertEqual(lifecycle["layout_id"], layout)
            self.assertEqual(lifecycle["expected_object"], obj)
            self.assertEqual(lifecycle["expected_movement_type"], movement)
            self.assertEqual(row["interaction"]["object"], obj)
            self.assertEqual(row["interaction_execution"]["start"], stance)
            self.assertEqual(row["interaction_execution"]["stance"], stance)
            self.assertEqual(row["interaction_execution"]["walk_sequence"], walk)
            self.assertEqual(row["interaction_execution"]["action"], action)
        alternate = contract["double_natural_current_floor_alternate"]
        self.assertEqual(
            alternate["precondition"], {"floors_cleared": 1, "floor_index": 1},
        )
        self.assertTrue(alternate["placement_only_alternate"])
        self.assertFalse(alternate["conversation_or_side_effect_branch"])
        self.assertEqual(
            alternate["owners"]["OBJECT:002/002:004"]["object"], [10, 13],
        )

    def test_trainer_tower_local_fallback_precondition_is_exact_schema(self) -> None:
        exact = deepcopy(TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION)
        self.assertEqual(
            _validate_trainer_tower_fixture_precondition(exact), exact,
        )
        broken_rows = []
        missing = deepcopy(exact)
        missing.pop("sector30_special_sentinel_present")
        broken_rows.append(missing)
        extra = deepcopy(exact)
        extra["external_save_path"] = "forbidden"
        broken_rows.append(extra)
        wrong_source = deepcopy(exact)
        wrong_source["trainer_tower_data_source"] = "EREADER"
        broken_rows.append(wrong_source)
        for key in (
            "sector30_special_sentinel_present",
            "sector31_special_sentinel_present",
            "ereader_fixture_admitted",
        ):
            row = deepcopy(exact)
            row[key] = True
            broken_rows.append(row)
        for row in broken_rows:
            with self.subTest(row=row), self.assertRaises(
                Stage61CatalogStateMatrixError
            ):
                _validate_trainer_tower_fixture_precondition(row)

    def test_trainer_tower_lifecycle_mutations_fail_closed(self) -> None:
        rom_base = 0x08000000

        def mutated_pair(address: int, value: int) -> tuple[bytes, bytes]:
            clean = bytearray(self.clean)
            stage61 = bytearray(self.stage61)
            offset = address - rom_base
            clean[offset] = value
            stage61[offset] = value
            return bytes(clean), bytes(stage61)

        challenge_address = TRAINER_TOWER_LOCAL_BLOB_ADDRESS + 8 + 2
        clean, stage61 = mutated_pair(challenge_address, 3)
        blob_offset = TRAINER_TOWER_LOCAL_BLOB_ADDRESS - rom_base
        blob_sha = hashlib.sha256(
            clean[blob_offset:blob_offset + TRAINER_TOWER_LOCAL_BLOB_SIZE]
        ).hexdigest()
        with patch(
            "tools.stage61_catalog_state_matrix.TRAINER_TOWER_LOCAL_BLOB_SHA256",
            blob_sha,
        ), self.assertRaises(Stage61CatalogStateMatrixError):
            _trainer_tower_local_fallback_lifecycle(
                self.legacy["npcs"], clean, stage61,
            )

        for address in (
            TRAINER_TOWER_LOCAL_BLOB_ADDRESS + 1,
            TRAINER_TOWER_INIT_ADDRESS,
            TRAINER_TOWER_TRANSITION_ADDRESS,
            0x08305E18,
        ):
            clean, stage61 = mutated_pair(
                address, self.clean[address - rom_base] ^ 1,
            )
            with self.subTest(address=hex(address)), self.assertRaises(
                Stage61CatalogStateMatrixError
            ):
                _trainer_tower_local_fallback_lifecycle(
                    self.legacy["npcs"], clean, stage61,
                )

        for field_offset in (0x4C, 0x50):
            address = TRAINER_TOWER_SETUP_ADDRESS + field_offset
            clean, stage61 = mutated_pair(
                address, self.clean[address - rom_base] ^ 1,
            )
            setup_offset = TRAINER_TOWER_SETUP_ADDRESS - rom_base
            setup_sha = hashlib.sha256(
                clean[setup_offset:setup_offset + TRAINER_TOWER_SETUP_SIZE]
            ).hexdigest()
            with self.subTest(field_offset=field_offset), patch(
                "tools.stage61_catalog_state_matrix.TRAINER_TOWER_SETUP_SHA256",
                setup_sha,
            ), self.assertRaises(Stage61CatalogStateMatrixError):
                _trainer_tower_local_fallback_lifecycle(
                    self.legacy["npcs"], clean, stage61,
                )

        with patch(
            "tools.stage61_catalog_state_matrix.TRAINER_TOWER_FLOOR_STRIDE",
            0x3D5,
        ), self.assertRaises(Stage61CatalogStateMatrixError):
            _trainer_tower_local_fallback_lifecycle(
                self.legacy["npcs"], self.clean, self.stage61,
            )
        broken_projection = deepcopy(self.semantic)
        broken_projection["stage61_map_script_projection"]["materialization"][
            "layout_installation"
        ]["table_pointer"] = "0x09443868"
        with self.assertRaises(Stage61CatalogStateMatrixError):
            _trainer_tower_local_fallback_lifecycle(
                self.legacy["npcs"], self.clean, self.stage61,
                semantic_report=broken_projection,
            )
        hide_real_owner = dict(TRAINER_TOWER_VISIBLE_OBJECTS)
        hide_real_owner[1] = frozenset()
        with patch(
            "tools.stage61_catalog_state_matrix.TRAINER_TOWER_VISIBLE_OBJECTS",
            hide_real_owner,
        ), self.assertRaises(Stage61CatalogStateMatrixError):
            _trainer_tower_local_fallback_lifecycle(
                self.legacy["npcs"], self.clean, self.stage61,
            )

    def test_trainer_tower_object_and_visibility_mutations_fail_closed(self) -> None:
        for field, value in (
            ("local_id", 99), ("flag", 99),
            ("movement_type", 99), ("x", 99),
            ("script_pointer", 0x0816E085),
            ("expected_template_raw_hex", "00" * 24),
        ):
            broken = deepcopy(self.legacy)
            npc = next(
                row for row in broken["npcs"]
                if row["npc_id"] == "OBJECT:002/001:001"
            )
            npc[field] = value
            with self.subTest(field=field), self.assertRaises(
                Stage61CatalogStateMatrixError
            ):
                _trainer_tower_local_fallback_lifecycle(
                    broken["npcs"], self.clean, self.stage61,
                )

        visible_1f_d1 = dict(TRAINER_TOWER_VISIBLE_OBJECTS)
        visible_1f_d1[1] = frozenset({1, 2})
        with patch(
            "tools.stage61_catalog_state_matrix.TRAINER_TOWER_VISIBLE_OBJECTS",
            visible_1f_d1,
        ), self.assertRaises(Stage61CatalogStateMatrixError):
            _trainer_tower_local_fallback_lifecycle(
                self.legacy["npcs"], self.clean, self.stage61,
            )

    def test_trainer_tower_runtime_map_lifecycle_schema_mutations_fail_closed(
        self,
    ) -> None:
        case = next(
            row for row in self.document["cases"]
            if row["owner_key"] == "OBJECT:002/002:004"
        )
        lifecycle = case["runtime_map_lifecycle"]
        self.assertEqual(
            _normalized_trainer_tower_runtime_map_lifecycle(
                lifecycle, case["interaction"], "positive",
            ),
            lifecycle,
        )
        broken_rows = []
        missing = deepcopy(lifecycle)
        missing.pop("layout_id")
        broken_rows.append(missing)
        extra = deepcopy(lifecycle)
        extra["control"] = {"kind": "GUESSED"}
        broken_rows.append(extra)
        for key, value in (
            ("root", "0x081A96EB"),
            ("map_script_tag", 3),
            ("layout_id", 368),
            ("expected_object", [10, 13]),
            ("expected_movement_type", True),
        ):
            row = deepcopy(lifecycle)
            row[key] = value
            broken_rows.append(row)
        precondition_extra = deepcopy(lifecycle)
        precondition_extra["local_fallback_precondition"]["control"] = 1
        broken_rows.append(precondition_extra)
        fresh_progress = deepcopy(lifecycle)
        fresh_progress["local_fallback_precondition"]["runtime_state"][
            "floors_cleared"
        ] = 1
        broken_rows.append(fresh_progress)
        ereader = deepcopy(lifecycle)
        ereader["local_fallback_precondition"]["save"][
            "ereader_fixture_admitted"
        ] = True
        broken_rows.append(ereader)
        for row in broken_rows:
            with self.subTest(row=row), self.assertRaises(
                Stage61CatalogStateMatrixError
            ):
                _normalized_trainer_tower_runtime_map_lifecycle(
                    row, case["interaction"], "broken",
                )
    def test_runtime_position_contract_rejects_false_root_preimage_and_runtime_spoof(
        self,
    ) -> None:
        npc = next(
            row for row in self.legacy["npcs"]
            if row["npc_id"] == "OBJECT:002/034:000"
        )
        contract, execution = _runtime_position_state_contract(
            npc, self.stage61,
        )
        self.assertIsNotNone(contract)
        self.assertEqual(contract["root"], "0x0816EB7A")
        prefix_hex = npc["runtime_position_state_contract"][
            "root_prefix_hex"
        ]
        self.assertTrue(prefix_hex.startswith("d0c0"))
        self.assertEqual(
            self.stage61[
                0x0816EB7A - 0x08000000:
                0x0816EB7A - 0x08000000 + len(bytes.fromhex(prefix_hex))
            ].hex(),
            prefix_hex,
        )
        self.assertEqual(
            contract["variants"][0]["object"],
            [int(npc["x"]), int(npc["y"])],
        )
        self.assertEqual(
            contract["variants"][1]["object"], npc["interaction_object"],
        )
        self.assertNotEqual(
            contract["variants"][0]["object"],
            contract["variants"][1]["object"],
        )
        self.assertEqual(execution, contract["variants"][1][
            "interaction_execution"
        ])

        false_prefix = json.loads(json.dumps(npc))
        false_prefix["runtime_position_state_contract"][
            "root_prefix_hex"
        ] = "02"
        with self.assertRaisesRegex(
            Stage61CatalogStateMatrixError, "root preimage",
        ):
            _runtime_position_state_contract(false_prefix, self.stage61)

        missing_runtime = json.loads(json.dumps(npc))
        missing_runtime.pop("interaction_object")
        with self.assertRaisesRegex(
            Stage61CatalogStateMatrixError, "interaction_object",
        ):
            _runtime_position_state_contract(missing_runtime, self.stage61)

        static_spoof = json.loads(json.dumps(npc))
        static_spoof["interaction_object"] = [
            int(npc["x"]), int(npc["y"]),
        ]
        with self.assertRaises(Stage61CatalogStateMatrixError):
            _runtime_position_state_contract(static_spoof, self.stage61)

    def test_all_event_owner_execution_scope_is_not_object_only(self) -> None:
        scope = build_stage61_event_owner_execution_scope(
            self.event_owner_inventory,
        )
        inventory_owner_counts = self.event_owner_inventory[
            "owner_kind_counts"
        ]
        inventory_runtime_counts = self.event_owner_inventory[
            "runtime_owner_kind_counts"
        ]
        expected_trigger_counts = dict(inventory_runtime_counts)
        expected_trigger_counts["COMMON"] -= 1
        self.assertEqual(
            scope["owner_count"], self.event_owner_inventory["owner_count"],
        )
        self.assertEqual(scope["owner_kind_counts"], inventory_owner_counts)
        self.assertEqual(
            scope["script_root_owner_count"],
            sum(inventory_runtime_counts.values()),
        )
        self.assertEqual(
            scope["runtime_script_owner_count"],
            sum(expected_trigger_counts.values()),
        )
        self.assertEqual(
            scope["runtime_script_owner_kind_counts"],
            expected_trigger_counts,
        )
        self.assertEqual(scope["hidden_item_owner_count"], 74)
        self.assertEqual(scope["dormant_common_standard_script_count"], 1)
        self.assertEqual(
            scope["runtime_required_owner_count"],
            sum(expected_trigger_counts.values()) + 74,
        )
        self.assertEqual(scope["structural_nontrigger_owner_count"], 1001)
        self.assertEqual(
            scope["structural_nontrigger_owner_kind_counts"],
            {"BG": 413, "COMMON": 1, "COORD": 583, "OBJECT": 4},
        )
        self.assertEqual(
            scope["dormant_common_standard_scripts"][0]["owner_id"],
            "COMMON:STANDARD:007",
        )
        self.assertEqual(
            sum(scope["map_trigger_subkind_counts"].values()),
            inventory_runtime_counts["MAP"],
        )
        self.assertFalse(
            scope["classification_policy"][
                "static_decode_alone_satisfies_runtime_owner"
            ]
        )
        self.assertTrue(all(scope["assertions"].values()))
        self.assertEqual(
            self.document["event_owner_runtime_scope"]["phase"],
            "RUNTIME_CONTROL_EXPANSION_PENDING",
        )

    def test_all_event_runtime_attach_requires_every_owner_assignment_and_hidden_state(
        self,
    ) -> None:
        owners = self.event_owner_inventory["owners"]
        owners_by_root: dict[int, list[str]] = {}
        for owner in owners:
            if owner.get("runtime_root") is True \
                    and owner["owner_id"] != "COMMON:STANDARD:007":
                owners_by_root.setdefault(int(owner["root"]), []).append(
                    owner["owner_id"]
                )
        roots = []
        assignment_by_root = {}
        owner_by_id = {owner["owner_id"]: owner for owner in owners}
        for ordinal, (root, owner_ids) in enumerate(sorted(owners_by_root.items())):
            assignment_id = f"root-assignment-{ordinal:04d}"
            assignment_by_root[root] = assignment_id
            nonobject_owner_ids = sorted(
                owner_id for owner_id in owner_ids
                if owner_by_id[owner_id]["owner_kind"] \
                    not in {"OBJECT", "MAP"}
            )
            roots.append({
                "owner_keys": sorted(owner_ids),
                "candidate_assignments": [{
                    "assignment_id": assignment_id,
                    "physical_trigger_owner_ids": nonobject_owner_ids,
                    "physical_trigger_binding_status": (
                        "BOUND_TO_NONOBJECT_PHYSICAL_TRIGGER"
                        if nonobject_owner_ids else
                        "NO_NONOBJECT_PHYSICAL_TRIGGER_MATCH"
                    ),
                }],
                "physical_trigger_owner_assignment_ids": {
                    owner_id: [assignment_id]
                    for owner_id in nonobject_owner_ids
                },
                "nonobject_physical_trigger_unbound_assignment_ids": (
                    [] if nonobject_owner_ids else [assignment_id]
                ),
            })

        object_case_ids: dict[str, list[str]] = {}
        for case in self.document["cases"]:
            object_case_ids.setdefault(case["owner_key"], []).append(
                case["case_id"]
            )
        event_cases = []
        event_case_ids: dict[str, list[str]] = {}

        def append_case(owner: dict, case_id: str, assignment_id, variant=None):
            address = int(owner["root"]) if owner.get("runtime_root") else 0x08000000
            sequence_id = f"{case_id}-sequence-0000"
            text_oracle = {
                "visible_text_count": 0,
                "ordered_raw_sha256s": [],
                "allowed_ordered_raw_sha256_sequences": [[]],
            }
            required = _empty_required_postconditions()
            trigger_path = {"kind": owner["owner_kind"]}
            if variant is not None:
                trigger_path = {"kind": "HIDDEN_ITEM", "variant": variant}
            event_cases.append({
                "case_id": case_id, "owner_id": owner["owner_id"],
                "root_assignment_id": assignment_id,
                "trigger_path": trigger_path,
                "input_sequence": {
                    "sequence_id": sequence_id, "tokens": ["A"],
                    "expected_static_branch_token": "SYNTHETIC_EXACT",
                    "basis": "PINNED_TEST_TRIGGER",
                    "visible_text_expected": False,
                    "silent_text_basis": {
                        "kind": "STATIC_NO_TEXT_PATH",
                        "source_instruction_addresses": [f"0x{address:08X}"],
                        "reason": "SYNTHETIC_PINNED_NO_TEXT_PATH",
                    },
                    "text_oracle": text_oracle,
                    "required_postconditions": required,
                    "battle_start_required_postconditions": None,
                    "post_battle_continuation": None,
                },
                "control_requirements": {"external": [], "internal": []},
                "effect_signature_ids": ["effect-no-mutation"],
                "required_postconditions": required,
                "battle_start_required_postconditions": None,
                "text_oracle": text_oracle,
                "terminal_kind": "FIELD_RELEASE",
                "source_provenance": {"kind": "PINNED_TEST_SOURCE"},
            })
            event_case_ids.setdefault(owner["owner_id"], []).append(case_id)

        for owner in owners:
            if owner["owner_kind"] in {"OBJECT", "MAP"}:
                continue
            if owner.get("runtime_root") is True \
                    and owner["owner_id"] != "COMMON:STANDARD:007":
                append_case(
                    owner,
                    f"event-{owner['owner_id']}-assignment",
                    assignment_by_root[int(owner["root"])],
                )
            elif owner.get("non_script_reason") == "HIDDEN_ITEM":
                variants = (
                    (
                        "AVAILABLE_SUCCESS", "AVAILABLE_COIN_FULL",
                        "AVAILABLE_NO_COIN_CASE", "ALREADY_COLLECTED",
                    )
                    if int(owner["raw_root"]) & 0xFFFF == 0 else
                    (
                        "AVAILABLE_SUCCESS", "AVAILABLE_BAG_FULL",
                        "ALREADY_COLLECTED",
                    )
                )
                for variant in variants:
                    append_case(
                        owner,
                        f"event-{owner['owner_id']}-{variant.lower()}",
                        None, variant,
                    )

        map_owners: dict[tuple[int, int], list[dict]] = {}
        for owner in owners:
            if owner["owner_kind"] == "MAP" \
                    and owner.get("runtime_root") is True:
                map_owners.setdefault(
                    (int(owner["group"]), int(owner["map"])), []
                ).append(owner)
        for (group, map_number), map_rows in sorted(map_owners.items()):
            case_id = f"map-lifecycle-{group:03d}-{map_number:03d}-" + "a" * 20
            covered = sorted(row["owner_id"] for row in map_rows)
            sequence_id = f"{case_id}--seq-0000-" + "b" * 16
            event_cases.append({
                "case_id": case_id,
                "case_kind": "MAP_LIFECYCLE_COMPOSITE",
                "map": {"group": group, "map": map_number},
                "covered_owner_ids": covered,
                "dispatched_owner_ids": covered,
                "trigger_path": {},
                "input_sequences": [{"sequence_id": sequence_id}],
                "effect_signature_ids": ["effect-no-mutation"],
                "map_lifecycle": {},
                "source_provenance": {"kind": "PINNED_TEST_SOURCE"},
            })
            for owner_id in covered:
                event_case_ids.setdefault(owner_id, []).append(case_id)

        triggers = []
        abi_source_blobs, _ = _interaction_abi_pinned_inputs()
        dormant_evidence = _dormant_common7_structural_evidence(
            self.clean, self.stage61, owners, abi_source_blobs,
        )
        for owner in owners:
            if owner["owner_id"] == "COMMON:STANDARD:007":
                triggers.append(_owner_trigger_contract(
                    self.stage61, owner, [], abi_source_blobs,
                    dormant_common7_evidence=dormant_evidence,
                ))
                continue
            required = bool(
                owner.get("runtime_root") is True
                and owner["owner_id"] != "COMMON:STANDARD:007"
                or owner.get("non_script_reason") == "HIDDEN_ITEM"
            )
            if owner["owner_kind"] == "OBJECT":
                case_ids = sorted(object_case_ids.get(owner["owner_id"], []))
            else:
                case_ids = sorted(event_case_ids.get(owner["owner_id"], []))
            trigger = {
                "owner_id": owner["owner_id"],
                "owner_kind": owner["owner_kind"],
                "trigger_class": (
                    "RUNTIME_TRIGGER" if required else "STRUCTURAL_NONTRIGGER"
                ),
                "trigger_consumer": "PINNED_ENGINE_CONSUMER",
                "entry_condition": "OWNER_SPECIFIC_EXACT",
                "effect_evidence": "STATIC_NO_MUTATION_TEST",
                "runtime_case_required": required,
                "representative_runtime_root": (
                    owner["root"] if owner.get("runtime_root") else None
                ),
                "runtime_case_ids": case_ids,
            }
            if owner.get("non_script_reason") == "HIDDEN_ITEM":
                trigger["consumer_subkind"] = "BG_HIDDEN_ITEM"
            elif owner["owner_kind"] == "MAP":
                trigger["consumer_subkind"] = f"MAP_{owner['root_subkind']}"
            triggers.append(trigger)
        contract = {
            "roots": roots,
            "effect_signatures": ["effect-no-mutation"],
            "event_runtime_cases": event_cases,
            "event_owner_trigger_contracts": triggers,
        }
        def validate_composite(case, _label, _inventory, _effects):
            return (
                [row["sequence_id"] for row in case["input_sequences"]],
                list(case["covered_owner_ids"]),
                list(case["dispatched_owner_ids"]),
            )

        with patch(
            "tools.stage61_catalog_state_matrix."
            "_validate_map_lifecycle_composite_case",
            side_effect=validate_composite,
        ):
            attached = attach_stage61_event_owner_runtime_scope(
                self.document, self.event_owner_inventory, contract,
            )
        scope = attached["event_owner_runtime_scope"]
        self.assertEqual(scope["phase"], "RUNTIME_CONTROL_EXPANDED")
        self.assertEqual(scope["oracle_phase"], "OBJECT_CASE_ORACLE_BINDING_REQUIRED")
        self.assertEqual(
            scope["runtime_owner_handoff_count"],
            scope["runtime_required_owner_count"],
        )
        self.assertEqual(scope["untested_runtime_owner_handoff_count"], 0)
        self.assertEqual(scope["hidden_item_runtime_state_case_count"], 234)
        self.assertTrue(all(attached["assertions"].values()))

        missing = json.loads(json.dumps(contract))
        missing["event_runtime_cases"] = missing["event_runtime_cases"][1:]
        removed_case = contract["event_runtime_cases"][0]["case_id"]
        for trigger in missing["event_owner_trigger_contracts"]:
            if removed_case in trigger["runtime_case_ids"]:
                trigger["runtime_case_ids"].remove(removed_case)
        with patch(
            "tools.stage61_catalog_state_matrix."
            "_validate_map_lifecycle_composite_case",
            side_effect=validate_composite,
        ), self.assertRaises(Stage61CatalogStateMatrixError):
            attach_stage61_event_owner_runtime_scope(
                self.document, self.event_owner_inventory, missing,
            )

        composite_indices = [
            index for index, row in enumerate(contract["event_runtime_cases"])
            if row.get("case_kind") == "MAP_LIFECYCLE_COMPOSITE"
        ]
        self.assertGreaterEqual(len(composite_indices), 2)
        for label, mutate in (
            ("covered-missing", lambda rows: rows[
                composite_indices[0]
            ]["covered_owner_ids"].pop()),
            ("covered-duplicate", lambda rows: rows[
                composite_indices[1]
            ]["covered_owner_ids"].append(
                rows[composite_indices[0]]["covered_owner_ids"][0]
            )),
        ):
            broken = deepcopy(contract)
            mutate(broken["event_runtime_cases"])
            with self.subTest(label=label), patch(
                "tools.stage61_catalog_state_matrix."
                "_validate_map_lifecycle_composite_case",
                side_effect=validate_composite,
            ), self.assertRaises(Stage61CatalogStateMatrixError):
                attach_stage61_event_owner_runtime_scope(
                    self.document, self.event_owner_inventory, broken,
                )

    def test_object_runtime_case_ids_are_rebound_after_matrix_set_cover(
        self,
    ) -> None:
        owners = self.event_owner_inventory["owners"]
        object_owner = next(
            row for row in owners
            if row["owner_kind"] == "OBJECT" and row["runtime_root"]
        )
        nonobject_owner = next(
            row for row in owners
            if row["owner_kind"] not in {"OBJECT", "MAP"}
            and row["runtime_root"]
        )
        placeholder_object = {
            "case_id": "oracle-pre-matrix-object-placeholder",
            "owner_id": object_owner["owner_id"],
        }
        retained_nonobject = {
            "case_id": "event-nonobject-exact-trigger",
            "owner_id": nonobject_owner["owner_id"],
        }
        map_owners_by_map: dict[tuple[int, int], list[str]] = {}
        for owner_row in owners:
            if owner_row["owner_kind"] == "MAP":
                map_owners_by_map.setdefault((
                    int(owner_row["group"]), int(owner_row["map"]),
                ), []).append(owner_row["owner_id"])
        map_composites = [{
            "case_id": (
                f"map-lifecycle-{group:03d}-{map_id:03d}-fixture"
            ),
            "case_kind": "MAP_LIFECYCLE_COMPOSITE",
            "covered_owner_ids": sorted(owner_ids),
        } for (group, map_id), owner_ids in sorted(
            map_owners_by_map.items()
        )]
        contract = {
            "event_owner_trigger_contracts": [
                {"owner_id": row["owner_id"], "runtime_case_ids": []}
                for row in owners
            ],
            "event_runtime_cases": [
                placeholder_object, retained_nonobject, *map_composites,
            ],
        }
        rebound = bind_stage61_object_runtime_case_ids(
            contract, self.event_owner_inventory, self.document["cases"],
        )
        self.assertEqual(
            rebound["event_runtime_cases"], [
                retained_nonobject, *map_composites,
            ],
        )
        by_owner = {
            row["owner_id"]: row
            for row in rebound["event_owner_trigger_contracts"]
        }
        expected = sorted(
            row["case_id"] for row in self.document["cases"]
            if row["owner_key"] == object_owner["owner_id"]
        )
        self.assertEqual(
            by_owner[object_owner["owner_id"]]["runtime_case_ids"],
            expected,
        )
        binding = rebound["object_matrix_case_binding"]
        self.assertEqual(binding["object_owner_count"], 3108)
        self.assertEqual(
            binding["removed_pre_matrix_object_event_case_count"], 1,
        )
        self.assertTrue(all(binding["assertions"].values()))

    def test_engine_special_flag_is_identity_and_never_persistent_state(
        self,
    ) -> None:
        contract = self.document["engine_special_flag_contract"]
        self.assertEqual(contract["domain"], "ENGINE_SPECIAL_FLAG")
        self.assertEqual(
            contract["storage"], "EWRAM_sSpecialFlags_NONPERSISTENT",
        )
        self.assertEqual(contract["identity_mapping"], {"0x4001": "0x4001"})
        self.assertEqual(contract["persistent_guard_id"], "0x18C4")
        bill = next(
            row for row in contract["roots"]
            if row["source_root"] == "0x08189851"
        )
        self.assertEqual(
            [(row["opcode"], row["value"])
             for row in bill["source_operations"]],
            [(0x29, 0x4001)],
        )
        self.assertEqual(
            [(row["opcode"], row["value"])
             for row in bill["target_operations"]],
            [],
        )
        self.assertEqual(
            bill["relation"],
            "ATOMIC_PRODUCER_SUPPRESSION_FOR_OUT_OF_SCOPE_DESTINATION",
        )
        self.assertTrue(all(contract["assertions"].values()))
        self.assertFalse(any(
            flag["id"] in {0x18C4, 0x4001}
            for case in self.document["cases"]
            for flag in case["state"]["flags"]
        ))
        lifecycle = self.document[
            "engine_special_flag_lifecycle_contract"
        ]
        self.assertEqual(lifecycle["status"], "PASS")
        self.assertEqual(
            [
                (
                    row["operation"], row["instruction_address"],
                    row["owner_ids"],
                )
                for row in lifecycle["final_operations"]
            ],
            [
                (
                    "SET", "0x0816F7D2",
                    ["COORD:003/000:000", "COORD:003/000:001"],
                ),
                (
                    "CLEAR", "0x0817C892",
                    ["MAP:004/003:002:000"],
                ),
            ],
        )
        self.assertEqual(
            lifecycle["retained_complete_lifecycles"][0]["relation"],
            "SET_THEN_DESTINATION_MAP_LOAD_CLEAR",
        )
        self.assertIsNone(lifecycle["producer_runtime_root"])
        self.assertIsNone(lifecycle["consumer_runtime_root"])
        self.assertEqual(
            lifecycle["product_policy"],
            "ATOMIC_PRODUCER_SUPPRESSION_FOR_OUT_OF_SCOPE_DESTINATION",
        )
        self.assertEqual(
            lifecycle["atomic_adapter"]["owner_id"],
            "OBJECT:098/077:006",
        )
        self.assertEqual(
            lifecycle["atomic_adapter"]["opcodes"],
            [0x6A, 0x5A, 0x0F, 0x09, 0x6C, 0x02],
        )
        self.assertTrue(all(lifecycle["assertions"].values()))

        fixture = _engine_special_flag_lifecycle_fixture(
            self.stage60, self.stage61,
            self.event_owner_inventory, self.document,
        )
        self.assertEqual(fixture["status"], "PASS")
        self.assertEqual(fixture["flag_id"], "0x4001")
        self.assertEqual(
            fixture["runtime_storage"],
            {
                "owner_address": "0x02037014", "size": 16,
                "encoding": "PLAIN_BITSET_ID_0x4000_IS_BIT_0",
                "byte_offset": 0, "bit_mask": 2,
                "persistence": "EWRAM_VOLATILE_NOT_SAVEBLOCK",
            },
        )
        self.assertEqual(
            [row["walk_tokens"] for row in fixture["producer"]["variants"]],
            [["DOWN"], ["UP"]],
        )
        self.assertEqual(
            fixture["transition"]["destination_map"], [4, 3],
        )
        self.assertEqual(
            fixture["consumer"]["clear_site"], "0x0817C892",
        )
        owner_literal = fixture["source_contract"][
            "runtime_owner_literal"
        ]
        self.assertEqual(
            (
                owner_literal["function"],
                owner_literal["literal_address"],
                owner_literal["literal_value"],
                owner_literal["literal_raw_hex"],
            ),
            ("GetFlagAddr", "0x0806DE70", "0x02037014", "14700302"),
        )
        self.assertEqual(
            owner_literal["owner"],
            {
                "name": "sSpecialFlags", "address": "0x02037014",
                "size": 16, "id_range": [0x4000, 0x407F],
                "encoding": "PLAIN_BITSET_ID_0x4000_IS_BIT_0",
                "persistence": "EWRAM_VOLATILE_NOT_SAVEBLOCK",
            },
        )
        self.assertEqual(
            owner_literal["bindings"]["stage60_input"]["rom_sha256"],
            hashlib.sha256(self.stage60).hexdigest(),
        )
        self.assertEqual(
            owner_literal["bindings"]["final_rom"]["rom_sha256"],
            hashlib.sha256(self.stage61).hexdigest(),
        )
        self.assertTrue(all(fixture["assertions"].values()))

    def test_builder_rejects_engine_special_flag_owner_literal_mutation(
        self,
    ) -> None:
        contract = _engine_special_flag_owner_literal_contract(
            self.stage60, self.stage61,
        )
        self.assertTrue(all(contract["assertions"].values()))
        offset = 0x0806DE70 - 0x08000000
        for source_is_mutated in (True, False):
            source = bytearray(self.stage60)
            final = bytearray(self.stage61)
            target = source if source_is_mutated else final
            target[offset] ^= 1
            with self.subTest(source_is_mutated=source_is_mutated), \
                    self.assertRaisesRegex(
                        Stage61BuildError,
                        "GetFlagAddr owner literal drift",
                    ):
                _engine_special_flag_owner_literal_contract(
                    bytes(source), bytes(final),
                )

    def test_mgba_gate_hashes_runner_normalized_matrix_not_raw_json(self) -> None:
        raw = (json.dumps(
            self.document, ensure_ascii=False, sort_keys=True, indent=2,
        ) + "\n").encode("utf-8")
        normalized_digest = _normalized_mgba_matrix_sha256(
            self.document,
            rom_sha256=hashlib.sha256(self.stage61).hexdigest(),
        )
        self.assertRegex(normalized_digest, r"^[0-9a-f]{64}$")
        self.assertNotEqual(hashlib.sha256(raw).hexdigest(), normalized_digest)
        root_mutation = json.loads(json.dumps(self.document))
        original_root = int(
            root_mutation["cases"][0]["interaction"]["runtime_root"], 0,
        )
        root_mutation["cases"][0]["interaction"]["runtime_root"] = (
            f"0x{original_root ^ 1:08X}"
        )
        self.assertNotEqual(
            _normalized_mgba_matrix_sha256(
                root_mutation,
                rom_sha256=hashlib.sha256(self.stage61).hexdigest(),
            ),
            normalized_digest,
        )

    def test_every_legacy_branch_has_a_matrix_case(self) -> None:
        expected = {
            (npc["npc_id"], branch)
            for npc in self.legacy["npcs"] for branch in npc["branches"]
        }
        actual = {
            (row["owner_key"], row["catalog_branch"])
            for row in self.document["cases"]
        }
        self.assertEqual(actual, expected)
        case_ids = [row["case_id"] for row in self.document["cases"]]
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_every_object_case_binds_final_catalog_xy_and_runtime_root(
        self,
    ) -> None:
        catalog = {row["npc_id"]: row for row in self.legacy["npcs"]}
        self.assertEqual(len(catalog), len(self.legacy["npcs"]))
        for case in self.document["cases"]:
            npc = catalog[case["owner_key"]]
            position_variant = case["runtime_position_variant"]
            runtime_lifecycle = case.get("runtime_map_lifecycle")
            if runtime_lifecycle is not None:
                expected_object = list(
                    runtime_lifecycle["expected_object"]
                )
            elif position_variant is None:
                expected_object = list(npc["interaction_object"])
            else:
                contract_variants = {
                    row["variant_id"]: row
                    for row in npc["runtime_position_state_contract"][
                        "variants"
                    ]
                }
                expected_object = list(contract_variants[
                    position_variant["variant_id"]
                ]["object"])
            self.assertEqual(case["interaction"], {
                "group": npc["group"], "map": npc["map"],
                "object_index": npc["object_index"],
                "local_id": npc["local_id"],
                "object": expected_object,
                "runtime_root": f"0x{npc['script_pointer']:08X}",
            })
        self.assertIn(
            "runtime_root", self.document["runner_projection"][
                "required_columns"
            ],
        )

    def test_catalog_script_pointer_is_required_and_final_rom_bounded(
        self,
    ) -> None:
        for label, mutate in (
            ("missing", lambda row: row.pop("script_pointer")),
            ("below", lambda row: row.update({"script_pointer": 0x07FFFFFF})),
            ("above", lambda row: row.update({"script_pointer": 0x0A000000})),
        ):
            legacy = json.loads(json.dumps(self.legacy))
            mutate(legacy["npcs"][0])
            with self.subTest(label=label), self.assertRaises(
                Stage61CatalogStateMatrixError,
            ):
                build_stage61_catalog_state_matrix(
                    legacy, self.semantic,
                    json.loads((
                        ROOT / "reports/generated/"
                        "stage61_event_dependency_graph.json"
                    ).read_text(encoding="utf-8")),
                    stage61_rom=self.stage61, clean_rom=self.clean,
                    event_owner_inventory=self.event_owner_inventory,
                )

    def test_all_live_state_rows_are_normalized(self) -> None:
        for row in self.document["cases"]:
            state = row["state"]
            self.assertEqual(set(state), {"flags", "vars", "items", "trainers"})
            flags = state["flags"]
            self.assertLessEqual(len(flags), MAX_FLAGS_PER_CASE)
            self.assertEqual(
                [flag["id"] for flag in flags],
                sorted({flag["id"] for flag in flags}),
            )
            if not row["interaction_expected"]:
                self.assertFalse(row["expected_object_visible"])
                self.assertEqual(row["choice_candidates"], [])
            for variable in state["vars"]:
                if variable["id"] == NATIONAL_DEX_VAR_ID:
                    self.assertEqual(row["owner_key"], "OBJECT:002/034:000")
                    self.assertIsNotNone(row["runtime_position_variant"])
                    self.assertIn(variable["value"], {
                        0, NATIONAL_DEX_ENABLED_VAR_VALUE,
                    })
                else:
                    self.assertGreaterEqual(variable["id"], 0x516D)
                    self.assertLessEqual(variable["id"], 0x517F)

    def test_trainers_cover_undefeated_and_defeated_live_ids(self) -> None:
        trainer_cases = [
            row for row in self.document["cases"]
            if row["owner_role"] == "TRAINER"
        ]
        self.assertEqual(len(trainer_cases), 825 * 2 + 2)
        by_owner: dict[str, list[dict]] = {}
        for row in trainer_cases:
            by_owner.setdefault(row["owner_key"], []).append(row)
        self.assertEqual(len(by_owner), 825)
        npc_by_owner = {
            row["npc_id"]: row for row in self.legacy["npcs"]
            if row["owner_role"] == "TRAINER"
        }
        graph = SemanticScriptGraph(self.stage61)
        graph.walk(
            int(row["script_pointer"]) for row in npc_by_owner.values()
        )
        self.assertEqual(graph.diagnostics, [])
        for owner, rows in by_owner.items():
            self.assertEqual(
                {row["catalog_branch"] for row in rows},
                {"TRAINER_PRE_BATTLE", "TRAINER_POST_BATTLE"},
            )
            self.assertEqual(
                len(rows),
                4 if owner == "OBJECT:001/095:022" else 2,
            )
            if owner == "OBJECT:001/095:022":
                self.assertEqual(
                    {
                        row["runtime_position_variant"]["variant_id"]
                        for row in rows
                    },
                    {"STATIC", "RUNTIME"},
                )
            root = int(npc_by_owner[owner]["script_pointer"])
            expected_ids = {
                int.from_bytes(instruction.raw[2:4], "little")
                for address in graph.distances(root)
                for instruction in graph.nodes[address].instructions
                if instruction.opcode == 0x5C
            }
            self.assertTrue(expected_ids)
            by_branch = {row["catalog_branch"]: row for row in rows}
            for branch, defeated in (
                ("TRAINER_PRE_BATTLE", False),
                ("TRAINER_POST_BATTLE", True),
            ):
                state = by_branch[branch]["state"]["trainers"]
                self.assertEqual({item["id"] for item in state}, expected_ids)
                self.assertEqual(len(state), len(expected_ids))
                self.assertTrue(all(
                    item["defeated"] is defeated
                    and item["reason"]
                        == "LIVE_REACHABLE_TRAINERBATTLE_OPERAND_SET"
                    for item in state
                ))

    def test_item_collected_branch_is_hidden_not_fake_dialogue(self) -> None:
        item_cases = [
            row for row in self.document["cases"]
            if row["catalog_branch"] in {"UNCOLLECTED", "COLLECTED"}
        ]
        self.assertEqual(len(item_cases), 263 * 2)
        collected = [
            row for row in item_cases if row["catalog_branch"] == "COLLECTED"
        ]
        self.assertEqual(len(collected), 263)
        self.assertTrue(all(not row["interaction_expected"] for row in collected))
        self.assertTrue(all(
            any(flag["value"] for flag in row["state"]["flags"])
            for row in collected
        ))
        self.assertTrue(all(
            row["state"]["items"][0]["count"] == 1 for row in collected
        ))

    def test_snorlax_and_fuji_use_consistent_story_item_state(self) -> None:
        route_expected = {
            "OBJECT:096/023:014": 0x149E,
            "OBJECT:096/027:005": 0x149F,
        }
        for owner, hidden_flag in route_expected.items():
            rows = [
                row for row in self.document["cases"]
                if row["owner_key"] == owner
            ]
            self.assertEqual(len(rows), 4)
            by_branch = {row["catalog_branch"]: row for row in rows}
            unavailable = by_branch["FLUTE_UNAVAILABLE"]
            no_branch = by_branch["CHOICE_NO"]
            yes_branch = by_branch["CHOICE_YES_BATTLE"]
            cleared = by_branch["CLEARED_AFTER_SAVE_LOAD"]
            for row, owned in (
                (unavailable, False), (no_branch, True),
                (yes_branch, True), (cleared, True),
            ):
                flags = {flag["id"]: flag["value"] for flag in row["state"]["flags"]}
                self.assertEqual(flags[0x119E], owned)
                self.assertEqual(
                    row["state"]["items"], [{
                        "id": 350, "count": int(owned),
                        "reason": "EVENT_DEPENDENCY_GRAPH_ITEM_CONSISTENCY",
                    }],
                )
            self.assertFalse(no_branch["state"]["flags"][1]["value"])
            self.assertFalse(yes_branch["state"]["flags"][1]["value"])
            self.assertEqual(
                {flag["id"]: flag["value"] for flag in cleared["state"]["flags"]}[hidden_flag],
                True,
            )
            self.assertFalse(cleared["interaction_expected"])

        fuji = [
            row for row in self.document["cases"]
            if row["owner_key"] == "OBJECT:098/030:000"
        ]
        self.assertEqual(len(fuji), 2)
        self.assertEqual(
            {
                row["catalog_branch"]:
                {flag["id"]: flag["value"] for flag in row["state"]["flags"]}[0x119E]
                for row in fuji
            },
            {"TOHOKU_FLUTE_UNAVAILABLE": False, "TOHOKU_FLUTE_OWNED": True},
        )

    def test_fossil_transaction_uses_exact_source_relation_and_combo_paths(
        self,
    ) -> None:
        root = next(
            row for row in self.document["semantic_roots"]
            if row["root"] == "0x08189234"
        )
        relation = root["relation_constraints"]
        self.assertEqual(len(relation), 1)
        evidence = relation[0]
        self.assertEqual(
            {
                row["which_fossil_write_address"]
                for row in evidence["producer_evidence"]
                if row["which_fossil_write_address"] is not None
            },
            {"0x08189456", "0x08189494", "0x081894D2"},
        )
        self.assertIn(
            "0x08188DDE",
            {
                row["revive_state_write_address"]
                for row in evidence["producer_evidence"]
            },
        )
        self.assertTrue(all(
            row["definition_lines"] and len(row["sha256"]) == 64
            for row in evidence["source_files"]
        ))
        self.assertEqual(
            {
                (row["which_fossil"], row["revive_state"])
                for row in evidence["allowed_pairs"]
            },
            {
                (0, 0),
                (1, 0), (2, 0), (3, 0),
                (1, 1), (2, 1), (3, 1),
                (1, 2), (2, 2), (3, 2),
            },
        )
        assignments = root["selected_source_assignments"]
        self.assertTrue(all(
            (row["var:4069"], row["var:406A"])
            in {
                (0, 0),
                (1, 0), (2, 0), (3, 0),
                (1, 1), (2, 1), (3, 1),
                (1, 2), (2, 2), (3, 2),
            }
            for row in assignments
        ))

        # Helix+Amber と Dome+Amber は、三条件以上の合取で初めて出る
        # multichoice option-set である。pairwise atom coverでは落ちるため、
        # ordered path signatureが両方を実際に選んだことを固定する。
        helix_amber = [
            row for row in assignments
            if row["flag:0273"] == 1 and row["flag:02ED"] == 0
            and row["flag:025E"] == 1 and row["flag:02EE"] == 0
        ]
        dome_amber = [
            row for row in assignments
            if row["flag:0272"] == 1 and row["flag:02EC"] == 0
            and row["flag:025E"] == 1 and row["flag:02EE"] == 0
        ]
        self.assertTrue(helix_amber)
        self.assertTrue(dome_amber)
        self.assertEqual(root["simulation_truncated_assignment_count"], 0)
        self.assertTrue(root["assertions"]["all_ordered_path_signatures_covered"])

    def test_celadon_roof_all_three_drink_masks_are_selected(self) -> None:
        root = next(
            row for row in self.document["semantic_roots"]
            if row["root"] == "0x08183F26"
        )
        masks = {
            assignment["item:001A"]
            | (assignment["item:001B"] << 1)
            | (assignment["item:001C"] << 2)
            for assignment in root["selected_source_assignments"]
        }
        self.assertEqual(masks, set(range(8)))
        self.assertEqual(root["simulation_truncated_assignment_count"], 0)
        self.assertTrue(root["assertions"]["all_ordered_path_signatures_covered"])

    def test_runner_projection_keeps_extended_and_hidden_cases(self) -> None:
        rows = runner_state_rows(self.document)
        self.assertEqual(len(rows), self.document["counts"]["matrix_case_count"])
        self.assertEqual(
            {row["case_id"] for row in rows},
            {row["case_id"] for row in self.document["cases"]},
        )
        projection = self.document["runner_projection"]
        self.assertEqual(projection["mode"], "EXTENDED_STATE_TSV_REQUIRED")
        self.assertEqual(projection["required_columns"], [
            "flags", "vars", "items", "trainers",
            "expect_visible", "expect_interaction", "runtime_root",
            "interaction_execution", "runtime_map_lifecycle",
            "runtime_position_control",
            "runtime_position_variant",
            "runtime_position_map_load_required",
        ])
        self.assertTrue(projection["extended_state_case_ids"])
        self.assertTrue(projection["hidden_assertion_case_ids"])
        self.assertEqual(
            len(projection["runtime_position_variant_case_ids"]), 34,
        )
        source_by_id = {
            case["case_id"]: case for case in self.document["cases"]
        }
        for row in rows:
            source = source_by_id[row["case_id"]]
            self.assertEqual(
                row["runtime_root"], source["interaction"]["runtime_root"],
            )
            self.assertEqual(
                row["interaction_execution"],
                source["interaction_execution"],
            )
            self.assertEqual(
                row["runtime_position_variant"],
                source["runtime_position_variant"],
            )
            self.assertEqual(
                row["runtime_position_map_load_required"],
                source["runtime_position_map_load_required"],
            )
            self.assertTrue(all(
                set(item) == {"id", "value"}
                for item in row["state"]["flags"] + row["state"]["vars"]
            ))
            self.assertTrue(all(
                set(item) == {"id", "count"}
                for item in row["state"]["items"]
            ))
            self.assertTrue(all(
                set(item) == {"id", "defeated"}
                for item in row["state"]["trainers"]
            ))


class Stage61RuinSealCatalogSchemaFocusedTests(unittest.TestCase):
    @staticmethod
    def _row(scenario_id: str = "completed") -> dict:
        fixtures: dict[str, dict] = {}
        projected = _materialize_control_requirement(
            (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes(), {
                "kind": RUIN_SEAL_PREFIX_KIND,
                "id": 0,
                "owner": f"RUIN_SEAL_PREFIX:{RUIN_SEAL_OBJECT_ROOT}",
                "candidate_values": sorted(
                    RUIN_SEAL_SCENARIO_IDS[int(RUIN_SEAL_OBJECT_ROOT, 16)]
                ),
                "required_value": scenario_id,
                "relation": RUIN_SEAL_PREFIX_RELATION,
            },
            owner_keys=["OBJECT:031/001:000"], fixtures=fixtures,
        )
        assert projected is not None
        return projected

    def test_strict_schema_accepts_exact_materialized_prefix(self) -> None:
        row = self._row()
        self.assertEqual(_runtime_control_value(row, "ruin"), row["value"])
        self.assertEqual(row["value"]["flag_values"], [
            *({"id": identifier, "value": True}
              for identifier in RUIN_SEAL_FLAGS),
            {"id": RUIN_SEAL_COMPLETION_FLAG, "value": True},
        ])

    def test_forged_completion_with_missing_seal_is_rejected(self) -> None:
        row = self._row()
        row["value"]["all_seals"] = False
        row["value"]["first_missing_index"] = 3
        row["value"]["flag_values"][3]["value"] = False
        with self.assertRaisesRegex(
            Stage61CatalogStateMatrixError,
            "RUIN_SEAL_PREFIX exact value不正",
        ):
            _runtime_control_value(row, "ruin-forged")

    def test_forged_flag_order_and_extra_field_are_rejected(self) -> None:
        row = self._row("missing_03")
        row["value"]["flag_values"] = list(
            reversed(row["value"]["flag_values"])
        )
        with self.assertRaisesRegex(
            Stage61CatalogStateMatrixError,
            "RUIN_SEAL_PREFIX exact value不正",
        ):
            _runtime_control_value(row, "ruin-order")
        row = self._row("missing_03")
        row["value"]["unexpected"] = True
        with self.assertRaisesRegex(
            Stage61CatalogStateMatrixError,
            "RUIN_SEAL_PREFIX exact value不正",
        ):
            _runtime_control_value(row, "ruin-extra")

    def test_forged_root_source_binding_is_rejected(self) -> None:
        rows = [self._row("all_seals_pending") for _ in range(3)]
        rows[0]["value"]["root_source_binding"]["sha256"] = "0" * 64
        rows[1]["relation_evidence"][0]["scenario_count"] = 14
        rows[2]["fixture_keys"] = ["0" * 64]
        for index, row in enumerate(rows):
            with self.subTest(index=index), self.assertRaisesRegex(
                Stage61CatalogStateMatrixError,
                "RUIN_SEAL_PREFIX exact value不正",
            ):
                _runtime_control_value(row, f"ruin-source-forged-{index}")


class Stage61FacilitySessionCatalogSchemaFocusedTests(unittest.TestCase):
    @staticmethod
    def _row(scenario_key: str = "codex/win_reward") -> dict:
        fixtures: dict[str, dict] = {}
        projected = _materialize_control_requirement(
            b"", {
                "kind": FACILITY_SESSION_KIND,
                "id": 1,
                "owner": "FACILITY_SESSION:FACTORY_OR_CODEX",
                "candidate_values": sorted(
                    _facility_scenario_keys(FACILITY_SHARED_ROOT)
                ),
                "required_value": scenario_key,
                "relation": FACILITY_SESSION_RELATION,
            },
            owner_keys=["OBJECT:TEST"], fixtures=fixtures,
        )
        assert projected is not None
        return projected

    def test_strict_schema_accepts_factory_and_codex_exact_values(self) -> None:
        for scenario_key in ("factory/battle_loss", "codex/win_reward"):
            with self.subTest(scenario_key=scenario_key):
                row = self._row(scenario_key)
                self.assertEqual(
                    _runtime_control_value(row, "facility"), row["value"],
                )
                self.assertIsNone(
                    row["value"]["initialization"]["raw_ewram_preimage"]
                )

    def test_forged_trace_count_hash_and_result_are_rejected(self) -> None:
        mutations = (
            lambda value: value.__setitem__(
                "trace_count", value["trace_count"] + 1,
            ),
            lambda value: value.__setitem__("trace_sha256", "0" * 64),
            lambda value: value["trace"][0].__setitem__("result", 0xFFFF),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                row = self._row("factory/prepare_error")
                mutate(row["value"])
                with self.assertRaisesRegex(
                    Stage61CatalogStateMatrixError,
                    "FACILITY_SESSION exact value不正",
                ):
                    _runtime_control_value(row, f"facility-trace-{index}")

    def test_forged_source_ewram_and_extra_schema_are_rejected(self) -> None:
        rows = [self._row() for _ in range(6)]
        rows[0]["value"]["source_binding"]["sources"][0]["sha256"] = \
            "0" * 64
        rows[1]["value"]["source_binding"]["ram_regions"][0]["address"] = \
            "0x02000000"
        rows[2]["value"]["unexpected"] = True
        rows[3]["relation_evidence"][0]["scenario_keys"] = []
        rows[4]["fixture_keys"] = ["0" * 64]
        rows[5]["value"]["source_binding"]["scenario_registry"][
            "sha256"
        ] = "0" * 64
        for index, row in enumerate(rows):
            with self.subTest(index=index), self.assertRaisesRegex(
                Stage61CatalogStateMatrixError,
                "FACILITY_SESSION exact value不正",
            ):
                _runtime_control_value(row, f"facility-source-{index}")

    def test_forged_family_branch_and_raw_preimage_are_rejected(self) -> None:
        rows = [self._row(), self._row(), self._row()]
        rows[0]["value"]["family"] = "factory"
        rows[1]["value"]["reception_branch"] = "FACTORY"
        rows[2]["value"]["initialization"]["raw_ewram_preimage"] = "00"
        for index, row in enumerate(rows):
            with self.subTest(index=index), self.assertRaisesRegex(
                Stage61CatalogStateMatrixError,
                "FACILITY_SESSION exact value不正",
            ):
                _runtime_control_value(row, f"facility-family-{index}")


if __name__ == "__main__":
    unittest.main()
