"""getterのfield namespace、自然fallback、literal所有を限定検証。"""
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_circus_getter_fields as f


class LiteralContracts(unittest.TestCase):
    def setUp(self):
        self.raw=bytes.fromhex(f.fixture()['getter']['hex'])

    def test_exact_five_fields(self):
        fixed,rows=f.repair_getter(self.raw)
        self.assertEqual([r['field_index'] for r in rows],[0,3,4,1,2])
        self.assertEqual(len(rows),5)
        for r in rows:
            offset=r['offset']+f.g.BASE-f.GETTER
            self.assertEqual(struct.unpack_from('<I',fixed,offset)[0],r['field_index'])

    def test_no_instruction_or_unowned_change(self):
        fixed,rows=f.repair_getter(self.raw)
        allowed={r['offset']+f.g.BASE-f.GETTER+i for r in rows for i in range(4)}
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(self.raw,fixed))))
        self.assertEqual(fixed[:0xb8],self.raw[:0xb8])
        self.assertEqual(fixed[0xdc:],self.raw[0xdc:])

    def test_truncated_rejected(self):
        with self.assertRaisesRegex(ValueError,'preimage'):f.repair_getter(self.raw[:-1])

    def test_other_runtime_rejected(self):
        with self.assertRaisesRegex(ValueError,'preimage'):f.repair_getter(b'\0'+self.raw[1:])

    def test_double_apply_rejected(self):
        with self.assertRaisesRegex(ValueError,'preimage'):f.repair_getter(f.repair_getter(self.raw)[0])

    def test_rollback(self):
        fixed,rows=f.repair_getter(self.raw);out=bytearray(fixed)
        for r in rows:
            at=r['offset']+f.g.BASE-f.GETTER;out[at:at+4]=bytes.fromhex(r['before'])
        self.assertEqual(bytes(out),self.raw)

    def test_state_api_range_gate(self):
        raw=bytes.fromhex(f.fixture()['state_get']['hex'])
        self.assertEqual(raw[:12].hex(),'70b504000a2801d9002070bd')
        self.assertEqual(f.g.identity(raw),f.fixture()['state_get']['identity'])

    def test_t06_enum_mapping(self):
        text=(f.ROOT/'scripts/build_battle_core.py').read_text()
        block=text.split('"enum VegaFacilityStateField\\n"',1)[1].split('SENTINEL',1)[0]
        names=['NUMBER','PARTY_SIZE','LEVEL','BATTLE_TYPE','TIER']
        self.assertEqual(sorted(names,key=lambda n:block.index('VEGA_FACILITY_STATE_'+n)),names)
        for _,_,_,index,name in f.FIELDS:self.assertEqual(names[index],name)


class RuntimeLeafContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();root=Path(cls.temp.name)
        source=(f.ROOT/f.RUNTIME).read_text()
        # commit前のローカルでは未変更sourceに同じ変換を適用する。
        # Actions prepareはsource mirrorを更新してからこの契約を検証する。
        if 'STATE_GET(0x403Au)' in source:source=f.repaired_source(source)
        start=source.index('enum CircusFacilityStateField')
        end=source.index('\nEXPORT void CircusStreakRuntimeLossReturn',start)
        body=source[start:end].replace('EXPORT ','')
        old='((uint16_t (*)(uint8_t, uint16_t, uint16_t, uint16_t, uint8_t))\n        (uintptr_t)0x091025EDu)'
        if body.count(old)!=1:raise AssertionError('fallback signature changed')
        body=body.replace(old,'mock_fallback')
        pre='''#include <stdint.h>
struct Owner {uint16_t current,best;} owner;
#define OWNER (&owner)
uint16_t fields[11],seen[8],fallback_args[5];
unsigned calls,fallbacks,armed;
uint16_t state_get(uint16_t n){seen[calls++]=n;return n<=10?fields[n]:0;}
#define STATE_GET state_get
unsigned CircusStreakRuntimeArmed(void){return armed;}
uint16_t mock_fallback(uint8_t a,uint16_t b,uint16_t c,uint16_t d,uint8_t e){
 ++fallbacks;fallback_args[0]=a;fallback_args[1]=b;fallback_args[2]=c;
 fallback_args[3]=d;fallback_args[4]=e;return 777;}
'''
        (root/'leaf.c').write_text(pre+body)
        subprocess.run(['cc','-std=c11','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',str(root/'leaf.c'),'-o',str(root/'leaf.so')],check=True,capture_output=True)
        cls.lib=ctypes.CDLL(str(root/'leaf.so'))
        cls.get=cls.lib.CircusStreakRuntimeGet;cls.get.argtypes=[ctypes.c_uint8,ctypes.c_uint16,ctypes.c_uint16,ctypes.c_uint16,ctypes.c_uint8];cls.get.restype=ctypes.c_uint16

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def setUp(self):
        self.fields=(ctypes.c_uint16*11).in_dll(self.lib,'fields')
        self.fields[:]=[3,3,50,4,0,0,0,0,0,0,0]
        (ctypes.c_uint16*2).in_dll(self.lib,'owner')[:]=[30,45]
        for n,v in [('calls',0),('fallbacks',0),('armed',1)]:ctypes.c_uint.in_dll(self.lib,n).value=v
        self.args=(0,65535,65535,65535,0)

    def test_current_30(self):
        self.assertEqual(self.get(*self.args),30)
        self.assertEqual(list((ctypes.c_uint16*8).in_dll(self.lib,'seen'))[:5],[0,3,4,1,2])
        self.assertEqual(ctypes.c_uint.in_dll(self.lib,'calls').value,5)
        self.assertEqual(ctypes.c_uint.in_dll(self.lib,'fallbacks').value,0)

    def test_best(self):self.assertEqual(self.get(1,*self.args[1:]),45)

    def test_explicit_parameters(self):
        self.assertEqual(self.get(0,4,0,3,50),30)
        self.assertEqual(ctypes.c_uint.in_dll(self.lib,'calls').value,1)

    def test_wrong_facility_fallback(self):
        self.fields[0]=0;self.assertEqual(self.get(*self.args),777)
        self.assertEqual(tuple((ctypes.c_uint16*5).in_dll(self.lib,'fallback_args')),self.args)
        self.assertEqual(ctypes.c_uint.in_dll(self.lib,'fallbacks').value,1)

    def test_not_armed(self):
        ctypes.c_uint.in_dll(self.lib,'armed').value=0;self.assertEqual(self.get(*self.args),777)

    def test_invalid_current_max(self):self.assertEqual(self.get(2,*self.args[1:]),777)

    def test_wrong_style(self):self.fields[3]=0;self.assertEqual(self.get(*self.args),777)

    def test_wrong_tier(self):self.fields[4]=1;self.assertEqual(self.get(*self.args),777)

    def test_wrong_size(self):self.fields[1]=6;self.assertEqual(self.get(*self.args),777)

    def test_wrong_level(self):self.fields[2]=100;self.assertEqual(self.get(*self.args),777)

    def test_explicit_invalid_arguments_preserved(self):
        args=(1,2,19,6,100);self.assertEqual(self.get(*args),777)
        self.assertEqual(tuple((ctypes.c_uint16*5).in_dll(self.lib,'fallback_args')),args)

    def test_source_double_repair_rejected(self):
        source=(f.ROOT/f.RUNTIME).read_text()
        if 'STATE_GET(0x403Au)' in source:source=f.repaired_source(source)
        with self.assertRaises(ValueError):f.repaired_source(source)


if __name__=='__main__':unittest.main()
