"""Save81から北2歩だけ。未発火停止・最初の新eventとPP予約を検証。"""
import json,pathlib,sys,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save82_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[10,16],xy=[6,9],live_xy=[13,16],facing=2,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=81,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11293356282,'3beb00ee134983ae76b2e41bdc9d5cdbf76e2d031d3f42d3a07fadb164a07633'))
    def test_start(self):m.start(self.base())
    def test_cold0_is_start(self):self.assertEqual(m.a.COLD_LEDGER,'e9f829d587b02ef89c69b1736e19875c43bf691510ae78054ddb668d18c59ba4');self.assertEqual(m.a.COLD_LEDGER,m.a.SETTLED_COLD_LEDGER)
    def test_exact_route(self):self.assertEqual(m.ROUTE,[[6,9],[6,8],[6,7]]);self.assertEqual(m.ROUTE,self.prep()['route'])
    def test_owner(self):
        o=self.prep()['interaction'];self.assertEqual((o['local_id'],o['target'],o['trainer_id'],o['range'],o['movement_type']),(1,[3,7],132,3,10));self.assertEqual(o['object_hex'],'0138000003000700030a110001000300a4c5360900000000')
    def test_initial_flags(self):self.assertEqual(self.prep()['initial_flags'],{str(f):int(f in(4376,4378))for f in range(4372,4379)})
    def test_branch_owner(self):
        p=self.prep();self.assertEqual(len(p['instructions']),5);self.assertEqual([x['hex']for x in p['instructions']if x['node']==154584484],['5c0084000000384f21085d4f2108','0566601808'])
    def test_texts(self):
        p=self.prep();self.assertEqual(set(p['texts']),{'136400696','136400733','136400761'});self.assertIn('ナギナタ',p['texts']['136400761']['decoded']);self.assertFalse(p['native_route_accepted'])
    def test_same_map(self):self.assertEqual((m.ORIGIN,m.DESTINATION),([10,16],[10,16]))
    def fake(self,event_at=None,stationary=False,jump=False):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1;key,frames=keys[0];xy=s.last['xy'];lock=0
                if key==64 and not stationary:xy=[xy[0],xy[1]-(2 if jump else 1)]
                if s.index==event_at:lock=1
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],lock=lock);s.observations.append(s.last);return s.last
        return Walking()
    def test_unpassed_edge(self):
        s=self.fake(stationary=True);route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,f['kind'],f['attempts'],f['target']),([[6,9]],None,'unpassed_edge',3,[6,8]));self.assertEqual(s.inputs,[(64,8),(0,48)]*3)
    def test_no_sight_stops_exactly(self):
        s=self.fake();route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,w),(m.ROUTE,None,[]));self.assertEqual(f,dict(kind='sight_not_triggered',map=[10,16],xy=[6,7],observation=2));self.assertEqual(s.inputs,[(64,8),(0,48)]*2)
    def test_early_event_stops_route(self):
        s=self.fake(event_at=1)
        with patch.object(m,'event',return_value='FIRST')as e:self.assertEqual(m.progress(s,{}),'FIRST');e.assert_called_once_with(s,[[6,9]],[6,8])
        self.assertEqual(s.inputs,[(64,8),(0,48)])
    def test_sight_event_stops_route(self):
        s=self.fake(event_at=2)
        with patch.object(m,'event',return_value='SECOND')as e:self.assertEqual(m.progress(s,{}),'SECOND');e.assert_called_once_with(s,[[6,9],[6,8]],[6,7])
        self.assertEqual(s.inputs,[(64,8),(0,48)]*2)
    def test_jump_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(jump=True),{})
    def test_pp_unchanged_budget(self):self.assertEqual(m.PP,[9,10,15,2])
    def test_pp_reserve_order(self):
        b=m.MoveBudget();got=[]
        for _ in range(11):slot=b.choose();got.append(slot);b.selected(slot,False)
        self.assertEqual(got,[0]*3+[2]*5+[1]*3)
        with self.assertRaises(ValueError):b.choose()
    def test_aerial_ace_never_reserved(self):self.assertNotIn(3,[m.select(v)for v in ([0,0,0,0],[3,0,0,0],[3,0,5,0])])
    def test_double_target_is_separate(self):
        b=m.MoveBudget();b.selected(0,True);self.assertEqual(b.target(0),0);self.assertEqual((b.commands,b.targets),([1,0,0,0],1))
    def test_wrong_double_target_rejected(self):
        b=m.MoveBudget();b.selected(0,True)
        with self.assertRaises(ValueError):b.target(1)
    def test_all_two_edges_adjacent(self):self.assertEqual([m.direction(a,b)for a,b in zip(m.ROUTE,m.ROUTE[1:])],[64,64])
    def test_diagonal_rejected(self):
        with self.assertRaises(ValueError):m.direction([6,9],[7,8])
    def test_unknown_callback_only_waits(self):self.assertEqual(m.event_input(dict(callback2=0x08012345,lock=1)),((0,60),))
    def test_unknown_unlocked_rejected(self):
        with self.assertRaises(ValueError):m.event_input(dict(callback2=0x08012345,lock=0))
    def test_non_rom_callback_rejected(self):
        with self.assertRaises(ValueError):m.event_input(dict(callback2=0x02000001,lock=1))
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',80),('outside_map','map',[3,2]),('old_xy','xy',[3,9]),('bad_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',1),('callback','callback2',m.m.BATTLE),('live','live_xy',[6,9])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
