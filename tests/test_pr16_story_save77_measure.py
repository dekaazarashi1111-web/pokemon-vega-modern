"""Save76からの初ディグダ有限入力・初回ownerを新規検証。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save77_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[10,16],xy=[6,18],live_xy=[13,25],facing=2,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=76,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11291861689,'10c7d4b96e2b36db13158ba3a8d8929caabac28275e98e01a93c586b0315d836'))
    def test_start(self):m.start(self.base())
    def test_exact_route(self):self.assertEqual(m.ROUTE,[[6,18],[6,17],[6,16],[6,15]]);self.assertEqual(m.ROUTE,self.prep()['route'])
    def test_owner(self):self.assertEqual(self.prep()['interaction'],dict(target=[6,14],local_id=5,script=141220048,visibility_flag=4372,first_use_flag=4378,button='A',from_xy=[6,15],facing=2))
    def test_initial_flags(self):self.assertEqual(self.prep()['initial_flags'],{str(f):0 for f in range(4372,4379)})
    def test_expected_event(self):self.assertEqual(self.prep()['expected_flag_changes'],[[4372,0,1],[4378,0,1]]);self.assertEqual(self.prep()['expected_removed_local_id'],5)
    def test_first_use_owner_only(self):
        p=self.prep();self.assertEqual(len(p['instructions']),29);self.assertEqual({x['node']for x in p['instructions']},{136400176,141219312,141219331,141219344,141220048});self.assertEqual([x['hex']for x in p['instructions']if x['node']==141219344],['291a11','291411','530500','03'])
    def test_texts(self):
        p=self.prep();self.assertEqual(set(p['texts']),{'136400648','136400673'});self.assertIn('はいちが',p['texts']['136400673']['decoded']);self.assertFalse(p['native_route_accepted'])
    def test_no_warp_or_battle_requested(self):self.assertEqual((m.ORIGIN,m.DESTINATION),([10,16],[10,16]));self.assertNotIn(92,[x['opcode']for x in self.prep()['instructions']])
    def test_unpassed_edge(self):
        class Stationary:
            def __init__(s,o):s.last=o;s.observations=[o];s.inputs=[]
            def step(s,*keys):s.inputs.extend(keys);s.observations.append(s.last);return s.last
        s=Stationary(self.base());route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,f['kind'],f['attempts'],f['target']),([[6,18]],None,'unpassed_edge',3,[6,17]));self.assertEqual(len(s.inputs),6)
    def fake(self,early=False,no_lock=False):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1
                if early:
                    xy=[6,17];lock=int(s.index==1)
                else:xy=m.ROUTE[min(s.index,3)];lock=int(s.index==4 and not no_lock)
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],lock=lock);s.observations.append(s.last);return s.last
        return Walking()
    def test_normal_interaction_once(self):
        s=self.fake();route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,w),([[6,18],[6,17],[6,16],[6,15],[6,15]],None,[]));self.assertEqual((f['kind'],f['local_id'],f['trigger'],f['observation']),('first_diglett_event',5,[6,14],5));self.assertEqual(s.inputs,[(64,8),(0,48)]*3+[(1,2),(0,60),(1,2),(0,180)])
    def test_no_event_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(no_lock=True),{})
    def test_unexpected_early_event_stops(self):
        s=self.fake(early=True);route,b,f,w=m.progress(s,{});self.assertEqual((f['kind'],f['trigger'],len(s.inputs)),('new_event',[6,17],4))
    def test_pp_unchanged_budget(self):self.assertEqual(m.PP,[9,10,15,2])
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',75),('outside_map','map',[3,2]),('old_xy','xy',[15,20]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',1),('callback','callback2',m.m.BATTLE),('live','live_xy',[6,18])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
