"""旧診断を走らせず、保存caller出自・新規一根/44byte境界の改変拒否を検査。"""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_owner_frontier as t

class CallerPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.nodes,_,_,cls.analysis=t.saved_inputs()
    def setUp(self):self.nodes=copy.deepcopy(type(self).nodes);self.analysis=copy.deepcopy(type(self).analysis)
    def plan(self):return t.plan(self.nodes,self.analysis)
    def change(self,at,**kw):next(n for n in self.nodes if n['address']==at).update(kw)
    def rejected(self):
        with self.assertRaises(ValueError):self.plan()
    def test_slot_zero(self):self.assertEqual(self.plan()['message_slot']['id'],0)
    def test_slot_extent(self):self.assertEqual(self.plan()['message_slot']['size'],32)
    def test_three_font_routes(self):self.assertEqual([r['font'] for r in self.plan()['font_routes']],[4,5,2])
    def test_speed_literal(self):self.assertEqual(self.plan()['new_root'],0x0937855d)
    def test_live_not_promoted(self):self.assertFalse(self.plan()['runtime_reachability_proven'])
    def test_initializer_not_assumed(self):self.assertFalse(self.plan()['initializer_entry_reached_from_message'])
    def test_source_buffer(self):self.assertEqual(self.plan()['text_pointer'],0x02021c88)
    def test_no_input_mutation(self):
        old=copy.deepcopy((self.nodes,self.analysis));self.plan();self.assertEqual(old,(self.nodes,self.analysis))
    def test_wrong_call(self):self.change(0x08068d94,target=0x080f7d28);self.rejected()
    def test_wrong_branch_font(self):self.change(0x080f7dfe,hex='ff21');self.rejected()
    def test_wrong_slot(self):self.change(0x080f7dfc,hex='1f20');self.rejected()
    def test_wrong_speed(self):self.change(0x080f8908,literal_value=0x09378589);self.rejected()
    def test_wrong_bx(self):self.change(0x080f890a,register=2);self.rejected()
    def test_wrong_text_pointer(self):self.change(0x080f7dee,literal_value=0x02021c89);self.rejected()
    def test_wrong_ldr_register(self):self.change(0x080f7dee,hex='074b');self.rejected()
    def test_wrong_callback(self):self.analysis['selected_fonts'][0]['callback']+=2;self.rejected()
    def test_wrong_table_hash(self):self.analysis['tables'][0]['identity']['sha256']='0'*64;self.rejected()
    def test_wrong_candidate(self):self.analysis['candidate']['crc32']='00000000';self.rejected()
    def test_duplicate_node(self):self.nodes.append(copy.deepcopy(self.nodes[0]));self.rejected()
    def test_old_speed_node_rejected(self):self.nodes[-1]['address']=t.LO;self.rejected()
    def test_unaccepted_stays_false(self):self.analysis['initializer_runtime_observed']=True;self.rejected()

class NewGraphTests(unittest.TestCase):
    def setUp(self):self.r=dict(initial_roots=[t.SPEED],saved_roots_reused=[],saved_nodes_redecoded=0,
        direct_calls_recursively_expanded=0,wave_limit_reached=False,deferred_by_wave_limit=[],
        new_nodes=[dict(address=t.LO,size=2,hex='7047',kind='return')])
    def rejected(self,known=()):
        with self.assertRaises(ValueError):t.validate_new(self.r,known)
    def test_valid_minimum(self):self.assertEqual(t.validate_new(self.r,set()),set(range(t.LO,t.LO+2)))
    def test_already_known(self):self.rejected({t.LO})
    def test_no_redecode(self):self.r['saved_nodes_redecoded']=1;self.rejected()
    def test_no_recursion(self):self.r['direct_calls_recursively_expanded']=1;self.rejected()
    def test_no_extra_root(self):self.r['initial_roots'].append(t.HI|1);self.rejected()
    def test_no_missing_root(self):self.r['new_nodes']=[];self.rejected()
    def test_no_window_escape(self):self.r['new_nodes'].append(dict(address=t.HI,size=2,hex='7047'));self.rejected()
    def test_no_partial_instruction(self):self.r['new_nodes'][0]['hex']='70';self.rejected()
    def test_no_outside_literal(self):self.r['new_nodes'][0]['literal_address']=t.HI;self.rejected()
    def test_budget_not_silenced(self):self.r['wave_limit_reached']=True;self.rejected()

if __name__=='__main__':unittest.main()
