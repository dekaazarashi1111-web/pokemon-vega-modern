"""PLA1新規境界だけ。受入済みPLC2/進化/孵化/通常level試験を呼ばない。"""
from __future__ import annotations
import copy
import ctypes as c
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from tools import pr16_learnset_supply as m
ROOT=Path(__file__).resolve().parents[1]
U16=c.c_uint16
U8=c.c_uint8
class View(c.Structure):
    _fields_=[('bytes',c.POINTER(U8)),('count',U16),('owner',U16)]


def fixture_rows():
    policies=bytearray([2]*m.COUNT)
    rows={(sid,f):None for sid in range(m.COUNT) for f in m.FAMILIES}
    for sid,machine,tutor in ((1,(),(156,237,92)),(13,(34,36,63,67,129),()),
        (151,tuple(range(1,132)),()),(1029,(63,76,80,104,118,129,219,263,318,347,420,682),()),
        (1670,(67,63,36,34,129),(237,156,92))):
        policies[sid]=1;rows[sid,'machine']=machine;rows[sid,'tutor']=tutor
    return rows,bytes(policies)


def library(directory):
    lib=Path(directory)/'supply.so'
    subprocess.run(['cc','-std=c11','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',
        '-Isrc/modernization','-Itests/fixtures','src/modernization/pr16_learnset_supply.c',
        'src/modernization/pr16_learnset_supply_game.c','tests/fixtures/pr16_learnset_supply_fixture.c',
        '-o',str(lib)],cwd=ROOT,check=True,capture_output=True)
    dll=c.CDLL(str(lib))
    dll.Pr16SupplyDecode.argtypes=[c.POINTER(U8),c.c_uint32,U16,U8,c.POINTER(U16),U16,c.POINTER(U16)]
    dll.Pr16SupplyDecode.restype=U8
    dll.Pr16SupplyPage.argtypes=[c.POINTER(U16),U16,c.POINTER(U16),U8,U8,c.POINTER(U16),U8]
    dll.Pr16SupplyPage.restype=U8
    dll.Pr16SupplyPageCount.argtypes=[U16];dll.Pr16SupplyPageCount.restype=U8
    dll.Pr16SupplyTutorBit.argtypes=[c.POINTER(View),U16,U8];dll.Pr16SupplyTutorBit.restype=U8
    dll.SupplyFixtureSetup.argtypes=[c.POINTER(U8),c.c_uint32,U8,U8,U8,c.POINTER(U8)]
    dll.Pr16_GameSupplyTutorSlot.argtypes=[c.c_void_p,U8];dll.Pr16_GameSupplyTutorSlot.restype=U8
    dll.Pr16_GameSupplyArchiveRowCount.argtypes=[c.c_void_p,U8];dll.Pr16_GameSupplyArchiveRowCount.restype=U16
    dll.Pr16_GameSupplyRelearner.argtypes=[c.c_void_p,c.POINTER(U16)];dll.Pr16_GameSupplyRelearner.restype=U8
    return dll


class SupplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,cls.policies=fixture_rows();cls.image,cls.receipt=m.compose(cls.rows,cls.policies)
        cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup)
        cls.dll=library(cls.temp.name)

    def decode(self,sid,family,raw=None,capacity=160):
        raw=self.image if raw is None else raw
        image=(U8*len(raw)).from_buffer_copy(raw)
        out=(U16*162)(*([0xbeef]*162));count=U16(0xcafe)
        result=self.dll.Pr16SupplyDecode(image,len(raw),sid,family,out,capacity,c.byref(count))
        self.assertEqual(bytes(image),raw)
        return result,count.value,list(out)

    def page(self,seq,known=(0,0,0,0),mode=3,gate=1,capacity=40):
        archive=(U16*max(1,len(seq)))(*seq);k=(U16*4)(*known);out=(U16*42)(*([0xbeef]*42))
        result=self.dll.Pr16SupplyPage(archive,len(seq),k,mode,gate,out,capacity)
        self.assertEqual(list(archive)[:len(seq)],list(seq));self.assertEqual(list(k),list(known))
        return result,list(out)

    def game(self,sid=1029,mode=3,gate=1,policy=1,egg=0,known=(0,0,0,0)):
        image=(U8*len(self.image)).from_buffer_copy(self.image);bits=(U8*16)();bits[0]=1;bits[7]=128
        self.dll.SupplyFixtureSetup(image,len(image),mode,gate,policy,bits)
        mon=(U8*100)(*([0xa5]*100));mon[0]=sid&255;mon[1]=sid>>8;mon[2]=egg
        for i,v in enumerate(known):mon[4+i*2]=v&255;mon[5+i*2]=v>>8
        return mon,image

    def test_roundtrip_and_deterministic_rows(self):
        self.assertEqual(m.validate(self.image),self.rows)
        reverse=dict(reversed(list(self.rows.items())))
        self.assertEqual(m.compose(reverse,self.policies),(self.image,self.receipt))
    def test_order_conflicts_not_sorted_or_flattened(self):
        self.assertGreater(self.receipt['templates'],1)
        self.assertEqual(m.validate(self.image)[1670,'machine'],(67,63,36,34,129))
    def test_missing_owner_rejected(self):
        rows=dict(self.rows);rows.pop((1,'machine'))
        with self.assertRaises(ValueError):m.compose(rows,self.policies)
    def test_nonlearning_not_empty_lookup(self):
        rows=dict(self.rows);rows[887,'machine']=()
        with self.assertRaises(ValueError):m.compose(rows,self.policies)
    def test_duplicate_source_rejected(self):
        rows=dict(self.rows);rows[1,'machine']=(34,34)
        with self.assertRaises(ValueError):m.compose(rows,self.policies)
    def test_unimplemented_move_rejected(self):
        rows=dict(self.rows);rows[1,'machine']=(1063,)
        with self.assertRaises(ValueError):m.compose(rows,self.policies)
    def test_source_capacity_rejected(self):
        rows=dict(self.rows);rows[1,'tutor']=tuple(range(1,42))
        with self.assertRaises(ValueError):m.compose(rows,self.policies)
    def test_truncation_and_trailing_bytes_rejected(self):
        for raw in (self.image[:31],self.image[:-1],self.image+b'\0'):
            with self.assertRaises(ValueError):m.validate(raw)
    def test_wrong_header_rejected(self):
        for at in (0,4,6,8,10,11,12,16,24,28):
            raw=bytearray(self.image);raw[at]^=128
            with self.assertRaises(ValueError):m.validate(raw)
    def test_middle_of_record_directory_rejected(self):
        raw=bytearray(self.image);at=m.DIRECTORY+1029*4;value=struct.unpack_from('<H',raw,at)[0]
        struct.pack_into('<H',raw,at,value+1)
        with self.assertRaises(ValueError):m.validate(raw)
    def test_self_referencing_record_rejected(self):
        raw=bytearray(self.image);at=struct.unpack_from('<H',raw,m.DIRECTORY+1029*4)[0]
        struct.pack_into('<H',raw,at,at)
        with self.assertRaises(ValueError):m.validate(raw)
        self.assertEqual(self.decode(1029,0,raw),(0,0xcafe,[0xbeef]*162))
    def test_c_exact_all_fixture_owners(self):
        for sid in (1,13,151,1029,1670):
            for family in range(2):
                expect=self.rows[sid,m.FAMILIES[family]]
                self.assertEqual(self.decode(sid,family),(1,len(expect),list(expect)+[0xbeef]*(162-len(expect))))
    def test_c_identity_and_invalid_owner_no_writes(self):
        for sid,fam in ((0,0),(887,0),(1671,0),(65535,1),(1,2)):
            self.assertEqual(self.decode(sid,fam),(0,0xcafe,[0xbeef]*162))
    def test_c_capacity_is_transactional(self):
        self.assertEqual(self.decode(151,0,capacity=130),(0,0xcafe,[0xbeef]*162))
    def test_c_bad_header_no_writes(self):
        raw=bytearray(self.image);raw[0]=0
        self.assertEqual(self.decode(1029,0,raw),(0,0xcafe,[0xbeef]*162))
    def test_c_invalid_template_move_no_writes(self):
        raw=bytearray(self.image);at=struct.unpack_from('<H',raw,m.DIRECTORY+1029*4)[0];ti=raw[at+2]
        start=struct.unpack_from('<H',raw,m.TEMPLATES+ti*4)[0];struct.pack_into('<H',raw,start,1063)
        self.assertEqual(self.decode(1029,0,raw),(0,0xcafe,[0xbeef]*162))
    def test_page_four_boundaries_131(self):
        seq=tuple(range(1,132))
        for page in range(4):
            expect=list(seq[page*40:(page+1)*40]);self.assertEqual(self.page(seq,mode=3+page),(len(expect),expect+[0xbeef]*(42-len(expect))))
    def test_known_filter_does_not_shift_pages(self):
        seq=tuple(range(1,82));known=(1,2,40,41)
        self.assertEqual(self.page(seq,known,4),(39,list(range(42,81))+[0xbeef]*3))
    def test_probe_and_tutor_mode(self):
        self.assertEqual(self.page((1,2,3,4,5),known=(1,2,3,4),mode=2),(1,[5]+[0xbeef]*41))
        self.assertEqual(self.page((92,156),known=(92,0,0,0),mode=7),(1,[156]+[0xbeef]*41))
    def test_locked_archive_never_lists_moves(self):
        for mode in range(2,8):self.assertEqual(self.page((63,76),mode=mode,gate=0),(0,[0xbeef]*42))
    def test_invalid_mode_capacity_and_tutor_overflow(self):
        for mode in (0,1,8,255):self.assertEqual(self.page((63,76),mode=mode),(0,[0xbeef]*42))
        self.assertEqual(self.page((63,76),capacity=1),(0,[0xbeef]*42))
        self.assertEqual(self.page(tuple(range(1,42)),mode=7),(0,[0xbeef]*42))
    def test_page_invalid_and_duplicate_ids(self):
        for seq in ((0,),(1063,),(34,34)):
            self.assertEqual(self.page(seq),(0,[0xbeef]*42))
    def test_page_counts(self):
        for count,want in ((0,0),(1,1),(40,1),(41,2),(80,2),(120,3),(131,4),(160,4),(161,0)):
            self.assertEqual(self.dll.Pr16SupplyPageCount(count),want)
    def test_tutor_bits_and_boundaries(self):
        data=(U8*16)();data[0]=1;data[3]=128;data[4]=1;data[7]=128;view=View(data,64,13)
        for i in range(256):self.assertEqual(self.dll.Pr16SupplyTutorBit(c.byref(view),13,i),int(i in (0,31,32,63)))
    def test_tutor_owner_and_padding_fail_closed(self):
        data=(U8*16)();data[0]=1;view=View(data,64,13)
        self.assertEqual(self.dll.Pr16SupplyTutorBit(c.byref(view),14,0),0)
        data[8]=1;self.assertEqual(self.dll.Pr16SupplyTutorBit(c.byref(view),13,0),0)
        view.count=63;self.assertEqual(self.dll.Pr16SupplyTutorBit(c.byref(view),13,0),0)
    def test_adapter_floette_archive_data_and_saved_bytes(self):
        mon,image=self.game(known=(63,76,0,0));before=bytes(mon);out=(U16*42)(*([0xbeef]*42))
        self.assertEqual(self.dll.Pr16_GameSupplyArchiveRowCount(mon,0),12)
        self.assertEqual(self.dll.Pr16_GameSupplyRelearner(mon,out),10)
        self.assertEqual(list(out),[80,104,118,129,219,263,318,347,420,682]+[0xbeef]*32)
        self.assertEqual(bytes(mon),before);self.assertEqual(bytes(image),self.image)
        self.assertEqual(self.dll.SupplyFixtureParentCalls(),0)
    def test_adapter_gate_egg_and_nonlearning(self):
        for args in ({'gate':0},{'egg':1},{'policy':4},{'sid':887},{'sid':1671},{'mode':8}):
            mon,image=self.game(**args);before=bytes(mon);out=(U16*42)(*([0xbeef]*42))
            self.assertEqual(self.dll.Pr16_GameSupplyRelearner(mon,out),0)
            self.assertEqual(list(out),[0xbeef]*42);self.assertEqual(bytes(mon),before)
            self.assertEqual(self.dll.SupplyFixtureParentCalls(),0)
    def test_adapter_normal_and_egg_delegate_only(self):
        for mode in (0,1):
            mon,image=self.game(mode=mode,gate=0);out=(U16*42)(*([0xbeef]*42))
            self.assertEqual(self.dll.Pr16_GameSupplyRelearner(mon,out),1)
            self.assertEqual(list(out),[777]+[0xbeef]*41);self.assertEqual(self.dll.SupplyFixtureParentCalls(),1)
    def test_adapter_table_tutor_only(self):
        mon,image=self.game(sid=13);before=bytes(mon)
        for slot,want in ((0,1),(1,0),(63,1),(64,0),(255,0)):
            self.assertEqual(self.dll.Pr16_GameSupplyTutorSlot(mon,slot),want)
        self.assertEqual(bytes(mon),before)
        mon,image=self.game(sid=13,egg=1);self.assertEqual(self.dll.Pr16_GameSupplyTutorSlot(mon,0),0)
    def test_adapter_null_inputs(self):
        mon,image=self.game();out=(U16*42)(*([0xbeef]*42))
        self.assertEqual(self.dll.Pr16_GameSupplyRelearner(None,out),0)
        self.assertEqual(self.dll.Pr16_GameSupplyRelearner(mon,None),0)
        self.assertEqual(self.dll.Pr16_GameSupplyTutorSlot(None,0),0)

if __name__=='__main__':unittest.main()
