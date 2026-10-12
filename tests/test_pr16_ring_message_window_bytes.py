"""保存calleeとframe literalを固定し採取範囲をfail closedで検査する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_window_bytes as m


class PlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=m.saved_inputs()
    def test_nine_roots(self):self.assertEqual(m.plan(self.c)['roots'],list(m.ROOTS))
    def test_byte_budget(self):self.assertEqual(m.plan(self.c)['max_bytes'],4096)
    def test_frame_binding(self):
        p=m.plan(self.c)['frame_callback'];self.assertEqual(p['pointer'],0x080f8185)
        self.assertFalse(p['callback_execution_proven'])
    def reject(self,key,value):
        c=copy.deepcopy(self.c);c['task_callees'][key]=value
        with self.assertRaises(ValueError):m.plan(c)
    def test_candidate(self):self.reject('candidate',{})
    def test_node_count(self):self.reject('new_node_count',153)
    def test_byte_count(self):self.reject('new_window_bytes',351)
    def test_direct_set(self):self.reject('pending_direct_callees',list(m.DIRECT)[1:])
    def test_continuation(self):self.reject('pending_continuations',[m.FRAME])
    def test_acceptance(self):
        for k in ('task_runtime_observed','normal_story_observed','task_state_transitions_proven',
                  'initializer_runtime_observed','actual_callback_table_observed','ring_acquisition_accepted','release_ready'):
            with self.subTest(key=k):self.reject(k,True)
    def reject_node(self,at,key,value):
        c=copy.deepcopy(self.c);next(n for n in c['nodes'] if n['address']==at)[key]=value
        with self.assertRaises(ValueError):m.plan(c)
    def test_call_target(self):
        for p,t in m.CALLS:
            with self.subTest(site=p):self.reject_node(p,'target',t+1)
    def test_frame_literal(self):self.reject_node(0x080f7f50,'literal_value',m.FRAME+2)
    def test_frame_literal_address(self):self.reject_node(0x080f7f50,'literal_address',0x080f7f74)
    def test_frame_opcode(self):self.reject_node(0x080f7f50,'hex','0049')
    def test_window_id(self):self.reject_node(0x080f7f52,'hex','0020')
    def test_duplicate_node(self):
        c=copy.deepcopy(self.c);c['nodes'].append(c['nodes'][0])
        with self.assertRaises(ValueError):m.plan(c)
    def test_resample(self):self.reject_node(self.c['nodes'][0]['address'],'address',m.FRAME&~1)


class BoundsTests(unittest.TestCase):
    def good(self):return dict(initial_roots=list(m.ROOTS),saved_roots_reused=[],saved_nodes_redecoded=0,
        direct_calls_recursively_expanded=0,new_nodes=[dict(address=0x08002e3c,size=2,hex='00b5')])
    def test_good(self):self.assertEqual(len(m.validate_new(self.good(),set())),2)
    def test_replay(self):
        for key,val in (('initial_roots',[]),('saved_roots_reused',[m.FRAME]),('saved_nodes_redecoded',1),('direct_calls_recursively_expanded',1)):
            with self.subTest(key=key):
                r=self.good();r[key]=val
                with self.assertRaises(ValueError):m.validate_new(r,set())
    def test_empty(self):
        r=self.good();r['new_nodes']=[]
        with self.assertRaises(ValueError):m.validate_new(r,set())
    def test_duplicate(self):
        r=self.good();r['new_nodes']*=2
        with self.assertRaises(ValueError):m.validate_new(r,set())
    def test_overlap(self):
        with self.assertRaises(ValueError):m.validate_new(self.good(),{0x08002e3d})
    def test_invalid_node(self):
        for k,v in (('address',0x0a000000),('address',0x08002e3d),('size',3),('hex','00')):
            with self.subTest(key=k):
                r=self.good();r['new_nodes'][0][k]=v
                with self.assertRaises(ValueError):m.validate_new(r,set())


if __name__=='__main__':unittest.main()
