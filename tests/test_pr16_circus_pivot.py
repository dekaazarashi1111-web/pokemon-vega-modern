"""第3戦だけの通常任意交代。前2戦無変更/個体証拠/再実行拒否。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pivot',ROOT/'scripts/pr16_circus_pivot.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def rows():
    return [dict(label='begin',frame=41181,**{'from':0},target=1,pid=123,ot=456,species=92),
            dict(label='done',frame=43000,**{'from':0},target=1,pid=123,ot=456,species=92)]
def raw(value):return ''.join('CIRCUS_PIVOT '+json.dumps(r)+'\n' for r in value).encode()
class PivotTests(unittest.TestCase):
    def test_host_policy_56_conditions(self):
        with tempfile.TemporaryDirectory() as folder:
            exe=Path(folder)/'policy'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/m.FIXTURE),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('PASS_CIRCUS_PIVOT_POLICY checks=56',result.stdout)
    def test_only_selector_changes(self):
        source='static void test(void){slot=wx_move_slot(c);br_trace(c,"turn-start");}'
        changed=m.adapt_policy(source)
        self.assertTrue(changed.startswith('static unsigned pv_move_slot(struct mCore *c);'))
        self.assertEqual(changed.split('\n',1)[1].replace('pv_move_slot','wx_move_slot'),source)
    def test_anchor_drift_rejected(self):
        for text in ('','slot=wx_move_slot(c);'*2,'slot=wx_move_slot(c); pv_move_slot'):
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
    def test_normal_input_and_read_only(self):
        text=(ROOT/m.HEADER).read_text()
        for bad in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'setRegister(', '0x03000EB8'):
            self.assertNotIn(bad,text)
        self.assertIn('n_cursor(c,2U)',text)
        self.assertIn('wx_cursor(c,target)',text)
        self.assertIn('return ef_move_slot(c)',text)
        self.assertIn('read32(c,mon+0x48U)==pid',text)
    def test_pivot_identity_contract(self):
        self.assertEqual(m.pivot_events(raw(rows()))['voluntary_switches'],1)
        for changes in ({'frame':1},{'pid':9},{'target':True},{'target':3},{'species':0},{'extra':0}):
            mutated=rows();mutated[1].update(changes)
            with self.assertRaises(ValueError):m.pivot_events(raw(mutated))
        for value in ([],rows()[:1],rows()+rows(),list(reversed(rows()))):
            with self.assertRaises(ValueError):m.pivot_events(raw(value))
    def test_pivot_inside_third_battle_only(self):
        def event(label,frame,battle):return ('CIRCUS_STREAK '+json.dumps(dict(label=label,frame=frame,battle=battle))+'\n').encode()
        blob=event('action',41181,2)+raw(rows())+event('outcome',55000,2)
        result=dict(switches=3,forced_identity_checks=3)
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            self.assertEqual(m.validate_pivot(result,blob,out),result)
            self.assertEqual(json.loads((out/'pivot-proof.json').read_bytes())['voluntary_switches'],1)
            with self.assertRaises(ValueError):m.validate_pivot(dict(result,forced_identity_checks=2),blob,out)
            with self.assertRaises(ValueError):m.validate_pivot(result,event('action',42000,2)+raw(rows())+event('outcome',55000,2),out)
if __name__=='__main__':unittest.main()
