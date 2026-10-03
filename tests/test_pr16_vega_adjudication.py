import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('vega_adjudication', ROOT / 'tools/pr16_vega_adjudication.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AdjudicationTests(unittest.TestCase):
    def test_multiset_difference_preserves_duplicate_and_order(self):
        rows = [{'move_id': 1, 'order': 0}, {'move_id': 1, 'order': 1}, {'move_id': 2, 'order': 2}]
        self.assertEqual(a.difference(rows, rows[:1]), rows[1:])

    def test_changed_level_is_a_difference(self):
        self.assertEqual(len(a.difference([{'move_id': 44, 'level': 18}], [{'move_id': 44, 'level': 20}])), 1)

    def test_owner_five_rows_and_pure_determinism(self):
        before = {p.name: a.digest(p) for p in (ROOT / a.EVIDENCE).iterdir() if p.is_file()}
        outputs = a.build(ROOT)
        self.assertEqual(outputs, a.build(ROOT))
        ledger = json.loads(outputs['source_collisions.json'])
        self.assertEqual(len(ledger['rows']), 5)
        self.assertEqual(len({r['decision_row_key'] for r in ledger['rows']}), 5)
        self.assertEqual(sum(len(g['wiki_only_rows']) for g in ledger['groups']), 3)
        raw = [json.loads(line) for line in (ROOT / a.EVIDENCE / 'vega_original_baseline.jsonl').read_text().splitlines()]
        projection = [json.loads(line) for line in outputs['adopted_vega_original_baseline.jsonl'].decode().splitlines()]
        self.assertEqual([r['methods'] for r in raw], [r['methods'] for r in projection])
        self.assertFalse(ledger['summary']['runtime_applied'])
        self.assertEqual(before, {p.name: a.digest(p) for p in (ROOT / a.EVIDENCE).iterdir() if p.is_file()})

    def test_tampered_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / a.EVIDENCE, root / a.EVIDENCE)
            shutil.copy2(ROOT / a.DECISION, root / a.DECISION)
            path = root / a.EVIDENCE / 'source_conflicts.json'
            path.write_bytes(path.read_bytes() + b' ')
            with self.assertRaisesRegex(ValueError, 'input size drift'):
                a.build(root)

    def test_unapproved_precedence_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / a.EVIDENCE, root / a.EVIDENCE)
            decision = copy.deepcopy(a.load(ROOT / a.DECISION))
            decision['priority_rule'] = 'WIKI_WINS'
            (root / a.DECISION).write_bytes(a.encoded(decision))
            with self.assertRaisesRegex(ValueError, 'precedence changed'):
                a.build(root)


if __name__ == '__main__':
    unittest.main()
