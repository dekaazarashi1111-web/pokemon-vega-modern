import hashlib
import json
import struct
import unittest
from pathlib import Path

from tools.release.bps import apply_bps
from tools.trainer_final.kanto_events import _stage_map_state


ROOT = Path(__file__).resolve().parents[1]


class WorldItemRecoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (ROOT / "build/stages/49_world_item_recovery.gba").read_bytes()
        cls.stage48 = (ROOT / "build/stages/48_species_form_backsprite_compat.gba").read_bytes()
        cls.clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        cls.meta = json.loads((ROOT / "build/stages/49_world_item_recovery.json").read_text())

    def test_exact_rom_and_bps_round_trips(self):
        self.assertEqual(len(self.rom), 32 * 1024 * 1024)
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(),
                         self.meta["output"]["sha256"])
        incremental = (ROOT / self.meta["bps"]["incremental"]["path"]).read_bytes()
        direct = (ROOT / self.meta["bps"]["clean"]["path"]).read_bytes()
        self.assertEqual(apply_bps(self.stage48, incremental), self.rom)
        self.assertEqual(apply_bps(self.clean, direct), self.rom)

    def test_world_services_and_map_graph(self):
        restored = self.meta["restored"]
        self.assertEqual(restored["nurses"], 12)
        self.assertGreaterEqual(restored["mart_clerks"], 8)
        self.assertGreaterEqual(restored["civilian_objects"], 650)
        self.assertGreaterEqual(restored["signs"], 350)
        self.assertEqual(restored["trash_events"], 15)
        self.assertEqual(restored["low_raid_hosts"], 6)
        self.assertEqual(self.meta["map_audit"]["total_maps"], 678)
        self.assertEqual(_stage_map_state(self.rom, 96, 5)["counts"]["objects"], 11)
        self.assertEqual(_stage_map_state(self.rom, 3, 21)["counts"]["objects"], 16)
        self.assertEqual(_stage_map_state(self.rom, 3, 21)["counts"]["bg"], 3)
        self.assertEqual(self.meta["physical_binding"]["representatives"], {
            "T501": [3, 19], "T511": [3, 29], "T523": [3, 38],
        })
        wild_patch = next(row for row in self.meta["runtime_patches"]
                          if row["name"].startswith("Tohoku exact"))
        self.assertNotEqual(wild_patch["expected_sha256"],
                            wild_patch["replacement_sha256"])

    def test_item_trainer_and_mgba_contracts(self):
        sash = self.meta["item_abi"]["selected"]["ITEM_KEY_FOCUS_SASH"]
        self.assertEqual(sash, {"id": 897, "hold_effect": 39,
                               "hold_effect_param": 100,
                               "mystery2": 1, "secondary_id": 0})
        self.assertEqual(self.meta["trainer_audit"]["encounters"], 1302)
        self.assertEqual(self.meta["trainer_audit"]["shinichi"]["target_trainer_id"], 299)
        self.assertTrue(all(self.meta["mgba"]["checks"].values()))
        self.assertEqual(self.meta["mgba"]["process_runs"], 2)

    def test_all_rebuilt_object_scripts_are_live(self):
        for row in self.meta["map_patches"]:
            state = _stage_map_state(self.rom, int(row["group"]), int(row["map"]))
            local_ids = [raw[0] for raw in state["objects"]]
            self.assertEqual(len(local_ids), len(set(local_ids)))
            for raw in state["objects"]:
                pointer = struct.unpack_from("<I", raw, 0x10)[0] & ~1
                self.assertGreaterEqual(pointer, 0x08000000)
                self.assertLess(pointer, 0x0A000000)


if __name__ == "__main__":
    unittest.main()
