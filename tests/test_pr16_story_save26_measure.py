"""新Save26の残PP/新経路/唯一の親だけ。受入済み旧suiteは呼ばない。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save26_measure as m
class Controller(unittest.TestCase):
    def test_initial_pp(self):self.assertEqual(m.select([0]*4),2)
    def test_second_fire(self):self.assertEqual(m.select([0,0,1,0]),2)
    def test_fire_to_ice(self):self.assertEqual(m.select([0,0,2,0]),3)
    def test_ice_to_slot1(self):self.assertEqual(m.select([0,0,2,5]),1)
    def test_final_slot0(self):self.assertEqual(m.select([0,14,2,5]),0)
    def test_pp_exhaustion(self):
        with self.assertRaises(ValueError):m.select([1,14,2,5])
    def test_wrong_pp(self):
        with self.assertRaises(ValueError):m.select([0,0,3,0])
    def test_bool_pp(self):
        with self.assertRaises(ValueError):m.select([False,0,0,0])
    def test_short_pp(self):
        with self.assertRaises(ValueError):m.select([0])
    def test_route_starts_after_save25(self):self.assertEqual(m.ROUTE[:2],[[31,7],[31,8]])
    def test_route_rock_stairs(self):self.assertEqual(m.ROUTE[m.ROUTE.index([23,14])-1:m.ROUTE.index([23,14])+2],[[23,15],[23,14],[23,13]])
    def test_all_route_steps(self):
        self.assertEqual(len(m.ROUTE),30)
        for a,b in zip(m.ROUTE,m.ROUTE[1:]):self.assertIn(m.direction(a,b),(16,32,64,128))
    def test_nonadjacent_rejected(self):
        with self.assertRaises(ValueError):m.direction([31,7],[31,9])
    def test_diagonal_rejected(self):
        with self.assertRaises(ValueError):m.direction([31,7],[32,8])
    def test_same_position_rejected(self):
        with self.assertRaises(ValueError):m.direction([31,7],[31,7])
if __name__=='__main__':unittest.main()
