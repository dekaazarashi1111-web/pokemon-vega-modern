"""原本positive controlを毎回通してから、別々の改変を拒否する。native再実行なし。"""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_research_standard_list_oracle as o

class OriginalOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=Path(os.environ['PR16_STANDARD_LIST_EVIDENCE'])
        cls.fixture=Path(os.environ['PR16_STANDARD_LIST_FIXTURE']).read_bytes()
        cls.raw=(cls.directory/'stdout.txt').read_bytes()
        cls.commands=(cls.directory/'commands.txt').read_bytes()
        cls.screens=json.loads((cls.directory/'measurement.json').read_bytes())['screens']
        cls.original=[o.load(line) for line in cls.raw.splitlines()]
    def setUp(self):
        self.assertEqual(o.validate(self.raw,self.commands,self.fixture,self.screens)['status'],'PASS_STANDARD_LIST_NATIVE_OBSERVATIONS')
        self.rows=copy.deepcopy(self.original)
    def check_bad(self):
        raw=('\n'.join(json.dumps(r,separators=(',',':')) for r in self.rows)+'\n').encode()
        with self.assertRaises(ValueError):o.validate(raw,self.commands,self.fixture,self.screens)
    def first(self,key,value=None):return next(r for r in self.rows if key in r and (value is None or r[key]==value))
    def test_original_positive(self):self.assertEqual(len(self.screens),22)
    def test_missing_terminal(self):self.rows.pop();self.check_bad()
    def test_extra_terminal(self):self.rows.append(self.rows[-1]);self.check_bad()
    def test_missing_row(self):self.rows.pop(10);self.check_bad()
    def test_reordered_inputs(self):self.first('input')['keys']=2;self.check_bad()
    def test_frame(self):self.first('state','menu_first')['frame']+=1;self.check_bad()
    def test_npc_map(self):self.first('state','menu_first')['map'][1]=4;self.check_bad()
    def test_false_field(self):self.first('state','menu_first')['field']=True;self.check_bad()
    def test_live_task_missing(self):self.first('menu','menu_first')['task_count']=0;self.check_bad()
    def test_duplicate_task(self):r=self.first('menu','menu_first');r['tasks']*=2;r['task_count']=2;self.check_bad()
    def test_busy_result(self):self.first('menu','menu_first')['result']=0;self.check_bad()
    def test_unreleased_task(self):self.first('menu','b_cancel_closed')['task_count']=1;self.check_bad()
    def test_unreleased_window(self):self.first('menu','b_cancel_closed')['window_descriptor']='00'*12;self.check_bad()
    def test_window_geometry(self):r=self.first('menu','menu_first');r['window_descriptor']='01'+r['window_descriptor'][2:];self.check_bad()
    def test_balance_text(self):self.first('state','balance_selected')['text']='ff';self.check_bad()
    def test_rank_buffer(self):self.first('menu','balance_selected')['buffers'][1]='a3ff';self.check_bad()
    def test_rp(self):self.first('menu','menu_first')['rp']=1;self.check_bad()
    def test_owner(self):self.first('event')['owner']='00'*64;self.check_bad()
    def test_ledger(self):self.first('ledger_event')['ledger_sha256']='0'*64;self.check_bad()
    def test_bag(self):self.first('event')['inventory_sha256']='0'*64;self.check_bad()
    def test_party(self):self.first('event')['party_count']=5;self.check_bad()
    def test_flash(self):self.first('state')['flash_sha256']='0'*64;self.check_bad()
    def test_save_counter(self):self.first('event')['counter']=3;self.check_bad()
    def test_screenshot_join(self):self.first('screen')['sha256']='0'*64;self.check_bad()
    def test_bool_is_not_count(self):self.first('menu','menu_first')['task_count']=True;self.check_bad()
    def test_release_promotion(self):self.rows[-1]['naturally_earned_spending_accepted']=True;self.check_bad()
    def test_duplicate_json_key(self):
        raw=self.raw.replace(b'"status":"MEASURED"',b'"status":"MEASURED","status":"MEASURED"')
        self.assertNotEqual(raw,self.raw)
        with self.assertRaises(ValueError):o.validate(raw,self.commands,self.fixture,self.screens)

if __name__=='__main__':unittest.main()
