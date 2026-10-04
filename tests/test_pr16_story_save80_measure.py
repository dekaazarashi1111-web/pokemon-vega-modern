"""Save79から第4ディグダへ新10歩/3旋回/通常Aの新規controller検証。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save80_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[10,16],xy=[9,13],live_xy=[16,20],facing=2,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=79,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11292333576,'88040caadde36a1cbad95bb8e558650089d868d742bba16809a3a32f8ae7553b'))
    def test_start(self):m.start(self.base())
    def test_cold0_is_start(self):self.assertEqual(m.a.COLD_LEDGER,'6027627107d4372b8f105caf2e5afbeafe1fe86b6d34bfb2a1931e0e3628f5bf');self.assertEqual(m.a.COLD_LEDGER,m.a.SETTLED_COLD_LEDGER)
    def test_exact_route(self):self.assertEqual(m.ROUTE,[[9,13],[9,12],[9,11]]+[[x,11]for x in range(8,2,-1)]+[[3,10],[3,9]]);self.assertEqual(m.ROUTE,self.prep()['route'])
    def test_owner(self):self.assertEqual(self.prep()['interaction'],dict(target=[2,9],local_id=9,script=141220736,visibility_flag=4375,button='A',from_xy=[3,9],facing=3))
    def test_initial_flags(self):self.assertEqual(self.prep()['initial_flags'],{str(f):int(f in(4372,4374,4378))for f in range(4372,4379)})
    def test_expected_flags(self):self.assertEqual(self.prep()['expected_flag_changes'],[[4372,1,0],[4374,1,0],[4375,0,1]])
    def test_expected_objects(self):self.assertEqual(self.prep()['expected_object_changes'],[dict(local_id=9,operation='removeobject'),dict(local_id=5,operation='addobject'),dict(local_id=8,operation='addobject')])
    def test_branch_owner(self):
        p=self.prep();self.assertEqual(len(p['instructions']),47);self.assertEqual({x['node']for x in p['instructions']},{136400176,141219312,141219331,141220736,141220800,141220832,141219848});self.assertEqual([x['hex']for x in p['instructions']if x['node']==141219848],['291711','530900','2a1411','550500','2a1611','550800','03'])
    def test_texts(self):
        p=self.prep();self.assertEqual(set(p['texts']),{'136400648','136400673'});self.assertIn('はいちが',p['texts']['136400673']['decoded']);self.assertFalse(p['native_route_accepted'])
    def test_no_warp_or_battle_requested(self):self.assertEqual((m.ORIGIN,m.DESTINATION),([10,16],[10,16]));self.assertNotIn(92,[x['opcode']for x in self.prep()['instructions']])
    def test_unpassed_edge(self):
        class Stationary:
            def __init__(s,o):s.last=o;s.observations=[o];s.inputs=[]
            def step(s,*keys):s.inputs.extend(keys);s.observations.append(s.last);return s.last
        s=Stationary(self.base());route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,f['kind'],f['attempts'],f['target']),([[9,13]],None,'unpassed_edge',3,[9,12]));self.assertEqual(len(s.inputs),6)
    def fake(self,early=False,no_lock=False,bad_turn=False):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0;s.event=False
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1;key,frames=keys[0];xy=s.last['xy'];facing=s.last['facing'];lock=0
                if key in (16,32,64,128):
                    face={16:4,32:3,64:2,128:1}[key]
                    if face==facing and frames>1:xy=[xy[0]+int(key==16)-int(key==32),xy[1]+int(key==128)-int(key==64)]
                    facing=face
                    if bad_turn and frames==1:facing=1
                if key==1:
                    lock=int(not s.event and not no_lock);s.event=True
                if early and s.index==1:lock=1
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],lock=lock,facing=facing);s.observations.append(s.last);return s.last
        return Walking()
    def test_normal_interaction_once(self):
        s=self.fake();route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,w),(m.ROUTE+[[3,9]],None,[]));self.assertEqual((f['kind'],f['local_id'],f['trigger'],f['observation']),('fourth_diglett_event',9,[2,9],15));self.assertEqual(s.inputs,[(64,8),(0,48)]*2+[(32,8),(0,48)]*7+[(64,8),(0,48)]*3+[(32,1),(0,24),(1,2),(0,60),(1,2),(0,180)])
    def test_west_turn_required(self):
        with self.assertRaises(ValueError):m.progress(self.fake(bad_turn=True),{})
    def test_no_event_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(no_lock=True),{})
    def test_unexpected_early_event_stops(self):
        s=self.fake(early=True);route,b,f,w=m.progress(s,{});self.assertEqual((f['kind'],f['trigger'],len(s.inputs)),('new_event',[9,12],4))
    def test_pp_unchanged_budget(self):self.assertEqual(m.PP,[9,10,15,2])
    def test_all_ten_edges_are_adjacent(self):self.assertEqual(len(m.ROUTE)-1,10);self.assertEqual([m.direction(a,b)for a,b in zip(m.ROUTE,m.ROUTE[1:])],[64]*2+[32]*6+[64]*2)
    def test_distinct_parent_flags(self):self.assertNotEqual(self.prep()['initial_flags'],{str(f):int(f in(4375,4378))for f in range(4372,4379)})
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',78),('outside_map','map',[3,2]),('old_xy','xy',[4,13]),('old_save77_ledger','ledger_sha256',m.a.m.a.m.a.COLD_LEDGER),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',1),('callback','callback2',m.m.BATTLE),('live','live_xy',[9,13])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
