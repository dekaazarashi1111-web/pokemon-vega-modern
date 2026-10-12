"""新しい完了記録の境界だけを検査。Wiki/ROM/旧受入は実行しない。"""
import copy
import unittest
from scripts.pr16_learnset_wiki_closeout import validate_completion


class CompletionTests(unittest.TestCase):
    def setUp(self):
        head='a'*40;branch='codex/modernization-followup-20260908'
        self.cp={'run_id':7,'source_head':head}
        self.run={'id':7,'head_sha':head,'head_branch':branch,'repository':{'full_name':'dekaazarashi1111-web/pokemon-vega-modern'},
            'status':'completed','conclusion':'success','event':'push','path':'.github/workflows/pr16-learnset-wiki-publish.yml',
            'created_at':'fixed','updated_at':'fixed'}
        steps=[{'name':n,'status':'completed','conclusion':'success'} for n in ('同branchへ非force commit/push','Run actions/upload-artifact@v4','Run actions/upload-artifact@v4')]
        steps.append({'name':'失敗時だけ公開処理のdiagnosticを保存','status':'completed','conclusion':'skipped'})
        self.jobs={'total_count':1,'jobs':[{'id':8,'run_id':7,'head_sha':head,'name':'wiki-publish',
            'status':'completed','conclusion':'success','steps':steps}]}
        self.artifact={'name':'pr16-learnset-wiki-proof','expired':False,'digest':'sha256:'+'b'*64,
            'workflow_run':{'id':7,'head_sha':head,'head_branch':branch}}
    def check(self):return validate_completion(self.cp,self.run,self.jobs,self.artifact)
    def reject(self):
        with self.assertRaises(ValueError):self.check()
    def test_success_is_readonly(self):
        before=copy.deepcopy((self.cp,self.run,self.jobs,self.artifact))
        self.assertEqual(self.check()['id'],7);self.assertEqual(before,(self.cp,self.run,self.jobs,self.artifact))
    def test_failed_run_rejected(self):self.run['conclusion']='failure';self.reject()
    def test_incomplete_run_rejected(self):self.run['status']='in_progress';self.reject()
    def test_wrong_head_rejected(self):self.run['head_sha']='c'*40;self.reject()
    def test_wrong_branch_rejected(self):self.run['head_branch']='main';self.reject()
    def test_wrong_workflow_rejected(self):self.run['path']='other.yml';self.reject()
    def test_wrong_event_rejected(self):self.run['event']='pull_request';self.reject()
    def test_incomplete_jobs_rejected(self):self.jobs['total_count']=2;self.reject()
    def test_failed_job_rejected(self):self.jobs['jobs'][0]['conclusion']='failure';self.reject()
    def test_skipped_step_rejected(self):self.jobs['jobs'][0]['steps'][0]['conclusion']='skipped';self.reject()
    def test_expired_artifact_rejected(self):self.artifact['expired']=True;self.reject()
    def test_missing_optional_step_rejected(self):self.jobs['jobs'][0]['steps'].pop();self.reject()
    def test_executed_failure_step_rejected(self):self.jobs['jobs'][0]['steps'][-1]['conclusion']='success';self.reject()
    def test_wrong_artifact_head_rejected(self):self.artifact['workflow_run']['head_sha']='d'*40;self.reject()


if __name__=='__main__':unittest.main()
