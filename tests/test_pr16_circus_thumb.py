"""Circus Thumb修復の命令型・固定配置・非影響証明を検査する。"""
import copy
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_thumb as thumb

class ThumbContracts(unittest.TestCase):
    def fixture(self):
        address=0x09FF4B10
        symbols={n:address+i*8 for i,n in enumerate(thumb.OWNERS)}
        code=b''.join(struct.pack('<HHI',0x4b00,0x4718,v) for v in thumb.OWNERS.values())
        elf='\n'.join(f' 1: {a|1:08x} 8 FUNC GLOBAL DEFAULT 1 {n}' for n,a in symbols.items())
        return code,address,symbols,elf
    def test_typed_thumb_owners(self):
        text=thumb.thumb_source(dict(thumb.OWNERS))
        self.assertEqual(text.count('.thumb_func'),2)
        self.assertEqual(text.count('bx r3'),2)
        self.assertNotIn('bx pc',text)
        thumb.check_thunks(*self.fixture())
    def test_reject_unknown_owner(self):
        for owners in ({},dict(thumb.OWNERS,unknown=1),{'x\n.word 0':1}):
            with self.assertRaises(ValueError):thumb.thumb_source(owners)
    def test_reject_even_or_changed_target(self):
        for value in (True,0x0910ed24,0x0910ed27):
            owners=dict(thumb.OWNERS);owners['cfru_integration_pending_copy']=value
            with self.assertRaises(ValueError):thumb.thumb_source(owners)
    def test_reject_arm_veneer_or_wrong_target(self):
        code,a,s,e=self.fixture()
        for i in (0,2,4,8,10,12):
            bad=bytearray(code);bad[i]^=1
            with self.assertRaises(ValueError):thumb.check_thunks(bad,a,s,e)
    def test_reject_untyped_even_or_duplicate_elf_symbol(self):
        code,a,s,e=self.fixture()
        for bad in (e.replace('FUNC','NOTYPE'),e.replace(f'{a|1:08x}',f'{a:08x}'),e+'\n'+e):
            with self.assertRaises(ValueError):thumb.check_thunks(code,a,s,bad)
    def test_reject_missing_or_outside_thunk(self):
        code,a,s,e=self.fixture()
        for bad in ({},dict(s,cfru_integration_pending_copy=a+1),dict(s,cfru_integration_pending_copy=a+64)):
            with self.assertRaises(ValueError):thumb.check_thunks(code,a,bad,e)
    def test_decode_saved_words_and_halfwords(self):
        a=0x09ff4b10
        text='\n'.join(f'{a+i:08x}: 47184b00' for i in range(0,304,4))
        self.assertEqual(thumb.decode_saved_adapter(text,a),bytes.fromhex('004b1847')*76)
    def test_reject_incomplete_duplicate_or_outside_disassembly(self):
        a=0x09ff4b10
        complete='\n'.join(f'{a+i:08x}: 00000000' for i in range(0,304,4))
        for text in ('',complete+'\n'+f'{a:08x}: 0000',complete+'\n'+f'{a+304:08x}: 0000'):
            with self.assertRaises(ValueError):thumb.decode_saved_adapter(text,a)
    def test_layout_changes_rejected_before_rom_reconstruction(self):
        candidate=b'test';base={'candidate':dict(size=33554432,sha256=thumb.PREVIOUS_SHA),
            'entries':{'selector':0x09ff4b11},'launch_sites':[],'gateway':{},'payload_offset':33508048,'payload':{'size':1014}}
        for key in ('entries','launch_sites','gateway','payload_offset','payload'):
            current=copy.deepcopy(base);current['candidate']=thumb.identity(candidate);current[key]=None
            with self.assertRaises((ValueError,TypeError)):thumb.prove_bytes(candidate,base,current,'')
    def test_reject_unbound_candidate(self):
        with self.assertRaises(ValueError):thumb.prove_bytes(b'test',{}, {'candidate':{}}, '')

if __name__=='__main__':unittest.main()
