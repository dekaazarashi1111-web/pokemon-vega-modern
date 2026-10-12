"""保存原本の陽性前提を必ず通し、独立oracleの拒否能力を検査する。"""
import copy
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_natural_spending_oracle as o

class OracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.zero=Path(os.environ['PR16_NATURAL_ZERO_INPUT']).read_bytes()
        cls.root=ROOT/o.BASE
        cls.original={m:o.parse((cls.root/f/'stdout.txt').read_bytes()) for f,m in [('earn-1','earn'),('spend-3','spend'),('ui-final','ui')]}
    def test_positive_receipt(self):
        v=o.validate(self.root,self.zero)
        self.assertTrue(v['naturally_earned_spending_accepted']);self.assertFalse(v['natural_story_progress_accepted'])
    def test_reject_footer_as_input(self):
        o.validate(self.root,self.zero)
        with self.assertRaises(ValueError):o.validate(self.root,self.zero+bytes(16))
    def test_reject_duplicate_json(self):
        o.parse(b'{"a":1}\n')
        with self.assertRaises(ValueError):o.parse(b'{"a":1,"a":2}\n')
    def test_reject_nonfinite(self):
        o.parse(b'{"a":1}\n')
        with self.assertRaises(ValueError):o.parse(b'{"a":NaN}\n')
    def test_reject_truncated_line(self):
        o.parse(b'{"a":1}\n')
        with self.assertRaises(ValueError):o.parse(b'{"a":1}')
    def reject(self,mode,selector,key,value):
        original=self.original[mode];o.validate_rows(original,mode,self.zero)
        rows=copy.deepcopy(original);row=next(r for r in rows if all(r.get(k)==v for k,v in selector.items()))
        row[key]=value
        with self.assertRaises(ValueError):o.validate_rows(rows,mode,self.zero)

CASES=[]
for mode,stage in [('earn','earning_fixture'),('earn','earned'),('spend','purchased'),('spend','purchase_continue'),('ui','declined'),('ui','end')]:
    for key,value in [('counter',99),('owner','00'*64),('item_quantity',77),('party_count',2),('party_sha256','0'*64),('other_inventory_sha256','0'*64)]:
        CASES.append((mode+'_'+stage+'_'+key,mode,{'event':stage},key,value))
    for key,value in [('checksum_valid',False),('ledger_sha256','0'*64),('unrelated_ledger_sha256','0'*64),('migration_dirty',1),('size',True)]:
        CASES.append((mode+'_'+stage+'_'+key,mode,{'ledger_event':stage},key,value))
for mode in ('spend','ui'):
    for key,value in [('rp',9999),('lifetime',0),('flash_sha256','0'*64),('window',0),('window0','00'*12),('shop_descriptor','00080015100f3800602d0002'),('eligible',23),('page',True),('result',0),('map',[98,3,1,1])]:
        CASES.append((mode+'_page_'+key,mode,{'stage':'page_0','kind':'state'},key,value))
    for key,value in [('natural_story_progress_accepted',True),('natural_travel_accepted',True),('old_matrix_executions',1),('fresh_cores',True)]:
        CASES.append((mode+'_summary_'+key,mode,{'kind':'summary'},key,value))
    for key,value in [('rp_injected',True),('stock_warp_calls',0),('natural_travel_accepted',True)]:
        CASES.append((mode+'_relocation_'+key,mode,{'kind':'relocation_fixture'},key,value))
for mode in ('earn','spend','ui'):
    CASES.append((mode+'_candidate',mode,{'kind':'input_save'},'candidate','0'*64))
    CASES.append((mode+'_input_save',mode,{'kind':'input_save'},'sha256','0'*64))
CASES.extend([
 ('ui_spent_input','ui',{'mode':'ui-spent'},'sha256',o.EARNED_SAVE),
 ('ui_purchase_repeat','ui',{'kind':'summary'},'new_purchases',1),
 ('ui_save_repeat','ui',{'kind':'summary'},'new_saves',1),
 ('ui_earning_repeat','ui',{'kind':'summary'},'new_earnings',1),
 ('earning_fixture_hidden','earn',{'setup':'mining'},'progression_is_fixture',False),
 ('earning_reward_injected','earn',{'setup':'mining'},'rp_injected',True),
 ('confirmation_wrong','spend',{'stage':'confirmation','kind':'state'},'text','00ff'),
 ('input_zero_frames','ui',{'kind':'input'},'frames',0),
 ('input_unknown_key','ui',{'kind':'input'},'keys',3),
])
def make_test(mode,selector,key,value):
    def test(self):self.reject(mode,selector,key,value)
    return test
for name,mode,selector,key,value in CASES:setattr(OracleTests,'test_reject_'+name,make_test(mode,selector,key,value))
if __name__=='__main__':unittest.main()
