"""Save26から先のPP/新17点/出典だけ。既受入suiteを再走しない。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save27_measure as m

class Controller(unittest.TestCase):
    def test_save26_remaining_pp(self):self.assertEqual(m.PP,[1,14,1,5])
    def test_last_flamethrower(self):self.assertEqual(m.select([0,0,0,0]),2)
    def test_switch_after_last_flamethrower(self):self.assertEqual(m.select([0,0,1,0]),3)
    def test_switch_after_ice(self):self.assertEqual(m.select([0,0,1,5]),1)
    def test_final_move(self):self.assertEqual(m.select([0,14,1,5]),0)
    def test_save26_pp_exhaustion(self):
        with self.assertRaises(ValueError):m.select([1,14,1,5])
    def test_old_save25_pp_rejected(self):
        with self.assertRaises(ValueError):m.select([0,0,2,0])
    def test_new_seventeen_points_only(self):
        self.assertEqual(m.ROUTE,[[x,15]for x in range(32,22,-1)]+[[23,14],[23,13]]+[[x,13]for x in range(22,18,-1)]+[[19,14]])
        self.assertEqual(len(m.ROUTE),17)
    def test_no_accepted_prefix(self):self.assertNotIn([31,7],m.ROUTE)
    def test_starts_west(self):self.assertEqual(m.direction(*m.ROUTE[:2]),32)
    def test_final_teleport_approach(self):self.assertEqual(m.direction(*m.ROUTE[-2:]),128)
    def test_unique_save26_source(self):
        self.assertEqual(m.a.ARTIFACT,11270502866)
        self.assertEqual(m.a.OUTPUT,dict(size=131088,sha256='e65fc5bb2c76d7cfcdd144c1a69451ad8508ff73ad82e4c7f24595d75200624d'))

if __name__=='__main__':unittest.main()
