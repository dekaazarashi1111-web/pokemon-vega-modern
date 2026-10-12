"""Circus限定predicateの全境界組合せとROM最小patchの負例。"""
import ctypes
import importlib.util
import itertools
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_retention as m
import pr16_circus_retention_native as native

class RetentionHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();so=Path(cls.tmp.name)/'predicate.so'
        defines=[f'-DCIRCUS_SCRIPT_{key}=0x{value:x}u' for key,value in zip(('FIRST','SECOND','THIRD'),m.CONTINUATIONS)]
        subprocess.run(['cc','-std=c11','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror','-DCIRCUS_RETENTION_HOST_TEST',*defines,str(ROOT/m.SOURCE),'-o',str(so)],check=True,capture_output=True)
        cls.lib=ctypes.CDLL(str(so));cls.fn=cls.lib.VegaCircusKeepRental
        cls.fn.restype=ctypes.c_uint8;cls.fn.argtypes=[ctypes.c_uint8]*6+[ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint16,ctypes.c_uint32]
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_exhaustive_145152_boundary_combinations(self):
        count=0
        for row in itertools.product((0,1,2),(0,1,2,3),(0,1),range(7),(0,3,6),(0,1,2,3),(*m.CONTINUATIONS,0x092cf6a5,0x092cf6e1,0),(0,0x54303650),(0,3),(0,0x04000000,0x0600010c)):
            valid,marker,snap,original,live,pending,script,magic,number,types=row
            expected=(valid==1 and marker==2 and snap==1 and 1<=original<=6 and live==3 and number==3 and magic in (0x54303650,0x54303641) and bool(types&0x04000000) and pending<3 and script==m.CONTINUATIONS[pending])
            self.assertEqual(self.fn(*row),int(expected),row);count+=1
        self.assertEqual(count,145152)
    def test_applied_command_and_upper_invalid_counts(self):
        for pending,script in enumerate(m.CONTINUATIONS):
            for original in (1,6):self.assertEqual(self.fn(1,2,1,original,3,pending,script,0x54303641,3,0x0600010c),1)
            for original in (7,255):self.assertEqual(self.fn(1,2,1,original,3,pending,script,0x54303641,3,0x0600010c),0)
    def test_original_called_once_and_no_memory_write(self):
        source=(ROOT/m.SOURCE).read_text()
        self.assertEqual(source.count('CIRCUS_PREVIOUS_PREDICATE)()'),1)
        self.assertIn('return previous;',source)
        for bad in ('->marker =','->snapshot_valid =','->party_count =','write8','write16','write32','memcpy','memset'):self.assertNotIn(bad,source)

class BuildTests(unittest.TestCase):
    def setUp(self):
        self.raw=b'\x00'*4+struct.pack('<I',0x08001001)+b'\xff'*248
        self.args=[self.raw,4,64,b'\x42'*32,0x08001001,0x08002001]
    def test_minimal_patch_only(self):
        new=m.bounded_patch(*self.args)
        self.assertEqual(new[:4],self.raw[:4]);self.assertEqual(new[8:64],self.raw[8:64]);self.assertEqual(new[96:],self.raw[96:])
        self.assertEqual(self.raw,self.args[0])
    def test_preimage_rejected(self):
        self.args[4]=0x08001003
        with self.assertRaises(ValueError):m.bounded_patch(*self.args)
    def test_not_erased_rejected(self):
        self.args[0]=self.raw[:64]+b'\x00'+self.raw[65:]
        with self.assertRaises(ValueError):m.bounded_patch(*self.args)
    def test_overlap_rejected(self):
        self.args[2]=4
        with self.assertRaises(ValueError):m.bounded_patch(*self.args)
    def test_unaligned_rejected(self):
        self.args[2]=65
        with self.assertRaises(ValueError):m.bounded_patch(*self.args)
    def test_arm_target_rejected(self):
        self.args[5]&=~1
        with self.assertRaises(ValueError):m.bounded_patch(*self.args)
    def test_oversize_rejected(self):
        self.args[3]=b'\x42'*(m.RESERVATION+1)
        with self.assertRaises(ValueError):m.bounded_patch(*self.args)
    def test_wrong_continuation_rejected(self):
        recipe={'launch_sites':[{'new':x-43,'size':43} for x in m.CONTINUATIONS]}
        self.assertEqual(m.continuation_contract(recipe),m.CONTINUATIONS)
        recipe['launch_sites'][1]['new']+=1
        with self.assertRaises(ValueError):m.continuation_contract(recipe)
    def test_runner_replaces_only_candidate_proof_and_scope(self):
        text=(ROOT/'scripts/pr16_circus_native.py').read_text();adapted=native.adapt_runner(text)
        self.assertEqual(adapted.count('verify_recipe(recipe)'),1)
        for kept in ('m.validate_guard(stdout,stderr,process)','protected source changed','previous.chooser.prepare(raw,out','for guard in previous.fixed.GUARDS:','accepted_native_cases_replayed=0'):
            self.assertIn(kept,adapted)
    def test_old_runner_anchor_rejected(self):
        with self.assertRaises(ValueError):native.adapt_runner('different runner')

if __name__=='__main__':unittest.main()
