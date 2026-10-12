"""Circus固有連勝traceの判定。合成fixtureをnative受入として記録しない。"""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest
import zlib
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('streak_native',ROOT/'scripts/pr16_streak_native.py')
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n);p=n.probe

def own(current=0,best=0,phase=0,prepared=0,settled=0,session=2):
    raw=bytearray(64)
    struct.pack_into('<IIHHIIIIIHHBBBBI',raw,0,0x31534356,0xCEACBCA9,1,64,0,3,session,prepared,settled,current,best,phase,0,0,0,123)
    struct.pack_into('<I',raw,12,zlib.crc32(raw)&0xffffffff);return bytes(raw)

def trace(wins=0,losses=1):
    battles=wins+losses;original=bytes(600);pool=b''.join(bytes([i+1])*100 for i in range(6));selected=pool[:300]+bytes(300)
    default=dict(label='',frame=1,battle=0,callback2=0x08055e75,script=0,newbs=0,outcome=0,flags=0,types=0,count=1,bp=0,
        save_counter=2,pending=0,snapshot=0,marker=0,order=[1,2,3],owner=own().hex(),party=original.hex(),factory=bytes(104).hex())
    events=[]
    def event(label,**kw):
        row=copy.deepcopy(default);row.update(label=label,frame=len(events)+1,**kw);events.append(row)
    event('fixture',owner=own(session=1).hex());event('selected',count=6,party=pool.hex(),owner=own(phase=1).hex())
    for battle in range(battles):
        armed=own(battle,battle,2,battle+1,battle).hex();outcome=2 if losses and battle==battles-1 else 1
        common=dict(battle=battle,count=3,snapshot=1,marker=1,party=selected.hex(),owner=armed)
        event('confirmation',script=p.LAUNCH[battle],**common)
        event('action',script=p.LAUNCH[battle]+43,newbs=0x02020000,types=0x04000000,**common)
        event('outcome',outcome=outcome,newbs=0x02020000,**common)
        current=battle+1 if outcome==1 else 0;best=battle+1 if outcome==1 else battle
        final=own(current,best,0 if outcome==2 or battle==2 else 1,battle+1,battle+1).hex()
        event('settled',battle=battle,owner=final)
    for label in ('returned','saved','reloaded'):event(label,battle=battles,owner=final,bp=9 if not losses else 0,save_counter=2 if label=='returned' else 3)
    result=dict(schema_version=1,status='PASS_CIRCUS_STREAK_NATIVE',case=p.CASE,candidate_sha256=p.SHA,
        wins=wins,losses=losses,battles=battles,turns=battles,switches=0,forced_identity_checks=0,
        save_counter_before=2,save_counter_after=3,manual_saves=1,fresh_cores=2,owner_bytes_verified=64,party_bytes_verified=600,
        host_write_barriers=7,total_frames=len(events),events=len(events),input_only_after_guard=True,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,warnings_errors=0)
    return result,events

def check(r,e):return p.validate(json.dumps(r).encode(),b'\n'.join(b'CIRCUS_STREAK '+json.dumps(x).encode() for x in e),0,p.CASE)

class ProbeTests(unittest.TestCase):
    def test_observed_loss_and_three_win_are_distinct(self):
        for wins,losses in ((0,1),(1,1),(2,1),(3,0)):
            r,e=trace(wins,losses);self.assertEqual(check(r,e),r)
            a=p.analyze(e,r);self.assertEqual(a['later_battle_launches_verified'],wins+losses-1)
            self.assertFalse(a['physical_admission_accepted'])
    def test_every_owner_single_bit_corruption_rejected(self):
        raw=own()
        for bit in range(512):
            changed=bytearray(raw);changed[bit//8]^=1<<(bit%8)
            with self.assertRaises(ValueError):p.owner(bytes(changed))
    def test_valid_crc_cannot_hide_bad_owner_invariants(self):
        raw=bytearray(own());raw[44]=1;raw[12:16]=bytes(4);struct.pack_into('<I',raw,12,zlib.crc32(raw)&0xffffffff)
        with self.assertRaises(ValueError):p.owner(bytes(raw))
    def test_early_loss_cannot_be_promoted_to_completion(self):
        r,e=trace();r.update(wins=3,losses=0,battles=3)
        with self.assertRaises(ValueError):check(r,e)
    def test_counters_truthiness_and_native_promotion_rejected(self):
        for key,value in (('physical_admission_accepted',True),('wins',False),('fresh_cores',1),('manual_saves',2),('warnings_errors',1)):
            r,e=trace();r[key]=value
            with self.assertRaises(ValueError):check(r,e)
    def test_party_factory_save_and_outcome_tampering_rejected(self):
        for index,key,value in ((3,'party','ff'*600),(4,'outcome',1),(5,'factory','ff'*104),(-1,'save_counter',2),(-1,'owner',own(1,1).hex())):
            r,e=trace();e[index][key]=value
            with self.assertRaises(ValueError):check(r,e)
    def test_event_order_and_duplicate_json_rejected(self):
        r,e=trace();e[3]['frame']=e[2]['frame']
        with self.assertRaises(ValueError):check(r,e)
        with self.assertRaises(ValueError):p.strict(b'{"a":1,"a":2}')

class AssemblyTests(unittest.TestCase):
    def test_policy_is_read_only_and_follows_forced_identity_fix(self):
        text=n.policy((ROOT/n.WX).read_text(),(ROOT/n.BR).read_text())
        self.assertIn('slot=wx_move_slot(c)',text);self.assertNotIn('i==active ||',text)
        for forbidden in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'setRegister(', 'wx_opening_switch'):self.assertNotIn(forbidden,text)
    def test_missing_or_duplicate_helper_boundaries_rejected(self):
        raw=(ROOT/n.WX).read_text()
        with self.assertRaises(ValueError):n.function(raw,'unknown_function')
        with self.assertRaises(ValueError):n.function(raw+raw,'wx_team')
    def test_runner_preserves_seven_guards_and_protected_inputs(self):
        raw=(ROOT/'scripts/pr16_circus_native.py').read_text();text=n.adapt(raw)
        for required in ('for guard in previous.fixed.GUARDS:','protected==','bindings==','previous.C_SOURCE_SHA','verify_recipe(recipe)'):self.assertIn(required,text)
        self.assertNotIn("recipe['entries']['circus']",text);self.assertIn("recipe['reception']['circus']",text)
        compile(text,'adapted','exec')
if __name__=='__main__':unittest.main()
