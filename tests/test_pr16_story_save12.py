"""実測57画面を使うSave12専用検査。旧受入試験とnativeは起動しない。"""
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
import pr16_story_save12 as m


class Save12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=Path(os.environ['PR16_SAVE12_ROOT']);cls.public=cls.folder/'public'
        cls.raw=(cls.public/'progress.stdout.txt').read_bytes()
        cls.cold_raw=(cls.public/'continue.stdout.txt').read_bytes()
        cls.command=(cls.public/'commands.txt').read_bytes()
        cls.cold_command=(cls.public/'continue-commands.txt').read_bytes()
        cls.before=(cls.folder/'private/input.srm').read_bytes()
        cls.after=(cls.folder/'private/training.srm').read_bytes()
        cls.cold=(cls.folder/'private/cold.srm').read_bytes()
        cls.parent=json.loads((ROOT/m.PARENT).read_text())
        cls.review=(ROOT/m.DEV/'verification.json').read_bytes()
        cls.a=m.trace(cls.raw,cls.command,m.INPUT_SAVE);cls.b=m.trace(cls.cold_raw,cls.cold_command,m.OUTPUT_SAVE)

    def test_full_saved_original_report(self):
        v=m.verify(self.raw,self.cold_raw,self.command,self.cold_command,self.parent,self.review,
                   self.folder/'progress',self.folder/'continue')
        self.assertEqual((v['screen_count'],v['full_image_comparisons']),(57,7))
        self.assertEqual(v['hp'],[[26,26],[15,15]])
        self.assertEqual(v['moves_pp'],[[35,30,25],[35,40]])
        self.assertEqual(v['experience_gained'],0)
        self.assertFalse(v['regional_pokedex_integration_accepted'])

    def test_all_save_and_rtc_bytes(self):
        p=m.saved_bytes(self.before,self.after,self.cold)
        self.assertEqual(p['save_counters'],[11,12,12])
        self.assertEqual(p['previous_save_bank_preserved_bytes'],57344)
        self.assertEqual(p['unused_party_bytes_preserved'],400)
        self.assertTrue(p['all_save_rtc_preserved_after_continue'])

    def test_walking_is_not_healing(self):
        p=m.save_structure(self.before,self.after,self.cold)
        self.assertEqual(p['walking_friendship_changed_offsets'],[41,141])
        self.assertEqual(p['healing_changed_offsets'],[54,86,152,153,186])
        self.assertEqual(self.a['observations'][26]['party_sha256'],m.PARTY_WALK)
        self.assertEqual(self.a['observations'][27]['party_sha256'],m.PARTY_AFTER)

    def test_locked_save_message_and_field_are_separate(self):
        v=m.semantic(self.a,self.b,self.parent)
        self.assertFalse(v['first_save']['field'])
        self.assertTrue(v['progress_field']['field'])
        self.assertTrue(v['continued']['field'])

    def test_review_has_all_57_images_and_no_victories(self):
        r=m.review(self.review)
        self.assertEqual((len(r['anchors']),len(r['cold_anchors'])),(48,9))
        self.assertEqual(r['claims']['trainer_victories'],0)
        self.assertEqual(r['claims']['captures'],0)
        self.assertFalse(r['claims']['natural_research_arrival'])
        self.assertFalse(r['claims']['release_ready'])

    def test_existing_unused_ff_sentinel_is_preserved(self):
        a=m.sections(self.before,0xe000,11)[1]+0x38
        b=m.sections(self.after,0,12)[1]+0x38
        self.assertEqual(self.before[a+285],255)
        self.assertEqual(self.before[a+200:a+600],self.after[b+200:b+600])


def semantic_case(which,index,key,value):
    def test(self):
        a,b=copy.deepcopy(self.a),copy.deepcopy(self.b)
        (a if which=='a' else b)['observations'][index][key]=value
        with self.assertRaises(ValueError):m.semantic(a,b,self.parent)
    return test

for name,which,index,key,value in [
    ('wrong_parent_position','a',0,'xy',[4,4]),
    ('wrong_road_connection','a',8,'map',[3,19]),
    ('wrong_home','a',14,'map',[4,3]),
    ('invented_rp','a',27,'rp',1),
    ('hidden_battle','a',10,'battle_flags',4),
    ('invented_victory','a',26,'battle_outcome',1),
    ('invented_capture','a',27,'battle_outcome',7),
    ('lost_party_member','a',32,'party_count',1),
    ('premature_healing','a',26,'party_sha256',m.PARTY_AFTER),
    ('missing_walk_friendship','a',11,'party_sha256',m.prior.PARTY_AFTER),
    ('missing_healing','a',27,'party_sha256',m.PARTY_WALK),
    ('party_ui_owner','a',32,'callback2',m.INFO),
    ('dialog_not_field','a',30,'field',True),
    ('save_complete_is_locked','a',46,'lock',0),
    ('missing_field_return','a',47,'lock',1),
    ('early_save_counter','a',45,'save_counter',12),
    ('early_complete_flash','a',45,'flash_sha256',m.FLASH_AFTER),
    ('unsaved_flash_rewrite','a',40,'flash_sha256',m.FLASH_AFTER),
    ('cold_no_battle','b',3,'battle_flags',4),
    ('cold_party_count','b',1,'party_count',3),
    ('cold_counter','b',7,'save_counter',11),
    ('cold_position','b',8,'xy',[8,4]),
    ('cold_facing','b',8,'facing',3),
    ('cold_party_bytes','b',6,'party_sha256','0'*64),
    ('cold_flash_bytes','b',8,'flash_sha256','0'*64),
    ('cold_ledger_bytes','b',0,'ledger_sha256','0'*64),
    ('cold_summary_owner','b',4,'callback2',m.PARTY),
    ('duplicate_observation','a',20,'observe',19),
    ('frame_rewind','a',20,'frame',1),
    ('boolean_not_integer','a',20,'lock',True),
]:setattr(Save12Tests,'test_semantic_reject_'+name,semantic_case(which,index,key,value))


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
]:setattr(Save12Tests,'test_raw_reject_'+name,raw_case(selector,key,value))


def saved_case(section,offset):
    def test(self):
        raw=bytearray(self.after)
        base=m.sections(bytes(raw),0,12)[section] if section is not None else 0
        raw[base+offset]^=1
        with self.assertRaises(ValueError):m.save_structure(self.before,bytes(raw),bytes(raw))
    return test

for name,section,offset in [
    ('count',1,0x34),('first_pp',1,0x38+54),('first_hp',1,0x38+86),
    ('first_friendship',1,0x38+41),('second_friendship',1,0x38+141),
    ('second_species',1,0x38+132),('second_exp',1,0x38+136),
    ('second_pp',1,0x38+152),('second_hp',1,0x38+186),('unused_slot',1,0x38+250),
    ('ball_count',1,0x432),('other_pocket',1,0x310),('money',1,0x290),
    ('parent_bank',None,0xe000+100),('ledger_clock',None,0x1f064+0x746),
    ('ledger_checksum',None,0x1f064+8),('section_signature',None,0xff8),
]:setattr(Save12Tests,'test_save_reject_'+name,saved_case(section,offset))


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
        p=copy.deepcopy(self.parent);p['retained_artifact_id']=10970079659
        with self.assertRaises(ValueError):m.parent_boundary(p)
    def false_review(self):
        r=json.loads(self.review);r['claims']['trainer_victories']=1
        with self.assertRaises(ValueError):m.review((json.dumps(r)+'\n').encode())
    def helper_command(self):
        with self.assertRaises(ValueError):m.commands(b'save\nquit\n')
    def screen_tamper(self):
        r=bytearray((self.folder/'progress/screen-0032.ppm').read_bytes());r[-1]^=1
        with self.assertRaises(ValueError):m.screen_bytes(bytes(r),self.a['screens'][32])
    return locals()
for name,fn in extra_tests().items():setattr(Save12Tests,'test_reject_'+name,fn)

if __name__=='__main__':unittest.main()
