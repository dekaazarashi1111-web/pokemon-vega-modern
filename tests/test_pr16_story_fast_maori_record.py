"""New metadata-only rejection tests. No native replay or network."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_fast_maori_record as r

def fixture():
    run=dict(id=r.RUN,head_sha=r.SOURCE,head_branch='codex/modernization-followup-20260908',path='.github/workflows/pr16-story-fast-maori.yml',status='completed',conclusion='success',run_attempt=1)
    names=['Set up job','Run actions/checkout@v4','Fixed resume integrity without native acceptance replay','New Maori176 and independent cold20 only','Lightweight task graph','Run actions/upload-artifact@v4','Post Run actions/checkout@v4','Complete job']
    jobs=dict(total_count=1,jobs=[dict(id=109201289995,run_id=r.RUN,name='measurement',status='completed',conclusion='success',steps=[dict(name=n,status='completed',conclusion='success') for n in names])])
    return run,jobs

class RecordTests(unittest.TestCase):
    def test_completed(self):
        run,jobs=fixture();self.assertEqual(r.completed(run,jobs)['run'],run)
    def test_incomplete_or_foreign_run(self):
        for k,v in [('id',1),('head_sha','f'*40),('head_branch','main'),('path','other'),('status','in_progress'),('conclusion','failure'),('run_attempt',True),('run_attempt',2)]:
            run,jobs=fixture();run[k]=v
            with self.subTest(key=k),self.assertRaises(ValueError):r.completed(run,jobs)
    def test_incomplete_job_page(self):
        run,jobs=fixture();jobs['total_count']=2
        with self.assertRaises(ValueError):r.completed(run,jobs)
    def test_post_step_failure(self):
        run,jobs=fixture();jobs['jobs'][0]['steps'][-2]['conclusion']='failure'
        with self.assertRaises(ValueError):r.completed(run,jobs)
    def test_skipped_upload(self):
        run,jobs=fixture();jobs['jobs'][0]['steps'][5]['conclusion']='skipped'
        with self.assertRaises(ValueError):r.completed(run,jobs)
    def test_missing_final_step(self):
        run,jobs=fixture();jobs['jobs'][0]['steps'].pop()
        with self.assertRaises(ValueError):r.completed(run,jobs)
    def test_wrong_job(self):
        run,jobs=fixture();jobs['jobs'][0]['id']=1
        with self.assertRaises(ValueError):r.completed(run,jobs)
    def test_artifact(self):
        a=dict(id=r.ARTIFACT,size_in_bytes=r.ARCHIVE['size'],digest='sha256:'+r.ARCHIVE['sha256'],expired=False,name='pr16-story-fast-maori-checkpoint',workflow_run=dict(id=r.RUN,head_sha=r.SOURCE))
        r.artifact_meta(a)
        for k,v in [('id',1),('expired',True),('size_in_bytes',0),('digest','sha256:0'),('name','other'),('workflow_run',dict(id=r.RUN,head_sha='f'*40))]:
            b=deepcopy(a);b[k]=v
            with self.subTest(key=k),self.assertRaises(ValueError):r.artifact_meta(b)
if __name__=='__main__':unittest.main()
