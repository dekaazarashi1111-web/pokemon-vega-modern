import copy
import hashlib
import json
from pathlib import Path
import unittest
from scripts.reconstruct_trainer_csv_inputs import reconstruct

ROOT = Path(__file__).resolve().parents[1]


class TrainerCsvReconstructionTests(unittest.TestCase):
    def test_task06_all_eight_original_hashes_are_reproduced(self):
        rows = json.loads((ROOT / 'content/trainer_changekit_final/source_manifest.json').read_text())['inputs']
        rows = [row for row in rows if row['path'].startswith('VEGA_TRAINER_CHANGEKIT_TASK06_KANTO/data/')]
        self.assertEqual(len(rows), 8)
        observed = reconstruct(ROOT, rows)
        self.assertEqual(set(observed), {row['path'] for row in rows})
        for row in rows:
            self.assertEqual(len(observed[row['path']]), row['size'])
            self.assertEqual(hashlib.sha256(observed[row['path']]).hexdigest(), row['sha256'])

    def test_unmatched_hash_is_not_published(self):
        rows = json.loads((ROOT / 'content/trainer_changekit_final/source_manifest.json').read_text())['inputs']
        row = copy.deepcopy(next(row for row in rows if row['path'].endswith('TASK06_KANTO/data/trainer_parties.csv')))
        row['sha256'] = '0' * 64
        self.assertEqual(reconstruct(ROOT, [row]), {})

    def test_reconstruction_is_read_only_and_deterministic(self):
        directory = ROOT / 'content/trainer_changekit_final'
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}
        rows = json.loads((directory / 'source_manifest.json').read_text())['inputs']
        first = reconstruct(ROOT, rows)
        self.assertEqual(first, reconstruct(ROOT, rows))
        self.assertGreaterEqual(len(first), 30)
        self.assertEqual(before, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()})
