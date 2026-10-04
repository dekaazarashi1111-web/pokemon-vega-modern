"""Save67より先のNPC北迂回・穴・保守的3PP予約だけを検証する。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save68_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[1,60],xy=[31,20],live_xy=[38,27],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=67,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11288432849,'a4543c8c8d1b47668159adc71a0aff60f2bcf58ac91139d50d6eb201bd9677f5'))
    def test_start(self):m.start(self.base())
    def test_exact_unread_suffix(self):
        self.assertEqual(m.ROUTE,m.a.next_route()['route']);self.assertEqual((len(m.ROUTE),m.ROUTE[-1]),(2,[31,21]))
    def test_adjacency(self):self.assertTrue(all(m.direction(a,b)in(16,32,64,128)for a,b in zip(m.ROUTE,m.ROUTE[1:])))
    def test_no_accepted_detour_replayed(self):self.assertEqual(m.ROUTE,[[31,20],[31,21]]);self.assertNotIn([25,6],m.ROUTE)
    def test_no_inert_landing(self):self.assertNotIn([20,24],m.ROUTE);self.assertNotIn([20,25],m.ROUTE)
    def test_valid_stair(self):
        p=json.loads((ROOT/m.PREP).read_bytes());cells={tuple(x['xy']):x for x in p['terrain']}
        for xy in m.ROUTE:self.assertEqual((cells[tuple(xy)]['collision'],cells[tuple(xy)]['elevation'],cells[tuple(xy)]['behavior']),(0,3,102 if xy==[31,21]else 8))
        w=next(x for x in p['interior']['warps']if x['xy']==[31,21]);self.assertEqual((w['target_map'],w['target_warp']),([1,59],7))
    def test_arrival_owner(self):
        p=json.loads((ROOT/'content/modernization/pr16_story_save56_preparation.json').read_bytes());w=next(x for x in p['interior']['warps']if x['id']==7);self.assertEqual((w['xy'],w['target_map']),([31,22],[1,60]))
    def test_real_pp(self):self.assertEqual(m.PP,[13,10,15,2]);self.assertEqual(m.select([0,0,0,0]),0);self.assertEqual(m.select([4,0,0,0]),2);self.assertEqual(m.select([4,0,5,0]),1)
    def test_exhaustion(self):
        with self.assertRaises(ValueError):m.select([4,3,5,0])
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
        self.assertEqual((route,battle,f['kind'],f['attempts'],f['target']),([[31,20]],None,'unpassed_edge',3,[31,21]));self.assertEqual(len(s.inputs),6)
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',66),('other_map','map',[1,59]),('old_xy','xy',[20,25]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',3),('callback','callback2',m.m.BATTLE),('live','live_xy',[19,13])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()

