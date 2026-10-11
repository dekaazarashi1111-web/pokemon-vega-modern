"""29戦目の通常先発維持と、受入済み28勝のraw prefixを限定検証する。"""
import ctypes
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_battle29_policy as p

class Battle29Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=(ROOT/'evidence/pr16_circus_battle28/35471833294/execution/circus-continuous-30-save.stderr').read_bytes()
        cls.text=(ROOT/'evidence/pr16_circus_battle25/35468164696/original-generated/pr16_streak_policy.c').read_text()
        cls.header=(ROOT/'tools/mgba_pr16_circus_battle25.h').read_text()
        cls.tmp=tempfile.TemporaryDirectory();base=Path(cls.tmp.name)
        source='#include <stdint.h>\n'+p.HELPER+'\nunsigned check(unsigned s,unsigned a,unsigned b,unsigned c,unsigned d,unsigned e,unsigned f,unsigned g,unsigned h){return sr_hold(s,a,b,c,d,e,f,g,h);}\n'
        (base/'case.c').write_text(source)
        subprocess.run(['cc','-std=c11','-shared','-fPIC','-Wall','-Wextra','-Werror',str(base/'case.c'),'-o',str(base/'case.so')],capture_output=True,check=True)
        cls.lib=ctypes.CDLL(str(base/'case.so'));cls.lib.check.argtypes=[ctypes.c_uint]*9;cls.lib.check.restype=ctypes.c_uint
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def synthetic(self):
        before=self.old[:self.old.index(b'CIRCUS_TACTICAL begin frame=460169 ')]
        return before+p.MARKER+b'{"frame":460169,"streak":28,"attacks":34816,"hp":182,"maxhp":182,"wanted":12}\n'
    def test_healthy_water_ice_matchup(self):
        self.assertEqual(self.lib.check(28,11,11,11,11,(1<<15)|(1<<11),182,182,12),1)
        self.assertEqual(self.lib.check(29,11,11,11,11,1<<15,92,182,12),1)
    def test_all_accepted_prefix_battles_disabled(self):
        for streak in range(28):self.assertEqual(self.lib.check(streak,11,11,11,11,1<<15,182,182,12),0)
    def test_rejects_bad_types_health_moves_and_target(self):
        good=[28,11,11,11,11,1<<15,182,182,12]
        for at,bad in [(1,12),(2,15),(3,10),(4,12),(5,1<<11),(5,(1<<15)|(1<<25)),(6,91),(6,0),(6,183),(7,0),(8,25)]:
            args=good.copy();args[at]=bad
            self.assertEqual(self.lib.check(*args),0,args)
    def test_parent_adapter_exact_and_change_only_host_input(self):
        old=p.parent.adapt(self.text,self.header)
        self.assertEqual(hashlib.sha256(old.encode()).hexdigest(),p.POLICY_SHA)
        new=p.adapt(self.text,self.header)
        self.assertEqual(new.count('CIRCUS_SWITCH_RISK '),1)
        self.assertIn('CIRCUS_SWITCH_HANDOFF ',new)
        self.assertIn('tp_seen=1U;tp_foe=pid;tp_foe_ot=ot;return;',new)
        addition=new.replace(p.HELPER+'\n','')
        start=addition.index('    if(sr_hold(');end=addition.index('    uint32_t active=',start)
        self.assertEqual(addition[:start]+addition[end:],old)
    def test_rejects_changed_or_double_adapted_source(self):
        with self.assertRaises(ValueError):p.adapt(self.text+'\n',self.header)
        with self.assertRaises(ValueError):p.adapt(p.adapt(self.text,self.header),self.header)
    def test_previous_failed_run_retains_scoped_save_success(self):
        d=p.original(self.old)
        self.assertEqual((d['settled_wins'],d['settled_losses']),(28,1))
        self.assertTrue(d['normal_save_observed'] and d['fresh_continue_observed'])
        with self.assertRaises(ValueError):p.original(self.old+b'\n')
    def test_exact_134_event_and_byte_prefix(self):
        proof=p.prefix_proof(self.old,self.synthetic())
        self.assertEqual(proof['exact_event_count'],134)
        self.assertEqual(proof['continuation_prefix_wins'],28)
    def test_rejects_forged_boundary_or_early_input_change(self):
        good=self.synthetic()
        for bad in [good.replace(b'"frame":',b'"frames":',1),good.replace(b'"streak":28,"attacks"',b'"streak":27,"attacks"'),good.replace(b'"attacks":34816',b'"attacks":2048'),good.replace(b'"hp":182',b'"hp":181')]:
            with self.assertRaises((ValueError,KeyError)):p.prefix_proof(self.old,bad)
        with self.assertRaises(ValueError):p.prefix_proof(self.old,self.old)

if __name__=='__main__':unittest.main()
