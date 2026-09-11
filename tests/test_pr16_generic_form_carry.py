"""Fail-closed metadata tests; native acceptance occurs only in mGBA Actions."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pr16_generic_form_carry as m


class GenericFormCarryTests(unittest.TestCase):
    def sample(self, name):
        out = m.expected(name)
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
            }
            out["traces"].append(trace)
        return out

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
            ("menu_page", 0),
            ("menu_cursor", 0),
            ("representative_route_ids", ["wrong"]),
            ("test_mode", True),
            ("release_ready", True),
            ("four_move_slots_preserved", False),
            ("generic_owner_representative_accepted", False),
        ]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate(json.dumps(good | {key: value}).encode(), m.CASES[0], 0)

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
        self.assertIn("read8(c,M_CURSOR)==5U", text)
        self.assertIn("m_waitmenu(c,2U,M_PAGE", text)
        self.assertIn("read16(c,M_STATE+10U)==M_FORM_INDEX", text)
        self.assertIn("read8(c,M_PARTY_SLOT)==1U", text)
        self.assertIn("a_guard(c);a_require(b_save(c)", text)
        self.assertIn("b_continue(c)", text)
        guarded = text.split("/* After this barrier, only GBA input and read-only observations. */", 1)[1]
        for forbidden in ("write8(", "write16(", "write32(", "set_mon_data_u32(", "call_preserving("):
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
