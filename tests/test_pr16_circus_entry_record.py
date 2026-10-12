import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_entry_record as record


def fixture():
    payload={'sha256':'1'*64,'size':1014}
    return dict(status='BUILT_CIRCUS_RECEPTION_NATIVE_PENDING',source_head='a'*40,run_id=99,
        parent=record.evidence.PARENT,candidate={'size':33554432,'sha256':'2'*64},
        new_emulator_processes=0,accepted_native_cases_replayed=0,physical_admission_accepted=False,
        suppression_accepted=False,release_ready=False,independent_new_adapter_links=2,independent_scoped_patches=2,
        old_trial_script_unchanged=True,old_cfru_owners_unchanged=True,inherited_link_run=35353620141,
        inherited_root_scan_repeated=False,launch_sites=[dict(original=i,draw=0x0910333D,size=43) for i in range(3)],
        gateway=dict(address=0x093CDA9C,before='90933c09'),existing_allocations_rehashed=['gateway'],payload_offset=0x1ff0000,
        payload=payload,allocation=dict(summaries=dict(overlap_count=0),allocations=[dict(name='pr16_circus_reception_runtime',
            start=0x1ff0000,end_exclusive=0x1ff0000+1014,content_sha256=payload['sha256'])]))


class RecordContracts(unittest.TestCase):
    def setUp(self):self.spec=dict(tested_head='a'*40,run_id=99)
    def test_accept_exact_bounded_build(self):record.validate_build(fixture(),self.spec)
    def test_reject_run_or_head_drift(self):
        for key,value in (('source_head','b'*40),('run_id',100)):
            r=fixture();r[key]=value
            with self.assertRaises(ValueError):record.validate_build(r,self.spec)
    def test_reject_acceptance_promotion_and_bool_as_count(self):
        for key,value in (('physical_admission_accepted',True),('suppression_accepted',True),('release_ready',True),
                          ('new_emulator_processes',False),('accepted_native_cases_replayed',1)):
            r=fixture();r[key]=value
            with self.assertRaises(ValueError):record.validate_build(r,self.spec)
    def test_reject_parent_or_unchanged_candidate(self):
        r=fixture();r['candidate']=r['parent']
        with self.assertRaises(ValueError):record.validate_build(r,self.spec)
        r=fixture();r['parent']={'sha256':'0'*64,'size':33554432}
        with self.assertRaises(ValueError):record.validate_build(r,self.spec)
    def test_reject_owner_or_launch_drift(self):
        for key,value in (('old_trial_script_unchanged',False),('old_cfru_owners_unchanged',False),('inherited_root_scan_repeated',True)):
            r=fixture();r[key]=value
            with self.assertRaises(ValueError):record.validate_build(r,self.spec)
        r=fixture();r['launch_sites'][1]['original']=0
        with self.assertRaises(ValueError):record.validate_build(r,self.spec)
    def test_reject_alignment_or_payload_hash_drift(self):
        for key,value in (('start',0x1ff0004),('content_sha256','0'*64),('end_exclusive',0x1ff2000)):
            r=fixture();r['allocation']['allocations'][0][key]=value
            with self.assertRaises(ValueError):record.validate_build(r,self.spec)
    def test_projection_preserves_authority_and_input_objects(self):
        state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes())
        backlog=json.loads((ROOT/'content/modernization/p08_remaining_work.json').read_bytes())
        before=copy.deepcopy((state,backlog));r=dict(classification='CIRCUS_SCRIPT_WIRED_CANDIDATE_BUILT_NATIVE_OPEN',
            tested_head='a'*40,build_run_id=99,physical_admission_accepted=False,release_ready=False,build=fixture())
        s,b=record.project(state,backlog,r)
        self.assertEqual((state,backlog),before)
        self.assertEqual(s['candidate'],state['candidate']);self.assertEqual(s['remaining_physical_gap_ids'],state['remaining_physical_gap_ids'])
        self.assertEqual(s['bp']['next_step'],s['next_action']['goal_ja'])
        self.assertIn('Circus固有streak',s['remaining_sequence_ja'])
        self.assertIsNone(next(x for x in b['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')['success_evidence'])
    def test_projection_rejects_already_closed_gap(self):
        state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes())
        backlog=json.loads((ROOT/'content/modernization/p08_remaining_work.json').read_bytes())
        next(x for x in backlog['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')['success_evidence']='accepted.json'
        with self.assertRaises(ValueError):record.project(state,backlog,dict(physical_admission_accepted=False,release_ready=False))

if __name__=='__main__':unittest.main()
