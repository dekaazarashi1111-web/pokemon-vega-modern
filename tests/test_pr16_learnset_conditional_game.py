"""新4入口のtyped engine seams。旧41試験/622669照合を再実行しない。"""
import ctypes as c
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]

class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        out = Path(cls.temp.name)/'game.so'
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
            '-I'+str(ROOT/'src/modernization'),'-I'+str(ROOT/'tests/fixtures'),
            *[str(ROOT/x) for x in ('src/modernization/pr16_learnset_conditional.c',
              'src/modernization/pr16_learnset_conditional_game.c','src/modernization/pr16_learnset_owner.c',
              'tests/fixtures/pr16_learnset_conditional_fixture.c')],'-o',str(out)],check=True)
        cls.dll = c.CDLL(str(out))
        u16 = c.POINTER(c.c_uint16)
        for name in ('Pr16_GameGetEggMoves','Pr16_GameGetConditionalRelearnerMoves'):
            f=getattr(cls.dll,name); f.argtypes=[c.c_void_p,u16]; f.restype=c.c_uint8
        cls.dll.Pr16_GameGetAllEggMoves.argtypes=[c.c_void_p,u16,c.c_uint8]
        cls.dll.Pr16_GameGetAllEggMoves.restype=c.c_uint8
        cls.dll.Pr16_GameAfterEvolution.argtypes=[c.c_void_p,c.c_uint8]
        cls.dll.Pr16_GameAfterEvolution.restype=c.c_uint16
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):
        self.mon=(c.c_uint32*66)();self.mon[11]=1;self.mon[56]=50
        self.cursor=c.c_uint8.in_dll(self.dll,'pr16_condition_cursor');self.cursor.value=255
        self.mode=c.c_uint8.in_dll(self.dll,'pr16_condition_mode');self.mode.value=0
        self.pending=c.c_uint16.in_dll(self.dll,'pr16_condition_pending');self.pending.value=999
        self.gives=c.c_uint32.in_dll(self.dll,'pr16_condition_gives');self.gives.value=0
        self.archives=c.c_uint32.in_dll(self.dll,'pr16_condition_archives');self.archives.value=0
    def listing(self, family, *args):
        out=(c.c_uint16*52)(*([0xBEEF]*52));before=bytes(self.mon)
        n=getattr(self.dll,family)(self.mon,out,*args)
        self.assertEqual(bytes(self.mon),before);self.assertEqual(list(out)[n:],[0xBEEF]*(52-n))
        return list(out)[:n]
    def test_direct_egg_not_shared(self):self.assertEqual(self.listing('Pr16_GameGetEggMoves'),[60,70])
    def test_direct_egg_works_during_breeding(self):
        self.mon[45]=1;self.assertEqual(self.listing('Pr16_GameGetEggMoves'),[60,70])
    def test_all_egg_is_explicit_union(self):self.assertEqual(self.listing('Pr16_GameGetAllEggMoves',0),[60,70,80])
    def test_all_egg_excludes_known_only_when_requested(self):
        self.mon[13]=70
        self.assertEqual(self.listing('Pr16_GameGetAllEggMoves',1),[60,80])
        self.assertEqual(self.listing('Pr16_GameGetAllEggMoves',0),[60,70,80])
    def test_normal_mode_distinct_from_egg(self):
        self.assertEqual(self.listing('Pr16_GameGetConditionalRelearnerMoves'),[40,20,10,50])
    def test_normal_mode_excludes_known_future(self):
        self.mon[13]=40;self.assertEqual(self.listing('Pr16_GameGetConditionalRelearnerMoves'),[20,10,50])
    def test_egg_mode_is_union_not_normal(self):
        self.mode.value=1;self.mon[13]=70
        self.assertEqual(self.listing('Pr16_GameGetConditionalRelearnerMoves'),[60,80]);self.assertEqual(self.archives.value,0)
    def test_preserve_existing_archive_dispatch(self):
        for mode in range(2,8):
            self.mode.value=mode;self.assertEqual(self.listing('Pr16_GameGetConditionalRelearnerMoves'),[100+mode])
        self.assertEqual(self.archives.value,6)
    def test_unknown_mode_fails_closed(self):
        for mode in (8,255):
            self.mode.value=mode;self.assertEqual(self.listing('Pr16_GameGetConditionalRelearnerMoves'),[])
        self.assertEqual(self.archives.value,0)
    def test_relearner_rejects_egg(self):
        self.mon[45]=1
        for mode in range(8):
            self.mode.value=mode;self.assertEqual(self.listing('Pr16_GameGetConditionalRelearnerMoves'),[])
        self.assertEqual(self.archives.value,0)
    def test_preserved_owner_no_grant_or_cursor_change(self):
        self.mon[11]=887
        for name in ('Pr16_GameGetEggMoves','Pr16_GameGetConditionalRelearnerMoves'):
            self.assertEqual(self.listing(name),[])
        self.mode.value=7;self.assertEqual(self.listing('Pr16_GameGetConditionalRelearnerMoves'),[])
        self.assertEqual(self.dll.Pr16_GameAfterEvolution(self.mon,1),0)
        self.assertEqual((self.cursor.value,self.pending.value,self.gives.value,self.archives.value),(255,999,0,0))
    def test_empty_owner_never_uses_species1(self):
        self.mon[11]=2
        self.assertEqual(self.listing('Pr16_GameGetEggMoves'),[])
        self.assertEqual(self.listing('Pr16_GameGetAllEggMoves',0),[])
        self.assertEqual(self.listing('Pr16_GameGetConditionalRelearnerMoves'),[])
        self.assertEqual(self.dll.Pr16_GameAfterEvolution(self.mon,1),0)
    def test_invalid_owner_rejected(self):
        self.mon[11]=1671;self.assertEqual(self.listing('Pr16_GameGetAllEggMoves',0),[])
        self.assertEqual(self.dll.Pr16_GameAfterEvolution(self.mon,1),0)
    def test_full_slots_notify_without_editing(self):
        self.mon[13:17]=[1,2,3,4];self.mon[17:21]=[7,8,9,10];self.mon[21]=0x39;before=bytes(self.mon)
        for i,move in enumerate((40,20,20)):
            self.assertEqual(self.dll.Pr16_GameAfterEvolution(self.mon,i==0),65535)
            self.assertEqual(self.pending.value,move);self.assertEqual(bytes(self.mon),before)
        self.assertEqual(self.dll.Pr16_GameAfterEvolution(self.mon,0),0);self.assertEqual(self.gives.value,3)
    def test_duplicate_continues_and_preserves_pp(self):
        self.mon[13]=40;self.mon[17]=9
        self.assertEqual(self.dll.Pr16_GameAfterEvolution(self.mon,1),65534)
        self.assertEqual(self.mon[17],9)
        self.assertEqual(self.dll.Pr16_GameAfterEvolution(self.mon,0),20)
        self.assertEqual(self.dll.Pr16_GameAfterEvolution(self.mon,0),65534)
        self.assertEqual(self.dll.Pr16_GameAfterEvolution(self.mon,0),0)
        self.assertEqual(list(self.mon)[13:17],[40,20,0,0])
    def test_evolution_egg_does_not_touch_cursor(self):
        self.mon[45]=1;self.assertEqual(self.dll.Pr16_GameAfterEvolution(self.mon,1),0)
        self.assertEqual((self.cursor.value,self.pending.value,self.gives.value),(255,999,0))
    def test_null_arguments_rejected(self):
        out=(c.c_uint16*50)()
        self.assertEqual(self.dll.Pr16_GameAfterEvolution(None,1),0)
        for name in ('Pr16_GameGetEggMoves','Pr16_GameGetConditionalRelearnerMoves'):
            self.assertEqual(getattr(self.dll,name)(None,out),0);self.assertEqual(getattr(self.dll,name)(self.mon,None),0)
        self.assertEqual(self.dll.Pr16_GameGetAllEggMoves(None,out,0),0)
        self.assertEqual(self.dll.Pr16_GameGetAllEggMoves(self.mon,None,0),0)

if __name__=='__main__':unittest.main()
