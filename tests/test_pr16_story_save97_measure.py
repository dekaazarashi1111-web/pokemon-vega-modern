"""Save96から未通過の博物館退出12歩/町field停止だけを検査。"""
import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save97_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[6,0],xy=[8,8],live_xy=[15,15],facing=3,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=96,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11299780050,'1f1d30d7f8261ff8b03f0bf290aaa61d052709b6a0a1c259da13f16895cd4b81'))
    def test_start(self):m.start(self.base())
    def test_exact_route(self):self.assertEqual(m.ROUTE,self.prep()['route']);self.assertEqual((len(m.ROUTE),m.ROUTE[0],m.ROUTE[-1]),(13,[8,8],[13,9]))
    def test_direction_budget(self):self.assertEqual([m.direction(a,b)for a,b in zip(m.ROUTE,m.ROUTE[1:])],[64,64,64,16,16,16,16,16,128,128,128,128])
    def test_warp_owner(self):self.assertEqual(self.prep()['warp_owner']['source'],dict(id=0,xy=[13,9],elevation=3,target_warp=0,target_map=[3,2]));self.assertEqual(self.prep()['warp_owner']['target']['xy'],[19,25])
    def test_no_interaction(self):self.assertIsNone(self.prep()['interaction'])
    def test_removed_objects(self):self.assertEqual(self.prep()['initial_expanded_flags'],{str(f):0 for f in range(4372,4379)})
    def test_exit_terrain(self):self.assertEqual(self.prep()['terrain'][12],dict(map=[6,0],xy=[13,9],elevation=3,collision=0,behavior=8))
    def test_static_not_accepted(self):self.assertFalse(self.prep()['route_native_accepted']);self.assertFalse(self.prep()['museum_exit_accepted'])
    def test_letter_already_delivered(self):p=self.prep();self.assertTrue(p['paper_delivered']);self.assertEqual(p['paper_quantity'],0);self.assertFalse(p['completion_flag4380'])
    def test_admission_already_paid(self):p=self.prep();self.assertEqual((p['admission_variable'],p['admission_value'],p['money']),(0x4061,1,23114))
    def test_admission_coords_nontrigger(self):self.assertEqual([(c['xy'],c['variable'],c['value'])for c in self.prep()['admission_coords']], [([x,5],0x4061,0)for x in(12,13,14)])
    def test_pp_unchanged(self):self.assertEqual(m.PP,[3,9,8,2])
    def fake(self,arrival=None,mode=None):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1;ix=min(s.index,12)
                xy=m.ROUTE[ix];where=m.ORIGIN;lock=0;cb=m.m.FIELD
                if s.index>=12:
                    xy=arrival or [19,26];where=m.DESTINATION
                    if mode=='transition'and s.index==12:xy=[13,9];where=m.ORIGIN;lock=1
                    if mode=='need_south_press'and s.index==12:xy=[13,9];where=m.ORIGIN
                    if mode=='forever':xy=[13,9];where=m.ORIGIN;lock=1
                if mode=='blocked':xy=[8,8];where=m.ORIGIN
                if mode=='event'and s.index==1:lock=1
                if mode=='battle'and s.index==1:cb=m.m.BATTLE
                if mode=='early_warp'and s.index==1:xy=[19,26];where=m.DESTINATION
                if mode=='npc_on_paid_coord'and s.index==7:lock=1
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],map=where,lock=lock,callback2=cb);s.observations.append(s.last);return s.last
        return Walking()
    def test_first_town_field_stops(self):
        s=self.fake();route,b,f,w=m.progress(s,{})
        self.assertEqual((b,w,f['kind'],f['map'],f['xy']),(None,[],'new_museum_exit',[3,2],[19,26]));self.assertEqual(len(s.inputs),24);self.assertEqual(route,m.ROUTE[:-1])
    def test_no_guessed_autostep(self):s=self.fake([19,25]);self.assertEqual(m.progress(s,{})[2]['xy'],[19,25]);self.assertEqual(len(s.inputs),24)
    def test_transition_only_wait(self):s=self.fake(mode='transition');m.progress(s,{});self.assertEqual(s.inputs[-1],(0,180));self.assertEqual(len(s.inputs),25)
    def test_exit_south_input(self):s=self.fake(mode='need_south_press');m.progress(s,{});self.assertEqual(s.inputs[-2:],[(128,8),(0,180)]);self.assertEqual(len(s.inputs),26)
    def test_blocked_edge_stops(self):s=self.fake(mode='blocked');self.assertEqual(m.progress(s,{})[2]['kind'],'unpassed_edge');self.assertEqual(len(s.inputs),6)
    def test_no_A_before_save(self):s=self.fake();m.progress(s,{});self.assertTrue(all(k in(0,16,32,64,128)for k,_ in s.inputs))
    def test_event_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(mode='event'),{})
    def test_paid_coord_event_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(mode='npc_on_paid_coord'),{})
    def test_battle_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(mode='battle'),{})
    def test_early_warp_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(mode='early_warp'),{})
    def test_wrong_arrival_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake([20,26]),{})
    def test_finite_wait_limit(self):
        s=self.fake(mode='forever')
        with self.assertRaises(ValueError):m.progress(s,{})
        self.assertEqual(len(s.inputs),32)
    def test_exit_reject_off_warp(self):
        s=self.fake(mode='need_south_press');step=s.step
        def bad(*keys):
            o=step(*keys)
            if len(s.observations)==13:o['xy']=[13,8];o['live_xy']=[20,15]
            return o
        s.step=bad
        with self.assertRaises(ValueError):m.progress(s,{})
        self.assertEqual(len(s.inputs),24)
    def test_party_changed_before_exit_rejected(self):
        o=self.base();o['party_sha256']='0'*64
        with self.assertRaises(ValueError):m.scope(o)
    def test_flash_changed_before_save_rejected(self):
        o=self.base();o['flash_sha256']='0'*64
        with self.assertRaises(ValueError):m.scope(o)
    def test_battle_flag_rejected(self):
        o=self.base();o['battle_flags']=8
        with self.assertRaises(ValueError):m.scope(o)
    def test_history_import_limit_preserved(self):self.assertGreaterEqual(sys.getrecursionlimit(),1500)
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('counter','save_counter',95),('map','map',[6,1]),('xy','xy',[11,8]),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('party','party_sha256','0'*64),('rp','rp',1),('count','party_count',3),('lock','lock',1),('face','facing',4),('callback','callback2',m.m.BATTLE),('live','live_xy',[9,11])]:setattr(Controller,'test_reject_'+name,negative(key,value))
class StaticPreparation(unittest.TestCase):
    def test_exact_parent_route(self):
        raw=(ROOT/'content/modernization/pr16_story_save96_next_route.json').read_bytes();p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(p['parent_route_binding'],m.identity(raw));self.assertEqual(len(raw),21068);self.assertNotEqual(p['parent_route_binding'],m.identity(raw+b'\n'))
    def test_static_bindings_and_unique_warp(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(len(p['bindings']),45);self.assertEqual([r['xy']for r in p['terrain']if r['map']==[6,0]and r['collision']!=0],[])
    def test_arrival_neighbor_allowlist(self):
        p=json.loads((ROOT/m.PREP).read_bytes());self.assertEqual(p['arrival_candidates'],[[19,25],[19,26]]);self.assertEqual(p['terrain'][13]['collision'],1);self.assertEqual(p['terrain'][14]['collision'],0)
    def test_no_stair_activation(self):self.assertNotIn('warp_activation',self.prep() if hasattr(self,'prep')else json.loads((ROOT/m.PREP).read_bytes()))
if __name__=='__main__':unittest.main()
