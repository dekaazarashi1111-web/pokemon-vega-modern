"""今回の局所roleだけ。既読initializer/alias ABIやnativeは呼ばない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_control_roles as m

RAW=bytes.fromhex('26091603123456')

class Roles(unittest.TestCase):
    def test_bcd_normal(self):
        vm,_=m.bcd_case(RAW)
        self.assertEqual(vm.read(m.CONVERTED,2),2026)
        self.assertEqual([vm.read(m.CONVERTED+i,1) for i in range(3,9)],[9,16,3,12,34,56])
    def test_bcd_year_low_digit_invalid(self):
        vm,_=m.bcd_case(bytes([0x2a])+RAW[1:]);self.assertEqual(vm.read(m.CONVERTED,2),2255)
    def test_bcd_year_high_digit_invalid(self):
        vm,_=m.bcd_case(bytes([0xa0])+RAW[1:]);self.assertEqual(vm.read(m.CONVERTED,2),2255)
    def test_bcd_year_boundary(self):
        for b,w in ((0,2000),(0x99,2099),(0xff,2255)):
            with self.subTest(b=b):self.assertEqual(m.bcd_case(bytes([b])+RAW[1:])[0].read(m.CONVERTED,2),w)
    def test_bcd_not_calendar_validation(self):
        vm,_=m.bcd_case(b'\x99'*7)
        self.assertEqual(vm.read(m.CONVERTED+3,1),99)
        self.assertEqual(vm.read(m.CONVERTED+6,1),99)
    def test_bcd_invalid_fields(self):
        vm,_=m.bcd_case(b'\xff'*7)
        self.assertEqual([vm.read(m.CONVERTED+i,1) for i in range(3,9)],[255]*6)
    def test_hour_toggle(self):
        for b,w in ((0,12),(0x11,23),(0x12,0),(0x23,11),(0x99,87),(0xff,243)):
            with self.subTest(b=b):
                raw=RAW[:4]+bytes([b])+RAW[5:]
                self.assertEqual(m.bcd_case(raw,1)[0].read(m.CONVERTED+6,1),w)
    def test_hour_any_nonzero_flag(self):
        for f in (1,2,128,255):self.assertEqual(m.bcd_case(RAW,f)[0].read(m.CONVERTED+6,1),0)
    def test_padding_unchanged(self):self.assertEqual(m.bcd_case(RAW)[0].read(m.CONVERTED+2,1),0xcc)
    def test_selector_limit_not_written(self):
        vm,_=m.bcd_case(RAW,1)
        self.assertFalse(any(m.SELECTOR<=w['address']<m.SELECTOR+7 for w in vm.writes))
    def test_converter_no_external_calls(self):self.assertEqual(m.bcd_case(RAW)[0].calls,[])
    def test_converter_frame(self):
        vm,_=m.bcd_case(RAW)
        self.assertEqual(min(w['address'] for w in vm.writes if w['address']>=m.SP-64),m.SP-16)
    def test_converter_inputs(self):
        for raw in (RAW[:-1],RAW+b'\0',bytearray(RAW),'1234567'):
            with self.assertRaises(ValueError):m.expected_bcd(raw)
        for f in (-1,256,True):
            with self.assertRaises(ValueError):m.expected_bcd(RAW,f)
    def test_independent_vectors(self):self.assertEqual(m.bcd_vectors(),2048)
    def test_reader_invalid_status(self):
        for status in (0,2,0xff,0x10000):
            vm=m.reader_case(status,123);self.assertEqual(len(vm.calls),2);self.assertEqual(vm.read(m.STATUS,2),1)
    def test_reader_status_low_nibble(self):
        for status in (1,17,0x10001,0xfffffff1):self.assertEqual(len(m.reader_case(status,0).calls),5)
    def test_reader_intermediate_status(self):
        for status,expected in ((1,0),(17,2),(0x10001,2)):
            self.assertEqual(m.reader_case(status,0).calls[2]['status_at_call'],expected)
    def test_reader_output_pointer(self):
        self.assertTrue(all(c['args'][0]==m.SELECTOR for c in m.reader_case(1,0).calls[2:]))
    def test_reader_truncates_validation(self):self.assertEqual(m.reader_case(1,0x12345678).read(m.STATUS,2),0x5678)
    def test_reader_io_restored(self):
        vm=m.reader_case(1,0);self.assertEqual(vm.read(m.IO,2),0x81)
        self.assertEqual([c['io_at_call'] for c in vm.calls],[0,0,0,0,0x81])
    def test_reader_requires_explicit_mock(self):
        vm=m.VM()
        for at,width in ((m.IO,2),(m.STATUS,2),(m.SAVED_IO,2),(m.RAW_STATUS,1)):vm.seed(at,bytes(width))
        with self.assertRaisesRegex(ValueError,'未証明外部callee'):vm.run(m.READER)
    def test_tick_zero_stops_before_reader(self):self.assertEqual(m.prefix(0)[1]['stopped_before_external_call'],m.READER)
    def test_tick_nonzero_all(self):
        for n in range(1,256):
            vm,_=m.prefix(n);self.assertEqual(vm.read(m.COUNTER,1),n+1 if n<60 else 0)
    def test_tick_frame_at_call(self):self.assertEqual(m.prefix(0)[0].r[13],m.SP-16)
    def test_init_resets_before_reader(self):
        vm,r=m.prefix(255,m.INIT);self.assertEqual(vm.read(m.COUNTER,1),0);self.assertEqual(r['stopped_before_external_call'],m.READER)
    def test_veneer_literal(self):
        vm=m.VM();self.assertEqual(vm.read(0x09099e64,4),0x081c9df9)
        self.assertEqual(vm.run(m.VENEER),{'steps':2,'tail_target':0x081c9df9})
    def test_veneer_preserves_until_tail_only(self):
        vm=m.VM();before=vm.r.copy();vm.run(m.VENEER)
        self.assertEqual(vm.r[:3]+vm.r[4:],before[:3]+before[4:]);self.assertEqual(vm.writes,[])
    def test_vm_rom_immutable(self):
        vm=m.VM()
        with self.assertRaises(ValueError):vm.write(m.BCD,2,0)
        with self.assertRaises(ValueError):vm.seed(m.BCD,b'\x00\x00')
    def test_vm_unseeded_read_write(self):
        vm=m.VM()
        with self.assertRaises(ValueError):vm.read(0x02000000,4)
        with self.assertRaises(ValueError):vm.write(0x02000000,4,0)
    def test_vm_unaligned(self):
        vm=m.VM()
        with self.assertRaises(ValueError):vm.read(m.SP-1,2)
        with self.assertRaises(ValueError):vm.write(m.SP-1,2,0)
    def test_vm_unknown_opcode(self):
        vm=m.VM();vm.mem[m.VENEER]=0;vm.mem[m.VENEER+1]=0xbe
        with self.assertRaises(ValueError):vm.run(m.VENEER)
    def test_vm_noncode_execution(self):
        vm=m.VM();vm.seed(0x02000000,b'\x00\x20')
        with self.assertRaisesRegex(ValueError,'code範囲外'):vm.run(0x02000000)
    def test_vm_blx_rejected(self):
        vm=m.VM();vm.mem[m.VENEER]=0x98;vm.mem[m.VENEER+1]=0x47
        with self.assertRaisesRegex(ValueError,'BLX'):vm.run(m.VENEER)
    def test_vm_step_limit(self):
        for n in (0,-1,501,True):
            with self.assertRaises(ValueError):m.VM().run(m.VENEER,max_steps=n)
        with self.assertRaisesRegex(ValueError,'step上限'):m.VM().run(m.VENEER,max_steps=1)
    def test_no_code_mutation(self):
        before=copy.deepcopy(m.CODES);m.bcd_case(RAW);m.reader_case(1,0);m.prefix(0)
        self.assertEqual(m.CODES,before)

if __name__=='__main__':unittest.main()
