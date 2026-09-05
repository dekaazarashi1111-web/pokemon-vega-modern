from __future__ import annotations
import csv
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.content.populate_content import HEADERS
from tools.content.validate_population import collect_population_errors

ROOT = Path(__file__).resolve().parents[1]


class PopulationEvidenceBoundaryTests(unittest.TestCase):
    def test_missing_or_malformed_inventory_is_a_validation_error(self):
        with tempfile.TemporaryDirectory(prefix="population-evidence-") as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "manifests", root / "manifests")
            shutil.copytree(ROOT / "content", root / "content")
            loaded = {}
            for name in HEADERS:
                with (root / "manifests" / name).open(encoding="utf-8-sig", newline="") as handle:
                    loaded[name] = list(csv.DictReader(handle))
            inventory = root / "reports/generated/id_inventory.json"
            for payload in (None, "not-json", "{}", '{"map_details": null}'):
                with self.subTest(payload=payload):
                    if payload is not None:
                        inventory.parent.mkdir(parents=True, exist_ok=True)
                        inventory.write_text(payload, encoding="utf-8")
                    errors = collect_population_errors(root, loaded)
                    self.assertIn("reports/generated/id_inventory.json: missing or invalid T16 physical map inventory", errors)

    def test_header_only_population_remains_a_valid_unbuilt_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(collect_population_errors(Path(temporary), {name: [] for name in HEADERS}), [])


if __name__ == "__main__":
    unittest.main()
