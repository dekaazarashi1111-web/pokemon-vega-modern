"""caller候補の字句境界・有限性・保存graphの否定過大主張を検査する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_story_caller_frontier as m

class CallerTests(unittest.TestCase):
    def node(self,at=0x8000100):return dict(address=at,size=2,hex='7047',kind='indirect')
    def table(self,body):return 'gScriptCmdTable::\n'+body+'\ngScriptCmdTableEnd::'
    def test_01_saved_real_entries(self):
        c=m.context();self.assertEqual(len(c['nodes']),8628)
        self.assertEqual(set(m.saved_inbound(c['nodes'])),set(m.TARGETS))
    def test_02_no_saved_inbound_is_not_exclusion(self):
        for r in m.saved_inbound(m.context()['nodes']).values():
            self.assertEqual(r['saved_inbound'],[]);self.assertFalse(r['all_callers_excluded'])
    def test_03_saved_bootstrap_not_replayed(self):
        a=m.context()['bootstrap_lifecycle'];self.assertEqual(a['successful_lifecycles'],12)
        self.assertFalse(a['normal_story_initializer_reachability_proven'])
    def test_04_missing_entry(self):
        with self.assertRaises(ValueError):m.saved_inbound([self.node()],{'f':0x8000201})
    def test_05_even_entry(self):
        with self.assertRaises(ValueError):m.saved_inbound([self.node()],{'f':0x8000100})
    def test_06_duplicate_node(self):
        with self.assertRaises(ValueError):m.saved_inbound([self.node(),self.node()],{'f':0x8000101})
    def test_07_bad_size(self):
        with self.assertRaises(ValueError):m.saved_inbound([dict(self.node(),size=4)],{'f':0x8000101})
    def test_08_call_is_recorded(self):
        n=dict(self.node(0x8000200),kind='call',target=0x8000100)
        self.assertEqual(m.saved_inbound([self.node(),n],{'f':0x8000101})['f']['saved_inbound'][0]['site'],0x8000200)
    def test_09_literal_is_not_call(self):
        n=dict(self.node(0x8000200),literal_value=0x8000101,literal_address=0x8000210)
        self.assertIn('not_executed',m.saved_inbound([self.node(),n],{'f':0x8000101})['f']['saved_inbound'][0]['kind'])
    def test_10_mask_preserves_lines(self):
        t='/* x\ny */ void f(){"x";}';self.assertEqual(len(m.mask_c(t)),len(t));self.assertEqual(m.mask_c(t).count('\n'),1)
    def test_11_comments_not_calls(self):
        self.assertEqual(m.definitions('void f(){/* g(); */ // h();\n}')[0]['calls'],[])
    def test_12_strings_not_calls(self):
        self.assertEqual(m.definitions('void f(){char *s="g(); { }";}')[0]['calls'],[])
    def test_13_char_braces(self):
        self.assertEqual(len(m.definitions("void f(){char c='}'; g();}")),1)
    def test_14_prototypes_ignored(self):
        self.assertEqual(m.definitions('void f(void);\nvoid g(){ f(); }')[0]['name'],'g')
    def test_15_nested_blocks(self):
        self.assertEqual([x['symbol']for x in m.definitions('void f(){if (1){g();}}')[0]['calls']],['g'])
    def test_16_unclosed_function(self):
        with self.assertRaises(ValueError):m.definitions('void f(){g();')
    def test_17_multiline_function(self):
        self.assertEqual(m.definitions('static bool8 f(\nint x\n)\n{g();}')[0]['name'],'f')
    def test_18_reverse_depth(self):
        src={'x.c':'void a(){b();}\nvoid b(){c();}\nvoid c(){target();}'}
        self.assertEqual([r['caller']for r in m.source_callers(src,('target',),2)['edges']],['c','b'])
    def test_19_recursion_is_finite(self):
        r=m.source_callers({'x.c':'void f(){f();}'},('f',),4)
        self.assertEqual(len(r['edges']),1);self.assertFalse(r['all_reference_callers_enumerated'])
    def test_20_depth_rejection(self):
        with self.assertRaises(ValueError):m.source_callers({},depth=0)
    def test_21_definition_name_not_inbound(self):
        self.assertEqual(m.source_callers({'x.c':'void target(){}'},('target',))['edges'],[])
    def test_22_table_comments(self):
        self.assertEqual(m.command_table(self.table('\t.4byte ScrCmd_message @ 0x67')),['ScrCmd_message'])
    def test_23_unknown_directive(self):
        with self.assertRaises(ValueError):m.command_table(self.table('.word ScrCmd_message'))
    def test_24_table_empty(self):
        with self.assertRaises(ValueError):m.command_table(self.table(''))
    def test_25_table_missing_label(self):
        with self.assertRaises(ValueError):m.command_table('.4byte ScrCmd_message')
    def test_26_reference_allowlist(self):
        with self.assertRaises(ValueError):m.reference_path('src/../private.c')
    def test_27_fixed_reference(self):
        self.assertTrue(m.reference_path('src/overworld.c').endswith(m.owners.PINS['pokefirered'][1]))
    def test_28_nul_rejected(self):
        with self.assertRaises(ValueError):m.mask_c('\0')
    def test_29_reference_never_live(self):
        r=m.source_callers({'x.c':'void f(){target();}'},('target',))
        self.assertTrue(r['edges'][0]['reference_only_not_candidate_binding'])
    def test_30_no_input_mutation(self):
        nodes=[self.node()];before=copy.deepcopy(nodes);m.saved_inbound(nodes,{'f':0x8000101});self.assertEqual(nodes,before)

    def test_31_direct_jump(self):
        n=dict(self.node(0x8000200),kind='jump',target=0x8000100)
        self.assertEqual(m.saved_inbound([self.node(),n],{'f':0x8000101})['f']['saved_inbound'][0]['kind'],'jump')

if __name__=='__main__':unittest.main()
