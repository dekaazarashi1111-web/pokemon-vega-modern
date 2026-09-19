"""限定traceの契約・負例。ゲーム/ROM/既存受入は起動しない。"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('identity',ROOT/'scripts/pr16_circus_identity.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def mon(pid,species):
    raw=bytearray(100);raw[:4]=pid.to_bytes(4,'little');raw[32:34]=species.to_bytes(2,'little')
    return dict(personality=pid,species=species,bytes=raw.hex())

def events():
    party=[mon(i+1,i+90) for i in range(6)]
    row=dict(label='fixture',frame=1,script=1,callback2=2,newbs=0,flags=0,pc=3,lr=4,count=6,marker=2,snapshot=1,pending=0,battle_species=90,battle_index=0,order=[1,2,3],party=party)
    rows=[row]
    for label,frame,count in [('first-confirm',2,6),('circus-second-confirm',3,3),('transition',4,3),('circus-action',5,3)]:
        r=copy.deepcopy(row);r.update(label=label,frame=frame,count=count)
        if frame>=4:r['party'][0]=mon(99,137);r.update(battle_species=137,newbs=0x02001000)
        rows.append(r)
    return rows

def encode(rows):return b'\n'.join(m.PREFIX+json.dumps(r).encode() for r in rows)+b'\n'

class IdentityTests(unittest.TestCase):
    def test_replacement_localized(self):
        result=m.analyze(m.parse_events(encode(events())))
        self.assertEqual(result['classification'],'CIRCUS_RENTALS_REPLACED_AT_BATTLE_INIT')
        self.assertEqual(result['first_changed_event']['frame'],4)
        self.assertTrue(result['selected_to_second_all_300_bytes_equal'])
        self.assertFalse(result['second_to_action_identity_equal'])
    def test_same_species_different_pid_is_not_same_individual(self):
        rows=events()
        for r in rows[3:]:r['party'][0]=mon(99,90);r['battle_species']=90
        self.assertFalse(m.analyze(m.parse_events(encode(rows)))['second_to_action_identity_equal'])
    def test_retained(self):
        rows=events()
        for r in rows[3:]:r['party']=copy.deepcopy(rows[2]['party']);r['battle_species']=90
        self.assertTrue(m.analyze(m.parse_events(encode(rows)))['second_to_action_identity_equal'])
    def test_preparation_change_is_distinct(self):
        rows=events();rows[2]['party'][0]=mon(80,77)
        self.assertEqual(m.analyze(m.parse_events(encode(rows)))['classification'],'CIRCUS_RENTALS_CHANGED_BEFORE_SECOND_CHOOSER')
    def test_no_full_acceptance(self):
        result=m.analyze(m.parse_events(encode(events())))
        for k in ('physical_admission_accepted','suppression_accepted','release_ready','first_turn_replayed'):self.assertIs(result[k],False)
    def test_raw_pid_mismatch(self):
        rows=events();rows[0]['party'][0]['personality']=8
        with self.assertRaises(ValueError):m.parse_events(encode(rows))
    def test_raw_species_mismatch(self):
        rows=events();rows[0]['party'][0]['species']=8
        with self.assertRaises(ValueError):m.parse_events(encode(rows))
    def test_short_raw(self):
        rows=events();rows[0]['party'][0]['bytes']='00'
        with self.assertRaises(ValueError):m.parse_events(encode(rows))
    def test_boolean_count(self):
        rows=events();rows[0]['count']=True
        with self.assertRaises(ValueError):m.parse_events(encode(rows))
    def test_duplicate_json(self):
        with self.assertRaises(ValueError):m.strict(b'{"a":1,"a":2}')
    def test_nonfinite(self):
        with self.assertRaises(ValueError):m.strict(b'{"a":NaN}')
    def test_missing_stage(self):
        rows=events();rows[1]['label']='other'
        with self.assertRaises(ValueError):m.analyze(m.parse_events(encode(rows)))
    def test_duplicate_stage(self):
        rows=events();rows[3]['label']='circus-second-confirm'
        with self.assertRaises(ValueError):m.analyze(m.parse_events(encode(rows)))
    def test_battle_species_mismatch(self):
        rows=events();rows[-1]['battle_species']=8
        with self.assertRaises(ValueError):m.analyze(m.parse_events(encode(rows)))
    def test_warning_rejected(self):
        with self.assertRaises(ValueError):m.parse_events(encode(events())+b'mGBA[warning]')
    def test_event_order(self):
        rows=events();rows[2]['frame']=10
        with self.assertRaises(ValueError):m.parse_events(encode(rows))
    def test_instrument_is_bounded_and_read_only(self):
        text=(ROOT/'tools/mgba_pr16_circus_native.c').read_text();new=m.instrument(text)
        self.assertIn('ci_snapshot(c,"first-confirm")',new)
        self.assertNotIn('bp_progress(c)',new)
        self.assertNotIn('ct.turn=turn.returned',new)
        for forbidden in ('write8(', 'write16(', 'write32(', 'writeRegister(', 'call_preserving(', 'run_key_frames('):self.assertNotIn(forbidden,m.C)
        self.assertEqual(new.count('ci_tick(c);'),2)
    def test_changed_anchor_rejected(self):
        with self.assertRaises(ValueError):m.instrument('not the accepted controller')
    def test_failed_process(self):
        with self.assertRaises(ValueError):m.validate(b'{}',encode(events()),1,m.CASE)
    def test_success_contract(self):
        raw=dict(schema_version=1,status='PASS_CIRCUS_IDENTITY_OBSERVATION',case=m.CASE,candidate_sha256=m.SHA,fresh_cores=1,frames=5,first_turn_replayed=False,physical_admission_accepted=False,release_ready=False)
        self.assertEqual(m.validate(json.dumps(raw).encode(),encode(events()),0,m.CASE),raw)
        raw['first_turn_replayed']=True
        with self.assertRaises(ValueError):m.validate(json.dumps(raw).encode(),encode(events()),0,m.CASE)

if __name__=='__main__':unittest.main()
