"""未受入3勝への別方策。read-only、再実行拒否、選択28条件を検査。"""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sustain',ROOT/'scripts/pr16_circus_sustain.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SustainTests(unittest.TestCase):
    def test_host_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            exe=Path(folder)/'policy'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/m.FIXTURE),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('PASS_CIRCUS_SUSTAIN_POLICY checks=28',result.stdout)
    def test_only_selector_changes(self):
        source='static void test(void){slot=wx_move_slot(c);br_trace(c,"turn-start");}'
        changed=m.adapt_policy(source)
        self.assertTrue(changed.startswith('static unsigned su_move_slot(struct mCore *c);'))
        self.assertEqual(changed.split('\n',1)[1].replace('su_move_slot','wx_move_slot'),source)
    def test_anchor_drift_rejected(self):
        for text in ('','slot=wx_move_slot(c);'*2,'slot=wx_move_slot(c); su_move_slot'):
            with self.assertRaises(ValueError):m.adapt_policy(text)
    def test_acceptance_or_same_policy_never_replayed(self):
        old=dict(classification='CIRCUS_THREE_WIN_DIAGNOSTIC_OPEN',recording_run=42)
        run=dict(id=42,status='completed',conclusion='failure')
        m.prior_allowed(old,run)
        for changes in ({'classification':'CIRCUS_THREE_WIN_CONTINUATIONS_9BP_SAVE_CONTINUE_VERIFIED'},
                        {'input_policy_id':m.POLICY},{'recording_run':41}):
            with self.assertRaises(ValueError):m.prior_allowed(dict(old,**changes),run)
        for changes in ({'status':'in_progress'},{'conclusion':'success'},{'conclusion':'action_required'}):
            with self.assertRaises(ValueError):m.prior_allowed(old,dict(run,**changes))
    def test_controller_is_input_and_read_only(self):
        text=(ROOT/m.HEADER).read_text()
        for bad in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'setRegister(', 'SC_OWNER', '0x03000EB8'):
            self.assertNotIn(bad,text)
        self.assertIn('wx_cursor(c,best);sp_entry(c,n,best);',text)
        self.assertIn('#define wx_team su_team',text)
        self.assertIn('BATTLE_CORE_MON_STATUS1',text)
if __name__=='__main__':unittest.main()
