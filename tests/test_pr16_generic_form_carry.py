"""Fail-closed metadata tests; native acceptance occurs only in mGBA Actions."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pr16_generic_form_carry as m


class GenericFormCarryTests(unittest.TestCase):
    def sample_probe(self, name, opened=False):
        out = m.expected_probe(name)
        mask = out["pre_mask"] | out["post_mask"]
        out.update({
            "save_counter_before": 0,
            "save_counter_after": out["finalize_count"],
            "baseline_readback": [0, 0, 0, 0, 0, 0],
            "progress_readback": [
                int(bool(mask & m.FIX_HOF_FLAG)),
                int(bool(mask & m.FIX_HOF_MIRROR)),
                int(bool(mask & m.FIX_LEDGER_20)),
                int(bool(mask & m.FIX_LEAGUE_II)),
            ],
            "host_readback": [1, 1],
            "interaction_frame": 2000,
            "root_menu_opened": opened,
            "root_frame": 2100 if opened else 0,
            "result": 9 if opened else 0,
            "host": 3 if opened else 0,
            "service": 3 if opened else 0,
            "mode": 0,
            "page": 0,
            "window": 1 if opened else 255,
            "field_lock": 1 if opened else 0,
            "main_callback2": 0x08055E75,
            "total_frames": 4000,
        })
        return out

    def sample(self, name):
        out = m.expected(name)
        out.update({
            "menu_page": 3,
            "menu_cursor": 2,
            "probe_count": 18,
            "pages_scanned": 4,
        })
        out["total_frames"] = 24000
        out["traces"] = []
        species = [900, 749] if name == m.CASES[0] else [749]
        for index in range(out["rounds"]):
            base = index * 10000
            trace = {
                "interaction": base + 100,
                "root": base + 200,
                "service": base + 300,
                "page": base + 400,
                "party": base + 500,
                "selection": base + 600 if name == m.CASES[0] else 0,
                "returned": base + 700,
                "species_after": species[index],
                "saved": base + 800,
                "reloaded": base + 900,
                "menu_page": out["menu_page"],
                "menu_cursor": out["menu_cursor"],
                "probe_count": out["probe_count"],
                "pages_scanned": out["pages_scanned"],
            }
            out["traces"].append(trace)
        return out

    def test_entry_probe_matrix_is_finite_unique_and_non_accepting(self):
        self.assertEqual(len(m.PROBES), 14)
        self.assertEqual(len(m.PROBE_BY_NAME), len(m.PROBES))
        self.assertEqual(
            len({(probe["normalize"], probe["pre_mask"], probe["post_mask"])
                 for probe in m.PROBES}),
            len(m.PROBES),
        )
        known = (m.FIX_HOF_FLAG | m.FIX_HOF_MIRROR | m.FIX_LEDGER_20
                 | m.FIX_LEAGUE_II | m.FIX_HOST_PROGRESS | m.FIX_FINALIZE)
        for probe in m.PROBES:
            with self.subTest(probe=probe["name"]):
                self.assertEqual((probe["pre_mask"] | probe["post_mask"]) & ~known, 0)
                self.assertTrue((probe["pre_mask"] | probe["post_mask"]) & m.FIX_HOST_PROGRESS)
                self.assertIn(m.expected_probe(probe["name"])["finalize_count"], (1, 2))
                self.assertFalse(m.expected_probe(probe["name"])["acceptance_claimed"])

    def test_entry_probe_matrix_separates_flag_mirrors_and_finalize_order(self):
        by_name = m.PROBE_BY_NAME
        self.assertEqual(
            by_name["entry-hof-flag-post-once"]["post_mask"],
            m.FIX_HOF_FLAG | m.FIX_HOST_PROGRESS | m.FIX_FINALIZE,
        )
        self.assertEqual(
            by_name["entry-hof-mirror-post-once"]["post_mask"],
            m.FIX_HOF_FLAG | m.FIX_HOF_MIRROR | m.FIX_HOST_PROGRESS | m.FIX_FINALIZE,
        )
        self.assertFalse(by_name["entry-legacy-ledgers-pre-split"]["pre_mask"] & m.FIX_HOF_FLAG)
        self.assertTrue(by_name["entry-hof-legacy-pre-split"]["pre_mask"] & m.FIX_HOF_FLAG)
        self.assertEqual(by_name["entry-hof-legacy-pre-split"]["post_mask"],
                         m.FIX_HOST_PROGRESS | m.FIX_FINALIZE)
        self.assertEqual(by_name["entry-hof-legacy-host-pre-once"]["post_mask"], 0)

    def test_entry_diagnostic_accounting_cannot_promote_acceptance(self):
        text = (ROOT / "scripts/pr16_generic_form_carry.py").read_text()
        final_report = text.rsplit("    report = {", 1)[1]
        self.assertIn('"entry_diagnostic_processes": len(PROBES)', final_report)
        self.assertIn('"actual_new_processes": len(CASES)', final_report)
        self.assertIn('"successful_fresh_cores": sum(', final_report)
        self.assertIn('"generic_form_carry_physical_accepted": not failures', final_report)
        self.assertNotIn('"actual_new_processes": len(PROBES)', final_report)
        self.assertNotIn('"generic_form_carry_physical_accepted": not diagnostic_failures',
                         final_report)

    def test_entry_probe_accepts_observation_not_product_acceptance(self):
        for opened in (False, True):
            for name in ("entry-host-only-normalized", "entry-hof-flag-post-once"):
                with self.subTest(opened=opened, name=name):
                    value = self.sample_probe(name, opened)
                    self.assertEqual(m.validate_probe(json.dumps(value).encode(), name, 0), value)
                    self.assertFalse(value["acceptance_claimed"])
                    self.assertEqual(value["status"], "OBSERVED")

    def test_entry_probe_schema_and_root_state_are_fail_closed(self):
        name = "entry-hof-flag-post-once"
        good = self.sample_probe(name, True)
        for key, value in [
            ("acceptance_claimed", True),
            ("release_ready", True),
            ("scope", m.SCOPE),
            ("normalize", False),
            ("pre_mask", 1),
            ("root_frame", 0),
            ("host", 0),
            ("window", 255),
            ("baseline_readback", [0, 0, 0, 0, 1, 0]),
        ]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate_probe(json.dumps(good | {key: value}).encode(), name, 0)
        for code in (1, None, False, 0.0):
            with self.assertRaises(ValueError):
                m.validate_probe(json.dumps(good).encode(), name, code)
        with self.assertRaises(ValueError):
            m.validate_probe(json.dumps(good | {"extra": 1}).encode(), name, 0)

    def test_two_cases_and_five_fresh_cores(self):
        self.assertEqual(sum(m.expected(name)["fresh_cores"] for name in m.CASES), 5)
        for name in m.CASES:
            value = self.sample(name)
            self.assertEqual(m.validate(json.dumps(value).encode(), name, 0), value)
            self.assertFalse(value["native_acceptance_claimed_for_all_61_individual_rows"])

    def test_roundtrip_is_target_then_base_and_preserves_four_slots(self):
        value = self.sample(m.CASES[0])
        self.assertEqual([trace["species_after"] for trace in value["traces"]], [900, 749])
        self.assertEqual(value["moves"], [98, 235, 552, 33])
        self.assertEqual(value["pp"], [11, 3, 4, 7])
        self.assertEqual(value["pp_bonuses"], 229)
        self.assertEqual(value["automatic_saves"], 2)
        self.assertTrue(value["four_move_slots_preserved"])

    def test_party_cancel_is_not_success_or_mutation(self):
        value = self.sample(m.CASES[1])
        self.assertEqual(value["result"], 20)
        self.assertEqual(value["automatic_saves"], 0)
        self.assertEqual(value["selected_party_slot"], 6)
        self.assertEqual(value["final_species"], 749)
        bad = value | {"result": 0}
        with self.assertRaises(ValueError):
            m.validate(json.dumps(bad).encode(), m.CASES[1], 0)

    def test_wrong_owner_identity_menu_or_scope_is_rejected(self):
        good = self.sample(m.CASES[0])
        for key, value in [
            ("rom_sha256", "0" * 64),
            ("generic_owner_rows_sha256", "0" * 64),
            ("form_index", 37),
            ("eligible_ordinal", 5),
            ("menu_page", m.MAX_MENU_PAGES),
            ("menu_cursor", m.MENU_ROWS_PER_PAGE),
            ("probe_count", 1),
            ("pages_scanned", 1),
            ("menu_discovery", "flat-ordinal"),
            ("representative_route_ids", ["wrong"]),
            ("test_mode", True),
            ("release_ready", True),
            ("four_move_slots_preserved", False),
            ("generic_owner_representative_accepted", False),
        ]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate(json.dumps(good | {key: value}).encode(), m.CASES[0], 0)

    def test_native_menu_location_is_runtime_measured_and_bounded(self):
        value = self.sample(m.CASES[0])
        self.assertEqual(value["menu_discovery"], "input-only-native-menu-probe")
        self.assertEqual(value["probe_count"], 18)
        self.assertEqual(value["pages_scanned"], 4)
        self.assertEqual(m.validate(json.dumps(value).encode(), m.CASES[0], 0), value)
        for key, value in [
            ("menu_page", -1),
            ("menu_page", m.MAX_MENU_PAGES),
            ("menu_cursor", -1),
            ("menu_cursor", m.MENU_ROWS_PER_PAGE),
            ("probe_count", 17),
            ("pages_scanned", 3),
        ]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                m.validate(
                    json.dumps(self.sample(m.CASES[0]) | {key: value}).encode(),
                    m.CASES[0],
                    0,
                )

    def test_witness_order_and_species_are_fail_closed(self):
        good = self.sample(m.CASES[0])
        for round_index, trace in enumerate(good["traces"]):
            for key in m.TRACE:
                bad = self.sample(m.CASES[0])
                bad["traces"][round_index][key] = (
                    0 if key != "species_after"
                    else (749 if round_index == 0 else 900)
                )
                with self.subTest(round=round_index, key=key), self.assertRaises(ValueError):
                    m.validate(json.dumps(bad).encode(), m.CASES[0], 0)
        bad = self.sample(m.CASES[0])
        bad["traces"].reverse()
        with self.assertRaises(ValueError):
            m.validate(json.dumps(bad).encode(), m.CASES[0], 0)

    def test_controller_uses_paged_real_host_and_no_post_guard_writes(self):
        text = (ROOT / m.SOURCE).read_text()
        self.assertIn("b_position(c,1,36,6,4)", text)
        self.assertIn("#define M_MAX_PAGES 20U", text)
        self.assertIn("#define M_ROWS_PER_PAGE 5U", text)
        self.assertIn("pending==M_FORM_INDEX", text)
        self.assertIn("static void m_open_form_row", text)
        self.assertIn("static bool m_native_form_terminal", text)
        self.assertIn("if(++terminal_frames==12U)return false;", text)
        self.assertIn("generic form index absent before native terminal item", text)
        self.assertIn("read8(c,M_PARTY_SLOT)==1U", text)
        scan = text.split("static void m_find_form", 1)[1].split(
            "static struct MTrace m_service", 1
        )[0]
        self.assertIn("b_press(c,QOL_KEY_B,180U);b_wait(c);", scan)
        self.assertIn("m_open_form_row(c,page,cursor,prefix,round)", scan)
        self.assertIn("b_position(c,1U,36U,6U,4U)", scan)
        self.assertIn(
            'a_require(b_field(c),"generic form probe cancel did not return to idle field")',
            scan,
        )
        self.assertNotIn("probe-return-timeout", scan)
        self.assertNotIn("m_waitmenu(c,2U,page", scan)
        self.assertNotIn("#define M_PAGE ", text)
        self.assertNotIn("#define M_PAGE_CURSOR ", text)
        service = text.split("static struct MTrace m_service", 1)[1].split(
            "static void m_check", 1
        )[0]
        self.assertNotIn("b_data(", service)
        self.assertIn(
            "a_restore(c,&saved);traces[r].species_after=b_data(c,M_TARGET,11U);",
            text,
        )
        self.assertIn("a_guard(c);a_require(b_save(c)", text)
        self.assertIn("b_continue(c)", text)
        self.assertIn("call_preserving(c,QOL_FLAG_SET,QOL_FLAG_HALL_OF_FAME", text)
        self.assertIn("call_preserving(c,QOL_FLAG_CLEAR,QOL_FLAG_HALL_OF_FAME", text)
        for probe in m.PROBES:
            self.assertIn('{' + json.dumps(probe["name"]) + ',', text)

        probe_guarded = text.split(
            "/* Probe observation barrier: only GBA input and read-only observations. */", 1
        )[1].split("/* Probe observation complete. */", 1)[0]
        for forbidden in ("write8(", "write16(", "write32(",
                          "set_mon_data_u32(", "call_preserving("):
            self.assertNotIn(forbidden, probe_guarded)

        acceptance = text.split(
            "/* Acceptance fixture begins; diagnostics do not alter this path. */", 1
        )[1]
        before_guard, guarded = acceptance.split(
            "/* After this barrier, only GBA input and read-only observations. */", 1
        )
        hof_flag = before_guard.index(
            "call_preserving(c,QOL_FLAG_SET,QOL_FLAG_HALL_OF_FAME"
        )
        hof_mirror = before_guard.index(
            "write8(c,QOL_LEDGER+QOL_LEDGER_HALL_OF_FAME,1U)"
        )
        league_ii = before_guard.index(
            "write8(c,QOL_LEDGER+QOL_LEDGER_LEAGUE_II,1U)"
        )
        host_progress = before_guard.index("write8(c,QOL_LEDGER+0x73FU,1U)")
        host_load = before_guard.index(
            "call_preserving(c,0x09220861U,1U,36U,6U,4U)"
        )
        self.assertLess(hof_flag, hof_mirror)
        self.assertLess(hof_mirror, league_ii)
        self.assertLess(league_ii, host_progress)
        self.assertLess(host_progress, host_load)
        self.assertEqual(before_guard.count("call_preserving(c,QOL_SAVE_FINALIZE"), 1)
        self.assertEqual(
            before_guard.count("read8(c,QOL_LEDGER+QOL_LEDGER_LEAGUE_II)==1U"),
            2,
        )
        self.assertNotIn("write8(c,QOL_LEDGER+M_LEDGER_UNKNOWN_20,1U)", before_guard)
        for forbidden in ("write8(", "write16(", "write32(",
                          "set_mon_data_u32(", "call_preserving("):
            self.assertNotIn(forbidden, guarded)

    def test_noninteger_exit_duplicate_json_and_extra_keys_rejected(self):
        name = m.CASES[0]
        good = self.sample(name)
        for code in (1, None, False, 0.0):
            with self.assertRaises(ValueError):
                m.validate(json.dumps(good).encode(), name, code)
        for raw in (
            b"{}",
            b'{"a":1,"a":2}',
            json.dumps(good | {"total_frames": True}).encode(),
            json.dumps(good | {"extra": 1}).encode(),
        ):
            with self.assertRaises(ValueError):
                m.validate(raw, name, 0)


if __name__ == "__main__":
    unittest.main()
