"""Save31後の南回廊/東階段/解禁後teleportだけの変更試験。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save32_measure as m
class Controller(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11273187310)
    def test_start(self):self.assertEqual(m.ROUTE[0],[14,14])
    def test_target(self):self.assertEqual(m.ROUTE[-1],[19,14])
    def test_new_jump(self):self.assertEqual(m.direction([14,14],[14,16]),128)
    def test_one_jump(self):self.assertEqual(len(m.JUMPS),1)
    def test_no_replay_jump(self):
        with self.assertRaises(ValueError):m.direction([14,12],[14,14])
    def test_reverse_jump(self):
        with self.assertRaises(ValueError):m.direction([14,16],[14,14])
    def test_three_tiles(self):
        with self.assertRaises(ValueError):m.direction([14,14],[14,17])
    def test_no_replayed_save30_path(self):self.assertNotIn([13,6],m.ROUTE)
    def test_south_bottom(self):self.assertIn([23,19],m.ROUTE)
    def test_new_stair(self):self.assertIn([23,14],m.ROUTE)
    def test_route_edges(self):self.assertEqual(len([m.direction(x,y)for x,y in zip(m.ROUTE,m.ROUTE[1:])]),24)
if __name__=='__main__':unittest.main()
