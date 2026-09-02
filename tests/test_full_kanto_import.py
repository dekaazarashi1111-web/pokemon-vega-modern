import csv
import copy
import io
import json
import unittest
from pathlib import Path

from tools.map_import.full_kanto_import import (
    ALLOCATION_END,
    ALLOCATION_START,
    COORD_PRODUCER_ROLE,
    DEFERRED_PRODUCER_POLICY,
    DEFERRED_SOURCES,
    TOPOLOGY_PRODUCER_ROLE,
    build_outputs,
)
from tools.regression.rom_runtime import (
    RuntimeBuildError,
    _validate_canonical_event_evidence,
)

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

    def test_source_event_producers_are_preserved_and_explicitly_deferred(self):
        maps = [json.loads(raw) for path, raw in self.outputs.items()
                if path.startswith("generated/maps/kanto/KANTO_")]
        topology = [event for item in maps for event in item["objects"]
                    if event["source_role"] == TOPOLOGY_PRODUCER_ROLE]
        coords = [event for item in maps for event in item["coord_events"]]
        overloaded = [event for event in topology
                      if event["source_evidence"]["trainer_type_overloaded"]]
        self.assertEqual(len(topology), 25)
        self.assertEqual(len(overloaded), 9)
        self.assertEqual(len(coords), 159)
        self.assertTrue(all(event["runtime_policy"] == DEFERRED_PRODUCER_POLICY
                            for event in topology))
        self.assertTrue(all(event["source_role"] == COORD_PRODUCER_ROLE
                            and event["runtime_policy"] == DEFERRED_PRODUCER_POLICY
                            for event in coords))

        seafoam = next(item for item in maps
                       if item["map_header"]["source_map"] == "SeafoamIslands_1F")
        evidence = seafoam["objects"][0]["source_evidence"]
        self.assertEqual(evidence["trainer_type"], "FLAG_HIDE_SEAFOAM_B1F_BOULDER_1")
        self.assertEqual(evidence["trainer_type_semantics"], "DESTINATION_REVEAL_FLAG")
        self.assertTrue(evidence["trainer_type_overloaded"])
        self.assertEqual(evidence["script"], "EventScript_StrengthBoulder")
        self.assertEqual(evidence["flag"], "FLAG_HIDE_SEAFOAM_1F_BOULDER_1")

    def test_runtime_contract_rejects_silent_object_or_coord_evidence_loss(self):
        victory_path = "generated/maps/kanto/KANTO_DUNGEON_VICTORY_ROAD_3_F.json"
        canonical = json.loads(self.outputs[victory_path])
        _validate_canonical_event_evidence(ROOT, canonical)

        object_loss = copy.deepcopy(canonical)
        object_loss["objects"][7]["source_evidence"]["trainer_type"] = "TRAINER_TYPE_NONE"
        with self.assertRaisesRegex(RuntimeBuildError, "trainer/script/flag evidence"):
            _validate_canonical_event_evidence(ROOT, object_loss)

        coord_loss = copy.deepcopy(canonical)
        coord_loss["coord_events"].clear()
        with self.assertRaisesRegex(RuntimeBuildError, "coord producer count"):
            _validate_canonical_event_evidence(ROOT, coord_loss)


if __name__ == "__main__":
    unittest.main()
