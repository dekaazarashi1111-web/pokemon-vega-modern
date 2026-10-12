"""今回追加の生成技auditだけを検証する。ROM/nativeの既存受入は実行しない。"""
from __future__ import annotations
import copy
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from pr16_candidate_wiki_inputs import Inputs,Rom,digest
from pr16_candidate_wiki_creation import predict,read_levels,overlay_rows,verify_source,declared_routes,SNAPSHOT,integer,local_proofs,c_unit

class CreationTests(unittest.TestCase):
    def rows(self, moves, levels=None):
        return [{'move_id':m,'level':l,'order':i} for i,(m,l) in enumerate(zip(moves,levels or [1]*len(moves)))]
    def block(self):
        raw=bytearray(104);raw[:6]=bytes([1,2,0,0,51,1]);struct.pack_into('<H',raw,8,1)
        raw[32]=5;raw[44]=10;raw[56]=40;raw[68]=50
        return raw
    def rom(self, rows):
        raw=struct.pack('<I',0x08000004)+b''.join(struct.pack('<HB',m,l) for m,l in rows)
        return Rom(raw)
    def test_empty(self):self.assertEqual(predict([],1)['move_ids'],[0]*4)
    def test_last_four_raw(self):self.assertEqual(predict(self.rows([1,2,3,4,5]),1)['move_ids'],[2,3,4,5])
    def test_duplicate_not_backfilled(self):self.assertEqual(predict(self.rows([1,2,3,4,4]),1)['move_ids'],[2,3,4,0])
    def test_duplicate_does_not_stop_next(self):self.assertEqual(predict(self.rows([1,1,2,3]),1)['move_ids'],[1,2,3,0])
    def test_zero_padding_preserved(self):
        r=predict(self.rows([1,2,0,3,4]),1);self.assertEqual(r['selected_raw_move_ids'],[2,0,3,4]);self.assertEqual(r['move_ids'],[2,3,4,0])
    def test_prefix_not_global_filter(self):self.assertEqual(predict(self.rows([1,2,3],[1,80,5]),10)['move_ids'],[1,0,0,0])
    def test_level_zero_is_included(self):self.assertEqual(predict(self.rows([1,2],[0,1]),1)['move_ids'],[1,2,0,0])
    def test_capacity40(self):self.assertEqual(predict(self.rows(list(range(1,41))),100)['move_ids'],[37,38,39,40])
    def test_capacity41_not_invented(self):
        r=predict(self.rows(list(range(1,42))),100);self.assertEqual(r['status'],'SOURCE_STACK_CAPACITY_EXCEEDED');self.assertNotIn('move_ids',r)
    def test_level100_valid(self):self.assertEqual(predict(self.rows([1],[100]),100)['move_ids'],[1,0,0,0])
    def test_level255_rejected(self):
        with self.assertRaises(ValueError):predict([],255)
    def test_bool_rejected(self):
        with self.assertRaises(ValueError):integer(True,0,1,'bool')
    def test_read_padding(self):
        r=read_levels(self.rom([(1,1),(0,5),(2,10),(0,255)]),0x08000000,0,1,3)
        self.assertEqual([x['move_id'] for x in r['rows']],[1,0,2]);self.assertEqual(r['rows'][2]['order'],2)
    def test_read_terminator_not_in_profile(self):self.assertEqual(read_levels(self.rom([(0,255)]),0x08000000,0,1,3)['rows'],[])
    def test_read_bad_move(self):
        with self.assertRaises(ValueError):read_levels(self.rom([(9,1),(0,255)]),0x08000000,0,1,3)
    def test_read_no_terminator(self):
        with self.assertRaises(ValueError):read_levels(self.rom([(1,1)]),0x08000000,0,1,3)
    def test_read_bad_species(self):
        with self.assertRaises(ValueError):read_levels(self.rom([(0,255)]),0x08000000,-1,1,3)
    def test_wild_threshold_not_percent(self):
        r=overlay_rows(bytes(self.block()),2)[0];self.assertEqual(r['roll_denominator'],256);self.assertEqual(r['roll_threshold_u8'],51)
    def test_wild_prepost(self):
        c=overlay_rows(bytes(self.block()),2)[0]['candidates'][0];self.assertEqual(c['pre_hall_of_fame_levels'],[5,10]);self.assertEqual(c['post_hall_of_fame_levels'],[40,50])
    def test_wild_radar_badge_bit(self):
        raw=self.block();raw[80]=0x83;c=overlay_rows(bytes(raw),2)[0]['candidates'][0];self.assertEqual(c['minimum_badges'],3);self.assertTrue(c['night_radar_badge_override'])
    def test_wild_hidden_forced(self):
        raw=self.block();raw[2]=4;raw[3]=5;self.assertTrue(overlay_rows(bytes(raw),2)[0]['forced_hidden_scan_bypasses_roll'])
    def test_wild_bad_stride(self):
        with self.assertRaises(ValueError):overlay_rows(bytes(103),2)
    def test_wild_bad_count(self):
        raw=self.block();raw[5]=13
        with self.assertRaises(ValueError):overlay_rows(bytes(raw),2)
    def test_wild_bad_range(self):
        raw=self.block();raw[44]=4
        with self.assertRaises(ValueError):overlay_rows(bytes(raw),2)
    def test_wild_invalid_species(self):
        raw=self.block();raw[8]=2
        with self.assertRaises(ValueError):overlay_rows(bytes(raw),2)
    def test_source_snapshot_valid(self):verify_source(Inputs().json(SNAPSHOT))
    def test_source_hash_tamper(self):
        d=Inputs().json(SNAPSHOT);d['sources']['src/learn_move.c']['units'][0]['text']+='x'
        with self.assertRaises(ValueError):verify_source(d)
    def test_source_rule_tamper(self):
        d=Inputs().json(SNAPSHOT);u=d['sources']['src/learn_move.c']['units'][0];u['text']=u['text'].replace('index = k - MAX_MON_MOVES;','index = 0;');u['sha256']=digest(u['text'].encode())
        with self.assertRaises(ValueError):verify_source(d)
    def test_nested_call_not_a_definition(self):
        text='static u8 f(void)\n{ return 1; }\nint g(void) { if (!f() || !h()) { return 0; } return 1; }\n'
        self.assertEqual(c_unit(text,'f')['start_line'],1)
    def test_local_source_contracts(self):self.assertEqual(len(local_proofs(Inputs())),7)
    def test_native_not_promoted(self):self.assertEqual(predict(self.rows([1]),5)['candidate_native_acceptance'],'DEFERRED_AUDIT')
    def test_deterministic(self):self.assertEqual(predict(self.rows([1,2,3]),5),predict(self.rows([1,2,3]),5))

if __name__=='__main__':unittest.main()
