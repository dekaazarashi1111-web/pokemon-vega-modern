"""保存結果の意味/実行完了を拒否検証。emulatorや旧試験は呼ばない。"""
import copy
import json
import unittest
from scripts import pr16_supply_native_closeout as c

class CloseoutTests(unittest.TestCase):
    def setUp(self):
        self.v=json.loads((c.ROOT/c.EVIDENCE/'verification.json').read_text())
        self.run={'id':c.RUN,'head_sha':c.TESTED,'head_branch':'codex/modernization-followup-20260908',
                  'path':'.github/workflows/pr16-learnset-supply-rom.yml','status':'completed','conclusion':'success'}
        steps=[{'name':str(i),'status':'completed','conclusion':'success'} for i in range(8)]
        steps.append({'name':'同branchへ非force commit/pushし最新refを照合','status':'completed','conclusion':'success'})
        self.jobs=[{'id':c.JOB,'name':'supply-rom','status':'completed','conclusion':'success','steps':steps}]

    def test_valid_fixed_evidence(self):c.validate_verification(self.v);c.validate_run(self.run,self.jobs)
    def test_wrong_head(self):
        self.v['source_head']='0'*40
        with self.assertRaises(ValueError):c.validate_verification(self.v)
    def test_wrong_run(self):
        self.v['run_id']+=1
        with self.assertRaises(ValueError):c.validate_verification(self.v)
    def test_wrong_candidate(self):
        self.v['candidate']['sha256']='0'*64
        with self.assertRaises(ValueError):c.validate_verification(self.v)
    def test_scope_escalation(self):
        for name in ('physical_supply_verified','gameplay_e2e_accepted','issue19_complete','release_ready'):
            v=copy.deepcopy(self.v);v[name]=True
            with self.subTest(name=name),self.assertRaises(ValueError):c.validate_verification(v)
    def test_unexpected_reexecution(self):
        self.v['accepted_tests_rerun']=1
        with self.assertRaises(ValueError):c.validate_verification(self.v)
    def test_boolean_counter(self):
        self.v['native_processes']=True
        with self.assertRaises(ValueError):c.validate_verification(self.v)
    def test_vacuous_special_positive(self):
        for r in self.v['native_results']:r['special_allowed']=0
        with self.assertRaises(ValueError):c.validate_verification(self.v)
    def test_process_mismatch(self):
        self.v['native_results'][1]['calls']-=1
        with self.assertRaises(ValueError):c.validate_verification(self.v)
    def test_placement_offset(self):
        self.v['placement_repair']['load_address']-=4
        with self.assertRaises(ValueError):c.validate_verification(self.v)
    def test_incomplete_or_failed_actions(self):
        for state,conclusion in (('in_progress',None),('completed','failure')):
            self.run.update(status=state,conclusion=conclusion)
            with self.subTest(status=state),self.assertRaises(ValueError):c.validate_run(self.run,self.jobs)
    def test_skipped_push(self):
        self.jobs[0]['steps'][-1]['conclusion']='skipped'
        with self.assertRaises(ValueError):c.validate_run(self.run,self.jobs)

if __name__=='__main__':unittest.main()
