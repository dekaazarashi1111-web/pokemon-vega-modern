"""保存初期化byteの限定実行。native/既存ABIテストを呼ばない。"""
import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).resolve().parents[1]/'scripts/pr16_ring_record_init.py'
S=importlib.util.spec_from_file_location('record_init',P)
a=importlib.util.module_from_spec(S);S.loader.exec_module(a)
PTR=0x02010000

class RecordInit(unittest.TestCase):
    def test_invalid_states_exhaustive(self):
        for state in range(256):
            r=a.execute(state,PTR,0,0)
            self.assertEqual(r['selector'],7 if state in (1,2) else 0)
            if state not in (1,2):self.assertEqual((r['record_base'],r['capacity'],r['index']),(0x02008000,123,17))
    def test_capacity_u16_exhaustive(self):
        for size in range(65536):
            # 保存命令LSL16/LSR18と独立仕様floor(u16/4)の全域一致。
            actual=((size<<16)&0xffffffff)>>18
            self.assertEqual(actual,a.contract(1,size,0)['registered_capacity'])
    def test_size_high_bits(self):
        r=a.execute(1,PTR,0xabcd000c,0)
        self.assertEqual(r['capacity'],3)
    def test_state_high_bits(self):
        r=a.execute(0xffffff01,PTR,8,0)
        self.assertEqual((r['capacity'],r['selector']),(2,7))
    def test_mode1_does_not_fill(self):
        r=a.execute(1,PTR,12,3,allocated_bytes=12)
        self.assertEqual(r['buffer_hex'],'cc'*12)
    def test_mode2_template_not_zero(self):
        r=a.execute(2,PTR,12,3,allocated_bytes=12)
        self.assertEqual(r['buffer_hex'],'d4c3b2a1'*3)
    def test_limit_not_capacity(self):
        r=a.execute(2,PTR,4,3,allocated_bytes=12)
        self.assertEqual((r['capacity'],r['limit']),(1,3))
        self.assertEqual(r['buffer_hex'],'d4c3b2a1'*3)
    def test_insufficient_allocation_rejected(self):
        with self.assertRaisesRegex(ValueError,'割当外'):a.execute(2,PTR,4,3,allocated_bytes=4)
    def test_zero_limit(self):
        r=a.execute(2,PTR,12,0,allocated_bytes=12)
        self.assertEqual(r['buffer_hex'],'cc'*12)
    def test_remainder_untouched(self):
        r=a.execute(2,PTR,15,3,allocated_bytes=15)
        self.assertEqual(r['buffer_hex'],'d4c3b2a1'*3+'cc'*3)
    def test_stack_preserved(self):
        r=a.execute(2,PTR,8,2,allocated_bytes=8)
        self.assertEqual((r['sp'],r['r0']),(a.SP,a.LR))
        self.assertEqual([w['address'] for w in r['writes'][:3]],[a.SP-12,a.SP-8,a.SP-4])
    def test_writes_in_order(self):
        r=a.execute(2,PTR,4,1,allocated_bytes=4)
        self.assertEqual([w['address'] for w in r['writes'][3:]],[a.RECORD,a.CAPACITY,a.INDEX,PTR])
    def test_no_selector_write_in_valid_init(self):
        for state in (1,2):
            r=a.execute(state,PTR,0,0,selector=255)
            self.assertFalse(any(w['address']==a.SELECTOR for w in r['writes']))
    def test_largest_limit_bounded(self):
        c=a.contract(2,65535,65535)
        self.assertEqual(c['required_initialization_bytes'],262140)
        self.assertTrue(c['initialization_exceeds_declared_size'])
    def test_extent_boundary(self):
        self.assertFalse(a.contract(2,12,3)['initialization_exceeds_declared_size'])
        self.assertTrue(a.contract(2,11,3)['initialization_exceeds_declared_size'])
    def test_alias_guard(self):
        for ptr in (a.RECORD,a.LIMIT,a.SELECTOR,a.SP-12):
            with self.subTest(ptr=ptr),self.assertRaises(ValueError):a.execute(2,ptr,4,1,allocated_bytes=4)
    def test_unaligned_pointer(self):
        with self.assertRaises(ValueError):a.execute(2,PTR+1,4,1,allocated_bytes=4)
    def test_canonical_mapping_boundary(self):
        with self.assertRaises(ValueError):a.execute(2,0x0203fffc,8,2,allocated_bytes=8)
    def test_bool_and_range(self):
        for value in (True,-1,1<<32):
            with self.subTest(value=value),self.assertRaises(ValueError):a.contract(value,4,1)
    def test_step_limit(self):
        with self.assertRaisesRegex(ValueError,'step上限'):a.execute(2,PTR,4,1,allocated_bytes=4,max_steps=2)
    def test_unread_byte_rejected(self):
        with self.assertRaises(ValueError):a.saved_bytes({'analysis':{'new_windows':[]}},0,2)
    def test_corrupt_saved_window(self):
        prior={'analysis':{'new_windows':[{'start':0,'end':2,'hex':'0000','identity':{'size':2,'sha256':'bad'}}]}}
        with self.assertRaises(ValueError):a.saved_bytes(prior,0,2)
    def test_template_parameter(self):
        r=a.execute(2,PTR,4,1,allocated_bytes=4,template=0x11223344)
        self.assertEqual(r['buffer_hex'],'44332211')
    def test_overlap_halfopen(self):
        self.assertFalse(a.overlap((0,4),(4,8)));self.assertTrue(a.overlap((0,5),(4,8)))

if __name__=='__main__':unittest.main()
