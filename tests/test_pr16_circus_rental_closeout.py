"""完了Actionsと記録の整合性。nativeを再実行せず原本のみ検証する。"""
from copy import deepcopy
from pathlib import Path
import inspect
import json
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_rental_closeout as t

class CloseoutTests(unittest.TestCase):
    def setUp(self):
        self.spec=dict(run_id=100,job_id=200,tested_head='a'*40,conclusion='failure',
                       classification='SCOPED_NATIVE_OPEN',stop_ja='実測を保存。未完を維持。',next_ja='次の停止から再開。',no_repeat_ja='既受入単体の再実行0。')
        self.run=dict(id=100,head_sha='a'*40,head_branch=t.ops.BRANCH,path='.github/workflows/pr16-circus-rental-resume.yml',
                      event='push',run_attempt=1,status='completed',conclusion='failure',
                      repository=dict(full_name=t.ops.REPO),head_repository=dict(full_name=t.ops.REPO))
        self.job=dict(id=200,run_id=100,head_sha='a'*40,status='completed',conclusion='failure',steps=[
            dict(name=n,status='completed',conclusion='success') for n in ('成否を区別して固定引継ぎと両ログを非force保存','ROMとsaveを除外して証跡を収録')])
        self.state=json.loads((ROOT/t.resume.STATE).read_bytes())
        self.backlog=json.loads((ROOT/t.resume.BACKLOG).read_bytes())
        self.state['pending_runs']=[dict(run_id=100,tested_head='a'*40,status='in_progress')]
        self.actions=[dict(id=100,head_sha='a'*40,status='completed',conclusion='failure')]

    def test_completed_failure_remains_failure(self):
        self.assertEqual(t.verify_actions(self.spec,self.run,self.job)['run']['conclusion'],'failure')

    def test_wrong_or_unfinished_run_rejected(self):
        for key,value in [('id',101),('head_sha','b'*40),('status','in_progress'),('conclusion','success'),('run_attempt',2),('event','workflow_dispatch')]:
            run=deepcopy(self.run);run[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):t.verify_actions(self.spec,run,self.job)

    def test_wrong_repo_or_failed_record_rejected(self):
        run=deepcopy(self.run);run['head_repository']['full_name']='other/repo'
        with self.assertRaises(ValueError):t.verify_actions(self.spec,run,self.job)
        job=deepcopy(self.job);job['steps'][0]['conclusion']='failure'
        with self.assertRaises(ValueError):t.verify_actions(self.spec,self.run,job)

    def test_wrong_job_rejected(self):
        for key,value in [('id',201),('run_id',101),('head_sha','b'*40),('status','in_progress')]:
            job=deepcopy(self.job);job[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):t.verify_actions(self.spec,self.run,job)

    def test_only_confirmed_pending_resolved_and_physical_gate_preserved(self):
        before=deepcopy(self.state);old=deepcopy(self.backlog)
        s,b=t.project(self.state,self.backlog,self.spec,{},self.actions,'c'*40)
        self.assertEqual(s['pending_runs'],[])
        self.assertEqual(self.state,before);self.assertEqual(self.backlog,old)
        self.assertEqual(s['candidate'],before['candidate'])
        self.assertEqual(s['last_accepted_native_run'],before['last_accepted_native_run'])
        gap=next(x for x in b['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')
        self.assertIsNone(gap['success_evidence']);self.assertFalse(gap.get('complete',False))
        self.assertEqual(s['remaining_physical_gap_ids'],before['remaining_physical_gap_ids'])
        self.assertEqual(s['remaining_p08_gate_ids'],before['remaining_p08_gate_ids'])

    def test_unresolved_pending_cannot_be_erased(self):
        self.state['pending_runs'].append(dict(run_id=999,tested_head='d'*40,status='in_progress'))
        with self.assertRaises(ValueError):t.project(self.state,self.backlog,self.spec,{},self.actions,'c'*40)

    def test_closed_physical_gate_cannot_be_reopened(self):
        next(x for x in self.backlog['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')['complete']=True
        with self.assertRaises(ValueError):t.project(self.state,self.backlog,self.spec,{},self.actions,'c'*40)

    def test_routing_mirrors_and_no_duplicate_note(self):
        s,b=t.project(self.state,self.backlog,self.spec,{},self.actions,'c'*40)
        s,b=t.project(s,b,self.spec,{},self.actions,'c'*40)
        self.assertEqual(s['bp']['next_step'],s['next_action']['goal_ja'])
        self.assertEqual(s['do_not_repeat'].count(self.spec['no_repeat_ja']),1)
        self.assertEqual(s['observed_head_checks']['runs'][0]['conclusion'],'failure')
        self.assertIn(t.REPORT,s['next_action']['read_paths'])

    def test_verify_evidence_does_not_run_native_or_compile(self):
        source=inspect.getsource(t.verify_evidence)
        self.assertIn('probe.validate(stdout,stderr,process[',source)
        self.assertNotIn('subprocess.',source)
        self.assertNotIn('reconstruct(',source)

    def test_actual24_win_original_revalidated_without_native(self):
        source=json.loads((ROOT/t.PREVIOUS).read_bytes())
        result=t.verify_evidence(source)
        self.assertEqual(result['scoped_result']['wins'],24)
        self.assertEqual(result['scoped_result']['losses'],1)
        self.assertEqual(result['scoped_result']['bp_earned'],72)
        self.assertTrue(result['standard_save_fresh_continue'])
        self.assertFalse(result['genuine_30_wins_verified'])
        self.assertTrue(result['inherited_pipeline_accounting']['ancestor_compile_reexecuted'])
        self.assertFalse(result['inherited_pipeline_accounting']['all_ancestor_arm_links_zero'])

    def test_original_cannot_be_promoted_to30_or_rebound(self):
        source=json.loads((ROOT/t.PREVIOUS).read_bytes())
        bad=deepcopy(source);bad['rental_drought_result']['genuine_30_wins_verified']=True
        with self.assertRaises(ValueError):t.verify_evidence(bad)
        bad=deepcopy(source);bad['candidate']['sha256']='0'*64
        with self.assertRaises(ValueError):t.verify_evidence(bad)

    def test_transitive_replay_count_is_not_fabricated(self):
        result=t.bootstrap_accounting()
        self.assertEqual(result['terminal_drought_payload_links'],0)
        self.assertIsNone(result['exact_ancestor_execution_count'])
        self.assertTrue(result['accepted_ring_host_test_command_reexecuted'])
        self.assertGreaterEqual(len(result['source_bindings']),5)

    def test_write_path_guards_remain(self):
        source=inspect.getsource(t.run)
        self.assertIn('changed==set(outputs)',source)
        self.assertIn('guard.guard()',source)
        self.assertIn('committed readback differs',source)
        self.assertIn('formal BP checkpoint changed',source)
        self.assertNotIn("'--force'",source)
        self.assertIn('not (ROOT/REPORT).exists()',source)

if __name__=='__main__':unittest.main()
