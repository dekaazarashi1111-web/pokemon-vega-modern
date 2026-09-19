from pathlib import Path
import hashlib
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_drought_launch_boundary_resume as t

class ResumeBindingTests(unittest.TestCase):
    def test_git_blob_matches_git_object_rule(self):
        raw=b'abc\n';self.assertEqual(t.git_blob(raw),hashlib.sha1(b'blob 4\0abc\n').hexdigest())
    def test_commit_scope_is_exact_and_add_only(self):
        value=t.validate_commit_scope('a'*40,t.BASE_HEAD,list(reversed(t.NEW_FILES)),list(t.NEW_FILES))
        self.assertTrue(value['added_only'])
        with self.assertRaises(ValueError):t.validate_commit_scope('a'*40,t.BASE_HEAD,[*t.NEW_FILES,'extra'],list(t.NEW_FILES))
        with self.assertRaises(ValueError):t.validate_commit_scope('a'*40,'b'*40,list(t.NEW_FILES),list(t.NEW_FILES))
    def test_stale_run_requires_prepare_only_failure(self):
        run={'id':t.STALE_RUN,'head_sha':t.STALE_HEAD,'status':'completed','conclusion':'failure'}
        steps=[{'number':3,'name':'既存失敗原本とreadonly境界scopeを非force保存','conclusion':'failure'}]
        steps += [{'number':n,'name':'x','conclusion':'skipped'} for n in (4,5,6,7)]
        jobs={'total_count':1,'jobs':[{'id':t.STALE_JOB,'conclusion':'failure','steps':steps}]}
        value=t.validate_stale_run(run,jobs,{'total_count':0,'artifacts':[]})
        self.assertEqual(value['native_processes'],0)
        jobs['jobs'][0]['steps'][1]['conclusion']='success'
        with self.assertRaises(ValueError):t.validate_stale_run(run,jobs,{'total_count':0,'artifacts':[]})
    def test_rebind_changes_only_expected_entries(self):
        script=b'new-script';test=b'new-test';new={p:(p+'\n').encode() for p in t.NEW_FILES}
        old_bindings={t.BOUNDARY_SCRIPT:dict(t.OLD_BINDINGS[t.BOUNDARY_SCRIPT]),t.BOUNDARY_TEST:dict(t.OLD_BINDINGS[t.BOUNDARY_TEST]),'keep':{'size':1,'sha256':'x'}}
        old_blobs=dict(t.BOUNDARY_BLOBS)
        try:
            t.BOUNDARY_BLOBS[t.BOUNDARY_SCRIPT]=t.git_blob(script);t.BOUNDARY_BLOBS[t.BOUNDARY_TEST]=t.git_blob(test)
            state,changes=t.rebind({'source_bindings':old_bindings},{t.BOUNDARY_SCRIPT:script,t.BOUNDARY_TEST:test},new)
        finally:t.BOUNDARY_BLOBS.clear();t.BOUNDARY_BLOBS.update(old_blobs)
        self.assertEqual(state['source_bindings']['keep'],{'size':1,'sha256':'x'})
        self.assertEqual(state['source_bindings'][t.BOUNDARY_SCRIPT],t.identity(script))
        self.assertEqual(set(changes),{t.BOUNDARY_SCRIPT,t.BOUNDARY_TEST,*t.NEW_FILES})
        self.assertEqual(old_bindings[t.BOUNDARY_SCRIPT],t.OLD_BINDINGS[t.BOUNDARY_SCRIPT])
    def test_rebind_rejects_old_binding_or_blob_drift(self):
        script=b'new-script';test=b'new-test';new={p:b'x' for p in t.NEW_FILES}
        state={'source_bindings':{t.BOUNDARY_SCRIPT:{'size':0,'sha256':'bad'},t.BOUNDARY_TEST:dict(t.OLD_BINDINGS[t.BOUNDARY_TEST])}}
        with self.assertRaises(ValueError):t.rebind(state,{t.BOUNDARY_SCRIPT:script,t.BOUNDARY_TEST:test},new)

if __name__=='__main__':unittest.main()
