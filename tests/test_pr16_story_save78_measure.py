"""Save77から第2ディグダへの4歩/旋回/通常Aだけを新規検証。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save78_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[10,16],xy=[6,15],live_xy=[13,22],facing=2,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=77,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11291697564,'11632f541a4c8b6a7782c32b5e30b0c4c9414a8cc4323da0e263e6454cc867e6'))
    def test_start(self):m.start(self.base())
    def test_cold0_is_start(self):self.assertEqual(m.a.COLD_LEDGER,'6270e89696f6f9772615bafcb7f2c84ad3d0d37b78444c099e04d139a4e244b0');self.assertNotEqual(m.a.COLD_LEDGER,m.a.SETTLED_COLD_LEDGER)
    def test_exact_route(self):self.assertEqual(m.ROUTE,[[6,15],[6,14],[6,13],[5,13],[4,13]]);self.assertEqual(m.ROUTE,self.prep()['route'])
    def test_owner(self):self.assertEqual(self.prep()['interaction'],dict(target=[4,12],local_id=6,script=141220288,visibility_flag=4373,button='A',from_xy=[4,13],facing=2))
    def test_initial_flags(self):self.assertEqual(self.prep()['initial_flags'],{str(f):int(f in(4372,4378))for f in range(4372,4379)})
    def test_expected_flags(self):self.assertEqual(self.prep()['expected_flag_changes'],[[4372,1,0],[4375,0,1]])
    def test_expected_objects(self):self.assertEqual(self.prep()['expected_object_changes'],[dict(local_id=9,operation='removeobject'),dict(local_id=5,operation='addobject')])
    def test_branch_owner(self):
        p=self.prep();self.assertEqual(len(p['instructions']),43);self.assertEqual({x['node']for x in p['instructions']},{136400176,141219312,141219331,141220288,141220352,141219510});self.assertEqual([x['hex']for x in p['instructions']if x['node']==141219510],['291711','530900','2a1411','550500','03'])
    def test_texts(self):
        p=self.prep();self.assertEqual(set(p['texts']),{'136400648','136400673'});self.assertIn('はいちが',p['texts']['136400673']['decoded']);self.assertFalse(p['native_route_accepted'])
    def test_no_warp_or_battle_requested(self):self.assertEqual((m.ORIGIN,m.DESTINATION),([10,16],[10,16]));self.assertNotIn(92,[x['opcode']for x in self.prep()['instructions']])
    def test_unpassed_edge(self):
        class Stationary:
            def __init__(s,o):s.last=o;s.observations=[o];s.inputs=[]
            def step(s,*keys):s.inputs.extend(keys);s.observations.append(s.last);return s.last
        s=Stationary(self.base());route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,f['kind'],f['attempts'],f['target']),([[6,15]],None,'unpassed_edge',3,[6,14]));self.assertEqual(len(s.inputs),6)
    def fake(self,early=False,no_lock=False,bad_turn=False):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1
                if early:xy=[6,14];lock=int(s.index==1);facing=2
                else:xy=m.ROUTE[min(s.index,4)];lock=int(s.index==6 and not no_lock);facing=2 if s.index<3 or s.index>=5 else 3
                if bad_turn and s.index==5:facing=3
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],lock=lock,facing=facing);s.observations.append(s.last);return s.last
        return Walking()
    def test_normal_interaction_once(self):
        s=self.fake();route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,w),(m.ROUTE+[[4,13]],None,[]));self.assertEqual((f['kind'],f['local_id'],f['trigger'],f['observation']),('second_diglett_event',6,[4,12],7));self.assertEqual(s.inputs,[(64,8),(0,48)]*2+[(32,8),(0,48)]*2+[(64,1),(0,24),(1,2),(0,60),(1,2),(0,180)])
    def test_north_turn_required(self):
        with self.assertRaises(ValueError):m.progress(self.fake(bad_turn=True),{})
    def test_no_event_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(no_lock=True),{})
    def test_unexpected_early_event_stops(self):
        s=self.fake(early=True);route,b,f,w=m.progress(s,{});self.assertEqual((f['kind'],f['trigger'],len(s.inputs)),('new_event',[6,14],4))
    def test_pp_unchanged_budget(self):self.assertEqual(m.PP,[9,10,15,2])
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',76),('outside_map','map',[3,2]),('old_xy','xy',[6,18]),('settled_cold_ledger','ledger_sha256',m.a.SETTLED_COLD_LEDGER),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',1),('callback','callback2',m.m.BATTLE),('live','live_xy',[6,15])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
