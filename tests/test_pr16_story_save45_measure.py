"""控え先頭の実PP/共通PP UIと西上段の未到達区間だけ。"""
import json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save45_measure as m
class Controller(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11278342404)
    def test_start(self):self.assertEqual(m.ROUTE[0],[39,12])
    def test_new_first_step(self):self.assertEqual(m.ROUTE[1],[38,12])
    def test_finite_frontier(self):self.assertEqual(m.ROUTE[-1],[26,12]);self.assertEqual(len(m.ROUTE),20)
    def test_same_map(self):self.assertEqual(m.ORIGIN,m.DESTINATION)
    def test_directions(self):self.assertTrue(all(m.direction(x,y)in(16,32,64,128)for x,y in zip(m.ROUTE,m.ROUTE[1:])))
    def test_old_prefix_excluded(self):self.assertNotIn([47,13],m.ROUTE)
    def test_jump_rejected(self):
        with self.assertRaises(ValueError):m.direction([39,12],[37,12])
    def test_pp(self):self.assertEqual(m.PP,[15,10,15,20]);self.assertEqual(m.select([0]*4),3)
    def test_pp_exhausted(self):
        with self.assertRaises(ValueError):m.select([15,10,15,20])
    def test_pp_switch(self):self.assertEqual(m.select([0,0,0,20]),0)
    def test_pp_negative(self):
        with self.assertRaises(ValueError):m.select([-1,0,0,0])
    def test_saved_terrain(self):
        cells={tuple(x['xy']):x for x in json.loads((m.ROOT/m.PREP).read_bytes())['allcells']};self.assertEqual(len(cells),1440);self.assertEqual(m.elevation_path(cells,m.ROUTE,4),[4]*18+[0,3])
    def test_descent(self):self.assertEqual(m.ROUTE[-3:],[[26,10],[26,11],[26,12]])
    def test_move_cursor(self):
        for i in range(4):
            v=['other']*4;v[i]=m.m.ARROW;self.assertEqual(m.classify_digests(m.PP_LABEL,v,''),('moves',i))
    def test_ambiguous_cursor(self):
        with self.assertRaises(ValueError):m.classify_digests(m.PP_LABEL,[m.m.ARROW]*4,'')
    def test_missing_cursor(self):
        with self.assertRaises(ValueError):m.classify_digests(m.PP_LABEL,['']*4,'')
    def test_shift(self):self.assertEqual(m.classify_digests('',[],m.m.SHIFT),('shift',None))
    def test_action_is_not_move(self):self.assertEqual(m.classify_digests('',['']*4,''),('other',None))
    def test_pp_label_required(self):self.assertEqual(m.classify_digests('',[m.m.ARROW,'','',''],''),('other',None))
if __name__=='__main__':unittest.main()
