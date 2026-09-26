"""Thumb修復記録の過大受入・原本破壊・proof欠落を拒否する。"""
import copy
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_thumb_record as record
import pr16_circus_thumb as thumb

class RecordContracts(unittest.TestCase):
    def fixture(self):
        candidate=dict(size=33554432,sha256='1'*64);address=0x09ff4b11;at=(address&~1)-0x08000000
        build=dict(status='BUILT_CIRCUS_RECEPTION_NATIVE_PENDING',candidate=candidate,entries=dict(selector=address),
            payload_offset=at-64,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
            accepted_native_cases_replayed=0,new_emulator_processes=0,independent_new_adapter_links=2,independent_scoped_patches=2,
            old_trial_script_unchanged=True,old_cfru_owners_unchanged=True,inherited_root_scan_repeated=False,
            inherited_link_run=35353620141,allocation=dict(summaries=dict(overlap_count=0)))
        proof=dict(status='PASS_ADAPTER_ONLY_PREFIX_INHERITANCE',candidate=candidate,
            previous=dict(size=33554432,sha256=thumb.PREVIOUS_SHA),restored_whole_rom_sha256=thumb.PREVIOUS_SHA,
            allowed_range=[at,at+304],changed_bytes=33,inherited_cases=['circus-cancel-save-continue','factory-fallback-cancel'],
            physical_admission_accepted=False,suppression_accepted=False,accepted_native_cases_replayed=0)
        return build,proof
    def test_valid_scoped_build(self):record.validate_build(*self.fixture())
    def test_reject_changed_proof_scope(self):
        build,proof=self.fixture()
        for key,value in (('status','PASS'),('candidate',{}),('previous',{}),('restored_whole_rom_sha256','2'*64),('allowed_range',[0,304]),('inherited_cases',[])):
            bad=dict(proof,**{key:value})
            with self.assertRaises(ValueError):record.validate_build(build,bad)
    def test_reject_nonpositive_or_boolean_changed_count(self):
        build,proof=self.fixture()
        for value in (0,-1,305,True):
            with self.assertRaises(ValueError):record.validate_build(build,dict(proof,changed_bytes=value))
    def test_reject_missing_independent_runs(self):
        build,proof=self.fixture()
        for key in ('independent_new_adapter_links','independent_scoped_patches'):
            for value in (1,True,0):
                with self.assertRaises(ValueError):record.validate_build(dict(build,**{key:value}),proof)
    def test_reject_native_or_accepted_replays(self):
        build,proof=self.fixture()
        for key in ('accepted_native_cases_replayed','new_emulator_processes'):
            with self.assertRaises(ValueError):record.validate_build(dict(build,**{key:1}),proof)
        with self.assertRaises(ValueError):record.validate_build(build,dict(proof,accepted_native_cases_replayed=True))
    def test_reject_acceptance_promotion(self):
        build,proof=self.fixture()
        for key in ('physical_admission_accepted','suppression_accepted','release_ready'):
            with self.assertRaises(ValueError):record.validate_build(dict(build,**{key:True}),proof)
        for key in ('physical_admission_accepted','suppression_accepted'):
            with self.assertRaises(ValueError):record.validate_build(build,dict(proof,**{key:True}))
    def test_reject_old_owner_mutation_or_reaudit(self):
        build,proof=self.fixture()
        for key,value in (('old_trial_script_unchanged',False),('old_cfru_owners_unchanged',False),('inherited_root_scan_repeated',True),('inherited_link_run',0)):
            with self.assertRaises(ValueError):record.validate_build(dict(build,**{key:value}),proof)
    def test_reject_overlap(self):
        build,proof=self.fixture();build['allocation']['summaries']['overlap_count']=1
        with self.assertRaises(ValueError):record.validate_build(build,proof)
    def state(self):
        state=dict(candidate={'sha256':'formal-bp'},status='BP_ACCEPTED',latest_native_run=34946969126,latest_native_job=1,
            latest_native_tested_head='a'*40,last_accepted_native_run=34946969126,last_accepted_native_tested_head='a'*40,
            release_ready=False,remaining_physical_gap_ids=['PHYSICAL_CIRCUS_ADMISSION'],remaining_p08_gate_ids=['FINAL_NATIVE_ACCEPTANCE','RELEASE_DECISION'],
            bp={'current_stop':'old','next_step':'old'},next_action={},do_not_repeat=[])
        backlog=dict(remaining_conditions=[dict(id='PHYSICAL_CIRCUS_ADMISSION',success_evidence=None),dict(id='FINAL_NATIVE_ACCEPTANCE',complete=False)])
        build,proof=self.fixture()
        checkpoint=dict(physical_admission_accepted=False,release_ready=False,classification='THUMB_ADAPTER_REPAIRED_PREFIX_INHERITED_NATIVE_OPEN',
            tested_head='a'*40,build_run_id=123,build=build,proof=proof)
        return state,backlog,checkpoint
    def test_projection_preserves_formal_authority_and_inputs(self):
        state,backlog,checkpoint=self.state();original=copy.deepcopy((state,backlog))
        s,b=record.project(state,backlog,checkpoint)
        self.assertEqual((state,backlog),original);self.assertEqual(s['candidate'],state['candidate'])
        self.assertEqual(s['bp']['next_step'],s['next_action']['goal_ja'])
        self.assertEqual(b['remaining_conditions'][1],backlog['remaining_conditions'][1])
        self.assertIsNone(b['remaining_conditions'][0]['success_evidence'])
        self.assertEqual(record.project(s,b,checkpoint),(s,b))
    def test_projection_rejects_claimed_admission(self):
        s,b,c=self.state();c['physical_admission_accepted']=True
        with self.assertRaises(ValueError):record.project(s,b,c)
    def test_projection_rejects_existing_closed_gap(self):
        s,b,c=self.state();b['remaining_conditions'][0]['success_evidence']='closed'
        with self.assertRaises(ValueError):record.project(s,b,c)

if __name__=='__main__':unittest.main()
