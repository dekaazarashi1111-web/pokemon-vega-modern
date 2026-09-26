"""Changed egg consumers: independent pool and ordinary lifecycle boundaries."""
from pathlib import Path
import json
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_learnset_egg_gameplay as m

class EggGameplayTests(unittest.TestCase):
    def setUp(self):
        self.name=m.CASES[0][0]
        self.pp={x:(5 if x else 0) for c in m.CASES for x in c[-1]}
        self.value=m.expected(self.name,self.pp)
        self.value.update(generation_steps=255,hatch_clock_start=31,hatch_steps=2784,
                          hatch_callback_frames=800,hatch_state_mask=(1<<6)|(1<<10),total_frames=50000,
                          witness={k:(i+1)*100 for i,k in enumerate(m.WITNESS)})
        self.stderr=b'original core destroyed; new core boot and normal Continue\n'*2
    def validate(self):return m.validate(json.dumps(self.value).encode(),self.stderr,self.name,self.pp)
    def test_source_matrix(self):
        self.assertEqual(len(m.CASES),8)
        for c in m.CASES:
            self.assertEqual(m.inherited(c,m.LEVELS[c[6]],m.EGGS[c[6]]),c[-1])
    def test_order_overflow_and_duplicates(self):
        c=m.CASES[0]
        self.assertEqual(m.inherited(c,[39,84],m.EGGS[24]),(84,175,273,344))
        c=m.CASES[4]
        self.assertEqual(m.inherited(c,[39,84],m.EGGS[24]),(39,84,175,273))
    def test_parent_item_symmetry(self):
        a,b=m.CASES[:2]
        self.assertEqual(m.inherited(a,m.LEVELS[24],m.EGGS[24]),m.inherited(b,m.LEVELS[24],m.EGGS[24]))
    def test_no_flatten_or_old_moves(self):
        self.assertNotIn(344,m.EGGS[24]);self.assertNotIn(440,m.EGGS[24])
        self.assertTrue(all(x not in m.EGGS[364] for x in (461,464,357)))
        self.assertEqual(m.inherited(m.CASES[2],m.LEVELS[24],m.EGGS[24]),(39,84,0,0))
    def test_egg_owner(self):
        raw=struct.pack('<3H',20024,175,65535)
        self.assertEqual(m.source_moves(raw,24,'egg'),[175])
        with self.assertRaises(ValueError):m.source_moves(raw,25,'egg')
    def test_egg_alignment(self):
        with self.assertRaises(ValueError):m.source_moves(b'abc',24,'egg')
    def test_unsupported_move(self):
        with self.assertRaises(ValueError):m.source_moves(struct.pack('<2H',20024,1063),24,'egg')
    def test_level_one_only(self):
        raw=struct.pack('<HBHBHB',39,1,84,4,0,255)
        self.assertEqual(m.source_moves(raw,24,'level_up'),[39])
    def test_level_terminator(self):
        with self.assertRaises(ValueError):m.source_moves(struct.pack('<HB',39,1),24,'level_up')
    def test_controller_preserves_guards(self):
        raw=(ROOT/m.PARENT).read_bytes();new=m.controller(raw)
        self.assertEqual(new.count('a_guard(c);'),raw.decode().count('a_guard(c);'))
        self.assertIn('z<12288U && !b_hatched',new)
        self.assertIn('initial_cycles==v->cycles',new)
        for c in m.CASES:self.assertIn('"'+c[0]+'"',new)
    def test_controller_preimage(self):
        with self.assertRaises(ValueError):m.controller((ROOT/m.PARENT).read_bytes()+b'\n')
    def test_valid_result(self):self.assertEqual(self.validate(),self.value)
    def test_fresh_core_missing(self):
        self.stderr=b'original core destroyed; new core boot and normal Continue\n'
        with self.assertRaises(ValueError):self.validate()
    def test_witness_order(self):
        self.value['witness']['claimed']=self.value['witness']['generated']
        with self.assertRaises(ValueError):self.validate()
    def test_physical_hatch_cadence(self):
        self.value['hatch_steps']+=1
        with self.assertRaises(ValueError):self.validate()
    def test_release_overclaim(self):
        self.value['release_ready']=True
        with self.assertRaises(ValueError):self.validate()
    def test_duplicate_key(self):
        raw=json.dumps(self.value).replace('"status": "PASS"','"status": "PASS", "status": "PASS"').encode()
        with self.assertRaises(ValueError):m.validate(raw,self.stderr,self.name,self.pp)
    def test_nested_boolean_counter(self):
        self.value['pp'][0]=True
        self.pp[84]=1
        with self.assertRaises(ValueError):self.validate()

if __name__=='__main__':unittest.main()
