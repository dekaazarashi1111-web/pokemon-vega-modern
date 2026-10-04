"""Save94からlocal2へ新13歩・通常紙引渡しだけのcontroller。"""
import json,pathlib,sys,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save95_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[6,1],xy=[11,8],live_xy=[18,15],facing=4,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=94,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_bytes())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11298740300,'a306d040197e63d32a3a3d3380041af66c05ec17b8dbe52225320dad4046bb4f'))
    def test_start(self):m.start(self.base())
    def test_route(self):self.assertEqual(m.ROUTE,self.prep()['route']);self.assertEqual((len(m.ROUTE),m.ROUTE[-1]),(14,[4,8]))
    def test_direction_budget(self):self.assertEqual([m.direction(a,b)for a,b in zip(m.ROUTE,m.ROUTE[1:])],[64]*3+[32]*5+[128]*2+[32]*2+[128])
    def test_no_stairs_replay(self):self.assertEqual((m.ORIGIN,m.DESTINATION),([6,1],[6,1]));self.assertEqual(sum(x['behavior']!=8 for x in self.prep()['terrain'][1:]),0)
    def test_exact_parent_bytes(self):raw=(ROOT/'content/modernization/pr16_story_save94_next_route.json').read_bytes();self.assertEqual(self.prep()['parent_route_binding'],m.identity(raw));self.assertEqual(len(raw),25132)
    def test_full_bindings(self):self.assertEqual(len(self.prep()['bindings']),73)
    def test_consumer(self):p=self.prep();self.assertEqual((p['consumer_local_id'],p['consumer_root'],p['consumer_xy']),(2,149013250,[4,9]));self.assertEqual(p['interaction'],dict(xy=[4,8],facing=1,button=1))
    def test_script_no_choice(self):p=self.prep();self.assertEqual({x['hex']for x in p['letter_owner']['instructions']if x['opcode']==9},{'0902'})
    def test_exact_consume(self):p=self.prep();self.assertEqual(p['script_boundaries'],dict(remove_item=dict(address=149013345,item=274,quantity=1),set_flag=dict(address=149013350,flag=4382),national_dex_unlock_present=False))
    def test_no_early_acceptance(self):p=self.prep();self.assertFalse(p['route_native_accepted']);self.assertFalse(p['letter_handoff_accepted']);self.assertFalse(p['paper_delivered'])
    def test_paid_badge_and_paper(self):p=self.prep();self.assertEqual((p['admission_variable'],p['admission_value'],p['money'],p['required_badge_flag'],p['paper_obtain_flag']),(0x4061,1,23114,2083,4383))
    def fake(self,mode=None,pages=3):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0;s.pages=0
            def step(s,*keys):
                s.inputs.extend(keys);key=keys[0][0];o=dict(s.last)
                if key in(16,32,64,128):
                    s.index+=1;xy=m.ROUTE[min(s.index,13)]
                    if mode=='blocked':xy=m.START
                    o.update(xy=xy,live_xy=[v+7 for v in xy],facing={16:4,32:3,64:2,128:1}[key])
                    if mode=='event'and s.index==1:o['lock']=1
                    if mode=='battle'and s.index==1:o['callback2']=m.m.BATTLE
                    if mode=='warp'and s.index==1:o['map']=[6,0]
                elif key==1:
                    s.pages+=1;o['lock']=int(s.pages<=pages)
                    if mode=='wrong_face':o['facing']=4
                    if mode=='party_change':o['party_sha256']='0'*64
                    if mode=='flash_change':o['flash_sha256']='0'*64
                    if mode=='callback_change':o['callback2']=m.TRANSITION
                s.last=o;s.observations.append(o);return o
        return Walking()
    def run_fake(self,s):
        with patch.object(m.m,'screen',return_value=b'P6\n240 160\n255\n'),patch.object(m,'npc_in_front',return_value=True):return m.progress(s,{})
    def test_npc_visual_first_event_stops(self):
        s=self.fake();route,b,f,w=self.run_fake(s);self.assertEqual((route,b,w,f['kind'],f['xy'],f['facing']),(m.ROUTE,None,[],'new_letter_handoff_event',[4,8],1));self.assertEqual(len(s.inputs),35);self.assertEqual(s.pages,4)
    def test_npc_visual_dialogue_observations(self):s=self.fake();f=self.run_fake(s)[2];self.assertEqual(f['dialogue_observations'],[15,16,17]);self.assertEqual(f['observation'],18)
    def test_blocked_no_save_or_A(self):s=self.fake('blocked');self.assertEqual(self.run_fake(s)[2]['kind'],'unpassed_edge');self.assertEqual(s.inputs,[(64,8),(0,48)]*3)
    def test_no_A_during_route(self):s=self.fake();self.run_fake(s);self.assertTrue(all(k in(0,16,32,64,128)for k,_ in s.inputs[:26]))
    def test_dialogue_budget(self):
        s=self.fake(pages=100)
        with self.assertRaises(ValueError):self.run_fake(s)
        self.assertEqual(s.pages,41)
    def test_missing_first_dialogue(self):
        with self.assertRaises(ValueError):self.run_fake(self.fake(pages=0))
    def test_reject_bad_screen(self):
        with patch.object(m.m,'screen',return_value=b'bad'):
            with self.assertRaises(ValueError):m.progress(self.fake(),{})
    def test_pp_preserved(self):self.assertEqual(m.PP,[3,9,8,2])
    def visual_ppm(self,mirror=False):
        raw=bytearray(b'P6\n240 160\n255\n'+b'\x00'*(240*160*3));v=json.loads((ROOT/m.NPC_VISUAL).read_bytes())
        for x,y,rgb in v['sparse_pixels']:
            at=15+3*((80+y)*240+112+(15-x if mirror else x));raw[at:at+3]=bytes(rgb)
        return bytes(raw)
    def test_npc_visual_direct(self):self.assertTrue(m.npc_in_front(self.visual_ppm()))
    def test_npc_visual_mirrored(self):self.assertTrue(m.npc_in_front(self.visual_ppm(True)))
    def test_npc_visual_empty_rejected(self):self.assertFalse(m.npc_in_front(b'P6\n240 160\n255\n'+b'\x00'*(240*160*3)))
    def test_npc_visual_pixel_mutation(self):
        raw=bytearray(self.visual_ppm());x,y,_=json.loads((ROOT/m.NPC_VISUAL).read_bytes())['sparse_pixels'][0];at=15+3*((80+y)*240+112+x);raw[at]^=1;self.assertFalse(m.npc_in_front(bytes(raw)))
    def test_npc_visual_wait_stable_twice(self):
        s=self.fake();s.last.update(xy=[4,8],live_xy=[11,15],facing=1)
        with patch.object(m.m,'screen',return_value=b''),patch.object(m,'npc_in_front',side_effect=[False,True,False,True,True]):waits=m.wait_for_npc(s)
        self.assertEqual(waits,[0,1,2,3]);self.assertEqual(s.inputs,[(0,30)]*4)
    def test_npc_visual_timeout_no_A(self):
        s=self.fake();s.last.update(xy=[4,8],live_xy=[11,15],facing=1)
        with patch.object(m.m,'screen',return_value=b''),patch.object(m,'npc_in_front',return_value=False):
            with self.assertRaises(ValueError):m.wait_for_npc(s)
        self.assertEqual(s.inputs,[(0,30)]*240)
    def test_npc_visual_rom_movement(self):
        p=self.prep();row=next(x for x in p['bindings']if x['address']==0x837df04);obj=bytes.fromhex(row['hex'])[24:48];self.assertEqual((obj[0],obj[9],obj[10]),(2,5,0x21))

def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('counter','save_counter',93),('map','map',[6,0]),('xy','xy',[4,8]),('ledger','ledger_sha256','0'*64),('flash','flash_sha256','0'*64),('party','party_sha256','0'*64),('rp','rp',1),('count','party_count',3),('lock','lock',1),('face','facing',1),('callback','callback2',m.m.BATTLE),('live','live_xy',[9,11])]:setattr(Controller,'test_start_reject_'+name,negative(key,value))
def mode_negative(mode):
    def test(self):
        with self.assertRaises(ValueError):self.run_fake(self.fake(mode))
    return test
for mode in ['event','battle','warp','wrong_face','party_change','flash_change','callback_change']:setattr(Controller,'test_progress_reject_'+mode,mode_negative(mode))
if __name__=='__main__':unittest.main()
