"""未受入3活動だけの契約。既存native/旧suiteは呼ばない。"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('remaining', ROOT/'scripts/pr16_research_followup_20260927.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RemainingContract(unittest.TestCase):
    def setUp(self):
        self.model = json.loads((ROOT/'content/research_economy_v1/canonical_model.json').read_text())
    def reject(self, f):
        f(self.model)
        with self.assertRaises(ValueError): m.activity_contract(self.model)
    def test_contract(self):
        self.assertEqual([r['points_awarded'] for r in m.activity_contract(self.model)], [4,10,3])
    def test_missing_row(self): self.reject(lambda x: x['activities'].pop())
    def test_extra_row(self): self.reject(lambda x: x['activities'].append(copy.deepcopy(x['activities'][0])))
    def test_order(self): self.reject(lambda x: x['activities'].reverse())
    def test_bool_index(self): self.reject(lambda x: x['activities'][0].update(index=False))
    def test_wrong_points(self): self.reject(lambda x: x['activities'][0].update(points_awarded=8))
    def test_wrong_cap(self): self.reject(lambda x: x['activities'][1].update(daily_cap=500))
    def test_wrong_unlock(self): self.reject(lambda x: x['activities'][2].update(unlock_key='KANTO_EARLY_ACCESS'))
    def test_wrong_mode(self): self.reject(lambda x: x['activities'][1].update(implementation_mode='SIMPLE_EVENT'))
    def test_scope(self):
        self.assertEqual(m.inventories(['userfile/fishing.json','tools/fishing.gba','config/fishing.json','tools/mgba_natural_capture.c','docs/fishing.md']), ['config/fishing.json','tools/mgba_natural_capture.c'])
