"""Reject forged observation records; these tests do not claim emulator runs."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_native_learning as m
PROCESS={'schema_version':1,'returncode':0,'timed_out':False,'spawn_error':None}

class NativeLearningContract(unittest.TestCase):
    def observation(self,case):
        value=m.expected(case)
        w=dict.fromkeys(m.WITNESS,0);w.update(bag_party=10,level=20,field=1000)
        if case[1]!=case[3]:w.update(evo_begin=30,evo_update=40)
        if case[-1]!=1:
            w.update(dialog=30,summary=40,selection=50,downs=1)
            if case[-1]==3:w['stop']=60
        value['witness']=w
        return value
    def test_all_exact_record_shapes_and_unchanged_move_slots(self):
        for case in m.CASES:
            value=self.observation(case)
            self.assertEqual(m.validate(json.dumps(value).encode(),case,PROCESS),value)
        canceled=m.expected(m.CASES[2])
        self.assertEqual(canceled['moves_after'],[33,81,45,52])
        self.assertEqual(canceled['pp_after'],[7,8,9,10])
        self.assertEqual(canceled['pp_bonuses_after'],229)
    def test_saved_pp_candidate_and_cold_continue_cannot_be_forged(self):
        case=m.CASES[0];original=self.observation(case)
        for key,wrong in [('rom_sha256','0'*64),('pp_after',[7,8,0,0]),('pp_bonuses_after',0),
                          ('normal_save_menu',False),('cold_continue',False),('save_counter_delta',0),
                          ('host_write_barriers',0),('fresh_cores',1),('level_after',12)]:
            bad=original|{key:wrong}
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate(json.dumps(bad).encode(),case,PROCESS)
    def test_evolution_requires_actual_ordered_observation(self):
        case=m.CASES[3]
        for key,value in [('evo_begin',0),('evo_update',0),('evo_begin',1200),('level',1200)]:
            bad=self.observation(case);bad['witness'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):m.validate(json.dumps(bad).encode(),case,PROCESS)
    def test_replacement_cancel_and_native_process_fail_closed(self):
        for index,key in [(1,'dialog'),(1,'summary'),(1,'selection'),(2,'stop')]:
            case=m.CASES[index];bad=self.observation(case);bad['witness'][key]=0
            with self.subTest(index=index,key=key),self.assertRaises(ValueError):m.validate(json.dumps(bad).encode(),case,PROCESS)
        case=m.CASES[0];raw=json.dumps(self.observation(case)).encode()
        for process in (PROCESS|{'returncode':1},PROCESS|{'timed_out':True}):
            with self.assertRaises(ValueError):m.validate(raw,case,process)
        with self.assertRaises(ValueError):m.validate(raw,case,PROCESS,b'mGBA[warning]')

if __name__=='__main__':unittest.main()
