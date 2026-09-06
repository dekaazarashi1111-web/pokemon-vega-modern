from __future__ import annotations

import ast
import json
import hashlib
import inspect
import unittest
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.stage61_catalog_state_matrix import (
    TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION,
)
from tools.stage61_facility_sessions import (
    SCENARIO_REGISTRIES as FACILITY_SCENARIO_REGISTRIES,
    SOURCE_BINDINGS as FACILITY_SOURCE_BINDINGS,
    resume_trace as facility_resume_trace,
)
from tools.stage61_interaction_oracle import (
    BAG_FULL_TEXT_POINTER,
    BAG_FULL_TEXT_SHA256,
    CENTER_LINK_GROUP_CAPACITIES,
    CENTER_LINK_SESSION_KIND,
    CENTER_LINK_SESSION_RELATION,
    CENTER_LINK_SESSION_SCENARIOS,
    DEFAULT_FIXTURE,
    DAYCARE_SCENARIO_IDS,
    DAYCARE_SPECIAL_IDS,
    DAYCARE_ORDERED_CAPTURE_RELATION,
    DAYCARE_ORDERED_CAPTURE_SITES,
    DAYCARE_TRANSACTION_KIND,
    DAYCARE_TRANSACTION_RELATION,
    ROUTE5_DAYCARE_SCENARIO_IDS,
    ROUTE5_DAYCARE_SOURCE_ROOT,
    ROUTE5_DAYCARE_SPECIAL_IDS,
    ROUTE5_DAYCARE_TRANSACTION_RELATION,
    FOSSIL_REVIVAL_KIND,
    FOSSIL_REVIVAL_RELATION,
    FOSSIL_REVIVAL_ROOT,
    FOSSIL_SCENARIO_IDS,
    FACILITY_MIRAGE_ROOT,
    FACILITY_SESSION_KIND,
    FACILITY_SESSION_REGISTRY_SOURCE_PATH,
    FACILITY_SESSION_REGISTRY_SOURCE_SHA256,
    FACILITY_SESSION_RELATION,
    FACILITY_SHARED_ROOT,
    FACILITY_FACTORY_LOSS_PREPARE_ORDERED_CAPTURE_RELATION,
    FACILITY_FACTORY_PREPARE_ADAPTER_SYMBOL,
    FACILITY_FACTORY_PREPARE_RESULT_CONSUMER,
    FACILITY_FACTORY_PREPARE_WRITER_SITE,
    GIFT_STORAGE_EXECUTOR_SCENARIO_IDS,
    GIFT_STORAGE_ROOTS,
    GIFT_STORAGE_RUNNER_SCENARIO_IDS,
    GIFT_STORAGE_TRANSACTION_KIND,
    GIFT_STORAGE_TRANSACTION_RELATION,
    MAX_EXECUTION_PATHS,
    PARTY_MOVE_DELETER_SCENARIO_IDS,
    PARTY_MOVE_MODEL_SOURCE_SHA256,
    PARTY_MOVE_RELEARNER_SCENARIO_IDS,
    PARTY_MOVE_ROOTS,
    PARTY_MOVE_SCENARIO_IDS,
    PARTY_MOVE_SPECIAL_IDS,
    PARTY_MOVE_TRANSACTION_KIND,
    PARTY_MOVE_TRANSACTION_RELATION,
    QUEST_LOG_STATE_OWNER,
    QUEST_LOG_STATE_VALUES,
    RUIN_SEAL_COMPLETION_FLAG,
    RUIN_SEAL_COORD_ROOT,
    RUIN_SEAL_FLAGS,
    RUIN_SEAL_OBJECT_ROOT,
    RUIN_SEAL_PREFIX_KIND,
    RUIN_SEAL_PREFIX_RELATION,
    RUIN_SEAL_SCENARIO_IDS,
    STAGE60_SOURCE_SHA256,
    TRAINER_TOWER_DYNAMIC_TEXT_PROVENANCE,
    TRAINER_TOWER_GSTRING_VAR4,
    Stage61InteractionOracleError,
    audit_all_cases,
    audit_all_event_owner_integrity,
    audit_generated_decision_coverage,
    audit_interaction_abi_registry,
    audit_pinned_stage60_project_negative_integrity,
    audit_repaired_stage61_runtime_integrity,
    audit_runtime_graph_integrity,
    bag_full_repair_tail_oracle,
    build_all_case_oracles,
    build_case_oracle,
    build_effect_case_initialization_binding,
    build_effect_source_registry,
    build_hidden_item_script_consumers,
    build_pinned_interaction_abi_manifest,
    build_project_source_manifest_skeleton,
    build_runtime_control_expansion_contract,
    effect_source_event_case_contracts,
    expand_placeholders,
    map_effect_sequence_case_contracts,
    map_lifecycle_expected_ordered_projection,
    object_effect_sequence_case_contracts,
    rebind_effect_signature_references,
    runner_control_abi_contract,
    runner_fixture_key,
    shop_input_sequences,
    validate_engine_special_flag_owner_literal,
    validate_effect_instance,
    validate_effect_registries,
    validate_effect_template,
    validate_instantiated_effect_contract,
)
from tools.stage61_interaction_oracle import (
    _Context,
    _Execution,
    _RepeatingMenuCheckpoint,
    _append_abi_printers,
    _append_message,
    _assert_repeating_menu_body_is_nonstate,
    _build_event_design_rank_model,
    _bind_ordered_result_capture_occurrences,
    _coins_add_transition,
    _center_link_session_input_control,
    _cyclic_menu_site_binding,
    _cyclic_quotient_real_exit_execution_valid,
    _cyclic_event_menu_quotient_identity_sets,
    _decode_hidden_item_owners,
    _daycare_install_scenario,
    _daycare_scenario_payload,
    _dormant_common7_structural_evidence,
    _effect_contract,
    _effect_group_key,
    _effect_abi_entry_watch,
    _effect_flash_consumer_cfg_evidence,
    _effect_flash_direct_inbound_edges,
    _effect_flash_slot_destination_writers,
    _effect_flash_target_cfg_evidence,
    _effect_raw_watch,
    _event_design_physical_controls,
    _execute_from_states,
    _execute_map_lifecycle,
    _execute,
    _execute_pinned_should_try_rematch_battle,
    _fossil_revival_scenario_payload,
    _facility_scenario_keys,
    _facility_scenario_payload,
    _facility_factory_yes_no_choice_contract,
    _facility_round4_yes_no_choice_contract,
    _facility_shared_reception_yes_no_choice_contract,
    FACILITY_ACTIVE_CONTINUATION_TERMINAL,
    _FACILITY_NON_NATIVE_TRACE_OPERATIONS,
    _finalize_facility_session_terminal,
    _flag_get,
    _fork_facility_session_native,
    _fork_pinned_rfu_role_result,
    _gift_storage_create_mon,
    _gift_storage_dedicated_sweep_manifest,
    _gift_storage_scenario_payload,
    _gift_storage_validate_create_mon_rom,
    _validate_gift_storage_model_sources,
    _execution_for_sibling_root,
    _fork_abi_command,
    _independent_runtime_text_assets,
    _interaction_abi_index,
    _map_lifecycle_coverage_findings,
    _map_lifecycle_player_position_fixture,
    _scope_map_lifecycle_player_position_controls,
    _validate_effect_composite_contract,
    _validate_effect_task_contract,
    _execute_trainerbattle,
    _joint_compare_assignments,
    _materialize_control_requirement,
    _move_name,
    _multichoice_rows,
    _party_move_checksum_valid,
    _party_move_delete_selected,
    _party_move_install_scenario,
    _party_move_input_control,
    _party_move_record_fields,
    _party_move_scenario_payload,
    _party_move_teach_selected,
    _NATIVE_GLOBAL_RESULT_WRITER_SPECS,
    _native_global_result_writer_evidence,
    _native_semantic_contract,
    _post_battle_continuation_contract,
    _pokedex_physical_scenarios,
    _POKEDEX_RATING_POINTERS,
    _printer_engine_binding,
    _record_completed_abi_dispatch,
    _record_effect,
    _reaching_bag_capacity_result,
    _reaching_bag_item_count_result,
    _runtime_context,
    _runtime_case_cardinality_findings,
    _runtime_common_caller_execution_binding,
    _runtime_control_rows,
    _runtime_effect_trace,
    _runtime_execution_representatives,
    _runtime_execute_with_seed_discovery,
    _runtime_graph_script_bytes,
    _runtime_catalog_map_key_index,
    _runtime_owner_npc,
    _runtime_path_matches_physical_trigger,
    _runtime_physical_trigger_var_domains,
    _runtime_physical_trigger_var_seeds,
    _runtime_root_plan,
    _ruin_seal_scenario_payload,
    _runner_allowed_post_effect_union,
    _runner_battle_start_required_postconditions,
    _runner_required_postconditions,
    _runner_sequence_lifecycle_projection,
    _runtime_trigger_var_requirements,
    _seagallop_destination_result,
    _set_flag,
    _set_var,
    _species_name,
    _special_global_result_writer_evidence,
    _static_control_domains,
    _static_result_writer_descriptor,
    _special_semantic_contract,
    _trainer_tower_easy_chat_word,
    _trainer_tower_floor_index,
    _trainer_tower_local_floor_source,
    _validate_effect_flash_consumer,
    _validate_effect_exact_final_after,
    _validate_effect_raw_watch_rom_binding,
    _validate_event_design_rank_abi_entry,
    _validate_printer_report_engine_contract,
    _validate_runner_flat_internal_controls,
    _validated_printer_source_contract,
    _validated_runtime_trigger_path,
    PrinterOracle,
    TEXT_PRINTER_ENGINE_FAMILIES,
    PC_ITEMS_SAVEBLOCK1_OFFSET,
    PC_ITEM_SLOT_COUNT,
    PC_ITEM_SLOT_SIZE,
)


ROOT = Path(__file__).resolve().parents[1]


def _synthetic_printer_engine_binding(
    _rom: bytes, family: str, *,
    source_instruction_address: int,
    source_caller_instruction_address: int | None,
) -> dict:
    """Test-only binding for tiny ROMs with no production printer engine."""

    return {
        "schema_version": 1,
        "kind": "SYNTHETIC_TEST_PRINTER_BINDING",
        "family": family,
        "source_instruction_address":
            f"0x{source_instruction_address:08X}",
        "source_caller_instruction_address": None
        if source_caller_instruction_address is None else
        f"0x{source_caller_instruction_address:08X}",
    }


def _effect_test_stable(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _seal_effect_template(value: dict) -> dict:
    result = deepcopy(value)
    core = deepcopy(result)
    core.pop("template_id", None)
    core.pop("template_sha256", None)
    result["template_id"] = "effect-template-" + hashlib.sha256(
        _effect_test_stable(core)
    ).hexdigest()
    unsigned = deepcopy(result)
    unsigned.pop("template_sha256", None)
    result["template_sha256"] = hashlib.sha256(
        _effect_test_stable(unsigned)
    ).hexdigest()
    return result


def _seal_effect_instance(value: dict) -> dict:
    result = deepcopy(value)
    core = deepcopy(result)
    core.pop("instance_id", None)
    core.pop("instance_sha256", None)
    result["instance_id"] = "effect-instance-" + hashlib.sha256(
        _effect_test_stable(core)
    ).hexdigest()
    unsigned = deepcopy(result)
    unsigned.pop("instance_sha256", None)
    result["instance_sha256"] = hashlib.sha256(
        _effect_test_stable(unsigned)
    ).hexdigest()
    return result


def _thumb_bl(source: int, target: int) -> bytes:
    delta = target - (source + 4)
    if delta & 1 or not -(1 << 22) <= delta < (1 << 22):
        raise AssertionError("synthetic Thumb BL range")
    encoded = delta & ((1 << 23) - 1)
    first = 0xF000 | ((encoded >> 12) & 0x7FF)
    second = 0xF800 | ((encoded >> 1) & 0x7FF)
    return first.to_bytes(2, "little") + second.to_bytes(2, "little")


def _seal_flash_consumer(value: dict) -> dict:
    result = deepcopy(value)
    unsigned = deepcopy(result)
    unsigned.pop("consumer_id", None)
    result["consumer_id"] = "flash-consumer-" + hashlib.sha256(
        _effect_test_stable(unsigned)
    ).hexdigest()
    return result


class Stage61EffectTraceIdentityTests(unittest.TestCase):
    @staticmethod
    def _flash_consumer_fixture() -> tuple[bytes, bytes, dict]:
        rom = bytearray(0x200)
        owner = 0x08000100
        pointer_slot = 0x03007474
        rom[0x80:0x84] = _thumb_bl(0x08000080, owner)
        rom[0x100:0x102] = bytes.fromhex("00b5")  # push {lr}
        rom[0x102:0x104] = bytes.fromhex("0748")  # ldr r0, =slot
        rom[0x104:0x106] = bytes.fromhex("0168")  # ldr r1, [r0]
        rom[0x106:0x108] = bytes.fromhex("0b46")  # mov r3, r1
        rom[0x108:0x10A] = bytes.fromhex("c046")  # nop
        rom[0x10A:0x10E] = _thumb_bl(0x0800010A, 0x08000130)
        rom[0x10E:0x110] = bytes.fromhex("7047")  # bx lr
        rom[0x120:0x124] = pointer_slot.to_bytes(4, "little")
        rom[0x130:0x132] = bytes.fromhex("1847")  # bx r3
        clean = bytes(rom)
        target_step = {
            "pc": "0x08000106", "raw_hex": "0b46", "kind": "MOV",
            "source_register": "R1", "destination_register": "R3",
            "stack_offset": None,
        }
        consumer = {
            "consumer_id": "", "classification": "LIVE_LITERAL",
            "owner_function_entry": "0x08000100",
            "owner_code_span": {
                "start": "0x08000100", "length": 0x24,
                "sha256": hashlib.sha256(bytes(rom[0x100:0x124])).hexdigest(),
            },
            "literal_word_address": "0x08000120",
            "address_load_pc": "0x08000102",
            "address_transfer_steps": [],
            "pointee_load_pc": "0x08000104", "target_register": "R1",
            "target_transfer_steps": [target_step],
            "veneer_bl_pc": "0x0800010A",
            "veneer_entry_pc": "0x08000130", "veneer_raw_hex": "1847",
            "inbound_roots": ["0x08000080"],
            "external_inbound_edges": [], "cfg_closure": {},
        }
        cfg, address_steps, target_steps, _ = \
            _effect_flash_consumer_cfg_evidence(
                bytes(rom), consumer, owner_start=owner,
                owner_end=owner + 0x24, label="synthetic consumer",
            )
        if address_steps != [] or target_steps != [target_step]:
            raise AssertionError("synthetic transfer derivation drift")
        consumer["cfg_closure"] = cfg
        inbound = _effect_flash_direct_inbound_edges(
            bytes(rom), clean,
            target_addresses=set(range(owner, owner + 0x24, 2)),
            source_owned_pcs={int(pc, 16) for pc in cfg["path_pcs"]},
        )
        consumer["external_inbound_edges"] = [{
            **row, "target_relation": "ENTRY" if target == owner
            else "INTERIOR",
        } for target in sorted(inbound)
          for row in inbound[target]
          if not owner <= int(row["source_pc"], 16) < owner + 0x24]
        consumer["external_inbound_edges"].sort(
            key=lambda row: (row["target_pc"], row["source_pc"], row["kind"]),
        )
        return bytes(rom), clean, _seal_flash_consumer(consumer)

    @staticmethod
    def _declarative_template_fixture() -> tuple[bytes, dict, dict, str]:
        rom = bytearray(0x200)
        rom[0x100:0x102] = b"\x00\x47"
        code_sha = hashlib.sha256(b"\x00\x47").hexdigest()
        abi_key = "NATIVE:0x08000101"
        source_sha = "d" * 64
        abi_index = {
            abi_key: {
                "target_pointer": "0x08000100",
                "source": {"sha256": source_sha},
                "rom_binding": {
                    "address": "0x08000100", "byte_length": 2,
                    "sha256": code_sha,
                },
            },
        }
        watch_id = _effect_raw_watch({
            "address_resolver": {
                "kind": "ABSOLUTE", "space": "EWRAM",
                "address": "0x02000000",
            },
            "length": 1, "hook_pc": None, "arg_capture": [],
            "completion_boundary": "SYNC_RETURN",
        })["watch_id"]
        template = _seal_effect_template({
            "schema_version": 1,
            "kind": "STAGE61_ABI_EFFECT_TEMPLATE_V1",
            "abi_binding": {
                "abi_key": abi_key, "dispatch_kind": "NATIVE",
                # callnative is script opcode 0x23.  Opcode 0x28 is the
                # waitstate bytecode and must never identify a NATIVE dispatch.
                "opcode": "0x23", "entry_pc": "0x08000100",
                "code_span": {
                    "start": "0x08000100", "length": 2,
                    "sha256": code_sha,
                },
                "source_provenance_sha256": source_sha,
            },
            "input_schema": [{
                "input_id": "choice", "value_type": "U8",
                "capture_phase": "BEFORE_TRIGGER",
                "source": {
                    "kind": "FIXTURE_LITERAL", "fixture_key": "choice",
                    "case_value_pointer": "/effect_inputs/choice",
                },
                "admissible": {"kind": "U_INTERVAL", "minimum": 0,
                               "maximum": 1},
            }],
            "snapshot_schema": [{
                "range_id": watch_id, "pre_required": True,
                "post_required": True,
            }],
            "selector": {
                "kind": "TOTAL_INPUT_PARTITION", "dimension_ids": ["choice"],
                "rows": [{
                    "selector_id": "selector-0", "predicates": [{
                        "input_id": "choice", "op": "EQ", "value": 0,
                    }],
                }, {
                    "selector_id": "selector-1", "predicates": [{
                        "input_id": "choice", "op": "EQ", "value": 1,
                    }],
                }],
                "default": "REJECT",
            },
            "transition_oracle": {
                "kind": "DECLARATIVE_V1",
                "effect_identity": {
                    "domain": "flags", "owner": "TEST_FLAG_BANK",
                    "relation": "EXACT_DECLARATIVE_TRANSITION",
                    "proof_mode": "STATE_RANGE_EXACT",
                },
                "ranges": [{
                    "watch_id": watch_id, "space": "EWRAM",
                    "resolver": "ABSOLUTE", "address": "0x02000000",
                    "length": 1, "source_owner": "TEST_FLAG_BANK",
                    "source_ref": "test/source.c", "canonicalization": "NONE",
                }],
                "rules": [{
                    "selector_id": "selector-0",
                    "expected_result": {
                        "capture": {"kind": "NONE"}, "value": None,
                    },
                    "operations": [{
                        "kind": "COPY_UNCHANGED", "range_id": watch_id,
                    }],
                }, {
                    "selector_id": "selector-1",
                    "expected_result": {
                        "capture": {"kind": "NONE"}, "value": None,
                    },
                    "operations": [{
                        "kind": "WRITE_LITERAL", "range_id": watch_id,
                        "offset": 0, "literal_hex": "01",
                    }],
                }],
            },
            "completion_boundary": "SYNC_RETURN",
        })
        return bytes(rom), abi_index, template, watch_id

    def test_effect_template_and_instance_are_independently_recomputed(self) -> None:
        rom, abi_index, template, watch_id = self._declarative_template_fixture()
        case_contract = {
            "case_id": "case-1", "control_requirements": {},
            "input_sequences": [], "effect_inputs": {"choice": 1},
            "effect_preimages": {watch_id: "00"},
        }
        fixture_binding = build_effect_case_initialization_binding(
            case_contract, {},
        )
        self.assertEqual(
            validate_effect_template(
                template, stage61_rom=rom, abi_index=abi_index,
            ),
            template,
        )
        final = b"\x01"
        expected_contract = {
            "domain": "flags", "owner": "TEST_FLAG_BANK",
            "relation": "EXACT_DECLARATIVE_TRANSITION",
            "proof_mode": "STATE_RANGE_EXACT",
            "observer_contract": {
                "completion_boundary": "SYNC_RETURN",
                "expected_result": {
                    "capture": {"kind": "NONE"}, "value": None,
                },
                "ranges": deepcopy(template["transition_oracle"]["ranges"]),
                "transitions": [{
                    "watch_id": watch_id, "kind": "EXACT_FINAL",
                    "expected_size": 1,
                    "expected_sha256": hashlib.sha256(final).hexdigest(),
                    "expected_hex": final.hex(),
                }],
            },
        }
        instance = _seal_effect_instance({
            "schema_version": 1, "kind": "STAGE61_EFFECT_INSTANCE_V1",
            "template_id": template["template_id"], "case_id": "case-1",
            "occurrence_kind": "EFFECT_MEMBER",
            "signature_id": "effect-test-signature",
            "group_member_ordinal": 0,
            "group_key": "effect-group-" + "a" * 64,
            "fixture_binding": fixture_binding,
            "input_values": {"choice": 1},
            "pre_images": [{
                "range_id": watch_id, "size": 1, "hex": "00",
                "sha256": hashlib.sha256(b"\x00").hexdigest(),
                "source_binding": {
                    "kind": "CASE_JSON_POINTER",
                    "json_pointer": f"/effect_preimages/{watch_id}",
                    "encoding": "LOWER_HEX", "byte_offset": 0,
                },
            }],
            "selected_selector_id": "selector-1",
            "expected_contract": expected_contract,
        })
        self.assertEqual(
            validate_effect_instance(
                instance, template=template, case_contract=case_contract,
                runner_fixtures={},
            ),
            instance,
        )

        # Even after resealing both content IDs, an emulator-derived alternate
        # final byte cannot replace the template/preimage-derived expectation.
        forged = deepcopy(instance)
        forged_transition = forged["expected_contract"]["observer_contract"][
            "transitions"
        ][0]
        forged_transition["expected_hex"] = "02"
        forged_transition["expected_sha256"] = hashlib.sha256(b"\x02").hexdigest()
        forged = _seal_effect_instance(forged)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "independent oracle",
        ):
            validate_effect_instance(
                forged, template=template, case_contract=case_contract,
                runner_fixtures={},
            )

    def test_effect_registry_closes_cases_occurrences_and_no_dispatch(self) -> None:
        rom, _, template, watch_id = self._declarative_template_fixture()
        abi_key = template["abi_binding"]["abi_key"]
        runtime_root = 0x08000020
        effect = {
            "domain": "flags", "owner": "TEST_FLAG_BANK",
            "relation": "EXACT_DECLARATIVE_TRANSITION",
            "instruction_address": "0x08000040",
            "execution_trace_index": 0, "opcode": "0x23",
            "abi_key": abi_key, "group_member_ordinal": 0,
            "group_key": "", "template_id": template["template_id"],
        }
        effect["group_key"] = _effect_group_key(runtime_root, effect)
        dispatch = {
            "execution_trace_index": 0,
            "instruction_address": "0x08000040", "opcode": "0x23",
            "abi_key": abi_key, "dispatch_kind": "NATIVE",
            "entry_pc": "0x08000100",
            "result_capture": {"kind": "NONE", "value": None},
            "effect_member_count": 1, "group_key": effect["group_key"],
        }
        signature = {
            "runtime_root": f"0x{runtime_root:08X}",
            "ordered_abi_dispatches": [dispatch],
            "ordered_effects": [effect], "terminal_kind": "END",
        }
        signature["signature_id"] = "effect-" + hashlib.sha256(
            _effect_test_stable(signature)
        ).hexdigest()[:24]
        empty_signature = {
            "runtime_root": "0x08000060", "ordered_abi_dispatches": [],
            "ordered_effects": [], "terminal_kind": "END",
        }
        empty_signature["signature_id"] = "effect-" + hashlib.sha256(
            _effect_test_stable(empty_signature)
        ).hexdigest()[:24]

        active_case = {
            "case_id": "case-active", "control_requirements": {},
            "input_sequence": [],
            "effect_signature_ids": [signature["signature_id"]],
            "effect_inputs": {"choice": 1},
            "effect_preimages": {watch_id: "00"},
        }
        no_dispatch_case = {
            "case_id": "case-no-dispatch", "control_requirements": {},
            "input_sequence": [],
            "effect_signature_ids": [empty_signature["signature_id"]],
        }
        fixture_binding = build_effect_case_initialization_binding(
            active_case, {},
        )
        final = b"\x01"
        instance = _seal_effect_instance({
            "schema_version": 1, "kind": "STAGE61_EFFECT_INSTANCE_V1",
            "template_id": template["template_id"],
            "case_id": active_case["case_id"],
            "occurrence_kind": "EFFECT_MEMBER",
            "signature_id": signature["signature_id"],
            "group_member_ordinal": 0, "group_key": effect["group_key"],
            "fixture_binding": fixture_binding,
            "input_values": {"choice": 1},
            "pre_images": [{
                "range_id": watch_id, "size": 1, "hex": "00",
                "sha256": hashlib.sha256(b"\x00").hexdigest(),
                "source_binding": {
                    "kind": "CASE_JSON_POINTER",
                    "json_pointer": f"/effect_preimages/{watch_id}",
                    "encoding": "LOWER_HEX", "byte_offset": 0,
                },
            }],
            "selected_selector_id": "selector-1",
            "expected_contract": {
                "domain": "flags", "owner": "TEST_FLAG_BANK",
                "relation": "EXACT_DECLARATIVE_TRANSITION",
                "proof_mode": "STATE_RANGE_EXACT",
                "observer_contract": {
                    "completion_boundary": "SYNC_RETURN",
                    "expected_result": {
                        "capture": {"kind": "NONE"}, "value": None,
                    },
                    "ranges": deepcopy(
                        template["transition_oracle"]["ranges"]
                    ),
                    "transitions": [{
                        "watch_id": watch_id, "kind": "EXACT_FINAL",
                        "expected_size": 1,
                        "expected_sha256": hashlib.sha256(final).hexdigest(),
                        "expected_hex": final.hex(),
                    }],
                },
            },
        })
        binding = {
            "occurrence_kind": "EFFECT_MEMBER",
            "case_id": active_case["case_id"],
            "signature_id": signature["signature_id"],
            "group_key": effect["group_key"], "group_member_ordinal": 0,
            "template_id": template["template_id"],
            "instance_id": instance["instance_id"],
        }
        code_sha = template["abi_binding"]["code_span"]["sha256"]
        manifest = {
            "special_abis": [],
            "native_abis": [{
                "abi_key": abi_key, "symbol": "TestNative",
                "source": {
                    "definition_line": 1, "path": "test/source.c",
                    "sha256": "d" * 64,
                },
                "rom_binding": {
                    "address": "0x08000100", "byte_length": 2,
                    "sha256": code_sha,
                },
                "execution": "SYNC", "input_controls": [],
                "result_contract": {
                    "global_var_result_write": None,
                    "specialvar_return": None,
                },
                "effects": [{
                    "domain": "flags", "owner": "TEST_FLAG_BANK",
                    "relation": "EXACT_DECLARATIVE_TRANSITION",
                }],
                "visible_printers": [], "interaction_sequences": [],
                "complete": True, "target_pointer": "0x08000101",
            }],
        }
        result = validate_effect_registries(
            rom, manifest, {}, [template], [instance],
            effect_signatures=sorted(
                [signature, empty_signature], key=lambda row: row["signature_id"],
            ),
            effect_case_bindings=[binding],
            case_contracts={
                active_case["case_id"]: active_case,
                no_dispatch_case["case_id"]: no_dispatch_case,
            },
            runner_fixtures={},
        )
        self.assertEqual(result["counts"]["dispatched_case_count"], 1)
        self.assertEqual(result["counts"]["no_dispatch_case_count"], 1)
        self.assertEqual(result["counts"]["occurrence_count"], 1)
        self.assertEqual(
            result["no_dispatch_contracts"][0]["case_id"],
            no_dispatch_case["case_id"],
        )
        self.assertTrue(
            result["no_dispatch_contracts"][0]
            ["expected_observation"]["all_owner_ranges_unchanged"]
        )

        hidden = deepcopy(active_case)
        hidden.update({
            "case_id": "case-hidden", "interaction_expected": False,
            "runtime_control_assignment": {
                "effect_signature_ids": [signature["signature_id"]],
            },
        })
        hidden.pop("effect_signature_ids")
        hidden_result = validate_effect_registries(
            rom, manifest, {}, [template], [instance],
            effect_signatures=sorted(
                [signature, empty_signature], key=lambda row: row["signature_id"],
            ), effect_case_bindings=[binding],
            case_contracts={
                active_case["case_id"]: active_case,
                no_dispatch_case["case_id"]: no_dispatch_case,
                hidden["case_id"]: hidden,
            }, runner_fixtures={},
        )
        self.assertEqual(hidden_result["counts"]["no_dispatch_case_count"], 2)

    def test_map_composite_effect_registry_binds_each_sequence_exactly(
        self,
    ) -> None:
        rom, _, template, watch_id = self._declarative_template_fixture()
        abi_key = template["abi_binding"]["abi_key"]
        runtime_root = 0x08000020
        effect = {
            "domain": "flags", "owner": "TEST_FLAG_BANK",
            "relation": "EXACT_DECLARATIVE_TRANSITION",
            "instruction_address": "0x08000040",
            "execution_trace_index": 0, "opcode": "0x23",
            "abi_key": abi_key, "group_member_ordinal": 0,
            "group_key": "", "template_id": template["template_id"],
        }
        effect["group_key"] = _effect_group_key(runtime_root, effect)
        dispatch = {
            "execution_trace_index": 0,
            "instruction_address": "0x08000040", "opcode": "0x23",
            "abi_key": abi_key, "dispatch_kind": "NATIVE",
            "entry_pc": "0x08000100",
            "result_capture": {"kind": "NONE", "value": None},
            "effect_member_count": 1, "group_key": effect["group_key"],
        }
        signature = {
            "runtime_root": f"0x{runtime_root:08X}",
            "ordered_abi_dispatches": [dispatch],
            "ordered_effects": [effect], "terminal_kind": "END",
        }
        signature["signature_id"] = "effect-" + hashlib.sha256(
            _effect_test_stable(signature)
        ).hexdigest()[:24]
        empty_signature = {
            "runtime_root": "0x08000060", "ordered_abi_dispatches": [],
            "ordered_effects": [], "terminal_kind": "END",
        }
        empty_signature["signature_id"] = "effect-" + hashlib.sha256(
            _effect_test_stable(empty_signature)
        ).hexdigest()[:24]

        phase_controls = {
            "PRE_TRANSITION": {"external": [], "internal": []},
            "PRE_FIELD_INPUT": {"external": [], "internal": []},
        }
        source_case = {
            "case_id": "map-lifecycle-001-002-synthetic",
            "case_kind": "MAP_LIFECYCLE_COMPOSITE",
            "map": {"group": 1, "map": 2},
            "covered_owner_ids": ["MAP:001/002:000"],
            "dispatched_owner_ids": ["MAP:001/002:000"],
            "trigger_path": {"kind": "MAP_LIFECYCLE_COMPOSITE_TRIGGER"},
            "input_sequences": [{
                "sequence_id": "map-sequence-active", "tokens": [],
                "control_requirements": deepcopy(phase_controls),
                "effect_signature_ids": [signature["signature_id"]],
            }, {
                "sequence_id": "map-sequence-no-dispatch", "tokens": [],
                "control_requirements": deepcopy(phase_controls),
                "effect_signature_ids": [empty_signature["signature_id"]],
            }],
            "effect_signature_ids": sorted({
                signature["signature_id"], empty_signature["signature_id"],
            }),
            "map_lifecycle": {}, "source_provenance": {},
            "effect_inputs": {"choice": 1},
            "effect_preimages": {watch_id: "00"},
        }
        sequence_cases = map_effect_sequence_case_contracts(source_case)
        self.assertEqual(
            [row["case_id"] for row in sequence_cases],
            [
                f"{source_case['case_id']}--run-0000",
                f"{source_case['case_id']}--run-0001",
            ],
        )
        self.assertEqual(
            [row["source_sequence_id"] for row in sequence_cases],
            ["map-sequence-active", "map-sequence-no-dispatch"],
        )
        missing_signature = deepcopy(source_case)
        missing_signature["effect_signature_ids"] = [
            signature["signature_id"]
        ]
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "source/sequence signature closure",
        ):
            map_effect_sequence_case_contracts(missing_signature)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "MAP_EFFECT_SEQUENCE_CASE_REQUIRED",
        ):
            build_effect_case_initialization_binding(source_case, {})

        active_case, no_dispatch_case = sequence_cases
        fixture_binding = build_effect_case_initialization_binding(
            active_case, {},
        )
        instance = _seal_effect_instance({
            "schema_version": 1, "kind": "STAGE61_EFFECT_INSTANCE_V1",
            "template_id": template["template_id"],
            "case_id": active_case["case_id"],
            "occurrence_kind": "EFFECT_MEMBER",
            "signature_id": signature["signature_id"],
            "group_member_ordinal": 0, "group_key": effect["group_key"],
            "fixture_binding": fixture_binding,
            "input_values": {"choice": 1},
            "pre_images": [{
                "range_id": watch_id, "size": 1, "hex": "00",
                "sha256": hashlib.sha256(b"\x00").hexdigest(),
                "source_binding": {
                    "kind": "CASE_JSON_POINTER",
                    "json_pointer": f"/effect_preimages/{watch_id}",
                    "encoding": "LOWER_HEX", "byte_offset": 0,
                },
            }],
            "selected_selector_id": "selector-1",
            "expected_contract": {
                "domain": "flags", "owner": "TEST_FLAG_BANK",
                "relation": "EXACT_DECLARATIVE_TRANSITION",
                "proof_mode": "STATE_RANGE_EXACT",
                "observer_contract": {
                    "completion_boundary": "SYNC_RETURN",
                    "expected_result": {
                        "capture": {"kind": "NONE"}, "value": None,
                    },
                    "ranges": deepcopy(
                        template["transition_oracle"]["ranges"]
                    ),
                    "transitions": [{
                        "watch_id": watch_id, "kind": "EXACT_FINAL",
                        "expected_size": 1,
                        "expected_sha256": hashlib.sha256(b"\x01").hexdigest(),
                        "expected_hex": "01",
                    }],
                },
            },
        })
        binding = {
            "occurrence_kind": "EFFECT_MEMBER",
            "case_id": active_case["case_id"],
            "signature_id": signature["signature_id"],
            "group_key": effect["group_key"], "group_member_ordinal": 0,
            "template_id": template["template_id"],
            "instance_id": instance["instance_id"],
        }
        code_sha = template["abi_binding"]["code_span"]["sha256"]
        manifest = {
            "special_abis": [],
            "native_abis": [{
                "abi_key": abi_key, "symbol": "TestNative",
                "source": {
                    "definition_line": 1, "path": "test/source.c",
                    "sha256": "d" * 64,
                },
                "rom_binding": {
                    "address": "0x08000100", "byte_length": 2,
                    "sha256": code_sha,
                },
                "execution": "SYNC", "input_controls": [],
                "result_contract": {
                    "global_var_result_write": None,
                    "specialvar_return": None,
                },
                "effects": [{
                    "domain": "flags", "owner": "TEST_FLAG_BANK",
                    "relation": "EXACT_DECLARATIVE_TRANSITION",
                }],
                "visible_printers": [], "interaction_sequences": [],
                "complete": True, "target_pointer": "0x08000101",
            }],
        }
        result = validate_effect_registries(
            rom, manifest, {}, [template], [instance],
            effect_signatures=sorted(
                [signature, empty_signature],
                key=lambda row: row["signature_id"],
            ),
            effect_case_bindings=[binding],
            case_contracts={row["case_id"]: row for row in sequence_cases},
            runner_fixtures={},
        )
        self.assertEqual(result["counts"]["runner_case_count"], 2)
        self.assertEqual(result["counts"]["dispatched_case_count"], 1)
        self.assertEqual(result["counts"]["no_dispatch_case_count"], 1)
        self.assertEqual(result["counts"]["occurrence_count"], 1)
        self.assertEqual(
            result["instances"][0]["fixture_binding"]["case_id"],
            active_case["case_id"],
        )
        self.assertEqual(
            result["no_dispatch_contracts"][0]["case_id"],
            no_dispatch_case["case_id"],
        )

    def test_task_contract_binds_create_return_to_exact_slot_and_function(self) -> None:
        sink = {
            "watch_id": "effect-watch-" + "a" * 64,
            "entry_instruction_address": "0x08000100",
            "rom_byte_length": 2, "rom_sha256": "b" * 64,
            "caller_instruction_addresses": ["0x08000120"],
            "calling_convention": "AAPCS_THUMB",
            "args": [{
                "ordinal": 0, "location": "R0", "width_bits": 32,
                "capture": "VALUE", "pointee_length": 0,
            }, {
                "ordinal": 1, "location": "R1", "width_bits": 8,
                "capture": "VALUE", "pointee_length": 0,
            }],
            "return_capture": {"location": "R0", "width_bits": 8},
        }
        expected_call = {
            "ordinal": 0, "watch_id": sink["watch_id"],
            "caller_instruction_address": "0x08000120",
            "arguments": [{
                "ordinal": 0, "location": "R0", "capture": "VALUE",
                "width_bits": 32, "expected_value": 0x08000201,
            }, {
                "ordinal": 1, "location": "R1", "capture": "VALUE",
                "width_bits": 8, "expected_value": 1,
            }],
            "return_capture": {
                "location": "R0", "width_bits": 8, "expected_value": 2,
            },
        }
        slot = "0x03005E50"
        contract = {
            "completion_boundary": "TASK_TERMINAL",
            "expected_result": {
                "capture": {"kind": "NONE"}, "value": None,
            },
            "start_sinks": [sink], "expected_start_calls": [expected_call],
            "identities": [{
                "identity_id": "task-test", "kind": "TASK",
                "function_pc": "0x08000201",
                "task_table_address": "0x03005E00",
                "function_code_span": {
                    "start": "0x08000200", "length": 2,
                    "sha256": "c" * 64,
                },
                "slot_count": 16, "stride": 40, "function_offset": 0,
                "active_offset": 4, "state_offset": 8,
                "create_function_arg_ordinal": 0,
            }],
            "expected_events": [{
                "ordinal": 0, "event": "START_SINK_ENTRY",
                "identity_id": "task-test", "state": None,
                "call_ordinal": 0,
            }, {
                "ordinal": 1, "event": "TASK_CREATED",
                "identity_id": "task-test", "state": None,
                "start_call_ordinal": 0, "task_id": 2,
                "slot_address": slot,
            }, {
                "ordinal": 2, "event": "STATE_ENTER",
                "identity_id": "task-test", "state": 0,
                "task_id": 2, "slot_address": slot,
            }, {
                "ordinal": 3, "event": "TASK_DESTROYED",
                "identity_id": "task-test", "state": None,
                "task_id": 2, "slot_address": slot,
            }],
            "input_sequence": [], "timeout_frames": 600,
            "extra_events_forbidden": True,
        }
        self.assertEqual(
            _validate_effect_task_contract(contract, "task"), contract,
        )
        forged = deepcopy(contract)
        forged["expected_start_calls"][0]["return_capture"][
            "expected_value"
        ] = 3
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "return→slot",
        ):
            _validate_effect_task_contract(forged, "task")

    def test_composite_contract_has_exact_child_and_global_event_ordinals(self) -> None:
        contract = {
            "completion_boundary": "FIELD_RELEASE",
            "expected_result": {
                "capture": {"kind": "NONE"}, "value": None,
            },
            "child_contract_ids": ["child-a", "child-b", "child-c"],
            "required_children": ["child-a", "child-b"],
            "forbidden_children": ["child-c"],
            "child_observations": [{
                "child_contract_id": "child-a", "expectation": "REQUIRED",
                "expected_hit_count": 1, "expected_global_ordinals": [0],
            }, {
                "child_contract_id": "child-b", "expectation": "REQUIRED",
                "expected_hit_count": 1, "expected_global_ordinals": [1],
            }, {
                "child_contract_id": "child-c", "expectation": "FORBIDDEN",
                "expected_hit_count": 0, "expected_global_ordinals": [],
            }],
            "global_event_count": 2,
            "required_order": [{"before": "child-a", "after": "child-b"}],
            "extra_child_events_forbidden": True,
        }
        self.assertEqual(
            _validate_effect_composite_contract(
                contract, "composite",
                available_contract_ids={"child-a", "child-b", "child-c"},
            ),
            contract,
        )
        forged = deepcopy(contract)
        forged["child_observations"][2].update({
            "expected_hit_count": 1, "expected_global_ordinals": [1],
        })
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "hit/ordinal",
        ):
            _validate_effect_composite_contract(
                forged, "composite",
                available_contract_ids={"child-a", "child-b", "child-c"},
            )

    def test_script_opcode_watch_observes_interpreter_cursor_not_data_pc(self) -> None:
        watch = _effect_abi_entry_watch({
            "abi_binding": {
                "dispatch_kind": "SCRIPT_OPCODE", "opcode": "0x44",
                "entry_pc": "0x0819413A",
            },
        }, "FIELD_RELEASE")
        self.assertEqual(watch["hook_pc"], "0x0806911A")
        self.assertNotEqual(watch["hook_pc"], "0x0819413A")
        resolver = watch["address_resolver"]
        self.assertEqual(resolver, {
            "kind": "SCRIPT_CURSOR_DISPATCH",
            "script_context_address": "0x03000EA8",
            "script_cursor_offset": 8,
            "opcode_register": "R1", "cursor_register": "R2",
            "opcode_load_pc": "0x08069118",
            "opcode_load_raw_hex": "1178", "hook_raw_hex": "501c",
            "handler_table_start_offset": 92,
            "handler_table_end_offset": 96,
        })
        self.assertEqual(
            [(row["location"], row["width_bits"])
             for row in watch["arg_capture"]],
            [("R1", 8), ("R2", 32)],
        )
        stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        _validate_effect_raw_watch_rom_binding(
            stage61, watch, "SCRIPT_CURSOR_DISPATCH test",
        )
        for address in (0x08069118, 0x0806911A, 0x08069124, 0x0806912A):
            broken_rom = bytearray(stage61)
            broken_rom[address - 0x08000000] ^= 1
            with self.subTest(address=f"0x{address:08X}"), \
                    self.assertRaisesRegex(
                        Stage61InteractionOracleError,
                        "preimage|handler resolution",
                    ):
                _validate_effect_raw_watch_rom_binding(
                    bytes(broken_rom), watch,
                    "SCRIPT_CURSOR_DISPATCH mutated test",
                )

    def test_flash_consumer_recomputes_continuous_cfg_and_rejects_clobber(self) -> None:
        rom, clean, consumer = self._flash_consumer_fixture()
        self.assertEqual(
            _validate_effect_flash_consumer(
                rom, clean, consumer, pointer_slot=0x03007474,
                label="synthetic consumer",
            ),
            consumer,
        )
        broken_rom = bytearray(rom)
        # Replace the otherwise harmless instruction between MOV and BL with
        # movs r3,#0, then update the superficial span SHA.  Data-flow, not a
        # stale hash, must reject the target-register clobber.
        broken_rom[0x108:0x10A] = bytes.fromhex("0023")
        broken = deepcopy(consumer)
        broken["owner_code_span"]["sha256"] = hashlib.sha256(
            bytes(broken_rom[0x100:0x124])
        ).hexdigest()
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "clobber",
        ):
            _effect_flash_consumer_cfg_evidence(
                bytes(broken_rom), broken, owner_start=0x08000100,
                owner_end=0x08000124, label="clobbered consumer",
            )

    def test_flash_consumer_rejects_stack_slot_overwrite_and_false_root(self) -> None:
        rom, clean, consumer = self._flash_consumer_fixture()
        forged_root = deepcopy(consumer)
        forged_root["inbound_roots"] = ["0x08000082"]
        forged_root = _seal_flash_consumer(forged_root)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "inbound roots",
        ):
            _validate_effect_flash_consumer(
                rom, clean, forged_root, pointer_slot=0x03007474,
                label="false-root consumer",
            )

        overwritten = bytearray(0x200)
        overwritten[0x100:0x102] = bytes.fromhex("00b5")
        overwritten[0x102:0x104] = bytes.fromhex("0748")
        overwritten[0x104:0x106] = bytes.fromhex("0168")
        overwritten[0x106:0x108] = bytes.fromhex("0091")  # spill r1
        overwritten[0x108:0x10A] = bytes.fromhex("0022")  # movs r2,#0
        overwritten[0x10A:0x10C] = bytes.fromhex("0092")  # overwrite slot
        overwritten[0x10C:0x10E] = bytes.fromhex("009b")  # reload r3
        overwritten[0x10E:0x112] = _thumb_bl(0x0800010E, 0x08000130)
        overwritten[0x120:0x124] = (0x03007474).to_bytes(4, "little")
        overwritten[0x130:0x132] = bytes.fromhex("1847")
        stack_consumer = deepcopy(consumer)
        stack_consumer.update({
            "owner_code_span": {
                "start": "0x08000100", "length": 0x24,
                "sha256": hashlib.sha256(
                    bytes(overwritten[0x100:0x124])
                ).hexdigest(),
            },
            "target_transfer_steps": [{
                "pc": "0x08000106", "raw_hex": "0091", "kind": "SPILL",
                "source_register": "R1", "destination_register": None,
                "stack_offset": 0,
            }, {
                "pc": "0x0800010C", "raw_hex": "009b", "kind": "RELOAD",
                "source_register": None, "destination_register": "R3",
                "stack_offset": 0,
            }],
            "veneer_bl_pc": "0x0800010E",
        })
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "clobber",
        ):
            _effect_flash_consumer_cfg_evidence(
                bytes(overwritten), stack_consumer,
                owner_start=0x08000100, owner_end=0x08000124,
                label="stack overwrite consumer",
            )

    def test_flash_consumer_rejects_current_only_old_body_interior_inbound(self) -> None:
        rom, clean, consumer = self._flash_consumer_fixture()
        broken_rom = bytearray(rom)
        broken_rom[0x90:0x94] = _thumb_bl(0x08000090, 0x08000108)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "interior inbound",
        ):
            _validate_effect_flash_consumer(
                bytes(broken_rom), clean, consumer,
                pointer_slot=0x03007474, label="interior consumer",
            )

    def test_flash_consumer_closes_real_erase_sector_loop(self) -> None:
        stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        clean = (ROOT / "build/reference/FireRed_JPN_Rev0_clean.gba").read_bytes()
        owner = 0x080DA714
        owner_length = 0x24
        consumer = {
            "consumer_id": "", "classification": "LIVE_LITERAL",
            "owner_function_entry": "0x080DA714",
            "owner_code_span": {
                "start": "0x080DA714", "length": owner_length,
                "sha256": hashlib.sha256(
                    stage61[owner - 0x08000000:
                            owner - 0x08000000 + owner_length]
                ).hexdigest(),
            },
            "literal_word_address": "0x080DA734",
            "address_load_pc": "0x080DA718",
            "address_transfer_steps": [],
            "pointee_load_pc": "0x080DA71A", "target_register": "R1",
            "target_transfer_steps": [],
            "veneer_bl_pc": "0x080DA71E",
            "veneer_entry_pc": "0x081C7ACC", "veneer_raw_hex": "0847",
            "inbound_roots": ["0x080F67CC"],
            "external_inbound_edges": [], "cfg_closure": {},
        }
        cfg, address_steps, target_steps, _ = \
            _effect_flash_consumer_cfg_evidence(
                stage61, consumer, owner_start=owner,
                owner_end=owner + owner_length,
                label="real ERASE_SECTOR consumer",
            )
        self.assertEqual(address_steps, [])
        self.assertEqual(target_steps, [])
        self.assertEqual(cfg["path_pcs"], [
            "0x080DA714", "0x080DA716", "0x080DA718",
            "0x080DA71A", "0x080DA71C", "0x080DA71E",
        ])
        consumer["cfg_closure"] = cfg
        inbound = _effect_flash_direct_inbound_edges(
            stage61, clean,
            target_addresses=set(range(owner, owner + owner_length, 2)),
            source_owned_pcs={int(pc, 16) for pc in cfg["path_pcs"]},
        )
        consumer["external_inbound_edges"] = [{
            **row,
            "target_relation": "ENTRY" if target == owner else "INTERIOR",
        } for target in sorted(inbound)
          for row in inbound[target]
          if not owner <= int(row["source_pc"], 16) < owner + owner_length]
        consumer["external_inbound_edges"].sort(
            key=lambda row: (row["target_pc"], row["source_pc"], row["kind"]),
        )
        consumer = _seal_flash_consumer(consumer)
        self.assertEqual(
            _validate_effect_flash_consumer(
                stage61, clean, consumer, pointer_slot=0x03007480,
                label="real ERASE_SECTOR consumer",
            ),
            consumer,
        )

    def test_flash_slot_writer_and_mutation_targets_close_against_real_rom(self) -> None:
        stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        clean = (ROOT / "build/reference/FireRed_JPN_Rev0_clean.gba").read_bytes()
        slots = {0x03007474, 0x0300746C, 0x0300747C, 0x03007480}
        writers = _effect_flash_slot_destination_writers(
            stage61, pointer_slots=slots, label="real slot writers",
        )
        self.assertEqual(len(writers), 4)
        self.assertEqual(
            {row["pointer_slot"] for row in writers},
            {f"0x{slot:08X}" for slot in slots},
        )
        extra_writer_rom = bytearray(stage61)
        extra_pc = 0x09FF0000
        extra_offset = extra_pc - 0x08000000
        extra_writer_rom[extra_offset:extra_offset + 2] = bytes.fromhex("0148")
        extra_writer_rom[extra_offset + 2:extra_offset + 4] = bytes.fromhex("0160")
        extra_writer_rom[extra_offset + 4:extra_offset + 6] = bytes.fromhex("7047")
        extra_writer_rom[extra_offset + 8:extra_offset + 12] = \
            (0x03007474).to_bytes(4, "little")
        self.assertEqual(len(_effect_flash_slot_destination_writers(
            bytes(extra_writer_rom), pointer_slots=slots,
            label="extra slot writer",
        )), 5)

        expected_counts = {
            0x081C2E1C: (1, 6), 0x081C2E90: (1, 6),
            0x081C2F60: (1, 4), 0x081C302C: (3, 10),
        }
        for entry, (function_count, leaf_count) in expected_counts.items():
            with self.subTest(entry=f"0x{entry:08X}"):
                closure = _effect_flash_target_cfg_evidence(
                    stage61, clean, root_entry=entry,
                    label=f"target {entry:#x}",
                )
                self.assertEqual(len(closure["functions"]), function_count)
                self.assertEqual(len(closure["flash_strb_leaves"]), leaf_count)
                self.assertTrue(all(
                    function["return_pcs"] for function in closure["functions"]
                ))
        program_sector = _effect_flash_target_cfg_evidence(
            stage61, clean, root_entry=0x081C302C,
            label="program sector descendants",
        )
        self.assertEqual(program_sector["direct_descendant_calls"], [{
            "caller_pc": "0x081C304E", "target_pc": "0x081C2E90",
            "kind": "ERASE_SECTOR_LEAF",
        }, {
            "caller_pc": "0x081C30B8", "target_pc": "0x081C2FF4",
            "kind": "PROGRAM_BYTE_LEAF",
        }])

    def test_flash_mutation_target_rejects_branch_write_and_interior_caller(self) -> None:
        stage61 = bytearray((
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes())
        clean = (ROOT / "build/reference/FireRed_JPN_Rev0_clean.gba").read_bytes()
        for pc, raw, reason in (
            (0x081C2E20, bytes.fromhex("00e0"), "branch"),
            (0x081C2E20, bytes.fromhex("0070"), "write leaf"),
        ):
            broken = bytearray(stage61)
            offset = pc - 0x08000000
            broken[offset:offset + 2] = raw
            with self.subTest(reason=reason), self.assertRaisesRegex(
                Stage61InteractionOracleError, "source divergence",
            ):
                _effect_flash_target_cfg_evidence(
                    bytes(broken), clean, root_entry=0x081C2E1C,
                    label=f"additional {reason}",
                )
        interior = bytearray(stage61)
        interior[0:4] = _thumb_bl(0x08000000, 0x081C2E9C)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "interior external inbound",
        ):
            _effect_flash_target_cfg_evidence(
                bytes(interior), clean, root_entry=0x081C2E90,
                label="interior caller",
            )

    def test_effect_template_selector_rejects_result_capture_and_gaps(self) -> None:
        rom, abi_index, template, _ = self._declarative_template_fixture()
        result_driven = deepcopy(template)
        result_driven["input_schema"][0].update({
            "capture_phase": "ABI_RETURN",
            "source": {
                "kind": "CALL_RETURN", "hook_pc": "0x08000100",
                "location": "R0", "width_bits": 16,
                "case_value_pointer": "/effect_inputs/choice",
            },
        })
        result_driven = _seal_effect_template(result_driven)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "結果/完了観測",
        ):
            validate_effect_template(
                result_driven, stage61_rom=rom, abi_index=abi_index,
            )
        gap = deepcopy(template)
        gap["selector"]["rows"] = gap["selector"]["rows"][:1]
        gap["transition_oracle"]["rules"] = \
            gap["transition_oracle"]["rules"][:1]
        gap = _seal_effect_template(gap)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "overlap/gap",
        ):
            validate_effect_template(gap, stage61_rom=rom, abi_index=abi_index)

    def test_pointer_watch_validates_worst_case_resolved_end(self) -> None:
        watch_id = "effect-watch-" + "f" * 64
        effect = {
            "domain": "party", "owner": "POINTER_RANGE",
            "relation": "UNCHANGED", "proof_mode": "STATE_RANGE_EXACT",
            "observer_contract": {
                "completion_boundary": "SYNC_RETURN",
                "expected_result": {
                    "capture": {"kind": "NONE"}, "value": None,
                },
                "ranges": [{
                    "watch_id": watch_id, "space": "EWRAM",
                    "resolver": "U32_POINTER",
                    "pointer_address": "0x02000000", "offset": 0,
                    "address_min": "0x0203FFF0",
                    "address_max_exclusive": "0x02040000",
                    "length": 2, "source_owner": "POINTER_RANGE",
                    "source_ref": "test/source.c", "canonicalization": "NONE",
                }],
                "transitions": [{
                    "watch_id": watch_id, "kind": "UNCHANGED",
                }],
            },
        }
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "pointer range",
        ):
            validate_instantiated_effect_contract(effect)

    def test_instantiated_state_effect_requires_one_precomputed_result(self) -> None:
        watch_id = "effect-watch-" + "a" * 64
        effect = {
            "domain": "flags", "owner": "EXPANDED_FLAGS",
            "relation": "UNCHANGED_FOR_THIS_SOURCE_CASE",
            "proof_mode": "STATE_RANGE_EXACT",
            "observer_contract": {
                "completion_boundary": "SYNC_RETURN",
                "expected_result": {
                    "capture": {"kind": "NONE"}, "value": None,
                },
                "ranges": [{
                    "watch_id": watch_id, "space": "EWRAM",
                    "resolver": "ABSOLUTE", "address": "0x0203B0E8",
                    "length": 0x200, "source_owner": "gExpandedFlags",
                    "source_ref": "config/ram_layout.csv",
                    "canonicalization": "NONE",
                }],
                "transitions": [{
                    "watch_id": watch_id, "kind": "UNCHANGED",
                }],
            },
        }
        self.assertEqual(
            validate_instantiated_effect_contract(effect),
            effect,
        )
        broken = deepcopy(effect)
        broken["observer_contract"]["expected_result"]["value"] = 0
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "NONE expected value",
        ):
            validate_instantiated_effect_contract(broken)

    def test_instantiated_call_effect_is_exact_and_rejects_partition(self) -> None:
        watch_id = "effect-watch-" + "b" * 64
        sink = {
            "watch_id": watch_id,
            "entry_instruction_address": "0x0806DE74",
            "rom_byte_length": 4, "rom_sha256": "c" * 64,
            "caller_instruction_addresses": ["0x08123456"],
            "calling_convention": "AAPCS_THUMB",
            "args": [{
                "ordinal": 0, "location": "R0", "width_bits": 16,
                "capture": "VALUE", "pointee_length": 0,
            }],
            "return_capture": {"location": "R0", "width_bits": 16},
        }
        effect = {
            "domain": "flags", "owner": "FlagSet",
            "relation": "CALL_EXACT", "proof_mode": "CALL_SINK_EXACT",
            "observer_contract": {
                "completion_boundary": "SYNC_RETURN",
                "expected_result": {
                    "capture": {"kind": "RETURN_R0", "width_bits": 16},
                    "value": 0,
                },
                "sinks": [sink],
                "expected_calls": [{
                    "ordinal": 0, "watch_id": watch_id,
                    "caller_instruction_address": "0x08123456",
                    "arguments": [{
                        "ordinal": 0, "location": "R0", "capture": "VALUE",
                        "width_bits": 16, "expected_value": 7,
                    }],
                    "return_capture": {
                        "location": "R0", "width_bits": 16,
                        "expected_value": 0,
                    },
                }],
                "extra_calls_forbidden": True,
            },
        }
        self.assertEqual(validate_instantiated_effect_contract(effect), effect)
        broken = deepcopy(effect)
        broken["observer_contract"]["result_selector"] = {
            "kind": "RETURN_R0", "width_bits": 16,
        }
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "schema",
        ):
            validate_instantiated_effect_contract(broken)

    def test_record_effect_stamps_dynamic_opcode_and_member_ordinal(self) -> None:
        at = 0x08123456
        state = _Execution(
            pc=at, execution_trace=[at],
            current_instruction_address=at, current_opcode=0x25,
        )
        _record_effect(
            state, "flags", "FLAG:1", "SET", at,
            abi_key="SPECIAL:0001:0x08000001",
        )
        _record_effect(
            state, "vars", "VAR:1", "SET", at,
            abi_key="SPECIAL:0001:0x08000001",
        )
        self.assertEqual(
            [(row["execution_trace_index"], row["opcode"],
              row["group_member_ordinal"]) for row in state.effects],
            [(0, "0x25", 0), (0, "0x25", 1)],
        )
        self.assertTrue(all(
            row["abi_key"] == "SPECIAL:0001:0x08000001"
            for row in state.effects
        ))

    def test_group_key_is_command_occurrence_only(self) -> None:
        effect = {
            "instruction_address": "0x08123456",
            "execution_trace_index": 7,
            "opcode": "0x25",
            "abi_key": "SPECIAL:0001:0x08000001",
            "domain": "flags", "owner": "FLAG:1", "relation": "SET",
            "group_member_ordinal": 0,
        }
        expected = _effect_group_key(0x08120000, effect)
        self.assertRegex(expected, r"^effect-group-[0-9a-f]{64}$")
        semantic_mutation = deepcopy(effect)
        semantic_mutation.update({
            "domain": "party", "owner": "PARTY", "relation": "OTHER",
            "group_member_ordinal": 9,
            "proof_mode": "STATE_RANGE_EXACT",
            "observer_contract": {"not": "part-of-command-identity"},
        })
        self.assertEqual(
            _effect_group_key(0x08120000, semantic_mutation), expected,
        )
        for key, value in (
            ("execution_trace_index", 8),
            ("instruction_address", "0x08123458"),
            ("opcode", "0x26"),
            ("abi_key", "SPECIAL:0002:0x08000003"),
        ):
            changed = deepcopy(effect)
            changed[key] = value
            self.assertNotEqual(_effect_group_key(0x08120000, changed), expected)
        self.assertNotEqual(_effect_group_key(0x08120002, effect), expected)

    def test_var_and_flag_writers_use_the_dynamic_effect_contract(self) -> None:
        context = SimpleNamespace(var_mapping={}, flag_mapping={})
        state = _Execution(pc=0x08123456)
        state.execution_trace = [0x08123456]
        state.current_instruction_address = 0x08123456
        state.current_opcode = 0x16
        _set_var(context, state, 0x8004, 7, 0x08123456)
        _set_flag(context, state, 0x0200, True, 0x08123456)
        self.assertEqual(
            [(row["execution_trace_index"], row["opcode"],
              row["group_member_ordinal"]) for row in state.effects],
            [(0, "0x16", 0), (0, "0x16", 1)],
        )
        self.assertEqual(
            [row["after"] for row in state.effects], [7, True],
        )
        rows = _runtime_effect_trace(0x08120000, state)
        self.assertEqual(rows[0]["group_key"], rows[1]["group_key"])

        abi_state = _Execution(pc=0x08123456)
        abi_state.execution_trace = [0x08123456]
        abi_state.current_instruction_address = 0x08123456
        abi_state.current_opcode = 0x25
        abi_state.current_abi_key = "SPECIAL:0001:0x08000001"
        _set_var(context, abi_state, 0x8004, 9, 0x08123456)
        _set_flag(context, abi_state, 0x0200, False, 0x08123456)
        self.assertEqual(
            {row["abi_key"] for row in abi_state.effects},
            {"SPECIAL:0001:0x08000001"},
        )
        self.assertEqual(
            len({_effect_group_key(0x08120000, row)
                 for row in abi_state.effects}),
            1,
        )

    def test_runtime_trace_separates_repeated_pc_and_requires_ordinals(self) -> None:
        state = _Execution(pc=0x08100000)
        state.effects = [{
            "domain": "flags", "owner": "FLAG:1", "relation": "SET",
            "instruction_address": "0x08123456",
            "execution_trace_index": 3, "opcode": "0x29", "abi_key": None,
            "group_member_ordinal": 0,
        }, {
            "domain": "vars", "owner": "VAR:1", "relation": "SET",
            "instruction_address": "0x08123456",
            "execution_trace_index": 3, "opcode": "0x29", "abi_key": None,
            "group_member_ordinal": 1,
        }, {
            "domain": "flags", "owner": "FLAG:1", "relation": "SET",
            "instruction_address": "0x08123456",
            "execution_trace_index": 9, "opcode": "0x29", "abi_key": None,
            "group_member_ordinal": 0,
        }]
        rows = _runtime_effect_trace(0x08120000, state)
        self.assertEqual(rows[0]["group_key"], rows[1]["group_key"])
        self.assertNotEqual(rows[1]["group_key"], rows[2]["group_key"])
        shuffled = deepcopy(state)
        shuffled.effects = [
            shuffled.effects[2], shuffled.effects[1], shuffled.effects[0],
        ]
        self.assertEqual(
            _runtime_effect_trace(0x08120000, shuffled), rows,
        )
        broken = deepcopy(state)
        broken.effects[1]["group_member_ordinal"] = 2
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "ordinal",
        ):
            _runtime_effect_trace(0x08120000, broken)


class Stage61EffectSourceProducerFocusedTests(unittest.TestCase):
    @staticmethod
    def _required(*, flag_value: bool | None = None) -> dict:
        return {
            "flags": [] if flag_value is None else [{
                "id": 1, "value": flag_value,
            }],
            "engine_special_flags": [], "vars": [], "items": [],
            "trainers": [], "objects": [], "warp": None,
            "battle": None, "money": None, "coins": None,
            "party": None, "storage": None, "berry_powder": None,
            "persistent": [],
        }

    @staticmethod
    def _signature(
        *, root: int, instruction: int, abi_key: str,
        with_effect: bool, terminal: str = "FIELD_RELEASE",
    ) -> dict:
        effect = {
            "domain": "flags", "owner": "TEST_FLAG_BANK",
            "relation": "EXACT_FINAL",
            "instruction_address": f"0x{instruction:08X}",
            "execution_trace_index": 0, "opcode": "0x23",
            "abi_key": abi_key, "group_member_ordinal": 0,
            "after": True,
        }
        group_key = _effect_group_key(root, effect)
        effect["group_key"] = group_key
        dispatch = {
            "execution_trace_index": 0,
            "instruction_address": f"0x{instruction:08X}",
            "opcode": "0x23", "abi_key": abi_key,
            "dispatch_kind": "NATIVE", "entry_pc": "0x08000100",
            "result_capture": {"kind": "NONE", "value": None},
            "effect_member_count": int(with_effect),
            "group_key": group_key,
        }
        payload = {
            "runtime_root": f"0x{root:08X}",
            "ordered_abi_dispatches": [dispatch],
            "ordered_effects": [effect] if with_effect else [],
            "terminal_kind": terminal,
        }
        return {
            "signature_id": "effect-" + hashlib.sha256(
                _effect_test_stable(payload)
            ).hexdigest()[:24],
            **payload,
        }

    @staticmethod
    def _empty_signature() -> dict:
        payload = {
            "runtime_root": "0x08000070",
            "ordered_abi_dispatches": [], "ordered_effects": [],
            "terminal_kind": "FIELD_RELEASE",
        }
        return {
            "signature_id": "effect-" + hashlib.sha256(
                _effect_test_stable(payload)
            ).hexdigest()[:24],
            **payload,
        }

    def _fixture(self) -> tuple[bytes, dict, dict, list[dict], list[dict]]:
        rom = bytearray(0x200)
        rom[0x40] = 0x23
        rom[0x50] = 0x23
        rom[0x100:0x102] = b"\x00\x47"
        code_sha = hashlib.sha256(b"\x00\x47").hexdigest()
        abi_key = "NATIVE:0x08000101"
        manifest = {
            "special_abis": [],
            "native_abis": [{
                "abi_key": abi_key, "symbol": "TestNative",
                "source": {
                    "definition_line": 1, "path": "test/source.c",
                    "sha256": "d" * 64,
                },
                "rom_binding": {
                    "address": "0x08000100", "byte_length": 2,
                    "sha256": code_sha,
                },
                "execution": "SYNC", "input_controls": [],
                "result_contract": {
                    "global_var_result_write": None,
                    "specialvar_return": None,
                },
                "effects": [{
                    "domain": "flags", "owner": "TEST_FLAG_BANK",
                    "relation": "EXACT_FINAL",
                }],
                "visible_printers": [], "interaction_sequences": [],
                "complete": True, "target_pointer": "0x08000101",
            }],
        }
        active = self._signature(
            root=0x08000020, instruction=0x08000040,
            abi_key=abi_key, with_effect=True,
        )
        abi_no_effect = self._signature(
            root=0x08000030, instruction=0x08000050,
            abi_key=abi_key, with_effect=False,
        )
        empty = self._empty_signature()
        required_active = self._required(flag_value=True)
        object_case = {
            "case_id": "object-source", "interaction_expected": True,
            "control_requirements": {"external": [], "internal": []},
            "runtime_control_assignment": {
                "assignment_id": "assignment-source",
                "effect_signature_ids": [active["signature_id"]],
            },
            "input_sequences": [{
                "sequence_id": "object-sequence", "tokens": ["A"],
                "basis": {
                    "kind": "event-cfg-oracle",
                    "effect_signature_id": active["signature_id"],
                },
                "effect_contract": {
                    "required_final": required_active,
                    "battle_start_required_postconditions": None,
                    "post_battle_continuation": None,
                },
            }],
        }
        phase_controls = {
            "PRE_TRANSITION": {"external": [], "internal": []},
            "PRE_FIELD_INPUT": {"external": [], "internal": []},
        }
        map_case = {
            "case_id": "map-source",
            "case_kind": "MAP_LIFECYCLE_COMPOSITE",
            "map": {"group": 1, "map": 2},
            "covered_owner_ids": ["MAP:001/002:000"],
            "dispatched_owner_ids": [],
            "trigger_path": {"kind": "MAP_LIFECYCLE_COMPOSITE_TRIGGER"},
            "input_sequences": [{
                "sequence_id": "map-sequence", "tokens": [],
                "basis": {"kind": "FINAL_MAP_LIFECYCLE_CFG_EXECUTION"},
                "control_requirements": phase_controls,
                "required_postconditions": self._required(),
                "battle_start_required_postconditions": None,
                "post_battle_continuation": None,
                "effect_signature_ids": [abi_no_effect["signature_id"]],
            }],
            "effect_signature_ids": [abi_no_effect["signature_id"]],
            "map_lifecycle": {}, "source_provenance": {},
        }
        no_dispatch_case = {
            "case_id": "event-no-dispatch",
            "owner_id": "COMMON:000", "control_requirements": {
                "external": [], "internal": [],
            },
            "input_sequence": {
                "sequence_id": "event-no-dispatch-sequence", "tokens": [],
                "required_postconditions": self._required(),
                "battle_start_required_postconditions": None,
                "post_battle_continuation": None,
            },
            "effect_signature_ids": [empty["signature_id"]],
        }
        signatures = sorted(
            [active, abi_no_effect, empty],
            key=lambda row: row["signature_id"],
        )
        runtime = {
            "schema_version": 1,
            "kind": "STAGE61_RUNTIME_CONTROL_EXPANSION_CONTRACT",
            "roots": [{
                "runtime_root": "0x08000020",
                "candidate_assignments": [{
                    "assignment_id": "assignment-source",
                    "effect_signature_ids": [active["signature_id"]],
                }],
            }],
            "effect_signatures": signatures,
            "runner_fixtures": {},
            "event_runtime_cases": [map_case, no_dispatch_case],
        }
        runtime["contract_sha256"] = hashlib.sha256(
            _effect_test_stable(runtime)
        ).hexdigest()
        return (
            bytes(rom), manifest, runtime, [object_case],
            [map_case, no_dispatch_case],
        )

    def test_source_producer_closes_virtual_cases_rebinds_and_validates(
        self,
    ) -> None:
        rom, manifest, runtime, objects, events = self._fixture()
        runtime["effect_raw_watch_plan"] = {"stale": True}
        result = build_effect_source_registry(
            rom, manifest, {}, runtime_control=runtime,
            final_object_cases=objects, event_runtime_cases=events,
            runner_fixtures={},
        )
        self.assertEqual(result["kind"], "STAGE61_EFFECT_SOURCE_REGISTRY_V1")
        unsigned_result = deepcopy(result)
        declared_result_sha = unsigned_result.pop("contract_sha256")
        self.assertEqual(
            declared_result_sha,
            hashlib.sha256(_effect_test_stable(unsigned_result)).hexdigest(),
        )
        unsigned_runtime = deepcopy(result["updated_runtime_control"])
        declared_runtime_sha = unsigned_runtime.pop("contract_sha256")
        self.assertEqual(
            declared_runtime_sha,
            hashlib.sha256(_effect_test_stable(unsigned_runtime)).hexdigest(),
        )
        self.assertEqual(
            result["updated_final_object_cases"][0]["case_id"],
            "object-source",
        )
        self.assertIn(
            "input_sequences", result["updated_final_object_cases"][0],
        )
        self.assertEqual(
            result["effect_object_runtime_cases"][0]["case_id"],
            "object-source--run-0000",
        )
        self.assertEqual(
            result["updated_event_runtime_cases"][0]["case_id"],
            "map-source",
        )
        self.assertIn(
            "input_sequences", result["updated_event_runtime_cases"][0],
        )
        self.assertEqual(
            result["effect_event_runtime_cases"][0]["case_id"],
            "map-source--run-0000",
        )
        self.assertNotIn(
            "effect_raw_watch_plan", result["updated_runtime_control"],
        )
        rebindings = {
            row["old_signature_id"]: row["new_signature_id"]
            for row in result["signature_id_rebindings"]
        }
        source_basis = result["updated_final_object_cases"][0][
            "input_sequences"
        ][0]["basis"]
        self.assertEqual(
            source_basis["effect_signature_id"],
            result["effect_object_runtime_cases"][0]
            ["runtime_control_assignment"]["effect_signature_ids"][0],
        )
        self.assertEqual(
            result["updated_runtime_control"]["roots"][0]
            ["candidate_assignments"][0]["effect_signature_ids"],
            [source_basis["effect_signature_id"]],
        )
        self.assertNotEqual(
            source_basis["effect_signature_id"],
            objects[0]["input_sequences"][0]["basis"]
            ["effect_signature_id"],
        )
        self.assertEqual(
            len(result["effect_instances"]), 2,
        )
        self.assertEqual(
            {row["occurrence_kind"] for row in result["effect_instances"]},
            {"EFFECT_MEMBER", "ABI_DISPATCH_NO_EFFECT"},
        )
        self.assertEqual(
            result["validation"]["counts"]["runner_case_count"], 3,
        )
        self.assertEqual(
            result["validation"]["counts"]["no_dispatch_case_count"], 1,
        )
        self.assertTrue(all(
            row["observed_after_used_as_expectation"] is False
            and row["final_state_proven_by_case_postconditions"] is True
            for row in result["relation_inventory"]
        ))
        template = next(
            row for row in result["effect_templates"]
            if row["transition_oracle"]["effect_identity"]["relation"]
            == "EXACT_FINAL"
        )
        virtual = result["effect_object_runtime_cases"][0]
        required = virtual["input_sequence"]["effect_contract"][
            "required_final"
        ]
        self.assertEqual(
            template["transition_oracle"]["source_contracts"][0]
            ["required_postconditions_sha256"],
            hashlib.sha256(_effect_test_stable(required)).hexdigest(),
        )
        rebound_copy = rebind_effect_signature_references(
            objects, result["signature_id_rebindings"],
        )
        self.assertEqual(
            rebound_copy, result["updated_final_object_cases"],
        )
        self.assertEqual(
            rebind_effect_signature_references(
                events, result["signature_id_rebindings"],
            ),
            result["updated_event_runtime_cases"],
        )
        self.assertEqual(
            rebound_copy[0]["input_sequences"][0]["basis"]
            ["effect_signature_id"],
            rebindings[objects[0]["input_sequences"][0]["basis"]
                       ["effect_signature_id"]],
        )

    def test_source_producer_rejects_unknown_effect_semantic_payload(
        self,
    ) -> None:
        rom, manifest, runtime, objects, events = self._fixture()
        signature = next(
            row for row in runtime["effect_signatures"]
            if row["ordered_effects"]
        )
        signature["ordered_effects"][0][
            "unexpected_semantic_payload"
        ] = "forged"
        unsigned_signature = deepcopy(signature)
        unsigned_signature.pop("signature_id")
        signature["signature_id"] = "effect-" + hashlib.sha256(
            _effect_test_stable(unsigned_signature)
        ).hexdigest()[:24]
        runtime["effect_signatures"].sort(
            key=lambda row: row["signature_id"],
        )
        runtime.pop("contract_sha256")
        runtime["contract_sha256"] = hashlib.sha256(
            _effect_test_stable(runtime)
        ).hexdigest()
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "ordered_effects",
        ):
            build_effect_source_registry(
                rom, manifest, {}, runtime_control=runtime,
                final_object_cases=objects, event_runtime_cases=events,
                runner_fixtures={},
            )

    def test_source_producer_rejects_resealed_after_payload_attacks(
        self,
    ) -> None:
        attacks = ({"after": "true"}, {
            "after": {"untyped": "payload"},
        }, {"after": [True]}, {"remove_after": True}, {
            "relation": "FORGED_RELATION", "after": True,
        })
        for attack in attacks:
            with self.subTest(attack=attack):
                rom, manifest, runtime, objects, events = self._fixture()
                signature = next(
                    row for row in runtime["effect_signatures"]
                    if row["ordered_effects"]
                )
                effect = signature["ordered_effects"][0]
                if attack.get("remove_after"):
                    effect.pop("after")
                else:
                    effect.update({
                        key: deepcopy(value) for key, value in attack.items()
                    })
                unsigned_signature = deepcopy(signature)
                unsigned_signature.pop("signature_id")
                signature["signature_id"] = "effect-" + hashlib.sha256(
                    _effect_test_stable(unsigned_signature)
                ).hexdigest()[:24]
                runtime["effect_signatures"].sort(
                    key=lambda row: row["signature_id"],
                )
                runtime.pop("contract_sha256")
                runtime["contract_sha256"] = hashlib.sha256(
                    _effect_test_stable(runtime)
                ).hexdigest()
                with self.assertRaisesRegex(
                    Stage61InteractionOracleError,
                    "EXACT_FINAL after bool不正|after relation/domain不正",
                ):
                    build_effect_source_registry(
                        rom, manifest, {}, runtime_control=runtime,
                        final_object_cases=objects,
                        event_runtime_cases=events, runner_fixtures={},
                    )

    def test_exact_final_after_shared_schema_accepts_all_producer_shapes(
        self,
    ) -> None:
        for domain in ("flags", "engine_special_flags", "trainers"):
            with self.subTest(domain=domain):
                self.assertIs(
                    _validate_effect_exact_final_after({
                        "domain": domain, "relation": "EXACT_FINAL",
                        "after": True,
                    }, "test effect"),
                    True,
                )
        for value in (0, 0xFFFF):
            with self.subTest(domain="vars", value=value):
                self.assertEqual(
                    _validate_effect_exact_final_after({
                        "domain": "vars", "relation": "EXACT_FINAL",
                        "after": value,
                    }, "test effect"),
                    value,
                )
        for value in (-1, 0x10000, False, "0"):
            with self.subTest(domain="vars", invalid=value), \
                    self.assertRaisesRegex(
                        Stage61InteractionOracleError,
                        "EXACT_FINAL after u16不正",
                    ):
                _validate_effect_exact_final_after({
                    "domain": "vars", "relation": "EXACT_FINAL",
                    "after": value,
                }, "test effect")

    def test_source_producer_rejects_its_enriched_second_projection(
        self,
    ) -> None:
        rom, manifest, runtime, objects, events = self._fixture()
        first = build_effect_source_registry(
            rom, manifest, {}, runtime_control=runtime,
            final_object_cases=objects, event_runtime_cases=events,
            runner_fixtures={},
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "ordered_effects",
        ):
            build_effect_source_registry(
                rom, manifest, {},
                runtime_control=first["updated_runtime_control"],
                final_object_cases=first["updated_final_object_cases"],
                event_runtime_cases=first["updated_event_runtime_cases"],
                runner_fixtures={},
            )

    def test_source_case_template_instance_and_preimage_tamper_fail_closed(
        self,
    ) -> None:
        rom, manifest, runtime, objects, events = self._fixture()
        result = build_effect_source_registry(
            rom, manifest, {}, runtime_control=runtime,
            final_object_cases=objects, event_runtime_cases=events,
            runner_fixtures={},
        )
        instance = next(
            row for row in result["effect_instances"]
            if row["occurrence_kind"] == "EFFECT_MEMBER"
        )
        template = next(
            row for row in result["effect_templates"]
            if row["template_id"] == instance["template_id"]
        )
        case = deepcopy(result["case_contracts"][instance["case_id"]])
        case["input_sequence"]["effect_contract"]["required_final"][
            "flags"
        ][0]["value"] = False
        case_tamper = deepcopy(instance)
        case_tamper["fixture_binding"] = \
            build_effect_case_initialization_binding(case, {})
        case_tamper = _seal_effect_instance(case_tamper)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "lifecycle source hash",
        ):
            validate_effect_instance(
                case_tamper, template=template, case_contract=case,
                runner_fixtures={}, stage61_rom=rom,
            )

        template_tamper = deepcopy(template)
        template_tamper["transition_oracle"]["source_contracts"][0][
            "required_postconditions_sha256"
        ] = "0" * 64
        template_tamper = _seal_effect_template(template_tamper)
        template_instance = deepcopy(instance)
        template_instance["template_id"] = template_tamper["template_id"]
        template_instance = _seal_effect_instance(template_instance)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "lifecycle source hash",
        ):
            validate_effect_instance(
                template_instance, template=template_tamper,
                case_contract=result["case_contracts"][instance["case_id"]],
                runner_fixtures={}, stage61_rom=rom,
            )

        expected_tamper = deepcopy(instance)
        expected_tamper["expected_contract"]["observer_contract"][
            "extra_calls_forbidden"
        ] = False
        expected_tamper = _seal_effect_instance(expected_tamper)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "independent oracle",
        ):
            validate_effect_instance(
                expected_tamper, template=template,
                case_contract=result["case_contracts"][instance["case_id"]],
                runner_fixtures={}, stage61_rom=rom,
            )

        preimage_tamper = deepcopy(instance)
        preimage_tamper["pre_images"] = [{
            "range_id": "effect-watch-" + "a" * 64,
            "size": 1, "hex": "00",
            "sha256": hashlib.sha256(b"\x00").hexdigest(),
            "source_binding": {
                "kind": "CASE_JSON_POINTER", "json_pointer": "/unused",
                "encoding": "LOWER_HEX", "byte_offset": 0,
            },
        }]
        preimage_tamper = _seal_effect_instance(preimage_tamper)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "pre_images",
        ):
            validate_effect_instance(
                preimage_tamper, template=template,
                case_contract=result["case_contracts"][instance["case_id"]],
                runner_fixtures={}, stage61_rom=rom,
            )

    def test_object_virtual_helper_requires_one_sequence_one_signature(self) -> None:
        first = "effect-" + "1" * 24
        second = "effect-" + "2" * 24
        source = {
            "case_id": "object-two", "interaction_expected": True,
            "runtime_control_assignment": {
                "effect_signature_ids": [first, second],
            },
            "input_sequences": [{
                "sequence_id": "first", "basis": {
                    "effect_signature_id": first,
                },
            }, {
                "sequence_id": "second", "basis": {
                    "effect_signature_id": second,
                },
            }],
        }
        projected = object_effect_sequence_case_contracts(source)
        self.assertEqual(
            [row["runtime_control_assignment"]["effect_signature_ids"]
             for row in projected],
            [[first], [second]],
        )
        broken = deepcopy(source)
        broken["input_sequences"][1]["basis"]["effect_signature_id"] = first
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "source/sequence signature closure",
        ):
            object_effect_sequence_case_contracts(broken)

        _, _, _, _, events = self._fixture()
        broken_map = deepcopy(events[0])
        map_first = broken_map["input_sequences"][0][
            "effect_signature_ids"
        ][0]
        map_second = "effect-" + "3" * 24
        broken_map["effect_signature_ids"] = sorted([
            map_first, map_second,
        ])
        broken_map["input_sequences"][0]["effect_signature_ids"] = [
            map_first, map_second,
        ]
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "複数signature",
        ):
            map_effect_sequence_case_contracts(broken_map)

    def test_effect_source_projection_rejects_every_second_projection(
        self,
    ) -> None:
        _rom, _manifest, _runtime, objects, events = self._fixture()
        projected_object = object_effect_sequence_case_contracts(objects[0])[0]
        projected_map = map_effect_sequence_case_contracts(events[0])[0]
        projected_event = effect_source_event_case_contracts(events[1])[0]
        for label, helper, row in (
            ("OBJECT", object_effect_sequence_case_contracts,
             projected_object),
            ("MAP", map_effect_sequence_case_contracts, projected_map),
            ("EVENT", effect_source_event_case_contracts, projected_event),
        ):
            with self.subTest(label=label), self.assertRaises(
                Stage61InteractionOracleError
            ):
                helper(row)

def _engine_teleport_trigger_fixture(
    stage61_rom: bytes,
) -> tuple[bytes, dict, dict]:
    """Build a byte-bound MAP tag-3 path for provenance schema tests."""

    rom = bytearray(stage61_rom)
    record = 0x09FFFF00
    root = 0x09FFFF10
    rom[record - 0x08000000] = 3
    final_rom = bytes(rom)
    owner = {
        "owner_id": "MAP:001/002:000:DIRECT",
        "owner_kind": "MAP",
        "group": 1,
        "map": 2,
        "root_subkind": "DIRECT",
        "record_address": record,
        "root": root,
    }
    block_address = 0x08000000
    block_raw = final_rom[:2]
    path = {
        "kind": "MAP_TRANSITION_LOAD",
        "group": 1,
        "map": 2,
        "root_subkind": "DIRECT",
        "map_script_tag": 3,
        "entry": (
            "STOCK_WARP_OR_CONNECTION_OR_ENGINE_TELEPORT_OR_RESUME_CALLBACK"
        ),
        "root_pc": root,
        "engine_teleport": {
            "kind": "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
            "destination": {"group": 1, "map": 2},
            "start_tile": {"x": 4, "y": 5},
            "engine_entry": "BOOTSTRAP_KANTO_WARP",
            "source_provenance": {
                "kind": (
                    "FINAL_ROM_GEOMETRY_BOUND_ENGINE_PLAYER_TELEPORT_MAP_LOAD"
                ),
                "rom_sha256": hashlib.sha256(final_rom).hexdigest(),
                "layout_address": "0x08000004",
                "block_address": f"0x{block_address:08X}",
                "block_raw_hex": block_raw.hex(),
                "block_raw_sha256": hashlib.sha256(block_raw).hexdigest(),
                "base_collision": 0,
                "base_elevation": 0,
                "foreign_stock_warp_scan": {
                    "destination": [1, 2],
                    "foreign_warp_reference_count": 1,
                    "usable_stock_warp_count": 0,
                    "invalid_source_warp_view_count": 0,
                    "unusable_reason_counts": {
                        "NO_FREE_CARDINAL_PREDECESSOR": 1,
                    },
                },
                "usable_stock_connection_count": 0,
                "incoming_usable_zero_reason_bound": True,
                "first_root_hit_map_identity_required": True,
                "settled_map_identity_not_substituted_for_first_root_hit": True,
                "direct_root_call_forbidden": True,
                "direct_callback_call_forbidden": True,
            },
        },
    }
    return final_rom, owner, path


class Stage61RepeatingMenuExecutorTests(unittest.TestCase):
    @staticmethod
    def _contracted_vending_fixture(
        *, exit_reenters: bool = False,
    ) -> tuple[_Context, list[tuple[int, int, bytes]]]:
        """One concrete purchase returns to its exact menu, then exits by B."""

        root = 0x08000000
        exit_pc = root + 59
        script = b"".join((
            bytes.fromhex("710000000100"),  # one item and an actual B path
            bytes.fromhex("210d807f00"),
            bytes((0x06, 0x01)) + exit_pc.to_bytes(4, "little"),
            bytes.fromhex("1604800100"),  # VAR_8004 = ITEM_MASTER_BALL
            bytes.fromhex("1605800100"),  # VAR_8005 = quantity 1
            bytes.fromhex("4404800580"),  # real additem success/failure
            bytes.fromhex("210d800100"),
            bytes((0x06, 0x01)) + (root + 48).to_bytes(4, "little"),
            bytes((0x05,)) + root.to_bytes(4, "little"),
            bytes.fromhex("91c800000000"),  # real money -200 effect
            bytes((0x05,)) + root.to_bytes(4, "little"),
            (
                bytes((0x05,)) + root.to_bytes(4, "little")
                if exit_reenters else bytes((0x02,))
            ),
        ))
        rom = script + bytes(0x200 - len(script))
        raw = bytes.fromhex("710000000100")
        effect_policy = {
            "persistent_or_external_write": True,
            "mutable_domains": ["money", "bag", "item_scratch"],
            "executor_policy": (
                "ONE_TRANSACTION_PER_ITEM_AND_BOUNDARY_FIXTURE_THEN_EXIT"
            ),
        }
        site = {
            "address": f"0x{root:08X}", "opcode": "0x71",
            "raw_hex": raw.hex(),
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "role": "DECISION_PRODUCER",
            "site_kind": "EVENT_MENU", "menu_id": 0,
            "result_policy": {
                "candidate_domain": {"kind": "FIXED", "values": [0, 127]},
                "result_variable": "VAR_RESULT",
                "result_classes": {
                    "looping": [0], "terminal": [127],
                    "state_conditional": [],
                },
            },
            "real_exit": {
                "input": "B", "result": 127,
                "proof": "IGNORE_B_FALSE_AND_CANCEL_BRANCH_LEAVES_SCC",
            },
        }
        contract = {
            "schema_version": 1,
            "kind": "STAGE61_BOUND_CYCLIC_DECISION_ROOT_CONTRACT",
            "contract_sha256": "a" * 64,
            "event_owner_inventory_sha256": "b" * 64,
            "target_root": f"0x{root:08X}",
            "execution_root": f"0x{root:08X}",
            "contract_owner_ids": ["BG:010/005:001"],
            "bound_owner_ids": ["BG:010/005:001"],
            "classification": "EXPLICIT_TRANSACTION",
            "loop_family": "VENDING_MACHINE",
            "effect_policy": effect_policy,
            "executor_state_key": [
                "scc_id", "decision_pc", "call_stack_return_pcs",
                "loop_carried_control_abstraction",
            ],
            "relocation_binding": None,
            "sites": [{
                "scc_id": "cyclic-scc-vending-test",
                "scc_instruction_binding_sha256": "c" * 64,
                "decision_pc": f"0x{root:08X}",
                "decision_site": site,
            }],
        }
        context = _Context(
            clean_rom=rom, stage61_rom=rom, semantic_report={},
            npc={"npc_id": "BG:010/005:001", "local_id": 0},
            case={
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "expected_object_visible": True,
            },
            root=root, target_root=root, execution_root=root, root_plan={},
            fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
            text_assets={}, text_provenance="SYNTHETIC_SOURCE_RAW",
            abi_index={}, instruction_repairs={},
            source_suppression_contract=None,
            stage61_script_bytes=frozenset(range(root, root + len(script))),
            cyclic_decision_contract=contract,
        )
        rows = [(root + 0x180, root + 0x180, b"\xA1\xFF")]
        return context, rows

    def test_contracted_vending_keeps_purchase_effects_then_executes_real_b(
        self,
    ) -> None:
        context, rows = self._contracted_vending_fixture()
        with patch(
            "tools.stage61_interaction_oracle._multichoice_rows",
            return_value=rows,
        ), patch(
            "tools.stage61_interaction_oracle._printer_engine_binding",
            side_effect=_synthetic_printer_engine_binding,
        ):
            states = _execute(context)
        purchased = [state for state in states if any(
            effect["domain"] == "items" for effect in state.effects
        )]
        self.assertEqual(len(purchased), 1)
        state = purchased[0]
        self.assertEqual(state.tokens[-1], "B")
        self.assertTrue(state.terminated)
        self.assertEqual(
            {effect["domain"] for effect in state.effects} & {"items", "money"},
            {"items", "money"},
        )
        self.assertEqual(len(state.cyclic_quotient_evidence), 1)
        evidence = state.cyclic_quotient_evidence[0]
        self.assertEqual(evidence["decision_pc"], "0x08000000")
        self.assertEqual(
            evidence["real_exit_execution"]["input"], "B",
        )
        self.assertEqual(
            evidence["real_exit_execution"]["result"], 127,
        )
        self.assertEqual(
            {effect["domain"] for effect in
             evidence["one_cycle_witness"]["effects"]}
            & {"items", "money"},
            {"items", "money"},
        )
        self.assertTrue(all(evidence["assertions"].values()))

    def test_product_vending_contract_keeps_each_real_purchase_then_b_exit(
        self,
    ) -> None:
        from tools.stage61_cyclic_decision_contracts import (
            build_stage61_cyclic_decision_contracts,
            load_stage61_cyclic_decision_source_blobs,
        )
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph
        from tools.stage61_interaction_oracle import (
            _bind_cyclic_decision_root_contract,
            _validate_cyclic_decision_contract_input,
        )

        clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        project = (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes()
        stage61 = (ROOT / "build/stages/61_display_npc_event_audit.gba").read_bytes()
        semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        document = build_stage61_cyclic_decision_contracts(
            stage61,
            inventory,
            load_stage61_cyclic_decision_source_blobs(ROOT),
        )
        index = _validate_cyclic_decision_contract_input(
            document,
            stage61,
            expected_event_owner_inventory_sha256=inventory["inventory_sha256"],
        )
        root = 0x0818428D
        owners = sorted(
            (
                row for row in inventory["owners"]
                if row.get("runtime_root") is True and row.get("root") == root
            ),
            key=lambda row: row["owner_id"],
        )
        binding = _bind_cyclic_decision_root_contract(
            index,
            semantic,
            owner_ids=[row["owner_id"] for row in owners],
            target_root=root,
            execution_root=root,
            require_exact_owner_set=True,
        )
        graph = SemanticScriptGraph(stage61)
        graph.walk([root])
        self.assertEqual(graph.diagnostics, [])
        executions, blockers = _runtime_execute_with_seed_discovery(
            clean,
            project,
            stage61,
            semantic,
            owners[0],
            graph,
            {},
            {},
            {},
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, root),
            cyclic_decision_contract=binding,
        )
        self.assertEqual(blockers, [])
        purchased = [
            state for _context, state in executions
            if state.cyclic_quotient_evidence
            and any(effect["domain"] == "items" for effect in state.effects)
        ]
        self.assertEqual(len(purchased), 3)
        self.assertEqual(
            {
                effect["owner"] for state in purchased
                for effect in state.effects if effect["domain"] == "items"
            },
            {"BAG_ITEM:26", "BAG_ITEM:27", "BAG_ITEM:28"},
        )
        for state in purchased:
            self.assertEqual(
                [row["result_value"] for row in state.decisions][-1],
                127,
            )
            evidence = state.cyclic_quotient_evidence[0]
            self.assertEqual(evidence["real_exit_execution"]["input"], "B")
            self.assertEqual(
                {effect["domain"] for effect in
                 evidence["one_cycle_witness"]["effects"]}
                & {"items", "money"},
                {"items", "money"},
            )

    def test_product_berry_vendor_correlates_amount_and_executes_real_exit(
        self,
    ) -> None:
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        from tools.stage61_cyclic_decision_contracts import (
            build_stage61_cyclic_decision_contracts,
            load_stage61_cyclic_decision_source_blobs,
        )
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph
        from tools.stage61_interaction_oracle import (
            _bind_cyclic_decision_root_contract,
            _validate_cyclic_decision_contract_input,
        )

        clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        project = (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes()
        stage61 = (ROOT / "build/stages/61_display_npc_event_audit.gba").read_bytes()
        semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        repair = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text())
        inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        source_blobs, _reports = _interaction_abi_pinned_inputs()
        rows = []
        for raw_entry in manifest["special_abis"]:
            if raw_entry["special_id"] not in {344, 412, 413, 414, 415, 416}:
                continue
            entry = deepcopy(raw_entry)
            if entry["special_id"] in {412, 413, 414, 415, 416}:
                entry.update(_special_semantic_contract(
                    entry["special_id"], entry["symbol"],
                ))
            rows.append(entry)
        abi_index = _interaction_abi_index(
            stage61, {"special_abis": rows, "native_abis": []},
            source_blobs=source_blobs,
        )

        root = 0x08181542
        owner = next(
            row for row in inventory["owners"]
            if row["owner_id"] == "OBJECT:007/009:000"
        )
        document = build_stage61_cyclic_decision_contracts(
            stage61, inventory,
            load_stage61_cyclic_decision_source_blobs(ROOT),
        )
        cyclic_index = _validate_cyclic_decision_contract_input(
            document, stage61,
            expected_event_owner_inventory_sha256=inventory["inventory_sha256"],
        )
        binding = _bind_cyclic_decision_root_contract(
            cyclic_index, semantic, owner_ids=[owner["owner_id"]],
            target_root=root, execution_root=root,
            require_exact_owner_set=True,
        )
        graph = SemanticScriptGraph(stage61)
        graph.walk([root])
        self.assertEqual(graph.diagnostics, [])
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(source_blobs[builder_path]).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        text_assets, _provenance = _independent_runtime_text_assets(
            clean, project, stage61, semantic, repair, graph,
            source_blobs=source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            clean, project, stage61, semantic, owner, graph,
            text_assets, abi_index, source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, root),
            cyclic_decision_contract=binding,
        )
        self.assertEqual(blockers, [])
        self.assertTrue(executions)
        self.assertLess(len(executions), MAX_EXECUTION_PATHS)
        self.assertTrue(all(state.terminated for _context, state in executions))
        berry_states = [
            state for _context, state in executions
            if state.berry_powder_initial is not None
        ]
        self.assertTrue(berry_states)
        self.assertTrue(all(
            len([
                row for row in state.abi_control_reads
                if row.get("kind") == "BERRY_POWDER"
            ]) == 1
            for state in berry_states
        ))
        self.assertEqual({
            row["required_value"]
            for state in berry_states
            for row in state.abi_control_reads
            if row.get("kind") == "BERRY_POWDER"
        }, {49, 50, 79, 80, 299, 300, 999, 1000, 2999, 3000})
        purchased = [
            (context, state) for context, state in executions
            if any(
                effect.get("domain") == "berry_powder"
                and effect.get("success") is True
                for effect in state.effects
            )
        ]
        insufficient = [
            (context, state) for context, state in executions
            if any(
                decision.get("kind") == "BERRY_POWDER_HAS_ENOUGH_EXACT"
                and decision.get("result_value") == 0
                for decision in state.decisions
            )
        ]
        self.assertTrue(purchased)
        self.assertTrue(insufficient)
        revisited_purchased = [
            (context, state) for context, state in purchased
            if state.cyclic_quotient_evidence
        ]
        self.assertTrue(revisited_purchased)
        self.assertTrue(all(
            state.cyclic_quotient_evidence
            and state.cyclic_quotient_evidence[0]["real_exit_execution"][
                "input"
            ] == "B"
            and state.cyclic_quotient_evidence[0]["real_exit_execution"][
                "result"
            ] == 127
            for _context, state in [*revisited_purchased, *insufficient]
        ))
        self.assertTrue(all(
            any(
                effect.get("domain") == "berry_powder"
                and effect.get("success") is True
                for effect in state.cyclic_quotient_evidence[0][
                    "one_cycle_witness"
                ]["effects"]
            )
            for _context, state in revisited_purchased
        ))
        self.assertTrue(all(
            _runner_required_postconditions(context, state)["berry_powder"]
            == state.berry_powder_current
            for context, state in purchased
        ))
        self.assertTrue(all(
            _runner_required_postconditions(context, state)["berry_powder"]
            is None
            for context, state in insufficient
        ))
        self.assertFalse(any(
            effect.get("domain") == "berry_powder"
            for _context, state in insufficient for effect in state.effects
        ))

        site_pc = 0x081815C5
        site_raw = stage61[
            site_pc - 0x08000000:site_pc - 0x08000000 + 3
        ]
        probe_context = berry_states and next(
            context for context, state in executions
            if state.berry_powder_initial is not None
        )
        self.assertTrue(any(
            any(
                left == 0x0818157E and right == 0x08193F49
                for left, right in zip(
                    state.execution_trace, state.execution_trace[1:],
                )
            )
            for _context, state in executions
        ))
        common_caller_binding = {
            "kind": "PHYSICAL_CALLER_PREFIX_THEN_EXACT_STANDARD_ROOT",
            "declared_root": 0x08193F49,
            "execution_root": root,
            "caller_owner_id": probe_context.npc["npc_id"],
            "standard_dispatch_proven_by_exact_table_entry": True,
            "direct_common_root_execution_forbidden": True,
        }
        common_context = replace(
            probe_context,
            target_root=0x08193F49,
            common_caller_binding=common_caller_binding,
        )
        self.assertIsNotNone(
            _cyclic_menu_site_binding(
                common_context, site_pc, 0x25, site_raw,
            )
        )
        drifted_common_caller_binding = deepcopy(common_caller_binding)
        drifted_common_caller_binding["declared_root"] = 0x08193F4A
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "CYCLIC_DECISION_COMMON_CALLER_BINDING_MISMATCH",
        ):
            _cyclic_menu_site_binding(
                replace(
                    common_context,
                    common_caller_binding=drifted_common_caller_binding,
                ),
                site_pc,
                0x25,
                site_raw,
            )
        menu_type = next(
            decision["menu_type"]
            for state in berry_states for decision in state.decisions
            if decision.get("instruction_address") == f"0x{site_pc:08X}"
            and decision.get("kind") in {
                "PINNED_LIST_MENU", "PINNED_LIST_MENU_CANCEL",
            }
        )
        probe = _Execution(
            pc=site_pc, vars={0x8004: menu_type},
            execution_trace=[site_pc],
            current_instruction_address=site_pc, current_opcode=0x25,
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "BERRY_TRANSACTION_CYCLIC_CONTRACT_REQUIRED",
        ):
            _fork_abi_command(
                replace(probe_context, cyclic_decision_contract=None),
                probe.clone(), site_pc, 0x25, site_raw,
            )
        drifted_binding = deepcopy(binding)
        drifted_binding["sites"][0]["decision_site"][
            "special_table_binding"
        ]["target"] = "0x081622B1"
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "CYCLIC_DECISION_INTERACTIVE_SPECIAL_BINDING_MISMATCH",
        ):
            _fork_abi_command(
                replace(
                    probe_context,
                    cyclic_decision_contract=drifted_binding,
                ),
                probe.clone(), site_pc, 0x25, site_raw,
            )

    def test_product_seagallop_pages_use_one_cycle_then_actual_b_exit(
        self,
    ) -> None:
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        from tools.stage61_cyclic_decision_contracts import (
            Stage61CyclicDecisionContractError,
            build_stage61_cyclic_decision_contracts,
            load_stage61_cyclic_decision_source_blobs,
        )
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph
        from tools.stage61_interaction_oracle import (
            _bind_cyclic_decision_root_contract,
            _validate_cyclic_decision_contract_input,
        )

        clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        project = (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes()
        stage61 = (ROOT / "build/stages/61_display_npc_event_audit.gba").read_bytes()
        semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        repair = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text())
        inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        source_blobs, _reports = _interaction_abi_pinned_inputs()
        special_ids = {379, 391, 392, 423, 424, 425, 429}
        rows = []
        for raw_entry in manifest["special_abis"]:
            if raw_entry["special_id"] not in special_ids:
                continue
            entry = deepcopy(raw_entry)
            entry.update(_special_semantic_contract(
                entry["special_id"], entry["symbol"],
            ))
            rows.append(entry)
        self.assertEqual({row["special_id"] for row in rows}, special_ids)
        abi_index = _interaction_abi_index(
            stage61, {"special_abis": rows, "native_abis": []},
            source_blobs=source_blobs,
        )

        root = 0x0818F658
        owner_id = "OBJECT:031/006:001"
        owner = next(
            row for row in inventory["owners"]
            if row["owner_id"] == owner_id
        )
        self.assertEqual(owner["root"], root)
        cyclic_sources = load_stage61_cyclic_decision_source_blobs(ROOT)
        document = build_stage61_cyclic_decision_contracts(
            stage61, inventory, cyclic_sources,
        )
        cyclic_index = _validate_cyclic_decision_contract_input(
            document, stage61,
            expected_event_owner_inventory_sha256=inventory["inventory_sha256"],
        )
        binding = _bind_cyclic_decision_root_contract(
            cyclic_index, semantic, owner_ids=[owner_id],
            target_root=root, execution_root=root,
            require_exact_owner_set=True,
        )
        self.assertEqual(binding["classification"], "PURE")
        self.assertEqual(binding["loop_family"], "SEAGALLOP_PAGES")
        self.assertEqual(
            {row["decision_pc"] for row in binding["sites"]},
            {"0x081966C8", "0x08196729"},
        )

        graph = SemanticScriptGraph(stage61)
        graph.walk([root])
        self.assertEqual(graph.diagnostics, [])
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(source_blobs[builder_path]).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        text_assets, _provenance = _independent_runtime_text_assets(
            clean, project, stage61, semantic, repair, graph,
            source_blobs=source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            clean, project, stage61, semantic, owner, graph,
            text_assets, abi_index, source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, root),
            cyclic_decision_contract=binding,
        )
        self.assertEqual(blockers, [])
        self.assertTrue(executions)
        self.assertLess(len(executions), MAX_EXECUTION_PATHS)
        self.assertTrue(all(state.terminated for _context, state in executions))
        states = [state for _context, state in executions]
        menu_decisions = [
            decision for state in states for decision in state.decisions
            if decision.get("kind") == "SEAGALLOP_DESTINATION_MENU"
        ]
        self.assertEqual(
            {decision["instruction_address"] for decision in menu_decisions},
            {"0x081966C8", "0x08196729"},
        )
        self.assertEqual(
            {decision["result_value"] for decision in menu_decisions},
            {0, 1, 2, 3, 4, 5, 6, 127, 254},
        )
        transforms = [
            decision for state in states for decision in state.decisions
            if decision.get("kind") == "SEAGALLOP_DESTINATION_RESULT_TRANSFORM"
        ]
        self.assertTrue(transforms)
        self.assertTrue(all(
            decision["result_value"] == _seagallop_destination_result(
                decision["starting_destination"], decision["page"],
                decision["raw_result_value"],
            )
            for decision in transforms
        ))

        quotient_states = [
            state for state in states if state.cyclic_quotient_evidence
        ]
        self.assertTrue(quotient_states)
        for state in quotient_states:
            evidence = state.cyclic_quotient_evidence[0]
            self.assertEqual(evidence["initial_choice"]["result_value"], 254)
            self.assertEqual(evidence["real_exit_execution"]["input"], "B")
            self.assertEqual(evidence["real_exit_execution"]["result"], 127)
            self.assertEqual(state.tokens[-1], "B")
            self.assertTrue(all(evidence["assertions"].values()))
            self.assertTrue({"0x081966C8", "0x08196729"} <= set(
                evidence["one_cycle_witness"]["instruction_addresses"]
            ))
            self.assertTrue(any(
                effect.get("domain") == "ui"
                and effect.get("relation") == "OPEN_SELECT_AND_CLOSE_EXACT"
                for effect in evidence["one_cycle_witness"]["effects"]
            ))
        expected, expected_sccs, expected_sites, consumed, consumed_sccs, \
            consumed_sites = _cyclic_event_menu_quotient_identity_sets(
                [binding], [
                    evidence for state in states
                    for evidence in state.cyclic_quotient_evidence
                ],
            )
        self.assertEqual(consumed, expected)
        self.assertEqual(consumed_sccs, expected_sccs)
        self.assertEqual(consumed_sites, expected_sites)
        self.assertFalse(any(
            row.get("kind") == "VAR" and row.get("owner") == "VAR:0x800D"
            for state in states for row in state.abi_control_reads
        ))
        player_side = [
            decision for state in states for decision in state.decisions
            if decision.get("kind") ==
                "IS_PLAYER_LEFT_OF_VERMILION_SAILOR_EXACT"
        ]
        self.assertTrue(player_side)
        self.assertEqual(
            {decision["result_value"] for decision in player_side}, {0},
        )
        self.assertTrue(all(
            decision["physical_map"] == {"group": 31, "map": 6}
            and decision["player_x"] is None
            for decision in player_side
        ))

        probe_context, _probe_state = next(
            (context, state) for context, state in executions
            if 0x081966C8 in state.execution_trace
        )
        site_pc = 0x081966C8
        site_raw = stage61[
            site_pc - 0x08000000:site_pc - 0x08000000 + 3
        ]
        probe = _Execution(
            pc=site_pc, vars={0x8004: 7, 0x8005: 0},
            execution_trace=[site_pc],
            current_instruction_address=site_pc, current_opcode=0x25,
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "SEAGALLOP_CYCLIC_CONTRACT_REQUIRED:0x081966C8",
        ):
            _fork_abi_command(
                replace(probe_context, cyclic_decision_contract=None),
                probe.clone(), site_pc, 0x25, site_raw,
            )
        drifted_binding = deepcopy(binding)
        drifted_binding["sites"][0]["decision_site"][
            "special_table_binding"
        ]["target"] = "0x0809D2FD"
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "CYCLIC_DECISION_INTERACTIVE_SPECIAL_BINDING_MISMATCH",
        ):
            _fork_abi_command(
                replace(
                    probe_context,
                    cyclic_decision_contract=drifted_binding,
                ),
                probe.clone(), site_pc, 0x25, site_raw,
            )

        source_drift = dict(cyclic_sources)
        source_drift["vendor/upstream/pokefirered/src/script_menu.c"] += b"\n"
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "SOURCE_BYTE_DRIFT:vendor/upstream/pokefirered/src/script_menu.c",
        ):
            build_stage61_cyclic_decision_contracts(
                stage61, inventory, source_drift,
            )
        rom_drift = bytearray(stage61)
        rom_drift[site_pc - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61CyclicDecisionContractError,
            "DECISION_SITE_BYTE_DRIFT:0x081966C8",
        ):
            build_stage61_cyclic_decision_contracts(
                bytes(rom_drift), inventory, cyclic_sources,
            )

    def test_product_celio_forced_accept_uses_one_no_witness_then_actual_yes(
        self,
    ) -> None:
        from scripts import run_stage61_mgba_validation as runner
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        from tools.stage61_cyclic_decision_contracts import (
            build_stage61_cyclic_decision_contracts,
            load_stage61_cyclic_decision_source_blobs,
        )
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph
        from tools.stage61_interaction_oracle import (
            _bind_cyclic_decision_root_contract,
            _cyclic_quotient_real_exit_execution_valid,
            _flat_result_internal_controls,
            _fork_yes_no,
            _runtime_case_internal_controls,
            _validate_cyclic_decision_contract_input,
            _validate_runner_flat_internal_controls,
        )

        clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        project = (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes()
        stage61 = (ROOT / "build/stages/61_display_npc_event_audit.gba").read_bytes()
        semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        repair = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text())
        inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        source_blobs, _reports = _interaction_abi_pinned_inputs()
        special_ids = {142, 297, 371, 403, 410}
        rows = []
        for raw_entry in manifest["special_abis"]:
            if raw_entry["special_id"] not in special_ids:
                continue
            entry = deepcopy(raw_entry)
            entry.update(_special_semantic_contract(
                entry["special_id"], entry["symbol"],
            ))
            rows.append(entry)
        self.assertEqual({row["special_id"] for row in rows}, special_ids)
        abi_index = _interaction_abi_index(
            stage61, {"special_abis": rows, "native_abis": []},
            source_blobs=source_blobs,
        )

        root = 0x0818F938
        owner_id = "OBJECT:032/000:002"
        owner = next(
            row for row in inventory["owners"]
            if row["owner_id"] == owner_id
        )
        self.assertEqual(owner["root"], root)
        cyclic_sources = load_stage61_cyclic_decision_source_blobs(ROOT)
        document = build_stage61_cyclic_decision_contracts(
            stage61, inventory, cyclic_sources,
        )
        cyclic_index = _validate_cyclic_decision_contract_input(
            document, stage61,
            expected_event_owner_inventory_sha256=inventory["inventory_sha256"],
        )
        binding = _bind_cyclic_decision_root_contract(
            cyclic_index, semantic, owner_ids=[owner_id],
            target_root=root, execution_root=root,
            require_exact_owner_set=True,
        )
        self.assertEqual(binding["classification"], "PURE")
        self.assertEqual(binding["loop_family"], "FORCED_ACCEPT_PROMPT")
        self.assertEqual(
            [row["decision_pc"] for row in binding["sites"]],
            ["0x0818FB12"],
        )
        site = binding["sites"][0]["decision_site"]
        self.assertEqual(site["site_kind"], "STANDARD_YES_NO")
        self.assertEqual(site["result_policy"]["result_classes"], {
            "looping": [0], "terminal": [1], "state_conditional": [],
        })
        self.assertEqual(site["real_exit"], {
            "input": "A", "result": 1,
            "proof": "YES_BRANCH_LEAVES_FORCED_ACCEPT_SCC",
        })

        graph = SemanticScriptGraph(stage61)
        graph.walk([root])
        self.assertEqual(graph.diagnostics, [])
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(source_blobs[builder_path]).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        text_assets, _provenance = _independent_runtime_text_assets(
            clean, project, stage61, semantic, repair, graph,
            source_blobs=source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            clean, project, stage61, semantic, owner, graph,
            text_assets, abi_index, source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, root),
            cyclic_decision_contract=binding,
        )
        self.assertEqual(blockers, [])
        self.assertTrue(executions)
        self.assertLess(len(executions), MAX_EXECUTION_PATHS)
        self.assertTrue(all(state.terminated for _context, state in executions))
        states = [state for _context, state in executions]

        prompt_callers = {"0x0818FAF9", "0x0818FB12"}

        def prompt_history(state: _Execution) -> tuple[tuple[str, int], ...]:
            return tuple(
                (decision["caller_instruction_address"],
                 decision["result_value"])
                for decision in state.decisions
                if decision.get("kind") == "YES_NO"
                and decision.get("caller_instruction_address") in prompt_callers
            )

        expected_histories = {
            (("0x0818FAF9", 1),),
            (("0x0818FAF9", 0), ("0x0818FB12", 1)),
            (("0x0818FAF9", 0), ("0x0818FB12", 0),
             ("0x0818FB12", 1)),
        }
        prompt_states = [state for state in states if prompt_history(state)]
        self.assertTrue(prompt_states)
        self.assertEqual(
            {prompt_history(state) for state in prompt_states},
            expected_histories,
        )
        # The earlier GiveRuby callstd5 is the same standard implementation,
        # but it is not the retry SCC producer and must remain unquotiented.
        self.assertTrue(all(
            "producer_instruction_address" not in decision
            and "finite_scc_quotient" not in decision
            for state in prompt_states for decision in state.decisions
            if decision.get("kind") == "YES_NO"
            and decision.get("caller_instruction_address") == "0x0818FAF9"
        ))
        fb12_decisions = [
            decision for state in prompt_states for decision in state.decisions
            if decision.get("kind") == "YES_NO"
            and decision.get("caller_instruction_address") == "0x0818FB12"
        ]
        self.assertTrue(fb12_decisions)
        self.assertTrue(all(
            decision["producer_instruction_address"] == "0x0818FB12"
            and decision["instruction_address"] == "0x08192DB3"
            for decision in fb12_decisions
        ))

        quotient_paths = [
            (context, state) for context, state in executions
            if state.cyclic_quotient_evidence
        ]
        quotient_states = [state for _context, state in quotient_paths]
        self.assertTrue(quotient_states)
        self.assertEqual(
            {prompt_history(state) for state in quotient_states},
            {(("0x0818FAF9", 0), ("0x0818FB12", 0),
              ("0x0818FB12", 1))},
        )
        for state in quotient_states:
            self.assertEqual(len(state.cyclic_quotient_evidence), 1)
            evidence = state.cyclic_quotient_evidence[0]
            self.assertEqual(evidence["decision_pc"], "0x0818FB12")
            self.assertEqual(evidence["initial_choice"]["result_value"], 0)
            self.assertEqual(evidence["real_exit_execution"]["input"], "A")
            self.assertEqual(evidence["real_exit_execution"]["result"], 1)
            self.assertNotEqual(evidence["real_exit_execution"]["input"], "B")
            self.assertEqual(
                evidence["standard_yes_no_execution_binding"],
                {
                    "projected_decision_pc": "0x0818FB12",
                    "actual_command_pc": "0x08192DB3",
                    "standard_return_pc": "0x0818FB14",
                    "standard_id": 5,
                },
            )
            self.assertTrue({"0x0818FB12", "0x08192DB3"} <= set(
                evidence["one_cycle_witness"]["instruction_addresses"]
            ))
            self.assertTrue(_cyclic_quotient_real_exit_execution_valid(evidence))

        for context, state in quotient_paths:
            _external, materialized_internal = _runtime_control_rows(
                context, state, owner_keys=[owner_id], fixtures={},
            )
            materialized_captures = [
                row for row in materialized_internal
                if row["instruction_address"] == "0x0818FB14"
                and row["writer"] == "YES_NO"
            ]
            self.assertEqual(
                [(row["capture"]["expected_token_index"],
                  row["capture"]["expected_value"])
                 for row in materialized_captures],
                [(8, 0), (9, 1)],
            )
            internal = _flat_result_internal_controls(
                context, state, sequence_id="celio-forced-accept",
            )
            captures = [
                row for row in internal
                if row["instruction_address"] == "0x0818FB14"
                and row["writer"] == "YES_NO"
            ]
            self.assertEqual(
                [row["capture"]["expected_value"] for row in captures],
                [0, 1],
            )
            self.assertEqual(
                [row["capture"]["expected_token_index"] for row in captures],
                [8, 9],
            )
            self.assertEqual(
                [row["capture"]["expected_execution_ordinal"]
                 for row in captures],
                [0, 0],
            )
            self.assertTrue(all(
                row["capture"]["owner_address"] == "0x02037004"
                for row in captures
            ))
            contracts = [
                row["producer"]["ordered_runtime_capture"]
                for row in captures
            ]
            self.assertEqual(
                [contract["occurrence_index"] for contract in contracts],
                [0, 1],
            )
            self.assertTrue(all(
                contract["kind"] ==
                    "SAME_CONSUMER_DYNAMIC_OCCURRENCE_SEQUENCE"
                and contract["value_sequence"] == [0, 1]
                and contract["token_index_sequence"] == [8, 9]
                and contract["owner_address"] == "0x02037004"
                and contract["relation"] ==
                    "DECLINE_REENTERS_THEN_ACTUAL_YES_EXITS_EXACT"
                for contract in contracts
            ))
            _validate_runner_flat_internal_controls(
                internal,
                [{
                    "sequence_id": "celio-forced-accept",
                    "tokens": state.tokens,
                }],
                "celio root-local ordered capture",
            )

            runtime_tokens = ["DOWN", "A", *state.tokens]
            unscoped = _flat_result_internal_controls(context, state)
            scoped = _runtime_case_internal_controls(
                unscoped, sequence_id="celio-runtime-sequence",
                tokens=runtime_tokens, trigger_token_count=3,
            )
            scoped_captures = [
                row for row in scoped
                if row["instruction_address"] == "0x0818FB14"
                and row["writer"] == "YES_NO"
            ]
            self.assertEqual(
                [row["capture"]["expected_token_index"]
                 for row in scoped_captures],
                [10, 11],
            )
            self.assertTrue(all(
                row["producer"]["ordered_runtime_capture"][
                    "token_index_sequence"
                ] == [10, 11]
                for row in scoped_captures
            ))
            self.assertEqual(len({
                row["producer"]["ordered_runtime_capture"]["group_sha256"]
                for row in scoped_captures
            }), 1)
            runner_normalized = runner._normalize_internal_controls(
                scoped,
                [{
                    "sequence_id": "celio-runtime-sequence",
                    "tokens": runtime_tokens,
                }],
                "celio-runtime-sequence",
            )
            runner_captures = [
                row for row in runner_normalized
                if row["instruction_address"] == 0x0818FB14
                and row["writer"] == "YES_NO"
            ]
            self.assertEqual(
                [(row["capture"]["expected_token_index"],
                  row["capture"]["expected_value"])
                 for row in runner_captures],
                [(10, 0), (11, 1)],
            )

        expected, expected_sccs, expected_sites, consumed, consumed_sccs, \
            consumed_sites = _cyclic_event_menu_quotient_identity_sets(
                [binding], [
                    evidence for state in states
                    for evidence in state.cyclic_quotient_evidence
                ],
            )
        self.assertEqual(consumed, expected)
        self.assertEqual(consumed_sccs, expected_sccs)
        self.assertEqual(consumed_sites, expected_sites)

        transaction_effects = {
            ("items", "BAG_ITEM:373", "SUBTRACT_EXACT_QUANTITY"),
            ("items", "BAG_ITEM:367", "SUBTRACT_EXACT_QUANTITY"),
            ("items", "BAG_ITEM:368", "ADD_EXACT_QUANTITY"),
            ("vars", "VAR:0x4076", "EXACT_FINAL"),
            ("flags", "FLAG:0x0846", "EXACT_FINAL"),
        }
        transaction_states = [
            state for state in prompt_states
            if transaction_effects <= {
                (effect.get("domain"), effect.get("owner"),
                 effect.get("relation"))
                for effect in state.effects
            }
        ]
        self.assertTrue(transaction_states)
        self.assertEqual(
            {prompt_history(state) for state in transaction_states},
            expected_histories,
        )
        self.assertTrue(all(0x0818FB25 in state.execution_trace
                            for state in transaction_states))
        self.assertTrue(all(any(
            effect.get("owner") == "VAR:0x4076"
            and effect.get("after") == 5
            for effect in state.effects
        ) for state in transaction_states))
        self.assertTrue(all(any(
            effect.get("owner") == "FLAG:0x0846"
            and effect.get("after") is True
            for effect in state.effects
        ) for state in transaction_states))

        probe_context = next(
            context for context, state in executions
            if state.cyclic_quotient_evidence
        )
        ordered_state = quotient_states[0]
        result_writes = sorted(
            (
                write for write in ordered_state.var_writes
                if write["instruction_address"] == 0x08192DB3
            ),
            key=lambda write: write["execution_trace_index"],
        )
        self.assertGreaterEqual(len(result_writes), 3)
        self.assertEqual(
            [(write["token_index"], write["value"])
             for write in result_writes[-2:]],
            [(8, 0), (9, 1)],
        )
        duplicate_token = ordered_state.clone()
        duplicate_writes = sorted(
            (
                write for write in duplicate_token.var_writes
                if write["instruction_address"] == 0x08192DB3
            ),
            key=lambda write: write["execution_trace_index"],
        )
        duplicate_writes[-1]["token_index"] = \
            duplicate_writes[-2]["token_index"]
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "VAR_RESULT_RUNTIME_CAPTURE_OCCURRENCE_ORDER_CONFLICT:"
            "0x0818FB14:YES_NO",
        ):
            _flat_result_internal_controls(probe_context, duplicate_token)

        duplicate_write = ordered_state.clone()
        duplicated = next(
            write for write in duplicate_write.var_writes
            if write["instruction_address"] == 0x08192DB3
            and write["token_index"] == 9
        )
        duplicate_write.var_writes.append(deepcopy(duplicated))
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "VAR_RESULT_RUNTIME_WRITE_OCCURRENCE_CONFLICT:"
            "0x08192DB3",
        ):
            _flat_result_internal_controls(probe_context, duplicate_write)

        value_sequence_drift = ordered_state.clone()
        drifted_writes = sorted(
            (
                write for write in value_sequence_drift.var_writes
                if write["instruction_address"] == 0x08192DB3
            ),
            key=lambda write: write["execution_trace_index"],
        )
        drifted_writes[-1]["value"] = 0
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "VAR_RESULT_ORDERED_RUNTIME_CAPTURE_CONTRACT_REQUIRED:"
            "0x0818FB14:YES_NO",
        ):
            _flat_result_internal_controls(
                probe_context, value_sequence_drift,
            )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "VAR_RESULT_ORDERED_RUNTIME_CAPTURE_CONTRACT_REQUIRED:"
            "0x0818FB14:YES_NO",
        ):
            _flat_result_internal_controls(
                replace(probe_context, cyclic_decision_contract=None),
                ordered_state,
            )

        initial_yes_context, initial_yes_state = next(
            (context, state) for context, state in executions
            if prompt_history(state) == (("0x0818FAF9", 1),)
        )
        initial_yes_internal = _flat_result_internal_controls(
            initial_yes_context, initial_yes_state,
            sequence_id="celio-initial-yes",
        )
        self.assertTrue(initial_yes_internal)
        self.assertFalse(any(
            "ordered_runtime_capture" in row["producer"]
            for row in initial_yes_internal
        ))
        _validate_runner_flat_internal_controls(
            initial_yes_internal,
            [{
                "sequence_id": "celio-initial-yes",
                "tokens": initial_yes_state.tokens,
            }],
            "celio non-repeating consumer isolation",
        )

        actual_yes_no_pc = 0x08192DB3
        actual_yes_no_raw = stage61[
            actual_yes_no_pc - 0x08000000:
            actual_yes_no_pc - 0x08000000 + 3
        ]
        forced_probe = _Execution(
            pc=actual_yes_no_pc,
            stack=[(0x0818FB14, 0x0818FB12)],
            loaded_words={0: 0x08190419},
            execution_trace=[0x0818FB12, actual_yes_no_pc],
            current_instruction_address=actual_yes_no_pc,
            current_opcode=0x6E,
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "FORCED_ACCEPT_CYCLIC_CONTRACT_REQUIRED:0x0818FB12",
        ):
            _fork_yes_no(
                replace(probe_context, cyclic_decision_contract=None),
                forced_probe.clone(), actual_yes_no_pc, actual_yes_no_raw,
            )
        drifted_binding = deepcopy(binding)
        drifted_binding["sites"][0]["decision_site"][
            "standard_script_binding"
        ]["target"] = "0x08192DAF"
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "CYCLIC_DECISION_STANDARD_YES_NO_BINDING_MISMATCH",
        ):
            _fork_yes_no(
                replace(
                    probe_context,
                    cyclic_decision_contract=drifted_binding,
                ),
                forced_probe.clone(), actual_yes_no_pc, actual_yes_no_raw,
            )
        for drifted_context in (
            replace(probe_context, npc={**probe_context.npc,
                                        "npc_id": "OBJECT:032/000:999"}),
            replace(probe_context, target_root=0x0818FAF3),
        ):
            with self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "CYCLIC_DECISION_CONTEXT_BINDING_MISMATCH",
            ):
                _fork_yes_no(
                    drifted_context, forced_probe.clone(),
                    actual_yes_no_pc, actual_yes_no_raw,
                )

        # Prove that the other callstd5 site does not inherit the FB12 policy.
        initial_prompt_probe = _Execution(
            pc=actual_yes_no_pc,
            stack=[(0x0818FAFB, 0x0818FAF9)],
            loaded_words={0: 0x081903DF},
            execution_trace=[0x0818FAF9, actual_yes_no_pc],
            current_instruction_address=actual_yes_no_pc,
            current_opcode=0x6E,
        )
        initial_branches = _fork_yes_no(
            probe_context, initial_prompt_probe,
            actual_yes_no_pc, actual_yes_no_raw,
        )
        self.assertEqual(
            {branch.decisions[-1]["result_value"] for branch in initial_branches},
            {0, 1},
        )
        self.assertTrue(all(
            not branch.repeating_menu_checkpoints
            and not branch.cyclic_quotient_evidence
            and "producer_instruction_address" not in branch.decisions[-1]
            and "finite_scc_quotient" not in branch.decisions[-1]
            for branch in initial_branches
        ))
        decline = next(
            branch for branch in initial_branches
            if branch.decisions[-1]["result_value"] == 0
        )
        self.assertEqual(decline.tokens[-2:], ["DOWN", "A"])
        self.assertNotEqual(decline.tokens[-1], "B")

    def test_specialvar_non_result_destination_is_not_result_writer(
        self,
    ) -> None:
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )

        stage61 = (ROOT / "build/stages/61_display_npc_event_audit.gba").read_bytes()
        manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        source_blobs, _reports = _interaction_abi_pinned_inputs()
        rows = []
        for raw_entry in manifest["special_abis"]:
            if raw_entry["special_id"] not in {424, 429}:
                continue
            entry = deepcopy(raw_entry)
            entry.update(_special_semantic_contract(
                entry["special_id"], entry["symbol"],
            ))
            rows.append(entry)
        abi_index = _interaction_abi_index(
            stage61, {"special_abis": rows, "native_abis": []},
            source_blobs=source_blobs,
        )
        for pc in (0x081966CC, 0x0819672D):
            with self.subTest(non_result_destination=f"0x{pc:08X}"):
                raw = stage61[
                    pc - 0x08000000:pc - 0x08000000 + 5
                ]
                self.assertEqual(raw, bytes.fromhex("260680a801"))
                writer, blockers = _static_result_writer_descriptor(
                    stage61,
                    SimpleNamespace(opcode=0x26, raw=raw, address=pc),
                    abi_index=abi_index,
                )
                self.assertIsNone(writer)
                self.assertEqual(blockers, [])

        result_pc = 0x0819669B
        result_raw = stage61[
            result_pc - 0x08000000:result_pc - 0x08000000 + 5
        ]
        self.assertEqual(result_raw, bytes.fromhex("260d80ad01"))
        writer, blockers = _static_result_writer_descriptor(
            stage61,
            SimpleNamespace(
                opcode=0x26, raw=result_raw, address=result_pc,
            ),
            abi_index=abi_index,
        )
        self.assertEqual(blockers, [])
        self.assertEqual(writer["writer"],
                         "SPECIALVAR:IsPlayerLeftOfVermilionSailor")
        self.assertEqual(writer["destination_var"], 0x800D)
        self.assertEqual(writer["candidate_values"], [0, 1])

        base_context = _Context(
            clean_rom=stage61, stage61_rom=stage61, semantic_report={},
            npc={
                "npc_id": "OBJECT:031/006:001", "local_id": 1,
                "flag": 0, "group": 31, "map": 6,
            },
            case={
                "owner_key": "OBJECT:031/006:001",
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "interaction": {"group": 31, "map": 6},
                "expected_object_visible": True,
            },
            root=result_pc, target_root=result_pc,
            execution_root=result_pc, root_plan={}, fixture=DEFAULT_FIXTURE,
            flag_mapping={}, var_mapping={}, text_assets={},
            text_provenance="PINNED_STAGE61_RAW", abi_index=abi_index,
            instruction_repairs={}, source_suppression_contract=None,
            stage61_script_bytes=frozenset(),
        )
        non_vermilion = _fork_abi_command(
            base_context,
            _Execution(
                pc=result_pc, execution_trace=[result_pc],
                current_instruction_address=result_pc, current_opcode=0x26,
            ),
            result_pc, 0x26, result_raw,
        )
        self.assertEqual(len(non_vermilion), 1)
        self.assertEqual(non_vermilion[0].vars[0x800D], 0)
        self.assertEqual(
            non_vermilion[0].decisions[-1]["result_value"], 0,
        )
        for x, expected in ((23, 1), (24, 0)):
            with self.subTest(vermilion_x=x):
                context = replace(
                    base_context,
                    npc={**base_context.npc, "group": 3, "map": 5},
                    case={
                        **base_context.case,
                        "interaction": {"group": 3, "map": 5},
                        "physical_player_position": {
                            "x": x, "y": 7, "group": 3, "map": 5,
                        },
                    },
                )
                paths = _fork_abi_command(
                    context,
                    _Execution(
                        pc=result_pc, execution_trace=[result_pc],
                        current_instruction_address=result_pc,
                        current_opcode=0x26,
                    ),
                    result_pc, 0x26, result_raw,
                )
                self.assertEqual(len(paths), 1)
                self.assertEqual(paths[0].vars[0x800D], expected)
                self.assertEqual(
                    paths[0].decisions[-1]["result_value"], expected,
                )

    def test_contracted_vending_rejects_owner_site_exit_and_policy_drift(
        self,
    ) -> None:
        mutations = {
            "owner": lambda contract: contract["contract_owner_ids"].__setitem__(
                0, "BG:010/005:999"
            ),
            "site": lambda contract: contract["sites"][0][
                "decision_site"
            ].__setitem__("raw_hex", "710100000100"),
            "real_exit": lambda contract: contract["sites"][0][
                "decision_site"
            ]["real_exit"].__setitem__("result", 0),
            "policy": lambda contract: contract["effect_policy"].__setitem__(
                "executor_policy", "FORCE_B_ON_ANY_REVISIT"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                context, rows = self._contracted_vending_fixture()
                mutate(context.cyclic_decision_contract)
                with patch(
                    "tools.stage61_interaction_oracle._multichoice_rows",
                    return_value=rows,
                ), patch(
                    "tools.stage61_interaction_oracle._printer_engine_binding",
                    side_effect=_synthetic_printer_engine_binding,
                ), self.assertRaises(Stage61InteractionOracleError) as caught:
                    _execute(context)
                self.assertRegex(
                    str(caught.exception),
                    "CYCLIC_DECISION_(CONTEXT_BINDING|SITE_RAW_POLICY|REAL_EXIT)_MISMATCH",
                )

    def test_mutating_vending_without_root_contract_still_fails_closed(
        self,
    ) -> None:
        context, rows = self._contracted_vending_fixture()
        context = replace(context, cyclic_decision_contract=None)
        with patch(
            "tools.stage61_interaction_oracle._multichoice_rows",
            return_value=rows,
        ), patch(
            "tools.stage61_interaction_oracle._printer_engine_binding",
            side_effect=_synthetic_printer_engine_binding,
        ), self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "MUTATING_MENU_LOOP_CONTRACT_REQUIRED:0x08000000",
        ):
            _execute(context)

    def test_contracted_vending_b_reentry_is_not_accepted_as_terminal(
        self,
    ) -> None:
        context, rows = self._contracted_vending_fixture(exit_reenters=True)
        with patch(
            "tools.stage61_interaction_oracle._multichoice_rows",
            return_value=rows,
        ), patch(
            "tools.stage61_interaction_oracle._printer_engine_binding",
            side_effect=_synthetic_printer_engine_binding,
        ), self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "(REPEATING_MENU_CANCEL_DID_NOT_EXIT|"
            "CYCLIC_DECISION_REVISIT_RESULT_POLICY_MISMATCH):0x08000000",
        ):
            _execute(context)

    def test_cyclic_site_coverage_is_exact_within_one_scc(self) -> None:
        """同一SCCの一site実走を別siteのcoverageへ水増ししない。"""

        root = 0x08000000
        scc_id = "cyclic-scc-two-menu-sites"

        def site(pc: int) -> dict[str, object]:
            return {
                "scc_id": scc_id,
                "decision_pc": f"0x{pc:08X}",
                "decision_site": {
                    "site_kind": "EVENT_MENU",
                    "role": "DECISION_PRODUCER",
                    "result_policy": {"result_classes": {
                        "looping": [0], "terminal": [127],
                        "state_conditional": [],
                    }},
                    "real_exit": {"input": "B", "result": 127},
                },
            }

        binding = {
            "target_root": f"0x{root:08X}",
            "sites": [site(root + 0x10), site(root + 0x20)],
        }
        complete_evidence = {
            "target_root": f"0x{root:08X}",
            "one_cycle_witness": {"instruction_addresses": [
                f"0x{root + 0x11:08X}",
                f"0x{root + 0x20:08X}",
                f"0x{root + 0x10:08X}",
            ]},
        }
        identities = _cyclic_event_menu_quotient_identity_sets(
            [binding], [complete_evidence],
        )
        self.assertEqual(identities[2], identities[5])
        self.assertEqual(len(identities[2]), 2)

        missing_site = deepcopy(complete_evidence)
        missing_site["one_cycle_witness"]["instruction_addresses"].remove(
            f"0x{root + 0x20:08X}"
        )
        identities = _cyclic_event_menu_quotient_identity_sets(
            [binding], [missing_site],
        )
        self.assertEqual(identities[0], identities[3])
        self.assertEqual(identities[1], identities[4])
        self.assertNotEqual(identities[2], identities[5])
        self.assertEqual(
            identities[2] - identities[5],
            {(root, scc_id, f"0x{root + 0x20:08X}")},
        )

    def test_real_viridian_school_grid_covers_each_first_choice_then_exit(
        self,
    ) -> None:
        """source定義だけで各説明choiceと実在exitを有限被覆する。"""

        from tools.stage61_event_semantic_relocator import SemanticScriptGraph

        clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        project = (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes()
        stage61 = (ROOT / "build/stages/61_display_npc_event_audit.gba").read_bytes()
        semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        owner = next(
            row for row in inventory["owners"]
            if row["owner_id"] == "BG:005/002:001"
        )
        self.assertEqual(owner["root"], 0x0817EAC6)
        graph = SemanticScriptGraph(stage61)
        graph.walk([owner["root"]])
        self.assertEqual(graph.diagnostics, [])
        executions, blockers = _runtime_execute_with_seed_discovery(
            clean, project, stage61, semantic, owner, graph, {}, {}, {},
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, owner["root"]),
        )
        self.assertEqual(blockers, [])
        states = [state for _context, state in executions]
        by_results = {
            tuple(int(row["result_value"]) for row in state.decisions): state
            for state in states
        }
        self.assertEqual(len(states), 7)
        self.assertEqual(
            set(by_results),
            {(127,), (5,)} | {(choice, 127) for choice in range(5)},
        )

        prefix = ["A", "ADVANCE_TEXT", "ADVANCE_TEXT", "ADVANCE_TEXT"]
        expected_tokens = {
            (127,): prefix + ["B"],
            (5,): prefix + ["DOWN", "RIGHT", "RIGHT", "A"],
            (0, 127): prefix + [
                "A", "ADVANCE_TEXT", "ADVANCE_TEXT", "B",
            ],
            (1, 127): prefix + [
                "RIGHT", "A", "ADVANCE_TEXT", "ADVANCE_TEXT",
                "ADVANCE_TEXT", "B",
            ],
            (2, 127): prefix + [
                "RIGHT", "RIGHT", "A", "ADVANCE_TEXT", "ADVANCE_TEXT",
                "ADVANCE_TEXT", "ADVANCE_TEXT", "B",
            ],
            (3, 127): prefix + [
                "DOWN", "A", "ADVANCE_TEXT", "ADVANCE_TEXT",
                "ADVANCE_TEXT", "ADVANCE_TEXT", "B",
            ],
            (4, 127): prefix + [
                "DOWN", "RIGHT", "A", "ADVANCE_TEXT", "ADVANCE_TEXT",
                "ADVANCE_TEXT", "B",
            ],
        }
        self.assertEqual(
            {results: state.tokens for results, state in by_results.items()},
            expected_tokens,
        )
        effect_cycle = [
            "0x08192DAA", "0x0817EADA", "0x0817EADB", "0x0817EAE1",
        ]
        for results, state in by_results.items():
            menu_choices = [
                printer.menu_choice_index for printer in state.printers
                if printer.kind == "UI_CHROME_MULTICHOICE"
            ]
            expected_cycles = 2 if len(results) == 2 else 1
            self.assertEqual(menu_choices, list(range(6)) * expected_cycles)
            self.assertEqual(
                [row["instruction_address"] for row in state.effects],
                effect_cycle * expected_cycles,
            )

    def test_repeating_menu_with_persistent_write_requires_explicit_contract(
        self,
    ) -> None:
        root = 0x08000000
        exit_pc = root + 27
        script = b"".join((
            bytes.fromhex("710000000100"),  # 1-choice grid、B有効
            bytes.fromhex("210d807f00"),  # VAR_RESULTとMENU_CANCELを比較
            bytes((0x06, 0x01)) + exit_pc.to_bytes(4, "little"),
            bytes.fromhex("1600400100"),  # 永続var 0x4000へ1を書込
            bytes((0x05,)) + root.to_bytes(4, "little"),
            bytes((0x02,)),
        ))
        rom = script + bytes(0x100 - len(script))
        context = _Context(
            clean_rom=rom, stage61_rom=rom, semantic_report={},
            npc={"local_id": 0},
            case={
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "expected_object_visible": True,
            },
            root=root, target_root=root, execution_root=root, root_plan={},
            fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
            text_assets={}, text_provenance="SYNTHETIC_SOURCE_RAW",
            abi_index={}, instruction_repairs={},
            source_suppression_contract=None,
            stage61_script_bytes=frozenset(range(root, root + len(script))),
        )
        with patch(
            "tools.stage61_interaction_oracle._multichoice_rows",
            return_value=[(root + 0x80, root + 0x80, b"\xA1\xFF")],
        ), patch(
            "tools.stage61_interaction_oracle._printer_engine_binding",
            side_effect=_synthetic_printer_engine_binding,
        ), self.assertRaises(Stage61InteractionOracleError) as caught:
            _execute(context)
        self.assertEqual(
            str(caught.exception),
            "MUTATING_MENU_LOOP_CONTRACT_REQUIRED:0x08000000:"
            "vars/VAR:0x4000/EXACT_FINAL@0x08000011",
        )

    def test_repeating_menu_arbitrary_scratch_write_is_not_pure_ui(
        self,
    ) -> None:
        """scratchでもVAR_RESULTからの厳密copy以外は有限化しない。"""

        root = 0x08000000
        exit_pc = root + 27
        script = b"".join((
            bytes.fromhex("710000000100"),  # 1-choice grid、B有効
            bytes.fromhex("210d807f00"),  # VAR_RESULTとMENU_CANCELを比較
            bytes((0x06, 0x01)) + exit_pc.to_bytes(4, "little"),
            bytes.fromhex("1600800100"),  # scratch VAR_8000へliteral 1
            bytes((0x05,)) + root.to_bytes(4, "little"),
            bytes((0x02,)),
        ))
        rom = script + bytes(0x100 - len(script))
        context = _Context(
            clean_rom=rom, stage61_rom=rom, semantic_report={},
            npc={"local_id": 0},
            case={
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "expected_object_visible": True,
            },
            root=root, target_root=root, execution_root=root, root_plan={},
            fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
            text_assets={}, text_provenance="SYNTHETIC_SOURCE_RAW",
            abi_index={}, instruction_repairs={},
            source_suppression_contract=None,
            stage61_script_bytes=frozenset(range(root, root + len(script))),
        )
        with patch(
            "tools.stage61_interaction_oracle._multichoice_rows",
            return_value=[(root + 0x80, root + 0x80, b"\xA1\xFF")],
        ), patch(
            "tools.stage61_interaction_oracle._printer_engine_binding",
            side_effect=_synthetic_printer_engine_binding,
        ), self.assertRaises(Stage61InteractionOracleError) as caught:
            _execute(context)
        self.assertEqual(
            str(caught.exception),
            "MUTATING_MENU_LOOP_CONTRACT_REQUIRED:0x08000000:"
            "vars/VAR:0x8000/EXACT_FINAL@0x08000011",
        )

    def test_repeating_menu_prior_scratch_read_is_not_hidden_by_later_copy(
        self,
    ) -> None:
        """前周scratchをreadした後の正規copyで履歴依存を隠さない。"""

        root = 0x08000000
        history_branch = root + 38
        exit_pc = root + 51
        script = b"".join((
            bytes.fromhex("710000000100"),  # 2-choice grid、B有効
            bytes.fromhex("210d807f00"),
            bytes((0x06, 0x01)) + exit_pc.to_bytes(4, "little"),
            # This read observes the previous cycle.  A later exact copy must
            # not retroactively make it history-independent.
            bytes.fromhex("2100800100"),
            bytes((0x06, 0x01)) + history_branch.to_bytes(4, "little"),
            bytes.fromhex("1900800d80"),
            bytes((0x05,)) + root.to_bytes(4, "little"),
            bytes.fromhex("286300"),  # only a real choice-1 -> choice-* history
            bytes.fromhex("1900800d80"),
            bytes((0x05,)) + root.to_bytes(4, "little"),
            bytes((0x02,)),
        ))
        self.assertEqual(len(script), 52)
        rom = script + bytes(0x100 - len(script))
        context = _Context(
            clean_rom=rom, stage61_rom=rom, semantic_report={},
            npc={"local_id": 0},
            case={
                "state": {
                    "flags": [], "vars": [{"id": 0x8000, "value": 0}],
                    "items": [], "trainers": [],
                },
                "expected_object_visible": True,
            },
            root=root, target_root=root, execution_root=root, root_plan={},
            fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
            text_assets={}, text_provenance="SYNTHETIC_SOURCE_RAW",
            abi_index={}, instruction_repairs={},
            source_suppression_contract=None,
            stage61_script_bytes=frozenset(range(root, root + len(script))),
        )
        rows = [
            (root + 0x80, root + 0x80, b"\xA1\xFF"),
            (root + 0x82, root + 0x82, b"\xA2\xFF"),
        ]
        with patch(
            "tools.stage61_interaction_oracle._multichoice_rows",
            return_value=rows,
        ), patch(
            "tools.stage61_interaction_oracle._printer_engine_binding",
            side_effect=_synthetic_printer_engine_binding,
        ), self.assertRaises(Stage61InteractionOracleError) as caught:
            _execute(context)
        self.assertEqual(
            str(caught.exception),
            "MUTATING_MENU_LOOP_CONTRACT_REQUIRED:0x08000000:"
            "scratch-read-before-result-copy:VAR:0x8000@0x08000011",
        )

    def test_repeating_menu_volatile_and_abi_effects_fail_closed(
        self,
    ) -> None:
        """volatileはexact benign identityだけ、ABIは明示contractだけを許可する。"""

        root = 0x08000000
        rom = bytes(0x100)
        context = _Context(
            clean_rom=rom, stage61_rom=rom, semantic_report={},
            npc={"local_id": 0}, case={"state": {}},
            root=root, target_root=root, execution_root=root, root_plan={},
            fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
            text_assets={}, text_provenance="SYNTHETIC_SOURCE_RAW",
            abi_index={}, instruction_repairs={},
            source_suppression_contract=None, stage61_script_bytes=frozenset(),
        )
        checkpoint = _RepeatingMenuCheckpoint(
            effect_count=0, abi_dispatch_count=0,
            special_var_access_count=0, persistent_vars=(), flags=(),
        )
        benign = _Execution(pc=root, effects=[{
            "domain": "volatile", "owner": "SCRIPT_DELAY_TIMER",
            "relation": "WAIT_EXACT_FRAMES",
            "instruction_address": "0x08000010", "opcode": "0x28",
            "abi_key": None,
        }])
        _assert_repeating_menu_body_is_nonstate(
            context, benign, root, checkpoint,
        )

        mutating = _Execution(pc=root, effects=[{
            "domain": "volatile",
            "owner": "EventDesign_ScriptSchedule:volatile",
            "relation": (
                "SETUP_SCRIPT_CONTEXT_ONLY_IFF_COMBINED_ADDRESS_IN_ROM_RANGE"
            ),
            "instruction_address": "0x08000010", "opcode": "0x23",
            "abi_key": None,
        }])
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "volatile/EventDesign_ScriptSchedule:volatile",
        ):
            _assert_repeating_menu_body_is_nonstate(
                context, mutating, root, checkpoint,
            )

        abi_dispatch = _Execution(pc=root, abi_dispatches=[{
            "abi_key": "SPECIAL:0001:0x08000101",
            "instruction_address": "0x08000010",
        }])
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "abi/SPECIAL:0001:0x08000101/DISPATCH",
        ):
            _assert_repeating_menu_body_is_nonstate(
                context, abi_dispatch, root, checkpoint,
            )

    def test_product_pc_menu_all_flag_domains_then_actual_b_exit(
        self,
    ) -> None:
        """PC各submenuを一周保持し、同一site再訪を実Bで閉じる。"""

        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        from tools.stage61_cyclic_decision_contracts import (
            build_stage61_cyclic_decision_contracts,
            load_stage61_cyclic_decision_source_blobs,
        )
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph
        from tools.stage61_interaction_oracle import (
            _bind_cyclic_decision_root_contract,
            _cyclic_quotient_real_exit_execution_valid,
            _validate_cyclic_decision_contract_input,
        )

        clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        project = (
            ROOT / "build/stages/60_wild_species_root_repair.gba"
        ).read_bytes()
        stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        repair = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text())
        inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        catalog = json.loads((
            ROOT / "reports/generated/stage61_npc_interaction_catalog_legacy.json"
        ).read_text())
        source_blobs, symbol_reports = _interaction_abi_pinned_inputs()
        manifest = build_pinned_interaction_abi_manifest(
            clean, project, stage61, catalog,
            source_blobs=source_blobs,
            runtime_symbol_reports=symbol_reports,
        )
        special_ids = {
            60, 212, 213, 214, 215, 250, 262, 263,
            381, 382, 383, 391, 400, 432,
        }
        abi_index = _interaction_abi_index(
            stage61, {
                "special_abis": [
                    deepcopy(row) for row in manifest["special_abis"]
                    if row["special_id"] in special_ids
                ],
                "native_abis": [],
            },
            source_blobs=source_blobs,
        )

        root = 0x08194221
        owner_id = "OBJECT:096/005:010"
        owner = next(
            row for row in inventory["owners"]
            if row["owner_id"] == owner_id
        )
        document = build_stage61_cyclic_decision_contracts(
            stage61, inventory,
            load_stage61_cyclic_decision_source_blobs(ROOT),
        )
        cyclic_index = _validate_cyclic_decision_contract_input(
            document, stage61,
            expected_event_owner_inventory_sha256=inventory["inventory_sha256"],
        )
        binding = _bind_cyclic_decision_root_contract(
            cyclic_index, semantic, owner_ids=[owner_id],
            target_root=root, execution_root=root,
            require_exact_owner_set=True,
        )
        self.assertEqual(binding["classification"], "EXPLICIT_TRANSACTION")
        self.assertEqual(binding["loop_family"], "PC_MAIN_AND_SUBMENUS")
        self.assertEqual(
            {row["decision_pc"] for row in binding["sites"]},
            {
                "0x0819426A", "0x081942C7",
                "0x081942EE", "0x08194339",
            },
        )

        graph = SemanticScriptGraph(stage61)
        graph.walk([root])
        self.assertEqual(graph.diagnostics, [])
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(source_blobs[builder_path]).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        text_assets, _provenance = _independent_runtime_text_assets(
            clean, project, stage61, semantic, repair, graph,
            source_blobs=source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            clean, project, stage61, semantic, owner, graph,
            text_assets, abi_index, source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, root),
            cyclic_decision_contract=binding,
        )
        self.assertEqual(blockers, [])
        self.assertEqual(len(executions), 232)
        self.assertLess(len(executions), MAX_EXECUTION_PATHS)
        self.assertTrue(all(state.terminated for _context, state in executions))

        expected_by_flags = {
            (False, False): {0, 1, 2, 127},
            (False, True): {0, 1, 2, 3, 127},
            (True, False): {0, 1, 2, 3, 4, 127},
            (True, True): {0, 1, 2, 3, 4, 127},
        }
        first_results_by_flags = {
            flags: set() for flags in expected_by_flags
        }
        quotient_states = []
        callback_states = []
        for _context, state in executions:
            flags = (state.flags[0x082C], state.flags[0x0829])
            decisions = [
                row for row in state.decisions
                if row.get("instruction_address") == "0x0819426A"
                and row.get("kind") in {
                    "PINNED_PC_MENU_SELECTION", "PINNED_PC_MENU_CANCEL",
                }
            ]
            if decisions:
                first_results_by_flags[flags].add(decisions[0]["result_value"])
            if state.cyclic_quotient_evidence:
                quotient_states.append(state)
                self.assertEqual(
                    [row["result_value"] for row in decisions][-1], 127,
                )
                evidence = state.cyclic_quotient_evidence[0]
                self.assertEqual(evidence["real_exit_execution"]["input"], "B")
                self.assertEqual(evidence["real_exit_execution"]["result"], 127)
                self.assertEqual(
                    evidence["one_cycle_witness"]["instruction_addresses"][-1],
                    "0x0819426A",
                )
                self.assertTrue(
                    _cyclic_quotient_real_exit_execution_valid(evidence)
                )
                self.assertTrue(all(evidence["assertions"].values()))
            if any(
                row.get("kind") ==
                    "PC_HALL_OF_FAME_CALLBACK_REOPENS_MENU"
                for row in state.decisions
            ):
                callback_states.append(state)
        self.assertEqual(first_results_by_flags, expected_by_flags)
        self.assertTrue(quotient_states)
        self.assertTrue(callback_states)
        self.assertTrue(all(state.tokens[-1] == "B" for state in quotient_states))

        # Product root may not silently fall back to the unbounded ABI fork.
        site_pc = 0x0819426A
        site_raw = stage61[
            site_pc - 0x08000000:site_pc - 0x08000000 + 3
        ]
        probe_context = next(
            context for context, state in executions
            if state.flags[0x082C] is False and state.flags[0x0829] is False
        )
        probe = _Execution(
            pc=site_pc, flags={0x082C: False, 0x0829: False},
            execution_trace=[site_pc],
            current_instruction_address=site_pc, current_opcode=0x25,
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "PC_TRANSACTION_CYCLIC_CONTRACT_REQUIRED",
        ):
            _fork_abi_command(
                replace(probe_context, cyclic_decision_contract=None),
                probe.clone(), site_pc, 0x25, site_raw,
            )

        initial = _fork_abi_command(
            probe_context, probe.clone(), site_pc, 0x25, site_raw,
        )
        selected = next(
            state for state in initial if state.vars[0x800D] == 0
        )
        revisit = selected.clone()
        revisit.pc = site_pc
        revisit.execution_trace.append(site_pc)
        revisit.current_instruction_address = site_pc
        revisit.current_opcode = 0x25
        forged = deepcopy(binding)
        producer = next(
            row["decision_site"] for row in forged["sites"]
            if row["decision_pc"] == "0x0819426A"
        )
        producer["result_policy"]["candidate_domain"]["cases"][0][
            "candidate_values"
        ] = [0, 2, 127]
        producer["result_policy"]["candidate_domain"]["cases"][0][
            "result_classes"
        ]["looping"] = [0]
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "PC_MENU_FLAG_CONDITIONAL_RESULT_POLICY_MISMATCH",
        ):
            _fork_abi_command(
                replace(probe_context, cyclic_decision_contract=forged),
                revisit, site_pc, 0x25, site_raw,
            )

class Stage61MapCompositeFocusedTests(unittest.TestCase):
    @staticmethod
    def _direct(tag: int, index: int, root: int) -> dict:
        record = 0x08001000 + index * 5
        return {
            "outer_index": index, "tag": tag,
            "record_address": record,
            "pointer_field_address": record + 1,
            "record_raw_hex": "00" * 5,
            "record_raw_sha256": "0" * 64,
            "dispatch_kind": "DIRECT", "root_pc": root,
            "root_field_address": record + 1,
            "owner_id": f"MAP:001/002:{index:03d}:DIRECT",
        }

    @staticmethod
    def _condition(
        tag: int, index: int, conditions: list[tuple[int, int, int]],
    ) -> dict:
        record = 0x08001000 + index * 5
        rows = []
        for condition_index, (variable, value, root) in enumerate(conditions):
            condition_record = 0x08002000 + index * 0x100 \
                + condition_index * 8
            rows.append({
                "condition_index": condition_index, "tag": tag,
                "record_address": condition_record,
                "root_field_address": condition_record + 4,
                "record_raw_hex": "00" * 8,
                "record_raw_sha256": "0" * 64,
                "variable": variable, "value": value, "root_pc": root,
                "owner_id": (
                    f"MAP:001/002:{index:03d}:{condition_index:03d}"
                ),
            })
        return {
            "outer_index": index, "tag": tag,
            "record_address": record,
            "pointer_field_address": record + 1,
            "record_raw_hex": "00" * 5,
            "record_raw_sha256": "0" * 64,
            "dispatch_kind": "CONDITION_TABLE",
            "condition_table_pointer": 0x08002000 + index * 0x100,
            "conditions": rows,
        }

    @classmethod
    def _topology(cls, *rows: dict) -> dict:
        return {
            "schema_version": 1,
            "kind": "STAGE61_MAP_LIFECYCLE_TOPOLOGY",
            "map": {"group": 1, "map": 2}, "map_id": "001/002",
            "header_address": 0x08000020, "table_pointer": 0x08001000,
            "outer_rows": list(rows),
            "by_tag": {str(row["tag"]): deepcopy(row) for row in rows},
            "rom_sha256": "0" * 64,
        }

    @staticmethod
    def _initial(variables: dict[int, int] | None = None) -> _Execution:
        return _Execution(
            pc=0, tokens=["WALK_ONTO_WARP", "WAIT_MAP_LOAD"],
            vars={} if variables is None else dict(variables), terminated=True,
        )

    @staticmethod
    def _return(prepared: _Execution) -> _Execution:
        prepared.terminated = True
        prepared.terminal_kind = "FIELD_RELEASE"
        prepared.lock_depth = 0
        return prepared

    @staticmethod
    def _serialized_lifecycle(
        result: dict, *, producer_kind: str,
        include_field_return: bool,
    ) -> dict:
        return {
            "schema_version": 1,
            "kind": "STAGE61_MAP_LIFECYCLE_SEQUENCE",
            "producer_ordinal": 0,
            "producer_kind": producer_kind,
            "control_variant_id": "map-control-focused",
            "include_field_return": include_field_return,
            "attempt_cap": 256,
            "phase_controls": deepcopy(result["phase_controls"]),
            "engine_transforms": deepcopy(result["engine_transforms"]),
            "ordered_attempts": deepcopy(result["ordered_attempts"]),
            "ordered_dispatches": deepcopy(result["ordered_dispatches"]),
            "ordered_effect_instances": deepcopy(
                result["ordered_effect_instances"]
            ),
            "dispatched_owner_ids": deepcopy(
                result["dispatched_owner_ids"]
            ),
            "attempt_count": result["attempt_count"],
            "dispatch_count": result["dispatch_count"],
        }

    def test_sibling_state_and_evidence_carry_but_root_locals_reset(self) -> None:
        tag3 = self._direct(3, 0, 0x08003000)
        tag1 = self._direct(1, 1, 0x08003100)
        topology = self._topology(tag3, tag1)
        initial = self._initial()
        initial.stack = [(0x08009999, 0x08008888)]
        initial.loaded_words = {0: 0x08123456}
        initial.comparison = 1
        initial.current_instruction_address = 0x08007777
        initial.current_opcode = 0x16
        initial.current_abi_key = "SPECIAL:test"
        initial.menu_depth = 1
        initial.flags = {0x0900: True}
        initial.effects = [{"kind": "BEFORE"}]
        initial.decisions = [{"kind": "BEFORE"}]
        initial.execution_trace = [0x08000010]
        roots: list[int] = []

        def execute(dispatch: dict, state: _Execution) -> list[_Execution]:
            root = int(dispatch["root_pc"])
            roots.append(root)
            self.assertEqual(state.pc, root)
            self.assertEqual(state.stack, [])
            self.assertEqual(state.loaded_words, {})
            self.assertIsNone(state.comparison)
            self.assertIsNone(state.current_instruction_address)
            self.assertIsNone(state.current_opcode)
            self.assertIsNone(state.current_abi_key)
            self.assertEqual(state.menu_depth, 0)
            if root == 0x08003000:
                state.vars[0x5000] = 7
                state.flags[0x0900] = False
                state.effects.append({"kind": "TAG3"})
                state.decisions.append({"kind": "TAG3"})
            else:
                self.assertEqual(state.vars[0x5000], 7)
                self.assertFalse(state.flags[0x0900])
                self.assertEqual(
                    [row["kind"] for row in state.effects],
                    ["BEFORE", "TAG3"],
                )
                self.assertEqual(
                    [row["kind"] for row in state.decisions],
                    ["BEFORE", "TAG3"],
                )
            state.execution_trace.append(root)
            return [self._return(state)]

        [result] = _execute_map_lifecycle(
            topology, "STOCK_WARP", initial, execute,
            include_field_return=False,
        )
        self.assertEqual(roots, [0x08003000, 0x08003100])
        self.assertEqual(result["state"].vars[0x5000], 7)
        self.assertFalse(result["state"].flags[0x0900])
        self.assertEqual(
            [row["kind"] for row in result["state"].effects],
            ["BEFORE", "TAG3"],
        )
        self.assertEqual(
            [(row["owner_id"], row["effect"]["kind"])
             for row in result["ordered_effect_instances"]],
            [("MAP:001/002:000:DIRECT", "TAG3")],
        )
        self.assertEqual(result["state"].execution_trace, [
            0x08000010, 0x08003000, 0x08003100,
        ])

    def test_sibling_lock_residue_fails_closed(self) -> None:
        state = self._initial()
        state.lock_depth = 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "field lock",
        ):
            _execution_for_sibling_root(state, 0x08003000)

    def test_destination_temp_clear_is_exact_and_pre_field_is_later(self) -> None:
        topology = self._topology()
        initial = self._initial({0x4000: 9, 0x5000: 4})
        initial.flags = {0: True, 0x0803: True, 0x0900: True}
        [result] = _execute_map_lifecycle(
            topology, "STOCK_WARP", initial,
            lambda _dispatch, _state: self.fail("dispatch unexpected"),
            include_field_return=False,
            pre_transition_controls={"vars": {0x4001: 8}},
            pre_field_input_controls={"vars": {0x5001: 3}},
        )
        state = result["state"]
        self.assertTrue(all(state.vars[key] == 0 for key in range(0x4000, 0x4010)))
        self.assertEqual(state.vars[0x5000], 4)
        self.assertEqual(state.vars[0x5001], 3)
        self.assertFalse(state.flags[0])
        self.assertFalse(state.flags[0x0803])
        self.assertTrue(state.flags[0x0900])
        self.assertEqual(
            [row["phase_marker"] for row in result["phase_controls"]],
            ["PRE_TRANSITION", "PRE_FIELD_INPUT"],
        )
        transform = result["engine_transforms"][0]
        self.assertEqual(len(transform["variable_writes"]), 16)
        self.assertEqual(len(transform["temporary_flag_writes"]), 32)
        self.assertEqual(
            [row["id"] for row in transform["system_flag_writes"]],
            [0x0803, 0x0804, 0x0805, 0x0807, 0x0842],
        )

    def test_tag2_repeats_in_rom_order_until_explicit_no_match(self) -> None:
        tag2 = self._condition(2, 0, [
            (0x5000, 0, 0x08003000),
            (0x5000, 1, 0x08003100),
        ])
        topology = self._topology(tag2)

        def execute(_dispatch: dict, state: _Execution) -> list[_Execution]:
            state.vars[0x5000] += 1
            return [self._return(state)]

        [result] = _execute_map_lifecycle(
            topology, "STOCK_WARP", self._initial(), execute,
            include_field_return=False,
            pre_field_input_controls={"vars": {0x5000: 0}},
        )
        tag2_attempts = [
            row for row in result["ordered_attempts"] if row["tag"] == 2
        ]
        self.assertEqual(
            [row["result"] for row in tag2_attempts],
            ["DISPATCH", "DISPATCH", "NO_CONDITION_MATCH"],
        )
        self.assertEqual(
            [row["selected_condition_index"] for row in tag2_attempts],
            [0, 1, None],
        )

    def test_tag2_condition_state_revisit_is_livelock(self) -> None:
        topology = self._topology(self._condition(
            2, 0, [(0x5000, 0, 0x08003000)],
        ))
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "MAP_ON_FRAME_LIVELOCK",
        ):
            _execute_map_lifecycle(
                topology, "STOCK_WARP", self._initial(),
                lambda _dispatch, state: [self._return(state)],
                include_field_return=False,
                pre_field_input_controls={"vars": {0x5000: 0}},
            )

    def test_field_return_runs_tag5_again_then_tag7(self) -> None:
        topology = self._topology(
            self._direct(5, 0, 0x08003000),
            self._direct(7, 1, 0x08003100),
        )
        [result] = _execute_map_lifecycle(
            topology, "STOCK_WARP", self._initial(),
            lambda _dispatch, state: [self._return(state)],
            include_field_return=True,
        )
        self.assertEqual(
            [row["tag"] for row in result["ordered_dispatches"]],
            [5, 5, 7],
        )
        self.assertEqual(
            [row["phase_marker"] for row in result["ordered_dispatches"]],
            ["INITIAL_RESUME", "FIELD_RETURN_RESUME",
             "FIELD_RETURN_RETURN_TO_FIELD"],
        )

    def test_connection_never_attempts_tag4(self) -> None:
        topology = self._topology(self._direct(4, 0, 0x08003000))
        [result] = _execute_map_lifecycle(
            topology, "CONNECTION", self._initial(),
            lambda _dispatch, state: [self._return(state)],
            include_field_return=False,
        )
        self.assertNotIn(4, [row["tag"] for row in result["ordered_attempts"]])
        self.assertEqual(result["dispatched_owner_ids"], [])
        projection = map_lifecycle_expected_ordered_projection(
            self._serialized_lifecycle(
                result, producer_kind="CONNECTION",
                include_field_return=False,
            )
        )
        self.assertNotIn(
            4, [row["tag"] for row in projection["ordered_attempts"]],
        )

    def test_tag4_uses_first_matching_rom_row(self) -> None:
        topology = self._topology(self._condition(4, 0, [
            (0x5000, 7, 0x08003000),
            (0x5001, 9, 0x08003100),
        ]))
        [result] = _execute_map_lifecycle(
            topology, "STOCK_WARP", self._initial(),
            lambda _dispatch, state: [self._return(state)],
            include_field_return=False,
            pre_transition_controls={
                "vars": {0x5000: 7, 0x5001: 9},
            },
        )
        [dispatch] = result["ordered_dispatches"]
        self.assertEqual(dispatch["tag"], 4)
        self.assertEqual(dispatch["owner_id"], "MAP:001/002:000:000")

    def test_expected_ordered_projection_is_canonical_and_exact(self) -> None:
        topology = self._topology(
            self._direct(3, 0, 0x08003000),
            self._direct(5, 1, 0x08003100),
            self._condition(4, 2, [(0x5001, 7, 0x08003200)]),
            self._condition(2, 3, [
                (0x5000, 0, 0x08003300),
                (0x5000, 1, 0x08003400),
            ]),
            self._direct(7, 4, 0x08003500),
        )

        def execute(dispatch: dict, state: _Execution) -> list[_Execution]:
            if dispatch["tag"] == 2:
                state.vars[0x5000] += 1
            state.execution_trace.append(int(dispatch["root_pc"]))
            return [self._return(state)]

        [result] = _execute_map_lifecycle(
            topology, "STOCK_WARP", self._initial(), execute,
            include_field_return=True,
            pre_transition_controls={"vars": {0x5001: 7}},
            pre_field_input_controls={"vars": {0x5000: 0}},
        )
        lifecycle = self._serialized_lifecycle(
            result, producer_kind="STOCK_WARP",
            include_field_return=True,
        )
        projection = map_lifecycle_expected_ordered_projection(lifecycle)
        self.assertEqual(projection["capacity"], 256)
        self.assertEqual(
            projection["capacity_scope"],
            "PRE_FIELD_INPUT_ON_FRAME_TAG2_ATTEMPTS",
        )
        self.assertEqual(
            [row["source_phase_marker"]
             for row in projection["ordered_attempts"]],
            [
                "INITIAL_TRANSITION", "INITIAL_LOAD", "INITIAL_RESUME",
                "INITIAL_WARP_IN", "PRE_FIELD_INPUT_ON_FRAME",
                "PRE_FIELD_INPUT_ON_FRAME", "PRE_FIELD_INPUT_ON_FRAME",
                "FIELD_RETURN_RESUME", "FIELD_RETURN_RETURN_TO_FIELD",
            ],
        )
        self.assertNotIn(
            "INITIAL_WARP_INTO",
            [row["source_phase_marker"]
             for row in projection["ordered_attempts"]],
        )
        self.assertEqual(
            projection["phase_boundaries"],
            [{
                "boundary_ordinal": 0, "phase_marker": "INITIAL_LOAD",
                "before_observed_attempt_ordinal": 0,
                "before_source_attempt_ordinal": 1,
            }, {
                "boundary_ordinal": 1, "phase_marker": "FIELD_RETURN",
                "before_observed_attempt_ordinal": 7,
                "before_source_attempt_ordinal": 8,
            }],
        )
        self.assertEqual(
            [row["observed_attempt_ordinal"]
             for row in projection["ordered_dispatches"]],
            [0, 2, 3, 4, 5, 7, 8],
        )
        unhashed = deepcopy(projection)
        digest = unhashed.pop("projection_sha256")
        self.assertEqual(
            digest, hashlib.sha256(
                (json.dumps(
                    unhashed, ensure_ascii=False, sort_keys=True,
                    separators=(",", ":"),
                ) + "\n").encode("utf-8")
            ).hexdigest(),
        )

        forged = deepcopy(lifecycle)
        forged["ordered_dispatches"][0]["owner_id"] = \
            "MAP:001/002:999:DIRECT"
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "dispatch/attempt binding",
        ):
            map_lifecycle_expected_ordered_projection(forged)

        forged_engine_type = deepcopy(lifecycle)
        forged_engine_type["engine_transforms"][0][
            "variable_writes"
        ][0]["value"] = False
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "variable_writes",
        ):
            map_lifecycle_expected_ordered_projection(forged_engine_type)

        missing_quiescence = deepcopy(lifecycle)
        tag2_terminal = next(
            index for index, row in enumerate(
                missing_quiescence["ordered_attempts"]
            ) if row["phase_marker"] == "PRE_FIELD_INPUT_ON_FRAME"
            and row["result"] != "DISPATCH"
        )
        missing_quiescence["ordered_attempts"].pop(tag2_terminal)
        missing_quiescence["attempt_count"] -= 1
        for index, row in enumerate(
            missing_quiescence["ordered_attempts"]
        ):
            row["attempt_ordinal"] = index
        for row in missing_quiescence["ordered_dispatches"]:
            if row["attempt_ordinal"] > tag2_terminal:
                row["attempt_ordinal"] -= 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "tag2 quiescence",
        ):
            map_lifecycle_expected_ordered_projection(missing_quiescence)

    def test_default_hard_cap_256_rejects_unquiesced_tag2_chain(self) -> None:
        topology = self._topology(self._condition(
            2, 0, [
                (0x5000, value, 0x08003000 + value)
                for value in range(256)
            ],
        ))

        def execute(_dispatch: dict, state: _Execution) -> list[_Execution]:
            state.vars[0x5000] += 1
            return [self._return(state)]

        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "MAP_LIFECYCLE_ATTEMPT_CAP_EXCEEDED",
        ):
            _execute_map_lifecycle(
                topology, "STOCK_WARP", self._initial(), execute,
                include_field_return=False,
                pre_field_input_controls={"vars": {0x5000: 0}},
            )

    def test_covered_owner_ids_form_exact_map_partition(self) -> None:
        owners = [{
            "owner_id": f"MAP:001/002:00{index}:DIRECT",
            "owner_kind": "MAP", "group": 1, "map": 2,
        } for index in range(2)]
        case = {
            "case_id": "map-lifecycle-001-002-test",
            "case_kind": "MAP_LIFECYCLE_COMPOSITE",
            "map": {"group": 1, "map": 2},
            "covered_owner_ids": [row["owner_id"] for row in owners],
        }
        self.assertEqual(
            _map_lifecycle_coverage_findings(owners, [case]), [],
        )
        broken = deepcopy(case)
        broken["covered_owner_ids"] = [owners[0]["owner_id"]] * 2
        kinds = {
            row["kind"]
            for row in _map_lifecycle_coverage_findings(owners, [broken])
        }
        self.assertEqual(kinds, {
            "MAP_COMPOSITE_CASE_OWNER_DUPLICATE",
            "MAP_COMPOSITE_OWNER_COVERAGE_MISMATCH",
        })

    def test_player_position_scope_is_exact_opcode42_consumer_union(
        self,
    ) -> None:
        owners = [
            "MAP:001/002:000:DIRECT",
            "MAP:001/002:001:DIRECT",
            "MAP:001/002:002:DIRECT",
        ]
        controls = [{
            "kind": "PLAYER_POSITION", "id": 0,
            "value": {"x": 4, "y": 5, "group": 1, "map": 2},
            "owner_keys": owners,
            "relation_evidence": [{"operator": "PLAYER_POSITION"}],
            "fixture_keys": ["position-fixture"],
        }, {
            "kind": "VAR", "id": 0x5000, "value": 7,
            "owner_keys": owners, "relation_evidence": [],
            "fixture_keys": [],
        }]

        def effect_instance(
            ordinal: int, dispatch: int, owner: str,
            *, axis: str, member: int,
        ) -> dict:
            return {
                "effect_instance_ordinal": ordinal,
                "dispatch_ordinal": dispatch, "owner_id": owner,
                "root_pc": f"0x{0x08003000 + dispatch * 0x100:08X}",
                "effect": {
                    "domain": "vars", "owner": f"VAR:0x800{4 + member:X}",
                    "relation": f"COPY_CURRENT_PLAYER_{axis}",
                    "instruction_address":
                        f"0x{0x08003010 + dispatch * 0x100:08X}",
                    "execution_trace_index": 10 + dispatch,
                    "opcode": "0x42", "abi_key": None,
                    "group_member_ordinal": member,
                },
            }

        lifecycle = {"ordered_effect_instances": [
            effect_instance(0, 0, owners[0], axis="X", member=0),
            effect_instance(1, 0, owners[0], axis="Y", member=1),
            {
                "effect_instance_ordinal": 2, "dispatch_ordinal": 1,
                "owner_id": owners[2], "root_pc": "0x08003100",
                "effect": {
                    "domain": "flags", "owner": "FLAG:0x0100",
                    "relation": "EXACT_FINAL",
                    "instruction_address": "0x08003108",
                    "execution_trace_index": 20, "opcode": "0x29",
                    "abi_key": None, "group_member_ordinal": 0,
                    "after": True,
                },
            },
            effect_instance(3, 2, owners[1], axis="X", member=0),
            effect_instance(4, 2, owners[1], axis="Y", member=1),
        ]}
        scoped = _scope_map_lifecycle_player_position_controls(
            controls, lifecycle,
        )
        self.assertEqual(scoped[0]["owner_keys"], owners[:2])
        self.assertEqual(scoped[1], controls[1])
        self.assertEqual(controls[0]["owner_keys"], owners)

        no_consumer = _scope_map_lifecycle_player_position_controls(
            controls[1:], {"ordered_effect_instances": []},
        )
        self.assertEqual(no_consumer, controls[1:])
        self.assertFalse(any(
            row["kind"] == "PLAYER_POSITION" for row in no_consumer
        ))

        partial = deepcopy(lifecycle)
        partial["ordered_effect_instances"].pop()
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "X/Y exact pair不一致",
        ):
            _scope_map_lifecycle_player_position_controls(controls, partial)


class Stage61RuntimeControlFocusedTests(unittest.TestCase):
    @staticmethod
    def _capacity_context(script: bytes) -> _Context:
        root = 0x08000000
        stage61 = bytearray((
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes())
        stage61[:len(script)] = script
        return _Context(
            clean_rom=script, stage61_rom=bytes(stage61), semantic_report={},
            npc={"local_id": 1, "flag": 0, "group": 3, "map": 14},
            case={
                "owner_key": "OBJECT:003/014:000",
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "expected_object_visible": True,
            },
            root=root, target_root=root, execution_root=root,
            root_plan={}, fixture=DEFAULT_FIXTURE,
            flag_mapping={}, var_mapping={}, text_assets={},
            text_provenance="SYNTHETIC_TEST", abi_index={},
            instruction_repairs={}, source_suppression_contract=None,
            # Execute the synthetic source bytes while retaining the real
            # Stage61 ROM for physical Bag fixture materialization.  Mirror
            # the tiny script at its synthetic address so runner semantic
            # relation extraction also sees the exact tested opcodes.
            stage61_script_bytes=frozenset(),
        )

    @staticmethod
    def _coins_context(
        script: bytes, current: int, *, variables: dict[int, int] | None = None,
    ) -> _Context:
        root = 0x08000000
        stage61 = bytearray((
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes())
        stage61[:len(script)] = script
        return _Context(
            clean_rom=script, stage61_rom=bytes(stage61), semantic_report={},
            npc={"local_id": 1, "flag": 0, "group": 1, "map": 40},
            case={
                "owner_key": "OBJECT:001/040:000",
                "state": {
                    "flags": [],
                    "vars": [
                        {"id": identifier, "value": value}
                        for identifier, value in sorted((variables or {}).items())
                    ],
                    "items": [], "trainers": [],
                },
                "expected_object_visible": True,
                "control_requirements": {
                    "external": [{"kind": "COINS", "id": 0, "value": current}],
                    "internal": [],
                },
            },
            root=root, target_root=root, execution_root=root,
            root_plan={}, fixture=replace(DEFAULT_FIXTURE, vega_coins=current),
            flag_mapping={}, var_mapping={}, text_assets={},
            text_provenance="SYNTHETIC_COINS_TEST", abi_index={},
            instruction_repairs={}, source_suppression_contract=None,
            stage61_script_bytes=frozenset(),
        )

    def test_coins_b3_correlates_add_remove_and_all_four_predicates(
        self,
    ) -> None:
        cases = (
            (bytes.fromhex("b30140b4320002"), 9998,
             "CURRENT_COINS_BELOW_MAX", 0, 9999),
            (bytes.fromhex("b30140b4320002"), 9999,
             "CURRENT_COINS_AT_MAX", 1, 9999),
            (bytes.fromhex("b30140b5320002"), 50,
             "CURRENT_COINS_AT_LEAST_AMOUNT", 0, 0),
            (bytes.fromhex("b30140b5320002"), 49,
             "CURRENT_COINS_BELOW_AMOUNT", 1, 49),
        )
        observed = set()
        for script, current, relation, result, after in cases:
            with self.subTest(relation=relation):
                context = self._coins_context(script, current)
                paths = _execute(context)
                self.assertEqual(len(paths), 1)
                state = paths[0]
                self.assertEqual(state.vega_coins_initial, current)
                self.assertEqual(state.vega_coins_current, after)
                self.assertEqual(state.vars[0x800D], result)
                self.assertEqual(len(state.abi_control_reads), 1)
                self.assertEqual(
                    state.abi_control_reads[0]["required_value"], current,
                )
                self.assertEqual(
                    state.abi_control_reads[0]["relation"], relation,
                )
                external, internal = _runtime_control_rows(
                    context, state,
                    owner_keys=["OBJECT:001/040:000"], fixtures={},
                )
                self.assertEqual(internal, [])
                self.assertEqual(len(external), 1)
                predicate = {
                    "operator": relation,
                    "amount": 50,
                    "result_value": result,
                }
                self.assertIn(predicate, external[0]["relation_evidence"])
                self.assertIn({
                    "operator": "WRITE_CURRENT_COINS_TO_VAR",
                    "destination_var": 0x4001,
                }, external[0]["relation_evidence"])
                self.assertEqual(external[0]["value"]["vega"], current)
                required = _runner_required_postconditions(context, state)
                self.assertEqual(
                    required["coins"],
                    {"vega": after} if after != current else None,
                )
                observed.add(relation)
        self.assertEqual(observed, {
            "CURRENT_COINS_BELOW_MAX", "CURRENT_COINS_AT_MAX",
            "CURRENT_COINS_AT_LEAST_AMOUNT", "CURRENT_COINS_BELOW_AMOUNT",
        })

    def test_addcoins_u16_truncate_then_cap_is_source_exact(self) -> None:
        self.assertEqual(_coins_add_transition(1, 0xFFFF), (0, 0))
        # checkcoins VAR_4001; addcoins VAR_8004; end
        context = self._coins_context(
            bytes.fromhex("b30140b4048002"), 1,
            variables={0x8004: 0xFFFF},
        )
        state = _execute(context)[0]
        self.assertEqual(state.vega_coins_current, 0)
        effect = next(row for row in state.effects
                      if row.get("domain") == "coins")
        self.assertEqual(effect["before"], 1)
        self.assertEqual(effect["after"], 0)
        self.assertEqual(
            effect["arithmetic"], "U16_TRUNCATE_THEN_CAP_9999",
        )
        self.assertEqual(
            _runner_required_postconditions(context, state)["coins"],
            {"vega": 0},
        )

    def test_coins_source_rom_and_predicate_drift_fail_closed(self) -> None:
        context = self._coins_context(
            bytes.fromhex("b30140b4320002"), 9998,
        )
        state = _execute(context)[0]
        row = deepcopy(state.abi_control_reads[0])

        source_drift = deepcopy(row)
        source_drift["source"]["producer"]["definition_line"] += 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "COINS_SOURCE_EVIDENCE_DRIFT",
        ):
            _materialize_control_requirement(
                context.stage61_rom, source_drift,
                owner_keys=["OBJECT:001/040:000"], fixtures={},
            )

        rom_drift = bytearray(context.stage61_rom)
        rom_drift[0x0806BF40 - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "COINS_COMMAND_ROM_BINDING_DRIFT",
        ):
            _materialize_control_requirement(
                bytes(rom_drift), row,
                owner_keys=["OBJECT:001/040:000"], fixtures={},
            )

        predicate_drift = deepcopy(row)
        predicate_drift["relation"] = "CURRENT_COINS_AT_MAX"
        predicate_drift["result_value"] = 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "COINS_PREDICATE_VALUE_RESULT_MISMATCH",
        ):
            _materialize_control_requirement(
                context.stage61_rom, predicate_drift,
                owner_keys=["OBJECT:001/040:000"], fixtures={},
            )

    def test_checkcoins_result_uses_path_exact_correlated_singleton(
        self,
    ) -> None:
        # checkcoins VAR_RESULT; compare VAR_RESULT, 0; end
        context = self._coins_context(
            bytes.fromhex("b30d80210d80000002"), 9499,
        )
        state = _execute(context)[0]
        external, internal = _runtime_control_rows(
            context, state,
            owner_keys=["OBJECT:001/040:000"], fixtures={},
        )
        coin = next(row for row in external if row["kind"] == "COINS")
        self.assertEqual(coin["value"]["vega"], 9499)
        self.assertEqual(len(internal), 1)
        result = internal[0]
        self.assertEqual(result["instruction_address"], "0x08000003")
        self.assertEqual(result["writer"], "GET_COINS_PATH_EXACT")
        self.assertEqual(result["candidate_values"], [9499])
        self.assertEqual(result["capture"]["expected_value"], 9499)
        self.assertEqual(result["producer"]["legal_domain"], {
            "minimum": 0, "maximum": 9999,
        })
        self.assertEqual(
            result["producer"]["relation"],
            "EXACT_GET_COINS_FROM_CORRELATED_PHYSICAL_CONTROL",
        )

        missing_correlation = state.clone()
        missing_correlation.control_reads = []
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "CHECKCOINS_VAR_RESULT_PHYSICAL_CORRELATION_REQUIRED",
        ):
            _runtime_control_rows(
                context, missing_correlation,
                owner_keys=["OBJECT:001/040:000"], fixtures={},
            )

        rom_drift = bytearray(context.stage61_rom)
        rom_drift[0x0806BF20 - 0x08000000] ^= 1
        drift_context = replace(context, stage61_rom=bytes(rom_drift))
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "COINS_COMMAND_ROM_BINDING_DRIFT",
        ):
            _runtime_control_rows(
                drift_context, state,
                owner_keys=["OBJECT:001/040:000"], fixtures={},
            )

        with patch(
            "tools.stage61_interaction_oracle.COINS_SOURCE_SHA256",
            "0" * 64,
        ), self.assertRaisesRegex(
            Stage61InteractionOracleError, "COINS_SOURCE_FILE_HASH_DRIFT",
        ):
            _runtime_control_rows(
                context, state,
                owner_keys=["OBJECT:001/040:000"], fixtures={},
            )

    def test_bag_capacity_check_and_add_share_exact_public_fixture(
        self,
    ) -> None:
        # checkitemspace ITEM_19,1; additem ITEM_19,1; end
        context = self._capacity_context(
            bytes.fromhex("4613000100441300010002")
        )
        paths = _execute(context)
        self.assertEqual(len(paths), 2)
        self.assertEqual({
            tuple(row["required_value"] for row in state.abi_control_reads)
            for state in paths
        }, {(0, 0), (1, 1)})
        self.assertFalse(any(
            [row["required_value"] for row in state.abi_control_reads]
            == [1, 0]
            for state in paths
        ))
        successful = next(
            state for state in paths
            if state.abi_control_reads[0]["required_value"] == 1
        )
        external, internal = _runtime_control_rows(
            context, successful,
            owner_keys=["OBJECT:003/014:000"], fixtures={},
        )
        self.assertEqual(internal, [])
        self.assertEqual(len(external), 1)
        self.assertEqual(set(external[0]), {
            "kind", "id", "value", "owner_keys",
            "relation_evidence", "fixture_keys",
        })
        self.assertEqual(set(external[0]["value"]), {
            "expected_result", "layout_ref",
        })
        self.assertEqual(external[0]["relation_evidence"], [
            {"operator": "ADD_ITEM_CAPACITY", "quantity": 1},
            {"operator": "HAS_SPACE", "quantity": 1},
        ])
        self.assertTrue(any(
            effect.get("owner") == "BAG_ITEM:19"
            and effect.get("relation") == "ADD_EXACT_QUANTITY"
            and effect.get("quantity") == 1
            for effect in successful.effects
        ))

    def test_bag_count_check_and_remove_share_exact_public_fixture(
        self,
    ) -> None:
        # checkitem ITEM_28,1; removeitem ITEM_28,1; end
        context = self._capacity_context(
            bytes.fromhex("471c000100451c00010002")
        )
        paths = _execute(context)
        self.assertEqual(len(paths), 2)
        self.assertEqual({
            tuple(row["required_value"] for row in state.abi_control_reads)
            for state in paths
        }, {(0, 0), (1, 1)})
        successful = next(
            state for state in paths
            if state.abi_control_reads[0]["required_value"] == 1
        )
        external, internal = _runtime_control_rows(
            context, successful,
            owner_keys=["OBJECT:098/047:001"], fixtures={},
        )
        self.assertEqual(internal, [])
        self.assertEqual(len(external), 1)
        self.assertEqual(external[0]["relation_evidence"], [
            {"operator": "HAS_COUNT", "quantity": 1},
            {"operator": "REMOVE_ITEM_COUNT", "quantity": 1},
        ])
        self.assertTrue(any(
            effect.get("owner") == "BAG_ITEM:28"
            and effect.get("relation") == "SUBTRACT_EXACT_QUANTITY"
            and effect.get("quantity") == 1
            for effect in successful.effects
        ))

    def test_repeated_party_move_check_reuses_unchanged_party_slot(
        self,
    ) -> None:
        # checkpartymove MOVE_249; checkpartymove MOVE_249; end
        context = self._capacity_context(
            bytes.fromhex("7cf9007cf90002")
        )
        paths = _execute(context)
        self.assertEqual(len(paths), 7)
        self.assertEqual({
            tuple(row["required_value"] for row in state.abi_control_reads)
            for state in paths
        }, {(slot, slot) for slot in range(7)})
        for state in paths:
            external, internal = _runtime_control_rows(
                context, state,
                owner_keys=["OBJECT:003/014:000"], fixtures={},
            )
            self.assertEqual(internal, [])
            self.assertEqual(len(external), 1)
            self.assertEqual(external[0]["kind"], "PARTY_MOVE")
            self.assertEqual(external[0]["id"], 249)
            self.assertEqual(
                external[0]["value"]["expected_slot"],
                state.abi_control_reads[0]["required_value"],
            )

    def test_other_item_removal_does_not_invalidate_count_predicate(
        self,
    ) -> None:
        # check ITEM_48; check ITEM_49; remove ITEM_48; remove ITEM_49; end
        context = self._capacity_context(bytes.fromhex(
            "473000010047310001004530000100453100010002"
        ))
        paths = _execute(context)
        self.assertEqual(len(paths), 4)
        self.assertEqual({
            tuple(row["required_value"] for row in state.abi_control_reads)
            for state in paths
        }, {
            (first, second, first, second)
            for first in (0, 1) for second in (0, 1)
        })
        for state in paths:
            external, internal = _runtime_control_rows(
                context, state,
                owner_keys=["OBJECT:003/014:000"], fixtures={},
            )
            self.assertEqual(internal, [])
            self.assertEqual(
                {(row["kind"], row["id"]) for row in external},
                {("ITEM", 48), ("ITEM", 49)},
            )

    def test_capacity_results_and_party_move_public_schema_fail_closed(
        self,
    ) -> None:
        for invalid in (2, "1", None):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "PC_CAPACITY control値不正",
            ):
                _materialize_control_requirement(
                    b"", {
                        "kind": "PC_CAPACITY", "owner": "ITEM:19",
                        "required_value": invalid,
                        "relation": "ADD_PC_ITEM_CAPACITY", "quantity": 1,
                    },
                    owner_keys=["OBJECT:003/014:000"], fixtures={},
                )
        fixtures: dict[str, dict] = {}
        projected = _materialize_control_requirement(
            b"", {
                "kind": "PC_CAPACITY", "owner": "ITEM:19",
                "required_value": 1,
                "relation": "ADD_PC_ITEM_CAPACITY", "quantity": 5,
                "instruction_address": "0x08000000",
            },
            owner_keys=["OBJECT:003/014:000"], fixtures=fixtures,
        )
        self.assertEqual(set(projected["value"]), {
            "expected_result", "layout_ref",
        })
        self.assertEqual(set(projected), {
            "kind", "id", "value", "owner_keys",
            "relation_evidence", "fixture_keys",
        })
        self.assertEqual(projected["relation_evidence"], [{
            "operator": "ADD_PC_ITEM_CAPACITY", "quantity": 5,
        }])
        party = _materialize_control_requirement(
            b"", {
                "kind": "PARTY_MOVE", "owner": "MOVE:15",
                "required_value": 2,
                "relation":
                    "FIRST_NON_EGG_MEMBER_KNOWING_MOVE_OR_PARTY_SIZE",
            },
            owner_keys=["OBJECT:003/014:000"], fixtures=fixtures,
        )
        self.assertEqual(set(party["value"]), {
            "move_id", "expected_slot", "party_layout_ref",
        })
        self.assertEqual(party["relation_evidence"], [{
            "operator": "FIRST_NON_EGG_MEMBER_KNOWING_MOVE",
        }])
        party_count = _materialize_control_requirement(
            b"", {
                "kind": "PARTY_COUNT", "owner": "PLAYER_PARTY_COUNT",
                "required_value": 2, "relation": "EXACT_PARTY_COUNT",
            },
            owner_keys=["OBJECT:003/014:000"], fixtures=fixtures,
        )
        self.assertEqual(party_count["relation_evidence"], [{
            "operator": "GET_PARTY_SIZE",
        }])
        gender = _materialize_control_requirement(
            b"", {
                "kind": "PLAYER_GENDER", "owner": "SAVE_BLOCK2_GENDER",
                "required_value": 1, "relation": "EXACT_U8",
            },
            owner_keys=["OBJECT:003/014:000"], fixtures=fixtures,
        )
        self.assertEqual(gender["relation_evidence"], [{
            "operator": "SAVE_BLOCK2_PLAYER_GENDER",
        }])
        ordinary_flag = _materialize_control_requirement(
            b"", {
                "kind": "FLAG", "id": 7, "required_value": False,
                "relation": "EXACT",
            },
            owner_keys=["OBJECT:003/014:000"], fixtures=fixtures,
        )
        self.assertEqual(ordinary_flag["relation_evidence"], [])
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "PC_CAPACITY quantity不正",
        ):
            _materialize_control_requirement(
                b"", {
                    "kind": "PC_CAPACITY", "owner": "ITEM:19",
                    "required_value": 1,
                    "relation": "ADD_PC_ITEM_CAPACITY",
                },
                owner_keys=["OBJECT:003/014:000"], fixtures={},
            )

    def test_additem_reuses_unmutated_reaching_capacity_result(self) -> None:
        state = _Execution(pc=0x081744F0)
        state.execution_trace = [0x081744C9, 0x081744F0]
        state.abi_control_reads = [{
            "kind": "BAG_CAPACITY", "owner": "ITEM:19",
            "relation": "HAS_SPACE", "quantity": 1,
            "required_value": 1,
            "instruction_address": "0x081744C9",
        }]
        self.assertEqual(
            _reaching_bag_capacity_result(state, 19, 1, 0x081744F0), 1,
        )
        state.execution_trace = [0x081744C9, 0x081744E0, 0x081744F0]
        state.effects = [{
            "domain": "items", "owner": "BAG_ITEM:28",
            "execution_trace_index": 1,
        }]
        self.assertIsNone(
            _reaching_bag_capacity_result(state, 19, 1, 0x081744F0),
        )

    def test_removeitem_reuses_unmutated_reaching_count_result(self) -> None:
        state = _Execution(pc=0x09431C60)
        state.execution_trace = [0x094319FA, 0x09431C60]
        state.abi_control_reads = [{
            "kind": "ITEM", "owner": "ITEM:28",
            "relation": "HAS_AT_LEAST_QUANTITY", "quantity": 1,
            "required_value": 1,
            "instruction_address": "0x094319FA",
        }]
        self.assertEqual(
            _reaching_bag_item_count_result(
                state, 28, 1, 0x09431C60,
            ),
            1,
        )
        state.execution_trace = [
            0x094319FA, 0x09431C20, 0x09431C60,
        ]
        state.effects = [{
            "domain": "items", "owner": "BAG_ITEM:28",
            "execution_trace_index": 1,
        }]
        self.assertIsNone(
            _reaching_bag_item_count_result(
                state, 28, 1, 0x09431C60,
            )
        )

    def test_map_player_position_uses_destination_arrival_not_predecessor(
        self,
    ) -> None:
        topology = {
            "map_id": "002/010", "map": {"group": 2, "map": 10},
        }
        stock = {
            "producer_kind": "STOCK_WARP",
            "producer_evidence": {
                "source": {"group": 1, "map": 1, "warp": 0},
                "predecessor_tile": {"x": 4, "y": 5},
                "trigger_tile": {"x": 4, "y": 6},
                "destination": {"group": 2, "map": 10, "warp": 1},
                "arrival_tile": {"x": 9, "y": 2},
            },
        }
        self.assertEqual(
            _map_lifecycle_player_position_fixture(stock, topology),
            {"x": 9, "y": 2, "group": 2, "map": 10},
        )
        engine = {
            "producer_kind": "ENGINE_TELEPORT",
            "producer_evidence": {
                "destination": {"group": 2, "map": 10},
                "start_tile": {"x": 30, "y": 16},
            },
        }
        self.assertEqual(
            _map_lifecycle_player_position_fixture(engine, topology),
            {"x": 30, "y": 16, "group": 2, "map": 10},
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "MAP_PLAYER_POSITION_DESTINATION_IDENTITY_MISMATCH",
        ):
            _map_lifecycle_player_position_fixture({
                **stock,
                "producer_evidence": {
                    **stock["producer_evidence"],
                    "destination": {"group": 2, "map": 11, "warp": 1},
                },
            }, topology)

    @staticmethod
    def _player_position_context(
        fixture: object,
        *, interaction_group: int = 3,
        interaction_map: int = 14,
    ) -> _Context:
        root = 0x08000000
        # Two dynamic getplayerpos occurrences prove that each command
        # overwrites both destinations instead of retaining a seed value.
        rom = bytes.fromhex("4204800580420480058002")
        return _Context(
            clean_rom=rom, stage61_rom=rom, semantic_report={},
            npc={
                "local_id": 3, "flag": 0,
                "group": interaction_group, "map": interaction_map,
            },
            case={
                "owner_key": "OBJECT:003/014:002",
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "interaction": {
                    "group": interaction_group, "map": interaction_map,
                    # NPC tile deliberately differs from the stance fixture.
                    "object": [9, 24],
                },
                "physical_player_position": fixture,
            },
            root=root, target_root=root, execution_root=root,
            root_plan={}, fixture=DEFAULT_FIXTURE,
            flag_mapping={}, var_mapping={}, text_assets={},
            text_provenance="SYNTHETIC_TEST", abi_index={},
            instruction_repairs={}, source_suppression_contract=None,
            stage61_script_bytes=frozenset(range(root, root + len(rom))),
        )

    def test_getplayerpos_uses_exact_stance_and_overwrites_every_time(
        self,
    ) -> None:
        context = self._player_position_context({
            "x": 9, "y": 23, "group": 3, "map": 14,
        })
        state = _execute(context)[0]
        self.assertEqual(state.vars[0x8004], 9)
        self.assertEqual(state.vars[0x8005], 23)
        self.assertEqual(
            [(row["target_id"], row["value"]) for row in state.var_writes],
            [(0x8004, 9), (0x8005, 23)] * 2,
        )
        self.assertEqual(len(state.abi_control_reads), 2)
        self.assertTrue(all(
            row["required_value"] == {
                "x": 9, "y": 23, "group": 3, "map": 14,
            }
            for row in state.abi_control_reads
        ))
        external, internal = _runtime_control_rows(
            context, state,
            owner_keys=[
                "OBJECT:003/014:002", "OBJECT:003/014:003",
            ],
            fixtures={},
        )
        self.assertEqual(internal, [])
        self.assertEqual(external[0]["owner_keys"], [
            "OBJECT:003/014:002",
        ])
        self.assertEqual(external[0]["value"], {
            "x": 9, "y": 23, "group": 3, "map": 14,
            "apply_relation": "ACTUAL_STOCK_WARP_THEN_REAL_MOVEMENT",
        })

    def test_getplayerpos_rejects_missing_partial_bool_and_map_drift(
        self,
    ) -> None:
        invalid = (
            None,
            {"x": 9, "y": 23, "group": 3},
            {"x": True, "y": 23, "group": 3, "map": 14},
            {"x": 9, "y": 23, "group": 3, "map": 15},
            {"x": 0x10000, "y": 23, "group": 3, "map": 14},
        )
        for fixture in invalid:
            with self.subTest(fixture=fixture), self.assertRaises(
                Stage61InteractionOracleError
            ):
                _execute(self._player_position_context(fixture))

    def test_physical_player_position_requires_all_shared_object_owners(
        self,
    ) -> None:
        root = 0x08174475
        owners = [{
            "owner_id": f"OBJECT:003/014:{index:03d}",
            "owner_kind": "OBJECT", "root": root,
        } for index in range(2, 8)]
        kwargs = {
            "trainer_tower_lifecycle_by_owner": {},
            "trainer_tower_visible_owner_set": set(),
            "trainer_tower_hidden_owner_set": set(),
        }
        self.assertEqual(len(_runtime_execution_representatives(
            root, owners, **kwargs,
        )), 1)
        self.assertEqual(
            [row["owner_id"] for row in _runtime_execution_representatives(
                root, owners, physical_context_required=True, **kwargs,
            )],
            [row["owner_id"] for row in owners],
        )

    def test_trainer_tower_shared_roots_probe_only_natural_visible_contexts(
        self,
    ) -> None:
        root = 0x0816E06D
        owners = [{
            "owner_id": f"OBJECT:002/{map_number:03d}:001",
            "owner_kind": "OBJECT", "root": root,
        } for map_number in range(1, 9)]
        lifecycle = {
            row["owner_id"]: {"owner_id": row["owner_id"]}
            for row in owners
        }
        visible = {
            "OBJECT:002/002:001", "OBJECT:002/003:001",
        }
        hidden = set(lifecycle) - visible
        selected = _runtime_execution_representatives(
            root, owners,
            trainer_tower_lifecycle_by_owner=lifecycle,
            trainer_tower_visible_owner_set=visible,
            trainer_tower_hidden_owner_set=hidden,
        )
        self.assertEqual(
            [row["owner_id"] for row in selected], sorted(visible),
        )
        self.assertFalse(any(
            "/005:" in row["owner_id"] or "/006:" in row["owner_id"]
            or "/007:" in row["owner_id"] or "/008:" in row["owner_id"]
            for row in selected
        ))

        # The floor-owner root also serves the roof.  Hidden floor owners must
        # not displace that live non-floor context as the representative.
        mixed = [{
            "owner_id": f"OBJECT:002/{map_number:03d}:000",
            "owner_kind": "OBJECT", "root": 0x0816E085,
        } for map_number in range(2, 10)]
        mixed_lifecycle = {
            row["owner_id"]: {"owner_id": row["owner_id"]}
            for row in mixed if "/009:" not in row["owner_id"]
        }
        selected = _runtime_execution_representatives(
            0x0816E085, mixed,
            trainer_tower_lifecycle_by_owner=mixed_lifecycle,
            trainer_tower_visible_owner_set=set(),
            trainer_tower_hidden_owner_set=set(mixed_lifecycle),
        )
        self.assertEqual(
            [row["owner_id"] for row in selected],
            ["OBJECT:002/009:000"],
        )

    def test_runtime_owner_npc_preserves_semantic_map_identity(self) -> None:
        stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        owner = deepcopy(next(
            row for row in inventory["owners"]
            if row["owner_id"] == "OBJECT:002/001:001"
        ))
        self.assertEqual(owner["physical_map_key"], "VEGA_STOCK:002/001")
        owner["runtime_map_key"] = "TrainerTower_1F"
        npc = _runtime_owner_npc(stage61, owner)
        self.assertEqual(
            {key: npc[key] for key in (
                "npc_id", "group", "map", "map_key", "local_id", "flag",
            )},
            {
                "npc_id": "OBJECT:002/001:001", "group": 2, "map": 1,
                "map_key": "TrainerTower_1F", "local_id": 2, "flag": 2,
            },
        )
        self.assertEqual(
            _trainer_tower_floor_index(SimpleNamespace(
                npc=npc, stage61_rom=stage61,
            )),
            0,
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "TRAINER_TOWER_JPN_MAP_IDENTITY_REQUIRED",
        ):
            _trainer_tower_floor_index(SimpleNamespace(
                npc={**npc, "map_key": owner["physical_map_key"]},
                stage61_rom=stage61,
            ))

    def test_runtime_catalog_map_identity_joins_non_object_owner(self) -> None:
        rows = [{
            "npc_id": "OBJECT:002/001:000",
            "group": 2, "map": 1, "map_key": "TrainerTower_1F",
        }, {
            "npc_id": "OBJECT:002/001:001",
            "group": 2, "map": 1, "map_key": "TrainerTower_1F",
        }]
        index = _runtime_catalog_map_key_index(rows)
        self.assertEqual(index, {(2, 1): "TrainerTower_1F"})
        npc = _runtime_owner_npc(b"", {
            "owner_id": "COORD:002/001:000", "owner_kind": "COORD",
            "group": 2, "map": 1,
            "runtime_map_key": index[(2, 1)],
        })
        self.assertEqual(npc["map_key"], "TrainerTower_1F")
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "runtime expansion NPC catalog map identity競合",
        ):
            _runtime_catalog_map_key_index([
                *rows,
                {
                    "npc_id": "OBJECT:002/001:002",
                    "group": 2, "map": 1,
                    "map_key": "FOREIGN_MAP_IDENTITY",
                },
            ])

    def test_common_runtime_binding_starts_at_physical_caller(self) -> None:
        common_root = 0x08000200
        caller_root = 0x08000100
        caller_pc = 0x08000110
        standard_table = 0x08163758
        table_record = standard_table + 2 * 4
        rom = bytearray(table_record - 0x08000000 + 4)
        rom[caller_pc - 0x08000000:caller_pc - 0x08000000 + 2] = \
            bytes.fromhex("0902")
        rom[table_record - 0x08000000:table_record - 0x08000000 + 4] = \
            common_root.to_bytes(4, "little")
        common = {
            "owner_id": "COMMON:STANDARD:002", "owner_kind": "COMMON",
            "root": common_root, "raw_root": common_root,
            "index": 2, "record_address": table_record,
            "root_field_address": table_record, "runtime_root": True,
        }
        caller = {
            "owner_id": "OBJECT:001/002:003", "owner_kind": "OBJECT",
            "root": caller_root, "runtime_root": True,
        }
        nodes = {
            caller_root: SimpleNamespace(instructions=[
                SimpleNamespace(address=caller_root),
                SimpleNamespace(address=caller_pc),
            ]),
            common_root: SimpleNamespace(instructions=[
                SimpleNamespace(address=common_root),
            ]),
        }
        graph = SimpleNamespace(
            clean_rom=bytes(rom), nodes=nodes,
            # SemanticScriptGraph intentionally does not manufacture a CFG
            # edge for callstd; the exact table entry proves that dispatch.
            distances=lambda root: {caller_root: 0}
            if root == caller_root else {common_root: 0},
        )
        physical, binding = _runtime_common_caller_execution_binding(
            common_root, [common], {caller["owner_id"]: caller}, {
                common["owner_id"]: {
                    "kind": "COMMON_CALLER_TRIGGER", "standard_index": 2,
                    "root_pc": common_root,
                    "caller_owner_id": caller["owner_id"],
                    "caller_owner_kind": "OBJECT",
                    "caller_instruction_pc": caller_pc,
                    "caller_trigger_path": {
                        "kind": "OBJECT_FACE_A", "root_pc": caller_root,
                    },
                },
            }, graph,
        )
        self.assertIs(physical, caller)
        self.assertEqual(binding["execution_root"], caller_root)
        self.assertEqual(
            binding["required_trace_pair"], [caller_pc, common_root],
        )
        self.assertEqual(binding["caller_instruction_raw_hex"], "0902")
        self.assertEqual(binding["standard_table_record"], table_record)
        self.assertTrue(
            binding["standard_dispatch_proven_by_exact_table_entry"]
        )
        self.assertFalse(binding["semantic_graph_standard_edge_required"])
        self.assertTrue(binding["direct_common_root_execution_forbidden"])

        drifted_rom = bytearray(rom)
        drifted_rom[
            table_record - 0x08000000:table_record - 0x08000000 + 4
        ] = (common_root + 4).to_bytes(4, "little")
        drifted_graph = SimpleNamespace(
            clean_rom=bytes(drifted_rom), nodes=nodes,
            distances=graph.distances,
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "COMMON_RUNTIME_CALLER_TABLE_DISPATCH_MISMATCH:",
        ):
            _runtime_common_caller_execution_binding(
                common_root, [common], {caller["owner_id"]: caller}, {
                    common["owner_id"]: {
                        "kind": "COMMON_CALLER_TRIGGER", "standard_index": 2,
                        "root_pc": common_root,
                        "caller_owner_id": caller["owner_id"],
                        "caller_owner_kind": "OBJECT",
                        "caller_instruction_pc": caller_pc,
                        "caller_trigger_path": {
                            "kind": "OBJECT_FACE_A", "root_pc": caller_root,
                        },
                    },
                }, drifted_graph,
            )

    def test_runtime_var_read_before_later_write_remains_external(self) -> None:
        # Silph Co.'s elevator reads VAR_ELEVATOR_FLOOR to decide whether a
        # move is needed, then writes the selected floor.  Final membership in
        # written_vars must not relabel that earlier physical pre-state read as
        # an internal reaching definition.
        read_pc, write_pc = 0x081685FB, 0x081686C9
        state = _Execution(pc=write_pc + 5)
        state.execution_trace = [read_pc, write_pc]
        state.control_reads = [{
            "kind": "VAR", "id": 0x403A, "source_id": 0x403A,
            "value": 10, "read_address": f"0x{read_pc:08X}",
        }]
        state.written_vars = {0x403A}
        state.var_writes = [{
            "source_id": 0x403A, "target_id": 0x403A, "value": 14,
            "instruction_address": write_pc,
            "execution_trace_index": 1, "token_index": 0,
        }]
        context = SimpleNamespace(
            stage61_rom=(
                ROOT / "build/stages/61_display_npc_event_audit.gba"
            ).read_bytes(),
            case={"owner_key": "BG:001/058:000"},
            npc={"flag": 0},
        )
        fixtures: dict[str, dict] = {}
        external, internal = _runtime_control_rows(
            context, state, owner_keys=["BG:001/058:000"],
            fixtures=fixtures,
        )
        self.assertEqual(internal, [])
        self.assertEqual([
            (row["kind"], row["id"], row["value"])
            for row in external
        ], [("VAR", 0x403A, 10)])
        self.assertEqual(fixtures, {})

    def test_physical_trigger_requirements_filter_shared_root_paths(self) -> None:
        coord_zero = {
            "kind": "COORD_STEP", "trigger_var": 0x407B,
            "trigger_value": 0,
        }
        coord_fourteen = {
            "kind": "COORD_STEP", "trigger_var": 0x407B,
            "trigger_value": 14,
        }
        map_condition = {
            "kind": "MAP_TRANSITION_LOAD", "root_subkind": "CONDITION",
            "left_operand": 0x4079, "right_operand": 8,
            "required_relation": "EQUAL", "precedence_guards": [],
        }
        common = {
            "kind": "COMMON_CALLER_TRIGGER",
            "caller_trigger_path": map_condition,
        }
        self.assertEqual(
            _runtime_trigger_var_requirements(coord_zero), {0x407B: 0},
        )
        self.assertEqual(
            _runtime_trigger_var_requirements(common), {0x4079: 8},
        )
        self.assertEqual(_runtime_trigger_var_requirements({
            "kind": "MAP_TRANSITION_LOAD", "root_subkind": "DIRECT",
        }), {})
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "physical trigger VAR/value不正",
        ):
            _runtime_trigger_var_requirements({
                **map_condition, "right_operand": 0x4000,
            })

        external_zero = [{
            "kind": "VAR", "id": 0x407B, "value": 0,
            "owner_keys": [], "relation_evidence": [], "fixture_keys": [],
        }]
        self.assertTrue(_runtime_path_matches_physical_trigger(
            external_zero, coord_zero,
        ))
        self.assertFalse(_runtime_path_matches_physical_trigger(
            external_zero, coord_fourteen,
        ))
        # An unread trigger variable is intentionally absent from the concrete
        # path requirements; the field engine may set it without changing the
        # root's behavior.
        self.assertTrue(_runtime_path_matches_physical_trigger(
            [], coord_fourteen,
        ))

        owners = [
            {"owner_id": "COORD:001/001:000"},
            {"owner_id": "COORD:001/001:001"},
            {"owner_id": "MAP:001/001:000:000"},
        ]
        paths = {
            owners[0]["owner_id"]: coord_zero,
            owners[1]["owner_id"]: coord_fourteen,
            owners[2]["owner_id"]: map_condition,
        }
        self.assertEqual(_runtime_physical_trigger_var_domains(
            owners, paths,
        ), {0x4079: [8], 0x407B: [0, 14]})
        self.assertEqual(_runtime_physical_trigger_var_seeds(
            owners, paths,
        ), [{0x4079: 8}, {0x407B: 0}, {0x407B: 14}])
        self.assertEqual(_runtime_physical_trigger_var_seeds(
            [{"owner_id": "OBJECT:001/001:001", "owner_kind": "OBJECT"}],
            {},
        ), [{}])

    def test_seed_discovery_starts_from_exact_correlated_physical_vectors(
        self,
    ) -> None:
        root = 0x0868D390
        owner = {"owner_id": "COORD:001/001:000", "root": root}

        def context_factory(*_args, **kwargs):
            variables = {
                int(row["id"]): int(row["value"])
                for row in kwargs.get("state", {}).get("vars", [])
            }
            return SimpleNamespace(seed_vars=variables)

        def execute(context):
            if 0x407B not in context.seed_vars:
                raise Stage61InteractionOracleError(
                    "CONTROL_REQUIREMENT_MISSING:VAR:0x407B:read@0x0868D390"
                )
            state = _Execution(pc=root + 1)
            state.vars = dict(context.seed_vars)
            return [state]

        with patch(
            "tools.stage61_interaction_oracle._event_design_rank_call_addresses",
            return_value=[],
        ), patch(
            "tools.stage61_interaction_oracle._static_control_domains",
            return_value=([{
                "kind": "VAR", "id": 0x407B,
                "candidate_values": [0, 1, 0xFFFF],
            }], []),
        ), patch(
            "tools.stage61_interaction_oracle._runtime_context",
            side_effect=context_factory,
        ), patch(
            "tools.stage61_interaction_oracle._execute", side_effect=execute,
        ), patch(
            "tools.stage61_interaction_oracle._runtime_execution_identity",
            side_effect=lambda state: f"seed-{state.vars[0x407B]}",
        ):
            executions, blockers = _runtime_execute_with_seed_discovery(
                b"", b"", b"", {}, owner, SimpleNamespace(), {}, {}, {},
                shared_script_bytes=frozenset(), shared_root_plan={},
                physical_trigger_var_seeds=[
                    {0x407B: value} for value in range(15)
                ],
            )
        self.assertEqual(blockers, [])
        self.assertEqual({
            state.vars[0x407B] for _context, state in executions
        }, set(range(15)))

    def test_exact_cardinality_detects_duplicate_and_unknown_owner(self) -> None:
        owners = [{"owner_id": "BG:001/001:000"}]
        self.assertEqual(_runtime_case_cardinality_findings(
            owners, {"BG:001/001:000": 2},
            {"BG:001/001:000": ["case-a", "case-b"]},
        ), [])
        findings = _runtime_case_cardinality_findings(
            owners, {"BG:001/001:000": 2}, {
                "BG:001/001:000": ["case-a", "case-a"],
                "BG:999/999:999": ["case-extra"],
            },
        )
        self.assertEqual([row["kind"] for row in findings], [
            "RUNTIME_CASE_CARDINALITY_MISMATCH",
            "RUNTIME_CASE_OWNER_NOT_IN_FINAL_INVENTORY",
        ])


def _current_stage61_interaction_fixture() -> tuple:
    """同じ現行候補にROM・semantic・all-event inventoryを結び付ける。"""
    from scripts.regenerate_stage61_unit_state import ensure_stage61_state_fixture
    from tools.stage61_interaction_oracle import build_all_event_owner_inventory

    fixture_root = ensure_stage61_state_fixture()
    stage61 = (
        fixture_root / "build/stages/61_display_npc_event_audit.gba"
    ).read_bytes()
    groups = json.loads(
        (ROOT / "vendor/upstream/pokefirered/data/maps/map_groups.json")
        .read_text()
    )
    source_coordinates = {
        name: (group, number)
        for group, group_name in enumerate(groups["group_order"])
        for number, name in enumerate(groups[group_name])
    }
    physical_maps = [{
        "group": group, "map": number,
        # 数値identityをcleanのmap名へ結び付けないこと自体がfixture契約。
        "map_key": f"VEGA_STOCK:{group:03d}/{number:03d}",
        "provenance": "VEGA_STOCK",
    } for group, group_name in enumerate(groups["group_order"])
      for number, _name in enumerate(groups[group_name])]
    for path in sorted((ROOT / "generated/maps/kanto").glob("*.json")):
        if path.name == "index.json":
            continue
        value = json.loads(path.read_text())
        header = value.get("map_header", {})
        if header.get("scope_decision") not in {"INCLUDE", "REBUILD"}:
            continue
        source_group, source_map = source_coordinates[header["source_map"]]
        physical_maps.append({
            "group": int(header["group_id"]),
            "map": int(header["map_id"]),
            "map_key": str(header["map_key"]),
            "provenance": "IMPORTED_KANTO",
            "source_group": source_group, "source_map": source_map,
            "source_map_name": str(header["source_map"]),
        })
    owner_ledger = json.loads(
        (ROOT / "reports/generated/world_runtime_owner_ledger.json").read_text()
    )
    # 復元済み旧reportのrom_sha256やPASSを転記せず、実ROMから全ownerを再decode。
    # unit専用候補であり、Stage60監査や通常releaseの完了認定には使わない。
    inventory = build_all_event_owner_inventory(stage61, physical_maps, owner_ledger)
    return fixture_root, stage61, physical_maps, owner_ledger, inventory


class Stage61InteractionOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        (
            fixture_root, cls.stage61, cls.physical_maps,
            cls.owner_ledger, cls.event_owner_inventory,
        ) = _current_stage61_interaction_fixture()
        cls.clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        cls.stage60 = (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes()
        cls.semantic = json.loads(
            (fixture_root / "reports/generated/stage61_event_semantic_relocation.json").read_text()
        )
        cls.catalog = json.loads(
            (ROOT / "reports/generated/stage61_npc_interaction_catalog_legacy.json").read_text()
        )
        cls.matrix = json.loads(
            (ROOT / "reports/generated/stage61_npc_state_matrix.json").read_text()
        )
        cls.repair_manifest = json.loads(
            (ROOT / "reports/generated/stage61_interaction_repair_manifest.json")
            .read_text()
        )
        cls.case_by_id = {row["case_id"]: row for row in cls.matrix["cases"]}
        cls.cases_by_owner = {
            owner: [row for row in cls.matrix["cases"] if row["owner_key"] == owner]
            for owner in {row["owner_key"] for row in cls.matrix["cases"]}
        }
        cls.integrity = audit_runtime_graph_integrity(cls.stage61, cls.catalog)
        cls.stage60_negative = audit_pinned_stage60_project_negative_integrity(
            cls.stage60, cls.catalog,
        )
        cls.stage61_positive = audit_repaired_stage61_runtime_integrity(
            cls.stage61, cls.catalog, cls.repair_manifest,
        )
        cls.coverage = audit_all_cases(
            cls.clean, cls.stage61, cls.semantic, cls.catalog,
            cls.matrix["cases"], require_complete=False,
        )
        cls.all_event_integrity = audit_all_event_owner_integrity(
            cls.clean, cls.stage60, cls.stage61, cls.semantic, cls.catalog,
            cls.owner_ledger, cls.physical_maps, require_complete=False,
        )

    @classmethod
    def pinned_abi_inputs(cls):
        source_paths = [
            ROOT / "vendor/upstream/pokefirered/data/specials.inc",
            ROOT / "vendor/upstream/pokefirered/data/scripts/obtain_item.inc",
            ROOT / "vendor/upstream/pokefirered/include/global.h",
            ROOT / "vendor/upstream/pokefirered/include/constants/maps.h",
            ROOT / "scripts/build_stage61_display_npc_event_audit.py",
            ROOT / "content/trainer_changekit_final/trainer_dialogue.csv",
            ROOT / "generated/runtime/"
            "trainer_changekit_final_serialized.json",
            ROOT / "overlays/trainer_changekit_final_runtime/"
            "trainer_changekit_final_runtime.c",
            *sorted((ROOT / "vendor/upstream/pokefirered/src").glob("*.c")),
            *(ROOT / path for path in (
                "overlays/qol_b/qol_b.c",
                "overlays/move_memory/move_memory.c",
                "overlays/acquisition_runtime/acquisition_engine_adapter_rom.c",
                "vendor/vega_acquisition/generated/acquisition_host_wrappers.c",
                "overlays/qol_production/qol_production.c",
                "overlays/qol_production/qol_production.h",
                "overlays/event_design/event_design.c",
                "content/event_design_implementation/event_plan.json",
                "generated/runtime/event_design_serialized.json",
                "generated/runtime/event_design_generated.h",
                "config/qol_production_bindings.csv",
                "content/trainer_changekit_final/trainer_runtime_consumers.csv",
                "overlays/mirage_production/mirage_production.c",
                "overlays/research_economy_v1/research_economy_v1.c",
                "overlays/research_economy_v1/research_economy_v1.h",
                "overlays/reward_encounters_v2/reward_encounters_v2.c",
                "overlays/factory_high_modes_v2/factory_high_modes_v2.c",
                "overlays/codex_battle_runtime/codex_battle_runtime.c",
                "overlays/codex_battle_rewards/codex_battle_rewards.c",
                "overlays/facility_runtime/facility_runtime.c",
                "overlays/collection_supply_v1/collection_supply_v1.c",
                "tools/world_runtime_e2e_repair.py",
                "scripts/build_stage58_qol_world_convenience_debug.py",
            )),
        ]
        source_blobs = {
            str(path.relative_to(ROOT)): path.read_bytes() for path in source_paths
        }
        reports = {
            str(path.relative_to(ROOT)): json.loads(path.read_text())
            for path in sorted((ROOT / "generated/runtime").glob("*symbols.json"))
        }
        return source_blobs, reports

    def test_production_loader_pins_ram_script_layout_and_map_sentinel(self) -> None:
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph
        from tools.stage61_interaction_oracle import (
            _independent_runtime_text_assets,
        )

        source_blobs, _reports = _interaction_abi_pinned_inputs()
        required = (
            "vendor/upstream/pokefirered/include/global.h",
            "vendor/upstream/pokefirered/include/constants/maps.h",
        )
        for path in required:
            self.assertIn(path, source_blobs)
            self.assertEqual(
                hashlib.sha256(source_blobs[path]).hexdigest(),
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
            )

            missing = dict(source_blobs)
            missing.pop(path)
            with self.subTest(path=path), self.assertRaisesRegex(
                Stage61InteractionOracleError,
                rf"signed RAM script source blob不一致:{path}",
            ):
                # The production entry point validates immutable RAM-script
                # layout/map constants before consuming the ABI manifest or
                # trigger inventory, so this is a focused fail-closed check.
                build_runtime_control_expansion_contract(
                    self.clean, self.stage61, self.semantic, self.catalog,
                    project_source_rom=self.stage60,
                    repair_manifest=self.repair_manifest,
                    interaction_abi_manifest={},
                    abi_source_blobs=missing,
                    event_owner_inventory=self.event_owner_inventory,
                    runtime_trigger_inputs=None,
                    require_complete=False,
                )

        runtime_text_sources = (
            (
                "scripts/build_stage61_display_npc_event_audit.py",
                "runtime explicit adapter source blob不一致",
            ),
            (
                "content/trainer_changekit_final/trainer_dialogue.csv",
                "runtime trainer defeat text source不一致",
            ),
        )
        # Existing artifacts correctly pin the builder generation that wrote
        # them.  Rebase only this test copy to today's loader byte identity so
        # each missing-source branch can be isolated without weakening the
        # production provenance check.
        semantic = deepcopy(self.semantic)
        builder_path = runtime_text_sources[0][0]
        builder_sha = hashlib.sha256(source_blobs[builder_path]).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        graph = SemanticScriptGraph(self.stage61)
        for path, failure in runtime_text_sources:
            self.assertIn(path, source_blobs)
            self.assertEqual(
                hashlib.sha256(source_blobs[path]).hexdigest(),
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
            )
            missing = dict(source_blobs)
            missing.pop(path)
            with self.subTest(path=path), self.assertRaisesRegex(
                Stage61InteractionOracleError, failure,
            ):
                _independent_runtime_text_assets(
                    self.clean, self.stage60, self.stage61, semantic,
                    self.repair_manifest, graph, source_blobs=missing,
                )

    def test_real_yes_no_slice_follows_callstd_and_orders_every_printer(self) -> None:
        case = self.cases_by_owner["OBJECT:096/002:005"]
        self.assertEqual(len(case), 1)
        output = build_case_oracle(
            self.clean, self.stage61, self.semantic, self.catalog, case[0],
        )
        self.assertEqual(output["source_root"], "0x08170AEA")
        expected_target = self.semantic["stage61_materialization"]["root_addresses"][
            "0x08170AEA"
        ]
        self.assertEqual(output["stage61_root"], expected_target)
        npc = next(
            row for row in self.catalog["npcs"]
            if row["npc_id"] == "OBJECT:096/002:005"
        )
        self.assertEqual(int(output["stage61_root"], 16), npc["script_pointer"])
        self.assertEqual(
            [row["tokens"] for row in output["input_sequences"]],
            [
                ["A", "ADVANCE_TEXT", "DOWN", "A", "ADVANCE_TEXT", "ADVANCE_TEXT"],
                ["A", "ADVANCE_TEXT", "A", "ADVANCE_TEXT"],
            ],
        )
        self.assertEqual(
            [[printer["source_pointer"] for printer in row["visible_printers"]]
             for row in output["sequences"]],
            [
                ["0x08170E1A", "0x083DD86A", "0x08170E48"],
                ["0x08170E1A", "0x083DD86A", "0x08170E32"],
            ],
        )
        for result, row in enumerate(output["sequences"]):
            self.assertEqual(row["visible_printers"][1]["ui_coordinates"], [20, 8])
            self.assertEqual(
                row["control_requirements"]["internal"][0]["capture"][
                    "expected_value"
                ], result,
            )
            contract = row["effect_contract"]
            self.assertTrue(contract["allowed_owner_coverage_one_to_one"])
            self.assertEqual(set(contract["domains"]), {
                "flags", "engine_special_flags", "vars", "items", "trainers", "objects", "warp",
                "battle", "money", "coins", "party", "storage",
                "berry_powder",
            })
        sequence_ids = [row["sequence_id"] for row in output["input_sequences"]]
        self.assertEqual(len(sequence_ids), len(set(sequence_ids)))
        self.assertTrue(all(value.startswith(case[0]["case_id"] + "--seq-")
                            for value in sequence_ids))
        for row in output["input_sequences"]:
            self.assertIn("text_oracle", row)
            self.assertIn("required_postconditions", row)
            self.assertEqual(row["visible_text_expected"],
                             bool(row["text_oracle"]["visible_text_count"]))
        self.assertTrue(all(output["assertions"].values()))

    def test_batch_api_requires_a_real_oracle_for_every_requested_case(self) -> None:
        supported = self.cases_by_owner["OBJECT:096/002:005"][0]
        unsupported = self.case_by_id["matrix-096-001-010-default-002"]
        output = build_all_case_oracles(
            self.clean, self.stage61, self.semantic, self.catalog,
            [unsupported, supported], require_complete=False,
        )
        self.assertEqual(output["case_count"], 2)
        self.assertEqual(output["generated_case_count"], 1)
        self.assertEqual(output["unresolved_case_count"], 1)
        self.assertEqual(output["cases"][0]["case_id"], supported["case_id"])
        self.assertEqual(
            output["unresolved"][0]["category"],
            "SPECIAL_OR_NATIVE_ABI_REQUIRED",
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "ALL_CASE_ORACLE_UNRESOLVED",
        ):
            build_all_case_oracles(
                self.clean, self.stage61, self.semantic, self.catalog,
                [unsupported, supported], require_complete=True,
            )

    def test_hidden_case_oracle_retains_catalog_derived_stage61_root(
        self,
    ) -> None:
        hidden = next(
            row for row in self.matrix["cases"]
            if row["interaction_expected"] is False
        )
        npc = next(
            row for row in self.catalog["npcs"]
            if row["npc_id"] == hidden["owner_key"]
        )
        output = build_all_case_oracles(
            self.clean, self.stage61, self.semantic, self.catalog,
            [hidden], require_complete=True,
        )
        self.assertEqual(output["unresolved"], [])
        self.assertEqual(output["generated_case_count"], 1)
        self.assertEqual(
            output["cases"][0]["stage61_root"],
            f"0x{npc['script_pointer']:08X}",
        )
        self.assertEqual(
            output["cases"][0]["stage61_root"],
            hidden["interaction"]["runtime_root"],
        )

    def test_batch_rejects_missing_or_out_of_rom_catalog_script_pointer(
        self,
    ) -> None:
        hidden = next(
            row for row in self.matrix["cases"]
            if row["interaction_expected"] is False
        )
        for label, mutate in (
            ("missing", lambda row: row.pop("script_pointer")),
            ("outside", lambda row: row.update({"script_pointer": 0x0A000000})),
        ):
            catalog = deepcopy(self.catalog)
            mutate(catalog["npcs"][0])
            with self.subTest(label=label), self.assertRaises(
                Stage61InteractionOracleError,
            ):
                build_all_case_oracles(
                    self.clean, self.stage61, self.semantic, catalog,
                    [hidden], require_complete=False,
                )

    def test_batch_rejects_missing_or_drifted_matrix_runtime_root(self) -> None:
        hidden = next(
            row for row in self.matrix["cases"]
            if row["interaction_expected"] is False
        )
        for label, mutate in (
            ("missing", lambda row: row["interaction"].pop("runtime_root")),
            ("drift", lambda row: row["interaction"].update({
                "runtime_root": "0x08000001",
            })),
            ("xy-drift", lambda row: row["interaction"].update({
                "object": [
                    row["interaction"]["object"][0] + 1,
                    row["interaction"]["object"][1],
                ],
            })),
        ):
            case = deepcopy(hidden)
            mutate(case)
            with self.subTest(label=label), self.assertRaisesRegex(
                Stage61InteractionOracleError, "xy/runtime-root不一致",
            ):
                build_all_case_oracles(
                    self.clean, self.stage61, self.semantic, self.catalog,
                    [case], require_complete=False,
                )

    def test_decision_coverage_detects_fossil_and_celadon_missing_option_sets(self) -> None:
        # 各siteの全menu resultは含めるが、state matrixで欠落していた三つの
        # option-set siteだけを意図的に省く。menu IDだけでなくinstruction siteを
        # identityにするため、同じchoice countでも取り違えられない。
        sites = {
            "OBJECT:098/047:001": {
                0x08184007: 2, 0x08184033: 2, 0x0818405F: 3,
                # 0x08184096(mask3) / 0x081840C2(mask4) are omitted.
                0x081840F9: 3, 0x08184130: 4,
            },
            "OBJECT:098/076:001": {
                0x08189311: 2, 0x08189353: 2, 0x08189385: 2,
                # 0x081893B1(Helix+Amber) is omitted.
                0x081893E8: 3,
            },
        }
        generated = []
        for owner, rows in sites.items():
            sequences = []
            for address, count in rows.items():
                for value in list(range(count)) + [127]:
                    sequences.append({
                        "decision_trace": [{
                            "kind": "MULTICHOICE_CANCEL" if value == 127
                            else "MULTICHOICE",
                            "instruction_address": f"0x{address:08X}",
                            "result_value": value,
                        }],
                    })
            generated.append({"owner_key": owner, "sequences": sequences})
        selected_cases = [
            self.cases_by_owner[owner][0] for owner in sorted(sites)
        ]
        output = audit_generated_decision_coverage(
            self.clean, self.stage60, self.catalog, selected_cases,
            generated, self.repair_manifest, require_complete=False,
        )
        self.assertEqual(output["missing_signature_count"], 3)
        self.assertEqual(
            {row["instruction_address"] for row in output["missing_signatures"]},
            {"0x08184096", "0x081840C2", "0x081893B1"},
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "MATRIX_DECISION_COVERAGE_MISSING",
        ):
            audit_generated_decision_coverage(
                self.clean, self.stage60, self.catalog, selected_cases,
                generated, self.repair_manifest, require_complete=True,
            )

    def test_oracle_is_deterministic_and_never_uses_calibration_output(self) -> None:
        case = deepcopy(self.cases_by_owner["OBJECT:096/002:005"][0])
        semantic = deepcopy(self.semantic)
        catalog = deepcopy(self.catalog)
        case["mgba_calibration_output"] = {"visible_hash": "adversarial"}
        semantic["mgba_calibration_output"] = {"branch": 127}
        catalog["mgba_calibration_output"] = {"text": "not-an-oracle"}
        left = build_case_oracle(
            self.clean, self.stage61, semantic, catalog, case,
        )
        right = build_case_oracle(
            self.clean, self.stage61, self.semantic, self.catalog,
            self.cases_by_owner["OBJECT:096/002:005"][0],
        )
        self.assertEqual(left, right)
        self.assertTrue(
            left["assertions"]["expected_text_independent_of_mgba_calibration"]
        )

    def test_placeholder_fixture_is_fixed_and_unknown_values_fail_closed(self) -> None:
        self.assertEqual(
            expand_placeholders(b"\xFD\x01\xFF"),
            DEFAULT_FIXTURE.placeholders()[1],
        )
        self.assertEqual(
            expand_placeholders(b"\xFD\x04\xFF").hex(), "cec2ccbfbfff",
        )
        self.assertEqual(expand_placeholders(b"\xFD\x05\xFF"), b"\xFF")
        with self.assertRaisesRegex(Stage61InteractionOracleError, "placeholder"):
            expand_placeholders(b"\xFD\x08\xFF")
        with self.assertRaisesRegex(Stage61InteractionOracleError, "0xF7"):
            expand_placeholders(b"\xF7\x00\xFF")

    def test_unknown_special_is_not_misreported_as_a_dialogue_pass(self) -> None:
        case = self.case_by_id["matrix-096-001-010-default-002"]
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "SPECIAL_OR_NATIVE_ABI_REQUIRED",
        ):
            build_case_oracle(
                self.clean, self.stage61, self.semantic, self.catalog, case,
            )

    def test_project_dialogue_uses_pinned_stage60_cfg_not_stage61_observation(self) -> None:
        owner = "OBJECT:001/000:023"
        case = self.cases_by_owner[owner][0]
        manifest = build_project_source_manifest_skeleton(
            self.stage60, self.stage61, self.catalog, owner_keys=[owner],
        )
        output = build_case_oracle(
            self.clean, self.stage61, self.semantic, self.catalog, case,
            project_source_rom=self.stage60, repair_manifest=manifest,
        )
        self.assertEqual(output["source_root"], "0x087FF884")
        self.assertEqual(output["input_sequences"][0]["tokens"], [
            "A", "ADVANCE_TEXT",
        ])
        self.assertIn("PINNED_STAGE60_PROJECT_RAW", output["text_oracle"]["meaning_source"])
        self.assertEqual(
            output["sequences"][0]["visible_printers"][0]["provenance"][
                "kind"
            ],
            "PINNED_STAGE60_PROJECT_RAW",
        )
        self.assertFalse(
            manifest["assertions"]["expected_text_derived_from_stage61_or_calibration"]
        )
        tampered = deepcopy(manifest)
        tampered["owner_roots"][owner]["reachable_instruction_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "owner evidence不一致",
        ):
            build_case_oracle(
                self.clean, self.stage61, self.semantic, self.catalog, case,
                project_source_rom=self.stage60, repair_manifest=tampered,
            )

    def test_stage60_manifest_covers_every_owner_without_clean_source(self) -> None:
        manifest = build_project_source_manifest_skeleton(
            self.stage60, self.stage61, self.catalog,
        )
        expected = {
            row["npc_id"] for row in self.catalog["npcs"]
            if row.get("source_script_pointer") is None
        }
        self.assertEqual(set(manifest["owner_roots"]), expected)
        self.assertEqual(len(expected), 2629)
        self.assertIn("OBJECT:001/000:002", manifest["owner_roots"])  # TRAINER
        self.assertIn("OBJECT:096/016:000", manifest["owner_roots"])  # thin native
        self.assertFalse(
            manifest["assertions"]["expected_text_derived_from_stage61_or_calibration"]
        )

    def test_stage60_negative_bag_full_text_as_script_signature_is_pinned(self) -> None:
        findings = self.stage60_negative["negative_audit"]["findings"]
        relevant = [row for row in findings if row.get("target") == "0x0817FC1D"]
        self.assertEqual(
            Counter(row["kind"] for row in relevant),
            Counter({
                "SCRIPT_EDGE_TEXT_INTERVAL_OVERLAP": 7,
                "SCRIPT_NODE_TEXT_INTERVAL_OVERLAP": 7,
            }),
        )
        native = [
            row for row in findings
            if row["kind"] == "NATIVE_POINTER_OUTSIDE_ROM"
            and row.get("instruction") == "0x0817FC1D"
        ]
        self.assertEqual(len(native), 7)
        self.assertEqual({row["pointer"] for row in native}, {"0x37192311"})
        affected = {
            owner for row in relevant + native for owner in row["affected_owners"]
        }
        self.assertEqual(affected, {
            "OBJECT:005/001:001", "OBJECT:007/005:002",
            "OBJECT:007/005:010", "OBJECT:009/006:000",
            "OBJECT:010/016:006", "OBJECT:011/003:006",
            "OBJECT:012/000:007", "OBJECT:014/003:005",
        })

    def test_stage60_negative_visible_eos_fields_are_runtime_consumers(self) -> None:
        negative = self.stage60_negative["negative_audit"]
        summary = negative["eos_only_visible_summary"]
        self.assertEqual(summary, {
            "pointer_count": 2, "instruction_count": 479,
            "owner_count": 270, "map_count": 46,
            "allowlisted_nonconsumer_count": 0,
        })
        empty = [
            row for row in negative["findings"]
            if row["kind"] == "VISIBLE_TEXT_EOS_ONLY"
        ]
        msgbox = [row for row in empty if row["pointer"] == "0x08AAAAAA"]
        trainer = [row for row in empty if row["pointer"] == "0x09363D90"]
        self.assertEqual(len(msgbox), 2)
        self.assertEqual({row["reference_kind"] for row in msgbox}, {"msgbox_loadword0"})
        self.assertEqual(len(trainer), 477)
        self.assertEqual(
            Counter(row["trainerbattle_type"] for row in trainer),
            Counter({0: 228, 4: 21, 5: 205, 6: 2, 7: 21}),
        )
        self.assertEqual(
            {row["runtime_consumer"] for row in trainer},
            {"ShowTrainerIntroSpeech"},
        )
        self.assertEqual(
            len({owner for row in trainer for owner in row["affected_owners"]}), 268,
        )

    def test_stage60_negative_bad_callstd_signature_is_pinned(self) -> None:
        findings = [
            row for row in self.stage60_negative["negative_audit"]["findings"]
            if row["kind"] == "STANDARD_SCRIPT_INDEX_OUT_OF_BOUNDS"
        ]
        self.assertEqual(
            {row["instruction"] for row in findings},
            {
                "0x08754EA9", "0x0876A6B2", "0x087CA029",
                "0x088B31CD", "0x08E240A7",
            },
        )
        self.assertEqual({row["standard_index"] for row in findings}, {0x66})
        self.assertEqual(
            len({root for row in findings for root in row["affected_roots"]}), 8,
        )
        self.assertFalse(
            self.stage60_negative["negative_audit"]["assertions"][
                "standard_script_indices_and_targets_bounded"
            ]
        )

    def test_special_native_inventory_separates_control_and_effect_abi(self) -> None:
        inventory = self.integrity["special_native_inventory"]
        self.assertEqual(inventory["site_count"], 1480)
        self.assertEqual(inventory["kind_counts"], {
            "CALLNATIVE": 609, "SPECIAL": 501, "SPECIALVAR": 370,
        })
        self.assertNotIn("0x37192311", inventory["native_target_counts"])
        self.assertEqual(len(inventory["native_target_counts"]), 75)
        self.assertEqual(len(inventory["special_id_counts"]), 135)
        self.assertEqual(inventory["special_id_counts"]["SPECIALVAR:0039"], 232)
        # The legacy graph is OBJECT-only.  Hidden-item SPECIAL 350 must not
        # be fabricated into it; the all-event ABI audit below adds the exact
        # stock hidden consumer as an independently pinned engine root.
        self.assertNotIn("SPECIALVAR:015E", inventory["special_id_counts"])
        self.assertTrue(all(
            row["control_role"] == "EXPLICIT_EVENT_VAR_PRODUCER"
            for row in inventory["sites"] if row["kind"] == "SPECIALVAR"
        ))
        self.assertTrue(all(
            row.get("target_in_rom", True) for row in inventory["sites"]
        ))

    def test_all_event_owner_integrity_enumerates_final_headers_not_legacy_rows(self) -> None:
        output = self.all_event_integrity
        self.assertEqual(output["physical_map_count"], 678)
        self.assertEqual(output["physical_provenance_counts"], {
            "IMPORTED_KANTO": 253, "VEGA_STOCK": 425,
        })
        # Stage54 ledgerのOBJECT 3093/BG 1422を流用せず、Stage61 final headerを
        # 構造抽出した値。NULL/non-script templateもtotalへ残す。
        self.assertEqual(output["event_template_counts"], {
            "BG": 1436, "COORD": 1231, "OBJECT": 3112,
        })
        self.assertEqual(output["runtime_owner_counts"], {
            "BG": 949, "COMMON": 10, "COORD": 648,
            "MAP": 628, "OBJECT": 3108,
        })
        self.assertEqual(output["unique_runtime_root_counts"], {
            "BG": 732, "COMMON": 10, "COORD": 188,
            "MAP": 262, "OBJECT": 2466,
        })
        self.assertEqual(output["runtime_root_count"], 3657)
        self.assertEqual(output["runtime_graph_node_count"], 11878)
        self.assertEqual(output["untested_owner_count"], 0)
        self.assertEqual(output["unresolved_owner_count"], 0)
        imported = output["imported_kanto_provenance"]
        self.assertEqual(imported["map_count"], 253)
        self.assertEqual(imported["semantic_clean_and_final_verified_count"], 844)
        self.assertEqual(
            imported["clean_coord_roots_explicitly_suppressed_by_stage60_policy"],
            152,
        )
        self.assertEqual(imported["clean_address_alias_count"], 0)
        self.assertTrue(output["assertions"]["source_direct_remaining_zero"])
        self.assertTrue(
            output["assertions"]["all_6417_event_owner_structures_checked"]
        )
        self.assertEqual(output["runtime_trigger_scope"], {
            "all_event_owner_count": 6417,
            "script_runtime_owner_count": 5342,
            "hidden_item_runtime_owner_count": 74,
            "runtime_case_required_count": 5416,
            "structural_nontrigger_count": 1001,
            "coverage_contract_api":
                "build_runtime_control_expansion_contract",
            "static_integrity_is_not_runtime_acceptance": True,
        })

    def test_all_event_integrity_is_clean_after_explicit_repairs(self) -> None:
        output = self.all_event_integrity
        self.assertEqual(output["finding_count"], 0)
        self.assertEqual(output["finding_kind_counts"], {})
        self.assertTrue(all(output["assertions"].values()))
        strict = audit_all_event_owner_integrity(
            self.clean, self.stage60, self.stage61, self.semantic,
            self.catalog, self.owner_ledger, self.physical_maps,
            require_complete=True,
        )
        self.assertEqual(strict["status"], "PASS")

    def test_stage60_negative_and_stage61_positive_audits_are_separate(self) -> None:
        negative = self.stage60_negative
        positive = self.stage61_positive
        self.assertEqual(negative["negative_audit"]["finding_count"], 505)
        self.assertEqual(negative["negative_audit"]["finding_kind_counts"], {
            "NATIVE_POINTER_OUTSIDE_ROM": 7,
            "SCRIPT_EDGE_TEXT_INTERVAL_OVERLAP": 7,
            "SCRIPT_NODE_TEXT_INTERVAL_OVERLAP": 7,
            "STANDARD_SCRIPT_INDEX_OUT_OF_BOUNDS": 5,
            "VISIBLE_TEXT_EOS_ONLY": 479,
        })
        self.assertEqual(positive["positive_audit"]["finding_count"], 0)
        self.assertEqual(positive["positive_audit"]["finding_kind_counts"], {})
        self.assertTrue(all(negative["assertions"].values()))
        self.assertTrue(all(positive["assertions"].values()))

    def test_vega_stock_numeric_map_cannot_claim_clean_source_identity(self) -> None:
        malformed = deepcopy(self.physical_maps)
        malformed[0].update({
            "source_group": 0, "source_map": 0,
            "source_map_name": "LinkRoom",
        })
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "clean source identity",
        ):
            audit_all_event_owner_integrity(
                self.clean, self.stage60, self.stage61, self.semantic,
                self.catalog, self.owner_ledger, malformed,
                require_complete=False,
            )

    def test_empty_abi_registry_cannot_resolve_any_special_or_native_site(self) -> None:
        manifest = {"special_abis": [], "native_abis": []}
        output = audit_interaction_abi_registry(
            self.stage61, self.catalog, manifest, require_complete=False,
        )
        self.assertEqual(output["site_count"], 1480)
        self.assertEqual(output["resolved_site_count"], 0)
        self.assertEqual(output["unresolved_site_count"], 1480)
        self.assertEqual(
            Counter(row["reason"] for row in output["unresolved_sites"]),
            Counter({"ABI_ENTRY_REQUIRED": 1480}),
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "INTERACTION_ABI_UNRESOLVED",
        ):
            audit_interaction_abi_registry(
                self.stage61, self.catalog, manifest, require_complete=True,
            )

    def test_pinned_abi_auto_builder_resolves_all_210_entries_and_live_sites(self) -> None:
        source_blobs, reports = self.pinned_abi_inputs()
        output = build_pinned_interaction_abi_manifest(
            self.clean, self.stage60, self.stage61, self.catalog,
            source_blobs=source_blobs, runtime_symbol_reports=reports,
        )
        self.assertEqual(len(output["special_abis"]), 135)
        self.assertEqual(len(output["native_abis"]), 75)
        self.assertEqual(output["registry_audit"]["site_count"], 1480)
        self.assertEqual(output["registry_audit"]["unresolved_site_count"], 0)
        self.assertTrue(all(output["assertions"].values()))
        self.assertEqual(
            {row["target_pointer"] for row in output["native_abis"]},
            {f"0x{int(line.split()[0], 16):08X}" for line in
             __import__("tools.stage61_interaction_oracle", fromlist=[
                 "_PINNED_NATIVE_SYMBOL_ROWS"
             ])._PINNED_NATIVE_SYMBOL_ROWS.splitlines()},
        )
        self.assertTrue(all(row["complete"] is True for row in
                            output["special_abis"] + output["native_abis"]))

    def test_special_result_writer_graph_and_pc_menu_completed_domain(
        self,
    ) -> None:
        """wrapper外Task writerとPC menuの完了resultをsource-closedに固定する。"""

        source_blobs, reports = self.pinned_abi_inputs()
        output = build_pinned_interaction_abi_manifest(
            self.clean, self.stage60, self.stage61, self.catalog,
            source_blobs=source_blobs, runtime_symbol_reports=reports,
        )
        by_id = {row["special_id"]: row for row in output["special_abis"]}
        expected = {
            61: [0, 1, 2],
            262: [0, 1, 2, 3, 4, 127],
            363: [1, 5, 8],
            364: [1, 5, 6, 8],
            402: [0, 1],
            411: [0, 1],
            438: [0, 1],
        }
        for special_id, candidates in expected.items():
            relation = by_id[special_id]["result_contract"][
                "global_var_result_write"
            ]
            self.assertEqual(relation["candidate_values"], candidates)
            evidence = relation["writer_evidence"]
            self.assertEqual(
                evidence["completed_candidate_values"], candidates,
            )
            self.assertEqual(
                sorted({
                    value
                    for function in evidence["source_functions"]
                    for site in function["write_sites"]
                    if site["phase"] != "NONTERMINAL_SENTINEL"
                    for value in site["candidate_values"]
                }),
                candidates,
            )
        self.assertEqual(
            by_id[262]["result_contract"]["global_var_result_write"]
                ["writer_evidence"]["nonterminal_candidate_values"],
            [255],
        )
        self.assertEqual(
            by_id[363]["result_contract"]["global_var_result_write"]
                ["writer_evidence"]["nonterminal_candidate_values"],
            [0],
        )
        self.assertEqual(
            by_id[364]["result_contract"]["global_var_result_write"]
                ["writer_evidence"]["nonterminal_candidate_values"],
            [0],
        )
        self.assertEqual(
            [(edge["caller"], edge["callee"])
             for edge in by_id[363]["result_contract"]
                 ["global_var_result_write"]["writer_evidence"]
                 ["ownership_edges"]],
            [
                ("TryBecomeLinkLeader", "Task_TryBecomeLinkLeader"),
                ("Task_TryBecomeLinkLeader",
                 "CreateTask_RunScriptAndFadeToActivity"),
                ("CreateTask_RunScriptAndFadeToActivity",
                 "Task_RunScriptAndFadeToActivity"),
            ],
        )
        self.assertEqual(
            [row["owner"] for row in by_id[262]["input_controls"]],
            ["FLAG:0x082C", "FLAG:0x0829"],
        )

        # Omitting the shared success task would previously leave only the
        # short wrapper span and silently drop result 1.  The closed writer
        # graph must reject that manifest before execution.
        malformed = deepcopy(output)
        malformed_363 = next(
            row for row in malformed["special_abis"]
            if row["special_id"] == 363
        )
        evidence = malformed_363["result_contract"][
            "global_var_result_write"
        ]["writer_evidence"]
        evidence["source_functions"] = [
            row for row in evidence["source_functions"]
            if row["symbol"] != "Task_RunScriptAndFadeToActivity"
        ]
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "SPECIAL363 result writer evidence不一致",
        ):
            _interaction_abi_index(
                self.stage61, malformed, source_blobs=source_blobs,
            )

        abi_index = _interaction_abi_index(
            self.stage61, output, source_blobs=source_blobs,
        )
        instruction = 0x08100000
        raw = bytes((0x25, 0x06, 0x01))  # special 0x0106 / CreatePCMenu
        expected_by_flags = {
            (False, False): [0, 1, 2, 127],
            (False, True): [0, 1, 2, 3, 127],
            (True, False): [0, 1, 2, 3, 4, 127],
            (True, True): [0, 1, 2, 3, 4, 127],
        }
        for (game_clear, pokedex), result_values in expected_by_flags.items():
            with self.subTest(game_clear=game_clear, pokedex=pokedex):
                context = _Context(
                    clean_rom=self.clean, stage61_rom=self.stage61,
                    semantic_report={}, npc={"local_id": 0},
                    case={"state": {"flags": [], "vars": [], "items": [],
                                    "trainers": []}},
                    root=instruction, target_root=instruction,
                    execution_root=instruction, root_plan={},
                    fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
                    text_assets={}, text_provenance="CLEAN_SOURCE_RAW",
                    abi_index=abi_index, instruction_repairs={},
                    source_suppression_contract=None,
                    stage61_script_bytes=frozenset(),
                )
                state = _Execution(
                    pc=instruction,
                    vars={0x800D: 255},  # wrapper sentinel / stale prior value
                    flags={0x082C: game_clear, 0x0829: pokedex},
                    execution_trace=[instruction],
                    current_instruction_address=instruction,
                    current_opcode=0x25,
                )
                branches = _fork_abi_command(
                    context, state, instruction, 0x25, raw,
                )
                self.assertEqual(
                    [branch.vars[0x800D] for branch in branches],
                    result_values,
                )
                self.assertNotIn(255, {
                    branch.vars[0x800D] for branch in branches
                })
                self.assertEqual(branches[-1].tokens[-1], "B")
                self.assertTrue(all(
                    branch.decisions[-1]["stale_sentinel_excluded"] == 255
                    for branch in branches
                ))

        # SetSeenMon is one exact species-table transform followed by the same
        # OR mask in all three physical seen mirrors.  It neither writes
        # VAR_RESULT nor keeps the old broad battle/flags effect approximation.
        set_seen = by_id[355]
        set_seen_contract = set_seen["effect_contract"]
        self.assertEqual(set_seen["effects"], [{
            "domain": "save", "owner": "SAVE_BLOCK2_POKEDEX_SEEN",
            "relation": "OR_NATIONAL_DEX_SEEN_MASK_EXACT",
        }, {
            "domain": "save", "owner": "SAVE_BLOCK1_SEEN_PRIMARY",
            "relation": "OR_NATIONAL_DEX_SEEN_MASK_EXACT",
        }, {
            "domain": "save", "owner": "SAVE_BLOCK1_SEEN_SECONDARY",
            "relation": "OR_NATIONAL_DEX_SEEN_MASK_EXACT",
        }])
        self.assertEqual(
            [(row["species"], row["national"], row["byte_index"], row["mask"])
             for row in set_seen_contract["bill_projection"]["choices"]],
            [
                (0x01E3, 133, 16, 0x10),
                (0x01E6, 136, 16, 0x80),
                (0x01E5, 135, 16, 0x40),
                (0x01E4, 134, 16, 0x20),
            ],
        )
        self.assertEqual(
            [row["base_offset"] for row in set_seen_contract["mirrors"]],
            [0x005C, 0x05F8, 0x3A18],
        )
        set_seen_raw = bytes((0x25, 0x63, 0x01))
        for species, national, mask in (
            (0x01E3, 133, 0x10), (0x01E6, 136, 0x80),
            (0x01E5, 135, 0x40), (0x01E4, 134, 0x20),
        ):
            with self.subTest(set_seen_species=species):
                context = _Context(
                    clean_rom=self.clean, stage61_rom=self.stage61,
                    semantic_report={}, npc={"local_id": 0},
                    case={"state": {"flags": [], "vars": [], "items": [],
                                    "trainers": []}},
                    root=instruction, target_root=instruction,
                    execution_root=instruction, root_plan={},
                    fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
                    text_assets={}, text_provenance="CLEAN_SOURCE_RAW",
                    abi_index=abi_index, instruction_repairs={},
                    source_suppression_contract=None,
                    stage61_script_bytes=frozenset(),
                )
                state = _Execution(
                    pc=instruction, vars={0x8004: species, 0x800D: 0xBEEF},
                    execution_trace=[instruction],
                    current_instruction_address=instruction,
                    current_opcode=0x25,
                )
                branches = _fork_abi_command(
                    context, state, instruction, 0x25, set_seen_raw,
                )
                self.assertEqual(len(branches), 1)
                branch = branches[0]
                self.assertEqual(branch.vars[0x800D], 0xBEEF)
                self.assertEqual(
                    [row["owner"] for row in branch.effects],
                    [
                        "SAVE_BLOCK2_POKEDEX_SEEN",
                        "SAVE_BLOCK1_SEEN_PRIMARY",
                        "SAVE_BLOCK1_SEEN_SECONDARY",
                    ],
                )
                self.assertEqual(
                    [(row["national_dex_number"], row["byte_index"],
                      row["mask"], row["byte_offset"], row["operation"])
                     for row in branch.effects],
                    [
                        (national, 16, mask, 0x006C, "OR"),
                        (national, 16, mask, 0x0608, "OR"),
                        (national, 16, mask, 0x3A28, "OR"),
                    ],
                )
                _record_completed_abi_dispatch(
                    context, branch, instruction, 0x25, set_seen_raw,
                )
                self.assertEqual(branch.abi_dispatches[-1]["result_capture"], {
                    "kind": "NONE", "value": None,
                })
                self.assertEqual(
                    branch.abi_dispatches[-1]["effect_member_count"], 3,
                )

        malformed = deepcopy(output)
        malformed_355 = next(
            row for row in malformed["special_abis"]
            if row["special_id"] == 355
        )
        malformed_355["effect_contract"]["mirrors"].pop()
        malformed_355["effects"].pop()
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "SPECIAL355 SetSeenMon effect contract不一致",
        ):
            _interaction_abi_index(
                self.stage61, malformed, source_blobs=source_blobs,
            )

        self.assertEqual(set_seen["result_contract"], {
            "global_var_result_write": None, "specialvar_return": None,
        })
        for forged_channel in (
            "global_var_result_write", "specialvar_return",
        ):
            with self.subTest(set_seen_forged_result=forged_channel):
                forged = deepcopy(output)
                forged_355 = next(
                    row for row in forged["special_abis"]
                    if row["special_id"] == 355
                )
                forged_355["result_contract"][forged_channel] = {
                    "candidate_values": [0],
                    "relation": "FORGED_SET_SEEN_RESULT",
                }
                with self.assertRaisesRegex(
                    Stage61InteractionOracleError,
                    "SPECIAL355 canonical result contract不一致",
                ):
                    _interaction_abi_index(
                        self.stage61, forged, source_blobs=source_blobs,
                    )

        # PurchaseSelected always delegates with confirmed=1.  The source-
        # closed writer graph therefore excludes EFFECTLESS(1), CANCELLED(2),
        # and BUSY(9), but includes DAILY_CAP(4) from shop_stock_result.
        research_symbol = "ResearchEconomy_PurchaseSelected"
        research_evidence = _native_global_result_writer_evidence(
            research_symbol, self.stage61, source_blobs,
            stage60_rom=self.stage60,
        )
        self.assertIsNotNone(research_evidence)
        research_semantics = _native_semantic_contract(
            research_symbol, writer_evidence=research_evidence,
        )
        research_candidates = research_semantics["result_contract"][
            "global_var_result_write"
        ]["candidate_values"]
        self.assertEqual(research_candidates, [0, 3, 4, 5, 7, 13, 14, 15])
        self.assertNotIn(1, research_candidates)
        self.assertIn(4, research_candidates)
        research_entry = {
            "abi_key": "NATIVE:0x093BE869",
            "target_pointer": "0x093BE869",
            "symbol": research_symbol,
            "source": {
                "path": (
                    "overlays/research_economy_v1/research_economy_v1.c"
                ),
                "definition_line": 1504,
                "sha256": (
                    "3f71ea1d9f308c652e70dd863b601ad39a9c648ca25bf55932b4966fa4246e62"
                ),
            },
            "rom_binding": {
                "address": "0x093BE868", "byte_length": 56,
                "sha256": (
                    "11f89c6bb3abf13c9df80f6d2f35b217cdaa53b047af833c55ada4325241271f"
                ),
            },
            **research_semantics,
            "complete": True,
        }
        research_manifest = {
            "special_abis": [], "native_abis": [research_entry],
        }
        research_index = _interaction_abi_index(
            self.stage61, research_manifest, source_blobs=source_blobs,
        )
        research_instruction = 0x08100020
        research_raw = bytes((0x23,)) + (0x093BE869).to_bytes(4, "little")
        research_context = _Context(
            clean_rom=self.clean, stage61_rom=self.stage61,
            semantic_report={}, npc={"local_id": 0},
            case={"state": {"flags": [], "vars": [], "items": [],
                            "trainers": []}},
            root=research_instruction, target_root=research_instruction,
            execution_root=research_instruction, root_plan={},
            fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
            text_assets={}, text_provenance="PROJECT_STAGE60_RAW",
            abi_index=research_index, instruction_repairs={},
            source_suppression_contract=None,
            stage61_script_bytes=frozenset(),
        )
        research_state = _Execution(
            pc=research_instruction, vars={0x800D: 1},
            execution_trace=[research_instruction],
            current_instruction_address=research_instruction,
            current_opcode=0x23,
        )
        research_branches = _fork_abi_command(
            research_context, research_state, research_instruction, 0x23,
            research_raw,
        )
        self.assertEqual(
            [branch.vars[0x800D] for branch in research_branches],
            [0, 3, 4, 5, 7, 13, 14, 15],
        )

        missing_daily_writer = deepcopy(research_manifest)
        evidence = missing_daily_writer["native_abis"][0][
            "result_contract"
        ]["global_var_result_write"]["writer_evidence"]
        evidence["source_functions"] = [
            row for row in evidence["source_functions"]
            if row["symbol"] != "shop_stock_result"
        ]
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "ResearchEconomy_PurchaseSelected result writer evidence不一致",
        ):
            _interaction_abi_index(
                self.stage61, missing_daily_writer,
                source_blobs=source_blobs,
            )

    def test_pinned_abi_all_event_scope_resolves_all_264_entries(self) -> None:
        source_blobs, reports = self.pinned_abi_inputs()
        output = build_pinned_interaction_abi_manifest(
            self.clean, self.stage60, self.stage61, self.catalog,
            source_blobs=source_blobs, runtime_symbol_reports=reports,
            event_owner_inventory=self.event_owner_inventory,
        )
        self.assertEqual(len(output["special_abis"]), 176)
        self.assertEqual(len(output["native_abis"]), 88)
        self.assertEqual(output["registry_audit"]["site_count"], 2590)
        self.assertEqual(output["registry_audit"]["unresolved_site_count"], 0)
        self.assertEqual(sum(
            row["abi_key"].startswith("SPECIAL:015E:")
            for row in output["registry_audit"]["resolved_sites"]
        ), 1)
        self.assertEqual(
            output["input_provenance"]["runtime_owner_scope"],
            "ALL_EVENT_OWNERS",
        )
        self.assertTrue(output["assertions"]["interaction_abi_264_exact"])
        self.assertTrue(all(output["assertions"].values()))
        by_id = {row["special_id"]: row for row in output["special_abis"]}
        check_add_coins = by_id[350]
        self.assertEqual(check_add_coins["symbol"], "CheckAddCoins")
        self.assertEqual(check_add_coins["target_pointer"], "0x080CC3A5")
        self.assertEqual(check_add_coins["rom_binding"], {
            "address": "0x080CC3A4", "byte_length": 0x2A,
            "sha256": (
                "d99ce8a5ba2e1a1d3c15562bd3f2b4f8b1a7851a962b21df5dc2fbb27b6b6ef3"
            ),
        })
        self.assertEqual(
            check_add_coins["result_contract"]["specialvar_return"],
            {
                "candidate_values": [0, 1],
                "relation": (
                    "TRUE_IFF_PRECALL_VAR_RESULT_CURRENT_COINS_PLUS_"
                    "VAR_8006_AT_MOST_9999"
                ),
            },
        )
        self.assertEqual(check_add_coins["input_controls"], [{
            "kind": "VAR", "owner": "gSpecialVar_Result_PRECALL",
            "candidate_values": {"minimum": 0, "maximum": 9999},
            "relation": "CURRENT_VEGA_COINS_COPIED_BY_GETCOINS_EXACT",
        }, {
            "kind": "VAR", "owner": "VAR:0x8006",
            "candidate_values": {"minimum": 1, "maximum": 127},
            "relation": "PACKED_HIDDEN_COIN_QUANTITY_EXACT",
        }])
        check_add_evidence = next(
            row for row in output["effect_abis"]
            if row["abi_key"] == check_add_coins["abi_key"]
        )["hidden_item_engine_binding"]
        self.assertEqual(
            check_add_evidence["special_table_entry"]["raw_hex"],
            "a5c30c08",
        )
        self.assertEqual(
            check_add_evidence["consumer_wrapper"]["address"],
            "0x0819410F",
        )
        daycare = by_id[184]
        self.assertEqual(
            daycare["symbol"],
            "VegaQolProduction_GiveEggFromDaycareSpecial",
        )
        self.assertEqual(daycare["target_pointer"], "0x09377BF5")
        self.assertEqual(daycare["rom_binding"]["byte_length"], 0x10)
        self.assertEqual(
            daycare["result_contract"]["specialvar_return"]
            ["candidate_values"],
            [0, 3, 5, 8, 11, 12],
        )
        self.assertEqual(
            {effect["domain"] for effect in daycare["effects"]},
            {"flags", "ledger", "party", "rng", "save", "storage"},
        )
        evidence = next(
            row for row in output["effect_abis"]
            if row["abi_key"] == daycare["abi_key"]
        )
        self.assertEqual(evidence["provenance"], "PINNED_STAGE60_PROJECT_REPOINT")
        self.assertEqual(evidence["semantic_owner_binding"], {
            "symbol": "give_egg_from_daycare_transaction",
            "address": "0x0937A2E4", "byte_length": 0x240,
            "sha256": (
                "cc968a63fa96c1db4d8d06fb814d57e15300af233d3acf0d20d7"
                "f08ce6ab1e3e"
            ),
            "span_evidence": (
                "generated/runtime/qol_production_symbols.json/"
                "symbols/give_egg_from_daycare_transaction"
            ),
            "entry_preconditions": [
                "SAVE_POINTER_VALID_OR_STATUS_3",
                "MODERN_SAVE_VALID_OR_STATUS_12",
                "PARTY_COUNT_0_TO_6_OR_STATUS_3",
                "EGG_QUEUE_COUNT_0_TO_5_AND_HEAD_0_TO_4_NORMALIZED_BY_SAVE_LOAD",
                "DESTINATION_PARTY_OR_FIRST_EMPTY_PC_OR_STATUS_5",
                "CROSS_STORE_FAILURE_COMPENSATED_WITH_STATUS_11",
            ],
        })
        self.assertEqual(by_id[348]["rom_binding"]["byte_length"], 0x118)
        self.assertEqual(by_id[353]["rom_binding"]["byte_length"], 0x30)

    def test_bag_full_repair_tail_uses_clean_raw_and_requires_release(self) -> None:
        output = bag_full_repair_tail_oracle(self.clean)
        self.assertEqual(output["source_raw_sha256"], BAG_FULL_TEXT_SHA256)
        self.assertEqual(output["tokens_after_repaired_branch_entry"], ["ADVANCE_TEXT"])
        self.assertEqual(output["required_final"], {
            "field_released": True,
            "script_terminated": True,
            "bag_items_relation": "UNCHANGED",
        })
        self.assertEqual(output["repair_preconditions"]["standard_script"], 4)

    def test_shop_sequences_cover_buy_sell_and_quit_without_mutation(self) -> None:
        rows = shop_input_sequences()
        self.assertEqual([row["branch"] for row in rows], [
            "BUY_EXIT_WITHOUT_PURCHASE", "SELL_EXIT_WITHOUT_SALE", "QUIT",
        ])
        self.assertEqual(rows[0]["tokens_after_shop_opcode"], [
            "A", "B", "ADVANCE_TEXT", "B",
        ])
        self.assertEqual(rows[1]["tokens_after_shop_opcode"], [
            "DOWN", "A", "B", "ADVANCE_TEXT", "B",
        ])
        self.assertEqual(rows[2]["tokens_after_shop_opcode"], ["DOWN", "DOWN", "A"])
        self.assertTrue(all("unchanged" in row["relation"] for row in rows))

    def test_runner_control_abi_pins_every_physical_owner_and_rng(self) -> None:
        abi = runner_control_abi_contract()
        self.assertEqual(abi["owners"], {
            "save_block1_pointer": "0x03005048",
            "save_block2_pointer": "0x0300504C",
            "pokemon_storage_pointer": "0x03005050",
            "player_party_count": "0x02023F89",
            "player_party": "0x020241E4",
            "var_result": "0x02037004",
            "special_var_8004": "0x02036FF4",
            "special_var_8005": "0x02036FF6",
            "special_var_8006": "0x02036FF8",
            "global_rng": "0x03005040",
            "quest_log_state": "0x0203AD72",
            "engine_special_flags": "0x02037014",
        })
        self.assertEqual(abi["layouts"]["quest_log_state"], {
            "owner_address": "0x0203AD72",
            "size": 1,
            "values": [0, 1, 2, 3],
            "encoding": "plain_u8",
            "apply": "WRITE_AND_READBACK_BEFORE_SCRIPT_DISPATCH",
        })
        self.assertEqual(
            abi["required_value_types"]["QUEST_LOG_STATE"], "u8(0..3)",
        )
        self.assertEqual(
            abi["function_abi"]["get_berry_powder"], "0x081622B1",
        )
        self.assertEqual(abi["layouts"]["berry_powder"], {
            "owner": "SAVE_BLOCK2", "offset": 2808, "size": 4,
            "encoding": "value XOR encryption_key_u32",
            "maximum": 99999,
            "readback_function": "0x081622B1",
            "relation": "EXACT_DECRYPTED_BERRY_POWDER",
        })
        self.assertEqual(
            abi["required_value_types"]["BERRY_POWDER"],
            "u32(0..99999)",
        )
        self.assertEqual(
            abi["layouts"]["bag"]["pocket_slot_counts"],
            [42, 30, 13, 58, 43],
        )
        self.assertEqual(abi["layouts"]["bag"]["total_slot_count"], 186)
        self.assertEqual(abi["layouts"]["pc_items"]["slot_count"], 30)
        self.assertEqual(abi["layouts"]["party"]["required_raw_bytes"], 600)
        self.assertEqual(abi["layouts"]["storage"]["size"], 0x83D0)
        self.assertEqual(abi["function_abi"]["random"], "0x0804448D")
        self.assertEqual(
            abi["rom_owner_provenance"]["engine_special_flags"],
            {
                "kind": "FINAL_JAPANESE_VEGA_GET_FLAG_ADDR_OWNER_LITERAL",
                "function": "GetFlagAddr",
                "literal_address": "0x0806DE70",
                "literal_value": "0x02037014",
                "literal_raw_hex": "14700302",
                "literal_sha256": (
                    "670819485fe75a97ab5bdb8b90c468f6d"
                    "f5fdf8e4af7c56ef3db5f7a7c897e83"
                ),
                "relation": (
                    "GET_FLAG_ADDR_LITERAL_IS_RUNTIME_OWNER;"
                    "UPSTREAM_SYMBOL_ADDRESS_GUESS_FORBIDDEN"
                ),
            },
        )
        self.assertEqual(abi["function_abi"]["add_pc_item"], "0x08099DD1")
        pc_probe = abi["mutation_safe_producers"]["PC_CAPACITY"]
        self.assertEqual(pc_probe["rom_binding"], {
            "address": "0x08099DD0", "byte_length": 0x96,
            "sha256": "02fc840390650c9f8b62622cc301ff789257d0c527cc113a76210e7d5259ce8e",
        })
        self.assertEqual(pc_probe["source"]["definition_line"], 385)
        self.assertEqual(
            hashlib.sha256(self.stage61[0x99DD0:0x99E66]).hexdigest(),
            pc_probe["rom_binding"]["sha256"],
        )
        source = (ROOT / pc_probe["source"]["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), pc_probe["source"]["sha256"])
        self.assertEqual(len(pc_probe["synthetic_reachable_cases"]), 4)
        self.assertEqual(
            {row["expected_result"] for row in pc_probe["synthetic_reachable_cases"]},
            {0, 1},
        )
        self.assertEqual(pc_probe["required_actual_mgba_case_count"], 4)
        self.assertFalse(pc_probe["direct_script_call_is_acceptance_evidence"])
        self.assertEqual(
            pc_probe["mutable_owner"]["encoding"],
            "item_id u16; quantity plain u16",
        )
        self.assertEqual(
            abi["layouts"]["pc_items"]["slot"]["quantity"], "plain u16",
        )
        self.assertEqual(
            abi["layouts"]["bag"]["slot"]["quantity"],
            "u16 XOR key_low_u16",
        )
        state = 0x12345678
        next_state = (state * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        self.assertEqual(next_state, 0x0B71C18B)
        self.assertEqual(next_state >> 16, 0x0B71)
        self.assertTrue(all(abi["assertions"].values()))

    def test_engine_special_flag_owner_literal_oracle_rejects_mutation(
        self,
    ) -> None:
        contract = validate_engine_special_flag_owner_literal(
            self.stage60, self.stage61,
        )
        self.assertEqual(contract["literal_address"], "0x0806DE70")
        self.assertEqual(contract["literal_value"], "0x02037014")
        self.assertTrue(all(contract["assertions"].values()))
        offset = 0x0806DE70 - 0x08000000
        final = bytearray(self.stage61)
        final[offset + 3] ^= 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "GetFlagAddr owner literal drift:final_rom",
        ):
            validate_engine_special_flag_owner_literal(
                self.stage60, bytes(final),
            )

    def test_hidden_item_public_consumer_contract_binds_full_stock_engine(self) -> None:
        patched_stage61 = bytearray(self.stage61)
        patch_offset = 0x0806C908 - 0x08000000
        self.assertEqual(
            patched_stage61[patch_offset:patch_offset + 4],
            bytes.fromhex("014866e0"),
        )
        patched_stage61[patch_offset:patch_offset + 2] = bytes.fromhex("0020")
        output = build_hidden_item_script_consumers(
            self.clean, self.stage60, bytes(patched_stage61),
        )
        self.assertEqual(output["kind"], "STAGE61_HIDDEN_ITEM_SCRIPT_CONSUMERS")
        self.assertEqual(output["underfoot_owner_count"], 0)
        self.assertEqual(set(output["by_entry"]), {"FACE_A"})
        face = output["by_entry"]["FACE_A"]
        self.assertEqual(face["consumer_script_root"], 0x0819410F)
        binding = face["source_provenance"]["binding"]
        self.assertEqual(binding["field_consumer"]["address"], "0x0806C8D8")
        self.assertEqual(binding["field_consumer"]["byte_length"], 0x10C)
        self.assertEqual(
            binding["field_consumer"]["declared_stage61_patch"], {
                "address": "0x0806C908",
                "preimage_hex": "0148",
                "replacement_hex": "0020",
                "preserved_adjacent_branch_hex": "66e0",
                "derivation": (
                    "STAGE60_FULL_PREIMAGE_PLUS_EXACT_TWO_BYTE_PATCH_"
                    "ALL_OTHER_BYTES_UNCHANGED"
                ),
            },
        )
        self.assertEqual(
            binding["field_consumer"]["already_collected_gate"], {
                "flag_get_instruction_pc": "0x0806C9A4",
                "compare_instruction_pc": "0x0806C9AC",
                "null_branch_instruction_pc": "0x0806C9AE",
                "null_return_instruction_pc": "0x0806C958",
                "relation": (
                    "FlagGet(gSpecialVar_0x8004)==TRUE_RETURNS_NULL_"
                    "BEFORE_EventScript_HiddenItemScript_ASSIGNMENT"
                ),
            },
        )
        self.assertEqual(binding["consumer_wrapper"]["byte_length"], 0x112)
        self.assertEqual(binding["full_engine_function"]["byte_length"], 0x2A)
        self.assertTrue(all(output["assertions"].values()))

        outside_patch = bytearray(patched_stage61)
        outside_patch[0x0806C8D8 - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "declared NULL repair外差分",
        ):
            build_hidden_item_script_consumers(
                self.clean, self.stage60, bytes(outside_patch),
            )

    def test_all_74_hidden_records_are_decoded_from_final_rom_bytes(self) -> None:
        rows, evidence = _decode_hidden_item_owners(
            self.stage61, self.event_owner_inventory,
        )
        self.assertEqual(len(rows), 74)
        self.assertEqual(Counter(row["reward_kind"] for row in rows), {
            "ITEM": 62, "COINS": 12,
        })
        self.assertFalse(any(row["underfoot"] for row in rows))
        self.assertTrue(all(
            hashlib.sha256(bytes.fromhex(row["record_raw_hex"])).hexdigest()
            == row["record_sha256"]
            for row in rows
        ))
        self.assertEqual(
            {row["item_id"] for row in rows if row["reward_kind"] == "COINS"},
            {0},
        )
        self.assertEqual(
            {row["quantity"] for row in rows if row["reward_kind"] == "COINS"},
            {10, 20, 40, 100},
        )
        self.assertEqual(evidence["owner_count"], 74)
        self.assertEqual(evidence["item_owner_count"], 62)
        self.assertEqual(evidence["coin_owner_count"], 12)
        self.assertEqual(evidence["underfoot_owner_count"], 0)
        self.assertTrue(evidence["all_records_decoded"])
        self.assertTrue(evidence["coin_branch_present"])

    def test_common7_is_exact_dormant_table_abi_not_fake_runtime_caller(self) -> None:
        source_blobs, _reports = self.pinned_abi_inputs()
        evidence = _dormant_common7_structural_evidence(
            self.clean, self.stage61,
            self.event_owner_inventory["owners"], source_blobs,
        )
        self.assertEqual(evidence["standard_index"], 7)
        self.assertEqual(evidence["record_address"], "0x08163774")
        self.assertEqual(evidence["table_raw_hex"], "38401908")
        self.assertEqual(
            evidence["representative_runtime_root"], "0x08194038",
        )
        self.assertEqual(evidence["cfg_node_count"], 4)
        self.assertTrue(evidence["clean_final_cfg_identical"])
        self.assertEqual(evidence["live_caller_count"], 0)
        self.assertEqual(evidence["live_caller_instruction_addresses"], [])
        self.assertEqual(
            evidence["source_provenance"]["inert_command"]["relation"],
            "DecorationAdd_CALL_COMMENTED_OUT_AND_gSpecialVar_Result_UNCHANGED",
        )
        self.assertTrue(all(evidence["assertions"].values()))

    def test_conditional_common_caller_reads_standard_index_at_operand_two(self) -> None:
        owner = {
            "owner_id": "COMMON:STANDARD:003", "owner_kind": "COMMON",
            "index": 3, "root": 0x08193F6D, "runtime_root": True,
        }
        caller_pc = 0x09FFFFF0
        base_path = {
            "kind": "COMMON_CALLER_TRIGGER", "standard_index": 3,
            "caller_owner_id": "BG:000/000:000",
            "caller_owner_kind": "BG", "caller_instruction_pc": caller_pc,
            "caller_trigger_path": {"kind": "BG_FACE_A"},
            "root_pc": owner["root"],
        }
        valid = bytearray(self.stage61)
        valid[caller_pc - 0x08000000:caller_pc - 0x08000000 + 3] = \
            bytes((0x0A, 0x01, 0x03))
        output = _validated_runtime_trigger_path(
            bytes(valid), owner, base_path,
        )
        self.assertEqual(output["caller_instruction_pc"], caller_pc)

        malformed = bytearray(self.stage61)
        # raw[1] looks like index 3, but callstd_if/gotostd_if owns it at
        # raw[2].  This is the exact false-positive accepted by the old parser.
        malformed[caller_pc - 0x08000000:caller_pc - 0x08000000 + 3] = \
            bytes((0x0A, 0x03, 0x01))
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "COMMON caller opcode/index",
        ):
            _validated_runtime_trigger_path(bytes(malformed), owner, base_path)

    def test_engine_teleport_foreign_warp_scan_is_exact_and_zero(self) -> None:
        rom, owner, path = _engine_teleport_trigger_fixture(self.stage61)
        normalized = _validated_runtime_trigger_path(rom, owner, path)
        scan = normalized["engine_teleport"]["source_provenance"][
            "foreign_stock_warp_scan"
        ]
        self.assertEqual(set(scan), {
            "destination", "foreign_warp_reference_count",
            "usable_stock_warp_count", "invalid_source_warp_view_count",
            "unusable_reason_counts",
        })
        self.assertEqual(scan["destination"], [1, 2])
        self.assertEqual(scan["usable_stock_warp_count"], 0)

    def test_only_exact_canonical_shadow_sources_may_face_a_without_walk(
        self,
    ) -> None:
        rom = bytearray(self.stage61)
        record_address = 0x09FFFF00
        root = 0x08100000
        raw = bytearray(24)
        raw[0] = 1
        struct.pack_into("<hhI", raw, 4, 9, 8, root)
        rom[
            record_address - 0x08000000:
            record_address - 0x08000000 + len(raw)
        ] = raw
        owner = {
            "owner_id": "OBJECT:003/022:000", "owner_kind": "OBJECT",
            "group": 3, "map": 22, "index": 0, "root": root,
            "record_address": record_address,
        }
        path = {
            "kind": "OBJECT_FACE_A", "group": 3, "map": 22,
            "local_id": 1, "object_index": 0, "root_pc": root,
            "approach": "TELEPORT_STANCE_FACE_A_CANONICAL_SHADOW_SOURCE",
            "start_tile": {"x": 9, "y": 7}, "walk_sequence": [],
            "stance_tile": {"x": 9, "y": 7},
            "required_facing": "DOWN",
            "runtime_topology_probe_required": True,
        }
        normalized = _validated_runtime_trigger_path(
            bytes(rom), owner, path,
        )
        self.assertEqual(normalized["walk_sequence"], [])

        broad = {**owner, "owner_id": "OBJECT:003/022:001", "index": 1}
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "runtime OBJECT trigger不正",
        ):
            _validated_runtime_trigger_path(bytes(rom), broad, path)

        ordinary = deepcopy(path)
        ordinary["approach"] = "WALK_ADJACENT_FACE_A"
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "actual walk欠落",
        ):
            _validated_runtime_trigger_path(bytes(rom), owner, ordinary)

    def test_engine_teleport_rejects_nonzero_or_wrong_destination_scan(
        self,
    ) -> None:
        rom, owner, base_path = _engine_teleport_trigger_fixture(self.stage61)
        mutations = {
            "usable_nonzero": ("usable_stock_warp_count", 1),
            "wrong_destination": ("destination", [1, 3]),
        }
        for label, (key, value) in mutations.items():
            path = deepcopy(base_path)
            path["engine_teleport"]["source_provenance"][
                "foreign_stock_warp_scan"
            ][key] = value
            with self.subTest(label=label), self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "engine teleport provenance不正",
            ):
                _validated_runtime_trigger_path(rom, owner, path)

    def test_engine_teleport_rejects_foreign_scan_schema_extra_or_missing(
        self,
    ) -> None:
        rom, owner, base_path = _engine_teleport_trigger_fixture(self.stage61)
        extra = deepcopy(base_path)
        extra["engine_teleport"]["source_provenance"][
            "foreign_stock_warp_scan"
        ]["unexpected"] = 0
        missing = deepcopy(base_path)
        del missing["engine_teleport"]["source_provenance"][
            "foreign_stock_warp_scan"
        ]["invalid_source_warp_view_count"]
        for label, path in (("extra", extra), ("missing", missing)):
            with self.subTest(label=label), self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "engine teleport provenance不正",
            ):
                _validated_runtime_trigger_path(rom, owner, path)

    def test_runner_fixture_registry_is_canonical_and_byte_exact(self) -> None:
        party = {
            "fixture_kind": "PARTY", "count": 0,
            "raw_hex": "00" * 600,
        }
        self.assertEqual(len(runner_fixture_key(party)), 64)
        with self.assertRaisesRegex(Stage61InteractionOracleError, "key不正"):
            runner_fixture_key({**party, "extra": 1})
        with self.assertRaisesRegex(Stage61InteractionOracleError, "lowercase"):
            runner_fixture_key({**party, "raw_hex": "AA" * 600})
        with self.assertRaisesRegex(Stage61InteractionOracleError, "raw size"):
            runner_fixture_key({**party, "raw_hex": "00" * 599})
        bag = {
            "fixture_kind": "BAG",
            "pockets": [
                {
                    "index": index,
                    "slots": [{"item_id": 0, "quantity": 0} for _ in range(count)],
                }
                for index, count in enumerate([42, 30, 13, 58, 43])
            ],
        }
        first = runner_fixture_key(bag)
        self.assertEqual(first, runner_fixture_key(deepcopy(bag)))
        bad = deepcopy(bag)
        bad["pockets"][2]["slots"].pop()
        with self.assertRaisesRegex(Stage61InteractionOracleError, "slot count"):
            runner_fixture_key(bad)

    def test_all_case_audit_covers_final_rom_and_cannot_claim_complete(self) -> None:
        output = self.coverage
        self.assertEqual(output["status"], "UNRESOLVED")
        self.assertEqual(
            output["case_count"],
            self.matrix["counts"]["matrix_case_count"],
        )
        self.assertEqual(output["owner_count"], 3108)
        self.assertEqual(output["runtime_root_count"], 2466)
        self.assertEqual(output["runtime_graph_node_count"], 8582)
        self.assertEqual(output["runtime_roots_with_pinned_branch_controls"], 1588)
        self.assertEqual(output["project_runtime_root_count"], 993)
        self.assertEqual(
            output["project_runtime_roots_with_pinned_branch_controls"], 522,
        )
        self.assertEqual(output["project_runtime_roots_with_menus"], 150)
        self.assertGreater(output["unresolved_case_count"], 0)
        self.assertFalse(output["assertions"]["unresolved_zero"])
        self.assertTrue(all(
            value for key, value in output["assertions"].items()
            if key != "unresolved_zero"
        ))
        project = [
            row for row in output["rows"]
            if row["classification"] == "UNRESOLVED_PROJECT_LIVE_ROOT"
        ]
        self.assertTrue(project)
        self.assertTrue(all(
            "PROJECT_TEXT_PROVENANCE_REQUIRED" in row["blockers"] for row in project
        ))
        self.assertTrue(any(
            row["classification"] == "HIDDEN_NO_INTERACTION"
            and row["control_requirements"]["external"]
            for row in output["rows"]
        ))

    def test_var_result_def_use_crosses_cfg_calls_without_default_zero(self) -> None:
        self.assertIsNone(
            self.coverage["internal_control_writer_counts"].get(
                "UNKNOWN_REACHING_DEFINITION"
            )
        )
        reads = [
            control
            for row in self.coverage["rows"]
            for control in row["control_requirements"]["internal"]
            if control["kind"] == "VAR_RESULT_BRANCH_READ"
        ]
        self.assertTrue(any(
            row["def_use_status"] == "CROSS_NODE_EXACT" for row in reads
        ))
        self.assertFalse(any(
            row["writer"] == "UNKNOWN_REACHING_DEFINITION" for row in reads
        ))
        self.assertTrue(all(
            row["capture"]["owner_address"] == 0x02037004 for row in reads
        ))

    def test_party_move_uses_party_size_sentinel_and_conditional_species_write(self) -> None:
        writers = [
            control
            for row in self.coverage["rows"]
            for control in row["control_requirements"]["internal"]
            if control.get("writer") == "CHECK_PARTY_MOVE"
            and control.get("kind") == "VAR_RESULT_WRITE"
        ]
        self.assertTrue(writers)
        self.assertTrue(all(
            row["candidate_values"] == list(range(7)) for row in writers
        ))
        self.assertTrue(all(127 not in row["candidate_values"] for row in writers))
        self.assertTrue(all(
            row["relation"]
            == "FIRST_NON_EGG_MEMBER_KNOWING_MOVE_OR_PARTY_SIZE"
            and row["conditional_side_effect"] == {
                "when": "result < PARTY_SIZE",
                "owner": "VAR:0x8004",
                "relation": "SET_TO_MATCHING_PARTY_SPECIES",
                "otherwise": "UNCHANGED",
            }
            for row in writers
        ))
        source = (ROOT / writers[0]["source"]["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), writers[0]["source"]["sha256"])

    def test_giveegg_models_party_storage_and_failure_results(self) -> None:
        writer, blockers = _static_result_writer_descriptor(
            self.stage61,
            SimpleNamespace(opcode=0x7A, raw=bytes.fromhex("7A0100"),
                            address=0x08123456),
        )
        self.assertEqual(blockers, [])
        self.assertEqual(writer["candidate_values"], [0, 1, 2])
        self.assertEqual(writer["result_effects"], {
            "0": "ADD_TO_PARTY",
            "1": "ADD_TO_STORAGE",
            "2": "PARTY_AND_STORAGE_UNCHANGED",
        })
        for source in writer["source"].values():
            blob = (ROOT / source["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(blob).hexdigest(), source["sha256"])

    def test_party_count_executor_writer_is_independent_of_party_move(self) -> None:
        writer, blockers = _static_result_writer_descriptor(
            self.stage61,
            SimpleNamespace(opcode=0x43, raw=b"\x43", address=0x08123456),
        )
        self.assertEqual(blockers, [])
        self.assertEqual(writer, {
            "writer": "GET_PARTY_SIZE",
            "instruction_address": "0x08123456",
            "candidate_values": list(range(7)),
        })

    def test_static_control_domains_canonically_sort_mapping_candidates(self) -> None:
        root = 0x08123400
        native = 0x08123456
        graph = SimpleNamespace(
            clean_rom=b"",
            nodes={root: SimpleNamespace(instructions=[SimpleNamespace(
                opcode=0x23,
                raw=b"\x23" + native.to_bytes(4, "little"),
                address=root,
            )])},
            distances=lambda _root: [root],
        )
        domains, blockers = _static_control_domains(
            graph,
            root,
            abi_index={f"NATIVE:0x{native:08X}": {
                "input_controls": [{
                    "kind": "PARTY_LAYOUT",
                    "owner": "PARTY_LAYOUT:0x02024284",
                    "candidate_values": [{"slots": 2}, {"slots": 1}],
                    "relation": "FINITE_STRUCTURAL_STATE",
                }],
            }},
        )
        self.assertEqual(blockers, [])
        self.assertEqual(
            domains[0]["candidate_values"],
            [{"slots": 1}, {"slots": 2}],
        )

    def test_event_design_rank_model_has_ten_physical_dispatch_scenarios(
        self,
    ) -> None:
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph

        source_blobs, _reports = self.pinned_abi_inputs()
        owner = next(
            row for row in self.event_owner_inventory["owners"]
            if row["owner_id"] == "BG:097/047:000"
        )
        self.assertEqual(owner["root"], 0x0938DD34)
        graph = SemanticScriptGraph(self.stage61)
        graph.walk([owner["root"]])
        self.assertEqual(graph.diagnostics, [])
        model = _build_event_design_rank_model(
            source_blobs, graph, owner["root"],
        )
        self.assertIsNotNone(model)
        assert model is not None
        self.assertEqual(model["event_indices"], [34, 61, 62, 63, 69])
        self.assertEqual(model["call_count"], 15)
        self.assertEqual(model["physical_assignment_class_count"], 8192)
        self.assertEqual(model["terminal_scenario_count"], 10)
        terminal_counts = Counter(
            (row["terminal"]["kind"], row["terminal"].get("rank"))
            for row in model["scenarios"]
        )
        self.assertEqual(terminal_counts, Counter({
            ("EVENT", 3): 5,
            ("EVENT", 1): 4,
            ("GOTO_FALLBACK", None): 1,
        }))
        rank_one_indices = {
            row["terminal"]["event_index"]
            for row in model["scenarios"]
            if row["terminal"].get("rank") == 1
        }
        self.assertEqual(rank_one_indices, {34, 61, 63, 69})
        self.assertNotIn(62, rank_one_indices)
        # QOL feature 30/31 are the same HOF+certification readiness owner.
        # Independent synthetic bools would admit one side without the other.
        self.assertTrue(all(
            bool(row["event_ranks"]["62"])
            == bool(row["event_ranks"]["63"])
            for row in model["scenarios"]
        ))

        fixtures: dict[str, dict] = {}
        projected = [
            _materialize_control_requirement(
                self.stage61, control,
                owner_keys=[owner["owner_id"]], fixtures=fixtures,
            )
            for scenario in model["scenarios"]
            for control in scenario["physical_controls"]
        ]
        self.assertTrue(all(row is not None for row in projected))
        physical = [row for row in projected if row is not None]
        normal_flags = [
            row for row in physical
            if row["kind"] == "FLAG"
            and not 0x1400 <= row["id"] <= 0x1407
            and row["id"] != 0x13FA
        ]
        self.assertTrue(normal_flags)
        self.assertTrue(all(row["relation_evidence"] == []
                            for row in normal_flags))
        self.assertTrue(all(
            row["relation_evidence"] == [{
                "operator":
                    "CERT_OWNER_FLAG_TO_MODERN_CERTIFICATION_BIT_MIRROR",
            }]
            for row in physical
            if row["kind"] == "FLAG" and 0x1400 <= row["id"] <= 0x1407
        ))
        self.assertTrue(all(
            row["relation_evidence"][0]["operator"]
            == "KANTO_LEAGUE_STATE_TO_LEAGUE_I_II_SAVE_MIRROR"
            for row in physical
            if row["kind"] == "FLAG" and row["id"] == 0x13FA
        ))

        daycare = _event_design_physical_controls(
            {("DAYCARE_OCCUPIED", 0): True},
            model["source_contract_sha256"],
        )[0]
        daycare_projected = _materialize_control_requirement(
            self.stage61, daycare,
            owner_keys=[owner["owner_id"]], fixtures=fixtures,
        )
        self.assertEqual(daycare_projected["kind"], "DAYCARE_OCCUPIED")
        self.assertEqual(daycare_projected["id"], 0)
        self.assertIs(daycare_projected["value"], True)
        self.assertEqual(daycare_projected["relation_evidence"], [{
            "operator": "EVENT_DESIGN_SOURCE_PHYSICAL_BOOL",
        }])
        self.assertEqual(fixtures, {})

        missing = dict(source_blobs)
        missing.pop("content/event_design_implementation/event_plan.json")
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "EVENT_DESIGN_RANK_SOURCE_BLOB_MISSING_OR_DRIFT",
        ):
            _build_event_design_rank_model(missing, graph, owner["root"])

    def test_event_design_native_candidates_and_widening_rejection(self) -> None:
        bool_symbols = (
            "EventDesign_ScriptCheckCondition",
            "EventDesign_ScriptSetState",
            "EventDesign_ScriptGrantReward",
            "EventDesign_ScriptOpenEggBasket",
        )
        self.assertEqual(
            _native_semantic_contract("EventDesign_ScriptEventRank")
            ["result_contract"]["global_var_result_write"]
            ["candidate_values"],
            [0, 1, 2, 3],
        )
        for symbol in bool_symbols:
            with self.subTest(symbol=symbol):
                self.assertEqual(
                    _native_semantic_contract(symbol)
                    ["result_contract"]["global_var_result_write"]
                    ["candidate_values"],
                    [0, 1],
                )
        entry = {
            "symbol": "EventDesign_ScriptEventRank",
            "target_pointer": "0x09388119",
            **_native_semantic_contract("EventDesign_ScriptEventRank"),
        }
        key = "NATIVE:0x09388119"
        _validate_event_design_rank_abi_entry(entry, key)
        widened = deepcopy(entry)
        widened["result_contract"]["global_var_result_write"][
            "candidate_values"
        ] = list(range(8))
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "EVENT_DESIGN_RANK_ABI_CANDIDATE_DRIFT",
        ):
            _validate_event_design_rank_abi_entry(widened, key)

    def test_bg_097_047_event_rank_executor_reuses_physical_scenario(
        self,
    ) -> None:
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph

        source_blobs, _reports = self.pinned_abi_inputs()
        owner = next(
            row for row in self.event_owner_inventory["owners"]
            if row["owner_id"] == "BG:097/047:000"
        )
        graph = SemanticScriptGraph(self.stage61)
        graph.walk([owner["root"]])
        self.assertEqual(graph.diagnostics, [])

        # The checked-in manifest is deliberately used only as ROM/source
        # binding material here.  Reconstruct every EventDesign semantic row
        # from today's source contract so this targeted executor test neither
        # trusts nor rewrites a stale generated candidate union.
        manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        abi_index = {}
        for raw_entry in [
            *manifest["special_abis"], *manifest["native_abis"],
        ]:
            entry = deepcopy(raw_entry)
            raw_pointer = int(entry["target_pointer"], 16)
            entry["target_pointer"] = (
                raw_pointer & ~1
                if entry["abi_key"].startswith("NATIVE:") else raw_pointer
            )
            entry["source_status"] = "PINNED_SOURCE_VERIFIED"
            if entry["symbol"].startswith("EventDesign_"):
                entry.update(_native_semantic_contract(entry["symbol"]))
            abi_index[entry["abi_key"]] = entry
        self.assertEqual(
            abi_index["NATIVE:0x09388119"]["target_pointer"], 0x09388118,
        )

        semantic = deepcopy(self.semantic)
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(source_blobs[builder_path]).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        text_assets, _text_provenance = _independent_runtime_text_assets(
            self.clean, self.stage60, self.stage61, semantic,
            self.repair_manifest, graph, source_blobs=source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            self.clean, self.stage60, self.stage61, semantic, owner, graph,
            text_assets, abi_index, source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, owner["root"]),
        )
        self.assertEqual(blockers, [])
        self.assertTrue(executions)
        self.assertEqual({
            state.event_design_scenario_id for _context, state in executions
        }, {
            row["scenario_id"]
            for row in executions[0][0].event_design_rank_model["scenarios"]
        })
        self.assertEqual(len({
            state.event_design_scenario_id for _context, state in executions
        }), 10)
        for _context, state in executions:
            rank_decisions = [
                row for row in state.decisions
                if row.get("kind") == "EVENT_DESIGN_EVENT_RANK"
            ]
            self.assertLessEqual(len(rank_decisions), 15)
            by_event: dict[int, set[int]] = {}
            for row in rank_decisions:
                by_event.setdefault(row["event_index"], set()).add(
                    row["result_value"]
                )
            self.assertTrue(all(len(values) == 1
                                for values in by_event.values()))
        self.assertFalse(any(
            "path数上限超過" in str(blocker.get("detail", ""))
            for blocker in blockers
        ))

    def test_bg_004_001_001_materializes_all_four_real_quest_log_states(
        self,
    ) -> None:
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph

        source_blobs, _reports = self.pinned_abi_inputs()
        semantic = deepcopy(self.semantic)
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(source_blobs[builder_path]).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha

        owner = next(
            row for row in self.event_owner_inventory["owners"]
            if row["owner_id"] == "BG:004/001:001"
        )
        self.assertEqual(owner["root"], 0x0817BF17)
        graph = SemanticScriptGraph(self.stage61)
        graph.walk([owner["root"]])
        self.assertFalse(graph.diagnostics)
        abi_index = _interaction_abi_index(
            self.stage61,
            json.loads((
                ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
            ).read_text()),
            source_blobs=source_blobs,
        )
        text_assets, _text_provenance = _independent_runtime_text_assets(
            self.clean, self.stage60, self.stage61, semantic,
            self.repair_manifest, graph, source_blobs=source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            self.clean, self.stage60, self.stage61, semantic, owner, graph,
            text_assets, abi_index, source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, owner["root"]),
        )
        self.assertEqual(blockers, [])
        self.assertEqual(len(executions), 4)
        fixtures: dict[str, dict] = {}
        controls = []
        for context, state in executions:
            external, _internal = _runtime_control_rows(
                context, state, owner_keys=[owner["owner_id"]],
                fixtures=fixtures,
            )
            quest = [
                row for row in external
                if row["kind"] == "QUEST_LOG_STATE"
            ]
            self.assertEqual(len(quest), 1)
            controls.append(quest[0])
        self.assertEqual(
            sorted(row["value"] for row in controls),
            list(QUEST_LOG_STATE_VALUES),
        )
        self.assertEqual({row["id"] for row in controls}, {0})
        self.assertTrue(all(row["relation_evidence"] == [{
            "operator": "ENGINE_GLOBAL_QL_STATE_EXACT",
        }] for row in controls))
        self.assertEqual(fixtures, {})

    def test_runtime_context_reuses_build_level_immutable_graph_inputs(self) -> None:
        root = 0x08123456
        shared_script_bytes = frozenset({root, root + 1})
        shared_root_plan = {"references": []}
        owner = {
            "owner_id": "BG:001/002:000",
            "owner_kind": "BG",
            "group": 1,
            "map": 2,
            "index": 0,
            "record_address": 0,
            "root": root,
        }
        contexts = [
            _runtime_context(
                b"", b"", b"", {}, owner, SimpleNamespace(), {}, {}, {},
                shared_script_bytes=shared_script_bytes,
                shared_root_plan=shared_root_plan,
            )
            for _ in range(3)
        ]
        self.assertTrue(all(
            context.stage61_script_bytes is shared_script_bytes
            for context in contexts
        ))
        self.assertTrue(all(
            context.root_plan is shared_root_plan for context in contexts
        ))

    def test_runtime_contract_build_constructs_graph_byte_set_once(self) -> None:
        source = inspect.getsource(build_runtime_control_expansion_contract)
        self.assertEqual(source.count("_runtime_graph_script_bytes(graph)"), 1)
        self.assertEqual(
            source.count("shared_script_bytes=shared_script_bytes"), 2,
        )

    def test_joint_var_compare_uses_known_value_boundaries_and_same_owner(self) -> None:
        self.assertEqual(_joint_compare_assignments(
            left_missing=True, right_missing=False,
            left_known=None, right_known=500, same_owner=False,
        ), [(499, 500), (500, 500), (501, 500)])
        self.assertEqual(_joint_compare_assignments(
            left_missing=False, right_missing=True,
            left_known=0, right_known=None, same_owner=False,
        ), [(0, 0), (0, 1)])
        self.assertEqual(_joint_compare_assignments(
            left_missing=True, right_missing=False,
            left_known=None, right_known=0xFFFF, same_owner=False,
        ), [(0xFFFE, 0xFFFF), (0xFFFF, 0xFFFF)])
        self.assertEqual(_joint_compare_assignments(
            left_missing=True, right_missing=True,
            left_known=None, right_known=None, same_owner=True,
        ), [(0, 0)])

    def test_coin_commands_use_reverse_bool_and_only_mutate_on_success(self) -> None:
        writers = [
            control
            for row in self.coverage["rows"]
            for control in row["control_requirements"]["internal"]
            if control.get("writer") in {"ADD_COINS", "REMOVE_COINS"}
        ]
        self.assertTrue(writers)
        self.assertEqual({row["writer"] for row in writers}, {
            "ADD_COINS", "REMOVE_COINS",
        })
        self.assertTrue(all(row["candidate_values"] == [0, 1]
                            for row in writers))
        self.assertTrue(all(row["success_result"] == 0
                            and row["failure_result"] == 1
                            and row["conditional_effect"]["when"] == "result == 0"
                            and row["conditional_effect"]["otherwise"] == "UNCHANGED"
                            for row in writers))
        for source in writers[0]["source"].values():
            blob = (ROOT / source["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(blob).hexdigest(), source["sha256"])

    def test_trainerbattle_already_fought_uses_command_end_not_defeat_or_victory_pointer(self) -> None:
        instruction = 0x08100000
        explicit_victory = 0x08123456
        raw = (
            bytes.fromhex("5c01") + (77).to_bytes(2, "little")
            + (3).to_bytes(2, "little")
            + (0x08111111).to_bytes(4, "little")
            + (0x08112222).to_bytes(4, "little")
            + explicit_victory.to_bytes(4, "little")
        )
        context = SimpleNamespace(
            clean_rom=self.clean,
            case={
                "catalog_branch": "TRAINER_POST_BATTLE",
                "state": {"trainers": [{"id": 77, "defeated": True}]},
            },
        )
        state = _Execution(
            pc=instruction, execution_trace=[instruction],
            current_instruction_address=instruction, current_opcode=0x5C,
        )
        _execute_trainerbattle(context, state, instruction, raw)
        self.assertEqual(state.pc, instruction + len(raw))
        self.assertNotEqual(state.pc, explicit_victory)
        self.assertEqual(state.printers, [])
        self.assertEqual(
            state.decisions[0]["runtime_consumer"],
            "BattleSetup_GetScriptAddrAfterBattle",
        )

        # Real type-0 evidence: the next bytes are loadword/callstd post CFG;
        # the command's lose-speech pointer must not be synthesized as a field
        # post-battle printer.
        owner = "OBJECT:001/000:002"
        case = next(
            row for row in self.matrix["cases"]
            if row["owner_key"] == owner
            and row["catalog_branch"] == "TRAINER_POST_BATTLE"
        )
        output = build_case_oracle(
            self.clean, self.stage61, self.semantic, self.catalog, case,
            project_source_rom=self.stage60,
            repair_manifest=self.repair_manifest,
        )
        root = int(self.repair_manifest["owner_roots"][owner]["stage60_root"], 16)
        defeat = int.from_bytes(
            self.stage60[root - 0x08000000 + 10:root - 0x08000000 + 14],
            "little",
        )
        printer_pointers = {
            int(row["source_pointer"], 16)
            for row in output["sequences"][0]["visible_printers"]
        }
        self.assertNotIn(defeat, printer_pointers)
        self.assertEqual(self.stage60[root - 0x08000000 + 14], 0x0F)

    def test_dynamic_species_and_move_buffers_use_pinned_source_or_project_tables(self) -> None:
        source_context = SimpleNamespace(
            clean_rom=self.clean, text_provenance="CLEAN_SOURCE_RAW",
        )
        project_context = SimpleNamespace(
            clean_rom=self.stage60,
            text_provenance="PINNED_STAGE60_PROJECT_RAW",
        )
        for context, species, expected_table, expected_stride in (
            (source_context, 411, 0x08203CB8, 6),
            (project_context, 1620, 0x09FD6CD8, 8),
        ):
            raw, table, stride = _species_name(context, species, 0x08123456)
            self.assertEqual((table, stride), (expected_table, expected_stride))
            self.assertEqual(raw[-1], 0xFF)
            self.assertNotIn(0xFF, raw[:-1])
        for context, move, expected_table, expected_stride in (
            (source_context, 354, 0x08204660, 13),
            (project_context, 1062, 0x090453C8, 16),
        ):
            raw, table, stride = _move_name(context, move, 0x08123456)
            self.assertEqual((table, stride), (expected_table, expected_stride))
            self.assertEqual(raw[-1], 0xFF)
            self.assertNotIn(0xFF, raw[:-1])
        with self.assertRaisesRegex(Stage61InteractionOracleError, "OUT_OF_BOUNDS"):
            _species_name(source_context, 412, 0x08123456)
        with self.assertRaisesRegex(Stage61InteractionOracleError, "OUT_OF_BOUNDS"):
            _species_name(project_context, 1621, 0x08123456)
        with self.assertRaisesRegex(Stage61InteractionOracleError, "OUT_OF_BOUNDS"):
            _move_name(source_context, 355, 0x08123456)
        with self.assertRaisesRegex(Stage61InteractionOracleError, "OUT_OF_BOUNDS"):
            _move_name(project_context, 1063, 0x08123456)

    def test_require_complete_and_unpinned_project_source_fail_closed(self) -> None:
        project_case = next(
            row for row in self.matrix["cases"]
            if row["owner_role"] == "EXISTING_PROJECT_OWNER"
            and row["interaction_expected"]
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "PROJECT_STAGE60_SOURCE",
        ):
            build_case_oracle(
                self.clean, self.stage61, self.semantic, self.catalog,
                project_case,
            )
        self.assertEqual(
            __import__("hashlib").sha256(self.stage60).hexdigest(),
            STAGE60_SOURCE_SHA256,
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "INTERACTION_ORACLE_UNRESOLVED",
        ):
            audit_all_cases(
                self.clean, self.stage61, self.semantic, self.catalog,
                self.matrix["cases"], require_complete=True,
            )


class Stage61PrinterEngineAbiFocusedTests(unittest.TestCase):
    """Every visible-printer family binds source identity to JPN engine ABI."""

    FAMILY_CASES = (
        ("EVENT_TEXT", "FIELD_MESSAGE", 0x08002CF0, 0x080F7DA4),
        ("TRAINER_TOWER_EASY_CHAT", "FIELD_MESSAGE",
         0x08002CF0, 0x080F7DA4),
        ("UI_CHROME_YES_NO", "YES_NO", 0x08002CF0, 0x08110B90),
        ("UI_CHROME_MULTICHOICE", "MULTICHOICE_VERTICAL",
         0x08002CF0, 0x0812EED0),
        ("UI_CHROME_MULTICHOICE", "MULTICHOICE_GRID",
         0x08002C44, 0x08110CD4),
        ("ABI_VISIBLE_TEXT", "ABI_FIELD_MESSAGE",
         0x08002CF0, 0x080F7DA4),
        ("LIST_MENU_OPTION", "LIST_MENU", 0x08002CF0, 0x0812EE22),
        ("SEAGALLOP_MENU_OPTION", "SEAGALLOP_DESTINATION",
         0x08002C44, 0x0809D254),
        ("SEAGALLOP_MENU_OPTION", "SEAGALLOP_OTHER",
         0x08002C44, 0x0809D29A),
        ("SEAGALLOP_MENU_OPTION", "SEAGALLOP_EXIT",
         0x08002C44, 0x0809D2B8),
        ("UI_BRAILLE_TEXT", "BRAILLE", 0x08002C44, 0x0806B4F2),
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()

    @classmethod
    def _binding(
        cls, family: str, *, source_instruction: int = 0x08170000,
        source_caller: int | None = 0x08170004,
        rom: bytes | None = None,
    ) -> dict:
        return _printer_engine_binding(
            cls.stage61 if rom is None else rom,
            family,
            source_instruction_address=source_instruction,
            source_caller_instruction_address=source_caller,
        )

    def test_all_printer_families_bind_exact_engine_and_keep_source_identity(
        self,
    ) -> None:
        self.assertEqual(
            {family for _kind, family, _entry, _caller in self.FAMILY_CASES},
            set(TEXT_PRINTER_ENGINE_FAMILIES),
        )
        for index, (kind, family, expected_entry, expected_caller) in enumerate(
            self.FAMILY_CASES
        ):
            source_instruction = 0x08170000 + index * 8
            source_caller = source_instruction + 4
            with self.subTest(kind=kind, family=family):
                binding = self._binding(
                    family,
                    source_instruction=source_instruction,
                    source_caller=source_caller,
                )
                report = PrinterOracle(
                    kind=kind,
                    instruction_address=source_instruction,
                    caller_instruction_address=source_caller,
                    source_pointer=BAG_FULL_TEXT_POINTER,
                    raw=b"\x01\xFF", expanded=b"\x01\xFF",
                    engine_printer_binding=binding,
                    provenance=(
                        TRAINER_TOWER_DYNAMIC_TEXT_PROVENANCE
                        if kind == "TRAINER_TOWER_EASY_CHAT" else None
                    ),
                    runtime_pointer=(
                        TRAINER_TOWER_GSTRING_VAR4
                        if kind == "TRAINER_TOWER_EASY_CHAT" else None
                    ),
                ).to_report()
                self.assertEqual(
                    report["instruction_address"],
                    f"0x{expected_entry:08X}",
                )
                self.assertEqual(
                    report["caller_instruction_address"],
                    f"0x{expected_caller:08X}",
                )
                self.assertEqual(
                    report["engine_printer_entries"],
                    [f"0x{expected_entry:08X}"],
                )
                self.assertEqual(
                    report["engine_printer_abi"]["family"], family,
                )
                self.assertEqual(
                    report["provenance"]["source_instruction_address"],
                    f"0x{source_instruction:08X}",
                )
                self.assertEqual(
                    report["provenance"][
                        "source_caller_instruction_address"
                    ],
                    f"0x{source_caller:08X}",
                )
                if kind == "TRAINER_TOWER_EASY_CHAT":
                    self.assertEqual(
                        report["runtime_pointer"], "0x02021C88",
                    )

    def test_every_printer_construction_site_supplies_engine_binding(
        self,
    ) -> None:
        tree = ast.parse((
            ROOT / "tools/stage61_interaction_oracle.py"
        ).read_text())
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "PrinterOracle"
        ]
        self.assertEqual(len(calls), 8)
        for call in calls:
            with self.subTest(line=call.lineno):
                self.assertEqual(
                    sum(
                        keyword.arg == "engine_printer_binding"
                        for keyword in call.keywords
                    ),
                    1,
                )

    def test_reports_match_existing_runner_normalizer_without_new_schema(
        self,
    ) -> None:
        from scripts.run_stage61_mgba_validation import (
            _normalize_printer_oracle,
        )

        for index, (kind, family, expected_entry, expected_caller) in enumerate(
            self.FAMILY_CASES
        ):
            source_instruction = 0x08171000 + index * 8
            source_caller = source_instruction + 4
            with self.subTest(kind=kind, family=family):
                report = PrinterOracle(
                    kind=kind,
                    instruction_address=source_instruction,
                    caller_instruction_address=source_caller,
                    source_pointer=BAG_FULL_TEXT_POINTER,
                    raw=b"\x01\xFF", expanded=b"\x01\xFF",
                    engine_printer_binding=self._binding(
                        family,
                        source_instruction=source_instruction,
                        source_caller=source_caller,
                    ),
                    ui_coordinates=(1, 2) if kind in {
                        "UI_CHROME_YES_NO", "UI_CHROME_MULTICHOICE",
                    } else None,
                    runtime_pointer=(
                        TRAINER_TOWER_GSTRING_VAR4
                        if kind == "TRAINER_TOWER_EASY_CHAT" else None
                    ),
                ).to_report()
                normalized = _normalize_printer_oracle(
                    report, f"focused.{family}",
                )
                self.assertEqual(normalized["instruction_address"], expected_entry)
                self.assertEqual(
                    normalized["caller_instruction_address"], expected_caller,
                )
                self.assertEqual(
                    normalized["engine_printer_entries"], [expected_entry],
                )
                self.assertIsInstance(normalized["provenance"], dict)
                if "ui_coordinates" in report:
                    self.assertEqual(normalized["ui_coordinates"], [1, 2])

    def test_entry_and_every_caller_bl_preimage_mutation_fail_closed(
        self,
    ) -> None:
        for entry, family in (
            (0x08002C44, "BRAILLE"),
            (0x08002CF0, "FIELD_MESSAGE"),
        ):
            with self.subTest(entry=f"0x{entry:08X}"):
                mutated = bytearray(self.stage61)
                mutated[entry - 0x08000000] ^= 1
                with self.assertRaisesRegex(
                    Stage61InteractionOracleError,
                    "TEXT_PRINTER_ENGINE_ENTRY_PREIMAGE_DRIFT",
                ):
                    self._binding(family, rom=bytes(mutated))
        for family, spec in TEXT_PRINTER_ENGINE_FAMILIES.items():
            caller = spec["caller"]
            with self.subTest(family=family, caller=f"0x{caller:08X}"):
                mutated = bytearray(self.stage61)
                mutated[caller - 0x08000000] ^= 1
                with self.assertRaisesRegex(
                    Stage61InteractionOracleError,
                    "TEXT_PRINTER_CALLER_BL_PREIMAGE_DRIFT",
                ):
                    self._binding(family, rom=bytes(mutated))

    def test_source_binding_drift_identity_collision_and_reseal_fail_closed(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "TEXT_PRINTER_ENGINE_FAMILY_UNSUPPORTED",
        ):
            self._binding("UNKNOWN")

        spec = TEXT_PRINTER_ENGINE_FAMILIES["FIELD_MESSAGE"]
        for source_instruction, source_caller in (
            (spec["entry"], 0x08170004),
            (spec["caller"], 0x08170004),
            (0x08170000, spec["entry"]),
            (0x08170000, spec["caller"]),
        ):
            with self.subTest(
                source_instruction=f"0x{source_instruction:08X}",
                source_caller=f"0x{source_caller:08X}",
            ), self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "TEXT_PRINTER_SOURCE_ENGINE_IDENTITY_COLLISION",
            ):
                self._binding(
                    "FIELD_MESSAGE",
                    source_instruction=source_instruction,
                    source_caller=source_caller,
                )

        _validated_printer_source_contract.cache_clear()
        try:
            with patch(
                "tools.stage61_interaction_oracle.Path.read_bytes",
                return_value=b"pinned-source-drift",
            ), self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "TEXT_PRINTER_PINNED_SOURCE_DRIFT",
            ):
                self._binding("FIELD_MESSAGE")
        finally:
            _validated_printer_source_contract.cache_clear()

        binding = self._binding("FIELD_MESSAGE")
        for instruction, caller in (
            (0x08170008, 0x08170004),
            (0x08170000, 0x08170008),
        ):
            with self.subTest(
                instruction=f"0x{instruction:08X}",
                caller=f"0x{caller:08X}",
            ), self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "PRINTER_SOURCE_INSTRUCTION_BINDING_DRIFT",
            ):
                PrinterOracle(
                    kind="EVENT_TEXT", instruction_address=instruction,
                    caller_instruction_address=caller,
                    source_pointer=BAG_FULL_TEXT_POINTER,
                    raw=b"\x01\xFF", expanded=b"\x01\xFF",
                    engine_printer_binding=binding,
                ).to_report()

        report = PrinterOracle(
            kind="EVENT_TEXT", instruction_address=0x08170000,
            caller_instruction_address=0x08170004,
            source_pointer=BAG_FULL_TEXT_POINTER,
            raw=b"\x01\xFF", expanded=b"\x01\xFF",
            engine_printer_binding=binding,
        ).to_report()
        forged = deepcopy(report)
        source_instruction = forged["provenance"][
            "source_instruction_address"
        ]
        forged["instruction_address"] = source_instruction
        forged["engine_printer_entries"] = [source_instruction]
        forged["engine_printer_abi"]["entry"][
            "instruction_address"
        ] = source_instruction
        forged["engine_printer_abi"]["caller"][
            "decoded_target"
        ] = source_instruction
        forged["provenance"]["engine_printer_binding_sha256"] = \
            hashlib.sha256(_effect_test_stable(
                forged["engine_printer_abi"]
            )).hexdigest()
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "PRINTER_REPORT_ENGINE_ABI_DRIFT",
        ):
            _validate_printer_report_engine_contract(forged)

    def test_provenance_must_be_exact_mapping(self) -> None:
        binding = self._binding("FIELD_MESSAGE")
        report = PrinterOracle(
            kind="EVENT_TEXT", instruction_address=0x08170000,
            caller_instruction_address=0x08170004,
            source_pointer=BAG_FULL_TEXT_POINTER,
            raw=b"\x01\xFF", expanded=b"\x01\xFF",
            engine_printer_binding=binding,
        ).to_report()
        for provenance in (
            "CLEAN_SOURCE_RAW",
            {**report["provenance"], "unexpected": False},
            {
                key: value for key, value in report["provenance"].items()
                if key != "engine_printer_binding_sha256"
            },
        ):
            with self.subTest(provenance=provenance), self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "PRINTER_REPORT_PROVENANCE_MAPPING_REQUIRED",
            ):
                broken = deepcopy(report)
                broken["provenance"] = provenance
                _validate_printer_report_engine_contract(broken)

    def test_abi_visible_printer_requires_exact_engine_family_schema(
        self,
    ) -> None:
        pointer = BAG_FULL_TEXT_POINTER
        start = pointer - 0x08000000
        end = self.stage61.index(0xFF, start, start + 512) + 1
        raw = self.stage61[start:end]
        context = _Context(
            clean_rom=self.stage61, stage61_rom=self.stage61,
            semantic_report={}, npc={}, case={}, root=0x08170000,
            target_root=0x08170000, execution_root=0x08170000,
            root_plan={}, fixture=DEFAULT_FIXTURE, flag_mapping={},
            var_mapping={}, text_assets={},
            text_provenance="CLEAN_SOURCE_RAW", abi_index={},
            instruction_repairs={}, source_suppression_contract=None,
            stage61_script_bytes=frozenset(),
        )
        row = {
            "kind": "ABI_VISIBLE_TEXT",
            "source_pointer": f"0x{pointer:08X}",
            "raw_hex": raw.hex(),
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "provenance": "CLEAN_SOURCE_RAW",
            "engine_printer_family": "ABI_FIELD_MESSAGE",
        }
        state = _Execution(pc=0x08170000)
        _append_abi_printers(
            context, state, 0x08170000,
            {"abi_key": "TEST:ABI", "visible_printers": [row]},
        )
        self.assertEqual(len(state.printers), 1)
        self.assertEqual(
            state.printers[0].to_report()["engine_printer_abi"]["family"],
            "ABI_FIELD_MESSAGE",
        )

        invalid_rows = (
            {key: value for key, value in row.items()
             if key != "engine_printer_family"},
            {**row, "engine_printer_family": "FIELD_MESSAGE"},
            {**row, "unexpected": False},
            {**row, "provenance": ""},
            {**row, "provenance": {"kind": "CLEAN_SOURCE_RAW"}},
        )
        for invalid in invalid_rows:
            with self.subTest(invalid=invalid), self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "visible printer schema不正",
            ):
                _append_abi_printers(
                    context, _Execution(pc=0x08170000), 0x08170000,
                    {"abi_key": "TEST:ABI", "visible_printers": [invalid]},
                )


class Stage61TrainerTowerDynamicTextFocusedTests(unittest.TestCase):
    """JPN local Trainer Tower speech must never trust a captured RAM string."""

    ROOT_PC = 0x0816E06D
    OWNER = "OBJECT:002/001:001"

    @classmethod
    def setUpClass(cls) -> None:
        cls.stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        tower = next(
            row for row in manifest["special_abis"]
            if row["special_id"] == 404
        )
        source_path = tower["source"]["path"]
        cls.abi_index = _interaction_abi_index(
            cls.stage61,
            {"special_abis": [tower], "native_abis": []},
            source_blobs={source_path: (ROOT / source_path).read_bytes()},
        )

    @classmethod
    def _context(cls, rom: bytes | None = None) -> _Context:
        source = cls.stage61 if rom is None else rom
        return _Context(
            clean_rom=source, stage61_rom=source, semantic_report={},
            npc={
                "npc_id": cls.OWNER, "group": 2, "map": 1,
                "map_key": "TrainerTower_1F", "local_id": 2, "flag": 2,
            },
            case={
                "case_id": "trainer-tower-1f-singles",
                "owner_key": cls.OWNER,
                "state": {
                    "flags": [{"id": 2, "value": False}],
                    "vars": [], "items": [], "trainers": [],
                },
            },
            root=cls.ROOT_PC, target_root=cls.ROOT_PC,
            execution_root=cls.ROOT_PC, root_plan={"references": []},
            fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
            text_assets={}, text_provenance="PINNED_STAGE60_PROJECT_RAW",
            abi_index=cls.abi_index, instruction_repairs={},
            source_suppression_contract=None,
            stage61_script_bytes=frozenset(),
        )

    def test_map1_root_rederives_challenge_and_exact_gstringvar4(self) -> None:
        paths = _execute(self._context())
        self.assertEqual(len(paths), 1)
        state = paths[0]
        self.assertEqual(
            [(row["kind"], row["result_value"], row["source_pointer"])
             for row in state.decisions],
            [("ABI_RESULT", 0, "0x08447AE6")],
        )
        self.assertEqual(state.decisions[0]["source_precondition"], {
            "save": {
                "trainer_tower_data_source":
                    "LOCAL_FALLBACK_CANONICAL_SAVE_ONLY",
                "sector30_special_sentinel_present": False,
                "sector31_special_sentinel_present": False,
                "ereader_fixture_admitted": False,
            },
            "scope_limit":
                "ARBITRARY_EXTERNAL_EREADER_SAVE_OUT_OF_SCOPE",
        })
        self.assertEqual(
            state.decisions[0]["source_precondition"]["save"],
            TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION,
        )
        # The fixed floor is SINGLE.  The impossible generic result=2 branch
        # used to select trainer 1's FFFF filler; source-exact execution must
        # retain only trainer 0.
        self.assertEqual(state.vars[0x8006], 0)
        self.assertEqual(len(state.printers), 1)
        printer = state.printers[0].to_report()
        self.assertEqual(printer["kind"], "TRAINER_TOWER_EASY_CHAT")
        self.assertEqual(printer["source_pointer"], "0x08447B18")
        self.assertNotEqual(printer["source_pointer"], "0x08447C5C")
        self.assertEqual(printer["runtime_pointer"], "0x02021C88")
        self.assertEqual(
            printer["raw_hex"],
            "235014000c360348000c1002fe442300020f370c0200440c36acff",
        )
        self.assertEqual(
            printer["raw_sha256"],
            "df656d63dfa1374c5bd6c40d1721bd24dc4b58e35b1351a524afad43bcfd6c35",
        )
        self.assertEqual(
            printer["provenance"]["kind"],
            TRAINER_TOWER_DYNAMIC_TEXT_PROVENANCE,
        )
        self.assertEqual(printer["instruction_address"], "0x08002CF0")
        self.assertEqual(
            printer["caller_instruction_address"], "0x080F7DA4",
        )
        self.assertEqual(
            printer["provenance"]["source_instruction_address"],
            "0x08192DA5",
        )
        self.assertEqual(
            printer["provenance"]["source_caller_instruction_address"],
            "0x081A9B2E",
        )
        self.assertEqual(
            printer["engine_printer_entries"], ["0x08002CF0"],
        )
        self.assertEqual(
            printer["engine_printer_abi"]["family"], "FIELD_MESSAGE",
        )
        self.assertEqual(
            [row["result_capture"] for row in state.abi_dispatches],
            [{
                "kind": "GLOBAL_VAR_RESULT", "source_id": 0x800D,
                "target_id": 0x800D, "value": 0,
            }, {"kind": "NONE", "value": None}],
        )
        self.assertEqual(
            [row["effect_member_count"] for row in state.abi_dispatches],
            [1, 0],
        )
        speech_trace = state.abi_dispatches[1]["execution_trace_index"]
        self.assertFalse(any(
            row["execution_trace_index"] == speech_trace
            for row in state.effects
        ))

    def test_dynamic_message_requires_exact_producer_and_pointer(self) -> None:
        context = self._context()
        consumer = 0x08192DA5
        missing = _Execution(
            pc=consumer, loaded_words={0: TRAINER_TOWER_GSTRING_VAR4},
            execution_trace=[consumer],
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "TRAINER_TOWER_GSTRINGVAR4_PRODUCER_REQUIRED",
        ):
            _append_message(context, missing, consumer, 0)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "EVENT_MESSAGE_DYNAMIC_POINTER_UNSUPPORTED",
        ):
            _append_message(context, _Execution(pc=consumer), consumer,
                            TRAINER_TOWER_GSTRING_VAR4 + 4)

        paths = _execute(context)
        drifted = paths[0].clone()
        produced = drifted.runtime_text_buffers[TRAINER_TOWER_GSTRING_VAR4]
        for bad_precondition in (
            {
                **produced.source_precondition,
                "save": {
                    **produced.source_precondition["save"],
                    "ereader_fixture_admitted": True,
                },
            },
            {
                **produced.source_precondition,
                "save": {
                    **produced.source_precondition["save"],
                    "sector30_special_sentinel_present": 0,
                },
            },
            {
                **produced.source_precondition,
                "unexpected": False,
            },
            {
                "save": produced.source_precondition["save"],
            },
        ):
            drifted.runtime_text_buffers[TRAINER_TOWER_GSTRING_VAR4] = \
                replace(produced, source_precondition=bad_precondition)
            with self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "TRAINER_TOWER_LOCAL_FALLBACK_PRECONDITION_DRIFT",
            ):
                _append_message(
                    context, drifted, consumer, TRAINER_TOWER_GSTRING_VAR4,
                )

    def test_all_naturally_interactive_local_floor_owners(self) -> None:
        # object_index is used here (not local_id).  These are exactly the
        # seven trainers left visible by the bundled floors 0..3.
        rows = (
            # map, object_index, root, local_id, flag, challenge, trainer,
            # Easy Chat speechAfter source
            (1, 2, 0x0816E073, 3, 3, 0, 0, 0x08447B18),
            (2, 1, 0x0816E06D, 2, 2, 1, 0, 0x08447EEC),
            (2, 4, 0x0816E07F, 5, 5, 1, 1, 0x08448030),
            (3, 1, 0x0816E06D, 2, 2, 2, 1, 0x08448404),
            (3, 2, 0x0816E073, 3, 3, 2, 2, 0x08448548),
            (3, 3, 0x0816E079, 4, 4, 2, 0, 0x084482C0),
            (4, 2, 0x0816E073, 3, 3, 0, 0, 0x08448694),
        )
        for (map_number, object_index, root, local_id, flag,
             expected_challenge, expected_trainer,
             expected_source) in rows:
            owner = f"OBJECT:002/{map_number:03d}:{object_index:03d}"
            with self.subTest(owner=owner):
                context = replace(
                    self._context(),
                    npc={
                        "npc_id": owner, "group": 2, "map": map_number,
                        "map_key": f"TrainerTower_{map_number}F",
                        "local_id": local_id, "flag": flag,
                    },
                    case={
                        "case_id": f"trainer-tower-natural-{map_number}-{object_index}",
                        "owner_key": owner,
                        "state": {
                            "flags": [{"id": flag, "value": False}],
                            "vars": [], "items": [], "trainers": [],
                        },
                    },
                    root=root, target_root=root, execution_root=root,
                )
                floor_source, challenge = \
                    _trainer_tower_local_floor_source(context)
                self.assertEqual(challenge, expected_challenge)
                self.assertEqual(
                    floor_source,
                    0x08447AE4 + (map_number - 1) * 0x3D4,
                )
                paths = _execute(context)
                self.assertEqual(len(paths), 1)
                state = paths[0]
                self.assertEqual(state.vars[0x8006], expected_trainer)
                self.assertEqual(len(state.printers), 1)
                printer = state.printers[0].to_report()
                self.assertEqual(
                    printer["source_pointer"], f"0x{expected_source:08X}",
                )
                self.assertEqual(
                    printer["runtime_pointer"], "0x02021C88",
                )
                self.assertNotEqual(printer["raw_hex"], "feff")

    def test_jpn_producer_abi_and_local_words_fail_closed_on_drift(self) -> None:
        abi_drift = bytearray(self.stage61)
        abi_drift[0x0816129C - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "TRAINER_TOWER_JPN_ABI_DRIFT",
        ):
            _execute(self._context(bytes(abi_drift)))

        word_drift = bytearray(self.stage61)
        word_drift[0x08447B18 - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "TRAINER_TOWER_JPN_LOCAL_DATA_DRIFT",
        ):
            _execute(self._context(bytes(word_drift)))

        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "TRAINER_TOWER_EASY_CHAT_WORD_INVALID",
        ):
            _trainer_tower_easy_chat_word(
                self._context(), 22 << 9, 0x081A9B23,
            )

    def test_jpn_local_prize_table_fails_closed_on_drift(self) -> None:
        drifted = bytearray(self.stage61)
        drifted[0x08448E10 - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "TRAINER_TOWER_JPN_PRIZE_LIST_DRIFT",
        ):
            _execute(self._context(bytes(drifted)))

    @classmethod
    def _synthetic_selector_context(
        cls, selector: int, *, initial_result: int | None = None,
        party_state: int | None = None,
    ) -> _Context:
        root = 0x09FFF000

        def setvar(identifier: int, value: int) -> bytes:
            return (
                b"\x16" + identifier.to_bytes(2, "little")
                + value.to_bytes(2, "little")
            )

        script = b""
        if initial_result is not None:
            script += setvar(0x800D, initial_result)
        script += setvar(0x8004, selector) + bytes.fromhex("25940102")
        rom = bytearray(cls.stage61)
        offset = root - 0x08000000
        rom[offset:offset + len(script)] = script
        external = [] if party_state is None else [{
            "kind": "PARTY_USABLE_FOR_DOUBLE", "id": 0,
            "value": party_state,
        }]
        base = cls._context(bytes(rom))
        return replace(
            base, root=root, target_root=root, execution_root=root,
            case={
                "case_id": f"trainer-tower-selector-{selector}-{party_state}",
                "owner_key": cls.OWNER,
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "control_requirements": {
                    "external": external, "internal": [],
                },
            },
            stage61_script_bytes=frozenset(
                range(root, root + len(script)),
            ),
        )

    @classmethod
    def _synthetic_selector_sequence_context(
        cls, selectors: tuple[int, ...],
    ) -> _Context:
        root = 0x09FFF000

        def setvar(identifier: int, value: int) -> bytes:
            return (
                b"\x16" + identifier.to_bytes(2, "little")
                + value.to_bytes(2, "little")
            )

        script = b"".join(
            setvar(0x8004, selector) + bytes.fromhex("259401")
            for selector in selectors
        ) + b"\x02"
        rom = bytearray(cls.stage61)
        offset = root - 0x08000000
        rom[offset:offset + len(script)] = script
        base = cls._context(bytes(rom))
        return replace(
            base, root=root, target_root=root, execution_root=root,
            case={
                "case_id": "trainer-tower-selector-sequence-"
                    + "-".join(str(selector) for selector in selectors),
                "owner_key": cls.OWNER,
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "control_requirements": {"external": [], "internal": []},
            },
            stage61_script_bytes=frozenset(
                range(root, root + len(script)),
            ),
        )

    def test_owner_transaction_correlates_status_prize_and_final_time(
        self,
    ) -> None:
        context = self._synthetic_selector_sequence_context((7, 8, 9))
        paths = _execute(context)
        self.assertEqual(len(paths), 2)

        by_capacity = {
            next(
                row["required_value"] for row in state.abi_control_reads
                if row["kind"] == "BAG_CAPACITY"
            ): state
            for state in paths
        }
        self.assertEqual(set(by_capacity), {0, 1})
        expected = {
            0: {
                "status": 6,
                "mode": "GIVE_PRIZE_BAG_FULL_EXACT",
                "items": [],
            },
            1: {
                "status": 7,
                "mode": "GIVE_PRIZE_BAG_SUCCESS_EXACT",
                "items": [{"id": 63, "count": 1}],
            },
        }
        for capacity, state in by_capacity.items():
            with self.subTest(capacity=capacity):
                self.assertEqual(
                    state.trainer_tower_status_current,
                    expected[capacity]["status"],
                )
                self.assertEqual(
                    list(state.trainer_tower_dispatch_modes.values()),
                    [
                        "GET_OWNER_STATE_PACKED_EXACT",
                        expected[capacity]["mode"],
                        "CHECK_FINAL_TIME_LOCAL_NEW_RECORD_EXACT",
                    ],
                )
                required = _runner_required_postconditions(context, state)
                self.assertEqual(required["items"], expected[capacity]["items"])
                self.assertEqual(required["persistent"], [{
                    "block": "SB1", "offset": 0x3D3E,
                    "value": expected[capacity]["status"],
                }])

    def test_has_spoken_to_owner_reads_the_correlated_status_bit(self) -> None:
        fresh = _execute(
            self._synthetic_selector_sequence_context((20,))
        )
        self.assertEqual(len(fresh), 1)
        self.assertEqual(fresh[0].vars[0x800D], 0)
        self.assertEqual(fresh[0].trainer_tower_status_current, 0)

        context = self._synthetic_selector_sequence_context((7, 20))
        spoken = _execute(context)
        self.assertEqual(len(spoken), 1)
        state = spoken[0]
        self.assertEqual(state.vars[0x800D], 1)
        self.assertEqual(state.trainer_tower_status_current, 4)
        self.assertEqual(
            list(state.trainer_tower_dispatch_modes.values()),
            [
                "GET_OWNER_STATE_PACKED_EXACT",
                "HAS_SPOKEN_TO_OWNER_PACKED_EXACT",
            ],
        )
        self.assertEqual(
            _runner_required_postconditions(context, state)["persistent"],
            [{"block": "SB1", "offset": 0x3D3E, "value": 4}],
        )

    def test_start_challenge_resets_fresh_timer_and_sets_validated(self) -> None:
        context = self._synthetic_selector_sequence_context((6,))
        paths = _execute(context)
        self.assertEqual(len(paths), 1)
        state = paths[0]
        self.assertNotIn(0x800D, state.vars)
        self.assertEqual(state.trainer_tower_status_current, 0x20)
        self.assertEqual(state.trainer_tower_timer_current, 0)
        self.assertEqual(
            list(state.trainer_tower_dispatch_modes.values()),
            ["START_CHALLENGE_LOCAL_FRESH_NO_RESULT"],
        )
        timer_effect = next(
            row for row in state.effects if row["domain"] == "volatile"
        )
        self.assertEqual(timer_effect["operation"], "RESET_ZERO_AND_ENABLE")
        self.assertEqual(
            _runner_required_postconditions(context, state)["persistent"],
            [{"block": "SB1", "offset": 0x3D3E, "value": 0x20}],
        )

    def test_challenge_status_clears_lost_then_returns_to_normal(self) -> None:
        context = self._synthetic_selector_sequence_context((11, 12, 12))
        paths = _execute(context)
        self.assertEqual(len(paths), 1)
        state = paths[0]
        self.assertEqual(state.vars[0x800D], 2)
        self.assertEqual(state.trainer_tower_status_current, 0)
        self.assertEqual(
            list(state.trainer_tower_dispatch_modes.values()),
            [
                "SET_LOST_FRESH_NO_RESULT",
                "GET_CHALLENGE_STATUS_LOST_CLEAR_EXACT",
                "GET_CHALLENGE_STATUS_NORMAL_EXACT",
            ],
        )
        self.assertEqual(
            [row["result_value"] for row in state.decisions], [0, 2],
        )

    def test_get_current_time_formats_three_fresh_jpn_buffers(self) -> None:
        paths = _execute(self._synthetic_selector_context(
            13, initial_result=7,
        ))
        self.assertEqual(len(paths), 1)
        state = paths[0]
        self.assertEqual(state.vars[0x800D], 7)
        self.assertEqual(state.string_vars, {
            0x02: bytes.fromhex("00a1ff"),
            0x03: bytes.fromhex("00a1ff"),
            0x04: bytes.fromhex("a1a1ff"),
        })
        self.assertEqual(
            state.abi_dispatches[-1]["result_capture"],
            {"kind": "NONE", "value": None},
        )
        self.assertEqual(
            list(state.trainer_tower_dispatch_modes.values()),
            ["GET_CURRENT_TIME_LOCAL_FRESH_BUFFERS_NO_RESULT"],
        )

    def test_check_doubles_uses_one_exact_party_control(self) -> None:
        for mons_state in (0, 1, 2):
            with self.subTest(mons_state=mons_state):
                paths = _execute(self._synthetic_selector_context(
                    16, party_state=mons_state,
                ))
                self.assertEqual(len(paths), 1)
                state = paths[0]
                self.assertEqual(state.vars[0x800D], mons_state)
                self.assertEqual(
                    state.abi_dispatches[-1]["result_capture"],
                    {
                        "kind": "GLOBAL_VAR_RESULT",
                        "source_id": 0x800D, "target_id": 0x800D,
                        "value": mons_state,
                    },
                )
                self.assertEqual(len(state.abi_control_reads), 1)
                self.assertEqual(
                    state.abi_control_reads[0]["required_value"],
                    mons_state,
                )
                self.assertEqual(
                    state.abi_control_reads[0]["relation"],
                    "GET_MONS_STATE_TO_DOUBLES",
                )

    def test_get_num_floors_uses_jpn_local_blob_comparison(self) -> None:
        paths = _execute(self._synthetic_selector_context(17))
        self.assertEqual(len(paths), 1)
        state = paths[0]
        self.assertEqual(state.vars[0x800D], 0)
        self.assertEqual(state.string_vars, {})
        self.assertEqual(
            list(state.trainer_tower_dispatch_modes.values()),
            ["GET_NUM_FLOORS_LOCAL_EQUAL_EXACT"],
        )
        decision = state.decisions[-1]
        self.assertEqual(decision["num_floors"], 4)
        self.assertEqual(decision["compared_floor_byte"], 4)

    def test_encounter_music_preserves_stale_result_and_has_audio_effect(
        self,
    ) -> None:
        paths = _execute(self._synthetic_selector_context(
            19, initial_result=7,
        ))
        self.assertEqual(len(paths), 1)
        state = paths[0]
        self.assertEqual(state.vars[0x800D], 7)
        self.assertEqual(
            state.abi_dispatches[-1]["result_capture"],
            {"kind": "NONE", "value": None},
        )
        self.assertEqual(
            [(row["domain"], row["owner"], row["relation"])
             for row in state.effects if row.get("abi_key")
             and row["domain"] == "audio"],
            [(
                "audio", "TRAINER_TOWER_ENCOUNTER_MUSIC",
                "PLAY_LOCAL_TRAINER_ENCOUNTER_MUSIC_EXACT",
            )],
        )

    def test_double_coordinate_root_is_bounded_and_battle_exact(self) -> None:
        root = 0x081A9C3C
        context = replace(
            self._context(),
            npc={
                "npc_id": "COORD:002/001:001", "group": 2, "map": 1,
                "map_key": "TrainerTower_1F", "local_id": 0, "flag": 0,
            },
            case={
                "case_id": "trainer-tower-double-coordinate-eligible",
                "owner_key": "COORD:002/001:001",
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "control_requirements": {
                    "external": [{
                        "kind": "PARTY_USABLE_FOR_DOUBLE", "id": 0,
                        "value": 0,
                    }],
                    "internal": [],
                },
            },
            root=root, target_root=root, execution_root=root,
        )
        paths = _execute(context)
        self.assertEqual(len(paths), 1)
        state = paths[0]
        self.assertIsNotNone(state.battle_start_effects)
        self.assertEqual(state.battle_resume_pc, 0x081A99AF)
        self.assertEqual(
            _runner_battle_start_required_postconditions(
                context, state,
            )["battle"],
            {
                "active": True, "trainer_opponent": 0,
                "enemy_species": 20, "outcome": 0,
            },
        )
        self.assertEqual(
            _runner_required_postconditions(context, state)["persistent"],
            [{"block": "SB1", "offset": 0x3D3C, "value": 1}],
        )
        continuation = _post_battle_continuation_contract(state)
        self.assertEqual(continuation["resume_kind"], "NEXT_PC")
        self.assertEqual(continuation["resume_pc"], "0x081A99AF")
        self.assertIn(
            "DO_BATTLE_LOCAL_CANONICAL_WIN",
            state.trainer_tower_dispatch_modes.values(),
        )


class Stage61PokedexPhysicalScenarioFocusedTests(unittest.TestCase):
    """Oak rating SPECIALs share one byte-exact save-state scenario."""

    OWNER_ID = "OBJECT:004/003:003"
    ROOT_PC = 0x0817CBB0

    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = (
            ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
        ).read_bytes()
        cls.stage60 = (
            ROOT / "build/stages/60_wild_species_root_repair.gba"
        ).read_bytes()
        cls.stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        cls.manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        cls.source_blobs, _reports = _interaction_abi_pinned_inputs()

    @classmethod
    def _pokedex_abi_index(cls) -> dict[str, dict]:
        rows = []
        for raw in cls.manifest["special_abis"]:
            if raw["special_id"] not in {212, 213, 432}:
                continue
            entry = deepcopy(raw)
            entry.update(_special_semantic_contract(
                entry["special_id"], entry["symbol"],
            ))
            rows.append(entry)
        return _interaction_abi_index(
            cls.stage61, {"special_abis": rows, "native_abis": []},
            source_blobs=cls.source_blobs,
        )

    @classmethod
    def _all_fresh_abi_entries(cls) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for raw in [
            *cls.manifest["special_abis"], *cls.manifest["native_abis"],
        ]:
            entry = deepcopy(raw)
            pointer = int(entry["target_pointer"], 16)
            entry["target_pointer"] = pointer \
                if entry["abi_key"].startswith("SPECIAL:") else pointer & ~1
            entry["source_status"] = "PINNED_SOURCE_VERIFIED"
            if entry.get("special_id") in {158, 212, 213, 432}:
                entry.update(_special_semantic_contract(
                    entry["special_id"], entry["symbol"],
                ))
            result[entry["abi_key"]] = entry
        return result

    @classmethod
    def _context(cls, abi_index: dict[str, dict]) -> _Context:
        return _Context(
            clean_rom=cls.stage61, stage61_rom=cls.stage61,
            semantic_report={}, npc={"local_id": 4},
            case={"state": {
                "flags": [], "vars": [], "items": [], "trainers": [],
            }},
            root=cls.ROOT_PC, target_root=cls.ROOT_PC,
            execution_root=cls.ROOT_PC, root_plan={},
            fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
            text_assets={}, text_provenance="PINNED_STAGE60_PROJECT_RAW",
            abi_index=abi_index, instruction_repairs={},
            source_suppression_contract=None,
            stage61_script_bytes=frozenset(),
        )

    def test_18_scenarios_cover_rating_mew_national_and_has_all_sources(
        self,
    ) -> None:
        scenarios = list(_pokedex_physical_scenarios())
        self.assertEqual(len(scenarios), 18)
        self.assertEqual(
            {row["rating_pointer"] for row in scenarios},
            set(_POKEDEX_RATING_POINTERS),
        )
        self.assertEqual(
            {(row["kanto_caught"], row["mew_caught"])
             for row in scenarios if row["kanto_caught"] == 150},
            {(150, False), (150, True)},
        )
        self.assertTrue(any(row["kanto_caught"] == 151 for row in scenarios))
        self.assertEqual(
            {row["national_enabled"] for row in scenarios}, {False, True},
        )
        self.assertEqual(
            {row["has_all_required"] for row in scenarios}, {False, True},
        )
        fixture_keys = {
            "fixture_kind", "scenario_id", "national_enabled",
            "national_magic", "national_var", "national_flag",
            "owned_hex", "seen_hex", "seen1_hex", "seen2_hex",
            "kanto_seen", "kanto_caught", "national_seen",
            "national_caught", "mew_caught", "has_all_required",
        }
        for scenario in scenarios:
            fixture = scenario["layout"]
            self.assertEqual(set(fixture), fixture_keys)
            self.assertEqual(runner_fixture_key(fixture), scenario["layout_ref"])
            for key in ("owned_hex", "seen_hex", "seen1_hex", "seen2_hex"):
                self.assertEqual(len(fixture[key]), 104)
                self.assertEqual(fixture[key], fixture[key].lower())
            self.assertEqual(
                fixture["seen_hex"],
                fixture["seen1_hex"],
            )
            self.assertEqual(
                fixture["seen_hex"],
                fixture["seen2_hex"],
            )

        broken = deepcopy(scenarios[0]["layout"])
        broken["seen1_hex"] = "00" * 52
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "seen mirror不一致",
        ):
            runner_fixture_key(broken)
        missing_source = dict(self.source_blobs)
        missing_source.pop("vendor/upstream/pokefirered/src/pokedex_screen.c")
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "POKEDEX physical model source不一致",
        ):
            rows = []
            for raw in self.manifest["special_abis"]:
                if raw["special_id"] in {212, 213, 432}:
                    entry = deepcopy(raw)
                    entry.update(_special_semantic_contract(
                        entry["special_id"], entry["symbol"],
                    ))
                    rows.append(entry)
            _interaction_abi_index(
                self.stage61,
                {"special_abis": rows, "native_abis": []},
                source_blobs=missing_source,
            )

    def test_212_213_432_reuse_scenario_and_materialize_exact_public_value(
        self,
    ) -> None:
        abi_index = self._pokedex_abi_index()
        context = self._context(abi_index)
        count_pc = 0x0819499A
        count_raw = self.stage61[
            count_pc - 0x08000000:count_pc - 0x08000000 + 5
        ]
        initial = _Execution(
            pc=count_pc, vars={0x8004: 0, 0x8005: 0xEEEE, 0x8006: 0xFFFF},
            execution_trace=[count_pc], current_instruction_address=count_pc,
            current_opcode=0x26,
        )
        branches = _fork_abi_command(
            context, initial, count_pc, 0x26, count_raw,
        )
        self.assertEqual(len(branches), 18)
        by_id = {
            row["scenario_id"]: row for row in _pokedex_physical_scenarios()
        }
        observed_rating_pointers = set()
        observed_has_all = set()
        for branch in branches:
            scenario = by_id[branch.pokedex_scenario_id]
            self.assertEqual(branch.vars[0x8005], scenario["kanto_seen"])
            self.assertEqual(branch.vars[0x8006], scenario["kanto_caught"])
            self.assertEqual(
                branch.vars[0x800D], int(scenario["national_enabled"]),
            )
            self.assertEqual(len(branch.abi_control_reads), 1)

            repeated = branch.clone()
            national_pc = 0x081949DC
            national_raw = self.stage61[
                national_pc - 0x08000000:national_pc - 0x08000000 + 5
            ]
            repeated.vars[0x8004] = 1
            repeated.execution_trace.append(national_pc)
            repeated.current_instruction_address = national_pc
            repeated.current_opcode = 0x26
            repeated.pc = national_pc
            national = _fork_abi_command(
                context, repeated, national_pc, 0x26, national_raw,
            )
            self.assertEqual(len(national), 1)
            self.assertEqual(national[0].pokedex_scenario_id,
                             branch.pokedex_scenario_id)
            self.assertEqual(len(national[0].abi_control_reads), 1)
            self.assertEqual(national[0].vars[0x8005],
                             scenario["national_seen"])
            self.assertEqual(national[0].vars[0x8006],
                             scenario["national_caught"])

            rating = branch.clone()
            rating_pc = 0x08194965
            rating_raw = self.stage61[
                rating_pc - 0x08000000:rating_pc - 0x08000000 + 3
            ]
            rating.vars[0x8004] = scenario["kanto_caught"]
            rating.execution_trace.append(rating_pc)
            rating.current_instruction_address = rating_pc
            rating.current_opcode = 0x25
            rating.pc = rating_pc
            rated = _fork_abi_command(
                context, rating, rating_pc, 0x25, rating_raw,
            )[0]
            self.assertEqual(rated.vars[0x800D], scenario["rating_result"])
            self.assertEqual(len(rated.printers), 1)
            self.assertEqual(
                rated.printers[0].source_pointer, scenario["rating_pointer"],
            )
            observed_rating_pointers.add(rated.printers[0].source_pointer)

            all_pc = 0x081949FB
            all_raw = self.stage61[
                all_pc - 0x08000000:all_pc - 0x08000000 + 5
            ]
            national_state = national[0]
            national_state.execution_trace.append(all_pc)
            national_state.current_instruction_address = all_pc
            national_state.current_opcode = 0x26
            national_state.pc = all_pc
            checked = _fork_abi_command(
                context, national_state, all_pc, 0x26, all_raw,
            )[0]
            self.assertEqual(
                checked.vars[0x800D], int(scenario["has_all_required"]),
            )
            observed_has_all.add(checked.vars[0x800D])
        self.assertEqual(observed_rating_pointers, set(_POKEDEX_RATING_POINTERS))
        self.assertEqual(observed_has_all, {0, 1})

        fixtures: dict[str, dict] = {}
        projected = _materialize_control_requirement(
            self.stage61, branches[0].abi_control_reads[0],
            owner_keys=[self.OWNER_ID], fixtures=fixtures,
        )
        self.assertEqual(set(projected["value"]), {
            "scenario_id", "national_enabled", "kanto_seen",
            "kanto_caught", "national_seen", "national_caught",
            "mew_caught", "has_all_required", "layout_ref",
        })
        self.assertEqual(projected["relation_evidence"], [{
            "operator": "EXACT_POKEDEX_SAVE_STATE",
        }])
        self.assertEqual(projected["fixture_keys"], [
            projected["value"]["layout_ref"],
        ])
        fixture = fixtures[projected["value"]["layout_ref"]]
        self.assertEqual(fixture["fixture_kind"], "POKEDEX_LAYOUT")

    def test_object_004_003_003_finishes_below_existing_path_cap(self) -> None:
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph

        semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        repair_manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text())
        inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        owner = next(
            row for row in inventory["owners"]
            if row["owner_id"] == self.OWNER_ID
        )
        self.assertEqual(owner["root"], self.ROOT_PC)
        graph = SemanticScriptGraph(self.stage61)
        graph.walk([self.ROOT_PC])
        self.assertEqual(graph.diagnostics, [])

        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(
            self.source_blobs[builder_path]
        ).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        text_assets, _provenance = _independent_runtime_text_assets(
            self.clean, self.stage60, self.stage61, semantic,
            repair_manifest, graph, source_blobs=self.source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            self.clean, self.stage60, self.stage61, semantic, owner, graph,
            text_assets, self._all_fresh_abi_entries(), self.source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, self.ROOT_PC),
        )
        self.assertEqual(blockers, [])
        self.assertEqual(len(executions), 3623)
        self.assertLess(len(executions), MAX_EXECUTION_PATHS)
        scenario_ids = {
            state.pokedex_scenario_id for _context, state in executions
            if state.pokedex_scenario_id is not None
        }
        self.assertEqual(scenario_ids, {
            row["scenario_id"] for row in _pokedex_physical_scenarios()
        })
        self.assertEqual({
            printer.source_pointer
            for _context, state in executions
            for printer in state.printers
            if printer.kind == "PROF_OAK_RATING_MESSAGE"
        }, set(_POKEDEX_RATING_POINTERS))
        self.assertTrue(all(
            len([
                row for row in state.abi_control_reads
                if row.get("kind") == "POKEDEX_STATE"
            ]) <= 1
            for _context, state in executions
        ))


class Stage61CoinsABIFocusedTests(unittest.TestCase):
    ROOT_PC = 0x0818509C
    OWNER_ID = "OBJECT:010/014:001"

    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = (
            ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
        ).read_bytes()
        cls.stage60 = (
            ROOT / "build/stages/60_wild_species_root_repair.gba"
        ).read_bytes()
        cls.stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        cls.semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        cls.repair_manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text())
        cls.inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        cls.manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        cls.source_blobs, _reports = _interaction_abi_pinned_inputs()

    @classmethod
    def _fresh_abi_entries(cls) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for raw in [
            *cls.manifest["special_abis"], *cls.manifest["native_abis"],
        ]:
            entry = deepcopy(raw)
            pointer = int(entry["target_pointer"], 16)
            entry["target_pointer"] = pointer \
                if entry["abi_key"].startswith("SPECIAL:") else pointer & ~1
            entry["source_status"] = "PINNED_SOURCE_VERIFIED"
            if entry.get("special_id") in {158, 212, 213, 432}:
                entry.update(_special_semantic_contract(
                    entry["special_id"], entry["symbol"],
                ))
            result[entry["abi_key"]] = entry
        return result

    def test_product_coins_clerk_root_correlates_full_amount_boundaries(
        self,
    ) -> None:
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph

        semantic = deepcopy(self.semantic)
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(
            self.source_blobs[builder_path]
        ).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        owner = next(
            row for row in self.inventory["owners"]
            if row["owner_id"] == self.OWNER_ID
        )
        self.assertEqual(owner["root"], self.ROOT_PC)
        graph = SemanticScriptGraph(self.stage61)
        graph.walk([self.ROOT_PC])
        self.assertEqual(graph.diagnostics, [])
        text_assets, _provenance = _independent_runtime_text_assets(
            self.clean, self.stage60, self.stage61, semantic,
            self.repair_manifest, graph, source_blobs=self.source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            self.clean, self.stage60, self.stage61, semantic, owner, graph,
            text_assets, self._fresh_abi_entries(), self.source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, self.ROOT_PC),
        )
        self.assertEqual(blockers, [])
        self.assertEqual(len(executions), 208)
        self.assertLess(len(executions), MAX_EXECUTION_PATHS)

        coin_rows = [
            (context, state, row)
            for context, state in executions
            for row in state.abi_control_reads
            if row.get("kind") == "COINS"
        ]
        self.assertTrue(coin_rows)
        self.assertEqual(
            {row["result_value"] for _context, _state, row in coin_rows},
            {0},
        )
        self.assertEqual(
            {row["instruction_address"] for _context, _state, row in coin_rows},
            {"0x08185134", "0x08185162"},
        )
        fifty_rows = [
            item for item in coin_rows
            if item[2]["instruction_address"] == "0x08185162"
        ]
        self.assertEqual(
            {state.vega_coins_initial for _context, state, _row in fifty_rows},
            {0, 1, 9499, 9500, 9501, 9949},
        )
        boundary_context, boundary_state, boundary_row = next(
            item for item in fifty_rows
            if item[1].vega_coins_initial == 9949
        )
        self.assertEqual(boundary_state.vega_coins_current, 9999)
        self.assertEqual(boundary_row["required_value"], 9949)
        self.assertEqual(boundary_row["result_value"], 0)
        self.assertEqual(
            _runner_required_postconditions(
                boundary_context, boundary_state,
            )["coins"],
            {"vega": 9999},
        )
        external, internal = _runtime_control_rows(
            boundary_context, boundary_state,
            owner_keys=[self.OWNER_ID], fixtures={},
        )
        self.assertTrue(all(
            row["kind"] == "VAR_RESULT_BRANCH_READ" for row in internal
        ))
        coin_controls = [row for row in external if row["kind"] == "COINS"]
        self.assertEqual(len(coin_controls), 1)
        self.assertEqual(coin_controls[0]["value"]["vega"], 9949)
        self.assertIn({
            "operator": "CURRENT_COINS_BELOW_MAX",
            "amount": 50, "result_value": 0,
        }, coin_controls[0]["relation_evidence"])

        full_states = [
            (context, state) for context, state in executions
            if state.vega_coins_initial == 9950
        ]
        self.assertTrue(full_states)
        self.assertTrue(all(
            not any(row.get("kind") == "COINS"
                    for row in state.abi_control_reads)
            and state.vega_coins_current == 9950
            and _runner_required_postconditions(context, state)["coins"] is None
            for context, state in full_states
        ))

    def test_product_prize_room_checkcoins_result_is_path_exact(
        self,
    ) -> None:
        from scripts.regenerate_stage61_unit_state import (
            ensure_stage61_state_fixture,
        )
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph

        root = 0x081859FA
        owner_id = "OBJECT:010/015:002"
        # 復元済み旧Stage61ではなく、HEAD・生成元・成果物hashを検証した
        # 同一候補のROMとsemantic reportを使う。通常releaseの認定ではない。
        fixture_root = ensure_stage61_state_fixture()
        stage61 = (
            fixture_root / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        semantic = json.loads((
            fixture_root / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(
            self.source_blobs[builder_path]
        ).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        owner = next(
            row for row in self.inventory["owners"]
            if row["owner_id"] == owner_id
        )
        self.assertEqual(owner["root"], root)
        graph = SemanticScriptGraph(stage61)
        graph.walk([root])
        self.assertEqual(graph.diagnostics, [])
        abi_entries = self._fresh_abi_entries()
        domains, domain_blockers = _static_control_domains(
            graph, root, abi_index=abi_entries,
        )
        self.assertEqual(domain_blockers, [])
        coin_domain = next(
            row for row in domains
            if row["kind"] == "COINS" and row["id"] == 0
        )
        expected_boundaries = {
            179, 180, 499, 500, 2799, 2800, 5499, 5500, 9998, 9999,
        }
        self.assertEqual(
            set(coin_domain["candidate_values"]), expected_boundaries,
        )
        self.assertTrue({0, 1, 2, 3}.isdisjoint(
            coin_domain["candidate_values"],
        ))
        text_assets, _provenance = _independent_runtime_text_assets(
            self.clean, self.stage60, stage61, semantic,
            self.repair_manifest, graph, source_blobs=self.source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            self.clean, self.stage60, stage61, semantic, owner, graph,
            text_assets, abi_entries, self.source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, root),
        )
        self.assertEqual(blockers, [])
        self.assertTrue(executions)
        prices = {
            state.vars.get(0x4002) for _context, state in executions
            if 0x08185AEE in state.execution_trace
        }
        self.assertEqual(prices, {180, 500, 2800, 5500, 9999})

        reached = [
            (context, state) for context, state in executions
            if 0x08185AEE in state.execution_trace
            and 0x08185AF1 in state.execution_trace
        ]
        self.assertEqual(
            {state.vega_coins_initial for _context, state in reached},
            expected_boundaries,
        )
        give_by_price = {
            180: 0x08185B46,
            500: 0x08185B5B,
            2800: 0x08185B70,
            5500: 0x08185B85,
            9999: 0x08185B9A,
        }
        for price, give_pc in give_by_price.items():
            with self.subTest(price=price):
                below = [
                    (context, state) for context, state in reached
                    if state.vars.get(0x4002) == price
                    and state.vega_coins_initial == price - 1
                ]
                enough = [
                    (context, state) for context, state in reached
                    if state.vars.get(0x4002) == price
                    and state.vega_coins_initial == price
                ]
                self.assertTrue(below)
                self.assertTrue(enough)
                self.assertTrue(all(
                    0x08185C17 in state.execution_trace
                    and give_pc not in state.execution_trace
                    and 0x08185C25 not in state.execution_trace
                    and 0x08185C52 not in state.execution_trace
                    and state.vega_coins_current == price - 1
                    and _runner_required_postconditions(
                        context, state,
                    )["coins"] is None
                    for context, state in below
                ))
                self.assertTrue(all(
                    0x08185AFC in state.execution_trace
                    and give_pc in state.execution_trace
                    for _context, state in enough
                ))
                paid = [
                    (context, state) for context, state in enough
                    if 0x08185C25 in state.execution_trace
                    or 0x08185C52 in state.execution_trace
                ]
                unchanged = [
                    (context, state) for context, state in enough
                    if 0x08185C25 not in state.execution_trace
                    and 0x08185C52 not in state.execution_trace
                ]
                self.assertTrue(paid)
                self.assertTrue(unchanged)
                for _context, state in paid:
                    self.assertEqual(state.vega_coins_current, 0)
                    coin_effects = [
                        effect for effect in state.effects
                        if effect.get("domain") == "coins"
                        and effect.get("owner") == "VEGA_COINS"
                    ]
                    self.assertEqual(len(coin_effects), 1)
                    self.assertEqual(
                        {
                            key: coin_effects[0][key]
                            for key in (
                                "relation", "amount", "before", "after",
                                "source_return_value", "result_value",
                                "arithmetic",
                            )
                        },
                        {
                            "relation": "SUBTRACT_EXACT",
                            "amount": price, "before": price, "after": 0,
                            "source_return_value": 1, "result_value": 0,
                            "arithmetic": "U16_SUBTRACT_EXACT",
                        },
                    )
                self.assertTrue(all(
                    0x08185BE6 in state.execution_trace
                    and state.vega_coins_current == price
                    and _runner_required_postconditions(
                        context, state,
                    )["coins"] is None
                    for context, state in unchanged
                ))

        samples = {
            state.vega_coins_initial: (context, state)
            for context, state in reached
        }
        for initial in sorted(expected_boundaries):
            with self.subTest(path_exact_initial=initial):
                context, state = samples[initial]
                external, internal = _runtime_control_rows(
                    context, state, owner_keys=[owner_id], fixtures={},
                )
                self.assertFalse(any(
                    row["kind"] == "VAR" and row["id"] == 0x800D
                    for row in external
                ))
                coin_controls = [
                    row for row in external if row["kind"] == "COINS"
                ]
                self.assertEqual(len(coin_controls), 1)
                self.assertEqual(
                    coin_controls[0]["value"]["vega"], initial,
                )
                captures = [
                    row for row in internal
                    if row["instruction_address"] == "0x08185AF1"
                ]
                self.assertEqual(len(captures), 1)
                capture = captures[0]
                self.assertEqual(capture["writer"], "GET_COINS_PATH_EXACT")
                self.assertEqual(capture["candidate_values"], [initial])
                self.assertEqual(
                    capture["capture"]["expected_value"], initial,
                )
                self.assertEqual(
                    capture["producer"]["instruction_address"],
                    "0x08185AEE",
                )
                self.assertEqual(
                    capture["producer"]["legal_domain"],
                    {"minimum": 0, "maximum": 9999},
                )
                self.assertEqual(
                    capture["producer"]["source"]["producer"][
                        "definition_line"
                    ],
                    11,
                )


class Stage61SpecialResultAbiFocusedTests(unittest.TestCase):
    """ABI writer tests that do not depend on generated matrix freshness."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = (
            ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
        ).read_bytes()
        cls.stage60 = (
            ROOT / "build/stages/60_wild_species_root_repair.gba"
        ).read_bytes()
        cls.stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        cls.catalog = json.loads((
            ROOT / "reports/generated/stage61_npc_interaction_catalog_legacy.json"
        ).read_text())

    @classmethod
    def pinned_abi_inputs(cls):
        return Stage61InteractionOracleTests.pinned_abi_inputs()

    def test_special_result_writer_graph_and_pc_menu_completed_domain(
        self,
    ) -> None:
        Stage61InteractionOracleTests \
            .test_special_result_writer_graph_and_pc_menu_completed_domain(self)

    def test_post_battle_outcome_is_correlated_to_normal_fight_win(
        self,
    ) -> None:
        manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        row = deepcopy(next(
            entry for entry in manifest["special_abis"]
            if entry["special_id"] == 180
        ))
        source_path = row["source"]["path"]
        index = _interaction_abi_index(
            self.stage61,
            {"special_abis": [row], "native_abis": []},
            source_blobs={source_path: (ROOT / source_path).read_bytes()},
        )
        # setwildbattle SPECIES_333,50,ITEM_NONE; dowildbattle;
        # specialvar VAR_RESULT,GetBattleOutcome; end
        context = replace(
            Stage61RuntimeControlFocusedTests._capacity_context(
                bytes.fromhex("b64d01320000b7260d80b40002")
            ),
            abi_index=index,
        )
        paths = _execute(context)
        self.assertEqual(len(paths), 1)
        state = paths[0]
        self.assertEqual(state.vars[0x800D], 1)
        self.assertEqual(
            state.decisions[-1]["kind"], "BATTLE_OUTCOME_EXACT",
        )
        self.assertEqual(
            state.decisions[-1]["source_relation"],
            "RUNNER_SIX_MON_LEVEL_100_NORMAL_FIGHT_WON",
        )
        self.assertEqual(
            state.abi_dispatches[-1]["result_capture"]["value"], 1,
        )
        self.assertEqual(
            _post_battle_continuation_contract(state)["resume_kind"],
            "NEXT_PC",
        )
        self.assertEqual(
            _runner_battle_start_required_postconditions(
                context, state,
            )["battle"],
            {
                "active": True, "trainer_opponent": 0,
                "enemy_species": 333, "outcome": 0,
            },
        )

    def test_special158_async_nickname_is_source_bound_no_result_writer(
        self,
    ) -> None:
        source_blobs, _reports = self.pinned_abi_inputs()
        manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        row = deepcopy(next(
            entry for entry in manifest["special_abis"]
            if entry["special_id"] == 158
        ))
        row.update(_special_semantic_contract(158, row["symbol"]))
        self.assertEqual(row["symbol"], "ChangePokemonNickname")
        self.assertEqual(row["execution"], "ASYNC_CONTEXT2")
        self.assertEqual(row["result_contract"], {
            "global_var_result_write": None,
            "specialvar_return": None,
        })
        index = _interaction_abi_index(
            self.stage61,
            {"special_abis": [row], "native_abis": []},
            source_blobs=source_blobs,
        )
        descriptor, blockers = _static_result_writer_descriptor(
            self.stage61,
            SimpleNamespace(
                opcode=0x25, raw=bytes((0x25, 158, 0)),
                address=0x08185A00,
            ),
            abi_index=index,
        )
        self.assertIsNone(descriptor)
        self.assertEqual(blockers, [])

        forged_result = deepcopy(row)
        forged_result["result_contract"]["global_var_result_write"] = {
            "candidate_values": [0, 1],
            "relation": "FORGED_NICKNAME_RESULT",
        }
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "SPECIAL158_NO_RESULT_ABI_DRIFT",
        ):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": [forged_result], "native_abis": []},
                source_blobs=source_blobs,
            )

        source_path = row["source"]["path"]
        drifted_source_blobs = dict(source_blobs)
        drifted_source_blobs[source_path] += b"\n"
        source_repin = deepcopy(row)
        source_repin["source"]["sha256"] = hashlib.sha256(
            drifted_source_blobs[source_path]
        ).hexdigest()
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "SPECIAL158_NO_RESULT_ABI_DRIFT",
        ):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": [source_repin], "native_abis": []},
                source_blobs=drifted_source_blobs,
            )

        drifted_rom = bytearray(self.stage61)
        drifted_rom[0x080CD200 - 0x08000000] ^= 1
        rom_repin = deepcopy(row)
        rom_repin["rom_binding"]["sha256"] = hashlib.sha256(
            drifted_rom[
                0x080CD200 - 0x08000000:
                0x080CD200 - 0x08000000 + 0xBC
            ]
        ).hexdigest()
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "SPECIAL158_NO_RESULT_ABI_DRIFT",
        ):
            _interaction_abi_index(
                bytes(drifted_rom),
                {"special_abis": [rom_repin], "native_abis": []},
                source_blobs=source_blobs,
            )

    def test_research_writer_graph_rejects_wrong_or_isolated_sink_and_enum_drift(
        self,
    ) -> None:
        source_blobs, _reports = self.pinned_abi_inputs()
        research_symbol = "ResearchEconomy_PurchaseSelected"
        evidence = _native_global_result_writer_evidence(
            research_symbol, self.stage61, source_blobs,
            stage60_rom=self.stage60,
        )
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence["schema_version"], 2)
        self.assertEqual(
            evidence["result_enum_header"]["path"],
            "overlays/research_economy_v1/research_economy_v1.h",
        )
        sink_edges = [
            edge for edge in evidence["ownership_edges"]
            if edge["callee"] == "set_result"
        ]
        self.assertEqual(len(sink_edges), 11)
        self.assertEqual(
            {edge["caller"] for edge in sink_edges},
            {
                "ResearchEconomy_PurchaseSelected",
                "ResearchEconomy_PurchaseByIndex",
            },
        )
        legacy_sources = dict(source_blobs)
        legacy_sources.pop(
            "overlays/research_economy_v1/research_economy_v1.h"
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "result enum header source不一致",
        ):
            _native_global_result_writer_evidence(
                research_symbol, self.stage61, legacy_sources,
                stage60_rom=self.stage60,
            )

        # The graph remains node-reachable, and line 1221 is a real pinned
        # call, but it calls the stock classifier rather than the writer sink.
        # A reachability-only check would therefore accept this forged sink.
        wrong_sink = deepcopy(
            _NATIVE_GLOBAL_RESULT_WRITER_SPECS[research_symbol]
        )
        forged_edge = next(
            edge for edge in wrong_sink["ownership_edges"]
            if edge["callee"] == "set_result" and edge["line"] == 1225
        )
        forged_edge["line"] = 1221
        forged_edge["source_line"] = \
            "stock_result = shop_stock_result(row);"
        with patch.dict(
            _NATIVE_GLOBAL_RESULT_WRITER_SPECS,
            {research_symbol: wrong_sink},
        ):
            with self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "reachable sink closure不一致",
            ):
                _native_global_result_writer_evidence(
                    research_symbol, self.stage61, source_blobs,
                    stage60_rom=self.stage60,
                )

        isolated_sink = deepcopy(
            _NATIVE_GLOBAL_RESULT_WRITER_SPECS[research_symbol]
        )
        isolated_sink["ownership_edges"] = [
            edge for edge in isolated_sink["ownership_edges"]
            if edge["callee"] != "set_result"
        ]
        with patch.dict(
            _NATIVE_GLOBAL_RESULT_WRITER_SPECS,
            {research_symbol: isolated_sink},
        ):
            with self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "reachable function closure不一致.*set_result",
            ):
                _native_global_result_writer_evidence(
                    research_symbol, self.stage61, source_blobs,
                    stage60_rom=self.stage60,
                )

        header_path = \
            "overlays/research_economy_v1/research_economy_v1.h"
        drifted_header = source_blobs[header_path].replace(
            b"RESEARCH_RESULT_DAILY_CAP = 4,",
            b"RESEARCH_RESULT_DAILY_CAP = 12,",
        )
        self.assertNotEqual(drifted_header, source_blobs[header_path])
        enum_drift = deepcopy(
            _NATIVE_GLOBAL_RESULT_WRITER_SPECS[research_symbol]
        )
        # Re-pin the forged bytes to prove the member parser, rather than only
        # the outer SHA gate, rejects a numeric enum drift.
        enum_drift["result_enum_header"]["source_sha256"] = \
            hashlib.sha256(drifted_header).hexdigest()
        drifted_sources = dict(source_blobs)
        drifted_sources[header_path] = drifted_header
        with patch.dict(
            _NATIVE_GLOBAL_RESULT_WRITER_SPECS,
            {research_symbol: enum_drift},
        ):
            with self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "result enum member mismatch",
            ):
                _native_global_result_writer_evidence(
                    research_symbol, self.stage61, drifted_sources,
                    stage60_rom=self.stage60,
                )


class Stage61BerryPowderABIFocusedTests(unittest.TestCase):
    """The five source SPECIALs share one decrypted SaveBlock2 owner."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        cls.manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        cls.source_blobs, _reports = _interaction_abi_pinned_inputs()

    @classmethod
    def _rows(cls) -> list[dict]:
        rows = []
        for raw in cls.manifest["special_abis"]:
            if raw["special_id"] not in {412, 413, 414, 415, 416}:
                continue
            entry = deepcopy(raw)
            entry.update(_special_semantic_contract(
                entry["special_id"], entry["symbol"],
            ))
            rows.append(entry)
        if {row["special_id"] for row in rows} != {412, 413, 414, 415, 416}:
            raise AssertionError("Berry Powder SPECIAL fixture incomplete")
        return rows

    @classmethod
    def _abi_index(cls) -> dict[str, dict]:
        return _interaction_abi_index(
            cls.stage61,
            {"special_abis": cls._rows(), "native_abis": []},
            source_blobs=cls.source_blobs,
        )

    @classmethod
    def _context(cls) -> _Context:
        root = 0x08181542
        return _Context(
            clean_rom=cls.stage61, stage61_rom=cls.stage61,
            semantic_report={},
            npc={
                "npc_id": "OBJECT:007/009:000", "local_id": 1,
                "flag": 0, "group": 7, "map": 9,
            },
            case={
                "case_id": "focused-berry-powder",
                "owner_key": "OBJECT:007/009:000",
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "control_requirements": {"external": [], "internal": []},
                "expected_object_visible": True,
            },
            root=root, target_root=root, execution_root=root,
            root_plan={"references": []}, fixture=DEFAULT_FIXTURE,
            flag_mapping={}, var_mapping={}, text_assets={},
            text_provenance="PINNED_STAGE60_PROJECT_RAW",
            abi_index=cls._abi_index(), instruction_repairs={},
            source_suppression_contract=None,
            stage61_script_bytes=frozenset(),
        )

    def test_412_is_sync_void_and_source_layout_drift_fails_closed(
        self,
    ) -> None:
        by_id = {
            row["special_id"]: _special_semantic_contract(
                row["special_id"], row["symbol"],
            )
            for row in self._rows()
        }
        self.assertEqual(by_id[412]["execution"], "SYNC")
        self.assertEqual(by_id[412]["result_contract"], {
            "global_var_result_write": None, "specialvar_return": None,
        })
        self.assertEqual(by_id[412]["input_controls"], [{
            "kind": "BERRY_POWDER", "owner": "BERRY_POWDER:0",
            "candidate_values": [
                49, 50, 79, 80, 299, 300, 999, 1000, 2999, 3000,
            ],
            "relation": "EXACT_DECRYPTED_BERRY_POWDER",
        }])
        self.assertEqual(
            {row["domain"] for row in by_id[415]["effects"]},
            {"berry_powder"},
        )
        self.assertEqual(by_id[414]["effects"], [])

        forged_result = self._rows()
        forged_result[0]["result_contract"]["global_var_result_write"] = {
            "candidate_values": [0, 1, 127],
            "relation": "FORGED_DISPLAY_RESULT",
        }
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "canonical result contract|BERRY_POWDER_SPECIAL_ABI_DRIFT",
        ):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": forged_result, "native_abis": []},
                source_blobs=self.source_blobs,
            )

        line_drift = self._rows()
        line_drift[0]["source"]["definition_line"] += 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "BERRY_POWDER_SPECIAL_ABI_DRIFT",
        ):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": line_drift, "native_abis": []},
                source_blobs=self.source_blobs,
            )

        execution_drift = self._rows()
        execution_drift[0]["execution"] = "ASYNC_CONTEXT2"
        with self.assertRaises(Stage61InteractionOracleError):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": execution_drift, "native_abis": []},
                source_blobs=self.source_blobs,
            )

        span_drift = self._rows()
        span_drift[0]["rom_binding"]["byte_length"] += 2
        with self.assertRaises(Stage61InteractionOracleError):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": span_drift, "native_abis": []},
                source_blobs=self.source_blobs,
            )

        special_id_drift = self._rows()
        special_id_drift[0]["special_id"] = 411
        with self.assertRaises(Stage61InteractionOracleError):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": special_id_drift, "native_abis": []},
                source_blobs=self.source_blobs,
            )

        source_hash_drift = dict(self.source_blobs)
        berry_path = "vendor/upstream/pokefirered/src/berry_powder.c"
        source_hash_drift[berry_path] = \
            source_hash_drift[berry_path] + b"\n"
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "source bytes SHA|BERRY_POWDER physical model source",
        ):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": self._rows(), "native_abis": []},
                source_blobs=source_hash_drift,
            )

        missing_layout = dict(self.source_blobs)
        missing_layout.pop("vendor/upstream/pokefirered/include/global.h")
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "BERRY_POWDER physical model source不一致",
        ):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": self._rows(), "native_abis": []},
                source_blobs=missing_layout,
            )

    def test_412_414_415_share_one_amount_and_take_is_exact(self) -> None:
        context = self._context()

        def invoke(
            state: _Execution, pc: int, opcode: int, raw: bytes,
        ) -> list[_Execution]:
            state.pc = pc
            state.execution_trace.append(pc)
            state.current_instruction_address = pc
            state.current_opcode = opcode
            return _fork_abi_command(context, state, pc, opcode, raw)

        display = invoke(
            _Execution(pc=0x08100000, vars={0x8004: 50}),
            0x08100000, 0x25, bytes((0x25, 412 & 0xFF, 412 >> 8)),
        )
        self.assertEqual(len(display), 10)
        self.assertEqual(
            {state.berry_powder_current for state in display},
            {49, 50, 79, 80, 299, 300, 999, 1000, 2999, 3000},
        )
        outcomes: dict[int, _Execution] = {}
        for amount in (49, 50):
            branch = next(
                state for state in display
                if state.berry_powder_current == amount
            )
            enough = invoke(
                branch, 0x08100010, 0x26,
                bytes((0x26, 0x0D, 0x80, 414 & 0xFF, 414 >> 8)),
            )[0]
            self.assertEqual(enough.vars[0x800D], int(amount >= 50))
            taken = invoke(
                enough, 0x08100020, 0x25,
                bytes((0x25, 415 & 0xFF, 415 >> 8)),
            )[0]
            outcomes[amount] = taken
            self.assertEqual(len([
                row for row in taken.abi_control_reads
                if row["kind"] == "BERRY_POWDER"
            ]), 1)
            effect = next(
                row for row in taken.effects
                if row["domain"] == "berry_powder"
            )
            self.assertEqual(effect["before"], amount)
            self.assertEqual(effect["after"], 0 if amount == 50 else amount)
            self.assertEqual(effect["success"], amount == 50)
            projected = _materialize_control_requirement(
                self.stage61,
                next(row for row in taken.abi_control_reads
                     if row["kind"] == "BERRY_POWDER"),
                owner_keys=["OBJECT:007/009:000"], fixtures={},
            )
            self.assertEqual(projected["kind"], "BERRY_POWDER")
            self.assertEqual(projected["id"], 0)
            self.assertEqual(projected["value"], amount)
            self.assertEqual(projected["relation_evidence"], [{
                "operator": "EXACT_DECRYPTED_BERRY_POWDER",
            }])

        self.assertIsNone(
            _runner_required_postconditions(
                context, outcomes[49],
            )["berry_powder"]
        )
        self.assertEqual(
            _runner_required_postconditions(
                context, outcomes[50],
            )["berry_powder"],
            0,
        )
        self.assertEqual(
            _effect_contract(context, outcomes[50])["domains"][
                "berry_powder"
            ],
            {"relation": "EXACT_BEFORE_AFTER", "before": 50, "after": 0},
        )


class Stage61PartyMinigameRFUFocusedTests(unittest.TestCase):
    """Lostelle's Daddy uses one party image and finite RFU outcomes."""

    ROOT_PC = 0x08190B8D
    OWNER_ID = "OBJECT:033/000:000"

    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = (
            ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
        ).read_bytes()
        cls.stage60 = (
            ROOT / "build/stages/60_wild_species_root_repair.gba"
        ).read_bytes()
        cls.stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        cls.semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        cls.repair_manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text())
        cls.inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        catalog = json.loads((
            ROOT / "reports/generated/stage61_npc_interaction_catalog_legacy.json"
        ).read_text())
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        cls.source_blobs, reports = _interaction_abi_pinned_inputs()
        cls.manifest = build_pinned_interaction_abi_manifest(
            cls.clean, cls.stage60, cls.stage61, catalog,
            source_blobs=cls.source_blobs,
            runtime_symbol_reports=reports,
        )
        cls.by_special_id = {
            row["special_id"]: row for row in cls.manifest["special_abis"]
        }
        required = {363, 364, 398, 402, 438}
        if not required <= set(cls.by_special_id):
            raise AssertionError("wireless minigame ABI fixture incomplete")
        cls.abi_index = _interaction_abi_index(
            cls.stage61, cls.manifest, source_blobs=cls.source_blobs,
        )

    @classmethod
    def _index_rows(cls, *special_ids: int) -> dict[str, dict]:
        return _interaction_abi_index(
            cls.stage61,
            {
                "special_abis": [
                    deepcopy(cls.by_special_id[special_id])
                    for special_id in special_ids
                ],
                "native_abis": [],
            },
            source_blobs=cls.source_blobs,
        )

    def test_special_398_402_438_source_abi_and_drift_fail_closed(
        self,
    ) -> None:
        from tools.stage61_interaction_oracle import (
            PARTY_MINIGAME_RELATION,
            _party_minigame_input_control,
        )

        choose = self.by_special_id[398]
        jump = self.by_special_id[402]
        dodrio = self.by_special_id[438]
        self.assertEqual(choose["symbol"], "ChooseMonForWirelessMinigame")
        self.assertEqual(choose["source"], {
            "path": "vendor/upstream/pokefirered/src/party_menu.c",
            "definition_line": 5818,
            "sha256": (
                "8290dfd5b6444e743029ab76543ed5e4b5b32c1c2f475c686946545f934d5f9b"
            ),
        })
        self.assertEqual(choose["rom_binding"], {
            "address": "0x081281C0", "byte_length": 0x2C,
            "sha256": (
                "15bd59feb9890511552c8f95b677c5cb65b78a731d117d9eb23187141d0b8f6c"
            ),
        })
        self.assertEqual(choose["result_contract"], {
            "global_var_result_write": None, "specialvar_return": None,
        })
        self.assertEqual(
            choose["input_controls"],
            [_party_minigame_input_control(mode) for mode in (0, 1)],
        )
        self.assertEqual(
            {row["domain"] for row in choose["effects"]}, {"ui"},
        )
        for row, mode, expected_source, expected_address in (
            (
                jump, 0,
                "vendor/upstream/pokefirered/src/pokemon_jump.c",
                "0x0814A008",
            ),
            (
                dodrio, 1,
                "vendor/upstream/pokefirered/src/dodrio_berry_picking.c",
                "0x0815693C",
            ),
        ):
            with self.subTest(special_id=row["special_id"]):
                result = row["result_contract"]["global_var_result_write"]
                self.assertEqual(result["candidate_values"], [0, 1])
                self.assertEqual(
                    result["writer_evidence"][
                        "completed_candidate_values"
                    ],
                    [0, 1],
                )
                self.assertEqual(
                    result["writer_evidence"][
                        "nonterminal_candidate_values"
                    ],
                    [],
                )
                self.assertEqual(row["input_controls"], [
                    _party_minigame_input_control(mode)
                ])
                self.assertEqual(row["source"]["path"], expected_source)
                self.assertEqual(row["rom_binding"]["address"],
                                 expected_address)
                self.assertEqual(row["effects"], [])
        self.assertTrue(all(
            control["relation"] == PARTY_MINIGAME_RELATION
            for row in (choose, jump, dodrio)
            for control in row["input_controls"]
        ))

        forged_result = deepcopy(choose)
        forged_result["result_contract"]["global_var_result_write"] = {
            "candidate_values": [0, 1], "relation": "FORGED_RESULT",
        }
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "SPECIAL398 canonical result contract不一致",
        ):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": [forged_result], "native_abis": []},
                source_blobs=self.source_blobs,
            )

        writer_drift = deepcopy(jump)
        writer_drift["result_contract"]["global_var_result_write"][
            "writer_evidence"
        ]["source_functions"][0]["write_sites"][0]["candidate_values"] = [0]
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "SPECIAL402 result writer evidence不一致",
        ):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": [writer_drift], "native_abis": []},
                source_blobs=self.source_blobs,
            )

        source_line_drift = deepcopy(choose)
        source_line_drift["source"]["definition_line"] += 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "PARTY_MINIGAME_SPECIAL_ABI_DRIFT:398",
        ):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": [source_line_drift], "native_abis": []},
                source_blobs=self.source_blobs,
            )

        source_path = "vendor/upstream/pokefirered/src/party_menu.c"
        source_bytes_drift = dict(self.source_blobs)
        source_bytes_drift[source_path] += b"\n"
        source_repin = deepcopy(choose)
        source_repin["source"]["sha256"] = hashlib.sha256(
            source_bytes_drift[source_path]
        ).hexdigest()
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "PARTY_MINIGAME_SPECIAL_ABI_DRIFT:398|PARTY_MINIGAME_SOURCE_DRIFT",
        ):
            _interaction_abi_index(
                self.stage61,
                {"special_abis": [source_repin], "native_abis": []},
                source_blobs=source_bytes_drift,
            )

        rom_drift = bytearray(self.stage61)
        rom_drift[0x081211E4 - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "PARTY_MINIGAME_SELECTOR_ROM_DRIFT:TryEnterMonForMinigame",
        ):
            _interaction_abi_index(
                bytes(rom_drift),
                {"special_abis": [deepcopy(choose)], "native_abis": []},
                source_blobs=self.source_blobs,
            )

    def test_party_control_materialization_is_correlated_and_strict(
        self,
    ) -> None:
        from tools.stage61_interaction_oracle import (
            PARTY_MINIGAME_RELATION,
            _party_minigame_input_control,
        )

        fixtures: dict[str, dict] = {}
        refs: dict[tuple[int, bool], str] = {}
        for mode, eligible, selected in (
            (0, False, None), (0, True, 0),
            (1, False, None), (1, True, 7),
        ):
            row = _party_minigame_input_control(mode)
            row["required_value"] = {
                "mode": mode, "eligible": eligible,
                "selected_slot": selected,
            }
            materialized = _materialize_control_requirement(
                self.stage61, row, owner_keys=[self.OWNER_ID],
                fixtures=fixtures,
            )
            self.assertIsNotNone(materialized)
            self.assertEqual(materialized["kind"], "PARTY_MINIGAME")
            self.assertEqual(materialized["id"], mode)
            self.assertEqual(materialized["value"]["mode"], mode)
            self.assertEqual(materialized["value"]["eligible"], eligible)
            self.assertEqual(
                materialized["value"]["selected_slot"], selected,
            )
            self.assertEqual(materialized["value"]["party_count"], 6)
            self.assertEqual(materialized["relation_evidence"], [{
                "operator": PARTY_MINIGAME_RELATION,
            }])
            self.assertEqual(len(materialized["fixture_keys"]), 1)
            ref = materialized["fixture_keys"][0]
            self.assertEqual(materialized["value"]["party_layout_ref"], ref)
            self.assertEqual(fixtures[ref]["fixture_kind"], "PARTY")
            self.assertEqual(fixtures[ref]["count"], 6)
            self.assertEqual(len(bytes.fromhex(fixtures[ref]["raw_hex"])),
                             600)
            refs[(mode, eligible)] = ref
        # Species 1 is Jump-eligible/Dodrio-ineligible; species 85 is the
        # exact inverse.  Equal refs prove both predicates consume one raw
        # party layout instead of independently fabricated booleans.
        self.assertEqual(refs[(0, True)], refs[(1, False)])
        self.assertEqual(refs[(0, False)], refs[(1, True)])
        self.assertNotEqual(refs[(0, True)], refs[(0, False)])

        invalid = (
            {"mode": 0, "eligible": True, "selected_slot": 6},
            {"mode": 0, "eligible": True, "selected_slot": 127},
            {"mode": 0, "eligible": False, "selected_slot": 0},
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaisesRegex(
                Stage61InteractionOracleError, "PARTY_MINIGAME",
            ):
                row = _party_minigame_input_control(0)
                row["required_value"] = value
                _materialize_control_requirement(
                    self.stage61, row, owner_keys=[self.OWNER_ID],
                    fixtures={},
                )

    def test_rfu_initializer_zero_and_double_retry_are_rejected_product_wide(
        self,
    ) -> None:
        from tools.stage61_cyclic_decision_contracts import (
            build_stage61_cyclic_decision_contracts,
            load_stage61_cyclic_decision_source_blobs,
        )
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph
        from tools.stage61_interaction_oracle import (
            _bind_cyclic_decision_root_contract,
            _flat_result_internal_controls,
            _validate_cyclic_decision_contract_input,
        )

        for special_id, completed in (
            (363, [1, 5, 8]), (364, [1, 5, 6, 8]),
        ):
            with self.subTest(special_id=special_id):
                relation = self.by_special_id[special_id][
                    "result_contract"
                ]["global_var_result_write"]
                self.assertEqual(relation["candidate_values"], completed)
                evidence = relation["writer_evidence"]
                self.assertEqual(
                    evidence["completed_candidate_values"], completed,
                )
                self.assertEqual(evidence["nonterminal_candidate_values"],
                                 [0])
                initializer_sites = [
                    site
                    for function in evidence["source_functions"]
                    for site in function["write_sites"]
                    if site["phase"] == "NONTERMINAL_SENTINEL"
                ]
                self.assertEqual(
                    [site["candidate_values"] for site in initializer_sites],
                    [[0]],
                )
                self.assertEqual(
                    {effect["domain"] for effect in
                     self.by_special_id[special_id]["effects"]},
                    {"ui", "volatile"},
                )
                forged = deepcopy(self.by_special_id[special_id])
                forged["result_contract"]["global_var_result_write"][
                    "candidate_values"
                ] = [0, *completed]
                with self.assertRaisesRegex(
                    Stage61InteractionOracleError,
                    f"SPECIAL{special_id} result writer candidate不一致",
                ):
                    _interaction_abi_index(
                        self.stage61,
                        {"special_abis": [forged], "native_abis": []},
                        source_blobs=self.source_blobs,
                    )

        owner = next(
            row for row in self.inventory["owners"]
            if row["owner_id"] == self.OWNER_ID
        )
        self.assertEqual(owner["root"], self.ROOT_PC)
        cyclic_document = build_stage61_cyclic_decision_contracts(
            self.stage61, self.inventory,
            load_stage61_cyclic_decision_source_blobs(ROOT),
        )
        cyclic_index = _validate_cyclic_decision_contract_input(
            cyclic_document, self.stage61,
            expected_event_owner_inventory_sha256=
                self.inventory["inventory_sha256"],
        )
        binding = _bind_cyclic_decision_root_contract(
            cyclic_index, self.semantic, owner_ids=[self.OWNER_ID],
            target_root=self.ROOT_PC, execution_root=self.ROOT_PC,
            require_exact_owner_set=True,
        )
        self.assertEqual(binding["classification"], "EXPLICIT_TRANSACTION")
        self.assertEqual(binding["loop_family"], "RFU_LEADER_JOIN")

        graph = SemanticScriptGraph(self.stage61)
        graph.walk([self.ROOT_PC])
        self.assertEqual(graph.diagnostics, [])
        domains, domain_blockers = _static_control_domains(
            graph, self.ROOT_PC, abi_index=self.abi_index,
        )
        self.assertEqual(domain_blockers, [])
        party_domains = sorted(
            (row for row in domains if row["kind"] == "PARTY_MINIGAME"),
            key=lambda row: row["id"],
        )
        self.assertEqual([row["id"] for row in party_domains], [0, 1])
        self.assertEqual(
            [
                {relation["abi_owner"] for relation in row["relations"]}
                for row in party_domains
            ],
            [
                {"WIRELESS_MINIGAME_MODE:0x00000000"},
                {"WIRELESS_MINIGAME_MODE:0x00000001"},
            ],
        )

        semantic = deepcopy(self.semantic)
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(
            self.source_blobs[builder_path]
        ).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        text_assets, _provenance = _independent_runtime_text_assets(
            self.clean, self.stage60, self.stage61, semantic,
            self.repair_manifest, graph, source_blobs=self.source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            self.clean, self.stage60, self.stage61, semantic, owner, graph,
            text_assets, self.abi_index, self.source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, self.ROOT_PC),
            cyclic_decision_contract=binding,
        )
        self.assertEqual(blockers, [])
        self.assertEqual(len(executions), 505)
        self.assertLess(len(executions), MAX_EXECUTION_PATHS)
        self.assertTrue(all(
            state.terminated and state.terminal_kind == "FIELD_RELEASE"
            for _context, state in executions
        ))

        party_decisions = [
            decision for _context, state in executions
            for decision in state.decisions
            if decision.get("kind", "").startswith("PARTY_MINIGAME_")
        ]
        for mode in (0, 1):
            self.assertEqual({
                decision["result_value"] for decision in party_decisions
                if decision["kind"] == "PARTY_MINIGAME_ELIGIBILITY_EXACT"
                and decision["mode"] == mode
            }, {0, 1})
            selections = [
                decision for decision in party_decisions
                if decision["kind"] == "PARTY_MINIGAME_SELECTION_EXACT"
                and decision["mode"] == mode
            ]
            self.assertEqual(
                {decision["selected_slot"] for decision in selections},
                {*range(6), 7},
            )
            self.assertTrue(all(decision["eligible"] is True
                                for decision in selections))

        expected_sequences = {
            "0x081A3461": {(1,), (5,), (8, 1), (8, 5)},
            "0x081A3469": {
                (1,), (5,), (6,), (8, 1), (8, 5), (8, 6),
            },
        }
        observed_sequences: dict[str, set[tuple[int, ...]]] = {
            pc: set() for pc in expected_sequences
        }
        ordered_path = None
        for context, state in executions:
            for pc in expected_sequences:
                values = tuple(
                    decision["result_value"]
                    for decision in state.decisions
                    if decision.get("kind") == "RFU_ROLE_RESULT_EXACT"
                    and decision.get("instruction_address") == pc
                )
                if values:
                    observed_sequences[pc].add(values)
                self.assertNotIn(0, values)
                self.assertLessEqual(values.count(8), 1)
                if 8 in values:
                    self.assertEqual(values[0], 8)
                if ordered_path is None and len(values) == 2:
                    ordered_path = (context, state, pc, values)
        self.assertEqual(observed_sequences, expected_sequences)
        self.assertIsNotNone(ordered_path)

        context, ordered_state, writer_pc, values = ordered_path
        internal = _flat_result_internal_controls(
            context, ordered_state, sequence_id="rfu-one-retry",
        )
        writer = (
            "SPECIAL:TryBecomeLinkLeader"
            if writer_pc == "0x081A3461"
            else "SPECIAL:TryJoinLinkGroup"
        )
        captures = [row for row in internal if row["writer"] == writer]
        self.assertEqual(
            [row["capture"]["expected_value"] for row in captures],
            list(values),
        )
        self.assertTrue(all(
            row["producer"]["ordered_runtime_capture"]["relation"] ==
                "ONE_RETRY_8_THEN_NON_8_SAME_RFU_ROLE_EXACT"
            for row in captures
        ))

        double_retry = ordered_state.clone()
        writes = sorted(
            (
                write for write in double_retry.var_writes
                if write["instruction_address"] == int(writer_pc, 16)
            ),
            key=lambda write: write["execution_trace_index"],
        )
        self.assertEqual([write["value"] for write in writes[-2:]],
                         list(values))
        writes[-1]["value"] = 8
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "RFU_ORDERED_RUNTIME_CAPTURE_CONTRACT_REQUIRED",
        ):
            _flat_result_internal_controls(
                context, double_retry, sequence_id="rfu-double-retry",
            )

    def test_center_link_registry_and_root_scoped_domain_are_exact(
        self,
    ) -> None:
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph

        self.assertEqual(len(CENTER_LINK_SESSION_SCENARIOS), 50)
        self.assertEqual(
            Counter(
                row["link_group"]
                for row in CENTER_LINK_SESSION_SCENARIOS.values()
            ),
            Counter({0: 10, 1: 10, 2: 10, 3: 10, 5: 10}),
        )
        multi = CENTER_LINK_SESSION_SCENARIOS["group2-leader-result1"]
        self.assertEqual(
            {
                key: multi[key] for key in (
                    "capacity_min", "capacity_max", "endpoint_count",
                    "topology_policy",
                )
            },
            {
                "capacity_min": 4, "capacity_max": 4,
                "endpoint_count": 4,
                "topology_policy": "EXACT_SOURCE_CAPACITY",
            },
        )
        berry = CENTER_LINK_SESSION_SCENARIOS[
            "group5-join-retry-result6"
        ]
        self.assertEqual(
            (berry["capacity_min"], berry["capacity_max"],
             berry["endpoint_count"], berry["topology_policy"]),
            (2, 5, 2, "MINIMUM_SOURCE_VALID_REPRESENTATIVE"),
        )
        cancel = CENTER_LINK_SESSION_SCENARIOS[
            "group5-join-result5"
        ]
        self.assertEqual(
            (cancel["endpoint_count"], cancel["topology_policy"]),
            (1, "LOCAL_CANCEL_BEFORE_DISCOVERY"),
        )
        self.assertEqual(CENTER_LINK_GROUP_CAPACITIES[5], (2, 5))

        center_graph = SemanticScriptGraph(self.stage61)
        center_graph.walk([0x081962AC])
        center_domains, center_blockers = _static_control_domains(
            center_graph, 0x081962AC, abi_index=self.abi_index,
        )
        self.assertEqual(center_blockers, [])
        center_kinds = {row["kind"] for row in center_domains}
        self.assertIn(CENTER_LINK_SESSION_KIND, center_kinds)
        self.assertNotIn("RFU_SESSION", center_kinds)

        minigame_graph = SemanticScriptGraph(self.stage61)
        minigame_graph.walk([self.ROOT_PC])
        minigame_domains, minigame_blockers = _static_control_domains(
            minigame_graph, self.ROOT_PC, abi_index=self.abi_index,
        )
        self.assertEqual(minigame_blockers, [])
        minigame_kinds = {row["kind"] for row in minigame_domains}
        self.assertIn("RFU_SESSION", minigame_kinds)
        self.assertNotIn(CENTER_LINK_SESSION_KIND, minigame_kinds)

        for scenario_id, payload in CENTER_LINK_SESSION_SCENARIOS.items():
            control = _center_link_session_input_control(payload["special"])
            control.update({
                "id": payload["special"],
                "required_value": deepcopy(payload),
            })
            materialized = _materialize_control_requirement(
                self.stage61, control,
                owner_keys=["OBJECT:005/005:002"], fixtures={},
            )
            self.assertEqual(
                materialized["value"]["scenario_id"], scenario_id,
            )
            self.assertEqual(
                materialized["relation_evidence"],
                [{"operator": CENTER_LINK_SESSION_RELATION}],
            )

    def test_center_link_uses_var8004_and_rejects_mode_injection(
        self,
    ) -> None:
        scenario = deepcopy(
            CENTER_LINK_SESSION_SCENARIOS["group2-join-result1"]
        )
        entry = deepcopy(self.by_special_id[364])
        context = _Context(
            clean_rom=self.stage61, stage61_rom=self.stage61,
            semantic_report={},
            npc={"npc_id": "OBJECT:005/005:002", "local_id": 2},
            case={
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "control_requirements": {"external": [{
                    "kind": CENTER_LINK_SESSION_KIND,
                    "id": 0,
                    "value": scenario,
                }]},
            },
            root=0x081962AC, target_root=0x081962AC,
            execution_root=0x081962AC, root_plan={},
            fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
            text_assets={}, text_provenance="PINNED_STAGE60_PROJECT_RAW",
            abi_index=self.abi_index, instruction_repairs={},
            source_suppression_contract=None,
            stage61_script_bytes=frozenset(),
        )
        group_writer = 0x081A3202
        special_pc = 0x081A3469
        raw = self.stage61[
            special_pc - 0x08000000:special_pc - 0x08000000 + 3
        ]
        state = _Execution(
            pc=group_writer, execution_trace=[group_writer],
            current_instruction_address=group_writer, current_opcode=0x16,
        )
        _set_var(context, state, 0x8004, 2, group_writer)
        state.pc = special_pc
        state.execution_trace.append(special_pc)
        state.current_instruction_address = special_pc
        state.current_opcode = 0x25
        branches = _fork_pinned_rfu_role_result(
            context, state, special_pc, raw, entry["abi_key"], entry, 364,
        )
        self.assertEqual(len(branches), 1)
        decision = branches[0].decisions[-1]
        self.assertEqual(
            (decision["profile"], decision["link_group"],
             decision["activity_mode"], decision["result_value"]),
            ("POKEMON_CENTER_LINK", 2, None, 1),
        )

        injected = state.clone()
        injected.pc = 0x081A3207
        injected.execution_trace.append(injected.pc)
        injected.current_instruction_address = injected.pc
        injected.current_opcode = 0x16
        _set_var(context, injected, 0x8005, 0, injected.pc)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "CENTER_LINK_SESSION_MODE_WRITER_FORBIDDEN",
        ):
            _fork_pinned_rfu_role_result(
                context, injected, special_pc, raw,
                entry["abi_key"], entry, 364,
            )

        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "LINK_SESSION_CALLING_ROOT_UNREGISTERED",
        ):
            _fork_pinned_rfu_role_result(
                replace(context, root=0x08123456), state.clone(),
                special_pc, raw, entry["abi_key"], entry, 364,
            )


class Stage61DaycareTransactionFocusedTests(unittest.TestCase):
    ROOT_PC = 0x08191780
    OWNER_ID = "OBJECT:035/000:000"

    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = (
            ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
        ).read_bytes()
        cls.stage60 = (
            ROOT / "build/stages/60_wild_species_root_repair.gba"
        ).read_bytes()
        cls.stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        cls.semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        cls.repair_manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text())
        cls.inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        cls.manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        cls.source_blobs, _reports = _interaction_abi_pinned_inputs()

    @classmethod
    def _fresh_abi_entries(cls) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for raw in [
            *cls.manifest["special_abis"], *cls.manifest["native_abis"],
        ]:
            entry = deepcopy(raw)
            pointer = int(entry["target_pointer"], 16)
            entry["target_pointer"] = pointer \
                if entry["abi_key"].startswith("SPECIAL:") else pointer & ~1
            entry["source_status"] = "PINNED_SOURCE_VERIFIED"
            if entry.get("special_id") in (
                DAYCARE_SPECIAL_IDS | ROUTE5_DAYCARE_SPECIAL_IDS
            ) | {
                158, 212, 213, 432,
            }:
                entry.update(_special_semantic_contract(
                    entry["special_id"], entry["symbol"],
                ))
            result[entry["abi_key"]] = entry
        return result

    @classmethod
    def _context(cls, abi_index: dict[str, dict]) -> _Context:
        return _Context(
            clean_rom=cls.stage61, stage61_rom=cls.stage61,
            semantic_report={}, npc={"local_id": 1},
            case={"state": {
                "flags": [], "vars": [], "items": [], "trainers": [],
            }},
            root=cls.ROOT_PC, target_root=cls.ROOT_PC,
            execution_root=cls.ROOT_PC, root_plan={},
            fixture=DEFAULT_FIXTURE, flag_mapping={}, var_mapping={},
            text_assets={}, text_provenance="PINNED_STAGE60_PROJECT_RAW",
            abi_index=abi_index, instruction_repairs={},
            source_suppression_contract=None,
            stage61_script_bytes=frozenset(),
        )

    @staticmethod
    def _special_key(entries: dict[str, dict], special_id: int) -> str:
        matches = [
            key for key, entry in entries.items()
            if entry.get("special_id") == special_id
        ]
        if len(matches) != 1:
            raise AssertionError((special_id, matches))
        return matches[0]

    def _manual_special(
        self, special_id: int, pc: int, scenario_id: str,
        *, result_before: int = 0xBEEF,
        mutate_entry=None,
    ) -> list[_Execution]:
        entries = self._fresh_abi_entries()
        key = self._special_key(entries, special_id)
        if mutate_entry is not None:
            mutate_entry(entries[key])
        context = self._context(entries)
        raw = self.stage61[pc - 0x08000000:pc - 0x08000000 + 5]
        opcode = raw[0]
        size = 3 if opcode == 0x25 else 5
        raw = raw[:size]
        state = _Execution(
            pc=pc, vars={0x800D: result_before}, execution_trace=[pc],
            current_instruction_address=pc, current_opcode=opcode,
        )
        _daycare_install_scenario(state, scenario_id)
        return _fork_abi_command(context, state, pc, opcode, raw)

    def test_raw_scenarios_and_runner_materialization_are_exact(self) -> None:
        self.assertEqual(len(DAYCARE_SCENARIO_IDS), 6)
        for scenario_id in DAYCARE_SCENARIO_IDS:
            payload = _daycare_scenario_payload(scenario_id)
            self.assertEqual(payload["fixture_kind"],
                             DAYCARE_TRANSACTION_KIND)
            self.assertEqual(len(bytes.fromhex(payload["party_raw_hex"])), 600)
            self.assertEqual(len(bytes.fromhex(payload["daycare_raw_hex"])), 284)
            self.assertEqual(runner_fixture_key(payload),
                             runner_fixture_key(deepcopy(payload)))

        entries = self._fresh_abi_entries()
        context = self._context(entries)
        state = _Execution(
            pc=0x08191790, execution_trace=[0x08191790],
            current_instruction_address=0x08191790, current_opcode=0x26,
        )
        raw = self.stage61[
            0x08191790 - 0x08000000:0x08191795 - 0x08000000
        ]
        branches = _fork_abi_command(
            context, state, 0x08191790, 0x26, raw,
        )
        self.assertEqual(
            {branch.daycare_scenario_id for branch in branches},
            set(DAYCARE_SCENARIO_IDS),
        )
        fixtures: dict[str, dict] = {}
        materialized = _materialize_control_requirement(
            self.stage61, branches[0].abi_control_reads[0],
            owner_keys=[self.OWNER_ID], fixtures=fixtures,
        )
        self.assertEqual(materialized["relation_evidence"], [{
            "operator": DAYCARE_TRANSACTION_RELATION,
            "state_owners": [
                "PLAYER_PARTY_COUNT", "PLAYER_PARTY_RAW",
                "SAVE_BLOCK1_DAYCARE_RAW", "PLAYER_MONEY",
                "PENDING_DAYCARE_EGG_FLAG", "MODERN_EGG_QUEUE",
                "PC_CAPACITY",
            ],
        }])
        self.assertEqual(len(materialized["fixture_keys"]), 1)
        fixture = fixtures[materialized["fixture_keys"][0]]
        self.assertEqual(fixture["scenario_id"],
                         branches[0].daycare_scenario_id)

    def test_special188_writes_var8004_only_and_189_writes_result_012(
        self,
    ) -> None:
        choices = self._manual_special(
            188, 0x081917ED, "empty_deposit",
        )
        self.assertEqual({row.vars[0x8004] for row in choices}, {0, 1, 7})
        self.assertTrue(all(row.vars[0x800D] == 0xBEEF for row in choices))
        entries = self._fresh_abi_entries()
        context = self._context(entries)
        for row in choices:
            _record_completed_abi_dispatch(
                context, row, 0x081917ED, 0x25,
                self.stage61[
                    0x081917ED - 0x08000000:0x081917F0 - 0x08000000
                ],
            )
            self.assertEqual(row.abi_dispatches[-1]["result_capture"], {
                "kind": "NONE", "value": None,
            })

        menu = self._manual_special(
            189, 0x081918F5, "two_sufficient",
        )
        self.assertEqual({row.vars[0x800D] for row in menu}, {0, 1, 2})
        for row in menu:
            _record_completed_abi_dispatch(
                context, row, 0x081918F5, 0x25,
                self.stage61[
                    0x081918F5 - 0x08000000:0x081918F8 - 0x08000000
                ],
            )
            capture = row.abi_dispatches[-1]["result_capture"]
            self.assertEqual(capture["kind"], "GLOBAL_VAR_RESULT")
            self.assertIn(capture["value"], (0, 1, 2))

    def test_daycare_result_and_control_abi_drift_fail_closed(self) -> None:
        def forge_188(entry: dict) -> None:
            entry["result_contract"]["global_var_result_write"] = {
                "candidate_values": [0, 1, 2, 3, 4, 5, 7],
                "relation": "FORGED",
            }

        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "DAYCARE_RESULT_ABI_DRIFT:188",
        ):
            self._manual_special(
                188, 0x081917ED, "empty_deposit", mutate_entry=forge_188,
            )

        def forge_189(entry: dict) -> None:
            entry["result_contract"]["global_var_result_write"][
                "candidate_values"
            ] = [0, 1, 127]

        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "DAYCARE_RESULT_ABI_DRIFT:189",
        ):
            self._manual_special(
                189, 0x081918F5, "two_sufficient", mutate_entry=forge_189,
            )

        def forge_global_four_island_control(entry: dict) -> None:
            entry["input_controls"] = [{
                "kind": DAYCARE_TRANSACTION_KIND,
                "owner": "FORGED_GLOBAL_OWNER",
                "candidate_values": list(DAYCARE_SCENARIO_IDS),
                "relation": DAYCARE_TRANSACTION_RELATION,
            }]

        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "DAYCARE_SPECIAL_ABI_DRIFT:182",
        ):
            self._manual_special(
                182, 0x08191790, "empty_deposit",
                mutate_entry=forge_global_four_island_control,
            )

    def test_special189_writer_graph_pins_source_handoff_and_task_rom(
        self,
    ) -> None:
        evidence = _special_global_result_writer_evidence(
            189, self.stage61, self.source_blobs,
            clean_rom=self.clean, stage60_rom=self.stage60,
        )
        self.assertEqual(evidence["completed_candidate_values"], [0, 1, 2])
        self.assertEqual(
            [row["symbol"] for row in evidence["source_functions"]],
            ["ShowDaycareLevelMenu", "Task_HandleDaycareLevelMenuInput"],
        )
        self.assertEqual(evidence["additional_rom_bindings"], [{
            "symbol": "Task_HandleDaycareLevelMenuInput",
            "address": "0x08045F84", "byte_length": 0xBC,
            "sha256": (
                "b34ca6e08c3e02c44d21794a527a52891bdb5d9c209fe9e2015d95d4bfa25a95"
            ),
            "provenance": "CLEAN_STAGE60_STAGE61_FULL_SPAN",
        }])
        drifted = dict(self.source_blobs)
        path = "vendor/upstream/pokefirered/src/daycare.c"
        drifted[path] = drifted[path] + b"\n"
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "SPECIAL189 result writer source不一致",
        ):
            _special_global_result_writer_evidence(
                189, self.stage61, drifted,
                clean_rom=self.clean, stage60_rom=self.stage60,
            )

    def test_object_035_000_000_finishes_at_94_paths_below_cap(self) -> None:
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph

        semantic = deepcopy(self.semantic)
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(
            self.source_blobs[builder_path]
        ).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        owner = next(
            row for row in self.inventory["owners"]
            if row["owner_id"] == self.OWNER_ID
        )
        self.assertEqual(owner["root"], self.ROOT_PC)
        graph = SemanticScriptGraph(self.stage61)
        graph.walk([self.ROOT_PC])
        self.assertEqual(len(graph.nodes), 19)
        self.assertEqual(graph.diagnostics, [])
        text_assets, _provenance = _independent_runtime_text_assets(
            self.clean, self.stage60, self.stage61, semantic,
            self.repair_manifest, graph, source_blobs=self.source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            self.clean, self.stage60, self.stage61, semantic, owner, graph,
            text_assets, self._fresh_abi_entries(), self.source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, self.ROOT_PC),
        )
        self.assertEqual(blockers, [])
        self.assertEqual(len(executions), 94)
        self.assertLess(len(executions), MAX_EXECUTION_PATHS)
        by_scenario = Counter(
            state.daycare_scenario_id for _context, state in executions
        )
        self.assertEqual(by_scenario, Counter({
            "egg_waiting": 3,
            "empty_only_one": 6,
            "empty_deposit": 18,
            "one_insufficient": 18,
            "one_sufficient": 18,
            "two_sufficient": 30,
            None: 1,
        }))
        decisions = [
            decision
            for _context, state in executions
            for decision in state.decisions
        ]
        self.assertTrue(any(
            row.get("special_id") == 187 for row in decisions
        ))
        self.assertTrue(any(
            row.get("special_id") == 192 for row in decisions
        ))
        self.assertTrue(any(
            row.get("special_id") == 197 and row.get("result_value") == 0
            for row in decisions
        ))
        self.assertTrue(any(
            row.get("kind") == "DAYCARE_PARTY_SELECTION_EXACT"
            and row.get("result_value") == 7 for row in decisions
        ))
        self.assertTrue(any(
            row.get("kind") == "DAYCARE_LEVEL_MENU_SELECTION_EXACT"
            and row.get("result_value") == 2 for row in decisions
        ))
        self.assertTrue(any(
            row.get("special_id") == 182 and row.get("result_value") == 1
            for row in decisions
        ))
        from tools.stage61_interaction_oracle import (
            _flat_result_internal_controls,
            _validate_runner_flat_internal_controls,
        )
        repeated_context, repeated_state = next(
            (context, state) for context, state in executions
            if sum(
                decision.get("special_id") == 190
                and decision.get("instruction_address") == "0x08191881"
                for decision in state.decisions
            ) == 2
        )
        repeated_internal = _flat_result_internal_controls(
            repeated_context, repeated_state, sequence_id="daycare-two-slots",
        )
        repeated_captures = [
            row for row in repeated_internal
            if row["instruction_address"] == "0x08191886"
            and row["writer"] ==
                "SPECIALVAR:GetNumLevelsGainedFromDaycare"
        ]
        self.assertEqual(
            [(row["capture"]["expected_token_index"],
              row["capture"]["expected_execution_ordinal"],
              row["capture"]["expected_value"])
             for row in repeated_captures],
            [(2, 0, 0), (2, 1, 0)],
        )
        daycare_contracts = [
            row["producer"]["ordered_runtime_capture"]
            for row in repeated_captures
        ]
        self.assertEqual(
            [contract["occurrence_index"] for contract in daycare_contracts],
            [0, 1],
        )
        self.assertTrue(all(
            contract["schema_version"] == 2
            and contract["token_index_sequence"] == [2, 2]
            and contract["execution_ordinal_sequence"] == [0, 1]
            and contract["relation"] == DAYCARE_ORDERED_CAPTURE_RELATION
            for contract in daycare_contracts
        ))
        _validate_runner_flat_internal_controls(
            repeated_internal,
            [{
                "sequence_id": "daycare-two-slots",
                "tokens": repeated_state.tokens,
            }],
            "daycare same-token ordered capture",
        )
        duplicate_ordinal = deepcopy(repeated_internal)
        duplicate_ordinal[duplicate_ordinal.index(repeated_captures[1])][
            "capture"
        ]["expected_execution_ordinal"] = 0
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "runner internal identity重複",
        ):
            _validate_runner_flat_internal_controls(
                duplicate_ordinal,
                [{
                    "sequence_id": "daycare-two-slots",
                    "tokens": repeated_state.tokens,
                }],
                "daycare duplicate occurrence forge",
            )
        observed_repeated_sites: set[tuple[str, str]] = set()
        for path_index, (context, state) in enumerate(executions):
            sequence_id = f"daycare-path-{path_index:03d}"
            internal = _flat_result_internal_controls(
                context, state, sequence_id=sequence_id,
            )
            _validate_runner_flat_internal_controls(
                internal,
                [{"sequence_id": sequence_id, "tokens": state.tokens}],
                sequence_id,
            )
            for row in internal:
                contract = row["producer"].get("ordered_runtime_capture")
                if isinstance(contract, dict) \
                        and contract.get("relation") == \
                            DAYCARE_ORDERED_CAPTURE_RELATION:
                    observed_repeated_sites.add((
                        row["instruction_address"], row["writer"],
                    ))
        self.assertEqual(
            observed_repeated_sites, set(DAYCARE_ORDERED_CAPTURE_SITES),
        )
        decision_drift = repeated_state.clone()
        second_level_decision = [
            decision for decision in decision_drift.decisions
            if decision.get("special_id") == 190
            and decision.get("instruction_address") == "0x08191881"
        ][1]
        second_level_decision["result_value"] = 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "DAYCARE_ORDERED_RUNTIME_CAPTURE_CONTRACT_REQUIRED:"
            "0x08191886",
        ):
            _flat_result_internal_controls(
                repeated_context, decision_drift,
                sequence_id="daycare-decision-drift",
            )
        projected = [
            (state, _runner_required_postconditions(context, state))
            for context, state in executions
        ]
        changed = [
            (state, required) for state, required in projected
            if required["party"] is not None
        ]
        self.assertTrue(changed)
        self.assertTrue(all(
            set(required["party"]) == {
                "count", "raw_sha256", "raw_byte_length",
            }
            and required["party"]["raw_byte_length"] == 600
            and len(required["party"]["raw_sha256"]) == 64
            for _state, required in changed
        ))
        self.assertTrue(all(
            row["block"] == "SB1"
            and 0x2F80 <= row["offset"] < 0x2F80 + 284
            and 0 <= row["value"] <= 0xFF
            for _state, required in changed
            for row in required["persistent"]
        ))
        self.assertTrue(any(
            required["party"]["count"] == 1
            for _state, required in changed
        ))
        self.assertTrue(any(
            required["party"]["count"] in {3, 4}
            for _state, required in changed
        ))
        self.assertEqual({
            required["money"] for _state, required in projected
            if required["money"] is not None
        }, {0, 100})

        drifted = next(
            state.clone() for state, required in changed
            if required["persistent"]
        )
        drifted.effects = [
            effect for effect in drifted.effects
            if not (
                effect.get("domain") == "save"
                and effect.get("owner") == "SAVE_BLOCK1_DAYCARE"
            )
        ]
        drift_context = next(
            context for context, state in executions
            if state.daycare_scenario_id == drifted.daycare_scenario_id
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "RUNNER_DAYCARE_CHANGED_WITHOUT_SAVE_EFFECT",
        ):
            _runner_required_postconditions(drift_context, drifted)

    def test_route5_single_mon_daycare_finishes_with_exact_raw_state(
        self,
    ) -> None:
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph

        semantic = deepcopy(self.semantic)
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(
            self.source_blobs[builder_path]
        ).hexdigest()
        for materialized_range in semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        owner = deepcopy(next(
            row for row in self.inventory["owners"]
            if row["owner_id"] == "OBJECT:098/098:000"
        ))
        owner["root"] = ROUTE5_DAYCARE_SOURCE_ROOT
        owner["raw_root"] = ROUTE5_DAYCARE_SOURCE_ROOT
        graph = SemanticScriptGraph(self.stage61)
        graph.walk([ROUTE5_DAYCARE_SOURCE_ROOT])
        self.assertEqual(graph.diagnostics, [])
        text_assets, _provenance = _independent_runtime_text_assets(
            self.clean, self.stage60, self.stage61, semantic,
            self.repair_manifest, graph, source_blobs=self.source_blobs,
        )
        context = _runtime_context(
            self.clean, self.stage60, self.stage61, semantic, owner, graph,
            text_assets, self._fresh_abi_entries(), self.source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(
                graph, ROUTE5_DAYCARE_SOURCE_ROOT,
            ),
            event_design_rank_model=None,
        )
        executions = _execute(context)
        self.assertEqual(len(executions), 37)
        scenarios = Counter(
            state.daycare_scenario_id for state in executions
        )
        self.assertEqual(
            set(scenarios), {None, *ROUTE5_DAYCARE_SCENARIO_IDS},
        )
        self.assertEqual(scenarios[None], 1)
        self.assertTrue(all(
            scenarios[scenario] > 0
            for scenario in ROUTE5_DAYCARE_SCENARIO_IDS
        ))

        projected = []
        fixture_kinds: set[str] = set()
        for state in executions:
            required = _runner_required_postconditions(context, state)
            fixtures: dict[str, dict] = {}
            external, _internal = _runtime_control_rows(
                context, state, owner_keys=[owner["owner_id"]],
                fixtures=fixtures,
            )
            fixture_kinds.update(
                fixture["fixture_kind"] for fixture in fixtures.values()
            )
            if state.daycare_scenario_id is not None:
                control = next(
                    row for row in external
                    if row["kind"] == DAYCARE_TRANSACTION_KIND
                )
                self.assertEqual(control["id"], 1)
                self.assertEqual(control["relation_evidence"][0][
                    "operator"
                ], ROUTE5_DAYCARE_TRANSACTION_RELATION)
            projected.append((state, required))
        self.assertEqual(fixture_kinds, {DAYCARE_TRANSACTION_KIND})

        changed = [
            (state, required) for state, required in projected
            if required["party"] is not None
        ]
        self.assertTrue(changed)
        self.assertEqual({
            required["party"]["count"] for _state, required in changed
        }, {1, 3})
        self.assertTrue(all(
            0x3C98 <= row["offset"] < 0x3C98 + 140
            for _state, required in changed
            for row in required["persistent"]
        ))
        self.assertIn(400, {
            required["money"] for _state, required in projected
            if required["money"] is not None
        })


class Stage61PartyMoveTransactionFocusedTests(unittest.TestCase):
    ROOT_OWNERS = {
        0x092D0A10: "OBJECT:033/001:000",
        0x092D0A98: "OBJECT:011/009:000",
        0x09432DD9: "OBJECT:098/071:000",
    }

    @classmethod
    def setUpClass(cls) -> None:
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        from tools.stage61_cyclic_decision_contracts import (
            build_stage61_cyclic_decision_contracts,
            load_stage61_cyclic_decision_source_blobs,
        )
        from tools.stage61_interaction_oracle import (
            _validate_cyclic_decision_contract_input,
        )

        cls.clean = (
            ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
        ).read_bytes()
        cls.stage60 = (
            ROOT / "build/stages/60_wild_species_root_repair.gba"
        ).read_bytes()
        cls.stage61 = (
            ROOT / "build/stages/61_display_npc_event_audit.gba"
        ).read_bytes()
        cls.semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        cls.repair_manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text())
        cls.inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        catalog = json.loads((
            ROOT / "reports/generated/stage61_npc_interaction_catalog_legacy.json"
        ).read_text())
        cls.source_blobs, symbol_reports = _interaction_abi_pinned_inputs()
        cls.manifest = build_pinned_interaction_abi_manifest(
            cls.clean, cls.stage60, cls.stage61, catalog,
            source_blobs=cls.source_blobs,
            runtime_symbol_reports=symbol_reports,
        )
        cls.abi_index = _interaction_abi_index(
            cls.stage61, cls.manifest, source_blobs=cls.source_blobs,
        )
        cyclic_document = build_stage61_cyclic_decision_contracts(
            cls.stage61, cls.inventory,
            load_stage61_cyclic_decision_source_blobs(ROOT),
        )
        cls.cyclic_index = _validate_cyclic_decision_contract_input(
            cyclic_document, cls.stage61,
            expected_event_owner_inventory_sha256=
                cls.inventory["inventory_sha256"],
        )
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(cls.source_blobs[builder_path]).hexdigest()
        for materialized_range in cls.semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        cls.runtime_cache: dict[int, tuple] = {}

    @classmethod
    def _run_root(cls, root: int) -> tuple:
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph
        from tools.stage61_interaction_oracle import (
            _bind_cyclic_decision_root_contract,
        )

        if root in cls.runtime_cache:
            return cls.runtime_cache[root]
        owner_id = cls.ROOT_OWNERS[root]
        owner = next(
            row for row in cls.inventory["owners"]
            if row["owner_id"] == owner_id
        )
        graph = SemanticScriptGraph(cls.stage61)
        graph.walk([root])
        if graph.diagnostics:
            raise AssertionError(graph.diagnostics)
        binding = _bind_cyclic_decision_root_contract(
            cls.cyclic_index, cls.semantic, owner_ids=[owner_id],
            target_root=root, execution_root=root,
            require_exact_owner_set=True,
        )
        text_assets, _provenance = _independent_runtime_text_assets(
            cls.clean, cls.stage60, cls.stage61, cls.semantic,
            cls.repair_manifest, graph, source_blobs=cls.source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            cls.clean, cls.stage60, cls.stage61, cls.semantic, owner, graph,
            text_assets, cls.abi_index, cls.source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, root),
            cyclic_decision_contract=binding,
        )
        cls.runtime_cache[root] = executions, blockers, binding, graph
        return cls.runtime_cache[root]

    @staticmethod
    def _special_entry(
        abi_index: dict[str, dict], special_id: int,
    ) -> tuple[str, dict]:
        matches = [
            (key, row) for key, row in abi_index.items()
            if key.startswith(f"SPECIAL:{special_id:04X}:")
        ]
        if len(matches) != 1:
            raise AssertionError((special_id, matches))
        return matches[0]

    def test_exact_public_runner_schema_and_13_raw_scenarios(self) -> None:
        self.assertEqual(
            PARTY_MOVE_SCENARIO_IDS,
            (*PARTY_MOVE_RELEARNER_SCENARIO_IDS,
             *PARTY_MOVE_DELETER_SCENARIO_IDS),
        )
        self.assertEqual(len(PARTY_MOVE_SCENARIO_IDS), 13)
        self.assertEqual(PARTY_MOVE_ROOTS, set(self.ROOT_OWNERS))
        for scenario_id in PARTY_MOVE_SCENARIO_IDS:
            payload = _party_move_scenario_payload(scenario_id)
            raw = bytes.fromhex(payload["party_raw_hex"])
            self.assertEqual(payload["fixture_kind"],
                             PARTY_MOVE_TRANSACTION_KIND)
            self.assertEqual(len(raw), 600)
            self.assertEqual(payload["party_count"], 2)
            self.assertTrue(all(
                _party_move_checksum_valid(raw[slot * 100:(slot + 1) * 100])
                for slot in range(2)
            ))
            self.assertEqual(
                payload["payment_policy"],
                "FREE_OVERLAY_NO_MUSHROOM_CONSUMPTION"
                if payload["family"] == "RELEARNER" else None,
            )
            self.assertEqual(runner_fixture_key(payload),
                             runner_fixture_key(deepcopy(payload)))

        abi = runner_control_abi_contract()
        self.assertEqual(
            abi["required_value_types"][PARTY_MOVE_TRANSACTION_KIND],
            {
                "scenario_id": "source-derived representative ID",
                "layout_ref": "sha256", "family": "RELEARNER|DELETER",
                "party_count": "u8<=6", "party_sha256": "sha256",
                "party_selection_sequence": "list[u8(0..5|7=cancel)]",
                "selected_move_slot": "null|u8(0..3|4=cancel)",
                "selected_relearn_move": "null|u16 move id",
                "teach_outcome": "null|u8(0=false|1=true)",
                "expected_relearnable_count": "null|u8",
                "payment_policy":
                    "null|FREE_OVERLAY_NO_MUSHROOM_CONSUMPTION",
                "expected_action": "source scenario action",
            },
        )
        self.assertEqual(
            abi["fixture_registry"]["payload_exact_keys"][
                PARTY_MOVE_TRANSACTION_KIND
            ],
            [
                "expected_action", "expected_relearnable_count", "family",
                "fixture_kind", "party_count", "party_raw_hex",
                "party_selection_sequence", "payment_policy", "scenario_id",
                "selected_move_slot", "selected_relearn_move",
                "teach_outcome",
            ],
        )

    def test_materialization_is_single_fixture_and_source_correlated(self) -> None:
        for scenario_id in PARTY_MOVE_SCENARIO_IDS:
            row = _party_move_input_control()
            row.update({"id": 0, "required_value": scenario_id})
            fixtures: dict[str, dict] = {}
            materialized = _materialize_control_requirement(
                self.stage61, row,
                owner_keys=[self.ROOT_OWNERS[0x092D0A10]],
                fixtures=fixtures,
            )
            self.assertEqual(len(materialized["fixture_keys"]), 1)
            ref = materialized["fixture_keys"][0]
            self.assertEqual(materialized["value"]["layout_ref"], ref)
            self.assertEqual(fixtures[ref],
                             _party_move_scenario_payload(scenario_id))
            self.assertEqual(materialized["relation_evidence"], [{
                "operator": PARTY_MOVE_TRANSACTION_RELATION,
                "state_owners": ["PLAYER_PARTY_COUNT", "PLAYER_PARTY_RAW"],
                "model_sources": dict(PARTY_MOVE_MODEL_SOURCE_SHA256),
            }])
            self.assertEqual(
                materialized["value"]["party_sha256"],
                hashlib.sha256(bytes.fromhex(
                    fixtures[ref]["party_raw_hex"]
                )).hexdigest(),
            )

        forged = _party_move_scenario_payload("deleter_valid_ppups")
        party = bytearray.fromhex(forged["party_raw_hex"])
        party[44] ^= 1
        forged["party_raw_hex"] = bytes(party).hex()
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "PARTY_MOVE_TRANSACTION_STATE source scenario不一致",
        ):
            runner_fixture_key(forged)

    def test_delete_compacts_moves_pp_and_ppups_with_checksum(self) -> None:
        payload = _party_move_scenario_payload("deleter_valid_ppups")
        party = bytearray.fromhex(payload["party_raw_hex"])
        before = bytes(party)
        transition = _party_move_delete_selected(party, 0, 1)
        self.assertEqual(transition[:3], (
            [10, 20, 30, 40], [35, 20, 25, 35], 0x08,
        ))
        self.assertEqual(transition[3:], (
            [10, 30, 40, 0], [35, 25, 35, 0], 0,
        ))
        self.assertEqual(_party_move_record_fields(party, 0),
                         transition[3:])
        self.assertTrue(_party_move_checksum_valid(party[:100]))
        self.assertEqual(bytes(party[100:]), before[100:])
        changed = {
            index for index, (old, new) in enumerate(zip(before, party))
            if old != new
        }
        self.assertTrue(changed)
        self.assertTrue(changed <= {
            28, 29, *range(46, 52), *range(53, 56), 56,
        })
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "PARTY_MOVE_DELETE_EMPTY_SLOT",
        ):
            _party_move_delete_selected(party, 0, 3)

    def test_teach_uses_rom_base_pp_clears_selected_ppups_and_checksum(self) -> None:
        replace_payload = _party_move_scenario_payload(
            "relearner_teach_replace_slot"
        )
        replacement = bytearray.fromhex(replace_payload["party_raw_hex"])
        transition = _party_move_teach_selected(
            self.stage61, replacement, 0, 1, 184,
        )
        expected_pp = self.stage61[
            0x090421F4 - 0x08000000 + 184 * 12 + 4
        ]
        self.assertEqual(transition[:3], (
            [98, 1, 2, 3], [30, 35, 25, 15], 0x08,
        ))
        self.assertEqual(transition[3], [98, 184, 2, 3])
        self.assertEqual(transition[4], [30, expected_pp, 25, 15])
        self.assertEqual(transition[5], 0)
        self.assertTrue(_party_move_checksum_valid(replacement[:100]))

        empty_payload = _party_move_scenario_payload(
            "relearner_teach_empty_slot"
        )
        empty = bytearray.fromhex(empty_payload["party_raw_hex"])
        _party_move_teach_selected(self.stage61, empty, 0, 1, 184)
        self.assertEqual(_party_move_record_fields(empty, 0)[0],
                         [98, 184, 0, 0])
        self.assertTrue(_party_move_checksum_valid(empty[:100]))
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "PARTY_MOVE_TEACH_EMPTY_SLOT_SELECTION_DRIFT",
        ):
            wrong = bytearray.fromhex(empty_payload["party_raw_hex"])
            _party_move_teach_selected(self.stage61, wrong, 0, 2, 184)

    def test_special_writer_truth_is_var8004_8005_not_var_result(self) -> None:
        for special_id in PARTY_MOVE_SPECIAL_IDS:
            _key, entry = self._special_entry(self.abi_index, special_id)
            global_write = entry["result_contract"][
                "global_var_result_write"
            ]
            if special_id == 223:
                self.assertEqual(global_write["candidate_values"],
                                 [0, 1, 2, 3, 4])
            else:
                self.assertIsNone(global_write)

        relearn, blockers, _binding, _graph = self._run_root(0x092D0A10)
        self.assertEqual(blockers, [])
        deleter, blockers, _binding, _graph = self._run_root(0x092D0A98)
        self.assertEqual(blockers, [])
        targets_by_pc: dict[int, set[int]] = {}
        for _context, state in [*relearn, *deleter]:
            for write in state.var_writes:
                targets_by_pc.setdefault(
                    int(write["instruction_address"]), set()
                ).add(int(write["target_id"]))
        self.assertEqual(targets_by_pc[0x092D07BC], {0x8004, 0x8005})
        self.assertEqual(targets_by_pc[0x092D07E4], {0x8004})
        self.assertEqual(targets_by_pc[0x092D0918], {0x8004})
        self.assertEqual(targets_by_pc[0x092D0945], {0x8005})
        self.assertEqual(targets_by_pc[0x092D0935], {0x800D})
        self.assertNotIn(0x092D0994, targets_by_pc)  # SPECIAL222 is buffer-only.

    def test_three_real_roots_are_finite_with_exact_cyclic_exit(self) -> None:
        expected_paths = {
            0x092D0A10: 70, 0x092D0A98: 11, 0x09432DD9: 11,
        }
        expected_nodes = {
            0x092D0A10: 12, 0x092D0A98: 11, 0x09432DD9: 6,
        }
        expected_evidence = {
            0x092D0A10: 30, 0x092D0A98: 4, 0x09432DD9: 1,
        }
        for root, owner_id in self.ROOT_OWNERS.items():
            with self.subTest(root=f"0x{root:08X}"):
                executions, blockers, binding, graph = self._run_root(root)
                self.assertEqual(blockers, [])
                self.assertEqual(len(graph.nodes), expected_nodes[root])
                self.assertEqual(len(executions), expected_paths[root])
                self.assertLess(len(executions), MAX_EXECUTION_PATHS)
                self.assertTrue(all(
                    state.terminated and state.terminal_kind == "FIELD_RELEASE"
                    for _context, state in executions
                ))
                self.assertEqual({
                    state.party_move_scenario_id
                    for _context, state in executions
                    if state.party_move_scenario_id is not None
                }, set(
                    PARTY_MOVE_RELEARNER_SCENARIO_IDS
                    if root == 0x092D0A10 else
                    PARTY_MOVE_DELETER_SCENARIO_IDS
                ))
                evidence = [
                    row for _context, state in executions
                    for row in state.cyclic_quotient_evidence
                ]
                self.assertEqual(len(evidence), expected_evidence[root])
                self.assertTrue(all(
                    _cyclic_quotient_real_exit_execution_valid(row)
                    for row in evidence
                ))
                expected_roots, expected_sccs, expected_sites, \
                    consumed_roots, consumed_sccs, consumed_sites = \
                    _cyclic_event_menu_quotient_identity_sets(
                        [binding], evidence,
                    )
                self.assertEqual(expected_roots, consumed_roots)
                self.assertEqual(expected_sccs, consumed_sccs)
                self.assertEqual(expected_sites, consumed_sites)
                self.assertEqual(binding["bound_owner_ids"], [owner_id])

        all_executions = [
            pair for root in self.ROOT_OWNERS
            for pair in self._run_root(root)[0]
        ]
        projected = [
            (context, state, _runner_required_postconditions(context, state))
            for context, state in all_executions
        ]
        changed = [
            (context, state, required)
            for context, state, required in projected
            if required["party"] is not None
        ]
        self.assertTrue(changed)
        self.assertEqual({
            state.party_move_scenario_id
            for _context, state, _required in changed
        }, {
            "relearner_teach_empty_slot", "relearner_teach_replace_slot",
            "deleter_valid_no_ppups", "deleter_valid_ppups",
            # The imported upstream Fuchsia script calls SPECIAL221 directly;
            # unlike the Vega overlay root, it has no native form-move guard.
            "deleter_unforgettable_then_cancel",
        })
        self.assertEqual({
            state.party_move_scenario_id
            for context, state, _required in changed
            if context.target_root == 0x092D0A98
        }, {"deleter_valid_no_ppups", "deleter_valid_ppups"})
        self.assertEqual({
            state.party_move_scenario_id
            for context, state, _required in changed
            if context.target_root == 0x09432DD9
        }, {
            "deleter_unforgettable_then_cancel",
            "deleter_valid_no_ppups", "deleter_valid_ppups",
        })
        self.assertTrue(all(
            required["party"] == {
                "count": state.party_move_party_count,
                "raw_sha256": hashlib.sha256(bytes.fromhex(
                    str(state.party_move_party_current_hex)
                )).hexdigest(),
                "raw_byte_length": 600,
            }
            for _context, state, required in changed
        ))

        drift_context, drift_state, _required = changed[0]
        drifted = drift_state.clone()
        drifted.effects = [
            effect for effect in drifted.effects
            if not (
                effect.get("domain") == "party"
                and effect.get("relation") == PARTY_MOVE_TRANSACTION_RELATION
            )
        ]
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "RUNNER_PARTY_MOVE_CHANGED_WITHOUT_EFFECT",
        ):
            _runner_required_postconditions(drift_context, drifted)

    def test_control_result_effect_and_cyclic_abi_forges_fail_closed(self) -> None:
        executions, blockers, binding, _graph = self._run_root(0x092D0A98)
        self.assertEqual(blockers, [])
        base_context = executions[0][0]
        key, _entry = self._special_entry(self.abi_index, 159)
        forged_abi = deepcopy(self.abi_index)
        forged_abi[key]["input_controls"] = [_party_move_input_control()]
        context = replace(base_context, abi_index=forged_abi)
        state = _Execution(
            pc=0x092D0918, vars={0x800D: 0xBEEF},
            execution_trace=[0x092D0918],
            current_instruction_address=0x092D0918, current_opcode=0x25,
        )
        _party_move_install_scenario(state, "deleter_party_cancel")
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "PARTY_MOVE_SPECIAL_ABI_DRIFT:159",
        ):
            _fork_abi_command(
                context, state, 0x092D0918, 0x25,
                bytes.fromhex("259f00"),
            )

        forged_binding = deepcopy(binding)
        selector = next(
            row for row in forged_binding["sites"]
            if row["decision_pc"] == "0x092D0918"
        )
        selector["decision_site"]["result_policy"][
            "result_variable"
        ] = "VAR_RESULT"
        context = replace(
            base_context, cyclic_decision_contract=forged_binding,
        )
        state = _Execution(
            pc=0x092D0918, vars={0x800D: 0xBEEF},
            execution_trace=[0x092D0918],
            current_instruction_address=0x092D0918, current_opcode=0x25,
        )
        _party_move_install_scenario(state, "deleter_party_cancel")
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "PARTY_MOVE_TRANSACTION_RESULT_POLICY_MISMATCH",
        ):
            _fork_abi_command(
                context, state, 0x092D0918, 0x25,
                bytes.fromhex("259f00"),
            )

        forged = deepcopy(self.manifest)
        special223 = next(
            row for row in forged["special_abis"]
            if row["special_id"] == 223
        )
        special223["result_contract"]["global_var_result_write"][
            "candidate_values"
        ] = [0, 1, 2, 3]
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "SPECIAL223 .*result contract不一致",
        ):
            _interaction_abi_index(
                self.stage61, forged, source_blobs=self.source_blobs,
            )


class Stage61GiftStorageFossilFocusedTests(unittest.TestCase):
    MAP_SECTIONS = {
        0x081859FA: 92,
        0x0869B090: 142,
        0x086B2EC3: 176,
        0x086B2FC8: 176,
        0x086B8E2C: 95,
        0x087FBA7B: 98,
        0x0880B396: 102,
        0x0880B3AA: 102,
        0x0880B3BE: 102,
        0x088B3190: 132,
        0x0942EEFE: 44,
        0x0943261F: 6,
        0x09433696: 8,
        0x09434187: 14,
    }

    @classmethod
    def setUpClass(cls) -> None:
        from scripts.build_stage61_display_npc_event_audit import (
            _interaction_abi_pinned_inputs,
        )
        from tools.stage61_cyclic_decision_contracts import (
            build_stage61_cyclic_decision_contracts,
            load_stage61_cyclic_decision_source_blobs,
        )
        from tools.stage61_interaction_oracle import (
            _validate_cyclic_decision_contract_input,
        )

        (
            fixture_root, cls.stage61, _physical_maps, _owner_ledger, cls.inventory,
        ) = _current_stage61_interaction_fixture()
        cls.clean = (
            ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
        ).read_bytes()
        cls.stage60 = (
            ROOT / "build/stages/60_wild_species_root_repair.gba"
        ).read_bytes()
        cls.semantic = json.loads((
            fixture_root / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        cls.repair_manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text())
        catalog = json.loads((
            ROOT / "reports/generated/stage61_npc_interaction_catalog_legacy.json"
        ).read_text())
        cls.source_blobs, symbol_reports = _interaction_abi_pinned_inputs()
        cls.manifest = build_pinned_interaction_abi_manifest(
            cls.clean, cls.stage60, cls.stage61, catalog,
            source_blobs=cls.source_blobs,
            runtime_symbol_reports=symbol_reports,
            event_owner_inventory=cls.inventory,
        )
        cls.abi_index = _interaction_abi_index(
            cls.stage61, cls.manifest, source_blobs=cls.source_blobs,
        )
        cyclic_document = build_stage61_cyclic_decision_contracts(
            cls.stage61, cls.inventory,
            load_stage61_cyclic_decision_source_blobs(ROOT),
        )
        cls.cyclic_index = _validate_cyclic_decision_contract_input(
            cyclic_document, cls.stage61,
            expected_event_owner_inventory_sha256=
                cls.inventory["inventory_sha256"],
        )
        builder_path = "scripts/build_stage61_display_npc_event_audit.py"
        builder_sha = hashlib.sha256(
            cls.source_blobs[builder_path]
        ).hexdigest()
        for materialized_range in cls.semantic["stage61_materialization"][
            "additional_materialized_ranges"
        ]:
            for relocation in materialized_range["text_relocations"]:
                contract = relocation.get("semantic_contract")
                if isinstance(contract, dict) \
                        and contract.get("source_path") == builder_path:
                    contract["source_sha256"] = builder_sha
        cls.runtime_cache: dict[int, tuple] = {}

    @classmethod
    def _run_root(cls, root: int) -> tuple:
        from tools.stage61_event_semantic_relocator import SemanticScriptGraph
        from tools.stage61_interaction_oracle import (
            _bind_cyclic_decision_root_contract,
        )

        if root in cls.runtime_cache:
            return cls.runtime_cache[root]
        owners = [
            row for row in cls.inventory["owners"]
            if row.get("runtime_root") is True and row.get("root") == root
        ]
        if len(owners) != 1:
            raise AssertionError((root, [row["owner_id"] for row in owners]))
        owner = owners[0]
        graph = SemanticScriptGraph(cls.stage61)
        graph.walk([root])
        if graph.diagnostics:
            raise AssertionError(graph.diagnostics)
        binding = _bind_cyclic_decision_root_contract(
            cls.cyclic_index, cls.semantic,
            owner_ids=[owner["owner_id"]],
            target_root=root, execution_root=root,
            require_exact_owner_set=True,
        )
        text_assets, _provenance = _independent_runtime_text_assets(
            cls.clean, cls.stage60, cls.stage61, cls.semantic,
            cls.repair_manifest, graph, source_blobs=cls.source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            cls.clean, cls.stage60, cls.stage61, cls.semantic,
            owner, graph, text_assets, cls.abi_index, cls.source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(graph),
            shared_root_plan=_runtime_root_plan(graph, root),
            cyclic_decision_contract=binding,
        )
        cls.runtime_cache[root] = executions, blockers, graph
        return cls.runtime_cache[root]

    def test_four_executor_representatives_and_thirty_runner_layouts(
        self,
    ) -> None:
        self.assertEqual(len(GIFT_STORAGE_EXECUTOR_SCENARIO_IDS), 4)
        self.assertEqual(len(GIFT_STORAGE_RUNNER_SCENARIO_IDS), 30)
        self.assertEqual(
            set(GIFT_STORAGE_EXECUTOR_SCENARIO_IDS), {
                "party_space", "pc_current_box_00",
                "pc_next_box_13", "storage_full",
            },
        )
        registry: dict[str, dict] = {}
        manifest = _gift_storage_dedicated_sweep_manifest(
            registry, stage61_rom=self.stage61,
        )
        self.assertEqual(len(registry), 30)
        self.assertEqual(
            manifest["executor_representative_count"], 4,
        )
        self.assertEqual(manifest["runner_exhaustive_layout_count"], 30)
        self.assertEqual(
            manifest["canonical_command"], {
                "opcode_pc": "0x08185B46",
                "opcode_raw_hex": "790140090000000000000000000000",
                "resolved_species": 18, "level": 9, "held_item": 0,
                "custom_give_operand": 0, "ball_operand": 0,
                "fixed_rng_seed": 0x61E661E6,
                "player_name_hex": "cebfcdceffffff",
                "player_gender": 0, "player_trainer_id": 0x12345678,
                "lead_has_synchronize": False,
                "custom_creation_flags": False,
                "shiny_charm": False, "fishing_streak": 0,
            },
        )
        self.assertIsNotNone(manifest["expected_generated_mon"])
        self.assertEqual(
            len(bytes.fromhex(
                manifest["expected_generated_mon"]["raw_100_hex"]
            )), 100,
        )
        self.assertEqual(
            len(bytes.fromhex(
                manifest["expected_generated_mon"]["raw_80_hex"]
            )), 80,
        )
        for scenario_id in GIFT_STORAGE_RUNNER_SCENARIO_IDS:
            payload = _gift_storage_scenario_payload(scenario_id)
            self.assertEqual(
                len(bytes.fromhex(payload["party_raw_hex"])), 600,
            )
            self.assertEqual(
                len(bytes.fromhex(payload["storage_raw_hex"])), 0x83D0,
            )
            self.assertEqual(
                runner_fixture_key(payload), runner_fixture_key(deepcopy(payload)),
            )
        wrap = _gift_storage_scenario_payload("pc_next_box_13")
        self.assertEqual(
            (wrap["current_box"], wrap["expected_mon_box_id"]), (13, 0),
        )

        # runner_fixture_key separates schema rejection from canonical-layout
        # rejection. Keep both boundaries strict; never accept an unknown key.
        for mutation in ("extra_key", "missing_key", "unknown_scenario"):
            forged = deepcopy(wrap)
            if mutation == "extra_key":
                forged["unregistered"] = True
            elif mutation == "missing_key":
                del forged["party_count"]
            else:
                forged["scenario_id"] = "unregistered"
            with self.subTest(mutation=mutation), self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "runner GIFT_STORAGE_TRANSACTION_STATE fixture schema不正",
            ):
                runner_fixture_key(forged)
        forged = deepcopy(wrap)
        forged["expected_mon_box_id"] = 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "runner GIFT_STORAGE_TRANSACTION_STATE source layout不一致",
        ):
            runner_fixture_key(forged)
        path = "vendor/upstream/CFRU-JP/src/build_pokemon.c"
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "GIFT_STORAGE_MODEL_SOURCE_DRIFT",
        ):
            _validate_gift_storage_model_sources({
                path: (ROOT / path).read_bytes() + b"\n",
            })

    def test_create_mon_game_corner_raw_exact_and_rom_drift(self) -> None:
        _gift_storage_validate_create_mon_rom(self.stage61)
        generated = _gift_storage_create_mon(
            self.stage61, species=18, level=9, held_item=0,
            map_section_id=92,
        )
        self.assertEqual(generated["party_raw"].hex(), (
            "d0fe6ce778563412648a9caeffffff0000000102cebfcdceffffff0000000000"
            "120000004702000000460400cc0076001f02ba00140a130a0000000000000000"
            "00000000005c09028707f90d000000000000000009ff190019000b000e000a00"
            "0f001100"
        ))
        self.assertEqual(generated["moves"], [204, 118, 543, 186])
        self.assertEqual(generated["pps"], [20, 10, 19, 10])
        self.assertEqual(generated["friendship"], 70)
        self.assertEqual(generated["rng_after"], 0x1BF2782A)
        self.assertEqual(generated["national_dex_number"], 18)
        self.assertEqual(generated["box_raw"][42], 4)
        self.assertEqual(generated["box_raw"][69], 92)

        drifted = bytearray(self.stage61)
        drifted[0x0803D384 - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "GIFT_STORAGE_CREATEBOXMON_ROM_DRIFT",
        ):
            _gift_storage_validate_create_mon_rom(bytes(drifted))
        drifted = bytearray(self.stage61)
        drifted[0x09FDA160 - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "GIFT_STORAGE_GET_SPECIES_NAME_IMPLEMENTATION_DRIFT",
        ):
            _gift_storage_validate_create_mon_rom(bytes(drifted))

    def test_fossil_prefix_catalog_excludes_impossible_locked_state(self) -> None:
        self.assertEqual(len(FOSSIL_SCENARIO_IDS), 13)
        payloads = [
            _fossil_revival_scenario_payload(scenario_id)
            for scenario_id in FOSSIL_SCENARIO_IDS
        ]
        self.assertEqual({
            (row["revive_state"], row["which_fossil"])
            for row in payloads
        }, {
            (0, 0), (1, 1), (1, 2), (1, 3),
            (2, 1), (2, 2), (2, 3),
        })
        self.assertFalse(any(
            row["revive_state"] == 2 and row["which_fossil"] == 0
            for row in payloads
        ))
        self.assertEqual({
            row["scenario_id"] for row in payloads
            if row["prefix_class"] == "IDLE_AVAILABILITY"
        }, {
            "idle_none", "idle_available_helix",
            "idle_available_dome", "idle_available_amber",
            "idle_available_helix_amber",
            "idle_available_dome_amber",
        })
        terminal = next(
            row for row in payloads
            if row["scenario_id"] == "idle_all_revived"
        )
        self.assertEqual(terminal["prefix_class"], "ALL_REVIVED_TERMINAL")

    def test_runtime_menu67_uses_actual_clean_semantic_source(self) -> None:
        executions, blockers, _graph = self._run_root(FOSSIL_REVIVAL_ROOT)
        self.assertEqual(blockers, [])
        context = executions[0][0]
        self.assertIs(context.clean_rom, context.stage61_rom)
        self.assertIs(context.semantic_source_rom, self.clean)
        rows = _multichoice_rows(context, 67)
        self.assertEqual(len(rows), 2)
        semantic_pointer = rows[0][0]
        drifted = bytearray(self.clean)
        drifted[semantic_pointer - 0x08000000] ^= 1
        forged = replace(context, semantic_source_rom=bytes(drifted))
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "MULTICHOICE_RUNTIME_TEXT_MISMATCH:67:0",
        ):
            _multichoice_rows(forged, 67)

    def _assert_gift_pokedex_projection(self, context, state, persistent) -> None:
        # Species is the resolved givemon INPUT, not the generated mon/dex output.
        # Decode the pinned native species-to-national table independently of
        # _gift_storage_national_dex_number and _gift_storage_pokedex_after.
        transactions = [
            row for row in state.decisions
            if row.get("kind") == "GIFT_STORAGE_TRANSACTION_EXACT"
        ]
        self.assertEqual(len(transactions), 1)
        transaction = transactions[0]
        species = transaction["species"]
        self.assertIs(type(species), int)
        self.assertGreater(species, 0)
        command_offset = int(transaction["instruction_address"], 16) - 0x08000000
        self.assertGreaterEqual(command_offset, 0)
        raw = context.stage61_rom[command_offset:command_offset + 15]
        self.assertEqual(len(raw), 15)
        self.assertEqual(raw[0], 0x79)
        operand = int.from_bytes(raw[1:3], "little")
        if operand < 0x4000:
            self.assertEqual(species, operand)
        table_offset = 0x09F79290 - 0x08000000 + (species - 1) * 2
        table_row = context.stage61_rom[table_offset:table_offset + 2]
        self.assertEqual(len(table_row), 2)
        national = int.from_bytes(table_row, "little")
        payload = _gift_storage_scenario_payload(state.gift_storage_scenario_id)
        self.assertEqual(transaction["result_value"], payload["expected_result"])
        self.assertEqual(state.gift_storage_national_dex_number, national)
        success = payload["expected_result"] in (0, 1)
        expected_writes = set()
        owner_ranges = []
        for field, block, base in (
            ("owned", "SB2", 0x28), ("seen", "SB2", 0x5C),
            ("seen1", "SB1", 0x5F8), ("seen2", "SB1", 0x3A18),
        ):
            before = bytes.fromhex(payload[f"pokedex_{field}_raw_hex"])
            self.assertIn(national, range(1, len(before) * 8 + 1))
            after = bytearray(before)
            if success:
                after[(national - 1) // 8] |= 1 << ((national - 1) % 8)
            self.assertEqual(
                getattr(state, f"gift_storage_pokedex_{field}_current_hex"),
                after.hex(),
            )
            owner_ranges.append((block, base, base + len(before)))
            expected_writes.update(
                (block, base + index, value)
                for index, value in enumerate(after) if before[index] != value
            )
        actual_writes = [
            (row["block"], row["offset"], row["value"])
            for row in persistent
            if any(row["block"] == block and start <= row["offset"] < end
                   for block, start, end in owner_ranges)
        ]
        self.assertEqual(len(actual_writes), len(expected_writes))
        self.assertEqual(set(actual_writes), expected_writes)

    def test_gift_dex_projection_uses_each_roots_input_species(self) -> None:
        from tools.stage61_interaction_oracle import (
            _runner_effect_rows, _runner_persistent_postconditions,
        )
        for root in sorted(GIFT_STORAGE_ROOTS):
            with self.subTest(root=f"0x{root:08X}"):
                executions, blockers, _graph = self._run_root(root)
                self.assertEqual(blockers, [])
                gift_executions = [
                    (context, state) for context, state in executions
                    if state.gift_storage_rng_consumed
                ]
                self.assertTrue(gift_executions)
                for context, state in gift_executions:
                    persistent = _runner_persistent_postconditions(
                        state, _runner_effect_rows(state, None),
                    )
                    self._assert_gift_pokedex_projection(context, state, persistent)

    def test_gift_dex_projection_rejects_missing_or_wrong_native_write(self) -> None:
        from tools.stage61_interaction_oracle import (
            _runner_effect_rows, _runner_persistent_postconditions,
        )
        context, state = next(
            (context, state) for context, state in self._run_root(0x081859FA)[0]
            if state.gift_storage_rng_consumed
            and state.gift_storage_scenario_id == "party_space"
        )
        persistent = _runner_persistent_postconditions(
            state, _runner_effect_rows(state, None),
        )
        self._assert_gift_pokedex_projection(context, state, persistent)
        owned_index = next(
            index for index, row in enumerate(persistent)
            if row["block"] == "SB2" and 0x28 <= row["offset"] < 0x5C
        )
        for mutation in ("missing_owner", "wrong_bit", "wrong_offset", "duplicate"):
            forged = deepcopy(persistent)
            if mutation == "missing_owner":
                del forged[owned_index]
            elif mutation == "wrong_bit":
                forged[owned_index]["value"] ^= 1
            elif mutation == "wrong_offset":
                forged[owned_index]["offset"] += 1
            else:
                forged.append(deepcopy(forged[owned_index]))
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                self._assert_gift_pokedex_projection(context, state, forged)

    def test_all_fourteen_roots_close_under_cap_with_exact_transactions(
        self,
    ) -> None:
        self.assertEqual(set(self.MAP_SECTIONS), GIFT_STORAGE_ROOTS)
        for root in sorted(GIFT_STORAGE_ROOTS):
            with self.subTest(root=f"0x{root:08X}"):
                executions, blockers, graph = self._run_root(root)
                self.assertEqual(blockers, [])
                self.assertTrue(executions)
                self.assertLess(len(executions), MAX_EXECUTION_PATHS)
                commands = [
                    instruction.raw
                    for address in graph.distances(root)
                    for instruction in graph.nodes[address].instructions
                    if instruction.opcode == 0x79
                ]
                self.assertTrue(commands)
                self.assertTrue(all(
                    len(raw) == 15 and raw[10:15] == bytes(5)
                    for raw in commands
                ))
                gift_states = [
                    state for _context, state in executions
                    if state.gift_storage_rng_consumed
                ]
                self.assertTrue(gift_states)
                self.assertEqual({
                    state.gift_storage_scenario_id for state in gift_states
                }, set(GIFT_STORAGE_EXECUTOR_SCENARIO_IDS))
                self.assertEqual({
                    state.gift_storage_map_section_id for state in gift_states
                }, {self.MAP_SECTIONS[root]})
                for context, state in executions:
                    if not state.gift_storage_rng_consumed:
                        continue
                    required = _runner_required_postconditions(context, state)
                    self.assertEqual(
                        state.gift_storage_rng_current, 0x1BF2782A,
                    )
                    if state.gift_storage_scenario_id == "party_space":
                        self.assertIsNotNone(required["party"])
                    elif state.gift_storage_scenario_id == "storage_full":
                        self.assertIsNone(required["party"])
                        self.assertIsNone(required["storage"])
                    else:
                        self.assertIsNotNone(required["storage"])
                    self._assert_gift_pokedex_projection(
                        context, state, required["persistent"],
                    )
        fossil_executions = self._run_root(FOSSIL_REVIVAL_ROOT)[0]
        self.assertEqual({
            state.fossil_revival_scenario_id
            for _context, state in fossil_executions
        }, set(FOSSIL_SCENARIO_IDS))


class Stage61RuntimeAggregateCapFocusedTests(unittest.TestCase):
    @staticmethod
    def _run_count(count: int) -> tuple[list, list]:
        root = 0x08123456
        owner = {"owner_id": "OBJECT:001/001:000", "root": root}
        states = [_Execution(pc=root + index + 1) for index in range(count)]

        with patch(
            "tools.stage61_interaction_oracle._event_design_rank_call_addresses",
            return_value=[],
        ), patch(
            "tools.stage61_interaction_oracle._static_control_domains",
            return_value=([], []),
        ), patch(
            "tools.stage61_interaction_oracle._runtime_context",
            return_value=SimpleNamespace(),
        ), patch(
            "tools.stage61_interaction_oracle._execute",
            return_value=states,
        ), patch(
            "tools.stage61_interaction_oracle._runtime_execution_identity",
            side_effect=lambda state: f"path-{state.pc:08X}",
        ):
            return _runtime_execute_with_seed_discovery(
                b"", b"", b"", {}, owner, SimpleNamespace(), {}, {}, {},
                shared_script_bytes=frozenset(), shared_root_plan={},
            )

    def test_4096_completed_paths_are_allowed(self) -> None:
        executions, blockers = self._run_count(MAX_EXECUTION_PATHS)
        self.assertEqual(len(executions), MAX_EXECUTION_PATHS)
        self.assertEqual(blockers, [])

    def test_4097_discards_partial_results_and_fails_closed(self) -> None:
        executions, blockers = self._run_count(MAX_EXECUTION_PATHS + 1)
        self.assertEqual(executions, [])
        self.assertEqual(len(blockers), 1)
        self.assertEqual(blockers[0], {
            "owner_id": "OBJECT:001/001:000",
            "runtime_root": "0x08123456",
            "physical_execution_root": "0x08123456",
            "kind": "RUNTIME_ROOT_EXECUTION_PATH_CAP_EXCEEDED",
            "completed_path_count": MAX_EXECUTION_PATHS + 1,
            "maximum_path_count": MAX_EXECUTION_PATHS,
            "partial_results_discarded": True,
        })


class Stage61P02RunnerPostconditionFocusedTests(unittest.TestCase):
    REQUIRED_KEYS = {
        "flags", "engine_special_flags", "vars", "items", "trainers",
        "objects", "warp", "battle", "money", "coins", "party",
        "storage", "berry_powder", "persistent",
    }

    def test_public_sequence_keeps_post_battle_continuation(self) -> None:
        continuation = {
            "phase": "POST_BATTLE_CONTINUATION",
            "runner_capture_required": True,
            "resume_kind": "EXPLICIT", "resume_pc": "0x08000012",
            "tokens": ["A"], "visible_printers": [],
            "decision_trace": [], "effect_relations": [],
            "chained_battles": [],
            "field_terminal_kind": "FIELD_RELEASE",
        }
        projected = _runner_sequence_lifecycle_projection({
            "effect_contract": {
                "required_final": {"flags": []},
                "battle_start_required_postconditions": None,
                "post_battle_continuation": continuation,
            },
        })
        self.assertEqual(projected["post_battle_continuation"], continuation)
        continuation["tokens"].append("B")
        self.assertEqual(
            projected["post_battle_continuation"]["tokens"], ["A"],
        )

    def test_post_battle_resume_kind_is_source_exact(self) -> None:
        common = {
            "battle_start_effects": [], "battle_start_tokens": [],
            "battle_start_printer_count": 0,
            "battle_start_decision_count": 0,
        }
        for trainer_id, resume_pc, kind, rendered_pc in (
            (7, None, "STANDARD", None),
            (7, 0x08000120, "EXPLICIT", "0x08000120"),
            (None, 0x08000140, "NEXT_PC", "0x08000140"),
        ):
            with self.subTest(kind=kind):
                contract = _post_battle_continuation_contract(_Execution(
                    pc=0x08000000, battle_trainer_id=trainer_id,
                    battle_resume_pc=resume_pc, **common,
                ))
                self.assertEqual(contract["resume_kind"], kind)
                self.assertEqual(contract["resume_pc"], rendered_pc)
        trainer_next = _post_battle_continuation_contract(_Execution(
            pc=0x08000000, battle_trainer_id=7,
            battle_resume_pc=0x08000160, battle_resume_kind="NEXT_PC",
            **common,
        ))
        self.assertEqual(trainer_next["resume_kind"], "NEXT_PC")
        self.assertEqual(trainer_next["resume_pc"], "0x08000160")
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "POST_BATTLE_RESUME_SOURCE_REQUIRED",
        ):
            _post_battle_continuation_contract(_Execution(
                pc=0x08000000, battle_trainer_id=None,
                battle_resume_pc=None, **common,
            ))

    @staticmethod
    def _context(
        rom: bytes = b"\x00" * 0x400,
        *, script_size: int = 1,
        case: dict | None = None,
    ) -> _Context:
        root = 0x08000000
        value = {
            "case_id": "focused-p02-case",
            "owner_key": "OBJECT:000/000:001",
            "state": {
                "flags": [], "vars": [], "items": [], "trainers": [],
            },
            "control_requirements": {"external": [], "internal": []},
            "expected_object_visible": True,
        }
        if case:
            value.update(deepcopy(case))
        return _Context(
            clean_rom=rom, stage61_rom=rom, semantic_report={},
            npc={"npc_id": value["owner_key"], "local_id": 1, "flag": 0},
            case=value, root=root, target_root=root, execution_root=root,
            root_plan={"references": []}, fixture=DEFAULT_FIXTURE,
            flag_mapping={}, var_mapping={}, text_assets={},
            text_provenance="SYNTHETIC_SOURCE_RAW", abi_index={},
            instruction_repairs={}, source_suppression_contract=None,
            stage61_script_bytes=frozenset(range(root, root + script_size)),
        )

    def test_relocated_rematch_uses_exact_changekit_alias_target(self) -> None:
        instruction = 0x09420000
        local_id = 11
        trainer_id = 1027
        raw = (
            bytes.fromhex("5c05") + trainer_id.to_bytes(2, "little")
            + bytes(2)
            + (0x09364000).to_bytes(4, "little")
            + (0x09364100).to_bytes(4, "little")
        )
        context = SimpleNamespace(
            clean_rom=b"",
            npc={"local_id": local_id},
            case={
                "catalog_branch": "TRAINER_PRE_BATTLE",
                "state": {"trainers": []},
                "control_requirements": {"external": [{
                    "kind": "REMATCH_STATE", "id": local_id,
                    "value": True,
                }]},
            },
            trainer_rematch_model={
                "contextual_by_data_address": {
                    instruction + 1: {
                        "data_address": instruction + 1,
                        "source_data_address": 0x0936B5E4,
                        "stock_trainer_id": trainer_id,
                        "target_trainer_id": trainer_id,
                        "trainerbattle_type": 5,
                        "encounter_key": "ENC_TOHOKU_REF_0007",
                        "intro_branch": "NORMAL_INTRO",
                        "relation":
                            "STAGE61_RELOCATED_COMMAND_ALIAS_EXACT",
                    },
                },
                "stock_rows": (),
                "evidence": {"kind": "SYNTHETIC_EXACT_ALIAS"},
            },
        )
        state = _Execution(
            pc=instruction, execution_trace=[instruction],
            current_instruction_address=instruction, current_opcode=0x5C,
        )
        with patch(
            "tools.stage61_interaction_oracle._append_message",
            return_value=None,
        ):
            _execute_trainerbattle(context, state, instruction, raw)
        self.assertEqual(state.battle_trainer_id, trainer_id)
        self.assertEqual(
            state.decisions[0]["effective_trainer_id"], trainer_id,
        )
        self.assertEqual(
            state.decisions[0]["rematch_resolution"]["relation"],
            "STAGE61_RELOCATED_COMMAND_ALIAS_EXACT",
        )
        self.assertEqual(
            [effect["owner"] for effect in state.effects],
            [f"TRAINER:{trainer_id}", f"TRAINER:{trainer_id}"],
        )
        self.assertEqual(
            [effect["domain"] for effect in state.battle_start_effects],
            ["battle"],
        )

    @staticmethod
    def _rematch_ready_entry() -> dict:
        return {
            "symbol": "ShouldTryRematchBattle",
            "execution": "SYNC",
            "input_controls": [],
            "effects": [],
            "source": {
                "path": "vendor/upstream/pokefirered/src/vs_seeker.c",
                "definition_line": 1013,
                "sha256": (
                    "35fae0cd75989534e25c463a21e1c5c74f5688b57d8b73b2ee58e03c5db4509d"
                ),
            },
            "rom_binding": {
                "address": "0x0810D824", "byte_length": 0x34,
                "sha256": (
                    "b9daa41a1bebbb3743100230b48c69df873196fc9ed260efb6c0099271e57b8c"
                ),
            },
            "result_contract": {
                "specialvar_return": {"candidate_values": [0, 1]},
            },
        }

    @staticmethod
    def _rematch_ready_state(trainer_id: int) -> _Execution:
        instruction = 0x0819720B
        return _Execution(
            pc=instruction,
            execution_trace=[instruction],
            current_instruction_address=instruction,
            current_opcode=0x26,
            decisions=[{
                "kind": "TRAINERBATTLE_POST",
                "trainer_id": trainer_id,
                "trainerbattle_type": 0,
            }],
        )

    @staticmethod
    def _rematch_ready_context(
        *, local_id: int, stock_rows: tuple[tuple[int, ...], ...],
        external: list[dict],
    ) -> SimpleNamespace:
        return SimpleNamespace(
            npc={"local_id": local_id},
            case={"control_requirements": {"external": external}},
            trainer_rematch_model={
                "stock_rows": stock_rows,
                "evidence": {"kind": "SYNTHETIC_PINNED_REMATCH_TABLE"},
            },
            var_mapping={},
        )

    def test_rematch_ready_rejects_non_stock_trainer_without_byte_read(
        self,
    ) -> None:
        instruction = 0x0819720B
        state = self._rematch_ready_state(258)
        context = self._rematch_ready_context(
            local_id=4,
            # A rematch-column match is deliberately not a base-column match.
            stock_rows=((1, 258, 3, 4, 5, 6, 0, 0),),
            external=[],
        )
        branches = _execute_pinned_should_try_rematch_battle(
            context, state, instruction, bytes.fromhex("260d803900"),
            "SPECIAL:0039:0x0810D825", self._rematch_ready_entry(),
        )
        self.assertEqual(len(branches), 1)
        branch = branches[0]
        self.assertEqual(branch.vars[0x800D], 0)
        self.assertEqual(branch.abi_control_reads, [])
        self.assertEqual(branch.decisions[-1]["stock_membership"], False)
        self.assertEqual(branch.decisions[-1]["local_id"], None)

    def test_rematch_ready_reads_physical_local_id_and_falls_back_to_flag(
        self,
    ) -> None:
        instruction = 0x0819720B
        trainer_id = 258
        local_id = 11
        state = self._rematch_ready_state(trainer_id)
        context = self._rematch_ready_context(
            local_id=local_id,
            stock_rows=((trainer_id, 2, 3, 4, 5, 6, 0, 0),),
            external=[
                {"kind": "REMATCH_STATE", "id": 0, "value": True},
                {"kind": "REMATCH_STATE", "id": local_id, "value": False},
            ],
        )
        branches = _execute_pinned_should_try_rematch_battle(
            context, state, instruction, bytes.fromhex("260d803900"),
            "SPECIAL:0039:0x0810D825", self._rematch_ready_entry(),
        )
        self.assertEqual(len(branches), 1)
        branch = branches[0]
        self.assertEqual(branch.vars[0x800D], 1)
        self.assertEqual(branch.abi_control_reads, [{
            "kind": "REMATCH_STATE",
            "owner": f"LOCAL_OBJECT:{local_id}",
            "candidate_values": [False, True],
            "required_value": False,
            "relation": "SAVEBLOCK1_TRAINER_REMATCH_BYTE_NONZERO",
            "save_block1_offset": 0x063A + local_id,
            "instruction_address": f"0x{instruction:08X}",
        }])
        self.assertEqual(branch.decisions[-1]["local_id"], local_id)
        self.assertEqual(
            branch.decisions[-1]["trainer_flag_fallback_checked"], True,
        )
        self.assertEqual(
            branch.decisions[-1]["trainer_already_fought"], True,
        )
        self.assertEqual(branch.decisions[-1]["result_value"], 1)

    def test_pc_item_add_projects_exact_saveblock1_bytes_not_bag(self) -> None:
        context = self._context()
        state = _Execution(pc=0x08000000, terminated=True)
        state.effects = [{
            "domain": "items", "owner": "PC_ITEM:4660",
            "relation": "ADD_EXACT_QUANTITY",
            "instruction_address": "0x08000000",
            "execution_trace_index": 0, "group_member_ordinal": 0,
            "opcode": "0x49", "abi_key": None, "quantity": 5,
        }]
        state.abi_control_reads = [{
            "kind": "PC_CAPACITY", "owner": "ITEM:4660",
            "candidate_values": [0, 1], "required_value": 1,
            "relation": "ADD_PC_ITEM_CAPACITY", "quantity": 5,
            "instruction_address": "0x08000000",
        }]
        required = _runner_required_postconditions(context, state)
        self.assertEqual(set(required), self.REQUIRED_KEYS)
        self.assertEqual(required["items"], [])
        self.assertEqual(required["persistent"], [
            {"block": "SB1", "offset": PC_ITEMS_SAVEBLOCK1_OFFSET,
             "value": 0x34},
            {"block": "SB1", "offset": PC_ITEMS_SAVEBLOCK1_OFFSET + 1,
             "value": 0x12},
            {"block": "SB1", "offset": PC_ITEMS_SAVEBLOCK1_OFFSET + 2,
             "value": 5},
        ])
        families, allowed = _runner_allowed_post_effect_union(
            context, [state],
        )
        self.assertEqual(families, ["PERSISTENT"])
        self.assertEqual(allowed["items"], [])
        self.assertEqual(allowed["persistent"], [{
            "block": "SB1", "start": PC_ITEMS_SAVEBLOCK1_OFFSET,
            "end": PC_ITEMS_SAVEBLOCK1_OFFSET
                + PC_ITEM_SLOT_COUNT * PC_ITEM_SLOT_SIZE,
            "meaning": "SaveBlock1.pcItems exact 30-slot owner",
        }])

    def test_berry_powder_postcondition_is_correlated_and_changed_only(
        self,
    ) -> None:
        context = self._context()

        def state(*, before: int, cost: int) -> _Execution:
            success = before >= cost
            after = before - cost if success else before
            return _Execution(
                pc=0x08000000, terminated=True,
                berry_powder_initial=before,
                berry_powder_current=after,
                effects=[{
                    "domain": "berry_powder", "owner": "BERRY_POWDER:0",
                    "relation": "EXACT_FINAL", "before": before,
                    "after": after, "cost": cost, "success": success,
                    "source_return_value": int(success),
                    "special_return_discarded": True,
                    "instruction_address": "0x08000000",
                    "execution_trace_index": 0,
                    "group_member_ordinal": 0,
                    "opcode": "0x25", "abi_key": "SPECIAL:019F",
                }],
            )

        insufficient = state(before=49, cost=50)
        purchased = state(before=50, cost=50)
        self.assertIsNone(
            _runner_required_postconditions(
                context, insufficient,
            )["berry_powder"]
        )
        self.assertEqual(
            _runner_required_postconditions(
                context, purchased,
            )["berry_powder"],
            0,
        )
        families, allowed = _runner_allowed_post_effect_union(
            context, [insufficient, purchased],
        )
        self.assertIn("BERRY_POWDER", families)
        self.assertEqual(allowed["berry_powder"], [{
            "owner": "BERRY_POWDER:0",
            "meaning": "source-defined exact decrypted Berry Powder delta",
            "operations": ["DECREASE"],
        }])

        drifted = state(before=50, cost=50)
        drifted.effects[0]["before"] = 49
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "BERRY_POWDER effect不正",
        ):
            _runner_required_postconditions(context, drifted)

    def test_checkpcitem_branches_independently_of_bag_state(self) -> None:
        script = bytes.fromhex("4a0100010002")
        context = self._context(
            script + bytes(0x100 - len(script)),
            script_size=len(script),
            case={
                "state": {
                    "flags": [], "vars": [],
                    "items": [{"id": 1, "count": 999}],
                    "trainers": [],
                },
            },
        )
        states = _execute(context)
        self.assertEqual(
            sorted(state.vars[0x800D] for state in states), [0, 1],
        )
        self.assertEqual(
            {row["required_value"] for state in states
             for row in state.abi_control_reads
             if row["kind"] == "PC_ITEM"},
            {0, 1},
        )
        self.assertFalse(any(
            effect["domain"] == "items" for state in states
            for effect in state.effects
        ))

    def test_trainer_battle_start_and_final_are_separate_exact_snapshots(
        self,
    ) -> None:
        table = 0x08000100
        party = 0x08000300
        trainer_id = 7
        rom = bytearray(0x500)
        record = table - 0x08000000 + trainer_id * 0x20
        rom[record] = 0
        rom[record + 0x18] = 1
        rom[record + 0x1C:record + 0x20] = party.to_bytes(4, "little")
        rom[party - 0x08000000 + 4:party - 0x08000000 + 6] = \
            (25).to_bytes(2, "little")
        context = self._context(bytes(rom))
        context = replace(context, case={
            **dict(context.case),
            "state": {
                "flags": [], "vars": [], "items": [],
                "trainers": [{"id": trainer_id, "defeated": False}],
            },
        })
        battle = {
            "domain": "battle", "owner": f"TRAINER:{trainer_id}",
            "relation": "BATTLE_STARTS_WITH_TRAINER",
            "instruction_address": "0x08000000",
            "execution_trace_index": 0, "group_member_ordinal": 0,
            "opcode": "0x5C", "abi_key": None,
        }
        defeated = {
            "domain": "trainers", "owner": f"TRAINER:{trainer_id}",
            "relation": "EXACT_FINAL", "after": True,
            "instruction_address": "0x08000000",
            "execution_trace_index": 0, "group_member_ordinal": 1,
            "opcode": "0x5C", "abi_key": None,
        }
        state = _Execution(
            pc=0x08000000, effects=[battle, defeated], terminated=True,
            battle_start_effects=[battle], battle_start_tokens=["A"],
            battle_start_printer_count=0, battle_start_decision_count=0,
            battle_start_var_write_count=0, battle_start_trace_count=1,
            battle_trainer_id=trainer_id,
        )
        with patch(
            "tools.stage61_interaction_oracle.TRAINER_TABLE_ADDRESS", table,
        ):
            start = _runner_battle_start_required_postconditions(
                context, state,
            )
            final = _runner_required_postconditions(context, state)
        self.assertEqual(start["battle"], {
            "active": True, "trainer_opponent": trainer_id,
            "enemy_species": 25, "outcome": 0,
        })
        self.assertEqual(start["trainers"], [])
        self.assertIsNone(final["battle"])
        self.assertEqual(final["trainers"], [{
            "id": trainer_id, "defeated": True,
        }])

    def test_explicit_trainer_victory_continuation_keeps_followup_effects(
        self,
    ) -> None:
        root = 0x08000000
        trainer_id = 7
        continuation = root + 18
        command = (
            bytes.fromhex("5c01") + trainer_id.to_bytes(2, "little")
            + (1).to_bytes(2, "little")
            + (root + 0x80).to_bytes(4, "little")
            + (root + 0x90).to_bytes(4, "little")
            + continuation.to_bytes(4, "little")
        )
        tail = bytes.fromhex("2900016c02")
        rom = command + tail + bytes(0x100 - len(command) - len(tail))
        context = self._context(
            rom, script_size=len(command) + len(tail),
            case={
                "catalog_branch": "TRAINER_PRE_BATTLE",
                "state": {
                    "flags": [], "vars": [], "items": [],
                    "trainers": [{"id": trainer_id, "defeated": False}],
                },
            },
        )
        with patch(
            "tools.stage61_interaction_oracle._append_message",
            return_value=None,
        ):
            states = _execute(context)
        self.assertEqual(len(states), 1)
        state = states[0]
        self.assertTrue(state.terminated)
        self.assertEqual(state.terminal_kind, "FIELD_RELEASE")
        self.assertEqual(state.battle_resume_pc, continuation)
        self.assertEqual(
            _post_battle_continuation_contract(state)["resume_kind"],
            "EXPLICIT",
        )
        self.assertEqual(
            _post_battle_continuation_contract(state)["resume_pc"],
            f"0x{continuation:08X}",
        )
        self.assertEqual(
            [effect["domain"] for effect in state.battle_start_effects],
            ["battle"],
        )
        self.assertTrue(any(
            effect["domain"] == "trainers" and effect["after"] is True
            for effect in state.effects
        ))
        self.assertTrue(any(
            effect["domain"] == "flags" and effect["owner"] == "FLAG:0x0100"
            for effect in state.effects
        ))

    def test_explicit_victory_continuation_keeps_second_battle_phase(
        self,
    ) -> None:
        root = 0x08000000
        first_trainer = 113
        second_trainer = 171
        continuation = root + 18
        first = (
            bytes.fromhex("5c02")
            + first_trainer.to_bytes(2, "little")
            + (0).to_bytes(2, "little")
            + (root + 0x80).to_bytes(4, "little")
            + (root + 0x90).to_bytes(4, "little")
            + continuation.to_bytes(4, "little")
        )
        second = (
            bytes.fromhex("5c03")
            + second_trainer.to_bytes(2, "little")
            + (0).to_bytes(2, "little")
            + (root + 0xA0).to_bytes(4, "little")
        )
        terminal = bytes((0x02,))
        rom = first + second + terminal \
            + bytes(0x200 - len(first) - len(second) - len(terminal))
        context = self._context(
            rom, script_size=len(first) + len(second) + len(terminal),
            case={
                "catalog_branch": "TRAINER_PRE_BATTLE",
                "state": {
                    "flags": [], "vars": [], "items": [],
                    "trainers": [{
                        "id": first_trainer, "defeated": False,
                    }],
                },
            },
        )
        with patch(
            "tools.stage61_interaction_oracle._append_message",
            return_value=None,
        ):
            states = _execute(context)
        self.assertEqual(len(states), 1)
        state = states[0]
        self.assertEqual(
            [phase["trainer_id"] for phase in state.battle_phases],
            [first_trainer, second_trainer],
        )
        continuation_contract = _post_battle_continuation_contract(state)
        self.assertEqual(continuation_contract["chained_battles"], [{
            "phase_index": 2,
            "battle_kind": "TRAINER",
            "trainer_id": second_trainer,
            "start_instruction_address": f"0x{continuation:08X}",
            "resume_kind": "NEXT_PC",
            "resume_pc": f"0x{continuation + len(second):08X}",
        }])
        with patch(
            "tools.stage61_interaction_oracle._runner_trainer_lead_species",
            return_value=25,
        ):
            start = _runner_battle_start_required_postconditions(
                context, state,
            )
            final = _runner_required_postconditions(context, state)
        self.assertEqual(start["battle"]["trainer_opponent"], first_trainer)
        self.assertEqual(final["trainers"], [
            {"id": first_trainer, "defeated": True},
            {"id": second_trainer, "defeated": True},
        ])
        self.assertIsNone(final["battle"])

    def test_build_case_oracle_wires_strict_sequence_and_runner_maps(self) -> None:
        context = self._context(b"\x02" + b"\x00" * 0xFF)
        state = _Execution(
            pc=0x08000000, terminated=True,
            execution_trace=[0x08000000],
        )
        with patch(
            "tools.stage61_interaction_oracle._validate_inputs",
            return_value=context,
        ), patch(
            "tools.stage61_interaction_oracle._execute", return_value=[state],
        ):
            output = build_case_oracle(b"", b"", {}, {}, context.case)
        sequence = output["input_sequences"][0]
        sequence_id = sequence["sequence_id"]
        self.assertEqual(set(sequence["required_postconditions"]),
                         self.REQUIRED_KEYS)
        self.assertIsNone(sequence["battle_start_required_postconditions"])
        self.assertNotIn("required_postconditions", output)
        self.assertEqual(
            output["required_postconditions_by_sequence"][sequence_id],
            sequence["required_postconditions"],
        )
        self.assertEqual(
            output["battle_start_required_postconditions"][sequence_id],
            sequence["battle_start_required_postconditions"],
        )
        self.assertEqual(
            output["runner_contract"]["input_sequences"],
            output["input_sequences"],
        )
        self.assertEqual(output["runner_contract"]["control_requirements"], {
            "external": [], "internal": [],
        })


class Stage61RuinSealPrefixFocusedTests(unittest.TestCase):
    @staticmethod
    def _graph(root: int) -> SimpleNamespace:
        identifiers = list(RUIN_SEAL_FLAGS)
        if root == RUIN_SEAL_OBJECT_ROOT:
            identifiers.append(RUIN_SEAL_COMPLETION_FLAG)
        instructions = [
            SimpleNamespace(
                opcode=0x2B,
                raw=b"\x2B" + identifier.to_bytes(2, "little"),
                address=root + index * 3,
            )
            for index, identifier in enumerate(identifiers)
        ]
        return SimpleNamespace(
            clean_rom=b"", nodes={root: SimpleNamespace(
                instructions=instructions,
            )}, distances=lambda _root: [root],
        )

    def test_root_domains_are_one_correlated_prefix_not_flag_product(self) -> None:
        for root, expected_count in (
            (RUIN_SEAL_OBJECT_ROOT, 16),
            (RUIN_SEAL_COORD_ROOT, 15),
        ):
            with self.subTest(root=f"0x{root:08X}"):
                domains, blockers = _static_control_domains(
                    self._graph(root), root,
                )
                self.assertEqual(blockers, [])
                self.assertEqual(len(domains), 1)
                self.assertEqual(domains[0]["kind"], RUIN_SEAL_PREFIX_KIND)
                self.assertEqual(
                    set(domains[0]["candidate_values"]),
                    set(RUIN_SEAL_SCENARIO_IDS[root]),
                )
                self.assertEqual(len(domains[0]["candidate_values"]), expected_count)

    def test_prefix_payloads_are_monotonic_and_completion_is_last(self) -> None:
        for root, scenarios in RUIN_SEAL_SCENARIO_IDS.items():
            for scenario_id in scenarios:
                payload = _ruin_seal_scenario_payload(root, scenario_id)
                seals = [row["value"] for row in payload["flags"][:14]]
                self.assertFalse(any(
                    not seals[index] and any(seals[index + 1:])
                    for index in range(14)
                ))
                if payload["completed"] is True:
                    self.assertTrue(payload["all_seals"])
                    self.assertEqual(scenario_id, "completed")
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "RUIN_SEAL_SCENARIO_INVALID",
        ):
            _ruin_seal_scenario_payload(
                RUIN_SEAL_OBJECT_ROOT, "completed_with_missing_03",
            )

    def test_flag_readback_uses_one_scenario_and_one_external_row(self) -> None:
        context = SimpleNamespace(
            target_root=RUIN_SEAL_OBJECT_ROOT,
            flag_mapping={},
            case={"control_requirements": {"external": [{
                "kind": RUIN_SEAL_PREFIX_KIND,
                "id": 0,
                "value": "missing_03",
            }]}},
        )
        state = _Execution(pc=RUIN_SEAL_OBJECT_ROOT)
        observed = [
            _flag_get(context, state, identifier, RUIN_SEAL_OBJECT_ROOT)
            for identifier in (*RUIN_SEAL_FLAGS, RUIN_SEAL_COMPLETION_FLAG)
        ]
        self.assertEqual(observed[:4], [True, True, True, False])
        self.assertFalse(any(observed[3:]))
        self.assertEqual(state.ruin_seal_scenario_id, "missing_03")
        self.assertEqual(len(state.abi_control_reads), 1)
        self.assertEqual(state.control_reads, [])

    def test_materialization_keeps_exact_flag_readback_and_content_id(self) -> None:
        fixtures: dict[str, dict] = {}
        row = {
            "kind": RUIN_SEAL_PREFIX_KIND,
            "id": 0,
            "owner": f"RUIN_SEAL_PREFIX:0x{RUIN_SEAL_OBJECT_ROOT:08X}",
            "candidate_values": sorted(
                RUIN_SEAL_SCENARIO_IDS[RUIN_SEAL_OBJECT_ROOT]
            ),
            "required_value": "completed",
            "relation": RUIN_SEAL_PREFIX_RELATION,
        }
        projected = _materialize_control_requirement(
            (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes(),
            row, owner_keys=["OBJECT:031/001:000"],
            fixtures=fixtures,
        )
        self.assertIsNotNone(projected)
        self.assertEqual(projected["value"]["scenario_id"], "completed")
        self.assertTrue(projected["value"]["all_seals"])
        self.assertTrue(projected["value"]["completed"])
        self.assertEqual(len(projected["value"]["flag_values"]), 15)
        self.assertEqual(projected["fixture_keys"], [
            projected["value"]["layout_ref"],
        ])
        self.assertEqual(set(fixtures), set(projected["fixture_keys"]))
        drifted = bytearray(
            (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes()
        )
        drifted[RUIN_SEAL_OBJECT_ROOT - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage61InteractionOracleError, "RUIN_SEAL_ROOT_SOURCE_DRIFT",
        ):
            _materialize_control_requirement(
                bytes(drifted), row,
                owner_keys=["OBJECT:031/001:000"], fixtures={},
            )


class Stage61FacilitySessionFocusedTests(unittest.TestCase):
    @staticmethod
    def _graph(root: int) -> SimpleNamespace:
        return SimpleNamespace(
            clean_rom=b"",
            nodes={root: SimpleNamespace(instructions=[])},
            distances=lambda _root: [root],
        )

    def test_domains_are_33_and_shared_10_plus_6_without_product(self) -> None:
        for root, expected_count in (
            (FACILITY_MIRAGE_ROOT, 33),
            (FACILITY_SHARED_ROOT, 16),
        ):
            with self.subTest(root=f"0x{root:08X}"):
                domains, blockers = _static_control_domains(
                    self._graph(root), root,
                )
                self.assertEqual(blockers, [])
                facility = [
                    row for row in domains
                    if row["kind"] == FACILITY_SESSION_KIND
                ]
                self.assertEqual(len(facility), 1)
                candidates = facility[0]["candidate_values"]
                self.assertEqual(len(candidates), expected_count)
                self.assertEqual(candidates, sorted(_facility_scenario_keys(root)))
        shared = _facility_scenario_keys(FACILITY_SHARED_ROOT)
        self.assertEqual(sum(key.startswith("factory/") for key in shared), 10)
        self.assertEqual(sum(key.startswith("codex/") for key in shared), 6)

    def test_payload_matches_helper_trace_sources_and_ewram_identity(self) -> None:
        payload = _facility_scenario_payload("mirage", "complete_tera")
        scenario = FACILITY_SCENARIO_REGISTRIES["mirage"]["complete_tera"]
        binding = FACILITY_SOURCE_BINDINGS["mirage"]
        self.assertEqual(payload["trace_count"], len(scenario.trace))
        self.assertEqual(
            payload["trace_sha256"],
            hashlib.sha256(_effect_test_stable(payload["trace"])).hexdigest(),
        )
        self.assertEqual(payload["source_binding"]["root_address"],
                         f"0x{binding.root_address:08X}")
        self.assertEqual(payload["source_binding"]["scenario_registry"], {
            "path": FACILITY_SESSION_REGISTRY_SOURCE_PATH,
            "sha256": FACILITY_SESSION_REGISTRY_SOURCE_SHA256,
        })
        self.assertEqual(
            hashlib.sha256((
                ROOT / FACILITY_SESSION_REGISTRY_SOURCE_PATH
            ).read_bytes()).hexdigest(),
            FACILITY_SESSION_REGISTRY_SOURCE_SHA256,
        )
        self.assertEqual(payload["source_binding"]["ram_regions"], [{
            "name": region.name,
            "address": f"0x{region.address:08X}",
            "size": region.size,
        } for region in binding.ram_regions])
        for source, row in zip(
            binding.sources, payload["source_binding"]["sources"],
        ):
            self.assertEqual(row, {
                "path": source.path, "sha256": source.sha256,
            })
            self.assertEqual(
                hashlib.sha256((ROOT / source.path).read_bytes()).hexdigest(),
                source.sha256,
            )
        self.assertIsNone(payload["initialization"]["raw_ewram_preimage"])
        self.assertIn(
            "UNDEFINED_RAW_BYTES_FORBIDDEN",
            payload["initialization"]["raw_preimage_policy"],
        )
        runner_abi = runner_control_abi_contract()
        self.assertEqual(
            runner_abi["layouts"]["facility_session"]["scenario_registry"],
            payload["source_binding"]["scenario_registry"],
        )
        self.assertTrue(runner_abi["assertions"][
            "facility_session_raw_ewram_preimage_is_never_fabricated"
        ])
        self.assertTrue(runner_abi["assertions"][
            "facility_session_terminal_cursor_is_exact_or_lifecycle_closed"
        ])
        for family, scenario_id in (
            ("factory", "battle_loss"),
            ("codex", "win_reward"),
        ):
            with self.subTest(family=family):
                family_payload = _facility_scenario_payload(
                    family, scenario_id,
                )
                family_binding = FACILITY_SOURCE_BINDINGS[family]
                self.assertEqual(
                    family_payload["source_binding"]["ram_regions"], [{
                        "name": region.name,
                        "address": f"0x{region.address:08X}",
                        "size": region.size,
                    } for region in family_binding.ram_regions],
                )
                self.assertEqual(
                    family_payload["initialization"]["readback_regions"],
                    family_payload["source_binding"]["ram_regions"],
                )
                self.assertIsNone(
                    family_payload["initialization"]["raw_ewram_preimage"]
                )

    def test_factory_loss_and_prepare_error_keep_exact_terminal_edges(self) -> None:
        loss = _facility_scenario_payload("factory", "battle_loss")
        prepare = _facility_scenario_payload("factory", "prepare_error")
        self.assertEqual(
            (loss["trace"][-1]["operation"],
             loss["trace"][-1]["phase"],
             loss["trace"][-1]["status"],
             loss["trace"][-1]["result"],
             loss["trace"][-1]["active"]),
            ("AfterBattle", 0, 1, 1, False),
        )
        self.assertEqual(
            [(row["operation"], row["phase"], row["status"], row["result"],
              row["active"]) for row in prepare["trace"][-2:]],
            [("PrepareBattle", 3, 0, 0, True),
             ("Abort", 0, 1, 1, False)],
        )
        self.assertNotEqual(loss["trace_sha256"], prepare["trace_sha256"])

    def test_codex_reward_window_is_correlated_until_close(self) -> None:
        payload = _facility_scenario_payload("codex", "win_reward")
        open_rows = [
            row for row in payload["trace"] if row["reward_window"] == 1
        ]
        self.assertEqual(
            [row["operation"] for row in open_rows],
            ["AfterBattleAdapter", "FieldFinishAdapter"],
        )
        self.assertTrue(all(
            row["phase"] == 10 and row["completion_pending"] == 1
            and row["active"] is False and row["reward_result_kind"] == 1
            for row in open_rows
        ))
        self.assertEqual(
            (payload["trace"][-1]["operation"],
             payload["trace"][-1]["reward_window"],
             payload["trace"][-1]["completion_pending"]),
            ("RewardClose", 0, 0),
        )

    def test_mirage_resume_points_match_helper_suffixes(self) -> None:
        payload = _facility_scenario_payload("mirage", "complete_tera")
        self.assertEqual(len(payload["resume_points"]), 28)
        point = payload["resume_points"][21]
        resumed = facility_resume_trace("mirage", "complete_tera", 21)
        suffix = payload["trace"][point["trace_offset"]:]
        self.assertEqual(suffix[0]["operation"], "PrepareBattle")
        self.assertEqual(suffix[0]["battle_index"], 21)
        self.assertEqual(suffix[0]["mechanic"], 4)
        self.assertEqual(point["trace_count"], len(resumed.steps))
        self.assertEqual(
            point["trace_sha256"],
            hashlib.sha256(_effect_test_stable(suffix)).hexdigest(),
        )

    def test_materialization_registers_one_exact_source_bound_fixture(self) -> None:
        fixtures: dict[str, dict] = {}
        projected = _materialize_control_requirement(
            b"", {
                "kind": FACILITY_SESSION_KIND,
                "id": 1,
                "owner": "FACILITY_SESSION:FACTORY_OR_CODEX",
                "candidate_values": sorted(
                    _facility_scenario_keys(FACILITY_SHARED_ROOT)
                ),
                "required_value": "codex/win_reward",
                "relation": FACILITY_SESSION_RELATION,
            },
            owner_keys=["OBJECT:TEST"], fixtures=fixtures,
        )
        self.assertIsNotNone(projected)
        assert projected is not None
        self.assertEqual(projected["value"]["scenario_key"],
                         "codex/win_reward")
        self.assertEqual(projected["value"]["reception_branch"], "CODEX")
        self.assertEqual(projected["fixture_keys"], [
            projected["value"]["layout_ref"],
        ])
        self.assertEqual(set(fixtures), set(projected["fixture_keys"]))

    def test_native_execution_consumes_one_scenario_trace_cursor(self) -> None:
        context = SimpleNamespace(
            target_root=FACILITY_SHARED_ROOT,
            var_mapping={},
            case={"control_requirements": {"external": [{
                "kind": FACILITY_SESSION_KIND,
                "id": 1,
                "value": "factory/battle_loss",
            }]}},
        )
        instruction = FACILITY_SHARED_ROOT
        state = _Execution(
            pc=instruction,
            execution_trace=[instruction],
            current_instruction_address=instruction,
            current_opcode=0x23,
            current_abi_key="NATIVE:RECEPTION",
        )
        branches = _fork_facility_session_native(
            context, state, instruction, b"\x23\x00\x00\x00\x00",
            "NATIVE:RECEPTION", {
                "symbol": "FactoryHighModesV2_FieldReception",
                "effects": [],
            },
        )
        self.assertEqual(len(branches), 1)
        branch = branches[0]
        self.assertEqual(branch.vars[0x800D], 11)
        self.assertEqual(branch.facility_trace_cursor, 2)
        self.assertEqual(len(branch.abi_control_reads), 1)
        next_instruction = instruction + 5
        branch.execution_trace.append(next_instruction)
        branch.current_instruction_address = next_instruction
        branch.current_opcode = 0x23
        branch.current_abi_key = "NATIVE:ENTER"
        next_branches = _fork_facility_session_native(
            context, branch, next_instruction, b"\x23\x00\x00\x00\x00",
            "NATIVE:ENTER", {
                "symbol": "FactoryHighModesV2_EnterSelected", "effects": [],
            },
        )
        self.assertEqual(len(next_branches), 1)
        self.assertEqual(next_branches[0].vars[0x800D], 1)
        self.assertEqual(next_branches[0].facility_trace_cursor, 3)
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "FACILITY_SESSION_NATIVE_FAMILY_MISMATCH",
        ):
            _fork_facility_session_native(
                context, branch, next_instruction,
                b"\x23\x00\x00\x00\x00", "NATIVE:CODEX", {
                    "symbol": "CodexBattleRuntime_FieldPrepareBattle",
                    "effects": [],
                },
            )

    def test_pre_session_abort_does_not_consume_scenario_control(self) -> None:
        context = SimpleNamespace(
            target_root=FACILITY_MIRAGE_ROOT,
            var_mapping={},
            case={"control_requirements": {"external": [{
                "kind": FACILITY_SESSION_KIND,
                "id": 0,
                "value": "mirage/complete_mega",
            }]}},
        )
        instruction = FACILITY_MIRAGE_ROOT
        state = _Execution(
            pc=instruction,
            execution_trace=[instruction],
            current_instruction_address=instruction,
            current_opcode=0x23,
            current_abi_key="NATIVE:ABORT",
        )
        branch = _fork_facility_session_native(
            context, state, instruction, b"\x23\x00\x00\x00\x00",
            "NATIVE:ABORT", {
                "symbol": "MirageProduction_Abort", "effects": [],
            },
        )[0]
        self.assertIsNone(branch.facility_family)
        self.assertIsNone(branch.facility_scenario_id)
        self.assertEqual(branch.facility_trace_cursor, 0)
        self.assertEqual(branch.vars[0x800D], 1)
        self.assertEqual(branch.abi_control_reads, [])
        self.assertEqual(
            branch.decisions[-1]["kind"], "FACILITY_PRE_SESSION_ABORT",
        )

    def test_mirage_round4_prompts_follow_one_session_mechanic(self) -> None:
        sites = (0x09391A6E, 0x09391A86, 0x09391A9E)
        cases = {
            "complete_mega": ((1, "YES"),),
            "complete_z": ((0, "NO"), (1, "YES")),
            "complete_tera": ((0, "NO"), (0, "NO"), (1, "YES")),
        }
        context = SimpleNamespace(target_root=FACILITY_MIRAGE_ROOT)
        for scenario_id, expected in cases.items():
            payload = _facility_scenario_payload("mirage", scenario_id)
            commit = next(
                index for index, row in enumerate(payload["trace"])
                if row["operation"] == "CommitRound4Mechanic"
            )
            cursor = commit
            if payload["trace"][commit - 1]["operation"] in \
                    _FACILITY_NON_NATIVE_TRACE_OPERATIONS:
                cursor -= 1
            state = _Execution(
                pc=FACILITY_MIRAGE_ROOT,
                facility_family="mirage",
                facility_scenario_id=scenario_id,
                facility_trace_cursor=cursor,
            )
            for site, (value, label) in zip(
                sites[:len(expected)], expected, strict=True,
            ):
                with self.subTest(scenario=scenario_id, site=f"0x{site:08X}"), \
                        patch(
                            "tools.stage61_interaction_oracle."
                            "_context_instruction",
                            return_value=(0x09, bytes((0x09, 0x05))),
                        ):
                    result = _facility_round4_yes_no_choice_contract(
                        context, state, site,
                    )
                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result[0][0][0], value)
                self.assertEqual(result[0][0][2], label)
                self.assertEqual(
                    result[1]["next_native_operation"],
                    "CommitRound4Mechanic",
                )

    def test_shared_reception_prompt_follows_session_family(self) -> None:
        site = 0x093CDA88
        for scenario_key, expected in (
            ("factory/battle_loss", (0, "NO", "FACTORY")),
            ("codex/busy", (1, "YES", "CODEX")),
        ):
            context = SimpleNamespace(
                target_root=FACILITY_SHARED_ROOT,
                case={"control_requirements": {"external": [{
                    "kind": FACILITY_SESSION_KIND,
                    "id": 1,
                    "value": scenario_key,
                }]}},
            )
            state = _Execution(pc=FACILITY_SHARED_ROOT)
            with self.subTest(scenario=scenario_key), patch(
                "tools.stage61_interaction_oracle._context_instruction",
                return_value=(0x09, bytes((0x09, 0x05))),
            ):
                result = _facility_shared_reception_yes_no_choice_contract(
                    context, state, site,
                )
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result[0][0][0], expected[0])
            self.assertEqual(result[0][0][2], expected[1])
            self.assertEqual(result[1]["reception_branch"], expected[2])
            self.assertEqual(state.facility_trace_cursor, 0)
            self.assertEqual(state.abi_control_reads, [])

    def test_factory_exchange_and_round_prompts_follow_session(self) -> None:
        sites = {
            "exchange_commit": (0x093C948A, 1, "COMMIT", "BeginExchange"),
            "exchange_skip": (0x093C948A, 0, "SKIP", "SkipExchange"),
            "round_continue": (0x093C94CE, 1, "CONTINUE", "PrepareBattle"),
            "round_retire": (0x093C94CE, 0, "RETIRE", "Retire"),
        }
        context = SimpleNamespace(target_root=FACILITY_SHARED_ROOT)
        for scenario_id, (site, value, decision, operation) in sites.items():
            payload = _facility_scenario_payload("factory", scenario_id)
            after = max(
                index for index, row in enumerate(payload["trace"])
                if row["operation"] == "AfterBattle"
            )
            state = _Execution(
                pc=FACILITY_SHARED_ROOT,
                facility_family="factory",
                facility_scenario_id=scenario_id,
                facility_trace_cursor=after + 1,
            )
            with self.subTest(scenario=scenario_id), patch(
                "tools.stage61_interaction_oracle._context_instruction",
                return_value=(0x09, bytes((0x09, 0x05))),
            ):
                result = _facility_factory_yes_no_choice_contract(
                    context, state, site,
                )
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result[0][0][0], value)
            self.assertEqual(result[1]["scenario_decision"], decision)
            self.assertEqual(result[1]["next_native_operation"], operation)

        payload = _facility_scenario_payload("factory", "battle_loss")
        loss = _Execution(
            pc=FACILITY_SHARED_ROOT,
            facility_family="factory",
            facility_scenario_id="battle_loss",
            facility_trace_cursor=payload["trace_count"],
        )
        with patch(
            "tools.stage61_interaction_oracle._context_instruction",
            return_value=(0x09, bytes((0x09, 0x05))),
        ):
            result = _facility_factory_yes_no_choice_contract(
                context, loss, 0x093C948A,
            )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(
            [(value, label) for value, _tokens, label in result[0]],
            [(1, "YES"), (0, "NO")],
        )
        self.assertTrue(result[1]["both_physical_answers_reachable"])

    def test_factory_inactive_and_trial_post_trace_tails_are_exact(self) -> None:
        def context_for(scenario_id: str) -> SimpleNamespace:
            return SimpleNamespace(
                target_root=FACILITY_SHARED_ROOT,
                var_mapping={},
                case={"control_requirements": {"external": [{
                    "kind": FACILITY_SESSION_KIND,
                    "id": 1,
                    "value": f"factory/{scenario_id}",
                }]}},
            )

        instruction = FACILITY_SHARED_ROOT
        loss_payload = _facility_scenario_payload("factory", "battle_loss")
        loss = _Execution(
            pc=instruction,
            facility_family="factory",
            facility_scenario_id="battle_loss",
            facility_trace_cursor=loss_payload["trace_count"],
        )
        for operation, expected_result in (
            ("SkipExchange", 7), ("PrepareBattle", 7), ("Abort", 1),
        ):
            loss.execution_trace.append(instruction)
            loss.current_instruction_address = instruction
            loss.current_opcode = 0x23
            loss.current_abi_key = f"NATIVE:{operation}"
            loss = _fork_facility_session_native(
                context_for("battle_loss"), loss, instruction,
                b"\x23\x00\x00\x00\x00", f"NATIVE:{operation}", {
                    "symbol": f"FactoryHighModesV2_{operation}",
                    "effects": [],
                },
            )[0]
            self.assertEqual(loss.vars[0x800D], expected_result)
            instruction += 5
        loss.terminated = True
        _finalize_facility_session_terminal(loss)

        trial_payload = _facility_scenario_payload(
            "factory", "reception_trial",
        )
        trial = _Execution(
            pc=instruction,
            facility_family="factory",
            facility_scenario_id="reception_trial",
            facility_trace_cursor=trial_payload["trace_count"],
        )
        trial.execution_trace.append(instruction)
        trial.current_instruction_address = instruction
        trial.current_opcode = 0x23
        trial.current_abi_key = "NATIVE:TRIAL"
        trial = _fork_facility_session_native(
            context_for("reception_trial"), trial, instruction,
            b"\x23\x00\x00\x00\x00", "NATIVE:TRIAL", {
                "symbol": "FactoryHighModesV2_TrialCompleteAdapter",
                "effects": [],
            },
        )[0]
        self.assertEqual(trial.vars[0x800D], 9)
        self.assertEqual(
            trial.facility_post_trace_operations,
            ["TrialCompleteAdapter"],
        )
        trial.terminated = True
        _finalize_facility_session_terminal(trial)

        invalid = _Execution(
            pc=instruction,
            facility_family="factory",
            facility_scenario_id="battle_loss",
            facility_trace_cursor=loss_payload["trace_count"],
        )
        invalid.execution_trace.append(instruction)
        invalid.current_instruction_address = instruction
        invalid.current_opcode = 0x23
        invalid.current_abi_key = "NATIVE:COMMIT"
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "FACILITY_FACTORY_LOSS_POST_TRACE_ORDER_MISMATCH",
        ):
            _fork_facility_session_native(
                context_for("battle_loss"), invalid, instruction,
                b"\x23\x00\x00\x00\x00", "NATIVE:COMMIT", {
                    "symbol": "FactoryHighModesV2_CommitExchange",
                    "effects": [],
                },
            )

    @staticmethod
    def _factory_loss_prepare_ordered_fixture() -> tuple[
        SimpleNamespace,
        _Execution,
        list[dict],
        list[tuple[dict, int]],
        dict[int, tuple[int, bytes]],
    ]:
        pointer = 0x09F00001
        abi_key = f"NATIVE:0x{pointer:08X}"
        candidate_values = [0, 1, 7, 12]
        result_relation = "FACTORY_PREPARE_RESULT_TEST_EXACT"
        payload = _facility_scenario_payload("factory", "battle_loss")
        trace_start = next(
            index for index, row in enumerate(payload["trace"])
            if row["operation"] == "PrepareBattle"
        )
        context = SimpleNamespace(
            root=FACILITY_SHARED_ROOT,
            target_root=FACILITY_SHARED_ROOT,
            execution_root=FACILITY_SHARED_ROOT,
            npc={"npc_id": "OBJECT:096/005:001"},
            abi_index={abi_key: {
                "source_status": "PINNED_SOURCE_VERIFIED",
                "symbol": FACILITY_FACTORY_PREPARE_ADAPTER_SYMBOL,
                "target_pointer": pointer & ~1,
                "result_contract": {
                    "global_var_result_write": {
                        "candidate_values": candidate_values,
                        "relation": result_relation,
                    },
                    "specialvar_return": None,
                },
            }},
        )
        state = _Execution(
            pc=FACILITY_SHARED_ROOT,
            tokens=[
                "A", "DOWN", "A", "DOWN", "A", "ADVANCE_TEXT",
            ],
            facility_family="factory",
            facility_scenario_id="battle_loss",
            facility_trace_cursor=payload["trace_count"],
            facility_post_trace_operations=[
                "SkipExchange", "PrepareBattle", "Abort",
            ],
            terminated=True,
            terminal_kind="FIELD_RELEASE",
            battle_start_effects=[],
            battle_start_trace_count=5,
            execution_trace=[FACILITY_SHARED_ROOT] * 8,
        )
        state.decisions = [{
            "kind": "FACILITY_SESSION_TRACE_STEP",
            "abi_key": abi_key,
            "instruction_address":
                f"0x{FACILITY_FACTORY_PREPARE_WRITER_SITE:08X}",
            "family": "factory",
            "scenario_id": "battle_loss",
            "operation": "PrepareBattle",
            "trace_start": trace_start,
            "trace_end": trace_start,
            "result_value": 1,
            "trace_count": payload["trace_count"],
            "trace_sha256": payload["trace_sha256"],
            "relation": FACILITY_SESSION_RELATION,
        }, {
            "kind": "FACILITY_POST_TRACE_NATIVE_TAIL",
            "abi_key": abi_key,
            "instruction_address":
                f"0x{FACILITY_FACTORY_PREPARE_WRITER_SITE:08X}",
            "family": "factory",
            "scenario_id": "battle_loss",
            "operation": "PrepareBattle",
            "operation_ordinal": 1,
            "operations": ["SkipExchange", "PrepareBattle"],
            "result_value": 7,
            "tail_complete": False,
            "relation": "FACTORY_LOSS_INACTIVE_FIELD_TAIL_EXACT",
        }]
        producer = {
            "writer": (
                "CALLNATIVE:" + FACILITY_FACTORY_PREPARE_ADAPTER_SYMBOL
            ),
            "instruction_address":
                f"0x{FACILITY_FACTORY_PREPARE_WRITER_SITE:08X}",
            "target_pointer": f"0x{pointer:08X}",
            "special_id": None,
            "abi_key": abi_key,
            "candidate_values": candidate_values,
            "relation": result_relation,
        }
        rows = [{
            "kind": "VAR_RESULT_BRANCH_READ",
            "instruction_address":
                f"0x{FACILITY_FACTORY_PREPARE_RESULT_CONSUMER:08X}",
            "writer": producer["writer"],
            "candidate_values": list(candidate_values),
            "producer": deepcopy(producer),
            "def_use_status": "LOCAL_EXACT",
            "capture": {
                "before_pc":
                    f"0x{FACILITY_FACTORY_PREPARE_RESULT_CONSUMER:08X}",
                "after_pc":
                    f"0x{FACILITY_FACTORY_PREPARE_RESULT_CONSUMER + 5:08X}",
                "owner_address": "0x02037004",
                "expected_value": value,
                "expected_token_index": token_index,
                "expected_execution_ordinal": 0,
            },
            "sequence_id": "factory-loss-prepare",
        } for value, token_index in ((1, 2), (7, 4))]
        records = [(rows[0], 2), (rows[1], 6)]
        instructions = {
            FACILITY_FACTORY_PREPARE_WRITER_SITE: (
                0x23, b"\x23" + pointer.to_bytes(4, "little"),
            ),
            FACILITY_FACTORY_PREPARE_RESULT_CONSUMER: (
                0x21, bytes.fromhex("210d800100"),
            ),
        }
        return context, state, rows, records, instructions

    def test_factory_loss_repeated_prepare_capture_is_source_ordered(
        self,
    ) -> None:
        context, state, rows, records, instructions = \
            self._factory_loss_prepare_ordered_fixture()
        with patch(
            "tools.stage61_interaction_oracle._context_instruction",
            side_effect=lambda _context, address: instructions[address],
        ):
            _bind_ordered_result_capture_occurrences(
                context, state, records,
            )
        contracts = [
            row["producer"]["ordered_runtime_capture"] for row in rows
        ]
        self.assertEqual(
            [row["occurrence_index"] for row in contracts], [0, 1],
        )
        self.assertTrue(all(
            row["value_sequence"] == [1, 7]
            and row["token_index_sequence"] == [2, 4]
            and row["relation"] ==
                FACILITY_FACTORY_LOSS_PREPARE_ORDERED_CAPTURE_RELATION
            for row in contracts
        ))
        _validate_runner_flat_internal_controls(
            rows, [{
                "sequence_id": "factory-loss-prepare",
                "tokens": state.tokens,
            }],
            "factory loss repeated prepare",
        )

        forged = deepcopy(rows)
        forged[1]["producer"]["ordered_runtime_capture"][
            "value_sequence"
        ] = [1, 1]
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "ordered internal capture contract不一致",
        ):
            _validate_runner_flat_internal_controls(
                forged, [{
                    "sequence_id": "factory-loss-prepare",
                    "tokens": state.tokens,
                }],
                "factory loss forged capture",
            )

    def test_factory_loss_repeated_prepare_rejects_tail_or_decision_drift(
        self,
    ) -> None:
        for drift in ("tail", "decision"):
            context, state, _rows, records, instructions = \
                self._factory_loss_prepare_ordered_fixture()
            if drift == "tail":
                state.facility_post_trace_operations.pop()
            else:
                state.decisions[1]["result_value"] = 1
            with self.subTest(drift=drift), patch(
                "tools.stage61_interaction_oracle._context_instruction",
                side_effect=lambda _context, address: instructions[address],
            ), self.assertRaisesRegex(
                Stage61InteractionOracleError,
                "FACILITY_FACTORY_LOSS_PREPARE_ORDERED_RUNTIME_"
                "CAPTURE_CONTRACT_REQUIRED",
            ):
                _bind_ordered_result_capture_occurrences(
                    context, state, records,
                )

    def test_terminal_gate_covers_all_49_scenarios_and_reward_close(self) -> None:
        def native_symbol(family: str, operation: str) -> str:
            if family == "mirage":
                return f"MirageProduction_{operation}"
            if family == "factory":
                return f"FactoryHighModesV2_{operation}"
            prefix = "CodexBattleRewards_" if operation in {
                "AfterBattleAdapter", "FieldFinishAdapter",
            } else "CodexBattleRuntime_"
            return f"{prefix}{operation}"

        scenario_count = 0
        for family, registry in FACILITY_SCENARIO_REGISTRIES.items():
            for scenario_id in registry:
                scenario_count += 1
                payload = _facility_scenario_payload(family, scenario_id)
                root = FACILITY_MIRAGE_ROOT if family == "mirage" else \
                    FACILITY_SHARED_ROOT
                identifier = 0 if family == "mirage" else 1
                context = SimpleNamespace(
                    target_root=root,
                    var_mapping={},
                    case={"control_requirements": {"external": [{
                        "kind": FACILITY_SESSION_KIND,
                        "id": identifier,
                        "value": f"{family}/{scenario_id}",
                    }]}},
                )
                complete = _Execution(pc=root)
                instruction = root
                while True:
                    cursor = complete.facility_trace_cursor
                    native_index = next((
                        index for index in range(cursor, payload["trace_count"])
                        if payload["trace"][index]["operation"] not in
                        _FACILITY_NON_NATIVE_TRACE_OPERATIONS
                    ), None)
                    if native_index is None:
                        break
                    operation = payload["trace"][native_index]["operation"]
                    complete.execution_trace.append(instruction)
                    complete.current_instruction_address = instruction
                    complete.current_opcode = 0x23
                    complete.current_abi_key = f"NATIVE:{scenario_count}"
                    complete = _fork_facility_session_native(
                        context, complete, instruction,
                        b"\x23\x00\x00\x00\x00",
                        f"NATIVE:{scenario_count}", {
                            "symbol": native_symbol(family, operation),
                            "effects": [],
                        },
                    )[0]
                    instruction += 5
                post_trace = {
                    ("factory", "battle_loss"): (
                        "SkipExchange", "PrepareBattle", "Abort",
                    ),
                    ("factory", "reception_trial"): (
                        "TrialCompleteAdapter",
                    ),
                }.get((family, scenario_id), ())
                for operation in post_trace:
                    complete.execution_trace.append(instruction)
                    complete.current_instruction_address = instruction
                    complete.current_opcode = 0x23
                    complete.current_abi_key = f"NATIVE:{scenario_count}"
                    complete = _fork_facility_session_native(
                        context, complete, instruction,
                        b"\x23\x00\x00\x00\x00",
                        f"NATIVE:{scenario_count}", {
                            "symbol": native_symbol(family, operation),
                            "effects": [],
                        },
                    )[0]
                    instruction += 5
                complete.terminated = True
                complete.terminal_kind = (
                    FACILITY_ACTIVE_CONTINUATION_TERMINAL
                    if payload["trace"][-1]["active"] else "FIELD_RELEASE"
                )
                _finalize_facility_session_terminal(complete)
                self.assertEqual(
                    complete.facility_trace_cursor, payload["trace_count"],
                )
                last_native = max(
                    index for index, row in enumerate(payload["trace"])
                    if row["operation"] not in
                    _FACILITY_NON_NATIVE_TRACE_OPERATIONS
                )
                incomplete = _Execution(
                    pc=0, terminated=True,
                    facility_family=family,
                    facility_scenario_id=scenario_id,
                    facility_trace_cursor=last_native,
                )
                with self.subTest(
                    family=family, scenario_id=scenario_id,
                ), self.assertRaisesRegex(
                    Stage61InteractionOracleError,
                    "FACILITY_SESSION_TERMINAL_TRACE_INCOMPLETE",
                ):
                    _finalize_facility_session_terminal(incomplete)
        self.assertEqual(scenario_count, 49)

        for scenario_id in (
            "win_reward", "loss_reward", "forfeit_reward",
        ):
            payload = _facility_scenario_payload("codex", scenario_id)
            lifecycle = _Execution(
                pc=0, terminated=True, terminal_kind="FIELD_RELEASE",
                facility_family="codex",
                facility_scenario_id=scenario_id,
                facility_trace_cursor=payload["trace_count"] - 1,
            )
            _finalize_facility_session_terminal(lifecycle)
            self.assertEqual(
                lifecycle.facility_trace_cursor, payload["trace_count"],
            )
            self.assertEqual(lifecycle.decisions[-1]["operations"], [
                "RewardClose",
            ])
            self.assertEqual(
                lifecycle.decisions[-1]["relation"],
                FACILITY_SESSION_RELATION,
            )

    def test_factory_active_scenarios_stop_at_exact_native_return(self) -> None:
        expected = {
            "exchange_commit": "CommitExchange",
            "exchange_skip": "SkipExchange",
            "round_continue": "PrepareBattle",
        }
        for scenario_id, operation in expected.items():
            payload = _facility_scenario_payload("factory", scenario_id)
            instruction = FACILITY_SHARED_ROOT
            context = SimpleNamespace(
                target_root=FACILITY_SHARED_ROOT,
                var_mapping={},
                case={"control_requirements": {"external": [{
                    "kind": FACILITY_SESSION_KIND,
                    "id": 1,
                    "value": f"factory/{scenario_id}",
                }]}},
            )
            state = _Execution(
                pc=instruction,
                facility_family="factory",
                facility_scenario_id=scenario_id,
                facility_trace_cursor=payload["trace_count"] - 1,
            )
            state.execution_trace.append(instruction)
            state.current_instruction_address = instruction
            state.current_opcode = 0x23
            state.current_abi_key = "NATIVE:ACTIVE_BOUNDARY"
            branch = _fork_facility_session_native(
                context, state, instruction, b"\x23\x00\x00\x00\x00",
                "NATIVE:ACTIVE_BOUNDARY", {
                    "symbol": f"FactoryHighModesV2_{operation}",
                    "effects": [],
                },
            )[0]
            with self.subTest(scenario=scenario_id):
                self.assertTrue(branch.terminated)
                self.assertEqual(
                    branch.terminal_kind,
                    FACILITY_ACTIVE_CONTINUATION_TERMINAL,
                )
                self.assertEqual(
                    branch.facility_trace_cursor, payload["trace_count"],
                )
                self.assertEqual(
                    branch.decisions[-1]["kind"],
                    "FACILITY_SESSION_ACTIVE_CONTINUATION_BOUNDARY",
                )
                _finalize_facility_session_terminal(branch)

                wrong = branch.clone()
                wrong.terminal_kind = "FIELD_RELEASE"
                with self.assertRaisesRegex(
                    Stage61InteractionOracleError,
                    "FACILITY_ACTIVE_CONTINUATION_TERMINAL_MISMATCH",
                ):
                    _finalize_facility_session_terminal(wrong)


if __name__ == "__main__":
    unittest.main()
