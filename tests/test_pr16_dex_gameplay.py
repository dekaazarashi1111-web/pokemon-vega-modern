import hashlib,json,struct,sys,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_gameplay as m
class Gameplay(unittest.TestCase):
 def test_init_record(self):
  r=m.record();self.assertEqual(len(r),522);self.assertEqual(r[:4],b'MDX1');self.assertEqual(r[8:],b'\1'+bytes(513));a=bytearray(r);a[4:8]=bytes(4);self.assertEqual(struct.unpack_from('<I',r,4)[0],zlib.crc32(a))
 def test_legacy_exact(self):
  old=bytes(range(208));r=m.record(old);self.assertEqual(r[314:],old);self.assertEqual(r[10],1);self.assertEqual(r[12:314],bytes(302))
 def test_legacy_size_reject(self):
  with self.assertRaises(ValueError):m.record(bytes(207))
 def test_bad_physical_reject(self):
  with self.assertRaises(ValueError):m.physical(bytes(131072),101)
 def test_observer_no_emulator_write(self):
  s=(ROOT/m.HEADER).read_text()
  for token in ('busWrite','rawWrite','writeRegister','si_call(','si_restore(','si_transaction('):self.assertNotIn(token,s)
 def test_observer_offsets(self):
  s=(ROOT/m.HEADER).read_text();self.assertIn('sb1+0x5F8+i',s);self.assertIn('sb1+0x3A18+i',s);self.assertIn('sb2+0x5C+i',s);self.assertIn('sb2+0x28+i',s)
if __name__=='__main__':unittest.main()
