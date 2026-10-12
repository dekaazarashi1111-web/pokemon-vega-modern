"""新しいtown入口とSave52 cold ledgerを限定検査。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save53_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[3,2],xy=[28,0],live_xy=[35,7],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=52,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11282311020)
    def test_start(self):m.start(self.base())
    def test_current_route(self):self.assertEqual((m.ROUTE[0],m.ROUTE[-1],len(m.ROUTE)),([28,0],[38,16],27))
    def test_adjacent(self):self.assertTrue(all(m.direction(a,b)in(16,32,64,128)for a,b in zip(m.ROUTE,m.ROUTE[1:])))
    def test_door_north(self):self.assertEqual(m.direction([38,16],[38,15]),64)
    def test_destination(self):
        o=self.base();o.update(map=[6,5],xy=[7,7],live_xy=[14,14],save_counter=53);m.idle(o,53)
    def test_owner_saved(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(p['candidate_interior']['map'],[6,5]);self.assertTrue(any(x['category']=='special'and x['value']==0 for x in p['graph']['references']))
    def test_terrain_saved(self):
        p=json.loads((ROOT/m.PREP).read_bytes());c={tuple(x['xy']):x for x in p['previous_terrain']+p['terrain']};self.assertTrue(all(c[tuple(x)]['elevation']==3 and c[tuple(x)]['collision']==0 for x in m.ROUTE[1:]))
    def test_new_scope(self):self.assertEqual(m.CODE,{'content/modernization/pr16_story_save53_owner.json','scripts/pr16_story_save53_measure.py','tests/test_pr16_story_save53_measure.py','.github/workflows/pr16-story-save53.yml'})
    def test_no_recovery_claim(self):self.assertNotEqual(m.a.COLD_LEDGER,m.a.LEDGER)
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',51),('old_map','map',[3,23]),('old_xy','xy',[31,24]),('old_ledger','ledger_sha256',m.a.LEDGER),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',2)]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
