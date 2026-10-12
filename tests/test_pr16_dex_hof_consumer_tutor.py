"""合成Thumb-1だけの拒否試験。ROM候補の受入ではない。"""
import copy,struct,unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_consumer_tutor as p

def encode(t,a):
 op=t[0]
 if op=='mov_reg':return struct.pack('<H',(t[2]<<3)|t[1])
 if op in('lsl','lsr','asr'):
  _,rd,rs,n=t;return struct.pack('<H',{'lsl':0,'lsr':0x800,'asr':0x1000}[op]|((n%32)<<6)|(rs<<3)|rd)
 if op in('add3','sub3'):
  _,rd,rs,kind,x=t;return struct.pack('<H',0x1800|(0x200 if op=='sub3'else 0)|(0x400 if kind=='imm'else 0)|(x<<6)|(rs<<3)|rd)
 if op in('mov_imm','cmp_imm','add_imm','sub_imm'):
  return struct.pack('<H',{'mov_imm':0x2000,'cmp_imm':0x2800,'add_imm':0x3000,'sub_imm':0x3800}[op]|(t[1]<<8)|t[2])
 if op in('and','lsl_reg','sbc'):return struct.pack('<H',0x4000|({'and':0,'lsl_reg':2,'sbc':6}[op]<<6)|(t[2]<<3)|t[1])
 if op in('push','pop'):
  high=15 if op=='pop'else 14;regs=t[1];return struct.pack('<H',(0xbc00 if op=='pop'else 0xb400)|(0x100 if high in regs else 0)|sum(1<<x for x in regs if x<8))
 if op=='ldr_literal':return struct.pack('<H',0x4800|(t[1]<<8)|((t[2]-((a+4)&~3))//4))
 if op=='ldr_word':return struct.pack('<H',0x6800|((t[3]//4)<<6)|(t[2]<<3)|t[1])
 if op=='bx':return struct.pack('<H',0x4700|(t[1]<<3))
 if op=='bcond':return struct.pack('<H',0xd000|(t[1]<<8)|(((t[2]-a-4)//2)&255))
 if op=='b':return struct.pack('<H',0xe000|(((t[1]-a-4)//2)&0x7ff))
 if op=='bl':
  off=t[1]-a-4;return struct.pack('<HH',0xf000|((off>>12)&0x7ff),0xf800|((off>>1)&0x7ff))
 raise ValueError(op)

def fixture():
 raw=bytearray(33554432)
 for offset,want in p.EXPECTED.items():
  a=0x9110000+offset;b=encode(want,a);raw[a-p.BASE:a-p.BASE+len(b)]=b
 a=0x9111c7a;raw[a-p.BASE:a-p.BASE+2]=encode(('bx',7),a)
 for a,v in [(0x9110380,0x803f355),(p.LITERAL,p.ROOT),(p.ROOT,p.OWNER['address'])]:struct.pack_into('<I',raw,a-p.BASE,v)
 return raw

class Contracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.raw=fixture()
 def test_entire_synthetic_semantics(self):
  s=p.semantic_check(self.raw);self.assertEqual(s['stride_bytes'],20);self.assertEqual(s['target_word_index'],4);self.assertEqual(s['regular_id_count'],152)
 def test_every_instruction_semantic_drift_rejected(self):
  for offset in p.EXPECTED:
   with self.subTest(address=hex(0x9110000+offset)):
    r=bytearray(self.raw);r[0x1110000+offset]^=1
    with self.assertRaises(ValueError):p.semantic_check(r)
 def test_current_stride16_rejected(self):
  r=bytearray(self.raw);struct.pack_into('<H',r,0x1110242,0x46c0)
  with self.assertRaises(ValueError):p.semantic_check(r)
 def test_current_tutor64_rejected(self):
  r=bytearray(self.raw);r[0x1110238]=63
  with self.assertRaises(ValueError):p.semantic_check(r)
 def test_current_trampoline_rejected(self):
  r=bytearray(self.raw);r[0x1110228:0x111022a]=encode(('ldr_literal',3,p.ENTRY+4),p.ENTRY)
  with self.assertRaises(ValueError):p.semantic_check(r)
 def test_wrong_root_rejected(self):
  r=bytearray(self.raw);struct.pack_into('<I',r,p.ROOT-p.BASE,p.OWNER['address']+16)
  with self.assertRaises(ValueError):p.semantic_check(r)
 def test_wrong_literal_rejected(self):
  r=bytearray(self.raw);struct.pack_into('<I',r,p.LITERAL-p.BASE,p.ROOT+4)
  with self.assertRaises(ValueError):p.semantic_check(r)
 def test_wrong_callee_rejected(self):
  r=bytearray(self.raw);struct.pack_into('<I',r,0x1110380,0x803f357)
  with self.assertRaises(ValueError):p.semantic_check(r)
 def test_wrong_veneer_rejected(self):
  r=bytearray(self.raw);r[0x1111c7a:0x1111c7c]=encode(('bx',6),0x9111c7a)
  with self.assertRaises(ValueError):p.semantic_check(r)
 def test_fourth_word_substitution_rejected(self):
  r=bytearray(self.raw);r[0x11102ce:0x11102d0]=encode(('ldr_word',0,0,12),0x91102ce)
  with self.assertRaises(ValueError):p.semantic_check(r)
 def test_synthetic_rom_not_historical(self):
  with self.assertRaisesRegex(ValueError,'whole actual Stage38'):p.historical_probe(bytes(self.raw),'.')
 def test_synthetic_rom_not_current(self):
  with self.assertRaisesRegex(ValueError,'whole exact current'):p.bind_current(bytes(self.raw),[],b'',{},'.')
 def test_truncated_rom_refused(self):
  with self.assertRaises(ValueError):p.semantic_check(b'')
 def test_unknown_instruction_refused(self):
  r=bytearray(self.raw);struct.pack_into('<H',r,0x111023c,0xffff)
  with self.assertRaises(ValueError):p.semantic_check(r)
 def test_target_row_geometry(self):
  self.assertEqual(p.ROW+16,p.HIT['address']);self.assertEqual(p.HIT['address']-p.OWNER['address'],278*20+16)
 def test_full_last_word_upper8_bits_not_address(self):
  self.assertEqual(p.EXPECTED[0x2ce],('ldr_word',0,0,16));self.assertEqual(p.EXPECTED[0x2d0],('and',0,3));self.assertEqual(p.EXPECTED[0x2d6],('b',0x911028e))

if __name__=='__main__':unittest.main(verbosity=2)
