from __future__ import annotations

import hashlib
import json
import unittest
from collections import Counter
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from tools.stage61_event_semantic_relocator import SemanticScriptGraph
from tools.stage61_interaction_oracle import (
    Stage61InteractionOracleError,
    _Execution,
    _build_event_design_rank_model,
    _event_design_source_binding,
    _event_design_source_model,
    _event_design_talk_source_aliases,
    _event_design_physical_controls,
    _fork_event_design_event_rank,
    _independent_runtime_text_assets,
    _materialize_control_requirement,
    _native_semantic_contract,
    _runtime_execute_with_seed_discovery,
    _runtime_control_candidate_values,
    _runtime_control_rows,
    _runtime_graph_script_bytes,
    _runtime_root_plan,
    _validate_event_design_rank_abi_entry,
    _validate_interaction_abi_entry,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER_ID = "BG:097/047:000"
OWNER_ROOT = 0x0938DD34
PORT_COORDINATOR_SOURCE_ROOT = 0x0938D304
PORT_COORDINATOR_FINAL_ROOT = 0x093EEA40
EXPECTED_TALK_ALIASES = {
    0x093EEA40: 0x0938D304,
    0x093EEB48: 0x0938D53C,
    0x093EEB94: 0x0938D5D0,
    0x093EEC60: 0x0938D698,
    0x093EECAC: 0x0938D778,
    0x093EED38: 0x0938D898,
    0x093EEDC4: 0x0938D970,
    0x093EEE10: 0x0938DA9C,
    0x093EEE5C: 0x0938DB78,
    0x093EEEA8: 0x0938DC58,
    0x093EEEF4: 0x0938DCA0,
    0x093EEF40: 0x0938DF60,
    0x093EEF8C: 0x0938E170,
    0x093EEFD8: 0x0938E2F4,
    0x093EF024: 0x0938E5E4,
}
MODEL_SOURCE_PATHS = (
    "content/event_design_implementation/event_plan.json",
    "generated/runtime/event_design_serialized.json",
    "generated/runtime/event_design_generated.h",
    "config/qol_production_bindings.csv",
    "content/trainer_changekit_final/trainer_runtime_consumers.csv",
    "overlays/event_design/event_design.c",
    "overlays/qol_production/qol_production.c",
    "overlays/qol_production/qol_production.h",
)


class Stage61EventDesignRankSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        cls.stage60 = (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes()
        cls.stage61 = (ROOT / "build/stages/61_display_npc_event_audit.gba").read_bytes()
        cls.semantic = json.loads((
            ROOT / "reports/generated/stage61_event_semantic_relocation.json"
        ).read_text())
        cls.inventory = json.loads((
            ROOT / "reports/generated/stage61_event_owner_inventory.json"
        ).read_text())
        cls.repair_manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_repair_manifest.json"
        ).read_text())
        cls.source_blobs = {
            path: (ROOT / path).read_bytes()
            for path in (
                *MODEL_SOURCE_PATHS,
                "scripts/build_stage61_display_npc_event_audit.py",
                "content/trainer_changekit_final/trainer_dialogue.csv",
            )
        }
        cls.owner = next(
            row for row in cls.inventory["owners"]
            if row["owner_id"] == OWNER_ID
        )
        if cls.owner["root"] != OWNER_ROOT:
            raise AssertionError("BG:097/047 root drift")
        cls.graph = SemanticScriptGraph(cls.stage61)
        cls.graph.walk([OWNER_ROOT])
        if cls.graph.diagnostics:
            raise AssertionError(cls.graph.diagnostics[0])

    def test_exact_native_candidates_and_widening_rejection(self) -> None:
        self.assertEqual(
            _native_semantic_contract("EventDesign_ScriptEventRank")
            ["result_contract"]["global_var_result_write"]
            ["candidate_values"],
            [0, 1, 2, 3],
        )
        for symbol in (
            "EventDesign_ScriptCheckCondition",
            "EventDesign_ScriptSetState",
            "EventDesign_ScriptGrantReward",
            "EventDesign_ScriptOpenEggBasket",
        ):
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

        manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        published = next(
            deepcopy(row) for row in manifest["native_abis"]
            if row["symbol"] == "EventDesign_ScriptEventRank"
        )
        # First form today's valid row, then prove the production manifest
        # validator rejects the historical widened mutation.
        published["result_contract"]["global_var_result_write"][
            "candidate_values"
        ] = [0, 1, 2, 3]
        validated_key, normalized = _validate_interaction_abi_entry(
            self.stage61, published, entry_kind="NATIVE",
            source_blobs=self.source_blobs,
        )
        self.assertEqual(validated_key, key)
        self.assertEqual(normalized["target_pointer"], 0x09388118)
        # The executor consumes this normalized row, so the specialized
        # EventRank validator must accept the same code identity after the
        # manifest Thumb bit has been stripped.
        _validate_event_design_rank_abi_entry(normalized, validated_key)
        published["result_contract"]["global_var_result_write"][
            "candidate_values"
        ] = list(range(8))
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "EVENT_DESIGN_RANK_ABI_CANDIDATE_DRIFT",
        ):
            _validate_interaction_abi_entry(
                self.stage61, published, entry_kind="NATIVE",
                source_blobs=self.source_blobs,
            )
        set_state = next(
            deepcopy(row) for row in manifest["native_abis"]
            if row["symbol"] == "EventDesign_ScriptSetState"
        )
        set_state.update(_native_semantic_contract(set_state["symbol"]))
        _validate_interaction_abi_entry(
            self.stage61, set_state, entry_kind="NATIVE",
            source_blobs=self.source_blobs,
        )
        set_state["result_contract"]["global_var_result_write"][
            "candidate_values"
        ] = list(range(8))
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "EVENT_DESIGN_NATIVE_ABI_SEMANTIC_DRIFT",
        ):
            _validate_interaction_abi_entry(
                self.stage61, set_state, entry_kind="NATIVE",
                source_blobs=self.source_blobs,
            )

    def test_structured_runtime_candidates_are_canonical_and_deduplicated(
        self,
    ) -> None:
        first = {"x": 3, "y": 2, "layout": {"id": 318}}
        same_different_key_order = {
            "layout": {"id": 318}, "y": 2, "x": 3,
        }
        second = {"x": 4, "y": 2, "layout": {"id": 319}}
        result = _runtime_control_candidate_values(
            "PLAYER_POSITION", 0,
            [second, first, same_different_key_order], (),
        )
        self.assertEqual(result, [first, second])
        self.assertIsNot(result[0], first)

    def test_runtime_context_requires_model_but_legacy_context_can_fallback(
        self,
    ) -> None:
        entry = {
            "symbol": "EventDesign_ScriptEventRank",
            "target_pointer": 0x09388119,
            **_native_semantic_contract("EventDesign_ScriptEventRank"),
        }
        state = _Execution(pc=OWNER_ROOT)
        raw = bytes.fromhex("2319813809")
        key = "NATIVE:0x09388119"
        legacy = SimpleNamespace(event_design_rank_model=None, case={})
        self.assertIsNone(_fork_event_design_event_rank(
            legacy, state, OWNER_ROOT, raw, key, entry,
        ))
        runtime = SimpleNamespace(
            event_design_rank_model=None,
            case={
                "owner_role": "ALL_EVENT_RUNTIME_OWNER",
                "owner_key": OWNER_ID,
            },
        )
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "EVENT_DESIGN_RANK_MODEL_REQUIRED",
        ):
            _fork_event_design_event_rank(
                runtime, state, OWNER_ROOT, raw, key, entry,
            )

    def test_source_model_has_exact_ten_physical_terminal_classes(self) -> None:
        model = _build_event_design_rank_model(
            self.source_blobs, self.graph, OWNER_ROOT,
        )
        self.assertIsNotNone(model)
        assert model is not None
        self.assertEqual(model["event_indices"], [34, 61, 62, 63, 69])
        self.assertEqual(model["call_count"], 15)
        self.assertEqual(model["physical_assignment_class_count"], 8192)
        self.assertEqual(model["terminal_scenario_count"], 10)
        self.assertEqual(Counter(
            (row["terminal"]["kind"], row["terminal"].get("rank"))
            for row in model["scenarios"]
        ), Counter({
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
        # Features 30 and 31 share the same HOF+certification readiness.
        self.assertTrue(all(
            bool(row["event_ranks"]["62"])
            == bool(row["event_ranks"]["63"])
            for row in model["scenarios"]
        ))

        missing = dict(self.source_blobs)
        missing.pop("content/event_design_implementation/event_plan.json")
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "EVENT_DESIGN_RANK_SOURCE_BLOB_MISSING_OR_DRIFT",
        ):
            _build_event_design_rank_model(missing, self.graph, OWNER_ROOT)

    def test_materialized_dispatcher_uses_pinned_source_binding_root(self) -> None:
        graph = SemanticScriptGraph(self.stage61)
        graph.walk(sorted(EXPECTED_TALK_ALIASES))
        self.assertEqual(graph.diagnostics, [])
        source_model = _event_design_source_model(self.source_blobs)
        aliases = _event_design_talk_source_aliases(
            self.stage60, source_model,
        )
        self.assertEqual({
            final_root: row["source_binding_root"]
            for final_root, row in aliases.items()
        }, EXPECTED_TALK_ALIASES)
        live_models = {}
        for final_root, expected_source_root in EXPECTED_TALK_ALIASES.items():
            binding = _event_design_source_binding(
                self.semantic, final_root, source_model, aliases,
            )
            live_model = _build_event_design_rank_model(
                self.source_blobs, graph, final_root,
                source_binding_root=int(binding["source_binding_root"]),
                source_binding_relation=str(binding["relation"]),
                source_binding_provenance=binding["provenance"],
                prebuilt_source_model=source_model,
            )
            self.assertIsNotNone(live_model)
            assert live_model is not None
            self.assertEqual(
                live_model["source_binding_root"],
                f"0x{expected_source_root:08X}",
            )
            self.assertEqual(
                live_model["event_indices"],
                source_model["bindings_by_root"][expected_source_root]
                ["event_indices"],
            )
            self.assertEqual(
                live_model["dispatcher"]["fallback_target"],
                int(binding["provenance"]["fallback"], 16),
            )
            live_models[final_root] = live_model
        source_binding = _event_design_source_binding(
            self.semantic, PORT_COORDINATOR_FINAL_ROOT,
            source_model, aliases,
        )
        self.assertEqual(
            source_binding["source_binding_root"],
            PORT_COORDINATOR_SOURCE_ROOT,
        )
        self.assertEqual(
            source_binding["relation"],
            "STAGE55_EVENT_DESIGN_VISIBLE_FALLBACK_REPAIR",
        )
        model = live_models[PORT_COORDINATOR_FINAL_ROOT]
        self.assertEqual(model["root"], "0x093EEA40")
        self.assertEqual(model["source_binding_root"], "0x0938D304")
        self.assertEqual(
            model["binding_relation"],
            "STAGE55_EVENT_DESIGN_VISIBLE_FALLBACK_REPAIR",
        )
        self.assertEqual(
            model["binding_provenance"]["prefix_sha256"],
            "231f58abcfbbb2d01c1959287dca294aae4a617039032a72116ba6911159dc6c",
        )
        self.assertEqual(model["event_indices"], [2, 3, 46, 51])
        with self.assertRaisesRegex(
            Stage61InteractionOracleError,
            "EVENT_DESIGN_RANK_DISPATCH_BINDING_DRIFT",
        ):
            _build_event_design_rank_model(
                self.source_blobs, graph, PORT_COORDINATOR_FINAL_ROOT,
                source_binding_root=OWNER_ROOT,
            )
        prefix_size = int(source_binding["provenance"]["prefix_size"])
        for relative_offset in (5, prefix_size + 1):
            with self.subTest(relative_offset=relative_offset):
                mutated = bytearray(self.stage61)
                mutated[
                    PORT_COORDINATOR_FINAL_ROOT - 0x08000000
                    + relative_offset
                ] ^= 1
                mutated_graph = SemanticScriptGraph(bytes(mutated))
                mutated_graph.walk([PORT_COORDINATOR_FINAL_ROOT])
                with self.assertRaisesRegex(
                    Stage61InteractionOracleError,
                    "EVENT_DESIGN_TALK_ALIAS_FINAL_BYTE_CONTRACT_DRIFT",
                ):
                    _build_event_design_rank_model(
                        self.source_blobs, mutated_graph,
                        PORT_COORDINATOR_FINAL_ROOT,
                        source_binding_root=int(
                            source_binding["source_binding_root"]
                        ),
                        source_binding_relation=str(
                            source_binding["relation"]
                        ),
                        source_binding_provenance=source_binding["provenance"],
                        prebuilt_source_model=source_model,
                    )

    def test_every_serialized_dispatcher_is_finitely_modelled(self) -> None:
        serialized = json.loads(self.source_blobs[
            "generated/runtime/event_design_serialized.json"
        ])
        roots = sorted({
            int(row["dispatcher_address"], 16)
            for row in serialized["physical_bindings"]
        })
        self.assertEqual(len(roots), 62)
        graph = SemanticScriptGraph(self.stage61)
        graph.walk(roots)
        self.assertEqual(graph.diagnostics, [])
        models = [
            _build_event_design_rank_model(
                self.source_blobs, graph, root,
            )
            for root in roots
        ]
        self.assertEqual(sum(model is not None for model in models), 61)
        self.assertEqual(sum(model is None for model in models), 1)
        self.assertTrue(all(
            model["terminal_scenario_count"] <= 10
            and model["physical_assignment_class_count"] <= 8192
            for model in models if model is not None
        ))

    def test_physical_controls_project_to_closed_runner_relations(self) -> None:
        model = _build_event_design_rank_model(
            self.source_blobs, self.graph, OWNER_ROOT,
        )
        assert model is not None
        fixtures: dict[str, dict] = {}
        projected = [
            _materialize_control_requirement(
                self.stage61, control,
                owner_keys=[OWNER_ID], fixtures=fixtures,
            )
            for scenario in model["scenarios"]
            for control in scenario["physical_controls"]
        ]
        self.assertTrue(all(row is not None for row in projected))
        rows = [row for row in projected if row is not None]
        normal_flags = [
            row for row in rows
            if row["kind"] == "FLAG"
            and not 0x1400 <= row["id"] <= 0x1407
            and row["id"] != 0x13FA
        ]
        cert_flags = [
            row for row in rows
            if row["kind"] == "FLAG" and 0x1400 <= row["id"] <= 0x1407
        ]
        league_flags = [
            row for row in rows
            if row["kind"] == "FLAG" and row["id"] == 0x13FA
        ]
        self.assertTrue(normal_flags)
        self.assertTrue(cert_flags)
        self.assertTrue(league_flags)
        self.assertTrue(all(row["relation_evidence"] == []
                            for row in normal_flags))
        self.assertEqual({
            evidence["operator"]
            for row in cert_flags for evidence in row["relation_evidence"]
        }, {"CERT_OWNER_FLAG_TO_MODERN_CERTIFICATION_BIT_MIRROR"})
        self.assertEqual({
            evidence["operator"]
            for row in league_flags for evidence in row["relation_evidence"]
        }, {"KANTO_LEAGUE_STATE_TO_LEAGUE_I_II_SAVE_MIRROR"})

        daycare = _event_design_physical_controls(
            {("DAYCARE_OCCUPIED", 0): True},
            model["source_contract_sha256"],
        )[0]
        daycare_row = _materialize_control_requirement(
            self.stage61, daycare,
            owner_keys=[OWNER_ID], fixtures=fixtures,
        )
        self.assertIsNotNone(daycare_row)
        assert daycare_row is not None
        self.assertEqual(
            (daycare_row["kind"], daycare_row["id"], daycare_row["value"]),
            ("DAYCARE_OCCUPIED", 0, True),
        )
        self.assertEqual([
            evidence["operator"]
            for evidence in daycare_row["relation_evidence"]
        ], ["EVENT_DESIGN_SOURCE_PHYSICAL_BOOL"])
        self.assertEqual(fixtures, {})

    def test_real_executor_reuses_rank_vector_without_path_cap(self) -> None:
        manifest = json.loads((
            ROOT / "reports/generated/stage61_interaction_abi_manifest.json"
        ).read_text())
        abi_index = {}
        for raw_entry in [
            *manifest["special_abis"], *manifest["native_abis"],
        ]:
            entry = deepcopy(raw_entry)
            entry["target_pointer"] = int(entry["target_pointer"], 16)
            entry["source_status"] = "PINNED_SOURCE_VERIFIED"
            if entry["symbol"].startswith("EventDesign_"):
                entry.update(_native_semantic_contract(entry["symbol"]))
            abi_index[entry["abi_key"]] = entry

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
        text_assets, _text_provenance = _independent_runtime_text_assets(
            self.clean, self.stage60, self.stage61, semantic,
            self.repair_manifest, self.graph,
            source_blobs=self.source_blobs,
        )
        executions, blockers = _runtime_execute_with_seed_discovery(
            self.clean, self.stage60, self.stage61, semantic,
            self.owner, self.graph, text_assets, abi_index,
            self.source_blobs,
            shared_script_bytes=_runtime_graph_script_bytes(self.graph),
            shared_root_plan=_runtime_root_plan(self.graph, OWNER_ROOT),
        )
        self.assertEqual(blockers, [])
        self.assertTrue(executions)
        model = executions[0][0].event_design_rank_model
        self.assertIsNotNone(model)
        assert model is not None
        scenario_ids = {
            state.event_design_scenario_id for _context, state in executions
        }
        self.assertEqual(scenario_ids, {
            row["scenario_id"] for row in model["scenarios"]
        })
        self.assertEqual(len(scenario_ids), 10)
        fixtures: dict[str, dict] = {}
        vectors_by_scenario: dict[str, set[str]] = {}
        for context, state in executions:
            external, _internal = _runtime_control_rows(
                context, state, owner_keys=[OWNER_ID], fixtures=fixtures,
            )
            vectors_by_scenario.setdefault(
                str(state.event_design_scenario_id), set()
            ).add(json.dumps(
                external, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"),
            ))
        self.assertEqual(len(vectors_by_scenario), 10)
        self.assertTrue(all(len(vectors) == 1
                            for vectors in vectors_by_scenario.values()))
        self.assertEqual(len({
            next(iter(vectors)) for vectors in vectors_by_scenario.values()
        }), 10)
        self.assertEqual(fixtures, {})
        physical_identities = sorted({
            identity
            for _context, state in executions
            for identity in state.event_design_physical_controls
        })
        for kind, identifier in physical_identities:
            observed = [
                state.event_design_physical_controls[(kind, identifier)]
                for _context, state in executions
            ]
            self.assertEqual(
                _runtime_control_candidate_values(
                    kind, identifier, observed,
                    (state for _context, state in executions),
                ),
                [False, True],
            )
        self.assertEqual(max(
            sum(
                row.get("kind") == "EVENT_DESIGN_EVENT_RANK"
                for row in state.decisions
            )
            for _context, state in executions
        ), 15)
        for _context, state in executions:
            decisions = [
                row for row in state.decisions
                if row.get("kind") == "EVENT_DESIGN_EVENT_RANK"
            ]
            self.assertLessEqual(len(decisions), 15)
            observed: dict[int, set[int]] = {}
            for row in decisions:
                observed.setdefault(row["event_index"], set()).add(
                    row["result_value"]
                )
            self.assertTrue(all(len(values) == 1
                                for values in observed.values()))
            self.assertTrue(all(
                state.flags[identifier] is value
                for (kind, identifier), value in
                    state.event_design_physical_controls.items()
                if kind == "FLAG"
            ))
            physical_reads = {
                (row["kind"], row["id"], row["required_value"])
                for row in state.abi_control_reads
                if isinstance(row.get("source"), dict)
                and row["source"].get("kind") ==
                    "EVENT_DESIGN_SOURCE_STATE_EQUIVALENCE_CLASS"
            }
            self.assertEqual(physical_reads, {
                (kind, identifier, value)
                for (kind, identifier), value in
                    state.event_design_physical_controls.items()
            })
        self.assertFalse(any(
            "path数上限超過" in str(blocker.get("detail", ""))
            for blocker in blockers
        ))


if __name__ == "__main__":
    unittest.main()
