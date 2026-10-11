"""保存owner結合の境界・mutation・実callsite回帰。ROM/nativeを使わない。"""
from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_owner_context as m


def n(hex_, at=0x08000000, kind='ordinary', **kw):
    return dict(address=at, size=len(bytes.fromhex(hex_)), hex=hex_, kind=kind, memory_write=False, **kw)


def regs(**kw):
    r = list(range(16))
    for k,v in kw.items(): r[int(k[1:])] = v
    return tuple(r)


class RegisterTests(unittest.TestCase):
    def test_01_add(self): self.assertEqual(m.expr('add', 0xffffffff, 2), 1)
    def test_02_sub(self): self.assertEqual(m.expr('sub', 0, 1), 0xffffffff)
    def test_03_lsl(self): self.assertEqual(m.expr('lsl', 1, 32), 0)
    def test_04_lsr(self): self.assertEqual(m.expr('lsr', 0xffffffff, 32), 0)
    def test_05_asr(self): self.assertEqual(m.expr('asr', 0x80000000, 32), 0xffffffff)
    def test_06_top(self): self.assertEqual(m.expr('add', m.TOP, 1), m.TOP)
    def test_07_identity(self): self.assertEqual(m.expr('add', ('entry',0), 0), ('entry',0))
    def test_08_widen(self): self.assertEqual(m.expr('add', ('x'*300,), 1), m.TOP)
    def test_09_mov(self): self.assertEqual(m.transfer(n('8021'), regs())[1], 128)
    def test_10_shift(self): self.assertEqual(m.transfer(n('0901'), regs(r1=128))[1], 2048)
    def test_11_addreg(self): self.assertEqual(m.transfer(n('c018'), regs(r0=2,r3=3))[0], 5)
    def test_12_addimm(self): self.assertEqual(m.transfer(n('0130'), regs(r0=9))[0], 10)
    def test_13_subimm(self): self.assertEqual(m.transfer(n('0138'), regs(r0=9))[0], 8)
    def test_14_cmp(self): self.assertEqual(m.transfer(n('0128'), regs()), regs())
    def test_15_literal(self):
        self.assertEqual(m.transfer(n('004b',literal_address=0x08000004,literal_value=0x123),regs())[3],0x123)
    def test_16_bad_literal(self):
        with self.assertRaises(ValueError): m.transfer(n('004b',literal_address=0x08000008,literal_value=3),regs())
    def test_17_store_keeps_registers(self): self.assertEqual(m.transfer(n('0460'),regs()),regs())
    def test_18_load(self): self.assertEqual(m.transfer(n('0078'),regs(r0=0x2000000))[0],('load',0x8000000,8,0x2000000))
    def test_19_push_keeps_registers(self): self.assertEqual(m.transfer(n('70b5'),regs()),regs())
    def test_20_pop_unknown(self): self.assertEqual(m.transfer(n('70bc'),regs())[4:7],(m.TOP,)*3)
    def test_21_unknown_stops(self):
        with self.assertRaises(ValueError): m.transfer(n('00de'),regs())
    def test_22_indirect_not_ordinary(self):
        with self.assertRaises(ValueError): m.transfer(n('1847'),regs())
    def test_23_node_overlap(self):
        with self.assertRaises(ValueError): m.node_map([n('00f000f8'),n('0020',0x8000002)])
    def test_24_node_conflict(self):
        with self.assertRaises(ValueError): m.node_map([n('0020'),n('0120')])
    def test_25_node_alignment(self):
        with self.assertRaises(ValueError): m.node_map([n('0020',0x8000001)])
    def test_26_join(self):
        a=(regs(),frozenset({'a'}));b=(regs(r0=20),frozenset({'b'}))
        c=m.join(a,b);self.assertEqual(c[0][0],m.TOP);self.assertEqual(c[1],frozenset({'a','b'}))
    def test_27_resource_limit(self):
        graph={'entry':0x8000001,'nodes':[n('0020'),n('7047',0x8000002,'return')]}
        with self.assertRaises(ValueError): m.contexts(graph,1)
    def test_28_branch_mutation(self):
        graph={'entry':0x8000001,'nodes':[n('00e0',kind='jump',target=0x8000006)]}
        with self.assertRaises(ValueError): m.contexts(graph)
    def test_29_call_mutation(self):
        graph={'entry':0x8000001,'nodes':[n('00f000f8',kind='call',target=0x8000008)]}
        with self.assertRaises(ValueError): m.contexts(graph)
    def test_30_opaque_abi(self):
        graph={'entry':0x8000001,'nodes':[n('00f000f8',kind='call',target=0x8000004),n('7047',0x8000004,'return')]}
        after=m.contexts(graph)['states'][0x8000004]
        self.assertEqual(after[0][1],m.TOP);self.assertTrue(any('NOT PROVEN' in r for r in after[1]))


class SavedContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frontier=json.loads((ROOT/m.PRIOR).read_text())['analysis']
        cls.patch=json.loads((ROOT/m.PATCH).read_text())
        cls.result=m.bind(cls.frontier,cls.patch)
    def row(self,entry): return next(r for r in self.result['rows'] if r['entry']==entry)
    def test_31_complete_frontier(self):
        self.assertEqual(self.result['old_target_count'],18);self.assertEqual(self.result['bound_callsite_count'],21)
    def test_32_actual_trampoline_targets(self):
        self.assertEqual(self.result['resolved_trampoline_targets'],[0x806dec5,0x81c2a55,0x92d12e1,0x92d28d9,0x92d2979])
        self.assertEqual(self.result['trampoline_callsite_count'],9)
    def test_33_copy_real_arguments(self):
        self.assertEqual(self.row(0x9378b95)['callsite_bindings'][0]['arguments']['r0'],'0x0203D000')
        self.assertEqual(self.row(0x9378b95)['callsite_bindings'][0]['arguments']['r1'],'0x02039A14')
        self.assertEqual(self.row(0x9378b95)['callsite_bindings'][0]['arguments']['r2'],'0x00000800')
    def test_34_two_validation_buffers(self):
        links=self.row(0x9378e2f)['callsite_bindings']
        self.assertEqual([r['arguments']['r0'] for r in links],['0x0203D000','0x02039A14'])
        self.assertTrue(all(r['arguments']['r1']=='0x00000800' for r in links))
        self.assertTrue(links[1]['required_unproven_abi'])
    def test_35_callback_owners(self):
        self.assertEqual([r['arguments']['r1'] for r in self.row(0x80690b5)['callsite_bindings']],['0x08068DDD','0x0806B159'])
    def test_36_saved_callee_reuse(self):
        self.assertEqual([r['target'] for r in self.result['saved_callee_links']],[0x93bee79,0x93bedc5,0x93bedfd])
    def test_37_no_acceptance_promotion(self):
        for key in ('all_callers_resolved','all_runtime_owners_excluded','caller_pointer_size_limit_proven','ring_acquisition_accepted','release_ready'):
            self.assertIs(self.result[key],False)
        self.assertEqual(self.result['candidate_reconstructions'],0)
        self.assertEqual(self.result['origin_missing_targets'],[0x9097105])
    def test_38_no_unsupported_owner_effects(self):
        self.assertFalse([s for v in self.result['owner_cfg_stops'].values() for s in v if s['kind']=='unsupported_effect'])
    def test_39_origin_mutation_rejected(self):
        altered=copy.deepcopy(self.frontier);altered['saved_origins'][str(0x8068cfd)][0]['site']+=2
        with self.assertRaises(ValueError): m.bind(altered,self.patch)
    def test_40_wrong_bx_rejected(self):
        altered=copy.deepcopy(self.frontier)
        next(n for n in altered['new_nodes'] if n['address']==0x9302f0c)['hex']='0020'
        with self.assertRaises(ValueError): m.bind(altered,self.patch)


if __name__=='__main__': unittest.main()
