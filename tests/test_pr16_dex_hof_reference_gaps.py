"""有限rootの境界とscalar/code/text取り違えを合成bytesで拒否。"""
import copy,hashlib,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_reference_gaps as m
import pr16_dex_hof_reference_chain as chain

class ScriptTests(unittest.TestCase):
 def setUp(self):
  self.base=0x08000000;self.raw=bytearray(128);self.text_address=self.base+80
  self.raw[0]=106;self.raw[1:9]=bytes([15,0])+self.text_address.to_bytes(4,'little')+bytes([9,4])
  self.text=dict(address=self.text_address,target_script_root=self.base,path=[self.row(0,1,106),self.row(1,6,15)],loadword_and_callstd=dict(address=self.base+1,size=8,sha256=m.identity(self.raw[1:9])['sha256'],pointer=self.text_address))
 def row(self,o,n,opcode):return dict(address=self.base+o,size=n,sha256=m.identity(self.raw[o:o+n])['sha256'],opcode=opcode)
 def test_finite_path(self):self.assertEqual(m.script_path(bytes(self.raw),self.text)['instructions'],2)
 def test_opcode_extent(self):
  self.text['path'][0]['size']=2
  with self.assertRaises(ValueError):m.script_path(bytes(self.raw),self.text)
 def test_wrong_root(self):
  self.text['target_script_root']+=1
  with self.assertRaises(ValueError):m.script_path(bytes(self.raw),self.text)
 def test_wrong_std(self):
  self.raw[8]=5;self.text['loadword_and_callstd']['sha256']=m.identity(self.raw[1:9])['sha256']
  with self.assertRaises(ValueError):m.script_path(bytes(self.raw),self.text)
 def test_wrong_data_index(self):
  self.raw[2]=1;self.text['path'][1]=self.row(1,6,15);self.text['loadword_and_callstd']['sha256']=m.identity(self.raw[1:9])['sha256']
  with self.assertRaises(ValueError):m.script_path(bytes(self.raw),self.text)
 def test_unsupported_opcode(self):
  self.raw[0]=255;self.text['path'][0]=self.row(0,1,255)
  with self.assertRaises(ValueError):m.script_path(bytes(self.raw),self.text)
 def test_gap(self):
  self.text['path'][1]['address']+=1
  with self.assertRaises(ValueError):m.script_path(bytes(self.raw),self.text)
 def test_unmatched_return(self):
  self.raw[0]=3;self.text['path'][0]=self.row(0,1,3)
  with self.assertRaises(ValueError):m.script_path(bytes(self.raw),self.text)
 def test_incomplete_final(self):
  self.text['loadword_and_callstd']['size']=7
  with self.assertRaises(ValueError):m.script_path(bytes(self.raw),self.text)
 def test_source_sha(self):
  self.raw[0]=90
  with self.assertRaises(ValueError):m.script_path(bytes(self.raw),self.text)

class ThumbTests(unittest.TestCase):
 def setUp(self):self.base=0x08000000
 def runpath(self,halfwords,rows):
  raw=b''.join(x.to_bytes(2,'little')for x in halfwords)
  records=[dict(address=self.base+at,size=size,sha256=m.identity(raw[at:at+size])['sha256'],**fields)for at,size,fields in rows]
  return m.thumb_path(raw,records,self.base)
 def test_straight(self):self.assertTrue(self.runpath([0xB510,0x2001],[(0,2,{}),(2,2,{})]))
 def test_conditional(self):self.assertTrue(self.runpath([0xD000,0x2001,0x2002],[(0,2,{}),(4,2,{})]))
 def test_unconditional(self):self.assertTrue(self.runpath([0xE000,0x2001,0x2002],[(0,2,{}),(4,2,{})]))
 def test_bad_edge(self):
  with self.assertRaises(ValueError):self.runpath([0x2000,0x2001,0x2002],[(0,2,{}),(4,2,{})])
 def test_bl_descend(self):self.assertTrue(self.runpath([0xF000,0xF800,0x2000],[(0,4,dict(target=self.base+4)),(4,2,{})]))
 def test_bad_bl_target(self):
  with self.assertRaises(ValueError):self.runpath([0xF000,0xF800],[(0,4,dict(target=self.base+6))])
 def test_partial_bl(self):
  with self.assertRaises(ValueError):self.runpath([0xF000,0xF800],[(0,2,{})])
 def test_bl_suffix(self):
  with self.assertRaises(ValueError):self.runpath([0xF800],[(0,2,{})])
 def test_bx(self):
  with self.assertRaises(ValueError):self.runpath([0x4770],[(0,2,{})])
 def test_pop_pc(self):
  with self.assertRaises(ValueError):self.runpath([0xBD10],[(0,2,{})])
 def test_reserved_condition(self):
  with self.assertRaises(ValueError):self.runpath([0xDE00],[(0,2,{})])
 def test_swi(self):
  with self.assertRaises(ValueError):self.runpath([0xDF00],[(0,2,{})])
 def test_newer_or_reserved_misc(self):
  for opcode in(0xBE00,0xB600,0xBA00):
   with self.subTest(opcode=opcode):
    with self.assertRaises(ValueError):self.runpath([opcode],[(0,2,{})])
 def test_mov_pc(self):
  with self.assertRaises(ValueError):self.runpath([0x4687],[(0,2,{})])

class GeometryTests(unittest.TestCase):
 def test_cross_text(self):self.assertEqual(chain.witness_geometry(dict(kind='adjacent_jp_text_crossing',evidence=dict(left=dict(address=10,size=5),right=dict(address=15,size=8),both_text_consumers_verified=True,source_pointer_interpretation=False))),(12,4))
 def test_cross_text_gap(self):
  with self.assertRaises(ValueError):chain.witness_geometry(dict(kind='adjacent_jp_text_crossing',evidence=dict(left=dict(address=10,size=5),right=dict(address=16,size=8),both_text_consumers_verified=True,source_pointer_interpretation=False)))
 def test_cross_text_unrooted(self):
  with self.assertRaises(ValueError):chain.witness_geometry(dict(kind='adjacent_jp_text_crossing',evidence=dict(left=dict(address=10,size=5),right=dict(address=15,size=8),both_text_consumers_verified=False,source_pointer_interpretation=False)))
 def test_cross_u16(self):self.assertEqual(chain.witness_geometry(dict(kind='packed_u16_cross_row',evidence=dict(selected_rows=dict(address=12,size=8),record_size=4,field_offsets=[0,2]))),(14,4))
 def test_u32_field(self):
  with self.assertRaises(ValueError):chain.witness_geometry(dict(kind='packed_u16_cross_row',evidence=dict(selected_rows=dict(address=12,size=8),record_size=4,field_offsets=[0])))
 def test_short_rows(self):
  with self.assertRaises(ValueError):chain.witness_geometry(dict(kind='packed_u16_cross_row',evidence=dict(selected_rows=dict(address=12,size=6),record_size=4,field_offsets=[0,2])))

if __name__=='__main__':unittest.main()
