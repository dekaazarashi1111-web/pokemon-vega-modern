import csv
import hashlib
import json
import struct
import unittest
from pathlib import Path

from scripts.build_trainer_rebalance_v4 import (
    GBA_ROM_BASE,
    STAGE19,
    STAGE19_META,
    build_outputs,
)


ROOT = Path(__file__).resolve().parents[1]


class TrainerRebalanceV4Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build_outputs(ROOT)
        cls.rom = cls.outputs[STAGE19.as_posix()]
        cls.meta = json.loads(cls.outputs[STAGE19_META.as_posix()])
        cls.stage17 = (ROOT / "build/stages/17_regression.gba").read_bytes()
        cls.normalized = list(csv.DictReader(
            cls.outputs["reports/generated/trainer_rebalance_v4.csv"].decode("utf-8").splitlines()
        ))

    def test_source_and_allocator_contract(self):
        self.assertEqual(self.meta["source"]["battle_count"], 141)
        self.assertEqual(self.meta["source"]["party_row_count"], 610)
        self.assertEqual(len(self.normalized), 610)
        self.assertEqual(len(self.rom), 32 * 1024 * 1024)
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(), self.meta["output"]["sha256"])
        self.assertEqual(self.meta["allocation"]["overlap_count"], 0)
        self.assertTrue(all(self.meta["invariants"].values()))

    def test_ai_ranks_reuse_only_fixed_cfru_stages(self):
        self.assertEqual(
            self.meta["ai"]["rank_to_flags"],
            {"1": 1, "2": 3, "3": 3, "4": 5, "5": 5},
        )
        self.assertFalse(self.meta["ai"]["custom_ai_added"])
        self.assertEqual(
            {row["ai_flags"] for row in self.meta["bindings"]["rows"]},
            {1, 3, 5},
        )

    def test_representative_story_records_use_real_rom_party_pointers(self):
        by_id = {row["trainer_id"]: row for row in self.meta["bindings"]["rows"]}
        expected = {
            326: ("RIVAL01_PLAYER_FAMER", 1, 1),
            414: ("GYM01_AMANA", 4, 3),
            438: ("CHAMPION_GINNO", 6, 5),
            704: ("GYM_RF_AMANA", 6, 5),
            735: ("LEAGUE_FINAL_HOONOKI", 6, 5),
        }
        table = self.meta["trainer_table"]["address"] - GBA_ROM_BASE
        payload_start = self.meta["payload"]["address"]
        payload_end = payload_start + self.meta["payload"]["size"]
        for trainer_id, (battle_id, size, ai_flags) in expected.items():
            row = by_id[trainer_id]
            self.assertEqual(row["battle_id"], battle_id)
            record = table + trainer_id * 0x20
            self.assertEqual(self.rom[record], 3)
            self.assertEqual(self.rom[record + 0x18], size)
            self.assertEqual(struct.unpack_from("<I", self.rom, record + 0x14)[0], ai_flags)
            pointer = struct.unpack_from("<I", self.rom, record + 0x1C)[0]
            self.assertGreaterEqual(pointer, payload_start)
            self.assertLess(pointer, payload_end)

    def test_form_aliases_and_vega_pre_evolutions_are_exact(self):
        by_key = {(row["battle_id"], int(row["party_slot"])): row for row in self.normalized}
        self.assertEqual(
            by_key[("RIVAL02_PLAYER_FAMER", 3)]["species_key"],
            "SPECIES_KEY_VEGA_008",
        )
        self.assertEqual(
            by_key[("MOS_RIVAL_TAG_PLAYER_ACTASHI", 5)]["species_key"],
            "SPECIES_KEY_VEGA_050",
        )
        self.assertEqual(
            by_key[("GYM_RF_HANZA", 4)]["species_key"],
            "SPECIES_KEY_URSALUNA_BLOODMOON",
        )

    def test_facility_rows_are_not_generically_overwritten(self):
        table = self.meta["trainer_table"]["address"] - GBA_ROM_BASE
        for trainer_id in (616, 688, 699, 700):
            start = table + trainer_id * 0x20
            self.assertEqual(self.rom[start:start + 0x20], self.stage17[start:start + 0x20])


if __name__ == "__main__":
    unittest.main()
