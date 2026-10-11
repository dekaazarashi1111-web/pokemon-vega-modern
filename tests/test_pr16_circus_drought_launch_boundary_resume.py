from copy import deepcopy
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_drought_launch_boundary_resume as t

class ResumeBindingTests(unittest.TestCase):
    def test_git_blob_matches_git_object_rule(self):
        raw=b'abc\n';self.assertEqual(t.git_blob(raw),hashlib.sha1(b'blob 4\0abc\n').hexdigest())
    def test_commit_scope_is_exact_and_add_only(self):
        value=t.validate_commit_scope('a'*40,t.RETRY_PARENT,list(reversed(t.NEW_FILES)),list(t.NEW_FILES))
        self.assertTrue(value['added_only'])
        with self.assertRaises(ValueError):t.validate_commit_scope('a'*40,t.RETRY_PARENT,[*t.NEW_FILES,'extra'],list(t.NEW_FILES))
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
    def failure_fixture(self,run_id,job_id,head):
        run={'id':run_id,'head_sha':head,'status':'completed','conclusion':'failure'}
        steps=[{'number':3,'name':'source binding差分を親HEADとblobで固定して先行保存','conclusion':'failure'}]
        steps += [{'number':n,'name':'x','conclusion':'skipped'} for n in (4,5,6,7,8)]
        return run,{'total_count':1,'jobs':[{'id':job_id,'conclusion':'failure','steps':steps}]},{'total_count':0,'artifacts':[]}
    def test_render_sync_run_requires_reconcile_only_failure(self):
        run,jobs,artifacts=self.failure_fixture(t.RENDER_RUN,t.RENDER_JOB,t.RENDER_HEAD)
        self.assertEqual(t.validate_render_run(run,jobs,artifacts)['native_processes'],0)
        jobs['jobs'][0]['steps'][-1]['conclusion']='success'
        with self.assertRaises(ValueError):t.validate_render_run(run,jobs,artifacts)
    def test_path_failure_is_not_native_or_success(self):
        args=self.failure_fixture(t.PATH_RUN,t.PATH_JOB,t.PATH_HEAD)
        value=t.validate_path_run(*args)
        self.assertEqual(value['native_processes'],0)
        self.assertEqual(value['original_conclusion'],'failure')
        self.assertEqual(value['artifacts'],0)
        for key,value in (('id',0),('head_sha','a'*40),('status','in_progress'),('conclusion','success')):
            run,jobs,artifacts=deepcopy(args);run[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):t.validate_path_run(run,jobs,artifacts)
    def test_path_failure_rejects_executed_or_missing_step_and_artifact(self):
        args=self.failure_fixture(t.PATH_RUN,t.PATH_JOB,t.PATH_HEAD)
        for index in range(1,6):
            run,jobs,artifacts=deepcopy(args);jobs['jobs'][0]['steps'][index]['conclusion']='success'
            with self.subTest(index=index),self.assertRaises(ValueError):t.validate_path_run(run,jobs,artifacts)
        run,jobs,artifacts=deepcopy(args);jobs['jobs'][0]['steps'].pop()
        with self.assertRaises(ValueError):t.validate_path_run(run,jobs,artifacts)
        run,jobs,artifacts=deepcopy(args);artifacts['artifacts']=[{'id':1}]
        with self.assertRaises(ValueError):t.validate_path_run(run,jobs,artifacts)
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
    def reference(self):
        return dict(path=t.REPORT,classification='CIRCUS_DROUGHT_BOUNDARY_SOURCE_BINDING_RECONCILED',run_id=123)
    def test_parent_reference_is_a_real_git_diff_without_acceptance_change(self):
        state={'accepted':{'bp':True}};loss={'classification':'OPEN','physical_admission_accepted':False,'evidence':[1]}
        new_state,new_loss=t.bind_checkpoint_reports(state,loss,self.reference())
        self.assertEqual(state,{'accepted':{'bp':True}})
        self.assertEqual(loss,{'classification':'OPEN','physical_admission_accepted':False,'evidence':[1]})
        self.assertEqual({k:v for k,v in new_loss.items() if k!='drought_launch_boundary_binding'},loss)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            def git(*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.DEVNULL,text=True)
            git('init','-q');git('config','user.name','test');git('config','user.email','test@example.invalid')
            for name,value in (('state.json',state),('loss.json',loss)):(root/name).write_bytes(t.stable(value))
            git('add','.');git('commit','-qm','fixture')
            for name,value in (('state.json',new_state),('loss.json',new_loss)):(root/name).write_bytes(t.stable(value))
            self.assertEqual(set(git('diff','--name-only').splitlines()),{'loss.json','state.json'})
        new_state['circus_drought_launch_boundary_binding']['run_id']=456
        self.assertEqual(new_loss['drought_launch_boundary_binding']['run_id'],123)
    def test_parent_reference_rejects_duplicate_or_invalid_identity(self):
        ref=self.reference();state,loss=t.bind_checkpoint_reports({}, {},ref)
        with self.assertRaises(ValueError):t.bind_checkpoint_reports(state,loss,ref)
        for key,value in (('path','other'),('classification','ACCEPTED'),('run_id',True),('run_id',0)):
            bad=dict(ref);bad[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):t.bind_checkpoint_reports({}, {},bad)

if __name__=='__main__':unittest.main()
