"""新しい剰余・中継・閏年suffixとfail-closed連結境界だけを検証。"""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_leap_contracts as m

class LeapContractTests(unittest.TestCase):
    def raw(self,year=0,day=0x29,**fields):
        data=[year,2,day,0,0x12,0x30,0x45,64]
        for key,value in fields.items():data[int(key)]=value
        return bytes(data)
    def test_code_size(self):self.assertEqual(len(m.CODE),192)
    def test_small_remainder(self):
        for a in (0,1,99,100,101,255):self.assertEqual(m.remainder_case(a,100)['remainder'],a%100)
    def test_unsigned_edges(self):
        for a,b in ((0xFFFFFFFF,1),(0xFFFFFFFF,100),(0xFFFFFFFF,0x80000000),(0x80000000,0x7FFFFFFF)):
            self.assertEqual(m.remainder_case(a,b)['remainder'],a%b)
    def test_linked_r1(self):
        self.assertEqual(m.remainder_case(0xFFFFFFFF,100,True)['remainder'],95)
    def test_short_stack(self):self.assertEqual(m.remainder_case(4,100,True)['stack_bytes'],4)
    def test_full_stack(self):self.assertEqual(m.remainder_case(101,100,True)['stack_bytes'],8)
    def test_register_preservation(self):
        vm=m.machine();vm.r[4:12]=[0,1,0xFFFFFFFF,0x80000000,7,8,9,10]
        before=vm.r[4:12].copy();vm.r[:2]=[0xFFFFFFFF,3]
        self.assertTrue(vm.run_linked(m.THUNK)['returned']);self.assertEqual(vm.r[4:12],before)
        self.assertEqual(vm.r[13],m.old.SP)
    def test_zero_divisor_boundary(self):
        vm=m.machine();vm.r[:2]=[7,0];r=vm.run_linked(m.TARGET)
        self.assertFalse(r['returned']);self.assertEqual(r['unread_call'],0x081C7FCC)
        self.assertEqual(vm.r[13],m.old.SP-4)
    def test_zero_case_rejected(self):
        with self.assertRaises(ValueError):m.remainder_case(7,0)
    def test_integer_types(self):
        for value in (-1,True,1<<32):
            with self.subTest(value=value),self.assertRaises(ValueError):m.remainder_case(value,100)
    def test_year_zero_day29(self):self.assertEqual(m.date_case(self.raw())['value'],0)
    def test_day30_rejected(self):self.assertEqual(m.date_case(self.raw(0x96,0x30))['value'],256)
    def test_day_zero_retained(self):self.assertEqual(m.date_case(self.raw(day=0))['value'],0)
    def test_invalid_day_bcd(self):
        for value in (0x1A,0xFF):self.assertEqual(m.date_case(self.raw(day=value))['value'],256)
    def test_status_flags(self):
        for status,want in ((0,16),(64,0),(128,48),(192,32)):
            self.assertEqual(m.date_case(self.raw(**{'7':status}))['value'],want)
    def test_hour_limit(self):
        for value,want in ((0x24,0),(0x25,512),(0xFF,512)):
            self.assertEqual(m.date_case(self.raw(**{'4':value}))['value'],want)
    def test_minute_limit(self):
        for value,want in ((0x60,0),(0x61,1024),(0xFF,1024)):
            self.assertEqual(m.date_case(self.raw(**{'5':value}))['value'],want)
    def test_second_limit(self):
        for value,want in ((0x60,0),(0x61,2048),(0xFF,2048)):
            self.assertEqual(m.date_case(self.raw(**{'6':value}))['value'],want)
    def test_weekday_ignored(self):self.assertEqual(m.date_case(self.raw(**{'3':255}))['value'],0)
    def test_combined_flags(self):
        self.assertEqual(m.date_case(self.raw(day=255,**{'4':255,'5':255,'6':255,'7':128}))['value'],256+512+1024+2048+48)
    def test_calendar_call_args(self):
        vm=m.date_probe(self.raw(0x96));self.assertEqual(len(vm.calls),2)
        self.assertEqual(vm.calls[0]['target'],m.THUNK);self.assertEqual(vm.calls[0]['args'][:2],[96,100])
    def test_date_input_readonly(self):
        raw=self.raw();vm=m.date_probe(raw)
        self.assertEqual(bytes(vm.mem[m.old.BUFFER+i] for i in range(8)),raw)
        self.assertEqual(m.old.SP-min(a for a,_,_ in vm.writes),28)
    def test_date_scope_rejected(self):
        for raw in (self.raw(1),self.raw(255),self.raw(**{'1':3}),b''):
            with self.subTest(raw=raw),self.assertRaises(ValueError):m.date_probe(raw)
    def test_budget_enforced_across_links(self):
        vm=m.machine();vm.r[:2]=[0xFFFFFFFF,1]
        with self.assertRaises(ValueError):vm.run_linked(m.THUNK,20)
        self.assertFalse(vm.executing)
    def test_unknown_indirect_rejected(self):
        vm=m.machine();vm.mem[m.POOL]=0xA7;vm.r[:2]=[4,100]
        # 保存窓外のThumb targetへ変え、未知間接辺で停止することを確認。
        vm.mem[m.POOL+1]=0x00
        with self.assertRaises(ValueError):vm.run_linked(m.THUNK)
    def test_arm_target_rejected(self):
        vm=m.machine();vm.mem[m.POOL]&=0xFE
        with self.assertRaises(ValueError):vm.run_linked(m.THUNK)
    def test_corrupt_return_rejected(self):
        vm=m.machine();vm.r[:2]=[4,100];vm.r[14]=0x08011111
        with self.assertRaises(ValueError):vm.run_linked(m.TARGET)
    def test_literal_execution_rejected(self):
        with self.assertRaises(ValueError):m.machine().run_linked(m.POOL)
    def test_rom_write_rejected(self):
        with self.assertRaises(ValueError):m.machine().write(m.TARGET,2,0)
    def test_ror_flags(self):
        for amount in (1,2,3):
            vm=m.LinkedVM({0x1000:bytes.fromhex('e3417047')},[(0x1000,0x1004)])
            vm.r[3]=0x80000001;vm.r[4]=amount;vm.flags=(False,False,False,True)
            self.assertTrue(vm.run_linked(0x1000)['returned'])
            want=((0x80000001>>amount)|(0x80000001<<(32-amount)))&0xFFFFFFFF
            self.assertEqual(vm.r[3],want);self.assertEqual(vm.flags,(bool(want&0x80000000),False,bool(want&0x80000000),True))
    def test_ror_scope_rejected(self):
        vm=m.LinkedVM({0x1000:bytes.fromhex('e3417047')},[(0x1000,0x1004)]);vm.r[4]=32
        with self.assertRaises(ValueError):vm.run_linked(0x1000)
    def test_vector_uniqueness(self):
        rows=m.vectors();self.assertEqual(len(rows),len(set(rows)));self.assertTrue(all(b>0 for a,b in rows))
        self.assertIn((0xFFFFFFFF,0x80000000),rows)
    def test_calendar_domain_complete(self):
        rows=m.calendar_vectors();self.assertEqual(len(rows),len(set(rows)))
        self.assertEqual({m.bcd(r[0]) for r in rows},set(range(0,100,4)))
        for year in range(0,100,4):self.assertEqual({r[2] for r in rows if m.bcd(r[0])==year},set(range(256)))

    def saved(self):
        import hashlib
        raw=m.CODE+bytes(512-len(m.CODE))
        return {'analysis':{'new_windows':[{'start':m.TARGET,'end':m.TARGET+512,
            'hex':raw.hex(),'identity':{'size':512,'sha256':hashlib.sha256(raw).hexdigest()}}]}}
    def test_saved_bytes_bound(self):self.assertEqual(m.bound_window(self.saved())[:192],m.CODE)
    def test_saved_opcode_rejected(self):
        import hashlib
        value=self.saved();row=value['analysis']['new_windows'][0];raw=bytearray.fromhex(row['hex']);raw[0]^=1
        row['hex']=raw.hex();row['identity']['sha256']=hashlib.sha256(raw).hexdigest()
        with self.assertRaises(ValueError):m.bound_window(value)
    def test_saved_hash_rejected(self):
        value=self.saved();value['analysis']['new_windows'][0]['identity']['sha256']='0'*64
        with self.assertRaises(ValueError):m.bound_window(value)
    def test_saved_extent_rejected(self):
        value=self.saved();value['analysis']['new_windows'][0]['end']-=2
        with self.assertRaises(ValueError):m.bound_window(value)

if __name__=='__main__':unittest.main()
