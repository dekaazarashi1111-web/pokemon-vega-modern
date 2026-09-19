"""明示text RAM、live stack、独立期待値の回帰。受入済み全suiteは実行しない。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_text_state_contracts as t

ENTRY=0x08008001
NODES=[{'address':ENTRY&~1,'size':2,'hex':'7047','kind':'return','register':14}]


def analysis():
    def row(at,n):
        data=bytes(n);return {'address':at,'hex':data.hex(),'identity':t.s.identity(data)}
    return {'state_table':row(0x0800577c,28),'dispatch_tables':[row(0x0800582c,32),row(0x08005ae4,24)],
        'tables':[row(0x083e30e8,192)]}


class TextStateTests(unittest.TestCase):
    def machine(self,segments=(),args=()):return t.strict.Machine(NODES,segments,args)
    def test_explicit_stack_size(self):self.assertEqual(t.strict.STACK_END-t.strict.STACK_START,512)
    def test_audio_not_stack(self):self.assertTrue(all(a<t.strict.STACK_START for a in t.strict.AUDIO))
    def test_missing_audio_rejected(self):
        with self.assertRaisesRegex(ValueError,'未map read'):self.machine().read(t.strict.AUDIO[0],4)
    def test_explicit_audio(self):
        m=self.machine([(t.strict.AUDIO[0],t.b.word(0x80000001),False)])
        self.assertEqual(m.read(t.strict.AUDIO[0],4),0x80000001)
    def test_audio_write_readonly(self):
        m=self.machine([(t.strict.AUDIO[0],bytes(4),False)])
        with self.assertRaisesRegex(ValueError,'未許可 write'):m.write(t.strict.AUDIO[0],4,1)
    def test_audio_write_visible_not_stack(self):
        m=self.machine([(t.strict.AUDIO[0],bytes(4),True)]);m.write(t.strict.AUDIO[0],4,1)
        self.assertEqual(m.nonstack_writes(),[(t.strict.AUDIO[0],4,1)])
    def test_overlapping_segments_rejected(self):
        with self.assertRaises(ValueError):self.machine([(0x02000000,bytes(4),False),(0x02000002,bytes(4),True)])
    def test_stack_alias_rejected(self):
        with self.assertRaises(ValueError):self.machine([(t.strict.STACK_START,bytes(4),True)])
    def test_negative_segment_rejected(self):
        with self.assertRaises(ValueError):self.machine([(-1,b'\0',False)])
    def test_bytearray_rejected(self):
        with self.assertRaises(ValueError):self.machine([(0x02000000,bytearray(4),False)])
    def test_permission_type_rejected(self):
        with self.assertRaises(ValueError):self.machine([(0x02000000,bytes(4),1)])
    def test_extra_argument_rejected(self):
        with self.assertRaises(ValueError):self.machine(args=(0,0,0,0,0))
    def test_unwritten_live_stack_rejected(self):
        m=self.machine();m.r[13]-=4
        with self.assertRaisesRegex(ValueError,'未map read'):m.read(m.r[13],4)
    def test_nonlive_stack_write_rejected(self):
        with self.assertRaisesRegex(ValueError,'非live stack write'):self.machine().write(t.b.vm.SP-4,4,1)
    def test_nonlive_stack_read_rejected(self):
        with self.assertRaisesRegex(ValueError,'非live stack read'):self.machine().read(t.b.vm.SP-4,4)
    def test_live_stack_roundtrip(self):
        m=self.machine();m.r[13]-=4;m.write(m.r[13],4,0x12345678)
        self.assertEqual(m.read(m.r[13],4),0x12345678);self.assertEqual(m.nonstack_writes(),[])
    def test_cases_return_and_registers(self):
        c=t.strict.Cases(NODES);c.run('return',ENTRY,[],(7,),value=7)
        self.assertTrue(c.rows[0]['return_sp_r4_r11_proven'])
    def test_case_duplicate_rejected(self):
        c=t.strict.Cases(NODES);c.run('x',ENTRY,[])
        with self.assertRaisesRegex(ValueError,'label重複'):c.run('x',ENTRY,[])
    def test_audio_first_active(self):self.assertTrue(t.audio_active(1,0))
    def test_audio_second_active(self):self.assertTrue(t.audio_active(0,1))
    def test_audio_double_disabled(self):self.assertFalse(t.audio_active(0x80000001,0x80000001))
    def test_audio_empty(self):self.assertFalse(t.audio_active(0,0))
    def test_audio_high_noncount_bits(self):self.assertFalse(t.audio_active(0x00010000,0x40000000))
    def test_audio_negative_rejected(self):
        with self.assertRaises(ValueError):t.audio_active(-1,0)
    def test_audio_bool_rejected(self):
        with self.assertRaises(ValueError):t.audio_active(True,0)
    def test_table_hash_rejected(self):
        row=analysis()['state_table'];row['hex']='01'+row['hex'][2:]
        with self.assertRaises(ValueError):t.checked_table(row,28)
    def test_table_size_rejected(self):
        with self.assertRaises(ValueError):t.checked_table(analysis()['state_table'],32)
    def test_fixture_nonzero_config_normal(self):
        _,_,segs=t.fixture(analysis(),full=True,fast=0)
        self.assertEqual(next(data for at,data,_ in segs if at==t.b.BUFFER)[28],1)
    def test_fixture_zero_config_fast(self):
        _,_,segs=t.fixture(analysis(),full=True,fast=1)
        self.assertEqual(next(data for at,data,_ in segs if at==t.b.BUFFER)[28],0)
    def test_fixture_last_slot(self):
        at,p,segs=t.fixture(analysis(),full=True,slot=31,font=5)
        self.assertEqual(at,t.b.POOL+992);self.assertEqual(segs[0][1][992:],bytes(p))
    def test_fixture_bad_slot(self):
        with self.assertRaises(ValueError):t.fixture(analysis(),slot=32)
    def test_fixture_unselected_font(self):
        with self.assertRaises(ValueError):t.fixture(analysis(),font=3)
    def test_fixture_too_long_text(self):
        with self.assertRaises(ValueError):t.fixture(analysis(),text=bytes(65))
    def test_fixture_cursor_shape(self):
        with self.assertRaises(ValueError):t.fixture(analysis(),cursor=(1,))
    def test_ready_fast_held_writes(self):
        self.assertEqual(t.ready_writes(t.b.POOL,7,4,1,18),[(t.b.POOL+30,1,0),(t.b.POOL+30,1,1),(t.b.POOL,4,t.b.TEMPLATE+1)])
    def test_setup_preserves_upper_flags(self):
        p=bytearray(32);p[20]=0xa9;p[21]=3
        self.assertEqual(t.setup_writes(t.b.POOL,p,4),[(t.b.POOL+20,1,0xa4),(t.b.POOL+21,1,0x83)])


if __name__=='__main__':unittest.main()
