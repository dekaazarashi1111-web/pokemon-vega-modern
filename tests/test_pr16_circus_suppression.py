import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_suppression_contract as c

class SuppressionContracts(unittest.TestCase):
    def generated(self):
        return {'controller.c':b'int main(int argc,char **argv){ sc_events++<160U; }',
                'pr16_shop_breeding_helpers.c':b'b_frames<=600000U', 'keep.c':b'untouched'}
    def draw(self):
        return dict(attempt=0,delay=0,current=30,best=30,bp=90,counter=3,types=c.TYPE,
                    flags=c.MASK,newbs=0x02010000,target=True)
    def calls(self):
        common=dict(flags=c.MASK,types=c.TYPE,host_writes=0,host_calls=0)
        return [dict(common,kind='predicate',bank=0,raw_ability=67,result=1,return_pc=0x09000000,
                     pcs=[0x090D7BB0,0x09000000]),
                dict(common,kind='dispatch',name='AccuracyCalc',root=0x090BC688,
                     delegate=0x09534408,expected_suppressed=0x09534408,preserve_r3=True,
                     r3_before=123,r3_after=123,pcs=[0x090BC688,0x09534408])]
    def test_01_adapt_only_expected_sources(self):
        src=self.generated();new=c.adapt(src);self.assertEqual(new['keep.c'],src['keep.c']);self.assertIn(b'ss_prefix_main',new['controller.c']);self.assertIn(b'4000000U',new['pr16_shop_breeding_helpers.c'])
    def test_02_adapt_does_not_mutate_input(self):
        src=self.generated();before=copy.deepcopy(src);c.adapt(src);self.assertEqual(src,before)
    def test_03_missing_source_anchor_rejected(self):
        src=self.generated();src['controller.c']=b'int other(void){}'
        with self.assertRaises(ValueError):c.adapt(src)
    def test_04_ambiguous_source_anchor_rejected(self):
        src=self.generated();src['controller.c']*=2
        with self.assertRaises(ValueError):c.adapt(src)
    def test_05_duplicate_json_rejected(self):
        with self.assertRaises(ValueError):c.strict(b'{"a":1,"a":2}')
    def test_06_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError):c.strict(b'{"a":NaN}')
    def test_07_real_draw_contract(self):
        self.assertTrue(c.validate_draws([self.draw()]))
    def test_08_pregate_streak_rejected(self):
        row=self.draw();row['current']=29
        with self.assertRaises(ValueError):c.validate_draws([row])
    def test_09_flag_without_actual_battle_rejected(self):
        row=self.draw();row['types']=0
        with self.assertRaises(ValueError):c.validate_draws([row])
    def test_10_repeated_target_rejected(self):
        row=self.draw();second=dict(row,attempt=1,delay=17)
        with self.assertRaises(ValueError):c.validate_draws([row,second])
    def test_11_all_nontarget_draws_retained(self):
        first=dict(self.draw(),flags=2,target=False);last=dict(self.draw(),attempt=1,delay=17)
        self.assertTrue(c.validate_draws([first,last]))
    def test_12_natural_calls_contract(self):
        self.assertTrue(c.validate_calls(self.calls())['observed'])
    def test_13_injected_call_rejected(self):
        rows=self.calls();rows[0]['host_calls']=1
        with self.assertRaises(ValueError):c.validate_calls(rows)
    def test_14_false_predicate_rejected(self):
        rows=self.calls();rows[0]['result']=0
        with self.assertRaises(ValueError):c.validate_calls(rows)
    def test_15_wrong_delegate_rejected(self):
        rows=self.calls();rows[1]['delegate']=0x095331B0
        with self.assertRaises(ValueError):c.validate_calls(rows)
    def test_16_fourth_argument_corruption_rejected(self):
        rows=self.calls();rows[1]['r3_after']=124
        with self.assertRaises(ValueError):c.validate_calls(rows)
    def test_17_prefix_drift_rejected(self):
        with self.assertRaises(ValueError):c.prefix_proof(b'{}\n',b'original\n',b'{}\n',b'different\n')
    def test_18_header_has_no_game_writes_or_host_calls(self):
        text=(ROOT/'tools/mgba_pr16_circus_suppression.h').read_text()
        for forbidden in ('write8(', 'write16(', 'write32(', 'writeRegister(', 'call_preserving(', 'loadState(', 'memWrite(', 'busWrite'):
            self.assertNotIn(forbidden,text)
        self.assertIn('c->step(c)',text);self.assertIn('c->readRegister',text)
    def test_19_normal_save_cache_is_not_artifact(self):
        text=(ROOT/'scripts/pr16_circus_suppression.py').read_text()
        self.assertIn("OUT/'runtime',CACHE,OUT/'input'",text)
        self.assertIn('existing attempt: inspect report/cache',text)
        self.assertIn("source_head=head, run_id=int(os.environ['GITHUB_RUN_ID'])",text)
    def test_20_lifecycle_never_accepts_failed_process(self):
        with self.assertRaises(ValueError):c.validate_lifecycle(b'{}',b'',1)

if __name__=='__main__':unittest.main()
