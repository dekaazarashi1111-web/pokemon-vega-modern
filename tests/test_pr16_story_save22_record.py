"""完了終端と実行会計の22拒否試験。native/受入68試験を呼ばない。"""
import copy
import json
import tempfile
from unittest.mock import patch
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save22_record as m


def fixture():
    run=dict(id=m.RUN,head_sha=m.SOURCE,head_branch=m.m.source.BRANCH,path=m.MEASURE_WF,
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


class OriginalBytes(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.folder=self.root/'original';self.folder.mkdir()
        (self.folder/'value.txt').write_bytes(b'original\n')
        self.manifest={'value.txt':m.m.identity(b'original\n')}
        self.write_manifest()
    def write_manifest(self):
        (self.folder/'manifest.json').write_text(json.dumps(self.manifest))
    def test_manifest_original_without_mutation(self):
        before=(self.folder/'manifest.json').read_bytes()
        self.assertEqual(m.members(self.folder,1),self.manifest)
        self.assertEqual((self.folder/'manifest.json').read_bytes(),before)
    def test_manifest_boolean_count_rejected(self):
        with self.assertRaises(ValueError):m.members(self.folder,True)
    def test_manifest_missing_member_rejected(self):
        (self.folder/'value.txt').unlink()
        with self.assertRaises(ValueError):m.members(self.folder,1)
    def test_manifest_extra_member_rejected(self):
        (self.folder/'extra.txt').write_text('unexpected')
        with self.assertRaises(ValueError):m.members(self.folder,1)
    def test_manifest_corrupt_member_rejected(self):
        (self.folder/'value.txt').write_text('changed')
        with self.assertRaises(ValueError):m.members(self.folder,1)
    def test_manifest_symlink_rejected(self):
        (self.folder/'alias.txt').symlink_to(self.folder/'value.txt')
        with self.assertRaises(ValueError):m.members(self.folder,1)
    def test_manifest_unsafe_names_rejected_before_read(self):
        for name in ('../outside','/absolute','a\\b','a/../b','./value.txt','manifest.json'):
            self.manifest={name:m.m.identity(b'original\n')};self.write_manifest()
            with self.subTest(name=name),self.assertRaises(ValueError):m.members(self.folder,1)
    def test_expected_original_recovery_without_native(self):
        raw=b'{}\n';binding=m.m.identity(raw)
        (self.folder/'expected.json').write_bytes(raw)
        dest=self.root/'new'/'expected.json'
        with patch.object(m,'EXPECTED',binding),patch.object(m.m,'decode_plan') as decode,patch('subprocess.run',side_effect=AssertionError('native forbidden')):
            m.recover_expected(self.folder,dest,binding)
            decode.assert_called_once_with({})
        self.assertEqual(dest.read_bytes(),raw)
        self.assertEqual((self.folder/'expected.json').read_bytes(),raw)
    def test_expected_wrong_binding_or_content_rejected_without_write(self):
        raw=b'{}\n';binding=m.m.identity(raw);dest=self.root/'new.json'
        for bad_binding,bad_raw in ((dict(size=3,sha256='0'*64),raw),(binding,b'changed')):
            (self.folder/'expected.json').write_bytes(bad_raw)
            with patch.object(m,'EXPECTED',binding),self.assertRaises(ValueError):m.recover_expected(self.folder,dest,bad_binding)
            self.assertFalse(dest.exists())
    def test_expected_existing_destination_never_overwritten(self):
        raw=b'{}\n';binding=m.m.identity(raw);dest=self.root/'existing.json';dest.write_bytes(b'keep')
        (self.folder/'expected.json').write_bytes(raw)
        with patch.object(m,'EXPECTED',binding),patch.object(m.m,'decode_plan'),self.assertRaises(ValueError):m.recover_expected(self.folder,dest,binding)
        self.assertEqual(dest.read_bytes(),b'keep')


if __name__=='__main__':unittest.main()
