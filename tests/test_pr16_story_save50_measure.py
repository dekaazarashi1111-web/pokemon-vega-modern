"""505で新しく追加した高度候補と現在PPだけ。旧試験を再走しない。"""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_save50_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[3,23],xy=[33,0],live_xy=[40,7],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=49,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH)
    def cells(self):return {(0,y):dict(elevation=3,collision=0,behavior=0)for y in range(3)}
    def test_parent49(self):self.assertEqual(m.a.ARTIFACT,11280742739);self.assertEqual(m.a.OUTPUT['sha256'],'21374dbfbc9e38f0febf16304706b7f3b14feacf204d5956bd622dcf941b1a04')
    def test_start49(self):m.start(self.base())
    def test_reject_old_counter(self):
        o=self.base();o['save_counter']=48
        with self.assertRaises(ValueError):m.start(o)
    def test_reject_wrong_map(self):
        o=self.base();o['map']=[3,44]
        with self.assertRaises(ValueError):m.start(o)
    def test_destination50(self):
        o=self.base();o.update(map=[3,2],save_counter=50);m.idle(o,50)
    def test_reject_lock(self):
        o=self.base();o['lock']=1
        with self.assertRaises(ValueError):m.start(o)
    def test_reject_camera(self):
        o=self.base();o['live_xy']=[33,0]
        with self.assertRaises(ValueError):m.start(o)
    def test_route_simple(self):self.assertEqual(m.route_to_south(self.cells(),set(),(0,0),3),([[0,0],[0,1],[0,2]],[3,3,3]))
    def test_route_reject_cliff(self):
        c=self.cells();c[(0,1)]['elevation']=4
        with self.assertRaises(ValueError):m.route_to_south(c,set(),(0,0),3)
    def test_route_stairs(self):
        c=self.cells();c[(0,1)]['elevation']=0;c[(0,2)]['elevation']=4
        self.assertEqual(m.route_to_south(c,set(),(0,0),3)[1],[3,0,4])
    def test_route_reject_wall(self):
        c=self.cells();c[(0,1)]['collision']=1
        with self.assertRaises(ValueError):m.route_to_south(c,set(),(0,0),3)
    def test_route_reject_object(self):
        with self.assertRaises(ValueError):m.route_to_south(self.cells(),{(0,1)},(0,0),3)
    def test_route_avoid_grass(self):
        c=self.cells();c[(0,1)]['behavior']=2
        for y in range(3):c[(1,y)]=dict(elevation=3,collision=0,behavior=0)
        route,_=m.route_to_south(c,set(),(0,0),3);self.assertNotIn([0,1],route)
    def test_route_reject_unread(self):
        c=self.cells();del c[(0,1)]
        with self.assertRaises(ValueError):m.route_to_south(c,set(),(0,0),3)
    def test_current_pp(self):self.assertEqual(m.PP,[11,10,15,20]);self.assertEqual(m.select([0]*4),3);self.assertEqual(m.select([0,0,0,20]),0)
    def test_pp_exhausted(self):
        with self.assertRaises(ValueError):m.select([11,10,15,20])
    def test_pp_negative(self):
        with self.assertRaises(ValueError):m.select([-1,0,0,0])
    def test_actual_classifier(self):self.assertIs(m.classify,m.a.m.classify)
    def test_direction(self):self.assertEqual(m.direction([33,0],[33,1]),128)
    def test_nonadjacent(self):
        with self.assertRaises(ValueError):m.direction([33,0],[32,1])
if __name__=='__main__':unittest.main()
