"""4種の境界、途中成功で停止、native3勝を弱めないことを検査。"""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('accuracy',ROOT/'scripts/pr16_circus_accuracy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class AccuracyTests(unittest.TestCase):
    def test_host_c(self):
        source=r'''
#define CIRCUS_ACCURACY_HOST_TEST
#include "mgba_pr16_circus_accuracy.h"
#include <assert.h>
int main(void){
for(unsigned v=1;v<=4;++v){
 assert(fp_select(v,1,126,0,2,10,10,0)==0);
 assert(fp_select(v,1,126,4,2,10,10,0)==1);
 assert(fp_select(v,3,182,4,2,12,11,0)==3);
 assert(fp_select(v,3,182,4,2,12,11,0x80)==(v>=2?2:3));
 assert(fp_select(v,2,73,4,0,12,10,0)==(v>=3?0:2));
 assert(fp_select(v,2,73,4,4,12,10,0)==2);
 assert(fp_select(v,0,202,4,1,12,10,0)==0);}
return 0;}
'''
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.c';p.write_text(source);exe=Path(d)/'test'
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(ROOT/'tools'),str(p),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True)
    def row(self,i,status='FAIL'):
        return dict(policy=m.VARIANTS[i],status=status,result=dict(wins=3,losses=0,battles=3,events=17))
    def test_stop_at_first_success(self):
        for i in range(4):
            rows=[self.row(n) for n in range(i)]+[self.row(i,'PASS_CIRCUS_SCOPED_NATIVE')]
            self.assertTrue(m.attempts_valid(rows))
            with self.assertRaises(ValueError):m.attempts_valid(rows+[self.row(0)])
    def test_no_duplicates_or_partial_win(self):
        with self.assertRaises(ValueError):m.attempts_valid([self.row(0),self.row(0)])
        bad=self.row(0,'PASS_CIRCUS_SCOPED_NATIVE');bad['result']['wins']=2
        with self.assertRaises(ValueError):m.attempts_valid([bad])
        with self.assertRaises(ValueError):m.attempts_valid([])
        self.assertFalse(m.attempts_valid([self.row(i) for i in range(4)]))
    def test_adapt_unique(self):
        source='slot=wx_move_slot(c);'
        values=[m.adapt(source,i) for i in range(1,5)]
        self.assertEqual(len(set(values)),4)
        for value in (True,0,5,None):
            with self.assertRaises(ValueError):m.adapt(source,value)
        with self.assertRaises(ValueError):m.adapt(values[0],1)
    def test_input_only(self):
        text=(ROOT/m.HEADER).read_text()
        for token in ('write8(', 'write16(', 'write32(', 'setRegister(', 'loadState(', 'call_preserving('):self.assertNotIn(token,text)
        self.assertIn('selected=cd_move_slot(c)',text)
        self.assertIn('!=2U)return selected',text)
    def test_review_is_three_hashed_screens(self):
        import json
        review=json.loads((ROOT/m.REVIEW).read_bytes())
        self.assertEqual(review['run_id'],35422605107)
        self.assertTrue(review['completed'])
        self.assertEqual(len(review['screens']),3)
        for bound in review['screens'].values():
            self.assertEqual(bound['size'],115215);self.assertEqual(len(bound['sha256']),64)
if __name__=='__main__':unittest.main()
