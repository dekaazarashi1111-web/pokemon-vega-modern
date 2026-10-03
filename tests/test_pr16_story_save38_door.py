"""初回の実出口矢印停止を修正する3件だけ。旧10件はActions原logを継承。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save38_measure as m
class Door(unittest.TestCase):
    def state(self,**changes):
        x=dict(map=m.ORIGIN,xy=[4,6],live_xy=[11,13],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,battle_outcome=0,save_counter=37);x.update(changes);return x
    def test_exit_direction(self):self.assertEqual(m.door_input(self.state()),((128,8),(0,300)))
    def test_wrong_position(self):
        with self.assertRaises(ValueError):m.door_input(self.state(xy=[4,5],live_xy=[11,12]))
    def test_already_outside(self):
        with self.assertRaises(ValueError):m.door_input(self.state(map=m.DESTINATION))
if __name__=='__main__':unittest.main()
