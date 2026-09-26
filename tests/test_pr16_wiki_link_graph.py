"""有界Thumb-1構造graphの差分試験。命令実行・元受入suiteなし。"""
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from pr16_candidate_wiki_inputs import Rom,BASE,digest
from pr16_candidate_wiki_link_graph import instruction,structural_graph,signed,validate_snapshot

class LinkGraphTests(unittest.TestCase):
    def rom(self,*words):return Rom(struct.pack('<'+'H'*len(words),*words))
    def ins(self,*words):return instruction(self.rom(*words),BASE)
    def graph(self,*words,limit=2048):return structural_graph(self.rom(*words),BASE,BASE,BASE+2*len(words),limit)
    def test_sign_positive(self):self.assertEqual(signed(1023,11),1023)
    def test_sign_negative(self):self.assertEqual(signed(2047,11),-1)
    def test_bl_forward(self):
        r=self.ins(0xf000,0xf802);self.assertEqual(r['call_target'],BASE+8);self.assertEqual(r['successors'],[BASE+4]);self.assertEqual(r['size'],4)
    def test_bl_backward(self):self.assertEqual(self.ins(0xf7ff,0xfffc)['call_target'],BASE-4)
    def test_bl_bad_second_half(self):self.assertEqual(self.ins(0xf000,0x1234)['kind'],'UNSUPPORTED_LONG_BRANCH')
    def test_orphan_second_half(self):self.assertEqual(self.ins(0xf800)['kind'],'UNSUPPORTED_ENCODING')
    def test_b_backward_loop(self):
        r=self.graph(0xe7fe);self.assertEqual(r['node_count'],1);self.assertFalse(r['limit_reached'])
    def test_b_no_fallthrough_into_data(self):
        r=self.graph(0xe000,0xf800,0x4770);self.assertEqual(r['node_count'],2)
    def test_conditional_two_edges(self):self.assertEqual(self.ins(0xd000)['successors'],[BASE+2,BASE+4])
    def test_swi_terminal(self):self.assertEqual(self.ins(0xdf00)['successors'],[])
    def test_undefined_terminal(self):self.assertEqual(self.ins(0xde00)['kind'],'TRAP_OR_UNDEFINED')
    def test_bx_terminal(self):self.assertEqual(self.ins(0x4770)['kind'],'INDIRECT_PC_TRANSFER')
    def test_pop_pc_terminal(self):self.assertEqual(self.ins(0xbd10)['kind'],'POP_PC_RETURN_OR_INDIRECT')
    def test_pop_without_pc_continues(self):self.assertEqual(self.ins(0xbc10)['successors'],[BASE+2])
    def test_mov_pc_terminal(self):self.assertEqual(self.ins(0x4687)['kind'],'INDIRECT_PC_TRANSFER')
    def test_literal_alignment_and_value(self):
        r=self.ins(0x4800,0x46c0,0x0008,0x0800);self.assertEqual(r['literal_site'],BASE+4);self.assertNotIn('rom_pointer_value',r)
    def test_rom_pointer_literal(self):
        r=self.ins(0x4800,0x46c0,0x0006,0x0800);self.assertEqual(r['rom_pointer_value'],BASE+6)
    def test_unrecognized_not_walked(self):self.assertEqual(self.graph(0xbe00,0x4770)['node_count'],1)
    def test_bl_target_not_followed(self):
        r=self.graph(0xf000,0xf802,0x4770,0xbe00,0x4770);self.assertEqual(r['node_count'],2);self.assertEqual(len(r['direct_calls']),1)
    def test_graph_limit_explicit(self):self.assertTrue(self.graph(0x46c0,0x46c0,0x46c0,limit=2)['limit_reached'])
    def test_boundary_explicit(self):self.assertEqual(self.graph(0xe001)['outside_branches'],[BASE+6])
    def test_odd_entry_rejected(self):
        with self.assertRaises(ValueError):structural_graph(self.rom(0x4770),BASE+1,BASE,BASE+2)
    def test_bad_limit_rejected(self):
        with self.assertRaises(ValueError):self.graph(0x4770,limit=0)
    def test_truncated_bl_not_guessed(self):self.assertEqual(self.graph(0xf000)['nodes'][0]['kind'],'TRUNCATED_INSTRUCTION_OR_LITERAL')
    def test_no_native_promotion(self):
        r=self.graph(0x4770);self.assertEqual(r['native_acceptance'],'DEFERRED_AUDIT');self.assertFalse(r['full_function_extent_proven'])
    def test_deterministic(self):self.assertEqual(self.graph(0xd000,0x4770,0x4770),self.graph(0xd000,0x4770,0x4770))

if __name__=='__main__':unittest.main()
