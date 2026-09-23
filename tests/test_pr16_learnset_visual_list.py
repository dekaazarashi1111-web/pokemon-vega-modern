"""Cursor-settle-only boundaries. Accepted screenshot/native suites are not run."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_learnset_visual_list as m

class ListTests(unittest.TestCase):
    def setUp(self):
        from pr16_learnset_gameplay_followup import render
        raw=render((m.ROOT/'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text()).replace('int main(int argc,char**argv)','int gameplay_old_archive(int argc,char**argv)').encode()
        self.archive=m.visual.archive(raw).encode();self.driver=m.visual.driver((m.ROOT/m.visual.SOURCE).read_bytes()).encode()
        self.result={'status':'PASS_LIST_CAPTURE','scope':m.SCOPE,'case':'floette-replace-420','candidate_sha256':m.m.CANDIDATE['sha256'],'species':1029,'page':0,'index':10,'candidate_count':12,'selected_move':420,'list_ready_frames':90,'list_frame':5600,'cores':1,'host_write_barriers':1,'saves':0,'learned':False,'summary_entered':False,'initial_moves_pp_unchanged':True,'visual_reviewed':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0}
    def validate(self):return m.validate(json.dumps(self.result).encode())
    def test_stable_target_counter(self):
        text=m.archive(self.archive)
        self.assertIn('if(++v_list_ready==90U)',text);self.assertIn('}else v_list_ready=0;',text)
        self.assertNotIn('stamp-t.list>=90U',text)
    def test_driver_stops_before_summary(self):
        text=m.driver(self.driver)
        self.assertIn('if(id!=11U)return 2;',text);self.assertIn('!t.summary',text)
        self.assertNotIn('a_save(c)',text);self.assertIn('!v_summary_shot && v_list_ready==90U',text)
    def test_archive_preimage(self):
        with self.assertRaises(ValueError):m.archive(self.archive+b'\n')
    def test_driver_preimage(self):
        with self.assertRaises(ValueError):m.driver(self.driver+b'\n')
    def test_valid_result(self):self.assertEqual(self.validate(),self.result)
    def test_unsettled(self):
        self.result['list_ready_frames']=1
        with self.assertRaises(ValueError):self.validate()
    def test_unexpected_summary(self):
        self.result['summary_entered']=True
        with self.assertRaises(ValueError):self.validate()
    def test_boolean_frame(self):
        self.result['list_frame']=True
        with self.assertRaises(ValueError):self.validate()

if __name__=='__main__':unittest.main()
