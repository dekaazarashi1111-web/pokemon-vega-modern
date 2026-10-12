"""Save64西隣NPCへA1回だけ、初会話/戦闘/無応答の境界を検証。"""
import json,pathlib,sys,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_save65_measure as m
class Controller(unittest.TestCase):
    def base(self):return dict(map=[1,60],xy=[26,6],live_xy=[33,13],facing=3,callback2=m.m.FIELD,lock=0,party_count=4,rp=0,save_counter=64,battle_flags=0,battle_outcome=0,party_sha256=m.a.PARTY,flash_sha256=m.a.FLASH,ledger_sha256=m.a.COLD_LEDGER)
    def test_parent(self):self.assertEqual((m.a.ARTIFACT,m.a.OUTPUT['sha256']),(11286858775,'7cab241382223fc8ddbd2d659f8c29619c5b9b0ff5fd6d24e9269b4f366833d0'))
    def test_start(self):m.start(self.base())
    def test_no_replayed_path(self):self.assertEqual(m.ROUTE,[[26,6]])
    def test_neighbor_owner(self):self.assertEqual(m.a.next_neighbor()['trainer_id'],155)
    def test_neighbor_scope(self):self.assertFalse(m.a.next_neighbor()['runtime_identity_resolved'])
    def test_real_pp(self):self.assertEqual(m.PP,[15,10,15,5]);self.assertEqual(m.select([0,0,0,5]),0)
    def test_exhaustion(self):
        with self.assertRaises(ValueError):m.select(m.PP)
    def test_no_nonadjacent_input(self):
        with self.assertRaises(ValueError):m.direction([26,6],[23,11])
    def test_transition_wait_only(self):self.assertEqual(m.event_input(dict(callback2=m.TRANSITION,lock=1)),((0,60),))
    def test_no_unlocked_unknown_callback(self):
        with self.assertRaises(ValueError):m.event_input(dict(callback2=0x08000201,lock=0))
    def test_move_target_separation(self):
        b=m.MoveBudget();b.selected(3,True);self.assertEqual(b.commands,[0,0,0,1]);self.assertEqual(b.target(3),3);self.assertEqual(b.targets,1)
    def session(self,**changes):
        class S:
            def __init__(s,o):s.last=o;s.observations=[o];s.inputs=[]
            def step(s,*keys):s.inputs.extend(keys);s.last=dict(s.last,**changes);s.observations.append(s.last);return s.last
        return S(self.base())
    def test_no_response_only_one_a(self):
        s=self.session();route,battle,f,_=m.progress(s,{})
        self.assertEqual((route,battle,f['kind'],f['ordinary_a_inputs']),([[26,6]],None,'adjacent_no_response',1));self.assertEqual(s.inputs,[(1,2),(0,60)])
    def test_dialogue_handed_to_event_once(self):
        s=self.session(lock=1)
        with patch.object(m,'event',return_value='new-event')as e:self.assertEqual(m.progress(s,{}),'new-event');e.assert_called_once_with(s,[[26,6]],[25,6])
        self.assertEqual(s.inputs,[(1,2),(0,60)])
    def test_unexpected_move_stops(self):
        with self.assertRaises(ValueError):m.progress(self.session(xy=[25,6]),{})
    def test_unexpected_map_stops(self):
        with self.assertRaises(ValueError):m.progress(self.session(map=[1,59]),{})
def negative(key,value):
    def test(self):
        o=self.base();o[key]=value
        with self.assertRaises(ValueError):m.start(o)
    return test
for name,key,value in [('old_counter','save_counter',63),('other_map','map',[1,59]),('old_xy','xy',[32,10]),('old_ledger','ledger_sha256','0'*64),('bad_flash','flash_sha256','0'*64),('bad_party','party_sha256','0'*64),('rp','rp',1),('party_count','party_count',3),('lock','lock',1),('facing','facing',4),('callback','callback2',m.m.BATTLE),('live','live_xy',[39,17])]:setattr(Controller,'test_reject_'+name,negative(key,value))
if __name__=='__main__':unittest.main()
