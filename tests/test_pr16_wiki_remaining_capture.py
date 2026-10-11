"""残件source inventoryの範囲・行保存を検査する。nativeは呼ばない。"""
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from pr16_wiki_remaining_capture import contexts

class CaptureTests(unittest.TestCase):
    def test_no_unrelated_source(self):
        self.assertEqual(contexts('int unrelated;\n'),[])
    def test_one_based_lines(self):
        self.assertEqual(contexts('a\nCalcMoveSplit\nc\n',0),[
            {'start_line':2,'end_line':2,'text':'CalcMoveSplit\n'}])
    def test_overlapping_ranges_merged(self):
        rows=contexts('a\nCalcMoveSplit\nhiddenAbility\nd\n',1)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['text'],'a\nCalcMoveSplit\nhiddenAbility\nd\n')
    def test_distinct_ranges_retained(self):
        rows=contexts('CalcMoveSplit\n'+'x\n'*12+'DetermineEggAbility\n',1)
        self.assertEqual([(r['start_line'],r['end_line']) for r in rows],[(1,2),(13,14)])
    def test_unicode_and_newline(self):
        self.assertEqual(contexts('日本語 hiddenAbility',0)[0]['text'],'日本語 hiddenAbility\n')
    def test_source_order_stable(self):
        text='FLAG_HIDDEN_ABILITY\nx\nGiveMonInitialMoveset\n'
        self.assertEqual(contexts(text,0),contexts(text,0))
        self.assertEqual([r['start_line'] for r in contexts(text,0)],[1,3])

if __name__=='__main__':unittest.main()
