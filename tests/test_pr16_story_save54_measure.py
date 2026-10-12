"""Save53室内経路と受付会話の新しい境界だけ。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save54_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[6,5],xy=[7,8],live_xy=[14,15],facing=2,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=53,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual(m.a.ARTIFACT,11283178064)
    def test_start(self):m.start(self.base())
    def test_four_steps(self):self.assertEqual(m.ROUTE,[[7,8],[7,7],[7,6],[7,5],[7,4]])
    def test_all_north(self):self.assertTrue(all(m.direction(a,b)==64 for a,b in zip(m.ROUTE,m.ROUTE[1:])))
    def test_counter(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(p['terrain'][-1],dict(xy=[7,3],elevation=0,collision=1,behavior=128))
    def test_path(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertTrue(all(x['elevation']==3 and x['collision']==x['behavior']==0 for x in p['terrain'][:-1]))
    def test_conversation(self):
        o=self.base();o.update(xy=[7,4],live_xy=[14,11],lock=1);m.conversation_scope(o)
    def test_heal_not_rejected(self):
        o=self.base();o.update(xy=[7,4],live_xy=[14,11],lock=1,party_sha256='new_observed_party');m.conversation_scope(o)
    def test_ledger(self):self.assertEqual(m.a.COLD_LEDGER,m.a.LEDGER)
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',52),('town','map',[3,2]),('old_xy','xy',[28,0]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',1),('callback','callback2',m.m.BATTLE),('live','live_xy',[7,8])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
