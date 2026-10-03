"""Save7後継のみ。陽性前提つき破損拒否。native/旧受入試験の起動はしない。"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_safe_training as m
DEV=ROOT/m.DEV


class ContractTests(unittest.TestCase):
    def test_review_is_fixed(self):
        r=m.review((DEV/'verification.json').read_bytes())
        self.assertEqual(r['claims'],m.CLAIMS)
    def test_parent_is_terminal_save7(self):
        m.parent_boundary(m.load((ROOT/m.PARENT).read_bytes()))
    def test_commands_only_new_keys(self):
        for name in ('commands.txt','continue-commands.txt'):
            self.assertEqual(m.commands((DEV/name).read_bytes())[-1],'quit')
    def test_review_mutation(self):
        raw=(DEV/'verification.json').read_bytes();m.review(raw)
        with self.assertRaises(ValueError):m.review(raw.replace(b'"wild_victories": 3',b'"wild_victories": 4'))
    def test_parent_pending_rejected(self):
        p=m.load((ROOT/m.PARENT).read_bytes());m.parent_boundary(p);p['actions_completion_confirmed']=False
        with self.assertRaises(ValueError):m.parent_boundary(p)
    def test_parent_old_save_rejected(self):
        p=m.load((ROOT/m.PARENT).read_bytes());m.parent_boundary(p);p['save_counter']=6
        with self.assertRaises(ValueError):m.parent_boundary(p)
    def test_parent_false_victory_rejected(self):
        p=m.load((ROOT/m.PARENT).read_bytes());m.parent_boundary(p);p['trainer_victories']=1
        with self.assertRaises(ValueError):m.parent_boundary(p)


def command_test(bad):
    def test(self):
        good=(DEV/'commands.txt').read_bytes();m.commands(good)
        with self.assertRaises(ValueError):m.commands(bad(good))
    return test

for name,change in {
 'helper_save':lambda r:r.replace(b'key 128 48',b'save'),
 'fixture':lambda r:r.replace(b'key 128 48',b'fixture 1'),
 'combined_key':lambda r:r.replace(b'key 128 48',b'key 3 48'),
 'unknown_key':lambda r:r.replace(b'key 128 48',b'key 256 48'),
 'negative_frames':lambda r:r.replace(b'key 128 48',b'key 128 -1'),
 'zero_frames':lambda r:r.replace(b'key 128 48',b'key 128 0'),
 'excess_frames':lambda r:r.replace(b'key 128 48',b'key 128 601'),
 'noncanonical_number':lambda r:r.replace(b'key 128 48',b'key 128 048'),
 'observe_order':lambda r:r.replace(b'observe 1\n',b'observe 2\n'),
 'double_quit':lambda r:r+b'quit\n',
 'missing_newline':lambda r:r[:-1],
 'unicode':lambda r:b'\xff'+r,
}.items():setattr(ContractTests,'test_command_reject_'+name,command_test(change))

EVIDENCE=os.environ.get('PR16_SAFE_TRAINING_EVIDENCE')
PRIVATE=os.environ.get('PR16_SAFE_TRAINING_PRIVATE')
SCREENS=os.environ.get('PR16_SAFE_TRAINING_SCREENS')

@unittest.skipUnless(EVIDENCE and PRIVATE and SCREENS,'専用Actions/保存済み新区間原本のみ。旧nativeは実行しない')
class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        e=Path(EVIDENCE);p=Path(PRIVATE);s=Path(SCREENS)
        cls.raw=(e/'progress.stdout.txt').read_bytes();cls.cold=(e/'continue.stdout.txt').read_bytes()
        cls.command=(DEV/'commands.txt').read_bytes();cls.cold_command=(DEV/'continue-commands.txt').read_bytes()
        cls.parent=m.load((ROOT/m.PARENT).read_bytes());cls.review=(DEV/'verification.json').read_bytes()
        cls.where=s/'progress';cls.cold_where=s/'continue'
        cls.before=(p/'input.srm').read_bytes();cls.after=(p/'training.srm').read_bytes();cls.savedcold=(p/'cold.srm').read_bytes()
        cls.a=m.trace(cls.raw,cls.command,m.INPUT_SAVE);cls.b=m.trace(cls.cold,cls.cold_command,m.OUTPUT_SAVE)
    def full(self):
        return m.verify(self.raw,self.cold,self.command,self.cold_command,self.parent,self.review,self.where,self.cold_where)
    def test_complete_positive(self):
        v=self.full();self.assertEqual(v['experience'],331);self.assertEqual(v['wild_victories'],3)
        self.assertFalse(v['natural_research_arrival_accepted'])
    def test_save_bytes_positive(self):
        p=m.saved_bytes(self.before,self.after,self.savedcold)
        self.assertEqual(p['other_party_bytes_preserved'],589)
        self.assertEqual(p['previous_save_bank_preserved_bytes'],57344)
    def test_cold_full_rtc(self):
        self.assertEqual(self.after,self.savedcold)
    def test_each_ui_pair(self):
        self.full()
        for x,y in ((53,1),(54,2),(55,3),(56,4)):
            self.assertEqual((self.where/f'screen-{x:04d}.ppm').read_bytes(),(self.cold_where/f'screen-{y:04d}.ppm').read_bytes())
    def test_screen_missing_directory(self):
        self.full()
        with self.assertRaises(ValueError):m.verify(self.raw,self.cold,self.command,self.cold_command,self.parent,self.review,None,self.cold_where)
    def test_seed_size_rejected(self):
        m.trace(self.raw,self.command,m.INPUT_SAVE)
        with self.assertRaises(ValueError):m.trace(self.raw,self.command,dict(m.INPUT_SAVE,size=True))
    def test_json_duplicate_key(self):
        m.trace(self.raw,self.command,m.INPUT_SAVE)
        with self.assertRaises(ValueError):m.trace(self.raw.replace(b'{"begin":',b'{"begin":"bad","begin":',1),self.command,m.INPUT_SAVE)
    def test_nonfinite_json(self):
        m.trace(self.raw,self.command,m.INPUT_SAVE)
        with self.assertRaises(ValueError):m.trace(self.raw.replace(b'"frame":0',b'"frame":NaN',1),self.command,m.INPUT_SAVE)


def trace_test(change):
    def test(self):
        m.trace(self.raw,self.command,m.INPUT_SAVE)
        rows=[m.load(line) for line in self.raw.splitlines()];change(rows)
        raw=b'\n'.join(json.dumps(r,separators=(',',':')).encode() for r in rows)+b'\n'
        with self.assertRaises(ValueError):m.trace(raw,self.command,m.INPUT_SAVE)
    return test

def first(rows,key):return next(r for r in rows if key in r)

def obs(rows):return first(rows,'observe')

for name,change in {
 'wrong_candidate':lambda r:r[0].update(candidate_sha256='0'*64),
 'wrong_seed':lambda r:r[0].update(initial_save_sha256='0'*64),
 'missing_guard':lambda r:r[0].update(host_write_barriers=6),
 'boolean_guard':lambda r:r[0].update(host_write_barriers=True),
 'unknown_start_key':lambda r:r[0].update(extra=0),
 'missing_start_key':lambda r:r[0].pop('begin'),
 'wrong_input_index':lambda r:first(r,'input').update(input=2),
 'wrong_input_frame':lambda r:first(r,'input').update(frame=1),
 'wrong_input_key':lambda r:first(r,'input').update(key=2),
 'boolean_input':lambda r:first(r,'input').update(input=False),
 'missing_input':lambda r:r.pop(1),
 'unknown_input_key':lambda r:first(r,'input').update(extra=0),
 'nonboolean_field':lambda r:obs(r).update(field=1),
 'wrong_live_xy':lambda r:obs(r).update(live_xy=[0,0]),
 'bad_map':lambda r:obs(r).update(map=[4]),
 'negative_coordinate':lambda r:obs(r).update(xy=[-1,0]),
 'bad_lock':lambda r:obs(r).update(lock=2),
 'too_many_party':lambda r:obs(r).update(party_count=7),
 'bad_digest':lambda r:obs(r).update(party_sha256='a'),
 'wrong_observe_index':lambda r:obs(r).update(observe=3),
 'wrong_observe_frame':lambda r:obs(r).update(frame=1),
 'wrong_screen_frame':lambda r:first(r,'screen').update(frame=1),
 'wrong_screen_index':lambda r:first(r,'screen').update(screen=1),
 'boolean_screen_index':lambda r:first(r,'screen').update(screen=False),
 'screen_extra_key':lambda r:first(r,'screen').update(extra=0),
 'screen_invalid_hash':lambda r:first(r,'screen').update(sha256='0'),
 'missing_end':lambda r:r.pop(),
 'extra_end':lambda r:r.append(r[-1].copy()),
 'wrong_end_inputs':lambda r:r[-1].update(inputs=315),
 'wrong_end_frames':lambda r:r[-1].update(frames=25207),
 'native_warning':lambda r:r[-1].update(warnings_errors=1),
 'host_write':lambda r:r[-1].update(guarded_host_writes=1),
 'fixture_call':lambda r:r[-1].update(fixture_calls=1),
 'false_research_arrival':lambda r:r[-1].update(natural_research_arrival_accepted=True),
}.items():setattr(EvidenceTests,'test_trace_reject_'+name,trace_test(change))


def semantic_test(change):
    def test(self):
        m.semantic(self.a,self.b,self.parent)
        a,b=copy.deepcopy(self.a),copy.deepcopy(self.b);change(a['observations'],b['observations'])
        with self.assertRaises(ValueError):m.semantic(a,b,self.parent)
    return test

for name,change in {
 'parent_start':lambda a,b:a[0].update(xy=[8,4]),
 'earned_rp':lambda a,b:a[25].update(rp=1),
 'capture_claim':lambda a,b:a[25].update(party_count=2),
 'trainer_flags':lambda a,b:a[11].update(battle_flags=12),
 'loss':lambda a,b:a[19].update(battle_outcome=2),
 'missing_victory':lambda a,b:a[19].update(battle_outcome=0),
 'research_map':lambda a,b:a[25].update(map=[96,5]),
 'early_save':lambda a,b:a[59].update(save_counter=8),
 'early_flash':lambda a,b:a[59].update(flash_sha256=m.FLASH_AFTER),
 'incomplete_flash':lambda a,b:a[63].update(flash_sha256=m.FLASH_BEFORE),
 'counter_not_saved':lambda a,b:a[63].update(save_counter=7),
 'save_ui_unlocked':lambda a,b:a[60].update(lock=0),
 'healing_not_observed':lambda a,b:a[34].update(party_sha256=a[32]['party_sha256']),
 'postheal_party_changed':lambda a,b:a[55].update(party_sha256=m.PARTY_BEFORE),
 'cold_party_changed':lambda a,b:b[0].update(party_sha256=m.PARTY_BEFORE),
 'cold_battle_residue':lambda a,b:b[0].update(battle_flags=4),
 'cold_resave':lambda a,b:b[-1].update(save_counter=9),
 'cold_exit_locked':lambda a,b:b[-1].update(lock=1),
 'ui_wrong_callback':lambda a,b:b[3].update(callback2=1),
}.items():setattr(EvidenceTests,'test_semantic_reject_'+name,semantic_test(change))


def save_test(which,offset):
    def test(self):
        m.saved_bytes(self.before,self.after,self.savedcold)
        args=[self.before,self.after,self.savedcold];raw=bytearray(args[which]);raw[offset]^=1;args[which]=bytes(raw)
        with self.assertRaises(ValueError):m.saved_bytes(*args)
    return test

for name,which,offset in [('parent',0,0),('identity',1,0x9038),('experience',1,0x9038+36),
                          ('moves',1,0x9038+44),('hp',1,0x9038+86),('section',1,0xffc),
                          ('ledger',1,0x1f064),('cold_rtc',2,131087)]:
    setattr(EvidenceTests,'test_save_reject_'+name,save_test(which,offset))


def screen_test(mode):
    def test(self):
        raw=(self.where/'screen-0055.ppm').read_bytes();record=self.a['screens'][55]
        m.screen_bytes(raw,record)
        if mode=='truncated':raw=raw[:-1]
        elif mode=='header':raw=b'P3'+raw[2:]
        elif mode=='pixel':raw=raw[:-1]+bytes([raw[-1]^1])
        elif mode=='blank':raw=m.prior.PPM_HEADER+b'\0'*(240*160*3);record=dict(record,sha256=m.identity(raw)['sha256'])
        elif mode=='wrong_sha':record=dict(record,sha256='0'*64)
        with self.assertRaises(ValueError):m.screen_bytes(raw,record)
    return test

for name in ('truncated','header','pixel','blank','wrong_sha'):
    setattr(EvidenceTests,'test_screen_reject_'+name,screen_test(name))

if __name__=='__main__':unittest.main()
