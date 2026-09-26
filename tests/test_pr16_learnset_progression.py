"""Issue19 progression専用の原本境界・実測schema・非再実行試験。"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_learnset_progression as p


def samples():
    return p.vectors({mid:20 for mid in range(1063)})


def native(v):
    r=p.expected(v)
    r['witness']={'party':1,'dialog':30 if v['dialogs'] else 0,'summary':60 if v['selections'] else 0,
      'selection':90 if v['selections'] else 0,'stop':120 if v['stops'] else 0,
      'begin':300 if v['evolution'] else 0,'update':301 if v['evolution'] else 0,
      'field':2000,'dialogs':v['dialogs'],'selections':v['selections'],'stops':v['stops']}
    err='original core destroyed; new core normal Continue\n'
    for stage in range(4):
        for at in range(4):
            pre=stage==0;sid=v['species'] if pre else v['target'];lv=v['level']+int(not pre)
            mid=(v['known'] if pre else v['after'])[at];pp=(v['pp'] if pre else v['after_pp'])[at]
            err+=f'PROGRESSION observed species={sid} level={lv} slot={at} move={mid} expected={mid} pp={pp} expected_pp={pp}\n'
    return r,err.encode()


class ProgressionTests(unittest.TestCase):
    def test_level_span_valid(self):
        raw=b''.join(struct.pack('<HB',*x) for x in [(77,12),(78,12)])+b'\0\0\xff'
        self.assertEqual(p.decode_span(raw,'level_up'),[(77,12),(78,12)])
    def test_level_terminator_rejected(self):
        with self.assertRaises(ValueError):p.decode_span(b'\1\0\1','level_up')
    def test_level_zero_rejected(self):
        with self.assertRaises(ValueError):p.decode_span(b'\1\0\0\0\0\xff','level_up')
    def test_level_order_rejected(self):
        with self.assertRaises(ValueError):p.decode_span(struct.pack('<HBHB',77,12,78,11)+b'\0\0\xff','level_up')
    def test_ally_switch_rejected(self):
        with self.assertRaises(ValueError):p.decode_span(struct.pack('<H',1063),'evolution')
    def test_empty_evolution_distinct(self):
        self.assertEqual(p.decode_span(b'','evolution'),[])
        with self.assertRaises(ValueError):p.decode_span(b'','level_up')
    def test_evolution_alignment_rejected(self):
        with self.assertRaises(ValueError):p.decode_span(b'\1','evolution')
    def test_empty_regular_then_evolution(self):
        v=samples()[6];self.assertEqual(v['regular_moves'],[535]);self.assertEqual(v['evolution_moves'],[106]);self.assertEqual(v['after'],[33,81,535,106])
    def test_evolution_move_not_regular(self):
        v=samples()[7];self.assertEqual(v['regular_moves'],[]);self.assertEqual(v['evolution_moves'],[16]);self.assertEqual(v['after'],[106,16,0,0])
    def test_multiple_rows_order(self):
        v=samples()[8];self.assertEqual(v['regular_moves'],[77,78,79]);self.assertEqual(v['after'],[33,79,77,78]);self.assertEqual(v['selections'],1)
    def test_known_first_continues(self):
        v=samples()[9];self.assertEqual(v['after'],[77,81,78,79]);self.assertEqual(v['dialogs'],0)
    def test_refuse_all_three(self):
        v=samples()[10];self.assertEqual(v['after'],v['known']);self.assertEqual(v['after_pp'],v['pp']);self.assertEqual((v['dialogs'],v['stops']),(3,3))
    def test_below_level_preserves(self):
        v=samples()[5];self.assertEqual(v['regular_moves'],[]);self.assertEqual(v['after'],v['known']);self.assertEqual(v['after_pp'],v['pp'])
    def test_known_no_prompt(self):
        v=samples()[4];self.assertEqual(v['after'],v['known']);self.assertEqual(v['dialogs'],0)
    def test_summary_cancel_preserves(self):
        v=samples()[3];self.assertEqual(v['after'],v['known']);self.assertEqual((v['dialogs'],v['selections'],v['stops']),(1,1,1))
    def test_all_native_schemas(self):
        for v in samples():
            with self.subTest(case=v['name']):
                r,err=native(v);self.assertEqual(p.validate(json.dumps(r).encode(),err,v),r)
    def test_fake_success_actual_move_rejected(self):
        v=samples()[0];r,err=native(v);err=err.replace(b'move=535 expected=535',b'move=33 expected=535',1)
        with self.assertRaises(ValueError):p.validate(json.dumps(r).encode(),err,v)
    def test_duplicate_json_key_rejected(self):
        v=samples()[0];r,err=native(v);out=json.dumps(r).encode().replace(b'"status": "PASS"',b'"status":"PASS","status":"PASS"')
        with self.assertRaises(ValueError):p.validate(out,err,v)
    def test_bool_counter_rejected(self):
        v=samples()[0];r,err=native(v);r['witness']['party']=True
        with self.assertRaises(ValueError):p.validate(json.dumps(r).encode(),err,v)
    def test_bad_save_counter_rejected(self):
        v=samples()[0];r,err=native(v);r['save_counters']=[2,3,4]
        with self.assertRaises(ValueError):p.validate(json.dumps(r).encode(),err,v)
    def test_missing_core_rejected(self):
        v=samples()[0];r,err=native(v)
        with self.assertRaises(ValueError):p.validate(json.dumps(r).encode(),err.replace(b'original core destroyed;',b'not restarted;'),v)
    def test_missing_slot_proof_rejected(self):
        v=samples()[0];r,err=native(v)
        with self.assertRaises(ValueError):p.validate(json.dumps(r).encode(),b'\n'.join(err.splitlines()[:-1])+b'\n',v)
    def test_release_promotion_rejected(self):
        v=samples()[0];r,err=native(v);r['release_ready']=True
        with self.assertRaises(ValueError):p.validate(json.dumps(r).encode(),err,v)
    def test_misordered_evolution_rejected(self):
        v=samples()[1];r,err=native(v);r['witness']['begin']=10
        with self.assertRaises(ValueError):p.validate(json.dumps(r).encode(),err,v)
    def test_only_failed_cases_pending(self):
        vv=samples();r,_=native(vv[0]);todo,old=p.pending(vv,{'candidate':p.m.CANDIDATE,'results':[r]})
        self.assertEqual([v['name'] for v in todo],[v['name'] for v in vv[1:]]);self.assertEqual(old,[r])
    def test_changed_accepted_vector_rejected(self):
        vv=samples();r,_=native(vv[0]);r['pp_after'][0]=1
        with self.assertRaises(ValueError):p.pending(samples(),{'candidate':p.m.CANDIDATE,'results':[r]})
    def test_duplicate_prior_case_rejected(self):
        vv=samples();r,_=native(vv[0])
        with self.assertRaises(ValueError):p.pending(vv,{'candidate':p.m.CANDIDATE,'results':[r,r]})
    def test_other_candidate_rejected(self):
        with self.assertRaises(ValueError):p.pending(samples(),{'candidate':{'sha256':'wrong'},'results':[]})
    def test_controller_uses_three_full_barriers(self):
        c=(ROOT/p.C).read_text();self.assertEqual(c.count('a_guard(c);'),3)
        phase=c[c.index('static struct PTrace p_scene'):c.index('static void p_check')]
        for forbidden in ('call_preserving(','call_rom_args(','write8(','write16(','write32(','p02s_set_data(','p02s_data('):self.assertNotIn(forbidden,phase)
        self.assertIn('a_require(!memcmp(party,again,100U)',c)
    def test_expected_scope_not_initial_or_exp(self):
        r=p.expected(samples()[0]);self.assertFalse(r['initial_creation_accepted']);self.assertFalse(r['battle_exp_accepted']);self.assertFalse(r['issue19_complete'])
    def test_header_unique_cases(self):
        text=p.header(samples());self.assertEqual(text.count('  {"'),11);self.assertEqual(len(set(v[0] for v in p.CASES)),11)


if __name__=='__main__':unittest.main()
