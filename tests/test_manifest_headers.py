import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ManifestHeadersTest(unittest.TestCase):
    def test_all_manifest_files_have_headers(self):
        for path in (ROOT/'manifests').glob('*.csv'):
            with path.open(encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                header = next(reader)
            self.assertGreater(len(header), 1, path.name)
            self.assertEqual(len(header), len(set(header)), path.name)

if __name__ == '__main__':
    unittest.main()
