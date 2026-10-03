"""新観測の出口NPC会話・変更controllerだけ。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save38_measure as m
class Event(unittest.TestCase):
    def state(self,**changes):
        x=dict(map=m.DESTINATION,xy=[9,76],save_counter=37,party_count=4,rp=0,callback2=m.m.FIELD,lock=1);x.update(changes);return x
    def test_dialogue(self):self.assertEqual(m.exit_event_input(self.state()),((1,2),(0,180)))
    def test_transition(self):self.assertEqual(m.exit_event_input(self.state(callback2=m.TRANSITION)),((0,60),))
    def test_wrong_map(self):
        with self.assertRaises(ValueError):m.exit_event_input(self.state(map=m.ORIGIN))
if __name__=='__main__':unittest.main()
