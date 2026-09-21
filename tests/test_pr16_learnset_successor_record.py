"""後継表の記録境界を小型fixtureだけで検査する。"""
import copy
import io
from pathlib import Path
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import record_pr16_learnset_successor as r
from tools import pr16_learnset_successor as s


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.request={'source_head':'a'*40,'run_id':1}
        self.log='\nRan 39 tests in 0.01s\n\nOK\n'
        self.report=dict(self.request,status='PASS_SUCCESSOR_TABLES_ONLY',focused_tests=39,
            two_process_outputs_identical=True,readonly_byte_mtime_unchanged=True,
            independent_source_row_audit=True,local_and_actions_output_identical=True,
            rom_changes=0,new_native_runs=0,accepted_native_reruns=0,official_baseline_reruns=0,
            vega_source_reruns=0,runtime_applied=False,issue19_complete=False,release_ready=False,
            source_rows_accounted=128447,files={})
        self.receipt=dict(selected_routes=128288,official_species=1299,vega_species=181,
            side_change_excluded=159,side_change_species=103,active_side_change=0,
            placeholder_rows=0,owner_overlay_rows=0,vega_nondirect_egg_rows=2394,
            hatch_baseline_membership_gaps=531,vega_nondirect_direct_grants=0,
            vega_nondirect_shared_grants=0,runtime_applied=False,issue19_complete=False,
            release_ready=False,files={},consumers={c:0 for c in s.CONSUMERS})
        self.state={'pr_merged':False,'active_baseline_changed':False,'release_ready':False,
            'bp':{},'observed_head':'b'*40,'observed_head_semantics':'旧scope',
            'observed_head_checks':{'reason_ja':'旧検証'},'do_not_repeat':['旧受入を保持'],
            'current_p08_candidate':{'sha256':'c'*64}}

    def validate(self):r.validate_report(self.report,self.receipt,self.request,self.log)

    def test_completed_scope_passes(self):self.validate()

    def test_missing_readonly_evidence_rejected(self):
        self.report['readonly_byte_mtime_unchanged']=False
        with self.assertRaises(ValueError):self.validate()

    def test_unmatched_head_rejected(self):
        self.report['source_head']='b'*40
        with self.assertRaises(ValueError):self.validate()

    def test_unrequested_runtime_promotion_rejected(self):
        self.receipt['runtime_applied']=True
        with self.assertRaises(ValueError):self.validate()

    def test_old_native_rerun_rejected(self):
        self.report['accepted_native_reruns']=1
        with self.assertRaises(ValueError):self.validate()

    def test_invented_egg_grant_rejected(self):
        self.receipt['vega_nondirect_direct_grants']=1
        with self.assertRaises(ValueError):self.validate()

    def test_failed_unit_log_rejected(self):
        self.log='\nRan 39 tests in 0.01s\nFAILED (failures=1)\n'
        with self.assertRaises(ValueError):self.validate()

    def test_synchronization_preserves_candidate_and_prior_state(self):
        before=copy.deepcopy(self.state)
        after=r.synchronize(self.state,self.request)
        self.assertEqual(self.state,before)
        self.assertEqual(after['current_p08_candidate'],before['current_p08_candidate'])
        self.assertEqual(after['bp']['next_step'],after['next_action']['goal_ja'])
        self.assertFalse(after['release_ready'])

    def test_duplicate_record_rejected(self):
        state=r.synchronize(self.state,self.request)
        with self.assertRaises(ValueError):r.synchronize(state,self.request)

    def test_archive_extra_entry_rejected(self):
        data=io.BytesIO()
        with zipfile.ZipFile(data,'w') as z:
            z.writestr('receipt.json',s.encode({'files':{}}));z.writestr('extra.txt','x')
        raw=data.getvalue();ident=r.raw_identity(raw)
        with self.assertRaises(ValueError):r.validate_archive(raw,{'digest':'sha256:'+ident['sha256'],'size_in_bytes':len(raw)},{'files':{}})


if __name__=='__main__':unittest.main()
