"""New creation/level progression only. Never reruns accepted runtime tests."""
import ctypes as c
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
U8P = c.POINTER(c.c_uint8)
class View(c.Structure):
    _fields_ = [('bytes', U8P), ('count', c.c_uint16), ('owner', c.c_uint16)]
class Mon(c.Structure):
    _fields_ = [('species', c.c_uint16), ('level', c.c_uint8), ('egg', c.c_uint8),
                ('moves', c.c_uint16 * 4), ('pp', c.c_uint8 * 4),
                ('bonus', c.c_uint8), ('opaque', c.c_uint8 * 15)]

def library(destination):
    output = Path(destination) / 'progress.so'
    sources = ['src/modernization/pr16_learnset_owner.c', 'src/modernization/pr16_learnset_runtime.c',
               'src/modernization/pr16_learnset_progress.c', 'src/modernization/pr16_learnset_progress_game.c',
               'tests/fixtures/pr16_learnset_progress_fixture.c']
    subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                    '-I'+str(ROOT/'src/modernization'), '-I'+str(ROOT/'tests/fixtures'),
                    *(str(ROOT/p) for p in sources), '-o', str(output)], check=True)
    dll = c.CDLL(str(output))
    dll.Pr16ProgressInitial.argtypes = [c.POINTER(View), c.c_uint8, c.POINTER(c.c_uint16), c.c_uint8]
    dll.Pr16ProgressInitial.restype = c.c_uint8
    dll.Pr16ProgressNext.argtypes = [c.POINTER(View), c.c_uint8, c.c_uint8, U8P]
    dll.Pr16ProgressNext.restype = c.c_uint16
    dll.Pr16_GameGiveBoxMonInitialMoveset.argtypes = [c.POINTER(Mon)]
    dll.Pr16_GameGiveBoxMonInitialMoveset.restype = None
    dll.Pr16_GameMonTryLearningNewMove.argtypes = [c.POINTER(Mon), c.c_uint8]
    dll.Pr16_GameMonTryLearningNewMove.restype = c.c_uint16
    return dll

def make_image(pairs):
    machine = (15072 + 3*(len(pairs)+1) + 3) & ~3
    raw = bytearray(machine + 1483*16)
    raw[:32] = struct.pack('<4sHHIIIIII', b'PLR1', 1, 1671, 32, 1704, 15072, machine, len(raw), 0)
    raw[32:1703] = bytes([2])*1671
    for sid in range(1671): struct.pack_into('<IHH', raw, 1704+sid*8, 0xFFFFFFFF, 0, 65535)
    raw[42] = 1
    struct.pack_into('<IHH', raw, 1784, 15072, len(pairs), 0)
    for i,(move,lv) in enumerate([*pairs, (0,255)]): struct.pack_into('<HB', raw, 15072+i*3, move, lv)
    return raw

class ProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(); cls.dll = library(cls.temp.name)
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()
    def setUp(self):
        self.pairs = [(33,1),(81,1),(535,9),(45,9),(85,10),(86,20)]
        self.set_view(self.pairs)
        self.out = (c.c_uint16*6)(*([0xDEAD]*6)); self.cursor=c.c_uint8(0)
        self.mon = Mon(10,9,0,(c.c_uint16*4)(),(c.c_uint8*4)(),0,(c.c_uint8*15)(*range(15)))
        self.bind()
    def set_view(self,pairs):
        raw = b''.join(struct.pack('<HB',*p) for p in pairs) or bytes(3)
        self.buf=(c.c_uint8*len(raw)).from_buffer_copy(raw); self.view=View(self.buf,len(pairs),10)
    def bind(self):
        raw=make_image(self.pairs);self.image=(c.c_uint8*len(raw)).from_buffer_copy(raw)
        c.c_void_p.in_dll(self.dll,'pr16_test_image').value=c.addressof(self.image)
        c.c_uint32.in_dll(self.dll,'pr16_test_image_size').value=len(raw)
        self.gc=c.c_uint8.in_dll(self.dll,'pr16_test_cursor');self.gc.value=0
        self.pending=c.c_uint16.in_dll(self.dll,'pr16_test_pending');self.pending.value=0xDEAD
    def initial(self,lv=9,cap=4): return self.dll.Pr16ProgressInitial(c.byref(self.view),lv,self.out,cap)
    def next(self,lv=9,first=0): return self.dll.Pr16ProgressNext(c.byref(self.view),lv,first,c.byref(self.cursor))
    def test_initial_level_one(self):
        self.assertEqual(self.initial(1),2);self.assertEqual(list(self.out),[33,81]+[0xDEAD]*4)
    def test_initial_last_four_raw_rows(self):
        self.assertEqual(self.initial(100),4);self.assertEqual(list(self.out),[535,45,85,86,0xDEAD,0xDEAD])
    def test_initial_excludes_future(self):
        self.assertEqual(self.initial(8),2);self.assertEqual(list(self.out)[:2],[33,81])
    def test_initial_duplicates_not_deduplicated_before_window(self):
        self.set_view([(33,1),(81,1),(45,2),(45,2),(85,3)])
        self.assertEqual(self.initial(),4);self.assertEqual(list(self.out)[:4],[81,45,45,85])
    def test_capacity_failure_atomic(self):
        self.assertEqual(self.initial(cap=3),0);self.assertEqual(list(self.out),[0xDEAD]*6)
    def test_empty_owned_span(self):
        self.set_view([]);self.assertEqual(self.initial(),0);self.assertEqual(self.next(first=1),0);self.assertEqual(self.cursor.value,255)
    def test_initial_null_output(self): self.assertEqual(self.dll.Pr16ProgressInitial(c.byref(self.view),9,None,4),0)
    def test_invalid_levels_unchanged(self):
        for lv in (0,101,255):
            self.assertEqual(self.initial(lv),0);self.assertEqual(self.next(lv,1),0)
        self.assertEqual(list(self.out),[0xDEAD]*6);self.assertEqual(self.cursor.value,0)
    def test_malformed_rows_reject_before_write(self):
        for p in ((0,1),(1063,1),(65535,1),(33,0),(33,101)):
            self.set_view([(33,1),p]);self.assertEqual(self.initial(),0);self.assertEqual(self.next(first=1),0)
        self.assertEqual(list(self.out),[0xDEAD]*6)
    def test_nonmonotonic_reject_without_sort(self):
        self.set_view([(33,9),(81,1)]);self.assertEqual(self.initial(),0);self.assertEqual(self.next(first=1),0)
    def test_owner_view_and_count_bounds(self):
        for owner,count in ((1671,6),(65535,6),(10,41)):
            self.view.owner=owner;self.view.count=count;self.assertEqual(self.initial(),0);self.assertEqual(self.next(first=1),0)
    def test_null_view(self):
        self.assertEqual(self.dll.Pr16ProgressInitial(None,9,self.out,4),0)
        self.assertEqual(self.dll.Pr16ProgressNext(None,9,1,c.byref(self.cursor)),0)
    def test_null_span(self):
        self.view.bytes=U8P();self.assertEqual(self.initial(),0);self.assertEqual(self.next(first=1),0)
    def test_null_cursor(self): self.assertEqual(self.dll.Pr16ProgressNext(c.byref(self.view),9,1,None),0)
    def test_same_level_sequence(self):
        self.assertEqual([self.next(first=1),self.next(),self.next(),self.next()],[535,45,0,0])
        self.assertEqual(self.cursor.value,255)
    def test_gap_no_grant(self): self.assertEqual(self.next(8,1),0);self.assertEqual(self.cursor.value,255)
    def test_cursor_reset_after_end(self):
        self.cursor.value=255;self.assertEqual(self.next(),0);self.assertEqual(self.next(1,1),33)
    def test_cursor_never_wraps(self):
        for value in (40,100,254,255): self.cursor.value=value;self.assertEqual(self.next(),0);self.assertEqual(self.cursor.value,255)
    def test_full_capacity_forty(self):
        self.set_view([(i+1,100) for i in range(40)])
        self.assertEqual(self.initial(100),4);self.assertEqual(list(self.out)[:4],[37,38,39,40])
        self.assertEqual([self.next(100,i==0) for i in range(41)],list(range(1,41))+[0])
    def test_game_initial_fresh_mon(self):
        self.dll.Pr16_GameGiveBoxMonInitialMoveset(c.byref(self.mon))
        self.assertEqual(list(self.mon.moves),[33,81,535,45]);self.assertEqual(list(self.mon.pp),[34,2,16,6])
        self.assertEqual(list(self.mon.opaque),list(range(15)))
    def test_game_existing_partial_mon_unchanged(self):
        self.mon.moves[2]=999;self.mon.pp[2]=17;self.mon.bonus=229;before=bytes(self.mon)
        self.dll.Pr16_GameGiveBoxMonInitialMoveset(c.byref(self.mon));self.assertEqual(bytes(self.mon),before)
    def test_game_existing_full_mon_unchanged(self):
        self.mon.moves[:]=[33,45,85,182];self.mon.pp[:]=[3,4,5,6];self.mon.bonus=229;before=bytes(self.mon)
        self.dll.Pr16_GameGiveBoxMonInitialMoveset(c.byref(self.mon));self.assertEqual(bytes(self.mon),before)
    def test_game_identity_owners_preserved(self):
        for policy in range(2,8):
            self.image[43]=policy;self.mon.species=11;before=bytes(self.mon)
            self.dll.Pr16_GameGiveBoxMonInitialMoveset(c.byref(self.mon))
            self.assertEqual(self.dll.Pr16_GameMonTryLearningNewMove(c.byref(self.mon),1),0)
            self.assertEqual(bytes(self.mon),before);self.assertEqual(self.pending.value,0xDEAD)
    def test_game_invalid_owner_preserved(self):
        self.mon.species=1671;before=bytes(self.mon)
        self.dll.Pr16_GameGiveBoxMonInitialMoveset(c.byref(self.mon));self.assertEqual(bytes(self.mon),before)
        self.assertEqual(self.dll.Pr16_GameMonTryLearningNewMove(c.byref(self.mon),1),0)
    def test_game_egg_does_not_level_learn(self):
        self.mon.egg=1;before=bytes(self.mon)
        self.assertEqual(self.dll.Pr16_GameMonTryLearningNewMove(c.byref(self.mon),1),0);self.assertEqual(bytes(self.mon),before)
    def test_game_full_slots_reports_pending_without_mutation(self):
        self.mon.moves[:]=[33,81,85,86];before=bytes(self.mon)
        self.assertEqual(self.dll.Pr16_GameMonTryLearningNewMove(c.byref(self.mon),1),65535)
        self.assertEqual(bytes(self.mon),before);self.assertEqual(self.pending.value,535)
        self.assertEqual(self.dll.Pr16_GameMonTryLearningNewMove(c.byref(self.mon),0),65535)
        self.assertEqual(self.pending.value,45);self.assertEqual(self.dll.Pr16_GameMonTryLearningNewMove(c.byref(self.mon),0),0)
    def test_game_duplicate_advances_cursor(self):
        self.mon.moves[0]=535;self.mon.pp[0]=3
        self.assertEqual(self.dll.Pr16_GameMonTryLearningNewMove(c.byref(self.mon),1),65534)
        self.assertEqual(self.dll.Pr16_GameMonTryLearningNewMove(c.byref(self.mon),0),45)
        self.assertEqual(list(self.mon.moves),[535,45,0,0]);self.assertEqual(self.mon.pp[0],3)
    def test_game_null_mon(self):
        self.dll.Pr16_GameGiveBoxMonInitialMoveset(None);self.assertEqual(self.dll.Pr16_GameMonTryLearningNewMove(None,1),0)
    def test_game_pending_retained_on_gap(self):
        self.mon.level=8;self.assertEqual(self.dll.Pr16_GameMonTryLearningNewMove(c.byref(self.mon),1),0)
        self.assertEqual(self.pending.value,0xDEAD)
    def test_game_no_initial_cursor_write(self):
        self.gc.value=19;self.dll.Pr16_GameGiveBoxMonInitialMoveset(c.byref(self.mon));self.assertEqual(self.gc.value,19)

if __name__ == '__main__': unittest.main()
