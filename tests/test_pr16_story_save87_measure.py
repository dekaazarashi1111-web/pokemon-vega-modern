"""Save86からleader417へ新13歩、原本partyと有限PP方針の専用検査。"""
import json,pathlib,sys,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save87_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[10,16],xy=[6,7],live_xy=[13,14],facing=1,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=86,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def prep(self):return json.loads((ROOT/m.PREP).read_text())
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11294997639,'d1ea60da2a4b4ea00fa6a6d70fde1c9be74b5c92fd90fc780b47737761041715'))
    def test_start(self):m.start(self.base())
    def test_cold0_is_start(self):self.assertEqual(m.a.COLD_LEDGER,'40086ba99a8d004ff07a5c5e800898c46003af5de36a8f922f8051485e701ad1');self.assertEqual(m.a.COLD_LEDGER,m.a.SETTLED_COLD_LEDGER)
    def test_exact_route(self):self.assertEqual(m.ROUTE,self.prep()['route']);self.assertEqual((m.ROUTE[0],m.ROUTE[-1],len(m.ROUTE)),([6,7],[7,3],14))
    def test_thirteen_edges(self):self.assertEqual([m.direction(a,b)for a,b in zip(m.ROUTE,m.ROUTE[1:])],[16]*5+[64]*4+[32]*4)
    def test_owner(self):self.assertEqual(self.prep()['interaction'],{'local_id':7,'target':[6,3],'script':142951392,'visibility_flag':0,'button':'A','from_xy':[7,3],'facing':3,'object_address':155169732,'object_hex':'07530000060003000308110000000000e043850800000000'})
    def test_initial_flags(self):self.assertEqual(self.prep()['initial_flags'],{str(f):int(f in(4373,4377,4378))for f in range(4372,4379)})
    def test_branch_owner(self):self.assertEqual((len(self.prep()['instructions']),len(self.prep()['graph']['nodes'])),(118,17))
    def test_trainer_battle(self):self.assertEqual([(r['value'],r['battle_type'])for r in self.prep()['graph']['references']if r['category']=='trainer'and r['access']=='battle'],[(417,1)])
    def test_badge_source(self):self.assertIn(('setflag',2083),[(r['command'],r['value'])for r in self.prep()['graph']['references']if r['category']=='flag'])
    def test_tm_source(self):self.assertIn(('additem',325),[(r['command'],r['value'])for r in self.prep()['graph']['references']if r['category']=='item'])
    def test_party(self):self.assertEqual([(p['species'],p['level'],p['held_item'])for p in self.prep()['trainer']['party']],[(71,21,139),(48,23,183),(17,24,142)])
    def test_moves(self):self.assertEqual([[m['id']for m in p['moves']]for p in self.prep()['trainer']['party']],[[422,424,157,393],[183,460,9,325],[454,332,370,157]])
    def test_physical_flag(self):self.assertEqual((self.prep()['trainer']['logical_win_flag'],self.prep()['trainer']['physical_win_flag']),(1697,1697));self.assertEqual(self.prep()['trainer']['double_battle'],0)
    def test_pp(self):self.assertEqual(m.PP,[4,10,12,2]);self.assertEqual(m.select([0]*4),0);self.assertEqual(m.select([1,0,0,0]),2);self.assertEqual(m.select([1,0,4,0]),1)
    def test_pp_exhaustion(self):
        with self.assertRaises(ValueError):m.select([1,3,4,0])
    def test_pp_reservation_sequence(self):
        b=m.MoveBudget();slots=[]
        for _ in range(8):slot=b.choose();slots.append(slot);b.selected(slot,False)
        self.assertEqual(slots,[0,2,2,2,2,1,1,1]);self.assertEqual(b.commands,[1,3,4,0])
    def test_double_confirmation_no_extra_reservation(self):
        b=m.MoveBudget();b.selected(0,True);self.assertEqual(b.target(0),0);self.assertEqual((b.commands,b.targets),([1,0,0,0],1))
    def test_no_speculative_double_target(self):
        with self.assertRaises(ValueError):m.MoveBudget().target(0)
    def test_unknown_callback_only_waits(self):self.assertEqual(m.event_input(dict(callback2=0x8123457,lock=1)),((0,60),))
    def test_unlocked_unknown_callback_rejected(self):
        with self.assertRaises(ValueError):m.event_input(dict(callback2=0x8123457,lock=0))
    def fake(self,blocked=False,early=False,no_lock=False):
        class Walking:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[];s.index=0
            def step(s,*keys):
                s.inputs.extend(keys);s.index+=1;key,frames=keys[0];xy=s.last['xy'];facing=s.last['facing'];lock=0
                if key in(16,32,64,128):
                    face={16:4,32:3,64:2,128:1}[key]
                    if face==facing and not blocked:xy=[xy[0]+int(key==16)-int(key==32),xy[1]+int(key==128)-int(key==64)]
                    facing=face
                if key==1:lock=int(not no_lock)
                if early and s.index==1:lock=1
                s.last=dict(s.last,xy=xy,live_xy=[v+7 for v in xy],lock=lock,facing=facing);s.observations.append(s.last);return s.last
        return Walking()
    def finish(self,s,route,trigger):
        s.last=dict(s.last,lock=0,battle_outcome=1,battle_flags=8)
        return route+[s.last['xy']],dict(trainer=True,outcome=1),dict(kind='new_battle',trigger=trigger),[]
    def test_normal_leader_interaction(self):
        s=self.fake()
        with patch.object(m,'event',side_effect=self.finish):route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,w),(m.ROUTE+[[7,3]],dict(trainer=True,outcome=1),[]));self.assertEqual((f['kind'],f['local_id'],f['trigger']),('leader417_victory_event',7,[6,3]));self.assertEqual(s.inputs,[(16,8),(0,48)]*6+[(64,8),(0,48)]*5+[(32,8),(0,48)]*5+[(1,2),(0,60)])
    def test_unpassed_edge_does_not_start_battle(self):
        s=self.fake(blocked=True);route,b,f,w=m.progress(s,{})
        self.assertEqual((route,b,f['kind']),([[6,7]],None,'unpassed_edge'));self.assertEqual(len(s.inputs),6)
    def test_unexpected_event_stops_route(self):
        s=self.fake(early=True)
        with patch.object(m,'event',return_value=('early',None,{},[]))as e:r=m.progress(s,{})
        self.assertEqual(r[0],'early');self.assertEqual(s.index,1);e.assert_called_once()
    def test_no_event_rejected(self):
        with self.assertRaises(ValueError):m.progress(self.fake(no_lock=True),{})
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',85),('outside_map','map',[3,2]),('old_xy','xy',[9,13]),('bad_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',3),('callback','callback2',m.m.BATTLE),('live','live_xy',[9,13])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
