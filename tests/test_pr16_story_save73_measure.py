"""Save72の像を初めて調べる限定controller。旧route/nativeは再走しない。"""
import json,pathlib,sys,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save73_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[1,60],xy=[16,27],live_xy=[23,34],facing=3,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=72,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11289800679,'851c87f8a8006eaecdcb6ea28ee9f097fbcab4ba0c7f5b626afb6edbec40fa49'))
    def test_start(self):m.start(self.base())
    def test_static_interaction(self):
        p=m.a.next_route();self.assertEqual((m.ROUTE,p['script'],p['turn_key'],p['target_facing'],p['interact_key']),([[16,27]],149012422,128,1,1))
    def test_item_owner(self):
        p=m.a.next_route();self.assertEqual((p['item_id'],p['item_quantity'],p['expanded_flag']),(274,1,4383))
    def test_no_choice_opcodes(self):
        p=json.loads((ROOT/m.PREP).read_bytes());xs={x['address']:x for x in p['instructions']if x['node']in(149012422,149012442,149012452)}
        self.assertEqual({x['opcode']for x in xs.values()},{2,6,9,15,26,33,41,43,68,70,106,108});self.assertEqual({x['hex']for x in xs.values()if x['opcode']==9},{'0902','0904','0909'})
    def test_pp_preserved(self):self.assertEqual(m.PP,[9,10,15,2])
    def fake(self,change=None,never=False):
        class Event:
            def __init__(s):s.last=self.base();s.observations=[s.last];s.inputs=[]
            def step(s,*keys):
                s.inputs.extend(keys);n=len(s.observations);s.last=dict(s.last,facing=1,lock=int(n>=2 and (never or n<=4)))
                if change and n==change[0]:s.last.update(change[1])
                s.observations.append(s.last);return s.last
        return Event()
    def test_first_event_only(self):
        s=self.fake()
        with patch.object(m.m,'screen',return_value=b'P6\n240 160\n255\n'):
            route,battle,frontier,warps=m.progress(s,{})
        self.assertEqual(route,[[16,27]]);self.assertIsNone(battle);self.assertEqual(warps,[]);self.assertEqual(frontier,dict(kind='new_statue_event',map=[1,60],xy=[16,27],facing=1,dialogue_observations=[2,3,4],observation=5));self.assertEqual(s.inputs,[(128,8),(0,48)]+[(1,2),(0,180)]*4)
    def test_wrong_facing_before_a(self):
        s=self.fake((1,dict(facing=3)))
        with self.assertRaises(ValueError):m.progress(s,{})
        self.assertEqual(s.inputs,[(128,8),(0,48)])
    def test_no_dialogue_is_rejected(self):
        s=self.fake((2,dict(lock=0)))
        with self.assertRaises(ValueError):m.progress(s,{})
        self.assertEqual(len(s.inputs),4)
    def test_unknown_callback_before_a(self):
        s=self.fake((1,dict(callback2=m.m.BATTLE)))
        with self.assertRaises(ValueError):m.progress(s,{})
        self.assertEqual(len(s.inputs),2)
    def test_invalid_screen_no_blind_a(self):
        s=self.fake()
        with patch.object(m.m,'screen',return_value=b'unknown'),self.assertRaises(ValueError):m.progress(s,{})
        self.assertEqual(len(s.inputs),4)
    def test_dialogue_finite(self):
        s=self.fake(never=True)
        with patch.object(m.m,'screen',return_value=b'P6\n240 160\n255\n'),self.assertRaises(ValueError):m.progress(s,{})
        self.assertEqual(len(s.inputs),36)
    def test_event_scope(self):m.event_scope(dict(self.base(),facing=1,lock=1))
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',71),('other_map','map',[1,59]),('old_xy','xy',[23,31]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',1),('callback','callback2',m.m.BATTLE),('live','live_xy',[30,38])]:setattr(Controller,'test_reject_'+name,negative(key,value))
def event_negative(key,value):
    def test(self):
        o=dict(self.base(),facing=1,lock=1);o[key]=value
        with self.assertRaises(ValueError):m.event_scope(o)
    return test
for name,key,value in [('new_map','map',[1,59]),('new_xy','xy',[16,28]),('battle','battle_flags',1),('outcome','battle_outcome',1),('autosave','save_counter',73),('party','party_sha256','0'*64),('flash','flash_sha256','0'*64)]:setattr(Controller,'test_event_reject_'+name,event_negative(key,value))
if __name__=='__main__':unittest.main()
