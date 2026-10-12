import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_fallback_cold as m
class Cold(unittest.TestCase):
 def test_closed_header(self):self.assertEqual(m.validate_header((ROOT/m.HEADER).read_text())['size']>0,True)
 def test_no_direct_writes(self):
  s=(ROOT/m.HEADER).read_text()
  for token in('busWrite8','writeRegister','cpu->gprs[0] ='):
   with self.assertRaises(ValueError):m.validate_header(s+'\n'+token+'(0);\n')
 def test_exact_copy_fixture(self):
  b=bytes(i%256 for i in range(131088))
  for name,offs in[('healthy',[]),('fallback',[0xFF8]),('corrupt-ledger',[0xFF8,0x1F06C])]:
   out,p=m.fixture(b,name);self.assertEqual(p['changed_byte_offsets'],offs);self.assertEqual(out[131072:],b[131072:]);self.assertEqual(len(out),len(b))
  with self.assertRaises(ValueError):m.fixture(b,'unknown')
if __name__=='__main__':unittest.main()
