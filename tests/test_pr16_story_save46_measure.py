"""Save45以西の下段候補だけを追加検査。無変更の技UI/controllerは継承。"""
import json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save46_measure as m
class Controller(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11278563389)
    def test_start(self):self.assertEqual(m.ROUTE[0],[26,12])
    def test_new_first_step(self):self.assertEqual(m.ROUTE[1],[25,12])
    def test_finite_frontier(self):self.assertEqual(m.ROUTE[-1],[3,12]);self.assertEqual(len(m.ROUTE),28)
    def test_same_map(self):self.assertEqual(m.ORIGIN,m.DESTINATION)
    def test_directions(self):self.assertTrue(all(m.direction(x,y)in(16,32,64,128)for x,y in zip(m.ROUTE,m.ROUTE[1:])))
    def test_upper_prefix_excluded(self):self.assertNotIn([39,12],m.ROUTE);self.assertNotIn([26,11],m.ROUTE)
    def test_jump_rejected(self):
        with self.assertRaises(ValueError):m.direction([26,12],[24,12])
    def test_pp_unchanged_source(self):self.assertIs(m.select,m.a.m.select);self.assertEqual(m.PP,m.a.m.PP)
    def test_classifier_unchanged_source(self):self.assertIs(m.classify,m.a.m.classify)
    def test_saved_terrain(self):
        cells={tuple(x['xy']):x for x in json.loads((m.ROOT/m.PREP).read_bytes())['allcells']};self.assertEqual(len(cells),1440);self.assertEqual(m.elevation_path(cells,m.ROUTE,3),[3]*28)
    def test_route_no_repeat(self):self.assertEqual(len(m.ROUTE),len(set(map(tuple,m.ROUTE))))
if __name__=='__main__':unittest.main()
