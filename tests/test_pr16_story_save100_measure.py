"""Save100の動的実画面/接近/会話だけを対象にした新規controller検査。"""
import json,pathlib,sys,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save100_measure as m
class Controller(unittest.TestCase):
    def prep(self):return json.loads((ROOT/m.PREP).read_bytes())
    def base(self):return dict(map=[3,23],xy=[18,28],live_xy=[25,35],facing=3,callback2=m.m.FIELD,field=True,lock=0,party_count=4,rp=0,save_counter=99,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def pixels(self,player=[18,28],npc=[20,28],index=0,dx=0,dy=0,empty=False):
        cal=self.prep()['visual_locator'];data=bytearray(240*160*3);left=114+16*(npc[0]-player[0])+dx;top=68+16*(npc[1]-player[1])+dy
        if not empty:
            for x,y in cal['templates'][index]['mask']:
                i=((top+y)*240+left+x)*3;data[i:i+3]=bytes(cal['colors'][0])
        return b'P6\n240 160\n255\n'+bytes(data)
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11301562515,'18de364bd911a9470965cf571e10aab899e8f4236bcaef327586e965b3a02b6b'))
    def test_parent_binding_exact(self):self.assertEqual(self.prep()['parent_route_binding'],m.identity((ROOT/'content/modernization/pr16_story_save99_next_route.json').read_bytes()))
    def test_start(self):m.start(self.base())
    def test_field_destination(self):m.idle(dict(self.base(),map=[3,2]),99)
    def test_no_healing_assumption(self):self.assertFalse(self.prep()['script_effects_static_only']['healing_branch_taken'])
    def test_town_auto(self):p=self.prep();self.assertEqual(p['town_event_owner']['map_script_refs'][0]['operand'],2);self.assertEqual(p['script_effects_static_only']['var4072_after_town'],3)
    def test_safe_terrain(self):p=self.prep();self.assertEqual(len(p['terrain']),28);self.assertTrue(all(x['behavior']in(0,33)and x['collision']==0 and x['elevation']==3 for x in p['terrain']))
    def test_no_sign_or_grass(self):ps=[x['xy']for x in self.prep()['terrain']];self.assertNotIn([17,27],ps);self.assertNotIn([21,25],ps)
    def test_three_real_mask_anchors(self):p=self.prep()['visual_locator'];self.assertEqual(len(p['templates']),3);self.assertEqual([x['parent_artifact']for x in p['templates']],[11301562515]*3)
    def test_locate_directions(self):
        for index in range(3):self.assertEqual(m.locate(self.pixels(index=index),[18,28],self.prep()['visual_locator'])['xy'],[20,28])
    def test_locate_y(self):self.assertEqual(m.locate(self.pixels(npc=[20,29]),[18,28],self.prep()['visual_locator'])['xy'],[20,29])
    def test_locate_camera_shift(self):self.assertEqual(m.locate(self.pixels(player=[19,29],npc=[18,27]),[19,29],self.prep()['visual_locator'])['xy'],[18,27])
    def test_unaligned_x_wait(self):self.assertIsNone(m.locate(self.pixels(dx=1),[18,28],self.prep()['visual_locator']))
    def test_unaligned_y_wait(self):self.assertIsNone(m.locate(self.pixels(dy=1),[18,28],self.prep()['visual_locator']))
    def test_missing_wait(self):self.assertIsNone(m.locate(self.pixels(empty=True),[18,28],self.prep()['visual_locator']))
    def test_other_purple_rejected(self):
        with self.assertRaises(ValueError):m.locate(self.pixels(npc=[21,28]),[18,28],self.prep()['visual_locator'])
    def test_dimensions(self):
        with self.assertRaises(ValueError):m.locate(b'P6\n1 1\n255\n000',[18,28],self.prep()['visual_locator'])
    def test_shortest_step(self):self.assertEqual(m.next_tile([18,28],[20,28],[x['xy']for x in self.prep()['terrain']]),[19,28])
    def test_adjacent_no_step(self):self.assertIsNone(m.next_tile([19,28],[20,28],[x['xy']for x in self.prep()['terrain']]))
    def test_unreachable(self):
        with self.assertRaises(ValueError):m.next_tile([18,28],[20,28],[[18,28]])
    def fake(self,mode=None):
        class Fake:
            def __init__(s):s.last=self.base();s.observations=[dict(s.last)];s.inputs=[];s.npc=[20,28];s.locked=False;s.calls=0
            def step(s,*keys):
                s.inputs.extend(keys);s.calls+=1;o=dict(s.last);key=keys[0][0]
                if key in m.FACING:
                    face=m.FACING[key]
                    if o['facing']==face:
                        dx,dy={16:(1,0),32:(-1,0),64:(0,-1),128:(0,1)}[key];target=[o['xy'][0]+dx,o['xy'][1]+dy]
                        if target!=s.npc:o['xy']=target
                    o['facing']=face
                elif key==1:
                    if not s.locked:o['lock']=1;s.locked=True
                    else:o.update(map=[3,2],xy=[5,16],facing=3,lock=0)
                if mode=='moving'and s.calls==1:s.npc=[20,29]
                o['live_xy']=[v+7 for v in o['xy']];s.last=o;s.observations.append(dict(o));return o
        return Fake()
    def run_fake(self,mode=None):
        s=self.fake(mode)
        with patch.object(m.m,'screen',side_effect=lambda s:self.pixels(player=s.last['xy'],npc=s.npc,empty=mode=='missing')):
            result=m.progress(s,self.prep())
        return s,result
    def test_dynamic_front_then_town(self):
        s,(route,episode,f,warps)=self.run_fake();self.assertEqual(route,[[18,28],[19,28]]);self.assertEqual(f['kind'],'ranger_town_chain_first_field');self.assertEqual(f['talk_attempts'][0]['ranger'],[20,28]);self.assertEqual(f['talk_attempts'][0]['facing'],4);self.assertTrue(f['talk_attempts'][0]['consecutive_position_confirmed']);self.assertIsNone(episode)
    def test_moving_npc_replanned(self):
        s,(_,_,f,_)=self.run_fake('moving');self.assertEqual(f['talk_attempts'][0]['ranger'],[20,29]);self.assertLess(f['approach_steps'],30)
    def test_missing_never_A(self):
        s=self.fake()
        with patch.object(m.m,'screen',side_effect=lambda s:self.pixels(empty=True)):
            with self.assertRaises(ValueError):m.progress(s,self.prep())
        self.assertEqual(s.inputs,[(0,4)]*160)
    def test_first_town_field_stops(self):s,(_,_,f,_)=self.run_fake();self.assertEqual(len(s.observations)-1,f['observation']);self.assertEqual(s.last['save_counter'],99)
    def test_import_bound(self):self.assertGreaterEqual(sys.getrecursionlimit(),1500)
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('counter','save_counter',98),('map','map',[3,2]),('xy','xy',[18,27]),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('party','party_sha256','0'*64),('rp','rp',1),('count','party_count',3),('lock','lock',1),('face','facing',4),('callback','callback2',m.m.BATTLE),('live','live_xy',[18,28]),('outcome','battle_outcome',1),('trainer','battle_flags',8)]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
