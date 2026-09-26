"""2leafだけの出自、SWI未受入、node/data予算を検証する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_tile_leaves as m

class LeavesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=m.saved_inputs()
    def mutate(self,f):
        c=copy.deepcopy(self.c);f(c)
        with self.assertRaises(ValueError):m.plan(c)
    def test_two_roots(self):self.assertEqual(m.plan(self.c)['roots'],list(m.ROOTS))
    def test_budget(self):self.assertEqual((m.plan(self.c)['max_nodes'],m.plan(self.c)['max_bytes']),(128,512))
    def test_no_replay(self):self.assertEqual(m.plan(self.c)['accepted_contract_cases_replayed'],0)
    def test_no_bios(self):self.assertIs(m.plan(self.c)['bios_execution_claimed'],False)
    def test_count(self):self.mutate(lambda c:c['nodes'].pop())
    def test_candidate(self):self.mutate(lambda c:c['window_dependencies'].update(candidate={}))
    def test_bytes(self):self.mutate(lambda c:c['window_dependencies'].update(new_window_bytes=615))
    def test_node_origin(self):self.mutate(lambda c:c['window_dependencies'].update(new_node_count=281))
    def test_pending(self):self.mutate(lambda c:c['window_dependencies'].update(pending_direct_callees=[]))
    def test_continuation(self):self.mutate(lambda c:c['window_dependencies'].update(pending_continuations=[1]))
    def test_bios_identity(self):self.mutate(lambda c:next(r for r in c['window_dependencies']['pending_boundaries']if r['site']==0x081c7a88).update(encoded='0cdf'))
    def test_acceptance_flags(self):
        for k in m.FALSE:
            with self.subTest(flag=k):self.mutate(lambda c:c['window_dependencies'].__setitem__(k,True))
    def test_origins(self):
        for site,_ in m.ORIGINS:
            with self.subTest(site=site):self.mutate(lambda c:next(n for n in c['nodes']if n['address']==site).update(target=0))
    def test_selector(self):self.mutate(lambda c:c['window_frontier']['selector0'].update(hex='00000000'))
    def test_old_contracts(self):self.mutate(lambda c:c['task_contracts'].update(contract_cases=0))
    def result(self):return dict(initial_roots=list(m.ROOTS),saved_roots_reused=[],saved_nodes_redecoded=0,
        direct_calls_recursively_expanded=0,new_nodes=[dict(address=m.ROOTS[0]&~1,size=2,hex='7047')])
    def test_fresh(self):m.validate_new(self.result(),self.c)
    def reject(self,f):
        r=self.result();f(r)
        with self.assertRaises(ValueError):m.validate_new(r,self.c)
    def test_root(self):self.reject(lambda r:r['initial_roots'].append(0x081c7a89))
    def test_redecode(self):self.reject(lambda r:r.update(saved_nodes_redecoded=1))
    def test_recursion(self):self.reject(lambda r:r.update(direct_calls_recursively_expanded=1))
    def test_data(self):self.reject(lambda r:r['new_nodes'][0].update(address=m.TABLE))
    def test_saved_node(self):self.reject(lambda r:r.update(new_nodes=[self.c['nodes'][0]]))
    def test_duplicate(self):self.reject(lambda r:r['new_nodes'].append(r['new_nodes'][0]))
    def test_odd(self):self.reject(lambda r:r['new_nodes'][0].update(address=m.ROOTS[0]))
    def test_size(self):self.reject(lambda r:r['new_nodes'][0].update(hex='00'))
    def test_empty(self):self.reject(lambda r:r.update(new_nodes=[]))

if __name__=='__main__':unittest.main()
