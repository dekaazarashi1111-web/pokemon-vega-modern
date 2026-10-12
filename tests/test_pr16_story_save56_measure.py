"""Save55以降の通常入館と新廊下の有界controller。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save56_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[3,2],xy=[16,20],live_xy=[23,27],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=55,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11284146293)
    def test_start(self):m.start(self.base())
    def test_entry_route(self):self.assertEqual(m.ROUTE,[[16,20],[15,20],[15,19]])
    def test_frontier(self):self.assertEqual((m.INTERIOR_ROUTE[0],m.INTERIOR_ROUTE[-1]),([20,33],[20,25]))
    def test_entry_spawn(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(next(w for w in p['interior']['warps']if w['id']==1)['xy'],m.INTERIOR_ROUTE[0])
    def test_adjacent(self):self.assertTrue(all(m.direction(a,b)==64 for a,b in zip(m.INTERIOR_ROUTE,m.INTERIOR_ROUTE[1:])))
    def test_pp(self):self.assertEqual(m.PP,[15,10,15,14]);self.assertEqual(m.select([0,0,0,14]),0)
    def test_entry(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(next(w for w in p['town']['warps']if w['xy']==[15,19])['target_map'],[1,59])
    def test_wild_terrain(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertTrue(all(t['behavior']==(101 if t['xy']==[20,33]else 8) and t['collision']==0 for t in p['terrain']if t['xy']in m.INTERIOR_ROUTE))
    def test_ledger(self):self.assertEqual(m.a.COLD_LEDGER,'77ccaa1d7ceee4a641d1094ab5b8f5caf44668ea125287542f3e2bed65a80e57')
    def test_unread_floor(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(next(w for w in p['interior']['warps']if w['xy']==[20,24])['target_map'],[1,60])
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',54),('other_map','map',[6,5]),('old_xy','xy',[7,4]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',2),('callback','callback2',m.m.BATTLE),('live','live_xy',[16,20])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
