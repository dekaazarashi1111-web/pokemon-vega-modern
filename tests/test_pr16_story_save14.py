"""Save14の新しい原本だけを検査。旧試験/nativeの実行・入力書込はしない。"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save14 as m

class Save14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=Path(os.environ['PR16_SAVE14_ROOT']);p=cls.folder/'public'
        cls.raw=(p/'progress.stdout.txt').read_bytes();cls.cold_raw=(p/'continue.stdout.txt').read_bytes()
        cls.command=(p/'commands.txt').read_bytes();cls.cold_command=(p/'continue-commands.txt').read_bytes()
        cls.before=(cls.folder/'private/input.srm').read_bytes();cls.after=(cls.folder/'private/training.srm').read_bytes()
        cls.cold=(cls.folder/'private/cold.srm').read_bytes();cls.parent=json.loads((ROOT/m.PARENT).read_text())
        cls.review=(ROOT/m.DEV/'verification.json').read_bytes()
        cls.a=m.trace(cls.raw,cls.command,m.INPUT_SAVE);cls.b=m.trace(cls.cold_raw,cls.cold_command,m.OUTPUT_SAVE)

    def test_complete_new_interval_and_97_images(self):
        v=m.verify(self.raw,self.cold_raw,self.command,self.cold_command,self.parent,self.review,self.folder/'progress',self.folder/'continue')
        self.assertEqual((v['screen_count'],v['full_image_comparisons']),(97,7))
        self.assertEqual((v['wild_victories'],v['party_faints'],v['losses']),(1,1,0))
        self.assertEqual((v['normal_battle_switches'],v['forced_replacements']),(2,1))
        self.assertEqual(v['experience_gained_by_species'],{'1129':0,'1':37})
        self.assertFalse(v['natural_research_arrival_accepted']);self.assertFalse(v['release_ready'])

    def test_one_party_faint_does_not_end_battle(self):
        e=m.victory_boundary(self.a['observations'])
        self.assertEqual((e['start'],e['end']),(12,43))
        self.assertTrue(all(o['battle_outcome']==0 for o in self.a['observations'][35:43]))
        self.assertEqual(e['losses'],0)

    def test_cancelled_party_selection_is_not_third_switch(self):
        self.assertEqual(self.a['observations'][23]['party_sha256'],self.a['observations'][20]['party_sha256'])
        e=m.victory_boundary(self.a['observations'])
        self.assertTrue(e['party_menu_cancel_observed']);self.assertEqual(e['normal_battle_switches'],2)

    def test_fainted_bird_receives_no_xp(self):
        v=m.saved_bytes(self.before,self.after,self.cold)
        self.assertEqual(v['experience_after_by_species'],{'1129':80,'1':516})
        self.assertEqual(v['experience_gained_by_species']['1129'],0)
        self.assertEqual(len(v['party_changed_bytes']),3)

    def test_four_heal_bytes_and_unchanged_bag(self):
        v=m.save_structure(self.before,self.after,self.cold)
        self.assertEqual(v['normal_healing_changed_offsets'],[52,86,152,186])
        self.assertTrue(v['all_five_bag_pockets_unchanged'])
        self.assertEqual((v['money_after'],v['poke_balls_after']),(2776,3))

    def test_previous_bank_and_unused_party_preserved(self):
        v=m.saved_bytes(self.before,self.after,self.cold)
        self.assertEqual((v['previous_save_bank_preserved_bytes'],v['unused_party_bytes_preserved']),(57344,400))
        self.assertEqual(v['save_counters'],[13,14,14]);self.assertEqual(self.after,self.cold)
        self.assertFalse(v['general_sector_checksum_acceptance_claimed'])

    def test_ram_clock_advance_does_not_modify_persistent_save(self):
        v=m.save_structure(self.before,self.after,self.cold)
        self.assertNotEqual(self.a['observations'][-1]['ledger_sha256'],self.b['observations'][-1]['ledger_sha256'])
        self.assertEqual(v['cold_ram_clock_only_changed_offsets'],[8,9,10,11,0x746])
        self.assertTrue(v['all_save_rtc_preserved_after_continue'])

    def test_save_text_and_unlocked_field_are_distinct(self):
        v=m.semantic(self.a,self.b,self.parent)
        self.assertEqual(v['first_save']['lock'],1);self.assertEqual(v['progress_field']['lock'],0)
        self.assertFalse(v['progress_field']['field']);self.assertTrue(v['continued']['field'])

    def test_scope_does_not_claim_dex_or_story_acceptance(self):
        r=m.review(self.review)
        self.assertEqual((len(r['anchors']),len(r['cold_anchors'])),(87,10))
        for key in ('trainer_victories','captures','losses','escapes','party_order_changes'):
            self.assertEqual(r['claims'][key],0)
        for key in ('natural_research_arrival','regional_pokedex_integration','full_story','release_ready'):
            self.assertIs(r['claims'][key],False)

    def test_empty_image_directory_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                m.verify(self.raw,self.cold_raw,self.command,self.cold_command,self.parent,self.review,Path(t),self.folder/'continue')


def semantic_case(which,index,key,value):
    def test(self):
        a,b=copy.deepcopy(self.a),copy.deepcopy(self.b)
        (a if which=='a' else b)['observations'][index][key]=value
        with self.assertRaises(ValueError):m.semantic(a,b,self.parent)
    return test

for name,which,index,key,value in [
    ('wrong_start','a',0,'xy',[7,5]),('wrong_road','a',5,'map',[3,0]),('wrong_home','a',48,'map',[4,3]),
    ('early_battle','a',11,'battle_flags',4),('trainer_flags','a',12,'battle_flags',8),
    ('no_start_callback','a',12,'callback2',m.FIELD),('false_first_switch','a',14,'callback2',m.BATTLE),
    ('false_party_cancel','a',23,'callback2',m.PARTY),('false_second_switch','a',25,'callback2',m.BATTLE),
    ('faint_is_not_loss','a',35,'battle_outcome',2),('faint_is_not_win','a',35,'battle_outcome',1),
    ('missing_forced_ui','a',37,'callback2',m.BATTLE),('opponent_faint_not_terminal','a',41,'battle_outcome',1),
    ('xp_not_terminal','a',42,'battle_outcome',1),('missing_win','a',43,'battle_outcome',0),
    ('capture_not_win','a',43,'battle_outcome',7),('escape_not_win','a',43,'battle_outcome',4),
    ('win_must_return','a',43,'callback2',m.BATTLE),('win_must_unlock','a',43,'lock',1),
    ('fake_rp','a',43,'rp',1),('fake_capture','a',43,'party_count',3),('battle_displacement','a',30,'xy',[1,1]),
    ('fake_fainted_xp','a',43,'party_sha256',m.PARTY_AFTER),('premature_heal','a',65,'party_sha256',m.PARTY_AFTER),
    ('missing_heal','a',66,'party_sha256',m.PARTY_PHASES[-2][1]),('dex_wrong_owner','a',50,'callback2',m.FIELD),
    ('early_save_counter','a',84,'save_counter',14),('early_save_flash','a',81,'flash_sha256',m.FLASH_AFTER),
    ('completed_text_locked','a',85,'lock',0),('final_field_unlock','a',86,'lock',1),
    ('residue_not_new_field_truth','a',86,'field',True),('missing_save_flash','a',85,'flash_sha256',m.prior.FLASH_AFTER),
    ('bool_counter','a',85,'save_counter',True),('bool_lock','a',0,'lock',False),('integer_field','a',0,'field',1),
    ('cold_battle_residue','b',0,'battle_flags',4),('cold_outcome_residue','b',9,'battle_outcome',1),
    ('cold_wrong_party','b',0,'party_sha256',m.prior.PARTY_AFTER),('cold_wrong_clock','b',0,'ledger_sha256',m.LEDGER_SAVED),
    ('cold_wrong_xy','b',9,'xy',[8,4]),('cold_wrong_map','b',9,'map',[3,0]),
    ('cold_bool_frame','b',2,'frame',True),('cold_wrong_info_owner','b',3,'callback2',m.FIELD),
    ('cold_early_field','b',2,'field',True),('cold_final_lock','b',9,'lock',1)]:
    setattr(Save14Tests,'test_reject_'+name,semantic_case(which,index,key,value))


def parent_case(key,value):
    def test(self):
        parent=copy.deepcopy(self.parent);parent[key]=value
        with self.assertRaises(ValueError):m.parent_boundary(parent)
    return test
for key,value in [('status','PASS_STORY_SAVE13_PENDING_TERMINAL'),('actions_completion_confirmed',False),
                  ('retained_artifact_id',10975157558),('run_id',36435307920),('save_counter',12),
                  ('save_counter',True),('release_ready',True),('natural_research_arrival_accepted',True)]:
    setattr(Save14Tests,'test_reject_parent_'+key+'_'+str(value),parent_case(key,value))


def save_case(region,offset):
    def test(self):
        data=bytearray(self.after)
        sections=m.sections(self.after,0,14)
        base=sections[1]+0x38 if region=='party' else sections[1] if region=='section1' else sections[0] if region=='section0' else 0
        data[base+offset]^=1
        with self.assertRaises(ValueError):m.save_structure(self.before,bytes(data),bytes(data))
    return test
for name,region,offset in [('identity','party',0),('species','party',32),('bird_xp','party',36),('leap_xp','party',136),
 ('unused_party','party',200),('bird_hp','party',86),('leap_hp','party',186),('bird_pp','party',52),('leap_pp','party',152),
 ('bird_level','party',84),('stats','party',90),('status','party',80),('party_count','section1',0x34),
 ('balls','section1',0x310),('money','section1',0x290),('encryption_key','section0',0xf20),
 ('old_bank','absolute',0xe100),('section_id','absolute',0xff4),('signature','absolute',0xff8),
 ('counter','absolute',0xffc),('ledger_owner','absolute',0x1f064+100),('ledger_clock','absolute',0x1f064+0x746)]:
    setattr(Save14Tests,'test_reject_save_'+name,save_case(region,offset))


def protocol_case(key,value):
    def test(self):
        lines=[json.loads(s) for s in self.raw.decode().splitlines()]
        lines[-1][key]=value
        altered=('\n'.join(json.dumps(s,separators=(',',':')) for s in lines)+'\n').encode()
        with self.assertRaises(ValueError):m.trace(altered,self.command,m.INPUT_SAVE)
    return test
for key,value in [('warnings_errors',1),('host_write_barriers',6),('guarded_host_writes',1),('fixture_calls',1),
                  ('inputs',302),('frames',23106),('natural_research_arrival_accepted',True)]:
    setattr(Save14Tests,'test_reject_protocol_'+key,protocol_case(key,value))


def command_case(raw):
    def test(self):
        with self.assertRaises(ValueError):m.commands(raw)
    return test
for name,raw in [('write',b'write 0 1\nquit\n'),('fixture',b'fixture\nquit\n'),('multi_key',b'key 3 2\nquit\n'),
 ('large_frame',b'key 0 601\nquit\n'),('duplicate_observe',b'observe 1\nobserve 1\nquit\n'),
 ('no_quit',b'key 0 2\n'),('after_quit',b'quit\nkey 0 2\n'),('non_ascii','観測 1\nquit\n'.encode())]:
    setattr(Save14Tests,'test_reject_command_'+name,command_case(raw))


def review_case(key,value):
    def test(self):
        r=json.loads(self.review);r['claims'][key]=value
        with self.assertRaises(ValueError):m.review((json.dumps(r,ensure_ascii=False,indent=2)+'\n').encode())
    return test
for key,value in [('party_faints',0),('losses',1),('normal_battle_switches',3),('forced_replacements',0),
                  ('trainer_victories',1),('regional_pokedex_integration',True)]:
    setattr(Save14Tests,'test_reject_review_'+key,review_case(key,value))


def byte_case(which):
    def test(self):
        if which=='rtc':
            changed=self.cold[:-1]+bytes([self.cold[-1]^1])
            with self.assertRaises(ValueError):m.saved_bytes(self.before,self.after,changed)
        elif which=='image':
            screen=self.a['screens'][35];raw=(self.folder/'progress/screen-0035.ppm').read_bytes()
            with self.assertRaises(ValueError):m.screen_bytes(raw[:-1]+bytes([raw[-1]^1]),screen)
        elif which=='duplicate_json':
            with self.assertRaises(ValueError):m.load(b'{"x":1,"x":2}')
        else:
            with self.assertRaises(ValueError):m.save_structure(self.before,self.after[:-1],self.cold[:-1])
    return test
for name in ('rtc','image','duplicate_json','truncated'):
    setattr(Save14Tests,'test_reject_'+name,byte_case(name))

if __name__=='__main__':unittest.main()
