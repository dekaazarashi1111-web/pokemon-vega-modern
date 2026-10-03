"""新階層の隣接経路と像eventだけを許すSave57 controller。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save57_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[1,59],xy=[20,25],live_xy=[27,32],facing=2,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=56,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11284293358)
    def test_start(self):m.start(self.base())
    def test_entry_route(self):self.assertEqual(m.ROUTE,[[20,25],[20,24]])
    def test_adjacent(self):self.assertEqual([m.direction(a,b)for a,b in zip(m.INTERIOR_ROUTE,m.INTERIOR_ROUTE[1:])],[64,32,32,128,128,32,32,128,128])
    def test_pp(self):self.assertEqual(m.PP,[15,10,15,14]);self.assertEqual(m.select([0,0,0,14]),0)
    def test_arrival_suffix(self):self.assertEqual(m.INTERIOR_ROUTE[:2],[[20,24],[20,23]])
    def test_statue_approach(self):self.assertEqual((m.INTERIOR_ROUTE[-1],m.STATUE),([16,27],[16,28]))
    def test_terrain(self):
        p=json.loads((ROOT/m.PREP).read_bytes());cells={tuple(x['xy']):x for x in p['terrain']}
        for xy in m.INTERIOR_ROUTE:self.assertEqual((cells[tuple(xy)]['collision'],cells[tuple(xy)]['elevation'],cells[tuple(xy)]['behavior']),(0,3,102 if xy==[20,24]else 8))
    def test_paper_owner(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(next(x for x in p['bgs']if x['xy']==m.STATUE)['value'],149012422)
        self.assertTrue(any(x['address']==149012477 and x['hex']=='4412010100'for x in p['instructions']))
        self.assertTrue(any(x['address']==149012505 and x['hex']=='291f11'for x in p['instructions']))
    def test_no_route_npc(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertTrue(all(x['xy']not in m.INTERIOR_ROUTE for x in p['interior']['objects']))
    def test_only_arrival_warp(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual([x['id']for x in p['interior']['warps']if x['xy']in m.INTERIOR_ROUTE],[5])
    def test_nonadjacent_rejected(self):
        with self.assertRaises(ValueError):m.direction([20,24],[18,23])
    def test_no_host_recovery(self):
        with self.assertRaises(ValueError):m.select(m.PP)
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',55),('other_map','map',[1,60]),('old_xy','xy',[16,20]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',1),('callback','callback2',m.m.BATTLE),('live','live_xy',[20,25])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
