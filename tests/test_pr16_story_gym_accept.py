"""今回の2戦・Save19/cold・新報酬だけの負例検査。旧受入suite/nativeを呼ばない。"""
import base64
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_gym_accept as m


def battles():
    layout=[(m.FIELD,0,0),(m.FIELD,1,0),(m.BATTLE,1,0),(m.PARTY_UI,1,0),
            (m.BATTLE,1,0),(m.BATTLE,1,1),(m.FIELD,0,1),(m.FIELD,1,1),
            (m.BATTLE,1,0),(m.BATTLE,1,1),(m.FIELD,1,1),(m.FIELD,1,1),
            (m.FIELD,0,1),(m.FIELD,0,1)]
    return [dict(observe=i,frame=1390+100*i,callback2=cb,lock=lock,battle_outcome=outcome,
                 battle_flags=0 if i<2 else 12,map=[6,2],save_counter=18,party_count=4,rp=0)
            for i,(cb,lock,outcome) in enumerate(layout)]


def completed():
    last=dict(save_counter=19,map=[5,4],xy=[7,4],live_xy=[14,11],facing=2,party_count=4,rp=0,
              callback2=m.FIELD,lock=0,field=True,party_sha256=m.PARTY,flash_sha256=m.FLASH,
              ledger_sha256=m.LEDGER,battle_flags=12,battle_outcome=1)
    cold=[dict(last,battle_flags=0,battle_outcome=0,lock=0 if i in (0,5,11) else 1,
               callback2=m.PARTY_UI if i == 3 else m.CARD_UI if i == 9 else m.FIELD) for i in range(12)]
    return last,cold


def legacy():
    fa=bytearray(0x120);fb=bytearray(0x120);va=[0]*256;vb=[0]*256
    for flag,a,b in m.FLAG_DELTA:
        fa[flag//8]|=a<<(flag%8);fb[flag//8]|=b<<(flag%8)
    for var,a,b in m.VAR_DELTA:va[var-0x4000]=a;vb[var-0x4000]=b
    return (bytes(fa),va),(bytes(fb),vb)


def expanded(changes=False,extra=None):
    p=bytearray(0x606)
    if changes:p[0]=64;p[257]=1;p[319]=32
    if extra is not None:p[extra]^=1
    payload=bytes(p);crc=zlib.crc32(payload)
    return struct.pack('<4sHHII',b'S61E',1,0x606,crc,crc^0xffffffff)+payload


def bags():
    a={'items':[(0,0)]*42,'balls':[(4,3)]+[(0,0)]*12,'berries':[(0,0)]*43,
       'key_items':[(361,1)]+[(0,0)]*29,'machines':[(0,0)]*58}
    b=copy.deepcopy(a);b['key_items'][:4]=[(361,1),(347,1),(348,1),(364,1)];b['machines'][0]=(303,1)
    return a,b


class EpisodeTests(unittest.TestCase):
    def bad(self,index,key,value):
        obs=battles();obs[index][key]=value
        with self.assertRaises(ValueError):m.episodes(obs)
    def test_two_distinct_victories(self):
        result=m.episodes(battles())
        self.assertEqual([(r['start'],r['victory'],r['field_return'],r['unlocked']) for r in result],[(2,5,6,6),(8,9,10,12)])
        self.assertEqual(result[0]['party_ui'],[3])
    def test_stale_field_outcome_is_not_third(self):self.assertEqual(len(m.episodes(battles())),2)
    def test_duplicate_observation(self):self.bad(4,'observe',3)
    def test_nonmonotonic_frame(self):self.bad(4,'frame',0)
    def test_boolean_frame(self):self.bad(4,'frame',True)
    def test_unknown_callback(self):self.bad(4,'callback2',0)
    def test_wild_flags(self):self.bad(4,'battle_flags',0)
    def test_loss(self):self.bad(5,'battle_outcome',2)
    def test_ko_without_victory(self):self.bad(5,'battle_outcome',0)
    def test_reset_after_victory(self):
        obs=battles();obs[4]['battle_outcome']=1;obs[5]['battle_outcome']=0
        with self.assertRaises(ValueError):m.episodes(obs)
    def test_party_ui_after_victory(self):self.bad(5,'callback2',m.PARTY_UI)
    def test_party_ui_outside_battle(self):self.bad(1,'callback2',m.PARTY_UI)
    def test_second_start_must_reset(self):self.bad(8,'battle_outcome',1)
    def test_missing_approach_lock(self):self.bad(1,'lock',0)
    def test_battle_unlock(self):self.bad(4,'lock',0)
    def test_wrong_map(self):self.bad(4,'map',[22,1])
    def test_wrong_parent_counter(self):self.bad(4,'save_counter',17)
    def test_party_injection(self):self.bad(4,'party_count',5)
    def test_rp_injection(self):self.bad(4,'rp',1)
    def test_missing_final_unlock(self):
        obs=battles();obs[12]['lock']=obs[13]['lock']=1
        with self.assertRaises(ValueError):m.episodes(obs)
    def test_truncated_second_battle(self):
        with self.assertRaises(ValueError):m.episodes(battles()[:10])
    def test_third_battle_rejected(self):
        obs=battles();row=dict(obs[-1],observe=14,frame=3000,callback2=m.BATTLE,lock=1,battle_outcome=0);obs.append(row)
        with self.assertRaises(ValueError):m.episodes(obs)


class CompletionTests(unittest.TestCase):
    def bad(self,key,value,index=None):
        last,rows=completed();(last if index is None else rows[index])[key]=value
        with self.assertRaises(ValueError):m.completion(last,rows)
    def test_save19_party_card_and_cold(self):m.completion(*completed())
    def test_incomplete_save18(self):self.bad('save_counter',18)
    def test_cold_fallback18(self):self.bad('save_counter',18,0)
    def test_completed_counter_but_locked(self):self.bad('lock',1)
    def test_partial_flash(self):self.bad('flash_sha256','0'*64)
    def test_cold_flash_changed(self):self.bad('flash_sha256','0'*64,11)
    def test_cold_party_changed(self):self.bad('party_sha256','0'*64,3)
    def test_cold_ledger_changed(self):self.bad('ledger_sha256','0'*64,0)
    def test_missing_party_ui(self):self.bad('callback2',m.FIELD,3)
    def test_missing_trainer_card(self):self.bad('callback2',m.FIELD,9)
    def test_card_unlocked(self):self.bad('lock',0,9)
    def test_cold_battle_residue(self):self.bad('battle_flags',12,0)
    def test_cold_victory_residue(self):self.bad('battle_outcome',1,11)
    def test_wrong_field_position(self):self.bad('xy',[7,5])
    def test_wrong_live_position(self):self.bad('live_xy',[14,12])
    def test_wrong_map(self):self.bad('map',[3,1])
    def test_wrong_facing(self):self.bad('facing',1)
    def test_boolean_counter(self):self.bad('save_counter',True)
    def test_integer_field_boolean(self):self.bad('field',1)
    def test_cold_rp(self):self.bad('rp',1,0)
    def test_missing_cold_ending(self):
        last,rows=completed()
        with self.assertRaises(ValueError):m.completion(last,rows[:-1])


class SavedStateTests(unittest.TestCase):
    def mutate_flag(self,flag):
        a,b=legacy();fb=bytearray(b[0]);fb[flag//8]^=1<<(flag%8)
        with self.assertRaises(ValueError):m.state_delta(a,(bytes(fb),b[1]))
    def test_exact_badge_trainers_and_story(self):self.assertEqual(m.state_delta(*legacy())['physical_flag_deltas'],m.FLAG_DELTA)
    def test_missing_badge(self):self.mutate_flag(0x820)
    def test_wrong_physical_trainer(self):self.mutate_flag(1422)
    def test_extra_flag(self):self.mutate_flag(900)
    def test_national_flag_injection(self):self.mutate_flag(0x840)
    def test_national_var_injection(self):
        a,b=legacy();b[1][0x4e]=1
        with self.assertRaises(ValueError):m.state_delta(a,b)
    def test_incomplete_mosugis_stage(self):
        a,b=legacy();b[1][0x71]=4
        with self.assertRaises(ValueError):m.state_delta(a,b)
    def test_truncated_flag_bitmap(self):
        a,b=legacy()
        with self.assertRaises(ValueError):m.state_delta((a[0][:-1],a[1]),b)
    def test_new_expanded_deltas(self):self.assertTrue(m.expanded_boundary(expanded(),expanded(True))['expanded_vars_ball_coins_unchanged'])
    def test_missing_window_flag(self):
        with self.assertRaises(ValueError):m.expanded_boundary(expanded(),expanded(True,257))
    def test_other_expanded_var(self):
        with self.assertRaises(ValueError):m.expanded_boundary(expanded(),expanded(True,0x200))
    def test_other_expanded_flag(self):
        with self.assertRaises(ValueError):m.expanded_boundary(expanded(),expanded(True,33))
    def test_corrupt_expanded_crc(self):
        raw=bytearray(expanded(True));raw[8]^=1
        with self.assertRaises(ValueError):m.expanded_boundary(expanded(),bytes(raw))
    def test_corrupt_expanded_complement(self):
        raw=bytearray(expanded(True));raw[12]^=1
        with self.assertRaises(ValueError):m.expanded_boundary(expanded(),bytes(raw))
    def test_partial_save_bytes(self):
        with self.assertRaises(ValueError):m.save_structure(b'\0'*131087,b'\0'*131088,b'\0'*131088)
    def test_changed_cold_rtc(self):
        with self.assertRaises(ValueError):m.save_structure(b'\0'*131088,b'\0'*131088,b'\0'*131087+b'\1')


class RewardTests(unittest.TestCase):
    def bad(self,pocket,index,value):
        a,b=bags();b[pocket][index]=value
        with self.assertRaises(ValueError):m.bag_boundary(a,b,3940,5776)
    def test_only_new_rewards(self):self.assertEqual(m.bag_boundary(*bags(),3940,5776)['key_items_added'],[347,348,364])
    def test_wrong_money(self):
        with self.assertRaises(ValueError):m.bag_boundary(*bags(),3940,5777)
    def test_wrong_tm(self):self.bad('machines',0,(339,1))
    def test_duplicate_key_reward(self):self.bad('key_items',4,(347,1))
    def test_missing_auxiliary_reward(self):self.bad('key_items',3,(0,0))
    def test_ball_changed(self):self.bad('balls',0,(4,2))
    def test_item_injection(self):self.bad('items',0,(13,1))
    def test_missing_pocket(self):
        a,b=bags();del b['berries']
        with self.assertRaises(ValueError):m.bag_boundary(a,b,3940,5776)


class PlanTests(unittest.TestCase):
    def plan(self):return json.loads((m.ROOT/m.DEV/'expected.json').read_text())
    def test_complete_new_input_plan(self):
        result=m.decode_plan(self.plan());self.assertEqual(len(result['progress']),6816);self.assertEqual(len(result['continue']),318)
    def test_old_parent_rejected(self):
        p=self.plan();p['input_save']['sha256']='0'*64
        with self.assertRaises(ValueError):m.decode_plan(p)
    def test_missing_cold_quit(self):
        p=self.plan();p['continue']['commands_text']=p['continue']['commands_text'].removesuffix('quit\n')
        with self.assertRaises(ValueError):m.decode_plan(p)
    def test_fixture_command_rejected(self):
        p=self.plan();p['continue']['commands_text']='fixture\nquit\n'
        with self.assertRaises(ValueError):m.decode_plan(p)
    def test_appended_compressed_stream_rejected(self):
        p=self.plan();raw=base64.b85decode(p['progress']['commands_zlib_b85'])+zlib.compress(b'quit\n')
        p['progress']['commands_zlib_b85']=base64.b85encode(raw).decode()
        with self.assertRaises(ValueError):m.decode_plan(p)
    def test_compressed_overlong_program_rejected(self):
        p=self.plan();p['progress']['commands_zlib_b85']=base64.b85encode(zlib.compress(b'x'*50000)).decode()
        with self.assertRaises(ValueError):m.decode_plan(p)


if __name__=='__main__':unittest.main()
