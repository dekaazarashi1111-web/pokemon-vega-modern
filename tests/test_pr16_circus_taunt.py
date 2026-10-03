"""選出3個体と15勝を保持する対状態技controllerの限定回帰。nativeは呼ばない。"""
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
import pr16_circus_taunt as task

class TauntTests(unittest.TestCase):
    def policy(self):return task.policy_text('slot=wx_move_slot(c);',{p:(ROOT/p).read_text() for p in task.c.HEADERS})
    def compile_run(self,source):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'test.c').write_text(source.replace('HEADER',(ROOT/task.HEADER).as_posix()))
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            subprocess.run([str(p/'test')],check=True,capture_output=True)
    def test_all_rental_permutations_and_bounded_status_attempts(self):
        self.compile_run(r'''#include <assert.h>
#define CIRCUS_TAUNT_HOST_TEST
#include "HEADER"
int main(void){
 unsigned chosen[3],capable[6];
 for(unsigned a=0;a<6;++a)for(unsigned b=0;b<6;++b)for(unsigned c=0;c<6;++c){
  chosen[0]=a;chosen[1]=b;chosen[2]=c;
  for(unsigned mask=0;mask<64;++mask){
   for(unsigned i=0;i<6;++i)capable[i]=(mask>>i)&1U;
   unsigned old=ta_lead(14,chosen,capable),now=ta_lead(15,chosen,capable);
   if(a==b || a==c || b==c){assert(old==3 && now==3);continue;}
   assert(old==0);assert(now<3);
   unsigned expected=0;
   for(unsigned i=0;i<3;++i)if(capable[chosen[i]]){expected=i;break;}
   assert(now==expected);
  }
 }
 chosen[0]=6;assert(ta_lead(15,chosen,capable)==3);
 struct ta_history h={0};
 assert(ta_attempt(&h,2,32,3,170,170,1)==2);assert(h.attempts==1 && h.pending==1);
 for(unsigned i=0;i<3;++i)assert(ta_attempt(&h,2,31,3,160,170,1)==1);
 assert(h.paid==1 && !h.cooldown);
 assert(ta_attempt(&h,2,31,3,160,170,1)==2);
 for(unsigned i=0;i<20;++i)assert(ta_attempt(&h,2,30,3,160,170,1)==1);
 assert(h.attempts==2 && h.paid==2);
 h=(struct ta_history){0};
 assert(ta_attempt(&h,2,32,3,170,170,1)==2);
 assert(ta_attempt(&h,2,32,3,170,170,1)==2); /* PPなし=混乱等も最大2回 */
 assert(ta_attempt(&h,2,32,3,170,170,1)==1 && h.paid==0);
 h=(struct ta_history){0};
 assert(ta_attempt(&h,4,32,3,170,170,1)==1);
 assert(ta_attempt(&h,2,0,3,170,170,1)==1);
 assert(ta_attempt(&h,2,32,1,170,170,1)==1);
 assert(ta_attempt(&h,2,32,3,40,160,1)==1);
 assert(ta_attempt(&h,2,32,3,0,0,1)==1 && h.attempts==0);
 assert(ta_attempt(&h,2,32,3,180,170,1)==1 && h.attempts==0);
 return 0;
}''')
    def test_runtime_header_compiles_and_pre15_is_readonly(self):
        self.compile_run(r'''#include <assert.h>
#include <stdio.h>
#include <stdint.h>
struct mCore {unsigned unused;};
enum {ADDR_BATTLE_MONS=0x2000000,BATTLE_MON_SIZE=88,BATTLE_CORE_MOVE_TABLE_REPOINT=0x80001CC,
 BATTLE_MON_MOVES_OFFSET=12,BATTLE_MON_PP_OFFSET=36,BATTLE_CORE_MON_HP=40};
static unsigned b_frames;
static unsigned read8(struct mCore*c,uint32_t p){(void)c;(void)p;return 0;}
static unsigned read16(struct mCore*c,uint32_t p){(void)c;(void)p;return 14;}
static uint32_t read32(struct mCore*c,uint32_t p){(void)c;(void)p;return 0;}
static void bp_require(struct mCore*c,unsigned ok,const char*s){(void)c;(void)s;assert(ok);}
#include "HEADER"
int main(void){struct mCore c={0};unsigned selected[3]={1,4,2},has[6]={0,0,0,0,1,0};
 assert(ta_move(&c,3)==3 && !ta_memory.seen);assert(ta_lead(15,selected,has)==1);return 0;}
''')
    def test_original_has_real_switches_and_last_enemy_seven_hp(self):
        old=json.loads((ROOT/task.OLD).read_bytes())
        self.assertEqual(old['native']['status'],'PASS_CIRCUS_SCOPED_NATIVE')
        self.assertEqual((old['scoped_result']['wins'],old['scoped_result']['bp_earned']),(15,45))
        self.assertFalse(old['genuine_30_wins_verified'])
        raw=(ROOT/(task.RAW+'.stderr')).read_text()
        self.assertEqual(raw.count('CIRCUS_TACTICAL begin '),2)
        self.assertEqual(raw.count('CIRCUS_TACTICAL done '),2)
        lines=[s for s in raw.splitlines() if s.startswith('BP_RETURN label=turn-stop')]
        self.assertIn('outcome=2',lines[-1]);self.assertIn('enemy_hp=7',lines[-1])
    def test_fifteen_wins_and_return_are_immutable(self):
        events=task.probe.parse((ROOT/(task.RAW+'.stderr')).read_bytes())
        prefix=(ROOT/task.previous.previous.previous.PREFIX).read_bytes();task.verify_prefix(events,prefix)
        for at in (0,1,40,66,70):
            changed=json.loads(json.dumps(events));changed[at]['frame']+=1
            with self.assertRaises(ValueError):task.verify_prefix(changed,prefix)
        changed=json.loads(json.dumps(events));changed[71]['frame']+=1
        task.verify_prefix(changed,prefix)  # 第16戦の新しい選出入力は未受入区間。
    def test_team_members_are_selected_before_stable_lead_permutation(self):
        text=self.policy()
        self.assertEqual(text.count('planned[n]=best;planned_scores[n]=top;'),1)
        self.assertIn('order[j++]=lead;',text)
        self.assertIn('if(i!=lead)order[j++]=i;',text)
        self.assertIn('best=planned[k]',text)
        self.assertIn('cv_utility(read16(c,0x0203DB20U),utility)',text)
    def test_paid_feedback_uses_actual_status_move_not_superseded_attack(self):
        text=self.policy();a=text.index('    actual=ta_move(c,actual);')
        self.assertLess(a,text.index('rr_memory.slot=actual;',a))
        self.assertLess(a,text.index('rr_memory.damaging=',a))
        self.assertEqual(text.count('actual=ta_move(c,actual)'),1)
        self.assertIn('    tp_consider(c);',text)
        self.assertIn('if(streak>=8U)actual=rl_pick',text)
    def test_reimport_after_configuration_keeps_one_expansion(self):
        expected=self.policy()
        with patch.object(task.c,'policy_text',task.policy_text),patch.object(task.c,'verify_prefix',task.verify_prefix):
            spec=importlib.util.spec_from_file_location('taunt_again',ROOT/task.SELF)
            again=importlib.util.module_from_spec(spec);spec.loader.exec_module(again)
            self.assertEqual(again.policy_text('slot=wx_move_slot(c);',{p:(ROOT/p).read_text() for p in task.c.HEADERS}),expected)
    def test_mutated_selection_or_move_anchor_fails_closed(self):
        with patch.object(task,'original_policy',return_value='slot=rr_move_slot(c);'):
            with self.assertRaises(ValueError):self.policy()
    def test_no_injection_and_no_acceptance_from_attempted_taunt(self):
        text=(ROOT/task.HEADER).read_text()+(ROOT/task.SELF).read_text()
        for token in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'loadState('):self.assertNotIn(token,text)
        self.assertIn('suppression_accepted=False',text)
        self.assertIn('def native():configure();c.native()',text)
        self.assertEqual(task.probe.SHA,'3101772a3b91fe0461f200bbd3faf19f01064132bd3d8db9b0fe8f747445b399')

if __name__=='__main__':unittest.main()
