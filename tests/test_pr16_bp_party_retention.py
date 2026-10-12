"""次戦限定predicateと旧失敗を保持する回帰。native証拠とは別。"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]

class RetentionScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        out=Path(cls.tmp.name)/'retention.so'
        subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-shared','-fPIC',
                        '-DFACILITY_PARTY_RETENTION_HOST_TEST',str(ROOT/'overlays/facility_party_retention/facility_party_retention.c'),'-o',str(out)],check=True,capture_output=True)
        cls.lib=ctypes.CDLL(str(out));cls.f=cls.lib.VegaFacilityKeepExchangedParty
        cls.f.argtypes=[ctypes.c_uint8]*6+[ctypes.c_uint32];cls.f.restype=ctypes.c_uint8
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_only_second_and_third_bound_continuations(self):
        for n in range(1,7):
            self.assertEqual(self.f(1,2,1,n,3,1,0x092cf6a5),1)
            self.assertEqual(self.f(1,2,1,n,3,2,0x092cf6e1),1)
    def test_all_invalid_ledger_markers_and_counts_fall_through(self):
        row=[1,2,1,6,3,1,0x092cf6a5]
        allowed=[{1},{2},{1},set(range(1,7)),{3},{1}]
        for index in range(6):
            for value in range(256):
                if value in allowed[index]:continue
                args=row.copy();args[index]=value
                self.assertEqual(self.f(*args),0,(index,value))
    def test_first_battle_ordinary_scripts_and_mismatched_reward_untouched(self):
        for script in (0,0x092cf669,0x092cf6a4,0x092cf6a6,0x092cf6e0,0x092cf6e2,0xffffffff):
            for pending in (0,1,2,3):self.assertEqual(self.f(1,2,1,6,3,pending,script),0)
        self.assertEqual(self.f(1,2,1,6,3,2,0x092cf6a5),0)
        self.assertEqual(self.f(1,2,1,6,3,1,0x092cf6e1),0)
    def test_runtime_has_no_party_or_ledger_write(self):
        text=(ROOT/'overlays/facility_party_retention/facility_party_retention.c').read_text()
        for term in ('memcpy(', 'memset(', 'VarSet(', '->marker =', '->reward_pending ='):
            self.assertNotIn(term,text)
        self.assertIn('return original;',text)
        self.assertIn('LEDGER_VALID() == 1u',text)

if __name__=='__main__':unittest.main()
