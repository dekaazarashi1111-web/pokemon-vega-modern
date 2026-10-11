"""Reject promoted/altered retained evidence; never counts this as a new run."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_physical_route_checkpoint as m

class PhysicalCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files={label:m.prior.archive((ROOT/m.DIRECTORY/str(rec[0])/'original.zip').read_bytes()) for label,rec in m.RECORDS.items()}
    def test_exact_original_positive_and_no_phase_promotion(self):
        self.assertEqual(m.verify_p06(self.files['p06_current'])['unit_tests'],34)
        r=m.verify_forms(self.files['forms']);self.assertEqual(r['fresh_cores'],25)
        self.assertEqual(r['successful_form_changes'],11);self.assertEqual(r['physical_service_interactions'],15)
        self.assertFalse(r['full_p03_acceptance']);self.assertFalse(r['release_ready'])
    def test_metadata_requires_success_exact_attempt_and_head(self):
        rec=m.RECORDS['forms'];run,aid,size,sha,head,wf,name,_=rec
        good=dict(run_id=run,head_sha=head,head_branch=m.prior.BRANCH,run_attempt=1,path='.github/workflows/'+wf+'.yml',status='completed',conclusion='success',artifact_id=aid,artifact_name=name,size=size,sha256=sha,jobs=[dict(run_id=run,head_sha=head,status='completed',conclusion='success',steps=[dict(status='completed',conclusion='success')])])
        m.prior.metadata(good,rec)
        for key,value in [('head_sha','0'*40),('conclusion','failure'),('run_attempt',2),('artifact_id',0)]:
            with self.subTest(key=key),self.assertRaises(ValueError):m.prior.metadata(good|{key:value},rec)
    def test_raw_and_aggregate_scope_cannot_be_promoted(self):
        path='pr16-form-routes/result.json';source=self.files['forms'];row=m.prior.load(source[path])
        for key,value in [('release_ready',True),('full_p03_acceptance',True),('successful_fresh_cores',26),('actual_new_processes',9),('old_runs_relabelled',1)]:
            with self.subTest(key=key),self.assertRaises(ValueError):m.verify_forms(source|{path:m.prior.stable(row|{key:value})})
    def test_missing_cold_save_or_false_zero_exit_cannot_pass(self):
        source=self.files['forms'];path='pr16-form-routes/heat-roundtrip.stdout';row=m.prior.load(source[path])
        bad=deepcopy(row);bad['traces'][1]['reloaded']=0
        with self.assertRaises(ValueError):m.verify_forms(source|{path:m.prior.stable(bad)})
        path='pr16-form-routes/heat-roundtrip.process.json';proc=m.prior.load(source[path]);proc['returncode']=False
        with self.assertRaises(ValueError):m.verify_forms(source|{path:m.prior.stable(proc)})
    def test_actual_write_guard_and_rendered_witness_required(self):
        source=self.files['forms'];path='pr16-form-routes/guard-bus8.stderr'
        with self.assertRaises(ValueError):m.verify_forms(source|{path:b'PASS'})
        path='pr16-form-routes/heat-roundtrip-0-root.ppm'
        with self.assertRaises(ValueError):m.verify_forms(source|{path:b'P6\n240 160\n255\n'+bytes(115200)})
    def test_p06_mirror_and_zero_new_execution_must_remain_exact(self):
        source=self.files['p06_current'];path='current-view.json';row=m.prior.load(source[path]);row['p06_adoption']['full_phase_accepted']=False
        with self.assertRaises(ValueError):m.verify_p06(source|{path:m.prior.stable(row)})
        path='check.json';row=m.prior.load(source[path]);row['new_emulator_runs']=1
        with self.assertRaises(ValueError):m.verify_p06(source|{path:m.prior.stable(row)})
    def test_happiny_exact_cycles_incense_and_parent_scope(self):
        source=self.files['happiny'];value=m.verify_happiny(source)
        self.assertEqual(value['fresh_cores'],15);self.assertEqual(value['historical_preserved_moves'],[461,464,357])
        self.assertFalse(value['full_p07_acceptance'])
        p='pr16-happiny-breeding/no-incense-chansey.stdout';row=m.prior.load(source[p]);row['child_species']=364
        with self.assertRaises(ValueError):m.verify_happiny(source|{p:m.prior.stable(row)})
    def test_projection_is_idempotent_preserves_policies_and_unclosed_conditions(self):
        before=dict(final_integration={'source_path':m.prior.RECEIPT},full_p03_acceptance=False,full_p05_acceptance=False,full_p07_acceptance=False,full_p06_acceptance=True,release_ready=False,repository_policy={'visibility':'public'},archive_economy={'cost':0},remaining_conditions=[{'id':'EVOLUTION_FORM_OTHER_EGG'},{'id':'PHYSICAL_CIRCUS_ADMISSION','resume':'unchanged'}])
        saved=deepcopy(before);receipt={'synthetic_unit_only':True}
        with patch.object(m,'build',return_value=receipt),patch.object(m.prior,'read',return_value=m.prior.stable(receipt)):
            after=m.project(before);twice=m.project(after)
        self.assertEqual(before,saved);self.assertEqual(after,twice)
        for k in ('repository_policy','archive_economy','full_p06_acceptance','full_p03_acceptance','full_p05_acceptance','full_p07_acceptance','release_ready'):self.assertEqual(after[k],before[k])
        self.assertEqual(after['remaining_conditions'][1],before['remaining_conditions'][1]);self.assertEqual(len(after['remaining_conditions']),2)

if __name__=='__main__':unittest.main()
