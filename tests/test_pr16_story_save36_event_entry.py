"""7,5 eventの保存座標先行とlive座標の限定受入。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save36_measure as m
class EventEntry(unittest.TestCase):
    def observation(self,**kw):return dict(dict(map=[1,73],xy=[7,10],live_xy=[14,12],lock=1,callback2=m.m.FIELD),**kw)
    def test_script_entry(self):self.assertTrue(m.allowed_step(self.observation(),[8,5],[7,5]))
    def test_other_edge_rejected(self):self.assertFalse(m.allowed_step(self.observation(),[13,5],[13,6]))
    def test_wrong_live_rejected(self):self.assertFalse(m.allowed_step(self.observation(live_xy=[14,17]),[8,5],[7,5]))
    def test_unlocked_rejected(self):self.assertFalse(m.allowed_step(self.observation(lock=0),[8,5],[7,5]))
if __name__=='__main__':unittest.main()
