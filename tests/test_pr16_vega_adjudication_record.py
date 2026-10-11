"""記録契約だけの12境界。受入済み採取/裁定/nativeを呼ばない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_vega_adjudication_record as r
from tools.pr16_vega_original_baseline import SourceError


def fixture():
    request = {'source_head':'1'*40,'run_id':123}
    report = {'status':'PASS_SOURCE_ADJUDICATION_ONLY','verification_head':request['source_head'],
        'verification_run_id':123,'focused_tests':13,'two_process_outputs_identical':True,
        'readonly_byte_mtime_unchanged':True,'files':{n:{} for n in r.OUTPUTS},
        'reused_collision_tests':{'run_id':35621880869,'head':'c8af78b793c554d43230cddeab5ce33ae515a742','tests':5}}
    for k in ('rom_changes','new_native_runs','accepted_native_reruns','official_baseline_reruns','wiki_pages_fetched'):report[k]=0
    for k in ('runtime_applied','issue19_complete','release_ready'):report[k]=False
    return report,request,'\nRan 13 tests in 0.10s\n\nOK\n'


def summary():
    return {'species':92,'rows':2394,'pre_evolution_egg_rows':2394,'receiver_direct_egg_rows_added':0,
        'shared_egg_rows_added':0,'reference_only_rows':0,'unresolved_rows':0,'original_consumer_species_checked':411,
        'note_scopes':{'HATCH_BASE_REFERENCE':2336,'SAME_FAMILY_INTERMEDIATE_REFERENCE':57,'NO_BREEDING_NOTE':1},
        'runtime_applied':False,'physical_donor_chain_verified':False,'issue19_complete':False,'release_ready':False}


class RecordTests(unittest.TestCase):
    def test_exact_scoped_report_and_summary(self):
        self.assertIsNone(r.validate_report(*fixture()))
        self.assertIsNone(r.validate_summary(summary()))

    def test_failed_independent_generation_or_readonly(self):
        for key in ('two_process_outputs_identical','readonly_byte_mtime_unchanged'):
            report,request,log=fixture();report[key]=False
            with self.subTest(key=key),self.assertRaises(SourceError):r.validate_report(report,request,log)

    def test_wrong_head_or_run(self):
        for key,value in (('verification_head','2'*40),('verification_run_id',124)):
            report,request,log=fixture();report[key]=value
            with self.subTest(key=key),self.assertRaises(SourceError):r.validate_report(report,request,log)

    def test_missing_or_extra_output_is_rejected(self):
        for extra in (False,True):
            report,request,log=fixture()
            if extra:report['files']['invented.json']={}
            else:del report['files']['nondirect_egg.jsonl']
            with self.subTest(extra=extra),self.assertRaises(SourceError):r.validate_report(report,request,log)

    def test_failed_or_duplicate_test_log(self):
        report,request,log=fixture()
        for bad in (log.replace('OK','FAILED (failures=1)'),log+log,log.replace('13','12')):
            with self.subTest(log=bad),self.assertRaises(SourceError):r.validate_report(report,request,bad)

    def test_rerun_or_boolean_counter_rejected(self):
        for key in ('rom_changes','new_native_runs','accepted_native_reruns','official_baseline_reruns','wiki_pages_fetched'):
            for value in (1,False):
                report,request,log=fixture();report[key]=value
                with self.subTest(key=key,value=value),self.assertRaises(SourceError):r.validate_report(report,request,log)

    def test_runtime_and_whole_issue_promotion_rejected(self):
        for key in ('runtime_applied','issue19_complete','release_ready'):
            report,request,log=fixture();report[key]=True
            with self.subTest(key=key),self.assertRaises(SourceError):r.validate_report(report,request,log)
        data=summary();data['physical_donor_chain_verified']=True
        with self.assertRaises(SourceError):r.validate_summary(data)

    def test_coverage_loss_and_direct_duplication_rejected(self):
        for key,value in (('rows',2393),('species',91),('pre_evolution_egg_rows',2393),
                          ('receiver_direct_egg_rows_added',1),('shared_egg_rows_added',1),('unresolved_rows',1)):
            data=summary();data[key]=value
            with self.subTest(key=key),self.assertRaises(SourceError):r.validate_summary(data)

    def test_note_invention_and_wrong_reuse_rejected(self):
        data=summary();data['note_scopes']['NO_BREEDING_NOTE']=0
        with self.assertRaises(SourceError):r.validate_summary(data)
        report,request,log=fixture();report['reused_collision_tests']['run_id']+=1
        with self.assertRaises(SourceError):r.validate_report(report,request,log)

    def test_only_exact_started_owner_append_metadata_can_be_repaired(self):
        for name,(old,new) in r.REPAIRS.items():
            raw=(ROOT/name).read_bytes()
            self.assertEqual(r.repaired_binding(name,old,raw),new)
            with self.assertRaises(SourceError):r.repaired_binding(name,old,raw+b' ')
            with self.assertRaises(SourceError):r.repaired_binding(name,new,raw)

    def test_state_mirrors_and_all_unrelated_accepted_history_preserved(self):
        state=json.loads((ROOT/r.STATE).read_bytes());state.pop('learnset_vega_adjudication',None)
        before=copy.deepcopy(state);report,_,_=fixture();result=r.synchronize(state,report)
        self.assertEqual(state,before)
        allowed={'bp','next_action','observed_head_history','observed_head','observed_head_semantics',
                 'observed_date_jst','observed_head_checks','learnset_vega_adjudication','do_not_repeat',
                 'remaining_sequence_ja','logs_synchronized'}
        for key in set(state)-allowed:self.assertEqual(result[key],state[key],key)
        for key in set(state['bp'])-{'current_stop','next_step'}:self.assertEqual(result['bp'][key],state['bp'][key],key)
        self.assertEqual(result['bp']['next_step'],result['next_action']['goal_ja'])
        self.assertEqual(result['next_action']['id'],'LEARNSET_RUNTIME_BASELINE_APPLICATION')

    def test_duplicate_record_rejected(self):
        with self.assertRaises(SourceError):r.synchronize({'learnset_vega_adjudication':{}},{})


if __name__ == '__main__':unittest.main()
