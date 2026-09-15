"""compiled receiptの過大主張・受入済みBP再open・破壊的投影を拒否する。"""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compiled_record', ROOT/'scripts/pr16_ring_compiled_record.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class RecordTests(unittest.TestCase):
    def fixture(self):
        state={'candidate':r.owner.CANDIDATE, 'bp':{'spending_accepted':True},
               'latest_native_run':34946969126,'remaining_physical_gap_ids':[r.GAP,'POLICY'],
               'next_action':{},'do_not_repeat':[], 'unrelated':{'unchanged':True}}
        backlog={'remaining_conditions':[{'id':'NATURAL_CAPTURE_GEAR',
                 'remaining_supply_gap_ids':[r.GAP,'POLICY'], 'status':'pending-two',
                 'selected_supply_entrypoints':{r.GAP:None,'POLICY':'existing'}},
                 {'id':'PHYSICAL_CIRCUS_ADMISSION','keep':'unchanged'}]}
        report={'classification':'COMPILED_OWNER_BOUNDARY_NOT_NATIVE_ACCEPTANCE','source_head':'a'*40,
                'verification':{'run':{'id':1}}}
        return state,backlog,report

    def receipt(self):
        v={'task':r.owner.TASK,'classification':'COMPILED_OWNER_BOUNDARY_NOT_NATIVE_ACCEPTANCE',
           'candidate':r.owner.CANDIDATE,'candidate_bytes_checked':True,
           'compiled_event_runtime_verified':True,'all_runtime_owners_excluded':False,
           'ring_acquisition_accepted':False,'release_ready':False,'new_emulator_processes':0,
           'accepted_native_cases_replayed':0,'rom_changes':0,'reachable_event_reward_calls':[],
           'script_nodes':[{'address':1}],'source_head':'a'*40,
           'source_bindings':{n:r.owner.identity(b'source') for n in r.owner.SOURCES},
           'verification':{'run':{'id':1,'head_sha':'a'*40,'status':'completed','conclusion':'success'},
           'job':{'id':2,'run_id':1,'status':'completed','conclusion':'success'},
           'artifact':{'id':3,'run_id':1,'head_sha':'a'*40,'sha256':'b'*64},
           'focused_tests':{'tests_run':24,'successful':True,'failures':0,'errors':0,'skips':0}}}
        return v

    def validate(self,value):
        with mock.patch.object(r.resume,'safe_path') as path:
            path.return_value.read_bytes.return_value=b'source'
            return r.validate_receipt(value)

    def test_good_receipt(self):
        self.assertEqual(self.validate(self.receipt()),self.receipt())

    def test_acceptance_flags_rejected(self):
        for key in ('all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
            v=self.receipt();v[key]=True
            with self.subTest(key=key),self.assertRaises(ValueError): self.validate(v)

    def test_missing_compiled_proof(self):
        for key in ('candidate_bytes_checked','compiled_event_runtime_verified'):
            v=self.receipt();v[key]=False
            with self.subTest(key=key),self.assertRaises(ValueError): self.validate(v)

    def test_emulator_or_replay_rejected(self):
        for key in ('new_emulator_processes','accepted_native_cases_replayed','rom_changes'):
            for value in (1,False):
                v=self.receipt();v[key]=value
                with self.subTest(key=key,value=value),self.assertRaises(ValueError): self.validate(v)

    def test_failed_or_pending_run_not_success(self):
        for key,value in (('status','in_progress'),('conclusion','failure'),('head_sha','c'*40)):
            v=self.receipt();v['verification']['run'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): self.validate(v)

    def test_wrong_job(self):
        v=self.receipt();v['verification']['job']['run_id']=9
        with self.assertRaises(ValueError): self.validate(v)

    def test_wrong_artifact(self):
        for key,value in (('run_id',9),('head_sha','c'*40),('sha256','missing')):
            v=self.receipt();v['verification']['artifact'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): self.validate(v)

    def test_stale_source(self):
        v=self.receipt();v['source_bindings'][r.owner.SELF]={'size':0,'sha256':'a'*64}
        with self.assertRaises(ValueError): self.validate(v)

    def test_missing_source(self):
        v=self.receipt();del v['source_bindings'][r.owner.SELF]
        with self.assertRaises(ValueError): self.validate(v)

    def test_reward_or_skipped_tests_rejected(self):
        v=self.receipt();v['reachable_event_reward_calls']=[1]
        with self.assertRaises(ValueError): self.validate(v)
        v=self.receipt();v['verification']['focused_tests']['skips']=1
        with self.assertRaises(ValueError): self.validate(v)

    def test_projection_is_pure_and_idempotent(self):
        s,b,v=self.fixture();original=copy.deepcopy((s,b))
        result=r.project(s,b,v)
        self.assertEqual((s,b),original)
        self.assertEqual(result,r.project(*result,v))

    def test_projection_preserves_bp_policy_circus(self):
        s,b,v=self.fixture();ss,bb=r.project(s,b,v)
        self.assertTrue(ss['bp']['spending_accepted']);self.assertEqual(ss['latest_native_run'],34946969126)
        self.assertEqual(ss['remaining_physical_gap_ids'],s['remaining_physical_gap_ids'])
        self.assertEqual(bb['remaining_conditions'][1],b['remaining_conditions'][1])
        self.assertEqual(bb['remaining_conditions'][0]['selected_supply_entrypoints'],b['remaining_conditions'][0]['selected_supply_entrypoints'])
        self.assertEqual(bb['remaining_conditions'][0]['remaining_supply_gap_ids'],b['remaining_conditions'][0]['remaining_supply_gap_ids'])

    def test_closed_gap_or_selected_giver_not_overwritten(self):
        for change in ('gap','entry'):
            s,b,v=self.fixture()
            if change=='gap':b['remaining_conditions'][0]['remaining_supply_gap_ids'].remove(r.GAP)
            else:b['remaining_conditions'][0]['selected_supply_entrypoints'][r.GAP]='real-owner'
            with self.subTest(change=change),self.assertRaises(ValueError): r.project(s,b,v)

    def test_native_checkpoint_advance_rejected(self):
        s,b,v=self.fixture();s['latest_native_run']=2
        with self.assertRaises(ValueError):r.project(s,b,v)


if __name__=='__main__':unittest.main()
