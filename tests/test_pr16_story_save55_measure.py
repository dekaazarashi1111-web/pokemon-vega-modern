"""Save54回復後出口・必須レンジャー経路の新境界。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save55_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[6,5],xy=[7,4],live_xy=[14,11],facing=2,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=54,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11283366654)
    def test_start(self):m.start(self.base())
    def test_exit_route(self):self.assertEqual(m.ROUTE,[[7,4],[7,5],[7,6],[7,7],[7,8]])
    def test_required_target(self):self.assertEqual((len(m.TOWN_ROUTE),m.TOWN_ROUTE[0],m.TOWN_ROUTE[-1]),(27,[38,16],[16,20]))
    def test_adjacency(self):self.assertTrue(all(m.direction(a,b)in(16,32,64,128)for a,b in zip(m.TOWN_ROUTE,m.TOWN_ROUTE[1:])))
    def test_recovered_pp(self):self.assertEqual(m.PP,[15,10,15,20]);self.assertEqual(m.select([0]*4),3)
    def test_owner(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual({x['value']for x in p['graph']['references']if 'town_npc_10'in x['roots']and x['category']=='trainer'},{329,330,331})
    def test_exit_arrow(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(p['new_terrain'][0],dict(map=[6,5],xy=[7,8],elevation=3,collision=0,behavior=101))
    def test_new_healed_ledger(self):self.assertEqual(m.a.COLD_LEDGER,'3aef553d4f2dba8f52868966ed63e2e315f111535d017321afe1c0df1a7bd384')
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',53),('town','map',[3,2]),('old_xy','xy',[7,8]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',1),('callback','callback2',m.m.BATTLE),('live','live_xy',[7,4])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
