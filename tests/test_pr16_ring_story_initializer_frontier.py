"""保存callee要求と有限may-call。帰還仮定をruntime証明へ昇格しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_story_initializer_frontier as x


class InitializerFrontierTests(unittest.TestCase):
    def previous(self):return {'analysis':{'field_unread_callees':{str(k):v for k,v in x.prior.UNREAD.items()},'contract_cases':786,'host_memory_writes_between_ticks':0,'actual_wait_callback':x.prior.d.WAIT,'cases':[{'case':'field-'+str(k),'stop':['保存node境界で停止',v&~1]}for k,v in x.prior.UNREAD.items()]}}
    def nodes(self):return x.prior.payload('saved-context.json')['nodes']
    def raw(self):
        data=bytearray(0x70000)
        for r in x.ROOTS:data[r-1-0x08000000:r+1-0x08000000]=bytes.fromhex('7047')
        return bytes(data)
    def node(self,at,kind='ordinary',target=None,encoded='0020'):
        n={'address':at,'size':len(bytes.fromhex(encoded)),'hex':encoded,'kind':kind,'memory_write':False}
        if target is not None:n['target']=target
        return n
    def calls(self):return [self.node(0x080565c4,'call',0x08003af0,'00f000f8')]
    def test_01_exact_pending(self):self.assertEqual(x.pending_roots(self.previous(),self.nodes())[0],list(x.ROOTS))
    def test_02_stale_requested(self):
        p=self.previous();p['analysis']['field_unread_callees']['0']+=2
        with self.assertRaises(ValueError):x.pending_roots(p,self.nodes())
    def test_03_stale_stop(self):
        p=self.previous();p['analysis']['cases'][0]['stop'][1]+=2
        with self.assertRaises(ValueError):x.pending_roots(p,self.nodes())
    def test_04_no_repeat_root(self):
        n=self.nodes()+[self.node(x.ROOTS[0]&~1)]
        with self.assertRaises(ValueError):x.pending_roots(self.previous(),n)
    def test_05_wrong_tick_boundary(self):
        p=self.previous();p['analysis']['host_memory_writes_between_ticks']=1
        with self.assertRaises(ValueError):x.pending_roots(p,self.nodes())
    def test_06_three_new_leaves(self):self.assertEqual(len(x.collect(self.raw(),list(x.ROOTS),{})['new_nodes']),3)
    def test_07_fixed_roots(self):
        with self.assertRaises(ValueError):x.collect(self.raw(),list(x.ROOTS)[:-1],{})
    def test_08_root_order_fixed(self):
        with self.assertRaises(ValueError):x.collect(self.raw(),list(x.ROOTS)[::-1],{})
    def test_09_cached_not_decoded(self):
        raw=self.raw();known={r&~1:x.decoder.thumb_instruction(raw,r&~1)for r in x.ROOTS}
        def fail(*args):raise AssertionError('保存node再解読')
        self.assertEqual(x.collect(raw,list(x.ROOTS),known,decode=fail)['new_nodes'],[])
    def test_10_scope_outside(self):self.assertFalse(x.in_scope(0x08003af0))
    def test_11_direct_endpoint(self):self.assertEqual(x.may_paths(self.calls())['paths']['InitWindows'][-1]['target'],0x08003af1)
    def test_12_missing_not_absent(self):self.assertIn('SetDefaultFontsPointer',x.may_paths(self.calls())['not_found_in_bounded_graph'])
    def test_13_return_assumption_label(self):
        ns=[self.node(0x080565c4,'call',0x08010000,'00f000f8'),self.node(0x080565c8,'call',0x08003af0,'00f000f8')]
        p=x.may_paths(ns)['paths']['InitWindows'];self.assertEqual(p[0]['kind'],'after_call_assumes_return')
    def test_14_indirect_not_invented(self):
        ns=[self.node(0x080565c4,'indirect',encoded='0047'),self.node(0x080565c6,'call',0x08003af0,'00f000f8')]
        self.assertEqual(x.may_paths(ns)['paths'],{})
    def test_15_return_stops(self):
        ns=[self.node(0x080565c4,'return',encoded='7047'),self.node(0x080565c6,'call',0x08003af0,'00f000f8')]
        self.assertEqual(x.may_paths(ns)['paths'],{})
    def test_16_no_runtime_claim(self):
        r=x.may_paths(self.calls());self.assertFalse(r['runtime_reachability_proven']);self.assertFalse(r['argument_or_return_abi_proven'])
    def test_17_budget(self):
        ns=[self.node(0x080565c4),self.node(0x080565c6,'call',0x08003af0,'00f000f8')]
        r=x.may_paths(ns,limit=1);self.assertEqual(r['visited_nodes'],1);self.assertEqual(r['deferred_by_node_limit'],[0x080565c6])
    def test_18_bad_budget(self):
        for limit in(0,1025,True):
            with self.subTest(limit=limit),self.assertRaises(ValueError):x.may_paths(self.calls(),limit=limit)
    def test_19_bad_entry(self):
        with self.assertRaises(ValueError):x.may_paths(self.calls(),entry=0x080565c4)
    def test_20_bad_target(self):
        with self.assertRaises(ValueError):x.may_paths(self.calls(),targets={'x':0x03000001})
    def test_21_conditional_branches(self):
        ns=[self.node(0x080565c4,'conditional',0x080565ca,'01d0'),self.node(0x080565c6,'call',0x08003af0,'00f000f8'),self.node(0x080565ca,'call',0x08002c28,'00f000f8')]
        self.assertEqual(set(x.may_paths(ns)['paths']),{'InitWindows','DeactivateAllTextPrinters'})
    def test_22_cycle_terminates(self):self.assertEqual(x.may_paths([self.node(0x080565c4,'jump',0x080565c4,'fee7')])['visited_nodes'],1)
    def test_23_does_not_change_nodes(self):
        ns=self.calls();before=copy.deepcopy(ns);x.may_paths(ns);self.assertEqual(ns,before)
    def test_24_pop_pc_stops_even_bad_metadata(self):
        ns=[self.node(0x080565c4,encoded='00bd'),self.node(0x080565c6,'call',0x08003af0,'00f000f8')]
        self.assertEqual(x.may_paths(ns)['paths'],{})


if __name__=='__main__':unittest.main()
