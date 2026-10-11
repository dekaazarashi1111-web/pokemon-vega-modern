"""Save13の実測76画面を読む新規試験。旧試験/nativeは起動しない。"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save13 as m


class Save13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=Path(os.environ['PR16_SAVE13_ROOT']);cls.public=cls.folder/'public'
        cls.raw=(cls.public/'progress.stdout.txt').read_bytes();cls.cold_raw=(cls.public/'continue.stdout.txt').read_bytes()
        cls.command=(cls.public/'commands.txt').read_bytes();cls.cold_command=(cls.public/'continue-commands.txt').read_bytes()
        cls.before=(cls.folder/'private/input.srm').read_bytes();cls.after=(cls.folder/'private/training.srm').read_bytes()
        cls.cold=(cls.folder/'private/cold.srm').read_bytes();cls.parent=json.loads((ROOT/m.PARENT).read_text())
        cls.review=(ROOT/m.DEV/'verification.json').read_bytes()
        cls.a=m.trace(cls.raw,cls.command,m.INPUT_SAVE);cls.b=m.trace(cls.cold_raw,cls.cold_command,m.OUTPUT_SAVE)

    def test_full_originals_and_76_images(self):
        v=m.verify(self.raw,self.cold_raw,self.command,self.cold_command,self.parent,self.review,self.folder/'progress',self.folder/'continue')
        self.assertEqual((v['screen_count'],v['full_image_comparisons']),(76,7))
        self.assertEqual(v['experience_gained_by_species'],{'1129':53,'1':29})
        self.assertEqual(v['hp'],[[17,17],[26,26]])
        self.assertEqual(v['party_species'],[1129,1])
        self.assertFalse(v['natural_research_arrival_accepted'])

    def test_save_rtc_and_previous_bank(self):
        p=m.saved_bytes(self.before,self.after,self.cold)
        self.assertEqual(p['save_counters'],[12,13,13])
        self.assertEqual(p['previous_save_bank_preserved_bytes'],57344)
        self.assertTrue(p['all_save_rtc_preserved_after_continue'])

    def test_party_order_and_exact_aligned_delta(self):
        p=m.save_structure(self.before,self.after,self.cold)
        self.assertEqual(p['party_species_before'],[1,1129]);self.assertEqual(p['party_species_after'],[1129,1])
        self.assertEqual(len(p['aligned_party_changed_bytes']),14)
        self.assertEqual(p['unused_party_bytes_preserved'],400)

    def test_normal_switch_is_one_wild_victory(self):
        e=m.victory_boundary(self.a['observations'])
        self.assertEqual((e['start'],e['end'],e['wild_victories'],e['normal_battle_switches']),(14,30,1,1))
        self.assertEqual(e['trainer_victories'],0)
        self.assertEqual(self.a['observations'][24]['battle_outcome'],0)
        self.assertEqual(self.a['observations'][29]['battle_outcome'],0)

    def test_residue_is_not_extra_victories_or_stuck_battle(self):
        o=self.a['observations'][66]
        self.assertEqual((o['callback2'],o['lock'],o['battle_flags'],o['battle_outcome']),(m.FIELD,0,4,1))
        self.assertIs(o['field'],False)
        self.assertEqual(m.semantic(self.a,self.b,self.parent)['victory_episode']['wild_victories'],1)
        self.assertIs(self.b['observations'][-1]['field'],True)

    def test_save_message_and_unlocked_return_are_distinct(self):
        v=m.semantic(self.a,self.b,self.parent)
        self.assertEqual(v['first_save']['lock'],1);self.assertEqual(v['progress_field']['lock'],0)
        self.assertIs(v['first_save']['field'],False);self.assertIs(v['progress_field']['field'],False)
        self.assertTrue(v['continued']['field'])

    def test_growth_persists_while_only_two_bytes_heal(self):
        p=m.save_structure(self.before,self.after,self.cold)
        self.assertEqual(p['experience_after_by_species'],{'1129':80,'1':479})
        self.assertEqual(p['normal_healing_changed_offsets'],[152,186])
        self.assertTrue(p['all_five_bag_pockets_unchanged'])
        self.assertEqual(p['poke_balls_after'],3);self.assertEqual(p['money_after'],2776)

    def test_review_has_battle_xp_and_unaccepted_dex(self):
        r=m.review(self.review)
        self.assertEqual((len(r['anchors']),len(r['cold_anchors'])),(67,9))
        self.assertEqual(r['claims']['wild_victories'],1)
        self.assertEqual(r['claims']['captures'],0)
        self.assertFalse(r['claims']['regional_pokedex_integration'])
        self.assertFalse(r['claims']['full_story']);self.assertFalse(r['claims']['release_ready'])


def semantic_case(which,index,key,value):
    def test(self):
        a,b=copy.deepcopy(self.a),copy.deepcopy(self.b)
        (a if which=='a' else b)['observations'][index][key]=value
        with self.assertRaises(ValueError):m.semantic(a,b,self.parent)
    return test

for name,which,index,key,value in [
    ('wrong_parent_position','a',0,'xy',[4,4]),
    ('premature_reorder','a',3,'party_sha256',m.PARTY_PHASES[1][1]),
    ('missing_reorder','a',4,'party_sha256',m.prior.PARTY_AFTER),
    ('wrong_road_connection','a',8,'map',[3,0]),
    ('wrong_home','a',44,'map',[4,3]),
    ('invented_rp','a',30,'rp',1),
    ('battle_before_encounter','a',13,'battle_flags',4),
    ('trainer_instead_of_wild','a',14,'battle_flags',8),
    ('missing_wild_start','a',14,'callback2',m.FIELD),
    ('premature_victory_at_faint','a',24,'battle_outcome',1),
    ('premature_victory_at_experience','a',29,'battle_outcome',1),
    ('missing_victory_endpoint','a',30,'battle_outcome',0),
    ('capture_is_not_victory','a',30,'battle_outcome',7),
    ('loss_is_not_victory','a',30,'battle_outcome',2),
    ('escape_is_not_victory','a',30,'battle_outcome',4),
    ('victory_callback_not_field','a',30,'callback2',m.BATTLE),
    ('victory_field_still_locked','a',30,'lock',1),
    ('switch_requires_party_ui','a',16,'callback2',m.BATTLE),
    ('switch_selection_requires_party_ui','a',17,'callback2',m.BATTLE),
    ('missing_hp_damage','a',22,'party_sha256',m.PARTY_PHASES[1][1]),
    ('missing_critical_hp_damage','a',23,'party_sha256',m.PARTY_PHASES[2][1]),
    ('missing_level_up','a',26,'party_sha256',m.PARTY_PHASES[5][1]),
    ('lost_party_member','a',35,'party_count',1),
    ('bag_does_not_imply_party','a',33,'callback2',m.PARTY),
    ('summary_requires_info_owner','a',37,'callback2',m.PARTY),
    ('premature_healing','a',46,'party_sha256',m.PARTY_AFTER),
    ('missing_healing','a',47,'party_sha256',m.PARTY_PHASES[-2][1]),
    ('new_battle_after_victory','a',42,'battle_outcome',0),
    ('wire_field_must_keep_residue','a',66,'field',True),
    ('save_message_locked','a',65,'lock',0),
    ('missing_final_field_return','a',66,'lock',1),
    ('early_counter','a',64,'save_counter',13),
    ('early_final_flash','a',64,'flash_sha256',m.FLASH_AFTER),
    ('flash_change_before_save','a',59,'flash_sha256',m.FLASH_AFTER),
    ('cold_no_battle_residue','b',0,'battle_flags',4),
    ('cold_no_outcome_residue','b',0,'battle_outcome',1),
    ('cold_party_count','b',1,'party_count',3),
    ('cold_counter','b',7,'save_counter',12),
    ('cold_position','b',8,'xy',[8,4]),
    ('cold_facing','b',8,'facing',3),
    ('cold_party_bytes','b',6,'party_sha256','0'*64),
    ('cold_flash_bytes','b',8,'flash_sha256','0'*64),
    ('cold_ledger_bytes','b',0,'ledger_sha256','0'*64),
    ('cold_summary_owner','b',4,'callback2',m.PARTY),
    ('duplicate_observation','a',20,'observe',19),
    ('frame_rewind','a',20,'frame',1),
    ('boolean_not_integer','a',20,'lock',True),
    ('cold_boolean_not_integer','b',1,'party_count',True),
]:setattr(Save13Tests,'test_semantic_reject_'+name,semantic_case(which,index,key,value))


def raw_case(selector,key,value):
    def test(self):
        rows=[json.loads(line) for line in self.raw.splitlines()]
        next(r for r in rows if selector in r)[key]=value
        raw=b''.join((json.dumps(r)+'\n').encode() for r in rows)
        with self.assertRaises(ValueError):m.trace(raw,self.command,m.INPUT_SAVE)
    return test

for name,selector,key,value in [
    ('wrong_save_identity','begin','initial_save_sha256','0'*64),
    ('wrong_rom_identity','begin','candidate_sha256','0'*64),
    ('unexpected_input','input','key',255),
    ('screen_frame_mismatch','screen','frame',1391),
    ('host_write','end','guarded_host_writes',1),
    ('fixture_call','end','fixture_calls',1),
    ('warning','end','warnings_errors',1),
    ('research_claim','end','natural_research_arrival_accepted',True),
]:setattr(Save13Tests,'test_raw_reject_'+name,raw_case(selector,key,value))


def saved_case(section,offset):
    def test(self):
        raw=bytearray(self.after)
        base=m.sections(bytes(raw),0xe000,13)[section] if section is not None else 0
        raw[base+offset]^=1
        with self.assertRaises(ValueError):m.save_structure(self.before,bytes(raw),bytes(raw))
    return test

for name,section,offset in [
    ('count',1,0x34),('bird_identity',1,0x38),('bird_pp',1,0x38+52),('bird_hp',1,0x38+86),
    ('bird_friendship',1,0x38+41),('bird_exp',1,0x38+36),('bird_level',1,0x38+84),
    ('bird_training_byte',1,0x38+59),('bird_stats',1,0x38+90),
    ('starter_friendship',1,0x38+141),('starter_species',1,0x38+132),('starter_exp',1,0x38+136),
    ('starter_pp',1,0x38+152),('starter_hp',1,0x38+186),('unused_slot',1,0x38+250),
    ('ball_count',1,0x432),('other_pocket',1,0x310),('money',1,0x290),
    ('parent_bank',None,100),('ledger_clock',None,0x1f064+0x746),
    ('ledger_checksum',None,0x1f064+8),('section_signature',None,0xe000+0xff8),
]:setattr(Save13Tests,'test_save_reject_'+name,saved_case(section,offset))


def extra_tests():
    def missing_observation(self):
        a=copy.deepcopy(self.a);a['observations'].pop()
        with self.assertRaises(ValueError):m.semantic(a,self.b,self.parent)
    def extra_observation(self):
        a=copy.deepcopy(self.a);a['observations'].append(a['observations'][-1])
        with self.assertRaises(ValueError):m.semantic(a,self.b,self.parent)
    def cold_rtc_mutation(self):
        cold=bytearray(self.cold);cold[-1]^=1
        with self.assertRaises(ValueError):m.save_structure(self.before,self.after,bytes(cold))
    def wrong_parent_terminal(self):
        p=copy.deepcopy(self.parent);p['actions_completion_confirmed']=False
        with self.assertRaises(ValueError):m.parent_boundary(p)
    def wrong_parent_artifact(self):
        p=copy.deepcopy(self.parent);p['retained_artifact_id']=10973111478
        with self.assertRaises(ValueError):m.parent_boundary(p)
    def false_review(self):
        r=json.loads(self.review);r['claims']['wild_victories']=2
        with self.assertRaises(ValueError):m.review((json.dumps(r)+'\n').encode())
    def helper_command(self):
        with self.assertRaises(ValueError):m.commands(b'save\nquit\n')
    def screen_tamper(self):
        r=bytearray((self.folder/'progress/screen-0051.ppm').read_bytes());r[-1]^=1
        with self.assertRaises(ValueError):m.screen_bytes(bytes(r),self.a['screens'][51])
    def undone_party_reorder(self):
        raw=bytearray(self.after);p=m.sections(bytes(raw),0xe000,13)[1]+0x38
        raw[p:p+200]=raw[p+100:p+200]+raw[p:p+100]
        with self.assertRaises(ValueError):m.save_structure(self.before,bytes(raw),bytes(raw))
    return locals()
for name,fn in extra_tests().items():setattr(Save13Tests,'test_reject_'+name,fn)

if __name__=='__main__':unittest.main()
