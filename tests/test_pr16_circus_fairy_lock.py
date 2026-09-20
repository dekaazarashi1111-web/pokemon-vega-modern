"""Fairy Lockのhost入力方針のみ検査。旧getter/ARM/native prefixは実行しない。"""
import copy
import ctypes
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_circus_fairy_lock as f


class FieldPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name)
        (root/'test.c').write_text('#define CIRCUS_FAIRY_LOCK_HOST_TEST\n#include "'+str(f.ROOT/f.HEADER)+'"\nunsigned probe(unsigned s,uint32_t f,uint32_t t){return fl_defer(s,f,t);}\n')
        subprocess.run(['cc','-std=c11','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',str(root/'test.c'),'-o',str(root/'test.so')],check=True,capture_output=True)
        cls.lib=ctypes.CDLL(str(root/'test.so'));cls.probe=cls.lib.probe
        cls.probe.argtypes=[ctypes.c_uint,ctypes.c_uint32,ctypes.c_uint32];cls.probe.restype=ctypes.c_uint
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_observed_field(self):self.assertEqual(self.probe(31,0x804000,0x0600010c),1)
    def test_exact_boundary(self):self.assertEqual(self.probe(30,0x4000,0x04000000),1)
    def test_accepted_30win_prefix_unchanged(self):
        for streak in range(30):self.assertEqual(self.probe(streak,0x4000,0x04000000),0)
    def test_other_facility_untouched(self):self.assertEqual(self.probe(31,0x4000,0x0200010c),0)
    def test_other_effect_untouched(self):self.assertEqual(self.probe(31,0x80000200,0x04000000),0)
    def test_no_effect(self):self.assertEqual(self.probe(31,0,0x04000000),0)
    def test_suppression_and_lock(self):self.assertEqual(self.probe(31,0x80004000,0x04000000),1)
    def test_later_streak(self):self.assertEqual(self.probe(65535,0x4000,0x04000000),1)


class GeneratedBoundary(unittest.TestCase):
    def setUp(self):
        root=f.ROOT/f'evidence/pr16_circus_getter/{f.RUN}/execution/generated'
        self.files={n:(root/n).read_bytes() for n in ('pr16_streak_policy.c','controller.c','getter_suppression.h','ss_routes.h')}
    def test_input_immutable(self):
        before=copy.deepcopy(self.files);f.adapt(self.files);self.assertEqual(before,self.files)
    def test_only_three_source_edits(self):
        out=f.adapt(self.files);self.assertEqual({n for n in out if out[n]!=self.files[n]},set(self.files)-{'ss_routes.h'})
    def test_forced_switch_unchanged(self):
        before=self.files['controller.c'].split(b'static void sc_switch(')[1].split(b'static unsigned sc_finish_battle')[0]
        after=f.adapt(self.files)['controller.c'].split(b'static void sc_switch(')[1].split(b'static unsigned sc_finish_battle')[0]
        self.assertEqual(before,after)
    def test_no_old_draw_sweep(self):
        text=f.adapt(self.files)['getter_suppression.h'];self.assertIn(b'attempt=3U;attempt<4U',text);self.assertNotIn(b'attempt<64U',text)
    def test_no_duplicate_cpu_trace(self):
        out=f.adapt(self.files)
        self.assertNotIn(b'ss_observe',out['getter_suppression.h'])
        self.assertNotIn(b'#include "mgba_pr16_circus_getter_trace.h"',out['controller.c'])
    def test_bootstrap_stays_forbidden(self):self.assertIn(b'a_require(!bootstrap',f.adapt(self.files)['getter_suppression.h'])
    def test_double_application_rejected(self):
        with self.assertRaises(ValueError):f.adapt(f.adapt(self.files))
    def test_changed_owner_boundary_rejected(self):
        self.files['pr16_streak_policy.c']=self.files['pr16_streak_policy.c'].replace(b'if(streak<15U)return;',b'if(streak<14U)return;')
        with self.assertRaises(ValueError):f.adapt(self.files)


class KnownDraw(unittest.TestCase):
    def setUp(self):
        self.row=dict(attempt=3,delay=51,frame=1000,current=30,best=30,bp=90,counter=3,flags=0x80000200,types=100663564,newbs=33650228,target=True)
        self.old=[{}, {}, {},copy.deepcopy(self.row)]
    def test_same_target_new_frame(self):self.row['frame']=2000;self.assertTrue(f.validate_draws([self.row],self.old))
    def test_different_effect_rejected(self):
        self.row['flags']=0x80000400
        with self.assertRaises(ValueError):f.validate_draws([self.row],self.old)
    def test_delay_mismatch_rejected(self):
        self.row['delay']=50
        with self.assertRaises(ValueError):f.validate_draws([self.row],self.old)
    def test_boolean_type_rejected(self):
        self.row['target']=1
        with self.assertRaises(ValueError):f.validate_draws([self.row],self.old)
    def test_repeated_draw_rejected(self):
        with self.assertRaises(ValueError):f.validate_draws([self.row,self.row],self.old)
    def test_prior_identity_shape_rejected(self):
        with self.assertRaises(ValueError):f.validate_draws([self.row],self.old[1:])


if __name__=='__main__':unittest.main()
