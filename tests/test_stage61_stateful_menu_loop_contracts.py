from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.stage61_stateful_menu_loop_contracts import (  # noqa: E402
    CONTRACT_KIND,
    StatefulMenuLoopContractError,
    apply_bill_seen_transition,
    build_stateful_menu_loop_contracts,
    evaluate_vending_transition,
    research_result_disjoint_proof,
    validate_stateful_menu_loop_contracts,
)


STAGE61 = ROOT / "build/stages/61_display_npc_event_audit.gba"


def _contract(document: dict[str, object], contract_id: str) -> dict[str, object]:
    rows = document["contracts"]
    if not isinstance(rows, list):
        raise AssertionError("contracts is not a list")
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("contract_id") == contract_id
    ]
    if len(matches) != 1:
        raise AssertionError(f"contract differs: {contract_id}")
    return matches[0]


def _witness(contract: dict[str, object], suffix: str) -> dict[str, object]:
    rows = contract["witnesses"]
    if not isinstance(rows, list):
        raise AssertionError("witnesses is not a list")
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and str(row.get("witness_id", "")).endswith(suffix)
    ]
    if len(matches) != 1:
        raise AssertionError(f"witness differs: {suffix}")
    return matches[0]


class Stage61StatefulMenuTransitionTests(unittest.TestCase):
    def test_vending_transition_partition_and_exact_effects(self) -> None:
        insufficient = evaluate_vending_transition(0, 199, 7, 1)
        self.assertEqual(insufficient["selector"], "MONEY_LT_PRICE")
        self.assertEqual(insufficient["next"], "TERMINAL_INSUFFICIENT")
        self.assertEqual(insufficient["pre"], insufficient["post"])
        self.assertEqual(insufficient["effects"], [])

        bag_full = evaluate_vending_transition(1, 300, 4, 0)
        self.assertEqual(
            bag_full["selector"], "MONEY_GE_PRICE_AND_NO_BAG_CAPACITY"
        )
        self.assertEqual(bag_full["next"], "TERMINAL_BAG_FULL")
        self.assertEqual(bag_full["pre"], bag_full["post"])

        success = evaluate_vending_transition(2, 700, 2, 3)
        self.assertEqual(
            success["selector"], "MONEY_GE_PRICE_AND_BAG_CAPACITY"
        )
        self.assertEqual(success["item_id"], "0x001C")
        self.assertEqual(success["price"], 350)
        self.assertEqual(
            success["post"],
            {"money": 350, "item_count": 3, "remaining_capacity": 2},
        )
        self.assertEqual(
            [(row["domain"], row["relation"]) for row in success["effects"]],
            [("money", "SUBTRACT_EXACT"), ("items", "ADD_EXACT_QUANTITY")],
        )

        for result in (3, 0x7F):
            with self.subTest(result=result):
                exit_row = evaluate_vending_transition(result, 850, 0, 2)
                self.assertEqual(exit_row["selector"], "EXIT")
                self.assertEqual(exit_row["next"], "TERMINAL")
                self.assertEqual(exit_row["pre"], exit_row["post"])

    def test_bill_transition_is_exact_three_mirror_idempotent_or(self) -> None:
        initial = {
            "SAVE_BLOCK2_POKEDEX_SEEN": 0x05,
            "SAVE_BLOCK1_SEEN_PRIMARY": 0x05,
            "SAVE_BLOCK1_SEEN_SECONDARY": 0x05,
        }
        first = apply_bill_seen_transition(0, initial)
        self.assertEqual(first["mask"], "0x10")
        self.assertEqual(set(first["post_mirrors"].values()), {0x15})
        self.assertTrue(first["raw_delta"])
        second = apply_bill_seen_transition(0, first["post_mirrors"])
        self.assertEqual(second["post_mirrors"], first["post_mirrors"])
        self.assertFalse(second["raw_delta"])
        self.assertTrue(second["special_dispatch"])

        state = initial
        for choice in (0, 1, 2, 3):
            state = apply_bill_seen_transition(choice, state)["post_mirrors"]
        self.assertEqual(set(state.values()), {0xF5})

    def test_research_result_disjoint_proof_detects_feasible_mutation(self) -> None:
        proof = research_result_disjoint_proof()
        self.assertEqual(
            proof["producer_candidate_values"], [0, 3, 4, 5, 7, 13, 14, 15]
        )
        self.assertEqual(proof["reentry_required_values"], [10])
        self.assertEqual(proof["intersection"], [])
        self.assertFalse(proof["cycle_feasible"])

        mutated = research_result_disjoint_proof(
            [0, 3, 4, 5, 7, 10, 13, 14, 15], [10]
        )
        self.assertEqual(mutated["intersection"], [10])
        self.assertTrue(mutated["cycle_feasible"])


class Stage61StatefulMenuContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rom = STAGE61.read_bytes()
        cls.document = build_stateful_menu_loop_contracts(
            cls.rom, workspace_root=ROOT
        )

    def _assert_invalid(self, document: dict[str, object], pattern: str) -> None:
        with self.assertRaisesRegex(StatefulMenuLoopContractError, pattern):
            validate_stateful_menu_loop_contracts(
                document, self.rom, workspace_root=ROOT
            )

    def test_exact_stage61_build_and_strict_validation_pass(self) -> None:
        self.assertEqual(self.document["kind"], CONTRACT_KIND)
        self.assertEqual(self.document["status"], "PASS")
        self.assertEqual(
            self.document["rom_binding"]["sha256"],
            sha256(self.rom).hexdigest(),
        )
        validated = validate_stateful_menu_loop_contracts(
            self.document, self.rom, workspace_root=ROOT
        )
        self.assertEqual(validated, self.document)
        self.assertIsNot(validated, self.document)

        source_ids = {
            row["source_id"] for row in self.document["source_bindings"]
        }
        self.assertEqual(
            source_ids,
            {
                "FIRERED_SCRCMD",
                "RESEARCH_RUNTIME",
                "RESEARCH_BUILDER",
                "FIRERED_FIELD_SPECIALS",
                "FIRERED_POKEDEX_SCREEN",
                "VEGA_SAVE_LAYOUT",
            },
        )
        self.assertEqual(
            set(self.document["raw_spans"]),
            {
                "VENDING_VEGA",
                "VENDING_KANTO",
                "RESEARCH_SHOP",
                "BILL_ROOT_PREFIX",
                "BILL_DISPLAY_LOOP",
            },
        )

    def test_exact_finite_witness_counts_and_second_hits(self) -> None:
        for contract_id in ("VENDING_0818429E", "VENDING_09431D20"):
            contract = _contract(self.document, contract_id)
            self.assertEqual(len(contract["witnesses"]), 22)
            for choice, price, item in (
                (0, 200, "0x001A"),
                (1, 300, "0x001B"),
                (2, 350, "0x001C"),
            ):
                row = _witness(
                    contract, f"choice-{choice}-two-success-exit-b"
                )
                self.assertEqual(row["expected_post"]["money"], 0)
                self.assertEqual(row["pre"]["bag_counts"][item], 997)
                self.assertEqual(row["expected_post"]["bag_counts"][item], 999)
                physical = row["pre"]["bag_physical_layout"]
                self.assertEqual(physical["pocket"], "ITEMS")
                self.assertEqual(physical["slot_count"], 42)
                self.assertEqual(physical["occupied_slots"], 42)
                self.assertEqual(physical["empty_slots"], 0)
                self.assertEqual(physical["stack_max"], 999)
                self.assertEqual(
                    [entry["slot_count"] for entry in physical["all_pocket_layout"]],
                    [42, 30, 13, 58, 43],
                )
                self.assertEqual(physical["all_pocket_total_slots"], 186)
                self.assertEqual(
                    physical["raw_snapshot_range"],
                    {
                        "owner": "SAVE_BLOCK1",
                        "start": "0x0310",
                        "end_exclusive": "0x05F8",
                        "byte_length": 0x2E8,
                    },
                )
                self.assertTrue(physical["target_item_id_and_slot_identity_exact"])
                self.assertEqual(row["dynamic_hits"]["removemoney"], 2)
                self.assertEqual(row["dynamic_hits"]["additem"], 2)
                first, second = row["steps"][:2]
                self.assertEqual(first["effects"][0]["amount"], price)
                self.assertEqual(second["effects"][0]["amount"], price)
                self.assertNotEqual(
                    first["required_dynamic_effect_group"],
                    second["required_dynamic_effect_group"],
                )
                self.assertTrue(
                    row["proof_obligations"]["second_mutating_hit_distinct"]
                )

                bag_boundary = _witness(
                    contract, f"choice-{choice}-success-then-bag-full"
                )
                self.assertEqual(
                    bag_boundary["pre"]["bag_counts"][item], 998
                )
                self.assertEqual(
                    bag_boundary["steps"][0]["post"]["bag_counts"][item],
                    999,
                )
                self.assertEqual(
                    bag_boundary["steps"][1]["pre"],
                    bag_boundary["steps"][1]["post"],
                )
                self.assertEqual(
                    bag_boundary["terminal"]["reason"], "BAG_FULL"
                )
                self.assertEqual(
                    bag_boundary["dynamic_hits"]["branch"], 3
                )

            insufficient = _witness(
                contract, "choice-0-insufficient-first"
            )
            self.assertEqual(insufficient["dynamic_hits"]["branch"], 2)

        bill = _contract(self.document, "BILL_SET_SEEN_09434AEC")
        self.assertEqual(len(bill["witnesses"]), 12)
        self.assertEqual(
            bill["owner_binding"]["root_flag_classes"],
            [
                {"temp_flag_3": False, "temp_flag_2": False},
                {"temp_flag_3": False, "temp_flag_2": True},
                {"temp_flag_3": True, "temp_flag_2": False},
                {"temp_flag_3": True, "temp_flag_2": True},
            ],
        )
        self.assertEqual(
            bill["owner_binding"]["root_flag_storage"]["owner_byte_offset"],
            "0x0EE0",
        )
        root_guards = [
            edge["guard"] for edge in bill["cfg"]["edges"]
            if edge["from"] == "0x094349F8"
        ]
        self.assertEqual(
            root_guards,
            [
                "TEMP_FLAG_3_TRUE",
                "TEMP_FLAG_3_FALSE_AND_TEMP_FLAG_2_TRUE",
                "TEMP_FLAG_3_FALSE_AND_TEMP_FLAG_2_FALSE",
            ],
        )
        self.assertNotIn("engine_special_flag_2", repr(bill).lower())
        self.assertNotIn("engine_special_flag_3", repr(bill).lower())
        pinned = bill["state_projection"]["pinned_canary_ranges"]
        self.assertEqual(
            [(entry["owner"], entry["offset"], entry["byte_length"])
             for entry in pinned],
            [
                ("SAVE_BLOCK2", "0x005C", 52),
                ("SAVE_BLOCK1", "0x05F8", 52),
                ("SAVE_BLOCK1", "0x3A18", 52),
                ("SAVE_BLOCK2", "0x0028", 52),
                ("SAVE_BLOCK1", "0x0034", 604),
                ("SAVE_BLOCK2", "0x0200", 32),
            ],
        )
        self.assertEqual(
            bill["state_projection"]["other_persistent"],
            "PINNED_CANARY_RANGES_EXACT",
        )
        for choice in range(4):
            row = _witness(bill, f"choice-{choice}-twice-exit-b")
            first, second = row["steps"][:2]
            self.assertTrue(first["raw_delta"])
            self.assertFalse(second["raw_delta"])
            self.assertTrue(second["special_dispatch"])
            self.assertNotEqual(
                first["required_dynamic_effect_group"],
                second["required_dynamic_effect_group"],
            )
        forward = _witness(bill, "all-forward-exit-explicit")
        reverse = _witness(bill, "all-reverse-exit-b")
        self.assertEqual(
            forward["expected_post"]["seen_mirror_bytes"],
            reverse["expected_post"]["seen_mirror_bytes"],
        )
        self.assertEqual(
            set(forward["expected_post"]["seen_mirror_bytes"].values()),
            {0xF5},
        )
        self.assertEqual(forward["dynamic_hits"]["branch"], 6)

    def test_runtime_owner_and_exact_trace_site_bindings(self) -> None:
        vega = _contract(self.document, "VENDING_0818429E")
        self.assertEqual(
            vega["owner_binding"]["runtime_owner_ids"],
            ["BG:010/005:001", "BG:010/005:003"],
        )
        self.assertEqual(
            vega["owner_binding"]["runtime_owner_exclusions"],
            [{
                "owner_id": "BG:010/005:002",
                "reason": "STANCE_OCCUPIED_IN_FRESH_BASELINE",
                "stance_object_free": False,
                "runtime_topology_probe_required": True,
            }],
        )
        self.assertEqual(
            vega["rom_binding"]["runtime_trace_sites"]["additem"],
            ["0x08184373"],
        )
        kanto = _contract(self.document, "VENDING_09431D20")
        self.assertEqual(
            kanto["rom_binding"]["runtime_trace_sites"]["additem"],
            ["0x09431DF1"],
        )
        bill = _contract(self.document, "BILL_SET_SEEN_09434AEC")
        self.assertEqual(
            bill["rom_binding"]["runtime_trace_sites"]["backedge"],
            [
                "0x09434B48", "0x09434B5C",
                "0x09434B70", "0x09434B84",
            ],
        )
        self.assertEqual(
            bill["rom_binding"]["runtime_trace_sites"]["special"],
            ["0x080CCF5C"],
        )

    def test_research_exact_result_disjoint_and_catalog_contract(self) -> None:
        research = _contract(
            self.document, "RESEARCH_RESULT_DISJOINT_093C03A4"
        )
        self.assertEqual(
            research["abi_results"]["purchase_selected"],
            [0, 3, 4, 5, 7, 13, 14, 15],
        )
        self.assertEqual(
            research["infeasible_cycle_proof"]["intersection"], []
        )
        self.assertEqual(research["loop_witnesses"], [])
        probe = research["physical_runtime_probe"]
        self.assertEqual(
            probe["locked_control"]["expected_open_shop_result"], 3
        )
        self.assertEqual(
            probe["native_b_cancel"]["precondition_flags"],
            {"0x0824": True, "0x114B": True},
        )
        self.assertEqual(
            probe["native_b_cancel"]["expected_open_shop_busy_result"], 9
        )
        self.assertEqual(
            probe["native_b_cancel"]["expected_post_shop_result"], 2
        )
        self.assertTrue(
            probe["native_b_cancel"]["engine_rejected_16_forbidden"]
        )
        self.assertEqual(len(research["catalog"]), 23)
        self.assertEqual(
            [
                row["index"]
                for row in research["catalog"]
                if row["daily_limit"] > 0
            ],
            [14, 15, 20, 21],
        )
        self.assertTrue(
            all(row["once_bit"] == "RESEARCH_NO_ONCE_BIT"
                for row in research["catalog"])
        )

    def test_price_and_item_drift_fail_closed(self) -> None:
        for field, value in (("price", 201), ("item_id", "0x001D")):
            with self.subTest(field=field):
                document = deepcopy(self.document)
                contract = _contract(document, "VENDING_0818429E")
                contract["products"][0][field] = value
                self._assert_invalid(document, rf"products.*{field}")

    def test_bill_mask_and_mirror_drift_fail_closed(self) -> None:
        document = deepcopy(self.document)
        bill = _contract(document, "BILL_SET_SEEN_09434AEC")
        bill["choices"][0]["mask"] = "0x20"
        self._assert_invalid(document, r"BILL\.choices.*mask")

        document = deepcopy(self.document)
        bill = _contract(document, "BILL_SET_SEEN_09434AEC")
        bill["seen_mirrors"][1]["byte_offset"] = "0x0609"
        self._assert_invalid(document, r"BILL\.seen_mirrors.*byte_offset")

    def test_research_candidate_drift_fail_closed(self) -> None:
        document = deepcopy(self.document)
        research = _contract(
            document, "RESEARCH_RESULT_DISJOINT_093C03A4"
        )
        research["abi_results"]["purchase_selected"] = [
            0, 1, 3, 5, 7, 13, 14, 15
        ]
        self._assert_invalid(document, "Research purchase candidate")

        document = deepcopy(self.document)
        research = _contract(
            document, "RESEARCH_RESULT_DISJOINT_093C03A4"
        )
        research["infeasible_cycle_proof"]["producer_candidate_values"].append(10)
        research["infeasible_cycle_proof"]["intersection"] = [10]
        self._assert_invalid(document, "intersection非空")

    def test_backedge_and_witness_omission_fail_closed(self) -> None:
        document = deepcopy(self.document)
        contract = _contract(document, "VENDING_09431D20")
        contract["cfg"]["backedges"][0]["to"] = "0x09431D21"
        self._assert_invalid(document, r"cfg\.backedges.*to")

        document = deepcopy(self.document)
        contract = _contract(document, "VENDING_0818429E")
        contract["witnesses"].pop()
        self._assert_invalid(document, "witness件数")

        document = deepcopy(self.document)
        contract = _contract(document, "VENDING_0818429E")
        contract["rom_binding"]["runtime_trace_sites"]["additem"] = [
            "0x08184372"
        ]
        self._assert_invalid(document, r"runtime_trace_sites.*additem")

    def test_second_hit_state_or_dispatch_drift_fail_closed(self) -> None:
        document = deepcopy(self.document)
        contract = _contract(document, "VENDING_0818429E")
        row = _witness(contract, "choice-0-two-success-exit-b")
        row["steps"][1]["post"]["money"] = 1
        self._assert_invalid(document, r"witnesses.*steps.*money")

        document = deepcopy(self.document)
        bill = _contract(document, "BILL_SET_SEEN_09434AEC")
        row = _witness(bill, "choice-0-twice-exit-b")
        row["steps"][1]["special_dispatch"] = False
        self._assert_invalid(document, r"BILL\.witnesses.*special_dispatch")

    def test_rom_backedge_byte_drift_fails_before_contract_generation(self) -> None:
        rom = bytearray(self.rom)
        # 0x08184384: goto 0x0818429E のtarget low byte。
        rom[0x08184385 - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            StatefulMenuLoopContractError, "ROM raw span不一致"
        ):
            build_stateful_menu_loop_contracts(bytes(rom), workspace_root=ROOT)


if __name__ == "__main__":
    unittest.main()
