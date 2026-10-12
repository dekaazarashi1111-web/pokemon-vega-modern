"""完了終端と実行会計の12拒否試験。native/受入60試験を呼ばない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_hm05_record as m


def fixture():
    run=dict(id=m.RUN,head_sha=m.SOURCE,head_branch=m.m.source.BRANCH,path=m.measure.WF,
        status='completed',conclusion='success',run_attempt=1)
    jobs=dict(total_count=1,jobs=[dict(id=m.JOB,run_id=m.RUN,name='continuation',status='completed',conclusion='success',
        steps=[dict(name=n,status='completed',conclusion='success') for n in m.STEPS])])
    return run,jobs


class Completion(unittest.TestCase):
    def test_completed_original_without_mutation(self):
        run,jobs=fixture();before=copy.deepcopy((run,jobs));m.terminal(run,jobs);self.assertEqual((run,jobs),before)
    def test_each_run_identity_and_status_required(self):
        run,jobs=fixture()
        for key,value in run.items():
            bad=copy.deepcopy(run);bad[key]=value+1 if type(value) is int else 'wrong'
            with self.subTest(key=key),self.assertRaises(ValueError):m.terminal(bad,jobs)
    def test_boolean_run_attempt_rejected(self):
        run,jobs=fixture();run['run_attempt']=True
        with self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_all_jobs_page_required(self):
        for count in (0,2,True):
            run,jobs=fixture();jobs['total_count']=count
            with self.subTest(count=count),self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_missing_job_rejected(self):
        run,jobs=fixture();jobs['jobs']=[]
        with self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_wrong_job_identity_and_status_rejected(self):
        for key,value in [('id',0),('run_id',0),('name','other'),('status','in_progress'),('conclusion','failure')]:
            run,jobs=fixture();jobs['jobs'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_each_step_missing_rejected(self):
        for i in range(len(m.STEPS)):
            run,jobs=fixture();del jobs['jobs'][0]['steps'][i]
            with self.subTest(step=i),self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_each_step_must_be_complete_success(self):
        for i in range(len(m.STEPS)):
            for key,value in [('status','in_progress'),('conclusion','skipped'),('conclusion','failure')]:
                run,jobs=fixture();jobs['jobs'][0]['steps'][i][key]=value
                with self.subTest(step=i,key=key,value=value),self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_duplicate_or_reordered_step_rejected(self):
        run,jobs=fixture();jobs['jobs'][0]['steps'][0]=copy.deepcopy(jobs['jobs'][0]['steps'][1])
        with self.assertRaises(ValueError):m.terminal(run,jobs)
    def test_original_execution_accounting(self):m.counts(copy.deepcopy(m.COUNTS))
    def test_modified_missing_or_boolean_accounting_rejected(self):
        for key,value in m.COUNTS.items():
            for kind in ('change','missing','boolean'):
                data=copy.deepcopy(m.COUNTS)
                if kind=='missing':del data[key]
                elif kind=='boolean':data[key]=not value if type(value) is bool else bool(value)
                else:data[key]=not value if type(value) is bool else value+1 if type(value) is int else 'wrong'
                with self.subTest(key=key,kind=kind),self.assertRaises(ValueError):m.counts(data)
    def test_no_native_or_accepted_tests_in_completion_gates(self):
        import unittest.mock
        with unittest.mock.patch('subprocess.run',side_effect=AssertionError('process forbidden')):
            run,jobs=fixture();m.terminal(run,jobs);m.counts(copy.deepcopy(m.COUNTS))


if __name__=='__main__':unittest.main()
