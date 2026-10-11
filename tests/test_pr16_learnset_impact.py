"""戦闘再実行なしで終端・scopeの誤昇格を拒否する追加境界試験。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_learnset_impact as m

class ImpactTests(unittest.TestCase):
    def setUp(self):
        self.run={'id':m.RUN,'head_sha':m.HEAD,'head_branch':'codex/modernization-followup-20260908','path':'.github/workflows/pr16-learnset-gameplay.yml','status':'completed','conclusion':'success'}
        self.job={'id':m.JOB,'run_id':m.RUN,'status':'completed','conclusion':'success','steps':[{'number':n,'status':'completed','conclusion':'success'} for n in (5,6,7,8)]}
        self.art=dict(m.ART,expired=False,workflow_run={'id':m.RUN,'head_sha':m.HEAD})
        self.v=json.loads((ROOT/m.CP).read_bytes())
    def check(self):m.metadata(self.run,self.job,self.art)
    def test_complete(self):self.check();m.report(self.v)
    def test_running_rejected(self):
        self.run['status']='in_progress'
        with self.assertRaises(ValueError):self.check()
    def test_action_required_rejected(self):
        self.run['conclusion']='action_required'
        with self.assertRaises(ValueError):self.check()
    def test_wrong_head_rejected(self):
        self.run['head_sha']=m.START
        with self.assertRaises(ValueError):self.check()
    def test_wrong_branch_rejected(self):
        self.run['head_branch']='main'
        with self.assertRaises(ValueError):self.check()
    def test_unfinished_upload_rejected(self):
        self.job['steps'][-1]['conclusion']='skipped'
        with self.assertRaises(ValueError):self.check()
    def test_missing_push_rejected(self):
        self.job['steps'].pop(2)
        with self.assertRaises(ValueError):self.check()
    def test_duplicate_step_rejected(self):
        self.job['steps'].append(copy.deepcopy(self.job['steps'][0]))
        with self.assertRaises(ValueError):self.check()
    def test_artifact_head_rejected(self):
        self.art['workflow_run']['head_sha']=m.START
        with self.assertRaises(ValueError):self.check()
    def test_expired_rejected(self):
        self.art['expired']=True
        with self.assertRaises(ValueError):self.check()
    def test_release_promotion_rejected(self):
        self.v['release_ready']=True
        with self.assertRaises(ValueError):m.report(self.v)
    def test_bool_counter_rejected(self):
        self.v['native_processes']=True
        with self.assertRaises(ValueError):m.report(self.v)
    def test_rerun_counter_rejected(self):
        self.v['accepted_test_reruns']=1
        with self.assertRaises(ValueError):m.report(self.v)
    def test_unbound_zip_rejected(self):
        with self.assertRaises(ValueError):m.unpack(b'PK not the bound original')

if __name__=='__main__':unittest.main()
