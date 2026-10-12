"""3勝の厳密ゲートとread-only決着方策。合成検査をnative受入にはしない。"""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('finish_policy',ROOT/'scripts/pr16_circus_finish.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FinishTests(unittest.TestCase):
    def test_c_policy(self):
        code=r'''
#define CIRCUS_FINISH_HOST_TEST
#include "mgba_pr16_circus_finish.h"
#include <assert.h>
#include <stdio.h>
int main(void){unsigned checks=0;
for(unsigned i=0;i<4;++i)for(unsigned j=0;j<4;++j){
 assert(fw_prefer(i,j,1000,950)==j);++checks;
 assert(fw_prefer(i,j,1000,949)==i);++checks;}
assert(fw_prefer(2,4,1000,1000)==2);++checks;
assert(fw_prefer(2,1,UINT64_MAX,UINT64_MAX)==1);++checks;
for(unsigned s=0;s<4096;++s){
 unsigned want=!(s&0x88U);
 assert(fw_protect(s,0x380,53,50,100,30,160)==want);++checks;}
assert(fw_protect(0,0,53,100,100,1,160)==0);++checks;
assert(fw_protect(0,0x380,182,50,100,30,160)==0);++checks;
assert(fw_protect(0,0x80,53,50,100,1,160)==0);++checks;
assert(fw_protect(0,0x380,53,50,100,31,160)==0);++checks;
assert(fw_protect(0,8,53,50,100,20,160)==1);++checks;
assert(fw_protect(0,8,53,50,100,21,160)==0);++checks;
assert(fw_protect(0,0x380,53,0,100,30,160)==0);++checks;
assert(fw_protect(0,0x380,53,50,0,30,160)==0);++checks;
assert(fw_protect(0,0x380,53,50,100,0,160)==0);++checks;
assert(fw_protect(0,0x380,53,50,100,30,0)==0);++checks;
printf("PASS_FINISH_POLICY checks=%u\n",checks);}
'''
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/'fixture.c';src.write_text(code);exe=Path(folder)/'test'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'tools'),str(src),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertEqual(result.stdout,'PASS_FINISH_POLICY checks=4140\n')
    def test_adapt_once(self):
        source='void input(void){slot=wx_move_slot(c);}'
        actual=m.adapt(source)
        self.assertEqual(actual.count('slot=fw_move_slot(c);'),1)
        for bad in ('',source+source,actual):
            with self.assertRaises(ValueError):m.adapt(bad)
    def test_three_real_wins_not_partial(self):
        good=dict(wins=3,losses=0,battles=3,events=17)
        self.assertEqual(m.require_three(good),good)
        for key in good:
            for value in (None,True,False,1.0,'3',-1,good[key]+1):
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):m.require_three(dict(good,**{key:value}))
        with self.assertRaises(ValueError):m.require_three(dict(good,wins=2,losses=1))
    def test_policy_has_no_host_injection(self):
        text=(ROOT/m.HEADER).read_text()
        for token in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'setRegister(', 'loadState(', 'saveState('):self.assertNotIn(token,text)
        self.assertIn('!=2U)return su_move_slot(c)',text)
        self.assertNotIn('m->seed',text)
    def test_recipe_reuses_accepted_link(self):
        text=(ROOT/m.SELF).read_text()
        self.assertIn("bounded_patch(raw,recipe['patches'])",text)
        self.assertNotIn('compile_bridge(',text)
        self.assertNotIn('force=True',text)
    def test_native_remains_strict(self):
        text=(ROOT/m.SELF).read_text()
        self.assertIn('require_three(old(raw,err,code,case))',text)
        self.assertIn("'finish attempt already recorded; inspect it instead of replaying'",text)
        self.assertIn("physical_admission_accepted=False,suppression_accepted=False,release_ready=False",text)
if __name__=='__main__':unittest.main()
