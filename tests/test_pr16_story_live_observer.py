"""読取専用live adapterの陽性条件付き拒否テスト。native連戦の代用ではない。"""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_live_observer as m
from pr16_story_milestones import DiagnosticStop

def pair():
    data={k:bytearray(n) for k,n in m.SIZES.items()}
    for i in range(4):
        p=data['party'];at=i*100
        struct.pack_into('<HHI',p,at+32,850+i,0,1250000)
        struct.pack_into('<4H',p,at+44,337,89,280,332)
        p[at+52:at+56]=bytes([3,9,8,2]);p[at+84]=100
        struct.pack_into('<HH',p,at+86,277,294)
    row={k:v.hex() for k,v in data.items()}
    row.update({k:0 for k in m.SCALARS});row.update(live=4,frame=2000,schema=1,
        save1_pointer=0x02025000,save2_pointer=0x02029000)
    obs=dict(observe=4,frame=2000,map=[3,24],xy=[44,13],callback2=m.FIELD,
             lock=0,party_count=4,save_counter=101,flash_sha256='a'*64,
             ledger_sha256=m.sha(data['ledger']),party_sha256=m.sha(data['party']),
             rp=0,battle_flags=4,battle_outcome=0)
    return row,obs

def parsed():
    return m.parse(*pair())

def ending():
    before=parsed();before['observation']['callback2']=m.BATTLE;after=deepcopy(before)
    after['observation'].update(callback2=m.FIELD,observe=5,frame=2500)
    p=bytearray(after['party']);p[52]-=1;struct.pack_into('<H',p,86,270)
    after['party']=bytes(p);after['party_mons'][0]=m.mon(after['party'][:100])
    after['observation']['party_sha256']=m.sha(after['party'])
    after['observation']['battle_outcome']=1
    return before,after

EMPTY=dict(flags=[],expanded_flags=[],variables=[],expanded_vars=[])

class LiveTests(unittest.TestCase):
    def test_actual_resources(self):
        p=parsed();self.assertEqual(m.resources(p),dict(hp=277,pp=[3,9,8,2]))
        self.assertEqual(p['party_mons'][0]['moves'],[337,89,280,332])
    def test_pair_and_hash(self):
        a,b=pair();self.assertEqual(m.parse(a,b)['observation'],b)
    def test_empty_story_effects(self):
        p=parsed();self.assertEqual(m.story_effects(p,p),EMPTY)
    def test_bit_exact_story_diff(self):
        a=parsed();b=deepcopy(a);b['flags']=b'\x08'+b['flags'][1:]
        self.assertEqual(m.story_effects(a,b)['flags'],[[3,0,1]])
    def test_expanded_flag_ids(self):
        a=parsed();b=deepcopy(a);b['expanded_flags']=b'\x01'+b['expanded_flags'][1:]
        self.assertEqual(m.story_effects(a,b)['expanded_flags'],[[2304,0,1]])
    def test_postbattle_actual_hp_pp(self):
        x,y=ending();r=m.field_evidence(x,y,'route506_land',EMPTY)
        self.assertEqual(r['resources'],dict(hp=270,pp=[2,9,8,2]));self.assertFalse(r['save_requested'])
        self.assertEqual(r['party_byte_deltas'],[[52,3,2],[86,21,14]])
    def test_two_battles_not_two_saves(self):
        a,b=ending();c=deepcopy(b);p=bytearray(c['party']);p[53]-=1;c['party']=bytes(p);c['party_mons'][0]=m.mon(c['party'][:100])
        first=m.field_evidence(a,b,'route506_land',EMPTY);b['observation'].update(callback2=m.BATTLE,battle_outcome=0);c['observation'].update(observe=6,frame=3000);second=m.field_evidence(b,c,'route506_land',EMPTY)
        self.assertEqual(second['resources']['pp'],[2,8,8,2]);self.assertFalse(first['save_requested'] or second['save_requested'])
    def test_action_ui(self):
        p=parsed();p['observation'].update(callback2=m.BATTLE)
        p['ui'].update(battle_main=0x08013861,controller=0x0802DC15,execution=1,command=0x12,action_cursor=0)
        self.assertEqual(m.battle_ui(p),('action',0))
    def test_move_ui(self):
        p=parsed();p['observation'].update(callback2=m.BATTLE)
        p['ui'].update(battle_main=0x08013861,controller=0x09118B85,execution=1,command=0x14,move_cursor=2)
        self.assertEqual(m.battle_ui(p),('moves',2))
    def test_source_read_only(self):
        s=(m.ROOT/'tools/mgba_pr16_story_live_observer.h').read_text();self.assertEqual(len(m.observer_source_check(s)),64)
    def test_unknown_source_call(self):
        s=(m.ROOT/'tools/mgba_pr16_story_live_observer.h').read_text()
        with self.assertRaises(DiagnosticStop):m.observer_source_check(s+'\nwrite8(c,0,0);')


def bad_pair(name, edit):
    def test(self):
        row,obs=pair();m.parse(row,obs);edit(row,obs)
        with self.assertRaises(DiagnosticStop):m.parse(row,obs)
    setattr(LiveTests,'test_reject_'+name,test)

for name,edit in {
    'extra_key':lambda r,o:r.update(extra=0),
    'missing_party':lambda r,o:r.pop('party'),
    'bool_integer':lambda r,o:r.update(frame=True),
    'wrong_observation':lambda r,o:r.update(live=5),
    'wrong_frame':lambda r,o:r.update(frame=2001),
    'wrong_schema':lambda r,o:r.update(schema=2),
    'ram_pointer_low':lambda r,o:r.update(save1_pointer=0x08000000),
    'ram_pointer_overflow':lambda r,o:r.update(save2_pointer=0x0203ffff),
    'short_party':lambda r,o:r.update(party=r['party'][:-2]),
    'bad_hex':lambda r,o:r.update(party='g'+r['party'][1:]),
    'uppercase_hex':lambda r,o:r.update(party=r['party'].upper()),
    'party_hash':lambda r,o:o.update(party_sha256='0'*64),
    'ledger_hash':lambda r,o:o.update(ledger_sha256='0'*64),
    'zero_party':lambda r,o:o.update(party_count=0),
    'bool_party':lambda r,o:o.update(party_count=True),
    'enemy_overflow':lambda r,o:r.update(enemy_count=7),
}.items():bad_pair(name,edit)

def bad_effect(name, edit):
    def test(self):
        a,b=ending();m.field_evidence(a,b,'route506_land',EMPTY);edit(a,b)
        with self.assertRaises(DiagnosticStop):m.field_evidence(a,b,'route506_land',EMPTY)
    setattr(LiveTests,'test_reject_effect_'+name,test)
for name,edit in {
    'nonvictory':lambda a,b:b['observation'].update(battle_outcome=2),
    'trainer':lambda a,b:b['observation'].update(battle_flags=12),
    'same_observation':lambda a,b:b['observation'].update(observe=4),
    'same_frame':lambda a,b:b['observation'].update(frame=2000),
    'warp':lambda a,b:b['observation'].update(map=[3,37]),
    'wrong_position':lambda a,b:b['observation'].update(xy=[45,13]),
    'lock':lambda a,b:b['observation'].update(lock=1),
    'callback':lambda a,b:b['observation'].update(callback2=1),
    'save':lambda a,b:b['observation'].update(save_counter=102),
    'flash':lambda a,b:b['observation'].update(flash_sha256='0'*64),
    'rp':lambda a,b:b['observation'].update(rp=1),
    'flag':lambda a,b:b.update(flags=b'\x01'+b['flags'][1:]),
    'var':lambda a,b:b['variables'].__setitem__(0x72,10),
    'bag':lambda a,b:b.update(save1=b['save1'][:0x290]+b'\x01'+b['save1'][0x291:]),
    'ledger':lambda a,b:b.update(ledger=b'\x01'+b['ledger'][1:]),
    'identity':lambda a,b:b.update(party=b'\x01'+b['party'][1:]),
    'dead':lambda a,b:b['party_mons'][0].update(hp=0),
    'status':lambda a,b:b['party_mons'][0].update(status=1),
    'heal':lambda a,b:b['party_mons'][0].update(hp=294),
    'pp_increase':lambda a,b:b['party_mons'][0].update(pp=[4,9,8,2]),
    'no_pp':lambda a,b:b['party_mons'][0].update(pp=[0,0,0,0]),
    'no_consumption':lambda a,b:b['party_mons'][0].update(pp=[3,9,8,2]),
}.items():bad_effect(name,edit)

if __name__=='__main__':unittest.main()
