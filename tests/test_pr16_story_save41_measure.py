"""Save40より先の西段差/橋候補/有限区間だけ。旧受入試験は継承。"""
import json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save41_measure as m
class West(unittest.TestCase):
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11276815366)
    def test_start(self):self.assertEqual(m.ROUTE[0],[60,10])
    def test_west(self):self.assertEqual(m.ROUTE[1:4],[[59,10],[58,10],[56,10]])
    def test_finite_frontier(self):self.assertEqual(m.ROUTE[-1],[16,19]);self.assertEqual(len(m.ROUTE),57)
    def test_same_map(self):self.assertEqual(m.ORIGIN,m.DESTINATION)
    def test_directions(self):self.assertTrue(all(m.direction(x,y)in(16,32,64,128)for x,y in zip(m.ROUTE,m.ROUTE[1:])))
    def test_ledge(self):self.assertEqual(m.direction([58,10],[56,10]),32)
    def test_other_jump_rejected(self):
        with self.assertRaises(ValueError):m.direction([59,10],[57,10])
    def test_south_jump_rejected(self):
        with self.assertRaises(ValueError):m.direction([58,10],[58,12])
    def test_pp(self):self.assertEqual(m.PP,[1,5,0,0])
    def test_pp_exhausted(self):
        with self.assertRaises(ValueError):m.select([1,5,0,0])
    def test_start_state(self):m.start(dict(map=m.ORIGIN,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=40,xy=[60,10],live_xy=[67,17],battle_outcome=0,facing=3,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH))
    def test_saved_terrain(self):
        p=json.loads((m.ROOT/m.PREP).read_bytes());cells={tuple(x['xy']):x for x in p['allcells']};self.assertEqual(len(cells),1440)
        self.assertTrue(all(cells[tuple(x)]['collision']==0 and cells[tuple(x)]['elevation']in(3,4,15)for x in m.ROUTE));self.assertEqual(cells[(57,10)],dict(xy=[57,10],elevation=0,collision=1,behavior=57))
    def test_three_bridge_cells(self):
        p=json.loads((m.ROOT/m.PREP).read_bytes());cells={tuple(x['xy']):x for x in p['allcells']};self.assertEqual([x for x in m.ROUTE if cells[tuple(x)]['elevation']==15],[[48,11],[34,13],[34,14]])
if __name__=='__main__':unittest.main()
