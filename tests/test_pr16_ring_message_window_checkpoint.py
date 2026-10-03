"""成功原本の構造・未受入境界・Actions出自を再実行なしで検査する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_window_checkpoint as m

class CheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.previous=m.s.load(m.PRIOR);cls.r=m.compact(cls.previous)
    def reject(self,change):
        p=copy.deepcopy(self.previous);change(p)
        with self.assertRaises(ValueError):m.compact(p)
    def test_compact_size(self):self.assertLess(len(m.s.stable(self.r)),14000)
    def test_no_replay(self):self.assertEqual(self.r['new_contract_cases_executed'],0)
    def test_reused_count(self):self.assertEqual(self.r['reused_contract_cases'],724)
    def test_partition(self):self.assertEqual((self.r['reused_conditional_return_cases'],self.r['reused_pending_stop_cases']),(587,137))
    def test_no_full_trace_copy(self):self.assertTrue(all(k not in self.r for k in ('cases','state01_sequences','executed_saved_sites')))
    def test_group_count(self):self.assertEqual(sum(self.r['groups'].values()),724)
    def test_artifact(self):self.assertEqual(self.r['evidence_access']['artifact_id'],10531358678)
    def test_zero_execution_flags(self):self.assertTrue(all(self.r[k]==0 for k in m.ZERO_FLAGS))
    def test_source(self):self.assertEqual(self.r['source_head'],m.SOURCE)
    def test_bios_prefix_known(self):self.assertFalse(self.r['bios_prefix_resampling_needed'])
    def test_second_palette_not_reached(self):self.assertFalse(self.r['pending_bios'][0]['second_copy_reached'])
    def test_task_source_mismatch(self):self.reject(lambda p:p.update(task='other'))
    def test_commit_mismatch(self):self.reject(lambda p:p.update(source_head='0'*40))
    def test_run_mismatch(self):self.reject(lambda p:p.update(run_id=0))
    def test_failed_tests(self):self.reject(lambda p:p['focused_tests'].update(failures=1))
    def test_skipped_tests(self):self.reject(lambda p:p['focused_tests'].update(skips=1))
    def test_duplicate_case(self):self.reject(lambda p:p['analysis']['cases'].__setitem__(0,p['analysis']['cases'][1]))
    def test_missing_case(self):self.reject(lambda p:p['analysis']['cases'].pop())
    def test_false_partition(self):self.reject(lambda p:p['analysis'].update(conditional_return_cases=588))
    def test_no_native_promotion(self):
        for k in m.FALSE_FLAGS:
            with self.subTest(flag=k):self.reject(lambda p:p['analysis'].__setitem__(k,True))
    def test_case_native_promotion(self):self.reject(lambda p:p['analysis']['cases'][0].update(native_observation=True))
    def test_case_success_stub(self):self.reject(lambda p:p['analysis']['cases'][0].update(successful_callee_stubs=1))
    def test_queue_failure_promotion(self):
        self.reject(lambda p:next(r for r in p['analysis']['cases']if r['case']=='state0-mode2-0-full').update(queue_reserved=True))
    def test_state2_promotion(self):self.reject(lambda p:p['analysis']['state01_sequences'][0].update(states=[0,1,2]))
    def test_host_mutation(self):self.reject(lambda p:p['analysis']['state01_sequences'][0].update(host_writes_between_calls=1))
    def test_duplicate_sequence(self):self.reject(lambda p:p['analysis']['state01_sequences'].__setitem__(0,p['analysis']['state01_sequences'][1]))
    def test_task_full_promotion(self):self.reject(lambda p:p['analysis']['task_full_boundary'].update(liveness_proven=True))
    def test_wrong_bios(self):self.reject(lambda p:p['analysis']['pending_bios'][0].update(service=12))
    def test_bad_bios_prefix_hash(self):self.reject(lambda p:p['analysis']['pending_bios'][1]['saved_prefix'].update(identity={}))
    def test_wrong_palette(self):self.reject(lambda p:p['analysis']['pending_bios'][0].update(destination_for_state0=0x020376ec))
    def test_wrong_fill(self):self.reject(lambda p:p['analysis']['pending_bios'][1].update(fill_word=0))
    def fixtures(self):
        return (dict(id=m.JOB,run_id=m.RUN,status='completed',conclusion='success',steps=[dict(status='completed',conclusion='success')]),
            dict(id=m.ARTIFACT,name='pr16-ring-message-window-contracts',expired=False,digest=m.DIGEST,
                workflow_run=dict(id=m.RUN,head_sha=m.SOURCE,head_branch=m.s.BRANCH)))
    def test_actions_accept(self):
        j,a=self.fixtures();self.assertEqual(m.verify_actions(j,a)['job_conclusion'],'success')
    def test_actions_reject_action_required(self):
        j,a=self.fixtures();j['conclusion']='action_required'
        with self.assertRaises(ValueError):m.verify_actions(j,a)
    def test_actions_reject_missing_steps(self):
        j,a=self.fixtures();j['steps']=[]
        with self.assertRaises(ValueError):m.verify_actions(j,a)
    def test_actions_reject_expired(self):
        j,a=self.fixtures();a['expired']=True
        with self.assertRaises(ValueError):m.verify_actions(j,a)
    def test_actions_reject_digest(self):
        j,a=self.fixtures();a['digest']='sha256:'+'0'*64
        with self.assertRaises(ValueError):m.verify_actions(j,a)
    def test_actions_reject_wrong_branch(self):
        j,a=self.fixtures();a['workflow_run']['head_branch']='main'
        with self.assertRaises(ValueError):m.verify_actions(j,a)
    def test_next_step(self):
        current,next_step=m.summaries(self.r);self.assertIn('再実行せず',current)
        self.assertIn('BIOS0B/0C',next_step);self.assertIn('prefix/724条件',next_step)

if __name__=='__main__':unittest.main()
