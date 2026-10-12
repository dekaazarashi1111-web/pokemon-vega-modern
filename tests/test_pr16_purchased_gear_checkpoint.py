"""Reject relabelled counts, replaced origins and hidden fixture boundaries."""
from copy import deepcopy
import io
import unittest
from unittest.mock import patch
import zipfile
from scripts import pr16_purchased_gear_checkpoint as m

class GearCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files=m.display.archive((m.ROOT/m.DIRECTORY/str(m.RECORD[0])/'original.zip').read_bytes())
    def mutated(self,path,change):
        files=dict(self.files);value=m.load(files[path]);change(value);files[path]=m.stable(value);return files
    def test_exact_four_process_nine_core_originals_and_58_images(self):
        value=m.verify(self.files)
        self.assertEqual((value['new_native_processes'],value['new_native_cores'],value['source_files'],len(value['reviewed_images'])),(4,9,37,58))
        self.assertEqual(value['screen_manifests_checked'],4)
        self.assertTrue(value['purchased_gear_to_battle_accepted'])
        self.assertFalse(value['full_p05_acceptance']);self.assertFalse(value['ordinary_policy_selection_accepted'])
        self.assertEqual([r['result']['fresh_cores'] for r in value['cases']],[2,2,2,3])
    def test_reject_old_schema_or_added_historical_successes(self):
        for delta in ({'schema_version':1},{'actual_new_processes':8},{'successful_fresh_cores':18},{'old_runs_relabelled':1}):
            files=self.mutated('pr16-purchased-gear/result.json',lambda v:v.update(delta))
            with self.subTest(delta=delta),self.assertRaises(ValueError):m.verify(files)
    def test_reject_scope_inflation_or_concealed_fixtures(self):
        for delta in ({'full_p05_acceptance':True},{'release_ready':True},{'ring_bp_natural_acquisition_accepted':True},{'initial_map_party_ring_bp_policy_are_fixtures':False}):
            files=self.mutated('pr16-purchased-gear/result.json',lambda v:v.update(delta))
            with self.subTest(delta=delta),self.assertRaises(ValueError):m.verify(files)
    def test_reject_wrong_head(self):
        files=dict(self.files);files[m.RECORD[7]+'tested-head.txt']=b'6dec0d4e58ffa0c7751be1e05bdd864f87d023bd\n'
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_replaced_compiled_controller(self):
        files=dict(self.files);key='pr16-purchased-gear/generated-controller.zip'
        members=m.display.archive(files[key]);members['controller.c']+=b'\n/* changed */\n';out=io.BytesIO()
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            for name,data in members.items():z.writestr(name,data)
        files[key]=out.getvalue()
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_source_binding_substitution(self):
        files=self.mutated(m.RECORD[7]+'source-bindings.json',lambda v:v.pop(m.native.SOURCE))
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_current_driver_change_without_source_matching(self):
        original=m.prior.read
        def changed(root,path):
            raw=original(root,path)
            return raw+b'\n' if str(path)==m.native.SELF else raw
        with patch.object(m.prior,'read',side_effect=changed),self.assertRaises(ValueError):m.verify(self.files)
    def test_reject_changed_raw_pixel(self):
        files=dict(self.files);key=next(k for k in files if k.endswith('native-turn.ppm'));files[key]=files[key][:-1]+bytes([files[key][-1]^1])
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_forged_screen_manifest(self):
        key='pr16-purchased-gear/eelektross-active.screens.json'
        for delta in ({'presentation_accepted':True},{'required_screens':0},{'native_result_schema':1}):
            files=self.mutated(key,lambda v:v.update(delta))
            with self.subTest(delta=delta),self.assertRaises(ValueError):m.verify(files)
    def test_reject_omitted_cold_reload_screen(self):
        key='pr16-purchased-gear/eelektross-cold-policy-reset.screens.json'
        files=self.mutated(key,lambda v:v['files'].pop('eelektross-cold-policy-reset-equipped-reloaded.ppm'))
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_ignored_failed_process(self):
        files=self.mutated('pr16-purchased-gear/eelektross-active.process.json',lambda v:v.update(returncode=1))
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_fabricated_cold_policy_persistence(self):
        key='pr16-purchased-gear/eelektross-cold-policy-reset.stdout'
        files=self.mutated(key,lambda v:v.update(mega_species=1634,ability=313))
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_hidden_midroute_restart_in_active_case(self):
        key='pr16-purchased-gear/eelektross-active.stdout'
        files=self.mutated(key,lambda v:v['witness'].update(reloaded=4500))
        with self.assertRaises(ValueError):m.verify(files)
    def test_reject_disabled_write_guard(self):
        files=self.mutated('pr16-purchased-gear/guard-register.process.json',lambda v:v.update(returncode=0))
        with self.assertRaises(ValueError):m.verify(files)
    def test_projection_preserves_accepted_data_and_does_not_close_supply(self):
        old={'full_p06_acceptance':True,'full_p05_acceptance':False,'release_ready':False,'p07_adoption':{'normal_species_to_vega_move':499,'vega_species_to_normal_move':1073},'captured_battle_checkpoint':{'captured_to_native_battle_accepted':True,'gear_to_battle_accepted':False},'remaining_conditions':[{'id':'NATURAL_CAPTURE_GEAR'},{'id':'PHYSICAL_CIRCUS_ADMISSION'}]}
        snapshot=deepcopy(old)
        with patch.object(m,'build',return_value={}),patch.object(m.prior,'read',return_value=b'{}'):
            value=m.project(old);twice=m.project(value)
        self.assertEqual(value,twice);self.assertEqual(old,snapshot)
        self.assertEqual(value['p07_adoption'],old['p07_adoption']);self.assertTrue(value['full_p06_acceptance']);self.assertFalse(value['release_ready']);self.assertFalse(value['full_p05_acceptance'])
        row=value['remaining_conditions'][0];self.assertFalse(row['gear_to_battle_required']);self.assertTrue(row['ring_bp_natural_supply_required']);self.assertTrue(row['ordinary_policy_selection_required'])
        self.assertEqual(value['remaining_conditions'][1],{'id':'PHYSICAL_CIRCUS_ADMISSION'})
        self.assertEqual(value['captured_battle_checkpoint']['purchased_gear_successor_receipt'],m.RECEIPT)

class HistoricalOriginalTests(unittest.TestCase):
    def test_prior_success_is_not_added_to_refreshed_counts(self):
        run=m.history.RECORDS['prior_success'][0]
        files=m.display.archive((m.ROOT/m.DIRECTORY/str(run)/'original.zip').read_bytes())
        value=m.history.verify('prior_success',files)
        self.assertEqual((value['historical_successful_processes'],value['historical_successful_cores'],value['new_native_passes']),(4,9,0))
        self.assertTrue(value['not_added_to_successor_counts'])
        key='pr16-purchased-gear/result.json';report=m.load(files[key]);report['successful_fresh_cores']=18;files[key]=m.stable(report)
        with self.assertRaises(ValueError):m.history.verify('prior_success',files)
    def test_probe_archive_rejects_unsafe_binary_and_paths(self):
        for name,data in [('evil.gba',b'ROM'),('../bad.txt',b'x'),('bad.txt',b'x\0y')]:
            out=io.BytesIO()
            with zipfile.ZipFile(out,'w') as z:z.writestr(name,data)
            with self.subTest(name=name),self.assertRaises(ValueError):m.history.probe_archive(out.getvalue())
    def test_failure_metadata_cannot_be_promoted(self):
        rec=m.history.RECORDS['policy_rejected'];run,aid,size,sha,head,wf,conclusion=rec
        meta=dict(run_id=run,artifact_id=aid,size=size,sha256=sha,head_sha=head,head_branch=m.prior.BRANCH,run_attempt=1,path='.github/workflows/'+wf+'.yml',artifact_name=wf,status='completed',conclusion=conclusion,jobs=[dict(run_id=run,head_sha=head,status='completed',conclusion=conclusion,steps=[dict(status='completed',conclusion='failure')])])
        m.history.metadata(meta,rec)
        meta['conclusion']='success'
        with self.assertRaises(ValueError):m.history.metadata(meta,rec)

if __name__=='__main__':unittest.main()
