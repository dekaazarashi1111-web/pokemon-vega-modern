"""Save88から第10ディグダへ南2西3南2東6の新13歩/4旋回/通常Aの新規controller検証。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save89_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[10,16],xy=[6,7],live_xy=[13,14],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=88,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11295552942,'a99af1391ac7bd9a05cffa8487d868aff2c6e31a48aea2a27c1c2a90ebeb1b0c'))
    def test_start(self):m.start(self.base())
    def test_cold0_is_start(self):self.assertEqual(m.a.COLD_LEDGER,'3a31eca68c049166e0aed0585c4bd44619b108ceea489c5e954f2dc34c916251');self.assertEqual(m.a.COLD_LEDGER,m.a.SETTLED_COLD_LEDGER)
    def test_exact_route(self):self.assertEqual(m.ROUTE,[[6, 7], [6, 8], [6, 9], [5, 9], [4, 9], [3, 9], [3, 10], [3, 11], [4, 11], [5, 11], [6, 11], [7, 11], [8, 11], [9, 11]]);self.assertEqual(m.ROUTE,self.prep()['route'])
    def test_owner(self):self.assertEqual(self.prep()['interaction'],{'local_id': 8, 'target': [9, 12], 'script': 141220512, 'visibility_flag': 4374, 'button': 'A', 'from_xy': [9, 11], 'facing': 1, 'object_address': 155169756, 'object_hex': '0881000009000c000308110000000000a0da6a0816110000'})
    def test_initial_flags(self):self.assertEqual(self.prep()['initial_flags'],{'4372': 0, '4373': 0, '4374': 0, '4375': 0, '4376': 1, '4377': 0, '4378': 1})
    def test_expected_flags(self):self.assertEqual(self.prep()['expected_flag_changes'],[[4375, 0, 1], [4376, 1, 0]])
    def test_expected_objects(self):self.assertEqual(self.prep()['expected_object_changes'],[{'local_id': 9, 'operation': 'removeobject'}, {'local_id': 10, 'operation': 'addobject'}])
    def test_branch_owner(self):
        p=self.prep();self.assertEqual(len(p['instructions']),39);self.assertEqual({x['node']for x in p['instructions']},{141220512, 141219331, 141219692, 136400176, 141219312, 141220720});self.assertEqual([x['hex']for x in p['instructions']if x['node']==141219692],['291711', '530900', '2a1811', '550a00', '03'])
    def test_texts(self):
        p=self.prep();self.assertEqual(set(p['texts']),{'136400648','136400673'});self.assertIn('はいちが',p['texts']['136400673']['decoded']);self.assertFalse(p['native_route_accepted'])
    def test_no_warp_or_battle_requested(self):self.assertEqual((m.ORIGIN,m.DESTINATION),([10,16],[10,16]));self.assertNotIn(92,[x['opcode']for x in self.prep()['instructions']])
    def test_unpassed_edge(self):
        class Stationary:
            def __init__(s,o):s.last=o;s.observations=[o];s.inputs=[]
            def step(s,*keys):s.inputs.extend(keys);s.observations.append(s.last);return s.last
        s=Stationary(self.base());route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,f['kind'],f['attempts'],f['target']),([[6,7]],None,'unpassed_edge',3,[6,8]));self.assertEqual(len(s.inputs),6)
    def fake(self,early=False,no_lock=False,bad_turn=False):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0;s.event=False
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1;key,frames=keys[0];xy=s.last['xy'];facing=s.last['facing'];lock=0
                if key in (16,32,64,128):
                    face={16:4,32:3,64:2,128:1}[key]
                    if face==facing and frames>1:xy=[xy[0]+int(key==16)-int(key==32),xy[1]+int(key==128)-int(key==64)]
                    facing=face
                    if bad_turn and frames==1:facing=2
                if key==1:
                    lock=int(not s.event and not no_lock);s.event=True
                if early and s.index==1:lock=1
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],lock=lock,facing=facing);s.observations.append(s.last);return s.last
        return Walking()
    def test_normal_interaction_once(self):
        s=self.fake();route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,w),(m.ROUTE+[[9,11]],None,[]));self.assertEqual((f['kind'],f['local_id'],f['trigger'],f['observation']),('tenth_diglett_event',8,[9,12],19));self.assertEqual(s.inputs,[(128,8),(0,48)]*2+[(32,8),(0,48)]*4+[(128,8),(0,48)]*3+[(16,8),(0,48)]*7+[(128,1),(0,24),(1,2),(0,60),(1,2),(0,180)])
    def test_south_turn_required(self):
        with self.assertRaises(ValueError):m.progress(self.fake(bad_turn=True),{})
    def test_no_event_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(no_lock=True),{})
    def test_unexpected_early_event_stops(self):
        s=self.fake(early=True);route,b,f,w=m.progress(s,{});self.assertEqual((f['kind'],f['trigger'],len(s.inputs)),('new_event',[6,8],6))
    def test_pp_unchanged_budget(self):self.assertEqual(m.PP,[3,9,8,2])
    def test_all_thirteen_edges_are_adjacent(self):self.assertEqual(len(m.ROUTE)-1,13);self.assertEqual([m.direction(a,b)for a,b in zip(m.ROUTE,m.ROUTE[1:])],[128]*2+[32]*3+[128]*2+[16]*6)
    def test_unexpected_battle_rejected(self):
        s=self.fake();s.last['callback2']=m.m.BATTLE
        with self.assertRaises(ValueError):m.event(s,[[6,7]],[6,8])
    def test_badge_and_money_bound_to_winning_parent(self):
        p=self.prep();self.assertTrue(p['required_badge_present']);self.assertFalse(p['paper_delivered']);self.assertEqual(p['input_save'],m.a.OUTPUT)
    def test_distinct_parent_flags(self):self.assertNotEqual(self.prep()['initial_flags'],{str(f):int(f in(4372,4374,4378))for f in range(4372,4379)})
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',87),('outside_map','map',[3,2]),('old_xy','xy',[9,13]),('bad_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',2),('callback','callback2',m.m.BATTLE),('live','live_xy',[9,13])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()


