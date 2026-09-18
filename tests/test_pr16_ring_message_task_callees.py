"""新規七calleeの保存出自/範囲/過大主張を検査。旧契約は実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_task_callees as m


class PlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.context=m.saved_inputs()

    def test_roots_and_budgets(self):
        p=m.plan(self.context)
        self.assertEqual(len(p['roots']),7)
        self.assertEqual(p['max_nodes'],1024)
        self.assertEqual(p['max_bytes'],4096)

    def test_saved_bl_bindings(self):
        self.assertEqual([(r['site'],r['target']) for r in m.plan(self.context)['saved_callsite_bindings']],list(m.CALLS))

    def test_no_runtime_or_recursive_claim(self):
        p=m.plan(self.context)
        for k in ('expand_direct_calls','redecode_saved_nodes','normal_story_observed'):self.assertIs(p[k],False)

    def mutate_summary(self,key,value):
        c=copy.deepcopy(self.context);c['task_frontier'][key]=value
        with self.assertRaises(ValueError):m.plan(c)

    def test_candidate(self):self.mutate_summary('candidate',{})
    def test_node_count(self):self.mutate_summary('new_node_count',63)
    def test_byte_count(self):self.mutate_summary('new_window_bytes',153)
    def test_root_set(self):self.mutate_summary('pending_direct_callees',list(m.ROOTS)[1:])
    def test_new_continuation(self):self.mutate_summary('pending_continuations',[m.ROOTS[0]])

    def test_proof_promotion(self):
        for k in ('task_state_transitions_proven','task_runtime_observed','initializer_runtime_observed',
                  'actual_callback_table_observed','ring_acquisition_accepted','release_ready'):
            with self.subTest(key=k):self.mutate_summary(k,True)

    def test_duplicate_node(self):
        c=copy.deepcopy(self.context);c['nodes'].append(c['nodes'][0])
        with self.assertRaises(ValueError):m.plan(c)

    def test_changed_callee(self):
        for p,t in m.CALLS:
            with self.subTest(site=p):
                c=copy.deepcopy(self.context);next(n for n in c['nodes'] if n['address']==p)['target']=t+1
                with self.assertRaises(ValueError):m.plan(c)

    def test_changed_call_kind(self):
        c=copy.deepcopy(self.context);next(n for n in c['nodes'] if n['address']==m.CALLS[0][0])['kind']='ordinary'
        with self.assertRaises(ValueError):m.plan(c)

    def test_no_resample(self):
        c=copy.deepcopy(self.context);c['nodes'][0]['address']=m.ROOTS[0]&~1
        with self.assertRaises(ValueError):m.plan(c)


class BoundsTests(unittest.TestCase):
    def good(self):
        return dict(initial_roots=list(m.ROOTS),saved_roots_reused=[],saved_nodes_redecoded=0,
            direct_calls_recursively_expanded=0,new_nodes=[dict(address=0x080692f8,size=2,hex='00b5',kind='ordinary')])
    def reject(self,key,value):
        r=self.good();r[key]=value
        with self.assertRaises(ValueError):m.validate_result(r,set())
    def test_valid(self):self.assertEqual(m.validate_result(self.good(),set()),{0x080692f8,0x080692f9})
    def test_root_order(self):self.reject('initial_roots',list(reversed(m.ROOTS)))
    def test_root_missing(self):self.reject('initial_roots',list(m.ROOTS)[1:])
    def test_reused_root(self):self.reject('saved_roots_reused',[m.ROOTS[0]])
    def test_redecode(self):self.reject('saved_nodes_redecoded',1)
    def test_recursion(self):self.reject('direct_calls_recursively_expanded',1)
    def test_no_nodes(self):self.reject('new_nodes',[])
    def test_duplicate(self):self.reject('new_nodes',self.good()['new_nodes']*2)
    def test_budget(self):self.reject('new_nodes',self.good()['new_nodes']*1025)
    def test_overlap(self):
        with self.assertRaises(ValueError):m.validate_result(self.good(),{0x080692f9})
    def test_instruction_boundaries(self):
        for key,value in (('address',0x080692f9),('address',0x0a000000),('size',3),('hex','00'),('kind','unknown')):
            with self.subTest(key=key,value=value):
                r=self.good();r['new_nodes'][0][key]=value
                with self.assertRaises(ValueError):m.validate_result(r,set())
    def test_literal_boundaries(self):
        for p in (0x07000000,0x0a000000,0x08001001):
            with self.subTest(address=p):
                r=self.good();r['new_nodes'][0]['literal_address']=p
                with self.assertRaises(ValueError):m.validate_result(r,set())


if __name__=='__main__':unittest.main()
