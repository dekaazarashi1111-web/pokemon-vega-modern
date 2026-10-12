"""Save47の残区間と実PP再束縛だけの新規試験。受入済UI/旧native再走なし。"""
import json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save48_measure as m
class Controller(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11279895650)
    def test_start(self):self.assertEqual(m.ROUTE[0],[11,5])
    def test_new_first_step(self):self.assertEqual(m.ROUTE[1],[11,4])
    def test_npc_avoided(self):self.assertNotIn([12,5],m.ROUTE);self.assertEqual(m.ROUTE[:4],[[11,5],[11,4],[12,4],[13,4]])
    def test_finite_frontier(self):self.assertEqual(m.ROUTE[-1],[17,19]);self.assertEqual(len(m.ROUTE),69)
    def test_same_map(self):self.assertEqual(m.ORIGIN,m.DESTINATION)
    def test_directions(self):self.assertTrue(all(m.direction(x,y)in(16,32,64,128)for x,y in zip(m.ROUTE,m.ROUTE[1:])))
    def test_upper_prefix_excluded(self):self.assertNotIn([39,12],m.ROUTE);self.assertNotIn([26,11],m.ROUTE)
    def test_jump_rejected(self):
        with self.assertRaises(ValueError):m.direction([11,5],[13,5])
    def test_pp_current_parent(self):self.assertEqual(m.PP,[11,10,15,20]);self.assertIsNot(m.select,m.a.m.select)
    def test_prefer_aerial_ace(self):self.assertEqual(m.select([0,0,0,0]),3)
    def test_fallback_uses_current_bounds(self):self.assertEqual(m.select([11,0,0,20]),2)
    def test_exhausted_rejected(self):
        with self.assertRaises(ValueError):m.select([11,10,15,20])
    def test_stale_pp_rejected(self):
        with self.assertRaises(ValueError):m.select([12,0,0,0])
    def test_invalid_count_rejected(self):
        for used in ([0,0,0],[0,0,0,-1],[False,0,0,0]):
            with self.assertRaises(ValueError):m.select(used)
    def test_classifier_inherited(self):self.assertIs(m.classify,m.a.classify_panel)
    def test_saved_terrain(self):
        cells={tuple(x['xy']):x for x in json.loads((m.ROOT/m.PREP).read_bytes())['allcells']};self.assertEqual(len(cells),1440);self.assertEqual(m.elevation_path(cells,m.ROUTE,3),[3]*69)
    def test_route_no_repeat(self):self.assertEqual(len(m.ROUTE),len(set(map(tuple,m.ROUTE))))
if __name__=='__main__':unittest.main()
