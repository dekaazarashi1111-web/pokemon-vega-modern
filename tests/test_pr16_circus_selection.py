from pathlib import Path
import inspect
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_selection as t
class SelectionTests(unittest.TestCase):
    def test_saved_count_selected_count_native_completion_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            exe=Path(directory)/'selection'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/t.FIXTURE),'-o',str(exe)],check=True,capture_output=True)
            p=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('combinations=13056',p.stdout)
    def test_actual_nine_rows_reject_script_zero_hypothesis(self):
        result=t.diagnose((ROOT/t.RAW).read_bytes())
        self.assertTrue(result['script_zero_field_drop_rejected']);self.assertEqual(result['original_party_count'],1)
        self.assertEqual(result['selected_party_count'],3);self.assertEqual(result['transition_rows'],9)
    def test_actual_transition_drift_rejected(self):
        raw=(ROOT/t.RAW).read_bytes()
        for before,after in [(b'"script":167726509',b'"script":0'),(b'"weather_state":2',b'"weather_state":5')]:
            self.assertIn(before,raw)
            with self.subTest(before=before),self.assertRaises(ValueError):t.diagnose(raw.replace(before,after))
    def test_runtime_patch_is_exact_and_preserves_snapshot_read(self):
        text='#include "circus_drought_launch.h"\nc.count = f->party_count;\nCircusDroughtInitializeLaunch(&c, w, DroughtOriginal, DroughtInitVars, DroughtStep);'
        result=t.repair(text);self.assertIn('c.count = f->party_count;',result);self.assertIn('READ8(0x02023F89u)',result)
        with self.assertRaises(ValueError):t.repair(result)
    def test_context_must_distinguish_saved1_from_selected3(self):
        r=dict(frame=285428,saved_count=1,selected_count=3,marker=2,snapshot=1,outcome=0,script=0x09FF4DAD,current=17,phase=2)
        def raw(v):return b'CIRCUS_SELECTION_CONTEXT '+t.stable(v).replace(b'\n',b'')+b'\n'
        self.assertEqual(t.selection_context(raw(r)),r)
        for k,v in [('saved_count',3),('selected_count',1),('outcome',1),('snapshot',True)]:
            bad=dict(r);bad[k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):t.selection_context(raw(bad))
        with self.assertRaises(ValueError):t.selection_context(raw(r)*2)
    def test_guard_has_no_game_state_writes_and_preserves_win_delegate(self):
        text=(ROOT/t.HEADER).read_text()
        self.assertNotRegex(text,r'(?:w\[[^\]]+\]|c->\w+)\s*=(?!=)')
        self.assertIn('CircusDroughtInitialize(c, w, original, init_vars, step);',text)
        self.assertIn('c->count >= 1u && c->count <= 6u',text)
        self.assertIn('selected_count == 3u',text)
    def test_no_prior_boundary_or_cpu_native_is_replayed(self):
        text=inspect.getsource(t.native)
        self.assertNotIn('boundary.native()',text);self.assertNotIn('launch.native()',text)
        self.assertIn('genuine 30-win target remains open',text)
    def test_watch_is_read_only_nonterminating_and_composes_once(self):
        import pr16_circus_win_return_trace as trace
        header=(ROOT/t.WATCH).read_text();text='void fw_frame(void){b_frame(c,keys);}\n#define b_frame fw_frame\n'
        result=t.boundary.compose_boundary_watch(text,header,trace.chained_watch)
        self.assertEqual(result.count('#define b_frame lb_frame'),1)
        self.assertNotIn('bp_require(c,false',header);self.assertNotIn('write8(',header);self.assertIn('BP_F(party_count)',header)
    def test_configure_reentry_keeps_child_command_and_source_scope(self):
        for _ in range(2):
            d,b=t.configure();self.assertEqual(b.SELF,t.SELF);self.assertEqual(d.SELF,t.SELF)
            self.assertTrue(set(t.NEW)<=set(d.FILES));self.assertEqual(len(d.FILES),len(set(d.FILES)))
if __name__=='__main__':unittest.main()
