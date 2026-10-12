"""Save8→9の新原本だけを検査。旧native/旧受入試験は起動しない。"""
from __future__ import annotations
import copy
import os
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save9 as m
DEV=ROOT/m.DEV


class ContractTests(unittest.TestCase):
    def test_save8_parent_terminal(self):
        m.parent_boundary(m.load((ROOT/m.PARENT).read_bytes()))
    def test_new_review_claims_and_new_input_only(self):
        r=m.review((DEV/'verification.json').read_bytes())
        self.assertEqual(r['claims'],m.CLAIMS)
        self.assertEqual(len(r['anchors']),30)
        for name in ('commands.txt','continue-commands.txt'):
            raw=(DEV/name).read_bytes()
            self.assertEqual(m.commands(raw)[-1],'quit')
            self.assertEqual(m.identity(raw),r['files'][name])
    def test_changed_review_not_accepted(self):
        raw=(DEV/'verification.json').read_bytes();m.review(raw)
        with self.assertRaises(ValueError):
            m.review(raw.replace(b'"wild_escapes": 2',b'"wild_escapes": 0'))
    def test_old_commands_not_accepted_as_new(self):
        r=m.review((DEV/'verification.json').read_bytes())
        old=ROOT/'content/modernization/pr16_story_safe_training_development/commands.txt'
        self.assertNotEqual(m.identity(old.read_bytes()),r['files']['commands.txt'])


def parent_test(key,value):
    def test(self):
        p=m.load((ROOT/m.PARENT).read_bytes());m.parent_boundary(p)
        p[key]=value
        with self.assertRaises(ValueError):m.parent_boundary(p)
    return test

for key,value in dict(actions_completion_confirmed=False,run_id=36370422350,
    retained_artifact_id=10948853813,output_save=m.OUTPUT_SAVE,save_counter=7,
    experience=270,trainer_victories=1,natural_research_arrival_accepted=True,release_ready=True).items():
    setattr(ContractTests,'test_reject_parent_'+key,parent_test(key,value))

E=os.environ.get('PR16_SAVE9_EVIDENCE')
P=os.environ.get('PR16_SAVE9_PRIVATE')
S=os.environ.get('PR16_SAVE9_SCREENS')

@unittest.skipUnless(E and P and S,'専用新区間の原本のみ。入力再生なし。')
class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        e,p,s=Path(E),Path(P),Path(S)
        cls.raw=(e/'progress.stdout.txt').read_bytes();cls.cold=(e/'continue.stdout.txt').read_bytes()
        cls.command=(DEV/'commands.txt').read_bytes();cls.ccommand=(DEV/'continue-commands.txt').read_bytes()
        cls.parent=m.load((ROOT/m.PARENT).read_bytes());cls.review=(DEV/'verification.json').read_bytes()
        cls.where=s/'progress';cls.cwhere=s/'continue'
        cls.before=(p/'input.srm').read_bytes();cls.after=(p/'training.srm').read_bytes();cls.savedcold=(p/'cold.srm').read_bytes()
        cls.a=m.trace(cls.raw,cls.command,m.INPUT_SAVE);cls.b=m.trace(cls.cold,cls.ccommand,m.OUTPUT_SAVE)
    def full(self):
        return m.verify(self.raw,self.cold,self.command,self.ccommand,self.parent,self.review,self.where,self.cwhere)
    def test_all_new_evidence(self):
        r=self.full()
        self.assertEqual((r['experience'],r['level'],r['wild_victories'],r['wild_escapes']),(450,9,3,2))
        self.assertFalse(r['natural_research_arrival_accepted'])
        self.assertFalse(r['release_ready'])
    def test_save9_structural_proof(self):
        r=m.saved_bytes(self.before,self.after,self.savedcold)
        self.assertEqual((r['before_party_offset'],r['after_party_offset']),(0x9038,0x18038))
        self.assertEqual(r['other_party_bytes_preserved'],589)
        self.assertEqual(r['previous_save_bank_preserved_bytes'],57344)
    def test_ui_pairs_complete(self):
        self.full()
        for a,b in m.PAIRS:
            self.assertEqual((self.where/f'screen-{a:04d}.ppm').read_bytes(),
                             (self.cwhere/f'screen-{b:04d}.ppm').read_bytes())
    def test_flee_not_victory_or_experience(self):
        m.semantic(self.a,self.b,self.parent)
        a=self.a['observations']
        for before,escape,after in ((24,27,28),(47,49,50)):
            self.assertEqual(a[escape]['battle_outcome'],4)
            self.assertEqual(a[before]['party_sha256'],a[after]['party_sha256'])
    def test_counter_ahead_of_completed_flash(self):
        m.semantic(self.a,self.b,self.parent)
        a=self.a['observations']
        self.assertEqual(a[65]['save_counter'],9)
        self.assertNotEqual(a[65]['flash_sha256'],m.FLASH_AFTER)
        self.assertEqual(a[66]['flash_sha256'],m.FLASH_AFTER)
    def test_preserve_stale_telemetry_and_fresh_continue(self):
        m.semantic(self.a,self.b,self.parent)
        a,b=self.a['observations'][-1],self.b['observations'][0]
        self.assertFalse(a['field']);self.assertEqual(a['battle_outcome'],4)
        self.assertTrue(b['field']);self.assertEqual(b['battle_outcome'],0)
        self.assertEqual(a['party_sha256'],b['party_sha256'])
    def test_missing_screen_directory(self):
        self.full()
        with self.assertRaises(ValueError):
            m.verify(self.raw,self.cold,self.command,self.ccommand,self.parent,self.review,None,self.cwhere)
    def test_new_progress_cannot_boot_old_seed(self):
        m.trace(self.raw,self.command,m.INPUT_SAVE)
        with self.assertRaises(ValueError):m.trace(self.raw,self.command,m.prior.INPUT_SAVE)
    def test_new_cold_cannot_boot_parent_seed(self):
        m.trace(self.cold,self.ccommand,m.OUTPUT_SAVE)
        with self.assertRaises(ValueError):m.trace(self.cold,self.ccommand,m.INPUT_SAVE)


def semantic_test(change):
    def test(self):
        m.semantic(self.a,self.b,self.parent)
        a,b=copy.deepcopy(self.a),copy.deepcopy(self.b)
        change(a,b)
        with self.assertRaises(ValueError):m.semantic(a,b,self.parent)
    return test

def patch(index,**values):
    return lambda a,b:a['observations'][index].update(values)

for name,change in {
    'old_interval_input_count':lambda a,b:a['end'].update(inputs=316),
    'old_interval_frames':lambda a,b:a['end'].update(frames=25208),
    'truncated_new_interval':lambda a,b:a['observations'].pop(),
    'parent_xy':patch(0,xy=[8,4]),
    'initial_field':patch(0,field=False),
    'extra_rp':patch(47,rp=1),
    'false_capture':patch(49,party_count=2),
    'false_research_map':patch(50,map=[96,5]),
    'trainer_battle':patch(7,battle_flags=12),
    'loss_as_progress':patch(24,battle_outcome=2),
    'missing_encounter':patch(26,lock=0),
    'victory_not_returned':patch(16,lock=1),
    'first_flee_as_victory':patch(27,battle_outcome=1),
    'second_flee_as_victory':patch(49,battle_outcome=1),
    'flee_not_returned':patch(28,lock=1),
    'flee_extra_growth':patch(27,party_sha256=m.PARTY_AFTER),
    'second_flee_extra_growth':patch(49,party_sha256=m.PARTY_AFTER),
    'first_heal_missing':lambda a,b:a['observations'][35].update(party_sha256=a['observations'][34]['party_sha256']),
    'second_heal_missing':lambda a,b:a['observations'][51].update(party_sha256=m.PARTY_AFTER),
    'early_save':patch(59,save_counter=9),
    'early_flash':patch(60,flash_sha256=m.FLASH_AFTER),
    'save_counter_too_early':patch(64,save_counter=9),
    'counter_alone_is_not_success':patch(65,flash_sha256=m.FLASH_AFTER),
    'save_ui_unlocked':patch(66,lock=0),
    'save_ui_callback':patch(59,callback2=0),
    'incomplete_save':patch(66,flash_sha256=m.FLASH_BEFORE),
    'not_returned_after_save':patch(67,lock=1),
    'stale_flags_rewritten':patch(67,battle_flags=0),
    'stale_field_rewritten':patch(67,field=True),
    'cold_party_changed':lambda a,b:b['observations'][0].update(party_sha256=m.PARTY_BEFORE),
    'cold_old_position':lambda a,b:b['observations'][0].update(xy=[8,3]),
    'cold_battle_residue':lambda a,b:b['observations'][0].update(battle_outcome=4),
    'cold_resave':lambda a,b:b['observations'][5].update(save_counter=10),
    'cold_exit_locked':lambda a,b:b['observations'][5].update(lock=1),
    'cold_summary_callback':lambda a,b:b['observations'][3].update(callback2=1),
}.items():setattr(EvidenceTests,'test_new_boundary_reject_'+name,semantic_test(change))


def save_test(which,offset):
    def test(self):
        m.save_structure(self.before,self.after,self.savedcold)
        x,y=bytearray(self.before),bytearray(self.after)
        raw=x if which=='before' else y;raw[offset]^=1
        with self.assertRaises(ValueError):
            m.save_structure(bytes(x),bytes(y),bytes(y))
    return test

for name,which,offset in [
    ('old_bank','after',100),
    ('new_section_id','after',0xe000+0xff4),
    ('new_section_signature','after',0x18000+0xff8),
    ('new_section_counter','after',0x18000+0xffc),
    ('old_section_counter','before',0x9000+0xffc),
    ('party_count','after',0x18034),
    ('party_identity','after',0x18038),
    ('party_experience','after',0x18038+36),
    ('party_move','after',0x18038+44),
    ('party_pp','after',0x18038+52),
    ('party_level','after',0x18038+84),
    ('party_hp','after',0x18038+86),
    ('empty_party','after',0x18038+100),
    ('ledger_signature','after',0x1f064),
    ('ledger_checksum','after',0x1f064+8),
    ('ledger_time','after',0x1f064+0x746),
    ('ledger_other_owner','after',0x1f064+100),
]:setattr(EvidenceTests,'test_new_save_reject_'+name,save_test(which,offset))

# 独立ContinueのRTC末尾と、構造検査外のbyteにも全体identityが掛かることを確認する。
def rtc_test(self):
    m.saved_bytes(self.before,self.after,self.savedcold)
    bad=self.savedcold[:-1]+bytes([self.savedcold[-1]^1])
    with self.assertRaises(ValueError):m.saved_bytes(self.before,self.after,bad)
def whole_identity_test(self):
    m.saved_bytes(self.before,self.after,self.savedcold)
    bad=bytearray(self.after);bad[0x1e100]^=1;bad=bytes(bad)
    m.save_structure(self.before,bad,bad)
    with self.assertRaises(ValueError):m.saved_bytes(self.before,bad,bad)
setattr(EvidenceTests,'test_continue_rtc_tail',rtc_test)
setattr(EvidenceTests,'test_whole_identity_outside_structural_fields',whole_identity_test)
