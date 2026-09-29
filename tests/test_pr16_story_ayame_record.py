"""Save18 original terminal metadata gates only: no emulator or accepted suite."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_ayame_record as m


def fixture():
    run=dict(id=m.RUN,head_sha=m.SOURCE,head_branch=m.m.source.BRANCH,
             path='.github/workflows/pr16-story-ayame.yml',status='completed',conclusion='success',run_attempt=1)
    job=dict(id=m.JOB,run_id=m.RUN,name='continuation',status='completed',conclusion='success',
             steps=[dict(name=n,status='completed',conclusion='success') for n in m.STEPS])
    return run,dict(total_count=1,jobs=[job])


def artifact():
    return dict(id=m.ARTIFACT,name='pr16-story-ayame-checkpoint',size_in_bytes=m.ARCHIVE['size'],
                digest='sha256:'+m.ARCHIVE['sha256'],expired=False,
                workflow_run=dict(id=m.RUN,head_sha=m.SOURCE))


class TerminalTests(unittest.TestCase):
    def reject_run(self,key,value):
        run,jobs=fixture();run[key]=value
        with self.assertRaises(ValueError):m.completed(run,jobs)
    def test_successful_original(self):
        run,jobs=fixture();before=copy.deepcopy((run,jobs))
        self.assertEqual(m.completed(run,jobs)['job']['id'],m.JOB)
        self.assertEqual((run,jobs),before)
    def test_pending_run_rejected(self):self.reject_run('status','in_progress')
    def test_failed_run_rejected(self):self.reject_run('conclusion','failure')
    def test_wrong_source_rejected(self):self.reject_run('head_sha','0'*40)
    def test_wrong_branch_rejected(self):self.reject_run('head_branch','main')
    def test_wrong_workflow_rejected(self):self.reject_run('path','.github/workflows/pr16-story-after-maori.yml')
    def test_wrong_run_id_rejected(self):self.reject_run('id',m.RUN-1)
    def test_second_attempt_rejected(self):self.reject_run('run_attempt',2)
    def test_boolean_attempt_rejected(self):self.reject_run('run_attempt',True)
    def test_job_page_incomplete_rejected(self):
        run,jobs=fixture();jobs['total_count']=2
        with self.assertRaises(ValueError):m.completed(run,jobs)
    def test_boolean_job_count_rejected(self):
        run,jobs=fixture();jobs['total_count']=True
        with self.assertRaises(ValueError):m.completed(run,jobs)
    def test_job_identity_status_rejected(self):
        for key,value in [('id',m.JOB-1),('run_id',m.RUN-1),('name','other'),('status','in_progress'),('conclusion','failure')]:
            run,jobs=fixture();jobs['jobs'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.completed(run,jobs)
    def test_missing_post_upload_or_complete_rejected(self):
        for index in (4,5,6):
            run,jobs=fixture();del jobs['jobs'][0]['steps'][index]
            with self.subTest(index=index),self.assertRaises(ValueError):m.completed(run,jobs)
    def test_each_step_must_complete_successfully(self):
        for index in range(7):
            for key,value in [('status','in_progress'),('conclusion','skipped'),('conclusion','failure')]:
                run,jobs=fixture();jobs['jobs'][0]['steps'][index][key]=value
                with self.subTest(index=index,key=key,value=value),self.assertRaises(ValueError):m.completed(run,jobs)
    def test_duplicated_or_reordered_steps_rejected(self):
        for index in (0,6):
            run,jobs=fixture();jobs['jobs'][0]['steps'][index]=copy.deepcopy(jobs['jobs'][0]['steps'][3])
            with self.subTest(index=index),self.assertRaises(ValueError):m.completed(run,jobs)
    def test_empty_job_page_rejected(self):
        run,jobs=fixture();jobs['jobs']=[]
        with self.assertRaises(ValueError):m.completed(run,jobs)


class ArtifactTests(unittest.TestCase):
    def reject(self,key,value):
        meta=artifact();meta[key]=value
        with self.assertRaises(ValueError):m.artifact_meta(meta)
    def test_exact_original(self):m.artifact_meta(artifact())
    def test_expired_or_missing_state_rejected(self):
        for value in (True,None,0):
            with self.subTest(value=value):self.reject('expired',value)
    def test_wrong_identity_rejected(self):self.reject('id',m.ARTIFACT-1)
    def test_wrong_name_rejected(self):self.reject('name','pr16-story-after-maori-checkpoint')
    def test_wrong_size_rejected(self):self.reject('size_in_bytes',m.ARCHIVE['size']-1)
    def test_wrong_digest_rejected(self):self.reject('digest','sha256:'+'0'*64)
    def test_wrong_run_rejected(self):self.reject('workflow_run',dict(id=m.RUN-1,head_sha=m.SOURCE))
    def test_wrong_source_rejected(self):self.reject('workflow_run',dict(id=m.RUN,head_sha='0'*40))


if __name__=='__main__':unittest.main()
