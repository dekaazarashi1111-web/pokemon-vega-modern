"""Save74より先のNPC北迂回・穴・保守的3PP予約だけを検証する。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save75_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[1,59],xy=[20,24],live_xy=[27,31],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=74,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11290343975,'34a689de13a412f4d81f396aef0ec90291050ff3334fec2b048b203f3a8bd76b'))
    def test_start(self):m.start(self.base())
    def test_exact_unread_suffix(self):
        self.assertEqual(m.ROUTE,m.a.next_route()['route']);self.assertEqual((len(m.ROUTE),m.ROUTE[-1]),(10,[20,33]))
    def test_adjacency(self):self.assertTrue(all(m.direction(a,b)in(16,32,64,128)for a,b in zip(m.ROUTE,m.ROUTE[1:])))
    def test_no_accepted_detour_replayed(self):self.assertEqual(m.ROUTE,[[20,y]for y in range(24,34)]);self.assertNotIn([16,27],m.ROUTE)
    def test_exit_distinct_from_old_descent(self):self.assertEqual((m.ORIGIN,m.DESTINATION),([1,59],[3,2]))
    def test_valid_exit(self):
        p=m.a.next_route();self.assertEqual((p['exit_warp']['xy'],p['exit_warp']['target_map'],p['exit_warp']['target_warp']),([20,33],[3,2],7))
        for c in p['terrain']:self.assertEqual((c['collision'],c['elevation'],c['behavior']),(0,3,101 if c['xy']==[20,33]else 8))
    def test_arrival_owner_not_guess(self):
        p=m.a.next_route();self.assertEqual((p['town_warp']['xy'],p['possible_auto_step_xy']),([15,19],[15,20]));self.assertFalse(p['arrival_xy_native_accepted'])
    def test_real_pp(self):self.assertEqual(m.PP,[9,10,15,2]);self.assertEqual(m.select([0,0,0,0]),0);self.assertEqual(m.select([3,0,0,0]),2);self.assertEqual(m.select([3,0,5,0]),1)
    def test_exhaustion(self):
        with self.assertRaises(ValueError):m.select([3,3,5,0])
    def test_no_nonadjacent_input(self):
        with self.assertRaises(ValueError):m.direction([19,13],[7,12])
    def test_transition_wait_only(self):self.assertEqual(m.event_input(dict(callback2=m.TRANSITION,lock=1)),((0,60),))
    def test_no_unlocked_unknown_callback(self):
        with self.assertRaises(ValueError):m.event_input(dict(callback2=0x08000201,lock=0))
    def test_move_target_separation(self):
        b=m.MoveBudget();b.selected(0,True);self.assertEqual(b.commands,[1,0,0,0]);self.assertEqual(b.target(0),0);self.assertEqual(b.commands,[1,0,0,0]);self.assertEqual(b.targets,1)
    def test_unpassed_edge_stops(self):
        class Stationary:
            def __init__(s,o):s.last=o;s.observations=[o];s.inputs=[]
            def step(s,*keys):s.inputs.extend(keys);s.observations.append(s.last);return s.last
        s=Stationary(self.base());route,battle,f,_=m.progress(s,{})
        self.assertEqual((route,battle,f['kind'],f['attempts'],f['target']),([[20,24]],None,'unpassed_edge',3,[20,25]));self.assertEqual(len(s.inputs),6)
    def fake(self,mode='exit',arrival=None):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1
                if mode=='event' and s.index<=2:
                    xy=m.ROUTE[1];s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],lock=int(s.index==1))
                else:
                    xy=(arrival or [15,20])if s.index>=9 else m.ROUTE[s.index];where=[3,2]if s.index>=9 else [1,59]
                    s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],map=where)
                s.observations.append(s.last);return s.last
        return Walking()
    def test_nine_steps_then_first_exit_stops(self):
        s=self.fake();route,b,f,w=m.progress(s,{})
        self.assertEqual((b,w,f['kind'],f['map'],f['xy']),(None,[],'new_mansion_exit',[3,2],[15,20]));self.assertEqual(len(s.inputs),18);self.assertTrue(all(k in(0,128)for k,n in s.inputs))
    def test_actual_warp_tile_retained_without_guessed_auto_step(self):
        s=self.fake(arrival=[15,19]);route,b,f,w=m.progress(s,{});self.assertEqual(f['xy'],[15,19]);self.assertEqual(len(s.inputs),18)
    def test_first_event_stops_before_exit(self):
        s=self.fake('event');route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,w,f['kind'],f['trigger']),([[20,24],[20,25]],None,[],'new_event',[20,25]));self.assertEqual(len(s.inputs),4)
    def test_letter_route_binding(self):
        p=m.a.next_route();self.assertEqual((p['paper_item'],p['paper_quantity'],p['paper_flag']),(274,1,4383));self.assertFalse(p['mansion_exit_observed'])
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',73),('other_map','map',[1,60]),('old_xy','xy',[20,25]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',3),('callback','callback2',m.m.BATTLE),('live','live_xy',[19,13])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()

