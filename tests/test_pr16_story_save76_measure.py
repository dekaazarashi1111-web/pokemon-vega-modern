"""封書のbadge gateとSave75からの新ジム入口を限定検証。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save76_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[3,2],xy=[15,20],live_xy=[22,27],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=75,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11290759615,'6554c5f872f710b4dbef5a2db06fbf3d2b91ab3a2984008be53c7ce1ecf4ffb2'))
    def test_start(self):m.start(self.base())
    def test_exact_route(self):self.assertEqual(m.ROUTE,self.prep()['route']);self.assertEqual((len(m.ROUTE),m.ROUTE[-1]),(16,[20,10]))
    def test_adjacency(self):self.assertTrue(all(m.direction(a,b)in(16,32,64,128)for a,b in zip(m.ROUTE,m.ROUTE[1:])))
    def test_no_old_mansion(self):self.assertNotIn([15,19],m.ROUTE);self.assertEqual((m.ORIGIN,m.DESTINATION),([3,2],[10,16]))
    def test_entry_warp_owner(self):
        p=self.prep()['route_owner'];self.assertEqual((p['town_warp']['xy'],p['town_warp']['target_map'],p['town_warp']['target_warp']),([20,10],[10,16],1));self.assertEqual(p['arrival']['xy'],[6,18])
    def test_consumer_owner(self):
        p=self.prep();self.assertEqual((p['consumer']['map'],p['consumer_local_id'],p['consumer_root']),([6,1],2,149013250));self.assertEqual(p['required_badge_flag'],2083)
    def test_check_then_remove(self):
        refs=self.prep()['selected_graph']['references'];self.assertTrue(any(r['command']=='checkitem'and r['value']==274 for r in refs));self.assertTrue(any(r['command']=='removeitem'and r['value']==274 for r in refs));self.assertTrue(any(r['command']=='checkflag'and r['value']==2083 for r in refs))
    def test_delivery_separate_from_pickup(self):
        p=self.prep();self.assertEqual((p['paper_delivered_flag'],p['paper_obtained_flag']),(4382,4383));self.assertFalse(p['native_route_accepted'])
    def test_door_collision_is_not_flat_ground(self):
        p=self.prep();c=p['terrain'][-1];self.assertEqual((c['xy'],c['elevation'],c['collision'],c['behavior']),([20,10],0,1,105))
    def test_bounded_provenance_disclaims_global(self):self.assertFalse(self.prep()['discovery']['full_global_correctness_claimed'])
    def test_real_pp(self):self.assertEqual(m.PP,[9,10,15,2]);self.assertEqual(m.select([0,0,0,0]),0)
    def test_unpassed_edge_stops(self):
        class Stationary:
            def __init__(s,o):s.last=o;s.observations=[o];s.inputs=[]
            def step(s,*keys):s.inputs.extend(keys);s.observations.append(s.last);return s.last
        s=Stationary(self.base());route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,f['kind'],f['attempts'],f['target']),([[15,20]],None,'unpassed_edge',3,[16,20]));self.assertEqual(len(s.inputs),6)
    def fake(self,event=False,arrival=None):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1
                if event and s.index<=2:xy=m.ROUTE[1];s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],lock=int(s.index==1))
                else:
                    xy=(arrival or [6,17])if s.index>=15 else m.ROUTE[s.index];where=[10,16]if s.index>=15 else [3,2];s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],map=where)
                s.observations.append(s.last);return s.last
        return Walking()
    def test_first_entry_stops(self):
        s=self.fake();route,b,f,w=m.progress(s,{});self.assertEqual((b,w,f['kind'],f['map'],f['xy']),(None,[],'new_gym_entry',[10,16],[6,17]));self.assertEqual(len(s.inputs),30)
    def test_no_guessed_automatic_step(self):
        s=self.fake(arrival=[6,18]);_,_,f,_=m.progress(s,{});self.assertEqual(f['xy'],[6,18]);self.assertEqual(len(s.inputs),30)
    def test_first_event_stops_before_entry(self):
        s=self.fake(event=True);route,b,f,w=m.progress(s,{});self.assertEqual((route,b,w,f['kind'],f['trigger']),([[15,20],[16,20]],None,[],'new_event',[16,20]));self.assertEqual(len(s.inputs),4)
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',74),('other_map','map',[1,59]),('old_xy','xy',[20,24]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',3),('callback','callback2',m.m.BATTLE),('live','live_xy',[19,13])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
