"""記録だけの10境界。原作採取・公式生成・nativeを呼び出さない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_vega_original_record as r
from tools.pr16_vega_original_baseline import SourceError


def fixture():
    request = {'source_head':'1'*40, 'run_id':123}
    report = {'status':'PASS_SOURCE_CAPTURE_AND_METHOD_AUDIT_ONLY','task':r.TASK,
        'verification_head':request['source_head'],'verification_run_id':123,
        'species':181,'wiki_pages':182,'total_direct_rows':9923,
        'method_rows':{'egg':1790,'level_up':3044,'machine':3549,'tutor':1540},
        'source_conflict_groups':3,'wiki_nondirect_egg_species':92,'wiki_nondirect_egg_routes':2394,
        'unknown_moves':0,'dex_mismatches':0,'focused_tests':43,
        'files':{name:{} for name in r.OUTPUTS}}
    for name in ('two_process_outputs_identical','readonly_byte_mtime_unchanged','tracked_tree_unchanged','local_and_actions_outputs_identical'):
        report[name] = True
    for name in ('rom_changes','new_native_runs','accepted_native_reruns','official_baseline_reruns','owner_overlay_rows'):
        report[name] = 0
    for name in ('adoption_ready','issue19_complete','release_ready','side_change_implementation_added'):
        report[name] = False
    return report, request, '\nRan 43 tests in 0.10s\n\nOK\n'


class RecordTests(unittest.TestCase):
    def test_source_scope_success_only(self):
        self.assertIsNone(r.validate_report(*fixture()))

    def test_failed_verification_not_accepted(self):
        for field in ('two_process_outputs_identical','readonly_byte_mtime_unchanged','tracked_tree_unchanged','local_and_actions_outputs_identical'):
            report, request, log = fixture(); report[field] = False
            with self.subTest(field=field), self.assertRaises(SourceError):
                r.validate_report(report,request,log)

    def test_wrong_head_not_accepted(self):
        report, request, log = fixture(); report['verification_head'] = '2'*40
        with self.assertRaises(SourceError):
            r.validate_report(report,request,log)

    def test_missing_proof_not_accepted(self):
        report, request, log = fixture(); del report['files']['source_conflicts.json']
        with self.assertRaises(SourceError):
            r.validate_report(report,request,log)

    def test_accepted_work_not_rerun(self):
        for field in ('rom_changes','new_native_runs','accepted_native_reruns','official_baseline_reruns','owner_overlay_rows'):
            report, request, log = fixture(); report[field] = 1
            with self.subTest(field=field), self.assertRaises(SourceError):
                r.validate_report(report,request,log)

    def test_not_promoted_to_whole_task_or_engine_acceptance(self):
        for field in ('adoption_ready','issue19_complete','release_ready','side_change_implementation_added'):
            report, request, log = fixture(); report[field] = True
            with self.subTest(field=field), self.assertRaises(SourceError):
                r.validate_report(report,request,log)

    def test_coverage_loss_not_accepted(self):
        report, request, log = fixture(); report['total_direct_rows'] -= 1
        with self.assertRaises(SourceError):
            r.validate_report(report,request,log)

    def test_failed_test_log_not_accepted(self):
        report, request, log = fixture()
        with self.assertRaises(SourceError):
            r.validate_report(report,request,log.replace('OK','FAILED (failures=1)'))

    def test_state_mirrors_and_accepted_history_preserved(self):
        state = json.loads((ROOT / r.STATE).read_bytes())
        # 次回の保守試験でも、新工程の記録済みstateを元工程へ戻して合成する。
        state.pop('learnset_vega_original', None)
        before = copy.deepcopy(state)
        report, _, _ = fixture()
        result = r.synchronize(state,report)
        self.assertEqual(state,before)
        for key in ('status','candidate','last_accepted_native_run','latest_native_evidence','learnset_baseline','learnset_baseline_storage','release_ready','merge_performed','active_baseline_changed'):
            self.assertEqual(result[key],state[key])
        self.assertEqual(result['bp']['next_step'],result['next_action']['goal_ja'])
        self.assertEqual(result['observed_head'],report['verification_head'])
        self.assertEqual(result['next_action']['id'],'LEARNSET_VEGA_SOURCE_ADJUDICATION')

    def test_duplicate_record_is_rejected(self):
        with self.assertRaises(SourceError):
            r.synchronize({'learnset_vega_original':{}},{})


if __name__ == '__main__':
    unittest.main()
