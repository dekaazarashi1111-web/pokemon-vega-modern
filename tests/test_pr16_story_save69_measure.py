"""Save68より先の入口階南東階段・保守的3PP予約だけを検証する。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save69_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[1,59],xy=[31,22],live_xy=[38,29],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=68,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11287919858,'f54e7eca96b2808752f7c5c3e6701cca162b569ab16394b50307717b58ec868e'))
    def test_start(self):m.start(self.base())
    def test_exact_unread_suffix(self):
        self.assertEqual(m.ROUTE,m.a.next_route()['route']);self.assertEqual((len(m.ROUTE),m.ROUTE[-1]),(17,[30,29]))
    def test_adjacency(self):self.assertTrue(all(m.direction(a,b)in(16,32,64,128)for a,b in zip(m.ROUTE,m.ROUTE[1:])))
    def test_no_accepted_detour_replayed(self):self.assertEqual(m.ROUTE[:3],[[31,22],[30,22],[29,22]]);self.assertNotIn([25,6],m.ROUTE)
    def test_no_inert_landing(self):self.assertNotIn([20,24],m.ROUTE);self.assertNotIn([20,25],m.ROUTE)
    def test_valid_stair(self):
        p=json.loads((ROOT/'content/modernization/pr16_story_save56_preparation.json').read_bytes());cells={tuple(x['xy']):x for x in p['terrain']}
        for xy in m.ROUTE:self.assertEqual((cells[tuple(xy)]['collision'],cells[tuple(xy)]['elevation'],cells[tuple(xy)]['behavior']),(0,3,108 if xy==[30,29]else 8))
        w=next(x for x in p['interior']['warps']if x['xy']==[30,29]);self.assertEqual((w['target_map'],w['target_warp']),([1,60],3))
    def test_arrival_owner(self):
        p=json.loads((ROOT/m.PREP).read_bytes());w=next(x for x in p['interior']['warps']if x['id']==3);self.assertEqual((w['xy'],w['target_map']),([33,29],[1,59]))
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
        self.assertEqual((route,battle,f['kind'],f['attempts'],f['target']),([[31,22]],None,'unpassed_edge',3,[30,22]));self.assertEqual(len(s.inputs),6)
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',67),('other_map','map',[1,60]),('old_xy','xy',[20,25]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',3),('callback','callback2',m.m.BATTLE),('live','live_xy',[19,13])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()


