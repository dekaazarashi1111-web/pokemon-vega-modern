"""個体追跡は診断であり、既受入/P08ゲートを変更しない。"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('identity_record',ROOT/'scripts/pr16_circus_identity_record.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class RecordTests(unittest.TestCase):
    def setUp(self):
        self.state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes())
        self.backlog=json.loads((ROOT/'content/modernization/p08_remaining_work.json').read_bytes())
        self.report=dict(classification='CIRCUS_RENTALS_REPLACED_AT_BATTLE_INIT',candidate=dict(size=33554432,sha256=m.trace.SHA),physical_admission_accepted=False)
    def test_projection_is_immutable(self):
        s,b=copy.deepcopy(self.state),copy.deepcopy(self.backlog);m.project(s,b,self.report)
        self.assertEqual((s,b),(self.state,self.backlog))
    def test_formal_authorities_unchanged(self):
        s,b=m.project(self.state,self.backlog,self.report)
        for k in ('candidate','status','latest_native_run','latest_native_job','latest_native_tested_head','last_accepted_native_run','last_accepted_native_tested_head','release_ready','remaining_physical_gap_ids','remaining_p08_gate_ids'):
            self.assertEqual(s[k],self.state[k])
    def test_unrelated_conditions_unchanged(self):
        _,b=m.project(self.state,self.backlog,self.report)
        for old,new in zip(self.backlog['remaining_conditions'],b['remaining_conditions']):
            if old['id']!='PHYSICAL_CIRCUS_ADMISSION':self.assertEqual(old,new)
    def test_no_gate_closure(self):
        s,b=m.project(self.state,self.backlog,self.report)
        row=next(r for r in b['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION')
        self.assertIsNone(row['success_evidence']);self.assertIs(s['circus_rental_identity']['rental_identity_verified'],False)
    def test_reject_promotion(self):
        self.report['physical_admission_accepted']=True
        with self.assertRaises(ValueError):m.project(self.state,self.backlog,self.report)
    def test_reject_missing_gate(self):
        self.backlog['remaining_conditions']=[r for r in self.backlog['remaining_conditions'] if r['id']!='PHYSICAL_CIRCUS_ADMISSION']
        with self.assertRaises(ValueError):m.project(self.state,self.backlog,self.report)
    def test_reject_changed_evidence(self):
        next(r for r in self.backlog['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION')['success_evidence']='other'
        with self.assertRaises(ValueError):m.project(self.state,self.backlog,self.report)
    def test_idempotent_note(self):
        s,b=m.project(self.state,self.backlog,self.report);s2,b2=m.project(s,b,self.report)
        self.assertEqual((s,b),(s2,b2))
if __name__=='__main__':unittest.main()
