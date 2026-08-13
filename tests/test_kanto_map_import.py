import csv
import io
import json
import unittest
from pathlib import Path

from tools.map_import.kanto_importer import IMPORTED_KEY, build_outputs, mainland_sources

ROOT = Path(__file__).resolve().parents[1]


class KantoMapImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build_outputs(ROOT)
        cls.canonical = json.loads(cls.outputs[f"generated/maps/{IMPORTED_KEY}.json"])

    def rows(self, path):
        return list(csv.DictReader(io.StringIO(self.outputs[path].decode())))

    def test_mainland_scope_and_safe_groups(self):
        self.assertEqual(len(mainland_sources(ROOT)), 256)
        rows = self.rows("reports/generated/kanto_map_inventory.csv")
        self.assertEqual({kind: sum(r["classification"] == kind for r in rows)
                          for kind in ("OUTDOOR", "DUNGEON", "INDOOR")},
                         {"OUTDOOR": 38, "DUNGEON": 96, "INDOOR": 122})
        self.assertTrue(all(int(r["map_id"]) < 127 for r in rows))
        self.assertTrue(all(int(r["group_id"]) not in range(43) for r in rows))
        self.assertEqual(len({(r["group_id"], r["map_id"]) for r in rows}), 256)
        imported = [r for r in rows if r["status"] == "IMPORTED"]
        self.assertEqual([r["map_key"] for r in imported], [IMPORTED_KEY])

    def test_clean_raw_assets_and_v2_crosswalk(self):
        rows = self.rows("reports/generated/kanto_map_inventory.csv")
        by_layout = {r["layout"]: r["raw_status"] for r in rows}
        self.assertEqual(len(by_layout), 180)
        self.assertEqual(sum(v == "MATCH" for v in by_layout.values()), 179)
        cross = self.rows("reports/generated/kanto_v2_crosswalk.csv")
        self.assertEqual(len(cross), 256)
        self.assertEqual({r["logical_code"] for r in cross}, {f"K{x:02d}" for x in range(1, 48)})
        self.assertTrue(all(r["layout"] and r["primary_tileset"] and r["secondary_tileset"] for r in cross))

    def test_vertical_slice_preserves_geometry_and_is_story_safe(self):
        item = self.canonical
        self.assertEqual((item["map_header"]["group_id"], item["map_header"]["map_id"]), (98, 0))
        self.assertEqual((item["layout"]["width"], item["layout"]["height"]), (11, 9))
        self.assertEqual((item["objects"][0]["x"], item["objects"][0]["y"]), (4, 5))
        self.assertEqual(len(item["warps"]), 3)
        self.assertTrue(all(w["dest_map"] == "KANTO_OUTDOOR_VERMILION_TERMINAL" for w in item["warps"]))
        self.assertEqual(item["safety"]["global_flags"], [])
        self.assertEqual(item["safety"]["global_vars"], [])
        raw = self.outputs[f"generated/maps/{IMPORTED_KEY}.json"].decode()
        self.assertNotIn("FLAG_GOT_OLD_ROD", raw)
        self.assertNotIn("VAR_RESULT", raw)

    def test_roundtrip_is_byte_identical(self):
        self.assertEqual(self.outputs[f"generated/maps/{IMPORTED_KEY}.json"],
                         self.outputs[f"generated/maps/{IMPORTED_KEY}.roundtrip.json"])


if __name__ == "__main__":
    unittest.main()
