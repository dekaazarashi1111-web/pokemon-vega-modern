"""Save28以後だけの新しい有界controller。旧受入suiteは実行しない。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save29_measure as m
class Controller(unittest.TestCase):
    def test_save28_remaining_pp(self):self.assertEqual(m.PP,[1,14,0,5])
    def test_ice_first(self):self.assertEqual(m.select([0,0,0,0]),3)
    def test_no_empty_flamethrower(self):self.assertEqual(m.select([0,0,0,5]),1)
    def test_last_move(self):self.assertEqual(m.select([0,14,0,5]),0)
    def test_exhaustion(self):
        with self.assertRaises(ValueError):m.select([1,14,0,5])
    def test_old_save27_pp_rejected(self):
        with self.assertRaises(ValueError):m.select([0,0,1,0])
    def test_negative_rejected(self):
        with self.assertRaises(ValueError):m.select([-1,0,0,0])
    def test_bool_rejected(self):
        with self.assertRaises(ValueError):m.select([False,0,0,0])
    def test_twenty_new_points(self):self.assertEqual(len(m.ROUTE),20)
    def test_west_start(self):self.assertEqual(m.direction(*m.ROUTE[:2]),32)
    def test_final_stair_descent(self):self.assertEqual(m.ROUTE[-3:],[[13,4],[13,5],[13,6]])
    def test_all_adjacent(self):self.assertTrue(all(m.direction(a,b)in(32,64,128)for a,b in zip(m.ROUTE,m.ROUTE[1:])))
    def test_no_repeated_teleport(self):self.assertEqual([v for v in m.ROUTE if v in [[27,7],[19,14],[8,10]]],[[27,7]])
    def test_not_false_story_completion(self):self.assertFalse(any([x,14]in m.ROUTE for x in range(11,17)))
    def test_teleport_direction_rejected(self):
        with self.assertRaises(ValueError):m.direction([27,7],[19,14])
    def test_unique_save28_parent(self):
        self.assertEqual(m.a.ARTIFACT,11271154923)
        self.assertEqual(m.a.OUTPUT,dict(size=131088,sha256='a5cfc5714bcc447550d78ff45f42c74109f12d607bad1d94dbf61fe96b06f4a4'))
if __name__=='__main__':unittest.main()
