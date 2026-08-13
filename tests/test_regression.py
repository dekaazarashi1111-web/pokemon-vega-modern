import hashlib
import json
import struct
import unittest
from pathlib import Path

from tools.regression.model import build_outputs as build_model_outputs
from tools.regression.rom_runtime import (
    GBA_ROM_BASE,
    STAGE17,
    STAGE17_META,
    build_runtime_outputs,
)


ROOT = Path(__file__).resolve().parents[1]


class RegressionReleaseCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build_runtime_outputs(ROOT)
        cls.rom = cls.outputs[STAGE17.as_posix()]
        cls.meta = json.loads(cls.outputs[STAGE17_META.as_posix()])

    def test_exact_rom_payload_and_invariants(self):
        self.assertEqual(len(self.rom), 32 * 1024 * 1024)
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(), self.meta["output"]["sha256"])
        start = self.meta["payload"]["offset"]
        size = self.meta["payload"]["size"]
        self.assertEqual(
            hashlib.sha256(self.rom[start:start + size]).hexdigest(),
            self.meta["payload"]["sha256"],
        )
        self.assertTrue(all(self.meta["invariants"].values()))
        self.assertEqual(self.meta["allocation"]["overlap_count"], 0)

    def test_generated_trainers_are_bound_to_engine_abi(self):
        trainer = self.meta["trainers"]
        self.assertEqual(trainer["generated_trainers"], 29)
        self.assertEqual(trainer["production_rows_bound"], 174)
        self.assertEqual(trainer["repoint_count"], 24)
        root = trainer["address"] - GBA_ROM_BASE
        for trainer_id in (751, 763):
            record = root + trainer_id * trainer["record_size"]
            self.assertEqual(self.rom[record], 3)
            self.assertEqual(self.rom[record + 0x18], 6)
            self.assertEqual(struct.unpack_from("<I", self.rom, record + 0x14)[0], 5)
            party = struct.unpack_from("<I", self.rom, record + 0x1C)[0]
            self.assertGreaterEqual(party, GBA_ROM_BASE)
            self.assertLess(party, GBA_ROM_BASE + len(self.rom))

    def test_kanto_progression_is_physical_and_ordered(self):
        progression = self.meta["progression"]
        self.assertEqual(progression["physical_battle_objects"], 13)
        self.assertEqual(len(progression["certification_flags"]), 8)
        self.assertEqual(len(progression["league_flags"]), 5)
        self.assertEqual(progression["final_objective_flag"], 0x140C)
        self.assertIn("progress::PewterCity_Gym", self.meta["symbols"])
        self.assertIn("progress::PokemonLeague_ChampionsRoom", self.meta["symbols"])

    def test_regression_model_matches_generated_artifacts(self):
        mgba = json.loads((ROOT / "build/stages/17_mgba_smoke.json").read_text())
        qol = json.loads((ROOT / "tests/fixtures/qol_b.json").read_text())
        outputs = build_model_outputs(ROOT, self.meta, mgba, qol)
        for relative, raw in outputs.items():
            self.assertEqual((ROOT / relative).read_bytes(), raw, relative)
        fixture = json.loads(outputs["tests/fixtures/regression.json"])
        self.assertEqual(fixture["status"], "PASS")
        self.assertEqual(fixture["round_trips"]["total"], 400)
        self.assertEqual(fixture["maps"]["reachable_from_vermilion"], 253)
        self.assertEqual(fixture["shared_captures"]["shared_keys"], 125)
        self.assertEqual(fixture["events"]["branch_cases"], 238)


if __name__ == "__main__":
    unittest.main()
