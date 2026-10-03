"""新しいBIOS効果だけを検証。旧724条件の評価器は呼ばない。"""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_bios_memory_contracts as b

SRC,DST=0x02001000,0x02002000


class BiosMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=b.context()

    def machine(self,control=10,source=None,dest=128,writable=True,src=SRC,dst=DST):
        if source is None:source=bytes(range(128))
        m=b.Machine(self.c,[(src,source,False),(dst,bytes(dest),writable)],(src,dst,control))
        m.last_pc=b.w.BIOS_COPY
        return m

    def apply(self,m,fast=False):
        b.transfer(m,b.w.BIOS_FILL if fast else b.w.BIOS_COPY)
        return m

    def test_halfword_copy_and_preserved_registers(self):
        m=self.machine();before=m.r.copy();flags=copy.deepcopy(m.flags);self.apply(m)
        self.assertEqual(m.data(DST,20),bytes(range(20)))
        self.assertEqual(m.r[:3],before[:3]);self.assertEqual(m.r[3],0x170)
        self.assertEqual(m.r[4:],before[4:]);self.assertEqual(m.flags,flags)
        self.assertEqual(m.writes,[(DST+2*i,2,2*i+(2*i+1)*256)for i in range(10)])

    def test_word_copy(self):
        m=self.apply(self.machine(0x04000003))
        self.assertEqual(m.data(DST,12),bytes(range(12)))
        self.assertEqual(len(m.writes),3)

    def test_halfword_fill(self):
        m=self.apply(self.machine(0x01000003,source=b'\x12\x34'))
        self.assertEqual(m.data(DST,6),b'\x12\x34'*3)
        self.assertEqual(len(m.reads),1)

    def test_word_fill(self):
        m=self.apply(self.machine(0x05000003,source=b'\x01\x23\x45\x67'))
        self.assertEqual(m.data(DST,12),b'\x01\x23\x45\x67'*3)

    def test_fast_fill_rounds_to_eight_words(self):
        m=self.machine(0x01000009,source=b'\x13\x57\x9b\xdf');before=m.r.copy()
        self.apply(m,True)
        self.assertEqual(m.data(DST,64),b'\x13\x57\x9b\xdf'*16)
        self.assertEqual(m.r[:4],[SRC,DST+64,before[2],0xdf9b5713])
        self.assertEqual(m.r[4:],before[4:])

    def test_fast_copy_registers_and_block_order(self):
        m=self.apply(self.machine(9),True)
        self.assertEqual(m.data(DST,64),bytes(range(64)))
        self.assertEqual(m.r[:4],[SRC+64,DST+64,9,0x23222120])
        self.assertEqual(len(m.writes),16)

    def test_fast_ignores_word_flag(self):
        m=self.apply(self.machine(0x04000001),True)
        self.assertEqual(len(m.writes),8)

    def test_fast_zero_copy_has_no_reads_writes(self):
        m=self.machine(0,source=b'',dest=0);r3=m.r[3];self.apply(m,True)
        self.assertEqual(m.r[3],r3);self.assertFalse(m.reads);self.assertFalse(m.writes)

    def test_fast_zero_fill_still_reads_one_word(self):
        m=self.apply(self.machine(0x01000000,source=b'abcd',dest=0),True)
        self.assertEqual(m.r[3],0x64636261);self.assertEqual(len(m.reads),1);self.assertFalse(m.writes)

    def test_set_zero_copy_clobbers_r3(self):
        m=self.apply(self.machine(0,source=b'',dest=0))
        self.assertEqual(m.r[3],0x170);self.assertFalse(m.reads)

    def test_set_zero_fill_needs_source(self):
        m=self.machine(0x01000000,source=b'',dest=0)
        with self.assertRaisesRegex(ValueError,'未map read'):self.apply(m)
        self.assertFalse(m.bios_events[0]['completed']);self.assertFalse(m.writes)

    def test_short_source_preserves_completed_halfwords(self):
        m=self.machine(source=b'abcde')
        with self.assertRaisesRegex(ValueError,'未map read'):self.apply(m)
        self.assertEqual(m.data(DST,6),b'abcd\0\0')
        self.assertEqual(m.bios_events[0]['writes_completed'],2)

    def test_short_destination_has_atomic_halfwords(self):
        m=self.machine(dest=5)
        with self.assertRaisesRegex(ValueError,'未許可 write'):self.apply(m)
        self.assertEqual(m.data(DST,5),bytes((0,1,2,3,0)))
        self.assertEqual(m.bios_events[0]['writes_completed'],2)

    def test_readonly_destination(self):
        m=self.machine(writable=False)
        with self.assertRaisesRegex(ValueError,'未許可 write'):self.apply(m)
        self.assertFalse(m.writes)

    def test_fast_short_first_block_does_not_write(self):
        m=self.machine(8,source=bytes(28))
        with self.assertRaisesRegex(ValueError,'未map read'):self.apply(m,True)
        self.assertFalse(m.writes)

    def test_fast_short_second_block_preserves_first(self):
        m=self.machine(9,source=bytes(range(60)))
        with self.assertRaisesRegex(ValueError,'未map read'):self.apply(m,True)
        self.assertEqual(m.data(DST,36),bytes(range(32))+bytes(4))
        self.assertEqual(len(m.writes),8);self.assertEqual(m.r[0],SRC+32)

    def test_fast_partial_store_keeps_previous_words(self):
        m=self.machine(0x01000001,source=b'abcd',dest=14)
        with self.assertRaisesRegex(ValueError,'未許可 write'):self.apply(m,True)
        self.assertEqual(m.data(DST,14),b'abcd'*3+b'\0\0')
        self.assertEqual(len(m.writes),3)

    def test_alignment_rejected_before_mutation(self):
        for fast,src,dst in ((False,SRC+1,DST),(True,SRC+2,DST),(True,SRC,DST+2)):
            with self.subTest(fast=fast,src=src,dst=dst):
                m=self.machine(src=src,dst=dst)
                with self.assertRaisesRegex(ValueError,'alignment'):self.apply(m,fast)
                self.assertFalse(m.writes);self.assertFalse(m.bios_events)

    def test_reserved_control_bits(self):
        for bit in (20,21,23,25,27,31):
            with self.subTest(bit=bit):
                m=self.machine(1<<bit)
                with self.assertRaisesRegex(ValueError,'予約control'):self.apply(m)
                self.assertFalse(m.writes)

    def test_budget_and_rounding_limit(self):
        for fast,count in ((False,2049),(True,2049),(True,0xfffff)):
            with self.subTest(fast=fast,count=count):
                m=self.machine(count)
                with self.assertRaisesRegex(ValueError,'count予算'):self.apply(m,fast)
                self.assertFalse(m.writes)

    def test_out_of_region_and_wrap(self):
        for at,size in ((0xffffffff,4),(0x0203fffe,4),(0x03007ffc,8),(0x01000000,4)):
            with self.subTest(at=at):
                with self.assertRaises(ValueError):b.region(at,size)

    def test_rom_destination_rejected(self):
        with self.assertRaises(ValueError):b.region(0x083e3000,20,True)

    def test_reserved_stack_destination_rejected(self):
        with self.assertRaisesRegex(ValueError,'stack alias'):b.region(b.w.strict.STACK_END-4,4,True)

    def test_alias_rejected(self):
        m=self.machine();m.r[1]=SRC+4
        with self.assertRaisesRegex(ValueError,'alias'):self.apply(m)
        self.assertFalse(m.writes)

    def test_unknown_service_rejected(self):
        m=self.machine()
        with self.assertRaisesRegex(ValueError,'未知'):b.transfer(m,0)

    def test_saved_prefix_mutation_rejected(self):
        c=copy.deepcopy(self.c);c['analysis']['bios_prefix']['hex']='00df7047'
        with self.assertRaisesRegex(ValueError,'保存BIOS'):b.Machine(c,[])

    def test_ldmia_stmia_independent_oracle(self):
        m=self.machine();m.r[1]=SRC;m.last_pc=0x08003f80;m.block_transfer(0xc91c)
        self.assertEqual(m.r[1],SRC+12)
        self.assertEqual(m.r[2:5],[0x03020100,0x07060504,0x0b0a0908])
        m.r[0]=DST;m.last_pc=0x08003f82;m.block_transfer(0xc01c)
        self.assertEqual(m.data(DST,12),bytes(range(12)));self.assertEqual(m.r[0],DST+12)

    def test_block_alias_and_empty_rejected(self):
        for h in (0xc100,0xc902,0xc002):
            m=self.machine()
            if h==0xc002:m.r[0]=DST+1
            with self.assertRaises(ValueError):m.block_transfer(h)

    def test_block_partial_store(self):
        m=self.machine(dest=9);m.r[0]=DST;m.r[2:5]=[1,2,3]
        with self.assertRaisesRegex(ValueError,'未許可'):m.block_transfer(0xc01c)
        self.assertEqual(len(m.writes),2);self.assertEqual(m.data(DST,9),b'\1\0\0\0\2\0\0\0\0')

    def test_new_suffix_cases_and_exact_stops(self):
        rows=b.integration();self.assertEqual(len(rows),25)
        self.assertEqual(len({r['case']for r in rows}),25)
        self.assertEqual(rows[0]['read_fault'],{'address':0x081534e4,'size':4,'site':0x081534dc})
        self.assertEqual(rows[3]['read_fault'],{'address':0x08001aec,'size':4,'site':0x08001abe})
        self.assertEqual(rows[3]['nonstack_write_count'],942)
        self.assertEqual(rows[3]['block_events'][0]['values'],rows[3]['block_events'][1]['values'])
        self.assertFalse(any(r['returned']for r in rows))

    def test_integration_is_single_cached_evaluation(self):
        self.assertIs(b.integration(),b.integration());self.assertEqual(b.integration.cache_info().misses,1)

    def test_no_bios_native_acceptance_claim(self):
        for row in b.integration():
            self.assertFalse(row['bios_stack_bytes_included'])
            for e in row['bios_events']:
                self.assertFalse(e['bios_execution_observed']);self.assertTrue(e['return_is_conditional'])
        self.assertEqual(b.PROVENANCE['git_blob'],'c891479a5ee8efb37eba00365c765d2fa90b12b1')
        self.assertEqual(len(b.PROVENANCE['preconditions_ja']),4)


if __name__=='__main__':unittest.main()
