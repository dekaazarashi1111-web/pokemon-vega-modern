import csv
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.map_import.vermilion_slice import SLICE_MAPS, build_outputs

ROOT = Path(__file__).resolve().parents[1]


class VermilionSliceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build_outputs(ROOT)
        cls.fixture = json.loads(cls.outputs["tests/fixtures/vermilion_slice.json"])

    def test_physical_binding_and_safe_route(self):
        self.assertEqual(set(self.fixture["bindings"]), SLICE_MAPS)
        self.assertTrue(all(v["group"] in (96, 97, 98) for v in self.fixture["bindings"].values()))
        self.assertEqual(self.fixture["safety"]["forced_battles"], 0)
        self.assertTrue(self.fixture["travel"]["return_permanent"])

    def test_unlock_gym_factory_and_encounter_contracts(self):
        self.assertTrue(self.fixture["unlock"]["after_both"])
        self.assertFalse(self.fixture["unlock"]["national_dex_required"])
        self.assertEqual(self.fixture["gym"]["vega_badge_writes"], 0)
        self.assertEqual(self.fixture["factory"]["rental_candidates"], 6)
        self.assertTrue(self.fixture["encounter"]["persist_before_battle"])

    def test_physical_emit_is_complete(self):
        emitted = json.loads(self.outputs["generated/kanto/vermilion/content.bin.json"])
        self.assertEqual(emitted["mode"], "PHYSICAL")
        self.assertEqual(len(emitted["physical_maps"]), 5)

    def test_runtime_fixture(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / "vermilion_fixture"
            command = ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                       "-I.", "src/kanto/vermilion/vermilion_slice.c",
                       "overlays/save_migration/save_migration.c",
                       "tests/fixtures/vermilion_slice_fixture.c", "-o", str(binary)]
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
            run = subprocess.run([str(binary)], check=True, capture_output=True, text=True)
            self.assertIn("PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
