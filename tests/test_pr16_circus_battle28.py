"""28戦目の限定handoff、原本保持、継続prefixの改作拒否。"""
import ctypes
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_battle28_policy as p
OLD=ROOT/'evidence/pr16_circus_battle25/35468164696'

class Battle28Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(OLD/'execution/circus-continuous-30-save.stderr').read_bytes()
        cls.generated=(OLD/'original-generated/pr16_streak_policy.c').read_text()
        cls.header=(ROOT/'tools/mgba_pr16_circus_battle25.h').read_text()
        cls.tmp=tempfile.TemporaryDirectory();base=Path(cls.tmp.name)
        source=p.HELPER+'\nunsigned check(unsigned s,unsigned a,unsigned m,unsigned h,unsigned i,unsigned o){return sh_kind(s,a,m,h,i,o)+0U*sh_pending;}\n'
        (base/'case.c').write_text(source)
        subprocess.run(['cc','-std=c11','-shared','-fPIC','-Wall','-Wextra','-Werror',str(base/'case.c'),'-o',str(base/'case.so')],check=True,capture_output=True)
        cls.lib=ctypes.CDLL(str(base/'case.so'));cls.lib.check.argtypes=[ctypes.c_uint]*6;cls.lib.check.restype=ctypes.c_uint
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def synthetic_success(self):
        before=self.raw[:self.raw.index(b'BREED Circus tactical selected individual did not survive to action')]
        return before+p.MARKER+b'{"frame":452000,"streak":27,"kind":1,"hp":0,"same_individual":1}\n'
    def test_original_failed_run_is_27_wins_not_saved(self):
        d=p.diagnostic(self.raw,original=True)
        self.assertEqual((d['events'],d['settled_wins'],d['returned_batches']),(130,27,9))
        self.assertFalse(d['lifecycle_accepted']);self.assertFalse(d['fresh_continue_observed'])
    def test_original_rejects_mutated_bytes(self):
        with self.assertRaises(ValueError):p.diagnostic(self.raw+b'\n',original=True)
    def test_real_25_adapter_matches_saved_parent(self):
        actual=p.previous.adapt(self.generated,self.header).encode()
        self.assertEqual(hashlib.sha256(actual).hexdigest(),'5356b9c74949aafaacbc5fdff65d00f9776b6ce675ddbea095a34d34b24be699')
    def test_adapter_hands_off_at_both_callers(self):
        text=p.adapt(self.generated,self.header)
        self.assertEqual(text.count('static unsigned sh_pending;'),1)
        self.assertLess(text.index('static unsigned sh_pending;'),text.index('static void br_move('))
        self.assertIn('if(sh_pending){bp_require(c,slot==4U && !n_action(c)',text)
        self.assertIn('if(sh_pending){bp_require(c,!n_action(c)',text)
        self.assertIn('Circus tactical selected individual did not survive to action',text)
        self.assertEqual(text.count('CIRCUS_SWITCH_HANDOFF '),1)
    def test_adapter_rejects_nonoriginal_or_duplicate(self):
        with self.assertRaises(ValueError):p.adapt(self.generated+'\n',self.header)
        with self.assertRaises(ValueError):p.adapt(p.adapt(self.generated,self.header),self.header)
    def test_kind_requires_real_faint_identity_and_party(self):
        fn=self.lib.check
        self.assertEqual(fn(27,0,1,0,1,0),1)
        for s in range(27):self.assertEqual(fn(s,0,1,0,1,0),0)
        for args in [(27,1,1,0,1,0),(27,0,0,0,1,0),(27,0,1,1,1,0),(27,0,1,0,0,0),(27,0,1,0,1,3)]:self.assertEqual(fn(*args),0)
    def test_kind_only_native_win_loss_handoff(self):
        fn=self.lib.check
        for outcome in [1,2]:
            self.assertEqual(fn(27,0,0,0,0,outcome),2)
            self.assertEqual(fn(26,0,0,0,0,outcome),0)
            self.assertEqual(fn(27,1,0,0,0,outcome),0)
        self.assertEqual(fn(27,0,0,0,0,4),0)
    def test_exact_130_event_prefix(self):
        proof=p.prefix_proof(self.raw,self.synthetic_success())
        self.assertEqual(proof['exact_event_count'],130)
        self.assertEqual(proof['continuation_prefix_wins'],27)
    def test_prefix_rejects_early_change_and_forged_marker(self):
        new=self.synthetic_success()
        for bad in [new.replace(b'"frame":',b'"frames":',1),new.replace(b'"streak":27,"kind":1',b'"streak":26,"kind":1'),new.replace(b'"same_individual":1}',b'"same_individual":0}')]:
            with self.assertRaises((ValueError,KeyError)):p.prefix_proof(self.raw,bad)
        with self.assertRaises(ValueError):p.prefix_proof(self.raw,self.raw)

if __name__=='__main__':unittest.main()
