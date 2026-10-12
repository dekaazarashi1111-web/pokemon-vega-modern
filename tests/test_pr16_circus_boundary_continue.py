"""再開時のタグ・実行境界・保存patch不変性を検証する。"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_boundary_continue as t

class ContinueTests(unittest.TestCase):
    def fixture(self):
        return (dict(id=t.PRIOR_RUN,head_sha=t.PRIOR_HEAD,status='completed',conclusion='failure'),
            dict(total_count=1,jobs=[dict(id=t.PRIOR_JOB,conclusion='failure',steps=[dict(number=i,conclusion=c) for i,c in [(3,'success'),(4,'failure'),*[(i,'skipped') for i in range(5,9)]]])]),
            dict(recording_run=t.PRIOR_RUN,parent_loss_reference_bound=True,classification='CIRCUS_DROUGHT_BOUNDARY_SOURCE_BINDING_RECONCILED'))
    def test_prior_success_checkpoint_is_not_native_success(self):
        v=t.prior_result(*self.fixture());self.assertEqual(v['native_processes'],0);self.assertTrue(v['binding_checkpoint_succeeded'])
        self.assertEqual(v['original_conclusion'],'failure')
    def test_rejects_any_execution_after_failed_prepare(self):
        for i in range(2,6):
            run,jobs,binding=self.fixture();jobs['jobs'][0]['steps'][i]['conclusion']='success'
            with self.subTest(step=i),self.assertRaises(ValueError):t.prior_result(run,jobs,binding)
    def test_rejects_unrecorded_binding(self):
        run,jobs,binding=self.fixture();binding['parent_loss_reference_bound']=False
        with self.assertRaises(ValueError):t.prior_result(run,jobs,binding)
    def test_run_tag_is_stable_unique_and_strict(self):
        self.assertEqual(t.task_for_run('123'),t.task_for_run('123'))
        self.assertNotEqual(t.task_for_run('123'),t.task_for_run('124'))
        self.assertNotIn('USER-20260919-CIRCUS-DROUGHT-LAUNCH-BOUNDARY-PREPARED',t.task_for_run('123')+'-PREPARED')
        for value in (None,True,123,'0','-1','１２','12\n','1/2'):
            with self.subTest(value=value),self.assertRaises(ValueError):t.task_for_run(value)
    def recipe(self):
        raw=b'abcdefgh';new=b'abXYefgh';actual={'source.py':b'source'}
        recipe=dict(parent=t.identity(raw),candidate=t.identity(new),source_bindings={p:t.identity(v) for p,v in actual.items()},
            patches=[dict(name='fixture',offset=2,before=b'cd'.hex(),after=b'XY'.hex())],
            allocation={'allocations':[dict(start=2,end_exclusive=4,content_sha256=t.identity(b'XY')['sha256'])]})
        return raw,recipe,actual
    def test_reconstruct_uses_saved_patches_without_mutating_recipe(self):
        raw,recipe,actual=self.recipe();before=deepcopy(recipe)
        self.assertEqual(t.restore_candidate(raw,recipe,actual),b'abXYefgh');self.assertEqual(recipe,before)
    def test_reconstruction_rejects_parent_source_candidate_and_allocation_drift(self):
        for kind in ('parent','source','candidate','allocation','preimage'):
            raw,recipe,actual=self.recipe()
            if kind=='parent':raw=b'Abcdefgh'
            elif kind=='source':actual['source.py']=b'drift'
            elif kind=='candidate':recipe['candidate']['sha256']='0'*64
            elif kind=='allocation':recipe['allocation']['allocations'][0]['content_sha256']='0'*64
            else:recipe['patches'][0]['before']='0000'
            with self.subTest(kind=kind),self.assertRaises(ValueError):t.restore_candidate(raw,recipe,actual)
    def test_configure_routes_child_commands_to_new_driver(self):
        for _ in range(2):
            base,d,b=t.configure()
            self.assertEqual(b.SELF,t.SELF);self.assertEqual(d.SELF,t.SELF)
            self.assertTrue(set(t.FILES)<=set(d.FILES));self.assertEqual(len(d.FILES),len(set(d.FILES)))
    def test_test_import_preserves_driver_provenance_and_no_recursive_configure(self):
        import runpy
        old=t.boundary.configure
        try:
            t.boundary.configure=t.configure
            other=runpy.run_path(str(ROOT/t.SELF),run_name='test_copy')
            self.assertIs(other['_original_configure'],t._original_configure)
            self.assertIs(t.boundary.configure,t.configure)
            other['configure']()
        finally:t.boundary.configure=old
    def test_reconstruction_has_no_compile_or_native_execution(self):
        import inspect
        text=inspect.getsource(t.reconstruct)
        self.assertNotIn('compile_bridge(',text);self.assertNotIn('boundary.reconstruct(',text)
        self.assertNotIn('.native(',text);self.assertIn('d.c.f.reconstruct()',text)

if __name__=='__main__':unittest.main()
