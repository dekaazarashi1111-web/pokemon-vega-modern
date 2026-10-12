"""文字/選択font分岐の保存byte根拠と有限境界。nativeは使わない。"""
from pathlib import Path
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_character_frontier as t


def fixture():
    nodes=[{'address':at,'hex':raw,'size':2,'kind':'ordinary'}for at,raw in t.PREFIX.items()];by={n['address']:n for n in nodes}
    for at,target in ((0x0800581a,0x0800581e),(0x0800581c,0x08005acc),(0x08005ad4,0x08005b2a)):by[at]['target']=target
    for _,address,_,site,literal,_ in t.SPECS:by[literal]['literal_value']=address;by[site]['kind']='indirect'
    by[0x08005bc2]['literal_value']=t.SCROLL;by[0x08005bc4]['literal_value']=0x0300504c
    return nodes,{'pending_boundaries':[{'site':s[3],'kind':'indirect_boundary'}for s in t.SPECS],
        'pending_direct_callees':list(t.CALLEES),'selected_fonts':[{'selector':i}for i in (2,4,5)],'ring_acquisition_accepted':False}


def raw(count=8):return b''.join((0x08006000+4*i).to_bytes(4,'little')for i in range(count))


class TextFrontierTests(unittest.TestCase):
    def test_char_eight(self):self.assertEqual(t.bind(*fixture())['tables'][0]['count'],8)
    def test_selected_font_only(self):self.assertEqual(t.bind(*fixture())['tables'][1]['selected_indices'],[2,4,5])
    def test_scroll_mask(self):self.assertEqual(t.bind(*fixture())['scroll']['mask'],7)
    def test_no_recursive_layer(self):self.assertEqual(t.bind(*fixture())['recursive_direct_layers'],0)
    def test_changed_prefix(self):
        n,a=fixture();n[0]['hex']='0000'
        with self.assertRaises(ValueError):t.bind(n,a)
    def test_duplicate_node(self):
        n,a=fixture()
        with self.assertRaises(ValueError):t.bind(n+n[:1],a)
    def test_missing_pending(self):
        n,a=fixture();a['pending_boundaries']=[]
        with self.assertRaises(ValueError):t.bind(n,a)
    def test_missing_callee(self):
        n,a=fixture();a['pending_direct_callees'].pop()
        with self.assertRaises(ValueError):t.bind(n,a)
    def test_added_callee(self):
        n,a=fixture();a['pending_direct_callees'].append(0x08009999)
        with self.assertRaises(ValueError):t.bind(n,a)
    def test_native_claim(self):
        n,a=fixture();a['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):t.bind(n,a)
    def test_font_claim(self):
        n,a=fixture();a['selected_fonts'][0]['selector']=0
        with self.assertRaises(ValueError):t.bind(n,a)
    def test_all_char_roots(self):self.assertEqual(len(t.targets(raw(),8,tuple(range(8)),set())[1]),8)
    def test_only_selected_roots(self):self.assertEqual(t.targets(raw(6),6,(2,4,5),set())[1],[0x08006009,0x08006011,0x08006015])
    def test_deduplicate_roots(self):self.assertEqual(len(t.targets(raw()[:4]*8,8,(0,1,2),set())[1]),1)
    def test_short_table(self):
        with self.assertRaises(ValueError):t.targets(raw()[:-1],8,(0,),set())
    def test_long_table(self):
        with self.assertRaises(ValueError):t.targets(raw()+bytes(4),8,(0,),set())
    def test_odd_target(self):
        with self.assertRaises(ValueError):t.targets(bytes([1])+raw()[1:],8,(0,),set())
    def test_nonrom_target(self):
        with self.assertRaises(ValueError):t.targets(bytes(4)+raw()[4:],8,(0,),set())
    def test_data_target(self):
        with self.assertRaises(ValueError):t.targets(raw(),8,(0,),{0x08006000})
    def test_outside_index(self):
        with self.assertRaises(ValueError):t.targets(raw(),8,(8,),set())
    def test_duplicate_index(self):
        with self.assertRaises(ValueError):t.targets(raw(),8,(0,0),set())
    def test_invalid_count(self):
        with self.assertRaises(ValueError):t.targets(raw()[:4]*7,7,(0,),set())


if __name__=='__main__':unittest.main()
