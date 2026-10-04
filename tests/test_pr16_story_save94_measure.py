"""Save93支払済み階段9歩だけの新controller。未知event/戦闘は停止。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save94_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[6,0],xy=[14,5],live_xy=[21,12],facing=4,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=93,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11298425525,'93cdaccd2cd5cb969a9d4bc78187b25b62fd0f9b05924f2c2bd0ad26ed73d255'))
    def test_start(self):m.start(self.base())
    def test_exact_route(self):self.assertEqual(m.ROUTE,self.prep()['route']);self.assertEqual((len(m.ROUTE),m.ROUTE[-1]),(10,[8,8]))
    def test_direction_budget(self):self.assertEqual([m.direction(a,b)for a,b in zip(m.ROUTE,m.ROUTE[1:])],[32]*6+[128]*3)
    def test_warp_owner(self):self.assertEqual(self.prep()['warp_owner']['source'],dict(id=5,xy=[8,8],elevation=3,target_warp=0,target_map=[6,1]));self.assertEqual(self.prep()['warp_owner']['target']['xy'],[11,8])
    def test_no_interaction(self):self.assertIsNone(self.prep()['interaction'])
    def test_removed_objects(self):self.assertEqual(self.prep()['initial_expanded_flags'],{str(f):0 for f in range(4372,4379)})
    def test_terrain(self):self.assertEqual(self.prep()['terrain'][9],dict(map=[6,0],xy=[8,8],elevation=3,collision=0,behavior=108))
    def test_static_not_accepted(self):self.assertFalse(self.prep()['route_native_accepted']);self.assertFalse(self.prep()['museum_second_floor_accepted'])
    def test_consumer_separate(self):p=self.prep();self.assertEqual((p['consumer']['map'],p['consumer_local_id']),([6,1],2));self.assertFalse(p['paper_delivered']);self.assertTrue(p['required_badge_present'])
    def fake(self,arrival=None,mode=None):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1;ix=min(s.index,9)
                xy=m.ROUTE[ix];where=m.ORIGIN;lock=0;cb=m.m.FIELD
                if s.index>=9:
                    xy=arrival or [11,7];where=m.DESTINATION
                    if mode=='transition'and s.index==9:xy=[8,8];where=m.ORIGIN;lock=1
                    if mode=='need_exit_press'and s.index==9:xy=[8,8];where=m.ORIGIN
                if mode=='blocked':xy=[14,5];where=m.ORIGIN
                if mode=='event'and s.index==1:lock=1
                if mode=='battle'and s.index==1:cb=m.m.BATTLE
                if mode=='early_warp'and s.index==1:xy=[11,7];where=m.DESTINATION
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],map=where,lock=lock,callback2=cb);s.observations.append(s.last);return s.last
        return Walking()
    def test_first_exit_stops(self):
        s=self.fake();route,b,f,w=m.progress(s,{})
        self.assertEqual((b,w,f['kind'],f['map'],f['xy']),(None,[],'new_museum_second_floor',[6,1],[11,7]));self.assertEqual(len(s.inputs),18);self.assertEqual(route,m.ROUTE[:-1])
    def test_no_guessed_autostep(self):s=self.fake([11,8]);self.assertEqual(m.progress(s,{})[2]['xy'],[11,8]);self.assertEqual(len(s.inputs),18)
    def test_transition_only_wait(self):s=self.fake(mode='transition');m.progress(s,{});self.assertEqual(s.inputs[-1],(0,180));self.assertEqual(len(s.inputs),19)
    def test_directional_stair_east_input(self):s=self.fake(mode='need_exit_press');m.progress(s,{});self.assertEqual(s.inputs[-2:],[(16,8),(0,180)]);self.assertEqual(len(s.inputs),20)
    def test_blocked_edge_stops(self):s=self.fake(mode='blocked');self.assertEqual(m.progress(s,{})[2]['kind'],'unpassed_edge');self.assertEqual(len(s.inputs),6)
    def test_no_A_before_save(self):s=self.fake();m.progress(s,{});self.assertTrue(all(k in(0,16,32,64,128)for k,_ in s.inputs))
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
for name,key,value in [('counter','save_counter',89),('map','map',[10,16]),('xy','xy',[6,7]),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('party','party_sha256','0'*64),('rp','rp',1),('count','party_count',3),('lock','lock',1),('face','facing',1),('callback','callback2',m.m.BATTLE),('live','live_xy',[9,11])]:setattr(Controller,'test_reject_'+name,negative(key,value))
class StaticPreparation(unittest.TestCase):
    def test_exact_parent_route(self):
        raw=(ROOT/'content/modernization/pr16_story_save93_next_route.json').read_bytes();p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(p['parent_route_binding'],m.identity(raw));self.assertEqual(len(raw),11998);self.assertNotEqual(p['parent_route_binding'],m.identity(raw+b'\n'))
    def test_no_story_claim(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertFalse(p['letter_handoff_accepted']);self.assertFalse(p['paper_delivered']);self.assertEqual(p['consumer']['map'],[6,1])
    def test_static_bindings_and_unique_warp(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(len(p['bindings']),33);self.assertEqual([r['xy']for r in p['terrain']if r['collision']!=0],[])
    def test_arrival_neighbor_allowlist(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(p['arrival_candidates'],[[11,8],[11,7],[11,9],[12,8]])
        for xy in p['arrival_candidates']:self.assertTrue(any(r['map']==[6,1]and r['xy']==xy and r['collision']==0 for r in p['terrain']))
    def test_no_extra_movement_on_east_autostep(self):
        s=Controller().fake([12,8]);self.assertEqual(m.progress(s,{})[2]['xy'],[12,8]);self.assertEqual(len(s.inputs),18)
    def test_admission_already_paid(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual((p['admission_variable'],p['admission_value']),(0x4061,1));self.assertTrue(p['museum_admission_paid']);self.assertEqual([(r['xy'],r['variable'],r['value'])for r in p['admission_coords']],[([x,5],0x4061,0)for x in [12,13,14]])
    def test_directional_stair_kind(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(p['terrain'][9]['behavior'],0x6c);self.assertEqual(p['warp_activation']['button'],16);self.assertEqual(p['warp_activation']['direction'],4)
    def test_directional_stair_reject_off_warp(self):
        s=Controller().fake(mode='need_exit_press');step=s.step
        def bad(*keys):
            o=step(*keys)
            if len(s.observations)==10:o['xy']=[8,9];o['live_xy']=[15,16]
            return o
        s.step=bad
        with self.assertRaises(ValueError):m.progress(s,{})
        self.assertEqual(len(s.inputs),18)
if __name__=='__main__':unittest.main()



