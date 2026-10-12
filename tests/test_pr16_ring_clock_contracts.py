"""新規GPIO/月表範囲/中継の限定回帰。旧7delegateや実ROM/nativeは再実行しない。"""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_clock_contracts as m
old=m.old


def date(month=1,day=0x31,year=1,status=64,hour=0x12,minute=0x30,second=0x45,weekday=0):
    return bytes([year,month,day,weekday,hour,minute,second,status])


class Contracts(unittest.TestCase):
    def test_read_bit_mapping(self):
        for byte,result in ((0,0),(1,0),(2,1),(4,0),(8,2),(16,0),(32,4),(64,64),(128,128),(255,199)):
            self.assertEqual(m.read_case(byte)['result_byte'],result)

    def test_read_busy_does_not_gate(self):
        for busy in (0,1,2,255): self.assertEqual(m.read_case(0xAA,busy)['io_reads'],8)

    def test_read_buffer_alignment_and_edges(self):
        for alignment in range(4): self.assertEqual(m.read_case(255,0,alignment)['nonstack_writes'],88)

    def test_read_all_payload_bytes(self):
        for byte in range(256):
            expected=(byte&0xC0)+4*bool(byte&32)+2*bool(byte&8)+bool(byte&2)
            self.assertEqual(m.read_case(byte)['result_byte'],expected)

    def test_write_bit_mapping(self):
        for value,expected in ((0,64),(1,66),(2,72),(4,96),(7,106),(8,64),(255,106)):
            self.assertEqual(m.write_case(value)['serialized_byte'],expected)

    def test_write_busy_does_not_gate(self):
        for busy in (0,1,2,255): self.assertEqual(m.write_case(7,busy)['nonstack_writes'],70)

    def test_write_upper_bits_ignored(self):
        for value in (0x100,0x10007,0xFFFFFFFF):
            self.assertEqual(m.write_case(value)['serialized_byte'],m.write_value(value&7))

    def test_write_all_low_bytes(self):
        for value in range(256):
            self.assertEqual(m.write_case(value)['serialized_byte'],64+32*bool(value&4)+8*bool(value&2)+2*bool(value&1))

    def test_payload_composition_not_hardware(self):
        for value in range(256): self.assertEqual(m.read_value(m.write_value(value)),64+(value&7))

    def test_bad_read_inputs(self):
        for value in (-1,256,True,b'x'):
            with self.assertRaises(ValueError):m.read_case(value)
        for alignment in (-1,4,True):
            with self.assertRaises(ValueError):m.read_case(0,0,alignment)

    def test_bad_write_or_busy_inputs(self):
        for value in (-1,1<<32,True):
            with self.assertRaises(ValueError):m.write_case(value)
        for busy in (-1,256,True):
            with self.assertRaises(ValueError):m.io_vm(busy)

    def bic_vm(self,tail=b'\x70\x47',opcode=m.BIC_OPCODE):
        raw=struct.pack('<H',opcode)+tail
        return m.ClockVM({m.BIC_SITE:raw},((m.BIC_SITE,m.BIC_SITE+len(raw)),))

    def test_bic_flags_and_preserved_state(self):
        for value,mask,negative,zero in ((0xFFFFFFFF,0x7FFFFFFF,True,False),(63,63,False,True),(64,63,False,False)):
            vm=self.bic_vm();vm.r[0]=value;vm.r[4]=mask;vm.flags=(False,False,True,True)
            before=vm.r[1:];mem=dict(vm.mem);result=vm.run(m.BIC_SITE)
            self.assertEqual(vm.r[0],value&~mask&old.MASK)
            self.assertEqual(vm.flags,(negative,zero,True,True))
            self.assertEqual(vm.r[1:],before);self.assertEqual(vm.mem,mem)
            self.assertEqual(result['bic_count'],1);self.assertEqual(result['instruction_halfword_fetches'],2)

    def test_bic_zero_flags_preserve_false_carry_overflow(self):
        vm=self.bic_vm();vm.r[0]=vm.r[4]=255;vm.flags=(True,False,False,False)
        vm.run(m.BIC_SITE);self.assertEqual(vm.flags,(False,True,False,False))

    def test_bic_site_mutation_rejected(self):
        vm=self.bic_vm(opcode=0x4000)
        with self.assertRaisesRegex(ValueError,'BIC'):vm.run(m.BIC_SITE)
        self.assertFalse(vm.executing)

    def test_bic_elsewhere_not_silently_supported(self):
        vm=m.ClockVM({0x08000000:struct.pack('<HH',m.BIC_OPCODE,0x4770)},((0x08000000,0x08000004),))
        with self.assertRaises(ValueError):vm.run(0x08000000)

    def test_segment_step_limit(self):
        vm=self.bic_vm()
        with self.assertRaisesRegex(ValueError,'fetch上限'):vm.run(m.BIC_SITE,1)
        self.assertFalse(vm.executing)

    def test_repeated_bic_cannot_reset_budget(self):
        vm=self.bic_vm(struct.pack('<H',0xE7FD))
        with self.assertRaisesRegex(ValueError,'fetch上限'):vm.run(m.BIC_SITE,7)
        self.assertLessEqual(vm.bic_count,4)

    def test_read_is_not_execution(self):
        vm=self.bic_vm()
        self.assertEqual(vm.read(m.BIC_SITE,2),m.BIC_OPCODE)
        self.assertEqual(vm.fetches,0)

    def test_missing_read_is_explicit(self):
        vm=self.bic_vm()
        with self.assertRaises(m.MissingRead) as cm:vm.read(0x02000000,4)
        self.assertEqual((cm.exception.at,cm.exception.width),(0x02000000,4))
        with self.assertRaises(ValueError):vm.read(0x02000001,4)

    def test_gpio_requires_supplied_io(self):
        vm=m.io_vm(0);vm.seed(old.BUFFER,bytes(16));vm.r[0]=old.BUFFER
        with self.assertRaises(ValueError):vm.run(m.READ)

    def test_rom_and_literal_safety(self):
        vm=m.io_vm(0)
        with self.assertRaises(ValueError):vm.seed(m.READ,b'\0')
        with self.assertRaises(ValueError):vm.run(0x0912C548)

    def test_run_bad_bounds(self):
        for entry,limit in ((m.READ+1,20),(m.READ,0),(m.READ,20001),(True,10),(m.READ,True)):
            with self.assertRaises(ValueError):m.io_vm(0).run(entry,limit)

    def test_valid_month_table_edges(self):
        for month in (1,3,4,5,6,7,8,9,0x10,0x11,0x12):
            days=m.MONTHS[m.bcd(month)-1]
            last=(days//10)*16+days%10;after=((days+1)//10)*16+(days+1)%10
            self.assertEqual(m.date_case(date(month,last)),{'returned':True,'value':0})
            self.assertEqual(m.date_case(date(month,after)),{'returned':True,'value':256})

    def test_day_zero_leniency_preserved(self):
        self.assertEqual(m.date_case(date(0x12,0)),{'returned':True,'value':0})

    def test_day_bcd_invalid(self):
        for day in (0x1A,0x9F,0xA0,0xFF):self.assertEqual(m.date_case(date(4,day))['value'],256)

    def test_invalid_month_zero_reads_before_table(self):
        result=m.date_case(date(0));self.assertFalse(result['returned'])
        self.assertEqual(result['table_read_address'],m.TABLE-4)

    def test_invalid_month_thirteen_reads_after_table(self):
        self.assertEqual(m.date_case(date(0x13))['table_read_address'],m.TABLE+48)

    def test_invalid_bcd_month_uses_sentinel_index(self):
        for month in (0x0A,0x9F,0xA0,255):
            self.assertEqual(m.date_case(date(month,255))['table_read_address'],m.TABLE+1016)

    def test_invalid_month_all_byte_values(self):
        count=0
        for month in range(256):
            if month==2:continue
            r=m.date_case(date(month,0))
            count+=not r['returned']
        self.assertEqual(count,244)

    def test_month_bounds_do_not_claim_hardware_fault(self):
        r=m.date_case(date(0))
        self.assertEqual(r['stop'],'outside_declared_month_table')
        self.assertNotIn('value',r)

    def test_old_february_scope_refused(self):
        for year in (0,1,4,99):
            with self.assertRaises(ValueError):m.date_case(date(2,year=year))

    def test_date_combined_errors_new_month(self):
        r=m.date_case(date(4,0x31,year=0xFF,status=0x80,hour=0x25,minute=0x61,second=0x61))
        self.assertEqual(r['value'],16+32+64+256+512+1024+2048)

    def test_date_input_length_or_type(self):
        for raw in (bytes(7),bytes(9),bytearray(8)):
            with self.assertRaises(ValueError):m.date_case(raw)

    def test_thunk_pc_alignment_and_pointer(self):
        r=m.thunk_contract()
        self.assertEqual(r['local_target'],0x09099E0E)
        self.assertEqual(r['literal_address'],0x09099E5C)
        self.assertEqual(r['unread_tail_target'],0x081C85A5)
        self.assertEqual(r['saved_lr_bytes'],4)
        self.assertEqual(r['callee_entry_sp_mod8_delta'],4)

    def test_thunk_is_not_invented_remainder_or_abi(self):
        r=m.thunk_contract()
        for k in ('external_return_or_abi_proven','remainder_semantics_proven','leap_year_suffix_proven'):
            self.assertIs(r[k],False)

    def test_thunk_bad_bytes_and_pointer(self):
        for i in range(len(m.THUNK_CODE)):
            raw=bytearray(m.THUNK_CODE);raw[i]^=1
            with self.assertRaises(ValueError):m.thunk_contract(bytes(raw))
        for raw in (bytes(3),struct.pack('<I',0x081C85A4),struct.pack('<I',0x02000001)):
            with self.assertRaises(ValueError):m.thunk_contract(literal=raw)


if __name__=='__main__':unittest.main()
