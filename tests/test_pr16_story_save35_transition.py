"""失敗原本に限定した新transition入力の検査。旧19controller再実行0。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save35_measure as m
class Transition(unittest.TestCase):
    def test_observed_wait_only(self):self.assertEqual(m.event_input(dict(callback2=134569577)),((0,60),))
    def test_field_dialogue(self):self.assertEqual(m.event_input(dict(callback2=m.m.FIELD)),((1,2),(0,180)))
    def test_unknown_rejected(self):
        with self.assertRaises(ValueError):m.event_input(dict(callback2=0))
    def test_battle_owned_elsewhere(self):
        with self.assertRaises(ValueError):m.event_input(dict(callback2=m.m.BATTLE))
if __name__=='__main__':unittest.main()
