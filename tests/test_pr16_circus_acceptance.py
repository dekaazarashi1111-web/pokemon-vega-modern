"""既受入nativeを再実行しないCircus receiptの拒否契約。"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('circus_receipt', ROOT/'scripts/pr16_circus_acceptance.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def pair():
    candidate = dict(size=33554432, sha256=m.SHA)
    old = dict(candidate=candidate, native_verified=False, process=dict(returncode=1), failures=['old failure'],
               getter_calls=[dict(result=30,owner_current=30,args=[0],host_writes=0,host_calls=0)],
               natural_calls=[dict(host_writes=0,host_calls=0) for _ in range(20)],
               original_failure=dict(normal_save30=dict(candidate=dict(size=33554432,sha256='2b107e7e'))),
               physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    new = dict(candidate=candidate,native_verified=True,failures=[],
               process=dict(schema_version=1,returncode=0,timed_out=False,spawn_error=None),
               cache=dict(host_state_injection=False,prefix_wins_reexecuted=0),
               physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
               analysis=dict(result=dict(candidate_sha256=m.SHA,status='PASS_CIRCUS_SUPPRESSION_LIFECYCLE',
                   new_battles=3,new_wins=3,new_losses=0,bp_after=99,fresh_cores=2,prefix_wins_reexecuted=0,
                   save_counter_before=3,save_counter_after=4,owner_bytes_verified=64,party_bytes_verified=600,
                   input_only_after_guard=True,host_write_barriers=7,warnings_errors=0,release_ready=False)))
    return old,new


class ReceiptTests(unittest.TestCase):
    def test_success_is_scoped_and_zero_new_native(self):
        old,new=pair(); before=copy.deepcopy((old,new)); r=m.verify_pair(old,new)
        self.assertEqual((old,new),before)
        self.assertTrue(r['physical_admission_accepted']); self.assertEqual(r['new_emulator_processes'],0)
        self.assertFalse(r['final_candidate_transfer_complete']);self.assertFalse(r['release_ready'])
        self.assertFalse(r['normal_battle_after_exit_newly_tested'])
    def test_candidate_mismatch(self):
        old,new=pair();new['candidate']=dict(size=33554432,sha256='0'*64)
        with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_old_failure_not_success(self):
        old,new=pair();old['native_verified']=True
        with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_old_failure_must_remain(self):
        old,new=pair();old['failures']=[]
        with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_new_failure_rejected(self):
        old,new=pair();new['process']['returncode']=1
        with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_getter_index_not_var_id(self):
        old,new=pair();old['getter_calls'][0]['args']=[0x403a]
        with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_getter_write_rejected(self):
        old,new=pair();old['getter_calls'][0]['host_writes']=1
        with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_suppression_write_rejected(self):
        old,new=pair();old['natural_calls'][0]['host_calls']=1
        with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_save30_injection_rejected(self):
        old,new=pair();new['cache']['host_state_injection']=True
        with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_prefix_replay_rejected(self):
        old,new=pair();new['cache']['prefix_wins_reexecuted']=30
        with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_result_fields_fail_closed(self):
        for key in ('bp_after','save_counter_after','party_bytes_verified','owner_bytes_verified','new_wins','fresh_cores'):
            with self.subTest(key=key):
                old,new=pair();new['analysis']['result'][key]+=1
                with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_bool_is_not_integer(self):
        old,new=pair();new['analysis']['result']['new_wins']=True
        with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_original_acceptance_not_overwritten(self):
        old,new=pair();new['physical_admission_accepted']=True
        with self.assertRaises(ValueError):m.verify_pair(old,new)
    def test_duplicate_json_rejected(self):
        with self.assertRaises(ValueError):m.strict('{"x":1,"x":2}')
    def test_wrong_archive_digest(self):
        with self.assertRaises(ValueError):m.archive(b'wrong',m.SOURCES[0])
    def test_action_required_not_success(self):
        s=m.SOURCES[1];run=dict(id=s['run'],head_sha=s['head'],head_branch='codex/modernization-followup-20260908',status='completed',conclusion='action_required')
        with self.assertRaises(ValueError):m.validate_actions(run,{},s)
    def test_review_manifest_covers_all_pixels(self):
        r=json.loads((ROOT/m.REVIEW).read_text())
        self.assertEqual(len(r['screens']),29)
        self.assertTrue(all(len(x['identity']['sha256'])==64 and x['observation_ja'] for x in r['screens'].values()))


if __name__=='__main__':unittest.main()
