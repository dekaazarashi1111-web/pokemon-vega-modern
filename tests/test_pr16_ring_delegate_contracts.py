"""未受入delegateの限定モデル・境界・誤証明拒否だけを検証。"""
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_delegate_contracts as m

class Contracts(unittest.TestCase):
    def small(self, halfwords):
        raw=struct.pack('<'+'H'*len(halfwords),*halfwords)
        return m.VM({0x08001000:raw},((0x08001000,0x08001000+len(raw)),))
    def test_fill_zero(self):
        self.assertEqual(m.fill_case(0,0,0),0)
    def test_fill_word_and_tail_boundaries(self):
        for n in (1,3,4,7,15,16,17,31,32,33,63,64):
            for a in range(4): m.fill_case(a,n,0xA5)
    def test_fill_truncates_value(self):
        for a in range(4): m.fill_case(a,19,0x123456AB)
    def test_fill_full_byte_classes(self):
        for b in range(256): m.fill_case(0,5,b)
    def test_fill_bad_inputs(self):
        for args in ((4,0,0),(0,256,0),(True,0,0),(0,-1,0),(0,1,1 << 32)):
            with self.assertRaises(ValueError): m.fill_case(*args)
    def test_reset_exact_writes(self):
        v=m.base_io(255); before=v.r[:12].copy(); r=v.run(m.RESET)
        self.assertTrue(r['returned']); self.assertEqual(v.writes,[(m.CONTROL,2,1),(m.BUSY,1,0)])
        self.assertEqual(v.r[:2],before[:2]); self.assertEqual(v.r[4:12],before[4:12])
    def test_reader_busy_blocks(self):
        for entry,n in ((m.READER,7),(m.TIME_READER,3)):
            self.assertEqual(m.reader_case(entry,1,bytes(n)),{'io_reads':0,'gpio_writes':0})
    def test_reader_non_one_busy(self):
        for busy in (0,2,127,255):
            self.assertEqual(m.reader_case(m.READER,busy,b'\xff'*7)['io_reads'],56)
    def test_reader_serial_bit_order(self):
        for pos in range(7):
            for bit in range(8):
                raw=bytearray(7);raw[pos]=1 << bit;m.reader_case(m.READER,0,bytes(raw))
    def test_time_reader_preserves_prefix(self):
        for b in (0,1,127,128,255): m.reader_case(m.TIME_READER,0,bytes([b,0x35,0x59]))
    def test_reader_gpio_write_counts(self):
        self.assertEqual(m.reader_case(m.READER,0,bytes(7))['gpio_writes'],374)
        self.assertEqual(m.reader_case(m.TIME_READER,0,bytes(3))['gpio_writes'],182)
    def test_reader_bad_inputs(self):
        for args in ((m.READER,0,bytes(6)),(m.READER,256,bytes(7)),(0,0,bytes(3))):
            with self.assertRaises(ValueError): m.reader_case(*args)
    def test_gate_busy(self):
        v=m.base_io(1);before=v.r[4:12].copy();m.checked_return(v,m.GATE,before)
        self.assertEqual(v.r[0],0)
    def test_gate_external_is_not_mocked(self):
        v=m.base_io(0);v.r[0]=m.BUFFER;r=v.run(m.GATE)
        self.assertFalse(r['returned']);self.assertEqual(r['unread_call'],0x0912C4A8)
        self.assertEqual(r['args'][0],m.BUFFER)
    def test_status_stack_pointer_argument(self):
        v=m.base_io(0);r=v.run(m.STATUS)
        self.assertEqual(r['args'][0],m.SP-28);self.assertFalse(r['returned'])
    def test_status_busy_returns(self):
        v=m.base_io(1);m.checked_return(v,m.STATUS,v.r[4:12].copy())
        self.assertEqual(v.r[0],0)
    def test_date_normal(self):
        r=m.date_case(bytes([1,2,0x28,6,0x23,0x59,0x59,64]))
        self.assertTrue(r['returned']);self.assertEqual(r['value'],0)
    def test_date_actual_lenient_edges(self):
        self.assertEqual(m.date_case(bytes([1,2,0,255,0x24,0x60,0x60,64]))['value'],0)
    def test_date_error_bits(self):
        self.assertEqual(m.date_case(bytes([0xFF,2,0xFF,0,0xFF,0xFF,0xFF,0x80]))['value'],0xF70)
    def test_date_status_bits(self):
        for status,result in ((0,16),(64,0),(128,48),(192,32)):
            self.assertEqual(m.date_case(bytes([1,2,1,0,0,0,0,status]))['value'],result)
    def test_date_weekday_unchecked(self):
        for weekday in range(256):
            self.assertEqual(m.date_case(bytes([1,2,1,weekday,0,0,0,64]))['value'],0)
    def test_date_leap_stops_before_external(self):
        r=m.date_case(bytes([4,2,0x29,0,0,0,0,64]))
        self.assertFalse(r['returned']);self.assertEqual(r['unread_call'],0x09099E04)
        self.assertEqual(r['args'][:2],[4,100])
    def test_date_month_table_not_invented(self):
        with self.assertRaisesRegex(ValueError,'09169530/4'):
            m.date_case(bytes([1,1,1,0,0,0,0,64]))
    def test_date_model_rejects_wrong_scope(self):
        for raw in (bytes([4,2,1,0,0,0,0,64]),bytes([1,3,1,0,0,0,0,64])):
            with self.assertRaises(ValueError): m.expected_february(raw)
    def test_date_bad_length(self):
        for raw in (b'',bytes(7),bytearray(8)):
            with self.assertRaises(ValueError): m.date_case(raw)
    def test_vm_arithmetic_and_signed_flags(self):
        v=m.VM()
        self.assertEqual(v.arithmetic(0x7FFFFFFF,1),0x80000000)
        self.assertEqual(v.flags,(True,False,False,True))
        self.assertEqual(v.arithmetic(0,1,True),0xFFFFFFFF)
        self.assertEqual(v.flags,(True,False,False,False))
        self.assertEqual(v.arithmetic(0xFFFFFFFF,0,carry=1),0)
        self.assertEqual(v.flags,(False,True,True,False))
    def test_vm_shift_boundaries(self):
        v=m.VM()
        for amount in (0,1,31,32,33,255):
            self.assertEqual(v.shift(0x80000001,amount,0),(0x80000001 << amount)&m.MASK)
            self.assertEqual(v.shift(0x80000001,amount,1),0x80000001 >> amount)
            self.assertEqual(v.shift(0x80000001,amount,2),(-2147483647 >> amount)&m.MASK)
    def test_vm_unknown_instruction(self):
        for h in (0xDE00,0xDF00,0xBE00,0xE800,0x4780):
            with self.assertRaises(ValueError): self.small([h]).run(0x08001000)
    def test_vm_literal_is_not_executable(self):
        with self.assertRaisesRegex(ValueError,'literal'):
            m.VM().run(0x0912C71C)
    def test_vm_rom_not_writable(self):
        v=m.VM()
        with self.assertRaisesRegex(ValueError,'ROM'): v.seed(m.FILL,b'\0')
        with self.assertRaisesRegex(ValueError,'write'): v.write(m.FILL,2,0)
    def test_vm_unprovided_unaligned(self):
        v=m.VM()
        for address,width in ((0x01000000,1),(m.SP-3,2)):
            with self.assertRaisesRegex(ValueError,'read'): v.read(address,width)
    def test_vm_step_and_entry_bounds(self):
        v=self.small([0xE7FE])
        with self.assertRaisesRegex(ValueError,'step'): v.run(0x08001000,2)
        for n in (0,True,20001):
            with self.assertRaises(ValueError): v.run(0x08001000,n)
        with self.assertRaises(ValueError): v.run(0x08001001)
    def test_vm_io_not_assumed(self):
        with self.assertRaisesRegex(ValueError,'bit不足'): m.base_io(0).read(m.DATA,2)
    def test_vm_stm_and_return(self):
        v=self.small([0xC108,0x4770]);v.seed(m.BUFFER,bytes(8));v.r[1]=m.BUFFER;v.r[3]=0x12345678
        self.assertTrue(v.run(0x08001000)['returned'])
        self.assertEqual(v.writes,[(m.BUFFER,4,0x12345678)]);self.assertEqual(v.r[1],m.BUFFER+4)
    def test_vm_sp_restore(self):
        v=self.small([0xB081,0xA800,0xB001,0x4770]);v.run(0x08001000)
        self.assertEqual(v.r[0],m.SP-4);self.assertEqual(v.r[13],m.SP)
    def test_boundaries_remain_explicit(self):
        source=Path(m.__file__).read_text()
        for expected in ("'rom_changes':0", "'new_emulator_processes':0", "'candidate_reconstructions':0", "'ring_acquisition_accepted':False", "'all_callers_resolved':False"):
            self.assertIn(expected,source)

if __name__=='__main__': unittest.main()
