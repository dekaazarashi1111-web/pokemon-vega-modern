"""有限wave/未読境界の回帰。旧ABI/nativeは呼ばない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_remaining_frontier as m

A=m.ROM_BASE
RAW=bytes(2048)

def node(at):
    return {'address':at,'size':2,'hex':'7047','kind':'return','memory_write':False}

def edge(kind,target=None,site=A):
    value={'site':site,'kind':kind}
    if target is not None:value['target']=target
    return value

def plan():
    return {'pending_direct_callees':list(m.DIRECT),'pending_effective_targets':list(m.EFFECTIVE),
        'validator_success_stops':[{'version':v,'stopped_at':at,'accepted':False} for v,at in m.SUCCESS.items()],
        'pending_continuations':[]}

class Fake:
    def __init__(self,edges=None):self.edges=edges or {};self.calls=[]
    def __call__(self,raw,roots,cached,decode):
        self.calls.append(list(roots))
        return {'roots':[{'entry':r,'boundaries':copy.deepcopy(self.edges.get(r,[]))} for r in roots],
            'new_nodes':[node(r&~1) for r in roots],'points':[x for r in roots for x in (r&~1,(r&~1)+1)]}

class FrontierTests(unittest.TestCase):
    def walk(self,f=None,**kw):return m.bounded_walk(RAW,[A|1],{},None,f or Fake(),**kw)
    def test_exact_plan(self):self.assertEqual(len(m.requested_roots(plan())),7)
    def test_plan_deduplicates_continuations(self):
        p=plan();p['pending_continuations']=[m.DIRECT[0],m.DIRECT[0]]
        self.assertEqual(len(m.requested_roots(p)),7)
    def test_direct_drift(self):
        p=plan();p['pending_direct_callees'].pop()
        with self.assertRaises(ValueError):m.requested_roots(p)
    def test_effective_drift(self):
        p=plan();p['pending_effective_targets']=[]
        with self.assertRaises(ValueError):m.requested_roots(p)
    def test_version2_has_distinct_stop(self):
        p=plan();p['validator_success_stops'][1]['stopped_at']=m.SUCCESS[1]
        with self.assertRaises(ValueError):m.requested_roots(p)
    def test_no_unearned_acceptance(self):
        p=plan();p['validator_success_stops'][0]['accepted']=True
        with self.assertRaises(ValueError):m.requested_roots(p)
    def test_plan_budget(self):
        p=plan();p['pending_continuations']=[A|1]*33
        with self.assertRaises(ValueError):m.requested_roots(p)
    def test_even_pointer_rejected(self):
        with self.assertRaises(ValueError):m.pointer(A)
    def test_boolean_pointer_rejected(self):
        with self.assertRaises(ValueError):m.pointer(True)
    def test_pointer_outside_rom(self):
        with self.assertRaises(ValueError):m.pointer(m.ROM_END|1)
    def test_single_root(self):self.assertEqual(self.walk()['new_nodes'],[node(A)])
    def test_saved_root_not_decoded(self):
        f=Fake();r=m.bounded_walk(RAW,[A|1],{A:node(A)},None,f)
        self.assertEqual(f.calls,[]);self.assertEqual(r['saved_roots_reused'],[A|1])
    def test_window_continues(self):
        f=Fake({A|1:[edge('window_boundary',A+129)]})
        self.assertEqual(len(self.walk(f)['new_nodes']),2)
    def test_branch_continues(self):
        f=Fake({A|1:[edge('outside_branch',A+257)]})
        self.assertEqual(len(self.walk(f)['waves']),2)
    def test_call_is_not_recursed(self):
        f=Fake({A|1:[edge('unread_call',A+129)]});r=self.walk(f)
        self.assertEqual(len(f.calls),1);self.assertEqual(r['pending_direct_callees'],[A+129])
    def test_cycle_reuses_node(self):
        f=Fake({A|1:[edge('outside_branch',A+129)],A+129:[edge('outside_branch',A|1,site=A+128)]})
        r=self.walk(f);self.assertEqual(len(f.calls),2);self.assertEqual(r['pending_continuations'],[])
    def test_shared_continuation_once(self):
        f=Fake({A|1:[edge('outside_branch',A+129),edge('window_boundary',A+129)]})
        self.assertEqual(self.walk(f)['waves'][1]['entries'],[A+129])
    def test_node_limit_continues_at_site(self):
        f=Fake({A|1:[edge('node_limit_boundary',site=A+128)]})
        self.assertEqual(len(self.walk(f)['waves']),2)
    def test_truncated_boundary_continues(self):
        f=Fake({A|1:[edge('truncated_instruction_boundary',site=A+128)]})
        self.assertEqual(len(self.walk(f)['waves']),2)
    def test_indirect_remains_unproven(self):
        r=self.walk(Fake({A|1:[edge('indirect_boundary')]}))
        self.assertEqual(r['pending_boundaries'][0]['kind'],'indirect_boundary')
    def test_decode_rejection_not_retried(self):
        f=Fake({A|1:[edge('decoder_rejection',site=A+2)]});r=self.walk(f)
        self.assertEqual(len(f.calls),1);self.assertEqual(len(r['pending_boundaries']),1)
    def test_wave_limit_explicit(self):
        r=self.walk(Fake({A|1:[edge('outside_branch',A+129)]}),max_rounds=1)
        self.assertTrue(r['wave_limit_reached']);self.assertEqual(r['deferred_by_wave_limit'],[A+129])
    def test_root_limit_fails_closed(self):
        with self.assertRaises(ValueError):self.walk(Fake({A|1:[edge('outside_branch',A+129)]}),max_roots=1)
    def test_node_limit_fails_closed(self):
        with self.assertRaises(ValueError):self.walk(Fake({A|1:[edge('outside_branch',A+129)]}),max_nodes=1)
    def test_byte_limit_fails_closed(self):
        with self.assertRaises(ValueError):self.walk(max_bytes=1)
    def test_invalid_budget(self):
        with self.assertRaises(ValueError):self.walk(max_rounds=0)
    def test_duplicate_roots_rejected(self):
        with self.assertRaises(ValueError):m.bounded_walk(RAW,[A|1,A|1],{},None,Fake())
    def test_root_outside_input_rejected(self):
        with self.assertRaises(ValueError):m.bounded_walk(RAW,[A+4097],{},None,Fake())
    def test_input_cache_unchanged(self):
        cached={A+128:node(A+128)};before=copy.deepcopy(cached)
        m.bounded_walk(RAW,[A|1],cached,None,Fake());self.assertEqual(cached,before)
    def test_resolved_call_not_abi_proof(self):
        rows=[{'entry':A|1,'boundaries':[edge('unread_call',A+129)]}]
        r=m.classify_boundaries(rows,{A+128:node(A+128)})
        self.assertEqual(r['pending_direct_callees'],[])
        self.assertIn('NOT_RETURN_OR_LIVE_FRAME',r['saved_boundary_links'][0]['binding'])

if __name__=='__main__':unittest.main()
