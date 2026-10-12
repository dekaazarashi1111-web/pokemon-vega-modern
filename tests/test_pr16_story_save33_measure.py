"""Save32後の東階段/解禁後teleportだけの変更試験。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save33_measure as m
class Controller(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11273920453)
    def test_start(self):self.assertEqual(m.ROUTE[0],[21,19])
    def test_target(self):self.assertEqual(m.ROUTE[-1],[19,14])
    def test_no_old_ledge(self):self.assertFalse(m.JUMPS)
    def test_no_old_route(self):self.assertNotIn([14,14],m.ROUTE)
    def test_no_jump(self):
        with self.assertRaises(ValueError):m.direction([14,14],[14,16])
    def test_diagonal(self):
        with self.assertRaises(ValueError):m.direction([21,19],[22,18])
    def test_stairs(self):self.assertIn([23,14],m.ROUTE)
    def test_edges(self):self.assertEqual(len([m.direction(x,y)for x,y in zip(m.ROUTE,m.ROUTE[1:])]),13)
    def test_remaining_pp(self):self.assertEqual(m.PP,[1,14,0,0])
    def test_main_move(self):self.assertEqual(m.select([0,0,0,0]),1)
    def test_backup(self):self.assertEqual(m.select([0,14,0,0]),0)
    def test_no_pp(self):
        with self.assertRaises(ValueError):m.select([1,14,0,0])
    def test_exhausted_ice(self):
        with self.assertRaises(ValueError):m.select([0,0,0,1])
    def test_exhausted_flame(self):
        with self.assertRaises(ValueError):m.select([0,0,1,0])
if __name__=='__main__':unittest.main()
