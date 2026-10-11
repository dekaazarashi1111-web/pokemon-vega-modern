"""未読84byte表の入力・分岐・保存境界だけ。旧ABI/native再実行なし。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_string_frontier as m


def table(words=None):
    words=[0x08008c08+i*2 for i in range(21)] if words is None else words
    raw=b''.join(w.to_bytes(4,'little') for w in words)
    return dict(m.TABLE,hex=raw.hex(),identity=m.identity(raw))


def prior():
    return {'pending_direct_callees':list(m.CALLEES),'pending_data_ranges':[copy.deepcopy(m.TABLE)],
        'pending_continuations':[],'saved_node_count':1576,'ring_acquisition_accepted':False,'release_ready':False}


class FrontierTests(unittest.TestCase):
    def test_exact_plan(self):self.assertEqual(m.data_plan(prior()),m.TABLE)
    def test_plan_copy(self):
        row=m.data_plan(prior());row['start']=0;self.assertNotEqual(row,m.TABLE)
    def test_callee_missing(self):
        row=prior();row['pending_direct_callees'].pop()
        with self.assertRaises(ValueError):m.data_plan(row)
    def test_callee_order(self):
        row=prior();row['pending_direct_callees'].reverse()
        with self.assertRaises(ValueError):m.data_plan(row)
    def test_table_drift(self):
        row=prior();row['pending_data_ranges'][0]['start']+=4
        with self.assertRaises(ValueError):m.data_plan(row)
    def test_continuation_drift(self):
        row=prior();row['pending_continuations']=[0x08000001]
        with self.assertRaises(ValueError):m.data_plan(row)
    def test_saved_count(self):
        row=prior();row['saved_node_count']+=1
        with self.assertRaises(ValueError):m.data_plan(row)
    def test_ring_promotion(self):
        row=prior();row['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):m.data_plan(row)
    def test_release_promotion(self):
        row=prior();row['release_ready']=True
        with self.assertRaises(ValueError):m.data_plan(row)
    def test_exact_84_bytes(self):self.assertEqual(len(m.validate_table(table(),[])),84)
    def test_missing_descriptor(self):
        row=table();row.pop('site')
        with self.assertRaises(ValueError):m.validate_table(row,[])
    def test_stride_drift(self):
        row=table();row['stride']=8
        with self.assertRaises(ValueError):m.validate_table(row,[])
    def test_short_payload(self):
        row=table();row['hex']='00'
        with self.assertRaises(ValueError):m.validate_table(row,[])
    def test_identity_drift(self):
        row=table();row['identity']['sha256']='a'*64
        with self.assertRaises(ValueError):m.validate_table(row,[])
    def test_nonhex(self):
        row=table();row['hex']='zz'
        with self.assertRaises(ValueError):m.validate_table(row,[])
    def test_code_overlap(self):
        with self.assertRaises(ValueError):m.validate_table(table(),[{'address':m.TABLE['start'],'size':2}])
    def test_other_data_overlap(self):
        with self.assertRaises(ValueError):m.validate_table(table(),[],[(m.TABLE['start']+80,8)])
    def test_other_data_disjoint(self):self.assertEqual(len(m.validate_table(table(),[],[(0x08008b68,24)])),84)
    def test_21_subtypes(self):self.assertEqual([r['subtype'] for r in m.dispatch_targets(table(),[])],list(range(4,25)))
    def test_table_addresses(self):self.assertEqual([r['table_address'] for r in m.dispatch_targets(table(),[])],list(range(m.TABLE['start'],m.TABLE['start']+84,4)))
    def test_even_word(self):self.assertEqual(m.dispatch_targets(table([0x08008c08]*21),[])[0]['effective_thumb_entry'],0x08008c09)
    def test_odd_word(self):self.assertEqual(m.dispatch_targets(table([0x08008c09]*21),[])[0]['effective_thumb_entry'],0x08008c09)
    def test_null_target(self):
        with self.assertRaises(ValueError):m.dispatch_targets(table([0]*21),[])
    def test_outside_rom(self):
        with self.assertRaises(ValueError):m.dispatch_targets(table([m.ROM_END]*21),[])
    def test_table_target(self):
        with self.assertRaises(ValueError):m.dispatch_targets(table([m.TABLE['start']]*21),[])
    def test_other_table_target(self):
        with self.assertRaises(ValueError):m.dispatch_targets(table([0x08008b68]*21),[],[(0x08008b68,24)])
    def test_operand_target(self):
        with self.assertRaises(ValueError):m.dispatch_targets(table([0x08008c0a]*21),[{'address':0x08008c08,'size':4}])
    def test_saved_entry(self):self.assertEqual(len(m.dispatch_targets(table([0x08008c08]*21),[{'address':0x08008c08,'size':4}])),21)
    def test_literal_target(self):
        with self.assertRaises(ValueError):m.dispatch_targets(table(),[{'address':0x08001000,'size':2,'literal_address':0x08008c08}])
    def test_short_rom(self):
        with self.assertRaises(ValueError):m.collect_table(bytes(128),[])
    def test_rom_type(self):
        with self.assertRaises(ValueError):m.collect_table(bytearray(0x9000),[])
    def test_collect_exact(self):
        row=table();at=m.TABLE['start']-m.ROM_BASE
        raw=bytes(at)+bytes.fromhex(row['hex'])+bytes(10)
        self.assertEqual(m.collect_table(raw,[]),row)


if __name__=='__main__':unittest.main()
