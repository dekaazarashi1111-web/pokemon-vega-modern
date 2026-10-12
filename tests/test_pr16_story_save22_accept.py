"""新Save22の拒否境界のみ。旧suite/nativeを起動しない。全Save変異はメモリ内。"""
from __future__ import annotations
import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save22_accept as m


class Save22Gates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=m.plan();m.decode_plan(cls.p)
        cls.data=Path(os.environ['PR16_SAVE22_FIXTURE'])
        cls.before=(cls.data/'input.srm').read_bytes();cls.after=(cls.data/'story-fast.srm').read_bytes()
        cls.rom=(cls.data/'candidate.gba').read_bytes()
        cls.raw={k:m.inflate(cls.p[k]['development_stdout_zlib_b85']) for k in ('progress','continue')}
        cls.cmd={k:m.inflate(cls.p[k]['development_commands_zlib_b85'],40000) for k in ('progress','continue')}
        cls.a=m.trace(cls.raw['progress'],cls.cmd['progress'],m.INPUT_SAVE)
        cls.b=m.trace(cls.raw['continue'],cls.cmd['continue'],m.OUTPUT_SAVE)
        cls.old,_=m.sectors.bank(cls.before,0xe000,21,m.sectors.LAYOUT)
        cls.new,_=m.sectors.bank(cls.after,0,22,m.sectors.LAYOUT)

    def reject_plan(self,change):
        p=deepcopy(self.p);change(p)
        with self.assertRaises(ValueError):m.decode_plan(p)

    def reject_semantic(self,lane,index,**values):
        a,b=deepcopy(self.a),deepcopy(self.b)
        (a if lane=='progress' else b)['observations'][index].update(values)
        with self.assertRaises(ValueError):m.semantic(a,b,True)

    def altered_save(self,offset,value,repair_section=None):
        raw=bytearray(self.after);raw[offset]=value
        if repair_section is not None:
            pos=self.new[repair_section];size=m.sectors.LAYOUT[repair_section][1]
            struct.pack_into('<H',raw,pos+0xff6,m.sectors.checksum(bytes(raw[pos:pos+size])))
        return bytes(raw)

    def reject_structure_under_new_hash(self,raw):
        # Root identity is deliberately rebound ONLY inside a unit test so deeper state gates execute.
        with patch.object(m,'OUTPUT_SAVE',m.identity(raw)):
            with self.assertRaises(ValueError):m.save_structure(self.before,raw,raw)

    def test_development_is_explicitly_not_acceptance(self):
        v=m.semantic(self.a,self.b,True)
        self.assertEqual(v['status'],'DEVELOPMENT_NOT_ACCEPTED')
        self.assertEqual(v['trainer_victories'],5)
        self.assertFalse(v['development_cold_card_end_accepted'])

    def test_synthetic_formal_tail_checks_scope_not_native_evidence(self):
        b=deepcopy(self.b)
        for n,frame,lock in ((4,3162,1),(5,3464,0)):
            o=deepcopy(b['observations'][0]);o.update(observe=n,frame=frame,callback2=m.FIELD,lock=lock,field=lock==0)
            b['observations'].append(o)
        b['end'].update(inputs=35,frames=3464)
        v=m.semantic(self.a,b,False)
        self.assertEqual(v['total_reward'],6040)
        for k in ('inner_cave_reached','natural_growth_accepted','natural_evolution_accepted','national_dex_unlocked',
                  'hm05_taught_or_used','hm05_root_cause_resolved','full_story_accepted','release_ready'):
            self.assertIs(v[k],False)

    def test_card_end_cannot_be_formal(self):
        with self.assertRaises(ValueError):m.semantic(self.a,self.b,False)

    def test_mode_not_truthy_integer(self):
        with self.assertRaises(ValueError):m.semantic(self.a,self.b,1)

    def test_completed_five_rewards_only(self):
        v=m.semantic(self.a,self.b,True)
        self.assertEqual([x['yen'] for x in v['trainer_rewards']],[240,132,2600,2600,468])
        self.assertEqual([x['trainer'] for x in v['trainer_rewards']],[102,108,94,1362,97])

    def test_second_return_is_locked_next_approach_not_idle(self):
        v=m.semantic(self.a,self.b,True)
        self.assertEqual(v['battles'][1]['field_callback'],37)
        self.assertEqual(v['battles'][1]['field_lock'],1)
        self.assertFalse(v['all_five_returns_unlocked_snapshots'])

    def test_plan_task_mismatch(self):self.reject_plan(lambda p:p.update(task='Save21'))
    def test_plan_old_input(self):self.reject_plan(lambda p:p.update(input_save=m.parent.INPUT_SAVE))
    def test_plan_wrong_output(self):self.reject_plan(lambda p:p.update(output_save=m.INPUT_SAVE))
    def test_plan_wrong_candidate(self):self.reject_plan(lambda p:p['candidate'].update(sha256='0'*64))
    def test_plan_command_hash(self):self.reject_plan(lambda p:p['progress']['commands'].update(sha256='0'*64))
    def test_plan_development_hash(self):self.reject_plan(lambda p:p['progress']['development_stdout'].update(size=1))
    def test_plan_cold_prefix_hash(self):self.reject_plan(lambda p:p['continue']['development_prefix'].update(sha256='0'*64))
    def test_plan_cold_cannot_drop_old_prefix(self):
        def change(p):
            c=m.COLD_SUFFIX;p['continue']['commands']=m.identity(c)
            p['continue']['commands_zlib_b85']=base64.b85encode(zlib.compress(c)).decode()
        self.reject_plan(change)

    def test_trace_old_save_is_not_new_interval(self):
        with self.assertRaises(ValueError):m.trace(self.raw['progress'],self.cmd['progress'],m.parent.INPUT_SAVE)

    def test_trace_rejects_new_coordinate_waiver(self):
        rows=[json.loads(x) for x in self.raw['progress'].splitlines()]
        row=next(x for x in rows if x.get('observe')==80);row['live_xy'][0]+=1
        raw=b''.join((json.dumps(x,separators=(',',':'))+'\n').encode() for x in rows)
        with self.assertRaises(ValueError):m.trace(raw,self.cmd['progress'],m.INPUT_SAVE)

    def test_trace_rejects_claimed_fixture_call(self):
        rows=self.raw['progress'].splitlines();end=json.loads(rows[-1]);end['fixture_calls']=1
        raw=b'\n'.join(rows[:-1]+[json.dumps(end).encode()])+b'\n'
        with self.assertRaises(ValueError):m.trace(raw,self.cmd['progress'],m.INPUT_SAVE)

    def test_trace_rejects_hidden_save_command(self):
        with self.assertRaises(ValueError):m.trace(self.raw['progress'],b'save\n'+self.cmd['progress'],m.INPUT_SAVE)

    def test_bad_route_before_warp(self):self.reject_semantic('progress',79,map=[1,36])
    def test_claim_inner_cave(self):self.reject_semantic('progress',80,map=[1,73])
    def test_different_start_xy(self):self.reject_semantic('progress',0,xy=[23,17])
    def test_different_start_party(self):self.reject_semantic('progress',0,party_sha256='0'*64)
    def test_party_count_changes(self):self.reject_semantic('progress',52,party_count=5)
    def test_rp_injection(self):self.reject_semantic('continue',0,rp=1)
    def test_party_menu_not_new_battle(self):self.reject_semantic('progress',8,callback2=m.BATTLE)
    def test_unresolved_first_trainer(self):self.reject_semantic('progress',18,battle_outcome=0)
    def test_capture_not_second_win(self):self.reject_semantic('progress',35,battle_outcome=7)
    def test_third_battle_must_reset(self):self.reject_semantic('progress',38,battle_outcome=1)
    def test_wild_not_fourth_trainer(self):self.reject_semantic('progress',51,battle_flags=4)
    def test_loss_not_fifth_win(self):self.reject_semantic('progress',77,battle_outcome=2)
    def test_reward_not_new_battle(self):self.reject_semantic('progress',78,battle_outcome=0)
    def test_field_residual_not_extra_win(self):self.reject_semantic('progress',64,callback2=m.BATTLE)
    def test_locked_second_return_cannot_be_called_idle(self):self.reject_semantic('progress',37,lock=0,field=True)
    def test_warp_loading_not_arrived(self):self.reject_semantic('progress',80,lock=1,field=False)
    def test_flash_before_save_must_remain(self):self.reject_semantic('progress',83,flash_sha256=m.FLASH)
    def test_partial_save_not_completed(self):self.reject_semantic('progress',84,save_counter=22)
    def test_old_flash_not_write_in_progress(self):self.reject_semantic('progress',85,flash_sha256=m.parent.FLASH)
    def test_save_final_lock_not_success(self):self.reject_semantic('progress',86,lock=1,field=False)
    def test_save_final_counter_not_success(self):self.reject_semantic('progress',86,save_counter=21)
    def test_cold_other_coordinate(self):self.reject_semantic('continue',0,xy=[6,4])
    def test_cold_other_facing(self):self.reject_semantic('continue',1,facing=1)
    def test_cold_stale_battle_flags(self):self.reject_semantic('continue',0,battle_flags=12)
    def test_cold_changed_party(self):self.reject_semantic('continue',1,party_sha256='0'*64)
    def test_cold_changed_flash(self):self.reject_semantic('continue',2,flash_sha256=m.parent.FLASH)
    def test_cold_changed_ledger(self):self.reject_semantic('continue',3,ledger_sha256='0'*64)

    def test_exact_save_structure_and_unchanged_inventory(self):
        v=m.save_structure(self.before,self.after,self.after)
        self.assertEqual(v['party_changed_bytes'],m.PARTY_DELTAS)
        self.assertEqual(v['money_after']-v['money_before'],6040)
        self.assertTrue(v['all_bag_slots_preserved'])
        self.assertEqual(v['sector_checksum_checks'],42)
        self.assertEqual(v['s61e_payload_deltas'],[])
        self.assertFalse(v['auxiliary_flag2056_and_vars_runtime_owners_claimed'])

    def test_rtc_change_after_cold_rejected(self):
        cold=bytearray(self.after);cold[-1]^=1
        with self.assertRaises(ValueError):m.save_structure(self.before,self.after,bytes(cold))

    def test_current_checksum_corruption_below_root_hash(self):
        raw=self.altered_save(self.new[1]+10,self.after[self.new[1]+10]^1)
        self.reject_structure_under_new_hash(raw)

    def test_current_counter_corruption_below_root_hash(self):
        raw=self.altered_save(self.new[0]+0xffc,21)
        self.reject_structure_under_new_hash(raw)

    def test_previous_bank_modified_even_with_valid_checksum(self):
        raw=bytearray(self.after);pos=self.old[0];raw[pos+10]^=1
        struct.pack_into('<H',raw,pos+0xff6,m.sectors.checksum(bytes(raw[pos:pos+m.sectors.LAYOUT[0][1]])))
        self.reject_structure_under_new_hash(bytes(raw))

    def test_new_hm_move_in_party_rejected_with_valid_checksum(self):
        raw=self.altered_save(self.new[1]+56+244,148,1)
        self.reject_structure_under_new_hash(raw)

    def test_national_dex_magic_rejected_with_valid_checksum(self):
        raw=self.altered_save(self.new[0]+0x1b,0xb9,0)
        self.reject_structure_under_new_hash(raw)

    def test_s61e_corruption_outside_stock_checksum_rejected(self):
        raw=self.altered_save(self.new[13]+0x7d0,self.after[self.new[13]+0x7d0]^1)
        self.reject_structure_under_new_hash(raw)

    def test_saved_trainer_flag_injection_rejected_with_valid_checksum(self):
        offset=self.new[1]+0xee0+10
        raw=self.altered_save(offset,self.after[offset]^1,1)
        self.reject_structure_under_new_hash(raw)

    def test_current_bag_or_money_cannot_be_reinterpreted(self):
        a,ma=m.shared.bag(self.before,self.old);b,mb=m.shared.bag(self.after,self.new)
        with patch.object(m.shared,'bag',side_effect=[(a,ma),(b,mb+1)]):
            with self.assertRaises(ValueError):m.save_structure(self.before,self.after,self.after)

    def test_rooted_five_trainers_and_cave_scope(self):
        v=m.owners(self.rom)
        self.assertEqual([x['physical_bit'] for x in v['trainers']],[1382,1388,1374,1376,1377])
        self.assertEqual((v['trainer_nodes'],v['cave_nodes'],v['graph_diagnostics']),(30,1,0))
        self.assertTrue(v['world_map_flag2217_owner_verified'])
        self.assertFalse(v['return_warp_executed'])
        self.assertFalse(v['flag2056_runtime_owner_resolved'])

    def test_warp_elevation_must_come_from_source_not_destination(self):
        original=m.source.map_view
        def changed(raw,groups,g,n):
            v=original(raw,groups,g,n)
            if (g,n)==(3,21):v['warps'][0]['elevation']=3
            return v
        with patch.object(m.source,'map_view',side_effect=changed):
            with self.assertRaises(ValueError):m.owners(self.rom)

    def test_different_rom_not_owner_proof(self):
        with self.assertRaises(ValueError):m.owners(b'not the ROM')


if __name__=='__main__':unittest.main()
