from __future__ import annotations

import json
import struct
import unittest
from pathlib import Path

from scripts import build_move_distribution_v4 as builder


ROOT = Path(__file__).resolve().parents[1]


class MoveDistributionV4Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / builder.CONFIG).read_text(encoding="utf-8"))
        cls.outputs = builder.build_outputs()
        cls.metadata = json.loads(cls.outputs[cls.config["outputs"]["metadata"]])
        cls.audit = json.loads(cls.outputs[builder.OUTPUT_AUDIT.as_posix()])
        cls.coverage = json.loads(cls.outputs[builder.OUTPUT_COVERAGE.as_posix()])
        cls.rom = cls.outputs[cls.config["outputs"]["rom"]]

    def test_fixed_input_and_canonical_counts(self) -> None:
        self.assertEqual(self.metadata["submission"]["validator_status"], "PASS")
        self.assertEqual(self.metadata["submission"]["entry_count"], 11)
        self.assertEqual(
            self.metadata["content"],
            {
                "level_up_rows": 28274,
                "egg_rows": 8219,
                "tm_tutor_changes": 2799,
                "form_rows": 509,
                "wild_rows": 1206,
                "source_rows": 1206,
            },
        )
        self.assertEqual(self.metadata["normalization"]["unresolved_references"], 0)
        self.assertEqual(self.metadata["normalization"]["duplicate_rows"], 0)
        self.assertEqual(self.metadata["normalization"]["egg_sentinel_id"], 412)

    def test_stage38_tables_are_rooted_and_exact(self) -> None:
        baseline = self.audit["stage38_root_audit"]["baseline"]
        self.assertTrue(baseline["stage37_packet_exact"])
        self.assertEqual(baseline["level_rows"], 25674)
        self.assertEqual(baseline["egg_rows"], 6851)
        self.assertEqual(baseline["compatibility_rows"], 1621)

    def test_production_roots_and_scoped_hooks(self) -> None:
        rows = self.metadata["consumer_bindings"]["rows"]
        self.assertEqual(len(rows), 10)
        self.assertEqual(
            {row["name"] for row in rows if row["kind"] == "TABLE_ROOT"},
            {
                "root::level_up",
                "root::level_up_runtime_literal",
                "root::egg",
                "root::tmhm",
                "root::tutor",
            },
        )
        self.assertEqual(
            {row["name"] for row in rows if row["name"].startswith("hook::wild_")},
            {"hook::wild_land_water", "hook::wild_fishing", "hook::wild_hidden"},
        )
        self.assertEqual(
            {row["name"] for row in rows if row["kind"] == "THUMB_INSTRUCTION"},
            {"instruction::tutor_stride_16"},
        )
        for row in rows:
            offset = int(row["offset"])
            replacement = bytes.fromhex(row["replacement_hex"])
            self.assertEqual(self.rom[offset:offset + len(replacement)], replacement)

    def test_table_roots_point_to_declared_runtime_tables(self) -> None:
        tables = self.metadata["runtime"]["tables"]
        expected = {
            0x0804346C: tables["level_up_pointers"]["address"],
            0x09FDA1F8: tables["level_up_pointers"]["address"],
            0x08045214: tables["egg_moves"]["address"],
            0x080432B4: tables["tmhm"]["address"],
            0x08121420: tables["tutor"]["address"],
        }
        for address, target in expected.items():
            offset = address - 0x08000000
            self.assertEqual(struct.unpack_from("<I", self.rom, offset)[0], target)
        self.assertEqual(tables["tmhm"]["size"], 1621 * 16)
        self.assertEqual(tables["tutor"]["size"], 1621 * 16)
        self.assertEqual(tables["wild_table"]["size"], 1621 * 8)
        self.assertEqual(tables["form_table"]["size"], 509 * 14)

    def test_additive_and_scope_guards(self) -> None:
        self.assertEqual(self.audit["tm_tutor"]["additions"], 2799)
        self.assertEqual(self.audit["tm_tutor"]["removed_bits"], 0)
        self.assertEqual(self.audit["tm_tutor"]["non_0_to_1"], 0)
        scope = self.audit["wild_scope"]
        self.assertEqual(scope["application"], "NEW_WILD_GENERATION_ONLY")
        self.assertFalse(scope["existing_save_rewrite"])
        for key in (
            "trainer_hook_count", "factory_hook_count", "mirage_hook_count",
            "raid_hook_count", "reward_hook_count",
        ):
            self.assertEqual(scope[key], 0)

    def test_declared_spans_and_upstream_regression(self) -> None:
        change = self.metadata["change_audit"]
        self.assertEqual(change["outside_declared_span_count"], 0)
        self.assertEqual(change["declared_span_overlap_count"], 0)
        self.assertEqual(self.metadata["overlap_audit"], {
            "rom": 0, "ram": 0, "save": 0, "hook": 0,
        })
        regression = self.metadata["upstream_regression"]
        self.assertEqual(regression["previous_allocations_changed_outside_consumer_patches"], 0)
        self.assertEqual(regression["trainer_battle_count"], 1302)
        self.assertEqual(regression["qol_feature_count"], 35)
        self.assertEqual(regression["event_count"], 76)
        self.assertEqual(regression["mirage_battle_count"], 28)

    def test_private_submission_is_not_copied_to_tracked_content(self) -> None:
        files = sorted(
            path.name for path in (ROOT / "content/move_distribution_v4").iterdir()
            if path.is_file()
        )
        self.assertEqual(files, ["PROVENANCE_JA.md", "consumer_contract.json"])
        self.assertFalse(any(name.endswith(".csv") for name in files))


if __name__ == "__main__":
    unittest.main()
