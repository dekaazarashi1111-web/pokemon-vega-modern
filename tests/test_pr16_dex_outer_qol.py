import struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_outer_qol as f
class OuterQol(unittest.TestCase):
 def test_signed_sole_boundary(self):
  p=f.proof();self.assertEqual(p['patch_call'],0x09377682);self.assertEqual(p['helper'],0x093797C0)
  self.assertEqual((f.BASE,f.END),(0x095FFFB0,0x09600000));self.assertEqual(len(p['windows']),6)
 def test_thumb_bl_reversible(self):
  for a,t in [(0x0937767E,f.BASE),(0x0937767E,0x093797C0),(f.BASE,0x09377660)]:
   x,y=struct.unpack('<HH',f.thumb_bl(a,t));delta=((x&2047)<<12)|((y&2047)<<1)
   if delta&0x400000:delta-=0x800000
   self.assertEqual(a+4+delta,t)
  for a,t in [(1,2),(0,0x400004),(0x400002,0)]:
   with self.assertRaises(ValueError):f.thumb_bl(a,t)
 def test_no_new_owner_or_destructive_retry(self):
  s=(ROOT/f.SOURCE).read_text();self.assertEqual(s.count('strh r0,[r1]'),1)
  for forbidden in ['.bss','.data','strb ','0x080F','0x080DB230']:self.assertNotIn(forbidden,s)
  self.assertIn('cmp r0,#1',s);self.assertIn('movs r0,#255',s);self.assertIn('0x03005470',s)
if __name__=='__main__':unittest.main()
