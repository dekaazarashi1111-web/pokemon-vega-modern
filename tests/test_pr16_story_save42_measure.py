"""Save41より先の橋下/階段/橋上候補だけ。旧受入試験を再実行しない。"""
import json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save42_measure as m
class Bridge(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11277075434)
    def test_start(self):self.assertEqual(m.ROUTE[0],[48,11])
    def test_south(self):self.assertEqual(m.ROUTE[:5],[[48,11],[48,12],[48,13],[48,14],[48,15]])
    def test_finite_frontier(self):self.assertEqual(m.ROUTE[-1],[47,13]);self.assertEqual(len(m.ROUTE),22)
    def test_same_map(self):self.assertEqual(m.ORIGIN,m.DESTINATION)
    def test_directions(self):self.assertTrue(all(m.direction(x,y)in(16,32,64,128)for x,y in zip(m.ROUTE,m.ROUTE[1:])))
    def test_no_blocked_edge(self):self.assertNotIn(([48,11],[47,11]),list(zip(m.ROUTE,m.ROUTE[1:])))
    def test_jump_rejected(self):
        with self.assertRaises(ValueError):m.direction([58,10],[56,10])
    def test_pp(self):self.assertEqual(m.PP,[1,5,0,0])
    def test_pp_exhausted(self):
        with self.assertRaises(ValueError):m.select([1,5,0,0])
    def test_pp_remaining(self):self.assertEqual(m.select([0,5,0,0]),0)
    def test_start_state(self):m.start(dict(map=m.ORIGIN,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=41,xy=[48,11],live_xy=[55,18],battle_outcome=0,facing=3,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH))
    def cells(self):return {tuple(x['xy']):x for x in json.loads((m.ROOT/m.PREP).read_bytes())['allcells']}
    def test_saved_terrain(self):self.assertEqual(len(self.cells()),1440);self.assertEqual(m.elevation_path(self.cells(),m.ROUTE,3),[3]*12+[0]+[4]*9)
    def test_old_failed_elevation_rejected(self):
        with self.assertRaises(ValueError):m.elevation_path(self.cells(),[[48,11],[47,11]],3)
    def test_same_bridge_two_levels(self):
        self.assertEqual(m.elevation_path(self.cells(),[[48,13]],3),[3]);self.assertEqual(m.elevation_path(self.cells(),[[48,13]],4),[4])
    def test_stairs(self):self.assertEqual(self.cells()[(54,15)],dict(xy=[54,15],elevation=0,collision=0,behavior=42))
if __name__=='__main__':unittest.main()
