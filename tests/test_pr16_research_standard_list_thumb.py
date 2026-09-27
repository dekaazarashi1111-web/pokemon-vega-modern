"""ARM/Thumb delegate metadata boundary; this is not a native menu replay."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_standard_list as s


def fixture(entries=None):
    if entries is None:entries=[(n,v,2) for n,v in s.API.items()]
    names=bytearray(b'\0');symbols=bytearray(16)
    for n,v,t in entries:
        offset=len(names);names.extend(n.encode()+b'\0')
        symbols.extend(struct.pack('<IIIBBH',offset,v,0,0x10|t,0,0xfff1))
    off=52+3*40
    header=struct.pack('<16sHHIIIIIHHHHHH',b'\x7fELF\x01\x01\x01'+bytes(9),2,40,1,0,0,52,0,52,0,0,40,3,0)
    sections=bytes(40)+struct.pack('<10I',0,3,0,0,off,len(names),0,0,1,0)+struct.pack('<10I',0,2,0,0,off+len(names),len(symbols),1,0,4,16)
    return header+sections+names+symbols

class ThumbSymbolTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(set(s.audit_thumb_symbols(fixture())),set(s.API))
        self.entries=[(n,v,2) for n,v in s.API.items()]
    def reject(self):
        with self.assertRaises(ValueError):s.audit_thumb_symbols(fixture(self.entries))
    def test_positive(self):self.assertEqual(len(s.audit_thumb_symbols(fixture())),17)
    def test_notype_odd_address_is_not_thumb_proof(self):n,v,t=self.entries[0];self.entries[0]=(n,v,0);self.reject()
    def test_even_function_is_not_thumb(self):n,v,t=self.entries[0];self.entries[0]=(n,v-1,t);self.reject()
    def test_wrong_delegate_address(self):n,v,t=self.entries[0];self.entries[0]=(n,v+2,t);self.reject()
    def test_missing_delegate(self):self.entries.pop();self.reject()
    def test_duplicate_delegate(self):self.entries.append(self.entries[0]);self.reject()
    def test_truncated_table(self):
        with self.assertRaises(ValueError):s.audit_thumb_symbols(fixture()[:-1])
    def test_non_arm_elf(self):
        b=bytearray(fixture());struct.pack_into('<H',b,18,62)
        with self.assertRaises(ValueError):s.audit_thumb_symbols(bytes(b))

if __name__=='__main__':unittest.main()
