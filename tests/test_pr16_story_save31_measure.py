"""Save30下層以降の新しい段差2辺・story終端だけ。旧suite再実行なし。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save31_measure as m
class Controller(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11273101471)
    def test_start(self):self.assertEqual(m.ROUTE[0],[13,6])
    def test_terminal_owner(self):self.assertEqual(m.ROUTE[-1],[14,14])
    def test_two_ledge_edges(self):self.assertEqual(len(m.JUMPS),2)
    def test_first_south_ledge(self):self.assertEqual(m.direction([14,8],[14,10]),128)
    def test_second_south_ledge(self):self.assertEqual(m.direction([14,12],[14,14]),128)
    def test_unauthorized_two_step(self):
        with self.assertRaises(ValueError):m.direction([13,6],[13,8])
    def test_reverse_ledge(self):
        with self.assertRaises(ValueError):m.direction([14,10],[14,8])
    def test_three_tiles(self):
        with self.assertRaises(ValueError):m.direction([14,8],[14,11])
    def test_all_route_edges(self):self.assertEqual([m.direction(x,y)for x,y in zip(m.ROUTE,m.ROUTE[1:])],[128,16,128,128,128,128,128])
    def test_no_replayed_west_stair(self):self.assertNotIn([13,5],m.ROUTE)
    def test_no_replayed_teleport(self):self.assertTrue(all(x not in m.ROUTE for x in [[27,7],[19,14],[8,10]]))
if __name__=='__main__':unittest.main()
