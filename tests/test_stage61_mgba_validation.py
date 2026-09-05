from __future__ import annotations

import importlib.util
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_stage61_mgba_validation.py"
SOURCE_PATH = ROOT / "tools/mgba_stage61_display_npc_event_e2e.c"

SPEC = importlib.util.spec_from_file_location("stage61_mgba_validation", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class Stage61MgbaValidationTests(unittest.TestCase):
    @staticmethod
    def _party_minigame_fixture(*, count: int = 6) -> dict[str, object]:
        return {
            "fixture_kind": "PARTY", "count": count,
            "raw_hex": bytes(600).hex(),
        }

    @classmethod
    def _party_minigame_external(
        cls, reference: str, *, mode: int = 0, eligible: bool = True,
        selected_slot: int | None = 0, party_count: int = 6,
    ) -> dict[str, object]:
        return {
            "kind": "PARTY_MINIGAME", "id": mode,
            "source_ids": [398, 402, 438],
            "read_addresses": ["0x081281C0", "0x0814A008", "0x0815693C"],
            "candidate_values": "PARTY_LAYOUT_REQUIRED",
            "relations": [{
                "operator":
                    "WIRELESS_MINIGAME_PARTY_ELIGIBILITY_AND_SELECTION",
            }],
            "required_value_in_matrix_case": {
                "mode": mode, "eligible": eligible,
                "selected_slot": selected_slot, "party_count": party_count,
                "party_layout_ref": reference,
            },
            "requirement_basis": "PINNED_WIRELESS_MINIGAME_PARTY_OWNER",
        }

    @staticmethod
    def _daycare_transaction_fixture(
        scenario_id: str = "one_sufficient",
    ) -> dict[str, object]:
        from tools.stage61_interaction_oracle import _daycare_scenario_payload

        return deepcopy(_daycare_scenario_payload(scenario_id))

    @classmethod
    def _daycare_transaction_external(
        cls, reference: str, *, scenario_id: str = "one_sufficient",
    ) -> dict[str, object]:
        fixture = cls._daycare_transaction_fixture(scenario_id)
        route5 = scenario_id.startswith("route5_")
        identifier = 1 if route5 else 0
        scenario_ids = (
            RUNNER._ROUTE5_DAYCARE_TRANSACTION_SCENARIO_IDS
            if route5 else RUNNER._DAYCARE_TRANSACTION_SCENARIO_IDS
        )
        relation = (
            RUNNER._ROUTE5_DAYCARE_TRANSACTION_RELATION
            if route5 else RUNNER._DAYCARE_TRANSACTION_RELATION
        )
        state_owners = (
            RUNNER._ROUTE5_DAYCARE_TRANSACTION_STATE_OWNERS
            if route5 else RUNNER._DAYCARE_TRANSACTION_STATE_OWNERS
        )
        return {
            "kind": "DAYCARE_TRANSACTION_STATE", "id": identifier,
            "source_ids": (
                [131, 132, 133, 186, 188, 197, 198,
                 374, 375, 376, 377, 378]
                if route5 else
                [131, 132, 133, 182, 186, 187, 188,
                 189, 190, 191, 192, 197, 198]
            ),
            "read_addresses": ["0x08127F00"],
            "candidate_values": list(scenario_ids),
            "relations": [{
                "operator": relation,
                "state_owners": list(state_owners),
            }],
            "required_value_in_matrix_case": {
                "scenario_id": scenario_id,
                "layout_ref": reference,
                "party_count": fixture["party_count"],
                "money": fixture["money"],
                "party_sha256": hashlib.sha256(bytes.fromhex(
                    str(fixture["party_raw_hex"])
                )).hexdigest(),
                "daycare_sha256": hashlib.sha256(bytes.fromhex(
                    str(fixture["daycare_raw_hex"])
                )).hexdigest(),
            },
            "requirement_basis": (
                "PINNED_ROUTE5_DAYCARE_TRANSACTION"
                if route5 else "PINNED_FOUR_ISLAND_DAYCARE_TRANSACTION"
            ),
        }

    @staticmethod
    def _party_move_transaction_fixture(
        scenario_id: str = "relearner_teach_empty_slot",
    ) -> dict[str, object]:
        from tools.stage61_interaction_oracle import _party_move_scenario_payload

        return deepcopy(_party_move_scenario_payload(scenario_id))

    @classmethod
    def _party_move_transaction_external(
        cls, reference: str,
        *, scenario_id: str = "relearner_teach_empty_slot",
    ) -> dict[str, object]:
        fixture = cls._party_move_transaction_fixture(scenario_id)
        return {
            "kind": "PARTY_MOVE_TRANSACTION_STATE", "id": 0,
            "source_ids": [159, 219, 220, 221, 222, 223, 224, 328],
            "read_addresses": ["0x092D0A10", "0x092D0A98", "0x09432DD9"],
            "candidate_values": list(
                RUNNER._PARTY_MOVE_TRANSACTION_SCENARIO_IDS
            ),
            "relations": [{
                "operator": RUNNER._PARTY_MOVE_TRANSACTION_RELATION,
                "state_owners": list(
                    RUNNER._PARTY_MOVE_TRANSACTION_STATE_OWNERS
                ),
                "model_sources": dict(
                    RUNNER._PARTY_MOVE_TRANSACTION_MODEL_SOURCES
                ),
            }],
            "required_value_in_matrix_case": {
                "scenario_id": scenario_id,
                "layout_ref": reference,
                "family": fixture["family"],
                "party_count": fixture["party_count"],
                "party_sha256": hashlib.sha256(bytes.fromhex(
                    str(fixture["party_raw_hex"])
                )).hexdigest(),
                "party_selection_sequence": deepcopy(
                    fixture["party_selection_sequence"]
                ),
                "selected_move_slot": fixture["selected_move_slot"],
                "selected_relearn_move": fixture["selected_relearn_move"],
                "teach_outcome": fixture["teach_outcome"],
                "expected_relearnable_count": fixture[
                    "expected_relearnable_count"
                ],
                "payment_policy": fixture["payment_policy"],
                "expected_action": fixture["expected_action"],
            },
            "requirement_basis": "PINNED_PARTY_MOVE_TRANSACTION_MODEL",
        }

    @staticmethod
    def _fossil_revival_fixture(
        scenario_id: str = "idle_available_helix",
    ) -> dict[str, object]:
        from tools.stage61_interaction_oracle import (
            _fossil_revival_scenario_payload,
        )

        return deepcopy(_fossil_revival_scenario_payload(scenario_id))

    @classmethod
    def _fossil_revival_external(
        cls, reference: str,
        *, scenario_id: str = "idle_available_helix",
    ) -> dict[str, object]:
        fixture = cls._fossil_revival_fixture(scenario_id)
        return {
            "kind": "FOSSIL_REVIVAL_STATE", "id": 0,
            "source_ids": [0x5176, 0x5177],
            "read_addresses": ["0x09433696"],
            "candidate_values": list(RUNNER._FOSSIL_REVIVAL_SCENARIO_IDS),
            "relations": [{"operator": RUNNER._FOSSIL_REVIVAL_RELATION}],
            "required_value_in_matrix_case": {
                "scenario_id": scenario_id,
                "layout_ref": reference,
                "revive_state": fixture["revive_state"],
                "which_fossil": fixture["which_fossil"],
            },
            "requirement_basis": "PINNED_CINNABAR_FOSSIL_PREFIX_STATE",
        }

    @staticmethod
    def _ruin_seal_fixture(
        root: int = 0x088668A0, scenario_id: str = "missing_07",
    ) -> dict[str, object]:
        from tools.stage61_interaction_oracle import (
            _ruin_seal_scenario_payload,
        )

        return deepcopy(_ruin_seal_scenario_payload(root, scenario_id))

    @classmethod
    def _ruin_seal_external(
        cls, reference: str, *, root: int = 0x088668A0,
        scenario_id: str = "missing_07",
    ) -> dict[str, object]:
        fixture = cls._ruin_seal_fixture(root, scenario_id)
        completion_flag = (
            RUNNER._RUIN_SEAL_COMPLETION_FLAG
            if root == RUNNER._RUIN_SEAL_OBJECT_ROOT else None
        )
        return {
            "kind": "RUIN_SEAL_PREFIX",
            "id": RUNNER._RUIN_SEAL_CONTROL_IDS[root],
            "source_ids": list(RUNNER._RUIN_SEAL_FLAGS) + (
                [RUNNER._RUIN_SEAL_COMPLETION_FLAG]
                if completion_flag is not None else []
            ),
            "read_addresses": [f"0x{root:08X}"],
            "candidate_values": sorted(
                RUNNER._RUIN_SEAL_SCENARIO_IDS[root], key=RUNNER._stable,
            ),
            "relations": [{
                "operator": RUNNER._RUIN_SEAL_PREFIX_RELATION,
                "root_address": f"0x{root:08X}",
                "seal_flag_ids": list(RUNNER._RUIN_SEAL_FLAGS),
                "completion_flag_id": completion_flag,
                "scenario_count": len(
                    RUNNER._RUIN_SEAL_SCENARIO_IDS[root]
                ),
            }],
            "required_value_in_matrix_case": {
                "root_address": f"0x{root:08X}",
                "scenario_id": scenario_id,
                "layout_ref": reference,
                "first_missing_index": fixture["first_missing_index"],
                "all_seals": fixture["all_seals"],
                "completed": fixture["completed"],
                "flag_values": deepcopy(fixture["flags"]),
                "root_source_binding": deepcopy(
                    fixture["root_source_binding"]
                ),
            },
            "requirement_basis": "PINNED_RUINOUS_SEAL_PREFIX_STATE",
        }

    @staticmethod
    def _facility_fixture(
        family: str = "mirage", scenario_id: str = "locked",
    ) -> dict[str, object]:
        return deepcopy(RUNNER._facility_session_scenario_payload(
            family, scenario_id,
        ))

    @classmethod
    def _facility_external(
        cls, reference: str, *, family: str = "mirage",
        scenario_id: str = "locked",
    ) -> dict[str, object]:
        fixture = cls._facility_fixture(family, scenario_id)
        root = int(str(fixture["source_binding"]["root_address"]), 0)
        families = ("mirage",) if root == RUNNER._FACILITY_MIRAGE_ROOT \
            else ("factory", "codex")
        manifest = RUNNER._facility_session_manifest()
        scenario_keys = [
            row["scenario_key"] for row in manifest["scenarios"]
            if row["family"] in families
        ]
        value = {
            key: deepcopy(fixture[key])
            for key in RUNNER._FACILITY_SESSION_REQUIRED_VALUE_TYPE
            if key != "layout_ref"
        }
        value["layout_ref"] = reference
        return {
            "kind": "FACILITY_SESSION",
            "id": RUNNER._FACILITY_CONTROL_IDS[root],
            "source_ids": [],
            "read_addresses": [f"0x{root:08X}"],
            "candidate_values": sorted(scenario_keys, key=RUNNER._stable),
            "relations": [{
                "operator": RUNNER._FACILITY_SESSION_RELATION,
                "root_address": f"0x{root:08X}",
                "scenario_keys": scenario_keys,
                "source_identity_owner": (
                    RUNNER._FACILITY_SESSION_REGISTRY_SOURCE_PATH
                ),
                "raw_ewram_preimage_policy": (
                    "UNDEFINED_RAW_BYTES_FORBIDDEN;"
                    "CALL_EXACT_EXPORT_SEQUENCE"
                ),
            }],
            "required_value_in_matrix_case": value,
            "requirement_basis": "PINNED_SOURCE_BOUND_FACILITY_SESSION",
        }

    @staticmethod
    def _facility_observation(
        control: dict[str, object],
    ) -> dict[str, object]:
        required = control["required_value_in_matrix_case"]
        assert isinstance(required, dict)
        trace = required["trace"]
        source_binding = required["source_binding"]
        assert isinstance(trace, list)
        assert isinstance(source_binding, dict)
        regions = source_binding["ram_regions"]
        assert isinstance(regions, list)
        digest = "a" * 64
        boundaries = []
        ordinal = 2
        native_count = 0
        for index, source in enumerate(trace):
            assert isinstance(source, dict)
            non_native = (
                source["operation"] in RUNNER._FACILITY_NON_NATIVE_OPERATIONS
            )
            if non_native:
                entry_ordinal = return_ordinal = ordinal
                ordinal += 1
                boundary_kind = (
                    "SESSION_DECISION_AT_FIELD_RELEASE"
                    if index + 1 == len(trace)
                    else "SESSION_DECISION_BEFORE_NEXT_NATIVE"
                )
                entry_pc = return_pc = None
                correlation_pc = "0x09000004"
            else:
                native_count += 1
                entry_ordinal, return_ordinal = ordinal, ordinal + 1
                ordinal += 2
                boundary_kind = "NATIVE_CALL_RETURN"
                entry_pc, return_pc = "0x09000000", "0x09000002"
                correlation_pc = None
            boundaries.append({
                "ordinal": index,
                "operation": source["operation"],
                "boundary_kind": boundary_kind,
                "entry_pc": entry_pc,
                "return_pc": return_pc,
                "correlation_pc": correlation_pc,
                "entry_instruction_ordinal": entry_ordinal,
                "return_instruction_ordinal": return_ordinal,
                **{
                    key: deepcopy(source[key]) for key in (
                        "state", "phase", "status", "result", "active",
                        "battle_index", "round_index", "mechanic",
                        "completion_pending", "reward_window",
                        "reward_result_kind",
                    )
                },
                "regions": [{
                    "address": region["address"], "size": region["size"],
                    "before_sha256": digest, "after_sha256": digest,
                } for region in regions],
                "party": {
                    "size": 600, "before_sha256": digest,
                    "after_sha256": digest,
                },
                "storage": {
                    "size": 33744, "before_sha256": digest,
                    "after_sha256": digest,
                },
                "entry_return_ordered": True,
                "record_exact": True,
            })
        active = bool(trace[-1]["active"])
        terminal_kind = (
            RUNNER._FACILITY_ACTIVE_CONTINUATION_TERMINAL
            if active else "FIELD_RELEASE"
        )
        return {
            "kind": "FACILITY_SESSION",
            "scenario_key": required["scenario_key"],
            "root_address": source_binding["root_address"],
            "layout_ref": required["layout_ref"],
            "trace_count": len(trace),
            "observed_trace_count": len(trace),
            "native_boundary_count": native_count,
            "non_native_boundary_count": len(trace) - native_count,
            "trace_sha256": required["trace_sha256"],
            "transport_exact": True,
            "raw_ewram_preimage_used": False,
            "physical_prefix": {
                "actual_stock_warp_walk_face_a": True,
                "attached_before_a": True,
                "declared_root_hit": True,
                "root_instruction_ordinal": 1,
                "first_native_entry_ordinal": 2,
                "root_before_first_native": True,
                "direct_native_only": False,
            },
            "host_writes": {
                "lifecycle_calls": 0, "phase_status_result": 0,
                "ewram_raw": 0,
            },
            "native_boundaries": boundaries,
            "terminal": {
                "cursor_exact": True, "final_active": active,
                "terminal_kind": terminal_kind,
                "party_restored": True, "storage_restored": True,
                "final_region_sha256": [digest for _ in regions],
                "final_party_sha256": digest,
                "final_storage_sha256": digest,
                "exact": True,
            },
            "factory_prepare_adapter_source_bound": True,
            "runtime_driver_completed": True,
        }

    @staticmethod
    def _gift_storage_sweep_schema() -> dict[str, object]:
        from tools.stage61_interaction_oracle import (
            _gift_storage_scenario_payload, runner_fixture_key,
        )

        fixtures: dict[str, object] = {}
        rows = []
        for scenario_id in RUNNER._GIFT_STORAGE_TRANSACTION_RUNNER_SCENARIO_IDS:
            fixture = deepcopy(_gift_storage_scenario_payload(scenario_id))
            reference = runner_fixture_key(fixture)
            fixtures[reference] = fixture
            rows.append({"scenario_id": scenario_id, "fixture_key": reference})
        return {
            "runner_fixtures": fixtures,
            "dedicated_fixture_sweeps": {
                "GIFT_STORAGE_TRANSACTION_STATE": {"scenarios": rows},
            },
        }

    @staticmethod
    def _gift_storage_sweep_document(
        controls: list[dict[str, object]],
    ) -> dict[str, object]:
        rows = []
        for ordinal, (control, layout) in enumerate(zip(
            controls, RUNNER._GIFT_STORAGE_TRANSACTION_SWEEP_MANIFEST,
            strict=True,
        )):
            value = control["required_value_in_matrix_case"]
            assert isinstance(value, dict)
            result = layout["expected_result"]
            box_id = layout["expected_mon_box_id"]
            box_pos = layout["expected_mon_box_pos"]
            rows.append({
                "ordinal": ordinal,
                "scenario_id": layout["scenario_id"],
                "fixture_ref": value["layout_ref"],
                "executor_equivalence_class": layout[
                    "executor_equivalence_class"
                ],
                "expected_result": result,
                "actual_result": result,
                "target_kind": (
                    "PARTY" if result == 0 else
                    "STORAGE" if result == 1 else "NONE"
                ),
                "party_count_before": layout["party_count"],
                "party_count_after": (
                    layout["party_count"] + int(result == 0)
                ),
                "current_box_before": layout["current_box"],
                "current_box_after": layout["current_box"],
                "original_box": layout["current_box"],
                "mon_box_id": 0xFFFF if box_id is None else box_id,
                "mon_box_pos": 0xFFFF if box_pos is None else box_pos,
                "var_pc_box_before": layout["var_pc_box_to_send_mon"],
                "var_pc_box_after": layout["expected_var_pc_box_after"],
                "shown_full_before": False,
                "shown_full_after": False,
                "rng_seed_at_handler": (
                    RUNNER._GIFT_STORAGE_TRANSACTION_RNG_SEED
                ),
                "rng_state_after": (
                    RUNNER._GIFT_STORAGE_TRANSACTION_EXPECTED_RNG_AFTER
                ),
                "generated_heap_capture_count": 1,
                "generated_mon_100_sha256": (
                    RUNNER._GIFT_STORAGE_TRANSACTION_GENERATED_MON_100_SHA256
                ),
                "generated_mon_80_sha256": (
                    RUNNER._GIFT_STORAGE_TRANSACTION_GENERATED_MON_80_SHA256
                ),
                "generated_mon_100_expected_exact": True,
                "generated_mon_80_expected_exact": True,
                "friendship_matches_base_stats": True,
                "party_postimage_exact": True,
                "storage_postimage_exact": True,
                "saveblock1_postimage_exact": True,
                "saveblock2_postimage_exact": True,
                "pokedex_four_owner_postimage_exact": True,
                "target_unique": True,
                "non_target_party_byte_exact": True,
                "non_target_storage_byte_exact": True,
                "storage_header_tail_byte_exact": True,
                "scheduler_lifecycle_exact": True,
                "physical_map_header_readback_exact": True,
            })
        return {
            "schema_version": 1,
            "status": "PASS",
            "case": "gift_storage_transaction_sweep",
            "source_owner": "OBJECT:010/015:002",
            "source_root": (
                RUNNER._GIFT_STORAGE_TRANSACTION_MAP_SECTION_SOURCE_ROOT
            ),
            "source_instruction": (
                f"0x{RUNNER._GIFT_STORAGE_TRANSACTION_SOURCE_INSTRUCTION:08X}"
            ),
            "source_command_raw_hex": (
                RUNNER._GIFT_STORAGE_TRANSACTION_SOURCE_COMMAND.hex().upper()
            ),
            "physical_map": [10, 15],
            "physical_map_header_address": (
                RUNNER._GIFT_STORAGE_TRANSACTION_MAP_HEADER_ADDRESS
            ),
            "physical_map_section_id": 92,
            "actual_script_context_opcode_0x79": True,
            "direct_host_script_run": False,
            "field_scheduler_script_context_run": True,
            "fixed_local_source_program": True,
            "tsv_arbitrary_program_field_count": 0,
            "host_var_result_write_count": 0,
            "host_rng_entry_seed_write_count": 30,
            "results": rows,
            "fixture_count": 30,
            "result_counts": {"party": 1, "storage": 28, "full": 1},
            "equivalence_class_counts": {
                "PARTY_SPACE": 1, "PC_CURRENT_BOX": 14,
                "PC_NEXT_BOX": 13, "PC_NEXT_BOX_WRAP": 1,
                "STORAGE_FULL": 1,
            },
            "all_fixture_refs_unique": True,
            "all_scenarios_fixed_order": True,
            "all_generated_mon_100_exact": True,
            "all_generated_mon_80_exact": True,
            "same_generated_mon_all_layouts": True,
            "all_rng_lifecycle_exact": True,
            "all_pokedex_four_owner_postimages_exact": True,
            "all_target_and_non_target_postimages_exact": True,
            "all_scheduler_lifecycles_exact": True,
            "all_physical_map_header_readbacks_exact": True,
            "generated_mon_100_raw_hex": (
                RUNNER._GIFT_STORAGE_TRANSACTION_GENERATED_MON_100_HEX.upper()
            ),
            "generated_mon_100_sha256": (
                RUNNER._GIFT_STORAGE_TRANSACTION_GENERATED_MON_100_SHA256
            ),
            "generated_mon_80_sha256": (
                RUNNER._GIFT_STORAGE_TRANSACTION_GENERATED_MON_80_SHA256
            ),
            "failed": 0,
            "untested": 0,
            "warnings": 0,
        }

    def test_fossil_revival_schema_tsv_binary_and_observation_are_exact(
        self,
    ) -> None:
        fixtures = {
            RUNNER._runner_fixture_key(
                self._fossil_revival_fixture(scenario_id)
            ): self._fossil_revival_fixture(scenario_id)
            for scenario_id in RUNNER._FOSSIL_REVIVAL_SCENARIO_IDS
        }
        registry = RUNNER._normalize_control_fixture_registry(fixtures)
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        normalized_rows = []
        for reference, fixture in registry.items():
            scenario_id = str(fixture["scenario_id"])
            with self.subTest(scenario=scenario_id):
                row = RUNNER._normalize_external_controls(
                    [self._fossil_revival_external(
                        reference, scenario_id=scenario_id,
                    )], state, registry, f"fossil-{scenario_id}",
                )[0]
                normalized_rows.append(row)
                self.assertEqual(
                    RUNNER._encode_external_control(row),
                    "@".join((
                        "FOSSIL_REVIVAL_STATE", "0",
                        ",".join((
                            scenario_id, reference,
                            str(fixture["revive_state"]),
                            str(fixture["which_fossil"]),
                        )),
                        RUNNER._FOSSIL_REVIVAL_RELATION + ":0",
                    )),
                )
                observed = [{
                    "kind": "FOSSIL_REVIVAL_STATE",
                    "scenario_id": scenario_id,
                    "layout_ref": reference,
                    "revive_state": fixture["revive_state"],
                    "which_fossil": fixture["which_fossil"],
                    "binary_fixture_verified": True,
                    "preinteraction_readback_exact": True,
                    "exact": True,
                }]
                self.assertEqual(
                    RUNNER._validate_deferred_external_controls(
                        observed, [row], label=f"fossil-{scenario_id}",
                    ),
                    observed,
                )

        prefix_codes = {
            "IDLE_AVAILABILITY": 0,
            "REVIVING_SELECTED": 1,
            "READY_SELECTED": 2,
            "ALL_REVIVED_TERMINAL": 3,
        }
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            RUNNER.write_control_fixture_files(destination, registry)
            for reference, fixture in registry.items():
                raw = (destination / f"{reference}.bin").read_bytes()
                scenario = str(fixture["scenario_id"]).encode("ascii")
                self.assertEqual(len(raw), 148)
                self.assertEqual(raw[:8], b"S61FSR01")
                self.assertEqual(raw[8:40], bytes.fromhex(reference))
                self.assertEqual(
                    raw[40:72], bytes.fromhex(str(fixture["source_sha256"])),
                )
                self.assertEqual(raw[72:72 + len(scenario)], scenario)
                self.assertEqual(
                    raw[72 + len(scenario):104], bytes(32 - len(scenario)),
                )
                self.assertEqual(
                    int.from_bytes(raw[104:106], "little"),
                    fixture["revive_state"],
                )
                self.assertEqual(
                    int.from_bytes(raw[106:108], "little"),
                    fixture["which_fossil"],
                )
                self.assertEqual(raw[108], prefix_codes[fixture["prefix_class"]])
                self.assertEqual(raw[109:112], bytes(3))
                for index, flag in enumerate(fixture["flags"]):
                    offset = 112 + index * 4
                    self.assertEqual(
                        int.from_bytes(raw[offset:offset + 2], "little"),
                        flag["id"],
                    )
                    self.assertEqual(raw[offset + 2:offset + 4], bytes((
                        int(flag["value"]), 0,
                    )))
                for index, item in enumerate(fixture["items"]):
                    offset = 136 + index * 4
                    self.assertEqual(
                        int.from_bytes(raw[offset:offset + 2], "little"),
                        item["id"],
                    )
                    self.assertEqual(
                        int.from_bytes(raw[offset + 2:offset + 4], "little"),
                        item["count"],
                    )

        source = SOURCE_PATH.read_text(encoding="utf-8")
        for exact in (
            "S61_CONTROL_FOSSIL_REVIVAL_STATE",
            'strcmp(value, "FOSSIL_REVIVAL_STATE") == 0',
            "CINNABAR_FOSSIL_PREFIX_FLAGS_ITEMS_EXACT",
            "S61_FOSSIL_REVIVAL_FIXTURE_SIZE == 148U",
            "s61_load_fossil_revival_fixture",
            "s61_apply_fossil_revival_fixture",
            "s61_verify_fossil_revival_fixture",
            "binary_fixture_verified",
            "preinteraction_readback_exact",
        ):
            self.assertIn(exact, source)

    def test_fossil_revival_tamper_and_domain_drift_fail_closed(self) -> None:
        fixture = self._fossil_revival_fixture()
        reference = RUNNER._runner_fixture_key(fixture)
        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        for label, mutate in (
            ("state", lambda row: row.update({"revive_state": 2})),
            ("flag", lambda row: row["flags"][0].update({"value": True})),
            ("item", lambda row: row["items"][0].update({"count": 1})),
            ("source", lambda row: row.update({"source_sha256": "0" * 64})),
        ):
            broken = deepcopy(fixture)
            mutate(broken)
            with self.subTest(label=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "source prefix",
            ):
                RUNNER._normalize_control_fixture_registry({
                    RUNNER._runner_fixture_key(broken): broken,
                })
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "SHA"):
            RUNNER._normalize_control_fixture_registry({"0" * 64: fixture})

        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        for label, mutate in (
            ("candidate", lambda row: row.update({
                "candidate_values": ["idle_available_helix"],
            })),
            ("relation", lambda row: row.update({
                "relations": [{"operator": "EXACT_PHYSICAL_VAR_VALUE"}],
            })),
            ("id", lambda row: row.update({"id": 1})),
            ("scalar", lambda row: row["required_value_in_matrix_case"].update({
                "revive_state": 2,
            })),
        ):
            broken = self._fossil_revival_external(reference)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [broken], state, registry, f"fossil-{label}",
                )

    def test_ruin_seal_prefix_schema_tsv_binary_and_observation_are_exact(
        self,
    ) -> None:
        fixtures = {}
        for root, scenarios in RUNNER._RUIN_SEAL_SCENARIO_IDS.items():
            for scenario_id in scenarios:
                fixture = self._ruin_seal_fixture(root, scenario_id)
                fixtures[RUNNER._runner_fixture_key(fixture)] = fixture
        self.assertEqual(len(fixtures), 31)
        registry = RUNNER._normalize_control_fixture_registry(fixtures)
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        normalized_rows = []
        for reference, fixture in registry.items():
            root = int(str(fixture["root_address"]), 0)
            scenario_id = str(fixture["scenario_id"])
            with self.subTest(root=f"0x{root:08X}", scenario=scenario_id):
                row = RUNNER._normalize_external_controls(
                    [self._ruin_seal_external(
                        reference, root=root, scenario_id=scenario_id,
                    )], state, registry,
                    f"ruin-seal-0x{root:08X}-{scenario_id}",
                )[0]
                normalized_rows.append(row)
                projected = RUNNER._normalize_event_compact_external_controls(
                    [{
                        "kind": "RUIN_SEAL_PREFIX",
                        "id": RUNNER._RUIN_SEAL_CONTROL_IDS[root],
                        "value": deepcopy(
                            row["required_value_in_matrix_case"]
                        ),
                        "owner_keys": [f"RUIN_SEAL_PREFIX:0x{root:08X}"],
                        "relation_evidence": deepcopy(row["relations"]),
                        "fixture_keys": [reference],
                    }],
                    registry, f"ruin-compact-{root}-{scenario_id}",
                    allowed_owner_ids={
                        f"RUIN_SEAL_PREFIX:0x{root:08X}"
                    },
                )
                self.assertEqual(
                    projected[0]["required_value_in_matrix_case"],
                    row["required_value_in_matrix_case"],
                )
                encoded = RUNNER._encode_external_control(row)
                self.assertTrue(encoded.startswith(
                    f"RUIN_SEAL_PREFIX@{RUNNER._RUIN_SEAL_CONTROL_IDS[root]}@"
                    f"{scenario_id},{reference},{root},"
                ))
                self.assertTrue(encoded.endswith(
                    RUNNER._RUIN_SEAL_PREFIX_RELATION + ":0"
                ))
                self.assertIn(
                    str(fixture["root_source_binding"]["sha256"]), encoded,
                )
                observed = [{
                    "kind": "RUIN_SEAL_PREFIX",
                    "root_address": fixture["root_address"],
                    "scenario_id": scenario_id,
                    "layout_ref": reference,
                    "first_missing_index": fixture["first_missing_index"],
                    "all_seals": fixture["all_seals"],
                    "completed": fixture["completed"],
                    "flag_values": deepcopy(fixture["flags"]),
                    "root_source_binding": deepcopy(
                        fixture["root_source_binding"]
                    ),
                    "binary_fixture_verified": True,
                    "preinteraction_readback_exact": True,
                    "exact": True,
                }]
                self.assertEqual(
                    RUNNER._validate_deferred_external_controls(
                        observed, [row],
                        label=f"ruin-seal-{root}-{scenario_id}",
                    ),
                    observed,
                )

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            RUNNER.write_control_fixture_files(destination, registry)
            for reference, fixture in registry.items():
                raw = (destination / f"{reference}.bin").read_bytes()
                root = int(str(fixture["root_address"]), 0)
                scenario = str(fixture["scenario_id"]).encode("ascii")
                object_root = root == RUNNER._RUIN_SEAL_OBJECT_ROOT
                self.assertEqual(len(raw), RUNNER._RUIN_SEAL_PREFIX_BINARY_BYTES)
                self.assertEqual(raw[:8], b"S61RSP01")
                self.assertEqual(raw[8:40], bytes.fromhex(reference))
                self.assertEqual(
                    raw[40:72], bytes.fromhex(str(
                        fixture["root_source_binding"]["sha256"]
                    )),
                )
                self.assertEqual(raw[72:72 + len(scenario)], scenario)
                self.assertEqual(
                    raw[72 + len(scenario):104], bytes(32 - len(scenario)),
                )
                self.assertEqual(int.from_bytes(raw[104:108], "little"), root)
                self.assertEqual(
                    int.from_bytes(raw[108:112], "little"), root,
                )
                self.assertEqual(
                    int.from_bytes(raw[112:116], "little"),
                    fixture["root_source_binding"]["byte_length"],
                )
                self.assertEqual(
                    int.from_bytes(raw[116:118], "little"),
                    RUNNER._RUIN_SEAL_PREFIX_NULL_U16
                    if fixture["first_missing_index"] is None
                    else fixture["first_missing_index"],
                )
                self.assertEqual(int.from_bytes(raw[118:120], "little"), 14)
                self.assertEqual(
                    int.from_bytes(raw[120:122], "little"),
                    RUNNER._RUIN_SEAL_COMPLETION_FLAG if object_root
                    else RUNNER._RUIN_SEAL_PREFIX_NULL_U16,
                )
                self.assertEqual(
                    int.from_bytes(raw[122:124], "little"),
                    15 if object_root else 14,
                )
                self.assertEqual(raw[124], int(fixture["all_seals"]))
                self.assertEqual(
                    raw[125], 0xFF if fixture["completed"] is None
                    else int(fixture["completed"]),
                )
                self.assertEqual(raw[126], RUNNER._RUIN_SEAL_CONTROL_IDS[root])
                self.assertEqual(raw[127], 0)
                for index, flag in enumerate(fixture["flags"]):
                    offset = 128 + index * 4
                    self.assertEqual(
                        int.from_bytes(raw[offset:offset + 2], "little"),
                        flag["id"],
                    )
                    self.assertEqual(
                        raw[offset + 2:offset + 4],
                        bytes((int(flag["value"]), 0)),
                    )
                if not object_root:
                    self.assertEqual(raw[184:188], b"\xff\xff\0\0")

        source = SOURCE_PATH.read_text(encoding="utf-8")
        from tools.stage61_interaction_oracle import runner_control_abi_contract

        self.assertEqual(
            runner_control_abi_contract()["required_value_types"]
            ["RUIN_SEAL_PREFIX"],
            RUNNER._RUIN_SEAL_PREFIX_REQUIRED_VALUE_TYPE,
        )
        for exact in (
            "S61_CONTROL_RUIN_SEAL_PREFIX",
            'strcmp(value, "RUIN_SEAL_PREFIX") == 0',
            "RUINOUS_SEAL_FIRST_MISSING_PREFIX_EXACT",
            "S61_RUIN_SEAL_FIXTURE_SIZE == 188U",
            "s61_load_ruin_seal_fixture",
            "s61_apply_ruin_seal_fixture",
            "s61_verify_ruin_seal_fixture",
            "generic FLAG double-apply",
            "root_source_binding",
            "preinteraction_readback_exact",
        ):
            self.assertIn(exact, source)

    def test_ruin_seal_prefix_tamper_and_generic_flag_fail_closed(self) -> None:
        root = RUNNER._RUIN_SEAL_OBJECT_ROOT
        fixture = self._ruin_seal_fixture(root, "missing_07")
        reference = RUNNER._runner_fixture_key(fixture)
        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        empty_state = {
            key: [] for key in ("flags", "vars", "items", "trainers")
        }
        for label, mutate in (
            ("flag", lambda row: row["flags"][6].update({"value": False})),
            ("completion", lambda row: row["flags"][-1].update({
                "value": True,
            })),
            ("binding", lambda row: row["root_source_binding"].update({
                "sha256": "0" * 64,
            })),
            ("generic-extra", lambda row: row["flags"].append({
                "id": 0x1200, "value": False,
            })),
        ):
            broken = deepcopy(fixture)
            mutate(broken)
            with self.subTest(fixture=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "prefix/root binding",
            ):
                RUNNER._normalize_control_fixture_registry({
                    RUNNER._runner_fixture_key(broken): broken,
                })

        for label, mutate in (
            ("candidate", lambda row: row.update({
                "candidate_values": ["missing_07"],
            })),
            ("root-id", lambda row: row.update({"id": 1})),
            ("relation-root", lambda row: row["relations"][0].update({
                "root_address": "0x088669B0",
            })),
            ("required-flag", lambda row: row[
                "required_value_in_matrix_case"
            ]["flag_values"][6].update({"value": False})),
            ("required-binding", lambda row: row[
                "required_value_in_matrix_case"
            ]["root_source_binding"].update({"byte_length": 1})),
        ):
            broken = self._ruin_seal_external(reference)
            mutate(broken)
            with self.subTest(control=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [broken], empty_state, registry, f"ruin-{label}",
                )

        generic_state = deepcopy(empty_state)
        generic_state["flags"] = [{"id": 0x11CC, "value": False}]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "generic independent",
        ):
            RUNNER._normalize_external_controls(
                [self._ruin_seal_external(reference)], generic_state,
                registry, "ruin-generic-double-apply",
            )

        row = RUNNER._normalize_external_controls(
            [self._ruin_seal_external(reference)], empty_state, registry,
            "ruin-observation",
        )[0]
        observed = [{
            "kind": "RUIN_SEAL_PREFIX",
            "root_address": fixture["root_address"],
            "scenario_id": fixture["scenario_id"],
            "layout_ref": reference,
            "first_missing_index": fixture["first_missing_index"],
            "all_seals": fixture["all_seals"],
            "completed": fixture["completed"],
            "flag_values": deepcopy(fixture["flags"]),
            "root_source_binding": deepcopy(fixture["root_source_binding"]),
            "binary_fixture_verified": True,
            "preinteraction_readback_exact": True,
            "exact": True,
        }]
        for label, mutate in (
            ("flag", lambda value: value[0]["flag_values"][0].update({
                "value": False,
            })),
            ("root", lambda value: value[0].update({
                "root_address": "0x088669B0",
            })),
            ("binding", lambda value: value[0][
                "root_source_binding"
            ].update({"byte_length": 1})),
        ):
            broken = deepcopy(observed)
            mutate(broken)
            with self.subTest(observation=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._validate_deferred_external_controls(
                    broken, [row], label=f"ruin-observation-{label}",
                )

    def test_facility_session_49_manifest_tsv_and_binary_are_exact(
        self,
    ) -> None:
        manifest = RUNNER._facility_session_manifest()
        self.assertEqual(manifest["scenario_count"], 49)
        self.assertEqual(
            manifest["family_counts"],
            {"mirage": 33, "factory": 10, "codex": 6},
        )
        self.assertTrue(manifest["shared_root_single_domain"])
        self.assertTrue(manifest["cartesian_product_forbidden"])
        fixtures = {}
        for manifest_row in manifest["scenarios"]:
            fixture = self._facility_fixture(
                str(manifest_row["family"]),
                str(manifest_row["scenario_id"]),
            )
            fixtures[RUNNER._runner_fixture_key(fixture)] = fixture
        self.assertEqual(len(fixtures), 49)
        registry = RUNNER._normalize_control_fixture_registry(fixtures)
        empty_state = {
            key: [] for key in ("flags", "vars", "items", "trainers")
        }
        normalized_rows = []
        for manifest_row in manifest["scenarios"]:
            family = str(manifest_row["family"])
            scenario_id = str(manifest_row["scenario_id"])
            fixture = self._facility_fixture(family, scenario_id)
            reference = RUNNER._runner_fixture_key(fixture)
            with self.subTest(scenario=fixture["scenario_key"]):
                row = RUNNER._normalize_external_controls(
                    [self._facility_external(
                        reference, family=family, scenario_id=scenario_id,
                    )], empty_state, registry,
                    f"facility-{family}-{scenario_id}",
                )[0]
                normalized_rows.append(row)
                root = int(str(
                    fixture["source_binding"]["root_address"]
                ), 0)
                encoded = RUNNER._encode_external_control(row)
                encoded_fields = encoded.split("@")
                self.assertEqual(len(encoded_fields), 4)
                self.assertEqual(encoded_fields[0], "FACILITY_SESSION")
                self.assertEqual(
                    int(encoded_fields[1]),
                    RUNNER._FACILITY_CONTROL_IDS[root],
                )
                values = encoded_fields[2].split(",")
                self.assertEqual(len(values), 25)
                self.assertEqual(values[:4], [
                    scenario_id, reference, family,
                    "-" if fixture["reception_branch"] is None
                    else fixture["reception_branch"],
                ])
                self.assertEqual(int(values[4]), root)
                self.assertEqual(
                    encoded_fields[3],
                    f"{RUNNER._FACILITY_SESSION_RELATION}:"
                    f"0x{root:08X}",
                )
                projected = RUNNER._normalize_event_compact_external_controls(
                    [{
                        "kind": "FACILITY_SESSION",
                        "id": RUNNER._FACILITY_CONTROL_IDS[root],
                        "value": deepcopy(
                            row["required_value_in_matrix_case"]
                        ),
                        "owner_keys": [
                            "FACILITY_SESSION:MIRAGE" if family == "mirage"
                            else "FACILITY_SESSION:FACTORY_OR_CODEX"
                        ],
                        "relation_evidence": deepcopy(row["relations"]),
                        "fixture_keys": [reference],
                    }],
                    registry, f"facility-compact-{family}-{scenario_id}",
                    allowed_owner_ids={
                        "FACILITY_SESSION:MIRAGE" if family == "mirage"
                        else "FACILITY_SESSION:FACTORY_OR_CODEX"
                    },
                )
                self.assertEqual(
                    projected[0]["required_value_in_matrix_case"],
                    row["required_value_in_matrix_case"],
                )

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            RUNNER.write_control_fixture_files(destination, registry)
            for reference, fixture in registry.items():
                raw = (destination / f"{reference}.bin").read_bytes()
                payload = RUNNER._facility_canonical_bytes(fixture)
                projection = RUNNER._facility_transport_projection(fixture)
                self.assertEqual(
                    len(raw), RUNNER._FACILITY_SESSION_BINARY_HEADER_BYTES
                    + len(payload),
                )
                self.assertEqual(raw[:8], b"S61FAC01")
                self.assertEqual(raw[8:40], bytes.fromhex(reference))
                self.assertEqual(
                    raw[40:72], bytes.fromhex(
                        RUNNER._FACILITY_SESSION_REGISTRY_SOURCE_SHA256
                    ),
                )
                self.assertEqual(
                    raw[72:104], bytes.fromhex(str(fixture["trace_sha256"])),
                )
                self.assertEqual(
                    raw[104:136], bytes.fromhex(
                        projection["resume_points_sha256"]
                    ),
                )
                self.assertEqual(
                    raw[136:168], bytes.fromhex(projection["fields_sha256"]),
                )
                self.assertEqual(
                    raw[168:200], bytes.fromhex(
                        projection["source_binding_sha256"]
                    ),
                )
                self.assertEqual(
                    raw[200:232], bytes.fromhex(
                        projection["initialization_sha256"]
                    ),
                )
                self.assertEqual(
                    int.from_bytes(raw[232:236], "little"), len(payload),
                )
                self.assertEqual(
                    int.from_bytes(raw[236:240], "little"),
                    int(str(projection["root_address"]), 0),
                )
                self.assertEqual(
                    int.from_bytes(raw[240:242], "little"),
                    projection["manifest_ordinal"],
                )
                self.assertEqual(
                    int.from_bytes(raw[242:244], "little"),
                    fixture["trace_count"],
                )
                self.assertEqual(
                    int.from_bytes(raw[244:246], "little"),
                    len(fixture["resume_points"]),
                )
                self.assertEqual(raw[249], projection["region_count"])
                self.assertEqual(raw[250], projection["source_count"])
                self.assertEqual(raw[251], projection["export_count"])
                self.assertEqual(
                    raw[252],
                    int(projection["prepare_fault_wrapper_required"]),
                )
                self.assertEqual(raw[253:256], bytes(3))
                expected_regions = []
                for region in projection["regions"]:
                    expected_regions.extend((
                        int(str(region["address"]), 0), region["size"],
                    ))
                expected_regions.extend(
                    [0, 0] * (3 - projection["region_count"])
                )
                self.assertEqual(
                    list(struct.unpack("<IIIIII", raw[256:280])),
                    expected_regions,
                )
                self.assertEqual(raw[280:], payload)
                self.assertEqual(hashlib.sha256(payload).hexdigest(), reference)

        from tools.stage61_interaction_oracle import runner_control_abi_contract

        self.assertEqual(
            runner_control_abi_contract()["required_value_types"]
            ["FACILITY_SESSION"],
            RUNNER._FACILITY_SESSION_REQUIRED_VALUE_TYPE,
        )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        for exact in (
            "S61_CONTROL_FACILITY_SESSION",
            'strcmp(value, "FACILITY_SESSION") == 0',
            "SOURCE_BOUND_FACILITY_SESSION_TRACE_EXACT",
            "S61_FACILITY_SESSION_HEADER_SIZE == 280U",
            "s61_facility_manifest",
            "s61_load_facility_session_fixture",
            "s61_attach_facility_execution",
            "s61_sample_facility_execution",
            "s61_finalize_facility_execution",
            "S61_FACILITY_SESSION_MAX_TRACE",
            "S61_FACILITY_SESSION_NATIVE_COUNT",
            "native_boundaries",
            "root_before_first_native",
            "raw_ewram_preimage_used",
            "FactoryHighModesV2_PrepareBattleStage61Adapter",
            "Stage61Facility_TestSetFactoryPrepareFault",
        ):
            self.assertIn(exact, source)

    def test_facility_active_terminal_and_runtime_trace_are_correlated(
        self,
    ) -> None:
        for family, scenario_id, expected_terminal in (
            (
                "factory", "exchange_commit",
                RUNNER._FACILITY_ACTIVE_CONTINUATION_TERMINAL,
            ),
            ("factory", "battle_loss", "FIELD_RELEASE"),
        ):
            fixture = self._facility_fixture(family, scenario_id)
            reference = RUNNER._runner_fixture_key(fixture)
            registry = RUNNER._normalize_control_fixture_registry({
                reference: fixture,
            })
            empty_state = {
                key: [] for key in ("flags", "vars", "items", "trainers")
            }
            control = RUNNER._normalize_external_controls(
                [self._facility_external(
                    reference, family=family, scenario_id=scenario_id,
                )], empty_state, registry,
                f"facility-terminal-{scenario_id}",
            )[0]
            sequence = {
                "post_battle_continuation": {
                    "field_terminal_kind": expected_terminal,
                },
            }
            RUNNER._validate_facility_continuation_terminals(
                [sequence], [control], f"facility-terminal-{scenario_id}",
            )
            broken_sequence = deepcopy(sequence)
            broken_sequence["post_battle_continuation"][
                "field_terminal_kind"
            ] = (
                "FIELD_RELEASE"
                if expected_terminal != "FIELD_RELEASE"
                else RUNNER._FACILITY_ACTIVE_CONTINUATION_TERMINAL
            )
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "terminal相関不一致",
            ):
                RUNNER._validate_facility_continuation_terminals(
                    [broken_sequence], [control],
                    f"facility-terminal-forged-{scenario_id}",
                )

            observed = self._facility_observation(control)
            self.assertEqual(
                RUNNER._validate_deferred_external_controls(
                    [observed], [control],
                    label=f"facility-observation-{scenario_id}",
                ),
                [observed],
            )
            for mutation_label, mutation in (
                ("terminal", lambda row: row["terminal"].update({
                    "terminal_kind": "FIELD_RELEASE"
                    if expected_terminal != "FIELD_RELEASE"
                    else RUNNER._FACILITY_ACTIVE_CONTINUATION_TERMINAL,
                })),
                ("trace", lambda row: row["native_boundaries"][0].update({
                    "status": 0xFFFF,
                })),
                ("host-write", lambda row: row["host_writes"].update({
                    "lifecycle_calls": 1,
                })),
            ):
                broken = deepcopy(observed)
                mutation(broken)
                with self.subTest(
                    scenario=scenario_id, mutation=mutation_label,
                ), self.assertRaises(RUNNER.Stage61MgbaError):
                    RUNNER._validate_deferred_external_controls(
                        [broken], [control],
                        label=(
                            f"facility-observation-{scenario_id}-"
                            f"{mutation_label}"
                        ),
                    )

    def test_facility_session_forgery_and_missing_seam_fail_closed(self) -> None:
        fixture = self._facility_fixture("factory", "prepare_error")
        reference = RUNNER._runner_fixture_key(fixture)
        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        for label, mutate in (
            ("trace", lambda row: row["trace"][0].update({"status": 9})),
            ("root", lambda row: row["source_binding"].update({
                "root_address": "0x09391A08",
            })),
            ("region", lambda row: row["source_binding"][
                "ram_regions"
            ][0].update({"size": 1})),
            ("raw-ewram", lambda row: row["initialization"].update({
                "raw_ewram_preimage": "00",
            })),
            ("helper-sha", lambda row: row["source_binding"][
                "scenario_registry"
            ].update({"sha256": "0" * 64})),
        ):
            broken = deepcopy(fixture)
            mutate(broken)
            with self.subTest(fixture=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "helper/source/trace",
            ):
                RUNNER._normalize_control_fixture_registry({
                    RUNNER._runner_fixture_key(broken): broken,
                })

        empty_state = {
            key: [] for key in ("flags", "vars", "items", "trainers")
        }
        for label, mutate in (
            ("missing", lambda row: row.update({
                "candidate_values": ["factory/prepare_error"],
            })),
            ("root", lambda row: row["relations"][0].update({
                "root_address": "0x09391A08",
            })),
            ("id", lambda row: row.update({"id": 0})),
            ("trace", lambda row: row[
                "required_value_in_matrix_case"
            ].update({"trace_sha256": "0" * 64})),
            ("direct-ewram", lambda row: row[
                "required_value_in_matrix_case"
            ]["initialization"].update({"raw_ewram_preimage": "00"})),
        ):
            broken = self._facility_external(
                reference, family="factory", scenario_id="prepare_error",
            )
            mutate(broken)
            with self.subTest(control=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [broken], empty_state, registry, f"facility-{label}",
                )

        adapter = 0x09D00000
        setter = 0x09D00020
        symbols = {
            "FactoryHighModesV2_PrepareBattleStage61Adapter": adapter,
            "Stage61Facility_TestSetFactoryPrepareFault": setter,
        }
        rom = bytearray((ROOT / RUNNER.DEFAULT_STAGE60_ROM).read_bytes())
        adapter_raw = bytes.fromhex("00b5012000bd")
        setter_raw = bytes.fromhex("00b5012000bd")
        rom[adapter - 0x08000000:
            adapter - 0x08000000 + len(adapter_raw)] = adapter_raw
        rom[setter - 0x08000000:
            setter - 0x08000000 + len(setter_raw)] = setter_raw
        script = bytearray(RUNNER._FACILITY_PREPARE_SCRIPT_PREIMAGE)
        replacement = struct.pack("<I", adapter | 1)
        script[1:5] = replacement
        script_offset = RUNNER._FACILITY_PREPARE_SCRIPT_ADDRESS - 0x08000000
        rom[script_offset:script_offset + len(script)] = script
        source_binding = []
        for path_text in RUNNER._FACILITY_PREPARE_SOURCE_PATHS:
            raw = (ROOT / path_text).read_bytes()
            source_binding.append({
                "path": path_text, "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            })
        audit = {
            "status": "PASS",
            "physical_script": {
                "address": (
                    f"0x{RUNNER._FACILITY_PREPARE_SCRIPT_ADDRESS:08X}"
                ),
                "byte_length": len(script),
                "stage60_sha256": (
                    RUNNER._FACILITY_PREPARE_SCRIPT_STAGE60_SHA256
                ),
                "stage61_sha256": hashlib.sha256(script).hexdigest(),
            },
            "pointer_patch": {
                "address": (
                    f"0x{RUNNER._FACILITY_PREPARE_POINTER_SITE:08X}"
                ),
                "expected_hex": RUNNER._FACILITY_PREPARE_POINTER_PREIMAGE,
                "replacement_hex": replacement.hex(),
                "original_target": (
                    f"0x{RUNNER._FACILITY_PREPARE_ORIGINAL_ENTRY:08X}"
                ),
                "adapter_target": f"0x{adapter | 1:08X}",
            },
            "adapter": {
                "symbol": "FactoryHighModesV2_PrepareBattleStage61Adapter",
                "address": f"0x{adapter:08X}",
                "byte_length": len(adapter_raw),
                "sha256": hashlib.sha256(adapter_raw).hexdigest(),
                "normal_delegate": (
                    f"0x{RUNNER._FACILITY_PREPARE_ORIGINAL_ENTRY:08X}"
                ),
            },
            "fault_setter": {
                "symbol": "Stage61Facility_TestSetFactoryPrepareFault",
                "address": f"0x{setter:08X}",
                "byte_length": len(setter_raw),
                "sha256": hashlib.sha256(setter_raw).hexdigest(),
                "lifecycle_calls": 0,
            },
            "original_delegate": {
                "address": (
                    f"0x{RUNNER._FACILITY_PREPARE_ORIGINAL_ENTRY:08X}"
                ),
                "byte_length": RUNNER._FACILITY_PREPARE_ORIGINAL_SIZE,
                "sha256": RUNNER._FACILITY_PREPARE_ORIGINAL_SHA256,
            },
            "arm_schema": deepcopy(RUNNER._FACILITY_PREPARE_ARM_SCHEMA),
            "source_binding": source_binding,
            "assertions": {
                key: True for key in RUNNER._FACILITY_PREPARE_ASSERTIONS
            },
        }
        metadata = {
            "runtime": {"symbols": symbols},
            "audit": {"factory_prepare_error_adapter": audit},
        }
        self.assertEqual(
            RUNNER._facility_runtime_symbol_environment(
                metadata, required=True, rom_raw=bytes(rom),
            ),
            {
                "S61_FACTORY_PREPARE_BATTLE_STAGE61_ADAPTER_SYMBOL":
                    str(adapter),
                "S61_FACILITY_TEST_SET_FACTORY_PREPARE_FAULT_SYMBOL":
                    str(setter),
            },
        )
        odd_symbols = deepcopy(metadata)
        odd_symbols["runtime"]["symbols"][
            "FactoryHighModesV2_PrepareBattleStage61Adapter"
        ] |= 1
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError,
            RUNNER._FACILITY_PREPARE_ERROR_SEAM,
        ):
            RUNNER._facility_runtime_symbol_environment(
                odd_symbols, required=True, rom_raw=bytes(rom),
            )
        for missing in symbols:
            broken = deepcopy(metadata)
            del broken["runtime"]["symbols"][missing]
            with self.subTest(missing=missing), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError,
                RUNNER._FACILITY_PREPARE_ERROR_SEAM,
            ):
                RUNNER._facility_runtime_symbol_environment(
                    broken, required=True, rom_raw=bytes(rom),
                )

    def test_gift_storage_30_layout_sweep_is_a_production_case(self) -> None:
        schema = self._gift_storage_sweep_schema()
        controls = RUNNER.gift_storage_transaction_sweep_controls(schema)
        self.assertEqual(len(controls), 30)
        self.assertEqual(
            [
                row["required_value_in_matrix_case"]["scenario_id"]
                for row in controls
            ],
            list(RUNNER._GIFT_STORAGE_TRANSACTION_RUNNER_SCENARIO_IDS),
        )
        self.assertIn(
            "gift_storage_transaction_sweep",
            RUNNER.CASE_DOMAINS["regressions"],
        )
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "gift-storage-sweep.txt"
            self.assertEqual(
                RUNNER.write_gift_storage_transaction_sweep_manifest(
                    manifest, schema,
                ),
                controls,
            )
            lines = manifest.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 30)
            self.assertTrue(all("\t" not in line for line in lines))
            self.assertIn("@party_space,", lines[0])
            self.assertIn("@storage_full,", lines[-1])
        document = self._gift_storage_sweep_document(controls)
        self.assertEqual(
            RUNNER._validate_gift_storage_transaction_sweep_result(
                document, controls,
            ),
            document,
        )
        c_document = deepcopy(document)
        c_document["framebuffer_artifacts"] = []
        normalized = RUNNER._validate_case(
            c_document, "gift_storage_transaction_sweep", {}, {}, {}, {},
            gift_storage_expected=controls,
        )
        normalized["artifacts"] = []
        self.assertEqual(
            RUNNER.validate_final_mgba_case_result(
                "gift_storage_transaction_sweep", normalized,
            )["fixture_count"],
            30,
        )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("s61_case_gift_storage_transaction_sweep", source)
        self.assertIn("S61_GIFT_STORAGE_SWEEP_MANIFEST is required", source)
        runner_source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn('process_env["S61_GIFT_STORAGE_SWEEP_MANIFEST"]', runner_source)

    def test_gift_storage_30_layout_sweep_negative_is_fail_closed(self) -> None:
        schema = self._gift_storage_sweep_schema()
        controls = RUNNER.gift_storage_transaction_sweep_controls(schema)
        document = self._gift_storage_sweep_document(controls)
        mutations = {
            "order": lambda item: item["results"].__setitem__(
                slice(0, 2), list(reversed(item["results"][:2])),
            ),
            "fixture-ref": lambda item: item["results"][1].__setitem__(
                "fixture_ref", item["results"][0]["fixture_ref"],
            ),
            "aggregate": lambda item: item["result_counts"].__setitem__(
                "storage", 27,
            ),
            "runtime-result": lambda item: item["results"][15].__setitem__(
                "actual_result", 2,
            ),
            "postimage": lambda item: item["results"][29].__setitem__(
                "storage_postimage_exact", False,
            ),
        }
        for label, mutate in mutations.items():
            broken = deepcopy(document)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._validate_gift_storage_transaction_sweep_result(
                    broken, controls,
                )
        missing = deepcopy(schema)
        missing["dedicated_fixture_sweeps"][
            "GIFT_STORAGE_TRANSACTION_STATE"
        ]["scenarios"].pop()
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "registry"):
            RUNNER.gift_storage_transaction_sweep_controls(missing)

    def test_daycare_transaction_schema_fixture_tsv_and_binary_are_exact(
        self,
    ) -> None:
        fixtures = {
            RUNNER._runner_fixture_key(
                self._daycare_transaction_fixture(scenario_id)
            ): self._daycare_transaction_fixture(scenario_id)
            for scenario_id in RUNNER._ALL_DAYCARE_TRANSACTION_SCENARIO_IDS
        }
        registry = RUNNER._normalize_control_fixture_registry(fixtures)
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        for reference, fixture in registry.items():
            scenario_id = str(fixture["scenario_id"])
            with self.subTest(scenario=scenario_id):
                rows = RUNNER._normalize_external_controls(
                    [self._daycare_transaction_external(
                        reference, scenario_id=scenario_id,
                    )], state, registry, f"daycare-{scenario_id}",
                )
                value = rows[0]["required_value_in_matrix_case"]
                route5 = scenario_id.startswith("route5_")
                self.assertEqual(
                    RUNNER._encode_external_control(rows[0]),
                    "@".join((
                        "DAYCARE_TRANSACTION_STATE", "1" if route5 else "0",
                        ",".join((
                            scenario_id, reference,
                            str(fixture["party_count"]),
                            str(fixture["money"]),
                            str(value["party_sha256"]),
                            str(value["daycare_sha256"]),
                        )),
                        (
                            RUNNER._ROUTE5_DAYCARE_TRANSACTION_RELATION
                            if route5 else RUNNER._DAYCARE_TRANSACTION_RELATION
                        ) + ":0",
                    )),
                )

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            RUNNER.write_control_fixture_files(destination, registry)
            for reference, fixture in registry.items():
                raw = (destination / f"{reference}.bin").read_bytes()
                scenario = str(fixture["scenario_id"]).encode("ascii")
                self.assertEqual(len(raw), 1028)
                self.assertEqual(raw[:8], b"S61DCT01")
                self.assertEqual(raw[8:40], bytes.fromhex(reference))
                self.assertEqual(
                    raw[40:72], hashlib.sha256(bytes.fromhex(
                        str(fixture["party_raw_hex"])
                    )).digest(),
                )
                self.assertEqual(
                    raw[72:104], hashlib.sha256(bytes.fromhex(
                        str(fixture["daycare_raw_hex"])
                    )).digest(),
                )
                self.assertEqual(raw[104:104 + len(scenario)], scenario)
                self.assertEqual(raw[104 + len(scenario):136], bytes(
                    32 - len(scenario)
                ))
                self.assertEqual(raw[136:140], bytes((
                    int(fixture["party_count"]), 0, 0, 1,
                )))
                self.assertEqual(
                    int.from_bytes(raw[140:144], "little"),
                    fixture["money"],
                )
                self.assertEqual(
                    raw[144:744].hex(), fixture["party_raw_hex"],
                )
                self.assertEqual(
                    raw[744:1028].hex(), fixture["daycare_raw_hex"],
                )

        reference = next(iter(registry))
        external = self._daycare_transaction_external(
            reference, scenario_id=str(registry[reference]["scenario_id"]),
        )
        compact = {
            "kind": external["kind"], "id": 0,
            "value": external["required_value_in_matrix_case"],
            "owner_keys": ["OBJECT:001/003:000"],
            "relation_evidence": external["relations"],
            "fixture_keys": [reference],
        }
        projected = RUNNER._normalize_event_compact_external_controls(
            [compact], registry, "daycare-compact",
            allowed_owner_ids={"OBJECT:001/003:000"},
        )
        self.assertEqual(projected[0]["fixture_keys"], [reference])

    def test_daycare_transaction_fixture_and_hash_tamper_fail_closed(
        self,
    ) -> None:
        fixture = self._daycare_transaction_fixture()
        reference = RUNNER._runner_fixture_key(fixture)
        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        mutations = {
            "extra": lambda row: row.update({"extra": 0}),
            "party-length": lambda row: row.update({
                "party_raw_hex": str(row["party_raw_hex"])[:-2],
            }),
            "daycare-length": lambda row: row.update({
                "daycare_raw_hex": str(row["daycare_raw_hex"])[:-2],
            }),
            "party-case": lambda row: row.update({
                "party_raw_hex": str(row["party_raw_hex"]).upper(),
            }),
            "pending": lambda row: row.update({
                "pending_daycare_egg_flag": True,
            }),
            "queue": lambda row: row.update({"queued_egg_count": 1}),
            "pc-space": lambda row: row.update({"pc_has_space": False}),
            "scenario": lambda row: row.update({
                "scenario_id": "empty_deposit",
            }),
            "party-byte": lambda row: row.update({
                "party_raw_hex": (
                    "01" + str(row["party_raw_hex"])[2:]
                ),
            }),
            "daycare-byte": lambda row: row.update({
                "daycare_raw_hex": (
                    "01" + str(row["daycare_raw_hex"])[2:]
                ),
            }),
        }
        for label, mutate in mutations.items():
            broken = deepcopy(fixture)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_control_fixture_registry({
                    RUNNER._runner_fixture_key(broken): broken,
                })
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "SHA"):
            RUNNER._normalize_control_fixture_registry({"0" * 64: fixture})

        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        for field, replacement in (
            ("party_sha256", "0" * 64),
            ("daycare_sha256", "f" * 64),
            ("party_count", 1),
            ("money", 99),
        ):
            external = self._daycare_transaction_external(reference)
            external["required_value_in_matrix_case"][field] = replacement
            with self.subTest(required_field=field), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "fixture scalar/hash",
            ):
                RUNNER._normalize_external_controls(
                    [external], state, registry, f"daycare-{field}",
                )

    def test_daycare_transaction_relation_owner_and_kind_boundary_are_exact(
        self,
    ) -> None:
        fixture = self._daycare_transaction_fixture()
        reference = RUNNER._runner_fixture_key(fixture)
        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        mutations = {
            "id": lambda row: row.update({"id": 1}),
            "candidate": lambda row: row.update({
                "candidate_values": ["one_sufficient"],
            }),
            "legacy-kind": lambda row: row.update({
                "kind": "DAYCARE_OCCUPIED",
            }),
            "operator": lambda row: row["relations"][0].update({
                "operator": "EVENT_DESIGN_SOURCE_PHYSICAL_BOOL",
            }),
            "owner-order": lambda row: row["relations"][0].update({
                "state_owners": list(reversed(
                    RUNNER._DAYCARE_TRANSACTION_STATE_OWNERS
                )),
            }),
            "owner-extra": lambda row: row["relations"][0][
                "state_owners"
            ].append("VAR_RESULT"),
            "duplicate": lambda row: row["relations"].append(
                deepcopy(row["relations"][0])
            ),
        }
        for label, mutate in mutations.items():
            broken = self._daycare_transaction_external(reference)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [broken], state, registry, f"daycare-{label}",
                )
        duplicate = self._daycare_transaction_external(reference)
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "control owner重複",
        ):
            RUNNER._normalize_external_controls(
                [duplicate, deepcopy(duplicate)], state, registry,
                "daycare-owner-duplicate",
            )

    def test_daycare_transaction_runner_abi_and_c_apply_are_closed(
        self,
    ) -> None:
        from tools.stage61_interaction_oracle import runner_control_abi_contract

        oracle_abi = runner_control_abi_contract()
        oracle_kinds = set(oracle_abi["required_value_types"])
        self.assertIn(
            RUNNER._CONTROL_EXTERNAL_KINDS - oracle_kinds,
            (set(), {"RFU_SESSION"}),
        )
        self.assertEqual(
            oracle_kinds - RUNNER._CONTROL_EXTERNAL_KINDS,
            set(),
        )
        patched_abi = deepcopy(oracle_abi)
        patched_abi["required_value_types"]["RFU_SESSION"] = deepcopy(
            RUNNER._RFU_SESSION_REQUIRED_VALUE_TYPE
        )
        with patch(
            "tools.stage61_interaction_oracle.runner_control_abi_contract",
            return_value=patched_abi,
        ):
            normalized_abi = RUNNER._runner_control_abi_contract()
        self.assertEqual(
            normalized_abi["required_value_types"][
                "DAYCARE_TRANSACTION_STATE"
            ],
            RUNNER._DAYCARE_TRANSACTION_REQUIRED_VALUE_TYPE,
        )
        self.assertEqual(
            normalized_abi["layouts"]["daycare_transaction"]["relation"],
            RUNNER._DAYCARE_TRANSACTION_RELATION,
        )
        self.assertEqual(
            normalized_abi["layouts"]["route5_daycare_transaction"],
            oracle_abi["layouts"]["route5_daycare_transaction"],
        )

        source = SOURCE_PATH.read_text(encoding="utf-8")
        for exact in (
            "S61_CONTROL_DAYCARE_TRANSACTION_STATE",
            'strcmp(value, "DAYCARE_TRANSACTION_STATE") == 0',
            "FOUR_ISLAND_DAYCARE_PARTY_DAYCARE_MONEY_TRANSACTION_EXACT",
            "ROUTE5_DAYCARE_PARTY_SINGLE_MON_MONEY_TRANSACTION_EXACT",
            "S61_SAVE1_ROUTE5_DAYCARE_OFFSET = 0x3C98U",
            "catalog DAYCARE_TRANSACTION tuple is outside fixed registry",
            "catalog DAYCARE_TRANSACTION exact relation differs",
            "S61_DAYCARE_TRANSACTION_FIXTURE_SIZE == 1028U",
            "s61_load_daycare_transaction_fixture",
            "s61_apply_daycare_transaction_fixture",
            "s61_verify_daycare_transaction_fixture",
            "WORLD_SET_MONEY",
            "WORLD_PENDING_DAYCARE_EGG_FLAG = 0x0266U",
            "S61_MODERN_EGG_QUEUE_COUNT_OFFSET = 512U",
            "S61_POKEMON_STORAGE_FIRST_BOX_MON_OFFSET = 4U",
            "daycare_transaction_control_contract",
        ):
            self.assertIn(exact, source)
        for scenario_id in RUNNER._ALL_DAYCARE_TRANSACTION_SCENARIO_IDS:
            fixture = self._daycare_transaction_fixture(scenario_id)
            for exact in (
                scenario_id,
                RUNNER._runner_fixture_key(fixture),
                hashlib.sha256(bytes.fromhex(
                    str(fixture["party_raw_hex"])
                )).hexdigest(),
                hashlib.sha256(bytes.fromhex(
                    str(fixture["daycare_raw_hex"])
                )).hexdigest(),
            ):
                self.assertIn(exact, source)

    def test_party_move_transaction_schema_tsv_and_binary_are_exact(
        self,
    ) -> None:
        fixtures = {
            RUNNER._runner_fixture_key(
                self._party_move_transaction_fixture(scenario_id)
            ): self._party_move_transaction_fixture(scenario_id)
            for scenario_id in RUNNER._PARTY_MOVE_TRANSACTION_SCENARIO_IDS
        }
        registry = RUNNER._normalize_control_fixture_registry(fixtures)
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        normalized_by_reference = {}
        for reference, fixture in registry.items():
            scenario_id = str(fixture["scenario_id"])
            with self.subTest(scenario=scenario_id):
                row = RUNNER._normalize_external_controls(
                    [self._party_move_transaction_external(
                        reference, scenario_id=scenario_id,
                    )], state, registry, f"party-move-{scenario_id}",
                )[0]
                normalized_by_reference[reference] = row
                value = row["required_value_in_matrix_case"]
                sequence = value["party_selection_sequence"]

                def nullable(item: object) -> str:
                    return str(
                        RUNNER._PARTY_MOVE_TRANSACTION_NULL_U16
                        if item is None else item
                    )

                expected_values = [
                    scenario_id, reference, str(fixture["family"]),
                    str(fixture["party_count"]),
                    str(value["party_sha256"]), str(len(sequence)),
                    str(sequence[0]),
                    str(
                        RUNNER._PARTY_MOVE_TRANSACTION_NULL_U16
                        if len(sequence) == 1 else sequence[1]
                    ),
                    nullable(value["selected_move_slot"]),
                    nullable(value["selected_relearn_move"]),
                    nullable(value["teach_outcome"]),
                    nullable(value["expected_relearnable_count"]),
                    "-" if value["payment_policy"] is None
                    else str(value["payment_policy"]),
                    str(value["expected_action"]),
                ]
                self.assertEqual(
                    RUNNER._encode_external_control(row),
                    "@".join((
                        "PARTY_MOVE_TRANSACTION_STATE", "0",
                        ",".join(expected_values),
                        RUNNER._PARTY_MOVE_TRANSACTION_RELATION + ":0",
                    )),
                )

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            RUNNER.write_control_fixture_files(destination, registry)
            for reference, fixture in registry.items():
                raw = (destination / f"{reference}.bin").read_bytes()
                scenario = str(fixture["scenario_id"]).encode("ascii")
                action = str(fixture["expected_action"]).encode("ascii")
                sequence = fixture["party_selection_sequence"]
                self.assertEqual(len(raw), 764)
                self.assertEqual(raw[:8], b"S61PMT01")
                self.assertEqual(raw[8:40], bytes.fromhex(reference))
                self.assertEqual(
                    raw[40:72], hashlib.sha256(bytes.fromhex(
                        str(fixture["party_raw_hex"])
                    )).digest(),
                )
                self.assertEqual(raw[72:72 + len(scenario)], scenario)
                self.assertEqual(
                    raw[72 + len(scenario):120],
                    bytes(48 - len(scenario)),
                )
                self.assertEqual(
                    raw[120], 0 if fixture["family"] == "RELEARNER" else 1,
                )
                self.assertEqual(raw[121], fixture["party_count"])
                self.assertEqual(raw[122], len(sequence))
                self.assertEqual(raw[123], sequence[0])
                self.assertEqual(
                    raw[124], 0xFF if len(sequence) == 1 else sequence[1],
                )
                self.assertEqual(
                    raw[125], 0xFF
                    if fixture["selected_move_slot"] is None
                    else fixture["selected_move_slot"],
                )
                self.assertEqual(
                    raw[126], 0xFF if fixture["teach_outcome"] is None
                    else fixture["teach_outcome"],
                )
                self.assertEqual(
                    raw[127], 0xFF
                    if fixture["expected_relearnable_count"] is None
                    else fixture["expected_relearnable_count"],
                )
                self.assertEqual(
                    int.from_bytes(raw[128:130], "little"),
                    RUNNER._PARTY_MOVE_TRANSACTION_NULL_U16
                    if fixture["selected_relearn_move"] is None
                    else fixture["selected_relearn_move"],
                )
                self.assertEqual(
                    raw[130], int(fixture["payment_policy"] is not None),
                )
                self.assertEqual(raw[131], 0)
                self.assertEqual(raw[132:132 + len(action)], action)
                self.assertEqual(
                    raw[132 + len(action):164], bytes(32 - len(action)),
                )
                self.assertEqual(raw[164:].hex(), fixture["party_raw_hex"])

        reference = next(iter(registry))
        external = normalized_by_reference[reference]
        compact = {
            "kind": external["kind"], "id": 0,
            "value": external["required_value_in_matrix_case"],
            "owner_keys": ["OBJECT:001/003:000"],
            "relation_evidence": external["relations"],
            "fixture_keys": [reference],
        }
        projected = RUNNER._normalize_event_compact_external_controls(
            [compact], registry, "party-move-compact",
            allowed_owner_ids={"OBJECT:001/003:000"},
        )
        self.assertEqual(projected[0]["fixture_keys"], [reference])

    def test_party_move_transaction_fixture_and_value_tamper_fail_closed(
        self,
    ) -> None:
        fixture = self._party_move_transaction_fixture()
        reference = RUNNER._runner_fixture_key(fixture)
        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        mutations = {
            "extra": lambda row: row.update({"extra": 0}),
            "family": lambda row: row.update({"family": "DELETER"}),
            "party-count": lambda row: row.update({"party_count": 1}),
            "party-length": lambda row: row.update({
                "party_raw_hex": str(row["party_raw_hex"])[2:],
            }),
            "party-case": lambda row: row.update({
                "party_raw_hex": str(row["party_raw_hex"]).upper(),
            }),
            "party-byte": lambda row: row.update({
                "party_raw_hex": "01" + str(row["party_raw_hex"])[2:],
            }),
            "selection": lambda row: row.update({
                "party_selection_sequence": [7],
            }),
            "move-slot": lambda row: row.update({
                "selected_move_slot": None,
            }),
            "relearn-move": lambda row: row.update({
                "selected_relearn_move": None,
            }),
            "teach": lambda row: row.update({"teach_outcome": 0}),
            "relearnable": lambda row: row.update({
                "expected_relearnable_count": None,
            }),
            "payment": lambda row: row.update({"payment_policy": None}),
            "action": lambda row: row.update({
                "expected_action": "PARTY_CANCEL",
            }),
            "scenario": lambda row: row.update({
                "scenario_id": "relearner_teach_replace_slot",
            }),
        }
        for label, mutate in mutations.items():
            broken = deepcopy(fixture)
            mutate(broken)
            with self.subTest(fixture=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_control_fixture_registry({
                    RUNNER._runner_fixture_key(broken): broken,
                })
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "SHA"):
            RUNNER._normalize_control_fixture_registry({"0" * 64: fixture})

        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        value_mutations = {
            "party-sha": lambda value: value.update({
                "party_sha256": "0" * 64,
            }),
            "family": lambda value: value.update({"family": "DELETER"}),
            "sequence": lambda value: value.update({
                "party_selection_sequence": [7],
            }),
            "move-slot": lambda value: value.update({
                "selected_move_slot": None,
            }),
            "relearn-move": lambda value: value.update({
                "selected_relearn_move": 185,
            }),
            "teach": lambda value: value.update({"teach_outcome": 0}),
            "relearnable": lambda value: value.update({
                "expected_relearnable_count": 4,
            }),
            "payment": lambda value: value.update({"payment_policy": None}),
            "action": lambda value: value.update({
                "expected_action": "PARTY_CANCEL",
            }),
            "nullable-bool": lambda value: value.update({
                "selected_move_slot": True,
            }),
        }
        for label, mutate in value_mutations.items():
            external = self._party_move_transaction_external(reference)
            mutate(external["required_value_in_matrix_case"])
            with self.subTest(value=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [external], state, registry, f"party-move-{label}",
                )

    def test_party_move_transaction_relation_and_kind_boundary_are_exact(
        self,
    ) -> None:
        fixture = self._party_move_transaction_fixture()
        reference = RUNNER._runner_fixture_key(fixture)
        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        mutations = {
            "id": lambda row: row.update({"id": 1}),
            "candidate": lambda row: row.update({
                "candidate_values": ["relearner_teach_empty_slot"],
            }),
            "legacy-kind": lambda row: row.update({"kind": "PARTY_MOVE"}),
            "operator": lambda row: row["relations"][0].update({
                "operator": "FIRST_NON_EGG_MEMBER_KNOWING_MOVE",
            }),
            "owner-order": lambda row: row["relations"][0].update({
                "state_owners": list(reversed(
                    RUNNER._PARTY_MOVE_TRANSACTION_STATE_OWNERS
                )),
            }),
            "source-hash": lambda row: row["relations"][0][
                "model_sources"
            ].update({
                "overlays/move_memory/move_memory.c": "0" * 64,
            }),
            "source-extra": lambda row: row["relations"][0][
                "model_sources"
            ].update({"foreign.c": "0" * 64}),
            "duplicate": lambda row: row["relations"].append(
                deepcopy(row["relations"][0])
            ),
        }
        for label, mutate in mutations.items():
            broken = self._party_move_transaction_external(reference)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [broken], state, registry, f"party-move-{label}",
                )
        duplicate = self._party_move_transaction_external(reference)
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "control owner重複",
        ):
            RUNNER._normalize_external_controls(
                [duplicate, deepcopy(duplicate)], state, registry,
                "party-move-owner-duplicate",
            )

    def test_party_move_transaction_runner_abi_and_c_apply_are_closed(
        self,
    ) -> None:
        from tools.stage61_interaction_oracle import runner_control_abi_contract

        oracle_abi = runner_control_abi_contract()
        oracle_kinds = set(oracle_abi["required_value_types"])
        self.assertIn(
            RUNNER._CONTROL_EXTERNAL_KINDS - oracle_kinds,
            (set(), {"RFU_SESSION"}),
        )
        self.assertEqual(oracle_kinds - RUNNER._CONTROL_EXTERNAL_KINDS, set())
        patched_abi = deepcopy(oracle_abi)
        patched_abi["required_value_types"]["RFU_SESSION"] = deepcopy(
            RUNNER._RFU_SESSION_REQUIRED_VALUE_TYPE
        )
        with patch(
            "tools.stage61_interaction_oracle.runner_control_abi_contract",
            return_value=patched_abi,
        ):
            normalized_abi = RUNNER._runner_control_abi_contract()
        self.assertEqual(
            normalized_abi["required_value_types"]
            ["PARTY_MOVE_TRANSACTION_STATE"],
            RUNNER._PARTY_MOVE_TRANSACTION_REQUIRED_VALUE_TYPE,
        )
        self.assertEqual(
            normalized_abi["layouts"]["party_move_transaction"],
            {
                "party_count_owner": "0x02023F89",
                "party_records_owner": "0x020241E4",
                "party_raw_bytes": 600,
                "record_size": 100,
                "moves_offsets": [44, 46, 48, 50],
                "pp_offsets": [52, 53, 54, 55],
                "pp_bonuses_offset": 56,
                "checksum_offset": 28,
                "checksum_range": {"offset": 32, "size": 48},
                "scenario_ids": list(
                    RUNNER._PARTY_MOVE_TRANSACTION_SCENARIO_IDS
                ),
                "relation": RUNNER._PARTY_MOVE_TRANSACTION_RELATION,
                "payment_policy": "FREE_OVERLAY_NO_MUSHROOM_CONSUMPTION",
                "source_model_sha256": dict(
                    RUNNER._PARTY_MOVE_TRANSACTION_MODEL_SOURCES
                ),
            },
        )

        source = SOURCE_PATH.read_text(encoding="utf-8")
        for exact in (
            "S61_CONTROL_PARTY_MOVE_TRANSACTION_STATE",
            'strcmp(value, "PARTY_MOVE_TRANSACTION_STATE") == 0',
            "PARTY_MOVE_RELEARN_DELETE_RAW_600_EXACT",
            "catalog PARTY_MOVE_TRANSACTION tuple is outside fixed registry",
            "catalog PARTY_MOVE_TRANSACTION exact relation differs",
            "S61_PARTY_MOVE_TRANSACTION_FIXTURE_SIZE == 764U",
            "s61_load_party_move_transaction_fixture",
            "s61_apply_party_move_transaction_fixture",
            "s61_verify_party_move_transaction_fixture",
            "party_move_transaction_control_contract",
            "host_var_result_writes\\\":0",
            "host_var_8004_writes\\\":0",
            "host_var_8005_writes\\\":0",
        ):
            self.assertIn(exact, source)
        for scenario_id in RUNNER._PARTY_MOVE_TRANSACTION_SCENARIO_IDS:
            fixture = self._party_move_transaction_fixture(scenario_id)
            for exact in (
                scenario_id,
                RUNNER._runner_fixture_key(fixture),
                hashlib.sha256(bytes.fromhex(
                    str(fixture["party_raw_hex"])
                )).hexdigest(),
                str(fixture["expected_action"]),
            ):
                self.assertIn(exact, source)
        apply_start = source.index(
            "static void s61_apply_party_move_transaction_fixture("
        )
        apply_end = source.index(
            "static uint8_t s61_gift_storage_equivalence_code(", apply_start,
        )
        apply_source = source[apply_start:apply_end]
        self.assertNotIn("WORLD_VAR_SET", apply_source)
        self.assertNotIn("WORLD_SPECIAL_VAR_8004", apply_source)
        self.assertNotIn("write16(", apply_source)
        for exact in (
            "result->party_raw_sha256",
            "result->storage_raw_sha256",
            "strcmp(before->party_raw_sha256, after->party_raw_sha256) == 0",
            "before->storage_raw_sha256, after->storage_raw_sha256",
            "S61_PARTY_SLOT_COUNT * S61_PARTY_RECORD_SIZE",
        ):
            self.assertIn(exact, source)
        runner_source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn(
            'if required["party"] != exact_party:', runner_source,
        )

    def test_party_minigame_control_schema_fixture_and_tsv_are_exact(
        self,
    ) -> None:
        fixture = self._party_minigame_fixture()
        reference = RUNNER._runner_fixture_key(fixture)
        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        cases = (
            (0, False, None, "0,0,65535,6"),
            (0, True, 5, "0,1,5,6"),
            (1, True, 7, "1,1,7,6"),
        )
        for mode, eligible, selected_slot, encoded_value in cases:
            with self.subTest(
                mode=mode, eligible=eligible, selected_slot=selected_slot,
            ):
                normalized = RUNNER._normalize_external_controls(
                    [self._party_minigame_external(
                        reference, mode=mode, eligible=eligible,
                        selected_slot=selected_slot,
                    )],
                    state, registry, "party-minigame",
                )
                self.assertEqual(
                    RUNNER._encode_external_control(normalized[0]),
                    "PARTY_MINIGAME@"
                    f"{mode}@{encoded_value},{reference}@"
                    "WIRELESS_MINIGAME_PARTY_ELIGIBILITY_AND_SELECTION:0",
                )

        compact = {
            "kind": "PARTY_MINIGAME", "id": 1,
            "value": {
                "mode": 1, "eligible": True, "selected_slot": 7,
                "party_count": 6, "party_layout_ref": reference,
            },
            "owner_keys": ["OBJECT:033/000:000"],
            "relation_evidence": [{
                "operator":
                    "WIRELESS_MINIGAME_PARTY_ELIGIBILITY_AND_SELECTION",
            }],
            "fixture_keys": [reference],
        }
        projected = RUNNER._normalize_event_compact_external_controls(
            [compact], registry, "party-minigame-compact",
            allowed_owner_ids={"OBJECT:033/000:000"},
        )
        self.assertEqual(projected[0]["fixture_keys"], [reference])

        with tempfile.TemporaryDirectory() as directory:
            RUNNER.write_control_fixture_files(Path(directory), registry)
            raw = (Path(directory) / f"{reference}.bin").read_bytes()
        self.assertEqual(len(raw), 600)
        self.assertEqual(raw, bytes(600))

    def test_party_minigame_control_rejects_semantic_and_fixture_drift(
        self,
    ) -> None:
        fixture = self._party_minigame_fixture()
        reference = RUNNER._runner_fixture_key(fixture)
        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}

        def normalize(row: dict[str, object]) -> None:
            RUNNER._normalize_external_controls(
                [row], state, registry, "party-minigame-negative",
            )

        mutations = {
            "id-mode": lambda row: row.update({"id": 1}),
            "false-slot": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"eligible": False, "selected_slot": 0}),
            "true-null": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"eligible": True, "selected_slot": None}),
            "slot-6": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"selected_slot": 6}),
            "slot-127": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"selected_slot": 127}),
            "count-not-6": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"party_count": 5}),
            "relation-wrong": lambda row: row.update({"relations": [{
                "operator": "GET_PARTY_SIZE",
            }]}),
            "relation-duplicate": lambda row: row["relations"].append(
                deepcopy(row["relations"][0])
            ),
        }
        for label, mutate in mutations.items():
            row = self._party_minigame_external(reference)
            mutate(row)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                normalize(row)

        count_drift = self._party_minigame_fixture(count=5)
        count_drift_ref = RUNNER._runner_fixture_key(count_drift)
        count_drift_registry = RUNNER._normalize_control_fixture_registry({
            count_drift_ref: count_drift,
        })
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "fixture count",
        ):
            RUNNER._normalize_external_controls(
                [self._party_minigame_external(count_drift_ref)], state,
                count_drift_registry, "party-minigame-fixture-count",
            )

        storage = {
            "fixture_kind": "STORAGE", "raw_hex": bytes(0x83D0).hex(),
        }
        storage_ref = RUNNER._runner_fixture_key(storage)
        mixed_registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture, storage_ref: storage,
        })
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "fixture_ref owner",
        ):
            RUNNER._normalize_external_controls(
                [self._party_minigame_external(storage_ref)], state,
                mixed_registry, "party-minigame-fixture-kind",
            )

        bad_size = {**fixture, "raw_hex": bytes(599).hex()}
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "PARTY raw_hex",
        ):
            RUNNER._normalize_control_fixture_registry({
                RUNNER._runner_fixture_key(bad_size): bad_size,
            })

        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "fixture_ref owner",
        ):
            RUNNER._normalize_external_controls(
                [self._party_minigame_external("f" * 64)], state, registry,
                "party-minigame-ref-drift",
            )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "canonical SHA-256",
        ):
            RUNNER._normalize_control_fixture_registry({"0" * 64: fixture})

    def test_party_minigame_runner_abi_and_c_transport_are_closed(
        self,
    ) -> None:
        self.assertIn("PARTY_MINIGAME", RUNNER._CONTROL_EXTERNAL_KINDS)
        abi = RUNNER._runner_control_abi_contract()
        self.assertEqual(
            abi["required_value_types"]["PARTY_MINIGAME"],
            RUNNER._PARTY_MINIGAME_REQUIRED_VALUE_TYPE,
        )
        drifted = deepcopy(abi)
        drifted["layouts"]["party_minigame"]["selected_slots"] = [
            0, 1, 2, 3, 4, 5, 6, 7,
        ]
        with patch(
            "tools.stage61_interaction_oracle.runner_control_abi_contract",
            return_value=drifted,
        ), self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "persistent layout",
        ):
            RUNNER._runner_control_abi_contract()
        source = SOURCE_PATH.read_text(encoding="utf-8")
        for exact in (
            "S61_CONTROL_PARTY_MINIGAME",
            'strcmp(value, "PARTY_MINIGAME") == 0',
            "WIRELESS_MINIGAME_PARTY_ELIGIBILITY_AND_SELECTION",
            "catalog PARTY_MINIGAME owner/value relation differs",
            "catalog PARTY_MINIGAME exact relation differs",
            "control->values[2] != 65535U",
            "control->values[3] != 6U",
            "core, control->fixture_refs[0], (uint8_t)control->values[3]",
            "The real SPECIAL and party-menu input produce their results",
        ):
            self.assertIn(exact, source)

    @staticmethod
    def _rfu_external(scenario_id: str) -> dict[str, object]:
        scenario = deepcopy(RUNNER._RFU_SESSION_SCENARIOS[scenario_id])
        special = scenario.pop("special")
        scenario["scenario_id"] = scenario_id
        return {
            "kind": "RFU_SESSION", "id": special,
            "source_ids": [special],
            "read_addresses": ["0x081281C0", "0x0814A008"],
            "candidate_values": (
                [1, 5, 8] if special == 363 else [1, 5, 6, 8]
            ),
            "relations": [{
                "operator": "NATURAL_RFU_ROLE_RESULT_SEQUENCE",
            }],
            "required_value_in_matrix_case": scenario,
            "requirement_basis": "PINNED_NATURAL_RFU_SPECIAL_RESULT",
        }

    @staticmethod
    def _rfu_evidence(control: dict[str, object]) -> dict[str, object]:
        required = control["required_value_in_matrix_case"]
        assert isinstance(required, dict)
        endpoints = int(required["endpoint_count"])
        fault = int(required["fault_code"])
        traces = []
        for slot in range(endpoints):
            traces.append({
                "slot": slot, "trace_count": 8,
                "trace_fnv1a64": f"{slot + 1:016X}",
                "healthy": True, "overflow": False,
                "station_id": 0x61F1 + slot * 8,
                "host_bitmap": 0 if slot else (1 << max(endpoints - 1, 0)) - 1,
                "signal": 0xFFFF if endpoints > 1 else 0,
                "rejection_count": (
                    2 if slot == 0 and fault == 3
                    else 1 if slot == 0 and fault in {1, 2}
                    else 0
                ),
                "disconnect_count": (
                    1 if slot == 0 and fault in {2, 3} else 0
                ),
                "exact": True,
            })
        sequence = list(required["result_sequence"])
        return {
            "scenario_id": required["scenario_id"],
            "special": control["id"],
            "role": "LEADER" if control["id"] == 363 else "JOIN",
            "activity_mode": required["activity_mode"],
            "endpoint_count": endpoints,
            "expected_results": sequence,
            "observed_results": sequence,
            "observed_result_overflow": False,
            "fault_code": fault, "reset_epoch": 1,
            "host_memory_writes": 0,
            "quiescent_load_before_attach": True,
            "hub_reset_after_all_loads": True,
            "exchange_isolated_used": False,
            "topology_discovered": True,
            "initial_fault_armed": fault != 0,
            "initial_fault_consumed": fault != 0,
            "retry_fault_reconfigured": fault == 3,
            "retry_fault_consumed": fault == 3,
            "scheduler": {
                "policy":
                    "MIN_GLOBAL_CYCLE_TIE_SLOT_ORDER_INSTRUCTION_STEP",
                "iterations": endpoints * 11,
                "tie_breaks": endpoints,
                "max_skew": 12,
                "slot_steps": [11] * endpoints,
                "run_frame_used": False,
            },
            "segment_count": len(sequence),
            "endpoint_traces": traces, "exact": True,
        }

    @staticmethod
    def _center_link_external(scenario_id: str) -> dict[str, object]:
        scenario = deepcopy(RUNNER._CENTER_LINK_SESSION_SCENARIOS[scenario_id])
        special = scenario.pop("special")
        return {
            "kind": "CENTER_LINK_SESSION", "id": special,
            "source_ids": [special],
            "read_addresses": ["0x081281C0", "0x0814A008"],
            "candidate_values": (
                [1, 5, 8] if special == 363 else [1, 5, 6, 8]
            ),
            "relations": [{
                "operator":
                    "NATURAL_CENTER_LINK_GROUP_ROLE_RESULT_SEQUENCE",
            }],
            "required_value_in_matrix_case": scenario,
            "requirement_basis": "PINNED_NATURAL_CENTER_LINK_RESULT",
        }

    @staticmethod
    def _center_link_evidence(
        control: dict[str, object], *,
        root: str = "0x081962AC",
        owner: str = "OBJECT:005/005:002",
    ) -> dict[str, object]:
        required = control["required_value_in_matrix_case"]
        assert isinstance(required, dict)
        special = int(control["id"])
        endpoints = int(required["endpoint_count"])
        fault = int(required["fault_code"])
        roles = [special]
        if endpoints > 1:
            roles.extend(
                [364] * (endpoints - 1) if special == 363
                else [363] + [364] * (endpoints - 2)
            )
        traces = []
        for slot in range(endpoints):
            traces.append({
                "slot": slot, "trace_count": 8,
                "trace_fnv1a64": f"{slot + 1:016X}",
                "healthy": True, "overflow": False,
                "station_id": 0x61F1 + slot * 8,
                "host_bitmap": 0 if slot else (1 << max(endpoints - 1, 0)) - 1,
                "signal": 0xFFFF if endpoints > 1 else 0,
                "rejection_count": (
                    2 if slot == 0 and fault == 3
                    else 1 if slot == 0 and fault in {1, 2}
                    else 0
                ),
                "disconnect_count": (
                    1 if slot == 0 and fault in {2, 3} else 0
                ),
                "exact": True,
            })
        sequence = list(required["result_sequence"])
        leaders = roles.count(363)
        return {
            "scenario_id": required["scenario_id"],
            "special": special,
            "role": "LEADER" if special == 363 else "JOIN",
            "profile": "POKEMON_CENTER_LINK",
            "calling_root": root, "owner_key": owner,
            "link_group": required["link_group"],
            "activity": required["activity"],
            "capacity_min": required["capacity_min"],
            "capacity_max": required["capacity_max"],
            "topology_policy": required["topology_policy"],
            "endpoint_count": endpoints,
            "expected_results": sequence,
            "observed_results": sequence,
            "observed_result_overflow": False,
            "fault_code": fault, "reset_epoch": 1,
            "host_memory_writes": 0,
            "quiescent_load_before_attach": True,
            "hub_reset_after_all_loads": True,
            "exchange_isolated_used": False,
            "topology_discovered": True,
            "initial_fault_armed": fault != 0,
            "initial_fault_consumed": fault != 0,
            "retry_fault_reconfigured": fault == 3,
            "retry_fault_consumed": fault == 3,
            "selector_preimage_sentinel_written": True,
            "selector_observed_endpoint_count": endpoints,
            "unexpected_link_group_observed": False,
            "mode_selector_write_observed": False,
            "host_selector_value_writes": 0,
            "leader_endpoint_count": leaders,
            "join_endpoint_count": endpoints - leaders,
            "endpoint_roles": roles,
            "scheduler": {
                "policy":
                    "MIN_GLOBAL_CYCLE_TIE_SLOT_ORDER_INSTRUCTION_STEP",
                "iterations": endpoints * 11,
                "tie_breaks": endpoints,
                "max_skew": 12,
                "slot_steps": [11] * endpoints,
                "run_frame_used": False,
            },
            "segment_count": len(sequence),
            "endpoint_traces": traces, "exact": True,
        }

    def test_rfu_session_registry_tsv_and_compact_projection_are_closed(
        self,
    ) -> None:
        self.assertEqual(len(RUNNER._RFU_SESSION_SCENARIOS), 20)
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        for scenario_id, scenario in RUNNER._RFU_SESSION_SCENARIOS.items():
            with self.subTest(scenario=scenario_id):
                normalized = RUNNER._normalize_external_controls(
                    [self._rfu_external(scenario_id)], state, {}, scenario_id,
                )
                sequence = scenario["result_sequence"]
                second = 65535 if len(sequence) == 1 else sequence[1]
                self.assertEqual(
                    RUNNER._encode_external_control(normalized[0]),
                    "RFU_SESSION@"
                    f"{scenario['special']}@{scenario_id},"
                    f"{scenario['endpoint_count']},"
                    f"{scenario['activity_mode']},{len(sequence)},"
                    f"{sequence[0]},{second},{scenario['fault_code']}@"
                    "NATURAL_RFU_ROLE_RESULT_SEQUENCE:0",
                )

        scenario_id = "mode1-join-retry-result6"
        scenario = RUNNER._RFU_SESSION_SCENARIOS[scenario_id]
        compact = {
            "kind": "RFU_SESSION", "id": scenario["special"],
            "value": {
                key: deepcopy(value) for key, value in scenario.items()
                if key != "special"
            } | {"scenario_id": scenario_id},
            "owner_keys": ["OBJECT:000/000:000"],
            "relation_evidence": [{
                "operator": "NATURAL_RFU_ROLE_RESULT_SEQUENCE",
            }],
            "fixture_keys": [],
        }
        projected = RUNNER._normalize_event_compact_external_controls(
            [compact], {}, "rfu-compact",
            allowed_owner_ids={"OBJECT:000/000:000"},
        )
        self.assertEqual(
            projected[0]["required_value_in_matrix_case"]["scenario_id"],
            scenario_id,
        )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        for exact in (
            "S61_CONTROL_RFU_SESSION",
            'strcmp(value, "RFU_SESSION") == 0',
            "catalog RFU_SESSION tuple is outside fixed registry",
            "catalog RFU_SESSION natural relation differs",
            "NATURAL_RFU_ROLE_RESULT_SEQUENCE",
            "No ROM/EWRAM/save owner encodes the wireless adapter",
        ):
            self.assertIn(exact, source)

    def test_rfu_session_registry_rejects_tuple_and_program_drift(self) -> None:
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        scenario_id = "mode0-leader-retry-result1"
        mutations = {
            "arbitrary-scenario": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"scenario_id": "mode0-leader-user-program"}),
            "special-role": lambda row: row.update({"id": 364}),
            "endpoint": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"endpoint_count": 3}),
            "mode": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"activity_mode": 1}),
            "result": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"result_sequence": [8, 6]}),
            "fault": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"fault_code": 3}),
            "candidate-domain": lambda row: row.update({
                "candidate_values": [1, 5, 6, 8],
            }),
            "relation": lambda row: row.update({"relations": [{
                "operator":
                    "WIRELESS_MINIGAME_PARTY_ELIGIBILITY_AND_SELECTION",
            }]}),
            "embedded-program": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"peer_program": [1, 2, 3]}),
        }
        for label, mutate in mutations.items():
            broken = self._rfu_external(scenario_id)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [broken], state, {}, f"rfu-negative-{label}",
                )

    def test_center_link_registry_tsv_observation_and_exact_set_are_closed(
        self,
    ) -> None:
        self.assertEqual(len(RUNNER._CENTER_LINK_SESSION_SCENARIOS), 50)
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        observations = []
        for scenario_id, scenario in RUNNER._CENTER_LINK_SESSION_SCENARIOS.items():
            with self.subTest(scenario=scenario_id):
                normalized = RUNNER._normalize_external_controls(
                    [self._center_link_external(scenario_id)],
                    state, {}, scenario_id,
                )
                sequence = scenario["result_sequence"]
                second = 65535 if len(sequence) == 1 else sequence[1]
                self.assertEqual(
                    RUNNER._encode_external_control(normalized[0]),
                    "CENTER_LINK_SESSION@"
                    f"{scenario['special']}@{scenario_id},"
                    f"{scenario['link_group']},{scenario['activity']},"
                    f"{scenario['capacity_min']},{scenario['capacity_max']},"
                    f"{scenario['topology_policy']},"
                    f"{scenario['endpoint_count']},{len(sequence)},"
                    f"{sequence[0]},{second},{scenario['fault_code']}@"
                    "NATURAL_CENTER_LINK_GROUP_ROLE_RESULT_SEQUENCE:0",
                )
                observation = RUNNER._validate_center_link_session_observation(
                    self._center_link_evidence(normalized[0]), normalized,
                    expected_root="0x081962AC",
                    expected_owner="OBJECT:005/005:002",
                    label=scenario_id,
                )
                assert observation is not None
                observations.append(observation)
        sweep = RUNNER._validate_center_link_catalog_exact_set(
            observations, sorted(RUNNER._CENTER_LINK_SESSION_SCENARIOS),
            label="center-link-unit",
        )
        self.assertEqual(sweep["logical_unique_count"], 50)
        self.assertEqual(sweep["attempt_count"], 50)
        self.assertTrue(sweep["production_registry_complete"])
        self.assertEqual(sweep["physical_owner_count"], 1)

        scenario_id = "group2-join-retry-result6"
        scenario = RUNNER._CENTER_LINK_SESSION_SCENARIOS[scenario_id]
        compact = {
            "kind": "CENTER_LINK_SESSION", "id": scenario["special"],
            "value": {
                key: deepcopy(value) for key, value in scenario.items()
                if key != "special"
            },
            "owner_keys": ["OBJECT:005/005:002"],
            "relation_evidence": [{
                "operator":
                    "NATURAL_CENTER_LINK_GROUP_ROLE_RESULT_SEQUENCE",
            }],
            "fixture_keys": [],
        }
        projected = RUNNER._normalize_event_compact_external_controls(
            [compact], {}, "center-link-compact",
            allowed_owner_ids={"OBJECT:005/005:002"},
        )
        self.assertEqual(
            projected[0]["required_value_in_matrix_case"], compact["value"],
        )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        for exact in (
            "S61_CONTROL_CENTER_LINK_SESSION",
            'strcmp(value, "CENTER_LINK_SESSION") == 0',
            "catalog CENTER_LINK_SESSION tuple is outside fixed registry",
            "NATURAL_CENTER_LINK_GROUP_ROLE_RESULT_SEQUENCE",
            "selector_preimage_sentinel_written",
            "mode_selector_write_observed",
            "fifth_endpoint_rejected",
        ):
            self.assertIn(exact, source)

    def test_center_link_registry_rejects_selector_topology_and_role_drift(
        self,
    ) -> None:
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        scenario_id = "group2-join-retry-result6"
        mutations = {
            "endpoint": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"endpoint_count": 3}),
            "group": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"link_group": 1}),
            "capacity": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"capacity_max": 5}),
            "policy": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"topology_policy": "MINIMUM_SOURCE_VALID_REPRESENTATIVE"}),
            "role": lambda row: row.update({"id": 363}),
            "mode-injection": lambda row: row[
                "required_value_in_matrix_case"
            ].update({"activity_mode": 1}),
        }
        for label, mutate in mutations.items():
            broken = self._center_link_external(scenario_id)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [broken], state, {}, f"center-negative-{label}",
                )
        control = self._center_link_external(scenario_id)
        normalized = RUNNER._normalize_external_controls(
            [control], state, {}, "center-evidence-negative",
        )
        evidence = self._center_link_evidence(normalized[0])
        for label, mutate in {
            "host-selector": lambda row: row.__setitem__(
                "host_selector_value_writes", 1,
            ),
            "mode-writer": lambda row: row.__setitem__(
                "mode_selector_write_observed", True,
            ),
            "selector-missing": lambda row: row.__setitem__(
                "selector_observed_endpoint_count", 3,
            ),
            "peer-role": lambda row: row["endpoint_roles"].__setitem__(
                2, 363,
            ),
        }.items():
            broken = deepcopy(evidence)
            mutate(broken)
            with self.subTest(evidence=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._validate_center_link_session_observation(
                    broken, normalized, expected_root="0x081962AC",
                    expected_owner="OBJECT:005/005:002", label=label,
                )

    def test_rfu_observation_schema_accepts_real_evidence_shape_and_fails_closed(
        self,
    ) -> None:
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        controls = {}
        evidence = {}
        for scenario_id in RUNNER._RFU_SESSION_SCENARIOS:
            normalized = RUNNER._normalize_external_controls(
                [self._rfu_external(scenario_id)], state, {}, scenario_id,
            )
            controls[scenario_id] = normalized
            evidence[scenario_id] = self._rfu_evidence(normalized[0])
            RUNNER._validate_rfu_session_observation(
                evidence[scenario_id], normalized, label=scenario_id,
            )
        self.assertIsNone(RUNNER._validate_rfu_session_observation(
            None, [], label="non-rfu",
        ))
        with self.assertRaises(RUNNER.Stage61MgbaError):
            RUNNER._validate_rfu_session_observation(
                evidence["mode0-leader-result1"], [], label="non-rfu",
            )

        scenario_id = "mode1-join-retry-result6"
        mutations = {
            "observed-result": lambda item: item.__setitem__(
                "observed_results", [8, 5],
            ),
            "host-write": lambda item: item.__setitem__(
                "host_memory_writes", 1,
            ),
            "isolated": lambda item: item.__setitem__(
                "exchange_isolated_used", True,
            ),
            "topology": lambda item: item.__setitem__(
                "topology_discovered", False,
            ),
            "fault-not-consumed": lambda item: item.__setitem__(
                "initial_fault_consumed", False,
            ),
            "retry-not-consumed": lambda item: item.__setitem__(
                "retry_fault_consumed", False,
            ),
            "run-frame": lambda item: item["scheduler"].__setitem__(
                "run_frame_used", True,
            ),
            "scheduler-sum": lambda item: item["scheduler"][
                "slot_steps"
            ].__setitem__(0, 10),
            "trace-overflow": lambda item: item["endpoint_traces"][
                0
            ].__setitem__("overflow", True),
            "station-repeat": lambda item: item["endpoint_traces"][
                1
            ].__setitem__(
                "station_id", item["endpoint_traces"][0]["station_id"],
            ),
            "disconnect-missing": lambda item: item["endpoint_traces"][
                0
            ].__setitem__("disconnect_count", 0),
            "reject-missing": lambda item: item["endpoint_traces"][
                0
            ].__setitem__("rejection_count", 1),
        }
        for label, mutate in mutations.items():
            broken = deepcopy(evidence[scenario_id])
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._validate_rfu_session_observation(
                    broken, controls[scenario_id], label=label,
                )

        catalog = {
            "schema_version": 9, "status": "PASS",
            "case": "catalog_batch",
            "baseline_natural_continue": True,
            "per_case_stock_warp": True,
            "input_sequence_probe_via_state_restore": True,
            "results": [], "fixture_count": 0, "interactive_count": 0,
            "hidden_count": 0, "input_sequence_attempt_count": 0,
            "successful_path_count": 0, "failed": 0, "empty_text": 0,
            "softlocks": 0, "terminal_mismatches": 0,
            "frame_diff_failures": 0, "input_recovery_failures": 0,
            "invalid_control_flow_failures": 0,
            "internal_control_failures": 0, "root_script_failures": 0,
            "link_session_attempt_count": 0,
            "rfu_session_attempt_count": 0,
            "rfu_session_failure_count": 0,
            "rfu_host_memory_write_count": 0,
            "center_link_session_attempt_count": 0,
            "center_link_session_failure_count": 0,
            "center_link_host_memory_write_count": 0,
            "side_effect_capture_failures": 0,
            "untested": 0, "warnings": 0,
        }
        checked = RUNNER._validate_catalog_batch(catalog, {}, {})
        self.assertEqual(checked["distinct_path_count"], 0)
        catalog_mutations = {
            "schema8": lambda item: item.__setitem__("schema_version", 8),
            "rfu-failure": lambda item: item.__setitem__(
                "rfu_session_failure_count", 1,
            ),
            "rfu-host-write": lambda item: item.__setitem__(
                "rfu_host_memory_write_count", 1,
            ),
            "rfu-attempt-aggregate": lambda item: item.__setitem__(
                "rfu_session_attempt_count", 1,
            ),
            "unknown-root-key": lambda item: item.__setitem__(
                "rfu_unbound_program", True,
            ),
        }
        for label, mutate in catalog_mutations.items():
            broken = deepcopy(catalog)
            mutate(broken)
            with self.subTest(catalog=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._validate_catalog_batch(broken, {}, {})

    def test_rfu_production_sweep_exact_set_and_two_run_gate(self) -> None:
        required = sorted(RUNNER._RFU_SESSION_SCENARIOS)
        observations = []
        for scenario_id in required:
            control = self._rfu_external(scenario_id)
            observation = RUNNER._validate_rfu_session_observation(
                self._rfu_evidence(control), [control],
                label=f"rfu-production-unit/{scenario_id}",
            )
            assert observation is not None
            observations.append(observation)
        sweep = RUNNER._validate_rfu_catalog_exact_set(
            observations, required, label="rfu-production-unit",
        )
        self.assertEqual(sweep["count"], 20)
        self.assertEqual(sweep["required_scenario_ids"], required)
        self.assertEqual(sweep["observed_scenario_ids"], required)
        self.assertTrue(sweep["exact_once"])
        self.assertTrue(sweep["all_real_mgba"])
        self.assertTrue(sweep["production_registry_complete"])
        self.assertEqual(sweep["manifest"]["count"], 20)
        RUNNER._validate_rfu_catalog_two_run_exact_set([
            deepcopy(sweep), deepcopy(sweep),
        ])

        catalog_expected = {
            "rfu-case": {
                "control_requirements": {
                    "external": [self._rfu_external(required[0])],
                },
                "input_sequences": [{"sequence_id": "rfu-only"}],
            },
        }
        self.assertEqual(
            RUNNER._rfu_catalog_expected_scenario_ids(catalog_expected),
            [required[0]],
        )
        duplicate_sequence = deepcopy(catalog_expected)
        duplicate_sequence["rfu-case"]["input_sequences"].append(
            {"sequence_id": "rfu-forged-second"}
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "case/sequence",
        ):
            RUNNER._rfu_catalog_expected_scenario_ids(duplicate_sequence)

        unvalidated = deepcopy(observations)
        unvalidated[0].pop("actual_validation_gate")
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "runtime provenance",
        ):
            RUNNER._validate_rfu_catalog_exact_set(
                unvalidated, required, label="rfu-unvalidated-forge",
            )

        duplicate_missing = deepcopy(observations)
        duplicate_missing[-1] = deepcopy(duplicate_missing[0])
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "exact-set",
        ):
            RUNNER._validate_rfu_catalog_exact_set(
                duplicate_missing, required, label="rfu-duplicate-missing",
            )
        for label, mutation in (
            ("scenario", lambda row: row.__setitem__(
                "scenario_id", "mode0-leader-user-forge",
            )),
            ("tuple", lambda row: row.__setitem__("activity_mode", 1)),
        ):
            forged = deepcopy(observations)
            mutation(forged[0])
            with self.subTest(label=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "tuple",
            ):
                RUNNER._validate_rfu_catalog_exact_set(
                    forged, required, label=f"rfu-{label}-forge",
                )
        drift = deepcopy(sweep)
        drift["observed_scenario_ids"] = list(reversed(
            drift["observed_scenario_ids"]
        ))
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "run間",
        ):
            RUNNER._validate_rfu_catalog_two_run_exact_set([sweep, drift])

    def test_rfu_runner_separate_tu_and_actual_attach_boundaries(self) -> None:
        rom = ROOT / "build/stages/61_display_npc_event_audit.gba"
        if not rom.is_file():
            self.skipTest("Stage61 ROM is not materialized")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            executable = directory / "stage61-rfu-runner"
            metadata = RUNNER._compile(executable)
            expected_sources = {
                str(RUNNER.SOURCE), str(RUNNER.RFU_SOURCE),
                str(RUNNER.RFU_HEADER),
            }
            self.assertEqual(set(metadata["sources"]), expected_sources)
            for relative, digest in metadata["sources"].items():
                self.assertEqual(
                    digest, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
                )
            work = directory / "runtime"
            completed = subprocess.run(
                [str(executable), str(rom), str(work),
                 "rfu_runner_attach_contract"],
                cwd=ROOT, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=120, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stderr, "")
            document = json.loads(completed.stdout)
        self.assertEqual(
            (document["schema_version"], document["case"],
             document["status"], document["failed"],
             document["untested"], document["warnings"]),
            (1, "rfu_runner_attach_contract", "PASS", 0, 0, 0),
        )
        self.assertFalse(document["production_exchange_isolated_used"])
        self.assertEqual(document["host_memory_writes"], 0)
        self.assertEqual(
            [row["endpoint_count"] for row in document["topologies"]],
            [1, 2, 3, 4],
        )
        for row in document["topologies"]:
            self.assertTrue(row["exact"])
            self.assertTrue(row["quiescent_load_before_attach"])
            self.assertTrue(row["hub_reset_after_all_loads"])
            self.assertTrue(row["registry_tuple_exact"])
            self.assertTrue(row["unregistered_scenario_rejected"])
            self.assertTrue(row["fifth_endpoint_rejected"])
            self.assertTrue(row["live_hub_destroy_rejected"])
            self.assertTrue(all(step > 0 for step in row["slot_steps"]))
        self.assertTrue(document["topologies"][0]["one_core_cancel_boundary"])
        source = SOURCE_PATH.read_text(encoding="utf-8")
        scheduler = source[
            source.rindex("static void s61_rfu_scheduler_step_local("):
            source.index("static void s61_rfu_attempt_begin(")
        ]
        self.assertNotIn("runFrame", scheduler)
        cleanup = source[
            source.rindex("static bool s61_rfu_attempt_cleanup("):
            source.index("static void s61_rfu_attempt_begin(")
        ]
        self.assertLess(
            cleanup.index("Stage61RfuPeripheralDetach("),
            cleanup.index("s61_bootstrap_close_core(peer)"),
        )
        self.assertLess(
            cleanup.index("s61_bootstrap_close_core(peer)"),
            cleanup.index("Stage61RfuPeripheralDestroy(peripheral)"),
        )
        self.assertLess(
            cleanup.index("Stage61RfuPeripheralDestroy(peripheral)"),
            cleanup.index("Stage61RfuHubDestroy(hub)"),
        )
        begin = source[
            source.index("static void s61_rfu_attempt_begin("):
            source.index("static void s61_rfu_collect_observed_results(")
        ]
        self.assertLess(
            begin.rindex("->loadState("),
            begin.index("Stage61RfuHubIsQuiescent("),
        )
        self.assertLess(
            begin.index("Stage61RfuHubIsQuiescent("),
            begin.index("Stage61RfuPeripheralAttach("),
        )
        self.assertLess(
            begin.index("Stage61RfuPeripheralAttach("),
            begin.index("Stage61RfuHubReset("),
        )
        drive = source[
            source.index("static struct S61SequenceDriveResult "
                         "s61_drive_input_sequence("):
            source.index("static void s61_sample_ball_throw(")
        ]
        self.assertEqual(
            drive.count("write16(core, WORLD_SPECIAL_RESULT, 0xFFFFU)"), 1,
        )
        self.assertLess(
            drive.index("} else {"),
            drive.index("write16(core, WORLD_SPECIAL_RESULT, 0xFFFFU)"),
        )
        self.assertNotIn("Stage61RfuPeripheralExchangeIsolated(", source)
        self.assertIn("RFU attempt did not start from quiescent VAR_RESULT", source)

    @staticmethod
    def _berry_powder_external(value: int = 50) -> dict[str, object]:
        candidates = sorted({0, 49, 50, 79, 80, 299, 300, 999,
                             1000, 2999, 3000, 99999, value})
        return {
            "kind": "BERRY_POWDER", "id": 0,
            "source_ids": [0x019C, 0x019E, 0x019F, 0x01A0],
            "read_addresses": [
                "0x081815A9", "0x0818175F", "0x0818178B", "0x0818178E",
            ],
            "candidate_values": candidates,
            "relations": [{
                "operator": "EXACT_DECRYPTED_BERRY_POWDER",
            }],
            "required_value_in_matrix_case": value,
            "requirement_basis": "PINNED_BERRY_POWDER_SPECIAL_OWNER",
        }

    def test_berry_powder_control_scalar_relation_and_transport_are_exact(
        self,
    ) -> None:
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        for value in (0, 50, 99999):
            row = self._berry_powder_external(value)
            normalized = RUNNER._normalize_external_controls(
                [row], state, {}, f"berry-powder-{value}",
            )
            self.assertEqual(
                RUNNER._encode_external_control(normalized[0]),
                f"BERRY_POWDER@0@{value}@EXACT_DECRYPTED_BERRY_POWDER:0",
            )

        compact = {
            "kind": "BERRY_POWDER", "id": 0, "value": 50,
            "owner_keys": ["BERRY_POWDER:0"],
            "relation_evidence": [{
                "operator": "EXACT_DECRYPTED_BERRY_POWDER",
            }],
            "fixture_keys": [],
        }
        projected = RUNNER._normalize_event_compact_external_controls(
            [compact], {}, "berry-powder-compact",
            allowed_owner_ids={"BERRY_POWDER:0"},
        )
        self.assertEqual(projected[0]["fixture_keys"], [])

        mutations = {
            "id": lambda row: row.update({"id": 1}),
            "bool": lambda row: row.update({
                "required_value_in_matrix_case": True,
            }),
            "overflow": lambda row: row.update({
                "required_value_in_matrix_case": 100000,
                "candidate_values": [0, 100000],
            }),
            "candidate-missing": lambda row: row.update({
                "candidate_values": [0, 99999],
            }),
            "candidate-order": lambda row: row.update({
                "candidate_values": [99999, 50, 0],
            }),
            "candidate-duplicate": lambda row: row.update({
                "candidate_values": [0, 50, 50, 99999],
            }),
            "relation-duplicate": lambda row: row.update({"relations": [
                {"operator": "EXACT_DECRYPTED_BERRY_POWDER"},
                {"operator": "EXACT_DECRYPTED_BERRY_POWDER"},
            ]}),
            "relation-wrong": lambda row: row.update({"relations": [{
                "operator": "AT_LEAST", "amount": 50,
            }]}),
        }
        for label, mutate in mutations.items():
            broken = self._berry_powder_external()
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [broken], state, {}, f"berry-powder-{label}",
                )

        compact_with_fixture = deepcopy(compact)
        compact_with_fixture["fixture_keys"] = ["0" * 64]
        with self.assertRaises(RUNNER.Stage61MgbaError):
            RUNNER._normalize_event_compact_external_controls(
                [compact_with_fixture], {}, "berry-powder-fixture",
                allowed_owner_ids={"BERRY_POWDER:0"},
            )

    def test_berry_powder_runner_abi_and_c_owner_are_exact(self) -> None:
        abi = RUNNER._runner_control_abi_contract()
        self.assertEqual(
            abi["function_abi"]["get_berry_powder"], "0x081622B1",
        )
        self.assertEqual(abi["layouts"]["berry_powder"], {
            "owner": "SAVE_BLOCK2", "offset": 0x0AF8, "size": 4,
            "encoding": "value XOR encryption_key_u32",
            "maximum": 99999,
            "readback_function": "0x081622B1",
            "relation": "EXACT_DECRYPTED_BERRY_POWDER",
        })
        self.assertEqual(
            abi["required_value_types"]["BERRY_POWDER"],
            "u32(0..99999)",
        )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        for exact in (
            "WORLD_GET_BERRY_POWDER = 0x081622B1U",
            "S61_SAVE2_BERRY_POWDER_OFFSET = 0x0AF8U",
            "S61_MAX_BERRY_POWDER = 99999U",
            "S61_CONTROL_BERRY_POWDER",
            'strcmp(value, "BERRY_POWDER") == 0',
            '"EXACT_DECRYPTED_BERRY_POWDER"',
            "catalog berry-powder apply/readback differs",
            "catalog berry-powder API/raw readback differs",
        ):
            self.assertIn(exact, source)

    @staticmethod
    def _coins_predicate_external(
        vega: int, operator: str, amount: int, result_value: int,
    ) -> dict[str, object]:
        return {
            "kind": "COINS", "id": 0,
            "source_ids": [0],
            "read_addresses": ["0x08100000"],
            "candidate_values": [vega],
            "relations": [{
                "operator": operator,
                "amount": amount,
                "result_value": result_value,
            }],
            "required_value_in_matrix_case": {"vega": vega, "cfru": 0},
            "requirement_basis": "PINNED_COINS_SOURCE_PREDICATE",
        }

    def test_coins_source_predicates_normalize_and_transport_exactly(
        self,
    ) -> None:
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        cases = (
            (9998, "CURRENT_COINS_BELOW_MAX", 50, 0),
            (9999, "CURRENT_COINS_AT_MAX", 50, 1),
            (50, "CURRENT_COINS_AT_LEAST_AMOUNT", 50, 0),
            (49, "CURRENT_COINS_BELOW_AMOUNT", 50, 1),
        )
        for vega, operator, amount, result_value in cases:
            with self.subTest(operator=operator):
                normalized = RUNNER._normalize_external_controls(
                    [self._coins_predicate_external(
                        vega, operator, amount, result_value,
                    )], state, {}, f"coins-{operator}",
                )
                self.assertEqual(
                    RUNNER._encode_external_control(normalized[0]),
                    f"COINS@0@{vega},0@{operator}:{amount}:{result_value}",
                )

        compact = {
            "kind": "COINS", "id": 0,
            "value": {"vega": 9998, "cfru": 0},
            "owner_keys": ["OBJECT:007/009:000"],
            "relation_evidence": [{
                "operator": "CURRENT_COINS_BELOW_MAX",
                "amount": 50,
                "result_value": 0,
            }],
            "fixture_keys": [],
        }
        projected = RUNNER._normalize_event_compact_external_controls(
            [compact], {}, "coins-compact",
            allowed_owner_ids={"OBJECT:007/009:000"},
        )
        self.assertEqual(projected[0]["relations"], compact["relation_evidence"])

        legacy = self._coins_predicate_external(
            10, "CURRENT_COINS_BELOW_MAX", 50, 0,
        )
        legacy["relations"] = [{
            "operator": "WRITE_CURRENT_COINS_TO_VAR",
            "destination_var": 0x8000,
        }]
        normalized_legacy = RUNNER._normalize_external_controls(
            [legacy], state, {}, "coins-b3-legacy",
        )
        self.assertEqual(
            RUNNER._encode_external_control(normalized_legacy[0]),
            "COINS@0@10,0@WRITE_CURRENT_COINS_TO_VAR:32768",
        )

    def test_coins_source_predicates_fail_closed_on_schema_and_truth_drift(
        self,
    ) -> None:
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}

        def wrong(
            vega: int = 9998,
            operator: str = "CURRENT_COINS_BELOW_MAX",
            amount: int = 50,
            result_value: int = 0,
        ) -> dict[str, object]:
            return self._coins_predicate_external(
                vega, operator, amount, result_value,
            )

        mutations = {
            "unknown-operator": lambda row: row["relations"][0].update({
                "operator": "CURRENT_COINS_UNKNOWN",
            }),
            "missing-field": lambda row: row["relations"][0].pop("amount"),
            "extra-field": lambda row: row["relations"][0].update({
                "maximum": 9999,
            }),
            "reverse-bool": lambda row: row["relations"][0].update({
                "result_value": 1,
            }),
            "result-range": lambda row: row["relations"][0].update({
                "result_value": 2,
            }),
            "amount-range": lambda row: row["relations"][0].update({
                "amount": 0x10000,
            }),
            "singleton-id": lambda row: row.update({"id": 1}),
            "duplicate": lambda row: row["relations"].append(
                deepcopy(row["relations"][0])
            ),
        }
        for label, mutate in mutations.items():
            broken = wrong()
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [broken], state, {}, f"coins-{label}",
                )

        false_predicates = (
            wrong(9999, "CURRENT_COINS_BELOW_MAX", 50, 0),
            wrong(9998, "CURRENT_COINS_AT_MAX", 50, 1),
            wrong(49, "CURRENT_COINS_AT_LEAST_AMOUNT", 50, 0),
            wrong(50, "CURRENT_COINS_BELOW_AMOUNT", 50, 1),
        )
        for row in false_predicates:
            operator = row["relations"][0]["operator"]
            with self.subTest(predicate=operator), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "predicate",
            ):
                RUNNER._normalize_external_controls(
                    [row], state, {}, f"coins-false-{operator}",
                )

    def test_coins_source_predicates_are_strict_in_c_runtime(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        for exact in (
            "S61_MAX_VEGA_COINS = 9999U",
            "CURRENT_COINS_BELOW_MAX",
            "CURRENT_COINS_AT_MAX",
            "CURRENT_COINS_AT_LEAST_AMOUNT",
            "CURRENT_COINS_BELOW_AMOUNT",
            "s61_coin_control_relation_matches",
            "catalog coin predicate relation must use OP:AMOUNT:RESULT",
            "catalog coins source predicate/result differs",
            "relation->has_result_value",
            "relation->result_value == expected_result",
        ):
            self.assertIn(exact, source)

    @staticmethod
    def _pokedex_bitmap(*nationals: int) -> str:
        raw = bytearray(52)
        for national in nationals:
            index = national - 1
            raw[index // 8] |= 1 << (index % 8)
        return raw.hex()

    @classmethod
    def _pokedex_fixture(cls) -> dict[str, object]:
        owned = cls._pokedex_bitmap(1, 151)
        seen = cls._pokedex_bitmap(1, 2, 151, 386)
        return {
            "fixture_kind": "POKEDEX_LAYOUT",
            "scenario_id": "pokedex-partial-national",
            "national_enabled": True,
            "national_magic": 0xB9,
            "national_var": 0x6258,
            "national_flag": True,
            "owned_hex": owned,
            "seen_hex": seen,
            "seen1_hex": seen,
            "seen2_hex": seen,
            "kanto_seen": 3,
            "kanto_caught": 2,
            "national_seen": 4,
            "national_caught": 2,
            "mew_caught": True,
            "has_all_required": False,
        }

    @classmethod
    def _pokedex_external(
        cls, reference: str,
    ) -> dict[str, object]:
        fixture = cls._pokedex_fixture()
        value = {
            key: fixture[key] for key in (
                "scenario_id", "national_enabled", "kanto_seen",
                "kanto_caught", "national_seen", "national_caught",
                "mew_caught", "has_all_required",
            )
        }
        value["layout_ref"] = reference
        return {
            "kind": "POKEDEX_STATE", "id": 0, "source_ids": [0],
            "read_addresses": ["0x081949DC"],
            "candidate_values": "POKEDEX_LAYOUT_REQUIRED",
            "relations": [{"operator": "EXACT_POKEDEX_SAVE_STATE"}],
            "required_value_in_matrix_case": value,
            "requirement_basis": "SYNTHETIC_POKEDEX_PHYSICAL_OWNER",
        }

    def test_pokedex_control_fixture_schema_projection_and_binary_are_exact(
        self,
    ) -> None:
        fixture = self._pokedex_fixture()
        reference = RUNNER._runner_fixture_key(fixture)
        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        rows = RUNNER._normalize_external_controls(
            [self._pokedex_external(reference)], state, registry, "pokedex",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            RUNNER._encode_external_control(rows[0]),
            "@".join((
                "POKEDEX_STATE", "0",
                "pokedex-partial-national,1,3,2,4,2,1,0," + reference,
                "EXACT_POKEDEX_SAVE_STATE:0",
            )),
        )
        with tempfile.TemporaryDirectory() as directory:
            RUNNER.write_control_fixture_files(Path(directory), registry)
            raw = (Path(directory) / f"{reference}.bin").read_bytes()
        self.assertEqual(len(raw), 212)
        self.assertEqual(raw[:4], bytes.fromhex("b9586201"))
        self.assertEqual(raw[4:56].hex(), fixture["owned_hex"])
        self.assertEqual(raw[56:108].hex(), fixture["seen_hex"])
        self.assertEqual(raw[108:160].hex(), fixture["seen1_hex"])
        self.assertEqual(raw[160:212].hex(), fixture["seen2_hex"])

    def test_pokedex_fixture_hash_count_and_mirrors_fail_closed(self) -> None:
        fixture = self._pokedex_fixture()
        reference = RUNNER._runner_fixture_key(fixture)
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "canonical SHA-256",
        ):
            RUNNER._normalize_control_fixture_registry({"0" * 64: fixture})

        extra_key = {**fixture, "unexpected": 0}
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "POKEDEX_LAYOUT keys",
        ):
            RUNNER._normalize_control_fixture_registry({
                RUNNER._runner_fixture_key(extra_key): extra_key,
            })

        triple_drift = deepcopy(fixture)
        triple_drift["national_magic"] = 0
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "national triple",
        ):
            RUNNER._normalize_control_fixture_registry({
                RUNNER._runner_fixture_key(triple_drift): triple_drift,
            })

        count_drift = deepcopy(fixture)
        count_drift["kanto_seen"] = 4
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "kanto_seen bitmap",
        ):
            RUNNER._normalize_control_fixture_registry({
                RUNNER._runner_fixture_key(count_drift): count_drift,
            })

        mirror_drift = deepcopy(fixture)
        seen1 = bytearray.fromhex(str(mirror_drift["seen1_hex"]))
        seen1[0] ^= 0x04
        mirror_drift["seen1_hex"] = seen1.hex()
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "seen mirror drift",
        ):
            RUNNER._normalize_control_fixture_registry({
                RUNNER._runner_fixture_key(mirror_drift): mirror_drift,
            })

        tail_drift = deepcopy(fixture)
        for key in ("owned_hex", "seen_hex", "seen1_hex", "seen2_hex"):
            bitmap = bytearray.fromhex(str(tail_drift[key]))
            bitmap[-1] |= 0x80
            tail_drift[key] = bitmap.hex()
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "unused tail bit",
        ):
            RUNNER._normalize_control_fixture_registry({
                RUNNER._runner_fixture_key(tail_drift): tail_drift,
            })

        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        scalar_drift = self._pokedex_external(reference)
        scalar_drift["required_value_in_matrix_case"]["national_seen"] = 3
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "fixture scalar",
        ):
            RUNNER._normalize_control_required_value(
                "POKEDEX_STATE",
                scalar_drift["required_value_in_matrix_case"],
                registry, "pokedex-scalar-drift",
            )

    def test_pokedex_control_relation_and_id_are_exact(self) -> None:
        fixture = self._pokedex_fixture()
        reference = RUNNER._runner_fixture_key(fixture)
        registry = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        state = {key: [] for key in ("flags", "vars", "items", "trainers")}
        for label, mutation in (
            ("id", lambda row: row.update({"id": 1})),
            ("relation", lambda row: row.update({"relations": [
                {"operator": "EXACT_POKEDEX_SAVE_STATE"},
                {"operator": "EXACT_POKEDEX_SAVE_STATE"},
            ]})),
            ("wrong-operator", lambda row: row.update({"relations": [{
                "operator": "ENGINE_GLOBAL_QL_STATE_EXACT",
            }]})),
        ):
            row = self._pokedex_external(reference)
            mutation(row)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [row], state, registry, f"pokedex-{label}",
                )

    def test_pokedex_has_all_required_excludes_six_stock_mythicals(self) -> None:
        required = (
            *range(1, 151), *range(152, 249), *range(252, 385),
        )
        self.assertEqual(len(required), 380)
        bitmap = self._pokedex_bitmap(*required)
        fixture = self._pokedex_fixture()
        fixture.update({
            "scenario_id": "pokedex-all-required-without-six-mythicals",
            "owned_hex": bitmap, "seen_hex": bitmap,
            "seen1_hex": bitmap, "seen2_hex": bitmap,
            "kanto_seen": 150, "kanto_caught": 150,
            "national_seen": 380, "national_caught": 380,
            "mew_caught": False, "has_all_required": True,
        })
        reference = RUNNER._runner_fixture_key(fixture)
        normalized = RUNNER._normalize_control_fixture_registry({
            reference: fixture,
        })
        self.assertTrue(normalized[reference]["has_all_required"])

        missing_required = deepcopy(fixture)
        owned = bytearray.fromhex(str(missing_required["owned_hex"]))
        index = 384 - 1
        owned[index // 8] &= ~(1 << (index % 8))
        for key in ("owned_hex", "seen_hex", "seen1_hex", "seen2_hex"):
            missing_required[key] = owned.hex()
        missing_required["national_seen"] = 379
        missing_required["national_caught"] = 379
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "has_all_required bitmap",
        ):
            RUNNER._normalize_control_fixture_registry({
                RUNNER._runner_fixture_key(missing_required): missing_required,
            })

    def test_exact_physical_var_relation_is_strict_and_runner_visible(
        self,
    ) -> None:
        relation = [{"operator": "EXACT_PHYSICAL_VAR_VALUE"}]
        self.assertEqual(
            RUNNER._normalize_control_relations(relation, "VAR", "unit"),
            relation,
        )
        with self.assertRaises(RUNNER.Stage61MgbaError):
            RUNNER._normalize_control_relations([{
                "operator": "EXACT_PHYSICAL_VAR_VALUE", "value": 0,
            }], "VAR", "unit-forged")

    def test_map_player_position_is_exact_destination_arrival_fixture(
        self,
    ) -> None:
        producer = {
            "producer_kind": "STOCK_WARP",
            "source_trigger_path": {
                "kind": "MAP_TRANSITION_LOAD", "group": 2, "map": 10,
                "stock_warp": {
                    "source": {"group": 1, "map": 1, "warp": 0},
                    "predecessor_tile": {"x": 4, "y": 5},
                    "trigger_tile": {"x": 4, "y": 6},
                    "destination": {"group": 2, "map": 10, "warp": 1},
                    "arrival_tile": {"x": 9, "y": 2},
                },
            },
        }
        self.assertEqual(
            RUNNER._event_map_player_position_from_producer(
                producer, {"group": 2, "map": 10}, "unit",
            ),
            {
                "x": 9, "y": 2, "group": 2, "map": 10,
                "apply_relation":
                    "ACTUAL_STOCK_WARP_THEN_REAL_MOVEMENT",
            },
        )
        resume = deepcopy(producer)
        resume["source_trigger_path"].pop("stock_warp")
        resume["source_trigger_path"]["resume_callback"] = {
            "actual_predecessor_consumer": {
                "kind": "STOCK_WARP_THEN_FIELD_RETURN",
                "stock_warp": producer["source_trigger_path"]["stock_warp"],
                "field_return": {},
            },
        }
        self.assertEqual(
            RUNNER._event_map_player_position_from_producer(
                resume, {"group": 2, "map": 10}, "unit-resume",
            )["y"],
            2,
        )
        for mutation in (
            lambda row: row.update({"producer_kind": "ENGINE_TELEPORT"}),
            lambda row: row["source_trigger_path"]["stock_warp"][
                "destination"
            ].update({"map": 11}),
            lambda row: row["source_trigger_path"]["stock_warp"][
                "arrival_tile"
            ].update({"x": True}),
        ):
            broken = deepcopy(producer)
            mutation(broken)
            with self.assertRaises(RUNNER.Stage61MgbaError):
                RUNNER._event_map_player_position_from_producer(
                    broken, {"group": 2, "map": 10}, "unit-broken",
                )

    def test_map_player_position_row_follows_dynamic_opcode42_effect_pair(
        self,
    ) -> None:
        owner = "MAP:002/010:001:DIRECT"
        producer = {
            "producer_kind": "STOCK_WARP",
            "source_trigger_path": {
                "kind": "MAP_TRANSITION_LOAD", "group": 2, "map": 10,
                "stock_warp": {
                    "source": {"group": 1, "map": 1, "warp": 0},
                    "predecessor_tile": {"x": 4, "y": 5},
                    "trigger_tile": {"x": 4, "y": 6},
                    "destination": {"group": 2, "map": 10, "warp": 1},
                    "arrival_tile": {"x": 9, "y": 2},
                },
            },
        }
        expected = RUNNER._event_map_player_position_from_producer(
            producer, {"group": 2, "map": 10}, "unit",
        )

        def effect(axis: str, member: int) -> dict[str, object]:
            return {
                "effect_instance_ordinal": member,
                "dispatch_ordinal": 0, "owner_id": owner,
                "root_pc": "0x08123456",
                "effect": {
                    "domain": "vars", "owner": f"VAR:0x800{4 + member:X}",
                    "relation": f"COPY_CURRENT_PLAYER_{axis}",
                    "instruction_address": "0x08123460",
                    "execution_trace_index": 7, "opcode": "0x42",
                    "abi_key": None, "group_member_ordinal": member,
                },
            }

        lifecycle = {"ordered_effect_instances": [effect("X", 0), effect("Y", 1)]}
        controls = {"external": [{
            "kind": "PLAYER_POSITION", "id": 0,
            "required_value_in_matrix_case": expected,
            "relations": [{
                "operator": "ACTUAL_PLAYER_COORDINATES_BEFORE_INTERACTION",
            }],
            "owner_keys": [owner], "fixture_keys": [],
        }]}
        RUNNER._validate_event_map_player_position_control(
            controls, lifecycle, producer, {"group": 2, "map": 10}, "unit",
        )

        for label, mutation in (
            ("missing-row", lambda c, _l: c["external"].clear()),
            ("partial-effect", lambda _c, l: l[
                "ordered_effect_instances"
            ].pop()),
            ("forged-scope", lambda c, _l: c["external"][0].update({
                "owner_keys": [owner, "MAP:002/010:002:DIRECT"],
            })),
        ):
            broken_controls = deepcopy(controls)
            broken_lifecycle = deepcopy(lifecycle)
            mutation(broken_controls, broken_lifecycle)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._validate_event_map_player_position_control(
                    broken_controls, broken_lifecycle, producer,
                    {"group": 2, "map": 10}, f"unit-{label}",
                )

        with self.assertRaises(RUNNER.Stage61MgbaError):
            RUNNER._validate_event_map_player_position_control(
                controls, {"ordered_effect_instances": []}, producer,
                {"group": 2, "map": 10}, "unit-extra-row",
            )

    @staticmethod
    def _artifact(
        case: str, path: str, *, sha256: str = "1" * 64,
        rgb_fnv1a64: str = "0123456789ABCDEF",
    ) -> dict[str, object]:
        return {
            "path": path, "size": 115215, "sha256": sha256,
            "rgb_fnv1a64": rgb_fnv1a64,
            "framebuffer_role": RUNNER._framebuffer_role(case, path),
        }

    @staticmethod
    def _ppm(seed: int) -> bytes:
        rgb = bytearray(240 * 160 * 3)
        for index in range(len(rgb)):
            rgb[index] = (index * 17 + seed * 31) & 0xFF
        return b"P6\n240 160\n255\n" + bytes(rgb)

    @staticmethod
    def _generated_fixture_source() -> dict[str, object]:
        """Read the generated fixture and adapt only an older build artifact.

        The runner itself deliberately rejects the retired product/non-product
        ABI.  This test-only adapter keeps focused unit tests runnable while a
        parent build is between source-schema migration and regeneration.
        """
        source = json.loads(
            (ROOT / RUNNER.DEFAULT_FIXTURES).read_text(encoding="utf-8")
        )
        retired_diagnostic = source.pop("non_product_map_diagnostics", None)
        if retired_diagnostic is not None:
            for map_row in retired_diagnostic["maps"]:
                map_row["classification"] = {
                    "ENGINE_DORMANT_UNREACHABLE_MAP": (
                        "ENGINE_DORMANT_LOCAL_INCOMING_ABSENT"
                    ),
                    "CANONICAL_CLONE_SHADOWED_ORPHAN": (
                        "CANONICAL_CLONE_SHADOWED_LOCAL_INCOMING_ABSENT"
                    ),
                }[map_row["classification"]]
                map_row["local_static_incoming_available"] = map_row.pop(
                    "product_entry_expected"
                )
                for row in map_row["object_probes"]:
                    row["local_static_incoming_available"] = row.pop(
                        "product_interaction_expected"
                    )
            source[
                "local_static_incoming_absent_map_diagnostics"
            ] = retired_diagnostic
        retired_regressions = source.pop(
            "product_map_script_regressions", None
        )
        if retired_regressions is not None:
            source["final_map_script_regressions"] = retired_regressions
        lifecycle = source.get("engine_special_flag_lifecycle")
        if isinstance(lifecycle, dict) \
                and lifecycle.get("runtime_storage", {}).get(
                    "owner_address"
                ) == "0x020370E0":
            lifecycle["runtime_storage"]["owner_address"] = "0x02037014"
        return source

    @staticmethod
    def _object_template_raw(
        *, local_id: int, graphics_id: int, x: int, y: int,
        movement_type: int, script_pointer: int, flag: int = 0,
    ) -> str:
        """Build an independent 24-byte ObjectEventTemplate fixture."""
        raw = bytearray(24)
        raw[0] = local_id
        raw[1] = graphics_id
        raw[4:6] = x.to_bytes(2, "little", signed=True)
        raw[6:8] = y.to_bytes(2, "little", signed=True)
        raw[8] = 3
        raw[9] = movement_type
        raw[16:20] = script_pointer.to_bytes(4, "little")
        raw[20:22] = flag.to_bytes(2, "little")
        return raw.hex().upper()

    @staticmethod
    def _physical_interaction_execution(
        *, start: list[int], walk_sequence: list[str], stance: list[int],
        action: str,
    ) -> dict[str, object]:
        return {
            "trigger": (
                "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A"
            ),
            "start": list(start),
            "walk_sequence": list(walk_sequence),
            "stance": list(stance),
            "action": action,
            "interaction_distance": 1,
            "counter_tile": None,
            "actual_walk_required": True,
            "actual_walk_exception": None,
            "walk_path_basis": (
                "EXACT_STOCK_INCOMING_ARRIVAL_TO_OWNER_STANCE"
            ),
            "direct_script_call_forbidden": True,
        }

    @staticmethod
    def _runtime_position_observation(
        producer: dict[str, object], control: dict[str, object], *,
        requested: list[int], visible: bool, host_prepare: bool = True,
        before_walk: bool | None = None,
    ) -> dict[str, object]:
        kind = producer["kind"]
        required = kind != "NONE"
        if before_walk is None:
            before_walk = visible if not required else False
        engine = kind == "ENGINE_TELEPORT"
        expected_control_value = int(bool(control["value"]))
        national = None
        if control["kind"] == "NATIONAL_DEX":
            national = {
                "flag_id": 0x0840,
                "flag_value": expected_control_value,
                "var_id": 0x404E,
                "var_value": 0x6258 if expected_control_value else 0,
                "saveblock2_offset": 0x001B,
                "magic": 0xB9 if expected_control_value else 0,
                "exact": True,
            }
        prepared = host_prepare and control["kind"] != "NONE"
        root = int(producer["root"])
        arrival = [int(producer["arrival_x"]), int(producer["arrival_y"])]
        zero = "0x00000000"
        pointer = f"0x{root:08X}" if required else zero
        hashes = "1234567890ABCDEF" if required else "0" * 16
        return {
            "kind": kind,
            "producer_required": required,
            "runtime_position_control": {
                "kind": control["kind"], "id": int(control["id"]),
                "value": expected_control_value,
                "host_prepared_before_producer": prepared,
                "host_write_count": int(prepared),
                "verified_before_producer": True,
                "flag_readback_exact": True,
                "national_dex_readback": national,
                "exact": True,
            },
            "root_expected": f"0x{root:08X}",
            "source": {
                "map": (
                    f"{producer['source_group']}/{producer['source_map']}"
                ),
                "warp_id": producer["source_warp"],
            },
            "predecessor": [
                producer["predecessor_x"], producer["predecessor_y"],
            ],
            "trigger": [producer["trigger_x"], producer["trigger_y"]],
            "trigger_key": producer["trigger_key"],
            "destination": {
                "map": (
                    f"{producer['destination_group']}/"
                    f"{producer['destination_map']}"
                ),
                "warp_id": producer["destination_warp"],
                "arrival": arrival,
            },
            "record_address": f"0x{int(producer['record_address']):08X}",
            "source_record_exact": required,
            "source_setup_exact": required,
            "predecessor_exact": required,
            "capture_armed_before_producer": required,
            "capture_armed_before_cardinal_trigger": required and not engine,
            "cardinal_trigger_pressed": required and not engine,
            "engine_teleport_started": required and engine,
            "physical_trigger_step_observed": required and not engine,
            "destination_loaded": required,
            "arrival_exact": required,
            "field_ready": required,
            "transition_frames": 91 if required else 0,
            "root_script_pointer_hits": int(required),
            "context_root_script_pointer_hits": 0,
            "root_dispatch_callsite_hits": int(required),
            "root_executor_hits": int(required),
            "all_map_script_dispatch_callsite_raw_hits": (
                2 if required else 0
            ),
            "all_map_script_executor_raw_hits": 2 if required else 0,
            "expected_root_dispatch_hits": int(required),
            "expected_root_executor_hits": int(required),
            "first_map_script_dispatch_pointer": pointer,
            "last_map_script_dispatch_pointer": pointer,
            "first_map_script_executor_pointer": pointer,
            "last_map_script_executor_pointer": pointer,
            "first_root_script_pointer": pointer,
            "first_root_context": {
                "map": (
                    f"{producer['destination_group']}/"
                    f"{producer['destination_map']}"
                    if required else "0/0"
                ),
                "player": arrival if required else [0, 0],
            },
            "invalid_control_flow": False,
            "target_materialized_before_walk": before_walk,
            "target_materialization_deferred_to_real_walk": (
                required and visible and not before_walk
            ),
            "target_materialized_before_a": visible,
            "local_player_positioning": {
                "host_branch_state_writes": 0,
                "host_coordinate_reposition_calls": (
                    0 if not required or arrival == list(requested) else 2
                ),
                "set_camera_focus_coords_entry": "0x080590A9",
                "move_player_to_map_coords_entry": "0x0805BFD9",
                "before": arrival if required else [0, 0],
                "requested": list(requested),
                "after": list(requested) if required else [0, 0],
                "loaded_templates_before_fnv1a64": hashes,
                "loaded_templates_after_fnv1a64": hashes,
                "loaded_templates_exact": required,
                "branch_state_exact": required,
                "same_map_exact": required,
                "live_player_position_exact": required,
                "exact": True,
            },
            "exact": True,
        }

    @staticmethod
    def _preinteraction_identity(
        raw_hex: str, *, template_index: int, interactive: bool,
        runtime_object: list[int] | None = None,
    ) -> dict[str, object]:
        raw = bytes.fromhex(raw_hex)
        x = int.from_bytes(raw[4:6], "little", signed=True)
        y = int.from_bytes(raw[6:8], "little", signed=True)
        movement_range = raw[10]
        script_pointer = int.from_bytes(raw[16:20], "little")
        raw_fnv1a64 = RUNNER._fnv1a64(raw)
        live_x, live_y = runtime_object or [x, y]
        return {
            "owner_object_index": template_index,
            "template_found": True,
            "template_index": template_index,
            "template_local_id": raw[0],
            "template_graphics_id": raw[1],
            "template_kind": raw[2],
            "template_position": [x, y],
            "template_elevation": raw[8],
            "template_movement_type": raw[9],
            "template_movement_range": [
                movement_range & 0x0F, movement_range >> 4,
            ],
            "template_trainer_type": int.from_bytes(
                raw[12:14], "little"
            ),
            "template_trainer_range_or_berry_tree_id": int.from_bytes(
                raw[14:16], "little"
            ),
            "template_script": f"0x{script_pointer:08X}",
            "template_hide_flag": int.from_bytes(raw[20:22], "little"),
            "template_storage": "gMapHeader.events.objectEvents",
            "expected_raw_hex": raw_hex,
            "observed_raw_hex": raw_hex,
            "expected_raw_fnv1a64": raw_fnv1a64,
            "observed_raw_fnv1a64": raw_fnv1a64,
            "runtime_template_found": True,
            "runtime_template_index": template_index,
            "runtime_template_local_id": raw[0],
            "runtime_template_position": [live_x, live_y],
            "runtime_template_script": f"0x{script_pointer:08X}",
            "runtime_template_position_exact": True,
            "runtime_template_script_exact": True,
            "live_active": interactive,
            "live_visible": interactive,
            "live_current": (
                [live_x + 7, live_y + 7] if interactive else None
            ),
            "map_lifecycle": None,
            "exact": True,
        }

    @staticmethod
    def _approach_observation(
        interaction: dict[str, object],
    ) -> dict[str, object]:
        facing_by_token = {"DOWN": 1, "UP": 2, "LEFT": 3, "RIGHT": 4}
        walk = interaction["walk_sequence"]
        walk_steps = len(walk)  # type: ignore[arg-type]
        action = interaction["action"]
        required = facing_by_token[action]  # type: ignore[index]
        after_walk = (
            facing_by_token[walk[-1]] if walk else required  # type: ignore[index]
        )
        movement_counters = {
            "happiness_step_counter": {
                "saveblock1_offset": 0x1042,
                "before": 126,
                "after": (126 + walk_steps) % 128,
                "expected_after": (126 + walk_steps) % 128,
                "transition": "ADD_MOD_128",
                "exact": True,
            },
            "poison_step_counter": {
                "saveblock1_offset": 0x1044,
                "before": 4,
                "after": (4 + walk_steps) % 5,
                "expected_after": (4 + walk_steps) % 5,
                "transition": "ADD_MOD_5",
                "exact": True,
            },
            "renewable_item_step_counter": {
                "saveblock1_offset": 0x1046,
                "before": 1499,
                "after": min(1499 + walk_steps, 1500),
                "expected_after": min(1499 + walk_steps, 1500),
                "transition": "ADD_CAP_1500",
                "exact": True,
            },
            "game_stat_steps": {
                "saveblock1_offset": 0x1214,
                "before": 0x00FFFFFE,
                "after": min(0x00FFFFFE + walk_steps, 0x00FFFFFF),
                "expected_after": min(
                    0x00FFFFFE + walk_steps, 0x00FFFFFF,
                ),
                "transition": "DECRYPT_ADD_CAP_16777215",
                "exact": True,
            },
            "daycare_step_counter": {
                "saveblock1_offset": 0x309A,
                "before": 255,
                "after": (255 + walk_steps) & 0xFF,
                "expected_after": (255 + walk_steps) & 0xFF,
                "transition": "ADD_MOD_256",
                "exact": True,
            },
        }
        return {
            "capture_armed_before_first_walk_instruction": True,
            "walk_path_basis": interaction["walk_path_basis"],
            "start": deepcopy(interaction["start"]),
            "stance": deepcopy(interaction["stance"]),
            "walk_step_count": walk_steps,
            "step_facing": [
                {
                    "expected": facing_by_token[token],
                    "observed": facing_by_token[token],
                }
                for token in walk  # type: ignore[union-attr]
            ],
            "facing": {
                "raw_owner": (
                    "gObjectEvents[gPlayerAvatar.objectEventId]"
                    "+0x18.low_nibble"
                ),
                "mapping": facing_by_token,
                "before_walk": after_walk,
                "after_walk": after_walk,
                "required": required,
                "after_face_input": required,
                "changed_when_required": True,
                "exact": True,
            },
            "transient_execution": {
                "script_context_active_instructions": 0,
                "message_active_frames": 0,
                "message_count": 0,
                "printer_call_count": 0,
                "non_overworld_instructions": 0,
                "effect_observer_enabled": True,
                "effect_hook_hits_before": 0,
                "effect_hook_hits_after": 0,
                "invalid_control_flow": False,
                "exact_zero": True,
            },
            "persistent_state": {
                "saveblock1_unexpected_changed_bytes": 0,
                "saveblock2_unexpected_changed_bytes": 0,
                "allowed_saveblock1_ranges": [
                    {"start": 0, "end": 4, "meaning": "player_xy"},
                    {
                        "start": 0x1042, "end": 0x1044,
                        "meaning": (
                            "happiness_step_counter_exact_transition"
                        ),
                    },
                    {
                        "start": 0x1044, "end": 0x1046,
                        "meaning": "poison_step_counter_exact_transition",
                    },
                    {
                        "start": 0x1046, "end": 0x1048,
                        "meaning": (
                            "renewable_item_step_counter_exact_transition"
                        ),
                    },
                    {
                        "start": 0x1214, "end": 0x1218,
                        "meaning": (
                            "encrypted_game_stat_steps_exact_transition"
                        ),
                    },
                    {
                        "start": 0x309A, "end": 0x309B,
                        "meaning": (
                            "daycare_step_counter_exact_transition"
                        ),
                    },
                ],
                "allowed_saveblock2_ranges": [{
                    "start": 14, "end": 19,
                    "meaning": "play_time_vblank_owner",
                }],
                "movement_owned_state": {
                    "walk_steps": walk_steps,
                    **movement_counters,
                    "exact": True,
                },
                "flags_exact": True,
                "engine_special_flags_exact": True,
                "vars_exact": True,
                "items_exact": True,
                "trainers_exact": True,
                "economy_exact": True,
                "party_exact": True,
                "storage_exact": True,
                "exact": True,
            },
            "exact": True,
        }

    @staticmethod
    def _field_roundtrip() -> dict[str, object]:
        return {
            "controls_released": True,
            "running_state_released": True,
            "tile_transition_released": True,
            "start_pressed": True,
            "start_menu_opened": True,
            "menu_callback_observed": "0x0806EA75",
            "back_pressed": True,
            "field_callback_before": "0x08055E75",
            "field_callback_after": "0x08055E75",
            "callback_ordered": True,
            "map_preserved": True,
            "field_input_recovered": True,
        }

    @staticmethod
    def _field_release_post_battle() -> dict[str, object]:
        return {
            "battle_started": False,
            "trainer_battle": False,
            "completed_via_keys": False,
            "forced_switch_count": 0,
            "forced_switch_cursor_observed": False,
            "forced_switch_usable_slot_selected": False,
            "forced_switch_cursor_initial": [],
            "forced_switch_selected_slots": [],
            "forced_switch_selected_hps": [],
            "route": "NONE",
            "outcome": 0,
            "won_or_escaped_not_loss": False,
            "field_released_after_battle": False,
            "start_pressed": False,
            "start_menu_opened": False,
            "back_pressed": False,
            "map_preserved": False,
            "field_input_recovered": False,
        }

    @staticmethod
    def _catalog_side_effects() -> dict[str, object]:
        warp = {
            "group": 96, "map": 23, "warp_id": 255,
            "x": 14, "y": 71,
        }
        world = {
            "map": "96/23", "position": [14, 71],
            "location": deepcopy(warp),
            "continue": deepcopy(warp),
            "dynamic": deepcopy(warp),
            "last_heal": deepcopy(warp),
            "escape": deepcopy(warp),
            "destination": deepcopy(warp),
        }
        object_state = {
            "active": True, "visible": True, "invisible": False,
            "slot": 3, "current": [21, 77], "previous": [21, 77],
        }
        battle_state = {
            "active": False, "trainer_opponent": 0, "enemy_species": 0,
            "outcome": 0,
        }
        input_state = {
            "callback_overworld": True, "controls_locked": False,
            "running_state": 0, "tile_transition_state": 0,
            "field_input_recovered": True, "battle_input_owned": False,
        }
        return {
            "complete": True,
            "coverage": {
                "flags": {
                    "ids_scanned": 6400,
                    "before_fnv1a64": "0" * 16,
                    "after_fnv1a64": "1" * 16,
                },
                "engine_special_flags": {
                    "ids_scanned": 128,
                    "owner_address": "0x02037014",
                    "before_fnv1a64": "F" * 16,
                    "after_fnv1a64": "F" * 16,
                },
                "vars": {
                    "ids_scanned": 768,
                    "before_fnv1a64": "2" * 16,
                    "after_fnv1a64": "3" * 16,
                },
                "items": {
                    "slots_scanned": 186,
                    "entries_before": 1,
                    "entries_after": 0,
                    "before_fnv1a64": "4" * 16,
                    "after_fnv1a64": "5" * 16,
                },
                "trainers": {
                    "ids_scanned": 768,
                    "before_fnv1a64": "6" * 16,
                    "after_fnv1a64": "7" * 16,
                },
                "objects": {
                    "slots_scanned": 16,
                    "active_before": 1,
                    "active_after": 1,
                    "before_fnv1a64": "8" * 16,
                    "after_fnv1a64": "8" * 16,
                },
                "object_templates": {
                    "capacity_scanned": 64,
                    "entries_before": 1,
                    "entries_after": 1,
                    "before_fnv1a64": "9" * 16,
                    "after_fnv1a64": "9" * 16,
                    "changed_local_ids": [],
                    "changes": [],
                },
                "party": {
                    "slots_scanned": 6,
                    "record_size": 100,
                    "raw_byte_length": 600,
                    "count_before": 6,
                    "count_after": 6,
                    "raw_sha256_before": "a" * 64,
                    "raw_sha256_after": "a" * 64,
                },
                "storage": {
                    "raw_byte_length": 0x83D0,
                    "raw_sha256_before": "b" * 64,
                    "raw_sha256_after": "b" * 64,
                },
                "persistent": {
                    "saveblock1": {
                        "bytes_scanned": 0x3D40,
                        "raw_before_fnv1a64": "C" * 16,
                        "raw_after_fnv1a64": "D" * 16,
                        "normalized_before_fnv1a64": "C" * 16,
                        "normalized_after_fnv1a64": "D" * 16,
                        "volatile_ranges": [],
                    },
                    "saveblock2": {
                        "bytes_scanned": 0x0F24,
                        "raw_before_fnv1a64": "E" * 16,
                        "raw_after_fnv1a64": "E" * 16,
                        "normalized_before_fnv1a64": "E" * 16,
                        "normalized_after_fnv1a64": "E" * 16,
                        "volatile_ranges": [{
                            "start": 0x0E, "end": 0x13,
                            "meaning": "play_time_vblank_owner",
                        }],
                    },
                },
            },
            "flags": [
                {"id": 0x519, "before": True, "after": False},
                {"id": 0x119E, "before": False, "after": True},
            ],
            "engine_special_flags": [],
            "vars": [{"id": 0x5170, "before": 7, "after": 8}],
            "items": [{"id": 350, "before": 1, "after": 0}],
            "trainers": [{"id": 25, "before": True, "after": False}],
            "economy": {
                "money": {"before": 3000, "after": 3000},
                "berry_powder": {"before": 500, "after": 500},
                "vega_coins": {"before": 10, "after": 10},
                "cfru_coins": {"before": 10, "after": 10},
            },
            "party": {
                "count_before": 6,
                "count_after": 6,
                "raw_byte_length": 600,
                "raw_sha256_before": "a" * 64,
                "raw_sha256_after": "a" * 64,
            },
            "storage": {
                "changed": False,
                "raw_byte_length": 0x83D0,
                "raw_sha256_before": "b" * 64,
                "raw_sha256_after": "b" * 64,
            },
            "persistent": {
                "saveblock1": {
                    "bytes_scanned": 0x3D40,
                    "raw_changed": True,
                    "normalized_changed": True,
                    "raw_changed_byte_count": 1,
                    "normalized_changed_byte_count": 1,
                    "raw_before_fnv1a64": "C" * 16,
                    "raw_after_fnv1a64": "D" * 16,
                    "normalized_before_fnv1a64": "C" * 16,
                    "normalized_after_fnv1a64": "D" * 16,
                    "changes": [{
                        "offset": 0x0EE0, "before": 0, "after": 1,
                        "volatile": False,
                    }],
                },
                "saveblock2": {
                    "bytes_scanned": 0x0F24,
                    "raw_changed": False,
                    "normalized_changed": False,
                    "raw_changed_byte_count": 0,
                    "normalized_changed_byte_count": 0,
                    "raw_before_fnv1a64": "E" * 16,
                    "raw_after_fnv1a64": "E" * 16,
                    "normalized_before_fnv1a64": "E" * 16,
                    "normalized_after_fnv1a64": "E" * 16,
                    "changes": [],
                },
            },
            "objects": {
                "changed": False,
                "before": [{
                    "slot": 3, "local_id": 15, "map": "96/23",
                    "invisible": False, "visible": True,
                    "current": [21, 77], "previous": [21, 77],
                }],
                "after": [{
                    "slot": 3, "local_id": 15, "map": "96/23",
                    "invisible": False, "visible": True,
                    "current": [21, 77], "previous": [21, 77],
                }],
                "changes": [],
                "changed_local_ids": [],
            },
            "world": {
                "changed": False,
                "before": deepcopy(world),
                "after": deepcopy(world),
            },
            "object": {
                "changed": False,
                "visibility_changed": False,
                "before": deepcopy(object_state),
                "after": deepcopy(object_state),
                "template_before": {
                    "found": True, "slot": 2, "local_id": 15,
                    "graphics_id": 1, "kind": 0,
                    "position": [14, 70], "script": "0x08100000",
                    "hide_flag": 0, "hide_flag_set": False,
                },
                "template_after": {
                    "found": True, "slot": 2, "local_id": 15,
                    "graphics_id": 1, "kind": 0,
                    "position": [14, 70], "script": "0x08100000",
                    "hide_flag": 0, "hide_flag_set": False,
                },
            },
            "battle": {
                "opponent_changed": False,
                "before": deepcopy(battle_state),
                "after": deepcopy(battle_state),
            },
            "input": {
                "recovered": True,
                "before": deepcopy(input_state),
                "after": deepcopy(input_state),
            },
        }

    @staticmethod
    def _catalog() -> dict[str, object]:
        return {
            "schema_version": 1,
            "task": RUNNER.TASK,
            "stage": RUNNER.STAGE,
            "rom_sha256": "0" * 64,
            "entries": [{
                "case_id": "route12_npc_15",
                "owner_key": "OBJECT:096/023:015",
                "group": 96,
                "map": 23,
                "local_id": 15,
                "object": [14, 70],
                "start": [14, 72],
                "action": "UP",
                "approach_steps": 1,
                "interaction_execution": (
                    Stage61MgbaValidationTests._physical_interaction_execution(
                        start=[14, 72], walk_sequence=["UP"],
                        stance=[14, 71], action="UP",
                    )
                ),
                "non_product_shadow_alias": None,
                "expected_template_raw_hex": (
                    Stage61MgbaValidationTests._object_template_raw(
                        local_id=15, graphics_id=18, x=14, y=70,
                        movement_type=9, script_pointer=0x08100000,
                    )
                ),
                "branches": [{
                    "branch_id": "flute_missing",
                    "flags": [{"id": 0x119E, "value": False}],
                    "choice": "ADVANCE",
                    "terminal": "FIELD_RELEASE",
                    "expected_raw_sha256_any": [],
                    "expected_utf8_contains_any": ["12ばん"],
                    "expected_var_result_values_exact": [],
                    "require_visible_text": True,
                    "expect_object_visible": True,
                }],
            }],
        }

    @staticmethod
    def _legacy_catalog() -> dict[str, object]:
        return {
            "schema_version": 1,
            "task": RUNNER.TASK,
            "stage": RUNNER.STAGE,
            "status": "PASS",
            "script_object_count": 1,
            "branch_count": 1,
            "owner_ledger_missing_object_count": 0,
            "static_failure_count": 0,
            "static_failures": [],
            "mgba_contract": {
                "trigger": "stock warp + walk + direction + A",
                "required": "choice/text calibration",
            },
            "npcs": [{
                "npc_id": "OBJECT:003/002:007",
                "group": 3,
                "map": 2,
                "map_key": "PewterCity",
                "object_index": 7,
                "local_id": 8,
                "x": 11,
                "y": 14,
                "graphics_id": 18,
                "movement_type": 9,
                "flag": 0,
                "script_pointer": 0x08100000,
                "owner_role": "EXISTING_PROJECT_OWNER",
                "source_script_pointer": None,
                "branches": ["DEFAULT"],
                "static_owner_status": "PASS",
                "mgba_status": "SCHEDULED_STAGE61_ALL_NPC_INPUT_AUDIT",
                "non_product_shadow_alias": None,
                "runtime_position_state_contract": None,
                "expected_template_raw_hex": (
                    Stage61MgbaValidationTests._object_template_raw(
                        local_id=8, graphics_id=18, x=11, y=14,
                        movement_type=9, script_pointer=0x08100000,
                    )
                ),
                "interaction_execution": (
                    Stage61MgbaValidationTests._physical_interaction_execution(
                        start=[11, 16], walk_sequence=["UP"],
                        stance=[11, 15], action="UP",
                    )
                ),
            }],
        }

    @staticmethod
    def _state_matrix() -> dict[str, object]:
        raw_hash = hashlib.sha256(
            bytes.fromhex("a2a3462e0045032bff")
        ).hexdigest()
        allowed_effects = {
            key: [] for key in RUNNER._POST_EFFECT_KEYS
        }
        allowed_effects.update({
            "flags": [{"id": 0x119E, "operations": ["SET"]}],
            "vars": [{"id": 0x5170, "operations": ["INCREMENT"]}],
            "items": [{"id": 350, "operations": ["REMOVE"]}],
            "trainers": [{"id": 25, "operations": ["CLEAR"]}],
            "persistent": [],
        })
        required_postconditions = {
            "flags": [{"id": 0x119E, "value": True}],
            "engine_special_flags": [],
            "vars": [{"id": 0x5170, "value": 8}],
            "items": [{"id": 350, "count": 0}],
            "trainers": [{"id": 25, "defeated": False}],
            "objects": [], "warp": None, "battle": None,
            "money": None, "berry_powder": None, "coins": None,
            "party": None,
            "storage": None,
            "persistent": [],
        }
        text_oracle = {
            "meaning_source": "synthetic independent fixture",
            "provenance": {
                "kind": "STATIC_SCRIPT_TEXT",
                "source_root": "unit-fixture",
                "source_text_addresses": [0x08101000],
                "raw_sha256s": [raw_hash],
            },
            "ordered_printers": [{
                "kind": "BRANCH_TEXT",
                "instruction_address": "0x08002C44",
                "caller_instruction_address": "0x08102000",
                "source_pointer": "0x08101000",
                "raw_hex": "A2A3462E0045032BFF",
                "raw_sha256": raw_hash,
                "expanded_hex": "A2A3462E0045032BFF",
                "expanded_sha256": raw_hash,
                "provenance": {"kind": "UNIT_STATIC"},
            }],
            "ordered_raw_sha256s": [raw_hash],
            "allowed_ordered_raw_sha256_sequences": [[raw_hash]],
            "visible_text_count": 1,
        }
        interactive = {
            "case_id": "matrix-096-023-015-default-000",
            "base_case_id": "route12_npc_15",
            "owner_key": "OBJECT:096/023:015",
            "catalog_branch": "DEFAULT",
            "owner_role": "EXISTING_PROJECT_OWNER",
            "interaction": {
                "group": 96, "map": 23, "object_index": 15,
                "local_id": 15, "object": [14, 70],
                "runtime_root": "0x08100000",
            },
            "interaction_execution": (
                Stage61MgbaValidationTests._physical_interaction_execution(
                    start=[14, 72], walk_sequence=["UP"],
                    stance=[14, 71], action="UP",
                )
            ),
            "runtime_position_variant": None,
            "runtime_position_map_load_required": False,
            "state": {
                "flags": [{"id": 0x18B4, "value": False}],
                "vars": [{"id": 0x5170, "value": 7}],
                "items": [{"id": 350, "count": 1}],
                "trainers": [{"id": 25, "defeated": True}],
            },
            "expected_object_visible": True,
            "interaction_expected": True,
            "choice_candidates": ["ADVANCE", "CANCEL"],
            "expected_terminal": "CALIBRATE",
            "reachability_basis": "TEST",
            "static_path_ids": [],
            "baseline": True,
            "input_sequences": [{
                "sequence_id": "advance",
                "tokens": ["A"],
                "expected_static_branch_token": "DEFAULT_ADVANCE",
                "basis": {
                    "kind": "STATIC_CFG",
                    "source_instruction_address": 0x08100000,
                },
                "visible_text_expected": True,
                "silent_text_basis": None,
                "text_oracle": deepcopy(text_oracle),
                "required_postconditions": deepcopy(required_postconditions),
                "battle_start_required_postconditions": None,
                "post_battle_continuation": None,
            }, {
                "sequence_id": "cancel",
                "tokens": ["A", "B"],
                "expected_static_branch_token": "DEFAULT_CANCEL",
                "basis": {
                    "kind": "STATIC_CFG",
                    "source_instruction_address": 0x08100002,
                },
                "visible_text_expected": True,
                "silent_text_basis": None,
                "text_oracle": deepcopy(text_oracle),
                "required_postconditions": deepcopy(required_postconditions),
                "battle_start_required_postconditions": None,
                "post_battle_continuation": None,
            }],
            "allowed_post_effect_families": [
                "FLAG", "VAR", "ITEM", "TRAINER",
            ],
            "allowed_post_effects": allowed_effects,
        }
        hidden = deepcopy(interactive)
        hidden.update({
            "case_id": "matrix-096-023-015-collected-000",
            "catalog_branch": "COLLECTED",
            "expected_object_visible": False,
            "interaction_expected": False,
            "choice_candidates": [],
            "expected_terminal": "NO_INTERACTION_HIDDEN",
        })
        for key in (
            "input_sequences", "allowed_post_effect_families",
            "allowed_post_effects",
        ):
            hidden.pop(key, None)
        hidden["state"] = {
            "flags": [{"id": 0x149E, "value": True}],
            "vars": [], "items": [], "trainers": [],
        }
        return {
            "schema_version": 1,
            "task": RUNNER.TASK,
            "stage": RUNNER.STAGE,
            "status": "PASS",
            "rom_sha256": "0" * 64,
            "counts": {
                "matrix_case_count": 2,
                "interactive_case_count": 1,
                "hidden_assertion_count": 1,
            },
            "runner_projection": {
                "mode": "EXTENDED_STATE_TSV_REQUIRED",
                "required_columns": [
                    "flags", "vars", "items", "trainers",
                    "expect_visible", "expect_interaction",
                    "runtime_position_control", "interaction_execution",
                ],
            },
            "assertions": {"synthetic_contract": True},
            "cases": [interactive, hidden],
        }

    @staticmethod
    def _calibration_document() -> dict[str, object]:
        raw = bytes.fromhex("a2a3462e0045032bff")
        capture = {
            "message_state_address": "0x02036FD0",
            "string_address": "0x02021C88",
            "printer_entry": RUNNER._TEXT_PRINTER_ENTRY,
            "printer_entry_preimage_hex": RUNNER._TEXT_PRINTER_PREIMAGE_HEX,
            "template_printer_entry": RUNNER._TEMPLATE_TEXT_PRINTER_ENTRY,
            "template_printer_entry_preimage_hex": (
                RUNNER._TEMPLATE_TEXT_PRINTER_PREIMAGE_HEX
            ),
            "execution": {
                "invalid_control_flow": False, "first_invalid_pc": None,
                "cpsr": None, "lr": None,
            },
            "active_frames": 2,
            "state_counts": [20, 0, 2, 0],
            "var_result": {
                "address": "0x02037004", "seen": True,
                "first": 1, "last": 0, "changes": 1,
                "values": [1, 0],
            },
            "framebuffer": {
                "first_fnv1a64": "0" * 16,
                "last_fnv1a64": "1" * 16,
                "changed_frames": 1,
                "maximum_baseline_pixel_difference": 2500,
            },
            "messages": [{
                "state": 2,
                "size": len(raw),
                "raw_hex": raw.hex().upper(),
                "raw_fnv1a64": RUNNER._fnv1a64(raw),
                "framebuffer_fnv1a64": "3" * 16,
            }],
            "printer_calls": [{
                "frame": 100,
                "instruction_address": RUNNER._TEXT_PRINTER_ENTRY,
                "caller_instruction_address": "0x08102000",
                "window": 0, "font": 2,
                "text_pointer": "0x08101000", "speed": 1,
                "size": len(raw), "raw_hex": raw.hex().upper(),
                "raw_fnv1a64": RUNNER._fnv1a64(raw),
            }],
        }
        paths = []
        for choice in ("CANCEL", "NO"):
            paths.append({
                "choice": choice,
                "terminal": "FIELD_RELEASE",
                "field_released": True,
                "battle_started": False,
                "capture": deepcopy(capture),
            })
        producer = RUNNER._none_runtime_position_producer(3, 2)
        control = RUNNER._none_runtime_position_control()
        return {
            "schema_version": 2,
            "status": "PASS",
            "case": "catalog_calibrate",
            "baseline_natural_continue": True,
            "choice_probe_via_state_restore": True,
            "pulse_limit": 48,
            "results": [{
                "case_id": "cal-003-002-007",
                "owner_key": "OBJECT:003/002:007",
                "map": "3/2",
                "local_id": 8,
                "object": [11, 14],
                "visibility_flag": 0,
                "status": "RESOLVED",
                "failure_reason": "NONE",
                "attempted_ports": 1,
                "attempted_choices": 4,
                "port": {
                    "start": [11, 16],
                    "action_key": RUNNER.KEYS["UP"],
                    "approach_steps": 1,
                },
                "runtime_position_producer": (
                    Stage61MgbaValidationTests._runtime_position_observation(
                        producer, control, requested=[11, 16], visible=True,
                    )
                ),
                "successful_paths": paths,
            }],
            "fixture_count": 1,
            "resolved": 1,
            "unresolved": 0,
            "failed": 0,
            "untested": 0,
            "warnings": 0,
        }

    @classmethod
    def _all_case_promotion_inputs(
        cls, digest: str = "a" * 64,
    ) -> tuple[dict[str, object], dict[str, object]]:
        """Small fixture with the builder's real all-case oracle root ABI."""
        matrix = cls._state_matrix()
        case = deepcopy(matrix["cases"][0])
        case_id = "matrix-003-002-007-default-000"
        sequence = deepcopy(case["input_sequences"][0])
        sequence_id = f"{case_id}--seq-000-a"
        sequence["sequence_id"] = sequence_id
        sequence["text_oracle"]["provenance"] = {
            "kind": "INDEPENDENT_STATIC_ORACLE",
            "source_root": "0x08100000",
            "stage61_root": "0x08100000",
            "sequence_id": sequence_id,
            "not_learned_from_mgba_calibration": True,
        }
        sequence["text_oracle"]["allowed_runtime_buffer_ranges"] = []
        case.update({
            "case_id": case_id,
            "base_case_id": "cal-003-002-007",
            "owner_key": "OBJECT:003/002:007",
            "catalog_branch": "DEFAULT",
            "interaction": {
                "group": 3, "map": 2, "object_index": 7,
                "local_id": 8, "object": [11, 14],
                "runtime_root": "0x08100000",
            },
            "interaction_execution": cls._physical_interaction_execution(
                start=[11, 16], walk_sequence=["UP"],
                stance=[11, 15], action="UP",
            ),
            "state": {
                "flags": [], "vars": [], "items": [], "trainers": [],
            },
            "choice_candidates": ["CANCEL", "NO"],
            "input_sequences": [sequence],
            "control_requirements": {
                "external": [], "internal": [], "missing_external": [],
                "all_external_requirements_materialized": True,
            },
        })
        matrix.update({
            "rom_sha256": digest,
            "counts": {
                "matrix_case_count": 1,
                "interactive_case_count": 1,
                "hidden_assertion_count": 0,
            },
            "cases": [case],
        })

        source_sequence = {
            "sequence_id": sequence_id,
            "tokens": deepcopy(sequence["tokens"]),
            "expected_static_branch_token": (
                sequence["expected_static_branch_token"]
            ),
            "basis": deepcopy(sequence["basis"]),
            "visible_text_expected": sequence["visible_text_expected"],
            "silent_text_basis": deepcopy(sequence["silent_text_basis"]),
            "decision_trace": [],
            "visible_printers": deepcopy(
                sequence["text_oracle"]["ordered_printers"]
            ),
            "control_requirements": {
                "external": [], "internal": [],
                "all_external_requirements_explicit": True,
            },
            "effect_contract": {
                "required_final": deepcopy(
                    sequence["required_postconditions"]
                ),
                "battle_start_required_postconditions": None,
            },
        }
        case_oracle = {
            "schema_version": 1,
            "kind": "STAGE61_INDEPENDENT_INTERACTION_ORACLE",
            "status": "PASS",
            "case_id": case_id,
            "owner_key": "OBJECT:003/002:007",
            "source_root": "0x08100000",
            "stage61_root": "0x08100000",
            "input_sequences": [deepcopy(sequence)],
            "sequences": [source_sequence],
            "text_oracle": {
                "meaning_source": "UNIT_INDEPENDENT_CFG",
                "provenance": {"kind": "INDEPENDENT_STATIC_ORACLE"},
            },
            "allowed_post_effect_families": deepcopy(
                case["allowed_post_effect_families"]
            ),
            "allowed_post_effects": deepcopy(case["allowed_post_effects"]),
            "required_postconditions_by_sequence": {
                sequence_id: deepcopy(sequence["required_postconditions"]),
            },
            "battle_start_required_postconditions": {
                sequence_id: None,
            },
            "explicit_source_suppression": None,
            "assertions": {
                "event_cfg_executed": True,
                "callstd_followed_through_pinned_table": True,
                "all_paths_terminal": True,
                "all_visible_printers_ordered": True,
                "expected_text_independent_of_mgba_calibration": True,
                "all_effect_owners_covered_once": True,
                "deterministic_order": True,
                "sequence_ids_case_prefixed_unique": True,
                "explicit_source_suppression_verified": True,
                "unresolved_zero": True,
            },
        }
        case_oracle["oracle_sha256"] = RUNNER._oracle_canonical_sha256(
            case_oracle
        )
        oracle = {
            "schema_version": 1,
            "kind": RUNNER._ALL_CASE_ORACLE_KIND,
            "status": "PASS",
            "case_count": 1,
            "generated_case_count": 1,
            "unresolved_case_count": 0,
            "cases": [case_oracle],
            "unresolved": [],
            "decision_coverage": {"missing_signature_count": 0},
            "assertions": {
                "all_cases_covered_once": True,
                "all_cases_have_exact_oracle": True,
                "deterministic_order": True,
                "expected_text_independent_of_stage61_calibration": True,
                "all_sequence_ids_globally_unique": True,
                "all_reachable_menu_signatures_covered": True,
                "unresolved_zero": True,
            },
        }
        oracle["audit_sha256"] = RUNNER._oracle_canonical_sha256(oracle)
        catalog_sha256 = RUNNER._oracle_canonical_sha256(oracle)
        matrix["oracle"] = {
            "kind": RUNNER._ALL_CASE_ORACLE_KIND,
            "catalog_sha256": catalog_sha256,
            "case_count": 1,
        }
        matrix["runtime_control_expansion"] = {
            "oracle_catalog_sha256": catalog_sha256,
        }
        return matrix, oracle

    def test_input_sequence_tsv_has_strict_post_battle_nine_fields(
        self,
    ) -> None:
        sequence = {
            "sequence_id": "case--seq-0000-deadbeefdeadbeef",
            "expected_static_branch_token": "NONE",
            "visible_text_expected": False,
            "silent_text_basis": None,
            "tokens": ["A"],
            "post_battle_continuation": None,
        }
        self.assertEqual(
            RUNNER._encode_input_sequence_tsv(sequence).split("@"),
            [
                sequence["sequence_id"], "NONE", "0", "-", "A",
                "NONE", "-", "-", "-",
            ],
        )
        standard = deepcopy(sequence)
        standard["post_battle_continuation"] = {
            "resume_kind": "STANDARD", "resume_pc": None, "tokens": [],
            "chained_battles": [],
        }
        self.assertEqual(
            RUNNER._encode_input_sequence_tsv(standard).split("@")[5:],
            ["STANDARD", "-", "-", "-"],
        )
        explicit = deepcopy(sequence)
        explicit["post_battle_continuation"] = {
            "resume_kind": "EXPLICIT", "resume_pc": "0x08123456",
            "tokens": ["ADVANCE_TEXT", "A"],
            "chained_battles": [{
                "phase_index": 2,
                "battle_kind": "TRAINER",
                "trainer_id": 171,
                "start_instruction_address": "0x08124567",
                "resume_kind": "NEXT_PC",
                "resume_pc": "0x08124571",
            }],
        }
        self.assertEqual(
            RUNNER._encode_input_sequence_tsv(explicit).split("@")[5:],
            [
                "EXPLICIT", str(0x08123456), "ADVANCE_TEXT,A",
                f"2|TRAINER|171|{0x08124567}|NEXT_PC|{0x08124571}",
            ],
        )
        for mutation in (
            lambda row: row["post_battle_continuation"].pop("resume_kind"),
            lambda row: row["post_battle_continuation"].__setitem__(
                "resume_pc", None,
            ),
            lambda row: row["post_battle_continuation"].__setitem__(
                "tokens", ["BAD@TOKEN"],
            ),
        ):
            broken = deepcopy(explicit)
            mutation(broken)
            with self.subTest(mutation=mutation), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._encode_input_sequence_tsv(broken)

    def test_post_battle_continuation_is_phase_exact_and_callsite_exact(
        self,
    ) -> None:
        def capture(*, visible: bool) -> dict[str, object]:
            result = deepcopy(
                self._calibration_document()["results"][0][
                    "successful_paths"
                ][0]["capture"]
            )
            if not visible:
                result["messages"] = []
                result["printer_calls"] = []
            return result

        def actual(
            *, visible: bool, effect_enabled: bool,
            resume_kind: str = "STANDARD",
            resume_pc: str | None = None,
        ) -> dict[str, object]:
            return {
                "phase": "POST_BATTLE_CONTINUATION",
                "resume_kind": resume_kind,
                "boundary_observed": True,
                "expected_resume_pc": resume_pc,
                "observed_resume_pc": (
                    "0x08000000" if resume_kind == "STANDARD" else resume_pc
                ),
                "resume_pc_hit_count": 1,
                "input_tokens": [],
                "input_step_count": 0,
                "input_steps_consumed": 0,
                "premature_terminal": False,
                "terminal": "FIELD_RELEASE",
                "field_released": True,
                "capture": capture(visible=visible),
                "decision_watch": {
                    "special_result_address": "0x02037004",
                    "initial_value": 0, "values": [], "change_count": 0,
                },
                "effect_watch": {
                    "enabled": effect_enabled,
                    "hook_hits_before": 0,
                    "hook_hits_after": 0,
                    "hook_hit_delta": 0,
                },
                "chained_battles": [],
            }

        standard_source = RUNNER._standard_empty_post_battle_source()
        rom_raw = bytes((0x6B, 0x02))
        RUNNER._validate_post_battle_continuation_observation(
            actual(visible=False, effect_enabled=True), standard_source,
            case_id="catalog-standard", charmap={}, rom_raw=rom_raw,
            effect_watch_required=True,
        )
        RUNNER._validate_post_battle_continuation_observation(
            actual(visible=False, effect_enabled=False), standard_source,
            case_id="product-standard", charmap={}, rom_raw=rom_raw,
            effect_watch_required=False,
        )

        raw = bytes.fromhex("a2a3462e0045032bff")
        visible_source = {
            **deepcopy(standard_source),
            "resume_kind": "EXPLICIT",
            "resume_pc": "0x08123456",
            "visible_printers": [{
                "instruction_address": RUNNER._TEXT_PRINTER_ENTRY,
                "caller_instruction_address": "0x08102000",
                "expanded_sha256": hashlib.sha256(raw).hexdigest(),
            }],
        }
        visible_actual = actual(
            visible=True, effect_enabled=True,
            resume_kind="EXPLICIT", resume_pc="0x08123456",
        )
        RUNNER._validate_post_battle_continuation_observation(
            visible_actual, visible_source, case_id="event-explicit",
            charmap={}, rom_raw=rom_raw, effect_watch_required=True,
        )
        chained_source = {
            **deepcopy(standard_source),
            "resume_kind": "EXPLICIT",
            "resume_pc": "0x08123456",
            "chained_battles": [{
                "phase_index": 2,
                "battle_kind": "TRAINER",
                "trainer_id": 171,
                "start_instruction_address": "0x08124567",
                "resume_kind": "NEXT_PC",
                "resume_pc": "0x08124571",
            }],
        }
        chained_actual = actual(
            visible=False, effect_enabled=True,
            resume_kind="EXPLICIT", resume_pc="0x08123456",
        )
        chained_actual["chained_battles"] = [{
            "phase_index": 2,
            "battle_kind": "TRAINER",
            "source_start_instruction_address": "0x08124567",
            "expected_trainer_id": 171,
            "trainer_battle": True,
            "observed_trainer_id": 171,
            "completed_via_keys": True,
            "outcome": 1,
            "won_or_escaped_not_loss": True,
            "resume_kind": "NEXT_PC",
            "expected_resume_pc": "0x08124571",
            "observed_resume_pc": "0x08124571",
            "resume_pc_hit_count": 1,
        }]
        RUNNER._validate_post_battle_continuation_observation(
            chained_actual, chained_source, case_id="event-chained",
            charmap={}, rom_raw=rom_raw, effect_watch_required=True,
        )
        chained_drift = deepcopy(chained_actual)
        chained_drift["chained_battles"][0]["observed_trainer_id"] = 172
        with self.assertRaises(RUNNER.Stage61MgbaError):
            RUNNER._validate_post_battle_continuation_observation(
                chained_drift, chained_source, case_id="event-chained-drift",
                charmap={}, rom_raw=rom_raw, effect_watch_required=True,
            )
        mutations = {
            "printer-entry": lambda row: row["capture"]["printer_calls"][0]
                .__setitem__("instruction_address", RUNNER._TEMPLATE_TEXT_PRINTER_ENTRY),
            "printer-caller": lambda row: row["capture"]["printer_calls"][0]
                .__setitem__("caller_instruction_address", "0x08102002"),
            "printer-hash": lambda row: row["capture"]["printer_calls"][0]
                .__setitem__("raw_hex", "41FF"),
            "effect-state": lambda row: row["effect_watch"].__setitem__(
                "enabled", False,
            ),
            "resume-pc": lambda row: row.__setitem__(
                "observed_resume_pc", "0x08123458",
            ),
            "extra": lambda row: row.__setitem__("extra", True),
        }
        for label, mutation in mutations.items():
            broken = deepcopy(visible_actual)
            mutation(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._validate_post_battle_continuation_observation(
                    broken, visible_source, case_id=label,
                    charmap={}, rom_raw=rom_raw,
                    effect_watch_required=True,
                )

    def test_effect_observer_env_is_scoped_and_all_cases_receive_rom(
        self,
    ) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="{}", stderr="",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rom = root / "stage61.gba"
            rom.write_bytes(b"\x6B\x02")
            work = root / "product"
            with patch.object(
                RUNNER.subprocess, "run", return_value=completed,
            ) as process, patch.object(
                RUNNER, "_validate_c_framebuffer_artifact_join",
            ), patch.object(
                RUNNER, "_validate_case", return_value={},
            ) as validate_case, patch.object(
                RUNNER, "_artifact_rows", return_value=[],
            ), patch.object(
                RUNNER, "_required_artifact_count", return_value=0,
            ):
                RUNNER._run_process(
                    Path("/tmp/fake-mgba"), rom, "product-generic", work,
                    {
                        "S61_EFFECT_RAW_WATCH_TSV": "/tmp/raw.tsv",
                        "S61_EFFECT_OBSERVER_OUTPUT": "/tmp/out.jsonl",
                    },
                    {}, {}, {}, {}, 60,
                )
            environment = process.call_args.kwargs["env"]
            self.assertNotIn("S61_EFFECT_RAW_WATCH_TSV", environment)
            self.assertNotIn("S61_EFFECT_OBSERVER_OUTPUT", environment)
            self.assertEqual(
                validate_case.call_args.kwargs["rom_raw"], b"\x6B\x02",
            )

            persistence = root / "persistence"
            persistence.mkdir()
            with patch.object(
                RUNNER.subprocess, "run", return_value=completed,
            ) as process, patch.object(
                RUNNER, "_validate_c_framebuffer_artifact_join",
            ):
                RUNNER._invoke_persistence_phase(
                    Path("/tmp/fake-mgba"), rom, "READ", persistence,
                    {
                        "S61_EFFECT_RAW_WATCH_TSV": "/tmp/raw.tsv",
                        "S61_EFFECT_OBSERVER_OUTPUT": "/tmp/out.jsonl",
                    }, 60,
                )
            environment = process.call_args.kwargs["env"]
            self.assertNotIn("S61_EFFECT_RAW_WATCH_TSV", environment)
            self.assertNotIn("S61_EFFECT_OBSERVER_OUTPUT", environment)

    def test_effect_runtime_root_requires_cyclic_integration_exactly(
        self,
    ) -> None:
        rom_sha256 = "a" * 64
        object_rows = [{
            "case_id": "object-a", "interaction_expected": True,
            "runtime_control_assignment": {
                "effect_signature_ids": ["effect-a", "effect-b"],
            },
            "input_sequences": [{
                "sequence_id": "object-a-seq-0",
                "basis": {"effect_signature_id": "effect-a"},
            }, {
                "sequence_id": "object-a-seq-1",
                "basis": {"effect_signature_id": "effect-b"},
            }],
        }, {
            "case_id": "object-hidden", "interaction_expected": False,
            "runtime_control_assignment": {
                "effect_signature_ids": ["effect-hidden"],
            },
            "input_sequences": [],
        }]
        ordinary_event = {"case_id": "event-a", "case_kind": "EVENT_RUNTIME"}
        map_event = {
            "case_id": "map-lifecycle-003-004-0123456789abcdefabcd",
            "case_kind": "MAP_LIFECYCLE_COMPOSITE",
            "effect_signature_ids": ["effect-map"],
            "input_sequences": [{
                "sequence_id": "map-seq-0", "control_requirements": {},
                "effect_signature_ids": ["effect-map"],
            }],
        }
        abi = {
            "kind": "STAGE61_INTERACTION_ABI_MANIFEST",
            "status": "PASS", "stage61_sha256": rom_sha256,
        }
        abi["manifest_sha256"] = RUNNER._effect_binding_sha256(abi)
        runtime = {
            "schema_version": 1,
            "kind": "STAGE61_RUNTIME_CONTROL_EXPANSION_CONTRACT",
            "status": "PASS", "stage61_sha256": rom_sha256,
            "input_provenance": {
                "interaction_abi_manifest_sha256": abi["manifest_sha256"],
            },
            "counts": {}, "roots": [], "decision_signatures": [],
            "effect_signatures": [], "effect_templates": [],
            "effect_instances": [], "effect_case_bindings": [],
            "effect_instance_watch_bindings": [],
            "no_dispatch_contracts": [],
            "no_dispatch_watch_bindings": [], "runner_fixtures": {},
            "event_owner_trigger_contracts": [],
            "hidden_item_execution": {},
            "cyclic_decision_contract_integration": {},
            "event_runtime_cases": [ordinary_event, map_event],
            "unresolved": [],
            "unresolved_count": 0, "assertions": {"complete": True},
        }
        runtime["contract_sha256"] = RUNNER._effect_binding_sha256(runtime)
        plan = {
            "schema_version": 1,
            "kind": "STAGE61_EFFECT_RAW_WATCH_PLAN_V1", "watches": [],
        }
        plan["plan_sha256"] = RUNNER._effect_binding_sha256(plan)

        def write(path: Path, value: object) -> None:
            path.write_text(json.dumps(value), encoding="utf-8")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime_path = root / "runtime.json"
            plan_path = root / "plan.json"
            abi_path = root / "abi.json"
            write(runtime_path, runtime)
            write(plan_path, plan)
            write(abi_path, abi)
            with patch(
                "scripts.build_stage61_display_npc_event_audit."
                "_mgba_effect_registry_source_binding",
                return_value={"binding": "unit"},
            ) as binding_builder, patch(
                "scripts.build_stage61_display_npc_event_audit."
                "_validate_mgba_effect_registry_binding",
            ):
                loaded, _, binding, _, runtime_identity = (
                    RUNNER.load_effect_observer_inputs(
                    runtime_control_path=runtime_path,
                    raw_watch_plan_path=plan_path,
                    interaction_abi_path=abi_path,
                    rom_raw=b"", rom_sha256=rom_sha256,
                    matrix_schema={"cases": object_rows},
                    )
                )
            self.assertEqual(
                loaded["cyclic_decision_contract_integration"], {},
            )
            self.assertEqual(binding, {"binding": "unit"})
            self.assertEqual(
                runtime_identity["declared_sha256"],
                runtime["contract_sha256"],
            )
            self.assertEqual(
                runtime_identity["artifact_sha256"],
                hashlib.sha256(runtime_path.read_bytes()).hexdigest(),
            )
            effect_object_rows = binding_builder.call_args.args[1]
            effect_event_rows = binding_builder.call_args.args[2]
            self.assertEqual(
                [row["case_id"] for row in effect_object_rows],
                ["object-a", "object-hidden"],
            )
            self.assertEqual(
                [row["case_id"] for row in effect_event_rows],
                ["event-a", map_event["case_id"]],
            )
            for label, mutation in (
                (
                    "missing",
                    lambda row: row.pop(
                        "cyclic_decision_contract_integration"
                    ),
                ),
                ("extra", lambda row: row.__setitem__("extra", True)),
            ):
                broken = deepcopy(runtime)
                mutation(broken)
                broken.pop("contract_sha256", None)
                broken["contract_sha256"] = (
                    RUNNER._effect_binding_sha256(broken)
                )
                write(runtime_path, broken)
                with self.subTest(label=label), self.assertRaises(
                    RUNNER.Stage61MgbaError
                ):
                    RUNNER.load_effect_observer_inputs(
                        runtime_control_path=runtime_path,
                        raw_watch_plan_path=plan_path,
                        interaction_abi_path=abi_path,
                        rom_raw=b"", rom_sha256=rom_sha256,
                        matrix_schema={"cases": object_rows},
                    )

    def test_effect_observer_projects_source_rows_to_virtual_runs(self) -> None:
        runtime = {
            "effect_instances": [
                {"instance_id": "instance-a", "case_id": "object-a--run-0000"},
                {"instance_id": "instance-b", "case_id": "object-a--run-0001"},
                {"instance_id": "instance-map", "case_id": "map-a--run-0000"},
            ],
            "effect_instance_watch_bindings": [
                {"instance_id": "instance-a", "watch_ids": ["watch-a"]},
                {"instance_id": "instance-b", "watch_ids": ["watch-b"]},
                {"instance_id": "instance-map", "watch_ids": ["watch-map"]},
            ],
            "no_dispatch_watch_bindings": [{
                "case_id": "hidden-a", "contract_sha256": "a" * 64,
                "watch_ids": ["watch-hidden"],
            }],
        }
        self.assertEqual(
            RUNNER._effect_observer_expected_case_ids(
                runtime, ["object-a", "hidden-a", "map-a--run-0000"],
            ),
            [
                "object-a--run-0000", "object-a--run-0001", "hidden-a",
                "map-a--run-0000",
            ],
        )
        for sources in (
            ["missing-a"],
            ["object-a", "object-a--run-0000"],
            ["object-a", "object-a"],
        ):
            with self.subTest(sources=sources), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                    RUNNER._effect_observer_expected_case_ids(runtime, sources)

    def test_effect_observer_shard_union_closes_selected_runtime_partition(
        self,
    ) -> None:
        runtime = {
            "effect_instances": [{
                "case_id": "case-a", "instance_id": "instance-a",
            }, {
                "case_id": "case-c", "instance_id": "instance-c",
            }],
            "effect_instance_watch_bindings": [{
                "instance_id": "instance-a", "watch_ids": ["watch-a"],
            }, {
                "instance_id": "instance-c", "watch_ids": ["watch-c"],
            }],
            "no_dispatch_watch_bindings": [{
                "case_id": "case-b", "contract_sha256": "b" * 64,
                "watch_ids": ["watch-b"],
            }, {
                "case_id": "case-d", "contract_sha256": "d" * 64,
                "watch_ids": ["watch-d"],
            }],
        }
        instance_a = {
            "case_id": "case-a", "instance_id": "instance-a",
            "watch_ids": ["watch-a"], "raw": {}, "hooks": [],
        }
        no_dispatch_b = {
            "case_id": "case-b", "watch_ids": ["watch-b"],
            "raw": {}, "hooks": [],
        }

        def observer(instances: list[dict], no_dispatch: list[dict]) -> dict:
            return {
                "instance_observations": instances,
                "instance_observations_sha256": RUNNER._sha256(
                    RUNNER._stable(instances).encode("utf-8")
                ),
                "no_dispatch_observations": no_dispatch,
                "no_dispatch_observations_sha256": RUNNER._sha256(
                    RUNNER._stable(no_dispatch).encode("utf-8")
                ),
            }

        documents = [{"effect_observer": observer([instance_a], [])}, {
            "effect_observer": observer([], [no_dispatch_b]),
        }]
        merged: dict[str, object] = {}
        RUNNER._merge_effect_observer_shards(merged, documents)
        RUNNER._validate_merged_effect_observer_closure(
            merged, runtime=runtime, expected_case_ids=["case-a", "case-b"],
        )
        for label, mutate in (
            ("missing", lambda rows: rows.pop(0)),
            ("extra", lambda rows: rows.append({
                "case_id": "case-c", "instance_id": "instance-c",
                "watch_ids": ["watch-c"], "raw": {}, "hooks": [],
            })),
        ):
            broken = deepcopy(merged)
            rows = broken["effect_observer"]["instance_observations"]
            mutate(rows)
            broken["effect_observer"]["instance_count"] = len(rows)
            with self.subTest(label=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "instance exact closure",
            ):
                RUNNER._validate_merged_effect_observer_closure(
                    broken, runtime=runtime,
                    expected_case_ids=["case-a", "case-b"],
                )
        duplicate_documents = deepcopy(documents)
        duplicate_documents[1]["effect_observer"] = observer(
            [deepcopy(instance_a)], [no_dispatch_b],
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "case×instance重複",
        ):
            RUNNER._merge_effect_observer_shards({}, duplicate_documents)

    def test_map_lifecycle_c_observation_is_full_order_and_phase_exact(
        self,
    ) -> None:
        destination = {"group": 3, "map": 4}
        owner4 = "MAP:003/004:000:001"
        owner2 = "MAP:003/004:001:000"
        topology = {
            "by_tag": {
                "4": {
                    "record_address": 0x08100000,
                    "condition_table_pointer": 0x08100100,
                    "conditions": [{
                        "condition_index": 0,
                        "record_address": 0x08100100,
                        "root_field_address": 0x08100104,
                        "root_pc": 0x08101000,
                    }, {
                        "condition_index": 1,
                        "record_address": 0x08100108,
                        "root_field_address": 0x0810010C,
                        "root_pc": 0x08101010,
                    }],
                },
                "2": {
                    "record_address": 0x08100020,
                    "condition_table_pointer": 0x08100200,
                    "conditions": [{
                        "condition_index": 0,
                        "record_address": 0x08100200,
                        "root_field_address": 0x08100204,
                        "root_pc": 0x08102000,
                    }],
                },
            },
        }
        empty = {
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
                "tag": tag, "result": result, **empty, **payload,
            }

        attempts = [
            attempt(0, "DESTINATION_TEMP_CLEAR", None, "ENGINE_TRANSFORM"),
            attempt(1, "INITIAL_TRANSITION", 3, "TAG_ABSENT"),
            attempt(2, "INITIAL_LOAD", 1, "TAG_ABSENT"),
            attempt(3, "INITIAL_RESUME", 5, "TAG_ABSENT"),
            attempt(
                4, "INITIAL_WARP_IN", 4, "DISPATCH", outer_index=0,
                outer_record_address="0x08100000",
                selected_condition_index=1,
                selected_condition_record_address="0x08100108",
                root_field_address="0x0810010C",
                root_pc="0x08101010", owner_id=owner4,
            ),
            attempt(
                5, "PRE_FIELD_INPUT_ON_FRAME", 2, "DISPATCH",
                outer_index=1, outer_record_address="0x08100020",
                selected_condition_index=0,
                selected_condition_record_address="0x08100200",
                root_field_address="0x08100204",
                root_pc="0x08102000", owner_id=owner2,
            ),
            attempt(
                6, "PRE_FIELD_INPUT_ON_FRAME", 2,
                "NO_CONDITION_MATCH", outer_index=1,
                outer_record_address="0x08100020",
            ),
        ]
        sequence = {
            "include_field_return": False,
            "ordered_attempts": attempts,
            "ordered_dispatches": [{
                "dispatch_ordinal": 0, "attempt_ordinal": 4, "tag": 4,
                "owner_id": owner4, "root_pc": "0x08101010",
                "root_field_address": "0x0810010C",
            }, {
                "dispatch_ordinal": 1, "attempt_ordinal": 5, "tag": 2,
                "owner_id": owner2, "root_pc": "0x08102000",
                "root_field_address": "0x08100204",
            }],
            "phase_controls": [{
                "phase_marker": "PRE_TRANSITION",
                "variables": [], "flags": [],
            }, {
                "phase_marker": "PRE_FIELD_INPUT",
                "variables": [{"id": 0x4001, "value": 1}], "flags": [],
            }],
        }
        projected_attempts = []
        for observed_ordinal, source in enumerate(attempts[1:]):
            projected_attempts.append({
                "observed_attempt_ordinal": observed_ordinal,
                "source_attempt_ordinal": observed_ordinal + 1,
                "phase_marker": "INITIAL_LOAD",
                "source_phase_marker": source["phase_marker"],
                **{key: source[key] for key in (
                    "tag", "result", "outer_index",
                    "outer_record_address", "selected_condition_index",
                    "selected_condition_record_address",
                    "root_field_address", "root_pc", "owner_id",
                )},
            })
        projected_dispatches = []
        for dispatch_ordinal, source_ordinal in enumerate((4, 5)):
            source = attempts[source_ordinal]
            projected_dispatches.append({
                "dispatch_ordinal": dispatch_ordinal,
                "observed_attempt_ordinal": source_ordinal - 1,
                "source_attempt_ordinal": source_ordinal,
                "phase_marker": "INITIAL_LOAD",
                "source_phase_marker": source["phase_marker"],
                "tag": source["tag"], "owner_id": source["owner_id"],
                "outer_record_address": source["outer_record_address"],
                "selected_condition_index": source[
                    "selected_condition_index"
                ],
                "selected_condition_record_address": source[
                    "selected_condition_record_address"
                ],
                "root_field_address": source["root_field_address"],
                "root_pc": source["root_pc"],
            })
        expected_projection = {
            "producer_kind": "STOCK_WARP", "include_field_return": False,
            "phase_boundaries": [{
                "boundary_ordinal": 0, "phase_marker": "INITIAL_LOAD",
                "before_observed_attempt_ordinal": 0,
                "before_source_attempt_ordinal": 1,
            }],
            "ordered_attempts": projected_attempts,
            "ordered_dispatches": projected_dispatches,
            "attempt_count": len(projected_attempts),
            "dispatch_count": len(projected_dispatches),
            "projection_sha256": "a" * 64,
        }
        fixture = {
            "map": destination,
            "map_lifecycle": {"common": {}, "sequence": sequence},
            "input_sequence": {"basis": {
                "map_lifecycle_expected_ordered_projection":
                    expected_projection,
            }},
        }
        observations: list[dict[str, object]] = []
        registers = {
            "r0": "0x00000000", "r1": "0x00000000",
            "r2": "0x00000000", "r4": "0x00000000",
            "r5": "0x00000000", "r6": "0x00000000",
            "lr": "0x00000000",
        }
        observations.append({
            "kind": "PHASE_BOUNDARY", "ordinal": 0,
            "instruction_ordinal": 0, "instruction_pc": "0x08000000",
            "frame": 0, "phase_marker": "INITIAL_LOAD",
            "phase_boundary": True, "attempt_ordinal": None, "tag": None,
            "result": "NONE", "map": destination,
            "outer_record_address": None, "root_field_address": None,
            "root_pc": None, "registers": deepcopy(registers),
        })
        instruction_ordinal = 1
        first_attempt_instruction: dict[int, int] = {}
        for c_ordinal, source_attempt in enumerate(attempts[1:]):
            first_attempt_instruction[c_ordinal] = instruction_ordinal
            for expected in RUNNER._expected_map_lifecycle_observations_for_attempt(
                source_attempt, topology,
            ):
                actual_registers = deepcopy(registers)
                if expected["kind"] in {
                    "DIRECT_ATTEMPT", "CONDITIONAL_ATTEMPT",
                }:
                    actual_registers["r0"] = f"0x{source_attempt['tag']:08X}"
                if expected["kind"] == "OUTER_MATCH":
                    actual_registers["r2"] = expected["outer_record_address"]
                if expected["register_r6"] is not None:
                    actual_registers["r6"] = f"0x{expected['register_r6']:08X}"
                if expected["kind"] in {
                    "DIRECT_RESULT", "DIRECT_DISPATCH", "DIRECT_RETURN",
                    "CONDITIONAL_RETURN", "ROOT_EXECUTOR",
                    "TAG2_DISPATCH", "TAG4_DISPATCH",
                }:
                    actual_registers["r0"] = (
                        source_attempt["root_pc"] or "0x00000000"
                    )
                observations.append({
                    "kind": expected["kind"],
                    "ordinal": len(observations),
                    "instruction_ordinal": instruction_ordinal,
                    "instruction_pc": RUNNER._MAP_LIFECYCLE_OBSERVATION_PCS[
                        expected["kind"]
                    ],
                    "frame": instruction_ordinal,
                    "phase_marker": "INITIAL_LOAD",
                    "phase_boundary": False,
                    "attempt_ordinal": c_ordinal,
                    "tag": source_attempt["tag"],
                    "result": expected["result"], "map": destination,
                    "outer_record_address": expected["outer_record_address"],
                    "root_field_address": expected["root_field_address"],
                    "root_pc": expected["root_pc"],
                    "registers": actual_registers,
                })
                instruction_ordinal += 1

        def image(*, cleared: bool) -> dict[str, object]:
            return {
                "variables": [
                    {"id": identifier, "value": 0 if cleared else index + 1}
                    for index, identifier in enumerate(range(0x4000, 0x4010))
                ],
                "temporary_flags": [
                    {"id": identifier, "value": not cleared}
                    for identifier in range(0x20)
                ],
                "system_flags": [
                    {"id": identifier, "value": not cleared}
                    for identifier in RUNNER._MAP_LIFECYCLE_SYSTEM_FLAG_IDS
                ],
            }

        first_tag2 = 4
        actual_projection = {
            "schema_version": 1,
            "kind": "STAGE61_MAP_LIFECYCLE_ACTUAL_ORDERED_PROJECTION",
            "capacity": 256,
            "capacity_scope": "PRE_FIELD_INPUT_ON_FRAME_TAG2_ATTEMPTS",
            "producer_kind": "STOCK_WARP",
            "include_field_return": False,
            "phase_boundaries": deepcopy(
                expected_projection["phase_boundaries"]
            ),
            "ordered_attempts": [
                {**deepcopy(row), "map": destination}
                for row in projected_attempts
            ],
            "ordered_dispatches": [{
                **deepcopy(row),
                "outer_index": attempts[row["source_attempt_ordinal"]][
                    "outer_index"
                ],
                "map": destination,
            } for row in projected_dispatches],
            "attempt_count": len(projected_attempts),
            "dispatch_count": len(projected_dispatches),
            "tag2_attempt_count": 2,
            "overflow": False,
        }
        value = {
            "capacity": 256, "count": len(observations),
            "attempt_count": len(attempts) - 1, "overflow": False,
            "phase_controls": [{
                "phase_marker": "PRE_TRANSITION", "applied": True,
                "application_count": 1, "readback_exact": True,
                "application_instruction_ordinal": 0,
                "first_attempt_ordinal": 0,
            }, {
                "phase_marker": "PRE_FIELD_INPUT", "applied": True,
                "application_count": 1, "readback_exact": True,
                "application_instruction_ordinal":
                    first_attempt_instruction[first_tag2],
                "first_attempt_ordinal": first_tag2,
            }],
            "engine_clear": {
                "phase_marker": "DESTINATION_TEMP_CLEAR",
                "capture_count": 1,
                "capture_instruction_ordinal": first_attempt_instruction[0],
                "first_attempt_ordinal": 0, "first_attempt_tag": 3,
                "preimage": image(cleared=False),
                "postimage": image(cleared=True), "readback_exact": True,
            },
            "ordered_projection": actual_projection,
            "observations": observations,
        }
        with patch.object(
            RUNNER, "_map_lifecycle_source_attempts_against_rom",
            return_value=topology,
        ):
            normalized = RUNNER._validate_event_map_lifecycle_observations(
                value, fixture, rom_raw=b"unit", label="map-unit",
            )
            self.assertTrue(normalized["all_attempts_exact"])
            self.assertTrue(normalized["all_dispatches_exact"])
            mutations = {
                "overflow": lambda row: row.__setitem__("overflow", True),
                "ordinal-gap": lambda row: row["observations"][1].__setitem__(
                    "ordinal", 9,
                ),
                "instruction-reset": lambda row: row["observations"][2]
                    .__setitem__("instruction_ordinal", 1),
                "phase-missing": lambda row: row["observations"].pop(0),
                "phase-reapply": lambda row: row["phase_controls"][1]
                    .__setitem__("application_count", 2),
                "register-extra": lambda row: row["observations"][1][
                    "registers"
                ].__setitem__("r3", "0x00000000"),
                "system-clear": lambda row: row["engine_clear"]["postimage"][
                    "system_flags"
                ][0].__setitem__("value", True),
                "attempt-missing": lambda row: row["observations"].pop(),
                "ordered-root-forge": lambda row: row[
                    "ordered_projection"
                ]["ordered_attempts"][3].__setitem__(
                    "root_pc", "0x08101020",
                ),
                "ordered-order-forge": lambda row: row[
                    "ordered_projection"
                ]["ordered_attempts"].__setitem__(
                    slice(3, 5), list(reversed(row["ordered_projection"][
                        "ordered_attempts"
                    ][3:5])),
                ),
                "ordered-conditional-forge": lambda row: row[
                    "ordered_projection"
                ]["ordered_attempts"][3].__setitem__(
                    "selected_condition_index", 0,
                ),
                "ordered-overflow": lambda row: row[
                    "ordered_projection"
                ].__setitem__("overflow", True),
                "ordered-phase-forge": lambda row: row[
                    "ordered_projection"
                ]["ordered_attempts"][3].__setitem__(
                    "source_phase_marker", "INITIAL_RESUME",
                ),
                "ordered-cap-forge": lambda row: row[
                    "ordered_projection"
                ].__setitem__("tag2_attempt_count", 257),
            }
            for label, mutation in mutations.items():
                broken = deepcopy(value)
                mutation(broken)
                with self.subTest(label=label), self.assertRaises(
                    RUNNER.Stage61MgbaError
                ):
                    RUNNER._validate_event_map_lifecycle_observations(
                        broken, fixture, rom_raw=b"unit", label=label,
                    )
    def test_default_fixture_schema_is_strict_and_roundtrips(self) -> None:
        fixture = RUNNER.validate_fixture_document(
            deepcopy(RUNNER.DEFAULT_FIXTURE_DOCUMENT)
        )
        self.assertEqual(fixture["story"]["flute_flag"], 0x119E)
        self.assertEqual(fixture["story"]["snorlax_hidden_flag"], 0x149E)
        self.assertEqual(fixture["story"]["snorlax_species"], 491)
        self.assertEqual(fixture["popup"]["runtime_section"], 22)
        self.assertEqual(fixture["popup"]["expected_name"], "12ばん どうろ")
        self.assertEqual(fixture["fly"]["destination"]["start"], [6, 6])
        for row in fixture["interactions"].values():
            self.assertGreaterEqual(row["approach_steps"], 1)

    def test_fixture_rejects_direct_flag_only_or_ambiguous_state(self) -> None:
        no_walk = deepcopy(RUNNER.DEFAULT_FIXTURE_DOCUMENT)
        no_walk["interactions"]["snorlax"]["approach_steps"] = 0
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "実歩行"):
            RUNNER.validate_fixture_document(no_walk)

        wrong_port = deepcopy(RUNNER.DEFAULT_FIXTURE_DOCUMENT)
        wrong_port["interactions"]["giver"]["object"] = [21, 24]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "object隣接"):
            RUNNER.validate_fixture_document(wrong_port)

        same_flag = deepcopy(RUNNER.DEFAULT_FIXTURE_DOCUMENT)
        same_flag["story"]["snorlax_hidden_flag"] = same_flag["story"]["flute_flag"]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "同一"):
            RUNNER.validate_fixture_document(same_flag)

    def test_fixture_environment_preserves_exact_ids_and_key_sequence(self) -> None:
        fixture = RUNNER.validate_fixture_document(
            deepcopy(RUNNER.DEFAULT_FIXTURE_DOCUMENT)
        )
        environment = RUNNER.fixture_environment(fixture)
        self.assertEqual(environment["S61_GIVER_GROUP"], "1")
        self.assertEqual(environment["S61_GIVER_MAP"], "45")
        self.assertEqual(environment["S61_SNORLAX_LOCAL_ID"], "15")
        self.assertEqual(environment["S61_SNORLAX_ACTION_KEY"], "16")
        self.assertEqual(environment["S61_FLUTE_FLAG"], str(0x119E))
        self.assertEqual(environment["S61_SNORLAX_HIDDEN_FLAG"], str(0x149E))
        self.assertEqual(environment["S61_FLY_CONTEXT_DOWN"], "1")
        self.assertEqual(environment["S61_FLY_VISITED_FLAG"], str(0x18E4))
        self.assertEqual(environment["S61_FLY_DESTINATION_GROUP"], "96")
        self.assertEqual(environment["S61_FLY_DESTINATION_MAP"], "4")
        self.assertEqual(environment["S61_FLY_DESTINATION_X"], "6")
        self.assertEqual(environment["S61_FLY_DESTINATION_Y"], "6")
        self.assertEqual(
            environment["S61_FLY_MAP_SEQUENCE"].count("UP:2:60"), 3,
        )
        self.assertIn("A:2:600", environment["S61_FLY_MAP_SEQUENCE"])

    def test_fly_requires_landing_unlock_and_start_back_recovery(self) -> None:
        fixtures = RUNNER.validate_fixture_document(
            self._generated_fixture_source()
        )
        fly = fixtures["fly"]
        destination = fly["destination"]
        self.assertIsNotNone(destination)
        capture = deepcopy(
            self._calibration_document()["results"][0][
                "successful_paths"
            ][0]["capture"]
        )
        document = {
            "schema_version": 3,
            "status": "PASS",
            "case": "fly_normal_menu",
            "preparation_only_host_writes": True,
            "start_party_town_map_via_keys": True,
            "town_map_visible": True,
            "context_down_steps": fly["party_context_down"],
            "sequence_steps": len(fly["map_sequence"]),
            "origin": f"{fly['origin']['group']}/{fly['origin']['map']}",
            "destination": (
                f"{destination['group']}/{destination['map']}"
            ),
            "landing": destination["start"],
            "landing_overworld": True,
            "landing_script_released": True,
            "landing_controls_unlocked": True,
            "start_pressed": True,
            "start_menu_opened": True,
            "back_pressed": True,
            "field_input_recovered": True,
            "field_framebuffer_fnv1a64": "1" * 16,
            "town_map_framebuffer_fnv1a64": "2" * 16,
            "capture": capture,
            "warnings": 0,
            "framebuffer_artifacts": [],
        }
        normalized = RUNNER._validate_case(
            document, "fly_normal_menu", fixtures,
            RUNNER._read_charmap(), {}, {},
        )
        required = RUNNER._required_artifact_count(
            "fly_normal_menu", normalized,
        )
        normalized["artifacts"] = [self._artifact(
            "fly_normal_menu", f"fly-{index}-peak.ppm",
            sha256=hashlib.sha256(str(index).encode()).hexdigest(),
            rgb_fnv1a64=f"{index + 1:016X}",
        ) for index in range(required)]
        final = RUNNER.validate_final_mgba_case_result(
            "fly_normal_menu", normalized,
        )
        self.assertIs(final["field_input_recovered"], True)
        for key in (
            "landing_overworld", "landing_script_released",
            "landing_controls_unlocked", "start_pressed",
            "start_menu_opened", "back_pressed", "field_input_recovered",
        ):
            with self.subTest(key=key):
                broken = deepcopy(document)
                broken[key] = False
                with self.assertRaises(RUNNER.Stage61MgbaError):
                    RUNNER._validate_case(
                        broken, "fly_normal_menu", fixtures,
                        RUNNER._read_charmap(), {}, {},
                    )

    def test_local_incoming_absent_diagnostics_schema_tsv_and_gate(self) -> None:
        source = self._generated_fixture_source()
        fixture = RUNNER.validate_fixture_document(source)
        diagnostics = fixture[
            "local_static_incoming_absent_map_diagnostics"
        ]
        self.assertEqual(
            (
                diagnostics["map_count"], diagnostics["object_probe_count"],
                diagnostics["object_visibility_negative_probe_count"],
                diagnostics["bg_script_probe_count"],
                diagnostics["bg_non_script_visibility_proof_count"],
            ),
            (40, 99, 14, 7, 5),
        )
        with tempfile.TemporaryDirectory() as temporary:
            tsv = Path(temporary) / "diagnostics.tsv"
            RUNNER.write_local_static_incoming_absent_diagnostic_tsv(
                tsv, diagnostics,
            )
            lines = tsv.read_text(encoding="ascii").splitlines()
        self.assertEqual(len(lines), 1 + 99 + 7 + 5)
        self.assertEqual(lines[0] + "\n", RUNNER._DIAGNOSTIC_TSV_HEADER)
        self.assertTrue(all(len(line.split("\t")) == 15 for line in lines[1:]))
        self.assertEqual(
            [line.split("\t", 1)[0] for line in lines[1:]],
            sorted(line.split("\t", 1)[0] for line in lines[1:]),
        )

        expected = RUNNER._diagnostic_expected_rows(diagnostics)
        capture = deepcopy(
            self._calibration_document()["results"][0][
                "successful_paths"
            ][0]["capture"]
        )
        inventory = {
            "runtime_count": 3, "runtime_fnv1a64": "1" * 16,
            "template_count": 2, "template_fnv1a64": "2" * 16,
        }
        empty_inventory = {
            "runtime_count": 0, "runtime_fnv1a64": "0" * 16,
            "template_count": 0, "template_fnv1a64": "0" * 16,
        }
        results = []
        for probe_id, row in sorted(expected.items()):
            hidden = row["kind"] == "BG_HIDDEN"
            has_negative = row["has_negative"]
            results.append({
                "probe_id": probe_id, "kind": row["kind"],
                "map": row["map"], "stock_warp": True,
                "actual_walk_steps": 2,
                "map_walk_owner": row["map_walk_owner"],
                "direction_plus_a": not hidden,
                "direct_script_call": False,
                "template_matches_fixture": True,
                "positive_visible": True, "negative_visible": False,
                "hidden_clear_absent": True, "hidden_set_absent": True,
                "owner_seen": not hidden,
                "terminal_or_battle": not hidden,
                "input_recovered": True,
                "positive_framebuffer_fnv1a64": "3" * 16,
                "negative_framebuffer_fnv1a64": (
                    "4" * 16 if has_negative else "0" * 16
                ),
                "positive_inventory": deepcopy(inventory),
                "negative_inventory": (
                    deepcopy(inventory) if has_negative
                    else deepcopy(empty_inventory)
                ),
                "capture": None if hidden else deepcopy(capture),
            })
        document = {
            "schema_version": 1, "status": "PASS",
            "case": "local_static_incoming_absent_map_diagnostics",
            "baseline_natural_continue": True,
            "per_probe_stock_warp": True, "direct_script_calls": 0,
            "results": results, "fixture_count": 111, "map_count": 40,
            "object_probe_count": 99,
            "object_visibility_negative_probe_count": 14,
            "bg_script_probe_count": 7, "bg_hidden_probe_count": 5,
            "all_maps_real_walk": True, "failed": 0, "untested": 0,
            "warnings": 0,
        }
        validated = (
            RUNNER._validate_local_static_incoming_absent_map_diagnostics(
            document, fixture, RUNNER._read_charmap(),
            )
        )
        self.assertEqual(len(validated["coverage"]["observed_probe_ids"]), 111)
        for status in (None, "FAIL"):
            invalid_status = deepcopy(document)
            if status is None:
                invalid_status.pop("status")
            else:
                invalid_status["status"] = status
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "root契約",
            ):
                RUNNER._validate_local_static_incoming_absent_map_diagnostics(
                    invalid_status, fixture, RUNNER._read_charmap(),
                )
        duplicate = deepcopy(document)
        duplicate["results"][-1]["probe_id"] = duplicate["results"][0][
            "probe_id"
        ]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "probe ID",
        ):
            RUNNER._validate_local_static_incoming_absent_map_diagnostics(
                duplicate, fixture, RUNNER._read_charmap(),
            )
        broken = deepcopy(source)
        broken["local_static_incoming_absent_map_diagnostics"]["maps"][0][
            "object_probes"
        ][0]["script_prefix_sha256"] = "0" * 64
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "ROM binding"):
            # The hash remains syntactically valid; a ROM binding check is what
            # must reject it, so normalize first and compare against a zero ROM.
            normalized = RUNNER.validate_fixture_document(broken)
            RUNNER._validate_diagnostic_rom_bindings(
                bytes(32 * 1024 * 1024),
                normalized[
                    "local_static_incoming_absent_map_diagnostics"
                ],
            )

    def test_product_map_scripts_requires_independent_preimage_and_prepost(self) -> None:
        maps = []
        for case_id, map_number, start, cycle, action, object_position, \
                trainer_id, script, baseline_pointer, baseline_preimage in (
            (
                "product-map-script-001-085", 85, [2, 12],
                ["UP", "DOWN"], "LEFT", [1, 12], 453, 0x09371DE0,
                0x0816B046, "f66a690800000000000000002bd20207",
            ),
            (
                "product-map-script-001-086", 86, [18, 3],
                ["DOWN", "UP"], "RIGHT", [19, 3], 432, 0x09371A4C,
                0x0816B047, "6a690800000000000000002bd2020700",
            ),
        ):
            maps.append({
                "case_id": case_id, "group": 1, "map": map_number,
                "start": start, "walk_cycle": cycle, "action": action,
                "expected_map_scripts_contract": "EMPTY_PROJECT_TABLE",
                "map_scripts_pointer": "0x09F10000",
                "stage60_map_scripts_pointer": f"0x{baseline_pointer:08X}",
                "stage60_preimage_hex": baseline_preimage,
                "stage61_preimage_hex": "00" + "11" * 15,
                "trainer": {
                    "local_id": 1, "object": object_position,
                    "trainer_id": trainer_id,
                    "script_pointer": f"0x{script:08X}",
                    "prepost": ["PRE", "POST"],
                },
            })
        raw_text = bytes.fromhex("a2a3462e0045032bff")
        text_hash = hashlib.sha256(raw_text).hexdigest()

        def text_oracle(address: int, meaning: str) -> dict[str, object]:
            return {
                "meaning_source": meaning,
                "provenance": {
                    "kind": "STATIC_SCRIPT_TEXT",
                    "source_root": "unit-independent-csv",
                    "source_text_addresses": [f"0x{address:08X}"],
                    "raw_sha256s": [text_hash],
                },
                "ordered_printers": [{
                    "kind": "BRANCH_TEXT",
                    "instruction_address": "0x08002C44",
                    "caller_instruction_address": "0x08102000",
                    "source_pointer": f"0x{address:08X}",
                    "raw_hex": raw_text.hex().upper(),
                    "raw_sha256": text_hash,
                    "expanded_hex": raw_text.hex().upper(),
                    "expanded_sha256": text_hash,
                    "provenance": {"kind": "UNIT_STATIC"},
                }],
                "ordered_raw_sha256s": [text_hash],
                "allowed_ordered_raw_sha256_sequences": [[text_hash]],
                "visible_text_count": 1,
            }

        gym_rows = []
        for index in range(8):
            record_address = 0x08150000 + index * 0x20
            script_root = 0x08160000 + index * 0x100
            site = script_root + 0x20
            prebattle = 0x08170000 + index * 0x200
            defeat = prebattle + 0x100
            record = (
                (10 + index).to_bytes(2, "little")
                + (20 + index).to_bytes(2, "little")
                + b"\x00\x00\x00\x00"
                + script_root.to_bytes(4, "little")
            )
            before = bytearray(32)
            after = bytearray(32)
            before[0:2] = b"\x5c\x00"
            after[0:2] = b"\x5c\x03"
            before[8:12] = (0x0938A585).to_bytes(4, "little")
            after[8:12] = defeat.to_bytes(4, "little")
            gym_rows.append({
                "case_id": f"product-gym-bg-{index:02d}",
                "owner_id": f"BG:GYM:{index}",
                "group": 3, "map": 10 + index, "bg_index": index,
                "position": [10 + index, 20 + index],
                "record_address": f"0x{record_address:08X}",
                "stage60_record_hex": record.hex(),
                "stage61_record_hex": record.hex(),
                "script_root": f"0x{script_root:08X}",
                "trainerbattle_site": f"0x{site:08X}",
                "trainerbattle_type_offset": 1,
                "stage60_trainerbattle_prefix_hex": before.hex(),
                "stage61_trainerbattle_prefix_hex": after.hex(),
                "stage60_eos_text_pointer": "0x0938A585",
                "prebattle_text_pointer": f"0x{prebattle:08X}",
                "repaired_defeat_text_pointer": f"0x{defeat:08X}",
                "trainer_id": 300 + index,
                "entry": {
                    "start": [10 + index, 21 + index],
                    "walk_cycle": ["RIGHT", "LEFT"], "action": "UP",
                    "entry_seed": "EXACT_STOCK_WARP",
                },
                "required_state": {"flags": [], "vars": []},
                "pre_text_oracle": text_oracle(
                    prebattle, "independent prebattle CSV row",
                ),
                "post_text_oracle": text_oracle(
                    defeat, "independent defeat CSV row",
                ),
                "expected_stage60_semantic": (
                    "TYPE0_TRAINERBATTLE_EOS_ONLY_TEXT"
                ),
                "expected_stage61_pre_terminal": "BATTLE_START",
                "expected_stage61_post_terminal": "FIELD_INPUT_RECOVERED",
                "prepost": ["PRE", "POST"],
            })
        raw_fixture = {
            "schema_version": 1, "status": "PASS",
            "baseline_rom": {
                "path_hint": str(RUNNER.DEFAULT_STAGE60_ROM),
                "sha256": "1" * 64,
            },
            "maps": maps, "gym_bg_trainer_regressions": gym_rows,
            "null_script_owners": [{
                "case_id": "product-null-coord", "owner_kind": "COORD",
                "consumer_kind": "COORD_TRIGGER_ALWAYS", "group": 3, "map": 2,
                "index": 0, "position": [5, 5],
                "record_address": "0x08110000",
                "stage60_record_hex": "05000500010000000000000000000008",
                "stage61_record_hex": "05000500010000000000000000000000",
                "entry": {
                    "start": [5, 6], "walk_cycle": ["RIGHT", "LEFT"],
                    "action": "UP", "entry_seed": "EXACT_WARP",
                },
                "required_state": {
                    "flags": [], "vars": [],
                },
                "trigger_var": 0, "trigger_value": 0,
                "expected_stage60_failure": "INVALID_POINTER_0x08000000",
                "expected_stage61_terminal": "FIELD_INPUT_RECOVERED_NO_SCRIPT",
                "consumer_pointer_read_pc": "0x0806F100",
                "consumer_pointer_read_preimage_hex": "11" * 16,
                "consumer_thumb_mode": True,
            }, {
                "case_id": "product-null-bg", "owner_kind": "BG",
                "consumer_kind": "BG_SCRIPT_NORMAL", "group": 3, "map": 3,
                "index": 1, "position": [8, 8],
                "record_address": "0x08120000",
                "stage60_record_hex": "080008000000000000000008",
                "stage61_record_hex": "080008000000000000000000",
                "entry": {
                    "start": [8, 9], "walk_cycle": ["RIGHT", "LEFT"],
                    "action": "UP", "entry_seed": "EXACT_WARP",
                },
                "required_state": {"flags": [], "vars": []},
                "trigger_var": 0, "trigger_value": 0,
                "expected_stage60_failure": "INVALID_POINTER_0x08000000",
                "expected_stage61_terminal": "FIELD_INPUT_RECOVERED_NO_SCRIPT",
                "consumer_pointer_read_pc": "0x0806F200",
                "consumer_pointer_read_preimage_hex": "22" * 16,
                "consumer_thumb_mode": True,
            }],
            "assertions": {
                key: True for key in RUNNER._PRODUCT_MAP_SCRIPT_ASSERTIONS
            },
        }
        fixture = RUNNER._normalize_final_map_script_regressions(raw_fixture)
        with tempfile.TemporaryDirectory() as temporary:
            tsv = Path(temporary) / "product.tsv"
            null_tsv = Path(temporary) / "product-null.tsv"
            gym_tsv = Path(temporary) / "product-gym.tsv"
            RUNNER.write_product_map_script_tsv(tsv, fixture)
            RUNNER.write_product_null_script_tsv(null_tsv, fixture)
            RUNNER.write_product_gym_bg_tsv(gym_tsv, fixture)
            lines = tsv.read_text(encoding="ascii").splitlines()
            null_lines = null_tsv.read_text(encoding="ascii").splitlines()
            gym_lines = gym_tsv.read_text(encoding="ascii").splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(len(line.split("\t")) == 14 for line in lines[1:]))
        self.assertEqual(len(null_lines), 3)
        self.assertTrue(
            all(len(line.split("\t")) == 18 for line in null_lines[1:])
        )
        self.assertEqual(len(gym_lines), 9)
        self.assertTrue(
            all(len(line.split("\t")) == 17 for line in gym_lines[1:])
        )

        baseline_rows = []
        for row in fixture["maps"]:
            baseline_rows.append({
                "case_id": row["case_id"],
                "map": f"1/{row['map']}",
                "expected_invalid_tag": bytes.fromhex(
                    row["stage60_preimage_hex"]
                )[0],
                "live_map_scripts_pointer": "0x0816B046",
                "live_map_scripts_tag": bytes.fromhex(
                    row["stage60_preimage_hex"]
                )[0],
                "map_loaded": False, "stock_warp_settled": False,
                "actual_walk_steps": 0,
                "direction_plus_a_attempted": False,
                "interaction_terminal": False,
                "warning_or_error_count": 1, "unknown_pc": True,
                "first_problem_pc": "0x08000000",
                "callback": "0x08000000", "controls_locked": True,
            })
        baseline_document = {
            "schema_version": 1, "status": "PASS",
            "case": "product_map_scripts_stage60_baseline",
            "negative_evidence_only": True, "results": baseline_rows,
            "fixture_count": 2, "failed": 0, "untested": 0,
            "warnings": 0,
        }
        validated_baseline = RUNNER._validate_product_map_scripts_stage60(
            baseline_document, fixture,
        )
        self.assertIs(validated_baseline["all_live_invalid_tags_exact"], True)
        self.assertIs(
            validated_baseline["all_negative_failure_symptoms_observed"],
            True,
        )
        wrong_live_tag = deepcopy(baseline_document)
        wrong_live_tag["results"][0]["live_map_scripts_tag"] ^= 0xFF
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "live tag"):
            RUNNER._validate_product_map_scripts_stage60(
                wrong_live_tag, fixture,
            )
        asymptomatic = deepcopy(baseline_document)
        asymptomatic_row = asymptomatic["results"][0]
        asymptomatic_row.update({
            "map_loaded": True,
            "stock_warp_settled": True,
            "actual_walk_steps": len(fixture["maps"][0]["walk_cycle"]),
            "direction_plus_a_attempted": True,
            "interaction_terminal": True,
            "warning_or_error_count": 0,
            "unknown_pc": False,
            "controls_locked": False,
        })
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "failure症状"):
            RUNNER._validate_product_map_scripts_stage60(
                asymptomatic, fixture,
            )

        capture = deepcopy(
            self._calibration_document()["results"][0][
                "successful_paths"
            ][0]["capture"]
        )
        field_roundtrip = {
            "controls_released": True,
            "running_state_released": True,
            "tile_transition_released": True,
            "start_pressed": True,
            "start_menu_opened": True,
            "menu_callback_observed": "0x0806EA75",
            "back_pressed": True,
            "field_callback_before": "0x08055E75",
            "field_callback_after": "0x08055E75",
            "callback_ordered": True,
            "map_preserved": True,
            "field_input_recovered": True,
        }
        post_battle_rom = b"\x6B\x02"

        def standard_post_battle_continuation() -> dict[str, object]:
            continuation_capture = deepcopy(capture)
            continuation_capture["messages"] = []
            continuation_capture["printer_calls"] = []
            return {
                "phase": "POST_BATTLE_CONTINUATION",
                "resume_kind": "STANDARD",
                "boundary_observed": True,
                "expected_resume_pc": None,
                "observed_resume_pc": "0x08000000",
                "resume_pc_hit_count": 1,
                "input_tokens": [],
                "input_step_count": 0,
                "input_steps_consumed": 0,
                "premature_terminal": False,
                "terminal": "FIELD_RELEASE",
                "field_released": True,
                "capture": continuation_capture,
                "decision_watch": {
                    "special_result_address": "0x02037004",
                    "initial_value": 0,
                    "values": [],
                    "change_count": 0,
                },
                "effect_watch": {
                    "enabled": False,
                    "hook_hits_before": 0,
                    "hook_hits_after": 0,
                    "hook_hit_delta": 0,
                },
                "chained_battles": [],
            }

        repaired_rows = []
        for row in fixture["maps"]:
            def branch(defeated: bool) -> dict[str, object]:
                lifecycle = {
                    "battle_started": not defeated,
                    "trainer_battle": not defeated,
                    "completed_via_keys": not defeated,
                    "forced_switch_count": 0,
                    "forced_switch_cursor_observed": False,
                    "forced_switch_usable_slot_selected": False,
                    "forced_switch_cursor_initial": [],
                    "forced_switch_selected_slots": [],
                    "forced_switch_selected_hps": [],
                    "route": "NONE" if defeated else "FIGHT",
                    "outcome": 0 if defeated else 1,
                    "won_or_escaped_not_loss": not defeated,
                    "field_released_after_battle": not defeated,
                    "start_pressed": not defeated,
                    "start_menu_opened": not defeated,
                    "back_pressed": not defeated,
                    "map_preserved": not defeated,
                    "field_input_recovered": not defeated,
                }
                return {
                    "branch": "POST" if defeated else "PRE",
                    "trainer_defeated": defeated,
                    "actual_walk_steps": len(row["walk_cycle"]),
                    "direction_plus_a": True, "owner_seen": True,
                    "battle_started": not defeated,
                    "field_released": defeated, "map_preserved": True,
                    "input_recovered": True,
                    "post_battle": lifecycle,
                    "post_battle_continuation": (
                        None if defeated
                        else standard_post_battle_continuation()
                    ),
                    "field_roundtrip": (
                        deepcopy(field_roundtrip) if defeated else None
                    ),
                    "invalid_control_flow": False,
                    "capture": deepcopy(capture),
                }
            repaired_rows.append({
                "case_id": row["case_id"], "map": f"1/{row['map']}",
                "expected_contract": "EMPTY_PROJECT_TABLE",
                "map_scripts_pointer": "0x09F10000",
                "map_scripts_tag": 0, "stock_warp_settled": True,
                "pre": branch(False), "post": branch(True),
            })
        repaired_document = {
            "schema_version": 2, "status": "PASS",
            "case": "product_map_scripts_stage61",
            "results": repaired_rows, "fixture_count": 2,
            "failed": 0, "untested": 0,
            "invalid_control_flow_failures": 0, "warnings": 0,
        }
        validated = RUNNER._validate_product_map_scripts_stage61(
            repaired_document, fixture, RUNNER._read_charmap(),
            post_battle_rom,
        )
        self.assertEqual(len(validated["results"]), 2)

        gym_capture = deepcopy(capture)
        gym_capture["printer_calls"] = [{
            "frame": 101,
            "instruction_address": RUNNER._TEXT_PRINTER_ENTRY,
            "caller_instruction_address": "0x08102000",
            "window": 0, "font": 2,
            "text_pointer": "0x02021C88", "speed": 1,
            "size": len(raw_text), "raw_hex": raw_text.hex().upper(),
            "raw_fnv1a64": RUNNER._fnv1a64(raw_text),
        }]
        gym_results = []
        for row in fixture["gym_bg_trainer_regressions"]:
            def gym_phase(defeated: bool) -> dict[str, object]:
                lifecycle = {
                    "battle_started": not defeated,
                    "trainer_battle": not defeated,
                    "completed_via_keys": not defeated,
                    "forced_switch_count": 0,
                    "forced_switch_cursor_observed": False,
                    "forced_switch_usable_slot_selected": False,
                    "forced_switch_cursor_initial": [],
                    "forced_switch_selected_slots": [],
                    "forced_switch_selected_hps": [],
                    "route": "NONE" if defeated else "FIGHT",
                    "outcome": 0 if defeated else 1,
                    "won_or_escaped_not_loss": not defeated,
                    "field_released_after_battle": not defeated,
                    "start_pressed": not defeated,
                    "start_menu_opened": not defeated,
                    "back_pressed": not defeated,
                    "map_preserved": not defeated,
                    "field_input_recovered": not defeated,
                }
                return {
                    "branch": "POST" if defeated else "PRE",
                    "trainer_defeated": defeated,
                    "actual_walk_steps": len(row["entry"]["walk_cycle"]),
                    "direction_plus_a": True, "owner_seen": True,
                    "trainerbattle_site_hit_count": 2,
                    "first_script_pointer": (
                        f"0x{row['trainerbattle_site']:08X}"
                    ),
                    "record_pointer": f"0x{row['script_root']:08X}",
                    "battle_started": not defeated,
                    "field_released": defeated, "map_preserved": True,
                    "input_recovered": True,
                    "post_battle": lifecycle,
                    "post_battle_continuation": (
                        None if defeated
                        else standard_post_battle_continuation()
                    ),
                    "field_roundtrip": (
                        deepcopy(field_roundtrip) if defeated else None
                    ),
                    "invalid_control_flow": False,
                    "capture": deepcopy(gym_capture),
                }
            gym_results.append({
                "case_id": row["case_id"], "owner_id": row["owner_id"],
                "map": f"{row['group']}/{row['map']}",
                "bg_index": row["bg_index"],
                "record_address": f"0x{row['record_address']:08X}",
                "script_root": f"0x{row['script_root']:08X}",
                "trainerbattle_site": f"0x{row['trainerbattle_site']:08X}",
                "trainer_id": row["trainer_id"],
                "stock_warp_settled": True,
                "pre": gym_phase(False), "post": gym_phase(True),
            })
        gym_document = {
            "schema_version": 2, "status": "PASS",
            "case": "product_gym_bg_stage61", "results": gym_results,
            "fixture_count": 8, "branch_count": 16, "failed": 0,
            "untested": 0, "invalid_control_flow_failures": 0,
            "warnings": 0,
        }
        gym_validated = RUNNER._validate_product_gym_bg_stage61(
            gym_document, fixture, RUNNER._read_charmap(), post_battle_rom,
        )
        self.assertEqual(len(gym_validated["results"]), 8)
        fake_recovery = deepcopy(gym_document)
        fake_recovery["results"][0]["pre"]["post_battle"][
            "field_input_recovered"
        ] = False
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "START/B復帰",
        ):
            RUNNER._validate_product_gym_bg_stage61(
                fake_recovery, fixture, RUNNER._read_charmap(),
                post_battle_rom,
            )
        unobserved_teleport = deepcopy(
            gym_document["results"][0]["pre"]["post_battle"]
        )
        unobserved_teleport.update({
            "trainer_battle": False, "route": "RUN", "outcome": 5,
        })
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "START/B復帰",
        ):
            RUNNER._validate_battle_lifecycle(
                unobserved_teleport, battle_started=True,
                label="unit-unobserved-teleport",
            )

        null_baseline_rows = []
        null_repaired_rows = []
        for row in fixture["null_script_owners"]:
            common = {
                "case_id": row["case_id"],
                "owner_kind": row["owner_kind"],
                "consumer_kind": row["consumer_kind"],
                "map": f"{row['group']}/{row['map']}",
                "record_address": f"0x{row['record_address']:08X}",
                "consumer_pointer_read_pc": (
                    f"0x{row['consumer_pointer_read_pc']:08X}"
                ),
                "consumer_hit_count": 1,
                "first_before_pc": "0x0806F104",
                "first_after_pc": "0x0806F106",
                "actual_walk_steps": len(row["entry"]["walk_cycle"]),
                "trigger_var": row["trigger_var"],
                "trigger_value": row["trigger_value"],
                "trigger_via_actual_input": True,
            }
            null_baseline_rows.append({
                **deepcopy(common), "pointer_value": "0x08000000",
                "pointer_execution_seen": True,
                "warning_or_error_count": 1,
                "field_input_recovered": False,
                "failure_observed": True,
            })
            null_repaired_rows.append({
                **deepcopy(common), "pointer_value": "0x00000000",
                "map_preserved": True, "field_input_recovered": True,
                "field_roundtrip": deepcopy(field_roundtrip),
                "softlock": False, "invalid_control_flow": False,
            })
        null_baseline = {
            "schema_version": 1, "status": "PASS",
            "case": "product_null_scripts_stage60_baseline",
            "negative_evidence_only": True, "results": null_baseline_rows,
            "fixture_count": 2, "failed": 0, "untested": 0,
            "warnings": 0,
        }
        null_repaired = {
            "schema_version": 2, "status": "PASS",
            "case": "product_null_scripts_stage61",
            "results": null_repaired_rows, "fixture_count": 2,
            "failed": 0, "untested": 0,
            "invalid_control_flow_failures": 0, "softlocks": 0,
            "warnings": 0,
        }
        RUNNER._validate_product_null_scripts(
            null_baseline, fixture, repaired=False,
        )
        RUNNER._validate_product_null_scripts(
            null_repaired, fixture, repaired=True,
        )
        no_hit = deepcopy(null_repaired)
        no_hit["results"][0]["consumer_hit_count"] = 0
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "consumer hit"):
            RUNNER._validate_product_null_scripts(
                no_hit, fixture, repaired=True,
            )
        broken = deepcopy(raw_fixture)
        broken["maps"][1]["stage61_preimage_hex"] = "6a" + "00" * 15
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "empty"):
            RUNNER._normalize_final_map_script_regressions(broken)
    def test_charmap_decodes_raw_message_and_rejects_missing_eos(self) -> None:
        charmap = RUNNER._read_charmap()
        # FireRed Rev.0 MAPSEC_ROUTE_12 exact bytes.
        raw = bytes.fromhex("a2a3462e0045032bff")
        self.assertEqual(RUNNER.decode_text(raw, charmap), "12ばん どうろ")
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "terminator"):
            RUNNER.decode_text(raw[:-1], charmap)

    def test_printer_oracle_ui_coordinates_are_exact_u8_pairs(self) -> None:
        raw = bytes.fromhex("1A02FE020204FF")
        digest = hashlib.sha256(raw).hexdigest()

        def printer(kind: str, coordinates: object) -> dict[str, object]:
            return {
                "kind": kind,
                "instruction_address": RUNNER._TEXT_PRINTER_ENTRY,
                "caller_instruction_address": "0x08003000",
                "source_pointer": "0x083DD86A",
                "raw_hex": raw.hex().upper(),
                "raw_sha256": digest,
                "expanded_hex": raw.hex().upper(),
                "expanded_sha256": digest,
                "provenance": {"kind": "PINNED_CLEAN_ENGINE_UI_CHROME"},
                "ui_coordinates": coordinates,
            }

        for kind, coordinates in (
            ("UI_CHROME_YES_NO", [20, 8]),
            ("UI_CHROME_MULTICHOICE", [0, 255]),
        ):
            with self.subTest(kind=kind):
                normalized = RUNNER._normalize_printer_oracle(
                    printer(kind, coordinates), f"printer.{kind}",
                )
                self.assertEqual(normalized["ui_coordinates"], coordinates)

        invalid = {
            "mapping": {"left": 20, "top": 8},
            "extra": [20, 8, 0],
            "element-type": [20, "8"],
            "bool-is-not-uint": [20, True],
            "outside-u8": [20, 256],
        }
        for label, coordinates in invalid.items():
            with self.subTest(label=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "ui_coordinates",
            ):
                RUNNER._normalize_printer_oracle(
                    printer("UI_CHROME_YES_NO", coordinates),
                    f"printer.invalid.{label}",
                )

    def test_every_add_text_printer_call_requires_a_visible_glyph(self) -> None:
        capture = deepcopy(
            self._calibration_document()["results"][0]
            ["successful_paths"][0]["capture"]
        )
        capture["printer_calls"].append({
            "frame": 101,
            "instruction_address": RUNNER._TEXT_PRINTER_ENTRY,
            "caller_instruction_address": "0x08102000",
            "window": 0, "font": 2,
            "text_pointer": "0x08AAAAAA", "speed": 1,
            "size": 1, "raw_hex": "FF",
            "raw_fnv1a64": RUNNER._fnv1a64(b"\xFF"),
        })
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "visible glyph 0"):
            RUNNER._validate_catalog_capture(
                capture, case_id="empty-text-regression",
                charmap=RUNNER._read_charmap(),
            )

    def test_c_source_uses_input_path_and_rendered_text_observation(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("S61_G_STRING_VAR4 = 0x02021C88U", source)
        self.assertIn("S61_FIELD_MESSAGE_STATE = 0x02036FD0U", source)
        self.assertIn("BOOTSTRAP_KANTO_WARP", source)
        self.assertIn("BOOTSTRAP_TRY_SAVE", source)
        self.assertIn("world_continue(core, fixture)", source)
        self.assertIn("world_walk_to_new_tile", source)
        self.assertIn("S61_CHOICE_NO", source)
        self.assertIn("S61_CHOICE_YES", source)
        self.assertIn("producer_via_normal_dialogue", source)
        self.assertIn("supplementary_direct_state_setup", source)
        self.assertIn("s61_enter_party_menu", source)
        self.assertIn("S61_CATALOG_TSV", source)
        self.assertIn("core->saveState", source)
        self.assertIn("core->loadState", source)
        self.assertIn("WORLD_FLAG_CLEAR", source)
        self.assertIn("WORLD_VAR_SET", source)
        self.assertIn("WORLD_REMOVE_BAG_ITEM", source)
        self.assertIn("WORLD_SET_TRAINER_FLAG", source)
        self.assertIn("catalog hidden row contract differs", source)
        self.assertIn("input_sequence_probe_via_state_restore", source)
        self.assertIn("s61_capture_printer_call", source)
        self.assertIn("S61_ADD_TEXT_PRINTER = 0x08002C44U", source)
        self.assertIn("s61_throw_master_ball_with_keys", source)
        self.assertIn("WORLD_BATTLE_COMMAND_CHOOSE_ACTION", source)
        self.assertIn("battle_action_cursor_host_write\\\":false", source)
        self.assertIn("s61_case_link_full_save_persistence", source)
        self.assertIn("delayed generation is not exactly chunks 0..12", source)
        self.assertIn("atomic commit changed more than signature", source)
        self.assertIn(r'\"untested\":0', source)
        self.assertIn("catalog_calibrate", source)
        self.assertIn("s61_prepare_calibration_attempt", source)
        self.assertIn("s61_call_synced(core, BOOTSTRAP_KANTO_WARP", source)
        self.assertIn("BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1", source)
        self.assertIn("mode == 0x1FU", source)
        self.assertIn("s61_case_save_corruption_probe", source)
        self.assertIn("tear_after_selection_before_copy", source)
        self.assertIn("safe_ui_framebuffer_start_fnv1a64", source)
        self.assertIn("s61_case_partial_link_save_persistence", source)
        self.assertIn("s61_case_species_picture_bounds", source)
        self.assertIn("s61_call_species_pic_watched", source)
        self.assertIn("field_party_boundary_1620", source)
        self.assertIn("caught_snorlax_party_summary", source)
        # Fly destination resolver itself must not be host-called by the E2E.
        self.assertNotIn("0x080C6460", source)

    def test_legacy_and_strict_catalog_defaults_are_separate(self) -> None:
        self.assertEqual(
            RUNNER.DEFAULT_CATALOG,
            Path("reports/generated/stage61_npc_interaction_catalog.json"),
        )
        self.assertEqual(
            RUNNER.DEFAULT_LEGACY_CATALOG,
            Path(
                "reports/generated/"
                "stage61_npc_interaction_catalog_legacy.json"
            ),
        )
        self.assertEqual(
            RUNNER.DEFAULT_STATE_MATRIX,
            Path("reports/generated/stage61_npc_state_matrix.json"),
        )
        self.assertIn("last_ball_persistence", RUNNER.ALL_CASES)
        self.assertIn("link_full_save_persistence", RUNNER.ALL_CASES)
        self.assertIn("species_picture_bounds", RUNNER.ALL_CASES)
        self.assertEqual(
            RUNNER.CASE_DOMAINS["regressions"],
            (
                "species_picture_bounds", "product_map_script_regressions",
                "pc_capacity_contract", "giveegg_result_contract",
                "gift_storage_transaction_sweep",
                "bill_sevii_scope_guard", "engine_special_flag_lifecycle",
                "stale_checkflag_var_result_matrix",
                "connection_transition_lifecycle",
                "stateful_menu_loop_batch",
            ),
        )

    def test_connection_transition_requires_real_boundary_root_and_resume(
        self,
    ) -> None:
        def capture() -> dict[str, object]:
            return {
                "message_state_address": "0x02036FD0",
                "string_address": "0x02021C88",
                "printer_entry": RUNNER._TEXT_PRINTER_ENTRY,
                "printer_entry_preimage_hex": (
                    RUNNER._TEXT_PRINTER_PREIMAGE_HEX
                ),
                "template_printer_entry": (
                    RUNNER._TEMPLATE_TEXT_PRINTER_ENTRY
                ),
                "template_printer_entry_preimage_hex": (
                    RUNNER._TEMPLATE_TEXT_PRINTER_PREIMAGE_HEX
                ),
                "execution": {
                    "invalid_control_flow": False,
                    "first_invalid_pc": None, "cpsr": None, "lr": None,
                },
                "active_frames": 0,
                "state_counts": [1, 0, 0, 0],
                "var_result": {
                    "address": "0x02037004", "seen": True,
                    "first": 0, "last": 0, "changes": 0, "values": [0],
                },
                "framebuffer": {
                    "first_fnv1a64": "0" * 16,
                    "last_fnv1a64": "1" * 16,
                    "changed_frames": 1,
                    "maximum_baseline_pixel_difference": 1,
                },
                "messages": [], "printer_calls": [],
            }

        rows = []
        for index, variant in enumerate(("DIRECT", "RESUME")):
            resume = index == 1
            rows.append({
                "variant": variant,
                "case_id": f"connection-west-{variant.lower()}",
                "save_generated": True, "fresh_title_continue": True,
                "stock_warp_source_setup": True,
                "source_map": [3, 19], "source_predecessor": [0, 15],
                "source_predecessor_exact": True,
                "actual_boundary_walk_steps": 1,
                "boundary_key_held_frames": 9, "boundary_key": "LEFT",
                "direct_destination_teleport": False,
                "destination_map": [3, 0], "arrival": [34, 15],
                "arrival_transform_exact": True,
                "transition_root": "0x087F1600",
                "root_absent_before_boundary_step": True,
                "first_root_hit_count": 1,
                "root_dispatch_pc": "0x0806948E",
                "root_executor_pc": "0x08069408",
                "root_dispatch_hits": 2, "root_executor_hits": 2,
                "root_dispatch_operand": "0x087F1600",
                "root_executor_operand": "0x087F1600",
                "root_last_dispatch_operand": "0x08866B10",
                "root_last_executor_operand": "0x08866B10",
                "root_dispatch_ordinal": 10, "root_executor_ordinal": 11,
                "root_last_dispatch_ordinal": 20,
                "root_last_executor_ordinal": 21,
                "root_last_position": [35, 15],
                "root_call_sequence_exact": True,
                "first_root_group": 3, "first_root_map": 0,
                "first_root_position": [35, 15],
                "first_root_context": (
                    "MAP_HEADER_RUN_SCRIPT_TYPE_R0_TO_SCRIPT_EXECUTOR"
                ),
                "first_root_identity_exact": True,
                "field_released_after_transition": True,
                "start_pressed": resume, "start_menu_opened": resume,
                "menu_callback_observed": (
                    "0x0806EA75" if resume else "0x00000000"
                ),
                "back_pressed": resume,
                "callback_install_pc": "0x0806EA18",
                "callback_dispatch_pc": "0x0806EA30",
                "field_return_callback_pc": "0x0806EA74",
                "callback_install_hits": 1 if resume else 0,
                "callback_dispatch_hits": 1 if resume else 0,
                "field_return_callback_hits": 1 if resume else 0,
                "callback_install_ordinal": 30 if resume else 0,
                "callback_dispatch_ordinal": 40 if resume else 0,
                "field_return_callback_ordinal": 41 if resume else 0,
                "callback_ordered": resume,
                "field_callback_before": "0x08055E75",
                "field_callback_after": "0x08055E75",
                "field_input_recovered": True,
                "invalid_control_flow": False, "capture": capture(),
            })
        document = {
            "schema_version": 1, "status": "PASS",
            "case": "connection_transition_lifecycle",
            "fixture_kind": "STOCK_CONNECTION_WEST_BOUNDARY",
            "connection_row_address": "0x08316A8C",
            "connection_row_hex": "030000000000000003000000",
            "connection_row_sha256": (
                "40272649e0393212abbc8ff2488eaf24e664d0b272a8f83539aedbd567e4bdbe"
            ),
            "source_header": "0x083148DC",
            "destination_header": "0x083146C8",
            "source_layout": "0x086F21E8",
            "destination_layout": "0x086F044C",
            "destination_map_script_table": "0x08866AF0",
            "transition_root": "0x087F1600",
            "source_dimensions": [60, 24],
            "destination_dimensions": [35, 30],
            "direction": 3, "offset": 0,
            "arrival_transform": (
                "WEST:DEST_X=DEST_WIDTH-1,DEST_Y=SOURCE_Y-OFFSET"
            ),
            "stock_warp_setup_only": True,
            "direct_destination_teleport": False,
            "results": rows, "variant_count": 2,
            "direct_boundary_transition_exact": True,
            "resume_start_back_callback_ordered": True,
            "all_current_owner_pointers_reresolved": True,
            "failed": 0, "untested": 0, "warnings": 0,
        }
        result = RUNNER._validate_connection_transition_lifecycle(
            document, RUNNER._read_charmap(),
        )
        self.assertTrue(result["real_boundary_walk_both_variants"])

        wrong_root = deepcopy(document)
        wrong_root["results"][0]["root_dispatch_operand"] = "0x08866B10"
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "exact transition",
        ):
            RUNNER._validate_connection_transition_lifecycle(
                wrong_root, RUNNER._read_charmap(),
            )

        unordered_resume = deepcopy(document)
        unordered_resume["results"][1]["field_return_callback_ordinal"] = 39
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "callback順",
        ):
            RUNNER._validate_connection_transition_lifecycle(
                unordered_resume, RUNNER._read_charmap(),
            )

    def test_stale_checkflag_matrix_requires_flag_only_real_input_branches(
        self,
    ) -> None:
        initial_values = [0, 1, 0xFFFF, 0x7A61]

        def capture(initial: int) -> dict[str, object]:
            return {
                "message_state_address": "0x02036FD0",
                "string_address": "0x02021C88",
                "printer_entry": RUNNER._TEXT_PRINTER_ENTRY,
                "printer_entry_preimage_hex": (
                    RUNNER._TEXT_PRINTER_PREIMAGE_HEX
                ),
                "template_printer_entry": (
                    RUNNER._TEMPLATE_TEXT_PRINTER_ENTRY
                ),
                "template_printer_entry_preimage_hex": (
                    RUNNER._TEMPLATE_TEXT_PRINTER_PREIMAGE_HEX
                ),
                "execution": {
                    "invalid_control_flow": False,
                    "first_invalid_pc": None, "cpsr": None, "lr": None,
                },
                "active_frames": 0,
                "state_counts": [1, 0, 0, 0],
                "var_result": {
                    "address": "0x02037004", "seen": True,
                    "first": initial, "last": initial,
                    "changes": 0, "values": [initial],
                },
                "framebuffer": {
                    "first_fnv1a64": "0" * 16,
                    "last_fnv1a64": "1" * 16,
                    "changed_frames": 1,
                    "maximum_baseline_pixel_difference": 1,
                },
                "messages": [], "printer_calls": [],
            }

        rows = []
        for flag in (False, True):
            expected_target = "0x092D0A28" if flag else "0x092D0A80"
            alternate_target = "0x092D0A80" if flag else "0x092D0A28"
            token = (
                "FLAG_SET_TRUE_TARGET_ITEMS_347_348_PRESENT" if flag
                else "FLAG_CLEAR_FALSE_TARGET_ITEMS_347_348_ABSENT"
            )
            for initial in initial_values:
                rows.append({
                    "case_id": (
                        f"stale-flag-{'set' if flag else 'clear'}-"
                        f"var-{initial:04X}"
                    ),
                    "flag_0820": flag,
                    "initial_var_result": initial,
                    "initial_var_result_readback": initial,
                    "save_generated": True, "stock_warp": True,
                    "fresh_title_continue": True,
                    "actual_walk_steps": 2,
                    "walk_sequence": ["UP", "DOWN"],
                    "direction_plus_a": True,
                    "direct_script_call": False,
                    "saveblock1_pointer_before_interaction": "0x020254EC",
                    "saveblock1_pointer_after_interaction": "0x020254C8",
                    "saveblock2_pointer_before_interaction": "0x02024548",
                    "saveblock2_pointer_after_interaction": "0x02024524",
                    "storage_pointer_before_interaction": "0x020292AC",
                    "storage_pointer_after_interaction": "0x02029288",
                    "owner_pointer_relocation_delta": -36,
                    "owner_pointer_relocation_observed": True,
                    "current_owner_pointers_reresolved": True,
                    "stale_preinteraction_pointer_rejected": True,
                    "root_absent_before_direction_a": True,
                    "object_visible": True,
                    "loaded_template_exact": True,
                    "expected_branch_target": expected_target,
                    "alternate_branch_target": alternate_target,
                    "root_hit_count": 1, "branch_hit_count": 1,
                    "alternate_branch_hit_count": 1 if flag else 0,
                    "true_target_hit_count": 1 if flag else 0,
                    "false_target_hit_count": 1,
                    "true_target_first_ordinal": 100 if flag else 0,
                    "false_target_first_ordinal": 200 if flag else 100,
                    "branch_target_trace_exact": True,
                    "true_arm_falls_through_false_entry": flag,
                    "branch_token": token,
                    "item_347_present_before": False,
                    "item_347_present_after": flag,
                    "item_348_present_before": False,
                    "item_348_present_after": flag,
                    "final_var_result": initial,
                    "visible_text_count": 0,
                    "controls_released": True,
                    "running_state_released": True,
                    "tile_transition_released": True,
                    "start_pressed": True,
                    "start_menu_opened": True,
                    "menu_callback_observed": "0x0806EA75",
                    "back_pressed": True,
                    "field_callback_before": "0x08055E75",
                    "field_callback_after": "0x08055E75",
                    "callback_ordered": True,
                    "field_input_recovered": True,
                    "map_preserved": True,
                    "invalid_control_flow": False,
                    "capture": capture(initial),
                })
        document = {
            "schema_version": 4, "status": "PASS",
            "case": "stale_checkflag_var_result_matrix",
            "owner_id": "OBJECT:033/001:000", "map": "33/1",
            "local_id": 1, "object": [7, 5], "stance": [7, 4],
            "owner_record": "0x08382618",
            "owner_record_sha256": (
                "e3bae8da4cabb92ce597e9b563f7425a4155d417b272a2f0e"
                "915e6038670fc31"
            ),
            "script_root": "0x092D0A10",
            "compare_site": "0x092D0A15",
            "compare_replacement_hex": "0000000000",
            "root_prefix_hex": (
                "6A5A2B200800000000000601280A2D0905800A2D09000000"
            ),
            "true_target_size": 88,
            "true_target_sha256": (
                "cf85d7e8bf2bb885e27f4dc60f722df721ec09ec19cb89cc"
                "7261146102f86a43"
            ),
            "false_target_size": 21,
            "false_target_sha256": (
                "231647f4bac5700c4fb98d4e10f73de9e875598c6b89dd2d"
                "a1723cb91f31db78"
            ),
            "branch_control": "FLAG_0820_ONLY",
            "initial_var_results": initial_values,
            "per_case_save_stock_warp_fresh_continue": True,
            "flag_persisted_in_two_generation_save": True,
            "results": rows, "fixture_count": 8,
            "flag_state_count": 2, "initial_var_result_count": 4,
            "branch_depends_only_on_flag": True,
            "all_field_controls_running_tile_released": True,
            "all_start_menu_roundtrip": True,
            "all_current_owner_pointers_reresolved": True,
            "all_stale_preinteraction_pointers_rejected": True,
            "failed": 0, "untested": 0, "warnings": 0,
        }
        result = RUNNER._validate_stale_checkflag_var_result_matrix(
            document, RUNNER._read_charmap(),
        )
        self.assertTrue(
            result["branch_invariance"]["initial_var_result_independent"]
        )
        self.assertEqual(
            result["branch_invariance"]["direct_script_call_count"], 0,
        )

        stale_owner_pointer = deepcopy(document)
        stale_owner_pointer["results"][0][
            "saveblock1_pointer_after_interaction"
        ] = "0x020254EC"
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "owner relocation",
        ):
            RUNNER._validate_stale_checkflag_var_result_matrix(
                stale_owner_pointer, RUNNER._read_charmap(),
            )

        stale_sensitive = deepcopy(document)
        stale_sensitive["results"][3]["expected_branch_target"] = \
            "0x092D0A28"
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "実入力branch契約",
        ):
            RUNNER._validate_stale_checkflag_var_result_matrix(
                stale_sensitive, RUNNER._read_charmap(),
            )

        overwritten = deepcopy(document)
        overwritten["results"][7]["capture"]["var_result"].update({
            "first": 1, "last": 1, "values": [1],
        })
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "A入力前に上書き",
        ):
            RUNNER._validate_stale_checkflag_var_result_matrix(
                overwritten, RUNNER._read_charmap(),
            )

        sentinel_missing = deepcopy(document)
        sentinel_missing["results"][2]["capture"]["var_result"].update({
            "seen": False, "first": None, "last": None, "values": [],
        })
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "A入力前に上書き",
        ):
            RUNNER._validate_stale_checkflag_var_result_matrix(
                sentinel_missing, RUNNER._read_charmap(),
            )

    def test_catalog_schema_expands_every_branch_to_deterministic_tsv(self) -> None:
        normalized, expanded = RUNNER.validate_catalog_document(
            self._catalog(), expected_rom_sha256="0" * 64,
        )
        self.assertEqual(normalized["rom_sha256"], "0" * 64)
        self.assertEqual(set(expanded), {"route12_npc_15--flute_missing"})
        row = expanded["route12_npc_15--flute_missing"]
        self.assertEqual(row["interaction"]["approach_steps"], 1)
        self.assertEqual(row["branch"]["flags"], [
            {"id": 0x119E, "value": False},
        ])
        _, matrix_rows = RUNNER.validate_state_matrix_document(
            self._state_matrix(), expected_rom_sha256="0" * 64,
        )
        projected = RUNNER.project_catalog_state_matrix(
            normalized, matrix_rows,
        )
        self.assertEqual(len(projected), 2)
        self.assertFalse(
            projected["matrix-096-023-015-collected-000"]["expect_interaction"]
        )
        execution_drift = deepcopy(matrix_rows)
        drifted_execution = execution_drift[
            "matrix-096-023-015-default-000"
        ]["interaction_execution"]
        drifted_execution["start"] = [13, 72]
        drifted_execution["walk_sequence"] = ["RIGHT", "UP"]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "strict execution二重正本",
        ):
            RUNNER.project_catalog_state_matrix(
                normalized, execution_drift,
            )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "catalog.tsv"
            RUNNER.write_catalog_tsv(path, projected)
            raw = path.read_bytes()
        self.assertTrue(raw.isascii())
        lines = raw.decode("ascii").splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(len(line.split("\t")) == 59 for line in lines))
        interactive_line = next(
            line for line in lines if "-default-" in line
        )
        interactive_fields = interactive_line.split("\t")
        self.assertIn(
            "advance@DEFAULT_ADVANCE@1@-@A@NONE@-@-@-;"
            "cancel@DEFAULT_CANCEL@1@-@A,B@NONE@-@-@-",
            interactive_fields[14],
        )
        self.assertIn(f"{0x5170}=7", interactive_fields[16])
        self.assertEqual(interactive_fields[23], str(0x08100000))
        self.assertIn("350=1", interactive_fields[17])
        self.assertEqual(interactive_fields[18], "25=1")
        self.assertEqual(
            interactive_fields[36],
            self._catalog()["entries"][0]["expected_template_raw_hex"],
        )

    def test_template_static_position_is_independent_of_live_runtime_target(
        self,
    ) -> None:
        catalog, _ = RUNNER.validate_catalog_document(self._catalog())
        _, matrix_rows = RUNNER.validate_state_matrix_document(
            self._state_matrix(), expected_rom_sha256="0" * 64,
        )
        fixture = RUNNER.project_catalog_state_matrix(
            catalog, matrix_rows,
            selected_case_ids=["matrix-096-023-015-default-000"],
        )["matrix-096-023-015-default-000"]
        interaction = fixture["interaction"]
        self.assertEqual(interaction["object"], [14, 70])
        interaction["object"] = [15, 70]
        identity = self._preinteraction_identity(
            interaction["expected_template_raw_hex"],
            template_index=15, interactive=True,
            runtime_object=[15, 70],
        )
        normalized = RUNNER._validate_catalog_preinteraction_identity(
            identity, fixture, label="moving-owner",
        )
        self.assertEqual(normalized["owner_object_index"], 15)
        self.assertEqual(normalized["template_index"], 15)
        self.assertEqual(normalized["template_position"], [14, 70])
        self.assertEqual(normalized["runtime_template_position"], [15, 70])
        self.assertTrue(normalized["runtime_template_script_exact"])
        self.assertEqual(normalized["live_current"], [22, 77])

        static_overwritten = deepcopy(identity)
        static_overwritten["template_position"] = [15, 70]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "object/root identity",
        ):
            RUNNER._validate_catalog_preinteraction_identity(
                static_overwritten, fixture, label="moving-static-drift",
            )

        live_replaced_by_static = deepcopy(identity)
        live_replaced_by_static["live_current"] = [21, 77]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "object/root identity",
        ):
            RUNNER._validate_catalog_preinteraction_identity(
                live_replaced_by_static, fixture, label="moving-live-drift",
            )

        identity_mutations = {
            "owner-index": lambda item: item.__setitem__(
                "owner_object_index", 14,
            ),
            "template-index": lambda item: item.__setitem__(
                "template_index", 14,
            ),
            "runtime-position": lambda item: item.__setitem__(
                "runtime_template_position", [14, 70],
            ),
            "runtime-script-exact": lambda item: item.__setitem__(
                "runtime_template_script_exact", False,
            ),
        }
        for label, mutate in identity_mutations.items():
            broken = deepcopy(identity)
            mutate(broken)
            with self.subTest(identity=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "object/root identity",
            ):
                RUNNER._validate_catalog_preinteraction_identity(
                    broken, fixture, label=f"moving-{label}",
                )

    def test_silent_sequence_requires_independent_static_no_text_basis(
        self,
    ) -> None:
        source = deepcopy(
            self._state_matrix()["cases"][0]["input_sequences"][0]
        )
        source.update({
            "visible_text_expected": False,
            "silent_text_basis": {
                "kind": "STATIC_NO_TEXT_PATH",
                "source_instruction_addresses": ["0x08100020"],
                "reason": "script terminates without any text opcode",
            },
        })
        source["text_oracle"].update({
            "ordered_printers": [],
            "ordered_raw_sha256s": [],
            "allowed_ordered_raw_sha256_sequences": [[]],
            "visible_text_count": 0,
        })
        source["text_oracle"]["provenance"].update({
            "source_text_addresses": [], "raw_sha256s": [],
        })
        normalized = RUNNER._normalize_input_sequences(
            [source], "silent-unit",
        )[0]
        self.assertFalse(normalized["visible_text_expected"])
        self.assertEqual(
            normalized["silent_text_basis"]["kind"],
            "STATIC_NO_TEXT_PATH",
        )

        missing_basis = deepcopy(source)
        missing_basis["silent_text_basis"] = None
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "silent_text_basis",
        ):
            RUNNER._normalize_input_sequences([missing_basis], "silent-unit")

        eos_disguised = deepcopy(source)
        eos_hash = hashlib.sha256(bytes.fromhex("a3ff")).hexdigest()
        eos_disguised["text_oracle"].update({
            "ordered_printers": [{
                "kind": "BRANCH_TEXT",
                "instruction_address": "0x08002C44",
                "caller_instruction_address": "0x08102000",
                "source_pointer": "0x08100040",
                "raw_hex": "A3FF", "raw_sha256": eos_hash,
                "expanded_hex": "A3FF", "expanded_sha256": eos_hash,
                "provenance": {"kind": "UNIT_STATIC"},
            }],
            "ordered_raw_sha256s": [eos_hash],
            "allowed_ordered_raw_sha256_sequences": [[eos_hash]],
            "visible_text_count": 1,
        })
        eos_disguised["text_oracle"]["provenance"].update({
            "source_text_addresses": [0x08100040],
            "raw_sha256s": [eos_hash],
        })
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "text source address|text ordered",
        ):
            RUNNER._normalize_input_sequences([eos_disguised], "silent-unit")

        visible_with_basis = deepcopy(source)
        visible_with_basis["visible_text_expected"] = True
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "visible path",
        ):
            RUNNER._normalize_input_sequences(
                [visible_with_basis], "silent-unit",
            )

    def test_state_matrix_summary_binds_full_case_sequence_cross_product(
        self,
    ) -> None:
        catalog, _ = RUNNER.validate_catalog_document(
            self._catalog(), expected_rom_sha256="0" * 64,
        )
        _, matrix_rows = RUNNER.validate_state_matrix_document(
            self._state_matrix(), expected_rom_sha256="0" * 64,
        )
        projected = RUNNER.project_catalog_state_matrix(catalog, matrix_rows)
        results = {
            "catalog_batch": {
                "status": "PASS", "process_runs": 2,
                "result": {
                    "input_sequence_attempt_count": 2,
                    "successful_path_count": 2,
                    "empty_text": 0, "softlocks": 0,
                    "results": [
                        {"owner_key": row["owner_key"]}
                        for row in projected.values()
                    ],
                },
            },
        }
        summary = RUNNER._state_matrix_execution_summary(
            matrix_rows, projected, results, catalog_selected=True,
        )
        self.assertEqual(summary, {
            "source_sequence_count": 2,
            "selected_sequence_count": 2,
            "executed_sequence_count": 2,
            "full_sequence_matrix": True,
            "all_reachable_input_options_enumerated": True,
            "unknown_effect_count": 0,
            "empty_visible_text_count": 0,
            "softlock_count": 0,
            "executed_owner_count": 1,
            "required_runtime_owner_count": 0,
            "untested_runtime_owner_count": 0,
            "structural_nontrigger_count": 0,
            "all_5416_trigger_event_owners_executed": False,
            "all_1001_structural_nontriggers_proven": False,
            "all_runtime_event_owners_executed": False,
            "all_structural_nontriggers_proven": False,
        })
        focused = {next(iter(projected)): next(iter(projected.values()))}
        focused_summary = RUNNER._state_matrix_execution_summary(
            matrix_rows, focused, {
                "catalog_batch": {
                    "status": "PASS", "process_runs": 2,
                    "result": {
                        "input_sequence_attempt_count": 2,
                        "successful_path_count": 2,
                        "empty_text": 0, "softlocks": 0,
                        "results": [
                            {"owner_key": row["owner_key"]}
                            for row in focused.values()
                        ],
                    },
                },
            }, catalog_selected=True,
        )
        self.assertFalse(focused_summary["full_sequence_matrix"])
        nondeterministic = deepcopy(results)
        nondeterministic["catalog_batch"]["process_runs"] = 1
        self.assertFalse(RUNNER._state_matrix_execution_summary(
            matrix_rows, projected, nondeterministic,
            catalog_selected=True,
        )["all_reachable_input_options_enumerated"])

    def test_control_abi_registry_all_domains_and_internal_trace_fail_closed(
        self,
    ) -> None:
        matrix = self._state_matrix()
        bag = {
            "fixture_kind": "BAG",
            "pockets": [{
                "index": index,
                "slots": [
                    {
                        "item_id": 350 if index == 0 and slot == 0 else 0,
                        "quantity": 1 if index == 0 and slot == 0 else 0,
                    }
                    for slot in range(count)
                ],
            } for index, count in enumerate((42, 30, 13, 58, 43))],
        }
        pc = {
            "fixture_kind": "PC_ITEMS",
            "slots": [
                {"item_id": 42 if slot == 0 else 0,
                 "quantity": 3 if slot == 0 else 0}
                for slot in range(30)
            ],
        }
        party = {
            "fixture_kind": "PARTY", "count": 1,
            "raw_hex": "00" * 600,
        }
        party_minigame = self._party_minigame_fixture()
        daycare_transaction = self._daycare_transaction_fixture()
        party_move_transaction = self._party_move_transaction_fixture()
        storage = {"fixture_kind": "STORAGE", "raw_hex": "00" * 0x83D0}
        pokedex = self._pokedex_fixture()
        wonder_card = bytearray(0x14C)
        wonder_card[0:2] = (1).to_bytes(2, "little")
        ram_script_data = bytearray(999)
        ram_script_data[0:4] = bytes((0x33, 0xFF, 0xFF, 0xFF))
        ram_script_data[4:10] = bytes.fromhex("160480a5610c")
        ram_script_crc = RUNNER._pokemon_crc16(bytes(ram_script_data))
        signed = {
            "fixture_kind": "SIGNED_RAM_SCRIPT",
            "variant": "VALID_SET_VAR_RETURN",
            "wonder_card_offset": 0x32E4,
            "wonder_card_raw_hex": bytes(wonder_card).hex(),
            "wonder_card_crc_offset": 0x32E0,
            "wonder_card_crc": RUNNER._pokemon_crc16(bytes(wonder_card)),
            "ram_script_offset": 0x361C,
            "ram_script_raw_hex": (
                ram_script_crc.to_bytes(4, "little")
                + bytes(ram_script_data) + b"\0"
            ).hex(),
            "ram_script_data_crc": ram_script_crc,
            "stored_ram_script_crc": ram_script_crc,
            "program_hex": "160480a5610c",
            "program_relation": "SET_VAR_8004_61A5_THEN_RETURNRAM",
        }
        fixtures = {
            RUNNER._runner_fixture_key(payload): payload
            for payload in (
                bag, pc, party, party_minigame, daycare_transaction,
                party_move_transaction, storage, signed, pokedex,
            )
        }
        (
            bag_ref, pc_ref, party_ref, party_minigame_ref,
            daycare_transaction_ref, party_move_transaction_ref,
            storage_ref, signed_ref, pokedex_ref,
        ) = (
            RUNNER._runner_fixture_key(payload)
            for payload in (
                bag, pc, party, party_minigame, daycare_transaction,
                party_move_transaction, storage, signed, pokedex,
            )
        )
        # Source-defined controls added since the original 27-domain fixture.
        # Keep complete-domain equality and independently exercise their transports.
        gift_schema = self._gift_storage_sweep_schema()
        gift_control = RUNNER.gift_storage_transaction_sweep_controls(gift_schema)[0]
        gift_ref = gift_control["required_value_in_matrix_case"]["layout_ref"]
        fossil, ruin, facility = (
            self._fossil_revival_fixture(), self._ruin_seal_fixture(),
            self._facility_fixture(),
        )
        fossil_ref, ruin_ref, facility_ref = (
            RUNNER._runner_fixture_key(payload)
            for payload in (fossil, ruin, facility)
        )
        fixtures.update(gift_schema["runner_fixtures"])
        fixtures.update({fossil_ref: fossil, ruin_ref: ruin, facility_ref: facility})
        from tools.stage61_interaction_oracle import _gift_storage_dedicated_sweep_manifest
        gift_manifest = _gift_storage_dedicated_sweep_manifest()
        matrix["dedicated_fixture_sweeps"] = {
            "GIFT_STORAGE_TRANSACTION_STATE": {
                key: gift_manifest[key] for key in (
                    "schema_version", "fixture_kind", "relation",
                    "executor_representative_count", "runner_exhaustive_layout_count",
                    "executor_representative_scenario_ids", "runner_exhaustive_scenario_ids",
                    "runner_sweep_root", "runner_sweep_map_section_id", "scenarios", "assertions",
                )
            }
        }
        matrix["runner_fixtures"] = fixtures
        matrix["runner_projection"]["required_columns"].append(
            "control_requirements"
        )

        def external(
            kind: str, identifier: int, value: object,
            relations: list[dict[str, object]],
            candidates: object | None = None,
        ) -> dict[str, object]:
            return {
                "kind": kind, "id": identifier, "source_ids": [identifier],
                "read_addresses": [
                    f"0x{identifier:08X}"
                    if kind == "SIGNED_RAM_SCRIPT" else "0x08100000"
                ],
                "candidate_values": [value] if candidates is None else candidates,
                "relations": relations,
                "required_value_in_matrix_case": value,
                "requirement_basis": "SYNTHETIC_INDEPENDENT_CFG",
            }

        seed = 0x12345678
        maximum = 7
        expected_modulo = (
            ((seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF) >> 16
        ) % maximum
        interactive = matrix["cases"][0]
        interactive["control_requirements"] = {
            "external": [
                external("FLAG", 0x18B4, False, []),
                external("DAYCARE_OCCUPIED", 0, False, [{
                    "operator": "EVENT_DESIGN_SOURCE_PHYSICAL_BOOL",
                }], [False, True]),
                external("ENGINE_SPECIAL_FLAG", 0x4001, False, [{
                    "operator": "ENGINE_SPECIAL_FLAG_BOOL",
                    "source_abi": deepcopy(
                        RUNNER._ENGINE_SPECIAL_FLAG_SOURCE
                    ),
                }]),
                external("VAR", 0x5170, 7, [{
                    "operator": "COMPARE_TO_VALUE", "value": 7,
                }]),
                external("ITEM", 350, 1, [{
                    "operator": "HAS_COUNT", "quantity": 1,
                }]),
                external("TRAINER", 25, True, [{
                    "operator": "DEFEATED_FLAG",
                }]),
                external("BAG_CAPACITY", 350, {
                    "expected_result": True, "layout_ref": bag_ref,
                }, [{"operator": "HAS_SPACE", "quantity": 1}],
                    "FIXTURE_BAG_LAYOUT_REQUIRED"),
                external("PC_ITEM", 42, {
                    "required_count": 3, "layout_ref": pc_ref,
                }, [{"operator": "PC_HAS_COUNT", "quantity": 3}]),
                external("PC_CAPACITY", 42, {
                    "expected_result": True, "layout_ref": pc_ref,
                }, [{"operator": "ADD_PC_ITEM_CAPACITY", "quantity": 1}],
                    "BAG_OR_PC_LAYOUT_REQUIRED"),
                external("PARTY_COUNT", 0, {
                    "count": 1, "party_layout_ref": party_ref,
                }, [{"operator": "GET_PARTY_SIZE"}]),
                self._daycare_transaction_external(
                    daycare_transaction_ref,
                ),
                external("PARTY_MINIGAME", 0, {
                    "mode": 0, "eligible": True, "selected_slot": 5,
                    "party_count": 6,
                    "party_layout_ref": party_minigame_ref,
                }, [{
                    "operator":
                        "WIRELESS_MINIGAME_PARTY_ELIGIBILITY_AND_SELECTION",
                }], "PARTY_LAYOUT_REQUIRED"),
                external("PARTY_MOVE", 15, {
                    "move_id": 15, "expected_slot": 6,
                    "party_layout_ref": party_ref,
                }, [{"operator": "FIRST_NON_EGG_MEMBER_KNOWING_MOVE"}]),
                self._party_move_transaction_external(
                    party_move_transaction_ref,
                ),
                self._rfu_external("mode0-leader-result5"),
                self._center_link_external("group0-leader-result5"),
                external("GIFT_STORAGE_TRANSACTION_STATE", 0,
                    gift_control["required_value_in_matrix_case"],
                    gift_control["relations"],
                    list(RUNNER._GIFT_STORAGE_TRANSACTION_EXECUTOR_SCENARIO_IDS)),
                self._fossil_revival_external(fossil_ref),
                self._ruin_seal_external(ruin_ref),
                self._facility_external(facility_ref),
                external("PARTY_OR_STORAGE_CAPACITY", 25, {
                    "expected_result": 0,
                    "party_layout_ref": party_ref,
                    "storage_layout_ref": storage_ref,
                }, [{
                    "operator": "CAN_RECEIVE_MON_OR_EGG",
                    "species_operand": 25,
                }], "PARTY_AND_BOX_LAYOUT_FIXTURE_REQUIRED"),
                external("MONEY", 0, 1000, [{
                    "operator": "AT_LEAST", "amount": 500,
                }]),
                self._berry_powder_external(50),
                external("COINS", 0, {"vega": 10, "cfru": 20}, [{
                    "operator": "WRITE_CURRENT_COINS_TO_VAR",
                    "destination_var": 0x8000,
                }]),
                external("PLAYER_GENDER", 0, 1, [{
                    "operator": "SAVE_BLOCK2_PLAYER_GENDER",
                }]),
                external("RNG", 0, {
                    "state": seed, "expected_modulo": expected_modulo,
                    "maximum": maximum,
                }, [{
                    "operator": "RANDOM_MODULO", "maximum_operand": maximum,
                    "exact_seed_or_stub_required": True,
                }]),
                external("REMATCH_STATE", 7, {
                    "ready": True, "local_id": 7,
                    "saveblock1_offset": 0x063A + 7,
                    "ready_byte": 1,
                }, [{
                    "operator": "SAVEBLOCK1_REMATCH_BYTE_NONZERO",
                    "save_block1_offset": 0x063A + 7,
                    "trainerbattle_type": 5,
                }]),
                external("PARTY_USABLE_FOR_DOUBLE", 25, {
                    "mons_state": 0, "party_layout_ref": party_ref,
                }, [{
                    "operator": "GET_MONS_STATE_TO_DOUBLES",
                    "trainerbattle_type": 4,
                    "result_meanings": {
                        "0": "TWO_USABLE_MONS", "1": "ONLY_ONE_MON",
                        "2": "ONLY_ONE_USABLE_MON",
                    },
                }], "PARTY_LAYOUT_REQUIRED"),
                external("PLAYER_POSITION", 0, {
                    "x": 14, "y": 71, "group": 96, "map": 23,
                    "apply_relation": "ACTUAL_STOCK_WARP_THEN_REAL_MOVEMENT",
                }, [{
                    "operator": "ACTUAL_PLAYER_COORDINATES_BEFORE_INTERACTION",
                }], "TELEPORT_FIXTURE_COORDINATES"),
                external("QUEST_LOG_STATE", 0, 3, [{
                    "operator": "ENGINE_GLOBAL_QL_STATE_EXACT",
                }], [0, 1, 2, 3]),
                external("SIGNED_RAM_SCRIPT", 0x08100020, {
                    "variant": "VALID_SET_VAR_RETURN",
                    "layout_ref": signed_ref,
                    "expected_dispatch": True,
                    "expected_var_8004": 0x61A5,
                    "expected_ram_script_after": "UNCHANGED",
                }, [{
                    "operator": "GET_SAVED_RAM_SCRIPT_IF_VALID_THREE_WAY",
                    "source": deepcopy(
                        RUNNER._runner_control_abi_contract()["layouts"]
                        ["signed_ram_script"]["source"]
                    ),
                    "valid_program_hex": "160480a5610c",
                }], "SIGNED_RAM_SCRIPT_FIXTURE_REQUIRED"),
                self._pokedex_external(pokedex_ref),
            ],
            "internal": [{
                "kind": "VAR_RESULT_BRANCH_READ",
                "sequence_id": sequence_id,
                "instruction_address": "0x08100010",
                "writer": "YES_NO", "candidate_values": [0, 1],
                "producer": {"writer": "YES_NO"},
                "def_use_status": "CROSS_NODE_EXACT",
                "capture": {
                    "before_pc": 0x08100010, "after_pc": 0x08100015,
                    "owner_address": "0x02037004",
                    "expected_value": value,
                    "expected_token_index": token_index,
                    "expected_execution_ordinal": 0,
                },
            } for sequence_id, value, token_index in (
                ("advance", 1, 0), ("cancel", 0, 1),
            )],
        }
        matrix["cases"][1]["control_requirements"] = {
            "external": [external("FLAG", 0x149E, True, [])],
            "internal": [],
        }
        document, rows = RUNNER.validate_state_matrix_document(
            matrix, expected_rom_sha256="0" * 64,
        )
        self.assertTrue(document["runner_control_abi_complete"])
        self.assertEqual(
            {row["kind"] for row in rows[
                "matrix-096-023-015-default-000"
            ]["control_requirements"]["external"]},
            RUNNER._CONTROL_EXTERNAL_KINDS,
        )
        projected = RUNNER.project_catalog_state_matrix(
            RUNNER.validate_catalog_document(
                self._catalog(), expected_rom_sha256="0" * 64,
            )[0], rows,
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            RUNNER.write_control_fixture_files(root / "fixtures", fixtures)
            RUNNER.write_catalog_tsv(root / "catalog.tsv", projected)
            self.assertEqual(
                sorted(path.stat().st_size for path in (root / "fixtures").iterdir()),
                sorted([186 * 4, 30 * 4, 600, 600, 0x83D0,
                        1028, 764, 4 + 0x14C + 0x3EC, 4 + 4 * 52,
                        # Gift: fixed header, party, storage, four Pokédex maps.
                        148, 188, 280 + len(RUNNER._facility_canonical_bytes(facility))]
                       + [192 + 600 + 0x83D0 + 4 * 52] * 30),
            )
            self.assertTrue(all(
                len(line.split("\t")) == 59
                for line in (root / "catalog.tsv").read_text(
                    encoding="ascii"
                ).splitlines()
            ))

        unknown = deepcopy(matrix)
        unknown["cases"][0]["control_requirements"]["external"][0][
            "kind"
        ] = "UNKNOWN"
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "kind未知"):
            RUNNER.validate_state_matrix_document(unknown)
        bad_key = deepcopy(matrix)
        payload = next(iter(bad_key["runner_fixtures"].values()))
        bad_key["runner_fixtures"] = {"f" * 64: payload}
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "canonical SHA"):
            RUNNER.validate_state_matrix_document(bad_key)
        unresolved = deepcopy(matrix)
        unresolved["cases"][0]["control_requirements"]["internal"][0][
            "writer"
        ] = "SPECIAL_UNRESOLVED"
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "未解決"):
            RUNNER.validate_state_matrix_document(unresolved)

        special_var_8000 = deepcopy(matrix)
        special_var_8000["cases"][0]["control_requirements"]["internal"][0][
            "capture"
        ]["owner_address"] = "0x02036FEC"
        _, special_rows = RUNNER.validate_state_matrix_document(
            special_var_8000, expected_rom_sha256="0" * 64,
        )
        special_control = special_rows[
            "matrix-096-023-015-default-000"
        ]["control_requirements"]["internal"][0]
        self.assertEqual(
            special_control["capture"]["owner_address"], 0x02036FEC,
        )
        self.assertIn(
            f"@{0x02036FEC}@",
            RUNNER._encode_internal_control(special_control),
        )

        non_special_owner = deepcopy(matrix)
        non_special_owner["cases"][0]["control_requirements"]["internal"][0][
            "capture"
        ]["owner_address"] = "0x02037006"
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "owner不一致"):
            RUNNER.validate_state_matrix_document(non_special_owner)

    def test_internal_control_dynamic_occurrences_use_token_and_ordinal_identity(
        self,
    ) -> None:
        sequence = {"sequence_id": "retry"}

        def control(
            token_index: int, expected_value: int,
            execution_ordinal: int = 0,
        ) -> dict[str, object]:
            return {
                "kind": "VAR_RESULT_BRANCH_READ",
                "sequence_id": sequence["sequence_id"],
                "instruction_address": "0x0818FB14",
                "writer": "YES_NO", "candidate_values": [0, 1],
                "producer": {"writer": "YES_NO"},
                "def_use_status": "CROSS_NODE_EXACT",
                "capture": {
                    "before_pc": "0x0818FB14",
                    "after_pc": "0x0818FB1A",
                    "owner_address": "0x02037004",
                    "expected_value": expected_value,
                    "expected_token_index": token_index,
                    "expected_execution_ordinal": execution_ordinal,
                },
            }

        normalized = RUNNER._normalize_internal_controls(
            [control(1, 1), control(0, 0)], [sequence], "dynamic-retry",
        )
        self.assertEqual(
            [row["capture"]["expected_token_index"] for row in normalized],
            [0, 1],
        )
        self.assertEqual(
            [row["capture"]["expected_value"] for row in normalized],
            [0, 1],
        )
        same_token = RUNNER._normalize_internal_controls(
            [control(0, 0, 1), control(0, 0, 0)], [sequence],
            "same-token-ordered",
        )
        self.assertEqual(
            [(row["capture"]["expected_token_index"],
              row["capture"]["expected_execution_ordinal"])
             for row in same_token],
            [(0, 0), (0, 1)],
        )

        exact_duplicate = [control(0, 0), control(0, 0)]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "internal control重複",
        ):
            RUNNER._normalize_internal_controls(
                exact_duplicate, [sequence], "duplicate-token",
            )
        conflicting_duplicate = [control(0, 0), control(0, 1)]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "internal control重複",
        ):
            RUNNER._normalize_internal_controls(
                conflicting_duplicate, [sequence], "conflicting-token",
            )
        implicit_duplicate = control(0, 0)
        implicit_duplicate.pop("sequence_id")
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "internal control重複",
        ):
            RUNNER._normalize_internal_controls(
                [implicit_duplicate, control(0, 1)], [sequence],
                "implicit-explicit-token",
            )

        def observed(
            token_index: int, expected_value: int,
            execution_ordinal: int = 0, execution_count: int = 1,
        ) -> dict[str, object]:
            return {
                "writer": "YES_NO",
                "instruction_address": "0x0818FB14",
                "before_pc": "0x0818FB14",
                "after_pc": "0x0818FB1A",
                "expected_token_index": token_index,
                "expected_execution_ordinal": execution_ordinal,
                "owner_address": "0x02037004",
                "expected_value": expected_value,
                "observed_value": expected_value,
                "observed_script_pointer": "0x0818FB14",
                "execution_count": execution_count,
                "hit_count": 1,
                "value_mismatch": False,
            }

        fixture = {"control_requirements": {"internal": normalized}}
        captures = [observed(0, 0), observed(1, 1)]
        self.assertEqual(
            RUNNER._validate_persistence_internal_controls(
                captures, fixture, sequence, label="dynamic-retry",
            ),
            captures,
        )
        same_token_fixture = {
            "control_requirements": {"internal": same_token},
        }
        same_token_captures = [
            observed(0, 0, 0, 2), observed(0, 0, 1, 2),
        ]
        self.assertEqual(
            RUNNER._validate_persistence_internal_controls(
                same_token_captures, same_token_fixture, sequence,
                label="same-token-ordered",
            ),
            same_token_captures,
        )
        wrong_execution_count = deepcopy(same_token_captures)
        wrong_execution_count[1]["execution_count"] = 3
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "capture不一致",
        ):
            RUNNER._validate_persistence_internal_controls(
                wrong_execution_count, same_token_fixture, sequence,
                label="same-token-extra-execution",
            )

        count_mutations = {
            "missing": captures[:1],
            "extra": captures + [observed(2, 1)],
        }
        for label, broken in count_mutations.items():
            with self.subTest(count=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "count不一致",
            ):
                RUNNER._validate_persistence_internal_controls(
                    broken, fixture, sequence, label="dynamic-retry",
                )

        duplicate_actual = deepcopy(captures)
        duplicate_actual[1]["expected_token_index"] = 0
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "owner過不足",
        ):
            RUNNER._validate_persistence_internal_controls(
                duplicate_actual, fixture, sequence, label="dynamic-retry",
            )

        token_swap = deepcopy(captures)
        token_swap[0]["expected_token_index"] = 1
        token_swap[1]["expected_token_index"] = 0
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "capture不一致",
        ):
            RUNNER._validate_persistence_internal_controls(
                token_swap, fixture, sequence, label="dynamic-retry",
            )

        value_swap = deepcopy(captures)
        for row in value_swap:
            row["expected_value"] ^= 1
            row["observed_value"] ^= 1
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "capture不一致",
        ):
            RUNNER._validate_persistence_internal_controls(
                value_swap, fixture, sequence, label="dynamic-retry",
            )

    def test_event_design_physical_bool_and_save_mirrors_fail_closed(
        self,
    ) -> None:
        self.assertEqual(
            RUNNER._runner_control_abi_contract()["required_value_types"][
                "DAYCARE_OCCUPIED"
            ],
            "bool",
        )
        empty_state = {
            "flags": [], "vars": [], "items": [], "trainers": [],
        }

        def control(
            kind: str, identifier: int, value: bool, relation: str,
        ) -> dict[str, object]:
            return {
                "kind": kind, "id": identifier,
                "source_ids": [identifier],
                "read_addresses": ["0x08100000"],
                "candidate_values": [False, True],
                "relations": [{"operator": relation}],
                "required_value_in_matrix_case": value,
                "requirement_basis": "EVENT_DESIGN_SOURCE_MODEL",
            }

        daycare = control(
            "DAYCARE_OCCUPIED", 0, True,
            "EVENT_DESIGN_SOURCE_PHYSICAL_BOOL",
        )
        normalized = RUNNER._normalize_external_controls(
            [daycare], empty_state, {}, "event-design-daycare",
        )
        self.assertEqual(normalized[0]["required_value_in_matrix_case"], True)
        self.assertEqual(
            RUNNER._encode_external_control(normalized[0]),
            "DAYCARE_OCCUPIED@0@1@EVENT_DESIGN_SOURCE_PHYSICAL_BOOL:0",
        )

        # Exact BG:097/047 production projection supplied by the oracle:
        # ordinary flag owners stay relation-free, all eight certification
        # flags and the league owner retain their physical save mirrors.
        ordinary_flag_ids = (
            0x0824, 0x0825, 0x0826, 0x0827, 0x082C,
            0x13D8, 0x13F2, 0x13F3, 0x13F4, 0x13F9, 0x140C,
        )
        projection_controls = []
        projection_flags = []
        for ordinal, identifier in enumerate(ordinary_flag_ids):
            projected = control(
                "FLAG", identifier, bool(ordinal & 1),
                "EVENT_DESIGN_SOURCE_PHYSICAL_BOOL",
            )
            projected["relations"] = []
            projection_controls.append(projected)
            projection_flags.append({
                "id": identifier, "value": bool(ordinal & 1),
            })
        for identifier in range(0x1400, 0x1408):
            value = bool(identifier & 1)
            projection_controls.append(control(
                "FLAG", identifier, value,
                "CERT_OWNER_FLAG_TO_MODERN_CERTIFICATION_BIT_MIRROR",
            ))
            projection_flags.append({"id": identifier, "value": value})
        projection_controls.append(control(
            "FLAG", 0x13FA, True,
            "KANTO_LEAGUE_STATE_TO_LEAGUE_I_II_SAVE_MIRROR",
        ))
        projection_flags.append({"id": 0x13FA, "value": True})
        projected_document = RUNNER._normalize_external_controls(
            projection_controls,
            {**empty_state, "flags": projection_flags}, {},
            "event-design-bg-097-047-projection",
        )
        relations_by_id = {
            row["id"]: [relation["operator"]
                        for relation in row["relations"]]
            for row in projected_document
        }
        self.assertTrue(all(
            relations_by_id[identifier] == []
            for identifier in ordinary_flag_ids
        ))
        self.assertTrue(all(
            relations_by_id[identifier] == [
                "CERT_OWNER_FLAG_TO_MODERN_CERTIFICATION_BIT_MIRROR"
            ]
            for identifier in range(0x1400, 0x1408)
        ))
        self.assertEqual(relations_by_id[0x13FA], [
            "KANTO_LEAGUE_STATE_TO_LEAGUE_I_II_SAVE_MIRROR",
        ])

        for label, mutate in {
            "id": lambda row: row.__setitem__("id", 1),
            "required-bool": lambda row: row.__setitem__(
                "required_value_in_matrix_case", 1,
            ),
            "candidate-missing": lambda row: row.__setitem__(
                "candidate_values", [False],
            ),
            "candidate-order": lambda row: row.__setitem__(
                "candidate_values", [True, False],
            ),
            "relation-missing": lambda row: row.__setitem__("relations", []),
            "relation-wrong": lambda row: row["relations"][0].__setitem__(
                "operator", "DEFEATED_FLAG",
            ),
        }.items():
            broken = deepcopy(daycare)
            mutate(broken)
            with self.subTest(daycare=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [broken], empty_state, {}, f"event-design-daycare-{label}",
                )

        for identifier, relation in (
            (0x1400, "CERT_OWNER_FLAG_TO_MODERN_CERTIFICATION_BIT_MIRROR"),
            (0x1407, "CERT_OWNER_FLAG_TO_MODERN_CERTIFICATION_BIT_MIRROR"),
            (0x13FA, "KANTO_LEAGUE_STATE_TO_LEAGUE_I_II_SAVE_MIRROR"),
        ):
            row = control("FLAG", identifier, False, relation)
            state = {**empty_state, "flags": [{"id": identifier, "value": False}]}
            normalized = RUNNER._normalize_external_controls(
                [row], state, {}, f"event-design-flag-{identifier:04x}",
            )
            self.assertEqual(normalized[0]["relations"], [{
                "operator": relation,
            }])
            missing = deepcopy(row)
            missing["relations"] = []
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "flag mirror",
            ):
                RUNNER._normalize_external_controls(
                    [missing], state, {},
                    f"event-design-flag-{identifier:04x}-missing",
                )

        foreign_mirror = control(
            "FLAG", 0x1234, False,
            "CERT_OWNER_FLAG_TO_MODERN_CERTIFICATION_BIT_MIRROR",
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "flag mirror",
        ):
            RUNNER._normalize_external_controls(
                [foreign_mirror], {
                    **empty_state,
                    "flags": [{"id": 0x1234, "value": False}],
                }, {}, "event-design-foreign-mirror",
            )

        ordinary_flag = control(
            "FLAG", 0x0824, False,
            "EVENT_DESIGN_SOURCE_PHYSICAL_BOOL",
        )
        ordinary_trainer = control(
            "TRAINER", 0x0123, False,
            "EVENT_DESIGN_SOURCE_PHYSICAL_BOOL",
        )
        projected_flag = deepcopy(ordinary_flag)
        projected_flag["relations"] = []
        projected_trainer = deepcopy(ordinary_trainer)
        projected_trainer["relations"] = [{"operator": "DEFEATED_FLAG"}]
        self.assertEqual(
            RUNNER._normalize_external_controls(
                [projected_flag], {
                    **empty_state,
                    "flags": [{"id": 0x0824, "value": False}],
                }, {}, "event-design-projected-flag",
            )[0]["relations"],
            [],
        )
        self.assertEqual(
            RUNNER._normalize_external_controls(
                [projected_trainer], {
                    **empty_state,
                    "trainers": [{"id": 0x0123, "defeated": False}],
                }, {}, "event-design-projected-trainer",
            )[0]["relations"],
            [{"operator": "DEFEATED_FLAG"}],
        )
        cross_mirrors = (
            control(
                "FLAG", 0x1400, False,
                "KANTO_LEAGUE_STATE_TO_LEAGUE_I_II_SAVE_MIRROR",
            ),
            control(
                "FLAG", 0x13FA, False,
                "CERT_OWNER_FLAG_TO_MODERN_CERTIFICATION_BIT_MIRROR",
            ),
        )
        relation_forgery_rows = [
            (
                "ordinary-flag-event-relation", ordinary_flag,
                {**empty_state, "flags": [{"id": 0x0824, "value": False}]},
            ),
            (
                "trainer-event-relation", ordinary_trainer,
                {**empty_state, "trainers": [{
                    "id": 0x0123, "defeated": False,
                }]},
            ),
        ]
        relation_forgery_rows.extend(
            (
                f"cross-mirror-{row['id']:04x}", row,
                {**empty_state, "flags": [{
                    "id": row["id"], "value": False,
                }]},
            )
            for row in cross_mirrors
        )
        for label, row, state in relation_forgery_rows:
            with self.subTest(event_design_relation=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_external_controls(
                    [row], state, {}, f"event-design-{label}",
                )

    def test_event_design_c_controls_use_physical_save_owners(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        for exact in (
            "S61_CONTROL_DAYCARE_OCCUPIED",
            'strcmp(value, "DAYCARE_OCCUPIED") == 0',
            '"EVENT_DESIGN_SOURCE_PHYSICAL_BOOL"',
            '"CERT_OWNER_FLAG_TO_MODERN_CERTIFICATION_BIT_MIRROR"',
            '"KANTO_LEAGUE_STATE_TO_LEAGUE_I_II_SAVE_MIRROR"',
            "S61_EVENT_DESIGN_STATE_KANTO_LEAGUE_CLEAR_FLAG = 0x13FAU",
            "S61_EVENT_DESIGN_CERT_OWNER_FLAG_BASE = 0x1400U",
            "S61_EVENT_DESIGN_CERT_OWNER_FLAG_COUNT = 8U",
            "S61_SAVE1_DAYCARE_OFFSET = 0x2F80U",
            "S61_DAYCARE_MON_STRIDE = 140U",
            "S61_BOX_MON_SIZE = 80U",
            "WORLD_MODERN_SAVE_LEAGUE_I_OFFSET = 20U",
            "WORLD_MODERN_SAVE_LEAGUE_II_OFFSET = 21U",
            "WORLD_MODERN_SAVE_CERTIFICATIONS_OFFSET = 24U",
            "WORLD_MODERN_SAVE_FINALIZE = 0x092D28D9U",
            "static bool s61_catalog_daycare_occupied(struct mCore *core)",
            "WORLD_GET_BOX_MON_DATA, daycare,",
            "WORLD_MON_DATA_SPECIES, 0U, 0U) != 0U",
            "S61_EVENT_DESIGN_CERT_OWNER_FLAG_BASE + index",
            "BOOTSTRAP_PLAYER_PARTY + byte",
            "s61_apply_catalog_event_design_physical_state(core, row);",
            "s61_verify_catalog_event_design_physical_state(core, row);",
            "catalog daycare physical seed readback differs",
            "catalog daycare physical state changed before input",
            "catalog certification modern-save mirror differs",
            "catalog Kanto League modern-save mirror differs",
            "catalog EventDesign modern-save checksum is empty",
        ):
            self.assertIn(exact, source)
        self.assertIn(
            "byte < S61_DAYCARE_MON_STRIDE * 2U", source,
        )
        self.assertIn(
            "daycare + S61_DAYCARE_MON_STRIDE", source,
        )
        self.assertIn(
            "BOOTSTRAP_PLAYER_PARTY + byte", source,
        )
        self.assertGreaterEqual(source.count("WORLD_GET_BOX_MON_DATA"), 5)
        self.assertIn(
            "WORLD_MODERN_SAVE_FINALIZE,\n"
            "            WORLD_SECTOR31_LEDGER", source,
        )

    def test_pc_capacity_uses_exact_add_pc_item_and_four_synthetic_probes(
        self,
    ) -> None:
        abi = RUNNER._runner_control_abi_contract()
        producer = abi["mutation_safe_producers"]["PC_CAPACITY"]
        self.assertEqual(producer["thumb_entry"], "0x08099DD1")
        self.assertEqual(producer["rom_binding"], {
            "address": "0x08099DD0", "byte_length": 0x96,
            "sha256": (
                "02fc840390650c9f8b62622cc301ff789257d0c527cc113a76210e7d5259ce8e"
            ),
        })
        self.assertEqual(producer["required_actual_mgba_case_count"], 4)
        self.assertEqual(producer["mutable_owner"]["encoding"], (
            "item_id u16; quantity plain u16"
        ))
        self.assertEqual(abi["layouts"]["pc_items"]["slot"], {
            "item_id": "u16", "quantity": "plain u16",
        })
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("S61_ADD_PC_ITEM = 0x08099DD1U", source)
        self.assertIn("s61_probe_pc_capacity", source)
        self.assertIn("s61_hash_all_mutable_owner_memory", source)
        self.assertIn("s61_pc_item_plain_count", source)
        self.assertNotIn("s61_pc_item_decrypted_count", source)
        self.assertIn("S61_MAP_NAME_POPUP_BUFFER_START = 0x03007DB4U", source)
        self.assertIn("S61_MAP_NAME_POPUP_BUFFER_END = 0x03007DCDU", source)
        self.assertNotIn(
            "catalog PC_CAPACITY producer ABI is not registered", source,
        )

        expected = [
            ("pc-capacity-existing-998-plus-1", 998, 999, 1, 0, [2, 3]),
            ("pc-capacity-existing-999-plus-1", 999, 999, 0, None, []),
            ("pc-capacity-empty-slot", 0, 1, 1, 29,
             [116, 117, 118, 119]),
            ("pc-capacity-full", 0, 0, 0, None, []),
        ]
        rows = []
        for case_id, before, after, result, target, allowed in expected:
            raw_before = bytearray(120)
            if case_id == "pc-capacity-existing-998-plus-1":
                raw_before[:4] = b"\x01\x00\xE6\x03"
            elif case_id == "pc-capacity-existing-999-plus-1":
                raw_before[:4] = b"\x01\x00\xE7\x03"
            elif case_id == "pc-capacity-empty-slot":
                for slot in range(29):
                    raw_before[slot * 4:slot * 4 + 4] = \
                        (slot + 2).to_bytes(2, "little") + b"\x01\x00"
            else:
                for slot in range(30):
                    raw_before[slot * 4:slot * 4 + 4] = \
                        (slot + 2).to_bytes(2, "little") + b"\x01\x00"
            raw_after = bytearray(raw_before)
            if result and target == 0:
                raw_after[2:4] = (999).to_bytes(2, "little")
            elif result and target == 29:
                raw_after[116:120] = b"\x01\x00\x01\x00"
            actual_deltas = [
                index for index, pair in enumerate(zip(raw_before, raw_after))
                if pair[0] != pair[1]
            ]
            before_hash = RUNNER._fnv1a64(raw_before)
            after_hash = RUNNER._fnv1a64(raw_after)
            rows.append({
                "case_id": case_id, "query_item": 1, "quantity": 1,
                "expected_result": result, "actual_result": result,
                "before_count": before, "after_count": after,
                "pc_raw_before_fnv1a64": before_hash,
                "pc_raw_after_fnv1a64": after_hash,
                "pc_raw_restored_fnv1a64": before_hash,
                "pc_mutation_exact": True,
                "all_owner_before_fnv1a64": "3" * 16,
                "all_owner_after_fnv1a64": (
                    "4" * 16 if result else "3" * 16
                ),
                "all_owner_restored_fnv1a64": "3" * 16,
                "pc_raw_before_hex": raw_before.hex().upper(),
                "pc_raw_after_hex": raw_after.hex().upper(),
                "pc_raw_restored_hex": raw_before.hex().upper(),
                "target_slot": target, "allowed_offsets": allowed,
                "actual_delta_offsets": actual_deltas,
                "pc_raw_expected_byte_exact": True,
                "all_memory_outside_allowed_exact": True,
                "all_owner_hashes_restored": True,
            })
        document = {
            "schema_version": 3, "status": "PASS",
            "case": "pc_capacity_contract",
            "oracle_thumb_entry": "0x08099DD1",
            "rom_preimage_checked": True,
            "savestate_actual_call_restore": True,
            "all_mutable_owner_hashes_restored": True,
            "actual_call_full_ewram_iwram_outside_allowed_byte_exact": True,
            "pc_slot_expected_bytes_all_cases_exact": True,
            "synthetic_case_count": 4, "results": rows,
            "fresh_core": True, "field_input_recovered": True,
            "failed": 0, "untested": 0, "warnings": 0,
            "framebuffer_artifacts": [],
        }
        validated = RUNNER._validate_case(
            document, "pc_capacity_contract", {}, {}, {}, {},
        )
        validated["artifacts"] = [self._artifact(
            "pc_capacity_contract", "pc-capacity-final.ppm",
        )]
        RUNNER.validate_final_mgba_case_result(
            "pc_capacity_contract", validated,
        )
        semantic_drift = deepcopy(validated)
        semantic_drift["results"][0]["actual_result"] = 0
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "outcome/hash",
        ):
            RUNNER.validate_final_mgba_case_result(
                "pc_capacity_contract", semantic_drift,
            )
        missing = deepcopy(document)
        missing["results"] = missing["results"][:-1]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "synthetic 4ケース",
        ):
            RUNNER._validate_case(
                missing, "pc_capacity_contract", {}, {}, {}, {},
            )

    def test_party_move_no_match_is_party_size_six_not_0x7f(self) -> None:
        party = {
            "fixture_kind": "PARTY", "count": 0,
            "raw_hex": "00" * 600,
        }
        reference = RUNNER._runner_fixture_key(party)
        registry = {reference: party}
        accepted = RUNNER._normalize_control_required_value(
            "PARTY_MOVE", {
                "move_id": 15, "expected_slot": 6,
                "party_layout_ref": reference,
            }, registry, "party-move",
        )
        self.assertEqual(accepted["expected_slot"], 6)
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "expected_slot",
        ):
            RUNNER._normalize_control_required_value(
                "PARTY_MOVE", {
                    "move_id": 15, "expected_slot": 0x7F,
                    "party_layout_ref": reference,
                }, registry, "party-move",
            )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("uint16_t result = 6U", source)
        self.assertNotIn("uint16_t result = 0x7FU", source)

    def test_giveegg_capacity_requires_exact_zero_one_two_result(self) -> None:
        party = {
            "fixture_kind": "PARTY", "count": 6,
            "raw_hex": "00" * 600,
        }
        storage = {
            "fixture_kind": "STORAGE", "raw_hex": "00" * 0x83D0,
        }
        party_ref = RUNNER._runner_fixture_key(party)
        storage_ref = RUNNER._runner_fixture_key(storage)
        registry = {party_ref: party, storage_ref: storage}
        for expected in range(3):
            normalized = RUNNER._normalize_control_required_value(
                "PARTY_OR_STORAGE_CAPACITY", {
                    "expected_result": expected,
                    "party_layout_ref": party_ref,
                    "storage_layout_ref": storage_ref,
                }, registry, f"giveegg-{expected}",
            )
            self.assertEqual(normalized["expected_result"], expected)
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "required value",
        ):
            RUNNER._normalize_control_required_value(
                "PARTY_OR_STORAGE_CAPACITY", {
                    "expected_result": True,
                    "party_layout_ref": party_ref,
                    "storage_layout_ref": storage_ref,
                }, registry, "giveegg-bool",
            )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("s61_execute_giveegg_opcode", source)
        self.assertIn("actual_script_context_opcode_0x7a", source)

        def giveegg_row(
            case_id: str, outcome: int, before: int, after: int,
            party_delta: int, storage_delta: int, *, current_box: int = 0,
            occupied_slots: set[int] | None = None,
        ) -> dict[str, object]:
            occupied_slots = set() if occupied_slots is None \
                else set(occupied_slots)
            target_kind = "PARTY" if outcome == 0 else (
                "STORAGE" if outcome == 1 else "NONE"
            )
            target_slot = 0 if outcome == 0 else None
            if outcome == 1:
                target_slot = next(
                    box * 30 + position
                    for relative_box in range(14)
                    for box in [(current_box + relative_box) % 14]
                    for position in range(30)
                    if box * 30 + position not in occupied_slots
                )
            destination_box = target_slot // 30 if outcome == 1 else 0
            occupancy = bytearray(53)
            for slot in occupied_slots:
                occupancy[slot // 8] |= 1 << (slot % 8)
            raw_boxmon = (
                "D0FE6CE7D535BE40606F8BFF9F59730000000106"
                "0101010101FF0000000000001900000001000000000A0300"
                "54002D00000000001E280000000000000000000000000000"
                "00FD00028707F94D00000000"
            ) if outcome < 2 else None
            api = [0, 1, 1, 0, 25, 1] if outcome < 2 else None
            return {
                "case_id": case_id, "species": 25,
                "expected_result": outcome, "actual_result": outcome,
                "party_before": before, "party_after": after,
                "party_changed_slots": party_delta,
                "storage_changed_slots": storage_delta,
                "party_before_fnv1a64": "1" * 16,
                "party_after_fnv1a64": (
                    "2" * 16 if party_delta else "1" * 16
                ),
                "storage_before_fnv1a64": "3" * 16,
                "storage_after_fnv1a64": (
                    "4" * 16 if storage_delta else "3" * 16
                ),
                "saveblock1_before_fnv1a64": "5" * 16,
                "saveblock1_after_fnv1a64": (
                    "7" * 16 if destination_box else "5" * 16
                ),
                "pc_box_var_before": 0,
                "pc_box_var_after": destination_box,
                "saveblock1_allowed_mutation_exact": True,
                "saveblock1_delta_offsets": (
                    [RUNNER._GIVEEGG_PC_BOX_VAR_OFFSET]
                    if destination_box else []
                ),
                "saveblock2_normalized_before_fnv1a64": "6" * 16,
                "saveblock2_normalized_after_fnv1a64": "6" * 16,
                "input_recovered": True,
                "rng_seed_before": RUNNER._GIVEEGG_RNG_SEED,
                "rng_state_after": 0x1BF2782A,
                "direct_host_script_run": False,
                "scheduler_dispatcher_observed": True,
                "scheduler_context_enabled_observed": True,
                "scheduler_context_disabled_observed": True,
                "scheduler_lifecycle_exact": True,
                "opcode_handler_entry_count": 1,
                "opcode_handler_entry_rng": RUNNER._GIVEEGG_RNG_SEED,
                "script_pointer_after_setup": "0x0203DF80",
                "script_pointer_at_handler_entry": "0x0203DF81",
                "script_pointer_after_handler": "0x0203DF83",
                "script_pointer_final": "0x00000000",
                "field_callback_before_scheduler": "0x0806E4A1",
                "field_callback_after_scheduler": "0x0806E4A1",
                "player_name_hex": "0101010101FF00",
                "player_gender": 0,
                "player_trainer_id": 0x40BE35D5,
                "storage_header_before_hex": f"{current_box:02X}000000",
                "storage_header_after_hex": f"{current_box:02X}000000",
                "storage_header_byte_exact": True,
                "storage_current_box_before": current_box,
                "storage_occupied_before_count": len(occupied_slots),
                "storage_occupancy_before_hex": occupancy.hex().upper(),
                "controls_released": True,
                "running_state_released": True,
                "tile_transition_released": True,
                "start_pressed": True,
                "start_menu_opened": True,
                "back_pressed": True,
                "callback_ordered": True,
                "field_callback_before": "0x0806E4A1",
                "menu_callback_observed": "0x0806EA75",
                "field_callback_after": "0x0806E4A1",
                "target_kind": target_kind, "target_slot": target_slot,
                "target_box": target_slot // 30 if outcome == 1 else None,
                "target_position": target_slot % 30 if outcome == 1 else None,
                "target_unique": outcome < 2,
                "non_target_party_byte_exact": True,
                "non_target_storage_byte_exact": True,
                "storage_tail_metadata_byte_exact": True,
                "storage_allowed_mutation_exact": True,
                "storage_delta_offsets": (
                    [
                        4 + target_slot * 80 + byte
                        for byte, value in enumerate(bytes.fromhex(raw_boxmon))
                        if value != 0
                    ] if outcome == 1 else []
                ),
                "raw_backup_species": 0,
                "raw_reserved": 0,
                "raw_plaintext_reserved_exact": outcome < 2,
                "raw_bad_egg": False,
                "raw_has_species": outcome < 2,
                "raw_header_is_egg": outcome < 2,
                "raw_boxmon_hex": raw_boxmon,
                "party_extra_hex": (
                    "0000000001FF0B000B0006000400060006000500"
                    if outcome == 0 else None
                ),
                "raw_before_getters_fnv1a64": (
                    "2077AECF7108F27E" if outcome < 2 else "0" * 16
                ),
                "raw_after_getters_fnv1a64": (
                    "2077AECF7108F27E" if outcome < 2 else "0" * 16
                ),
                "raw_unchanged_by_getters": outcome < 2,
                "get_mon_data_observed": outcome == 0,
                "get_box_mon_data_observed": outcome < 2,
                "get_box_mon_data_at_observed": outcome == 1,
                "api_field_ids": [4, 5, 6, 9, 11, 45],
                "get_mon_data_values": api if outcome == 0 else None,
                "get_box_mon_data_values": api,
                "get_box_mon_data_at_values": api if outcome == 1 else None,
                "getter_values_exact": outcome < 2,
            }

        giveegg_document = {
            "schema_version": 7, "status": "PASS",
            "case": "giveegg_result_contract",
            "actual_script_context_opcode_0x7a": True,
            "script_context_run_entry": "0x08069369",
            "giveegg_opcode_handler_entry": "0x0806B845",
            "direct_host_script_run": False,
            "field_scheduler_script_context_run": True,
            "scheduler_lifecycle_all_paths_exact": True,
            "fixed_rng_seed": RUNNER._GIVEEGG_RNG_SEED,
            "base_stats_species25_address": "0x09600320",
            "base_stats_species25_raw_hex": (
                RUNNER._GIVEEGG_BASE_STATS_SPECIES25_HEX
            ),
            "get_mon_data_entry": "0x0803F355",
            "get_box_mon_data_entry": "0x0803F4B1",
            "get_box_mon_data_at_entry": "0x0808B4B5",
            "getter_transaction_single_scheduler_boundary": True,
            "boxmon_storage_layout": "CFRU_JP_PLAINTEXT_80",
            "raw_boxmon_plaintext_and_sanity_exact": True,
            "all_non_target_slots_byte_exact": True,
            "storage_metadata_tail_all_paths_byte_exact": True,
            "storage_allowed_mutation_all_paths_exact": True,
            "saveblock1_pc_destination_var_all_paths_exact": True,
            "current_box_search_variants": 4,
            "synthetic_case_count": 6,
            "results": [
                giveegg_row("giveegg-party-space", 0, 0, 1, 1, 0),
                giveegg_row(
                    "giveegg-party-full-pc-space", 1, 6, 6, 0, 1,
                ),
                giveegg_row(
                    "giveegg-pc-current5-partial", 1, 6, 6, 0, 1,
                    current_box=5,
                    occupied_slots=set(range(5 * 30, 5 * 30 + 12)),
                ),
                giveegg_row(
                    "giveegg-pc-current5-next-box", 1, 6, 6, 0, 1,
                    current_box=5,
                    occupied_slots=set(range(5 * 30, 6 * 30)),
                ),
                giveegg_row(
                    "giveegg-pc-current13-wrap-box0", 1, 6, 6, 0, 1,
                    current_box=13,
                    occupied_slots=set(range(13 * 30, 14 * 30)),
                ),
                giveegg_row(
                    "giveegg-party-pc-full", 2, 6, 6, 0, 0,
                    occupied_slots=set(range(420)),
                ),
            ],
            "fresh_core": True, "field_input_recovered": True,
            "failed": 0, "untested": 0, "warnings": 0,
            "framebuffer_artifacts": [],
        }
        fixtures = RUNNER.validate_fixture_document(
            deepcopy(RUNNER.DEFAULT_FIXTURE_DOCUMENT)
        )
        validated = RUNNER._validate_case(
            giveegg_document, "giveegg_result_contract", fixtures,
            RUNNER._read_charmap(), {}, {},
        )
        self.assertTrue(validated["all_non_target_slots_byte_exact"])
        self.assertTrue(validated["independent_semantic_oracle_exact"])
        self.assertTrue(validated["same_seed_party_pc_boxmon_byte_exact"])
        bad_sanity = deepcopy(giveegg_document)
        bad_sanity["results"][0]["raw_has_species"] = False
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "raw/API contract",
        ):
            RUNNER._validate_case(
                bad_sanity, "giveegg_result_contract", fixtures,
                RUNNER._read_charmap(), {}, {},
            )
        bad_semantic = deepcopy(giveegg_document)
        raw = bytearray.fromhex(bad_semantic["results"][0]["raw_boxmon_hex"])
        raw[32] ^= 1
        bad_semantic["results"][0]["raw_boxmon_hex"] = raw.hex().upper()
        bad_semantic["results"][0]["raw_before_getters_fnv1a64"] = \
            RUNNER._fnv1a64(raw)
        bad_semantic["results"][0]["raw_after_getters_fnv1a64"] = \
            RUNNER._fnv1a64(raw)
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "semantic vector",
        ):
            RUNNER._validate_case(
                bad_semantic, "giveegg_result_contract", fixtures,
                RUNNER._read_charmap(), {}, {},
            )

    def test_save_link_cow_metadata_and_callback_trace_are_bound(self) -> None:
        metadata = json.loads((
            ROOT / "reports/generated/stage61_display_npc_event_audit.json"
        ).read_text(encoding="utf-8"))
        symbols = RUNNER._link_save_cow_runtime_contract(metadata)
        self.assertEqual(set(symbols), {
            "handle_saving", "ensure_backup", "handle_write_sector",
            "update_record", "preflight_callbacks", "stock_callbacks",
            "post_callbacks",
        })
        self.assertEqual(
            (symbols["preflight_callbacks"], symbols["stock_callbacks"],
             symbols["post_callbacks"]),
            (57358, 20485, 57359),
        )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        for evidence in (
            "S61_COW_PREFLIGHT_CALLBACKS = 57358U",
            "S61_COW_STOCK_CALLBACKS = 20485U",
            "S61_COW_POST_CALLBACKS = 57359U",
            "WORLD_PROGRAM_FLASH_SECTOR_PTR = 0x0300746CU",
            "S61_STOCK_PROGRAM_FLASH_SECTOR = 0x081C302DU",
            "S61_STOCK_INTERNAL_PROGRAM_FLASH_BYTE = 0x081C2FF5U",
            "s61_cow_callback_invariants",
            "s61_cow_stock_program_sector_return_invariants",
            "s61_cow_raw_selected_counter",
            "s61_cow_run_checkpoint_fault",
            "checkpoint_without_prefix_reexecution",
            "real_callback_executed_to_return",
            "return_status_replaced_before_caller",
            "S61_ENSURE_BACKUP_GENERATION_SYMBOL",
            "enum S61CowSilentSuccessMode",
            "ERASE_SILENT_SUCCESS_NO_EFFECT",
            "PROGRAM_NO_OP_SUCCESS",
            "PROGRAM_WRONG_BYTE_SUCCESS",
            "s61_cow_run_silent_success_fault",
            "physical_readback_rejected",
            "silent_success_fault_injection",
            "savedata->settling != local_sector",
            "savedata->settling = local_sector",
        ):
            self.assertIn(evidence, source)

    def test_default_state_matrix_is_builder_full_arbitrary_case_source(self) -> None:
        path = ROOT / RUNNER.DEFAULT_STATE_MATRIX
        self.assertTrue(path.is_file(), path)
        document = json.loads(path.read_text(encoding="utf-8"))
        count = document["counts"]["matrix_case_count"]
        self.assertGreater(count, 0)
        self.assertEqual(len(document["cases"]), count)
        self.assertEqual(
            document["counts"]["interactive_case_count"]
            + document["counts"]["hidden_assertion_count"],
            count,
        )

    def test_map_popup_builder_fixture_has_exact_seven_physical_maps(
        self,
    ) -> None:
        source = self._generated_fixture_source()
        fixture = RUNNER.validate_fixture_document(source)
        popup = fixture["map_popup_regressions"]
        self.assertEqual(
            {(row["group"], row["map"]) for row in popup["cases"]},
            {
                (97, 36), (97, 37), (97, 38),
                (1, 36), (1, 37), (1, 38), (1, 73),
            },
        )
        self.assertEqual(
            {
                row["physical_provenance"]
                for row in popup["cases"] if row["group"] == 97
            },
            {"IMPORTED_KANTO_CANONICAL"},
        )
        self.assertEqual(
            {
                row["physical_provenance"]
                for row in popup["cases"] if row["group"] == 1
            },
            {"VEGA_STOCK_PHYSICAL"},
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "popup.tsv"
            RUNNER.write_map_popup_tsv(path, popup)
            lines = path.read_text(encoding="ascii").splitlines()
        self.assertEqual(len(lines), 8)
        self.assertEqual(lines[0] + "\n", RUNNER._MAP_POPUP_TSV_HEADER)
        self.assertTrue(all(len(line.split("\t")) == 19 for line in lines[1:]))
        diglett = fixture["diglett_b1f_natural_interaction"]
        self.assertEqual(diglett["walk_step_count"], len(
            diglett["walk_key_sequence"]
        ))
        self.assertEqual(
            diglett["walk_tiles"][0], diglett["stock_warp"]["arrival_tile"],
        )
        self.assertEqual(diglett["walk_tiles"][-1], diglett["stance"])
        source_text = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("fresh_core_per_map", source_text)
        self.assertIn("actual incoming warp was not traversed", source_text)

    def test_catalog_rejects_unbound_rom_no_expectation_and_illegal_port(self) -> None:
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "ROM SHA-256"):
            RUNNER.validate_catalog_document(
                self._catalog(), expected_rom_sha256="1" * 64,
            )

        no_expectation = self._catalog()
        branch = no_expectation["entries"][0]["branches"][0]  # type: ignore[index]
        branch["expected_utf8_contains_any"] = []  # type: ignore[index]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "期待表示根拠"):
            RUNNER.validate_catalog_document(no_expectation)

        illegal_port = self._catalog()
        illegal_execution = illegal_port["entries"][0][  # type: ignore[index]
            "interaction_execution"
        ]
        illegal_execution["start"] = [14, 71]  # type: ignore[index]
        illegal_execution["stance"] = [14, 70]  # type: ignore[index]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "object距離"):
            RUNNER.validate_catalog_document(illegal_port)

    def test_conditional_runtime_position_contract_is_fail_closed(self) -> None:
        group, map_number = 1, 74
        owner_key = "OBJECT:001/074:000"
        expected = RUNNER._RUNTIME_POSITION_EXPECTED_CONTROLS[
            (group, map_number)
        ]
        static_object = [10, 10]
        runtime_object = [11, 10]
        template_raw = self._object_template_raw(
            local_id=1, graphics_id=18,
            x=static_object[0], y=static_object[1],
            movement_type=9, script_pointer=0x08100000,
        )

        def execution(position: list[int]) -> dict[str, object]:
            return self._physical_interaction_execution(
                start=[position[0], position[1] + 2],
                walk_sequence=["UP"],
                stance=[position[0], position[1] + 1],
                action="UP",
            )

        contract = {
            "kind": "CONDITIONAL_MAP_SCRIPT_RUNTIME_POSITION",
            "root": f"0x{expected['root']:08X}",
            "map_script_tag": 3,
            "control": {
                key: deepcopy(value) for key, value in expected.items()
                if key not in {"root", "owner_count"}
            },
            "variants": [{
                "variant_id": "STATIC",
                "object": static_object,
                "state": {
                    "flags": [{
                        "id": expected["id"], "value": False,
                        "reason": (
                            "MAP_TAG3_RUNTIME_POSITION_CONDITION_STATIC"
                        ),
                    }],
                    "vars": [],
                },
                "baseline": True,
                "interaction_execution": execution(static_object),
            }, {
                "variant_id": "RUNTIME",
                "object": runtime_object,
                "state": {
                    "flags": [{
                        "id": expected["id"], "value": True,
                        "reason": (
                            "MAP_TAG3_RUNTIME_POSITION_CONDITION_RUNTIME"
                        ),
                    }],
                    "vars": [],
                },
                "baseline": False,
                "interaction_execution": execution(runtime_object),
            }],
            "setobjectxyperm_instruction_addresses": ["0x08100000"],
            "root_prefix_hex": "00",
            "assertions": {
                "all_setobjectxyperm_writes_accounted": True,
                "static_and_runtime_positions_distinct": True,
            },
        }
        normalized = RUNNER._normalize_legacy_runtime_position_contract(
            contract, npc_id=owner_key,
            group=group, map_number=map_number,
            runtime_object=runtime_object,
            expected_template_raw_hex=template_raw,
            local_id=1, shadow=None,
        )
        self.assertEqual(
            [row["variant_id"] for row in normalized["variants"]],
            ["STATIC", "RUNTIME"],
        )
        self.assertEqual(normalized["variants"][0]["object"], static_object)
        self.assertEqual(normalized["variants"][1]["object"], runtime_object)

        contract_mutations = {
            "missing-runtime": lambda item: item["variants"].pop(),
            "runtime-object": lambda item: item["variants"][1].__setitem__(
                "object", static_object,
            ),
            "runtime-control": lambda item: item["control"].__setitem__(
                "runtime_value", False,
            ),
            "runtime-state": lambda item: item["variants"][1][
                "state"
            ]["flags"][0].__setitem__("value", False),
            "runtime-walk": lambda item: item["variants"][1][
                "interaction_execution"
            ].__setitem__("walk_sequence", []),
        }
        for label, mutate in contract_mutations.items():
            broken = deepcopy(contract)
            mutate(broken)
            with self.subTest(position_contract=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._normalize_legacy_runtime_position_contract(
                    broken, npc_id=owner_key,
                    group=group, map_number=map_number,
                    runtime_object=runtime_object,
                    expected_template_raw_hex=template_raw,
                    local_id=1, shadow=None,
                )

        control = {
            "kind": "FLAG", "id": expected["id"], "value": True,
        }
        self.assertEqual(
            RUNNER._validate_runtime_position_control(
                control, required=True, label="unit-runtime-control",
                state={
                    "flags": [{"id": expected["id"], "value": True}],
                    "vars": [],
                },
            ),
            control,
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "control/state",
        ):
            RUNNER._validate_runtime_position_control(
                control, required=True, label="unit-runtime-control",
                state={
                    "flags": [{"id": expected["id"], "value": False}],
                    "vars": [],
                },
            )

        dex_expected = RUNNER._RUNTIME_POSITION_EXPECTED_CONTROLS[(2, 34)]
        dex_control = {"kind": "NATIONAL_DEX", "id": 0, "value": False}
        self.assertEqual(
            RUNNER._validate_runtime_position_control(
                dex_control, required=True, label="unit-runtime-dex",
                state={
                    "flags": [{"id": 0x0840, "value": False}],
                    "vars": [{"id": 0x404E, "value": 0}],
                },
            ),
            dex_control,
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "NATIONAL_DEX control/state",
        ):
            RUNNER._validate_runtime_position_control(
                dex_control, required=True, label="unit-runtime-dex",
                state={
                    "flags": [{"id": 0x0840, "value": False}],
                    "vars": [{"id": 0x404E, "value": 0x6258}],
                },
            )

        record_raw = bytes(range(8))
        producer = {
            "kind": "STOCK_WARP", "root": expected["root"],
            "source_group": 1, "source_map": 73, "source_warp": 0,
            "predecessor_x": 5, "predecessor_y": 6,
            "trigger_x": 5, "trigger_y": 5,
            "trigger_key": RUNNER.KEYS["UP"],
            "destination_group": group,
            "destination_map": map_number,
            "destination_warp": 0,
            "arrival_x": 10, "arrival_y": 10,
            "record_address": 0x08100000,
            "map_script_tag": 3,
            "event_case_id": "runtime-position-unit",
            "source_provenance": {
                "record_address": "0x08100000",
                "record_raw_hex": record_raw.hex(),
                "record_raw_sha256": hashlib.sha256(record_raw).hexdigest(),
            },
        }
        self.assertEqual(
            RUNNER._validate_runtime_position_producer(
                producer, group=group, map_number=map_number,
                required=True, label="unit-runtime-producer",
            ),
            producer,
        )
        interaction = {
            "group": group, "map": map_number,
            "object": runtime_object,
            "expected_template_raw_hex": template_raw,
            "runtime_position_map_load_required": True,
            "runtime_position_control": control,
        }
        row = {
            "owner_key": owner_key,
            "state": {
                "flags": [{"id": expected["id"], "value": True}],
                "vars": [],
            },
            "runtime_position_producer": producer,
        }
        self.assertEqual(len(RUNNER._runtime_position_control_tsv_fields(
            row, interaction, "runtime-position-unit",
        )), 3)
        self.assertEqual(len(RUNNER._runtime_position_producer_tsv_fields(
            row, interaction, "runtime-position-unit",
        )), 19)

        producer_mutations = {
            "root": lambda item: item.__setitem__(
                "root", expected["root"] + 2,
            ),
            "physical-step": lambda item: item.__setitem__("trigger_y", 4),
            "record-hash": lambda item: item["source_provenance"].__setitem__(
                "record_raw_sha256", "0" * 64,
            ),
            "destination": lambda item: item.__setitem__(
                "destination_map", map_number + 1,
            ),
        }
        for label, mutate in producer_mutations.items():
            broken = deepcopy(producer)
            mutate(broken)
            with self.subTest(position_producer=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._validate_runtime_position_producer(
                    broken, group=group, map_number=map_number,
                    required=True, label="unit-runtime-producer",
                )

        observation_fixture = {
            "runtime_position_producer": producer,
            "runtime_position_control": control,
        }
        observation = self._runtime_position_observation(
            producer, control, requested=[11, 12], visible=True,
        )
        self.assertEqual(
            observation["local_player_positioning"][
                "host_coordinate_reposition_calls"
            ],
            2,
        )
        self.assertTrue(RUNNER._validate_catalog_runtime_position_observation(
            observation, observation_fixture,
            label="unit-runtime-observation", host_prepare_control=True,
            expected_visible=True, expected_interaction=True,
            actual_walk_required=True, requested_start=[11, 12],
        )["exact"])
        observation_mutations = {
            "logical-root-count": lambda item: item.__setitem__(
                "root_dispatch_callsite_hits", 2,
            ),
            "raw-root-join": lambda item: item.__setitem__(
                "all_map_script_executor_raw_hits", 3,
            ),
            "control-write": lambda item: item[
                "runtime_position_control"
            ].__setitem__("host_write_count", 0),
            "deferred-walk": lambda item: item.__setitem__(
                "target_materialization_deferred_to_real_walk", False,
            ),
            "host-branch-write": lambda item: item[
                "local_player_positioning"
            ].__setitem__("host_branch_state_writes", 1),
            "jp-position-api": lambda item: item[
                "local_player_positioning"
            ].__setitem__("move_player_to_map_coords_entry", "0x0805BFD8"),
            "missing-coordinate-api-count": lambda item: item[
                "local_player_positioning"
            ].pop("host_coordinate_reposition_calls"),
            "wrong-coordinate-api-count": lambda item: item[
                "local_player_positioning"
            ].__setitem__("host_coordinate_reposition_calls", 0),
            "boolean-coordinate-api-count": lambda item: item[
                "local_player_positioning"
            ].__setitem__("host_coordinate_reposition_calls", True),
        }
        for label, mutate in observation_mutations.items():
            broken = deepcopy(observation)
            mutate(broken)
            with self.subTest(runtime_observation=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._validate_catalog_runtime_position_observation(
                    broken, observation_fixture,
                    label="unit-runtime-observation",
                    host_prepare_control=True, expected_visible=True,
                    expected_interaction=True, actual_walk_required=True,
                    requested_start=[11, 12],
                )

        hidden_observation = self._runtime_position_observation(
            producer, control, requested=[11, 12], visible=False,
        )
        RUNNER._validate_catalog_runtime_position_observation(
            hidden_observation, observation_fixture,
            label="unit-runtime-hidden", host_prepare_control=True,
            expected_visible=False, expected_interaction=False,
            actual_walk_required=True, requested_start=[11, 12],
        )
        transiently_visible_hidden = deepcopy(hidden_observation)
        transiently_visible_hidden["target_materialized_before_walk"] = True
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "walk前materialization",
        ):
            RUNNER._validate_catalog_runtime_position_observation(
                transiently_visible_hidden, observation_fixture,
                label="unit-runtime-hidden", host_prepare_control=True,
                expected_visible=False, expected_interaction=False,
                actual_walk_required=True, requested_start=[11, 12],
            )

        visible_without_walk = self._runtime_position_observation(
            producer, control, requested=[11, 12], visible=True,
            before_walk=True,
        )
        RUNNER._validate_catalog_runtime_position_observation(
            visible_without_walk, observation_fixture,
            label="unit-runtime-visible-no-walk", host_prepare_control=True,
            expected_visible=True, expected_interaction=False,
            actual_walk_required=False, requested_start=[11, 12],
        )
        missing_before_unwalked = deepcopy(visible_without_walk)
        missing_before_unwalked["target_materialized_before_walk"] = False
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "walk前materialization",
        ):
            RUNNER._validate_catalog_runtime_position_observation(
                missing_before_unwalked, observation_fixture,
                label="unit-runtime-visible-no-walk",
                host_prepare_control=True, expected_visible=True,
                expected_interaction=False, actual_walk_required=False,
                requested_start=[11, 12],
            )

        boolean_coordinate = deepcopy(observation)
        boolean_coordinate["source"]["warp_id"] = True
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "source.warp_id",
        ):
            RUNNER._validate_catalog_runtime_position_observation(
                boolean_coordinate, observation_fixture,
                label="unit-runtime-observation",
                host_prepare_control=True, expected_visible=True,
                expected_interaction=True, actual_walk_required=True,
                requested_start=[11, 12],
            )

        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "非条件owner",
        ):
            RUNNER._validate_runtime_position_producer(
                producer, group=group, map_number=map_number,
                required=False, label="unit-static-producer",
            )

        none_producer = RUNNER._none_runtime_position_producer(96, 23)
        none_control = RUNNER._none_runtime_position_control()
        none_observation = self._runtime_position_observation(
            none_producer, none_control,
            requested=[14, 72], visible=True,
        )
        RUNNER._validate_catalog_runtime_position_observation(
            none_observation, {
                "runtime_position_producer": none_producer,
                "runtime_position_control": none_control,
            }, label="unit-none-runtime-observation",
            host_prepare_control=True, expected_visible=True,
            expected_interaction=True, actual_walk_required=True,
            requested_start=[14, 72],
        )
        broken_none = deepcopy(none_observation)
        broken_none["runtime_position_control"]["exact"] = False
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "control",
        ):
            RUNNER._validate_catalog_runtime_position_observation(
                broken_none, {
                    "runtime_position_producer": none_producer,
                    "runtime_position_control": none_control,
                }, label="unit-none-runtime-observation",
                host_prepare_control=True, expected_visible=True,
                expected_interaction=True, actual_walk_required=True,
                requested_start=[14, 72],
            )

        engine_producer = {
            "kind": "ENGINE_TELEPORT", "root": dex_expected["root"],
            "source_group": 0, "source_map": 0, "source_warp": 255,
            "predecessor_x": 12, "predecessor_y": 13,
            "trigger_x": 12, "trigger_y": 13, "trigger_key": 0,
            "destination_group": 2, "destination_map": 34,
            "destination_warp": 255,
            "arrival_x": 12, "arrival_y": 13,
            "record_address": 0, "map_script_tag": 3,
            "event_case_id": "runtime-position-engine-unit",
            "source_provenance": {
                "incoming_usable_zero_reason_bound": True,
                "foreign_stock_warp_scan": {
                    "usable_stock_warp_count": 0,
                },
                "usable_stock_connection_count": 0,
            },
        }
        RUNNER._validate_runtime_position_producer(
            engine_producer, group=2, map_number=34,
            required=True, label="unit-runtime-engine-producer",
        )
        engine_observation = self._runtime_position_observation(
            engine_producer, dex_control,
            requested=[12, 13], visible=True, host_prepare=False,
        )
        self.assertEqual(
            engine_observation["local_player_positioning"][
                "host_coordinate_reposition_calls"
            ],
            0,
        )
        RUNNER._validate_catalog_runtime_position_observation(
            engine_observation, {
                "runtime_position_producer": engine_producer,
                "runtime_position_control": dex_control,
            }, label="unit-runtime-engine-observation",
            host_prepare_control=False, expected_visible=True,
            expected_interaction=True, actual_walk_required=True,
            requested_start=[12, 13],
        )
        forged_engine_reposition = deepcopy(engine_observation)
        forged_engine_reposition["local_player_positioning"][
            "host_coordinate_reposition_calls"
        ] = 2
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "coordinate API count",
        ):
            RUNNER._validate_catalog_runtime_position_observation(
                forged_engine_reposition, {
                    "runtime_position_producer": engine_producer,
                    "runtime_position_control": dex_control,
                }, label="unit-runtime-engine-observation",
                host_prepare_control=False, expected_visible=True,
                expected_interaction=True, actual_walk_required=True,
                requested_start=[12, 13],
            )
        for label, mutate in {
            "stock-warp-exists": lambda item: item[
                "source_provenance"
            ]["foreign_stock_warp_scan"].__setitem__(
                "usable_stock_warp_count", 1,
            ),
            "connection-exists": lambda item: item[
                "source_provenance"
            ].__setitem__("usable_stock_connection_count", 1),
            "arrival": lambda item: item.__setitem__("arrival_x", 11),
        }.items():
            broken = deepcopy(engine_producer)
            mutate(broken)
            with self.subTest(engine_producer=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._validate_runtime_position_producer(
                    broken, group=2, map_number=34,
                    required=True, label="unit-runtime-engine-producer",
                )

        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("bool arrival_is_requested =", source)
        self.assertIn("if (!arrival_is_requested) {", source)
        self.assertEqual(
            source.count(
                "++observation->host_coordinate_reposition_calls;"
            ),
            2,
        )
        self.assertIn(
            "== (arrival_is_requested ? 0U : 2U)", source,
        )

    def test_state_matrix_runtime_position_pair_is_fail_closed(self) -> None:
        matrix = self._state_matrix()
        expected = RUNNER._RUNTIME_POSITION_EXPECTED_CONTROLS[(1, 74)]

        def variant_case(
            variant_id: str, position: list[int], value: bool,
        ) -> dict[str, object]:
            row = deepcopy(matrix["cases"][0])
            row.update({
                "case_id": (
                    "matrix-001-074-000-default-position-"
                    f"{variant_id.lower()}"
                ),
                "base_case_id": "runtime-position-owner-001-074-000",
                "owner_key": "OBJECT:001/074:000",
                "catalog_branch": "DEFAULT",
                "interaction": {
                    "group": 1, "map": 74, "object_index": 0,
                    "local_id": 1, "object": position,
                    "runtime_root": "0x08100000",
                },
                "interaction_execution": (
                    self._physical_interaction_execution(
                        start=[position[0], position[1] + 2],
                        walk_sequence=["UP"],
                        stance=[position[0], position[1] + 1], action="UP",
                    )
                ),
                "runtime_position_variant": {
                    "variant_id": variant_id,
                    "control": {
                        "kind": "FLAG", "id": expected["id"],
                        "value": value,
                    },
                },
                "runtime_position_map_load_required": True,
                "state": {
                    "flags": [{"id": expected["id"], "value": value}],
                    "vars": [], "items": [], "trainers": [],
                },
                "expected_object_visible": True,
                "interaction_expected": True,
                "choice_candidates": ["ADVANCE"],
                "expected_terminal": "CALIBRATE",
            })
            for key in (
                "input_sequences", "allowed_post_effect_families",
                "allowed_post_effects", "control_requirements",
            ):
                row.pop(key, None)
            return row

        matrix["cases"].extend([
            variant_case("STATIC", [10, 10], False),
            variant_case("RUNTIME", [11, 10], True),
        ])
        matrix["counts"].update({
            "matrix_case_count": 4,
            "interactive_case_count": 3,
            "hidden_assertion_count": 1,
            "runtime_position_conditioned_owner_count": 1,
            "runtime_position_variant_case_count": 2,
            "runtime_position_expanded_case_count": 2,
        })
        matrix["assertions"].update({
            "all_runtime_position_variants_expanded_exactly_once": True,
            "all_runtime_position_base_cases_survive_runtime_expansion": True,
        })
        _, rows = RUNNER.validate_state_matrix_document(
            matrix, expected_rom_sha256="0" * 64,
        )
        static = rows[
            "matrix-001-074-000-default-position-static"
        ]
        runtime = rows[
            "matrix-001-074-000-default-position-runtime"
        ]
        self.assertEqual(static["object"], [10, 10])
        self.assertEqual(runtime["object"], [11, 10])
        self.assertFalse(
            static["runtime_position_variant"]["control"]["value"]
        )
        self.assertTrue(
            runtime["runtime_position_variant"]["control"]["value"]
        )
        base_phase = deepcopy(matrix)
        base_phase["assertions"].pop(
            "all_runtime_position_base_cases_survive_runtime_expansion"
        )
        RUNNER.validate_state_matrix_document(
            base_phase, expected_rom_sha256="0" * 64,
        )
        expanded_without_survival = deepcopy(base_phase)
        expanded_without_survival["runtime_control_expansion"] = {
            "phase": "CONTROL_EXPANDED_ORACLE_CASE_BINDING_REQUIRED",
        }
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "runtime position owner coverage",
        ):
            RUNNER.validate_state_matrix_document(
                expanded_without_survival,
                expected_rom_sha256="0" * 64,
            )

        matrix_mutations = {
            "pair-base": lambda item: item["cases"][3].__setitem__(
                "base_case_id", "runtime-position-owner-drift",
            ),
            "control-state": lambda item: item["cases"][3]["state"][
                "flags"
            ][0].__setitem__("value", False),
            "physical-execution": lambda item: item["cases"][2][
                "interaction_execution"
            ].__setitem__("walk_sequence", []),
            "variant-count": lambda item: item["counts"].__setitem__(
                "runtime_position_variant_case_count", 1,
            ),
            "owner-count": lambda item: item["counts"].__setitem__(
                "runtime_position_conditioned_owner_count", 2,
            ),
            "required-column": lambda item: item["runner_projection"][
                "required_columns"
            ].remove("runtime_position_control"),
            "ordinary-execution": lambda item: item["cases"][0][
                "interaction_execution"
            ].__setitem__("stance", [14, 72]),
        }
        for label, mutate in matrix_mutations.items():
            broken = deepcopy(matrix)
            mutate(broken)
            with self.subTest(matrix_position=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER.validate_state_matrix_document(
                    broken, expected_rom_sha256="0" * 64,
                )

    def test_engine_runtime_position_rebinds_start_and_final_layout_block(
        self,
    ) -> None:
        rom = (ROOT / RUNNER.DEFAULT_ROM).read_bytes()
        rom_sha256 = hashlib.sha256(rom).hexdigest()
        seed_provenance = self._engine_teleport_provenance(2, 34)
        seed_provenance["rom_sha256"] = rom_sha256
        seed_provenance.update(RUNNER._runtime_position_engine_geometry(
            rom, group=2, map_number=34, start=[5, 3], layout_id=318,
        ))
        root = RUNNER._RUNTIME_POSITION_EXPECTED_CONTROLS[(2, 34)]["root"]
        trigger = RUNNER._normalize_event_trigger_path({
            "kind": "MAP_TRANSITION_LOAD", "group": 2, "map": 34,
            "root_subkind": "DIRECT", "map_script_tag": 3,
            "entry": (
                "STOCK_WARP_OR_CONNECTION_OR_ENGINE_TELEPORT_OR_"
                "RESUME_CALLBACK"
            ),
            "root_pc": f"0x{root:08X}",
            "engine_teleport": {
                "kind": "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
                "destination": {"group": 2, "map": 34},
                "start_tile": {"x": 5, "y": 3},
                "engine_entry": "BOOTSTRAP_KANTO_WARP",
                "source_provenance": seed_provenance,
            },
        }, "runtime-position-layout-unit")
        event_rows = {
            "runtime-position-layout-unit": {"trigger_path": trigger},
        }
        template_raw = self._object_template_raw(
            local_id=1, graphics_id=18, x=23, y=2,
            movement_type=9, script_pointer=0x08100000,
        )

        def fixture(
            *, case_id: str, variant: str, control_value: bool,
            start: list[int], object_position: list[int],
        ) -> dict[str, dict[str, object]]:
            control = {
                "kind": "NATIONAL_DEX", "id": 0,
                "value": control_value,
            }
            return {case_id: {
                "owner_key": "OBJECT:002/034:000",
                "runtime_position_variant": {
                    "variant_id": variant, "control": deepcopy(control),
                },
                "interaction": {
                    "group": 2, "map": 34, "object": object_position,
                    "start": start,
                    "expected_template_raw_hex": template_raw,
                    "runtime_position_map_load_required": True,
                    "runtime_position_control": control,
                },
            }}

        runtime = RUNNER.attach_catalog_runtime_position_producers(
            fixture(
                case_id="runtime-layout-318", variant="RUNTIME",
                control_value=False, start=[5, 3], object_position=[6, 3],
            ), event_rows, rom_raw=rom, rom_sha256=rom_sha256,
        )["runtime-layout-318"]["runtime_position_producer"]
        self.assertEqual(
            [runtime["predecessor_x"], runtime["predecessor_y"]], [5, 3],
        )
        self.assertEqual(
            [runtime["trigger_x"], runtime["trigger_y"]], [5, 3],
        )
        self.assertEqual(
            [runtime["arrival_x"], runtime["arrival_y"]], [5, 3],
        )
        self.assertEqual(
            runtime["source_provenance"]["layout_address"], "0x083092A8",
        )
        self.assertEqual(
            runtime["source_provenance"]["block_raw_hex"], "8132",
        )

        static = RUNNER.attach_catalog_runtime_position_producers(
            fixture(
                case_id="static-layout-319", variant="STATIC",
                control_value=True, start=[23, 1], object_position=[23, 2],
            ), event_rows, rom_raw=rom, rom_sha256=rom_sha256,
        )["static-layout-319"]["runtime_position_producer"]
        self.assertEqual(
            [static["arrival_x"], static["arrival_y"]], [23, 1],
        )
        self.assertEqual(
            static["source_provenance"]["layout_address"], "0x08309470",
        )
        self.assertEqual(
            static["source_provenance"]["block_raw_hex"], "db32",
        )

        wrong_variant = fixture(
            case_id="wrong-layout-control", variant="STATIC",
            control_value=False, start=[5, 3], object_position=[6, 3],
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "variant/control",
        ):
            RUNNER.attach_catalog_runtime_position_producers(
                wrong_variant, event_rows,
                rom_raw=rom, rom_sha256=rom_sha256,
            )

        missing_variant = fixture(
            case_id="missing-layout-variant", variant="RUNTIME",
            control_value=False, start=[5, 3], object_position=[6, 3],
        )
        missing_variant["missing-layout-variant"].pop(
            "runtime_position_variant",
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "variant欠落",
        ):
            RUNNER.attach_catalog_runtime_position_producers(
                missing_variant, event_rows,
                rom_raw=rom, rom_sha256=rom_sha256,
            )

        legacy_runtime = fixture(
            case_id="legacy-runtime-layout", variant="RUNTIME",
            control_value=False, start=[5, 3], object_position=[6, 3],
        )
        legacy_row = legacy_runtime["legacy-runtime-layout"]
        legacy_row.pop("runtime_position_variant")
        legacy_interaction = legacy_row.pop("interaction")
        for key in (
            "group", "map", "object", "expected_template_raw_hex",
            "runtime_position_map_load_required", "runtime_position_control",
        ):
            legacy_row[key] = deepcopy(legacy_interaction[key])
        legacy_execution = {
            "normalized_legacy_runtime": True,
            "start": deepcopy(legacy_interaction["start"]),
        }
        legacy_row["interaction_execution"] = legacy_execution
        legacy_row["runtime_position_state_contract"] = {
            "control": {
                "kind": "NATIONAL_DEX", "id": 0,
                "runtime_value": False, "static_value": True,
            },
            "variants": [
                {
                    "variant_id": "STATIC",
                    "interaction_execution": {
                        "normalized_legacy_static": True,
                    },
                },
                {
                    "variant_id": "RUNTIME",
                    "interaction_execution": legacy_execution,
                },
            ],
        }
        legacy_producer = RUNNER.attach_catalog_runtime_position_producers(
            legacy_runtime, event_rows, rom_raw=rom, rom_sha256=rom_sha256,
        )["legacy-runtime-layout"]["runtime_position_producer"]
        self.assertEqual(
            legacy_producer["source_provenance"]["layout_address"],
            "0x083092A8",
        )

        missing_variant_control = fixture(
            case_id="missing-variant-control", variant="RUNTIME",
            control_value=False, start=[5, 3], object_position=[6, 3],
        )
        missing_variant_control["missing-variant-control"][
            "runtime_position_variant"
        ].pop("control")
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "variant欠落",
        ):
            RUNNER.attach_catalog_runtime_position_producers(
                missing_variant_control, event_rows,
                rom_raw=rom, rom_sha256=rom_sha256,
            )

        missing_layout_control = fixture(
            case_id="missing-layout-control", variant="RUNTIME",
            control_value=False, start=[5, 3], object_position=[6, 3],
        )
        missing_layout_control["missing-layout-control"]["interaction"].pop(
            "runtime_position_control",
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "layout-control",
        ):
            RUNNER.attach_catalog_runtime_position_producers(
                missing_layout_control, event_rows,
                rom_raw=rom, rom_sha256=rom_sha256,
            )

        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "final ROM SHA",
        ):
            RUNNER.attach_catalog_runtime_position_producers(
                fixture(
                    case_id="wrong-rom-sha", variant="RUNTIME",
                    control_value=False, start=[5, 3], object_position=[6, 3],
                ), event_rows, rom_raw=rom, rom_sha256="0" * 64,
            )

        # Every other dynamic map resolves its final map-header layout;
        # Dunsparce Tunnel's 318/319 override must not leak to map 2/35.
        other_control = {"kind": "FLAG", "id": 0x0849, "value": True}
        self.assertIsNone(RUNNER._runtime_position_engine_layout_id(
            {"runtime_position_variant": {
                "variant_id": "RUNTIME", "control": other_control,
            }}, {"runtime_position_control": other_control},
            group=2, map_number=35, label="map-header-layout-unit",
        ))
        map_header_geometry = RUNNER._runtime_position_engine_geometry(
            rom, group=2, map_number=35, start=[7, 2], layout_id=None,
        )
        self.assertEqual(
            map_header_geometry["layout_address"], "0x0830BD04",
        )

        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "provenance",
        ):
            RUNNER._validate_runtime_position_producer(
                runtime, group=2, map_number=34, required=True,
                label="runtime-layout-wrong-id", rom_raw=rom,
                rom_sha256=rom_sha256, expected_engine_start=[5, 3],
                engine_layout_id=319,
            )
        mutated = bytearray(rom)
        block_offset = (
            int(runtime["source_provenance"]["block_address"], 16)
            - RUNNER._RUNTIME_POSITION_GBA_BASE
        )
        mutated[block_offset] ^= 1
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "provenance",
        ):
            RUNNER._validate_runtime_position_producer(
                runtime, group=2, map_number=34, required=True,
                label="runtime-layout-mutated-block", rom_raw=bytes(mutated),
                rom_sha256=rom_sha256, expected_engine_start=[5, 3],
                engine_layout_id=318,
            )

    def test_required_postconditions_strict_nested_schema(self) -> None:
        required = deepcopy(
            self._state_matrix()["cases"][0]["input_sequences"][0][
                "required_postconditions"
            ]
        )
        self.assertEqual(
            RUNNER._normalize_required_postconditions(required, "unit"),
            required,
        )
        mutations = {
            "top-extra": lambda value: value.update({"extra": []}),
            "flag-extra": lambda value: value["flags"][0].update({
                "extra": 0,
            }),
            "var-gap": lambda value: value["vars"][0].update({
                "id": 0x4100,
            }),
            "item-overflow": lambda value: value["items"][0].update({
                "count": 1000,
            }),
            "object-active": lambda value: value["objects"].append({
                "local_id": 15,
                "after": {
                    "active": True, "map": "96/23",
                    "invisible": False, "visible": True,
                    "current": [21, 77], "previous": [21, 77],
                },
            }),
            "battle-partial": lambda value: value.update({
                "battle": {"active": True},
            }),
            "party-extra": lambda value: value.update({
                "party": {
                    "count": 1, "changed_slots": [0],
                    "after_fnv1a64": "A" * 16, "extra": 0,
                },
            }),
            "party-legacy-fnv": lambda value: value.update({
                "party": {
                    "count": 1, "changed_slots": [0],
                    "after_fnv1a64": "A" * 16,
                },
            }),
            "storage-legacy-fnv": lambda value: value.update({
                "storage": {
                    "changed": True, "after_fnv1a64": "B" * 16,
                },
            }),
        }
        for label, mutate in mutations.items():
            broken = deepcopy(required)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._normalize_required_postconditions(broken, label)

    def test_party_storage_raw_sha_contract_rejects_legacy_fingerprints(
        self,
    ) -> None:
        required = deepcopy(
            self._state_matrix()["cases"][0]["input_sequences"][0][
                "required_postconditions"
            ]
        )
        required["party"] = {
            "count": 6, "raw_sha256": "c" * 64,
            "raw_byte_length": 600,
        }
        required["storage"] = {
            "raw_sha256": "d" * 64, "raw_byte_length": 0x83D0,
        }
        normalized = RUNNER._normalize_required_postconditions(
            required, "raw-sha-positive",
        )
        self.assertEqual(normalized["party"], required["party"])
        self.assertEqual(normalized["storage"], required["storage"])

        legacy_party = deepcopy(required)
        legacy_party["party"] = {
            "count": 6, "changed_slots": [0],
            "after_fnv1a64": "A" * 16,
        }
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "required.party schema",
        ):
            RUNNER._normalize_required_postconditions(
                legacy_party, "legacy-party-fnv",
            )
        legacy_storage = deepcopy(required)
        legacy_storage["storage"] = {
            "changed": True, "after_fnv1a64": "B" * 16,
        }
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "required.storage schema",
        ):
            RUNNER._normalize_required_postconditions(
                legacy_storage, "legacy-storage-fnv",
            )

        effects = self._catalog_side_effects()
        effects["party"]["raw_sha256_after"] = "c" * 64
        effects["coverage"]["party"]["raw_sha256_after"] = "c" * 64
        effects["storage"]["changed"] = True
        effects["storage"]["raw_sha256_after"] = "d" * 64
        effects["coverage"]["storage"]["raw_sha256_after"] = "d" * 64
        validated = RUNNER._validate_catalog_side_effects(
            effects, case_id="raw-sha-runtime", expected_map="96/23",
            expected_visible=True, expected_local_id=15,
            battle_terminal=False,
        )
        self.assertEqual(validated["party"]["raw_byte_length"], 600)
        self.assertEqual(
            validated["storage"]["raw_byte_length"], 0x83D0,
        )
        old_result = deepcopy(effects)
        old_result["party"] = {
            "count_before": 6, "count_after": 6,
            "before_fnv1a64": "A" * 16,
            "after_fnv1a64": "B" * 16,
            "slot_hashes_before": ["A" * 16] * 6,
            "slot_hashes_after": ["B" * 16] * 6,
            "changed_slots": list(range(6)),
        }
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "party schema",
        ):
            RUNNER._validate_catalog_side_effects(
                old_result, case_id="legacy-runtime-fnv",
                expected_map="96/23", expected_visible=True,
                expected_local_id=15, battle_terminal=False,
            )

    def test_map_lifecycle_phase_and_engine_clear_bool_are_exact(self) -> None:
        flag_ids = [0x0803, 0x0804]
        flag_rows = [
            {"id": identifier, "value": False}
            for identifier in flag_ids
        ]
        self.assertEqual(
            RUNNER._normalize_map_lifecycle_write_rows(
                flag_rows, "bool-false", identifiers=flag_ids,
                boolean=True,
            ),
            flag_rows,
        )
        var_ids = [0x4000, 0x4001]
        var_rows = [{"id": identifier, "value": 0} for identifier in var_ids]
        self.assertEqual(
            RUNNER._normalize_map_lifecycle_write_rows(
                var_rows, "numeric-zero", identifiers=var_ids,
                boolean=False,
            ),
            var_rows,
        )
        invalid_numeric = deepcopy(var_rows)
        invalid_numeric[0]["value"] = False
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "engine write"):
            RUNNER._normalize_map_lifecycle_write_rows(
                invalid_numeric, "numeric-bool", identifiers=var_ids,
                boolean=False,
            )

        attempts = [
            {"phase_marker": "DESTINATION_TEMP_CLEAR", "tag": None,
             "result": "ENGINE_TRANSFORM"},
            {"phase_marker": "INITIAL_TRANSITION", "tag": 3,
             "result": "TAG_ABSENT"},
            {"phase_marker": "INITIAL_LOAD", "tag": 1,
             "result": "TAG_ABSENT"},
            {"phase_marker": "INITIAL_RESUME", "tag": 5,
             "result": "TAG_ABSENT"},
            {"phase_marker": "INITIAL_WARP_IN", "tag": 4,
             "result": "DISPATCH"},
            {"phase_marker": "PRE_FIELD_INPUT_ON_FRAME", "tag": 2,
             "result": "NO_CONDITION_MATCH"},
        ]
        lifecycle = {
            "producer_kind": "STOCK_WARP", "include_field_return": False,
            "ordered_attempts": attempts,
        }
        RUNNER._validate_map_lifecycle_attempt_phase_order(
            lifecycle, "phase-positive",
        )
        lifecycle["ordered_attempts"] = deepcopy(attempts)
        lifecycle["ordered_attempts"][4]["phase_marker"] = "INITIAL_WARP_INTO"
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "initial phase"):
            RUNNER._validate_map_lifecycle_attempt_phase_order(
                lifecycle, "phase-legacy",
            )
        over_cap = deepcopy(attempts[:5])
        over_cap.extend({
            "phase_marker": "PRE_FIELD_INPUT_ON_FRAME", "tag": 2,
            "result": "DISPATCH" if index < 256 else "TAG_ABSENT",
        } for index in range(257))
        lifecycle["ordered_attempts"] = over_cap
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "tag2"):
            RUNNER._validate_map_lifecycle_attempt_phase_order(
                lifecycle, "phase-cap-overflow",
            )

    def test_berry_powder_changed_only_effect_and_raw_owner_are_exact(
        self,
    ) -> None:
        fixture = deepcopy(self._state_matrix()["cases"][0])
        fixture["oracle_complete"] = True
        fixture["allowed_post_effect_families"].append("BERRY_POWDER")
        fixture["allowed_post_effect_families"].sort()
        berry_allowed_row = {
            "owner": "BERRY_POWDER:0",
            "meaning": "berry-powder vendor exact subtraction",
            "operations": ["DECREASE"],
        }
        fixture["allowed_post_effects"]["berry_powder"] = [
            deepcopy(berry_allowed_row)
        ]
        fixture["allowed_post_effects"] = RUNNER._normalize_allowed_post_effects(
            fixture["allowed_post_effects"], "berry-powder-effect",
        )
        required = deepcopy(
            fixture["input_sequences"][0]["required_postconditions"]
        )
        required["berry_powder"] = 450
        required = RUNNER._normalize_required_postconditions(
            required, "berry-powder-effect",
        )
        side_effects = self._catalog_side_effects()
        side_effects["economy"]["berry_powder"] = {
            "before": 500, "after": 450,
        }
        save2 = side_effects["persistent"]["saveblock2"]
        save2["changes"] = [
            {
                "offset": 0x0AF8 + index, "before": index,
                "after": index + 1, "volatile": False,
            }
            for index in range(4)
        ]

        catalog = RUNNER._validate_catalog_post_effect_contract(
            side_effects, fixture, required=required,
            label="berry-powder-effect",
        )
        event = RUNNER._validate_event_required_effects(
            side_effects, required, label="berry-powder-effect",
        )
        self.assertIn("BERRY_POWDER", catalog["actual_families"])
        self.assertTrue(event["observed"]["berry_powder_changed"])
        self.assertEqual(catalog["observed"]["persistent"], [])
        self.assertEqual(RUNNER._residual_persistent_changes(side_effects), [])

        wrong_owner = deepcopy(
            self._state_matrix()["cases"][0]["allowed_post_effects"]
        )
        wrong_row = deepcopy(berry_allowed_row)
        wrong_row["owner"] = "berry_powder"
        wrong_owner["berry_powder"] = [wrong_row]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "owner"):
            RUNNER._normalize_allowed_post_effects(
                wrong_owner, "berry-powder-wrong-owner",
            )

        missing_required = deepcopy(required)
        missing_required["berry_powder"] = None
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "exact final|changed-only",
        ):
            RUNNER._validate_catalog_post_effect_contract(
                side_effects, fixture, required=missing_required,
                label="berry-powder-missing-required",
            )

        unchanged = deepcopy(side_effects)
        unchanged["economy"]["berry_powder"]["after"] = 500
        unchanged["persistent"]["saveblock2"]["changes"] = []
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "changed-only"):
            RUNNER._validate_catalog_post_effect_contract(
                unchanged, fixture, required=required,
                label="berry-powder-unchanged-required",
            )

        key_change = {
            "offset": 0x0F20, "before": 1, "after": 2,
            "volatile": False,
        }
        side_effects["persistent"]["saveblock2"]["changes"].append(key_change)
        self.assertEqual(
            RUNNER._residual_persistent_changes(side_effects),
            [{
                "block": "SB2", "offset": 0x0F20,
                "before": 1, "after": 2,
            }],
        )

        for value in (0, 99999):
            bounded = deepcopy(required)
            bounded["berry_powder"] = value
            self.assertEqual(
                RUNNER._normalize_required_postconditions(
                    bounded, f"berry-powder-required-{value}",
                )["berry_powder"],
                value,
            )
        for value in (True, 100000):
            invalid = deepcopy(required)
            invalid["berry_powder"] = value
            with self.assertRaises(RUNNER.Stage61MgbaError):
                RUNNER._normalize_required_postconditions(
                    invalid, f"berry-powder-required-invalid-{value}",
                )

    def test_object_dimensions_and_residual_persistent_are_exact(self) -> None:
        side_effects = self._catalog_side_effects()
        fixture = deepcopy(self._state_matrix()["cases"][0])
        fixture["oracle_complete"] = True
        fixture["allowed_post_effect_families"].append("OBJECT")
        fixture["allowed_post_effects"]["objects"] = [{
            "local_id": 15, "allowed_fields": ["current", "template"],
        }]
        required = deepcopy(
            fixture["input_sequences"][0]["required_postconditions"]
        )

        runtime_before = deepcopy(side_effects["objects"]["before"][0])
        runtime_after = deepcopy(runtime_before)
        runtime_after["current"] = [22, 77]
        side_effects["objects"].update({
            "changed": True,
            "after": [deepcopy(runtime_after)],
            "changes": [{
                "local_id": 15, "before": runtime_before,
                "after": runtime_after,
            }],
            "changed_local_ids": [15],
        })
        template_coverage = side_effects["coverage"]["object_templates"]
        template_coverage.update({
            "after_fnv1a64": "E" * 16,
            "changed_local_ids": [15],
            "changes": [{
                "local_id": 15, "before_fnv1a64": "9" * 16,
                "after_fnv1a64": "E" * 16,
            }],
        })
        required["objects"] = [{
            "local_id": 15,
            "after": {
                "map": "96/23", "invisible": False, "visible": True,
                "current": [22, 77], "previous": [21, 77],
            },
            "template_after_fnv1a64": "E" * 16,
        }]
        required = RUNNER._normalize_required_postconditions(
            required, "object-runtime-template",
        )

        catalog_contract = RUNNER._validate_catalog_post_effect_contract(
            side_effects, fixture, required=required,
            label="object-runtime-template",
        )
        event_contract = RUNNER._validate_event_required_effects(
            side_effects, required, label="object-runtime-template",
        )
        self.assertEqual(len(catalog_contract["observed"]["objects"]), 1)
        self.assertEqual(event_contract["observed"]["objects"], [15])
        self.assertEqual(catalog_contract["observed"]["persistent"], [])
        self.assertEqual(event_contract["observed"]["persistent"], [])
        self.assertNotIn(
            "active",
            RUNNER._mapping_changed_fields(
                required["objects"][0]["after"],
                required["objects"][0]["after"],
            ),
        )

        missing_template = deepcopy(required)
        missing_template["objects"][0].pop("template_after_fnv1a64")
        for gate in ("catalog", "event"):
            with self.subTest(gate=gate), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "runtime/template dimension",
            ):
                if gate == "catalog":
                    RUNNER._validate_catalog_post_effect_contract(
                        side_effects, fixture, required=missing_template,
                        label="missing-template",
                    )
                else:
                    RUNNER._validate_event_required_effects(
                        side_effects, missing_template,
                        label="missing-template",
                    )

        fixture["allowed_post_effect_families"].append("PERSISTENT")
        fixture["allowed_post_effects"]["persistent"] = [{
            "block": "SB1", "start": 0x0298, "end": 0x0299,
        }]
        persistent = side_effects["persistent"]["saveblock1"]
        persistent["changes"].insert(0, {
            "offset": 0x0298, "before": 0, "after": 1,
            "volatile": False,
        })
        persistent["raw_changed_byte_count"] = 2
        persistent["normalized_changed_byte_count"] = 2
        required["persistent"] = [{
            "block": "SB1", "offset": 0x0298, "value": 1,
        }]
        catalog_contract = RUNNER._validate_catalog_post_effect_contract(
            side_effects, fixture, required=required,
            label="pc-item-residual",
        )
        event_contract = RUNNER._validate_event_required_effects(
            side_effects, required, label="pc-item-residual",
        )
        expected_residual = [{
            "block": "SB1", "offset": 0x0298, "value": 1,
        }]
        self.assertEqual(
            [
                {
                    "block": row["block"], "offset": row["offset"],
                    "value": row["after"],
                }
                for row in catalog_contract["observed"]["persistent"]
            ],
            expected_residual,
        )
        self.assertEqual(
            event_contract["observed"]["persistent"], expected_residual,
        )

    def test_catalog_batch_gate_requires_visible_text_and_zero_untested(self) -> None:
        raw = bytes.fromhex("a2a3462e0045032bff")
        catalog, _ = RUNNER.validate_catalog_document(self._catalog())
        self.assertEqual(len(catalog["entries"]), 1)
        _, matrix_rows = RUNNER.validate_state_matrix_document(
            self._state_matrix(), expected_rom_sha256="0" * 64,
        )
        expected = RUNNER.project_catalog_state_matrix(catalog, matrix_rows)
        for fixture in expected.values():
            fixture["runtime_position_producer"] = (
                RUNNER._none_runtime_position_producer(
                    fixture["interaction"]["group"],
                    fixture["interaction"]["map"],
                )
            )
        interactive_fixture = expected[
            "matrix-096-023-015-default-000"
        ]
        dynamic_internal_controls = RUNNER._normalize_internal_controls(
            [{
                "kind": "VAR_RESULT_BRANCH_READ",
                "sequence_id": "cancel",
                "instruction_address": "0x0818FB14",
                "writer": "YES_NO", "candidate_values": [0, 1],
                "producer": {"writer": "YES_NO"},
                "def_use_status": "CROSS_NODE_EXACT",
                "capture": {
                    "before_pc": "0x0818FB14",
                    "after_pc": "0x0818FB1A",
                    "owner_address": "0x02037004",
                    "expected_value": expected_value,
                    "expected_token_index": token_index,
                    "expected_execution_ordinal": 0,
                },
            } for token_index, expected_value in ((0, 0), (1, 1))],
            interactive_fixture["input_sequences"], "catalog-dynamic-retry",
        )
        interactive_fixture["control_requirements"]["internal"] = (
            dynamic_internal_controls
        )
        capture = {
            "message_state_address": "0x02036FD0",
            "string_address": "0x02021C88",
            "printer_entry": RUNNER._TEXT_PRINTER_ENTRY,
            "printer_entry_preimage_hex": RUNNER._TEXT_PRINTER_PREIMAGE_HEX,
            "template_printer_entry": RUNNER._TEMPLATE_TEXT_PRINTER_ENTRY,
            "template_printer_entry_preimage_hex": (
                RUNNER._TEMPLATE_TEXT_PRINTER_PREIMAGE_HEX
            ),
            "execution": {
                "invalid_control_flow": False, "first_invalid_pc": None,
                "cpsr": None, "lr": None,
            },
            "active_frames": 1,
            "state_counts": [20, 1, 0, 0],
            "var_result": {
                "address": "0x02037004", "seen": False,
                "first": None, "last": None, "changes": 0,
                "values": [],
            },
            "framebuffer": {
                "first_fnv1a64": "0" * 16,
                "last_fnv1a64": "1" * 16,
                "changed_frames": 1,
                "maximum_baseline_pixel_difference": 2000,
            },
            "messages": [{
                "state": 1,
                "size": len(raw),
                "raw_hex": raw.hex().upper(),
                "raw_fnv1a64": RUNNER._fnv1a64(raw),
                "framebuffer_fnv1a64": "3" * 16,
            }],
            "printer_calls": [{
                "frame": 100,
                "instruction_address": RUNNER._TEXT_PRINTER_ENTRY,
                "caller_instruction_address": "0x08102000",
                "window": 0, "font": 2,
                "text_pointer": "0x08101000", "speed": 1,
                "size": len(raw), "raw_hex": raw.hex().upper(),
                "raw_fnv1a64": RUNNER._fnv1a64(raw),
            }],
        }
        warp = {
            "group": 96, "map": 23, "warp_id": 255,
            "x": 14, "y": 71,
        }
        world = {
            "map": "96/23", "position": [14, 71],
            "location": deepcopy(warp),
            "continue": deepcopy(warp),
            "dynamic": deepcopy(warp),
            "last_heal": deepcopy(warp),
            "escape": deepcopy(warp),
            "destination": deepcopy(warp),
        }
        object_state = {
            "active": True, "visible": True, "invisible": False,
            "slot": 3, "current": [21, 77], "previous": [21, 77],
        }
        battle_state = {
            "active": False, "trainer_opponent": 0, "enemy_species": 0,
            "outcome": 0,
        }
        input_state = {
            "callback_overworld": True, "controls_locked": False,
            "running_state": 0, "tile_transition_state": 0,
            "field_input_recovered": True, "battle_input_owned": False,
        }
        side_effects = {
            "complete": True,
            "coverage": {
                "flags": {
                    "ids_scanned": 6400,
                    "before_fnv1a64": "0" * 16,
                    "after_fnv1a64": "1" * 16,
                },
                "engine_special_flags": {
                    "ids_scanned": 128,
                    "owner_address": "0x02037014",
                    "before_fnv1a64": "F" * 16,
                    "after_fnv1a64": "F" * 16,
                },
                "vars": {
                    "ids_scanned": 768,
                    "before_fnv1a64": "2" * 16,
                    "after_fnv1a64": "3" * 16,
                },
                "items": {
                    "slots_scanned": 186,
                    "entries_before": 1, "entries_after": 0,
                    "before_fnv1a64": "4" * 16,
                    "after_fnv1a64": "5" * 16,
                },
                "trainers": {
                    "ids_scanned": 768,
                    "before_fnv1a64": "6" * 16,
                    "after_fnv1a64": "7" * 16,
                },
                "objects": {
                    "slots_scanned": 16,
                    "active_before": 1, "active_after": 1,
                    "before_fnv1a64": "8" * 16,
                    "after_fnv1a64": "8" * 16,
                },
                "object_templates": {
                    "capacity_scanned": 64,
                    "entries_before": 1, "entries_after": 1,
                    "before_fnv1a64": "9" * 16,
                    "after_fnv1a64": "9" * 16,
                    "changed_local_ids": [],
                    "changes": [],
                },
                "party": {
                    "slots_scanned": 6, "record_size": 100,
                    "raw_byte_length": 600,
                    "count_before": 6, "count_after": 6,
                    "raw_sha256_before": "a" * 64,
                    "raw_sha256_after": "a" * 64,
                },
                "storage": {
                    "raw_byte_length": 0x83D0,
                    "raw_sha256_before": "b" * 64,
                    "raw_sha256_after": "b" * 64,
                },
                "persistent": {
                    "saveblock1": {
                        "bytes_scanned": 0x3D40,
                        "raw_before_fnv1a64": "C" * 16,
                        "raw_after_fnv1a64": "D" * 16,
                        "normalized_before_fnv1a64": "C" * 16,
                        "normalized_after_fnv1a64": "D" * 16,
                        "volatile_ranges": [],
                    },
                    "saveblock2": {
                        "bytes_scanned": 0x0F24,
                        "raw_before_fnv1a64": "E" * 16,
                        "raw_after_fnv1a64": "E" * 16,
                        "normalized_before_fnv1a64": "E" * 16,
                        "normalized_after_fnv1a64": "E" * 16,
                        "volatile_ranges": [{
                            "start": 0x0E, "end": 0x13,
                            "meaning": "play_time_vblank_owner",
                        }],
                    },
                },
            },
            "flags": [
                {"id": 0x519, "before": True, "after": False},
                {"id": 0x119E, "before": False, "after": True},
            ],
            "engine_special_flags": [],
            "vars": [{"id": 0x5170, "before": 7, "after": 8}],
            "items": [{"id": 350, "before": 1, "after": 0}],
            "trainers": [{"id": 25, "before": True, "after": False}],
            "economy": {
                "money": {"before": 3000, "after": 3000},
                "berry_powder": {"before": 500, "after": 500},
                "vega_coins": {"before": 10, "after": 10},
                "cfru_coins": {"before": 10, "after": 10},
            },
            "party": {
                "count_before": 6, "count_after": 6,
                "raw_byte_length": 600,
                "raw_sha256_before": "a" * 64,
                "raw_sha256_after": "a" * 64,
            },
            "storage": {
                "changed": False,
                "raw_byte_length": 0x83D0,
                "raw_sha256_before": "b" * 64,
                "raw_sha256_after": "b" * 64,
            },
            "persistent": {
                "saveblock1": {
                    "bytes_scanned": 0x3D40,
                    "raw_changed": True,
                    "normalized_changed": True,
                    "raw_changed_byte_count": 1,
                    "normalized_changed_byte_count": 1,
                    "raw_before_fnv1a64": "C" * 16,
                    "raw_after_fnv1a64": "D" * 16,
                    "normalized_before_fnv1a64": "C" * 16,
                    "normalized_after_fnv1a64": "D" * 16,
                    "changes": [{
                        "offset": 0x0EE0, "before": 0, "after": 1,
                        "volatile": False,
                    }],
                },
                "saveblock2": {
                    "bytes_scanned": 0x0F24,
                    "raw_changed": False,
                    "normalized_changed": False,
                    "raw_changed_byte_count": 0,
                    "normalized_changed_byte_count": 0,
                    "raw_before_fnv1a64": "E" * 16,
                    "raw_after_fnv1a64": "E" * 16,
                    "normalized_before_fnv1a64": "E" * 16,
                    "normalized_after_fnv1a64": "E" * 16,
                    "changes": [],
                },
            },
            "objects": {
                "changed": False,
                "before": [{
                    "slot": 3, "local_id": 15, "map": "96/23",
                    "invisible": False, "visible": True,
                    "current": [21, 77], "previous": [21, 77],
                }],
                "after": [{
                    "slot": 3, "local_id": 15, "map": "96/23",
                    "invisible": False, "visible": True,
                    "current": [21, 77], "previous": [21, 77],
                }],
                "changes": [], "changed_local_ids": [],
            },
            "world": {
                "changed": False,
                "before": deepcopy(world), "after": deepcopy(world),
            },
            "object": {
                "changed": False, "visibility_changed": False,
                "before": deepcopy(object_state),
                "after": deepcopy(object_state),
                "template_before": {
                    "found": True, "slot": 2, "local_id": 15,
                    "graphics_id": 1, "kind": 0, "position": [14, 70],
                    "script": "0x08100000", "hide_flag": 0,
                    "hide_flag_set": False,
                },
                "template_after": {
                    "found": True, "slot": 2, "local_id": 15,
                    "graphics_id": 1, "kind": 0, "position": [14, 70],
                    "script": "0x08100000", "hide_flag": 0,
                    "hide_flag_set": False,
                },
            },
            "battle": {
                "opponent_changed": False,
                "before": deepcopy(battle_state),
                "after": deepcopy(battle_state),
            },
            "input": {
                "recovered": True,
                "before": deepcopy(input_state),
                "after": deepcopy(input_state),
            },
        }
        expected_sequences = expected[
            "matrix-096-023-015-default-000"
        ]["input_sequences"]
        interaction = expected[
            "matrix-096-023-015-default-000"
        ]["interaction"]
        template_raw = interaction["expected_template_raw_hex"]
        preinteraction_identity = self._preinteraction_identity(
            template_raw, template_index=15, interactive=True,
        )
        approach_observation = self._approach_observation(interaction)
        none_position_producer = expected[
            "matrix-096-023-015-default-000"
        ]["runtime_position_producer"]
        none_position_control = RUNNER._none_runtime_position_control()
        runtime_internal_controls = [{
            "writer": control["writer"],
            "instruction_address": (
                f"0x{control['instruction_address']:08X}"
            ),
            "before_pc": f"0x{control['capture']['before_pc']:08X}",
            "after_pc": f"0x{control['capture']['after_pc']:08X}",
            "expected_token_index": control["capture"][
                "expected_token_index"
            ],
            "expected_execution_ordinal": control["capture"][
                "expected_execution_ordinal"
            ],
            "owner_address": (
                f"0x{control['capture']['owner_address']:08X}"
            ),
            "expected_value": control["capture"]["expected_value"],
            "observed_value": control["capture"]["expected_value"],
            "observed_script_pointer": (
                f"0x{control['capture']['before_pc']:08X}"
            ),
            "execution_count": 1,
            "hit_count": 1,
            "value_mismatch": False,
        } for control in dynamic_internal_controls]
        attempts = [{
            "sequence_id": sequence["sequence_id"],
            "expected_static_branch_token": sequence[
                "expected_static_branch_token"
            ],
            "visible_text_expected": sequence["visible_text_expected"],
            "silent_text_basis_sha256": None,
            "input_tokens": sequence["tokens"],
            "input_step_count": len(sequence["tokens"]),
            "input_steps_consumed": len(sequence["tokens"]),
            "premature_terminal": False,
            "success": True,
            "failure_reason": "NONE",
            "terminal": "FIELD_RELEASE",
            "field_released": True,
            "battle_started": False,
            "root_script_pointer_expected": "0x08100000",
            "root_counter_armed_after_identity": True,
            "root_script_pointer_hits": 1,
            "first_root_script_pointer": "0x08100000",
            "first_root_context": {"map": "96/23", "player": [14, 71]},
            "preinteraction_object_identity": deepcopy(
                preinteraction_identity
            ),
            "post_battle": {
                "battle_started": False, "trainer_battle": False,
                "completed_via_keys": False,
                "forced_switch_count": 0,
                "forced_switch_cursor_observed": False,
                "forced_switch_usable_slot_selected": False,
                "forced_switch_cursor_initial": [],
                "forced_switch_selected_slots": [],
                "forced_switch_selected_hps": [],
                "route": "NONE", "outcome": 0,
                "won_or_escaped_not_loss": False,
                "field_released_after_battle": False,
                "start_pressed": False, "start_menu_opened": False,
                "back_pressed": False, "map_preserved": False,
                "field_input_recovered": False,
            },
            "post_battle_continuation": None,
            "field_roundtrip": self._field_roundtrip(),
            "capture": deepcopy(capture),
            "internal_controls": (
                deepcopy(runtime_internal_controls)
                if sequence["sequence_id"] == "cancel" else []
            ),
            "deferred_external_controls": [],
            "rfu_session": None,
            "battle_start_side_effects": None,
            "side_effects": deepcopy(side_effects),
        } for sequence in expected_sequences]
        document = {
            "schema_version": 9,
            "status": "PASS",
            "case": "catalog_batch",
            "baseline_natural_continue": True,
            "per_case_stock_warp": True,
            "input_sequence_probe_via_state_restore": True,
            "results": [{
                "case_id": "matrix-096-023-015-default-000",
                "base_case_id": "route12_npc_15",
                "owner_key": "OBJECT:096/023:015",
                "catalog_branch": "DEFAULT",
                "map": "96/23",
                "local_id": 15,
                "runtime_root": "0x08100000",
                "actual_walk_steps": 1,
                "direction_plus_a": True,
                "interaction_trigger": (
                    "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A"
                ),
                "walk_path_basis": (
                    "EXACT_STOCK_INCOMING_ARRIVAL_TO_OWNER_STANCE"
                ),
                "stance": [14, 71], "interaction_distance": 1,
                "counter_tile_present": False,
                "actual_walk_required": True,
                "map_level_real_walk_probe_required": False,
                "direct_script_call": False,
                "state_counts": {
                    "flags": 1, "vars": 1, "items": 1, "trainers": 1,
                    "external_controls": 0, "internal_controls": 2,
                },
                "control_abi_complete": False,
                "expect_visible": True,
                "interaction_expected": True,
                "object_visible": True,
                "final_map": "96/23",
                "visibility_framebuffer_fnv1a64": "4" * 16,
                "approach_observation": deepcopy(approach_observation),
                "runtime_position_producer": (
                    self._runtime_position_observation(
                        none_position_producer, none_position_control,
                        requested=interaction["start"], visible=True,
                    )
                ),
                "preinteraction_object_identity": deepcopy(
                    preinteraction_identity
                ),
                "root_probe": {
                    "expected": "0x08100000",
                    "armed_after_identity": True,
                    "input_attempted": True,
                    "hidden_idle_frames": 0,
                    "hidden_hits": 0,
                    "hidden_first": None,
                },
                "input_sequence_attempts": attempts,
            }, {
                "case_id": "matrix-096-023-015-collected-000",
                "base_case_id": "route12_npc_15",
                "owner_key": "OBJECT:096/023:015",
                "catalog_branch": "COLLECTED",
                "map": "96/23",
                "local_id": 15,
                "runtime_root": "0x08100000",
                "actual_walk_steps": 0,
                "direction_plus_a": False,
                "interaction_trigger": (
                    "TELEPORT_TO_WALK_START_REAL_WALK_TO_STANCE_FACE_AND_A"
                ),
                "walk_path_basis": (
                    "EXACT_STOCK_INCOMING_ARRIVAL_TO_OWNER_STANCE"
                ),
                "stance": [14, 71], "interaction_distance": 1,
                "counter_tile_present": False,
                "actual_walk_required": True,
                "map_level_real_walk_probe_required": False,
                "direct_script_call": False,
                "state_counts": {
                    "flags": 1, "vars": 0, "items": 0, "trainers": 0,
                    "external_controls": 0, "internal_controls": 0,
                },
                "control_abi_complete": False,
                "expect_visible": False,
                "interaction_expected": False,
                "object_visible": False,
                "final_map": "96/23",
                "visibility_framebuffer_fnv1a64": "5" * 16,
                "approach_observation": None,
                "runtime_position_producer": (
                    self._runtime_position_observation(
                        none_position_producer, none_position_control,
                        requested=interaction["start"], visible=False,
                    )
                ),
                "preinteraction_object_identity": (
                    self._preinteraction_identity(
                        template_raw, template_index=15,
                        interactive=False,
                    )
                ),
                "root_probe": {
                    "expected": "0x08100000",
                    "armed_after_identity": True,
                    "input_attempted": False,
                    "hidden_idle_frames": 3,
                    "hidden_hits": 0,
                    "hidden_first": "0x00000000",
                },
                "input_sequence_attempts": [],
            }],
            "fixture_count": 2,
            "interactive_count": 1,
            "hidden_count": 1,
            "input_sequence_attempt_count": 2,
            "successful_path_count": 2,
            "failed": 0,
            "empty_text": 0,
            "softlocks": 0,
            "terminal_mismatches": 0,
            "frame_diff_failures": 0,
            "input_recovery_failures": 0,
            "invalid_control_flow_failures": 0,
            "internal_control_failures": 0,
            "root_script_failures": 0,
            "link_session_attempt_count": 0,
            "rfu_session_attempt_count": 0,
            "rfu_session_failure_count": 0,
            "rfu_host_memory_write_count": 0,
            "center_link_session_attempt_count": 0,
            "center_link_session_failure_count": 0,
            "center_link_host_memory_write_count": 0,
            "side_effect_capture_failures": 0,
            "untested": 0,
            "warnings": 0,
        }
        result = RUNNER._validate_catalog_batch(
            document, expected, RUNNER._read_charmap(),
        )
        self.assertEqual(
            result["results"][0]["input_sequence_attempts"][1]
            ["internal_control_oracle_match"]["captured_count"],
            2,
        )
        catalog_internal_mutations = {
            "missing": lambda rows: rows.pop(),
            "extra": lambda rows: rows.append(deepcopy(rows[-1])),
            "same-token-duplicate": lambda rows: rows[1].__setitem__(
                "expected_token_index", 0,
            ),
            "token-swap": lambda rows: (
                rows[0].__setitem__("expected_token_index", 1),
                rows[1].__setitem__("expected_token_index", 0),
            ),
            "value-swap": lambda rows: (
                rows[0].update({"expected_value": 1, "observed_value": 1}),
                rows[1].update({"expected_value": 0, "observed_value": 0}),
            ),
        }
        for label, mutate in catalog_internal_mutations.items():
            broken = deepcopy(document)
            rows = broken["results"][0]["input_sequence_attempts"][1][
                "internal_controls"
            ]
            mutate(rows)
            with self.subTest(internal_control=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._validate_catalog_batch(
                    broken, expected, RUNNER._read_charmap(),
                )
        retained_raw = deepcopy(document)
        retained_raw["framebuffer_artifacts"] = []
        retained_expected = deepcopy(result)
        retained_expected["framebuffer_artifacts"] = []
        raw_stdout = (
            json.dumps(retained_raw, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        RUNNER._retention_join_stdout(
            case_id="catalog_batch", phase="catalog_batch",
            raw=raw_stdout, expected=retained_expected, sharded=True,
        )
        retained_mutations = {
            "row-root": lambda item: item["results"][0].__setitem__(
                "runtime_root", "0x08100002",
            ),
            "zero-hit": lambda item: item["results"][0][
                "input_sequence_attempts"
            ][0].__setitem__("root_script_pointer_hits", 0),
            "wrong-first": lambda item: item["results"][0][
                "input_sequence_attempts"
            ][0].__setitem__("first_root_script_pointer", "0x08100002"),
            "wrong-live-xy": lambda item: item["results"][0][
                "preinteraction_object_identity"
            ].__setitem__("live_current", [22, 77]),
            "wrong-template-xy": lambda item: item["results"][0][
                "preinteraction_object_identity"
            ].__setitem__("template_position", [15, 70]),
            "wrong-template-root": lambda item: item["results"][0][
                "preinteraction_object_identity"
            ].__setitem__("template_script", "0x08100002"),
            "hidden-active": lambda item: item["results"][1][
                "preinteraction_object_identity"
            ].update({
                "live_active": True, "live_visible": True,
                "live_current": [21, 77],
            }),
            "hidden-hit": lambda item: item["results"][1][
                "root_probe"
            ].update({
                "hidden_hits": 1, "hidden_first": "0x08100000",
            }),
        }
        for label, mutate in retained_mutations.items():
            retained_broken = deepcopy(retained_raw)
            mutate(retained_broken)
            with self.subTest(retention=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "stdout value",
            ):
                RUNNER._retention_join_stdout(
                    case_id="catalog_batch", phase="catalog_batch",
                    raw=(json.dumps(
                        retained_broken, sort_keys=True, separators=(",", ":"),
                    ) + "\n").encode("utf-8"),
                    expected=retained_expected, sharded=True,
                )
        message = result["results"][0]["input_sequence_attempts"][0][
            "capture"
        ]["messages"][0]
        self.assertEqual(message["utf8"], "12ばん どうろ")
        self.assertEqual(message["raw_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["distinct_path_count"], 1)
        self.assertEqual(
            result["results"][0]["distinct_paths"][0]["sequences"],
            ["advance", "cancel"],
        )
        self.assertEqual(
            result["results"][0]["input_sequence_attempts"][0]
            ["side_effects"]["items"],
            [{"id": 350, "before": 1, "after": 0}],
        )

        physical_negative_mutations = {
            "template-raw-one-byte": lambda item: item["results"][0][
                "preinteraction_object_identity"
            ].__setitem__(
                "observed_raw_hex", "00" + template_raw[2:],
            ),
            "step-facing": lambda item: item["results"][0][
                "approach_observation"
            ]["step_facing"][0].__setitem__("observed", 3),
            "approach-transient": lambda item: item["results"][0][
                "approach_observation"
            ]["transient_execution"].__setitem__("message_count", 1),
            "approach-persistent": lambda item: item["results"][0][
                "approach_observation"
            ]["persistent_state"].__setitem__("vars_exact", False),
            "movement-owned-transition": lambda item: item["results"][0][
                "approach_observation"
            ]["persistent_state"]["movement_owned_state"][
                "happiness_step_counter"
            ].__setitem__("after", 126),
            "field-roundtrip": lambda item: item["results"][0][
                "input_sequence_attempts"
            ][0]["field_roundtrip"].__setitem__(
                "start_menu_opened", False,
            ),
        }
        for label, mutate in physical_negative_mutations.items():
            broken = deepcopy(document)
            mutate(broken)
            with self.subTest(physical_contract=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._validate_catalog_batch(
                    broken, expected, RUNNER._read_charmap(),
                )

        wrong_root = deepcopy(document)
        wrong_root["results"][0]["input_sequence_attempts"][0][
            "first_root_script_pointer"
        ] = "0x08100002"
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "runtime root hit",
        ):
            RUNNER._validate_catalog_batch(
                wrong_root, expected, RUNNER._read_charmap(),
            )

        zero_root_hit = deepcopy(document)
        zero_root_hit["results"][0]["input_sequence_attempts"][0][
            "root_script_pointer_hits"
        ] = 0
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "runtime root hit",
        ):
            RUNNER._validate_catalog_batch(
                zero_root_hit, expected, RUNNER._read_charmap(),
            )

        wrong_live_xy = deepcopy(document)
        wrong_side = wrong_live_xy["results"][0][
            "input_sequence_attempts"
        ][0]["side_effects"]
        for phase in ("before", "after"):
            wrong_side["object"][phase]["current"] = [22, 77]
            wrong_side["objects"][phase][0]["current"] = [22, 77]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "snapshot/root identity",
        ):
            RUNNER._validate_catalog_batch(
                wrong_live_xy, expected, RUNNER._read_charmap(),
            )

        hidden_root_hit = deepcopy(document)
        hidden_probe = hidden_root_hit["results"][1]["root_probe"]
        hidden_probe["hidden_hits"] = 1
        hidden_probe["hidden_first"] = "0x08100000"
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "hidden probe",
        ):
            RUNNER._validate_catalog_batch(
                hidden_root_hit, expected, RUNNER._read_charmap(),
            )

        battle_document = deepcopy(document)
        battle_expected = deepcopy(expected)
        battle_expected["matrix-096-023-015-default-000"][
            "expected_terminal"
        ] = "BATTLE_START"
        battle_fixture = battle_expected[
            "matrix-096-023-015-default-000"
        ]
        battle_fixture["allowed_post_effect_families"] = sorted(
            set(battle_fixture["allowed_post_effect_families"]) | {"BATTLE"}
        )
        battle_fixture["allowed_post_effects"]["battles"] = [{
            "meaning": "synthetic trainer battle start",
            "allowed_fields": [
                "active", "enemy_species", "trainer_opponent",
            ],
        }]
        battle_start_required = {
            "flags": [], "engine_special_flags": [], "vars": [],
            "items": [], "trainers": [], "objects": [], "warp": None,
            "battle": {
                "active": True, "trainer_opponent": 25,
                "enemy_species": 150, "outcome": 0,
            },
            "money": None, "berry_powder": None, "coins": None,
            "party": None,
            "storage": None, "persistent": [],
        }
        for sequence in battle_expected[
            "matrix-096-023-015-default-000"
        ]["input_sequences"]:
            sequence["battle_start_required_postconditions"] = deepcopy(
                battle_start_required
            )
        for attempt in battle_document["results"][0][
            "input_sequence_attempts"
        ]:
            battle_start = deepcopy(side_effects)
            for kind in ("flags", "vars", "items", "trainers"):
                battle_start[kind] = []
                coverage = battle_start["coverage"][kind]
                coverage["after_fnv1a64"] = coverage["before_fnv1a64"]
            battle_start["coverage"]["items"]["entries_after"] = (
                battle_start["coverage"]["items"]["entries_before"]
            )
            persistent_start = battle_start["persistent"]["saveblock1"]
            persistent_start.update({
                "raw_changed": False,
                "normalized_changed": False,
                "raw_changed_byte_count": 0,
                "normalized_changed_byte_count": 0,
                "raw_after_fnv1a64": persistent_start["raw_before_fnv1a64"],
                "normalized_after_fnv1a64": persistent_start[
                    "normalized_before_fnv1a64"
                ],
                "changes": [],
            })
            battle_start["coverage"]["persistent"]["saveblock1"].update({
                "raw_after_fnv1a64": persistent_start["raw_before_fnv1a64"],
                "normalized_after_fnv1a64": persistent_start[
                    "normalized_before_fnv1a64"
                ],
            })
            battle_start["battle"]["opponent_changed"] = True
            battle_start["battle"]["after"] = {
                "active": True, "trainer_opponent": 25,
                "enemy_species": 150, "outcome": 0,
            }
            battle_start["input"]["recovered"] = False
            battle_start["input"]["after"] = {
                "callback_overworld": False, "controls_locked": True,
                "running_state": 0, "tile_transition_state": 0,
                "field_input_recovered": False,
                "battle_input_owned": True,
            }
            attempt.update({
                "terminal": "BATTLE_START", "field_released": False,
                "battle_started": True,
                "field_roundtrip": None,
                "battle_start_side_effects": battle_start,
                "post_battle": {
                    "battle_started": True, "trainer_battle": True,
                    "completed_via_keys": True,
                    "forced_switch_count": 1,
                    "forced_switch_cursor_observed": True,
                    "forced_switch_usable_slot_selected": True,
                    "forced_switch_cursor_initial": [0],
                    "forced_switch_selected_slots": [1],
                    "forced_switch_selected_hps": [128],
                    "route": "FIGHT", "outcome": 1,
                    "won_or_escaped_not_loss": True,
                    "field_released_after_battle": True,
                    "start_pressed": True, "start_menu_opened": True,
                    "back_pressed": True, "map_preserved": True,
                    "field_input_recovered": True,
                },
            })
        validated_battle = RUNNER._validate_catalog_batch(
            battle_document, battle_expected, RUNNER._read_charmap(),
        )
        battle_attempt = validated_battle["results"][0][
            "input_sequence_attempts"
        ][0]
        self.assertIs(
            battle_attempt["battle_start_side_effects"]["battle"][
                "after"
            ]["active"],
            True,
        )
        self.assertIs(
            battle_attempt["side_effects"]["input"]["recovered"], True,
        )
        wrong_battle_identity = deepcopy(battle_expected)
        wrong_battle_identity[
            "matrix-096-023-015-default-000"
        ]["input_sequences"][0][
            "battle_start_required_postconditions"
        ]["battle"]["enemy_species"] = 151
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "BATTLE exact snapshot",
        ):
            RUNNER._validate_catalog_batch(
                battle_document, wrong_battle_identity,
                RUNNER._read_charmap(),
            )

        contaminated_final = deepcopy(battle_expected)
        contaminated_final[
            "matrix-096-023-015-default-000"
        ]["input_sequences"][0]["required_postconditions"]["battle"] = (
            deepcopy(battle_start_required["battle"])
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "required BATTLE",
        ):
            RUNNER._validate_catalog_batch(
                battle_document, contaminated_final,
                RUNNER._read_charmap(),
            )

        nonbattle_start_contract = deepcopy(expected)
        nonbattle_start_contract[
            "matrix-096-023-015-default-000"
        ]["input_sequences"][0][
            "battle_start_required_postconditions"
        ] = deepcopy(battle_start_required)
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "non-battle枝にbattle-start",
        ):
            RUNNER._validate_catalog_batch(
                document, nonbattle_start_contract,
                RUNNER._read_charmap(),
            )
        missing_field_return = deepcopy(battle_document)
        missing_field_return["results"][0]["input_sequence_attempts"][0][
            "side_effects"
        ]["input"]["recovered"] = False
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "input recovery",
        ):
            RUNNER._validate_catalog_batch(
                missing_field_return, battle_expected,
                RUNNER._read_charmap(),
            )

        unknown_visible = deepcopy(document)
        extra_raw = bytes.fromhex("a3ff")
        extra_call = deepcopy(
            unknown_visible["results"][0]["input_sequence_attempts"][0]
            ["capture"]["printer_calls"][0]
        )
        extra_call.update({
            "frame": 101, "text_pointer": "0x08101001",
            "size": len(extra_raw), "raw_hex": extra_raw.hex().upper(),
            "raw_fnv1a64": RUNNER._fnv1a64(extra_raw),
        })
        unknown_visible["results"][0]["input_sequence_attempts"][0] \
            ["capture"]["printer_calls"].append(extra_call)
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "independent ordered text oracle",
        ):
            RUNNER._validate_catalog_batch(
                unknown_visible, expected, RUNNER._read_charmap(),
            )

        invalid_native = deepcopy(document)
        invalid_capture = invalid_native["results"][0][
            "input_sequence_attempts"
        ][0]["capture"]
        invalid_capture["execution"] = {
            "invalid_control_flow": True,
            "first_invalid_pc": "0x37192311",
            "cpsr": "0x6000003F",
            "lr": "0x0818C349",
        }
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "invalid native/control-flow",
        ):
            RUNNER._validate_catalog_batch(
                invalid_native, expected, RUNNER._read_charmap(),
            )

        missing_exact = deepcopy(expected)
        missing_exact["matrix-096-023-015-default-000"]["input_sequences"][0] \
            ["required_postconditions"]["flags"] = []
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "sequence別exact postcondition",
        ):
            RUNNER._validate_catalog_batch(
                document, missing_exact, RUNNER._read_charmap(),
            )

        unexpected_residual = deepcopy(document)
        residual_block = unexpected_residual["results"][0][
            "input_sequence_attempts"
        ][0]["side_effects"]["persistent"]["saveblock1"]
        residual_block["changes"].insert(0, {
            "offset": 0x0298, "before": 0, "after": 1,
            "volatile": False,
        })
        residual_block["raw_changed_byte_count"] = 2
        residual_block["normalized_changed_byte_count"] = 2
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "PERSISTENT effect",
        ):
            RUNNER._validate_catalog_batch(
                unexpected_residual, expected, RUNNER._read_charmap(),
            )

        different_side_effect = deepcopy(document)
        different_var = different_side_effect["results"][0][
            "input_sequence_attempts"
        ][1]["capture"]["var_result"]
        different_var.update({
            "seen": True, "first": 7, "last": 7,
            "changes": 0, "values": [7],
        })
        distinct = RUNNER._validate_catalog_batch(
            different_side_effect, expected, RUNNER._read_charmap(),
        )
        self.assertEqual(distinct["distinct_path_count"], 2)

        trainer_mismatch = deepcopy(document)
        trainer_mismatch["results"][0]["input_sequence_attempts"][0] \
            ["side_effects"]["trainers"] = []
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "trainer/flag delta",
        ):
            RUNNER._validate_catalog_batch(
                trainer_mismatch, expected, RUNNER._read_charmap(),
            )

        incomplete = deepcopy(document)
        incomplete["untested"] = 1
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "JSON契約"):
            RUNNER._validate_catalog_batch(
                incomplete, expected, RUNNER._read_charmap(),
            )

    def test_catalog_batch_requires_two_independent_process_runs(self) -> None:
        RUNNER._validate_process_run_count(2, ["catalog_batch"])
        RUNNER._validate_process_run_count(2, ["stateful_menu_loop_batch"])
        RUNNER._validate_process_run_count(1, ["map_popup"])
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "独立2 process以上",
        ):
            RUNNER._validate_process_run_count(1, ["catalog_batch"])
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "独立2 process以上",
        ):
            RUNNER._validate_process_run_count(
                1, ["stateful_menu_loop_batch"],
            )

    def test_process_result_hash_lattice_rejects_run_and_column_drift(
        self,
    ) -> None:
        result = {"schema_version": 1, "case": "unit", "status": "PASS"}
        merged_sha = RUNNER._sha256(
            RUNNER._stable(result).encode("utf-8")
        )
        shard_shas = ["1" * 64, "2" * 64, "3" * 64]
        wrapper = {
            "status": "PASS",
            "process_runs": 2,
            "process_shards": 3,
            "same_shard_boundaries_across_runs": True,
            "per_shard_identical_results": True,
            "per_shard_result_sha256": shard_shas,
            "per_run_merged_result_sha256": [merged_sha, merged_sha],
            "per_run_per_shard_result_sha256": [
                deepcopy(shard_shas), deepcopy(shard_shas),
            ],
            "identical_results": True,
            "result": result,
        }
        normalized = RUNNER.validate_mgba_process_result_hashes(wrapper)
        self.assertEqual(
            normalized["per_run_per_shard_result_sha256"][0],
            normalized["per_shard_result_sha256"],
        )
        mutations = {
            "run-hash": lambda item: item[
                "per_run_merged_result_sha256"
            ].__setitem__(1, "0" * 64),
            "matrix-cardinality": lambda item: item[
                "per_run_per_shard_result_sha256"
            ].pop(),
            "row-cardinality": lambda item: item[
                "per_run_per_shard_result_sha256"
            ][1].pop(),
            "column-drift": lambda item: item[
                "per_run_per_shard_result_sha256"
            ][1].__setitem__(2, "4" * 64),
            "first-run-drift": lambda item: item[
                "per_shard_result_sha256"
            ].__setitem__(0, "5" * 64),
            "extra-key": lambda item: item.__setitem__("unbound", True),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                broken = deepcopy(wrapper)
                mutate(broken)
                with self.assertRaises(RUNNER.Stage61MgbaError):
                    RUNNER.validate_mgba_process_result_hashes(broken)

    def test_trainer_tower_canonical_save_evidence_is_byte_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            save = bytearray(b"\xFF" * 0x20000)
            save[31 * 0x1000:31 * 0x1000 + 4] = b"\0\0\0\0"
            path = work / "canonical.srm"
            path.write_bytes(save)
            shard = RUNNER._trainer_tower_shard_save_precondition(
                work, process_identity="catalog_batch/run-1/shard-1",
            )
            document = {
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
                "cases": {"catalog_batch": [[shard]]},
            }
            checked = RUNNER.validate_trainer_tower_save_precondition(
                document, selected=["catalog_batch"], runs=1,
                shard_counts={"catalog_batch": 1},
            )
            sectors = checked["cases"]["catalog_batch"][0][0][
                "canonical_source_srms"
            ][0]["sectors"]
            self.assertEqual(
                [row["first_u32_le_hex"] for row in sectors],
                ["0xFFFFFFFF", "0x00000000"],
            )

    def test_trainer_tower_external_ereader_save_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ereader.srm"
            save = bytearray(b"\xFF" * 0x20000)
            save[30 * 0x1000:30 * 0x1000 + 4] = struct.pack(
                "<I", 0x0000B39D,
            )
            save[31 * 0x1000:31 * 0x1000 + 4] = b"\0\0\0\0"
            path.write_bytes(save)
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "external/eReader save",
            ):
                RUNNER._trainer_tower_save_image_evidence(
                    path, relative_path=path.name,
                )

    def test_trainer_tower_on_transition_producer_is_exact_none_control_exception(
        self,
    ) -> None:
        case_id = "matrix-002-001-002-default-000"
        rom_sha = "a" * 64
        lifecycle = {
            "kind": "TRAINER_TOWER_ON_TRANSITION",
            "root": "0x081A96EA",
            "map_script_tag": 2,
            "layout_id": 298,
            "expected_object": [15, 13],
            "expected_movement_type": 9,
            "local_fallback_precondition": {
                "save": deepcopy(RUNNER._TRAINER_TOWER_LOCAL_FALLBACK_SAVE),
                "runtime_state": deepcopy(RUNNER._TRAINER_TOWER_RUNTIME_STATE),
            },
        }
        producer = {
            "kind": "TRAINER_TOWER_ON_TRANSITION",
            "root": 0x081A96EA,
            "source_group": 0, "source_map": 0, "source_warp": 255,
            "predecessor_x": 14, "predecessor_y": 13,
            "trigger_x": 14, "trigger_y": 13, "trigger_key": 0,
            "destination_group": 2, "destination_map": 1,
            "destination_warp": 255,
            "arrival_x": 14, "arrival_y": 13,
            "record_address": 0, "map_script_tag": 2,
            "event_case_id": case_id,
            "source_provenance": {
                "rom_sha256": rom_sha,
                "owner_id": "OBJECT:002/001:002",
                "kind": "TRAINER_TOWER_ON_TRANSITION",
                "root": "0x081A96EA", "map_script_tag": 2,
                "local_fallback_precondition": deepcopy(
                    lifecycle["local_fallback_precondition"]
                ),
            },
        }
        self.assertEqual(
            RUNNER._validate_trainer_tower_runtime_map_lifecycle(
                lifecycle, group=2, map_number=1,
                expected_object=[15, 13], label="unit Trainer Tower",
            ),
            lifecycle,
        )
        template = bytearray(24)
        struct.pack_into("<hh", template, 4, 15, 13)
        template[9] = 9
        rom_raw = (ROOT / RUNNER.DEFAULT_ROM).read_bytes()
        self.assertEqual(
            RUNNER._validate_trainer_tower_lifecycle_rom_binding(
                lifecycle, owner_key="OBJECT:002/001:002",
                expected_template_raw_hex=template.hex().upper(),
                rom_raw=rom_raw, label="unit Trainer Tower ROM",
            ),
            lifecycle,
        )
        wrong_movement = deepcopy(lifecycle)
        wrong_movement["expected_movement_type"] = 8
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "movement/source preimage",
        ):
            RUNNER._validate_trainer_tower_lifecycle_rom_binding(
                wrong_movement, owner_key="OBJECT:002/001:002",
                expected_template_raw_hex=template.hex().upper(),
                rom_raw=rom_raw, label="unit Trainer Tower ROM",
            )
        lifecycle_mutations = {
            "layout": lambda item: item.__setitem__("layout_id", 299),
            "extra": lambda item: item.__setitem__("unbound", True),
            "save-sentinel": lambda item: item[
                "local_fallback_precondition"
            ]["save"].__setitem__(
                "sector30_special_sentinel_present", True,
            ),
            "implicit-progress": lambda item: item[
                "local_fallback_precondition"
            ]["runtime_state"].__setitem__("implicit_progress_seeded", True),
        }
        for mutation, mutate in lifecycle_mutations.items():
            broken_lifecycle = deepcopy(lifecycle)
            mutate(broken_lifecycle)
            with self.subTest(lifecycle=mutation), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._validate_trainer_tower_runtime_map_lifecycle(
                    broken_lifecycle, group=2, map_number=1,
                    expected_object=[15, 13], label="unit Trainer Tower",
                )
        checked = RUNNER._validate_runtime_position_producer(
            producer, group=2, map_number=1, required=True,
            label="unit Trainer Tower", rom_sha256=rom_sha,
            expected_engine_start=[14, 13],
        )
        self.assertEqual(checked["kind"], "TRAINER_TOWER_ON_TRANSITION")
        self.assertEqual(
            RUNNER._validate_runtime_position_control(
                RUNNER._none_runtime_position_control(), required=False,
                label="unit Trainer Tower control",
            )["kind"],
            "NONE",
        )
        row = {
            "owner_key": "OBJECT:002/001:002",
            "runtime_position_producer": checked,
            "runtime_map_lifecycle": lifecycle,
        }
        interaction = {
            "group": 2, "map": 1, "object": [15, 13],
            "expected_template_raw_hex": "00" * 24,
            "runtime_position_map_load_required": True,
            "runtime_position_control": RUNNER._none_runtime_position_control(),
        }
        fields = RUNNER._runtime_position_producer_tsv_fields(
            row, interaction, case_id,
        )
        self.assertEqual(len(fields), 19)
        self.assertEqual(fields[-3:], ["2", "298", "9"])
        for key, replacement in (
            ("root", 0x081A96EC), ("map_script_tag", 3),
        ):
            broken = deepcopy(producer)
            broken[key] = replacement
            with self.subTest(key=key), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._validate_runtime_position_producer(
                    broken, group=2, map_number=1, required=True,
                    label="unit Trainer Tower", rom_sha256=rom_sha,
                    expected_engine_start=[14, 13],
                )

    def test_catalog_partition_is_contiguous_complete_and_deterministic(self) -> None:
        expected = {f"case-{index:03d}": {"index": index} for index in range(10)}
        first = RUNNER._partition_catalog(expected, 4)
        second = RUNNER._partition_catalog(expected, 4)
        self.assertEqual(first, second)
        self.assertEqual([len(shard) for shard in first], [3, 3, 2, 2])
        self.assertEqual(
            [case_id for shard in first for case_id in shard], sorted(expected),
        )
        for shard in first:
            self.assertEqual(list(shard), sorted(shard))

    def test_catalog_shards_merge_arbitrary_state_sequence_cartesian_once(
        self,
    ) -> None:
        expected = {}
        shadow_owners = {
            0: (
                "OBJECT:003/022:000",
                "CANONICAL_SHADOW_NON_PRODUCT_SOURCE_DIAGNOSTIC_STANCE",
                False,
            ),
            1: (
                "OBJECT:003/022:003",
                "CANONICAL_SHADOW_NON_PRODUCT_SOURCE_DIAGNOSTIC_STANCE",
                False,
            ),
            2: (
                "OBJECT:096/015:007",
                "CANONICAL_SHADOW_EXACT_STOCK_INCOMING_ARRIVAL_TO_STANCE",
                True,
            ),
            3: (
                "OBJECT:096/015:008",
                "CANONICAL_SHADOW_EXACT_STOCK_INCOMING_ARRIVAL_TO_STANCE",
                True,
            ),
        }
        for index in range(137):
            interactive = index in shadow_owners or index % 5 != 0
            sequences = [
                {"sequence_id": f"s{choice}"}
                for choice in range(1 + index % 4)
            ] if interactive else []
            owner_key, walk_path_basis, walk_required = shadow_owners.get(
                index,
                (
                    f"OBJECT:096/023:{index:03d}",
                    "EXACT_STOCK_INCOMING_ARRIVAL_TO_OWNER_STANCE",
                    interactive,
                ),
            )
            expected[f"runtime-root-{index:04d}"] = {
                "expect_interaction": interactive,
                "interaction_expected": interactive,
                "input_sequences": sequences,
                "owner_key": owner_key,
                "walk_path_basis": walk_path_basis,
                "actual_walk_required": walk_required,
            }
        shards = RUNNER._partition_catalog(expected, 64)
        self.assertEqual(len(shards), 64)
        documents = []
        for shard_index, shard in enumerate(shards):
            interactive = sum(
                int(row["expect_interaction"]) for row in shard.values()
            )
            attempts = sum(
                len(row["input_sequences"]) for row in shard.values()
            )
            documents.append({
                "schema_version": 9, "status": "PASS",
                "case": "catalog_batch",
                "baseline_natural_continue": True,
                "per_case_stock_warp": True,
                "input_sequence_probe_via_state_restore": True,
                "failed": 0, "empty_text": 0, "softlocks": 0,
                "terminal_mismatches": 0, "frame_diff_failures": 0,
                "input_recovery_failures": 0,
                "invalid_control_flow_failures": 0,
                "internal_control_failures": 0,
                "root_script_failures": 0,
                "link_session_attempt_count": 0,
                "rfu_session_attempt_count": 0,
                "rfu_session_failure_count": 0,
                "rfu_host_memory_write_count": 0,
                "center_link_session_attempt_count": 0,
                "center_link_session_failure_count": 0,
                "center_link_host_memory_write_count": 0,
                "side_effect_capture_failures": 0,
                "untested": 0, "warnings": 0,
                "results": [{
                    "case_id": case_id, "map": "96/23",
                    "owner_key": expected[case_id]["owner_key"],
                    "interaction_expected": expected[case_id][
                        "interaction_expected"
                    ],
                    "direction_plus_a": expected[case_id][
                        "interaction_expected"
                    ],
                    "actual_walk_required": expected[case_id][
                        "actual_walk_required"
                    ],
                    "actual_walk_steps": int(
                        expected[case_id]["interaction_expected"]
                        and expected[case_id]["actual_walk_required"]
                    ),
                    "walk_path_basis": expected[case_id][
                        "walk_path_basis"
                    ],
                    "interaction_distance": 1,
                    "map_level_real_walk_probe_required": False,
                } for case_id in shard],
                "fixture_count": len(shard),
                "interactive_count": interactive,
                "hidden_count": len(shard) - interactive,
                "input_sequence_attempt_count": attempts,
                "successful_path_count": attempts,
                "distinct_path_count": attempts,
                "artifacts": [],
            })
        merged = RUNNER._merge_catalog_shards(documents, expected)
        expected_attempts = sum(
            len(row["input_sequences"]) for row in expected.values()
        )
        self.assertEqual(merged["fixture_count"], len(expected))
        self.assertEqual(merged["input_sequence_attempt_count"], expected_attempts)
        self.assertEqual(merged["successful_path_count"], expected_attempts)
        self.assertEqual(merged["rfu_session_attempt_count"], 0)
        self.assertEqual(merged["rfu_session_sweep"]["count"], 0)
        self.assertEqual(
            [row["case_id"] for row in merged["results"]], sorted(expected),
        )

        duplicate = deepcopy(documents)
        duplicate[-1]["results"][-1]["case_id"] = duplicate[0]["results"][0][
            "case_id"
        ]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "重複/欠落"):
            RUNNER._merge_catalog_shards(duplicate, expected)

    def test_legacy_catalog_becomes_deterministic_calibration_tsv(self) -> None:
        normalized, calibration = RUNNER.validate_legacy_catalog_document(
            self._legacy_catalog()
        )
        self.assertEqual(normalized["script_object_count"], 1)
        self.assertEqual(set(calibration), {"cal-003-002-007"})
        row = calibration["cal-003-002-007"]
        self.assertEqual(row["object"], [11, 14])
        self.assertEqual(row["branches"], ["DEFAULT"])
        self.assertEqual(
            row["expected_template_raw_hex"],
            self._legacy_catalog()["npcs"][0]["expected_template_raw_hex"],
        )
        self.assertEqual(
            row["interaction_execution"],
            self._legacy_catalog()["npcs"][0]["interaction_execution"],
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "calibration.tsv"
            RUNNER.write_calibration_tsv(path, calibration)
            lines = path.read_text(encoding="ascii").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(len(lines[0].split("\t")), 30)
        self.assertEqual(len(lines[1].split("\t")), 30)
        calibration_fields = lines[1].split("\t")
        self.assertEqual(calibration_fields[5:8], ["11", "14", "0"])
        self.assertEqual(calibration_fields[8:11], ["NONE", "0", "0"])
        self.assertEqual(calibration_fields[11], "NONE")

        broken = self._legacy_catalog()
        broken["branch_count"] = 2
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "branch_count"):
            RUNNER.validate_legacy_catalog_document(broken)

    def test_expanded_state_persistence_phase_requires_restart_canaries(self) -> None:
        self.assertEqual(
            RUNNER._validate_reader_save_image_hash(
                "a" * 64, "a" * 64, label="unit-reader",
            ),
            "a" * 64,
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "131072-byte save SHA",
        ):
            RUNNER._validate_reader_save_image_hash(
                "a" * 64, "b" * 64, label="unit-reader",
            )
        for case in (
            "catalog_state_persistence",
            "catalog_state_legacy_persistence",
            "link_full_save_persistence",
        ):
            self.assertIn(
                "reader_save_image_unchanged",
                RUNNER._FINAL_MGBA_CASE_REQUIRED_KEYS[case],
            )
        catalog, _ = RUNNER.validate_catalog_document(self._catalog())
        _, matrix_rows = RUNNER.validate_state_matrix_document(
            self._state_matrix(), expected_rom_sha256="0" * 64,
        )
        fixture = RUNNER.project_catalog_state_matrix(
            catalog, matrix_rows,
            selected_case_ids=["matrix-096-023-015-default-000"],
        )["matrix-096-023-015-default-000"]
        fixture["expected_terminal"] = "FIELD_RELEASE"
        fixture["runtime_position_producer"] = (
            RUNNER._none_runtime_position_producer(
                fixture["interaction"]["group"],
                fixture["interaction"]["map"],
            )
        )
        interaction = fixture["interaction"]
        sequence = fixture["input_sequences"][0]
        capture = deepcopy(
            self._calibration_document()["results"][0][
                "successful_paths"
            ][0]["capture"]
        )
        fresh_read_consumer = {
            "fresh_process_after_title_continue": True,
            "branch_state_host_rewrites_after_continue": 0,
            "host_positioning_only": True,
            "stock_warp_map_load": True,
            "engine_teleport_map_load": False,
            "runtime_position_producer": (
                self._runtime_position_observation(
                    fixture["runtime_position_producer"],
                    RUNNER._none_runtime_position_control(),
                    requested=interaction["start"], visible=True,
                    host_prepare=False,
                )
            ),
            "object_visible": True,
            "visibility_framebuffer_fnv1a64": "7" * 16,
            "actual_walk_steps": len(interaction["walk_sequence"]),
            "approach_observation": self._approach_observation(
                interaction
            ),
            "preinteraction_object_identity": (
                self._preinteraction_identity(
                    interaction["expected_template_raw_hex"],
                    template_index=15, interactive=True,
                )
            ),
            "input_sequence_id": sequence["sequence_id"],
            "input_steps_consumed": len(sequence["tokens"]),
            "root_script_pointer_hits": 1,
            "first_root_script_pointer": "0x08100000",
            "capture": capture,
            "internal_controls": [],
            "deferred_external_controls": [],
            "field_roundtrip": self._field_roundtrip(),
            "post_battle": self._field_release_post_battle(),
            "post_battle_continuation": None,
            "side_effects": self._catalog_side_effects(),
            "effect_visibility_and_input_exact": True,
            "field_input_recovered": True,
            "exact": True,
        }
        document = {
            "schema_version": 3,
            "status": "PASS",
            "case": "catalog_state_persistence",
            "phase": "WRITE",
            "persistence_kind": "GENERATED",
            "case_id": fixture["case_id"],
            "base_case_id": fixture["base_case_id"],
            "fresh_title_continue": True,
            "fresh_process_rtc_offset_notice": False,
            "save_via_start_menu_input": True,
            "normal_save_generations": 2,
            "state_counts": {
                "flags": 1, "vars": 1, "items": 1, "trainers": 1,
            },
            "expanded_flag_readback": True,
            "expanded_var_readback": True,
            "expanded_state_zero_before_write": False,
            "legacy_save_zero_migration_baseline": False,
            "legacy_state_preserved": True,
            "legacy_state_fnv1a64": "1111111111111111",
            "sector31_full_preserved": True,
            "sector31_full_fnv1a64_before": "2222222222222222",
            "sector31_full_fnv1a64_after": "2222222222222222",
            "sector31_ledger_match": True,
            "sector31_ledger_fnv1a64": "0123456789ABCDEF",
            "legacy_saveblock1_var_canaries": [
                {"id": 0x4000, "value": 0x1357},
                {"id": 0x4040, "value": 0x2468},
                {"id": 0x40FF, "value": 0x369C},
            ],
            "fresh_read_consumer": None,
            "warnings": 0,
        }
        writer = RUNNER._validate_persistence_phase(
            document, fixture, "catalog_state_persist_write",
        )
        self.assertEqual(writer["normal_save_generations"], 2)
        self.assertTrue(writer["sector31_ledger_match"])
        reader_document = deepcopy(document)
        reader_document["phase"] = "READ"
        reader_document["fresh_process_rtc_offset_notice"] = True
        reader_document["save_via_start_menu_input"] = False
        reader_document["normal_save_generations"] = 0
        reader_document["expanded_state_zero_before_write"] = False
        reader_document["fresh_read_consumer"] = fresh_read_consumer
        reader = RUNNER._validate_persistence_phase(
            reader_document, fixture, "catalog_state_persist_read",
            charmap=RUNNER._read_charmap(),
        )
        self.assertEqual(reader["phase"], "READ")
        self.assertTrue(reader["fresh_read_consumer"]["exact"])
        self.assertEqual(
            reader["fresh_read_consumer"]["text_oracle_match"][
                "visible_text_count"
            ],
            1,
        )

        fraudulent_writer = deepcopy(document)
        fraudulent_writer["fresh_read_consumer"] = deepcopy(
            fresh_read_consumer
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "fresh physical consumer偽証跡",
        ):
            RUNNER._validate_persistence_phase(
                fraudulent_writer, fixture, "catalog_state_persist_write",
            )

        fresh_consumer_mutations = {
            "missing": lambda item: item.__setitem__(
                "fresh_read_consumer", None,
            ),
            "host-branch-rewrite": lambda item: item[
                "fresh_read_consumer"
            ].__setitem__("branch_state_host_rewrites_after_continue", 1),
            "walk-count": lambda item: item[
                "fresh_read_consumer"
            ].__setitem__("actual_walk_steps", 0),
            "movement-transition": lambda item: item[
                "fresh_read_consumer"
            ]["approach_observation"]["persistent_state"][
                "movement_owned_state"
            ]["poison_step_counter"].__setitem__("after", 4),
            "runtime-template": lambda item: item[
                "fresh_read_consumer"
            ]["preinteraction_object_identity"].__setitem__(
                "runtime_template_position", [13, 70],
            ),
            "field-roundtrip": lambda item: item[
                "fresh_read_consumer"
            ]["field_roundtrip"].__setitem__("start_menu_opened", False),
        }
        for label, mutate in fresh_consumer_mutations.items():
            broken = deepcopy(reader_document)
            mutate(broken)
            with self.subTest(fresh_consumer=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._validate_persistence_phase(
                    broken, fixture, "catalog_state_persist_read",
                )

        legacy_document = deepcopy(document)
        legacy_document["case"] = "catalog_state_legacy_persistence"
        legacy_document["persistence_kind"] = "LEGACY_STAGE60"
        legacy_document["fresh_process_rtc_offset_notice"] = True
        legacy_document["expanded_state_zero_before_write"] = True
        legacy_document["legacy_save_zero_migration_baseline"] = True
        legacy_document["legacy_saveblock1_var_canaries"] = []
        legacy_document["fresh_read_consumer"] = None
        legacy = RUNNER._validate_persistence_phase(
            legacy_document, fixture,
            "catalog_state_legacy_persist_write", legacy_source=True,
        )
        self.assertEqual(legacy["persistence_kind"], "LEGACY_STAGE60")

        corrupted = deepcopy(reader_document)
        corrupted["legacy_saveblock1_var_canaries"][1]["value"] ^= 1
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "canary"):
            RUNNER._validate_persistence_phase(
                corrupted, fixture, "catalog_state_persist_read",
            )

        corrupted_hash = deepcopy(reader_document)
        corrupted_hash["sector31_ledger_fnv1a64"] = "0123456789abcdef"
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "sector31"):
            RUNNER._validate_persistence_phase(
                corrupted_hash, fixture, "catalog_state_persist_read",
            )

    def test_legacy_save_contract_resolves_complete_latest_generation(self) -> None:
        self.assertEqual(RUNNER._fnv1a64(b""), "CBF29CE484222325")
        raw = bytearray(b"\xFF" * 0x20000)
        for identifier in range(14):
            section = bytearray(0x1000)
            section[0xFF4:0xFF6] = identifier.to_bytes(2, "little")
            section[0xFF8:0xFFC] = (0x08012025).to_bytes(4, "little")
            section[0xFFC:0x1000] = (7).to_bytes(4, "little")
            if identifier == 1:
                section[0:2] = (20).to_bytes(2, "little")
                section[2:4] = (21).to_bytes(2, "little")
                section[4:6] = bytes((96, 5))
            raw[identifier * 0x1000:(identifier + 1) * 0x1000] = section
        raw[31 * 0x1000:32 * 0x1000] = bytes(
            index & 0xFF for index in range(0x1000)
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "legacy.srm"
            path.write_bytes(raw)
            contract = RUNNER._legacy_save_contract(path)
        self.assertEqual(contract["latest_counter"], 7)
        self.assertEqual(
            contract["location"], {"x": 20, "y": 21, "group": 96, "map": 5},
        )
        self.assertEqual(contract["sector31"], bytes(raw[-0x1000:]))

    def test_last_ball_phase_requires_real_bag_keys_and_restart(self) -> None:
        fixtures = RUNNER.validate_fixture_document(
            deepcopy(RUNNER.DEFAULT_FIXTURE_DOCUMENT)
        )
        writer = {
            "schema_version": 2,
            "status": "PASS",
            "case": "last_ball_persistence",
            "phase": "WRITE",
            "fresh_title_continue": True,
            "fresh_process_rtc_offset_notice": True,
            "producer_via_normal_dialogue": True,
            "fresh_consumer_continue_before_battle": True,
            "stock_warp_before_battle": True,
            "actual_walk_direction_a_battle": True,
            "actual_battle_bag_direction_a": True,
            "battle_action_cursor_host_write": False,
            "battle_preparation_host_writes_only": True,
            "actual_walk_steps": 2,
            "battle_species": fixtures["story"]["snorlax_species"],
            "battle_outcome": 7,
            "master_ball_consumed": True,
            "last_used_ball_address": "0x0203B6EC",
            "last_used_ball": 1,
            "save_via_start_menu_input": True,
            "normal_save_generations": 2,
            "separate_process_readback": False,
            "warnings": 0,
        }
        validated = RUNNER._validate_last_ball_phase(
            writer, fixtures, "last_ball_persist_write",
        )
        self.assertTrue(validated["actual_battle_bag_direction_a"])
        reader = deepcopy(writer)
        reader.update({
            "phase": "READ",
            "producer_via_normal_dialogue": False,
            "fresh_consumer_continue_before_battle": False,
            "stock_warp_before_battle": False,
            "actual_walk_direction_a_battle": False,
            "actual_battle_bag_direction_a": False,
            "actual_walk_steps": 0,
            "battle_species": 0,
            "battle_outcome": 0,
            "save_via_start_menu_input": False,
            "normal_save_generations": 0,
            "separate_process_readback": True,
        })
        RUNNER._validate_last_ball_phase(
            reader, fixtures, "last_ball_persist_read",
        )
        direct_cursor = deepcopy(writer)
        direct_cursor["battle_action_cursor_host_write"] = True
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "last-ball"):
            RUNNER._validate_last_ball_phase(
                direct_cursor, fixtures, "last_ball_persist_write",
            )

    def test_link_full_phase_gates_delayed_id13_atomic_commit(self) -> None:
        writer = {
            "schema_version": 1,
            "status": "PASS",
            "case": "link_full_save_persistence",
            "phase": "WRITE",
            "fresh_title_continue": True,
            "fresh_process_rtc_offset_notice": False,
            "task_link_full_save_scheduler": True,
            "union_room_peer_barrier_fixture": True,
            "union_room_dynamic_warp_prepared": True,
            "task_entry": "0x080DB61D",
            "task_state_seed": 3,
            "task_states_seen": list(range(3, 12)),
            "handle_replace_symbol": "0x0943D458",
            "logical_record_chunk": 13,
            "previous_counter": 4,
            "committed_counter": 5,
            "delayed_signature_observed": True,
            "delayed_generation_valid_chunk_count": 13,
            "committed_generation_valid_chunk_count": 14,
            "record_payload_crc_exact": True,
            "atomic_sector_diff_count": 1,
            "atomic_sector_diff_offset": 0xFF8,
            "expanded_flag_var_last_ball_coins_readback": True,
            "sector31_full_preserved": True,
            "sector31_ledger_match": True,
            "sector31_ledger_fnv1a64": "0123456789ABCDEF",
            "separate_process_readback": False,
            "warnings": 0,
        }
        validated = RUNNER._validate_link_full_save_phase(
            writer, "link_full_save_persist_write",
        )
        self.assertEqual(validated["atomic_sector_diff_offset"], 0xFF8)
        reader = deepcopy(writer)
        reader.update({
            "phase": "READ",
            "task_link_full_save_scheduler": False,
            "union_room_peer_barrier_fixture": False,
            "union_room_dynamic_warp_prepared": False,
            "task_states_seen": [],
            "previous_counter": 5,
            "committed_counter": 5,
            "delayed_signature_observed": False,
            "delayed_generation_valid_chunk_count": 14,
            "atomic_sector_diff_count": 0,
            "atomic_sector_diff_offset": None,
            "separate_process_readback": True,
        })
        RUNNER._validate_link_full_save_phase(
            reader, "link_full_save_persist_read",
        )
        mixed = deepcopy(writer)
        mixed["delayed_generation_valid_chunk_count"] = 14
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "atomic"):
            RUNNER._validate_link_full_save_phase(
                mixed, "link_full_save_persist_write",
            )

    def test_calibration_gate_enriches_every_successful_choice(self) -> None:
        _, calibration = RUNNER.validate_legacy_catalog_document(
            self._legacy_catalog()
        )
        for fixture in calibration.values():
            fixture["runtime_position_producer"] = (
                RUNNER._none_runtime_position_producer(
                    fixture["group"], fixture["map"],
                )
            )
        raw = bytes.fromhex("a2a3462e0045032bff")
        document = self._calibration_document()
        result = RUNNER._validate_catalog_calibration(
            document, calibration, RUNNER._read_charmap(),
        )
        self.assertEqual(
            [path["choice"] for path in result["results"][0]["successful_paths"]],
            ["CANCEL", "NO"],
        )
        message = result["results"][0]["successful_paths"][0][
            "capture"
        ]["messages"][0]
        self.assertEqual(message["utf8"], "12ばん どうろ")
        self.assertEqual(message["raw_sha256"], hashlib.sha256(raw).hexdigest())

        invalid_port = deepcopy(document)
        invalid_port["results"][0]["port"]["start"] = [11, 15]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "objectの1歩隣接"):
            RUNNER._validate_catalog_calibration(
                invalid_port, calibration, RUNNER._read_charmap(),
            )

    def test_calibration_runtime_position_unresolved_visibility_is_exact(
        self,
    ) -> None:
        _, calibration = RUNNER.validate_legacy_catalog_document(
            self._legacy_catalog()
        )
        fixture = calibration["cal-003-002-007"]
        control = {"kind": "FLAG", "id": 0x1100, "value": True}
        producer = {
            "kind": "STOCK_WARP", "root": 0x08100000,
            "source_group": 3, "source_map": 1, "source_warp": 0,
            "predecessor_x": 5, "predecessor_y": 6,
            "trigger_x": 5, "trigger_y": 5,
            "trigger_key": RUNNER.KEYS["UP"],
            "destination_group": 3, "destination_map": 2,
            "destination_warp": 0,
            "arrival_x": 10, "arrival_y": 10,
            "record_address": 0x08100080,
            "map_script_tag": 3,
            "event_case_id": "calibration-runtime-position-unit",
            "source_provenance": {"unit": True},
        }
        fixture["runtime_position_map_load_required"] = True
        fixture["runtime_position_control"] = control
        fixture["runtime_position_producer"] = producer

        def unresolved_document(
            reason: str, observation: dict[str, object], *, port: bool,
        ) -> dict[str, object]:
            document = self._calibration_document()
            row = document["results"][0]
            row.update({
                "status": "UNRESOLVED", "failure_reason": reason,
                "attempted_ports": 1 if port else 4,
                "attempted_choices": 4 if port else 0,
                "port": row["port"] if port else None,
                "runtime_position_producer": observation,
                "successful_paths": [],
            })
            document.update({"resolved": 0, "unresolved": 1})
            return document

        finite_observation = self._runtime_position_observation(
            producer, control, requested=[11, 16], visible=True,
        )
        finite = unresolved_document(
            "NO_FINITE_VISIBLE_PATH", finite_observation, port=True,
        )
        RUNNER._validate_catalog_calibration(
            finite, calibration, RUNNER._read_charmap(),
        )

        final_probe = [9, 14]
        no_legal_observation = self._runtime_position_observation(
            producer, control, requested=[0, 0], visible=True,
        )
        no_legal_observation["local_player_positioning"]["after"] = (
            final_probe
        )
        no_legal = unresolved_document(
            "NO_LEGAL_APPROACH", no_legal_observation, port=False,
        )
        RUNNER._validate_catalog_calibration(
            no_legal, calibration, RUNNER._read_charmap(),
        )

        no_visible_observation = self._runtime_position_observation(
            producer, control, requested=[0, 0], visible=False,
        )
        no_visible_observation[
            "target_materialization_deferred_to_real_walk"
        ] = True
        no_visible_observation["local_player_positioning"]["after"] = (
            final_probe
        )
        no_visible_observation["local_player_positioning"]["exact"] = False
        no_visible_observation["exact"] = False
        no_visible = unresolved_document(
            "NO_VISIBLE_OBJECT", no_visible_observation, port=False,
        )
        RUNNER._validate_catalog_calibration(
            no_visible, calibration, RUNNER._read_charmap(),
        )

        wrong_final_probe = deepcopy(no_visible)
        wrong_final_probe["results"][0]["runtime_position_producer"][
            "local_player_positioning"
        ]["after"] = [0, 0]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "local positioning",
        ):
            RUNNER._validate_catalog_calibration(
                wrong_final_probe, calibration, RUNNER._read_charmap(),
            )

        incomplete_port_probe = deepcopy(no_legal)
        incomplete_port_probe["results"][0]["attempted_ports"] = 3
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "unresolved port probe数",
        ):
            RUNNER._validate_catalog_calibration(
                incomplete_port_probe, calibration, RUNNER._read_charmap(),
            )

    def test_full_calibration_promotes_all_successes_to_strict_catalog(self) -> None:
        digest = "a" * 64
        oracle = self._catalog()
        oracle["rom_sha256"] = digest
        entry = oracle["entries"][0]  # type: ignore[index]
        entry.update({
            "case_id": "cal-003-002-007",
            "owner_key": "OBJECT:003/002:007",
            "group": 3, "map": 2, "local_id": 8,
            "object": [11, 14], "start": [11, 16], "action": "UP",
            "interaction_execution": self._physical_interaction_execution(
                start=[11, 16], walk_sequence=["UP"],
                stance=[11, 15], action="UP",
            ),
            "expected_template_raw_hex": self._object_template_raw(
                local_id=8, graphics_id=18, x=11, y=14,
                movement_type=9, script_pointer=0x08100000,
            ),
        })
        independent_hashes = ("b" * 64, "c" * 64)
        entry["branches"] = [
            {
                "branch_id": f"independent_{choice.lower()}",
                "flags": [], "choice": choice,
                "terminal": "FIELD_RELEASE",
                "expected_raw_sha256_any": [independent_hashes[index]],
                "expected_utf8_contains_any": [f"independent-{choice}"],
                "expected_var_result_values_exact": None,
                "require_visible_text": True,
                "expect_object_visible": True,
            }
            for index, choice in enumerate(("CANCEL", "NO"))
        ]
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "independent_oracle_catalog",
        ):
            RUNNER.build_strict_catalog_from_calibration(
                self._legacy_catalog(), self._calibration_document(),
                rom_sha256=digest,
            )
        strict = RUNNER.build_strict_catalog_from_calibration(
            self._legacy_catalog(), self._calibration_document(),
            rom_sha256=digest, independent_oracle_catalog=oracle,
        )
        normalized, expanded = RUNNER.validate_catalog_document(
            strict, expected_rom_sha256=digest,
        )
        self.assertEqual(len(normalized["entries"]), 1)
        self.assertEqual(
            normalized["entries"][0]["interaction_execution"],
            self._legacy_catalog()["npcs"][0]["interaction_execution"],
        )
        self.assertEqual(
            normalized["entries"][0]["expected_template_raw_hex"],
            self._legacy_catalog()["npcs"][0]["expected_template_raw_hex"],
        )
        self.assertEqual(
            set(expanded),
            {
                "cal-003-002-007--independent_cancel",
                "cal-003-002-007--independent_no",
            },
        )
        self.assertEqual(
            {
                row["branch"]["expected_raw_sha256_any"][0]
                for row in expanded.values()
            },
            set(independent_hashes),
        )
        self.assertTrue(all(
            row["branch"]["expected_var_result_values_exact"] is None
            for row in expanded.values()
        ))

        calibration_result = self._calibration_document()
        calibration_sha256 = RUNNER._sha256(
            RUNNER._stable(calibration_result).encode("utf-8")
        )
        shard_sha256 = "d" * 64
        wrapper = {
            "schema_version": 1,
            "task": RUNNER.TASK,
            "stage": RUNNER.STAGE,
            "status": "PASS",
            "rom_sha256": digest,
            "calibration_source": {
                "full_catalog": True,
                "failed": 0,
                "untested": 0,
                "script_object_count": 1,
                "source_script_object_count": 1,
            },
            "results": {
                "catalog_calibrate": {
                    "status": "PASS",
                    "process_runs": 2,
                    "process_shards": 1,
                    "same_shard_boundaries_across_runs": True,
                    "per_shard_identical_results": True,
                    "per_shard_result_sha256": [shard_sha256],
                    "per_run_merged_result_sha256": [
                        calibration_sha256, calibration_sha256,
                    ],
                    "per_run_per_shard_result_sha256": [
                        [shard_sha256], [shard_sha256],
                    ],
                    "identical_results": True,
                    "result": calibration_result,
                },
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            legacy_path = directory / "legacy.json"
            calibration_path = directory / "calibration.json"
            output_path = directory / "strict.json"
            oracle_path = directory / "oracle.json"
            legacy_path.write_text(
                json.dumps(self._legacy_catalog()), encoding="utf-8",
            )
            calibration_path.write_text(
                json.dumps(wrapper), encoding="utf-8",
            )
            oracle_path.write_text(json.dumps(oracle), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable, str(RUNNER_PATH),
                    "--legacy-catalog", str(legacy_path),
                    "--calibration-result", str(calibration_path),
                    "--independent-oracle-catalog", str(oracle_path),
                    "--write-strict-catalog", str(output_path),
                ],
                cwd=ROOT, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=120, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stderr, "")
            promoted = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(promoted, json.loads(completed.stdout))
            self.assertEqual(len(promoted["entries"][0]["branches"]), 2)
            self.assertEqual(
                promoted["entries"][0]["interaction_execution"],
                self._legacy_catalog()["npcs"][0][
                    "interaction_execution"
                ],
            )

            single_process = deepcopy(wrapper)
            run = single_process["results"]["catalog_calibrate"]
            run["process_runs"] = 1
            run["per_run_merged_result_sha256"] = [calibration_sha256]
            run["per_run_per_shard_result_sha256"] = [[shard_sha256]]
            single_path = directory / "single-process.json"
            single_path.write_text(json.dumps(single_process), encoding="utf-8")
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "独立2 process",
            ):
                RUNNER.load_full_calibration_run(
                    single_path, expected_script_object_count=1,
                )

    def test_all_case_oracle_promotion_uses_matrix_semantics_not_calibration(
        self,
    ) -> None:
        digest = "a" * 64
        matrix, oracle = self._all_case_promotion_inputs(digest)
        strict = RUNNER.build_strict_catalog_from_calibration(
            self._legacy_catalog(), self._calibration_document(),
            rom_sha256=digest, independent_oracle_catalog=oracle,
            state_matrix=matrix,
        )
        branch = strict["entries"][0]["branches"][0]
        self.assertEqual(
            strict["entries"][0]["interaction_execution"],
            self._legacy_catalog()["npcs"][0]["interaction_execution"],
        )
        self.assertEqual(branch, {
            "branch_id": "DEFAULT",
            "identity_only": True,
            "semantic_contract": RUNNER._IDENTITY_ONLY_BRANCH_CONTRACT,
            "matrix_case_ids": ["matrix-003-002-007-default-000"],
            "matrix_case_binding_sha256": branch[
                "matrix_case_binding_sha256"
            ],
        })
        self.assertRegex(branch["matrix_case_binding_sha256"], r"^[0-9a-f]{64}$")
        _, matrix_rows = RUNNER.validate_state_matrix_document(
            matrix, expected_rom_sha256=digest,
        )
        projected = RUNNER.project_catalog_state_matrix(strict, matrix_rows)
        self.assertEqual(set(projected), set(matrix_rows))
        self.assertTrue(
            RUNNER.validate_identity_only_strict_catalog_contract(
                strict, matrix_rows,
            )
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "LEGACY_EXPECTATION",
        ):
            RUNNER.validate_identity_only_strict_catalog_contract(
                self._catalog(), matrix_rows,
            )
        self.assertNotIn("choice", branch)
        self.assertNotIn("expected_raw_sha256_any", branch)

        calibration_result = self._calibration_document()
        merged_sha = RUNNER._sha256(
            RUNNER._stable(calibration_result).encode("utf-8")
        )
        shard_sha = "e" * 64
        wrapper = {
            "schema_version": 1, "task": RUNNER.TASK,
            "stage": RUNNER.STAGE, "status": "PASS",
            "rom_sha256": digest,
            "calibration_source": {
                "full_catalog": True, "failed": 0, "untested": 0,
                "script_object_count": 1,
                "source_script_object_count": 1,
            },
            "results": {"catalog_calibrate": {
                "status": "PASS", "process_runs": 2, "process_shards": 1,
                "same_shard_boundaries_across_runs": True,
                "per_shard_identical_results": True,
                "per_shard_result_sha256": [shard_sha],
                "per_run_merged_result_sha256": [merged_sha, merged_sha],
                "per_run_per_shard_result_sha256": [
                    [shard_sha], [shard_sha],
                ],
                "identical_results": True, "result": calibration_result,
            }},
        }
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            paths = {
                "legacy": directory / "legacy.json",
                "calibration": directory / "calibration.json",
                "oracle": directory / "oracle.json",
                "matrix": directory / "matrix.json",
                "output": directory / "strict.json",
            }
            for key, source in (
                ("legacy", self._legacy_catalog()),
                ("calibration", wrapper), ("oracle", oracle),
                ("matrix", matrix),
            ):
                paths[key].write_text(json.dumps(source), encoding="utf-8")
            completed = subprocess.run([
                sys.executable, str(RUNNER_PATH),
                "--legacy-catalog", str(paths["legacy"]),
                "--calibration-result", str(paths["calibration"]),
                "--independent-oracle-catalog", str(paths["oracle"]),
                "--state-matrix", str(paths["matrix"]),
                "--write-strict-catalog", str(paths["output"]),
            ], cwd=ROOT, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=120, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                json.loads(completed.stdout),
                json.loads(paths["output"].read_text(encoding="utf-8")),
            )

    def test_all_case_oracle_promotion_rejects_cross_source_mutations(
        self,
    ) -> None:
        digest = "a" * 64

        def resign(
            matrix: dict[str, object], oracle: dict[str, object],
        ) -> None:
            for row in oracle["cases"]:
                if row.get("kind") \
                        == "STAGE61_INDEPENDENT_INTERACTION_ORACLE":
                    row.pop("oracle_sha256", None)
                    row["oracle_sha256"] = RUNNER._oracle_canonical_sha256(row)
            oracle.pop("audit_sha256", None)
            oracle["audit_sha256"] = RUNNER._oracle_canonical_sha256(oracle)
            digest_value = RUNNER._oracle_canonical_sha256(oracle)
            matrix["oracle"]["catalog_sha256"] = digest_value
            matrix["runtime_control_expansion"][
                "oracle_catalog_sha256"
            ] = digest_value

        mutations = {}
        matrix, oracle = self._all_case_promotion_inputs(digest)
        oracle["cases"] = []
        oracle["case_count"] = 0
        oracle["generated_case_count"] = 0
        matrix["oracle"]["case_count"] = 0
        resign(matrix, oracle)
        mutations["case-missing"] = (matrix, oracle)

        matrix, oracle = self._all_case_promotion_inputs(digest)
        oracle["cases"][0]["owner_key"] = "OBJECT:003/002:099"
        resign(matrix, oracle)
        mutations["owner"] = (matrix, oracle)

        matrix, oracle = self._all_case_promotion_inputs(digest)
        matrix["cases"][0]["base_case_id"] = "cal-003-002-099"
        mutations["base"] = (matrix, oracle)

        matrix, oracle = self._all_case_promotion_inputs(digest)
        oracle["cases"][0]["input_sequences"][0]["tokens"] = ["A", "B"]
        oracle["cases"][0]["sequences"][0]["tokens"] = ["A", "B"]
        resign(matrix, oracle)
        mutations["sequence"] = (matrix, oracle)

        matrix, oracle = self._all_case_promotion_inputs(digest)
        text = oracle["cases"][0]["input_sequences"][0]["text_oracle"]
        text["ordered_printers"][0]["raw_sha256"] = "f" * 64
        oracle["cases"][0]["sequences"][0]["visible_printers"][0][
            "raw_sha256"
        ] = "f" * 64
        resign(matrix, oracle)
        mutations["text-hash"] = (matrix, oracle)

        matrix, oracle = self._all_case_promotion_inputs(digest)
        oracle["cases"][0]["input_sequences"][0]["text_oracle"][
            "provenance"
        ]["not_learned_from_mgba_calibration"] = False
        resign(matrix, oracle)
        mutations["calibration-learning"] = (matrix, oracle)

        for label, (matrix, oracle) in mutations.items():
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER.build_strict_catalog_from_calibration(
                    self._legacy_catalog(), self._calibration_document(),
                    rom_sha256=digest,
                    independent_oracle_catalog=oracle,
                    state_matrix=matrix,
                )

    def test_calibration_shards_cover_once_and_merge_deterministically(self) -> None:
        base = {
            f"cal-001-001-{index:03d}": {"ordinal": index}
            for index in range(5)
        }
        shards = RUNNER._partition_calibration(base, 3)
        self.assertEqual([len(shard) for shard in shards], [2, 2, 1])
        self.assertEqual(
            set().union(*(set(shard) for shard in shards)), set(base),
        )
        documents = []
        for shard_index, shard in enumerate(shards):
            rows = [{"case_id": case_id} for case_id in reversed(shard)]
            documents.append({
                "schema_version": 2,
                "status": "PASS",
                "case": "catalog_calibrate",
                "baseline_natural_continue": True,
                "choice_probe_via_state_restore": True,
                "pulse_limit": 16,
                "results": rows,
                "fixture_count": len(rows),
                "resolved": len(rows),
                "unresolved": 0,
                "failed": 0,
                "untested": 0,
                "warnings": 0,
                "artifacts": [{
                    "path": f"proof-{shard_index}.ppm",
                    "size": 1,
                    "sha256": "0" * 64,
                }],
            })
        merged = RUNNER._merge_calibration_shards(documents)
        self.assertEqual(merged["fixture_count"], 5)
        self.assertEqual(merged["resolved"], 5)
        self.assertEqual(
            [row["case_id"] for row in merged["results"]], sorted(base),
        )
        self.assertEqual(merged["artifacts"][1]["path"], "shard-2/proof-1.ppm")

    def test_msc17_transition_fixtures_require_real_adjacent_warp(self) -> None:
        rows = [
            RUNNER.validate_consumer_transition_fixture(row)
            for row in RUNNER.DEFAULT_CONSUMER_TRANSITIONS
        ]
        self.assertEqual(
            [(row["source"]["group"], row["source"]["map"])
             for row in rows],
            [(6, 2), (98, 0)],
        )
        self.assertIn(
            "msc17_quest_log_transitions", RUNNER.CASE_DOMAINS["consumers"],
        )
        environment = RUNNER._consumer_transition_environment(rows[0])
        self.assertEqual(environment["S61_TRANSITION_ACTION_KEY"], "128")
        self.assertEqual(environment["S61_TRANSITION_EXPECTED_ENTRANCE"], "8")
        invalid = deepcopy(rows[0])
        invalid["warp_tile"] = [6, 15]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "実歩行1歩先"):
            RUNNER.validate_consumer_transition_fixture(invalid)

    def test_msc17_transition_result_requires_departed_event_delta(self) -> None:
        fixture = RUNNER.validate_consumer_transition_fixture(
            RUNNER.DEFAULT_CONSUMER_TRANSITIONS[0]
        )
        source = fixture["source"]
        destination = fixture["destination"]
        document = {
            "schema_version": 1,
            "status": "PASS",
            "case": "consumer_warp_transition",
            "case_id": fixture["case_id"],
            "preparation_only_host_writes": True,
            "entry_check_via_stock_map_load": True,
            "exit_try_via_actual_walk": True,
            "source": f"{source['group']}/{source['map']}",
            "start": source["start"],
            "warp_tile": fixture["warp_tile"],
            "destination": f"{destination['group']}/{destination['map']}",
            "action_key": RUNNER.KEYS[fixture["action"]],
            "transition_frames": 77,
            "prepared": {"flag": False, "var": fixture["sentinel"]},
            "after_check": {
                "flag": True, "var": fixture["expected_entrance"],
            },
            "after_try": {
                "flag": False, "var": fixture["expected_post_var"],
            },
            "quest_log": {
                "before_map_fnv1a64": "0" * 16,
                "before_exit_fnv1a64": "1" * 16,
                "after_exit_fnv1a64": "2" * 16,
                "departed_before_map": 0,
                "departed_before_exit": 0,
                "departed_after_exit": 1,
                "matching_before_exit": 0,
                "matching_after_exit": 1,
                "last_section": 88,
                "last_location": fixture["expected_entrance"],
            },
            "input_recovered": True,
            "failed": 0,
            "untested": 0,
            "warnings": 0,
        }
        result = RUNNER._validate_consumer_transition_result(document, fixture)
        self.assertEqual(result["case_id"], fixture["case_id"])
        missing = deepcopy(document)
        missing["quest_log"]["departed_after_exit"] = 0
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "event未生成"):
            RUNNER._validate_consumer_transition_result(missing, fixture)

    def test_msc17_lifecycle_requires_component_preserve_and_rearm(self) -> None:
        document = {
            "schema_version": 1, "status": "PASS",
            "case": "quest_log_lifecycle",
            "stock_map_load_checks": True,
            "actual_warp_tile_tries": True,
            "two_hop": {
                "location": 19, "canonical_inside": "97/5",
                "component_extra": "97/4",
                "component_landing": [32, 15], "component_frames": 20,
                "pending_preserved": True, "departed_before": 2,
                "departed_after_component": 2,
                "canonical_exit": "96/5", "exit_landing": [30, 6],
                "exit_frames": 40, "pending_cleared": True,
                "event35_generated": True, "matching_before_exit": 0,
                "matching_after_exit": 1,
            },
            "mismatch_rearm": {
                "location_before": 19, "mismatch_destination": "97/6",
                "mismatch_landing": [3, 9], "mismatch_frames": 20,
                "pending_cleared": True, "event35_generated": False,
                "departed_before": 2, "departed_after": 2,
                "rearm_inside": "98/12", "rearmed_location": 8,
                "rearmed": True,
            },
            "input_recovered": True, "failed": 0, "untested": 0,
            "warnings": 0,
        }
        result = RUNNER._validate_quest_log_lifecycle_result(document)
        self.assertEqual(result["two_hop"]["component_landing"], [32, 15])
        invalid = deepcopy(document)
        invalid["mismatch_rearm"]["rearmed"] = False
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "rearm"):
            RUNNER._validate_quest_log_lifecycle_result(invalid)

    def test_warp_preview_requires_stock_hooks_and_exact_duration(self) -> None:
        fixture = RUNNER.DEFAULT_WARP_PREVIEW_TRANSITIONS[0]
        source = fixture["source"]
        destination = fixture["destination"]
        document = {
            "schema_version": 1, "status": "PASS",
            "case": "warp_preview_transition",
            "case_id": fixture["case_id"],
            "preparation_only_host_writes": True,
            "actual_warp_via_player_input": True,
            "source": f"{source['group']}/{source['map']}",
            "start": source["start"], "warp_tile": fixture["warp_tile"],
            "destination": f"{destination['group']}/{destination['map']}",
            "destination_warp_id": destination["warp_id"],
            "landing": [17, 3], "action_key": RUNNER.KEYS[fixture["action"]],
            "initially_visited": fixture["initially_visited"],
            "visit_flag": fixture["visit_flag"], "visit_flag_after": True,
            "preview_duration": fixture["expected_duration"],
            "duration_task_slot": 2,
            "hook_hits": {
                "stock_warp_fade": 1, "stock_preview_index": 1,
                "cfru_warp_fade": 0,
            },
            "transition_frames": 240, "input_recovered": True,
            "failed": 0, "untested": 0, "warnings": 0,
        }
        result = RUNNER._validate_warp_preview_result(document, fixture)
        self.assertEqual(result["preview_duration"], 120)
        wrong_owner = deepcopy(document)
        wrong_owner["hook_hits"]["cfru_warp_fade"] = 1
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "provenance"):
            RUNNER._validate_warp_preview_result(wrong_owner, fixture)

    def test_raid_consumer_requires_script_and_collision_canaries(self) -> None:
        symbols = {
            "resolver": 0x0943DAB0, "get": 0x0943DAEC,
            "set": 0x0943DB1C, "clear": 0x0943DB4C,
        }
        rows = []
        for fixture in RUNNER.DEFAULT_RAID_CONSUMERS:
            index = fixture["raid_index"]
            storage = 0x15C0 + index
            rows.append({
                **fixture,
                "logical_flag": 0x1800 + index,
                "storage_flag": storage,
                "neighbor_flag": storage + 1,
                "set_special": {
                    "storage_set": True,
                    "logical_canary_preserved": True,
                    "neighbor_preserved": True,
                },
                "clear_special": {
                    "storage_cleared": True,
                    "logical_canary_preserved": True,
                    "neighbor_preserved": True,
                },
                "legacy_adapter": {
                    "get_true": True, "storage_set": True,
                    "logical_bit_clear": True, "storage_cleared": True,
                },
                "input_recovered": True,
            })
        document = {
            "schema_version": 1,
            "status": "PASS",
            "case": "raid_flag_collision",
            "special_via_ewram_script_context1": True,
            "direct_special_function_call": False,
            "resolver_symbol": f"0x{symbols['resolver']:08X}",
            "flag_adapter_symbols": [
                f"0x{symbols[key]:08X}" for key in ("get", "set", "clear")
            ],
            "results": rows,
            "fixture_count": len(rows),
            "failed": 0,
            "untested": 0,
            "warnings": 0,
        }
        result = RUNNER._validate_raid_flag_collision(document, symbols)
        self.assertEqual(result["fixture_count"], 3)
        collision = deepcopy(document)
        collision["results"][0]["set_special"][
            "logical_canary_preserved"
        ] = False
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "collision"):
            RUNNER._validate_raid_flag_collision(collision, symbols)

    def test_save_corruption_matrix_is_complete_and_bounded(self) -> None:
        raw = bytearray([0xFF] * 0x20000)
        for physical_base, counter in ((0, 2), (14, 3)):
            for identifier in range(14):
                physical = physical_base + identifier
                start = physical * 0x1000
                raw[start + 0xFF4:start + 0xFF6] = identifier.to_bytes(
                    2, "little",
                )
                raw[start + 0xFF6:start + 0xFF8] = b"\x00\x00"
                raw[start + 0xFF8:start + 0xFFC] = (
                    0x08012025
                ).to_bytes(4, "little")
                raw[start + 0xFFC:start + 0x1000] = counter.to_bytes(
                    4, "little",
                )
        cases = RUNNER._build_save_corruption_cases(bytes(raw))
        self.assertEqual(len(cases), 17)
        self.assertEqual(len({case["case_id"] for case in cases}), 17)
        self.assertEqual(
            tuple(case["case_id"] for case in cases),
            RUNNER._SAVE_CORRUPTION_FIXTURE_IDS,
        )
        final_rows = [
            {"fixture_id": value}
            for value in RUNNER._SAVE_CORRUPTION_FIXTURE_IDS
        ]
        RUNNER._validate_save_corruption_fixture_id_sequence(final_rows)
        replaced = deepcopy(final_rows)
        replaced[0]["fixture_id"] = "arbitrary_unique_replacement"
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "fixture ID coverage",
        ):
            RUNNER._validate_save_corruption_fixture_id_sequence(replaced)
        self.assertEqual(
            len({hashlib.sha256(case["image"]).digest() for case in cases}),
            len(cases),
        )
        by_id = {case["case_id"]: case for case in cases}
        self.assertEqual(
            by_id["valid_signature_footer_id14"]["expected_status"], 0xFF,
        )
        self.assertFalse(
            by_id["both_slots_invalid_fail_closed"]["expected_valid"],
        )
        self.assertEqual(
            by_id["counter_wrap_ffffffff_to_zero"]["expected_counter"], 0,
        )
        self.assertEqual(
            by_id["counter_wrap_fffffffe_to_one"]["expected_counter"], 1,
        )
        self.assertEqual(
            by_id["counter_reverse_two_vs_ffffffff_first"][
                "expected_counter"
            ], 2,
        )
        self.assertEqual(
            by_id["counter_half_range_minus_one_second"][
                "expected_counter"
            ], 0x80000001,
        )
        self.assertEqual(
            by_id["counter_half_range_plus_one_first"][
                "expected_counter"
            ], 2,
        )
        self.assertEqual(
            by_id["counter_wrap_fffffffe_to_one"][
                "expected_first_sector"
            ], 0,
        )
        self.assertFalse(
            by_id["both_slots_physical_rotation_invalid_no_copy"][
                "expected_valid"
            ]
        )
        tear = by_id["selected_then_torn_before_copy"]
        self.assertEqual(tear["expected_selected_counter"], 3)
        self.assertEqual(tear["expected_counter"], 2)
        self.assertEqual(tear["tear_physical"], 27)
        footer = 27 * 0x1000 + RUNNER._SAVE_SIGNATURE_OFFSET
        self.assertEqual(
            by_id["missing_chunk_full_mask"]["image"][footer:footer + 4],
            b"\xFF" * 4,
        )
        self.assertEqual(
            by_id["newest_torn_precommit_signature"]["image"][footer],
            0xFF,
        )

    def test_save_corruption_flash_transition_is_three_way_exact(self) -> None:
        base = {
            "tear_after_selection_before_copy": False,
            "resave_after_fallback": False,
            "input_image_sha256": "1" * 64,
            "output_image_sha256": "1" * 64,
            "flash_changed_offsets": [],
            "resave_via_start_menu_input": False,
            "resave_fresh_continue": False,
            "resave_canaries_exact": False,
            "resave_field_input_recovered": False,
        }
        RUNNER._validate_save_corruption_flash_transition(base)
        resave = deepcopy(base)
        resave.update({
            "resave_after_fallback": True,
            "output_image_sha256": "2" * 64,
            "flash_changed_offsets": [0x1000],
            "resave_via_start_menu_input": True,
            "resave_fresh_continue": True,
            "resave_canaries_exact": True,
            "resave_field_input_recovered": True,
        })
        RUNNER._validate_save_corruption_flash_transition(resave)
        tear = deepcopy(base)
        tear.update({
            "tear_after_selection_before_copy": True,
            "output_image_sha256": "2" * 64,
            "flash_changed_offsets": [0x1FFF],
        })
        RUNNER._validate_save_corruption_flash_transition(tear)
        false_immutable = deepcopy(base)
        false_immutable.update({
            "output_image_sha256": "2" * 64,
            "flash_changed_offsets": [0x1000],
        })
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "immutable probe",
        ):
            RUNNER._validate_save_corruption_flash_transition(false_immutable)
        false_resave = deepcopy(resave)
        false_resave["flash_changed_offsets"] = []
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "resave FLASH",
        ):
            RUNNER._validate_save_corruption_flash_transition(false_resave)

    def test_save_counter_comparator_is_half_range_modular(self) -> None:
        vectors = (
            (0xFFFFFFFE, 1, True),
            (1, 0xFFFFFFFE, False),
            (7, 7, False),
            (7, 0x80000007, False),
            (0x80000007, 7, False),
        )
        for first, second, expected in vectors:
            with self.subTest(first=first, second=second):
                self.assertIs(
                    RUNNER._second_save_counter_is_newer(first, second),
                    expected,
                )

    def test_both_invalid_save_proves_start_and_back_ui_responsiveness(
        self,
    ) -> None:
        expected = {
            "case_id": "both_slots_invalid_fail_closed",
            "expected_valid": False, "expected_status": 2,
            "expected_selected_counter": 0, "tear_physical": None,
            "expected_counter": 0, "expected_first_sector": 0,
            "expected_selected_first_sector": 0,
            "expected_owner_fnv1a64": "0" * 16,
            "resave_after_fallback": False,
        }
        document = {
            "schema_version": 2, "status": "PASS",
            "case": "save_corruption_probe",
            "fixture_id": expected["case_id"], "expected_valid": False,
            "fresh_title_continue": False, "no_continue_safe_ui": True,
            "fresh_mcore_boot": True, "runtime_loader_fresh_mcore": True,
            "get_save_valid_status": 2, "handle_load_status": 1,
            "selected_owner_image_size": 0,
            "selected_owner_image_fnv1a64": "0" * 16,
            "selected_owner_full_byte_exact": False,
            "selected_counter_before_load": 0,
            "selected_first_sector_before_load": 0,
            "tear_after_selection_before_copy": False,
            "tear_physical_sector": None, "expected_counter": 0,
            "selected_counter": 0,
            "selected_first_sector": 0,
            "saveblock1_saveblock2_storage_unchanged": True,
            "resave_after_fallback": False,
            "resave_via_start_menu_input": False,
            "resave_fresh_continue": False,
            "resave_canaries_exact": False,
            "resave_field_input_recovered": False,
            "resave_selected_counter": 0,
            "resave_selected_first_sector": 0,
            # B is allowed to return to the exact initial title frame.  The
            # intermediate START frame proves both key transitions instead
            # of incorrectly requiring before != after-B.
            "safe_ui_framebuffer_before_fnv1a64": "1" * 16,
            "safe_ui_framebuffer_start_fnv1a64": "2" * 16,
            "safe_ui_framebuffer_after_fnv1a64": "1" * 16,
            "input_recovered": True, "warnings": 0,
        }
        result = RUNNER._validate_save_corruption_probe(document, expected)
        self.assertTrue(result["no_continue_safe_ui"])
        no_start_response = deepcopy(document)
        no_start_response["safe_ui_framebuffer_start_fnv1a64"] = "1" * 16
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "safe UI"):
            RUNNER._validate_save_corruption_probe(no_start_response, expected)

    def test_partial_link_phase_requires_exact_record_interval(self) -> None:
        writer = {
            "schema_version": 1, "status": "PASS",
            "case": "partial_link_save_persistence", "phase": "WRITE",
            "fresh_title_continue": True,
            "generic_save_link_wrapper": True,
            "save_ereader_stock_only": True,
            "record_only_symbol": "0x0943D100",
            "handle_saving_symbol": "0x0943D200",
            "selected_counter": 3,
            "selected_id13_physical_sector": 27,
            "link_result": 0, "ereader_result": 0,
            "record_changed_bytes": 144,
            "record_outside_changed_bytes": 0,
            "backup_slot_changed_bytes": 0,
            "ereader_id13_changed_bytes": 0,
            "record_payload_crc_exact": True,
            "injected_erase_failure_result": 0xFF,
            "injected_failure_damaged_state": True,
            "injected_failure_flash_changed_bytes": 0,
            "program_failure_count": 3,
            "program_failure_results": [
                {
                    "failure_id": failure_id,
                    "target_offset": target,
                    "program_calls_before_failure": calls,
                    "result": 0xFF,
                    "damaged_state": True,
                    "flash_changed_bytes": 0x800,
                    "active_signature_invalid": True,
                    "backup_slot_unchanged": True,
                    "selector_status": 0xFF,
                    "fallback_generation_selected": True,
                }
                for failure_id, target, calls in (
                    ("first_program_byte", 0, 0),
                    ("record_middle", 0x7D0 + 0x616 // 2,
                     0x7D0 + 0x616 // 2),
                    ("signature_commit_byte", 0xFF8, 0xFFF),
                )
            ],
            "expanded_flag_var_last_ball_coins_readback": True,
            "separate_process_readback": False, "warnings": 0,
        }
        result = RUNNER._validate_partial_link_phase(writer, writer=True)
        self.assertEqual(result["record_changed_bytes"], 144)
        leaked = deepcopy(writer)
        leaked["record_outside_changed_bytes"] = 1
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "契約不一致"):
            RUNNER._validate_partial_link_phase(leaked, writer=True)
        non_atomic = deepcopy(writer)
        non_atomic["injected_failure_flash_changed_bytes"] = 1
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "atomic"):
            RUNNER._validate_partial_link_phase(non_atomic, writer=True)
        accepted_torn = deepcopy(writer)
        accepted_torn["program_failure_results"][2][
            "fallback_generation_selected"
        ] = False
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "program failure"):
            RUNNER._validate_partial_link_phase(accepted_torn, writer=True)
        wrong_slot = deepcopy(writer)
        wrong_slot["selected_id13_physical_sector"] = 13
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "sector/slot parity"):
            RUNNER._validate_partial_link_phase(wrong_slot, writer=True)

    def test_save_link_silent_success_media_faults_are_exact_and_fail_closed(
        self,
    ) -> None:
        phases = {
            "PREFLIGHT": {
                "callbacks": 57358, "target_slot": 1,
                "protected_counter": 0, "target_counter": 1,
            },
            "STOCK": {
                "callbacks": 20485, "target_slot": 0,
                "protected_counter": 1, "target_counter": 0,
            },
            "POST": {
                "callbacks": 57359, "target_slot": 1,
                "protected_counter": 0, "target_counter": 1,
            },
        }

        def row(
            mode: str, phase: str, kind: str, ordinal: int,
        ) -> dict[str, object]:
            program = kind == "PROGRAM"
            wrong = mode == "PROGRAM_WRONG_BYTE_SUCCESS"
            erase = mode == "ERASE_SILENT_SUCCESS_NO_EFFECT"
            return {
                "mode": mode, "scenario": "EMPTY", "phase": phase,
                "callback_kind": kind,
                "phase_callback_ordinal": ordinal,
                "callback_owner": "0x09ABCDEF", "physical_sector": 27,
                "offset": 0xFF8 if program else None,
                "expected_byte": 0x25 if program else None,
                "injected_byte": 0x24 if wrong else None,
                "observed_byte_before": 0xFF if program else None,
                "observed_byte_after": (
                    0x24 if wrong else 0xFF if program else None
                ),
                "callback_body_executed": True,
                "callback_status_before_force": 0,
                "callback_return_forced_success": True,
                "immediate_changed_bytes": 1 if wrong else 0,
                "immediate_media_unchanged": not wrong,
                "sector_fnv1a64_before": (
                    "AAAAAAAAAAAAAAAA" if not wrong else "CCCCCCCCCCCCCCCC"
                ),
                "sector_fnv1a64_immediate": (
                    "AAAAAAAAAAAAAAAA" if not wrong else "DDDDDDDDDDDDDDDD"
                ),
                "sector_fnv1a64_after_product": "BBBBBBBBBBBBBBBB",
                "fallback_program_reached": erase,
                "fallback_program_body_executed": erase,
                "fallback_program_forced_success": erase,
                "fallback_observed_byte": 0x25 if erase else None,
                "physical_readback_hits": 27,
                "physical_readback_rejected": True, "result": 0xFF,
                "damaged_target_marked": True,
                "protected_generation_exact": True,
                "selector_not_promoted": True,
                "target_generation_complete": erase,
                "target_bank_checkpoint_exact": erase,
                "stock_not_reentered": True, "fresh_continue": True,
                "input_recovered": True,
                "expected_selected_counter": 1 if erase else 0,
                "selected_counter": 1 if erase else 0,
                "fresh_selected_expected_generation": True,
            }

        document = {
            "real_callback_entry_checkpoint": True,
            "physical_media_readback_observed": True,
            "variant_count": 3,
            "results": [
                row("ERASE_SILENT_SUCCESS_NO_EFFECT", "POST", "ERASE", 1),
                row("PROGRAM_NO_OP_SUCCESS", "PREFLIGHT", "PROGRAM", 4097),
                row(
                    "PROGRAM_WRONG_BYTE_SUCCESS", "POST", "PROGRAM", 57359,
                ),
            ],
            "all_product_results_error": True,
            "all_damaged_targets_marked": True,
            "all_protected_generations_exact": True,
            "all_selectors_not_promoted": True,
            "all_fresh_continue_safe": True,
            "failed": 0, "untested": 0,
        }
        scenario_by_name = {"EMPTY": {"phases": phases}}
        normalized = RUNNER._validate_cow_silent_success_faults(
            deepcopy(document), scenario_by_name=scenario_by_name,
        )
        self.assertEqual(normalized["variant_count"], 3)

        mutations = {
            "missing_variant": lambda value: value["results"].pop(),
            "false_success_result": lambda value: value["results"][0].__setitem__(
                "result", 0,
            ),
            "erase_media_changed": lambda value: value["results"][0].__setitem__(
                "immediate_media_unchanged", False,
            ),
            "callback_returned_error": lambda value: value["results"][1].__setitem__(
                "callback_status_before_force", 0xFF,
            ),
            "no_op_wrote_expected": lambda value: value["results"][1].__setitem__(
                "observed_byte_after", 0x25,
            ),
            "wrong_byte_spoof": lambda value: value["results"][2].__setitem__(
                "injected_byte", 0x23,
            ),
            "not_final_commit": lambda value: value["results"][2].__setitem__(
                "phase_callback_ordinal", 57358,
            ),
            "no_physical_readback": lambda value: value["results"][2].__setitem__(
                "physical_readback_hits", 1,
            ),
            "selector_promoted": lambda value: value["results"][2].__setitem__(
                "selector_not_promoted", False,
            ),
            "wrong_physical_slot": lambda value: value["results"][0].__setitem__(
                "physical_sector", 13,
            ),
            "aggregate_variant_spoof": lambda value: value.__setitem__(
                "variant_count", 2,
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                broken = deepcopy(document)
                mutate(broken)
                with self.assertRaises(RUNNER.Stage61MgbaError):
                    RUNNER._validate_cow_silent_success_faults(
                        broken, scenario_by_name=scenario_by_name,
                    )

    def test_species_picture_bounds_requires_cartesian_guard_and_ui_e2e(
        self,
    ) -> None:
        table = 0x09F00000
        direct = []
        for name, entry, guard in RUNNER._SPECIES_PICTURE_CALLS:
            for species in RUNNER._SPECIES_PICTURE_VALUES:
                effective = species if species <= 1620 else 0
                direct.append({
                    "callsite": name,
                    "entry": f"0x{entry:08X}",
                    "guard": f"0x{guard:08X}",
                    "species": species,
                    "effective_species": effective,
                    "fallback_to_row0": species > 1620,
                    "passed_row": f"0x{table + species * 8:08X}",
                    "effective_row": f"0x{table + effective * 8:08X}",
                    "guard_pc_seen": True,
                    "returned": True,
                    "instructions": 42,
                    "output_fnv1a64": "1234567890ABCDEF",
                    "expected_fnv1a64": "1234567890ABCDEF",
                    "output_exact": True,
                    "allocation_guards_intact": True,
                    "heap_header_intact": True,
                    "heap_reallocated_after_free": True,
                })
        common = {
            "normal_start_party_summary_keys": True,
            "summary_visible": True,
            "input_recovered": True,
            "picture_guard_pc_hits": [0, 0, 1, 0],
            "field_framebuffer_fnv1a64": "0123456789ABCDEF",
            "summary_framebuffer_fnv1a64": "FEDCBA9876543210",
        }
        document = {
            "schema_version": 1, "status": "PASS",
            "case": "species_picture_bounds",
            "front_table": f"0x{table:08X}", "maximum_species": 1620,
            "direct_results": direct, "direct_result_count": 16,
            "ui_results": [{
                "fixture_id": "field_party_boundary_1620",
                "species": 1620,
                "picture_guard_species_r9_values": [[], [], [1620], []],
                **deepcopy(common),
            }, {
                "fixture_id": "caught_snorlax_party_summary",
                "species": RUNNER.DEFAULT_FIXTURE_DOCUMENT["story"][
                    "snorlax_species"
                ],
                "producer_dialogue": True,
                "actual_walk_direction_a_battle": True,
                "actual_master_ball_menu_keys": True,
                "actual_walk_steps": 99,
                "picture_guard_species_r9_values": [
                    [], [], [0xFFFF], [],
                ],
                **deepcopy(common),
            }],
            "ui_result_count": 2, "failed": 0, "untested": 0,
            "warnings": 0,
        }
        result = RUNNER._validate_species_picture_bounds(
            document, RUNNER.DEFAULT_FIXTURE_DOCUMENT,
        )
        self.assertEqual(result["direct_result_count"], 16)

        duplicate = deepcopy(document)
        duplicate["direct_results"][-1] = deepcopy(
            duplicate["direct_results"][-2]
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "Cartesian coverage",
        ):
            RUNNER._validate_species_picture_bounds(
                duplicate, RUNNER.DEFAULT_FIXTURE_DOCUMENT,
            )

        wrong_fallback = deepcopy(document)
        wrong_fallback["direct_results"][-1]["fallback_to_row0"] = False
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "fallback row"):
            RUNNER._validate_species_picture_bounds(
                wrong_fallback, RUNNER.DEFAULT_FIXTURE_DOCUMENT,
            )

        no_ui_pc = deepcopy(document)
        no_ui_pc["ui_results"][0]["picture_guard_pc_hits"] = [0, 0, 0, 0]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "guard PC"):
            RUNNER._validate_species_picture_bounds(
                no_ui_pc, RUNNER.DEFAULT_FIXTURE_DOCUMENT,
            )
        no_original_sentinel = deepcopy(document)
        no_original_sentinel["ui_results"][1][
            "picture_guard_species_r9_values"
        ][2] = [491]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "captured-mon"):
            RUNNER._validate_species_picture_bounds(
                no_original_sentinel, RUNNER.DEFAULT_FIXTURE_DOCUMENT,
            )

    @staticmethod
    def _map_resume_trigger() -> dict[str, object]:
        stock_warp = {
            "source": {"group": 3, "map": 3, "warp_id": 1},
            "predecessor_tile": {"x": 5, "y": 5},
            "trigger_tile": {"x": 5, "y": 4},
            "trigger_key": "UP",
            "destination": {"group": 3, "map": 4, "warp_id": 2},
            "arrival_tile": {"x": 7, "y": 8},
            "connection_or_warp_record_address": "0x08123400",
            "source_provenance": {"kind": "UNIT_WARP_RECORD"},
        }
        return {
            "kind": "MAP_TRANSITION_LOAD", "group": 3, "map": 4,
            "root_subkind": "DIRECT", "map_script_tag": 2,
            "entry": (
                "STOCK_WARP_OR_CONNECTION_OR_ENGINE_TELEPORT_OR_"
                "RESUME_CALLBACK"
            ),
            "root_pc": "0x09100000",
            "resume_callback": {
                "callback_address": "0x08012345",
                "actual_predecessor_consumer": {
                    "kind": "STOCK_WARP_THEN_FIELD_RETURN",
                    "stock_warp": stock_warp,
                    "field_return": {
                        "kind": "START_MENU_OPEN_CLOSE",
                        "normal_trigger_tokens": ["START", "B"],
                        "callback_install_instruction_pc": "0x08045678",
                        "callback_dispatch_instruction_pc": "0x080456A0",
                        "expected_map": {"group": 3, "map": 4},
                    },
                },
                "normal_trigger_tokens": ["START", "B"],
                "source_provenance": {"kind": "UNIT_RESUME_CALLBACK"},
            },
        }

    @staticmethod
    def _engine_teleport_provenance(
        group: int = 3, map_number: int = 4,
    ) -> dict[str, object]:
        block_raw = bytes.fromhex("0000")
        return {
            "kind": (
                "FINAL_ROM_GEOMETRY_BOUND_ENGINE_PLAYER_TELEPORT_MAP_LOAD"
            ),
            "rom_sha256": "0" * 64,
            "layout_address": "0x08120000",
            "block_address": "0x08121000",
            "block_raw_hex": block_raw.hex(),
            "block_raw_sha256": hashlib.sha256(block_raw).hexdigest(),
            "base_collision": 0, "base_elevation": 0,
            "foreign_stock_warp_scan": {
                "destination": [group, map_number],
                "foreign_warp_reference_count": 0,
                "usable_stock_warp_count": 0,
                "invalid_source_warp_view_count": 0,
                "unusable_reason_counts": {},
            },
            "usable_stock_connection_count": 0,
            "incoming_usable_zero_reason_bound": True,
            "first_root_hit_map_identity_required": True,
            "settled_map_identity_not_substituted_for_first_root_hit": True,
            "direct_root_call_forbidden": True,
            "direct_callback_call_forbidden": True,
        }

    def test_map_resume_nested_contract_flattens_exact_tsv(self) -> None:
        trigger = RUNNER._normalize_event_trigger_path(
            self._map_resume_trigger(), "unit-map-resume",
        )
        predecessor = trigger["resume_callback"][
            "actual_predecessor_consumer"
        ]
        self.assertEqual(
            predecessor["kind"], "STOCK_WARP_THEN_FIELD_RETURN",
        )
        self.assertEqual(
            predecessor["field_return"]["normal_trigger_tokens"],
            ["START", "B"],
        )
        fields = RUNNER._event_trigger_fields({
            "case_id": "map-resume-unit", "owner_id": "MAP:003/004:000",
            "root_assignment_id": "ROOT:09100000",
            "trigger_path": trigger, "terminal_kind": "FIELD_RELEASE",
        })
        header = RUNNER._EVENT_TRIGGER_TSV_HEADER.rstrip("\n").split("\t")
        self.assertEqual(len(header), 67)
        values = dict(zip(header, fields, strict=True))
        self.assertEqual(values["source_group"], "3")
        self.assertEqual(values["source_map"], "3")
        self.assertEqual(values["predecessor_x"], "5")
        self.assertEqual(values["trigger_y"], "4")
        self.assertEqual(values["destination_map"], "4")
        self.assertEqual(
            values["transition_contract"],
            "STOCK_WARP_THEN_FIELD_RETURN",
        )
        self.assertEqual(values["callback_install_instruction_pc"], str(
            0x08045678,
        ))
        self.assertEqual(values["callback_dispatch_instruction_pc"], str(
            0x080456A0,
        ))
        self.assertEqual(values["field_return_token_count"], "2")

    def test_map_condition_precedence_guard_flattens_with_rom_evidence(self) -> None:
        trigger = self._map_resume_trigger()
        trigger.update({
            "root_subkind": "CONDITION",
            "left_operand": 0x406F,
            "right_operand": 8,
            "required_relation": "EQUAL",
        })
        record_raw = struct.pack("<HHI", 0x4079, 0, 0x08012345)
        trigger["precedence_guards"] = [{
            "variable": 0x4079,
            "required_value": 1,
            "forbidden_values": [0],
            "relation": "NOT_EQUAL_ALL_PRECEDING_VALUES",
            "source_conditions": [{
                "condition_index": 0,
                "record_address": 0x08123400,
                "record_raw_hex": record_raw.hex(),
                "record_raw_sha256": hashlib.sha256(record_raw).hexdigest(),
                "variable": 0x4079,
                "value": 0,
                "root_pc": 0x08012345,
            }],
        }]
        normalized = RUNNER._normalize_event_trigger_path(
            trigger, "unit-map-condition-precedence",
        )
        fields = dict(zip(
            RUNNER._EVENT_TRIGGER_TSV_HEADER.rstrip("\n").split("\t"),
            RUNNER._event_trigger_fields({
                "case_id": "map-condition-unit",
                "owner_id": "MAP:003/004:000:001",
                "root_assignment_id": "ROOT:09100000",
                "trigger_path": normalized,
                "terminal_kind": "FIELD_RELEASE",
            }), strict=True,
        ))
        self.assertEqual(fields["trigger_var"], str(0x406F))
        self.assertEqual(fields["trigger_value"], "8")
        self.assertEqual(fields["map_precedence_guards"], f"{0x4079}:1")

        bad_hash = deepcopy(trigger)
        bad_hash["precedence_guards"][0]["source_conditions"][0][
            "record_raw_sha256"
        ] = "0" * 64
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "ROM evidence"):
            RUNNER._normalize_event_trigger_path(bad_hash, "bad-guard-hash")
        dynamic_rhs = deepcopy(trigger)
        dynamic_rhs["right_operand"] = 0x4000
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "operand"):
            RUNNER._normalize_event_trigger_path(dynamic_rhs, "dynamic-rhs")

    def test_map_field_return_callback_contract_is_static_rom_bound(self) -> None:
        final_rom = (ROOT / RUNNER.DEFAULT_ROM).read_bytes()
        contract = RUNNER.build_map_field_return_callback_contracts(final_rom)
        self.assertEqual(
            contract["kind"],
            "STAGE61_MAP_FIELD_RETURN_CALLBACK_CONTRACTS",
        )
        self.assertEqual(contract["rom_sha256"], hashlib.sha256(
            final_rom,
        ).hexdigest())
        self.assertEqual(set(contract["by_tag"]), {"5", "7"})
        for tag in ("5", "7"):
            row = contract["by_tag"][tag]
            self.assertEqual(row["callback_address"], 0x0806EA75)
            self.assertEqual(
                row["callback_install_instruction_pc"], 0x0806EA18,
            )
            self.assertEqual(
                row["callback_dispatch_instruction_pc"], 0x0806EA30,
            )
            self.assertEqual(row["normal_trigger_tokens"], ["START", "B"])
            provenance = row["source_provenance"]
            self.assertEqual(provenance["rom_sha256"], contract["rom_sha256"])
            self.assertEqual(
                provenance["derivation"],
                "STATIC_FINAL_ROM_PREIMAGE_NOT_RUNTIME_LEARNED",
            )
            self.assertEqual(
                [binding["address"] for binding in provenance["bindings"]],
                ["0x0806EA14", "0x0806EA2C", "0x0806EA74"],
            )

    def test_map_field_return_callback_contract_rejects_preimage_drift(
        self,
    ) -> None:
        final_rom = (ROOT / RUNNER.DEFAULT_ROM).read_bytes()
        for address in (0x0806EA14, 0x0806EA30, 0x0806EA74):
            with self.subTest(address=f"0x{address:08X}"):
                mutated = bytearray(final_rom)
                mutated[address - 0x08000000] ^= 0x01
                with self.assertRaisesRegex(
                    RUNNER.Stage61MgbaError, "static preimage",
                ):
                    RUNNER.build_map_field_return_callback_contracts(
                        bytes(mutated),
                    )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "immutable bytes",
        ):
            RUNNER.build_map_field_return_callback_contracts(
                bytearray(final_rom),  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "size"):
            RUNNER.build_map_field_return_callback_contracts(final_rom[:-1])

    def test_map_resume_nested_contract_rejects_incomplete_predecessor(
        self,
    ) -> None:
        for mutation in ("kind", "tokens", "destination", "callback_pc"):
            with self.subTest(mutation=mutation):
                trigger = self._map_resume_trigger()
                resume = trigger["resume_callback"]
                predecessor = resume["actual_predecessor_consumer"]
                field_return = predecessor["field_return"]
                if mutation == "kind":
                    predecessor["kind"] = "HOST_CALLBACK"
                elif mutation == "tokens":
                    field_return["normal_trigger_tokens"] = ["START"]
                elif mutation == "destination":
                    field_return["expected_map"]["map"] = 5
                else:
                    field_return["callback_dispatch_instruction_pc"] = 0
                with self.assertRaises(RUNNER.Stage61MgbaError):
                    RUNNER._normalize_event_trigger_path(
                        trigger, f"unit-map-resume-{mutation}",
                    )

    def test_map_connection_and_engine_teleport_are_exact_one_of(self) -> None:
        entry = (
            "STOCK_WARP_OR_CONNECTION_OR_ENGINE_TELEPORT_OR_RESUME_CALLBACK"
        )
        base = {
            "kind": "MAP_TRANSITION_LOAD", "group": 5, "map": 6,
            "root_subkind": "DIRECT", "map_script_tag": 2,
            "entry": entry, "root_pc": "0x09100000",
        }
        connection = {
            "kind": "STOCK_CONNECTION_BOUNDARY_STEP",
            "source": {"group": 5, "map": 5},
            "predecessor_tile": {"x": 8, "y": 9},
            "trigger_tile": {"x": 9, "y": 9},
            "trigger_key": "RIGHT",
            "destination": {"group": 5, "map": 6},
            "arrival_tile": {"x": 0, "y": 9},
            "connection_or_warp_record_address": "0x08123400",
            "source_provenance": {"kind": "UNIT_CONNECTION_RECORD"},
        }
        connection_path = RUNNER._normalize_event_trigger_path(
            {**base, "stock_connection": connection}, "unit-map-connection",
        )
        self.assertEqual(
            RUNNER._event_trigger_tokens(connection_path),
            ("WALK_ACROSS_CONNECTION", "WAIT_FIRST_ROOT_HIT"),
        )
        connection_fields = dict(zip(
            RUNNER._EVENT_TRIGGER_TSV_HEADER.rstrip("\n").split("\t"),
            RUNNER._event_trigger_fields({
                "case_id": "map-connection-unit",
                "owner_id": "MAP:005/006:000",
                "root_assignment_id": "ROOT:09100000",
                "trigger_path": connection_path,
                "terminal_kind": "FIELD_RELEASE",
            }), strict=True,
        ))
        self.assertEqual(connection_fields["seed_kind"], "stock_connection")
        self.assertEqual(connection_fields["trigger_key"], str(RUNNER.KEYS["RIGHT"]))
        self.assertEqual(
            connection_fields["transition_contract"],
            "STOCK_CONNECTION_BOUNDARY_STEP",
        )

        engine = {
            "kind": "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
            "destination": {"group": 5, "map": 6},
            "start_tile": {"x": 11, "y": 12},
            "engine_entry": "BOOTSTRAP_KANTO_WARP",
            "source_provenance": self._engine_teleport_provenance(5, 6),
        }
        engine_path = RUNNER._normalize_event_trigger_path(
            {**base, "engine_teleport": engine}, "unit-map-engine",
        )
        self.assertEqual(
            RUNNER._event_trigger_tokens(engine_path),
            ("ENGINE_PLAYER_TELEPORT_MAP_LOAD", "WAIT_FIRST_ROOT_HIT"),
        )
        engine_fields = dict(zip(
            RUNNER._EVENT_TRIGGER_TSV_HEADER.rstrip("\n").split("\t"),
            RUNNER._event_trigger_fields({
                "case_id": "map-engine-unit", "owner_id": "MAP:005/006:000",
                "root_assignment_id": "ROOT:09100000",
                "trigger_path": engine_path, "terminal_kind": "FIELD_RELEASE",
            }), strict=True,
        ))
        self.assertEqual(engine_fields["seed_kind"], "engine_teleport")
        self.assertEqual(engine_fields["trigger_key"], "0")
        self.assertEqual(engine_fields["arrival_x"], "11")
        self.assertEqual(
            engine_fields["transition_contract"],
            "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
        )
        callback = self._map_resume_trigger()["resume_callback"]
        callback["actual_predecessor_consumer"] = {
            "kind": "ENGINE_TELEPORT_THEN_FIELD_RETURN",
            "engine_teleport": engine,
            "field_return": callback["actual_predecessor_consumer"][
                "field_return"
            ],
        }
        callback["actual_predecessor_consumer"]["field_return"][
            "expected_map"
        ] = {"group": 5, "map": 6}
        resume_engine = RUNNER._normalize_event_trigger_path(
            {**base, "map_script_tag": 5, "resume_callback": callback},
            "unit-map-engine-resume",
        )
        self.assertEqual(
            resume_engine["resume_callback"]["actual_predecessor_consumer"][
                "kind"
            ],
            "ENGINE_TELEPORT_THEN_FIELD_RETURN",
        )
        self.assertEqual(RUNNER._event_trigger_tokens(resume_engine), ("START", "B"))

        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "seed"):
            RUNNER._normalize_event_trigger_path(
                {**base, "stock_connection": connection,
                 "engine_teleport": engine},
                "unit-map-two-seeds",
            )
        broken_engine = deepcopy(engine)
        broken_engine["source_provenance"]["kind"] = "HOST_SHORTCUT"
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "engine_teleport"):
            RUNNER._normalize_event_trigger_path(
                {**base, "engine_teleport": broken_engine},
                "unit-map-engine-bad-provenance",
            )
        broken_connection = deepcopy(connection)
        broken_connection["trigger_tile"]["x"] = 10
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "geometry"):
            RUNNER._normalize_event_trigger_path(
                {**base, "stock_connection": broken_connection},
                "unit-map-connection-bad-geometry",
            )

    def test_all_38_engine_fallback_owners_use_production_provenance(
        self,
    ) -> None:
        entry = (
            "STOCK_WARP_OR_CONNECTION_OR_ENGINE_TELEPORT_OR_RESUME_CALLBACK"
        )
        normalized = []
        for index in range(38):
            path = {
                "kind": "MAP_TRANSITION_LOAD", "group": 40,
                "map": index % 17, "root_subkind": "DIRECT",
                "map_script_tag": 2, "entry": entry,
                "root_pc": 0x09100000 + index * 2,
                "engine_teleport": {
                    "kind": "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
                    "destination": {"group": 40, "map": index % 17},
                    "start_tile": {"x": 10 + index, "y": 12},
                    "engine_entry": "BOOTSTRAP_KANTO_WARP",
                    "source_provenance": self._engine_teleport_provenance(
                        40, index % 17,
                    ),
                },
            }
            normalized.append(RUNNER._normalize_event_trigger_path(
                path, f"production-shaped-engine-fallback[{index}]",
            ))
        self.assertEqual(len(normalized), 38)
        self.assertTrue(all(
            row["engine_teleport"]["source_provenance"]["kind"]
            == "FINAL_ROM_GEOMETRY_BOUND_ENGINE_PLAYER_TELEPORT_MAP_LOAD"
            for row in normalized
        ))
        legacy = deepcopy(normalized[0])
        legacy["engine_teleport"]["source_provenance"]["kind"] = (
            "FINAL_ROM_COLLISION_BOUND_ENGINE_TELEPORT_START"
        )
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "engine_teleport"):
            RUNNER._normalize_event_trigger_path(
                legacy, "legacy-engine-fallback-provenance",
            )
        provenance_mutations = {
            "foreign-destination-drift": lambda source: source[
                "foreign_stock_warp_scan"
            ].__setitem__("destination", [40, 99]),
            "usable-stock-warp": lambda source: source[
                "foreign_stock_warp_scan"
            ].__setitem__("usable_stock_warp_count", 1),
            "usable-stock-connection": lambda source: source.__setitem__(
                "usable_stock_connection_count", 1,
            ),
        }
        for label, mutate in provenance_mutations.items():
            broken = deepcopy(normalized[0])
            mutate(broken["engine_teleport"]["source_provenance"])
            with self.subTest(label=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "engine_teleport",
            ):
                RUNNER._normalize_event_trigger_path(broken, label)

    def test_map_side_effect_before_map_resolves_direct_and_resume_3_seeds(
        self,
    ) -> None:
        resume_warp_raw = self._map_resume_trigger()
        stock_warp = deepcopy(resume_warp_raw["resume_callback"][
            "actual_predecessor_consumer"
        ]["stock_warp"])
        stock_connection = {
            "kind": "STOCK_CONNECTION_BOUNDARY_STEP",
            "source": {
                "group": stock_warp["source"]["group"],
                "map": stock_warp["source"]["map"],
            },
            "predecessor_tile": stock_warp["predecessor_tile"],
            "trigger_tile": stock_warp["trigger_tile"],
            "trigger_key": stock_warp["trigger_key"],
            "destination": {
                "group": stock_warp["destination"]["group"],
                "map": stock_warp["destination"]["map"],
            },
            "arrival_tile": stock_warp["arrival_tile"],
            "connection_or_warp_record_address": (
                stock_warp["connection_or_warp_record_address"]
            ),
            "source_provenance": {"kind": "UNIT_CONNECTION_RECORD"},
        }
        engine_teleport = {
            "kind": "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
            "destination": {"group": 3, "map": 4},
            "start_tile": {"x": 7, "y": 8},
            "engine_entry": "BOOTSTRAP_KANTO_WARP",
            "source_provenance": self._engine_teleport_provenance(),
        }
        seed_values = {
            "stock_warp": stock_warp,
            "stock_connection": stock_connection,
            "engine_teleport": engine_teleport,
        }
        expected_before = {
            "stock_warp": "3/3", "stock_connection": "3/3",
            "engine_teleport": "96/5",
        }
        normalized: dict[tuple[str, str], dict[str, object]] = {}
        for mode in ("direct", "resume"):
            for seed_kind, seed in seed_values.items():
                with self.subTest(mode=mode, seed_kind=seed_kind):
                    raw = self._map_resume_trigger()
                    if mode == "direct":
                        raw.pop("resume_callback")
                        raw[seed_kind] = deepcopy(seed)
                    else:
                        predecessor = raw["resume_callback"][
                            "actual_predecessor_consumer"
                        ]
                        field_return = predecessor["field_return"]
                        raw["resume_callback"][
                            "actual_predecessor_consumer"
                        ] = {
                            "kind": {
                                "stock_warp": (
                                    "STOCK_WARP_THEN_FIELD_RETURN"
                                ),
                                "stock_connection": (
                                    "STOCK_CONNECTION_THEN_FIELD_RETURN"
                                ),
                                "engine_teleport": (
                                    "ENGINE_TELEPORT_THEN_FIELD_RETURN"
                                ),
                            }[seed_kind],
                            seed_kind: deepcopy(seed),
                            "field_return": field_return,
                        }
                    path = RUNNER._normalize_event_trigger_path(
                        raw, f"unit-before-map-{mode}-{seed_kind}",
                    )
                    normalized[(mode, seed_kind)] = path
                    resume, outer_kind, actual_kind, actual_seed = (
                        RUNNER._event_map_actual_seed(
                            path, f"unit-before-map-{mode}-{seed_kind}",
                        )
                    )
                    self.assertIs(resume, mode == "resume")
                    self.assertEqual(
                        outer_kind,
                        "resume_callback" if mode == "resume" else seed_kind,
                    )
                    self.assertEqual(actual_kind, seed_kind)
                    self.assertEqual(actual_seed, path[
                        "resume_callback"
                    ]["actual_predecessor_consumer"][seed_kind]
                        if mode == "resume" else path[seed_kind])
                    self.assertEqual(
                        RUNNER._event_side_effect_before_map(
                            path, f"unit-before-map-{mode}-{seed_kind}",
                        ),
                        expected_before[seed_kind],
                    )

        direct_multiple = deepcopy(normalized[("direct", "stock_warp")])
        direct_multiple["stock_connection"] = deepcopy(stock_connection)
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "direct seed exact-one",
        ):
            RUNNER._event_side_effect_before_map(
                direct_multiple, "unit-before-map-direct-multiple",
            )
        resume_multiple = deepcopy(normalized[("resume", "stock_warp")])
        resume_multiple["resume_callback"]["actual_predecessor_consumer"][
            "stock_connection"
        ] = deepcopy(stock_connection)
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "resume seed exact-one",
        ):
            RUNNER._event_side_effect_before_map(
                resume_multiple, "unit-before-map-resume-multiple",
            )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("S61_EVENT_RUNTIME_BASE_GROUP = 96U", source)
        self.assertIn("S61_EVENT_RUNTIME_BASE_MAP = 5U", source)
        self.assertIn(
            "S61_EVENT_RUNTIME_BASE_GROUP, S61_EVENT_RUNTIME_BASE_MAP",
            source,
        )

    def test_engine_direct_and_resume_zero_walk_tsv_matches_c_parser(
        self,
    ) -> None:
        rows = {}
        for mode in ("direct", "resume"):
            raw = self._map_resume_trigger()
            engine = {
                "kind": "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
                "destination": {"group": 3, "map": 4},
                "start_tile": {"x": 7, "y": 8},
                "engine_entry": "BOOTSTRAP_KANTO_WARP",
                "source_provenance": self._engine_teleport_provenance(),
            }
            if mode == "direct":
                raw.pop("resume_callback")
                raw["engine_teleport"] = engine
                tokens = [
                    "ENGINE_PLAYER_TELEPORT_MAP_LOAD", "WAIT_FIRST_ROOT_HIT",
                ]
            else:
                predecessor = raw["resume_callback"][
                    "actual_predecessor_consumer"
                ]
                raw["resume_callback"]["actual_predecessor_consumer"] = {
                    "kind": "ENGINE_TELEPORT_THEN_FIELD_RETURN",
                    "engine_teleport": engine,
                    "field_return": predecessor["field_return"],
                }
                tokens = ["START", "B"]
            trigger = RUNNER._normalize_event_trigger_path(
                raw, f"unit-engine-zero-walk-{mode}",
            )
            case_id = f"engine-zero-walk-{mode}"
            rows[case_id] = {
                "case_id": case_id, "owner_id": "MAP:003/004:000",
                "root_assignment_id": "ROOT:09100000",
                "trigger_path": trigger,
                "input_sequence": {
                    "sequence_id": f"{case_id}-sequence",
                    "expected_static_branch_token": "MAP:DIRECT",
                    "visible_text_expected": True,
                    "silent_text_basis": None, "tokens": tokens,
                },
                "state": {
                    "flags": [], "vars": [], "items": [], "trainers": [],
                },
                "control_requirements": {"external": [], "internal": []},
                "terminal_kind": "FIELD_RELEASE",
            }
        with tempfile.TemporaryDirectory() as temporary:
            catalog_path = Path(temporary) / "event-catalog.tsv"
            trigger_path = Path(temporary) / "event-trigger.tsv"
            RUNNER.write_event_runtime_tsv_files(
                catalog_path, trigger_path, rows,
            )
            catalog_lines = catalog_path.read_text(
                encoding="ascii",
            ).splitlines()
            trigger_lines = trigger_path.read_text(
                encoding="ascii",
            ).splitlines()
        catalog_header = catalog_lines[0].split("\t")
        trigger_header = trigger_lines[0].split("\t")
        self.assertEqual(len(catalog_lines), 3)
        self.assertEqual(len(trigger_lines), 3)
        catalog_rows = {
            values[0]: dict(zip(catalog_header, values, strict=True))
            for values in (line.split("\t") for line in catalog_lines[1:])
        }
        trigger_rows = {
            values[0]: dict(zip(trigger_header, values, strict=True))
            for values in (line.split("\t") for line in trigger_lines[1:])
        }
        for mode in ("direct", "resume"):
            case_id = f"engine-zero-walk-{mode}"
            catalog = catalog_rows[case_id]
            self.assertEqual(
                (
                    catalog["interaction_trigger"], catalog["walk_keys"],
                    catalog["approach_steps"],
                    catalog["actual_walk_required"],
                    catalog["map_level_real_walk_probe_required"],
                ),
                ("EVENT_RUNTIME_TRIGGER_DISPATCH", "-", "0", "0", "0"),
            )
            self.assertEqual(
                trigger_rows[case_id]["seed_kind"],
                "engine_teleport" if mode == "direct" else "resume_callback",
            )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("event_runtime_engine_zero_walk_contract", source)
        self.assertIn("event runtime engine zero-walk lockstep differs", source)

    def test_common_effective_object_requires_direction_plus_a(self) -> None:
        object_path = {
            "kind": "OBJECT_FACE_A", "group": 3, "map": 4,
            "local_id": 2, "object_index": 1,
            "root_pc": "0x08125001", "approach": "WALK_ADJACENT_FACE_A",
            "start_tile": {"x": 8, "y": 7},
            "walk_sequence": ["DOWN"],
            "stance_tile": {"x": 8, "y": 8},
            "required_facing": "DOWN",
            "runtime_topology_probe_required": False,
        }
        common = RUNNER._normalize_event_trigger_path({
            "kind": "COMMON_CALLER_TRIGGER", "standard_index": 2,
            "caller_owner_id": "OBJECT:003/004:001",
            "caller_owner_kind": "OBJECT",
            "caller_instruction_pc": "0x08120001",
            "caller_trigger_path": object_path,
            "root_pc": "0x08130001",
        }, "unit-common-effective-object")
        effective, _binding = RUNNER._event_effective_trigger(common)
        self.assertEqual(effective["kind"], "OBJECT_FACE_A")
        self.assertIs(RUNNER._event_direction_plus_a_expected(effective), True)
        fields = dict(zip(
            RUNNER._EVENT_TRIGGER_TSV_HEADER.rstrip("\n").split("\t"),
            RUNNER._event_trigger_fields({
                "case_id": "common-object-unit",
                "owner_id": "COMMON:STANDARD:002",
                "root_assignment_id": "ROOT:08130001",
                "trigger_path": common, "terminal_kind": "FIELD_RELEASE",
            }), strict=True,
        ))
        self.assertEqual(fields["declared_kind"], "COMMON_CALLER_TRIGGER")
        self.assertEqual(fields["effective_kind"], "OBJECT_FACE_A")
        self.assertEqual(fields["root_pc"], str(0x08130001))
        self.assertEqual(fields["physical_root_pc"], str(0x08125001))
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "trigger.effective_kind == S61_EVENT_OBJECT_FACE_A\n"
            "                   || trigger.effective_kind == S61_EVENT_BG_FACE_A",
            source,
        )

    def test_common_dispatcher_edge_is_exact_and_fail_closed(self) -> None:
        physical_root = 0x08125001

        def declared(index: int, caller_pc: int, root: int) -> dict[str, object]:
            return RUNNER._normalize_event_trigger_path({
                "kind": "COMMON_CALLER_TRIGGER", "standard_index": index,
                "caller_owner_id": "OBJECT:003/004:001",
                "caller_owner_kind": "OBJECT",
                "caller_instruction_pc": caller_pc,
                "caller_trigger_path": {
                    "kind": "OBJECT_FACE_A", "group": 3, "map": 4,
                    "local_id": 2, "object_index": 1,
                    "root_pc": physical_root,
                    "approach": "WALK_ADJACENT_FACE_A",
                    "start_tile": {"x": 8, "y": 7},
                    "walk_sequence": ["DOWN"],
                    "stance_tile": {"x": 8, "y": 8},
                    "required_facing": "DOWN",
                    "runtime_topology_probe_required": False,
                },
                "root_pc": root,
            }, f"unit-common-{index}")

        def evidence(
            binding: Mapping[str, object], *, opcode: int = 0x09,
        ) -> dict[str, object]:
            effective, _ = RUNNER._event_effective_trigger(binding)
            return {
                "dispatcher_pc": "0x0806911A",
                "physical_root_pc": f"0x{int(effective['root_pc']):08X}",
                "physical_root_hits": 1,
                "physical_root_context": "0x03000EA8",
                "physical_root_ordinal": 10,
                "caller_pc": (
                    f"0x{int(binding['caller_instruction_pc']):08X}"
                ),
                "caller_hits": 1, "caller_context": "0x03000EA8",
                "caller_ordinal": 20, "opcode": opcode,
                "opcode_family_exact": True,
                "standard_index": binding["standard_index"],
                "standard_index_exact": True,
                "last_talked_local_id": effective["local_id"],
                "last_talked_exact": True,
                "declared_root_pc": f"0x{int(binding['root_pc']):08X}",
                "declared_root_hits": 1,
                "declared_root_context": "0x03000EA8",
                "declared_root_ordinal": 21, "same_context": True,
                "physical_root_before_caller": True,
                "caller_to_root_adjacent": True, "edge_hits": 1,
            }

        common2 = declared(2, 0x08120001, 0x08130001)
        common9 = declared(9, 0x08120011, 0x08130021)
        rom = bytearray(0x163758 + 10 * 4)
        for binding in (common2, common9):
            caller_offset = int(binding["caller_instruction_pc"]) - 0x08000000
            rom[caller_offset:caller_offset + 2] = bytes((
                0x09, int(binding["standard_index"]),
            ))
            table_offset = 0x163758 + int(binding["standard_index"]) * 4
            rom[table_offset:table_offset + 4] = int(
                binding["root_pc"]
            ).to_bytes(4, "little")
        for binding in (common2, common9):
            effective, _ = RUNNER._event_effective_trigger(binding)
            observed = evidence(binding)
            self.assertEqual(
                RUNNER._validate_event_common_dispatch_evidence(
                    observed, declared=binding, effective=effective,
                    label="unit-common-edge", rom_raw=bytes(rom),
                ),
                observed,
            )

        effective2, _ = RUNNER._event_effective_trigger(common2)
        mutations = {
            "caller-pc-missing": lambda item: item.__setitem__(
                "caller_pc", "0x00000000",
            ),
            "same-root-other-callsite": lambda item: item.__setitem__(
                "caller_pc", f"0x{int(common9['caller_instruction_pc']):08X}",
            ),
            "nonadjacent-root": lambda item: item.__setitem__(
                "declared_root_ordinal", 22,
            ),
            "opcode-mismatch": lambda item: item.__setitem__("opcode", 0x08),
            "standard-index-mismatch": lambda item: item.__setitem__(
                "standard_index", 9,
            ),
            "ordinal-inversion": lambda item: item.__setitem__(
                "physical_root_ordinal", 30,
            ),
            "last-talked-mismatch": lambda item: item.__setitem__(
                "last_talked_local_id", 3,
            ),
            "context-mismatch": lambda item: item.__setitem__(
                "declared_root_context", "0x03000F28",
            ),
        }
        for label, mutate in mutations.items():
            broken = evidence(common2)
            mutate(broken)
            with self.subTest(label=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "COMMON dispatcher",
            ):
                RUNNER._validate_event_common_dispatch_evidence(
                    broken, declared=common2, effective=effective2,
                    label=label, rom_raw=bytes(rom),
                )

        # COMMON 2/9 intentionally share the physical OBJECT root.  Swapping
        # their bytecode callsites must still fail despite that shared prefix.
        swapped = evidence(common2)
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "COMMON dispatcher",
        ):
            RUNNER._validate_event_common_dispatch_evidence(
                swapped, declared=common9,
                effective=RUNNER._event_effective_trigger(common9)[0],
                label="common2-common9-swapped", rom_raw=bytes(rom),
            )

        for standard_index, local_id, visibility_flag in (
            (1, 3, 0x018F), (5, 6, 0x0011), (6, 9, 0x11E1),
        ):
            binding = declared(
                standard_index, 0x08120100 + standard_index * 4,
                0x08130100 + standard_index * 4,
            )
            binding["caller_trigger_path"]["local_id"] = local_id
            projection = RUNNER._event_catalog_projection({
                "case_id": f"common-{standard_index}",
                "owner_id": f"COMMON:STANDARD:{standard_index:03d}",
                "root_assignment_id": f"ROOT:{standard_index}",
                "trigger_path": binding, "terminal_kind": "FIELD_RELEASE",
                "state": {
                    "flags": [{"id": visibility_flag, "value": False}],
                    "vars": [], "items": [], "trainers": [],
                },
                "control_requirements": {
                    "external": [], "internal": [],
                    "missing_external": [],
                    "all_external_requirements_materialized": True,
                },
                "input_sequence": {
                    "expected_static_branch_token": "UNIT",
                },
            })
            self.assertEqual(projection["interaction"]["local_id"], local_id)
            self.assertEqual(
                projection["state"]["flags"],
                [{"id": visibility_flag, "value": False}],
            )

        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("s61_event_common_dispatch_sample", source)
        self.assertIn('read_register(core, "r2")', source)
        self.assertIn('read_register(core, "r1")', source)
        self.assertIn("WORLD_SPECIAL_LAST_TALKED", source)
        self.assertNotRegex(
            source,
            r"event_consumer_instruction_pc\s*=\s*"
            r"trigger\.caller_instruction_pc",
        )

    def test_map_resume_evidence_rejects_host_only_false_positives(self) -> None:
        trigger = RUNNER._normalize_event_trigger_path(
            self._map_resume_trigger(), "unit-map-resume-evidence",
        )
        evidence = {
            "seed_kind": "resume_callback",
            "contract": "STOCK_WARP_THEN_FIELD_RETURN",
            "source_map": "3/3", "predecessor_tile": [5, 5],
            "source_setup": True, "predecessor_tile_confirmed": True,
            "real_warp_step": True, "real_connection_step": False,
            "engine_teleport": False,
            "destination_map": "3/4", "arrival_tile": [7, 8],
            "destination_map_loaded": True, "arrival_tile_confirmed": True,
            "load_root_hit_map": "3/4", "load_root_hit_tile": [7, 8],
            "load_root_hit_identity_captured": True,
            "load_identity_source": "MAP_OWNER_ROOT_HIT",
            "field_return_root_hit_map": "3/4",
            "field_return_root_hit_tile": [7, 8],
            "field_return_root_hit_identity_captured": True,
            "map_owner_callback": True,
            "map_owner_hits_before_start": 0,
            "map_owner_hits_after_field_return": 3,
            "resume_callback_pc": "0x08012344", "resume_callback_hits": 1,
            "callback_install_instruction_pc": "0x08045678",
            "callback_install_hits": 1,
            "callback_dispatch_instruction_pc": "0x080456A0",
            "callback_dispatch_hits": 1,
            "callback_install_ordinal": 10,
            "callback_dispatch_ordinal": 20,
            "resume_callback_ordinal": 30, "map_owner_ordinal": 40,
            "callback_ordered": True,
            "field_recovered_before_start": True,
            "start_pressed": True, "start_menu_opened": True,
            "back_pressed": True,
            "field_return_callback_dispatched": True,
            "input_recovered": True, "direct_callback_call": False,
            "lifecycle_order": (
                "SOURCE_SETUP_WARP_STEP_LOAD_ROOT_FIELD_START_BACK_"
                "CALLBACK_OWNER"
            ),
        }
        RUNNER._validate_event_map_transition_evidence(
            evidence, trigger, root_hits=3, label="unit-map-resume",
        )
        stock_source = self._map_resume_trigger()
        stock_source["stock_warp"] = stock_source.pop("resume_callback")[
            "actual_predecessor_consumer"
        ]["stock_warp"]
        stock = RUNNER._normalize_event_trigger_path(
            stock_source, "unit-map-stock-evidence",
        )
        stock_evidence = deepcopy(evidence)
        stock_evidence.update({
            "seed_kind": "stock_warp",
            "contract": "STOCK_WARP",
            "map_owner_hits_before_start": 0,
            "resume_callback_pc": "0x00000000", "resume_callback_hits": 0,
            "callback_install_instruction_pc": "0x00000000",
            "callback_install_hits": 0,
            "callback_dispatch_instruction_pc": "0x00000000",
            "callback_dispatch_hits": 0,
            "callback_install_ordinal": 0,
            "callback_dispatch_ordinal": 0,
            "resume_callback_ordinal": 0, "map_owner_ordinal": 40,
            "callback_ordered": False,
            "field_recovered_before_start": False,
            "start_pressed": False, "start_menu_opened": False,
            "back_pressed": False,
            "field_return_callback_dispatched": False,
            "input_recovered": False,
            "field_return_root_hit_map": "0/0",
            "field_return_root_hit_tile": [0, 0],
            "field_return_root_hit_identity_captured": False,
            "lifecycle_order": "SOURCE_SETUP_WARP_STEP_LOAD_ROOT_OWNER",
        })
        RUNNER._validate_event_map_transition_evidence(
            stock_evidence, stock, root_hits=3, label="unit-map-stock",
        )
        settled_resume = deepcopy(evidence)
        settled_resume["load_root_hit_identity_captured"] = False
        settled_resume["load_identity_source"] = "SETTLED_PREDECESSOR_FIELD"
        RUNNER._validate_event_map_transition_evidence(
            settled_resume, trigger, root_hits=3,
            label="unit-map-resume-settled-predecessor",
        )

        connection_source = self._map_resume_trigger()
        predecessor = connection_source.pop("resume_callback")[
            "actual_predecessor_consumer"
        ]["stock_warp"]
        connection_source["stock_connection"] = {
            "kind": "STOCK_CONNECTION_BOUNDARY_STEP",
            "source": {
                "group": predecessor["source"]["group"],
                "map": predecessor["source"]["map"],
            },
            "predecessor_tile": predecessor["predecessor_tile"],
            "trigger_tile": predecessor["trigger_tile"],
            "trigger_key": predecessor["trigger_key"],
            "destination": {
                "group": predecessor["destination"]["group"],
                "map": predecessor["destination"]["map"],
            },
            "arrival_tile": predecessor["arrival_tile"],
            "connection_or_warp_record_address": (
                predecessor["connection_or_warp_record_address"]
            ),
            "source_provenance": {"kind": "UNIT_CONNECTION_RECORD"},
        }
        connection = RUNNER._normalize_event_trigger_path(
            connection_source, "unit-map-connection-evidence",
        )
        connection_evidence = deepcopy(stock_evidence)
        connection_evidence.update({
            "seed_kind": "stock_connection",
            "contract": "STOCK_CONNECTION_BOUNDARY_STEP",
            "real_warp_step": False, "real_connection_step": True,
            "lifecycle_order": "SOURCE_SETUP_CONNECTION_STEP_LOAD_ROOT_OWNER",
        })
        RUNNER._validate_event_map_transition_evidence(
            connection_evidence, connection, root_hits=3,
            label="unit-map-connection-result-pass",
        )

        engine_source = self._map_resume_trigger()
        engine_source.pop("resume_callback")
        engine_source["engine_teleport"] = {
            "kind": "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
            "destination": {"group": 3, "map": 4},
            "start_tile": {"x": 7, "y": 8},
            "engine_entry": "BOOTSTRAP_KANTO_WARP",
            "source_provenance": self._engine_teleport_provenance(),
        }
        engine = RUNNER._normalize_event_trigger_path(
            engine_source, "unit-map-engine-first-root-before-rewarp",
        )
        engine_evidence = deepcopy(stock_evidence)
        engine_evidence.update({
            "seed_kind": "engine_teleport",
            "contract": "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
            "source_map": "0/0", "predecessor_tile": [7, 8],
            "real_warp_step": False, "engine_teleport": True,
            "lifecycle_order": "ENGINE_TELEPORT_LOAD_ROOT_OWNER",
        })
        RUNNER._validate_event_map_transition_evidence(
            engine_evidence, engine, root_hits=3,
            label="unit-map-engine-immediate-rewarp-first-root",
        )
        mutations = (
            ("source_setup", False),
            ("real_warp_step", False),
            ("destination_map_loaded", False),
            ("resume_callback_hits", 0),
            ("callback_dispatch_hits", 0),
            ("callback_dispatch_ordinal", 5),
            ("start_menu_opened", False),
            ("input_recovered", False),
            ("direct_callback_call", True),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                broken = deepcopy(evidence)
                broken[key] = value
                with self.assertRaises(RUNNER.Stage61MgbaError):
                    RUNNER._validate_event_map_transition_evidence(
                        broken, trigger, root_hits=3,
                        label=f"unit-map-resume-{key}",
                    )

    def test_map_resume_c_source_uses_real_field_lifecycle_only(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "SOURCE_SETUP_WARP_STEP_LOAD_ROOT_FIELD_START_BACK_CALLBACK_OWNER",
            source,
        )
        self.assertIn("trigger->source_group, trigger->source_map", source)
        self.assertIn("sequence->steps[0].key", source)
        self.assertIn("sequence->steps[1].key", source)
        self.assertIn("s61_event_resume_callback_ordered", source)
        self.assertIn(
            "result->map_real_connection_step = connection", source,
        )
        self.assertIn("|| drive.map_real_connection_step", source)
        self.assertIn(
            "result->map_load_root_identity_captured || resume", source,
        )
        self.assertIn("S61_EVENT_TRIGGER_FIELD_COUNT = 67U", source)
        self.assertIn("WORLD_MAP_SCRIPT_ON_FRAME_CALLSITE_PC = 0x08069548U", source)
        self.assertIn("WORLD_MAP_SCRIPT_ON_WARP_IN_CALLSITE_PC = 0x08069568U", source)
        self.assertIn("event_map_condition_target_readback_exact", source)
        self.assertIn("event_map_precedence_guards_readback_exact", source)
        self.assertNotIn(
            "s61_call_synced(core, trigger->resume_callback", source,
        )

    def test_event_signed_ram_deferred_control_requires_actual_dispatch(
        self,
    ) -> None:
        expected = [{
            "kind": "SIGNED_RAM_SCRIPT", "id": 0x08100020,
            "required_value_in_matrix_case": {
                "variant": "VALID_SET_VAR_RETURN",
                "expected_dispatch": True,
                "expected_var_8004": 0x61A5,
                "expected_ram_script_after": "UNCHANGED",
            },
        }]
        observed = [{
            "kind": "SIGNED_RAM_SCRIPT",
            "instruction_address": "0x08100020", "variant": 1,
            "expected_dispatch": True, "observed_dispatch": True,
            "ram_script_program_hit_count": 1,
            "expected_var_8004": 0x61A5,
            "observed_var_8004": 0x61A5,
            "expected_ram_script_cleared": False,
            "ram_script_postcondition_exact": True,
            "actual_object_consumer_only": True,
        }]
        normalized = RUNNER._validate_deferred_external_controls(
            observed, expected, label="event signed unit",
        )
        self.assertEqual(normalized, observed)
        for key, value in (
            ("observed_dispatch", False),
            ("ram_script_program_hit_count", 0),
            ("observed_var_8004", 0),
            ("ram_script_postcondition_exact", False),
            ("actual_object_consumer_only", False),
        ):
            with self.subTest(key=key):
                broken = deepcopy(observed)
                broken[0][key] = value
                with self.assertRaisesRegex(
                    RUNNER.Stage61MgbaError,
                    "signed RAM dispatch/postcondition",
                ):
                    RUNNER._validate_deferred_external_controls(
                        broken, expected, label=f"event signed {key}",
                    )

    def test_rematch_deferred_control_requires_prewarp_seed_and_no_writes(
        self,
    ) -> None:
        expected = [{
            "kind": "REMATCH_STATE", "id": 7,
            "required_value_in_matrix_case": {
                "ready": True, "local_id": 7,
                "saveblock1_offset": 0x063A + 7,
                "ready_byte": 1,
            },
        }]
        observed = [{
            "kind": "REMATCH_STATE", "local_id": 7,
            "last_talked": 7, "saveblock1_offset": 0x063A + 7,
            "expected_ready_byte": 1,
            "seeded_before_stock_warp": True,
            "postwarp_readback_exact": True,
            "pre_a_readback_exact": True,
            "producer_observed_ready_byte": 1,
            "postinteraction_ready_byte": 0,
            "actual_object_consumer_hit_count": 1,
            "producer_window_host_writes": 0,
            "host_wrote_last_talked": False,
        }]
        normalized = RUNNER._validate_deferred_external_controls(
            observed, expected, label="rematch unit",
        )
        self.assertEqual(normalized, observed)
        for key, value in (
            ("seeded_before_stock_warp", False),
            ("postwarp_readback_exact", False),
            ("pre_a_readback_exact", False),
            ("producer_observed_ready_byte", 0),
            ("actual_object_consumer_hit_count", 0),
            ("producer_window_host_writes", 1),
            ("host_wrote_last_talked", True),
        ):
            with self.subTest(key=key):
                broken = deepcopy(observed)
                broken[0][key] = value
                with self.assertRaisesRegex(
                    RUNNER.Stage61MgbaError, "rematch actual consumer",
                ):
                    RUNNER._validate_deferred_external_controls(
                        broken, expected, label=f"rematch {key}",
                    )

    def test_event_physical_walk_preserves_non_up_multistep_and_common(self) -> None:
        bg_raw = {
            "kind": "BG_FACE_A", "group": 3, "map": 4,
            "x": 2, "y": 2, "elevation": 0,
            "start_tile": {"x": 1, "y": 1},
            "walk_sequence": ["RIGHT", "DOWN", "RIGHT"],
            "stance_tile": {"x": 3, "y": 2},
            "required_facing": "LEFT", "root_pc": "0x08123401",
        }
        bg = RUNNER._normalize_event_trigger_path(bg_raw, "unit-bg-walk")
        evidence = {
            "start_tile": [1, 1],
            "walk_sequence": ["RIGHT", "DOWN", "RIGHT"],
            "expected_tiles": [[2, 1], [2, 2], [3, 2]],
            "observed_tiles": [[2, 1], [2, 2], [3, 2]],
            "step_count": 3, "start_tile_confirmed": True,
            "all_intermediate_tiles_confirmed": True,
            "final_tile_confirmed": True, "stance_tile": [3, 2],
            "stance_confirmed": True, "trigger_key": None,
            "required_facing": "LEFT",
            "runtime_topology_probe_required": False,
            "runtime_topology_probe_satisfied": True,
        }
        RUNNER._validate_event_physical_walk_evidence(
            evidence, bg, "unit-bg-walk",
        )
        common = RUNNER._normalize_event_trigger_path({
            "kind": "COMMON_CALLER_TRIGGER", "standard_index": 2,
            "caller_owner_id": "BG:003/004:000", "caller_owner_kind": "BG",
            "caller_instruction_pc": "0x08120001",
            "caller_trigger_path": bg_raw, "root_pc": "0x08130001",
        }, "unit-common-bg-walk")
        self.assertEqual(
            common["caller_trigger_path"]["walk_sequence"],
            ["RIGHT", "DOWN", "RIGHT"],
        )
        coord = RUNNER._normalize_event_trigger_path({
            "kind": "COORD_STEP", "group": 3, "map": 4,
            "x": 4, "y": 6, "elevation": 0,
            "trigger_var": 0, "trigger_value": 0,
            "start_tile": {"x": 5, "y": 5},
            "walk_sequence": ["DOWN", "LEFT"],
            "trigger_key": "LEFT", "root_pc": "0x08124001",
        }, "unit-coord-walk")
        self.assertEqual(coord["trigger_key"], "LEFT")
        object_raw = {
            "kind": "OBJECT_FACE_A", "group": 3, "map": 4,
            "local_id": 2, "object_index": 1,
            "root_pc": "0x08125001", "approach": "WALK_ADJACENT_FACE_A",
            "start_tile": {"x": 8, "y": 8}, "walk_sequence": [],
            "stance_tile": {"x": 8, "y": 8},
            "required_facing": "DOWN",
            "runtime_topology_probe_required": True,
        }
        object_path = RUNNER._normalize_event_trigger_path(
            object_raw, "unit-object-topology-probe",
        )
        self.assertEqual(object_path["walk_sequence"], [])
        self.assertIs(object_path["runtime_topology_probe_required"], True)
        bad_object = deepcopy(object_raw)
        bad_object["runtime_topology_probe_required"] = False
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "topology probe"):
            RUNNER._normalize_event_trigger_path(
                bad_object, "unit-object-empty-without-probe",
            )
        broken_evidence = deepcopy(evidence)
        broken_evidence["observed_tiles"][1] = [99, 99]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "physical walk"):
            RUNNER._validate_event_physical_walk_evidence(
                broken_evidence, bg, "unit-bg-dynamic-topology",
            )
        bad_endpoint = deepcopy(bg_raw)
        bad_endpoint["walk_sequence"] = ["RIGHT", "RIGHT"]
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "walk終点"):
            RUNNER._normalize_event_trigger_path(
                bad_endpoint, "unit-bg-bad-endpoint",
            )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "event runtime loaded-field intermediate walk tile differs", source,
        )
        self.assertNotIn("s61_event_closed_walk_cycle", source)

    def test_hidden_item_and_coin_variants_bind_shared_root_and_dispatch(
        self,
    ) -> None:
        base = {
            "kind": "HIDDEN_ITEM", "group": 3, "map": 4,
            "variant": "AVAILABLE_SUCCESS", "x": 5, "y": 6,
            "elevation": 0, "underfoot": False, "item_id": 1,
            "quantity": 1, "collection_flag": 0x3E8,
            "consumer_root_expected_hit": True,
            "entry": "FACE_A", "consumer_script_root": "0x0819410F",
            "source_provenance": {"kind": "UNIT_HIDDEN_ENGINE"},
            "start_tile": {"x": 2, "y": 6},
            "walk_sequence": ["RIGHT", "RIGHT"],
            "stance_tile": {"x": 4, "y": 6},
            "required_facing": "RIGHT",
        }
        variants = {
            "AVAILABLE_SUCCESS", "AVAILABLE_BAG_FULL",
            "AVAILABLE_COIN_FULL", "AVAILABLE_NO_COIN_CASE",
            "ALREADY_COLLECTED",
        }
        for variant in variants:
            with self.subTest(variant=variant):
                raw = deepcopy(base)
                raw["variant"] = variant
                raw["consumer_root_expected_hit"] = (
                    variant != "ALREADY_COLLECTED"
                )
                trigger = RUNNER._normalize_event_trigger_path(
                    raw, f"unit-hidden-{variant}",
                )
                self.assertEqual(trigger["consumer_script_root"], 0x0819410F)
                fields = RUNNER._event_trigger_fields({
                    "case_id": f"hidden-{variant.lower()}",
                    "owner_id": "HIDDEN:003/004:000",
                    "root_assignment_id": None,
                    "trigger_path": trigger,
                    "terminal_kind": "FIELD_RELEASE",
                })
                self.assertEqual(fields[5], str(0x0819410F))
                self.assertEqual(fields[6], str(0x0806C902))
        unknown = deepcopy(base)
        unknown["variant"] = "COIN_HOST_SHORTCUT"
        with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "variant"):
            RUNNER._normalize_event_trigger_path(unknown, "unit-hidden-bad")

    def test_structural_nontrigger_evidence_binds_null_and_dormant_common7(
        self,
    ) -> None:
        null_owner = {
            "owner_id": "BG:003/004:000", "owner_kind": "BG",
            "representative_runtime_root": None,
            "trigger_consumer": {
                "symbol": "NULL_EVENT_RECORD", "entry": None,
                "source": None,
            },
            "entry_condition": {
                "relation": "ENGINE_TREATS_NULL_AS_NO_EVENT_SCRIPT",
                "record_address": "0x08123400",
            },
            "effect_evidence": {
                "relation": "NO_SCRIPT_DISPATCH_NO_MUTATION",
            },
        }
        normalized_null = RUNNER._normalize_structural_nontrigger_evidence(
            null_owner, "unit-null", null_scope_asserted=True,
        )
        self.assertEqual(normalized_null["raw_root"], 0)
        self.assertIs(
            normalized_null["zero_raw_proven_by_final_inventory_scope"],
            True,
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "zero raw",
        ):
            RUNNER._normalize_structural_nontrigger_evidence(
                null_owner, "unit-null-no-scope", null_scope_asserted=False,
            )

        cfg_nodes = []
        for address, raw_hex, end_reason, edges in (
            ("0x08194038", "4b0080", "goto", ["0x08194040"]),
            ("0x08194040", "0200", "call", ["0x08194050"]),
            ("0x08194050", "0300", "return", []),
            ("0x08194060", "0400", "end", []),
        ):
            raw = bytes.fromhex(raw_hex)
            cfg_nodes.append({
                "address": address, "end_reason": end_reason,
                "raw_hex": raw_hex,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "edges": edges,
            })
        evidence = {
            "kind": "UNREFERENCED_STANDARD_SCRIPT_TABLE_ENTRY",
            "owner_id": "COMMON:STANDARD:007", "standard_index": 7,
            "record_address": "0x08163774",
            "table_raw_hex": "38401908",
            "table_raw_sha256": hashlib.sha256(
                bytes.fromhex("38401908"),
            ).hexdigest(),
            "representative_runtime_root": "0x08194038",
            "clean_final_cfg_identical": True,
            "cfg_node_count": 4, "cfg_nodes": cfg_nodes,
            "cfg_sha256": RUNNER._event_contract_sha256(cfg_nodes),
            "live_noncommon_root_count": 5414,
            "live_caller_count": 0,
            "live_caller_instruction_addresses": [],
            "source_provenance": {"kind": "UNIT_STATIC_CFG"},
            "assertions": {
                "table_entry_exact": True,
                "clean_final_full_cfg_identical": True,
                "all_noncommon_live_cfg_caller_count_zero": True,
                "coverage_only_consumer_not_invented": True,
            },
        }
        evidence["evidence_sha256"] = RUNNER._event_contract_sha256(evidence)
        common_owner = {
            "owner_id": "COMMON:STANDARD:007", "owner_kind": "COMMON",
            "consumer_subkind": (
                "UNREFERENCED_STANDARD_SCRIPT_TABLE_ENTRY"
            ),
            "representative_runtime_root": "0x08194038",
            "trigger_consumer": {
                "symbol": "Std_ObtainDecoration", "entry": None,
                "source": {"kind": "UNIT_STATIC_CFG"},
            },
            "entry_condition": {
                "relation": "ALL_FINAL_NONCOMMON_CFG_CALLER_COUNT_ZERO",
                "standard_index": 7,
                "structural_evidence": evidence,
            },
            "effect_evidence": {
                "relation": "NO_LIVE_DISPATCH_NO_PRODUCT_MUTATION",
                "coverage_only_caller_forbidden": True,
            },
        }
        normalized_common = RUNNER._normalize_structural_nontrigger_evidence(
            common_owner, "unit-common7", null_scope_asserted=True,
        )
        self.assertEqual(normalized_common["live_caller_count"], 0)
        self.assertEqual(
            normalized_common["representative_runtime_root"], "0x08194038",
        )
        for mutation in ("caller", "table", "cfg", "evidence_digest"):
            with self.subTest(mutation=mutation):
                broken = deepcopy(common_owner)
                broken_evidence = broken["entry_condition"][
                    "structural_evidence"
                ]
                if mutation == "caller":
                    broken_evidence["live_caller_count"] = 1
                    broken_evidence[
                        "live_caller_instruction_addresses"
                    ] = ["0x08120000"]
                elif mutation == "table":
                    broken_evidence["table_raw_hex"] = "00000000"
                elif mutation == "cfg":
                    broken_evidence["cfg_nodes"][0]["raw_hex"] = "000080"
                else:
                    broken_evidence["evidence_sha256"] = "0" * 64
                with self.assertRaises(RUNNER.Stage61MgbaError):
                    RUNNER._normalize_structural_nontrigger_evidence(
                        broken, f"unit-common7-{mutation}",
                        null_scope_asserted=True,
                    )

    def test_engine_special_flag_lifecycle_exact_two_branch_capture(self) -> None:
        fixtures = RUNNER.validate_fixture_document(
            self._generated_fixture_source()
        )
        fixture = fixtures["engine_special_flag_lifecycle"]
        capture = self._calibration_document()["results"][0][
            "successful_paths"
        ][0]["capture"]
        owners = {
            row["owner_id"]: row
            for row in fixture["producer"]["record_owners"]
        }
        rows = []
        for variant in fixture["producer"]["variants"]:
            owner = owners[variant["coord_owner_id"]]
            rows.append({
                "variant": variant["variant"],
                "temporary_side": variant["temporary_side"],
                "producer_map": fixture["producer"]["map"],
                "start": variant["start"],
                "trigger_tile": variant["trigger_tile"],
                "walk_key": RUNNER.KEYS[variant["walk_tokens"][0]],
                "actual_walk_steps": 1,
                "direct_script_call": False,
                "coord_root": f"0x{owner['runtime_root']:08X}",
                "coord_root_hits": 1,
                "set_site": f"0x{fixture['producer']['set_site']:08X}",
                "set_site_hits": 1,
                "flag_clear_before_step": True,
                "get_flag_addr_return": fixture["runtime_storage"][
                    "owner_address"
                ],
                "flag_get_before_step": False,
                "raw_flag_before_step": False,
                "flag_set_observed": True,
                "flag_get_during_producer": True,
                "raw_flag_during_producer": True,
                "destination_map": fixture["transition"]["destination_map"],
                "destination_position": fixture["transition"][
                    "destination_position"
                ],
                "destination_endpoint_observed": True,
                "final_position": [6, 8],
                "map_transition_observed": True,
                "map_root": (
                    f"0x{fixture['consumer']['owner']['runtime_root']:08X}"
                ),
                "map_root_hits": 1,
                "clear_site": f"0x{fixture['consumer']['clear_site']:08X}",
                "clear_site_hits": 1,
                "flag_clear_observed_after_consumer": True,
                "flag_get_after_consumer": False,
                "raw_flag_after_consumer": False,
                "api_raw_trace_ordered": True,
                "bgm_transition_completed": True,
                "bgm": {
                    "current_before_idle": 300,
                    "current_after_idle": 300,
                    "next_before_idle": 0,
                    "next_after_idle": 0,
                    "state_before_idle": 2,
                    "state_after_idle": 2,
                    "stable_normal_play": True,
                },
                "start_menu_opened": True,
                "field_input_recovered": True,
                "input_advance_pulses": 1,
                "trace_ordered": True,
                "trace": fixture["expected_trace"],
                "invalid_control_flow": False,
                "capture": deepcopy(capture),
            })
        document = {
            "schema_version": 1,
            "status": "PASS",
            "case": "engine_special_flag_lifecycle",
            "kind": fixture["kind"],
            "flag_id": f"0x{fixture['flag_id']:04X}",
            "owner_address": fixture["runtime_storage"]["owner_address"],
            "bit_mask": fixture["runtime_storage"]["bit_mask"],
            "actual_coord_step_variant_count": 2,
            "direct_engine_flag_call": False,
            "results": rows,
            "all_trace_ordered": True,
            "all_final_engine_special_flag_clear": True,
            "final_map": fixture["transition"]["destination_map"],
            "invalid_script_pc_count": 0,
            "softlock_count": 0,
            "failed": 0,
            "untested": 0,
            "warnings": 0,
            "framebuffer_artifacts": [],
        }
        normalized = RUNNER._validate_case(
            document, "engine_special_flag_lifecycle", fixtures,
            RUNNER._read_charmap(), {}, {},
        )
        self.assertIs(normalized["fixture_lifecycle_exact"], True)
        self.assertIs(normalized["producer_consumer_branches_complete"], True)
        self.assertIs(normalized["get_flag_addr_core_verified"], True)
        self.assertIs(normalized["api_raw_trace_exact"], True)
        self.assertIs(normalized["stock_warp_endpoint_both_observed"], True)
        self.assertIs(normalized["final_position_converged"], True)
        self.assertIs(normalized["bgm_stable_normal_play"], True)
        self.assertEqual(
            normalized["results"][0]["capture"]["framebuffer"]
            ["maximum_baseline_pixel_difference"],
            2500,
        )
        self.assertEqual(
            RUNNER._required_artifact_count(
                "engine_special_flag_lifecycle", normalized,
            ),
            2,
        )
        normalized["artifacts"] = [self._artifact(
            "engine_special_flag_lifecycle", f"{name}-peak.ppm",
            sha256=char * 64,
            rgb_fnv1a64=("A" if name == "left" else "B") * 16,
        ) for name, char in (("left", "1"), ("right", "2"))]
        final = RUNNER.validate_final_mgba_case_result(
            "engine_special_flag_lifecycle", normalized,
        )
        self.assertEqual(len(final["results"]), 2)

        mutations = {
            "missing-branch": lambda item: item["results"].pop(),
            "root-drift": lambda item: item["results"][0].__setitem__(
                "coord_root", "0x08000001"
            ),
            "clear-site-drift": lambda item: item["results"][1].__setitem__(
                "clear_site", "0x08000001"
            ),
            "missing-hit": lambda item: item["results"][0].__setitem__(
                "map_root_hits", 0
            ),
            "trace-drift": lambda item: item["results"][1]["trace"].pop(),
            "no-frame-diff": lambda item: item["results"][0]["capture"][
                "framebuffer"
            ].__setitem__("maximum_baseline_pixel_difference", 0),
            "direct-flag-shortcut": lambda item: item.__setitem__(
                "direct_engine_flag_call", True
            ),
            "get-flag-addr-drift": lambda item: item["results"][0].__setitem__(
                "get_flag_addr_return", "0x020370E0"
            ),
            "api-set-missing": lambda item: item["results"][0].__setitem__(
                "flag_get_during_producer", False
            ),
            "raw-set-missing": lambda item: item["results"][1].__setitem__(
                "raw_flag_during_producer", False
            ),
            "warp-endpoint-missing": lambda item: item["results"][0].__setitem__(
                "destination_endpoint_observed", False
            ),
            "branch-final-position-diverges": lambda item: item["results"][
                1
            ].__setitem__("final_position", [7, 8]),
            "bgm-fade-pending": lambda item: item["results"][0][
                "bgm"
            ].__setitem__("state_after_idle", 7),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                broken = deepcopy(document)
                mutate(broken)
                with self.assertRaises(RUNNER.Stage61MgbaError):
                    RUNNER._validate_case(
                        broken, "engine_special_flag_lifecycle", fixtures,
                        RUNNER._read_charmap(), {}, {},
                    )
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("s61_case_engine_special_flag_lifecycle", source)
        self.assertIn("WORLD_GET_FLAG_ADDR = 0x0806DDB5U", source)
        self.assertIn("get_flag_addr_before == flag_owner", source)
        self.assertIn("s61_write_peak_frame(&capture, \"peak\")", source)
        self.assertIn(
            "capture.maximum_baseline_pixel_difference > 0U", source,
        )
        self.assertIn(
            'strcmp(argv[3], "engine_special_flag_lifecycle") == 0',
            source,
        )

    def test_all_final_case_anchor_keys_are_source_derived_and_fail_closed(
        self,
    ) -> None:
        derived = tuple(
            case for cases in RUNNER.CASE_DOMAINS.values() for case in cases
        )
        self.assertEqual(RUNNER.ALL_CASES, derived)
        self.assertEqual(len(derived), len(set(derived)))
        RUNNER._validate_final_mgba_case_registry_closure()
        self.assertEqual(
            set(RUNNER._FINAL_MGBA_CASE_REQUIRED_KEYS),
            set(RUNNER.ALL_CASES),
        )
        self.assertEqual(
            set(RUNNER._FINAL_MGBA_CASE_SCHEMA_VERSIONS),
            set(RUNNER.ALL_CASES),
        )
        self.assertEqual(
            set(RUNNER._FINAL_MGBA_CASE_ZERO_COUNTERS),
            set(RUNNER.ALL_CASES),
        )
        self.assertEqual(
            RUNNER._FINAL_MGBA_CASE_SCHEMA_VERSIONS["catalog_batch"], 9,
        )
        self.assertEqual(
            RUNNER._FINAL_MGBA_CASE_SCHEMA_VERSIONS["catalog_calibrate"], 2,
        )
        self.assertEqual(
            RUNNER._FINAL_MGBA_CASE_SCHEMA_VERSIONS[
                "catalog_state_persistence"
            ], 2,
        )
        self.assertEqual(
            RUNNER._FINAL_MGBA_CASE_SCHEMA_VERSIONS[
                "catalog_state_legacy_persistence"
            ], 2,
        )
        self.assertEqual(
            RUNNER._FINAL_MGBA_CASE_SCHEMA_VERSIONS["map_popup"], 3,
        )
        self.assertEqual(
            RUNNER._FINAL_MGBA_CASE_SCHEMA_VERSIONS[
                "partial_link_save_persistence"
            ],
            2,
        )
        for label, source in (
            ("deletion", RUNNER._FINAL_MGBA_CASE_REQUIRED_KEYS),
            ("extra", RUNNER._FINAL_MGBA_CASE_SCHEMA_VERSIONS),
            ("rename", RUNNER._FINAL_MGBA_CASE_ZERO_COUNTERS),
        ):
            broken = dict(source)
            first = RUNNER.ALL_CASES[0]
            if label == "deletion":
                del broken[first]
            elif label == "extra":
                broken["not-a-real-case"] = 1
            else:
                broken["renamed-case"] = broken.pop(first)
            kwargs = {
                "required_keys": (
                    broken if label == "deletion"
                    else RUNNER._FINAL_MGBA_CASE_REQUIRED_KEYS
                ),
                "schema_versions": (
                    broken if label == "extra"
                    else RUNNER._FINAL_MGBA_CASE_SCHEMA_VERSIONS
                ),
                "zero_counters": (
                    broken if label == "rename"
                    else RUNNER._FINAL_MGBA_CASE_ZERO_COUNTERS
                ),
            }
            with self.subTest(registry_mutation=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "case closure",
            ):
                RUNNER._validate_final_mgba_case_registry_closure(**kwargs)
        for case, keys in RUNNER._FINAL_MGBA_CASE_REQUIRED_KEYS.items():
            with self.subTest(case=case, key="positive"):
                document = {key: True for key in keys}
                RUNNER._validate_final_mgba_anchor_presence(case, document)
            for key in keys:
                with self.subTest(case=case, key=key):
                    broken = {item: True for item in keys if item != key}
                    with self.assertRaisesRegex(
                        RUNNER.Stage61MgbaError, "anchor欠落",
                    ):
                        RUNNER._validate_final_mgba_anchor_presence(
                            case, broken,
                        )

    def test_orchestrator_identity_binds_current_python_source(self) -> None:
        identity = RUNNER.build_orchestrator_identity()
        self.assertEqual(identity, {
            "source": "scripts/run_stage61_mgba_validation.py",
            "source_sha256": hashlib.sha256(
                RUNNER_PATH.read_bytes()
            ).hexdigest(),
            "status": "PASS",
        })

    def test_final_event_anchor_consumer_zero_and_hidden_collected_root(self) -> None:
        capture = deepcopy(
            self._calibration_document()["results"][0][
                "successful_paths"
            ][0]["capture"]
        )
        capture = RUNNER._validate_catalog_capture(
            capture, case_id="unit-final-event", charmap=RUNNER._read_charmap(),
            require_visible_text=False,
        )

        def document(*, hidden_collected: bool) -> dict[str, object]:
            root = "0x0819410F" if hidden_collected else "0x08123401"
            evidence = {
                "direct_script_call": False,
                "host_map_setup": True,
                "consumer_pc": (
                    "0x0806C902" if hidden_collected else "0x00000000"
                ),
                "consumer_hits": 1 if hidden_collected else 0,
                "root_script_pointer": root,
                "root_script_pointer_hits": 0 if hidden_collected else 1,
                "first_root_script_pointer": (
                    "0x00000000" if hidden_collected else root
                ),
                "map_transition": None,
            }
            attempt = {
                "success": True, "failure_reason": "NONE",
                "sequence_id": "unit-sequence",
                "input_step_count": 1, "input_steps_consumed": 1,
                "visible_text_expected": False,
                "terminal": "FIELD_RELEASE",
                "battle_started": False, "field_released": True,
                "post_battle": {
                    "battle_started": False, "trainer_battle": False,
                    "completed_via_keys": False,
                    "forced_switch_count": 0,
                    "forced_switch_cursor_observed": False,
                    "forced_switch_usable_slot_selected": False,
                    "forced_switch_cursor_initial": [],
                    "forced_switch_selected_slots": [],
                    "forced_switch_selected_hps": [],
                    "route": "NONE", "outcome": 0,
                    "won_or_escaped_not_loss": False,
                    "field_released_after_battle": False,
                    "start_pressed": False, "start_menu_opened": False,
                    "back_pressed": False, "map_preserved": False,
                    "field_input_recovered": False,
                },
                "text_oracle_match": {
                    "independent_provenance": True,
                    "actual_ordered_raw_sha256s": [],
                    "visible_text_count": 0,
                    "unclassified_visible_printer_calls": 0,
                },
                "post_effect_contract": {
                    "deny_by_default": True,
                    "required_postconditions_satisfied": True,
                    "actual_families": [],
                    "observed": {"flags": []},
                },
                "battle_start_side_effects": None,
                "side_effects": {
                    "complete": True,
                    "coverage": {
                        key: {} for key in (
                            "flags", "engine_special_flags", "vars",
                            "items", "trainers", "objects",
                            "object_templates", "party", "storage",
                            "persistent",
                        )
                    },
                    "flags": [], "engine_special_flags": [], "vars": [],
                    "items": [], "trainers": [], "economy": {},
                    "party": {}, "storage": {}, "persistent": {},
                    "objects": {}, "world": {}, "object": {},
                    "battle": {"after": {"active": False}},
                    "input": {
                        "recovered": True,
                        "after": {
                            "field_input_recovered": True,
                            "battle_input_owned": False,
                        },
                    },
                },
                "capture": deepcopy(capture),
            }
            row = {
                "case_id": "unit-hidden" if hidden_collected else "unit-object",
                "owner_id": "UNIT:OWNER",
                "effective_kind": (
                    "HIDDEN_ITEM" if hidden_collected else "OBJECT_FACE_A"
                ),
                "root_expected_hit": not hidden_collected,
                "trigger_evidence": evidence,
                "input_sequence_attempt": attempt,
            }
            result = {
                "schema_version": 2, "status": "PASS",
                "case": "event_runtime_batch",
                "actual_consumer_trigger_dispatch": True,
                "fixture_count": 1, "owner_count": 1,
                "source_owner_count": 1,
                "sequence_count": 1, "failed": 0, "untested": 0,
                "warnings": 0,
                "results": [row],
                "executed_owner_ids": ["UNIT:OWNER"],
                "executed_owner_count": 1,
                "executed_logical_owner_ids": ["UNIT:OWNER"],
                "executed_logical_owner_count": 1,
                "executed_sequence_ids": ["unit-sequence"],
                "executed_case_ids": [row["case_id"]],
                "source_case_ids": [row["case_id"]],
                "source_case_count": 1,
                "executed_source_case_ids": [row["case_id"]],
                "artifacts": [self._artifact(
                    "event_runtime_batch", "unit-peak.ppm",
                )],
            }
            result.update(RUNNER._event_map_transition_seed_summary([row]))
            return result

        for hidden in (False, True):
            with self.subTest(hidden=hidden):
                RUNNER.validate_final_mgba_case_result(
                    "event_runtime_batch", document(hidden_collected=hidden),
                )
        for label, mutate in {
            "schema": lambda item: item.__setitem__("schema_version", 1),
            "failed-missing": lambda item: item.pop("failed"),
            "untested-missing": lambda item: item.pop("untested"),
            "warnings-missing": lambda item: item.pop("warnings"),
        }.items():
            broken_root = document(hidden_collected=False)
            mutate(broken_root)
            with self.subTest(label=label), self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "root status",
            ):
                RUNNER.validate_final_mgba_case_result(
                    "event_runtime_batch", broken_root,
                )
        mutations = {
            "zero-consumer-fake-hit": lambda item: item["results"][0][
                "trigger_evidence"
            ].__setitem__("consumer_hits", 1),
            "nonzero-consumer-missing-hit": lambda item: item["results"][0][
                "trigger_evidence"
            ].__setitem__("consumer_hits", 0),
            "required-root-missing": lambda item: item["results"][0][
                "trigger_evidence"
            ].__setitem__("root_script_pointer_hits", 0),
            "collected-hidden-fake-root": lambda item: item["results"][0][
                "trigger_evidence"
            ].__setitem__("root_script_pointer_hits", 1),
        }
        for label, mutate in mutations.items():
            hidden = label in {
                "nonzero-consumer-missing-hit", "collected-hidden-fake-root",
            }
            broken = document(hidden_collected=hidden)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER.validate_final_mgba_case_result(
                    "event_runtime_batch", broken,
                )

    def test_final_map_transition_contracts_and_production_recount(self) -> None:
        direct_contract = {
            "stock_warp": "STOCK_WARP",
            "stock_connection": "STOCK_CONNECTION_BOUNDARY_STEP",
            "engine_teleport": "ENGINE_PLAYER_TELEPORT_MAP_LOAD",
        }
        resume_contract = {
            "stock_warp": "STOCK_WARP_THEN_FIELD_RETURN",
            "stock_connection": "STOCK_CONNECTION_THEN_FIELD_RETURN",
            "engine_teleport": "ENGINE_TELEPORT_THEN_FIELD_RETURN",
        }

        def transition(mechanism: str, *, resume: bool) -> dict[str, object]:
            value = {
                "seed_kind": "resume_callback" if resume else mechanism,
                "contract": (
                    resume_contract[mechanism] if resume
                    else direct_contract[mechanism]
                ),
                "source_map": "0/0" if mechanism == "engine_teleport" else "3/3",
                "predecessor_tile": [5, 5],
                "source_setup": True, "predecessor_tile_confirmed": True,
                "real_warp_step": mechanism == "stock_warp",
                "real_connection_step": mechanism == "stock_connection",
                "engine_teleport": mechanism == "engine_teleport",
                "destination_map": "3/4", "arrival_tile": [7, 8],
                "destination_map_loaded": True,
                "arrival_tile_confirmed": True,
                "load_root_hit_map": "3/4", "load_root_hit_tile": [7, 8],
                "load_root_hit_identity_captured": not (
                    resume and mechanism == "engine_teleport"
                ),
                "load_identity_source": (
                    "SETTLED_PREDECESSOR_FIELD"
                    if resume and mechanism == "engine_teleport"
                    else "MAP_OWNER_ROOT_HIT"
                ),
                "field_return_root_hit_map": "3/4" if resume else "0/0",
                "field_return_root_hit_tile": [7, 8] if resume else [0, 0],
                "field_return_root_hit_identity_captured": resume,
                "map_owner_callback": True,
                "map_owner_hits_before_start": 1 if resume else 0,
                "map_owner_hits_after_field_return": 3,
                "resume_callback_pc": "0x08012344" if resume else "0x00000000",
                "resume_callback_hits": 1 if resume else 0,
                "callback_install_instruction_pc": (
                    "0x08045678" if resume else "0x00000000"
                ),
                "callback_install_hits": 1 if resume else 0,
                "callback_dispatch_instruction_pc": (
                    "0x080456A0" if resume else "0x00000000"
                ),
                "callback_dispatch_hits": 1 if resume else 0,
                "callback_install_ordinal": 10 if resume else 0,
                "callback_dispatch_ordinal": 20 if resume else 0,
                "resume_callback_ordinal": 30 if resume else 0,
                "map_owner_ordinal": 40,
                "callback_ordered": resume,
                "field_recovered_before_start": resume,
                "start_pressed": resume, "start_menu_opened": resume,
                "back_pressed": resume,
                "field_return_callback_dispatched": resume,
                "input_recovered": resume, "direct_callback_call": False,
                "lifecycle_order": "UNIT",
            }
            return value

        for resume in (False, True):
            for mechanism in direct_contract:
                with self.subTest(resume=resume, mechanism=mechanism):
                    RUNNER._final_mgba_event_map_transition_anchor(
                        transition(mechanism, resume=resume),
                        label="unit-final-map", root_hits=3,
                    )

        mutations = {
            "resume-start-bypass": (
                transition("stock_warp", resume=True),
                lambda item: item.__setitem__("start_pressed", False),
            ),
            "resume-field-root-missing": (
                transition("stock_connection", resume=True),
                lambda item: item.__setitem__(
                    "field_return_root_hit_identity_captured", False,
                ),
            ),
            "direct-engine-settled": (
                transition("engine_teleport", resume=False),
                lambda item: item.__setitem__(
                    "load_identity_source", "SETTLED_PREDECESSOR_FIELD",
                ),
            ),
            "resume-engine-root-substitution": (
                transition("engine_teleport", resume=True),
                lambda item: item.update({
                    "load_root_hit_identity_captured": True,
                    "load_identity_source": "MAP_OWNER_ROOT_HIT",
                }),
            ),
            "load-map-drift": (
                transition("stock_warp", resume=False),
                lambda item: item.__setitem__("load_root_hit_map", "3/5"),
            ),
            "callback-order-drift": (
                transition("stock_warp", resume=True),
                lambda item: item.__setitem__("callback_dispatch_ordinal", 5),
            ),
        }
        for label, (value, mutate) in mutations.items():
            mutate(value)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._final_mgba_event_map_transition_anchor(
                    value, label=label, root_hits=3,
                )

        def event_row(
            mechanism: str, *, resume: bool, ordinal: int,
        ) -> dict[str, object]:
            source_case_id = (
                f"map-lifecycle-003-{ordinal:03d}-"
                f"{ordinal:020x}"
            )
            return {
                "effective_kind": "MAP_TRANSITION_LOAD",
                "case_id": f"{source_case_id}--run-0000",
                "source_case_id": source_case_id,
                "owner_id": f"MAP_LIFECYCLE:003/{ordinal:03d}",
                "covered_owner_ids": [
                    f"MAP:003/{ordinal:03d}:000",
                ],
                "trigger_evidence": {
                    "map_transition": transition(mechanism, resume=resume),
                },
            }

        rows = [
            event_row("stock_warp", resume=False, ordinal=1),
            event_row("stock_warp", resume=True, ordinal=2),
            event_row("stock_connection", resume=False, ordinal=3),
            event_row("engine_teleport", resume=False, ordinal=4),
            event_row("engine_teleport", resume=True, ordinal=5),
        ]
        summary = RUNNER._event_map_transition_seed_summary(rows)
        self.assertEqual(summary, {
            "map_transition_row_count": 5,
            "map_transition_source_case_count": 5,
            "map_transition_source_case_ids": sorted(
                row["source_case_id"] for row in rows
            ),
            "map_transition_covered_owner_count": 5,
            "map_transition_covered_owner_ids": sorted(
                row["covered_owner_ids"][0] for row in rows
            ),
            "map_transition_seed_counts": {
                "stock_warp": 2, "stock_connection": 1,
                "engine_teleport": 2,
            },
            "map_transition_producer_kind_counts": {
                "STOCK_WARP": 2, "CONNECTION": 1,
                "ENGINE_TELEPORT": 2,
            },
            "map_transition_direct_seed_counts": {
                "stock_warp": 1, "stock_connection": 1,
                "engine_teleport": 1,
            },
            "map_transition_resume_seed_counts": {
                "stock_warp": 1, "stock_connection": 0,
                "engine_teleport": 1,
            },
            "map_transition_counts_source_derived": True,
        })
        physical_owner_ids = summary["map_transition_covered_owner_ids"]
        logical_owner_ids = sorted(row["owner_id"] for row in rows)
        source_case_ids = summary["map_transition_source_case_ids"]
        production_document = {
            **summary, "fixture_count": len(rows), "results": rows,
            "owner_count": len(logical_owner_ids),
            "executed_logical_owner_count": len(logical_owner_ids),
            "executed_logical_owner_ids": logical_owner_ids,
            "source_owner_count": len(physical_owner_ids),
            "executed_owner_count": len(physical_owner_ids),
            "executed_owner_ids": physical_owner_ids,
            "source_case_count": len(source_case_ids),
            "source_case_ids": source_case_ids,
            "executed_source_case_ids": source_case_ids,
        }
        RUNNER._final_mgba_event_production_map_count_anchor(
            production_document,
        )
        owner_bound_drift = deepcopy(production_document)
        owner_bound_drift["map_transition_seed_counts"]["engine_teleport"] = 1
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "source-derived MAP",
        ):
            RUNNER._final_mgba_event_production_map_count_anchor(
                owner_bound_drift,
            )
        count_drift = deepcopy(production_document)
        count_drift["source_owner_count"] -= 1
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "source/runtime owner count",
        ):
            RUNNER._final_mgba_event_production_map_count_anchor(count_drift)
        multiple = deepcopy(rows[0])
        multiple["trigger_evidence"]["map_transition"][
            "real_connection_step"
        ] = True
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "mechanism exact-one",
        ):
            RUNNER._event_map_transition_seed_summary([multiple])

    def test_final_artifact_and_capture_anchors_reject_placeholders(self) -> None:
        raw_hex = "41FF"
        digest = hashlib.sha256(bytes.fromhex(raw_hex)).hexdigest()
        capture = {
            "framebuffer": {
                "changed_frames": 2,
                "maximum_baseline_pixel_difference": 2000,
            },
            "printer_calls": [{
                "raw_hex": raw_hex, "raw_sha256": digest,
                "instruction_address": "0x0806C5D8",
                "caller_instruction_address": "0x08012344",
            }],
            "messages": [{"raw_hex": raw_hex, "raw_sha256": digest}],
        }
        RUNNER._final_mgba_capture_anchor(
            capture, label="unit-capture", require_printer=True,
        )
        artifacts = {
            "artifacts": [
                self._artifact("map_popup", "one-peak.ppm"),
                self._artifact(
                    "map_popup", "two-peak.ppm", sha256="2" * 64,
                    rgb_fnv1a64="FEDCBA9876543210",
                ),
            ],
        }
        RUNNER._final_mgba_artifact_anchor(
            artifacts, case="map_popup", minimum=2,
        )
        artifact_mutations = {
            "none": lambda item: item["artifacts"].__setitem__(0, None),
            "path-only": lambda item: item["artifacts"].__setitem__(
                0, {"path": "one-peak.ppm"},
            ),
            "extra-key": lambda item: item["artifacts"][0].__setitem__(
                "extra", True,
            ),
            "duplicate": lambda item: item["artifacts"][1].__setitem__(
                "path", "one-peak.ppm",
            ),
            "bad-suffix": lambda item: item["artifacts"][0].__setitem__(
                "path", "one-peak.bin",
            ),
            "bad-size": lambda item: item["artifacts"][0].__setitem__(
                "size", 0,
            ),
            "bad-sha": lambda item: item["artifacts"][0].__setitem__(
                "sha256", "A" * 64,
            ),
        }
        for label, mutate in artifact_mutations.items():
            broken = deepcopy(artifacts)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._final_mgba_artifact_anchor(
                    broken, case="map_popup", minimum=2,
                )
        capture_mutations = {
            "printer-none": lambda item: item["printer_calls"].__setitem__(
                0, None,
            ),
            "printer-empty": lambda item: item.__setitem__("printer_calls", []),
            "printer-sha": lambda item: item["printer_calls"][0].__setitem__(
                "raw_sha256", "0" * 64,
            ),
            "message-none": lambda item: item["messages"].__setitem__(0, None),
            "message-sha": lambda item: item["messages"][0].__setitem__(
                "raw_sha256", "0" * 64,
            ),
        }
        for label, mutate in capture_mutations.items():
            broken = deepcopy(capture)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER._final_mgba_capture_anchor(
                    broken, label=label, require_printer=True,
                )

    def test_final_catalog_attempt_and_effect_anchors_fail_closed(self) -> None:
        coverage = {
            key: {} for key in (
                "flags", "engine_special_flags", "vars", "items",
                "trainers", "objects", "object_templates", "party",
                "storage", "persistent",
            )
        }
        side_effects = {
            "complete": True, "coverage": coverage,
            "flags": [], "engine_special_flags": [], "vars": [],
            "items": [], "trainers": [], "economy": {}, "party": {},
            "storage": {}, "persistent": {}, "objects": {}, "world": {},
            "object": {}, "battle": {"after": {"active": False}},
            "input": {
                "recovered": True,
                "after": {
                    "field_input_recovered": True,
                    "battle_input_owned": False,
                },
            },
        }
        capture = {
            "framebuffer": {
                "changed_frames": 1,
                "maximum_baseline_pixel_difference": 2000,
            },
            "printer_calls": [], "messages": [],
        }
        template_raw = self._object_template_raw(
            local_id=8, graphics_id=18, x=10, y=20,
            movement_type=9, script_pointer=0x08100000,
        )
        interactive_identity = self._preinteraction_identity(
            template_raw, template_index=7, interactive=True,
        )
        normal_execution = self._physical_interaction_execution(
            start=[10, 22], walk_sequence=["UP"],
            stance=[10, 21], action="UP",
        )
        attempt = {
            "success": True, "failure_reason": "NONE",
            "input_step_count": 1, "input_steps_consumed": 1,
            "terminal": "FIELD_RELEASE", "battle_started": False,
            "field_released": True, "visible_text_expected": False,
            "root_script_pointer_expected": "0x08100000",
            "root_counter_armed_after_identity": True,
            "root_script_pointer_hits": 1,
            "first_root_script_pointer": "0x08100000",
            "first_root_context": {"map": "3/4", "player": [10, 21]},
            "preinteraction_object_identity": deepcopy(
                interactive_identity
            ),
            "post_battle": {
                "battle_started": False, "trainer_battle": False,
                "completed_via_keys": False,
                "forced_switch_count": 0,
                "forced_switch_cursor_observed": False,
                "forced_switch_usable_slot_selected": False,
                "forced_switch_cursor_initial": [],
                "forced_switch_selected_slots": [],
                "forced_switch_selected_hps": [],
                "route": "NONE", "outcome": 0,
                "won_or_escaped_not_loss": False,
                "field_released_after_battle": False,
                "start_pressed": False, "start_menu_opened": False,
                "back_pressed": False, "map_preserved": False,
                "field_input_recovered": False,
            },
            "field_roundtrip": self._field_roundtrip(),
            "text_oracle_match": {
                "independent_provenance": True,
                "actual_ordered_raw_sha256s": [], "visible_text_count": 0,
                "unclassified_visible_printer_calls": 0,
            },
            "post_effect_contract": {
                "deny_by_default": True, "allowed_families": [],
                "actual_families": [],
                "required_postconditions_satisfied": True,
                "observed": {"flags": []},
            },
            "battle_start_side_effects": None,
            "side_effects": side_effects, "capture": capture,
        }
        rows = [{
            "case_id": "unit-interactive", "map": "3/4",
            "owner_key": "OBJECT:003/004:007",
            "local_id": 8, "runtime_root": "0x08100000",
            "stance": [10, 21], "interaction_distance": 1,
            "interaction_expected": True, "direct_script_call": False,
            "direction_plus_a": True, "actual_walk_required": True,
            "actual_walk_steps": 1,
            "walk_path_basis": (
                "EXACT_STOCK_INCOMING_ARRIVAL_TO_OWNER_STANCE"
            ),
            "approach_observation": self._approach_observation(
                normal_execution
            ),
            "map_level_real_walk_probe_required": False,
            "preinteraction_object_identity": deepcopy(
                interactive_identity
            ),
            "root_probe": {
                "expected": "0x08100000", "armed_after_identity": True,
                "input_attempted": True, "hidden_idle_frames": 0,
                "hidden_hits": 0, "hidden_first": None,
            },
            "input_sequence_attempts": [attempt],
        }, {
            "case_id": "unit-hidden", "map": "3/4",
            "owner_key": "OBJECT:003/004:008",
            "local_id": 8, "runtime_root": "0x08100000",
            "stance": [10, 21], "interaction_distance": 1,
            "interaction_expected": False, "direct_script_call": False,
            "direction_plus_a": False, "actual_walk_required": False,
            "actual_walk_steps": 0,
            "walk_path_basis": (
                "EXACT_STOCK_INCOMING_ARRIVAL_TO_OWNER_STANCE"
            ),
            "approach_observation": None,
            "map_level_real_walk_probe_required": False,
            "preinteraction_object_identity": self._preinteraction_identity(
                template_raw, template_index=8, interactive=False,
            ),
            "root_probe": {
                "expected": "0x08100000", "armed_after_identity": True,
                "input_attempted": False, "hidden_idle_frames": 3,
                "hidden_hits": 0, "hidden_first": "0x00000000",
            },
            "input_sequence_attempts": [],
        }]
        for case_id, owner_key, walk_path_basis, walk_required in (
            (
                "unit-shadow-source-000", "OBJECT:003/022:000",
                "CANONICAL_SHADOW_NON_PRODUCT_SOURCE_DIAGNOSTIC_STANCE",
                False,
            ),
            (
                "unit-shadow-source-003", "OBJECT:003/022:003",
                "CANONICAL_SHADOW_NON_PRODUCT_SOURCE_DIAGNOSTIC_STANCE",
                False,
            ),
            (
                "unit-shadow-canonical-007", "OBJECT:096/015:007",
                "CANONICAL_SHADOW_EXACT_STOCK_INCOMING_ARRIVAL_TO_STANCE",
                True,
            ),
            (
                "unit-shadow-canonical-008", "OBJECT:096/015:008",
                "CANONICAL_SHADOW_EXACT_STOCK_INCOMING_ARRIVAL_TO_STANCE",
                True,
            ),
        ):
            row = deepcopy(rows[0])
            row.update({
                "case_id": case_id,
                "owner_key": owner_key,
                "walk_path_basis": walk_path_basis,
                "actual_walk_required": walk_required,
                "actual_walk_steps": int(walk_required),
            })
            object_index = int(owner_key.rsplit(":", 1)[1])
            row_identity = self._preinteraction_identity(
                template_raw, template_index=object_index,
                interactive=True,
            )
            row["preinteraction_object_identity"] = deepcopy(row_identity)
            for row_attempt in row["input_sequence_attempts"]:
                row_attempt["preinteraction_object_identity"] = deepcopy(
                    row_identity
                )
            execution = deepcopy(normal_execution)
            execution["walk_path_basis"] = walk_path_basis
            if not walk_required:
                execution.update({
                    "start": [10, 21], "walk_sequence": [],
                    "stance": [10, 21],
                })
            row["approach_observation"] = self._approach_observation(
                execution
            )
            rows.append(row)
        none_producer = RUNNER._none_runtime_position_producer(3, 4)
        none_control = RUNNER._none_runtime_position_control()
        for row in rows:
            approach = row.get("approach_observation")
            requested = (
                list(approach["start"])
                if isinstance(approach, dict) else [10, 22]
            )
            row["runtime_position_producer"] = (
                self._runtime_position_observation(
                    none_producer, none_control, requested=requested,
                    visible=row["interaction_expected"],
                )
            )
        document = {
            "schema_version": 9, "status": "PASS", "case": "catalog_batch",
            "baseline_natural_continue": True, "per_case_stock_warp": True,
            "input_sequence_probe_via_state_restore": True,
            "fixture_count": 6, "interactive_count": 5, "hidden_count": 1,
            "input_sequence_attempt_count": 5, "successful_path_count": 5,
            "distinct_path_count": 5, "failed": 0, "untested": 0,
            "warnings": 0, "root_script_failures": 0, "results": rows,
            "link_session_attempt_count": 0,
            "rfu_session_attempt_count": 0,
            "rfu_session_failure_count": 0,
            "rfu_host_memory_write_count": 0,
            "center_link_session_attempt_count": 0,
            "center_link_session_failure_count": 0,
            "center_link_host_memory_write_count": 0,
            "rfu_session_sweep": RUNNER._validate_rfu_catalog_exact_set(
                [], [], label="final-catalog-unit",
            ),
            "center_link_session_sweep": (
                RUNNER._validate_center_link_catalog_exact_set(
                    [], [], label="final-catalog-unit",
                )
            ),
            "physical_interaction_geometry": {
                "distance_one_count": 6,
                "counter_distance_two_count": 0,
                "actual_walk_owner_count": 3,
                "direct_script_call_count": 0, "isolated_owner_count": 0,
                "isolated_maps_with_real_walk_evidence": [],
                "canonical_shadow_non_product_source_count": 2,
                "canonical_shadow_non_product_source_ids": [
                    "OBJECT:003/022:000", "OBJECT:003/022:003",
                ],
                "canonical_shadow_physical_owner_count": 2,
                "canonical_shadow_physical_owner_ids": [
                    "OBJECT:096/015:007", "OBJECT:096/015:008",
                ],
            },
            "artifacts": [
                self._artifact(
                    "catalog_batch", f"unit-{index}-visibility.ppm",
                    sha256=f"{index + 1:x}" * 64,
                    rgb_fnv1a64=f"{index + 1:016X}",
                )
                for index in range(11)
            ],
        }
        RUNNER.validate_final_mgba_case_result("catalog_batch", document)
        mutations = {
            "empty-attempts": lambda item: item["results"][0].__setitem__(
                "input_sequence_attempts", [],
            ),
            "text-empty": lambda item: item["results"][0][
                "input_sequence_attempts"
            ][0].__setitem__("text_oracle_match", {}),
            "effect-empty": lambda item: item["results"][0][
                "input_sequence_attempts"
            ][0].__setitem__("post_effect_contract", {}),
            "side-empty": lambda item: item["results"][0][
                "input_sequence_attempts"
            ][0].__setitem__("side_effects", {}),
            "root-hit-zero": lambda item: item["results"][0][
                "input_sequence_attempts"
            ][0].__setitem__("root_script_pointer_hits", 0),
            "interaction-bool-type": lambda item: item["results"][0].__setitem__(
                "interaction_expected", 1,
            ),
            "template-position-type": lambda item: item["results"][0][
                "preinteraction_object_identity"
            ].__setitem__("template_position", [10, "20"]),
            "template-root-drift": lambda item: item["results"][0][
                "preinteraction_object_identity"
            ].__setitem__("template_script", "0x08100002"),
            "template-raw-drift": lambda item: item["results"][0][
                "preinteraction_object_identity"
            ].__setitem__("observed_raw_hex", "00" + template_raw[2:]),
            "approach-transient": lambda item: item["results"][0][
                "approach_observation"
            ]["transient_execution"].__setitem__("printer_call_count", 1),
            "movement-owned-transition": lambda item: item["results"][0][
                "approach_observation"
            ]["persistent_state"]["movement_owned_state"][
                "daycare_step_counter"
            ].__setitem__("transition", "ADD_CAP_256"),
            "field-roundtrip": lambda item: item["results"][0][
                "input_sequence_attempts"
            ][0]["field_roundtrip"].__setitem__("back_pressed", False),
            "hidden-active": lambda item: item["results"][1][
                "preinteraction_object_identity"
            ].update({
                "live_active": True, "live_visible": True,
                "live_current": [17, 27],
            }),
            "hidden-root-hit": lambda item: item["results"][1][
                "root_probe"
            ].update({
                "hidden_hits": 1, "hidden_first": "0x08100000",
            }),
            "aggregate-drift": lambda item: item.__setitem__(
                "successful_path_count", 0,
            ),
            "partition-drift": lambda item: item.__setitem__(
                "hidden_count", 0,
            ),
            "canonical-shadow-source-missing": lambda item: item[
                "physical_interaction_geometry"
            ]["canonical_shadow_non_product_source_ids"].pop(),
            "runtime-position-api-count-one": lambda item: item["results"][0][
                "runtime_position_producer"
            ]["local_player_positioning"].__setitem__(
                "host_coordinate_reposition_calls", 1,
            ),
        }
        for label, mutate in mutations.items():
            broken = deepcopy(document)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError
            ):
                RUNNER.validate_final_mgba_case_result(
                    "catalog_batch", broken,
                )

    def test_compile_only_is_warning_clean_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.json"
            second = Path(temporary) / "second.json"
            documents = []
            for output in (first, second):
                completed = subprocess.run(
                    [sys.executable, str(RUNNER_PATH), "--compile-only",
                     "--fixtures", str(Path(temporary) / "embedded.json"),
                     "--output", str(output)],
                    cwd=ROOT, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, timeout=120, check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(completed.stderr, "")
                stdout = json.loads(completed.stdout)
                written = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(stdout, written)
                self.assertEqual(stdout["status"], "PASS")
                self.assertEqual(stdout["compile"]["status"], "PASS")
                documents.append(stdout)
            self.assertEqual(documents[0], documents[1])

    def test_framebuffer_registry_exact_join_rejects_gradient_and_role_swap(
        self,
    ) -> None:
        header_size = len(b"P6\n240 160\n255\n")
        first = self._ppm(11)
        replacement = self._ppm(12)
        self.assertEqual(len(first), len(replacement))
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            path = work / "unit-peak.ppm"
            path.write_bytes(first)
            document = {
                "schema_version": 1, "status": "PASS", "case": "map_popup",
                "framebuffer_artifacts": [{
                    "path": path.name,
                    "rgb_fnv1a64": RUNNER._fnv1a64(first[header_size:]),
                    "framebuffer_role": "INTERACTION_PEAK_FRAME",
                }],
            }
            self.assertEqual(
                RUNNER._validate_c_framebuffer_artifact_join(
                    document, case="map_popup", directory=work,
                ),
                document["framebuffer_artifacts"],
            )
            path.write_bytes(replacement)
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "RGB FNV",
            ):
                RUNNER._validate_c_framebuffer_artifact_join(
                    document, case="map_popup", directory=work,
                )
            path.write_bytes(first)
            (work / "unreported-peak.ppm").write_bytes(replacement)
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "path exact join",
            ):
                RUNNER._validate_c_framebuffer_artifact_join(
                    document, case="map_popup", directory=work,
                )

        fly = {
            "framebuffer_artifacts": [{
                "path": "fly_normal_menu-town-map.ppm",
                "rgb_fnv1a64": "1" * 16,
                "framebuffer_role": "FLY_TOWN_MAP_FRAME",
            }, {
                "path": "fly_normal_menu-final.ppm",
                "rgb_fnv1a64": "2" * 16,
                "framebuffer_role": "FLY_DESTINATION_FRAME",
            }],
        }
        RUNNER._split_c_framebuffer_artifacts(fly, case="fly_normal_menu")
        swapped = deepcopy(fly)
        swapped["framebuffer_artifacts"][0]["framebuffer_role"], \
            swapped["framebuffer_artifacts"][1]["framebuffer_role"] = (
                swapped["framebuffer_artifacts"][1]["framebuffer_role"],
                swapped["framebuffer_artifacts"][0]["framebuffer_role"],
            )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "identity",
        ):
            RUNNER._split_c_framebuffer_artifacts(
                swapped, case="fly_normal_menu",
            )
        self.assertEqual(
            RUNNER._framebuffer_role(
                "msc17_quest_log_transitions", "x-two-hop-final.ppm",
            ),
            "QUEST_LOG_TWO_HOP_FRAME",
        )
        self.assertEqual(
            RUNNER._framebuffer_role(
                "msc17_quest_log_transitions", "x-rearm-final.ppm",
            ),
            "QUEST_LOG_REARM_FRAME",
        )

    def test_calibration_enrichment_strips_only_exact_joined_registry(
        self,
    ) -> None:
        artifact = self._artifact(
            "catalog_calibrate", "cal-001-visibility.ppm",
        )
        registry = [{
            key: artifact[key] for key in (
                "path", "rgb_fnv1a64", "framebuffer_role",
            )
        }]
        document = {
            "payload": True, "artifacts": [artifact],
            "framebuffer_artifacts": registry,
        }
        self.assertEqual(
            RUNNER._without_calibration_enrichment(document),
            {"payload": True},
        )
        for label, mutate in {
            "missing-c-registry": lambda item: item.pop(
                "framebuffer_artifacts"
            ),
            "fnv-drift": lambda item: item["framebuffer_artifacts"][0].update(
                {"rgb_fnv1a64": "F" * 16}
            ),
            "role-drift": lambda item: item["framebuffer_artifacts"][0].update(
                {"framebuffer_role": "DIALOGUE_MESSAGE_FRAME"}
            ),
        }.items():
            broken = deepcopy(document)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._without_calibration_enrichment(broken)

    def test_multiphase_retention_projection_is_explicit_and_exact(self) -> None:
        def raw(value: object) -> bytes:
            return (
                json.dumps(value, sort_keys=True, separators=(",", ":"))
                + "\n"
            ).encode("utf-8")

        corruption_c = {
            "schema_version": 2, "status": "PASS",
            "case": "save_corruption_probe", "fixture_id": "fault",
            "framebuffer_artifacts": [],
        }
        corruption_final = {
            **corruption_c,
            "input_image_sha256": "1" * 64,
            "output_image_sha256": "2" * 64,
            "flash_changed_offsets": [1, 4096],
            "expected_owner_image_sha256": None,
        }
        self.assertEqual(
            RUNNER._retention_join_stdout(
                case_id="save_corruption_matrix",
                phase="fault/save_corruption_probe", raw=raw(corruption_c),
                expected=corruption_final, sharded=False,
            ),
            corruption_c,
        )
        missing = deepcopy(corruption_final)
        missing.pop("input_image_sha256")
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "corruption enrichment",
        ):
            RUNNER._retention_join_stdout(
                case_id="save_corruption_matrix",
                phase="fault/save_corruption_probe", raw=raw(corruption_c),
                expected=missing, sharded=False,
            )
        extra_c = {**corruption_c, "forged": True}
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "normalized result",
        ):
            RUNNER._retention_join_stdout(
                case_id="save_corruption_matrix",
                phase="fault/save_corruption_probe", raw=raw(extra_c),
                expected=corruption_final, sharded=False,
            )

        predicates = {
            "warning_or_error": True, "unknown_pc": False,
            "controls_locked": False, "map_load_failed": False,
            "stock_warp_failed": False, "actual_walk_failed": False,
            "direction_plus_a_failed": False,
            "interaction_terminal_failed": False,
        }
        stage60_c = {
            "schema_version": 1, "status": "PASS",
            "case": "product_map_scripts_stage60_baseline",
            "results": [{"case_id": "stage60-a"}],
            "framebuffer_artifacts": [],
        }
        stage60_final = deepcopy(stage60_c)
        stage60_final.update({
            "all_live_invalid_tags_exact": True,
            "all_negative_failure_symptoms_observed": True,
        })
        stage60_final["results"][0].update({
            "stage60_failure_predicates": predicates,
            "stage60_failure_observed": True,
        })
        RUNNER._retention_join_stdout(
            case_id="product_map_script_regressions",
            phase="stage60/product_map_scripts_stage60_baseline",
            raw=raw(stage60_c), expected=stage60_final, sharded=False,
        )
        bad_predicates = deepcopy(stage60_final)
        bad_predicates["results"][0]["stage60_failure_predicates"].pop(
            "unknown_pc"
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "Stage60 derived row",
        ):
            RUNNER._retention_join_stdout(
                case_id="product_map_script_regressions",
                phase="stage60/product_map_scripts_stage60_baseline",
                raw=raw(stage60_c), expected=bad_predicates, sharded=False,
            )

        raw_hex = "41FF"
        decoded = RUNNER.decode_text(
            bytes.fromhex(raw_hex), RUNNER._read_charmap(),
        )
        gym_c = {
            "schema_version": 2, "status": "PASS",
            "case": "product_gym_bg_stage61", "branch_count": 1,
            "capture": {"raw_hex": raw_hex},
            "framebuffer_artifacts": [],
        }
        gym_final = deepcopy(gym_c)
        gym_final["capture"].update({
            "raw_sha256": hashlib.sha256(bytes.fromhex(raw_hex)).hexdigest(),
            "utf8": decoded,
            "text_oracle_match": {"independent_provenance": True},
        })
        RUNNER._retention_join_stdout(
            case_id="product_map_script_regressions",
            phase="gym/product_gym_bg_stage61", raw=raw(gym_c),
            expected=gym_final, sharded=False,
        )
        no_oracle = deepcopy(gym_final)
        no_oracle["capture"].pop("text_oracle_match")
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "text oracle enrichment",
        ):
            RUNNER._retention_join_stdout(
                case_id="product_map_script_regressions",
                phase="gym/product_gym_bg_stage61", raw=raw(gym_c),
                expected=no_oracle, sharded=False,
            )

    def test_sharded_retention_projection_strips_only_verified_derivatives(
        self,
    ) -> None:
        raw_stdout = self._calibration_document()
        raw_stdout["framebuffer_artifacts"] = []
        encoded_stdout = (
            json.dumps(raw_stdout, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        RUNNER._retention_join_stdout(
            case_id="catalog_calibrate", phase="catalog_calibrate",
            raw=encoded_stdout, expected=raw_stdout, sharded=True,
        )
        forged_root = deepcopy(raw_stdout)
        forged_root["ignored_integer"] = 1
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "root schema",
        ):
            RUNNER._retention_join_stdout(
                case_id="catalog_calibrate", phase="catalog_calibrate",
                raw=(
                    json.dumps(
                        forged_root, sort_keys=True, separators=(",", ":"),
                    ) + "\n"
                ).encode("utf-8"),
                expected=raw_stdout, sharded=True,
            )

        raw = bytes.fromhex("41FF")
        decoded = RUNNER.decode_text(raw, RUNNER._read_charmap())

        def shard(case_id: str, index: int) -> dict[str, object]:
            capture = {
                "messages": [{"raw_hex": raw.hex().upper()}],
                "printer_calls": [{"raw_hex": raw.hex().upper()}],
            }
            return {
                "schema_version": 2, "status": "PASS",
                "case": "catalog_calibrate",
                "baseline_natural_continue": True,
                "choice_probe_via_state_restore": True,
                "pulse_limit": 48, "failed": 0, "untested": 0,
                "warnings": 0, "fixture_count": 1, "resolved": 1,
                "unresolved": 0,
                "results": [{
                    "case_id": case_id,
                    "successful_paths": [{"capture": capture}],
                }],
                "artifacts": [{"path": f"cal-{index}-visibility.ppm"}],
                "framebuffer_artifacts": [{
                    "path": f"cal-{index}-visibility.ppm",
                    "rgb_fnv1a64": f"{index:016X}",
                    "framebuffer_role": "OWNER_VISIBILITY_FRAME",
                }],
            }

        documents = [shard("cal-001", 1), shard("cal-002", 2)]
        expected = RUNNER._merge_calibration_shards(deepcopy(documents))
        for row in expected["results"]:
            capture = row["successful_paths"][0]["capture"]
            capture["printer_capture_primary"] = True
            capture["gstringvar4_supplementary"] = True
            for message in [
                *capture["messages"], *capture["printer_calls"],
            ]:
                message["raw_sha256"] = hashlib.sha256(raw).hexdigest()
                message["utf8"] = decoded

        RUNNER._retention_join_shards(
            "catalog_calibrate", documents, expected,
        )
        bad_sha = deepcopy(expected)
        bad_sha["results"][0]["successful_paths"][0]["capture"][
            "messages"
        ][0]["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "capture SHA",
        ):
            RUNNER._retention_join_shards(
                "catalog_calibrate", documents, bad_sha,
            )
        unknown = deepcopy(expected)
        unknown["results"][0]["successful_paths"][0][
            "forged_python_derivative"
        ] = True
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "union/disjoint closure",
        ):
            RUNNER._retention_join_shards(
                "catalog_calibrate", documents, unknown,
            )

    def test_all_domain_persistence_vectors_and_final_payloads_are_exact(
        self,
    ) -> None:
        required = list(RUNNER._ALL_DOMAIN_STATE_PERSISTENCE_CASE_IDS)
        modes = list(RUNNER._ALL_DOMAIN_STATE_PERSISTENCE_MODES)
        fixtures = {
            case_id: {
                "state": {
                    "flags": [{"id": 0x18B4, "value": True}],
                    "vars": [{"id": 0x5170, "value": index}],
                },
            }
            for index, case_id in enumerate(required, start=1)
        }
        RUNNER._validate_all_domain_state_persistence_inputs(
            selected=modes, requested_case_ids=required, fixtures=fixtures,
        )
        for label, mutate in {
            "order": lambda requested, values: requested.reverse(),
            "flag": lambda requested, values: values[required[0]]["state"][
                "flags"
            ].append({"id": 0x18B5, "value": True}),
            "var": lambda requested, values: values[required[1]]["state"][
                "vars"
            ][0].update({"value": 3}),
        }.items():
            requested = list(required)
            broken = deepcopy(fixtures)
            mutate(requested, broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._validate_all_domain_state_persistence_inputs(
                    selected=modes, requested_case_ids=requested,
                    fixtures=broken,
                )

        report = {
            "state_persistence": {
                "selected_case_count": 3, "case_ids": required,
                "modes": modes,
            },
            "results": {
                mode: {"result": {
                    "case": mode, "fixture_count": 3,
                    "results": [{"case_id": case_id} for case_id in required],
                }}
                for mode in modes
            },
        }
        RUNNER._validate_all_domain_state_persistence_output(report)
        for label, mutate in {
            "summary-count": lambda item: item["state_persistence"].update(
                {"selected_case_count": 2}
            ),
            "summary-order": lambda item: item["state_persistence"][
                "case_ids"
            ].reverse(),
            "mode-missing": lambda item: item["results"].pop(modes[0]),
            "payload-duplicate": lambda item: item["results"][modes[1]][
                "result"
            ]["results"].__setitem__(
                2, {"case_id": required[1]},
            ),
        }.items():
            broken = deepcopy(report)
            mutate(broken)
            with self.subTest(label=label), self.assertRaises(
                RUNNER.Stage61MgbaError,
            ):
                RUNNER._validate_all_domain_state_persistence_output(broken)

    def test_artifact_retention_manifest_roles_and_negative_closure(
        self,
    ) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)

        def wrapper(
            case_id: str, result: dict[str, object], *, runs: int, shards: int,
        ) -> dict[str, object]:
            result_sha = hashlib.sha256(
                RUNNER._stable(result).encode("utf-8")
            ).hexdigest()
            shard_hashes = [
                hashlib.sha256(
                    f"{case_id}:raw-shard:{index}".encode("ascii")
                ).hexdigest()
                for index in range(1, shards + 1)
            ]
            return {
                "status": "PASS", "process_runs": runs,
                "process_shards": shards,
                "same_shard_boundaries_across_runs": True,
                "per_shard_identical_results": True,
                "per_shard_result_sha256": shard_hashes,
                "per_run_merged_result_sha256": [result_sha] * runs,
                "per_run_per_shard_result_sha256": [
                    list(shard_hashes) for _ in range(runs)
                ],
                "identical_results": True, "result": result,
            }

        def source_tree(
            base: Path, case_id: str, *, runs: int, shards: int,
            phases: tuple[str, ...], ppm_by_shard: dict[int, list[tuple[str, bytes]]],
            srm_by_path: dict[str, bytes] | None = None,
            stdout_by_phase: dict[str, dict[str, object]] | None = None,
        ) -> Path:
            temp = base / "source"
            for run_index in range(1, runs + 1):
                for shard_index in range(1, shards + 1):
                    work = temp / (
                        f"{case_id}-run-{run_index}-shard-{shard_index}"
                    )
                    work.mkdir(parents=True)
                    for phase in phases:
                        phase_path = Path(phase)
                        stream_dir = work / phase_path.parent
                        stream_dir.mkdir(parents=True, exist_ok=True)
                        stem = phase_path.name
                        (stream_dir / f"observer-{stem}-stdout.json").write_text(
                            json.dumps(
                                (stdout_by_phase or {})[phase],
                                ensure_ascii=False, sort_keys=True,
                                separators=(",", ":"),
                            ) + "\n", encoding="utf-8",
                        )
                        (stream_dir / f"observer-{stem}-stderr.log").write_bytes(
                            b""
                        )
                    for relative, raw in ppm_by_shard[shard_index]:
                        target = work / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(raw)
                    for relative, raw in (srm_by_path or {}).items():
                        target = work / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(raw)
            return temp

        with tempfile.TemporaryDirectory(dir=local) as temporary:
            base = Path(temporary)
            case_id = "map_popup"
            raw = self._ppm(1)
            relative = "capture-peak.ppm"
            rgb_fnv1a64 = RUNNER._fnv1a64(raw[15:])
            c_result = {
                "schema_version": 1, "status": "PASS", "case": case_id,
                "framebuffer_artifacts": [{
                    "path": relative, "rgb_fnv1a64": rgb_fnv1a64,
                    "framebuffer_role": "INTERACTION_PEAK_FRAME",
                }],
            }
            result = {
                **c_result,
                "artifacts": [self._artifact(
                    case_id, relative,
                    sha256=hashlib.sha256(raw).hexdigest(),
                    rgb_fnv1a64=rgb_fnv1a64,
                )],
            }
            temp = source_tree(
                base, case_id, runs=2, shards=1, phases=(case_id,),
                ppm_by_shard={1: [(relative, raw)]},
                stdout_by_phase={case_id: c_result},
            )
            rom = base / "stage61.gba"
            rom.write_bytes(b"stage61-rom")
            digest = hashlib.sha256(rom.read_bytes()).hexdigest()
            results = {case_id: wrapper(case_id, result, runs=2, shards=1)}
            retained = base / "retained"
            retention = RUNNER._build_artifact_retention(
                retained, temp=temp, rom_path=rom, rom_sha256=digest,
                results=results, report_path=base / "report.json",
                effects=False,
            )
            self.assertEqual(retention["schema_version"], 3)
            self.assertEqual(
                retention["kind"], "STAGE61_MGBA_ARTIFACT_RETENTION_V3",
            )
            manifest = json.loads(
                (retained / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["schema_version"], 3)
            self.assertEqual(
                manifest["kind"],
                "STAGE61_MGBA_RETAINED_ARTIFACT_MANIFEST_V3",
            )
            RUNNER._validate_artifact_retention(
                retention, workspace_root=ROOT,
                report_path=base / "report.json", rom_sha256=digest,
                results=results, effects=False,
            )
            retired_retention = deepcopy(retention)
            retired_retention.update({
                "schema_version": 2,
                "kind": "STAGE61_MGBA_ARTIFACT_RETENTION_V2",
            })
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "retention report schema",
            ):
                RUNNER._validate_artifact_retention(
                    retired_retention, workspace_root=ROOT,
                    report_path=base / "report.json", rom_sha256=digest,
                    results=results, effects=False,
                )
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "root既存非空|再利用",
            ):
                RUNNER._build_artifact_retention(
                    retained, temp=temp, rom_path=rom, rom_sha256=digest,
                    results=results, report_path=base / "report.json",
                    effects=False,
                )
            rogue = retained / "rogue.bin"
            rogue.write_bytes(b"unmanifested")
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "manifest外leaf",
            ):
                RUNNER._validate_artifact_retention(
                    retention, workspace_root=ROOT,
                    report_path=base / "report.json", rom_sha256=digest,
                    results=results, effects=False,
                )
            rogue.unlink()
            result_entry = next(
                row for row in manifest["entries"]
                if row["role"] == "CASE_RESULT_JSON"
            )
            result_leaf = retained / result_entry["relative_path"]
            result_leaf.write_bytes(b"forged")
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "leaf size/SHA",
            ):
                RUNNER._validate_artifact_retention(
                    retention, workspace_root=ROOT,
                    report_path=base / "report.json", rom_sha256=digest,
                    results=results, effects=False,
                )

        with tempfile.TemporaryDirectory(dir=local) as temporary:
            base = Path(temporary)
            case_id = "map_popup"
            raw = self._ppm(2)
            relative = "missing-stream-peak.ppm"
            rgb_fnv1a64 = RUNNER._fnv1a64(raw[15:])
            c_result = {
                "schema_version": 1, "status": "PASS", "case": case_id,
                "framebuffer_artifacts": [{
                    "path": relative, "rgb_fnv1a64": rgb_fnv1a64,
                    "framebuffer_role": "INTERACTION_PEAK_FRAME",
                }],
            }
            temp = source_tree(
                base, case_id, runs=1, shards=1, phases=(case_id,),
                ppm_by_shard={1: [(relative, raw)]},
                stdout_by_phase={case_id: c_result},
            )
            next(temp.rglob("observer-map_popup-stdout.json")).unlink()
            rom = base / "stage61.gba"
            rom.write_bytes(b"stage61-rom")
            result = {
                **c_result,
                "artifacts": [self._artifact(
                    case_id, relative,
                    sha256=hashlib.sha256(raw).hexdigest(),
                    rgb_fnv1a64=rgb_fnv1a64,
                )],
            }
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "required role|process stream partition",
            ):
                RUNNER._build_artifact_retention(
                    base / "retained", temp=temp, rom_path=rom,
                    rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
                    results={case_id: wrapper(
                        case_id, result, runs=1, shards=1,
                    )}, report_path=base / "report.json", effects=False,
                )

        with tempfile.TemporaryDirectory(dir=local) as temporary:
            base = Path(temporary)
            case_id = "last_ball_persistence"
            writer_raw = self._ppm(3)
            reader_raw = self._ppm(4)
            writer_path = "last-ball-writer.ppm"
            reader_path = "last-ball-reader.ppm"
            writer_fnv = RUNNER._fnv1a64(writer_raw[15:])
            reader_fnv = RUNNER._fnv1a64(reader_raw[15:])
            writer = {
                "schema_version": 1, "status": "PASS",
                "case": case_id, "phase": "WRITE",
                "framebuffer_artifacts": [{
                    "path": writer_path, "rgb_fnv1a64": writer_fnv,
                    "framebuffer_role": "PERSISTENCE_WRITER_FRAME",
                }],
            }
            reader = {
                "schema_version": 1, "status": "PASS",
                "case": case_id, "phase": "READ",
                "framebuffer_artifacts": [{
                    "path": reader_path, "rgb_fnv1a64": reader_fnv,
                    "framebuffer_role": "PERSISTENCE_READER_FRAME",
                }],
            }
            phases = ("last_ball_persist_write", "last_ball_persist_read")
            srm_paths = {
                name: b"\x61" * 0x20000 for name in (
                    "retention-writer-before.srm",
                    "retention-writer-after.srm",
                    "retention-reader-before.srm",
                    "retention-reader-after.srm",
                )
            }
            temp = source_tree(
                base, case_id, runs=1, shards=1, phases=phases,
                ppm_by_shard={1: [
                    (writer_path, writer_raw), (reader_path, reader_raw),
                ]},
                srm_by_path=srm_paths,
                stdout_by_phase={
                    "last_ball_persist_write": writer,
                    "last_ball_persist_read": reader,
                },
            )
            bad = next(temp.rglob("retention-reader-after.srm"))
            bad.write_bytes(b"short")
            rom = base / "stage61.gba"
            rom.write_bytes(b"stage61-rom")
            result = {
                "status": "PASS", "case": case_id,
                "writer": writer, "reader": reader,
                "artifacts": [
                    self._artifact(
                        case_id, writer_path,
                        sha256=hashlib.sha256(writer_raw).hexdigest(),
                        rgb_fnv1a64=writer_fnv,
                    ),
                    self._artifact(
                        case_id, reader_path,
                        sha256=hashlib.sha256(reader_raw).hexdigest(),
                        rgb_fnv1a64=reader_fnv,
                    ),
                ],
            }
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "SRM size",
            ):
                RUNNER._build_artifact_retention(
                    base / "retained", temp=temp, rom_path=rom,
                    rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
                    results={case_id: wrapper(
                        case_id, result, runs=1, shards=1,
                    )}, report_path=base / "report.json", effects=False,
                )

        save_result = {
            "status": "PASS", "case": "save_corruption_matrix",
            "results": [{"fixture_id": "fault-a"},
                        {"fixture_id": "fault-b"}],
            "artifacts": [{
                "path": "baseline.ppm", "size": 1,
                "sha256": hashlib.sha256(b"x").hexdigest(),
            }],
        }
        self.assertEqual(
            len(RUNNER._retention_expected_persistence_identities(
                "save_corruption_matrix", save_result,
            )),
            6,
        )

    def test_effect_observer_case_scoped_raw_closure_rejects_swap_and_order(self) -> None:
        watch_entry = "effect-watch-" + "0" * 64
        watch_a = "effect-watch-" + "a" * 64
        watch_b = "effect-watch-" + "b" * 64
        runtime = {
            "effect_templates": [{
                "template_id": "template-a",
                "abi_binding": {
                    "dispatch_kind": "SPECIAL", "entry_pc": "0x08000000",
                },
            }],
            "effect_signatures": [{
                "signature_id": "signature-a",
                "ordered_abi_dispatches": [{
                    "group_key": "group-a", "execution_trace_index": 0,
                    "instruction_address": "0x08100000",
                    "entry_pc": "0x08000000",
                }],
                "ordered_effects": [],
            }],
            "effect_instances": [{
                "instance_id": "instance-a", "case_id": "case-a",
                "template_id": "template-a", "signature_id": "signature-a",
                "group_key": "group-a",
                "expected_contract": {
                    "proof_mode": "STATE_RANGE_EXACT",
                    "observer_contract": {
                        "completion_boundary": "SYNC_RETURN",
                        "transitions": [{"watch_id": watch_a,
                                         "kind": "EXACT_FINAL",
                                         "expected_hex": "01"}],
                    },
                },
            }, {
                "instance_id": "instance-c", "case_id": "case-c",
                "expected_contract": {
                    "proof_mode": "STATE_RANGE_EXACT",
                    "observer_contract": {
                        "completion_boundary": "SYNC_RETURN",
                        "transitions": [{"watch_id": watch_b,
                                         "kind": "UNCHANGED"}],
                    },
                },
            }],
            "effect_instance_watch_bindings": [{
                "instance_id": "instance-a",
                "watch_ids": sorted([watch_entry, watch_a]),
            }, {
                "instance_id": "instance-c", "watch_ids": [watch_b],
            }],
            "no_dispatch_watch_bindings": [{
                "case_id": "case-b", "contract_sha256": "c" * 64,
                "watch_ids": [watch_b],
            }],
        }
        plan = {"watches": [
            {"watch_id": watch_entry, "length": 0,
             "hook_pc": "0x08000000", "completion_boundary": "SYNC_RETURN",
             "address_resolver": {"kind": "NONE"}, "arg_capture": []},
            {"watch_id": watch_a, "length": 1,
             "hook_pc": None, "completion_boundary": "SYNC_RETURN",
             "address_resolver": {"kind": "ABSOLUTE"}},
            {"watch_id": watch_b, "length": 0,
             "hook_pc": None, "completion_boundary": "SYNC_RETURN",
             "address_resolver": {"kind": "ABSOLUTE"}},
        ]}
        hook = {
            "kind": "HOOK", "case_id": "case-a", "watch_id": watch_entry,
            "ordinal": 1, **{
                key: "0x08000000" for key in ("pc", "lr", "r0", "r1", "r2", "r3", "raw_pc")
            },
            "capture_phase": "ENTRY", "captures": [],
        }
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            effect_dir = work / "effects" / "case-a"
            effect_dir.mkdir(parents=True)
            before_path = effect_dir / "effect-a-before.bin"
            after_path = effect_dir / "effect-a-after.bin"
            before_path.write_bytes(b"\x00")
            after_path.write_bytes(b"\x01")
            effect_dir_b = work / "effects" / "case-b"
            effect_dir_b.mkdir(parents=True)
            (effect_dir_b / "effect-a-before.bin").write_bytes(b"\x00")
            (effect_dir_b / "effect-a-after.bin").write_bytes(b"\x00")
            def capture(before: bytes, after: bytes, *, path: str) -> dict[str, object]:
                before_name = f"effects/{path}/effect-a-before.bin"
                after_name = f"effects/{path}/effect-a-after.bin"
                return {
                    "before_fnv1a64": "0" * 16 if before == after else "1" * 16,
                    "after_fnv1a64": "0" * 16 if before == after else "2" * 16,
                    "length": len(before),
                    "before": {"path": before_name if before else "", "sha256": hashlib.sha256(before).hexdigest() if before else "", "address": "0x02000000" if before else "0x00000000"},
                    "after": {"path": after_name if after else "", "sha256": hashlib.sha256(after).hexdigest() if after else "", "address": "0x02000000" if after else "0x00000000"},
                    "transition": {"path": after_name, "sha256": hashlib.sha256(after).hexdigest()} if before != after else None,
                    "completion": {"boundary": "SYNC_RETURN", "ordinal": 1},
                }
            raw_a = {watch_entry: capture(b"", b"", path="case-a"),
                     watch_a: capture(b"\x00", b"\x01", path="case-a"),
                     watch_b: capture(b"", b"", path="case-a")}
            raw_b = {watch_entry: capture(b"", b"", path="case-b"),
                     watch_a: capture(b"\x00", b"\x00", path="case-b"),
                     watch_b: capture(b"", b"", path="case-b")}
            for capture_row in raw_b.values():
                capture_row["completion"]["ordinal"] = 0
            boundaries = [
                {"kind": "CASE_END", "case_id": "case-a", "watch_ids": sorted([watch_entry, watch_a, watch_b]), "raw": raw_a, "hook_hits": {watch_entry: 1, watch_a: 0, watch_b: 0}},
                {"kind": "CASE_END", "case_id": "case-b", "watch_ids": sorted([watch_entry, watch_a, watch_b]), "raw": raw_b, "hook_hits": {watch_entry: 0, watch_a: 0, watch_b: 0}},
            ]
            (work / "effect-observer.jsonl").write_text(
                "\n".join(json.dumps(row) for row in (
                    [{"kind": "META", "watch_count": 3}, hook, *boundaries]
                )) + "\n", encoding="utf-8",
            )
            result = RUNNER._validate_effect_observer_output(
                work, case="catalog_batch", runtime=runtime, plan=plan,
                expected_case_ids=["case-a", "case-b"],
            )
            self.assertEqual(result["case_count"], 2)
            # A shard observes only its virtual executions; instances owned
            # by other source rows remain in the global runtime registry.
            (work / "effect-observer.jsonl").write_text(
                "\n".join(json.dumps(row) for row in (
                    [{"kind": "META", "watch_count": 3}, hook, boundaries[0]]
                )) + "\n", encoding="utf-8",
            )
            shard = RUNNER._validate_effect_observer_output(
                work, case="catalog_batch", runtime=runtime, plan=plan,
                expected_case_ids=["case-a"],
            )
            self.assertEqual(shard["case_count"], 1)
            (work / "effect-observer.jsonl").write_text(
                "\n".join(json.dumps(row) for row in (
                    [{"kind": "META", "watch_count": 3}, hook, *boundaries]
                )) + "\n", encoding="utf-8",
            )
            # The JSONL digest is not trusted: the leaf is independently
            # reopened, so a post-observation byte mutation is fatal.
            after_path.write_bytes(b"\x02")
            with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "SHA/path"):
                RUNNER._validate_effect_observer_output(
                    work, case="catalog_batch", runtime=runtime, plan=plan,
                    expected_case_ids=["case-a", "case-b"],
                )
            after_path.write_bytes(b"\x01")
            reused = deepcopy(runtime)
            reused["effect_instances"].append({
                "instance_id": "instance-reused", "case_id": "case-a",
                "template_id": "template-a", "signature_id": "signature-a",
                "group_key": "group-a",
                "expected_contract": deepcopy(
                    runtime["effect_instances"][0]["expected_contract"]
                ),
            })
            reused["effect_instance_watch_bindings"].append({
                "instance_id": "instance-reused",
                "watch_ids": sorted([watch_entry, watch_a]),
            })
            reused["effect_signatures"][0]["ordered_effects"] = [{
                "group_key": "group-a", "execution_trace_index": 0,
            }, {
                "group_key": "group-a", "execution_trace_index": 0,
            }]
            with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "reuse"):
                RUNNER._validate_effect_observer_output(
                    work, case="catalog_batch", runtime=reused, plan=plan,
                    expected_case_ids=["case-a", "case-b"],
                )
            swapped = deepcopy(boundaries)
            swapped[1]["case_id"] = "case-c"
            (work / "effect-observer.jsonl").write_text(
                "\n".join(json.dumps(row) for row in (
                    [{"kind": "META", "watch_count": 3}, hook, *swapped]
                )) + "\n", encoding="utf-8",
            )
            with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "closure"):
                RUNNER._validate_effect_observer_output(
                    work, case="catalog_batch", runtime=runtime, plan=plan,
                    expected_case_ids=["case-a", "case-b"],
                )
            unordered = deepcopy(boundaries)
            bad_hook = deepcopy(hook)
            bad_hook["ordinal"] = 2
            (work / "effect-observer.jsonl").write_text(
                "\n".join(json.dumps(row) for row in (
                    [{"kind": "META", "watch_count": 3}, bad_hook, *unordered]
                )) + "\n", encoding="utf-8",
            )
            with self.assertRaisesRegex(RUNNER.Stage61MgbaError, "execution順序"):
                RUNNER._validate_effect_observer_output(
                    work, case="catalog_batch", runtime=runtime, plan=plan,
                    expected_case_ids=["case-a", "case-b"],
                )

    def test_effect_observer_shared_entry_watch_is_command_occurrence_exact(
        self,
    ) -> None:
        watch_id = "effect-watch-" + "d" * 64
        group_a = "group-a"
        group_b = "group-b"
        runtime = {
            "effect_templates": [{
                "template_id": "script-template",
                "abi_binding": {
                    "dispatch_kind": "SCRIPT_OPCODE", "opcode": "0x29",
                },
            }],
            "effect_signatures": [{
                "signature_id": "script-signature",
                "ordered_abi_dispatches": [],
                "ordered_effects": [{
                    "group_key": group_a, "execution_trace_index": 0,
                    "instruction_address": "0x08100000", "opcode": "0x29",
                }, {
                    # A single command owns two semantic domains.
                    "group_key": group_a, "execution_trace_index": 0,
                    "instruction_address": "0x08100000", "opcode": "0x29",
                }, {
                    "group_key": group_b, "execution_trace_index": 1,
                    "instruction_address": "0x08100010", "opcode": "0x2A",
                }],
            }],
            "effect_instances": [{
                "instance_id": instance_id, "case_id": "case-script",
                "signature_id": "script-signature",
                "template_id": "script-template", "group_key": group_key,
                "expected_contract": {
                    "proof_mode": "STATE_RANGE_EXACT",
                    "observer_contract": {
                        "completion_boundary": "FIELD_RELEASE",
                        "transitions": [],
                    },
                },
            } for instance_id, group_key in (
                ("instance-a0", group_a), ("instance-a1", group_a),
                ("instance-b0", group_b),
            )],
            "effect_instance_watch_bindings": [{
                "instance_id": instance_id, "watch_ids": [watch_id],
            } for instance_id in (
                "instance-a0", "instance-a1", "instance-b0",
            )],
            "no_dispatch_watch_bindings": [],
        }
        plan = {"watches": [{
            "watch_id": watch_id, "length": 0,
            "hook_pc": "0x0806911A",
            "completion_boundary": "FIELD_RELEASE",
            "address_resolver": {"kind": "SCRIPT_CURSOR_DISPATCH"},
            "arg_capture": [{
                "ordinal": 0, "phase": "ENTRY", "location": "R1",
                "width_bits": 8, "capture": "VALUE",
                "pointee_length": 0,
            }, {
                "ordinal": 1, "phase": "ENTRY", "location": "R2",
                "width_bits": 32, "capture": "VALUE",
                "pointee_length": 0,
            }],
        }]}

        def hook(ordinal: int, cursor: int, opcode: int) -> dict[str, object]:
            cursor_hex = f"0x{cursor:08X}"
            opcode_register = f"0x{opcode:08X}"
            return {
                "kind": "HOOK", "case_id": "case-script",
                "watch_id": watch_id, "ordinal": ordinal,
                "pc": "0x0806911A", "lr": "0x08070001",
                "r0": "0x00000000", "r1": opcode_register,
                "r2": cursor_hex, "r3": "0x00000000",
                "raw_pc": "0x0806911E", "capture_phase": "ENTRY",
                "captures": [{
                    "ordinal": 0, "location": "R1", "width_bits": 8,
                    "capture": "VALUE", "value": opcode_register,
                }, {
                    "ordinal": 1, "location": "R2", "width_bits": 32,
                    "capture": "VALUE", "value": cursor_hex,
                }],
                "script": {
                    "context_cursor": cursor_hex,
                    "opcode": f"0x{opcode:02X}", "cursor": cursor_hex,
                },
            }

        raw = {
            "before_fnv1a64": "0" * 16, "after_fnv1a64": "0" * 16,
            "length": 0,
            "before": {"path": "", "sha256": "", "address": "0x00000000"},
            "after": {"path": "", "sha256": "", "address": "0x00000000"},
            "transition": None,
            "completion": {"boundary": "FIELD_RELEASE", "ordinal": 2},
        }
        valid_hooks = [hook(1, 0x08100000, 0x29),
                       hook(2, 0x08100010, 0x2A)]
        boundary = {
            "kind": "CASE_END", "case_id": "case-script",
            "watch_ids": [watch_id], "raw": {watch_id: raw},
            "hook_hits": {watch_id: 2},
        }

        def validate(work: Path, hooks: list[dict[str, object]]) -> dict:
            (work / "effect-observer.jsonl").write_text(
                "\n".join(json.dumps(row) for row in [
                    {"kind": "META", "watch_count": 1}, *hooks, boundary,
                ]) + "\n", encoding="utf-8",
            )
            return RUNNER._validate_effect_observer_output(
                work, case="catalog_batch", runtime=runtime, plan=plan,
                expected_case_ids=["case-script"],
            )

        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            result = validate(work, valid_hooks)
            self.assertEqual(result["hook_count"], 2)
            self.assertEqual(len(result["instance_observations"]), 3)
            for label, mutate in (
                ("cursor", lambda rows: rows[1].update({
                    "r2": "0x08100020",
                    "script": {
                        "context_cursor": "0x08100020", "opcode": "0x2A",
                        "cursor": "0x08100020",
                    },
                    "captures": [{
                        **rows[1]["captures"][0],
                    }, {
                        **rows[1]["captures"][1], "value": "0x08100020",
                    }],
                })),
                ("opcode", lambda rows: rows[1].update({
                    "r1": "0x0000002B",
                    "script": {
                        "context_cursor": "0x08100010", "opcode": "0x2B",
                        "cursor": "0x08100010",
                    },
                    "captures": [{
                        **rows[1]["captures"][0], "value": "0x0000002B",
                    }, {
                        **rows[1]["captures"][1],
                    }],
                })),
                ("order", lambda rows: (
                    rows[0].update({
                        key: deepcopy(rows[1][key]) for key in (
                            "r1", "r2", "captures", "script",
                        )
                    }),
                    rows[1].update({
                        key: deepcopy(valid_hooks[0][key]) for key in (
                            "r1", "r2", "captures", "script",
                        )
                    }),
                )),
            ):
                broken = deepcopy(valid_hooks)
                mutate(broken)
                with self.subTest(label=label), self.assertRaisesRegex(
                    RUNNER.Stage61MgbaError, "command occurrence/order",
                ):
                    validate(work, broken)

        abi_watch = "effect-watch-" + "e" * 64
        abi_runtime = {
            "effect_templates": [{
                "template_id": "abi-template",
                "abi_binding": {
                    "dispatch_kind": "SPECIAL", "entry_pc": "0x08070000",
                },
            }],
            "effect_signatures": [{
                "signature_id": "abi-signature", "ordered_effects": [],
                "ordered_abi_dispatches": [{
                    "group_key": "abi-group-0", "execution_trace_index": 0,
                    "instruction_address": "0x08110000",
                    "entry_pc": "0x08070000",
                }, {
                    "group_key": "abi-group-1", "execution_trace_index": 1,
                    "instruction_address": "0x08110010",
                    "entry_pc": "0x08070000",
                }],
            }],
        }
        abi_instances = [{
            "instance_id": f"abi-instance-{index}",
            "signature_id": "abi-signature", "template_id": "abi-template",
            "group_key": f"abi-group-{index}",
            "expected_contract": {"observer_contract": {
                "completion_boundary": "SYNC_RETURN",
            }},
        } for index in range(2)]
        entry_by_instance, commands = RUNNER._effect_entry_command_contracts(
            abi_runtime, expected_case_ids=["abi-case"],
            watch_by_id={abi_watch: {
                "hook_pc": "0x08070000",
                "completion_boundary": "SYNC_RETURN",
                "address_resolver": {"kind": "NONE"},
            }},
            instance_by_case={"abi-case": abi_instances},
            binding_by_instance={
                row["instance_id"]: (abi_watch,) for row in abi_instances
            },
        )
        self.assertEqual(set(entry_by_instance.values()), {abi_watch})
        abi_hooks = [{"watch_id": abi_watch, "pc": "0x08070000"},
                     {"watch_id": abi_watch, "pc": "0x08070000"}]
        RUNNER._validate_effect_entry_command_observations(
            commands_by_case=commands, hooks_by_case={"abi-case": abi_hooks},
            boundaries={"abi-case": {"hook_hits": {abi_watch: 2}}},
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "occurrence/order|occurrence count",
        ):
            RUNNER._validate_effect_entry_command_observations(
                commands_by_case=commands,
                hooks_by_case={"abi-case": abi_hooks[:1]},
                boundaries={"abi-case": {"hook_hits": {abi_watch: 1}}},
            )

    def test_effect_observer_return_is_lifo_and_value_exact(self) -> None:
        entry_watch = "effect-watch-" + "f" * 64
        call_watch = "effect-watch-" + "9" * 64
        captures = lambda width: [{
            "ordinal": 0, "phase": "ENTRY", "location": "LR",
            "width_bits": 32, "capture": "VALUE", "pointee_length": 0,
        }, {
            "ordinal": 1, "phase": "RETURN", "location": "R0",
            "width_bits": width, "capture": "VALUE", "pointee_length": 0,
        }]
        plan = {"watches": [{
            "watch_id": entry_watch, "length": 0,
            "hook_pc": "0x08070000", "completion_boundary": "SYNC_RETURN",
            "address_resolver": {"kind": "NONE"},
            "arg_capture": captures(32),
        }, {
            "watch_id": call_watch, "length": 2, "hook_pc": None,
            "completion_boundary": "SYNC_RETURN",
            "address_resolver": {
                "kind": "U32_CODE_POINTER_AT",
                "pointer_slot": "0x02000020", "target_thumb": True,
            },
            "arg_capture": captures(16),
        }]}
        runtime = {
            "effect_templates": [{
                "template_id": "abi-template",
                "abi_binding": {
                    "dispatch_kind": "SPECIAL", "entry_pc": "0x08070000",
                },
            }],
            "effect_signatures": [{
                "signature_id": "abi-signature", "ordered_effects": [],
                "ordered_abi_dispatches": [{
                    "group_key": "abi-group", "execution_trace_index": 0,
                    "instruction_address": "0x08120000",
                    "entry_pc": "0x08070000",
                }],
            }],
            "effect_instances": [{
                "instance_id": "abi-instance", "case_id": "abi-case",
                "signature_id": "abi-signature",
                "template_id": "abi-template", "group_key": "abi-group",
                "expected_contract": {
                    "proof_mode": "CALL_SINK_EXACT",
                    "observer_contract": {
                        "completion_boundary": "SYNC_RETURN",
                        "sinks": [{
                            "watch_id": call_watch,
                            "entry_instruction_address": "0x08071000",
                            "rom_byte_length": 2,
                            "rom_sha256": hashlib.sha256(
                                b"\x00\x47"
                            ).hexdigest(),
                        }],
                        "expected_calls": [{
                            "watch_id": call_watch,
                            "caller_instruction_address": "0x08072000",
                            "arguments": [],
                            "return_capture": {
                                "location": "R0", "width_bits": 16,
                                "expected_value": 0x1234,
                            },
                        }],
                    },
                },
            }],
            "effect_instance_watch_bindings": [{
                "instance_id": "abi-instance",
                "watch_ids": sorted([entry_watch, call_watch]),
            }],
            "no_dispatch_watch_bindings": [],
        }

        def entry(
            ordinal: int, watch_id: str, pc: int, link: int,
        ) -> dict[str, object]:
            return {
                "kind": "HOOK", "case_id": "abi-case",
                "watch_id": watch_id, "ordinal": ordinal,
                "pc": f"0x{pc:08X}", "lr": f"0x{link:08X}",
                "r0": "0x00000000", "r1": "0x00000000",
                "r2": "0x00000000", "r3": "0x00000000",
                "raw_pc": f"0x{pc + 4:08X}", "capture_phase": "ENTRY",
                "captures": [{
                    "ordinal": 0, "location": "LR", "width_bits": 32,
                    "capture": "VALUE", "value": f"0x{link:08X}",
                }],
            }

        def returned(
            ordinal: int, entry_ordinal: int, watch_id: str,
            pc: int, value: int, width: int,
        ) -> dict[str, object]:
            value_hex = f"0x{value:08X}"
            return {
                "kind": "RETURN", "case_id": "abi-case",
                "watch_id": watch_id, "ordinal": ordinal,
                "entry_ordinal": entry_ordinal, "pc": f"0x{pc:08X}",
                "lr": "0x00000000", "r0": value_hex,
                "r1": "0x00000000", "r2": "0x00000000",
                "r3": "0x00000000", "raw_pc": f"0x{pc + 4:08X}",
                "capture_phase": "RETURN", "captures": [{
                    "ordinal": 1, "location": "R0", "width_bits": width,
                    "capture": "VALUE", "value": value_hex,
                }],
            }

        valid_records = [
            entry(1, entry_watch, 0x08070000, 0x08073001),
            entry(2, call_watch, 0x08071000, 0x08072005),
            returned(3, 2, call_watch, 0x08072004, 0x1234, 16),
            returned(4, 1, entry_watch, 0x08073000, 0, 32),
        ]

        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            leaf_dir = work / "effects" / "abi-case"
            leaf_dir.mkdir(parents=True)
            code = b"\x00\x47"
            before_path = leaf_dir / "call-before.bin"
            after_path = leaf_dir / "call-after.bin"
            before_path.write_bytes(code)
            after_path.write_bytes(code)
            zero_raw = {
                "before_fnv1a64": "0" * 16,
                "after_fnv1a64": "0" * 16, "length": 0,
                "before": {"path": "", "sha256": "",
                           "address": "0x00000000"},
                "after": {"path": "", "sha256": "",
                          "address": "0x00000000"},
                "transition": None,
                "completion": {"boundary": "SYNC_RETURN", "ordinal": 4},
            }
            code_sha = hashlib.sha256(code).hexdigest()
            call_raw = {
                "before_fnv1a64": "1" * 16,
                "after_fnv1a64": "1" * 16, "length": 2,
                "before": {
                    "path": "effects/abi-case/call-before.bin",
                    "sha256": code_sha, "address": "0x08071000",
                },
                "after": {
                    "path": "effects/abi-case/call-after.bin",
                    "sha256": code_sha, "address": "0x08071000",
                },
                "transition": None,
                "completion": {"boundary": "SYNC_RETURN", "ordinal": 4},
            }
            boundary = {
                "kind": "CASE_END", "case_id": "abi-case",
                "watch_ids": sorted([entry_watch, call_watch]),
                "raw": {entry_watch: zero_raw, call_watch: call_raw},
                "hook_hits": {entry_watch: 1, call_watch: 1},
            }

            def validate(
                records: list[dict[str, object]],
                selected_runtime: dict | None = None,
            ) -> dict:
                (work / "effect-observer.jsonl").write_text(
                    "\n".join(json.dumps(row) for row in [
                        {"kind": "META", "watch_count": 2},
                        *records, boundary,
                    ]) + "\n", encoding="utf-8",
                )
                return RUNNER._validate_effect_observer_output(
                    work, case="catalog_batch",
                    runtime=runtime if selected_runtime is None
                        else selected_runtime,
                    plan=plan,
                    expected_case_ids=["abi-case"],
                )

            result = validate(valid_records)
            self.assertEqual(
                [row["kind"]
                 for row in result["instance_observations"][0]["hooks"]],
                ["HOOK", "HOOK", "RETURN", "RETURN"],
            )
            for label, mutation, pattern in (
                ("lifo", lambda rows: rows[2].update({"entry_ordinal": 1}),
                 "LIFO/PC"),
                ("pc", lambda rows: rows[2].update({"pc": "0x08072006"}),
                 "LIFO/PC"),
                ("value", lambda rows: rows[2].update({
                    "r0": "0x00001235",
                    "captures": [{
                        **rows[2]["captures"][0], "value": "0x00001235",
                    }],
                }), "return value"),
                ("missing", lambda rows: rows.pop(),
                 "completion ordinal|RETURN欠落"),
            ):
                broken = deepcopy(valid_records)
                mutation(broken)
                with self.subTest(label=label), self.assertRaisesRegex(
                    RUNNER.Stage61MgbaError, pattern,
                ):
                    validate(broken)
            wrong_source = deepcopy(runtime)
            wrong_source["effect_instances"][0]["expected_contract"][
                "observer_contract"
            ]["sinks"][0]["rom_sha256"] = "0" * 64
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "dynamic code source span",
            ):
                validate(valid_records, wrong_source)

    def test_effect_observer_entry_watch_cannot_be_other_instance_non_entry(
        self,
    ) -> None:
        entry_x = "effect-watch-" + "4" * 64
        entry_y = "effect-watch-" + "5" * 64
        runtime = {
            "effect_templates": [{
                "template_id": "template-x",
                "abi_binding": {
                    "dispatch_kind": "SPECIAL", "entry_pc": "0x08070000",
                },
            }, {
                "template_id": "template-y",
                "abi_binding": {
                    "dispatch_kind": "SPECIAL", "entry_pc": "0x08071000",
                },
            }],
            "effect_signatures": [{
                "signature_id": "cross-role-signature", "ordered_effects": [],
                "ordered_abi_dispatches": [{
                    "group_key": "group-x", "execution_trace_index": 0,
                    "instruction_address": "0x08122000",
                    "entry_pc": "0x08070000",
                }, {
                    "group_key": "group-y", "execution_trace_index": 1,
                    "instruction_address": "0x08122010",
                    "entry_pc": "0x08071000",
                }],
            }],
            "effect_instances": [{
                "instance_id": "instance-x", "case_id": "cross-role-case",
                "signature_id": "cross-role-signature",
                "template_id": "template-x", "group_key": "group-x",
                "expected_contract": {
                    "proof_mode": "STATE_RANGE_EXACT",
                    "observer_contract": {
                        "completion_boundary": "SYNC_RETURN",
                        "transitions": [],
                    },
                },
            }, {
                "instance_id": "instance-y", "case_id": "cross-role-case",
                "signature_id": "cross-role-signature",
                "template_id": "template-y", "group_key": "group-y",
                "expected_contract": {
                    "proof_mode": "COMPOSITE",
                    "observer_contract": {
                        "completion_boundary": "SYNC_RETURN",
                    },
                },
            }],
            "effect_instance_watch_bindings": [{
                "instance_id": "instance-x", "watch_ids": [entry_x],
            }, {
                # X is Y's non-entry proof while remaining X's ENTRY.
                "instance_id": "instance-y",
                "watch_ids": sorted([entry_x, entry_y]),
            }],
            "no_dispatch_watch_bindings": [],
        }
        plan = {"watches": [{
            "watch_id": entry_x, "length": 0,
            "hook_pc": "0x08070000",
            "completion_boundary": "SYNC_RETURN",
            "address_resolver": {"kind": "NONE"}, "arg_capture": [],
        }, {
            "watch_id": entry_y, "length": 0,
            "hook_pc": "0x08071000",
            "completion_boundary": "SYNC_RETURN",
            "address_resolver": {"kind": "NONE"}, "arg_capture": [],
        }]}

        def hook(
            ordinal: int, watch_id: str, pc: int,
        ) -> dict[str, object]:
            return {
                "kind": "HOOK", "case_id": "cross-role-case",
                "watch_id": watch_id, "ordinal": ordinal,
                "pc": f"0x{pc:08X}", "lr": "0x0807F001",
                "r0": "0x00000000", "r1": "0x00000000",
                "r2": "0x00000000", "r3": "0x00000000",
                "raw_pc": f"0x{pc + 4:08X}",
                "capture_phase": "ENTRY", "captures": [],
            }

        raw = {
            "before_fnv1a64": "0" * 16,
            "after_fnv1a64": "0" * 16, "length": 0,
            "before": {"path": "", "sha256": "",
                       "address": "0x00000000"},
            "after": {"path": "", "sha256": "",
                      "address": "0x00000000"},
            "transition": None,
            "completion": {"boundary": "SYNC_RETURN", "ordinal": 2},
        }
        rows = [
            {"kind": "META", "watch_count": 2},
            hook(1, entry_x, 0x08070000),
            hook(2, entry_y, 0x08071000),
            {
                "kind": "CASE_END", "case_id": "cross-role-case",
                "watch_ids": sorted([entry_x, entry_y]),
                "raw": {entry_x: deepcopy(raw), entry_y: deepcopy(raw)},
                "hook_hits": {entry_x: 1, entry_y: 1},
            },
        ]
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / "effect-observer.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "entry/non-entry cross-role",
            ):
                RUNNER._validate_effect_observer_output(
                    work, case="catalog_batch", runtime=runtime, plan=plan,
                    expected_case_ids=["cross-role-case"],
                )

    def test_effect_observer_map_lifecycle_effect_order_is_single_signature(
        self,
    ) -> None:
        watch_id = "effect-watch-" + "8" * 64
        signature_effects = [{
            "group_key": "map-group-0", "template_id": "map-template",
            "execution_trace_index": 10,
            "instruction_address": "0x08130000", "opcode": "0x29",
            "abi_key": None, "group_member_ordinal": 0,
            "domain": "flags", "owner": "FLAG:1", "relation": "SET",
        }, {
            "group_key": "map-group-1", "template_id": "map-template",
            "execution_trace_index": 20,
            "instruction_address": "0x08130010", "opcode": "0x2A",
            "abi_key": None, "group_member_ordinal": 0,
            "domain": "vars", "owner": "VAR:1", "relation": "SET",
        }]
        lifecycle_effects = [{
            "effect_instance_ordinal": index, "dispatch_ordinal": index,
            "owner_id": f"MAP:003/004:00{index}:000",
            "root_pc": f"0x08130{index:03X}",
            "effect": {
                key: value for key, value in effect.items()
                if key not in {"group_key", "template_id"}
            },
        } for index, effect in enumerate(signature_effects)]
        sequence = {
            "sequence_id": "map-sequence",
            "effect_signature_ids": ["map-signature"],
            "map_lifecycle": {
                "ordered_effect_instances": lifecycle_effects,
            },
        }
        runtime = {
            "effect_templates": [{
                "template_id": "map-template",
                "abi_binding": {
                    "dispatch_kind": "SCRIPT_OPCODE", "opcode": "0x29",
                },
            }],
            "effect_signatures": [{
                "signature_id": "map-signature",
                "ordered_abi_dispatches": [],
                "ordered_effects": signature_effects,
            }],
            "event_runtime_cases": [{
                "case_id": "map-source",
                "case_kind": "MAP_LIFECYCLE_COMPOSITE",
                "input_sequences": [sequence],
            }],
        }
        instances = [{
            "instance_id": f"map-instance-{index}",
            "signature_id": "map-signature", "template_id": "map-template",
            "group_key": f"map-group-{index}",
            "expected_contract": {"observer_contract": {
                "completion_boundary": "FIELD_RELEASE",
            }},
        } for index in range(2)]
        watch = {
            "hook_pc": "0x0806911A",
            "completion_boundary": "FIELD_RELEASE",
            "address_resolver": {"kind": "SCRIPT_CURSOR_DISPATCH"},
        }
        kwargs = {
            "expected_case_ids": ["map-source--run-0000"],
            "watch_by_id": {watch_id: watch},
            "instance_by_case": {"map-source--run-0000": instances},
            "binding_by_instance": {
                row["instance_id"]: (watch_id,) for row in instances
            },
        }
        _entries, commands = RUNNER._effect_entry_command_contracts(
            runtime, **kwargs,
        )
        self.assertEqual(
            [row["trace"] for row in commands["map-source--run-0000"]],
            [10, 20],
        )
        reordered = deepcopy(runtime)
        reordered["event_runtime_cases"][0]["input_sequences"][0][
            "map_lifecycle"
        ]["ordered_effect_instances"][0]["effect"], reordered[
            "event_runtime_cases"
        ][0]["input_sequences"][0]["map_lifecycle"][
            "ordered_effect_instances"
        ][1]["effect"] = (
            reordered["event_runtime_cases"][0]["input_sequences"][0][
                "map_lifecycle"
            ]["ordered_effect_instances"][1]["effect"],
            reordered["event_runtime_cases"][0]["input_sequences"][0][
                "map_lifecycle"
            ]["ordered_effect_instances"][0]["effect"],
        )
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "MAP lifecycle/effect order",
        ):
            RUNNER._effect_entry_command_contracts(reordered, **kwargs)

        multiple = deepcopy(runtime)
        multiple["effect_signatures"].append({
            "signature_id": "map-signature-2",
            "ordered_abi_dispatches": [], "ordered_effects": [],
        })
        multiple["event_runtime_cases"][0]["input_sequences"][0][
            "effect_signature_ids"
        ].append("map-signature-2")
        multiple_instances = deepcopy(instances)
        multiple_instances.append({
            "instance_id": "map-instance-extra",
            "signature_id": "map-signature-2", "template_id": "map-template",
            "group_key": "map-group-extra",
            "expected_contract": {"observer_contract": {
                "completion_boundary": "FIELD_RELEASE",
            }},
        })
        with self.assertRaisesRegex(
            RUNNER.Stage61MgbaError, "signature exact-one",
        ):
            RUNNER._effect_entry_command_contracts(
                multiple, **{
                    **kwargs,
                    "instance_by_case": {
                        "map-source--run-0000": multiple_instances,
                    },
                    "binding_by_instance": {
                        row["instance_id"]: (watch_id,)
                        for row in multiple_instances
                    },
                },
            )

    def test_effect_observer_entry_call_fallback_joins_its_group_not_lr(
        self,
    ) -> None:
        watch_id = "effect-watch-" + "7" * 64
        capture_plan = [{
            "ordinal": 0, "phase": "ENTRY", "location": "LR",
            "width_bits": 32, "capture": "VALUE", "pointee_length": 0,
        }, {
            "ordinal": 1, "phase": "RETURN", "location": "R0",
            "width_bits": 32, "capture": "VALUE", "pointee_length": 0,
        }]
        plan = {"watches": [{
            "watch_id": watch_id, "length": 0,
            "hook_pc": "0x08076000", "completion_boundary": "SYNC_RETURN",
            "address_resolver": {"kind": "NONE"},
            "arg_capture": capture_plan,
        }]}
        fallback_contract = {
            "proof_mode": "CALL_SINK_EXACT",
            "observer_contract": {
                "completion_boundary": "SYNC_RETURN",
                "sinks": [{
                    "watch_id": watch_id,
                    "entry_instruction_address": "0x08076000",
                    "rom_byte_length": 2,
                    "rom_sha256": hashlib.sha256(b"\x00\x47").hexdigest(),
                    "calling_convention": "STAGE61_ABI_ENTRY_DISPATCH",
                }],
                "expected_calls": [{
                    "watch_id": watch_id,
                    # This is bytecode identity, not the live CPU LR.
                    "caller_instruction_address": "0x08140000",
                    "arguments": [],
                    "return_capture": {
                        "location": "NONE", "width_bits": 0,
                        "expected_value": None,
                    },
                }],
            },
        }
        runtime = {
            "effect_templates": [{
                "template_id": "fallback-template",
                "abi_binding": {
                    "dispatch_kind": "SPECIAL", "entry_pc": "0x08076000",
                },
            }],
            "effect_signatures": [{
                "signature_id": "fallback-signature", "ordered_effects": [],
                "ordered_abi_dispatches": [{
                    "group_key": "fallback-group-0",
                    "execution_trace_index": 0,
                    "instruction_address": "0x08140000",
                    "entry_pc": "0x08076000",
                }, {
                    "group_key": "fallback-group-1",
                    "execution_trace_index": 1,
                    "instruction_address": "0x08140010",
                    "entry_pc": "0x08076000",
                }],
            }],
            "effect_instances": [{
                "instance_id": "fallback-instance-0", "case_id": "case-fallback",
                "signature_id": "fallback-signature",
                "template_id": "fallback-template",
                "group_key": "fallback-group-0",
                "expected_contract": fallback_contract,
            }, {
                "instance_id": "fallback-instance-1", "case_id": "case-fallback",
                "signature_id": "fallback-signature",
                "template_id": "fallback-template",
                "group_key": "fallback-group-1",
                "expected_contract": {
                    "proof_mode": "STATE_RANGE_EXACT",
                    "observer_contract": {
                        "completion_boundary": "SYNC_RETURN",
                        "transitions": [],
                    },
                },
            }],
            "effect_instance_watch_bindings": [{
                "instance_id": f"fallback-instance-{index}",
                "watch_ids": [watch_id],
            } for index in range(2)],
            "no_dispatch_watch_bindings": [],
        }

        def entry_row(ordinal: int, link: int) -> dict[str, object]:
            link_hex = f"0x{link:08X}"
            return {
                "kind": "HOOK", "case_id": "case-fallback",
                "watch_id": watch_id, "ordinal": ordinal,
                "pc": "0x08076000", "lr": link_hex,
                "r0": "0x00000000", "r1": "0x00000000",
                "r2": "0x00000000", "r3": "0x00000000",
                "raw_pc": "0x08076004", "capture_phase": "ENTRY",
                "captures": [{
                    "ordinal": 0, "location": "LR", "width_bits": 32,
                    "capture": "VALUE", "value": link_hex,
                }],
            }

        def return_row(
            ordinal: int, entry_ordinal: int, pc: int,
        ) -> dict[str, object]:
            return {
                "kind": "RETURN", "case_id": "case-fallback",
                "watch_id": watch_id, "ordinal": ordinal,
                "entry_ordinal": entry_ordinal, "pc": f"0x{pc:08X}",
                "lr": "0x00000000", "r0": "0x00000000",
                "r1": "0x00000000", "r2": "0x00000000",
                "r3": "0x00000000", "raw_pc": f"0x{pc + 4:08X}",
                "capture_phase": "RETURN", "captures": [{
                    "ordinal": 1, "location": "R0", "width_bits": 32,
                    "capture": "VALUE", "value": "0x00000000",
                }],
            }

        records = [
            entry_row(1, 0x08078001), return_row(2, 1, 0x08078000),
            entry_row(3, 0x08079001), return_row(4, 3, 0x08079000),
        ]
        raw = {
            "before_fnv1a64": "0" * 16, "after_fnv1a64": "0" * 16,
            "length": 0,
            "before": {"path": "", "sha256": "", "address": "0x00000000"},
            "after": {"path": "", "sha256": "", "address": "0x00000000"},
            "transition": None,
            "completion": {"boundary": "SYNC_RETURN", "ordinal": 4},
        }
        boundary = {
            "kind": "CASE_END", "case_id": "case-fallback",
            "watch_ids": [watch_id], "raw": {watch_id: raw},
            "hook_hits": {watch_id: 2},
        }

        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)

            def validate(
                selected_runtime: dict, selected_records: list[dict],
            ) -> dict:
                (work / "effect-observer.jsonl").write_text(
                    "\n".join(json.dumps(row) for row in [
                        {"kind": "META", "watch_count": 1},
                        *selected_records, boundary,
                    ]) + "\n", encoding="utf-8",
                )
                return RUNNER._validate_effect_observer_output(
                    work, case="catalog_batch", runtime=selected_runtime,
                    plan=plan, expected_case_ids=["case-fallback"],
                )

            validate(runtime, records)
            different_live_lr = deepcopy(records)
            different_live_lr[0] = entry_row(1, 0x0807A001)
            different_live_lr[1] = return_row(2, 1, 0x0807A000)
            validate(runtime, different_live_lr)

            mixed = deepcopy(runtime)
            mixed["effect_instances"][0]["expected_contract"][
                "observer_contract"
            ]["expected_calls"][0]["caller_instruction_address"] = (
                "0x08140010"
            )
            with self.assertRaisesRegex(
                RUNNER.Stage61MgbaError, "entry/call group join",
            ):
                validate(mixed, records)

    def test_effect_observer_c_uses_instruction_steps_and_preinput_window(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("S61_EFFECT_RAW_WATCH_TSV", source)
        self.assertIn("s61_effect_observer_sample_pc(core, raw_pc)", source)
        self.assertIn("core->step(core)", source)
        self.assertIn("s61_effect_observer_begin_case(core, row.case_id)", source)
        self.assertIn("s61_effect_observer_end_case(core)", source)
        self.assertIn("0x0806911A", RUNNER._validate_effect_raw_watch.__code__.co_consts)


if __name__ == "__main__":
    unittest.main()
