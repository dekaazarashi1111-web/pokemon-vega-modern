"""Capture readiness and no learning/save/release overclaims."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_learnset_visual as m

class VisualTests(unittest.TestCase):
    def setUp(self):
        self.case={'name':'machine-page4-replace','species':151,'page':3,'index':0,'count':11,'expected':795}
        self.r={'status':'PASS_CAPTURE','scope':m.SCOPE,'case':self.case['name'],'candidate_sha256':m.m.CANDIDATE['sha256'],
                'species':151,'page':3,'index':0,'candidate_count':11,'selected_move':795,'summary_ready_frames':90,
                'host_write_barriers':1,'cores':1,'saves':0,'learned':False,'initial_moves_pp_unchanged':True,
                'visual_reviewed':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0,'list_frame':1000,'summary_frame':1500}
    def validate(self):return m.validate(json.dumps(self.r).encode(),self.case)
    def test_archive_render_waits(self):
        from pr16_learnset_gameplay_followup import render
        raw=render((ROOT/'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text()).replace('int main(int argc,char**argv)','int gameplay_old_archive(int argc,char**argv)').encode()
        text=m.archive(raw)
        self.assertIn('stamp-t.list>=90U',text);self.assertIn('++v_summary_ready==90U',text)
        self.assertIn('if(v_list_shot)',text);self.assertIn('!summary_selected && v_summary_shot',text)
    def test_driver_never_saves_or_learns(self):
        text=m.driver((ROOT/m.SOURCE).read_bytes())
        self.assertNotIn('a_save(c)',text);self.assertNotIn('g_party(',text)
        self.assertEqual(text.count('a_guard(c);'),1)
        self.assertIn('!t.selection && !t.replaced && !t.learned',text)
        self.assertIn('id!=0U && id!=11U',text)
    def test_source_preimage_rejected(self):
        with self.assertRaises(ValueError):m.driver((ROOT/m.SOURCE).read_bytes()+b'\n')
    def test_colorful_pixels(self):
        raw=b'P6\n240 160\n255\n'+b''.join(bytes((i%256,128,64)) for i in range(240*160))
        self.assertEqual(m.image(raw)['distinct_colors'],256)
    def test_black_rejected(self):
        with self.assertRaises(ValueError):m.image(b'P6\n240 160\n255\n'+b'\0'*(240*160*3))
    def test_wrong_shape_rejected(self):
        with self.assertRaises(ValueError):m.image(b'P6\n240 160\n255\n'+b'abc')
    def test_valid_capture(self):self.assertEqual(self.validate(),self.r)
    def test_learning_rejected(self):
        self.r['learned']=True
        with self.assertRaises(ValueError):self.validate()
    def test_visual_review_overclaim(self):
        self.r['visual_reviewed']=True
        with self.assertRaises(ValueError):self.validate()
    def test_boolean_frame_rejected(self):
        self.r['list_frame']=True
        with self.assertRaises(ValueError):self.validate()

if __name__=='__main__':unittest.main()
