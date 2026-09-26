"""Fail-closed metadata tests for the diagnostic-only fixed FORM probe."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pr16_fixed_form_probe as m


class FixedFormProbeTests(unittest.TestCase):
    def sample(self, name, ordinal=42, outcome="selected-target"):
        value = m.expected(name, ordinal)
        party_opened = outcome in {"selected-target", "pending-mismatch", "party-slot-not-selected"}
        target_match = outcome in {"selected-target", "party-slot-not-selected"}
        selection_sent = outcome == "selected-target"
        value.update({
            "menu_opened": outcome != "menu-navigation-failed",
            "party_opened": party_opened,
            "target_match": target_match,
            "selection_sent": selection_sent,
            "field_returned": outcome in {"pending-mismatch", "native-terminal"},
            "probe_outcome": outcome,
            "wait_kind": 2 if outcome == "native-terminal" else (1 if party_opened else 0),
            "pending_form": value["form_index"] if target_match else 37,
            "result": 20 if party_opened else 9,
            "main_callback2": 0x08055E75,
            "window": 1,
            "species_after": value["base_species"],
            "held_item_after": 0,
            "moves_after": [98, 235, 552, 33],
            "pp_after": [11, 3, 4, 7],
            "pp_bonuses_after": 229,
            "identity_preserved": True,
            "nonselected_preserved": True,
            "save_counter_before": 10,
            "save_counter_after": 10,
            "total_frames": 12000,
        })
        if outcome == "menu-navigation-failed":
            value["pending_form"] = 0
        return value

    def test_case_matrix_is_exact_finite_and_contract_bound(self):
        self.assertEqual(
            tuple(m.CASES),
            (
                "necrozma-dusk-mane-native-probe",
                "necrozma-dawn-wings-native-probe",
                "zacian-crowned-native-probe",
                "zamazenta-crowned-native-probe",
            ),
        )
        self.assertEqual(
            {case["target_species"] for case in m.CASES.values()},
            {1260, 1261, 1386, 1387},
        )
        self.assertEqual(
            {case["form_index"] for case in m.CASES.values()},
            {245, 246, 280, 281},
        )
        self.assertEqual(
            {case["route_id"] for case in m.CASES.values()},
            {
                "667255b406678096a7fa9344",
                "a79bbbec71c9a6be03a7d1e4",
                "371ffcca84ed4eb8fbb6d56b",
                "2a8a2a856af40ec96087c9a7",
            },
        )

    def test_all_observation_outcomes_validate_without_claiming_acceptance(self):
        name = next(iter(m.CASES))
        for outcome in (
            "menu-navigation-failed",
            "native-terminal",
            "party-not-opened",
            "pending-mismatch",
            "selected-target",
            "party-slot-not-selected",
        ):
            with self.subTest(outcome=outcome):
                value = self.sample(name, outcome=outcome)
                self.assertEqual(
                    m.validate(json.dumps(value).encode(), name, 42, 0), value
                )
                self.assertEqual(value["status"], "OBSERVED")
                self.assertFalse(value["acceptance_claimed"])
                self.assertFalse(value["p03_fixed_form_gap_closed"])
                self.assertFalse(value["full_p03_acceptance"])
                self.assertFalse(value["release_ready"])

    def test_schema_identity_and_acceptance_flags_are_fail_closed(self):
        name = next(iter(m.CASES))
        good = self.sample(name)
        changes = (
            ("status", "PASS"),
            ("scope", "PR16_P03_FIXED_FORM_TRANSITION_PHYSICAL"),
            ("rom_sha256", "0" * 64),
            ("form_index", 43),
            ("canonical_ordinal", 41),
            ("menu_page", 0),
            ("menu_navigation", "host-write"),
            ("route_id", "wrong"),
            ("identity_preserved", False),
            ("nonselected_preserved", False),
            ("acceptance_claimed", True),
            ("p03_fixed_form_gap_closed", True),
            ("full_p03_acceptance", True),
            ("release_ready", True),
        )
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate(json.dumps(good | {key: value}).encode(), name, 42, 0)
        with self.assertRaises(ValueError):
            m.validate(json.dumps(good | {"extra": 1}).encode(), name, 42, 0)
        for code in (1, None, False, 0.0):
            with self.assertRaises(ValueError):
                m.validate(json.dumps(good).encode(), name, 42, code)

    def test_selection_requires_native_target_match(self):
        name = next(iter(m.CASES))
        good = self.sample(name)
        for key, value in (
            ("party_opened", False),
            ("target_match", False),
            ("pending_form", 37),
            ("wait_kind", 0),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate(json.dumps(good | {key: value}).encode(), name, 42, 0)
        mismatch = self.sample(name, outcome="pending-mismatch")
        mismatch["selection_sent"] = True
        with self.assertRaises(ValueError):
            m.validate(json.dumps(mismatch).encode(), name, 42, 0)

    def test_vectors_and_runtime_ranges_are_bounded(self):
        name = next(iter(m.CASES))
        good = self.sample(name)
        for key, value in (
            ("moves_after", [1, 2, 3]),
            ("moves_after", [1, 2, 3, 1063]),
            ("pp_after", [1, 2, 3]),
            ("pp_after", [1, 2, 3, 64]),
            ("pp_bonuses_after", 256),
            ("pending_form", 65536),
            ("result", 65536),
            ("main_callback2", 0x100000000),
            ("window", 256),
            ("total_frames", 0),
            ("save_counter_after", 9),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate(json.dumps(good | {key: value}).encode(), name, 42, 0)

    def test_controller_uses_native_menu_input_and_no_post_barrier_writes(self):
        text = (ROOT / m.SOURCE).read_text(encoding="utf-8")
        self.assertIn("b_position(core, 1U, 36U, 6U, 4U)", text)
        self.assertIn("b_press(core, QOL_KEY_A", text)
        self.assertIn("b_press(core, QOL_KEY_DOWN", text)
        self.assertIn("read16(core, F_STATE + 10U)", text)
        self.assertIn("P02S_CB2_PARTY", text)
        self.assertIn("canonical-ordinal-native-input", text)
        self.assertNotIn("write16(core, F_STATE", text)
        self.assertNotIn("write8(core, F_CURSOR", text)
        self.assertNotIn("write8(core, F_PARTY_SLOT", text)
        guarded = text.split(
            "/* Observation barrier: only native GBA input and read-only observations. */",
            1,
        )[1].split("a_restore(core, &saved);", 1)[0]
        for forbidden in (
            "write8(",
            "write16(",
            "write32(",
            "call_preserving(",
            "create_mon(",
            "set_mon_data_u32(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, guarded)

    def test_report_cannot_convert_diagnostic_to_acceptance(self):
        text = (ROOT / m.SELF).read_text(encoding="utf-8")
        report = text.rsplit("    report = {", 1)[1]
        self.assertIn('"status": "FAIL" if failures else "PASS_DIAGNOSTIC_ONLY"', report)
        self.assertIn('"actual_new_processes": len(CASES)', report)
        self.assertIn('"native_acceptance_claimed": False', report)
        self.assertIn('"p03_fixed_form_gap_closed": False', report)
        self.assertIn('"full_p03_acceptance": False', report)
        self.assertIn('"release_ready": False', report)
        self.assertNotIn('"fixed_form_transition_physical_accepted": True', report)

    def test_workflow_preserves_sources_and_excludes_private_binaries(self):
        text = (ROOT / m.WORKFLOW).read_text(encoding="utf-8")
        for path in (m.SELF, m.SOURCE, m.TEST, m.WORKFLOW, m.CONTRACT_JSON):
            self.assertIn(path, text)
        self.assertIn("include-hidden-files: true", text)
        self.assertIn("never ROM, save or private archive", text)
        self.assertNotIn("*.gba", text)
        self.assertNotIn("*.srm", text)
        self.assertNotIn("pokemon-vega-private-env-v1-inputs.zip\n          ", text)


if __name__ == "__main__":
    unittest.main()
