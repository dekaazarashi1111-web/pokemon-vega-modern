"""Save90退出10歩だけの新controller。未知event/戦闘は停止。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save91_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[10,16],xy=[9,11],live_xy=[16,18],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=90,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11296466834,'5ac6f0f42f6f0cb43e984e34eb6fe5d17667abb29a3b465934e03cd708f20d47'))
    def test_start(self):m.start(self.base())
    def test_exact_route(self):self.assertEqual(m.ROUTE,self.prep()['route']);self.assertEqual((len(m.ROUTE),m.ROUTE[-1]),(11,[6,18]))
    def test_direction_budget(self):self.assertEqual([m.direction(a,b)for a,b in zip(m.ROUTE,m.ROUTE[1:])],[128]*2+[32]*3+[128]*5)
    def test_warp_owner(self):self.assertEqual(self.prep()['warp_owner']['source'],dict(id=1,xy=[6,18],elevation=3,target_warp=2,target_map=[3,2]));self.assertEqual(self.prep()['warp_owner']['target']['xy'],[20,10])
    def test_no_interaction(self):self.assertIsNone(self.prep()['interaction'])
    def test_removed_objects(self):self.assertEqual(self.prep()['initial_expanded_flags'],{str(f):int(f in(4372,4374,4378))for f in range(4372,4379)})
    def test_terrain(self):self.assertEqual(self.prep()['terrain'][10],dict(map=[10,16],xy=[6,18],elevation=3,collision=0,behavior=101))
    def test_static_not_accepted(self):self.assertFalse(self.prep()['route_native_accepted']);self.assertFalse(self.prep()['exit_accepted'])
    def test_consumer_separate(self):p=self.prep();self.assertEqual((p['consumer']['map'],p['consumer']['local_id']),([6,1],2));self.assertFalse(p['paper_delivered']);self.assertTrue(p['required_badge_present'])
    def fake(self,arrival=None,mode=None):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1;ix=min(s.index,10)
                xy=m.ROUTE[ix];where=m.ORIGIN;lock=0;cb=m.m.FIELD
                if s.index>=10:
                    xy=arrival or [20,11];where=m.DESTINATION
                    if mode=='transition'and s.index==10:xy=[6,18];where=m.ORIGIN;lock=1
                    if mode=='need_exit_press'and s.index==10:xy=[6,18];where=m.ORIGIN
                if mode=='blocked':xy=[9,11];where=m.ORIGIN
                if mode=='event'and s.index==1:lock=1
                if mode=='battle'and s.index==1:cb=m.m.BATTLE
                if mode=='early_warp'and s.index==1:xy=[20,11];where=m.DESTINATION
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],map=where,lock=lock,callback2=cb);s.observations.append(s.last);return s.last
        return Walking()
    def test_first_exit_stops(self):
        s=self.fake();route,b,f,w=m.progress(s,{})
        self.assertEqual((b,w,f['kind'],f['map'],f['xy']),(None,[],'new_gym_exit',[3,2],[20,11]));self.assertEqual(len(s.inputs),20);self.assertEqual(route,m.ROUTE[:-1])
    def test_no_guessed_autostep(self):s=self.fake([20,10]);self.assertEqual(m.progress(s,{})[2]['xy'],[20,10]);self.assertEqual(len(s.inputs),20)
    def test_transition_only_wait(self):s=self.fake(mode='transition');m.progress(s,{});self.assertEqual(s.inputs[-1],(0,180));self.assertEqual(len(s.inputs),21)
    def test_exit_press_only_at_warp(self):s=self.fake(mode='need_exit_press');m.progress(s,{});self.assertEqual(s.inputs[-2:],[(128,8),(0,180)]);self.assertEqual(len(s.inputs),22)
    def test_blocked_edge_stops(self):s=self.fake(mode='blocked');self.assertEqual(m.progress(s,{})[2]['kind'],'unpassed_edge');self.assertEqual(len(s.inputs),6)
    def test_no_A_before_save(self):s=self.fake();m.progress(s,{});self.assertTrue(all(k in(0,32,128)for k,_ in s.inputs))
    def test_event_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(mode='event'),{})
    def test_battle_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(mode='battle'),{})
    def test_early_warp_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(mode='early_warp'),{})
    def test_wrong_arrival_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake([21,11]),{})
    def test_pp_unchanged(self):self.assertEqual(m.PP,[3,9,8,2])
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('counter','save_counter',89),('map','map',[6,1]),('xy','xy',[6,7]),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('party','party_sha256','0'*64),('rp','rp',1),('count','party_count',3),('lock','lock',1),('face','facing',2),('callback','callback2',m.m.BATTLE),('live','live_xy',[9,11])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
