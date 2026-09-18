"""初戦保持だけを受入し、継続戦/連勝/physical/P08へ過大昇格しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_retention_record as m
class RecordTests(unittest.TestCase):
    def setUp(self):
        self.state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes())
        self.backlog=json.loads((ROOT/'content/modernization/p08_remaining_work.json').read_bytes())
        self.report=dict(classification='CIRCUS_FIRST_BATTLE_RETENTION_ACCEPTED_STREAK_OPEN',first_battle_rental_identity_verified=True,
            later_battle_rental_identity_verified=False,circus_streak_verified=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    def test_inputs_unchanged(self):
        s,b=copy.deepcopy(self.state),copy.deepcopy(self.backlog);m.project(s,b,self.report)
        self.assertEqual((s,b),(self.state,self.backlog))
    def test_formal_acceptance_unchanged(self):
        s,b=m.project(self.state,self.backlog,self.report)
        for k in ('candidate','status','latest_native_run','latest_native_job','latest_native_tested_head','last_accepted_native_run','last_accepted_native_tested_head','release_ready','remaining_physical_gap_ids','remaining_p08_gate_ids'):self.assertEqual(s[k],self.state[k])
    def test_unrelated_rows_unchanged(self):
        _,b=m.project(self.state,self.backlog,self.report)
        for old,new in zip(self.backlog['remaining_conditions'],b['remaining_conditions']):
            if old['id']!='PHYSICAL_CIRCUS_ADMISSION':self.assertEqual(old,new)
    def test_gate_stays_open(self):
        _,b=m.project(self.state,self.backlog,self.report)
        self.assertIsNone(next(r for r in b['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION')['success_evidence'])
    def test_missing_first_battle_proof_rejected(self):
        self.report['first_battle_rental_identity_verified']=False
        with self.assertRaises(ValueError):m.project(self.state,self.backlog,self.report)
    def test_later_battle_promotion_rejected(self):
        self.report['later_battle_rental_identity_verified']=True
        with self.assertRaises(ValueError):m.project(self.state,self.backlog,self.report)
    def test_streak_promotion_rejected(self):
        self.report['circus_streak_verified']=True
        with self.assertRaises(ValueError):m.project(self.state,self.backlog,self.report)
    def test_physical_promotion_rejected(self):
        self.report['physical_admission_accepted']=True
        with self.assertRaises(ValueError):m.project(self.state,self.backlog,self.report)
    def test_suppression_promotion_rejected(self):
        self.report['suppression_accepted']=True
        with self.assertRaises(ValueError):m.project(self.state,self.backlog,self.report)
    def test_release_promotion_rejected(self):
        self.report['release_ready']=True
        with self.assertRaises(ValueError):m.project(self.state,self.backlog,self.report)
    def test_no_duplicate_note(self):
        s,b=m.project(self.state,self.backlog,self.report);s2,b2=m.project(s,b,self.report)
        self.assertEqual((s,b),(s2,b2))
    def test_missing_gate_rejected(self):
        self.backlog['remaining_conditions']=[r for r in self.backlog['remaining_conditions'] if r['id']!='PHYSICAL_CIRCUS_ADMISSION']
        with self.assertRaises(ValueError):m.project(self.state,self.backlog,self.report)
if __name__=='__main__':unittest.main()
