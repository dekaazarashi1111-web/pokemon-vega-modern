"""フォーム技術準備の新scopeだけを検査。既受入nativeを再実行しない。"""
from __future__ import annotations
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "scripts/pr16_form_readiness.py"
spec = importlib.util.spec_from_file_location("pr16_form_readiness", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.wiki = self.root / m.WIKI
        self.wiki.mkdir(parents=True)
        doc = "固定レビュー版 R0 " + m.REVIEW_ID + "\n全機能の新native受入ではありません\n"
        mega = []
        for i in range(76):
            target = 1000 if i == 75 else i + 1000
            mega.append(f"| [{i}](pokemon/{i}.md) | [m](mega/{i}-{target}.md) | [stone](items/{i}.md) |")
        gmax = [f"| [{i}](pokemon/{i}.md) | [g](gmax/{i}.md) | 個別body・native未監査 |"
                for i in range(1441, 1475)]
        z = [f"| [{i}](pokemon/{i}.md) | [stone](items/{i}.md) | [move](moves/{i}.md) | [z](z/{i}.md) |"
             for i in range(31)]
        for category, rows in (("mega", mega), ("gmax", gmax), ("exclusive_z", z)):
            (self.root / m.FILES[category]).write_text(doc + "\n".join(rows) + "\n", encoding="utf-8")
        for name, payload in {
            "mega": {
                "native_mega_turn_revert_cold_save_cases": list("abcdef"),
                "closed_scope": ["36_nonactivation_controls"],
                "nonactivation_controls_per_species": list(range(6)),
                "full_p05_acceptance": False, "release_ready": False,
            },
            "fixed_form": {
                "originals": [{"selected_successful_cases": ["1", "2"]},
                              {"selected_successful_cases": ["3", "4", "5"]}],
                "p03_fixed_form_gap_closed": True, "full_p03_acceptance": False,
                "release_ready": False,
            },
            "generic_form": {
                "accepted_scope": {"generic_owner_route_count": 61,
                                   "all_61_rows_individually_executed": False,
                                   "representative_native_acceptance": True},
                "generic_form_carry_physical_accepted": True,
                "full_p03_acceptance": False, "release_ready": False,
            },
        }.items():
            path = self.root / m.RECEIPTS[name]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload), encoding="utf-8")

    def edit(self, path, old, new):
        file = self.root / path
        data = file.read_text(encoding="utf-8")
        self.assertIn(old, data)
        file.write_text(data.replace(old, new, 1), encoding="utf-8")

    def test_scoped_report_only(self):
        r = m.inspect(self.root)
        self.assertEqual(r["r0_review_registration"]["gmax_rows"], 34)
        self.assertEqual(r["r0_review_registration"]["mega_distinct_target_forms"], 75)
        self.assertEqual(r["inherited_accepted_original_scopes"]["fixed_form_native_cases"], 5)
        self.assertFalse(r["release_ready"])
        self.assertIn("gmax_individual_body_palette_effect_and_native_path", r["not_proven_by_this_audit"])

    def test_missing_gmax_unaccepted_marker_fails(self):
        self.edit(m.FILES["gmax"], "個別body・native未監査", "native PASS")
        with self.assertRaisesRegex(ValueError, "gmax"):
            m.inspect(self.root)

    def test_mega_duplicate_row_fails(self):
        self.edit(m.FILES["mega"], "(mega/2-1002.md)", "(mega/1-1001.md)")
        with self.assertRaisesRegex(ValueError, "mega inverse"):
            m.inspect(self.root)

    def test_missing_z_key_fails(self):
        self.edit(m.FILES["exclusive_z"], "(z/30.md)", "(z/29.md)")
        with self.assertRaisesRegex(ValueError, "exclusive Z"):
            m.inspect(self.root)

    def test_old_mega_full_p05_overclaim_rejected(self):
        p = self.root / m.RECEIPTS["mega"]
        o = json.loads(p.read_text())
        o["full_p05_acceptance"] = True
        p.write_text(json.dumps(o))
        with self.assertRaisesRegex(ValueError, "old mega"):
            m.inspect(self.root)

    def test_old_fixed_form_duplicate_rejected(self):
        p = self.root / m.RECEIPTS["fixed_form"]
        o = json.loads(p.read_text())
        o["originals"][1]["selected_successful_cases"][0] = "2"
        p.write_text(json.dumps(o))
        with self.assertRaisesRegex(ValueError, "fixed-form"):
            m.inspect(self.root)

    def test_generic_61_not_full_native(self):
        p = self.root / m.RECEIPTS["generic_form"]
        o = json.loads(p.read_text())
        o["accepted_scope"]["all_61_rows_individually_executed"] = True
        p.write_text(json.dumps(o))
        with self.assertRaisesRegex(ValueError, "generic-form"):
            m.inspect(self.root)

    def test_missing_receipt_rejected(self):
        (self.root / m.RECEIPTS["mega"]).unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            m.inspect(self.root)

    def test_check_is_read_only(self):
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in self.root.rglob("*") if p.is_file()}
        m.inspect(self.root)
        after = {p.relative_to(self.root): p.read_bytes()
                 for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
