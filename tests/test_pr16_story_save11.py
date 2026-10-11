"""実測83画面を使うSave11専用検査。旧受入/旧28境界試験は呼ばない。"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import struct
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save11 as m


class Save11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = Path(os.environ['PR16_SAVE11_ROOT'])
        cls.public = cls.folder/'public'
        cls.raw = (cls.public/'progress.stdout.txt').read_bytes()
        cls.cold_raw = (cls.public/'continue.stdout.txt').read_bytes()
        cls.command = (cls.public/'commands.txt').read_bytes()
        cls.cold_command = (cls.public/'continue-commands.txt').read_bytes()
        cls.before = (cls.folder/'private/input.srm').read_bytes()
        cls.after = (cls.folder/'private/training.srm').read_bytes()
        cls.cold = (cls.folder/'private/cold.srm').read_bytes()
        cls.parent = json.loads((ROOT/m.PARENT).read_text())
        cls.review = (ROOT/m.DEV/'verification.json').read_bytes()
        cls.a = m.trace(cls.raw,cls.command,m.INPUT_SAVE)
        cls.b = m.trace(cls.cold_raw,cls.cold_command,m.OUTPUT_SAVE)

    def test_full_saved_original_report(self):
        v=m.verify(self.raw,self.cold_raw,self.command,self.cold_command,self.parent,self.review,
                   self.folder/'progress',self.folder/'continue')
        self.assertEqual((v['captures'],v['capture_attempts'],v['failed_capture_attempts']),(1,2,1))
        self.assertEqual((v['screen_count'],v['full_image_comparisons']),(83,7))
        self.assertFalse(v['regional_pokedex_integration_accepted'])

    def test_all_save_and_rtc_bytes(self):
        p=m.saved_bytes(self.before,self.after,self.cold)
        self.assertEqual(p['save_counters'],[10,11,11])
        self.assertEqual(p['previous_save_bank_preserved_bytes'],57344)
        self.assertEqual(p['unused_party_bytes_preserved'],400)
        self.assertTrue(p['all_save_rtc_preserved_after_continue'])

    def test_capture_residue_not_counted_again(self):
        e=m.capture_boundary(self.a['observations'])
        self.assertEqual((e['start'],e['end'],e['outcome'],e['captures']),(10,47,7,1))
        self.assertEqual((e['wild_victories'],e['trainer_victories'],e['escapes']),(0,0,0))

    def test_locked_save_message_and_cold_field_are_separate(self):
        v=m.semantic(self.a,self.b,self.parent)
        self.assertEqual(v['first_save']['lock'],1)
        self.assertFalse(v['first_save']['field'])
        self.assertEqual(v['continued']['lock'],0)
        self.assertTrue(v['continued']['field'])

    def test_review_scope_excludes_release_and_pokedex(self):
        v=m.review(self.review)
        self.assertFalse(v['claims']['regional_pokedex_integration'])
        self.assertFalse(v['claims']['release_ready'])
        self.assertEqual(v['nonidentical_pairs'][0]['changed_pixels'],80)

    def test_empty_slots_keep_existing_ff_sentinel(self):
        before=m.sections(self.before,0,10)[1]+0x38
        after=m.sections(self.after,0xe000,11)[1]+0x38
        self.assertEqual(self.before[before+285],255)
        self.assertEqual(self.after[after+285],255)
        self.assertEqual(self.before[before+200:before+600],self.after[after+200:after+600])


def boundary_case(index,key,value):
    def test(self):
        a=copy.deepcopy(self.a)
        a['observations'][index][key]=value
        with self.assertRaises(ValueError):m.capture_boundary(a['observations'])
    return test

for name,index,key,value in [
    ('missing_wild_start',10,'callback2',m.FIELD),
    ('trainer_capture',10,'battle_flags',12),
    ('capture_without_start',9,'battle_outcome',7),
    ('first_ball_not_a_win',18,'battle_outcome',1),
    ('first_ball_not_escape',18,'battle_outcome',4),
    ('premature_party_addition',40,'party_count',2),
    ('nickname_not_capture_end',44,'battle_outcome',7),
    ('nickname_callback_owner',45,'callback2',m.BATTLE),
    ('missing_capture_return',47,'callback2',m.BATTLE),
    ('capture_is_not_victory',47,'battle_outcome',1),
    ('capture_requires_added_mon',47,'party_count',1),
    ('capture_return_unlocked',47,'lock',1),
    ('residual_outcome_must_not_change',58,'battle_outcome',4),
    ('no_second_battle',58,'callback2',m.BATTLE),
    ('no_extra_party_member',59,'party_count',3),
    ('no_duplicate_observation',35,'observe',34),
    ('no_frame_rewind',35,'frame',1),
    ('boolean_not_integer',10,'battle_flags',True),
]:
    setattr(Save11Tests,'test_boundary_reject_'+name,boundary_case(index,key,value))


def semantic_case(which,index,key,value):
    def test(self):
        a,b=copy.deepcopy(self.a),copy.deepcopy(self.b)
        (a if which=='a' else b)['observations'][index][key]=value
        with self.assertRaises(ValueError):m.semantic(a,b,self.parent)
    return test

for name,which,index,key,value in [
    ('wrong_parent_position','a',0,'xy',[4,4]),
    ('wrong_destination','a',4,'map',[4,3]),
    ('invented_rp','a',50,'rp',1),
    ('early_save_counter','a',68,'save_counter',11),
    ('early_complete_flash','a',68,'flash_sha256',m.FLASH_AFTER),
    ('unsaved_flash_rewrite','a',30,'flash_sha256',m.FLASH_AFTER),
    ('save_complete_not_field_unlock','a',69,'field',True),
    ('cold_was_not_new_battle','b',5,'battle_flags',4),
    ('cold_party_not_one','b',1,'party_count',1),
    ('cold_counter_retention','b',7,'save_counter',10),
    ('cold_position_retention','b',12,'xy',[14,10]),
    ('cold_party_bytes','b',8,'party_sha256','0'*64),
    ('cold_flash_bytes','b',12,'flash_sha256','0'*64),
    ('cold_field_unlocked','b',12,'lock',1),
]:
    setattr(Save11Tests,'test_semantic_reject_'+name,semantic_case(which,index,key,value))


def raw_case(selector,key,value):
    def test(self):
        rows=[json.loads(line) for line in self.raw.splitlines()]
        target=next(r for r in rows if selector in r)
        target[key]=value
        raw=b''.join((json.dumps(r)+'\n').encode() for r in rows)
        with self.assertRaises(ValueError):m.trace(raw,self.command,m.INPUT_SAVE)
    return test

for name,selector,key,value in [
    ('wrong_save_identity','begin','initial_save_sha256','0'*64),
    ('wrong_rom_identity','begin','candidate_sha256','0'*64),
    ('unexpected_input','input','key',255),
    ('screen_frame_not_observation','screen','frame',1391),
    ('guarded_host_write','end','guarded_host_writes',1),
    ('fixture_call','end','fixture_calls',1),
    ('warning','end','warnings_errors',1),
    ('claim_research_arrival','end','natural_research_arrival_accepted',True),
]:
    setattr(Save11Tests,'test_raw_reject_'+name,raw_case(selector,key,value))


def saved_case(which,section,offset):
    def test(self):
        before,after,cold=self.before,self.after,self.cold
        raw=bytearray(before if which=='before' else after)
        base=m.sections(bytes(raw),0 if which=='before' else 0xe000,10 if which=='before' else 11)[section] if section is not None else 0
        raw[base+offset]^=1
        if which=='before':before=bytes(raw)
        else:after=cold=bytes(raw)
        with self.assertRaises(ValueError):m.save_structure(before,after,cold)
    return test

for name,which,section,offset in [
    ('count','after',1,0x34),('first_pp','after',1,0x38+54),('first_hp','after',1,0x38+86),
    ('captured_species','after',1,0x38+132),('captured_exp','after',1,0x38+136),
    ('captured_pp','after',1,0x38+152),('unused_slot','after',1,0x38+250),
    ('ball_count','after',1,0x432),('other_pocket','after',1,0x310),('money','after',1,0x290),
    ('parent_bank','after',None,100),('ledger_clock','after',None,0x1f064+0x746),
    ('ledger_checksum','after',None,0x1f064+8),('section_signature','after',None,0xe000+0xff8),
]:
    setattr(Save11Tests,'test_save_reject_'+name,saved_case(which,section,offset))


def reject_extra_tests():
    def missing_observation(self):
        with self.assertRaises(ValueError):m.capture_boundary(self.a['observations'][:-1])
    def extra_observation(self):
        with self.assertRaises(ValueError):m.capture_boundary(self.a['observations']+[self.a['observations'][-1]])
    def cold_rtc_mutation(self):
        cold=bytearray(self.cold);cold[-1]^=1
        with self.assertRaises(ValueError):m.save_structure(self.before,self.after,bytes(cold))
    def wrong_parent_terminal(self):
        parent=copy.deepcopy(self.parent);parent['actions_completion_confirmed']=False
        with self.assertRaises(ValueError):m.parent_boundary(parent)
    def wrong_parent_artifact(self):
        parent=copy.deepcopy(self.parent);parent['retained_artifact_id']=10963436148
        with self.assertRaises(ValueError):m.parent_boundary(parent)
    def false_review(self):
        review=json.loads(self.review);review['claims']['captures']=2
        with self.assertRaises(ValueError):m.review((json.dumps(review)+'\n').encode())
    def helper_command(self):
        with self.assertRaises(ValueError):m.commands(b'save\nquit\n')
    def screen_tamper(self):
        raw=bytearray((self.folder/'progress/screen-0041.ppm').read_bytes());raw[-1]^=1
        with self.assertRaises(ValueError):m.screen_bytes(bytes(raw),self.a['screens'][41])
    return locals()
for name,fn in reject_extra_tests().items():setattr(Save11Tests,'test_reject_'+name,fn)

if __name__ == '__main__':unittest.main()
