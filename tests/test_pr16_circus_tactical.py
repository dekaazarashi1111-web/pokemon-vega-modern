"""15勝原本保持と、16戦目からの通常交代の限定回帰。nativeは実行しない。"""
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
import pr16_circus_tactical as task

class TacticalTests(unittest.TestCase):
    def headers(self):return {p:(ROOT/p).read_text() for p in task.c.HEADERS}
    def policy(self):return task.policy_text('slot=wx_move_slot(c);',self.headers())
    def compile_run(self,source):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'test.c').write_text(source.replace('HEADER',(ROOT/task.HEADER).as_posix()))
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            subprocess.run([str(p/'test')],check=True,capture_output=True)
    def test_pure_request_and_rank_boundaries(self):
        self.compile_run(r'''#include <assert.h>
#define CIRCUS_TACTICAL_HOST_TEST
#include "HEADER"
int main(void){
 for(unsigned n=0;n<15;++n)assert(tp_request(n,11,11,0,0,1U<<7)==25);
 assert(tp_request(15,11,11,0,0,1U<<7)==17);
 assert(tp_request(15,17,17,0,0,1U<<7)==25);
 assert(tp_request(15,11,11,0,0,(1U<<7)|(1U<<1))==25);
 assert(tp_request(15,17,17,10,10,1U<<10)==11);
 assert(tp_request(15,11,11,10,10,1U<<10)==25);
 assert(tp_request(15,10,10,11,11,1U<<11)==12);
 assert(tp_request(15,11,11,12,12,1U<<12)==10);
 assert(tp_request(15,11,11,12,3,1U<<12)==25);
 assert(tp_rank(80,100,182,141,141)==1456000ULL);
 assert(tp_rank(80,100,182,0,141)==0);
 assert(tp_rank(80,100,182,142,141)==0);
 assert(tp_rank(80,101,182,141,141)==0);
 assert(tp_rank(80,0,182,141,141)==1456000ULL);
 assert(tp_rank(0,100,182,141,141)==0);
 assert(tp_rank(255,100,65535,65535,65535)==1671142500ULL);
 return 0;
}''')
    def test_entire_runtime_header_compiles_without_host_write_functions(self):
        self.compile_run(r'''#include <assert.h>
#include <stdint.h>
#include <stdio.h>
struct mCore {unsigned unused;};
enum { ADDR_BATTLE_MONS=0x2000000,BATTLE_MON_SIZE=88,BATTLE_CORE_MOVE_TABLE_REPOINT=0x80001CC,
 BATTLE_MON_MOVES_OFFSET=12,BATTLE_MON_PP_OFFSET=36,BATTLE_CORE_MON_TYPE1=33,BATTLE_CORE_MON_TYPE2=34,
 QOL_PLAYER_PARTY=0x2000200,QOL_PLAYER_PARTY_COUNT=0x2000201,BATTLE_CORE_MAIN_CALLBACK2=0x2000300,
 P02S_CB2_PARTY=0x8123456,QOL_KEY_A=1,QOL_KEY_B=2,BATTLE_CORE_BATTLE_OUTCOME=0x2000400,BATTLE_CORE_MON_HP=40};
static unsigned b_frames;
static unsigned read8(struct mCore*c,uint32_t p){(void)c;(void)p;return 0;}
static unsigned read16(struct mCore*c,uint32_t p){(void)c;(void)p;return 14;}
static uint32_t read32(struct mCore*c,uint32_t p){(void)c;(void)p;return 0;}
static unsigned n_action(struct mCore*c){(void)c;return 1;}
static void bp_require(struct mCore*c,unsigned ok,const char*s){(void)c;(void)s;assert(ok);}
static void n_cursor(struct mCore*c,unsigned p){(void)c;(void)p;}
static void b_press(struct mCore*c,unsigned p,unsigned n){(void)c;(void)p;(void)n;}
static void b_frame(struct mCore*c,unsigned p){(void)c;(void)p;}
static void b_frames_run(struct mCore*c,unsigned p,unsigned n){(void)c;(void)p;(void)n;}
static void wx_cursor(struct mCore*c,unsigned p){(void)c;(void)p;}
static unsigned mi_find(unsigned n,const uint32_t*p,const uint32_t*t,const uint16_t*s,uint32_t pid,uint32_t ot,unsigned species){(void)n;(void)p;(void)t;(void)s;(void)pid;(void)ot;(void)species;return 3;}
#include "HEADER"
int main(void){struct mCore c={0};tp_consider(&c);assert(!tp_seen && !tp_switches);return 0;}
''')
    def test_fifteen_win_original_remains_failed_target(self):
        old=json.loads((ROOT/task.OLD).read_bytes())
        self.assertEqual(old['native']['status'],'PASS_CIRCUS_SCOPED_NATIVE')
        self.assertEqual((old['scoped_result']['wins'],old['scoped_result']['losses'],old['scoped_result']['bp_earned']),(15,1,45))
        self.assertFalse(old['genuine_30_wins_verified'])
        self.assertEqual(old['recording_run'],35428983641)
    def test_exact_fifteen_wins_and_sixteenth_launch(self):
        events=task.probe.parse((ROOT/(task.RAW+'.stderr')).read_bytes())
        prefix=(ROOT/task.previous.previous.PREFIX).read_bytes();task.verify_prefix(events,prefix)
        self.assertEqual(len(events),79)
        for at,key in ((1,'frame'),(40,'frame'),(70,'frame'),(73,'frame')):
            changed=json.loads(json.dumps(events));changed[at][key]+=1
            with self.assertRaises(ValueError):task.verify_prefix(changed,prefix)
    def test_choice_is_after_switch_and_real_identity_is_resolved_again(self):
        text=self.policy()
        at=text.index('    tp_consider(c);')
        self.assertLess(at,text.index('selected=streak<3U?',at))
        self.assertEqual(text.count('static void tp_consider(struct mCore *c)\n{'),1)
        self.assertEqual(text.count('    tp_consider(c);'),1)
        header=(ROOT/task.HEADER).read_text()
        self.assertLess(header.index('n_cursor(c,2U)'),header.index('unsigned slot=mi_find'))
        self.assertIn('menu_pid,menu_ot,menu_species,target_pid,target_ot,species',header)
        self.assertIn('read32(c,own+0x48U)==target_pid',header)
        self.assertIn('read32(c,own+0x54U)==target_ot',header)
        self.assertIn('read16(c,own)==species',header)
    def test_bounded_switches_and_paid_accuracy_feedback_preserved(self):
        header=(ROOT/task.HEADER).read_text();text=self.policy()
        self.assertIn('if(tp_switches>=6U)return',header)
        self.assertIn('if(tp_seen && pid==tp_foe && ot==tp_foe_ot)return',header)
        self.assertIn('if(streak<15U)return;',header)
        self.assertIn('rr_memory.slot=actual;',text)
        self.assertIn('if(streak>=8U)actual=rl_pick',text)
    def test_module_reimport_after_configuration_is_idempotent(self):
        expected=self.policy()
        with patch.object(task.c,'policy_text',task.policy_text),patch.object(task.c,'verify_prefix',task.verify_prefix):
            spec=importlib.util.spec_from_file_location('tactical_again',ROOT/task.SELF)
            again=importlib.util.module_from_spec(spec);spec.loader.exec_module(again)
            self.assertEqual(again.policy_text('slot=wx_move_slot(c);',self.headers()),expected)
    def test_missing_policy_anchor_fails_closed(self):
        with self.assertRaises(ValueError):task.policy_text('',self.headers())
        with patch.object(task,'original_policy',return_value='slot=rr_move_slot(c);'):
            with self.assertRaises(ValueError):self.policy()
    def test_no_host_state_injection_or_new_candidate(self):
        text=(ROOT/task.HEADER).read_text()+(ROOT/task.SELF).read_text()
        for token in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'loadState('):self.assertNotIn(token,text)
        self.assertEqual(task.probe.SHA,'3101772a3b91fe0461f200bbd3faf19f01064132bd3d8db9b0fe8f747445b399')
        self.assertIn('def native():configure();c.native()',text)

if __name__=='__main__':unittest.main()
