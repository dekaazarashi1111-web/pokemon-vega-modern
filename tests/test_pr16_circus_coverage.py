"""既存原本に結びつけた再入場専用編成と汎用入力の境界検査。native再実行なし。"""
from pathlib import Path
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_coverage as task

class CoverageTests(unittest.TestCase):
    def headers(self):return {p:(ROOT/p).read_text() for p in task.c.HEADERS}
    def test_original_four_win_lifecycle_is_reused_without_target_promotion(self):
        old=json.loads((ROOT/task.OLD).read_bytes())
        self.assertEqual(old['classification'],'CIRCUS_REENTRY_FIRST_LOSS_SAVE_VERIFIED_TARGET_OPEN')
        self.assertEqual(old['native']['status'],'PASS_CIRCUS_SCOPED_NATIVE')
        self.assertEqual((old['scoped_result']['wins'],old['scoped_result']['losses']),(4,1))
        self.assertFalse(old['genuine_30_wins_verified'])
    def test_raw_rental_ranking_and_exact_initial_prefix_pure_c(self):
        raw=(ROOT/(task.RAW+'.stderr')).read_text()
        rows=re.findall(r'CIRCUS_SUSTAIN_RENTAL slot=(\d+) score=(\d+) types=([a-f0-9]+)',raw)
        self.assertEqual(len(rows),12)
        self.assertEqual([int(r[0]) for r in rows],list(range(6))*2)
        a=[int(r[1]) for r in rows[:6]];b=[int(r[1]) for r in rows[6:]]
        self.assertEqual(b,[245977200,328473600,571032000,373218300,378483840,238901850])
        types=[[int(r[2],16) for r in rows[n:n+6]] for n in (0,6)]
        # utility加点対象は原本の実moves（初回2/3/4、再入場4）。
        import pr16_circus_reentry_probe as probe
        events=probe.parse(raw.encode());selected=[e for e in events if e['label']=='selected']
        utility=[]
        for event in selected:
            party=bytes.fromhex(event['party']);flags=[]
            for n in range(6):
                mon=party[n*100:(n+1)*100]
                flags.append(int(any(int.from_bytes(mon[44+2*j:46+2*j],'little') in (92,73) and mon[52+j] for j in range(4))))
            utility.append(flags)
        def array(values):return '{'+','.join(str(v)+'ULL' for v in values)+'}'
        source='''#include <assert.h>
#include <stdint.h>
#include "HEADER"
static void rank(unsigned streak,const uint64_t score[6],const uint64_t types[6],const uint64_t utility[6],const unsigned expected[3]){
 uint64_t scores[6];unsigned used=0;uint64_t covered=0;
 for(unsigned i=0;i<6;++i){scores[i]=score[i]/(utility[i]?2U:1U);if(cv_utility(streak,utility[i]))scores[i]*=2;}
 for(unsigned n=0;n<3;++n){unsigned best=6;uint64_t top=0;
  for(unsigned i=0;i<6;++i){uint64_t v=scores[i];if(!(types[i]&~covered))v/=4;
   if(!(used&(1U<<i)) && (best==6 || v>top)){best=i;top=v;}}
  assert(best==expected[n]);used|=1U<<best;covered|=types[best];
 }
}
int main(void){
 const uint64_t a[6]=A,b[6]=B,ta[6]=TA,tb[6]=TB,ua[6]=UA,ub[6]=UB;
 const unsigned initial[3]={2,4,5},previous[3]={2,4,3},coverage[3]={2,3,1};
 for(unsigned s=0;s<32;++s)for(unsigned u=0;u<2;++u)assert(cv_utility(s,u)==(s<3?u:0));
 rank(0,a,ta,ua,initial);rank(0,b,tb,ub,previous);
 for(unsigned s=3;s<=30;s+=3)rank(s,b,tb,ub,coverage);
 return 0;
}'''.replace('HEADER',(ROOT/task.HEADER).as_posix())
        for key,value in [('TA',types[0]),('TB',types[1]),('UA',utility[0]),('UB',utility[1]),('A',a),('B',b)]:
            source=source.replace('='+key+';', '='+array(value)+';').replace('='+key+',','='+array(value)+',')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'test.c').write_text(source)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            subprocess.run([str(p/'test')],check=True,capture_output=True)
    def test_first_three_remain_specialized_but_later_use_generic_damage(self):
        text=task.policy_text('slot=wx_move_slot(c);',self.headers())
        self.assertEqual(text.count('selected=streak<3U?fp_move_slot(c):wx_move_slot(c);'),1)
        self.assertEqual(text.count('if(streak<3U)return selected;'),1)
        self.assertNotIn('if(streak<4U)return selected;',text)
        self.assertEqual(text.count('slot=rr_move_slot(c);'),1)
        self.assertEqual(text.count('cv_utility(read16(c,0x0203DB20U),utility)'),1)
        self.assertEqual(text.count('(read16(c,0x0203DB20U)%3U)'),4)
    def test_unexpected_rental_or_move_boundary_is_rejected(self):
        headers=self.headers()
        with self.assertRaises(ValueError):task.policy_text('',headers)
        path='tools/mgba_pr16_circus_sustain.h';headers[path]=headers[path].replace(',utility);',',0U);')
        with self.assertRaises(ValueError):task.policy_text('slot=wx_move_slot(c);',headers)
    def test_mutable_predecessor_reimport_does_not_double_wrap(self):
        expected=task.policy_text('slot=wx_move_slot(c);',self.headers())
        with patch.object(task.c,'policy_text',task.policy_text),patch.object(task.c,'verify_prefix',task.verify_prefix):
            spec=importlib.util.spec_from_file_location('coverage_again',ROOT/task.SELF)
            again=importlib.util.module_from_spec(spec);spec.loader.exec_module(again)
            self.assertEqual(again.policy_text('slot=wx_move_slot(c);',self.headers()),expected)
    def test_existing_paid_feedback_preserves_threshold_and_host_write_barriers(self):
        text=task.policy_text('slot=wx_move_slot(c);',self.headers())
        self.assertIn('rr_memory.stalls[i]>=2U',text)
        for name in (task.HEADER,task.FEEDBACK):
            for token in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'loadState('):
                self.assertNotIn(token,(ROOT/name).read_text())
    def test_prefix_contract_and_single_native_case_remain_fixed(self):
        source=(ROOT/task.SELF).read_text()
        self.assertIn('original_prefix(events,raw)',source)
        self.assertIn('def native():configure();c.native()',source)
        self.assertNotIn('original_prefix(events[:',source)
        self.assertEqual(task.probe.CASE,'circus-continuous-30-save')
        self.assertEqual(task.probe.SHA,'3101772a3b91fe0461f200bbd3faf19f01064132bd3d8db9b0fe8f747445b399')

if __name__=='__main__':unittest.main()
