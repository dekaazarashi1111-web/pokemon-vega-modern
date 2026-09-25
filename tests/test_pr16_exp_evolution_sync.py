"""読取と入力同期の修正だけ。初回24成功unitはhash照合し再実行0。"""
import copy
import json
from pathlib import Path
import re
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_exp_evolution_sync as g
from tests.test_pr16_exp_evolution_share import example,PP,ROWS


def complete_example(mode):
    result,err,case=example(mode);data,mon=g.e.party_evidence(err,result['party_count'])
    for stage,raw in zip(g.e.STAGES,data):
        updated=bytearray(raw)
        for i in range(result['party_count']):
            at=100*i;v=mon[stage,i]
            struct.pack_into('<HHI',updated,at+32,v['species'],v['held'],v['xp']);updated[at+40]=v['bonus']
            struct.pack_into('<4H',updated,at+44,*v['moves']);updated[at+52:at+56]=bytes(v['pp'])
        prefix=f'ESHARE_PARTY stage={stage} count={result["party_count"]} counter='.encode()
        for line in err.splitlines():
            if line.startswith(prefix):err=err.replace(line,line[:line.index(b'hex=')+4]+updated.hex().encode())
    return result,err+b'ESHARE_FIGHT frame=25 pulses=1\n',case


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.folder=g.e.ROOT/g.e.EVIDENCE/str(g.PRIOR);self.v=g.e.load(self.folder/'verification.json')
        self.reader=lambda leaf:(self.folder/leaf).read_bytes();self.source=lambda path:(g.e.ROOT/path).read_bytes()
    def test_24_successful_units_and_four_native_layouts_are_reused(self):
        r=g.reuse(self.v,self.reader,self.source);self.assertEqual(r['unchanged_unit_tests_reused'],24);self.assertEqual(r['native_layout_samples'],4)
    def test_changed_unit_source_cannot_be_reused(self):
        for name in (g.BASE_SELF,g.BASE_TEST,g.BASE_C):
            with self.subTest(name=name),self.assertRaises(ValueError):g.reuse(self.v,self.reader,lambda p:self.source(p)+(b'\n' if p==name else b''))
    def test_changed_unit_original_cannot_be_reused(self):
        for leaf in ('unit.stderr.txt','unit.process.json'):
            with self.subTest(leaf=leaf),self.assertRaises(ValueError):g.reuse(self.v,lambda p:self.reader(p)+(b' ' if p==leaf else b''),self.source)
    def test_failed_units_cannot_be_promoted(self):
        v=copy.deepcopy(self.v);v['new_unit_tests']=23
        with self.assertRaises(ValueError):g.reuse(v,self.reader,self.source)
    def test_changed_native_getter_layout_rejected(self):
        name='butterfree-exp-share.stderr.txt'
        with self.assertRaises(ValueError):g.reuse(self.v,lambda p:self.reader(p).replace(b'species=414',b'species=413') if p==name else self.reader(p),self.source)
    def test_three_native_contracts_accept_complete_raw_data(self):
        for mode in range(3):
            r,err,c=complete_example(mode)
            with self.subTest(mode=mode):self.assertTrue(g.validate(json.dumps(r).encode(),err,c,ROWS,PP)['read_only_party_layout_verified'])
    def test_raw_species_exp_move_pp_and_bonus_are_independently_checked(self):
        for offset in (32,34,36,40,44,52):
            r,err,c=complete_example(2);lines=err.splitlines()
            for i,line in enumerate(lines):
                if line.startswith(b'ESHARE_PARTY stage=fixture '):
                    at=line.index(b'hex=')+4;raw=bytearray.fromhex(line[at:].decode());raw[100+offset]^=1;lines[i]=line[:at]+raw.hex().encode()
            with self.subTest(offset=offset),self.assertRaises(ValueError):g.validate(json.dumps(r).encode(),b'\n'.join(lines)+b'\n',c,ROWS,PP)
    def test_whole_100byte_layout_required(self):
        for size in (0,99,101,200):
            with self.subTest(size=size),self.assertRaises(ValueError):g.decode(bytes(size))
    def test_missing_or_duplicate_fight_evidence_rejected(self):
        r,err,c=complete_example(0)
        for bad in (err.replace(b'ESHARE_FIGHT',b'OTHER'),err+b'ESHARE_FIGHT frame=25 pulses=1\n'):
            with self.assertRaises(ValueError):g.validate(json.dumps(r).encode(),bad,c,ROWS,PP)
    def test_unbounded_or_unordered_fight_key_rejected(self):
        for old,new in ((b'pulses=1',b'pulses=0'),(b'pulses=1',b'pulses=31'),(b'frame=25 pulses',b'frame=10 pulses')):
            r,err,c=complete_example(0)
            with self.subTest(new=new),self.assertRaises(ValueError):g.validate(json.dumps(r).encode(),err.replace(old,new),c,ROWS,PP)
    def test_observation_is_read_only_and_all_three_barriers_remain(self):
        c=(g.e.ROOT/g.C).read_text();get=c.split('static unsigned e_get(')[1].split('static void e_choose(')[0]
        for forbidden in ('qol_get_party_data','call_preserving','write','runFrame','->step'):self.assertNotIn(forbidden,get)
        self.assertIn('x_trace(c)',c);self.assertEqual(c.count('a_guard(c);'),3)
        main=c.split('int main(int argc,char **argv)')[1]
        for b in main.split('a_guard(c);')[1:]:
            observed=b.split('a_restore(c,&saved)')[0]
            for forbidden in ('write8(','write16(','write32(','call_preserving(','create_mon(','p02s_set_data('):self.assertNotIn(forbidden,observed)
    def test_fight_wait_is_bounded_neutral_then_ordinary_key(self):
        c=(g.e.ROOT/g.C).read_text();choose=c.split('static void e_choose(')[1].split('static void e_frame(')[0]
        self.assertIn('ready<12',choose);self.assertIn('i<1200',choose);self.assertIn('i<900',choose);self.assertIn('lb_frame(c,0)',choose)
        self.assertIn('QOL_KEY_A',choose);self.assertNotIn('write',choose);self.assertIn('read8(c,0x02022B24)==0x14',choose)


if __name__=='__main__':unittest.main()
