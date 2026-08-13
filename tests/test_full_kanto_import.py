import csv
import io
import json
import unittest
from pathlib import Path

from tools.map_import.full_kanto_import import (ALLOCATION_END, ALLOCATION_START,
                                                DEFERRED_SOURCES, build_outputs)

ROOT = Path(__file__).resolve().parents[1]


class FullKantoImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build_outputs(ROOT)
        cls.index = json.loads(cls.outputs["generated/maps/kanto/index.json"])
        cls.scope = list(csv.DictReader(io.StringIO(cls.outputs["content/kanto_map_scope.csv"].decode())))

    def test_scope_and_reachability(self):
        self.assertEqual(len(self.scope), 256)
        self.assertEqual(self.index["scope_counts"], {"DEFER": 3, "INCLUDE": 252, "REBUILD": 1})
        self.assertEqual(self.index["maps"], 253)
        self.assertEqual(self.index["reachable"], 253)
        self.assertEqual({r["source_map"] for r in self.scope if r["scope_decision"] == "DEFER"},
                         DEFERRED_SOURCES)

    def test_every_logical_location_and_namespace(self):
        self.assertEqual(self.index["logical_locations"], 47)
        maps = [json.loads(raw) for path, raw in self.outputs.items()
                if path.startswith("generated/maps/kanto/KANTO_")]
        ids = [(m["map_header"]["group_id"], m["map_header"]["map_id"]) for m in maps]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(group in (96, 97, 98) and map_id < 127 for group, map_id in ids))
        self.assertTrue(all(not m["scripts"]["vega_flag_writes"] for m in maps))

    def test_references_and_one_way_policy(self):
        self.assertEqual(self.index["one_way_unexpected"], 0)
        self.assertGreater(self.index["one_way_intentional"], 0)
        self.assertIn(b"unresolved warp destinations: 0", self.outputs["reports/generated/kanto_connectivity.md"])
        self.assertIn(b"accidental Vega destinations: 0", self.outputs["reports/generated/kanto_connectivity.md"])

    def test_allocation_is_non_overlapping(self):
        self.assertEqual(self.index["allocation_start"], ALLOCATION_START)
        self.assertLessEqual(self.index["allocation_end"], ALLOCATION_END)
        self.assertEqual(self.index["overlap"], 0)
        self.assertEqual(self.index["vega_writes"], 0)


if __name__ == "__main__":
    unittest.main()
