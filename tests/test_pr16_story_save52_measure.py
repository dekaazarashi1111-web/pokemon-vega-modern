"""Save51の新入力境界とtrainer全方向過大近似の回避だけ。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save52_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[3,23],xy=[31,24],live_xy=[38,31],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=51,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH)
    def objects(self):return [dict(xy=[29,27],movement_range_x=1,movement_range_y=1,trainer_range=1)]
    def cells(self):return {(x,y):dict(elevation=3,collision=0,behavior=0)for x in range(4)for y in range(4)}
    def test_parent51(self):self.assertEqual(m.a.ARTIFACT,11281768926);self.assertEqual(m.a.OUTPUT['sha256'],'8661346e2de9bc73fc61d5a63af5bd6acd10008486b54c66c9459820a5447d65')
    def test_start51(self):m.start(self.base())
    def test_old_counter_rejected(self):
        o=self.base();o['save_counter']=50
        with self.assertRaises(ValueError):m.start(o)
    def test_old_xy_rejected(self):
        o=self.base();o.update(xy=[22,18],live_xy=[29,25])
        with self.assertRaises(ValueError):m.start(o)
    def test_old_party_rejected(self):
        o=self.base();o['party_sha256']=m.a.m.a.PARTY
        with self.assertRaises(ValueError):m.start(o)
    def test_current_pp14(self):self.assertEqual(m.PP,[11,10,15,14]);self.assertEqual(m.select([0,0,0,14]),0)
    def test_old_pp_rejected(self):
        with self.assertRaises(ValueError):m.select([0,0,0,15])
    def test_destination52(self):
        o=self.base();o.update(map=[3,2],xy=[28,0],live_xy=[35,7],save_counter=52);m.idle(o,52)
    def test_center_excluded(self):self.assertTrue(m.excluded((29,27),self.objects()))
    def test_moved_sight_excluded(self):self.assertTrue(m.excluded((31,27),self.objects()))
    def test_other_direction_excluded(self):self.assertTrue(m.excluded((29,29),self.objects()))
    def test_outside_conservative_range(self):self.assertFalse(m.excluded((32,27),self.objects()))
    def test_diagonal_outside(self):self.assertFalse(m.excluded((31,29),self.objects()))
    def test_no_objects(self):self.assertFalse(m.excluded((0,0),[]))
    def test_route_basic(self):self.assertEqual(m.route_to_south(self.cells(),set(),[],(0,0),(0,3)),[[0,0],[0,1],[0,2],[0,3]])
    def test_route_avoids_grass(self):
        c=self.cells();c[(0,1)]['behavior']=2;self.assertNotIn([0,1],m.route_to_south(c,set(),[],(0,0),(0,3)))
    def test_unreachable_rejected(self):
        with self.assertRaises(ValueError):m.route_to_south({},set(),[],(0,0),(0,3))
    def test_fixed_reused_route(self):
        t=json.loads((ROOT/m.TERRAIN).read_bytes());p=json.loads((ROOT/m.PREP).read_bytes());c={tuple(x['xy']):x for x in t['allcells']};occupied={tuple(o['xy'])for o in t['inherited_view']['objects']};r=m.route_to_south(c,occupied,p['objects']);self.assertEqual(len(r),21);self.assertEqual(r[0],[31,24]);self.assertEqual(r[-1],[28,39]);self.assertTrue(all(not m.excluded(tuple(x),p['objects'])for x in r));self.assertEqual(sum(c[tuple(x)]['behavior']==2 for x in r),4)
if __name__=='__main__':unittest.main()
