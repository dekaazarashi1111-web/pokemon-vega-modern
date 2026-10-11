"""Save97から新35歩と通常北connectionだけ。旧受入caseの再走なし。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save98_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[3,2],xy=[19,26],live_xy=[26,33],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=97,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11300361541,'4871ba79e718ea8dc8bc701394846ce1b393cd41a5961564ed4d670437a52139'))
    def test_start(self):m.start(self.base())
    def test_exact_route(self):self.assertEqual(m.ROUTE,self.prep()['route']);self.assertEqual((len(m.ROUTE),m.ROUTE[0],m.ROUTE[-1]),(36,[19,26],[28,0]))
    def test_route_directions(self):self.assertEqual([m.direction(a,b)for a,b in zip(m.ROUTE,m.ROUTE[1:])],[16]*4+[64]*15+[16]*2+[64]*2+[16]*3+[64]*9)
    def test_no_interaction(self):self.assertIsNone(self.prep()['interaction']);self.assertFalse(self.prep()['ranger_interaction_authorized_for_this_checkpoint'])
    def test_connection_owner(self):p=self.prep()['connection_owner'];self.assertEqual((p['source'],p['reciprocal']),(dict(direction=2,offset=0,target_map=[3,23]),dict(direction=1,offset=0,target_map=[3,2])))
    def test_normal_connection_preflight(self):p=self.prep()['connection_owner'];self.assertEqual((p['classification'],p['button'],p['direction'],p['source_edge'],p['input_target'],p['target_candidate']),('CONTIGUOUS_MAP_CONNECTION_NOT_WARP_EVENT',64,2,[28,0],[28,-1],[28,39]));self.assertFalse(p['native_accepted'])
    def test_edge_and_landing_behavior(self):self.assertEqual(self.prep()['terrain'][-2:],[dict(map=[3,2],xy=[28,0],collision=0,elevation=3,behavior=33),dict(map=[3,23],xy=[28,39],collision=0,elevation=3,behavior=33)])
    def test_no_coord_intersections(self):self.assertEqual(self.prep()['route_coord_intersections'],[])
    def test_no_warp_events(self):p=self.prep();self.assertFalse(any(w['xy']in m.ROUTE for w in p['town']['warps']));self.assertFalse(any(w['xy']==m.ARRIVAL for w in p['north']['warps']))
    def test_no_static_npc_intersections(self):p=self.prep();self.assertFalse(any(o['xy']in m.ROUTE for o in p['town']['objects']));self.assertFalse(any(o['xy']==m.ARRIVAL for o in p['north']['objects']))
    def test_letter_and_fee_preserved(self):p=self.prep();self.assertEqual((p['paper_quantity'],p['money'],p['museum_admission_var4061']),(0,23114,1));self.assertTrue(p['paper_delivered_flag4382']);self.assertTrue(p['paper_obtain_flag4383']);self.assertFalse(p['completion_flag4380'])
    def test_pp(self):self.assertEqual(m.PP,[3,9,8,2])
    def fake(self,mode=None,arrival=None):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1;xy=m.ROUTE[min(s.index,35)];where=m.ORIGIN;lock=0;cb=m.m.FIELD
                if s.index>=36:xy=arrival or m.ARRIVAL;where=m.DESTINATION
                if mode=='transition'and s.index==36:xy=m.EDGE;where=m.ORIGIN;lock=1
                if mode=='forever'and s.index>=36:xy=m.EDGE;where=m.ORIGIN;lock=1
                if mode=='connection_blocked'and s.index>=36:xy=m.EDGE;where=m.ORIGIN
                if mode=='blocked':xy=m.START;where=m.ORIGIN
                if mode=='event'and s.index==1:lock=1
                if mode=='battle'and s.index==1:cb=m.m.BATTLE
                if mode=='early_map'and s.index==1:xy=m.ARRIVAL;where=m.DESTINATION
                party=m.PARTY_AFTER_WALK if where==m.DESTINATION or xy in m.ROUTE[6:]else m.a.PARTY
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],map=where,lock=lock,callback2=cb,facing=2,party_sha256=party);s.observations.append(s.last);return s.last
        return Walking()
    def test_first_field_stops(self):
        s=self.fake();route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,w,f['kind'],f['map'],f['xy'],f['edge_observation']),(m.ROUTE,None,[],'new_town_north_connection',[3,23],[28,39],35));self.assertEqual(len(s.inputs),72);self.assertEqual(s.inputs[-2:],[(64,8),(0,180)])
    def test_transition_wait_only(self):s=self.fake(mode='transition');m.progress(s,{});self.assertEqual(s.inputs[-1],(0,180));self.assertEqual(len(s.inputs),73)
    def test_no_A_before_save(self):s=self.fake();m.progress(s,{});self.assertTrue(all(k in(0,16,32,64,128)for k,_ in s.inputs))
    def test_blocked_edge_stop(self):s=self.fake(mode='blocked');self.assertEqual(m.progress(s,{})[2]['kind'],'unpassed_edge');self.assertEqual(len(s.inputs),6)
    def test_event_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(mode='event'),{})
    def test_battle_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(mode='battle'),{})
    def test_early_map_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(mode='early_map'),{})
    def test_wrong_arrival_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(arrival=[28,38]),{})
    def test_finite_transition(self):
        s=self.fake(mode='forever')
        with self.assertRaises(ValueError):m.progress(s,{})
        self.assertEqual(len(s.inputs),75)
    def test_finite_blocked_connection(self):
        s=self.fake(mode='connection_blocked')
        with self.assertRaises(ValueError):m.progress(s,{})
        self.assertEqual(len(s.inputs),78)
    def test_scope_party_changed(self):
        o=self.base();o['party_sha256']='0'*64
        with self.assertRaises(ValueError):m.scope(o)
    def test_scope_flash_changed(self):
        o=self.base();o['flash_sha256']='0'*64
        with self.assertRaises(ValueError):m.scope(o)
    def test_scope_battle_flags(self):
        o=self.base();o['battle_flags']=8
        with self.assertRaises(ValueError):m.scope(o)
    def test_exact_party_phase(self):
        o=dict(self.base(),xy=[23,24],live_xy=[30,31],party_sha256=m.PARTY_AFTER_WALK);m.scope(o)
        o['party_sha256']=m.a.PARTY
        with self.assertRaises(ValueError):m.scope(o)
    def test_party_phase_too_early(self):
        o=dict(self.base(),xy=[23,25],live_xy=[30,32],party_sha256=m.PARTY_AFTER_WALK)
        with self.assertRaises(ValueError):m.scope(o)
    def test_preimage_identity_bytes_contract(self):
        source=(ROOT/'scripts/pr16_story_save98_measure.py').read_text();self.assertIn("identity(bytes(derived))",source);self.assertNotIn("identity(derived)",source)
        with self.assertRaises(ValueError):m.identity(bytearray(b'123'))
        self.assertEqual(m.identity(bytes(bytearray(b'123'))),m.identity(b'123'))
    def test_failed_input_preserved(self):
        p=json.loads((ROOT/m.RECOVERY).read_bytes());self.assertEqual(p['failed_execution']['initial_save'],p['failed_execution']['final_save']);self.assertEqual(p['diagnostic_exact_preimage_deltas'],[[41,48,49],[141,13,14],[241,111,112]]);self.assertFalse(p['runtime_owner_resolved']);self.assertEqual((p['inputs'],p['observations'],p['ordinary_saves']),(28,9,0))
    def test_history_import_limit(self):self.assertGreaterEqual(sys.getrecursionlimit(),1500)
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('counter','save_counter',96),('map','map',[6,0]),('xy','xy',[19,25]),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('party','party_sha256','0'*64),('rp','rp',1),('count','party_count',3),('lock','lock',1),('face','facing',4),('callback','callback2',m.m.BATTLE),('live','live_xy',[9,11])]:setattr(Controller,'test_reject_'+name,negative(key,value))
class StaticPreparation(unittest.TestCase):
    def test_exact_parent_route(self):raw=(ROOT/'content/modernization/pr16_story_save97_next_route.json').read_bytes();p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(p['parent_route_binding'],m.identity(raw));self.assertNotEqual(p['parent_route_binding'],m.identity(raw+b'\n'))
    def test_bindings(self):self.assertEqual(len(json.loads((ROOT/m.PREP).read_bytes())['bindings']),94)
    def test_route_terrain(self):p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(len(p['terrain']),37);self.assertTrue(all(t['collision']==0 and t['behavior']in(0,33)for t in p['terrain']))
if __name__=='__main__':unittest.main()
