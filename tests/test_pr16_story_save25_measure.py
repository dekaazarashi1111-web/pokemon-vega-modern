"""保存済み画面をread-onlyで使う新入力controller検査。旧native/旧suiteは呼ばない。"""
import os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save25_measure as m
class Controller(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.folder=pathlib.Path(os.environ['PR16_SAVE25_CALIBRATION'])
    def raw(self,n):return (self.folder/f'screen-{n:04d}.ppm').read_bytes()
    def test_move_cursor_zero(self):self.assertEqual(m.classify(self.raw(6)),('moves',0))
    def test_move_cursor_one(self):self.assertEqual(m.classify(self.raw(69)),('moves',1))
    def test_move_cursor_two(self):self.assertEqual(m.classify(self.raw(11)),('moves',2))
    def test_move_cursor_three(self):self.assertEqual(m.classify(self.raw(56)),('moves',3))
    def test_shift_menu(self):self.assertEqual(m.classify(self.raw(10)),('shift',None))
    def test_field_is_not_menu(self):self.assertEqual(m.classify(self.raw(0)),('other',None))
    def test_text_is_not_menu(self):self.assertEqual(m.classify(self.raw(7)),('other',None))
    def test_missing_pixel_rejected(self):
        with self.assertRaises(ValueError):m.pixels(self.raw(6)[:-1])
    def test_extra_pixel_rejected(self):
        with self.assertRaises(ValueError):m.pixels(self.raw(6)+b'x')
    def test_header_rejected(self):
        with self.assertRaises(ValueError):m.pixels(b'P5'+self.raw(6)[2:])
    def test_outside_crop_rejected(self):
        with self.assertRaises(ValueError):m.crop(self.raw(6),[-1,0,2,2])
    def test_empty_crop_rejected(self):
        with self.assertRaises(ValueError):m.crop(self.raw(6),[1,1,1,2])
    def test_navigation_all16(self):
        for x in range(4):
            for y in range(4):
                z=x
                for key in m.navigation(x,y):z+=2 if key==128 else -2 if key==64 else 1 if key==16 else -1
                self.assertEqual(z,y)
    def test_navigation_bool_rejected(self):
        with self.assertRaises(ValueError):m.navigation(True,0)
    def test_navigation_negative_rejected(self):
        with self.assertRaises(ValueError):m.navigation(-1,0)
    def test_navigation_overflow_rejected(self):
        with self.assertRaises(ValueError):m.navigation(0,4)
if __name__=='__main__':unittest.main()
