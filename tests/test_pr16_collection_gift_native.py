"""合成unit-cacheの境界。人工証明はnative受入へ昇格しない。"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pr16_collection_gift_native import certificate

def fixture():
    old=dict(unit_passed=True,unit_origin=36110983368,unit_binding={'a':dict(sha256='old',size=1)})
    rep=dict(run_id=36118048058,status='PASS_HOST_BG_REPAIR_NATIVE_PENDING',unit_tests=7,unit_skips=0,
             new_native_processes=0,rom_changes=0,arm_compiles=0,host_compiles=0,
             source_before={'a':'old'},source_after={'a':dict(sha256='new',size=2),
                '.github/workflows/pr16-supply-followup-20260925.yml':dict(sha256='workflow',size=1)})
    return old,rep,{'a':dict(sha256='new',size=2)}

class CertificateTests(unittest.TestCase):
    def test_explicit_composite_not_current_execution(self):
        old,rep,now=fixture();snapshot=deepcopy((old,rep,now));r=certificate(old,rep,now)
        self.assertEqual(r['current_run_unit_executions'],0)
        self.assertEqual(r['unchanged_old_tests']+r['repair_tests'],24)
        self.assertEqual((old,rep,now),snapshot)
    def test_changed_current_source_rejected(self):
        old,rep,now=fixture();now['a']['size']=3
        with self.assertRaises(ValueError):certificate(old,rep,now)
    def test_missing_binding_rejected(self):
        old,rep,now=fixture()
        with self.assertRaises(ValueError):certificate(old,rep,{})
    def test_unaccepted_or_wrong_origin_rejected(self):
        for edit in ({'unit_passed':False},{'unit_origin':0}):
            old,rep,now=fixture();old.update(edit)
            with self.assertRaises(ValueError):certificate(old,rep,now)
    def test_wrong_repair_scope_rejected(self):
        for key,value in [('unit_skips',1),('unit_tests',6),('rom_changes',1),('new_native_processes',1)]:
            old,rep,now=fixture();rep[key]=value
            with self.assertRaises(ValueError):certificate(old,rep,now)
if __name__=='__main__':unittest.main()
