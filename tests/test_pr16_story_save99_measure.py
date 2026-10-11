"""Save99専用controller。旧受入の無影響再走なし。"""
import json,pathlib,sys,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save99_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[3,23],xy=[28,39],live_xy=[35,46],facing=2,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=98,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_bytes())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11300996343,'af8190f911ef0e182b22860531c8d0f1a160a57556600a16044edcfca8553cec'))
    def test_start(self):m.start(self.base())
    def test_exact_route(self):self.assertEqual(m.ROUTE,self.prep()['route']);self.assertEqual((len(m.ROUTE),m.ROUTE[0],m.ROUTE[-1]),(62,[28,39],[18,28]))
    def test_directions(self):self.assertEqual(set(m.direction(a,b)for a,b in zip(m.ROUTE,m.ROUTE[1:])),{16,32,64,128})
    def test_pair_avoidance(self):self.assertFalse(any(m.excluded(xy)for xy in m.ROUTE));self.assertTrue(m.excluded([29,27]));self.assertTrue(m.excluded([30,28]));self.assertFalse(m.excluded([32,27]))
    def test_first_grass(self):p=self.prep();self.assertEqual(p['terrain'][12]['xy'],[32,31]);self.assertEqual(p['terrain'][12]['behavior'],2)
    def test_rock_stairs(self):o=self.prep()['rock_stairs_owner'];self.assertEqual((o['behavior'],o['metatile_predicate'],o['player_direction_predicate']),(42,0x8059d1c,0x805b368));self.assertFalse(o['warp']);self.assertFalse(o['one_way_ledge']);self.assertEqual([x['button']for x in o['crossings']],[64,128])
    def test_no_ranger_A(self):p=self.prep();self.assertIsNone(p['interaction']);self.assertFalse(p['ranger_interaction_authorized_for_this_checkpoint']);self.assertEqual(p['objects'][8]['movement_ranges'],[2,2])
    def test_walk_owner_budget(self):p=self.prep()['walk_maintenance'];self.assertEqual((p['happiness_counter'],p['poison_counter'],p['next_happiness_wrap_after_steps']),(30,0,98));self.assertLess(30+len(m.ROUTE)-1,128)
    def test_pp_reservation(self):self.assertEqual(m.PP,[3,9,8,2]);self.assertEqual([m.select(x)for x in([0,0,0,0],[0,0,1,0],[0,0,2,0],[1,0,2,0])],[2,2,0,1])
    def test_pp_exhaustion(self):
        with self.assertRaises(ValueError):m.select([1,3,2,0])
    def test_bad_count(self):
        with self.assertRaises(ValueError):m.select([0,0,-1,0])
    def test_preparation_binding(self):raw=(ROOT/'content/modernization/pr16_story_save98_next_route.json').read_bytes();self.assertEqual(self.prep()['parent_route_binding'],m.identity(raw))
    def test_bindings_count(self):self.assertEqual(len(self.prep()['bindings']),92)
    def test_no_coords(self):self.assertEqual(self.prep()['route_coord_intersections'],[])
    def test_training_flags(self):self.assertEqual(self.prep()['trainer_flag_preflight'],[dict(trainer=1054,physical_flag=1406,won=True),dict(trainer=1055,physical_flag=1407,won=True),dict(trainer=1113,physical_flag=1282,won=False)])
    def fake(self,mode=None):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1;xy=m.ROUTE[min(s.index,61)];cb=m.m.FIELD;lock=0;flags=0
                if mode=='blocked':xy=m.START
                if mode=='event'and s.index==1:lock=1
                if mode=='unknown'and s.index==1:cb=0x8001235
                if mode in('wild','trainer')and s.index==12:cb=m.m.BATTLE;flags=8 if mode=='trainer'else 0
                if mode=='transition'and s.index==12:cb=m.TRANSITION
                if mode=='transition'and s.index==13:xy=m.ROUTE[12];cb=m.m.BATTLE
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],callback2=cb,lock=lock,battle_flags=flags,facing=2);s.observations.append(s.last);return s.last
        return Walking()
    def test_full_route_no_talk(self):
        s=self.fake();route,b,f,w=m.progress(s,self.prep());self.assertEqual((route,b,w,f['kind']),(m.ROUTE,None,[],'ranger_approach_no_interaction'));self.assertEqual(len(s.inputs),122);self.assertTrue(all(k in(0,16,32,64,128)for k,_ in s.inputs))
    def test_blocked_stops(self):s=self.fake('blocked');self.assertEqual(m.progress(s,self.prep())[2]['kind'],'unpassed_edge');self.assertEqual(len(s.inputs),6)
    def test_event_no_decision(self):
        s=self.fake('event')
        with self.assertRaises(ValueError):m.progress(s,self.prep())
        self.assertEqual(s.inputs,[(64,8),(0,48)])
    def test_unknown_no_decision(self):
        s=self.fake('unknown')
        with self.assertRaises(ValueError):m.progress(s,self.prep())
        self.assertEqual(len(s.inputs),2)
    def test_trainer_stops_before_battle_input(self):
        s=self.fake('trainer')
        with patch.object(m,'battle')as battle:
            with self.assertRaises(ValueError):m.progress(s,self.prep())
            battle.assert_not_called()
        self.assertFalse(any(k==1 for k,_ in s.inputs))
    def test_first_wild_then_stop_walk(self):
        s=self.fake('wild');episode=dict(outcome=1,trainer=False)
        with patch.object(m,'battle',return_value=episode)as battle:
            route,b,f,w=m.progress(s,self.prep());battle.assert_called_once()
        self.assertEqual(route,m.ROUTE[:13]);self.assertIs(b,episode);self.assertEqual(f['kind'],'first_new_wild');self.assertEqual(s.index,12)
    def test_transition_zero_only(self):
        s=self.fake('transition')
        with patch.object(m,'battle',return_value=dict(outcome=1,trainer=False)):m.progress(s,self.prep())
        self.assertEqual(s.inputs[-1],(0,60));self.assertFalse(any(k==1 for k,_ in s.inputs))
    def test_party_guard_owner_limited(self):
        o=dict(self.base(),party_sha256='0'*64)
        with self.assertRaises(ValueError):m.walking(o)
    def test_battle_allows_observed_party_change(self):m.scope(dict(self.base(),party_sha256='0'*64,callback2=m.m.BATTLE))
    def test_no_native_in_unit(self):self.assertGreaterEqual(sys.getrecursionlimit(),1500)
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('counter','save_counter',97),('map','map',[3,2]),('xy','xy',[28,38]),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('party','party_sha256','0'*64),('rp','rp',1),('count','party_count',3),('lock','lock',1),('face','facing',4),('callback','callback2',m.m.BATTLE),('live','live_xy',[28,39]),('outcome','battle_outcome',1),('trainer','battle_flags',8)]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
