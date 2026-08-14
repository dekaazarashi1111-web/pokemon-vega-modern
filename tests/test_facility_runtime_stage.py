import hashlib
import json
import struct
import unittest
from pathlib import Path

from scripts.build_facility_runtime import (
    GBA_ROM_BASE,
    REQUIRED_ENTRYPOINTS,
    STAGE20,
    STAGE20_META,
    build_runtime_outputs,
)


ROOT = Path(__file__).resolve().parents[1]


class FacilityRuntimeStageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build_runtime_outputs(ROOT)
        cls.rom = cls.outputs[STAGE20.as_posix()]
        cls.meta = json.loads(cls.outputs[STAGE20_META.as_posix()])

    def test_stage_identity_allocator_and_contract(self):
        self.assertEqual(len(self.rom), 32 * 1024 * 1024)
        self.assertEqual(
            hashlib.sha256(self.rom).hexdigest(),
            self.meta["output"]["sha256"],
        )
        self.assertEqual(self.meta["allocation"]["overlap_count"], 0)
        self.assertTrue(all(self.meta["invariants"].values()))
        self.assertEqual(self.meta["contract"]["random_candidates"], 6)
        self.assertEqual(self.meta["contract"]["manual_selections"], 3)
        self.assertEqual(self.meta["contract"]["battle_count"], 3)
        self.assertEqual(self.meta["contract"]["exact_party_snapshot_bytes"], 600)

    def test_all_thumb_entrypoints_are_inside_payload(self):
        self.assertEqual(set(self.meta["entrypoints"]), REQUIRED_ENTRYPOINTS)
        start = self.meta["payload"]["address"]
        end = start + self.meta["payload"]["size"]
        for name, address in self.meta["entrypoints"].items():
            with self.subTest(name=name):
                self.assertEqual(address & 1, 1)
                self.assertGreaterEqual(address & ~1, start)
                self.assertLess(address & ~1, end)

    def test_vermilion_object_and_recovery_script_are_physical(self):
        header = self.meta["map"]["header_offset"]
        events = struct.unpack_from("<I", self.rom, header + 4)[0]
        scripts = struct.unpack_from("<I", self.rom, header + 8)[0]
        self.assertEqual(events, self.meta["symbols"]["facility_vermilion_events"])
        self.assertEqual(scripts, self.meta["symbols"]["facility_vermilion_map_scripts"])
        event_offset = events - GBA_ROM_BASE
        objects = struct.unpack_from("<I", self.rom, event_offset + 4)[0]
        object_offset = objects - GBA_ROM_BASE + 0x18
        self.assertEqual(self.rom[event_offset], 2)
        self.assertEqual(self.rom[object_offset], 2)
        self.assertEqual(struct.unpack_from("<HH", self.rom, object_offset + 4), (20, 19))
        self.assertEqual(
            struct.unpack_from("<I", self.rom, object_offset + 0x10)[0],
            self.meta["scripts"]["npc_address"],
        )
        scripts_offset = scripts - GBA_ROM_BASE
        self.assertEqual(self.rom[scripts_offset], 3)
        recovery = struct.unpack_from("<I", self.rom, scripts_offset + 1)[0]
        recovery_offset = recovery - GBA_ROM_BASE
        self.assertEqual(self.rom[recovery_offset], 0x23)
        self.assertEqual(self.rom[recovery_offset + 5], 0x02)

    def test_published_exact_rom_smoke_covers_playable_trial(self):
        smoke = json.loads((ROOT / "build/stages/20_mgba_smoke.json").read_text())
        self.assertEqual(smoke["status"], "PASS")
        self.assertEqual(smoke["process_runs"], 2)
        self.assertEqual(smoke["rom_sha256"], self.meta["output"]["sha256"])
        required = {
            "random_six_unique",
            "manual_select_three",
            "cfru_policy_pending",
            "win_exchange",
            "exact_restore_all_exits",
            "seen_only",
            "reward_and_streak",
            "physical_npc_and_recovery_script",
            "save_sector_round_trip",
        }
        self.assertTrue(required.issubset(smoke["checks"]))
        self.assertTrue(all(smoke["checks"][key] for key in required))


if __name__ == "__main__":
    unittest.main()
