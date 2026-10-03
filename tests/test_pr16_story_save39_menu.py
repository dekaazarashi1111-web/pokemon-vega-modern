"""通常メニュー実cursorの4変更検査。旧11件は原log継承。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save39_measure as m
class Menu(unittest.TestCase):
    def test_pokedex(self):self.assertEqual(m.menu_index_from_digests([m.MENU_ARROW]+['0']*6,m.REPORT_LABEL),0)
    def test_save(self):self.assertEqual(m.menu_index_from_digests(['0']*4+[m.MENU_ARROW]+['0']*2,m.REPORT_LABEL),4)
    def test_duplicate(self):
        with self.assertRaises(ValueError):m.menu_index_from_digests([m.MENU_ARROW]*7,m.REPORT_LABEL)
    def test_wrong_label(self):
        with self.assertRaises(ValueError):m.menu_index_from_digests([m.MENU_ARROW]+['0']*6,'0')
if __name__=='__main__':unittest.main()
