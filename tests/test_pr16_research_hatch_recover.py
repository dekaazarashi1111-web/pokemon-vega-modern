"""Recovery projection boundaries only; no fixture/emulator execution."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_hatch_recover as r


def fixture():
    v=dict(run_id=r.RUN,source_head=r.SOURCE,status='RUNNING',candidate=r.CANDIDATE,
           accepted={n:{'original':n} for n in r.CASES},failures={},native_processes=5,
           host_compiles=1,new_unit_tests=32,unit_passed=True,unit_origin=r.RUN,
           actions_completion_confirmed=False,issue19_complete=False,release_ready=False,
           active_baseline_changed=False,accepted_case_reruns=0,gift_reruns=0,arm_compiles=0,
           rom_changes=0,wiki_generations=0,pending_cases=list(r.CASES))
    names=list(r.CASES)+['remaining-'+str(i) for i in range(10)]
    return v,names


class RecoveryTests(unittest.TestCase):
    def test_projection_preserves_original(self):
        v,n=fixture();before=copy.deepcopy(v);out=r.project(v,n)
        self.assertEqual(v,before);self.assertEqual(out['accepted'],v['accepted'])
        self.assertEqual(len(out['pending_cases']),10)
        self.assertNotEqual(out['status'],v['status'])
        out['accepted'].clear();self.assertEqual(v,before)
    def test_stale_pending_is_recomputed(self):
        v,n=fixture();self.assertEqual(r.project(v,n)['pending_cases'],n[5:])
    def test_wrong_source(self):
        v,n=fixture();v['source_head']='0'*40
        with self.assertRaises(ValueError):r.project(v,n)
    def test_wrong_candidate(self):
        v,n=fixture();v['candidate']={}
        with self.assertRaises(ValueError):r.project(v,n)
    def test_unknown_success(self):
        v,n=fixture();v['accepted']['unknown']={}
        with self.assertRaises(ValueError):r.project(v,n)
    def test_failure_not_promoted(self):
        v,n=fixture();v['failures']={'case':'failure'}
        with self.assertRaises(ValueError):r.project(v,n)
    def test_unsafe_flags(self):
        for key in ('actions_completion_confirmed','issue19_complete','release_ready','active_baseline_changed'):
            with self.subTest(key=key):
                v,n=fixture();v[key]=True
                with self.assertRaises(ValueError):r.project(v,n)
    def test_rerun_counter(self):
        v,n=fixture();v['accepted_case_reruns']=1
        with self.assertRaises(ValueError):r.project(v,n)
    def test_duplicate_domain(self):
        v,n=fixture();n[-1]=n[-2]
        with self.assertRaises(ValueError):r.project(v,n)


if __name__=='__main__':unittest.main()
