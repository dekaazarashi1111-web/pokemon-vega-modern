"""Task03の元coverageを固定manifestで検証する。入力本文や新しい期待hashは持ち込まない。"""
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import unittest
from scripts.invert_trainer_normalization import inverse_rows
from scripts.reconstruct_trainer_csv_inputs import PHASES

ROOT = Path(__file__).resolve().parents[1]


class TrainerCoverageRestorationTests(unittest.TestCase):
    def test_task03_all_rows_recover_the_existing_manifest_identity(self):
        base = ROOT / 'content/trainer_changekit_final'
        def read(name):
            with (base / name).open(encoding='utf-8', newline='') as stream:
                reader = csv.DictReader(stream)
                return reader.fieldnames, list(reader)
        fields, rows = read('coverage.csv')
        rows = [row for row in rows if row['task_id'] == 'TASK03_TOHOKU_MID']
        original = copy.deepcopy(rows)
        ledger = {row['encounter_key']: row for row in read('normalization_ledger.csv')[1]}
        encounters = {row['encounter_key']: row for row in read('trainer_encounters.csv')[1]}
        restored = inverse_rows('coverage.csv', 'VEGA_TRAINER_CHANGEKIT_TASK03_TOHOKU_MID', rows, ledger, {})
        self.assertEqual(rows, original)
        self.assertEqual(len(restored), 342)
        self.assertEqual(sum(row['decision'] == 'FAIL_CLOSED_SOURCE_PRESERVED' for row in restored), 34)
        restored.sort(key=lambda row: (PHASES.index(encounters[row['encounter_key']]['story_phase']), row['encounter_key']))
        output = io.StringIO(newline='')
        writer = csv.DictWriter(output, fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(restored)
        raw = output.getvalue().encode('utf-8')
        manifest = json.loads((base / 'source_manifest.json').read_text())
        expected = next(row for row in manifest['inputs'] if row['path'].endswith('TASK03_TOHOKU_MID/data/coverage.csv'))
        self.assertEqual(len(raw), expected['size'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), expected['sha256'])

    def test_missing_note_provenance_is_not_classified(self):
        row = {'encounter_key': 'TEST', 'decision': 'UNRESOLVED', 'notes': 'unproven'}
        ledger = {'TEST': {'archive_consumer_key': 'ARCHIVE_REMATCH_0001', 'normalization_action': 'MOVE_TO_ARCHIVE_REMATCH', 'original_battle_type': 'UNKNOWN'}}
        result = inverse_rows('coverage.csv', 'VEGA_TRAINER_CHANGEKIT_TASK03_TOHOKU_MID', [row], ledger, {})
        self.assertEqual(result, [row])
