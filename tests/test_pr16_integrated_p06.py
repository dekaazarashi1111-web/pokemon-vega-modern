import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_integrated_p06 as m
import run_modernization_p06_decided_e2e as historical

class P06Binding(unittest.TestCase):
    def test_exactly_one_candidate_path_changes(self):
        before='parent=unchanged;child='+m.OLD_CHILD+';seed=unchanged'
        self.assertEqual(m.path_adapter(before),'parent=unchanged;child='+m.NEW_CHILD+';seed=unchanged')
        for bad in ('',m.OLD_CHILD+m.OLD_CHILD,m.NEW_CHILD+m.OLD_CHILD):
            with self.assertRaises(ValueError):m.path_adapter(bad)
    def test_new_identity_does_not_mutate_the_historical_validator(self):
        module=m.load_base()
        self.assertEqual(module.FINAL_SHA,m.new.ROM_SHA)
        self.assertEqual(historical.FINAL_SHA,m.prior.SHA)
        self.assertNotEqual(module.FINAL_SHA,historical.FINAL_SHA)
        self.assertEqual(module.CASES,historical.CASES)
        self.assertEqual(len(module.CASES),8)
    def test_reviewed_displays_are_distinct_exact_hashes(self):
        self.assertEqual(len(m.REVIEWED),3)
        self.assertEqual(len(set(m.REVIEWED.values())),3)
        for sha in m.REVIEWED.values():self.assertEqual(len(bytes.fromhex(sha)),32)

if __name__=='__main__':unittest.main()
