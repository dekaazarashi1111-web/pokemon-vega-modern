"""保存証拠だけを使うIPS/DPE有限境界の独立回帰。既受入profileは再走しない。"""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pr16_selected_ips_dpe_frontier as m


class IpsDpeFrontierTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provenance = m.read_json(m.PROVENANCE)
        cls.xrefs = m.read_json(m.XREFS)
        cls.source = (ROOT / m.DPE_SOURCE).read_text(encoding="utf-8")
        cls.state = m.read_json(m.STATE)

    def run_bound(self, p=None, x=None, src=None, s=None):
        return m.bound(p if p is not None else self.provenance,
                       x if x is not None else self.xrefs,
                       src if src is not None else self.source,
                       s if s is not None else self.state)

    def test_exact_ips_interval_and_tail(self):
        r = self.run_bound()
        self.assertEqual((r["ips"]["write_start"], r["ips"]["write_end_exclusive"]),
                         (0x0880B7B0, 0x0880FAD0))
        self.assertEqual((r["ips"]["target_offset"], r["ips"]["bytes_after_target"]),
                         (17076, 104))
        self.assertFalse(r["ips"]["caller_proven"])

    def test_all_saved_pointers_and_no_automatic_readers(self):
        r = self.run_bound()
        self.assertEqual(r["saved_first_level_count"], 11)
        self.assertTrue(all(not x["instruction_reader_proven"]
                            for x in r["saved_first_level_refs_inside_ips_record"]))
        self.assertEqual([x["target"] for x in r["saved_first_level_refs_inside_ips_record"]
                          if x["origin"] == m.DPE_POINTER], [0x0880EFD0])

    def test_dpe_envelope_not_live_owner(self):
        d = self.run_bound()["dpe"]
        self.assertEqual((d["envelope_start"], d["envelope_end_exclusive"],
                          d["offset_from_envelope_start"]),
                         (0x09600000, 0x0A000000, 0x73660))
        self.assertFalse(d["output_blob_extent_proven"])
        self.assertFalse(d["real_owner_proven"])
        self.assertFalse(d["free_space_proven"])

    def test_formal_counts_stable(self):
        r = self.run_bound()
        self.assertEqual([r[k] for k in ("formal_classified", "formal_unclassified",
                         "selected_unknown_origins", "donor_safe_bytes")], [789, 85, 6, 0])

    def test_reject_1byte_outside_write(self):
        p = copy.deepcopy(self.provenance)
        row = next(x for x in p["rows"] if x["address"] == m.ORIGIN)
        row["ips"]["overlapping_records"][0]["end_exclusive"] = 0x80FA66
        with self.assertRaises(ValueError):
            self.run_bound(p=p)

    def test_reject_unverified_replacement_writer(self):
        p = copy.deepcopy(self.provenance)
        row = next(x for x in p["rows"] if x["address"] == m.ORIGIN)
        row["ips"]["last_writer_indices"][3] = 11872
        with self.assertRaises(ValueError):
            self.run_bound(p=p)

    def test_reject_pointer_outside_write(self):
        x = copy.deepcopy(self.xrefs)
        x["first_level"][0]["canonical_target"] = 0x0880B7AF
        with self.assertRaises(ValueError):
            self.run_bound(x=x)

    def test_reject_implicit_dpe_ownership(self):
        p = copy.deepcopy(self.provenance)
        next(x for x in p["rows"] if x["address"] == m.DPE_POINTER)["modernization"]["fully_owned"] = True
        with self.assertRaises(ValueError):
            self.run_bound(p=p)

    def test_reject_free_space_assumption(self):
        p = copy.deepcopy(self.provenance)
        next(x for x in p["rows"] if x["address"] == m.DPE_POINTER)["modernization"]["free_space_proven"] = True
        with self.assertRaises(ValueError):
            self.run_bound(p=p)

    def test_reject_changed_dpe_offset(self):
        with self.assertRaises(ValueError):
            self.run_bound(src=self.source.replace("DPE_OFFSET = 0x1600000", "DPE_OFFSET = 0x1700000"))

    def test_reject_unaccepted_formal_progress(self):
        s = copy.deepcopy(self.state)
        s["owner_execution_plan"]["technical_lanes"]["save_capacity"]["donor_safe_bytes"] = 6528
        with self.assertRaises(ValueError):
            self.run_bound(s=s)

    def test_reject_missing_pointer(self):
        x = copy.deepcopy(self.xrefs)
        x["first_level"] = [r for r in x["first_level"] if r["address"] != m.DPE_POINTER]
        x["first_level_count"] = 10
        with self.assertRaises(ValueError):
            self.run_bound(x=x)


if __name__ == "__main__":
    unittest.main()
