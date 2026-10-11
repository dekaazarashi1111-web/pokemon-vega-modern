"""合成ARMv4T命令のみで、型根とBL/LDR境界拒否を検査。"""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_reference_code as m

def bl(address,target):
 delta=target-address-4
 return struct.pack('<HH',0xf000|((delta>>12)&0x7ff),0xf800|((delta>>1)&0x7ff))

class CodeTests(unittest.TestCase):
 def setUp(self):
  self.root=0x08001000;self.targets=[0x08000e00,0x08001200];self.literal=self.root+32
  self.raw=struct.pack('<H',0xb510)+bl(self.root+2,self.targets[0])+bl(self.root+6,self.targets[1])+struct.pack('<H',0x4b05)
 def run_entry(self,raw=None,address=None,targets=None,literal=None):
  return m.entry_sequence(self.raw if raw is None else raw,self.root if address is None else address,self.targets if targets is None else targets,self.literal if literal is None else literal)
 def test_synthetic_valid_prefix(self):self.assertEqual(self.run_entry()['exact_instruction_sizes'],[2,4,4,2])
 def test_backward_bl_sign(self):self.assertEqual(m.thumb_bl(bl(self.root,self.root-512),self.root),self.root-512)
 def test_forward_bl(self):self.assertEqual(m.thumb_bl(bl(self.root,self.root+512),self.root),self.root+512)
 def test_wrong_bl_suffix(self):
  with self.assertRaises(ValueError):m.thumb_bl(struct.pack('<HH',0xf000,0xe800),self.root)
 def test_wrong_bl_prefix(self):
  with self.assertRaises(ValueError):m.thumb_bl(struct.pack('<HH',0xe000,0xf800),self.root)
 def test_short_bl(self):
  with self.assertRaises(ValueError):m.thumb_bl(bytes(2),self.root)
 def test_odd_bl(self):
  with self.assertRaises(ValueError):m.thumb_bl(bl(self.root,self.root+8),self.root+1)
 def test_wrong_target(self):
  with self.assertRaises(ValueError):self.run_entry(targets=[self.targets[0]+2,self.targets[1]])
 def test_donor_call_rejected(self):
  root=m.d.DONOR_LO-128;targets=[m.d.DONOR_LO,m.d.DONOR_LO+4];raw=struct.pack('<H',0xb510)+bl(root+2,targets[0])+bl(root+6,targets[1])+struct.pack('<H',0x4b05)
  with self.assertRaises(ValueError):m.entry_sequence(raw,root,targets,root+32)
 def test_unaligned_entry(self):
  with self.assertRaises(ValueError):self.run_entry(address=self.root+1)
 def test_short_entry(self):
  with self.assertRaises(ValueError):self.run_entry(raw=self.raw[:-1])
 def test_extra_entry(self):
  with self.assertRaises(ValueError):self.run_entry(raw=self.raw+b'00')
 def test_missing_lr_push(self):
  with self.assertRaises(ValueError):self.run_entry(raw=struct.pack('<H',0xb410)+self.raw[2:])
 def test_empty_frame(self):
  with self.assertRaises(ValueError):self.run_entry(raw=struct.pack('<H',0xb500)+self.raw[2:])
 def test_wrong_ldr(self):
  with self.assertRaises(ValueError):self.run_entry(raw=self.raw[:-2]+struct.pack('<H',0x6800))
 def test_wrong_literal_slot(self):
  with self.assertRaises(ValueError):self.run_entry(literal=self.literal+4)
 def test_literal_in_instruction_span(self):
  with self.assertRaises(ValueError):self.run_entry(literal=self.root+8)
if __name__=='__main__':unittest.main()
