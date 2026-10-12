"""messageで使用するfontと初期化の保存境界だけを検査する。

run35231497691は28tests中1FAIL。拒否fixtureに正常callsiteを渡した誤りで、
候補復元/byte採取/nativeは開始していない。元runを成功へ読み替えない。
artifact10501750832 / SHA256 fd1acc51179e701774d6c77a2b6fd4df63e30660b63dbd301577e3328c9fc5f5。
"""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_font_frontier as t
import pr16_ring_followup_v2 as s


def message():
    return [*({'address':p,'hex':raw,'size':2,'kind':'ordinary'}for p,raw,_ in t.SELECTOR_SITES),
        *({'address':p,'hex':raw,'size':4,'kind':'call','target':0x080f7d28}for p,raw in t.CALLS),
        {'address':0x080f7d4a,'hex':'6846','size':2,'kind':'ordinary'},
        {'address':0x080f7d4c,'hex':'4171','size':2,'kind':'ordinary'}]


def analysis():
    # fixtureはfont2/4/5に必要な有限12byte recordだけを構成する。
    data=bytearray(192);targets=(0x080053b5,0x08005425,0x0800545d)
    for i,target in zip(t.SELECTORS,targets):data[i*12:i*12+4]=target.to_bytes(4,'little')
    return {'candidate_font_pointer_suppliers_bound':True,'candidate_font_descriptor_lookup_bound':True,
        'actual_font_table_length_proven':False,'initializer_runtime_observed':False,
        'tables':[{'address':t.TABLE,'hex':data.hex(),'identity':s.identity(data),
            'actual_table_length_proven':False,'supplier_callsites':[0x080f8a2c]}],
        'pending_font_callback_targets':list(targets)}


def initializer():
    return [{'address':0x080f8a28,'hex':'00b5','size':2,'kind':'ordinary'},
        {'address':0x080f8a2a,'hex':'0248','size':2,'kind':'ordinary','literal_address':0x080f8a34,'literal_value':t.TABLE},
        {'address':0x080f8a2c,'hex':'0af7f6f8','size':4,'kind':'call','target':t.prior.SETTER&~1},
        {'address':0x080f8a30,'hex':'01bc','size':2,'kind':'ordinary'},
        {'address':0x080f8a32,'hex':'0047','size':2,'kind':'indirect','register':0},
        {'address':0x08002c1c,'hex':'0149','size':2,'kind':'ordinary','literal_address':0x08002c24,'literal_value':t.prior.GFONTS},
        {'address':0x08002c1e,'hex':'0860','size':2,'kind':'ordinary'},
        {'address':0x08002c20,'hex':'7047','size':2,'kind':'return','register':14}]


class FontFrontierTests(unittest.TestCase):
    def test_only_message_selectors_are_selected(self):self.assertEqual(t.message_selectors(message())['selectors'],[2,4,5])
    def test_message_binding_not_live_execution(self):self.assertIs(t.message_selectors(message())['message_path_runtime_observed'],False)
    def test_changed_message_immediate_rejected(self):
        n=message();n[0]['hex']='0321'
        with self.assertRaisesRegex(ValueError,'selector差分'):t.message_selectors(n)
    def test_changed_message_call_rejected(self):
        n=message();n[3]['target']+=2
        with self.assertRaisesRegex(ValueError,'call差分'):t.message_selectors(n)
    def test_template_font_offset_mismatch_rejected(self):
        n=message();n[-1]['hex']='8171'
        with self.assertRaisesRegex(ValueError,'font保存差分'):t.message_selectors(n)
    def test_duplicate_saved_message_node_rejected(self):
        n=message()
        with self.assertRaisesRegex(ValueError,'node重複'):t.message_selectors(n+n[:1])
    def test_record_stride_and_selector_targets(self):
        rows=t.selected_fonts(analysis(),[2,4,5]);self.assertEqual([r['record_address']for r in rows],[t.TABLE+24,t.TABLE+48,t.TABLE+60])
        self.assertEqual([r['callback']for r in rows],[0x080053b5,0x08005425,0x0800545d])
    def test_no_unselected_offset_is_promoted(self):self.assertEqual(len(t.selected_fonts(analysis(),[2,4,5])),3)
    def test_wrong_selector_set_rejected(self):
        with self.assertRaisesRegex(ValueError,'選択font集合'):t.selected_fonts(analysis(),[0,1,2,3,4,5,6])
    def test_missing_pointer_supplier_proof_rejected(self):
        a=analysis();a['candidate_font_pointer_suppliers_bound']=False
        with self.assertRaisesRegex(ValueError,'保存table結合'):t.selected_fonts(a,[2,4,5])
    def test_missing_lookup_proof_rejected(self):
        a=analysis();a['candidate_font_descriptor_lookup_bound']=False
        with self.assertRaisesRegex(ValueError,'保存table結合'):t.selected_fonts(a,[2,4,5])
    def test_live_initialization_claim_rejected(self):
        a=analysis();a['initializer_runtime_observed']=True
        with self.assertRaisesRegex(ValueError,'過大主張'):t.selected_fonts(a,[2,4,5])
    def test_table_length_claim_rejected(self):
        a=analysis();a['actual_font_table_length_proven']=True
        with self.assertRaisesRegex(ValueError,'過大主張'):t.selected_fonts(a,[2,4,5])
    def test_duplicate_table_rejected(self):
        a=analysis();a['tables']*=2
        with self.assertRaisesRegex(ValueError,'table集合'):t.selected_fonts(a,[2,4,5])
    def test_changed_table_bytes_rejected(self):
        a=analysis();a['tables'][0]['hex']='00'*192
        with self.assertRaisesRegex(ValueError,'identity'):t.selected_fonts(a,[2,4,5])
    def test_changed_supplier_callsite_rejected(self):
        a=analysis();a['tables'][0]['supplier_callsites']=[0x080f8a2a]
        self.assertNotEqual(a['tables'][0]['supplier_callsites'],analysis()['tables'][0]['supplier_callsites'])
        with self.assertRaisesRegex(ValueError,'出自'):t.selected_fonts(a,[2,4,5])
    def test_callback_not_in_saved_frontier_rejected(self):
        a=analysis();a['pending_font_callback_targets']=[]
        with self.assertRaisesRegex(ValueError,'callback集合'):t.selected_fonts(a,[2,4,5])
    def test_even_callback_rejected(self):
        a=analysis();table=a['tables'][0];raw=bytearray.fromhex(table['hex']);raw[24]&=254
        table.update(hex=raw.hex(),identity=s.identity(raw))
        with self.assertRaisesRegex(ValueError,'callback形式'):t.selected_fonts(a,[2,4,5])
    def test_complete_initializer_return_and_frame(self):
        rows=t.initializer_contracts(initializer());self.assertEqual(len(rows),9)
        self.assertEqual(sum(r['returned']for r in rows),4);self.assertTrue(all(r['maximum_stack_bytes']==4 for r in rows))
    def test_wrong_init_table_store_fails_closed(self):
        n=initializer();n[1]['literal_value']+=4
        with self.assertRaises(ValueError):t.initializer_contracts(n)
    def test_missing_initializer_return_not_success(self):
        with self.assertRaises(ValueError):t.initializer_contracts(initializer()[:4]+initializer()[5:])
    def test_direct_layer_is_not_recursive(self):
        self.assertEqual(t.follow_direct({'direct_calls_recursively_expanded':0,'pending_direct_callees':[0x08006001]},set()),[0x08006001])
    def test_already_recursive_walker_rejected(self):
        with self.assertRaisesRegex(ValueError,'再帰禁止'):t.follow_direct({'direct_calls_recursively_expanded':1},set())
    def test_duplicate_direct_roots_rejected(self):
        with self.assertRaisesRegex(ValueError,'予算'):t.follow_direct({'direct_calls_recursively_expanded':0,'pending_direct_callees':[0x08006001]*2},set())
    def test_known_callee_not_resampled(self):
        with self.assertRaisesRegex(ValueError,'direct境界'):t.follow_direct({'direct_calls_recursively_expanded':0,'pending_direct_callees':[0x08006001]},{0x08006000})
    def test_even_callee_rejected(self):
        with self.assertRaisesRegex(ValueError,'direct境界'):t.follow_direct({'direct_calls_recursively_expanded':0,'pending_direct_callees':[0x08006000]},set())
    def test_unrelated_assert_not_expanded(self):
        with self.assertRaisesRegex(ValueError,'assert'):t.follow_direct({'direct_calls_recursively_expanded':0,'pending_direct_callees':[t.ui.LOG|1]},set())
    def test_empty_direct_frontier_stays_empty(self):self.assertEqual(t.follow_direct({'direct_calls_recursively_expanded':0,'pending_direct_callees':[]},set()),[])


if __name__=='__main__':unittest.main()
