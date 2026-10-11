"""Save71より先の上階南側・紙側初到着・保守的3PP予約だけを検証する。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save72_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[1,60],xy=[23,31],live_xy=[30,38],facing=3,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=71,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11289573274,'87f67074b6d470df8260e15d2bd58566f949a6297318a1e7a9ee3d9b80cbb6fd'))
    def test_start(self):m.start(self.base())
    def test_exact_unread_suffix(self):
        self.assertEqual(m.ROUTE,m.a.next_route()['route']);self.assertEqual((len(m.ROUTE),m.ROUTE[-1]),(12,[16,27]))
    def test_adjacency(self):self.assertTrue(all(m.direction(a,b)in(16,32,64,128)for a,b in zip(m.ROUTE,m.ROUTE[1:])))
    def test_no_accepted_detour_replayed(self):self.assertEqual(m.ROUTE[:3],[[23,31],[22,31],[21,31]]);self.assertNotIn([30,29],m.ROUTE)
    def test_no_inert_landing(self):self.assertNotIn([20,24],m.ROUTE);self.assertNotIn([20,25],m.ROUTE)
    def test_upper_terrain(self):
        p=json.loads((ROOT/m.PREP).read_bytes());cells={tuple(x['xy']):x for x in p['terrain']}
        for xy in m.ROUTE:self.assertEqual((cells[tuple(xy)]['collision'],cells[tuple(xy)]['elevation'],cells[tuple(xy)]['behavior']),(0,3,8))
    def test_paper_side_only(self):
        self.assertEqual((m.ORIGIN,m.DESTINATION,m.ROUTE[-1]),([1,60],[1,60],[16,27]));self.assertNotIn([16,28],m.ROUTE)
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
        self.assertEqual((route,battle,f['kind'],f['attempts'],f['target']),([[23,31]],None,'unpassed_edge',3,[22,31]));self.assertEqual(len(s.inputs),6)
    def test_complete_route_stops_without_interaction(self):
        class Walking:
            def __init__(s,o):s.last=o;s.observations=[o];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1;s.last=dict(s.last,xy=m.ROUTE[s.index],live_xy=[v+7 for v in m.ROUTE[s.index]]);s.observations.append(s.last);return s.last
        s=Walking(self.base());route,battle,f,_=m.progress(s,{})
        self.assertEqual((route,battle,f['kind'],f['observation']),(m.ROUTE,None,'new_paper_side_arrival',11));self.assertEqual(len(s.inputs),22);self.assertTrue(all(k in(0,16,32,64,128)for k,n in s.inputs))
    def test_locked_event_stops_at_first_new_event(self):
        class Event:
            def __init__(s,o):s.last=o;s.observations=[o];s.inputs=[]
            def step(s,*keys):
                s.inputs.extend(keys);s.last=dict(s.last,xy=[22,31],live_xy=[29,38],lock=1 if len(s.observations)==1 else 0);s.observations.append(s.last);return s.last
        s=Event(self.base());route,battle,f,_=m.progress(s,{})
        self.assertEqual((route,battle,f['kind'],f['trigger']),([[23,31],[22,31]],None,'new_event',[22,31]));self.assertEqual(len(s.observations),3)
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',70),('other_map','map',[1,59]),('old_xy','xy',[20,25]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',4),('callback','callback2',m.m.BATTLE),('live','live_xy',[19,13])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()


