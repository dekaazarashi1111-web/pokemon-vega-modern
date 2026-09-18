"""Native受入投影の否定テスト。fixtureを正規取得/戦闘受入へ昇格しない。"""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ring_native',ROOT/'scripts/pr16_ring_npc_native.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SHA='a'*64
HOST=[96,17,1,13,38]


def fixture(name='gift-save-revisit'):
    result=m.CASES[name];quantity=int(result==1)
    return dict(schema_version=1,status='PASS',scope=m.SCOPE,case=name,rom_sha256=SHA,
        initial_result=result,revisit_result=2 if result==1 else result,ring_before=0,
        ring_after=quantity,ring_after_continue=quantity,manual_saves=1,automatic_saves=0,
        fresh_cores=2,host_write_barriers=7,physical_host=HOST,ring_is_fixture=False,
        initial_progression_map_capacity_are_fixtures=True,party_and_other_inventory_preserved=True,
        ordinary_battle_accepted=False,ring_full_acceptance=False,release_ready=False,warnings_errors=0,
        save_before=2,save_after=3,bp_before=8,bp_after=8,total_frames=800,
        witness={key:(i+1)*100 for i,key in enumerate(m.TRACE)})


class NativeAcceptanceContracts(unittest.TestCase):
    def reject(self,row):
        with self.assertRaises(ValueError): m.validate(row,'gift-save-revisit',SHA,HOST)

    def test_all_case_results_are_distinct(self):
        for name in m.CASES:
            self.assertEqual(m.validate(fixture(name),name,SHA,HOST),fixture(name))

    def test_injected_ring_rejected(self):
        row=fixture();row['ring_is_fixture']=True;self.reject(row)
        row=fixture();row['ring_before']=1;self.reject(row)

    def test_unobserved_battle_release_promotion_rejected(self):
        for key in ('ordinary_battle_accepted','ring_full_acceptance','release_ready'):
            row=fixture();row[key]=True;self.reject(row)

    def test_missing_or_extra_field_rejected(self):
        row=fixture();row.pop('revisit_result');self.reject(row)
        row=fixture();row['claimed']=True;self.reject(row)

    def test_boolean_not_integer_counter(self):
        for key in ('manual_saves','save_before','bp_after','total_frames'):
            row=fixture();row[key]=True;self.reject(row)

    def test_durable_one_ring_required(self):
        for key in ('ring_after','ring_after_continue'):
            for value in (0,2):
                row=fixture();row[key]=value;self.reject(row)

    def test_repeat_must_be_already_owned(self):
        row=fixture();row['revisit_result']=1;self.reject(row)

    def test_candidate_and_npc_bound(self):
        row=fixture();row['rom_sha256']='b'*64;self.reject(row)
        row=fixture();row['physical_host']=[96,5,1,13,38];self.reject(row)

    def test_save_bp_and_core_counts_bound(self):
        for key,value in (('save_after',2),('bp_after',9),('fresh_cores',1),('host_write_barriers',6),('automatic_saves',1)):
            row=fixture();row[key]=value;self.reject(row)

    def test_frame_sequence_cannot_be_reordered_or_invented(self):
        for key in m.TRACE:
            row=fixture();row['witness'][key]=0;self.reject(row)
        row=fixture();row['witness']['saved']=row['witness']['reloaded'];self.reject(row)
        row=fixture();row['total_frames']=801;self.reject(row)


if __name__=='__main__': unittest.main()
