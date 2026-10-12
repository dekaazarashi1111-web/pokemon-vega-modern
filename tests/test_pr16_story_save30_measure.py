"""Save29以後だけの新しい有界controller。旧受入suiteは実行しない。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save30_measure as m
class Controller(unittest.TestCase):
    def test_save29_remaining_pp(self):self.assertEqual(m.PP,[1,14,0,4])
    def test_no_empty_flamethrower(self):self.assertEqual(m.select([0,0,0,4]),1)
    def test_last_move(self):self.assertEqual(m.select([0,14,0,4]),0)
    def test_exhaustion(self):
        with self.assertRaises(ValueError):m.select([1,14,0,4])
    def test_seven_new_points(self):self.assertEqual(len(m.ROUTE),7)
    def test_west_start(self):self.assertEqual(m.direction(*m.ROUTE[:2]),32)
    def test_final_stair_descent(self):self.assertEqual(m.ROUTE[-3:],[[13,4],[13,5],[13,6]])
    def test_all_adjacent(self):self.assertTrue(all(m.direction(a,b)in(32,64,128)for a,b in zip(m.ROUTE,m.ROUTE[1:])))
    def test_no_repeated_teleport(self):self.assertEqual([v for v in m.ROUTE if v in [[27,7],[19,14],[8,10]]],[])
    def test_not_false_story_completion(self):self.assertFalse(any([x,14]in m.ROUTE for x in range(11,17)))
    def test_unique_save29_parent(self):
        self.assertEqual(m.a.ARTIFACT,11271899477)
        self.assertEqual(m.a.OUTPUT,dict(size=131088,sha256='780c27a138bc0795e2f30c328f69a77ded3569a9960318a61f0dc3d431f56a83'))
    def test_old_ice_pp_rejected(self):
        with self.assertRaises(ValueError):m.select([0,0,0,5])
if __name__=='__main__':unittest.main()

