"""実8勝原本・高命中境界・実行技feedbackの限定回帰。emulatorは呼ばない。"""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_reliability as task

class ReliabilityTests(unittest.TestCase):
    def headers(self):return {p:(ROOT/p).read_text() for p in task.c.HEADERS}
    def policy(self):return task.policy_text('slot=wx_move_slot(c);',self.headers())
    def test_pure_c_expected_damage_accuracy_and_block_boundaries(self):
        source=r'''#include <assert.h>
#include <stdint.h>
#include "HEADER"
int main(void){
 uint64_t s[4]={4185000ULL,4347750ULL,771428ULL,0};unsigned a[4]={100,85,100,0};
 assert(rl_pick(1,0,s,a)==0);assert(rl_pick(1,1,s,a)==1);
 assert(rl_pick(0,0,s,a)==0);assert(rl_pick(4,0,s,a)==4);
 s[0]=3912975ULL;assert(rl_pick(1,0,s,a)==0);--s[0];assert(rl_pick(1,0,s,a)==1);
 s[0]=0;assert(rl_pick(1,0,s,a)==1);s[1]=0;assert(rl_pick(1,0,s,a)==1);
 s[0]=s[1]=100;s[2]=100;a[0]=a[2]=100;a[1]=85;
 assert(rl_pick(1,0,s,a)==0);assert(rl_pick(1,1,s,a)==2);assert(rl_pick(1,5,s,a)==1);
 a[0]=0;a[2]=101;assert(rl_pick(1,0,s,a)==1);
 s[0]=s[1]=UINT64_MAX;a[0]=100;a[1]=85;assert(rl_pick(1,0,s,a)==0);
 for(unsigned blocked=0;blocked<16;++blocked){
  unsigned actual=rl_pick(1,blocked,s,a);
  assert(actual==1 || !(blocked&(1U<<actual)));
 }
 return 0;
}'''.replace('HEADER',(ROOT/task.HEADER).as_posix())
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'test.c').write_text(source)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            subprocess.run([str(p/'test')],check=True,capture_output=True)
    def test_former_eight_wins_are_not_promoted_to_thirty(self):
        old=json.loads((ROOT/task.OLD).read_bytes())
        self.assertEqual(old['native']['status'],'PASS_CIRCUS_SCOPED_NATIVE')
        self.assertEqual((old['scoped_result']['wins'],old['scoped_result']['losses'],old['scoped_result']['bp_earned']),(8,1,18))
        self.assertFalse(old['genuine_30_wins_verified'])
    def test_exact_eight_win_prefix_and_ninth_launch(self):
        events=task.probe.parse((ROOT/(task.RAW+'.stderr')).read_bytes())
        prefix=(ROOT/task.previous.PREFIX).read_bytes()
        task.verify_prefix(events,prefix)
        for at,key in ((1,'frame'),(20,'frame'),(39,'frame')):
            changed=json.loads(json.dumps(events));changed[at][key]+=1
            with self.assertRaises(ValueError):task.verify_prefix(changed,prefix)
    def test_selected_move_feedback_not_superseded_move(self):
        text=self.policy()
        order=[text.index('if(streak>=8U)actual=rl_pick'),text.index('rr_memory.slot=actual;'),text.index('rr_memory.damaging=',text.index('rr_memory.slot=actual;')),text.index('CIRCUS_RELIABILITY frame=')]
        self.assertEqual(order,sorted(order))
        self.assertIn('rr_memory.pp=read8(c,own+BATTLE_MON_PP_OFFSET+actual)',text)
        self.assertIn('rr_memory.stalls[i]>=2U',text)
    def test_first_eight_boundary_and_single_expansion(self):
        text=self.policy()
        self.assertEqual(text.count('if(streak>=8U)actual=rl_pick'),1)
        self.assertEqual(text.count('static unsigned rl_pick('),1)
        self.assertEqual(text.count('slot=rr_move_slot(c);'),1)
        self.assertIn('selected=streak<3U?fp_move_slot(c):wx_move_slot(c)',text)
        self.assertEqual(text.count('CIRCUS_RELIABILITY frame='),1)
    def test_configured_module_reimport_stays_idempotent(self):
        expected=self.policy()
        with patch.object(task.c,'policy_text',task.policy_text),patch.object(task.c,'verify_prefix',task.verify_prefix):
            spec=importlib.util.spec_from_file_location('reliability_again',ROOT/task.SELF)
            again=importlib.util.module_from_spec(spec);spec.loader.exec_module(again)
            self.assertEqual(again.policy_text('slot=wx_move_slot(c);',self.headers()),expected)
    def test_missing_selector_or_feedback_anchor_fails_closed(self):
        with self.assertRaises(ValueError):task.policy_text('',self.headers())
        with patch.object(task,'original_policy',return_value='slot=rr_move_slot(c);'):
            with self.assertRaises(ValueError):self.policy()
    def test_no_host_state_injection_or_new_native_case(self):
        source=(ROOT/task.SELF).read_text();header=(ROOT/task.HEADER).read_text()
        for token in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'loadState('):
            self.assertNotIn(token,source+header)
        self.assertIn('def native():configure();c.native()',source)
        self.assertEqual(task.probe.CASE,'circus-continuous-30-save')
        self.assertEqual(task.probe.SHA,'3101772a3b91fe0461f200bbd3faf19f01064132bd3d8db9b0fe8f747445b399')

if __name__=='__main__':unittest.main()
