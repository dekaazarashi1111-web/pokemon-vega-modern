"""Stage61へ渡すcompanion bridgeの実C境界。bank scheduler/native未接続。"""
import ctypes as C
from pathlib import Path
import struct,subprocess,tempfile,unittest,zlib
ROOT=Path(__file__).resolve().parents[1]
class SaveBridge(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup);out=Path(cls.tmp.name)/'bridge.so'
  subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-pedantic','-fPIC','-shared',str(ROOT/'overlays/dex_owner/dex_owner.c'),str(ROOT/'overlays/dex_owner/dex_save_bridge.c'),'-o',str(out)],check=True)
  cls.lib=C.CDLL(str(out));p=C.c_void_p;n=C.c_size_t;u=C.c_uint32;b=C.c_uint8
  for k,args in {'VegaDexInitNew':[p,n],'VegaDexValidate':[p,n],'VegaDexAccess':[p,n,C.c_uint16,b,p],'VegaDexClassifyRecord':[p,n],'VegaDexCheckSector':[p,n,u,b],'VegaDexInjectSector':[p,n,p,n,u,b],'VegaDexTailMatches':[p,n,p,n,u,b,p],'VegaDexLoadSelected':[p,n,p,n,p,n,p,n,u,b],'VegaDexInvalidateSession':[p,n]}.items():getattr(cls.lib,k).argtypes=args
 def setUp(self):
  self.live=(C.c_ubyte*522)();self.lib.VegaDexInitNew(self.live,522)
  self.sector=(C.c_ubyte*4096)(*([0xA5]*4096));self.counter=101
  self.sector[0xDE6:0xFF0]=bytes(522);self.sector[0xFF4:]=struct.pack('<HHII',13,0x1234,0x08012025,101)
  self.s1=(C.c_ubyte*0x3D40)(*[(i*13)&255 for i in range(0x3D40)])
  self.s2=(C.c_ubyte*0xF24)(*[(i*29+1)&255 for i in range(0xF24)])
 def record(self):return C.cast(C.byref(self.sector,0xDE6),C.c_void_p)
 def check(self):return self.lib.VegaDexCheckSector(self.sector,4096,self.counter,1)
 def inject(self):return self.lib.VegaDexInjectSector(self.sector,4096,self.live,522,self.counter,1)
 def load(self):return self.lib.VegaDexLoadSelected(self.live,522,self.sector,4096,self.s1,len(self.s1),self.s2,len(self.s2),self.counter,1)
 def test_blank_zero_allowed(self):self.assertEqual(self.check(),0);self.assertEqual(self.lib.VegaDexClassifyRecord(self.record(),522),1)
 def test_blank_erased_allowed(self):self.sector[0xDE6:0xFF0]=b'\xff'*522;self.assertEqual(self.check(),0);self.assertEqual(self.lib.VegaDexClassifyRecord(self.record(),522),2)
 def test_mixed_blank_rejected(self):self.sector[0xDE6]=255;self.assertNotEqual(self.check(),0)
 def test_valid_record_allowed(self):self.assertEqual(self.inject(),0);self.assertEqual(self.check(),0);self.assertEqual(self.lib.VegaDexClassifyRecord(self.record(),522),0)
 def test_invalid_version_rejected(self):self.inject();self.sector[0xDEE]=2;self.assertEqual(self.check(),4)
 def test_crc_rejected(self):self.inject();self.sector[0xE30]^=1;self.assertEqual(self.check(),5)
 def test_final_record_byte_crc(self):self.inject();self.sector[0xFEF]^=1;self.assertEqual(self.check(),5)
 def test_unknown_flags_rejected(self):self.inject();self.sector[0xDF0]=128;self.assertEqual(self.check(),6)
 def test_wrong_logical_id(self):self.sector[0xFF4]=12;self.assertEqual(self.check(),11)
 def test_signature_missing(self):self.sector[0xFF8]=255;self.assertEqual(self.check(),11)
 def test_wrong_counter(self):self.counter=100;self.assertEqual(self.check(),11)
 def test_unverified_parent(self):self.assertEqual(self.lib.VegaDexCheckSector(self.sector,4096,101,0),11)
 def test_bad_verified_mode(self):self.assertEqual(self.lib.VegaDexCheckSector(self.sector,4096,101,2),11)
 def test_counter_wrap(self):self.counter=0xFFFFFFFF;self.sector[0xFFC:]=struct.pack('<I',self.counter);self.assertEqual(self.inject(),0);self.assertEqual(self.check(),0)
 def test_inject_only522(self):
  before=bytes(self.sector);self.assertEqual(self.inject(),0);after=bytes(self.sector)
  self.assertEqual(before[:0xDE6],after[:0xDE6]);self.assertEqual(before[0xFF0:],after[0xFF0:]);self.assertEqual(after[0xDE6:0xFF0],bytes(self.live))
 def test_inject_bad_live_atomic(self):self.live[0]=0;before=bytes(self.sector);self.assertNotEqual(self.inject(),0);self.assertEqual(bytes(self.sector),before)
 def test_inject_bad_parent_atomic(self):self.counter=100;before=bytes(self.sector);self.assertNotEqual(self.inject(),0);self.assertEqual(bytes(self.sector),before)
 def test_inject_alias_reject(self):self.assertEqual(self.lib.VegaDexInjectSector(self.sector,4096,self.record(),522,101,1),1)
 def test_tail_match(self):self.inject();v=C.c_ubyte(99);self.assertEqual(self.lib.VegaDexTailMatches(self.sector,4096,self.live,522,101,1,C.byref(v)),0);self.assertEqual(v.value,1)
 def test_tail_different_valid_record(self):
  self.inject();v=C.c_ubyte(99);self.lib.VegaDexAccess(self.live,522,1206,3,C.byref(v));self.assertEqual(self.lib.VegaDexTailMatches(self.sector,4096,self.live,522,101,1,C.byref(v)),0);self.assertEqual(v.value,0)
 def test_tail_bad_record_output_unchanged(self):
  self.inject();self.sector[0xE30]^=1;v=C.c_ubyte(99);self.assertEqual(self.lib.VegaDexTailMatches(self.sector,4096,self.live,522,101,1,C.byref(v)),5);self.assertEqual(v.value,99)
 def test_tail_output_alias_live(self):self.assertEqual(self.lib.VegaDexTailMatches(self.sector,4096,self.live,522,101,1,self.live),1)
 def test_tail_output_alias_sector(self):self.assertEqual(self.lib.VegaDexTailMatches(self.sector,4096,self.live,522,101,1,self.sector),1)
 def test_snapshot_selected_saveblocks(self):
  self.assertEqual(self.load(),0);expected=bytes(self.s1[0x5F8:0x62C])+bytes(self.s1[0x3A18:0x3A4C])+bytes(self.s2[0x5C:0x90])+bytes(self.s2[0x28:0x5C]);self.assertEqual(bytes(self.live[314:]),expected);self.assertEqual(bytes(self.live[12:314]),bytes(302));self.assertEqual(self.live[10],1)
 def test_valid_load_does_not_resnapshot(self):
  self.load();expected=bytes(self.live);self.inject();self.s1[0x5F8]^=255;self.s2[0x28]^=255;self.lib.VegaDexInitNew(self.live,522);self.assertEqual(self.load(),0);self.assertEqual(bytes(self.live),expected)
 def test_corrupt_load_no_mutation(self):self.inject();self.sector[0xE30]^=1;before=bytes(self.live);self.assertNotEqual(self.load(),0);self.assertEqual(bytes(self.live),before)
 def test_load_bad_saveblock_size_no_mutation(self):
  before=bytes(self.live);self.assertEqual(self.lib.VegaDexLoadSelected(self.live,522,self.sector,4096,self.s1,1,self.s2,len(self.s2),101,1),2);self.assertEqual(bytes(self.live),before)
 def test_load_alias_reject(self):self.assertEqual(self.lib.VegaDexLoadSelected(self.record(),522,self.sector,4096,self.s1,len(self.s1),self.s2,len(self.s2),101,1),1)
 def test_load_preserves_all_input_bytes(self):
  before=(bytes(self.sector),bytes(self.s1),bytes(self.s2));self.load();self.assertEqual(before,(bytes(self.sector),bytes(self.s1),bytes(self.s2)))
 def test_failed_load_invalidation_not_newgame(self):self.assertEqual(self.lib.VegaDexInvalidateSession(self.live,522),0);self.assertEqual(bytes(self.live),bytes(522));self.assertEqual(self.lib.VegaDexValidate(self.live,522),3)
 def test_invalidation_short_no_mutation(self):before=bytes(self.live);self.assertEqual(self.lib.VegaDexInvalidateSession(self.live,521),2);self.assertEqual(bytes(self.live),before)
 def test_null_and_short_classify(self):self.assertEqual(self.lib.VegaDexClassifyRecord(None,522),3);self.assertEqual(self.lib.VegaDexClassifyRecord(self.live,521),3)
 def test_sector_size_bounds(self):self.assertEqual(self.lib.VegaDexCheckSector(self.sector,4095,101,1),2);self.assertEqual(self.lib.VegaDexCheckSector(None,4096,101,1),1)
 def test_newgame_explicit_init_only(self):self.lib.VegaDexInvalidateSession(self.live,522);self.assertEqual(self.lib.VegaDexValidate(self.live,522),3);self.lib.VegaDexInitNew(self.live,522);self.assertEqual(self.lib.VegaDexValidate(self.live,522),0)
if __name__=='__main__':unittest.main()
