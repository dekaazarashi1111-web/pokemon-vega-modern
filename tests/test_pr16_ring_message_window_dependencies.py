"""既読8280命令を再実行せず、5依存の出自と厳密予算を検査する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_window_dependencies as m

class DependenciesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=m.saved_inputs()
    def mutate(self,f):
        c=copy.deepcopy(self.c);f(c)
        with self.assertRaises(ValueError):m.plan(c)
    def test_five_roots(self):self.assertEqual(m.plan(self.c)['roots'],list(m.ROOTS))
    def test_no_recursive_calls(self):self.assertIs(m.plan(self.c)['recursive_direct_calls'],False)
    def test_no_replay(self):self.assertEqual(m.plan(self.c)['accepted_contract_cases_replayed'],0)
    def test_budget(self):self.assertEqual((m.plan(self.c)['max_nodes'],m.plan(self.c)['max_bytes']),(2048,8192))
    def test_node_count(self):self.mutate(lambda c:c['nodes'].pop())
    def test_duplicate_old_node(self):self.mutate(lambda c:c['nodes'].__setitem__(0,c['nodes'][1]))
    def test_candidate(self):self.mutate(lambda c:c['window_frontier'].update(candidate={}))
    def test_prior_bytes(self):self.mutate(lambda c:c['window_frontier'].update(new_window_bytes=79))
    def test_selector_target(self):self.mutate(lambda c:c['window_frontier']['selector0'].update(target=0x0800495a))
    def test_selector_word(self):self.mutate(lambda c:c['window_frontier']['selector0'].update(hex='00000000'))
    def test_pending(self):self.mutate(lambda c:c['window_frontier'].update(pending_direct_callees=[]))
    def test_continuation(self):self.mutate(lambda c:c['window_frontier'].update(pending_continuations=[1]))
    def test_acceptance_flags(self):
        for k in m.prior.FALSE:
            with self.subTest(flag=k):self.mutate(lambda c:c['window_frontier'].__setitem__(k,True))
    def test_call_origins(self):
        for site,_ in m.ORIGINS:
            with self.subTest(site=site):self.mutate(lambda c:next(n for n in c['nodes']if n['address']==site).__setitem__('target',0))
    def test_r8(self):self.mutate(lambda c:next(n for n in c['nodes']if n['address']==0x081c7ae8).__setitem__('register',7))
    def test_prior_contracts(self):self.mutate(lambda c:c['task_contracts'].update(contract_cases=0))
    def result(self):return dict(initial_roots=list(m.ROOTS),saved_roots_reused=[],saved_nodes_redecoded=0,
        direct_calls_recursively_expanded=0,new_nodes=[dict(address=m.ROOTS[0]&~1,size=2,hex='7047')])
    def test_new_only(self):m.validate_new(self.result(),self.c)
    def reject(self,f):
        r=self.result();f(r)
        with self.assertRaises(ValueError):m.validate_new(r,self.c)
    def test_extra_root(self):self.reject(lambda r:r['initial_roots'].append(0x08000001))
    def test_redecode(self):self.reject(lambda r:r.update(saved_nodes_redecoded=1))
    def test_recursion(self):self.reject(lambda r:r.update(direct_calls_recursively_expanded=1))
    def test_saved_root(self):self.reject(lambda r:r.update(saved_roots_reused=[m.ROOTS[0]]))
    def test_old_node(self):self.reject(lambda r:r.update(new_nodes=[self.c['nodes'][0]]))
    def test_duplicate(self):self.reject(lambda r:r['new_nodes'].append(r['new_nodes'][0]))
    def test_word_data(self):self.reject(lambda r:r['new_nodes'][0].update(address=m.prior.TABLE))
    def test_odd_address(self):self.reject(lambda r:r['new_nodes'][0].update(address=m.ROOTS[0]))
    def test_truncated(self):self.reject(lambda r:r['new_nodes'][0].update(hex='00'))
    def test_no_nodes(self):self.reject(lambda r:r.update(new_nodes=[]))

if __name__=='__main__':unittest.main()
