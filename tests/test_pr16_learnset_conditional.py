"""新規PLC1の境界・owner分離・候補順序のみを検証する。旧受入試験は呼ばない。"""
from __future__ import annotations
import ctypes as c
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
U8 = c.POINTER(c.c_uint8)
U16 = c.POINTER(c.c_uint16)


class View(c.Structure):
    _fields_ = [('bytes', U8), ('count', c.c_uint16), ('owner', c.c_uint16)]


def library(directory):
    path = Path(directory) / 'conditional.so'
    subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
        str(ROOT/'src/modernization/pr16_learnset_conditional.c'),
        str(ROOT/'src/modernization/pr16_learnset_owner.c'), '-o', str(path)], check=True)
    dll = c.CDLL(str(path))
    dll.Pr16ReadLearnsetConditional.argtypes = [U8,c.c_uint32,c.c_uint16,c.c_uint8,c.POINTER(View)]
    dll.Pr16ReadLearnsetConditional.restype = c.c_uint8
    dll.Pr16ConditionalList.argtypes = [c.POINTER(View),U16,c.c_uint8,U16,c.c_uint16]
    dll.Pr16ConditionalList.restype = c.c_uint8
    dll.Pr16ConditionalEvolutionNext.argtypes = [c.POINTER(View),c.POINTER(View),c.c_uint8,c.c_uint8,U8]
    dll.Pr16ConditionalEvolutionNext.restype = c.c_uint16
    dll.Pr16ConditionalReminder.argtypes = [c.POINTER(View),c.POINTER(View),c.POINTER(View),c.c_uint8,U16,U16,c.c_uint16]
    dll.Pr16ConditionalReminder.restype = c.c_uint8
    dll.Pr16ConditionalTutorAllowed.argtypes = [U8,c.c_uint32,c.c_uint16,c.c_uint16]
    dll.Pr16ConditionalTutorAllowed.restype = c.c_uint8
    return dll


def view(moves, owner=1, levels=False):
    raw = b''.join(struct.pack('<HB', *v) if levels else struct.pack('<H', v) for v in moves)
    buffer = (c.c_uint8 * max(1, len(raw)))()
    buffer[:len(raw)] = raw
    value = View(buffer, len(moves), owner)
    value.keepalive = buffer
    return value


def image():
    raw = bytearray(68544 + 16)
    struct.pack_into('<4sHHIIIIII', raw, 0, b'PLC1',1,1671,32,1704,68544,len(raw),0x1c3,0)
    raw[32:1703] = bytes([2]) * 1671
    for sid in range(1671):
        for col, cid in enumerate((0,1,6,7,8)):
            struct.pack_into('<IHH',raw,1704+(sid*5+col)*8,0xffffffff,0,(sid<<4)|cid)
    raw[33] = 1
    for col,cid in enumerate((0,1,6,7,8)):
        struct.pack_into('<IHH',raw,1704+(5+col)*8,68544,64 if cid==8 else 0,(1<<4)|cid)
    return raw


class ConditionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dll = library(cls.tmp.name)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def read(self, raw=None, species=1, consumer=1, size=None):
        raw = image() if raw is None else raw
        self.buf = (c.c_uint8*len(raw)).from_buffer_copy(raw)
        out = View(c.cast(c.c_void_p(1),U8),999,999)
        result = self.dll.Pr16ReadLearnsetConditional(self.buf,len(raw) if size is None else size,species,consumer,c.byref(out))
        self.assertEqual(bytes(self.buf), bytes(raw))
        return result,out

    def invalid(self, raw=None, **kw):
        code,out = self.read(raw,**kw)
        self.assertEqual((code,out.count,out.owner,bool(out.bytes)),(0,0,65535,False))

    def test_empty_explicit_owner(self):
        code,out=self.read();self.assertEqual((code,out.count,out.owner),(1,0,1))
    def test_identity_is_not_empty_owner(self):
        code,out=self.read(species=0);self.assertEqual((code,out.count,out.owner,bool(out.bytes)),(2,0,0,False))
    def test_battle_identity_carries(self):
        for policy in (5,6,7):
            raw=image();raw[32]=policy
            code,out=self.read(raw,species=0);self.assertEqual((code,out.owner,bool(out.bytes)),(3,0,False))
    def test_no_species_fallback(self): self.invalid(species=1671)
    def test_unknown_consumer(self): self.invalid(consumer=9)
    def test_normal_consumer_not_routed(self):
        for cid in (3,4):self.assertEqual(self.read(consumer=cid)[0],5)
    def test_carry_and_form_condition_not_granted(self):
        for cid in (2,5):
            code,out=self.read(consumer=cid);self.assertEqual((code,bool(out.bytes)),(4,False))
    def test_bad_header_fields(self):
        for at in (0,4,6,8,12,16,20,24,28):
            raw=image();raw[at]^=1
            with self.subTest(at=at):self.invalid(raw)
    def test_truncated_header_and_index(self):
        for size in (0,4,31,32,1703,1704,68543):self.invalid(size=size)
    def test_invalid_policy(self):
        for policy in (0,8,255):
            raw=image();raw[33]=policy;self.invalid(raw)
    def test_mismatched_owner_consumer_tag(self):
        raw=image();raw[1704+6*8+6]^=1;self.invalid(raw)
    def test_identity_span_leak_rejected(self):
        raw=image();struct.pack_into('<I',raw,1704+8,68544);self.invalid(raw,species=0)
    def test_span_bounds_alignment_and_overflow(self):
        for at,count in ((0,1),(68543,1),(68545,1),(len(image()),1),(0xfffffffe,1),(68544,51)):
            raw=image();struct.pack_into('<IH',raw,1704+6*8,at,count);self.invalid(raw)
    def test_bad_move_values(self):
        for move in (0,1063,65535,20001):
            raw=image();struct.pack_into('<H',raw,68544,move);struct.pack_into('<H',raw,1704+6*8+4,1);self.invalid(raw)
    def test_valid_move_and_count(self):
        raw=image();struct.pack_into('<HH',raw,68544,1062,1);struct.pack_into('<H',raw,1704+6*8+4,2)
        code,out=self.read(raw);self.assertEqual((code,out.count,out.owner),(1,2,1));self.assertEqual(c.string_at(out.bytes,4),struct.pack('<HH',1062,1))
    def test_tutor_existing_bits_only(self):
        raw=image();raw[68544]=1;raw[68544+7]=128;self.read(raw,consumer=8)
        for bit in range(66):self.assertEqual(self.dll.Pr16ConditionalTutorAllowed(self.buf,len(raw),1,bit),int(bit in (0,63)))
    def test_tutor_upper_bits_rejected(self):
        for at in range(8,16):
            raw=image();raw[68544+at]=1;self.invalid(raw,consumer=8)
    def test_tutor_wrong_stride_rejected(self):
        raw=image();struct.pack_into('<H',raw,1704+9*8+4,128);self.invalid(raw,consumer=8)
    def test_null_pointers_rejected(self):
        out=View();self.assertEqual(self.dll.Pr16ReadLearnsetConditional(None,0,1,1,c.byref(out)),0)
        self.assertEqual(self.dll.Pr16ReadLearnsetConditional(None,0,1,1,None),0)

    def listing(self, values, known=(), capacity=50):
        v=view(values);k=(c.c_uint16*max(1,len(known)))(*known);out=(c.c_uint16*52)(*([0xbeef]*52))
        n=self.dll.Pr16ConditionalList(c.byref(v),k,len(known),out,capacity)
        return n,list(out)
    def test_list_deduplicates_and_excludes_known(self):
        n,out=self.listing([1,2,1,3],(2,));self.assertEqual((n,out[:4]),(2,[1,3,0xbeef,0xbeef]))
    def test_list_capacity_all_or_nothing(self):
        n,out=self.listing([1,2,3],capacity=2);self.assertEqual((n,out),(0,[0xbeef]*52))
    def test_list_no_truncation_at_fifty(self):
        n,out=self.listing(list(range(1,51)));self.assertEqual(n,50);self.assertEqual(out[50:],[0xbeef]*2)
    def test_list_invalid_late_move_leaves_output(self):
        n,out=self.listing([1,2,1063]);self.assertEqual((n,out),(0,[0xbeef]*52))
    def test_list_excess_known_rejected(self):
        n,out=self.listing([6],(1,2,3,4,5));self.assertEqual((n,out),(0,[0xbeef]*52))

    def next_moves(self, evo, levels, level=50, owner=1):
        a=view(evo);b=view(levels,owner=owner,levels=True);cursor=c.c_uint8(233);result=[]
        for step in range(100):
            value=self.dll.Pr16ConditionalEvolutionNext(c.byref(a),c.byref(b),level,step==0,c.byref(cursor))
            if not value:break
            result.append(value)
        else:self.fail('cursor did not terminate')
        return result,cursor.value
    def test_evolution_then_matching_level(self):
        self.assertEqual(self.next_moves([10,20],[(1,1),(30,50),(40,51),(50,50)]),([10,20,30,50],6))
    def test_evolution_no_level_match(self):self.assertEqual(self.next_moves([10],[(1,1)]),([10],2))
    def test_evolution_empty(self):self.assertEqual(self.next_moves([],[]),([],0))
    def test_evolution_donor_owner_rejected(self):self.assertEqual(self.next_moves([1],[(2,50)],owner=2),([],233))
    def test_evolution_invalid_level_rejected(self):
        for level in (0,101):self.assertEqual(self.next_moves([1],[],level=level),([],233))
    def test_evolution_invalid_late_entry_all_or_nothing(self):self.assertEqual(self.next_moves([1,1063],[]),([],233))
    def test_evolution_duplicate_progress_not_loop(self):self.assertEqual(self.next_moves([10],[(10,50),(20,50)])[0],[10,10,20])
    def test_evolution_exhausted_cursor_stays_bounded(self):
        a=view([1]);b=view([],levels=True);cursor=c.c_uint8(255)
        self.assertEqual(self.dll.Pr16ConditionalEvolutionNext(c.byref(a),c.byref(b),50,0,c.byref(cursor)),0);self.assertEqual(cursor.value,1)

    def reminder(self,evo,levels,extra,level=50,known=(0,0,0,0),capacity=40,owner=1):
        a=view(evo);b=view(levels,levels=True);d=view(extra,owner=owner);k=(c.c_uint16*4)(*known);out=(c.c_uint16*42)(*([0xbeef]*42))
        n=self.dll.Pr16ConditionalReminder(c.byref(a),c.byref(b),c.byref(d),level,k,out,capacity)
        return n,list(out)
    def test_reminder_dedup_known_level_filter(self):
        n,out=self.reminder([1,2],[(2,1),(3,50),(4,51)],[3,5],known=(1,0,0,0));self.assertEqual((n,out[:5]),(3,[2,3,5,0xbeef,0xbeef]))
    def test_reminder_ignore_level_is_explicit(self):
        self.assertEqual(self.reminder([],[(1,100)],[],level=50)[0],0);self.assertEqual(self.reminder([],[(1,100)],[],level=100)[0],1)
    def test_reminder_capacity_atomic(self):
        n,out=self.reminder([1],[(2,50)],[3],capacity=2);self.assertEqual((n,out),(0,[0xbeef]*42))
    def test_reminder_forty_boundary(self):
        n,out=self.reminder([],[(x,50) for x in range(1,41)],[]);self.assertEqual(n,40);self.assertEqual(out[40:],[0xbeef]*2)
    def test_reminder_overflow_atomic(self):
        n,out=self.reminder([41],[(x,50) for x in range(1,41)],[]);self.assertEqual((n,out),(0,[0xbeef]*42))
    def test_reminder_donor_rejected(self):
        n,out=self.reminder([1],[],[2],owner=2);self.assertEqual((n,out),(0,[0xbeef]*42))
    def test_reminder_invalid_late_move_rejected(self):
        n,out=self.reminder([1],[],[1063]);self.assertEqual((n,out),(0,[0xbeef]*42))
    def test_reminder_invalid_level_rejected(self):
        for level in (0,101):self.assertEqual(self.reminder([1],[],[],level=level)[0],0)
    def test_reminder_invalid_level_row_rejected(self):self.assertEqual(self.reminder([1],[(2,0)],[])[0],0)


if __name__ == '__main__': unittest.main()
