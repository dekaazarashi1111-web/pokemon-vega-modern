"""29戦目の初手維持をHP閾値まで再評価し、受入済みprefixを限定検証する。"""
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_battle29_recheck_policy as p

class Battle29RecheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=(ROOT/'evidence/pr16_circus_battle29/35473090294/execution/circus-continuous-30-save.stderr').read_bytes()
        cls.text=(ROOT/'evidence/pr16_circus_battle25/35468164696/original-generated/pr16_streak_policy.c').read_text()
        cls.header=(ROOT/'tools/mgba_pr16_circus_battle25.h').read_text()
        cls.tmp=tempfile.TemporaryDirectory();base=Path(cls.tmp.name)
        source='#include <stdint.h>\n'+p.HELPER+'\nunsigned check(unsigned s,unsigned h,unsigned hp,unsigned maxhp){return hr_defer_seen(s,h,hp,maxhp);}\n'
        (base/'case.c').write_text(source)
        subprocess.run(['cc','-std=c11','-shared','-fPIC','-Wall','-Wextra','-Werror',str(base/'case.c'),'-o',str(base/'case.so')],capture_output=True,check=True)
        cls.lib=ctypes.CDLL(str(base/'case.so'));cls.lib.check.argtypes=[ctypes.c_uint]*4;cls.lib.check.restype=ctypes.c_uint
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def synthetic(self):
        at=self.old.index(p.parent.MARKER);end=self.old.index(b'\n',at)+1
        first={"frame":460169,"streak":28,"hp":182,"maxhp":182,"deferred":1,"seen":0,"foe":1,"foe_ot":2}
        last={"frame":468129,"streak":28,"hp":102,"maxhp":182,"deferred":1,"seen":0,"foe":3,"foe_ot":4}
        return (self.old[:end]+p.MARKER+json.dumps(first,separators=(',',':')).encode()+b'\n'
                +p.MARKER+json.dumps(last,separators=(',',':')).encode()+b'\n'
                +b'CIRCUS_TACTICAL begin frame=469713 streak=28 foe=3 foe_ot=4 target_pid=5 target_ot=6 species=2 attack_type=12 count=1\n')
    def test_defers_seen_only_while_healthy_hold_applies(self):
        self.assertEqual(self.lib.check(28,1,182,182),1)
        self.assertEqual(self.lib.check(29,1,92,182),1)
        self.assertEqual(self.lib.check(28,1,91,182),0)
    def test_rejects_old_streak_nonhold_and_invalid_health(self):
        for args in [(27,1,182,182),(28,0,182,182),(28,1,0,182),(28,1,183,182),(28,1,1,0)]:
            self.assertEqual(self.lib.check(*args),0,args)
    def test_parent_adapter_exact_and_only_seen_latch_changes(self):
        old=p.parent.adapt(self.text,self.header)
        self.assertEqual(hashlib.sha256(old.encode()).hexdigest(),p.POLICY_SHA)
        new=p.adapt(self.text,self.header)
        self.assertEqual(new.count('CIRCUS_HOLD_RECHECK '),1)
        self.assertEqual(new.count('CIRCUS_SWITCH_RISK '),1)
        block=r'''        unsigned deferred=hr_defer_seen(streak,1U,read16(c,own+BATTLE_CORE_MON_HP),read16(c,own+0x2CU));
        fprintf(stderr,"CIRCUS_HOLD_RECHECK {\"frame\":%u,\"streak\":%u,\"hp\":%u,\"maxhp\":%u,\"deferred\":%u,\"seen\":%u,\"foe\":%u,\"foe_ot\":%u}\n",
            b_frames,streak,read16(c,own+BATTLE_CORE_MON_HP),read16(c,own+0x2CU),deferred,tp_seen,pid,ot);
        if(!deferred){tp_seen=1U;tp_foe=pid;tp_foe_ot=ot;}
        return;
'''
        reduced=new.replace(p.HELPER+'\n','').replace(block,'        tp_seen=1U;tp_foe=pid;tp_foe_ot=ot;return;\n')
        self.assertEqual(reduced,old)
    def test_rejects_changed_or_double_adapted_source(self):
        with self.assertRaises(ValueError):p.adapt(self.text+'\n',self.header)
        with self.assertRaises(ValueError):p.adapt(p.adapt(self.text,self.header),self.header)
    def test_previous_battle29_identity_and_lifecycle(self):
        d=p.original(self.old)
        self.assertEqual((d['settled_wins'],d['settled_losses']),(28,1))
        self.assertTrue(d['normal_save_observed'] and d['fresh_continue_observed'])
        with self.assertRaises(ValueError):p.original(self.old+b'\n')
    def test_exact_134_event_and_byte_prefix(self):
        proof=p.prefix_proof(self.old,self.synthetic())
        self.assertEqual(proof['exact_event_count'],134)
        self.assertEqual(proof['continuation_prefix_wins'],28)
    def test_threshold_switch_is_bound_to_half_hp_recheck(self):
        proof=p.prefix_proof(self.old,self.synthetic())
        self.assertEqual(proof['last_deferred_hold']['hp'],102)
        self.assertEqual(proof['threshold_switch_frame'],469713)
    def test_rejects_forged_marker_or_missing_switch(self):
        good=self.synthetic()
        bads=[good.replace(b'"frame":460169',b'"frame":460170',1),
              good.replace(b'"deferred":1',b'"deferred":0',1),
              good.replace(b'"hp":102',b'"hp":91',1),
              good.replace(b'frame=469713',b'frame=469714',1)]
        for bad in bads:
            with self.assertRaises((ValueError,KeyError)):p.prefix_proof(self.old,bad)
    def test_marker_parser_ignores_other_traces(self):
        rows=p.marker_rows(b'noise\n'+p.MARKER+b'{"frame":1}\n')
        self.assertEqual(rows,[{'frame':1}])

if __name__=='__main__':unittest.main()
