"""Portable negative tests: synthetic observations only, no native replay or save fixture."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_fast_maori as m
from pr16_story_safe_training import BOOT


def sample(cold=False):
    count=4 if cold else 44
    rows=[]
    for i in range(count):
        if cold:
            flags,outcome=0,0; callback=m.FIELD; lock=int(i in (1,2)); field=i in (0,3)
            map_id=[3,19]; counter=16; party=m.PARTY[-1][1]; flash=m.FLASH[2]; facing=2 if i==0 else 4
        else:
            flags,outcome=(0,0) if i<9 else (4,0) if i<13 else (4,4) if i<18 else (12,0) if i<33 else (12,1)
            callback=m.BATTLE if 9<=i<=13 or 18<=i<=35 else m.FIELD
            lock=int(9<=i<=14 or 17<=i<=35 or 37<=i<=41); field=i<9
            map_id=[4,0] if i==0 else [3,0] if i<5 else [3,19];counter=15 if i<42 else 16
            party=next(v for n,v in reversed(m.PARTY) if i>=n);flash=m.FLASH[0 if i<41 else 1 if i==41 else 2]; facing=2
        rows.append(dict(observe=i,frame=i*100,map=map_id,xy=[53,10],live_xy=[60,17],facing=facing,
            field=field,lock=lock,callback2=callback,party_count=4,save_counter=counter,rp=0,
            battle_flags=flags,battle_outcome=outcome,party_sha256=party,flash_sha256=flash,ledger_sha256='0'*64))
    return dict(observations=rows,end=dict(end='STORY_INPUT_CHECKPOINT',frames=1848 if cold else 15106,
        inputs=20 if cold else 176,warnings_errors=0,host_write_barriers=7,guarded_host_writes=0,
        fixture_calls=0,natural_research_arrival_accepted=False))


def wire(cold=False):
    parsed=sample(cold);seed=m.OUTPUT_SAVE if cold else m.INPUT_SAVE
    name='continue-commands.txt' if cold else 'commands.txt';command=(ROOT/m.DEV/name).read_bytes()
    rows=[dict(begin='INDEPENDENT_CONTINUE',candidate_sha256=m.CANDIDATE['sha256'],
               initial_save_sha256=seed['sha256'],host_write_barriers=7)]
    frames=0;inputs=0
    def key(k,n):
        nonlocal frames,inputs
        rows.append(dict(input=inputs,frame=frames,key=k,frames=n));frames+=n;inputs+=1
    def observe(n):
        o=deepcopy(parsed['observations'][n]);o['frame']=frames;rows.append(o)
        rows.append(dict(screen=n,frame=frames,sha256='1'*64))
    for k,n in BOOT:key(k,n)
    observe(0)
    for line in command.decode().splitlines()[:-1]:
        p=line.split()
        if p[0]=='key':key(int(p[1]),int(p[2]))
        else:observe(int(p[1]))
    end=parsed['end'];end.update(frames=frames,inputs=inputs);rows.append(end)
    return rows,command,seed


class MaoriTests(unittest.TestCase):
    def test_semantic_positive_and_claim_limits(self):
        result=m.semantic(sample(),sample(True))
        self.assertEqual((result['trainer_victories'],result['wild_victories'],result['escapes']),(1,0,1))
        self.assertFalse(result['save_success_text_frame_captured'])
        for key in ('natural_growth_accepted','natural_difficulty_accepted','full_story_accepted','release_ready','evolution_accepted'):
            self.assertFalse(result[key])
    def test_wire_positive_both_lanes(self):
        for cold in (False,True):
            rows,command,seed=wire(cold)
            result=m.trace(('\n'.join(json.dumps(r) for r in rows)+'\n').encode(),command,seed)
            self.assertEqual(len(result['observations']),4 if cold else 44)
    def test_commands_forbid_host_and_save_helpers(self):
        for command in (b'fixture 1\nquit\n',b'save 1\nquit\n',b'key 3 2\nquit\n',b'quit\nquit\n'):
            with self.subTest(command=command),self.assertRaises(ValueError):m.prior.commands(command)
    def test_ledger_complete_roundtrip_and_empty_diff(self):
        a=bytes(range(100));b=bytearray(a);b[0:3]=b'abc';b[50]=7;b[-1]=8
        value=m.byte_ledger(a,bytes(b));self.assertEqual(value['changed_bytes'],5)
        c=bytearray(a)
        for row in value['ranges']:c[row['offset']:row['offset']+row['size']]=bytes.fromhex(row['after'])
        self.assertEqual(c,b);self.assertEqual(m.byte_ledger(a,a)['ranges'],[])
    def test_ledger_rejects_bad_size_and_type(self):
        for x,y in [(b'a',b''),(bytearray(b'a'),b'a')]:
            with self.subTest(x=x),self.assertRaises(ValueError):m.byte_ledger(x,y)
    def test_structure_rejects_length_type_and_cold_change(self):
        for x,y,z in [(b'',b'',b''),(bytes(131088),bytes(131088),bytes(131087)+b'x'),
                      (bytearray(131088),bytes(131088),bytes(131088))]:
            with self.subTest(length=len(x)),self.assertRaises(ValueError):m.save_structure(x,y,z)
    def test_sector_missing_duplicate_signature_counter(self):
        raw=bytearray(0xe000)
        for n in range(14):struct.pack_into('<HHII',raw,n*4096+0xff4,n,0,0x08012025,16)
        self.assertEqual(len(m.sections(bytes(raw),0,16)),14)
        for offset,value in [(0xff4,1),(0xff8,0),(0xffc,15)]:
            with self.subTest(offset=offset):
                changed=bytearray(raw);struct.pack_into('<I',changed,offset,value)
                with self.assertRaises(ValueError):m.sections(bytes(changed),0,16)
    def test_parent_confirmed_not_evolution(self):
        p=dict(run_id=36500700863,actions_completion_confirmed=True,actions_conclusion='success',claims=dict(evolution_accepted=False))
        m.parent_boundary(p)
        for key,value in [('run_id',1),('actions_completion_confirmed',False),('actions_conclusion','failure'),('claims',{'evolution_accepted':True})]:
            changed=deepcopy(p);changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.parent_boundary(changed)
    def test_other_rom_rejected(self):
        with self.assertRaises(ValueError):m.rom_owner(b'not a candidate')


# Every targeted mutation is a separately reported test, not an emulator run.
MUTATIONS={
 'escape_not_win':(False,13,'battle_outcome',1),
 'escape_tail_locked':(False,14,'lock',0),
 'escape_field_required':(False,15,'callback2',m.BATTLE),
 'trainer_not_wild':(False,18,'battle_flags',4),
 'faint_first_not_win':(False,22,'battle_outcome',1),
 'faint_second_not_win':(False,27,'battle_outcome',1),
 'faint_final_not_win':(False,32,'battle_outcome',1),
 'defeat_not_victory':(False,33,'battle_outcome',2),
 'field_required':(False,36,'callback2',m.BATTLE),
 'unlocked_field_required':(False,36,'lock',1),
 'residue_not_new_battle':(False,37,'battle_outcome',0),
 'wire_flag_not_rewritten':(False,36,'field',True),
 'writing_not_saved':(False,41,'save_counter',16),
 'incomplete_flash':(False,42,'flash_sha256',m.FLASH[1]),
 'early_flash':(False,40,'flash_sha256',m.FLASH[2]),
 'counter_bool':(False,0,'save_counter',True),
 'rp_injection':(False,25,'rp',10),
 'party_injection':(False,18,'party_count',6),
 'pp_replenishment':(False,31,'party_sha256',m.PARTY[1][1]),
 'wrong_map':(False,16,'map',[4,0]),
 'wrong_trainer_position':(False,18,'xy',[54,10]),
 'cold_rematch':(True,1,'battle_flags',12),
 'cold_save_corruption':(True,0,'flash_sha256',m.FLASH[0]),
 'cold_party_corruption':(True,0,'party_sha256',m.PARTY[0][1]),
 'cold_ledger_corruption':(True,0,'ledger_sha256','f'*64),
 'cold_wrong_direction':(True,1,'facing',2),
 'cold_dialogue_tail':(True,3,'lock',1),
}
for name,(cold,index,key,value) in MUTATIONS.items():
    def reject(self,cold=cold,index=index,key=key,value=value):
        a,b=sample(),sample(True);(b if cold else a)['observations'][index][key]=value
        with self.assertRaises(ValueError):m.semantic(a,b)
    setattr(MaoriTests,'test_reject_'+name,reject)

WIRE_MUTATIONS={
 'fixture_calls':(-1,'fixture_calls',1),'host_write':(-1,'guarded_host_writes',1),
 'warning':(-1,'warnings_errors',1),'no_barrier':(0,'host_write_barriers',6),
 'foreign_rom':(0,'candidate_sha256','f'*64),'foreign_save':(0,'initial_save_sha256','f'*64),
 'input_frame':(2,'frame',0),'input_bool':(1,'key',False),
}
for name,(index,key,value) in WIRE_MUTATIONS.items():
    def reject_wire(self,index=index,key=key,value=value):
        rows,command,seed=wire();rows[index][key]=value
        with self.assertRaises(ValueError):m.trace(('\n'.join(json.dumps(r) for r in rows)+'\n').encode(),command,seed)
    setattr(MaoriTests,'test_wire_reject_'+name,reject_wire)

if __name__=='__main__':unittest.main()
