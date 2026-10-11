"""新規の記録ゲートだけ。保存/戦闘/既受入34・19試験は再実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).resolve().parents[1])]
import pr16_story_after_maori_record as r

class RecordTests(unittest.TestCase):
    def fixture(self):
        run=dict(id=r.RUN,head_sha=r.SOURCE,head_branch=r.m.source.BRANCH,
            path='.github/workflows/pr16-story-after-maori.yml',status='completed',conclusion='success',run_attempt=1)
        job=dict(id=r.JOB,run_id=r.RUN,name='continuation',status='completed',conclusion='success',
            steps=[dict(name=x,status='completed',conclusion='success') for x in r.STEP_NAMES])
        return run,dict(total_count=1,jobs=[job])
    def reject(self,run_key=None,value=None,step=None):
        a,b=self.fixture()
        if run_key:a[run_key]=value
        else:b['jobs'][0]['steps'][step]['conclusion']=value
        with self.assertRaises(ValueError):r.completed(a,b)
    def test_exact_terminal(self):
        a,b=self.fixture();self.assertEqual(r.completed(a,b)['job']['id'],r.JOB)
    def test_wrong_source(self):self.reject('head_sha','0'*40)
    def test_wrong_branch(self):self.reject('head_branch','main')
    def test_pending(self):self.reject('status','in_progress')
    def test_failure(self):self.reject('conclusion','failure')
    def test_rerun(self):self.reject('run_attempt',2)
    def test_bool_attempt(self):self.reject('run_attempt',True)
    def test_skipped_measurement(self):self.reject(value='skipped',step=2)
    def test_failed_upload(self):self.reject(value='failure',step=4)
    def test_failed_post(self):self.reject(value='failure',step=5)
    def test_missing_tail(self):
        a,b=self.fixture();b['jobs'][0]['steps'].pop()
        with self.assertRaises(ValueError):r.completed(a,b)
    def test_extra_page(self):
        a,b=self.fixture();b['total_count']=2
        with self.assertRaises(ValueError):r.completed(a,b)
    def meta(self):
        return dict(id=r.ARTIFACT,size_in_bytes=r.ARCHIVE['size'],digest='sha256:'+r.ARCHIVE['sha256'],
            expired=False,name='pr16-story-after-maori-checkpoint',workflow_run=dict(id=r.RUN,head_sha=r.SOURCE))
    def test_exact_artifact(self):r.artifact_meta(self.meta())
    def test_expired_artifact(self):
        v=self.meta();v['expired']=True
        with self.assertRaises(ValueError):r.artifact_meta(v)
    def test_wrong_artifact_digest(self):
        v=self.meta();v['digest']='sha256:'+'0'*64
        with self.assertRaises(ValueError):r.artifact_meta(v)
    def test_wrong_artifact_source(self):
        v=self.meta();v['workflow_run']['head_sha']='0'*40
        with self.assertRaises(ValueError):r.artifact_meta(v)

if __name__=='__main__':unittest.main()
