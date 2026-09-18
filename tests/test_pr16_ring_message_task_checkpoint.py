"""成功原本を読み直すだけ。命令実行モデル/1231条件は起動しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_task_checkpoint as m


class CompactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.p=m.s.load(m.PRIOR);cls.r=m.compact(cls.p)
    def bad(self,key,value,analysis=False):
        p=copy.deepcopy(self.p)
        (p['analysis'] if analysis else p)[key]=value
        with self.assertRaises(ValueError):m.compact(p)
    def test_compact_size(self):self.assertLess(len(m.s.stable(self.r)),16000)
    def test_no_large_case_copy(self):self.assertTrue({'cases','state2_sequences','executed_saved_sites'}.isdisjoint(self.r))
    def test_counts_are_reused(self):self.assertEqual((self.r['reused_contract_cases'],self.r['reused_source_tests'],self.r['new_contract_cases_executed']),(1231,55,0))
    def test_source_task(self):self.bad('task','wrong')
    def test_source_head(self):self.bad('source_head','0'*40)
    def test_source_run(self):self.bad('run_id',m.RUN+1)
    def test_failed_tests(self):self.bad('focused_tests',dict(tests_run=55,failures=1,errors=0,skips=0,successful=False))
    def test_candidate(self):self.bad('candidate',{},True)
    def test_node_count(self):self.bad('saved_node_count',8250,True)
    def test_case_count(self):self.bad('contract_cases',1230,True)
    def test_repeat(self):self.bad('evaluation_cache_misses',2,True)
    def test_return_count(self):self.bad('conditional_return_cases',913,True)
    def test_duplicate_label(self):
        p=copy.deepcopy(self.p);p['analysis']['cases'][0]=p['analysis']['cases'][1]
        with self.assertRaises(ValueError):m.compact(p)
    def test_stop_promotion(self):
        p=copy.deepcopy(self.p);next(r for r in p['analysis']['cases'] if r['stop'])['stop']=None
        with self.assertRaises(ValueError):m.compact(p)
    def test_domain(self):self.bad('window_flag_byte_values',list(range(255)),True)
    def test_native_promotion(self):
        for key in m.FALSE_FLAGS:
            with self.subTest(key=key):self.bad(key,True,True)
    def test_replay_promotion(self):
        for key in m.ZERO_FLAGS:
            with self.subTest(key=key):self.bad(key,1,True)
    def test_sequence_reference(self):
        p=copy.deepcopy(self.p);p['analysis']['state2_sequences'][0]['cases'][0]='missing'
        with self.assertRaises(ValueError):m.compact(p)
    def test_sequence_reorder(self):
        p=copy.deepcopy(self.p);p['analysis']['state2_sequences'][0]['cases'].reverse()
        with self.assertRaises(ValueError):m.compact(p)
    def test_task_full_promotion(self):
        p=copy.deepcopy(self.p);p['analysis']['task_full_boundary']['task_allocated']=True
        with self.assertRaises(ValueError):m.compact(p)
    def test_artifact_route(self):
        self.assertEqual(self.r['evidence_access']['artifact_id'],m.ARTIFACT)
        self.assertEqual(self.r['evidence_access']['manifest_member'],'export/manifest.json')


class ActionsTests(unittest.TestCase):
    def fixtures(self):
        return (dict(id=m.JOB,run_id=m.RUN,status='completed',conclusion='success',steps=[dict(status='completed',conclusion='success')]),
            dict(id=m.ARTIFACT,name='pr16-ring-message-task-contracts',expired=False,digest=m.DIGEST,
                workflow_run=dict(id=m.RUN,head_sha=m.SOURCE,head_branch=m.s.BRANCH)))
    def test_success(self):self.assertEqual(m.verify_actions(*self.fixtures())['job_conclusion'],'success')
    def test_job_failure(self):
        j,a=self.fixtures();j['conclusion']='failure'
        with self.assertRaises(ValueError):m.verify_actions(j,a)
    def test_step_failure(self):
        j,a=self.fixtures();j['steps'][0]['conclusion']='failure'
        with self.assertRaises(ValueError):m.verify_actions(j,a)
    def test_archive_digest(self):
        j,a=self.fixtures();a['digest']='sha256:'+'0'*64
        with self.assertRaises(ValueError):m.verify_actions(j,a)
    def test_artifact_expired(self):
        j,a=self.fixtures();a['expired']=True
        with self.assertRaises(ValueError):m.verify_actions(j,a)
    def test_artifact_source(self):
        j,a=self.fixtures();a['workflow_run']['head_sha']='0'*40
        with self.assertRaises(ValueError):m.verify_actions(j,a)


if __name__=='__main__':unittest.main()
