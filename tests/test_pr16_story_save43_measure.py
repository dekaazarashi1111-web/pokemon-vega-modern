"""Save42橋上から先の上段西進/下り階段候補だけ。旧受入の再実行0。"""
import json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save43_measure as m
class UpperWest(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11277536596)
    def test_start(self):self.assertEqual(m.ROUTE[0],[47,13])
    def test_first_turn(self):self.assertEqual(m.ROUTE[:3],[[47,13],[46,13],[46,12]])
    def test_finite_frontier(self):self.assertEqual(m.ROUTE[-1],[26,12]);self.assertEqual(len(m.ROUTE),29)
    def test_same_map(self):self.assertEqual(m.ORIGIN,m.DESTINATION)
    def test_directions(self):self.assertTrue(all(m.direction(x,y)in(16,32,64,128)for x,y in zip(m.ROUTE,m.ROUTE[1:])))
    def test_old_boundary_excluded(self):self.assertNotIn([48,11],m.ROUTE)
    def test_jump_rejected(self):
        with self.assertRaises(ValueError):m.direction([58,10],[56,10])
    def test_pp(self):self.assertEqual(m.PP,[1,5,0,0])
    def test_pp_exhausted(self):
        with self.assertRaises(ValueError):m.select([1,5,0,0])
    def test_pp_remaining(self):self.assertEqual(m.select([0,5,0,0]),0)
    def test_start_state(self):m.start(dict(map=m.ORIGIN,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=42,xy=[47,13],live_xy=[54,20],battle_outcome=0,facing=3,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH))
    def cells(self):return {tuple(x['xy']):x for x in json.loads((m.ROOT/m.PREP).read_bytes())['allcells']}
    def test_saved_terrain(self):self.assertEqual(len(self.cells()),1440);self.assertEqual(m.elevation_path(self.cells(),m.ROUTE,4),[4]*27+[0,3])
    def test_wrong_start_height_rejected(self):
        with self.assertRaises(ValueError):m.elevation_path(self.cells(),m.ROUTE,3)
    def test_descent_vertices(self):self.assertEqual(m.ROUTE[-3:],[[26,10],[26,11],[26,12]])
    def test_stairs(self):self.assertEqual(self.cells()[(26,11)],dict(xy=[26,11],elevation=0,collision=0,behavior=42))
if __name__=='__main__':unittest.main()
