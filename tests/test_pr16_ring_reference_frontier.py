"""新規133byte表とcallback候補の境界。ROM/旧契約を再実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_reference_frontier as m


def analysis():
    return {'pending_direct_callees':list(m.CALLEES),'pending_effective_targets':list(m.EFFECTIVE),
        'pending_data_ranges':copy.deepcopy(list(m.TABLES)),'pending_continuations':[],
        'saved_node_count':1752,'ring_acquisition_accepted':False,'release_ready':False}


def tables(words=None):
    words=[0x08008d01]*14 if words is None else words
    data=[b''.join(w.to_bytes(4,'little')for w in words),bytes(range(76)),b'\xff']
    return [dict(d,hex=b.hex(),identity=m.identity(b))for d,b in zip(m.TABLES,data)]


class PlanTests(unittest.TestCase):
    def test_exact(self):self.assertEqual(m.data_plan(analysis()),list(m.TABLES))
    def test_copy(self):
        value=m.data_plan(analysis());value[0]['length']=0;self.assertEqual(m.TABLES[0]['length'],56)
    def test_callee(self):
        a=analysis();a['pending_direct_callees'].pop()
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_effective(self):
        a=analysis();a['pending_effective_targets']=[0x09378a33]
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_data(self):
        a=analysis();a['pending_data_ranges'][1]['length']+=1
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_nodes(self):
        a=analysis();a['saved_node_count']+=1
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_continuations(self):
        a=analysis();a['pending_continuations']=[0x08000001]
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_no_promotion(self):
        for key in ('ring_acquisition_accepted','release_ready'):
            a=analysis();a[key]=True
            with self.assertRaises(ValueError):m.data_plan(a)


class TableTests(unittest.TestCase):
    def test_byte_count(self):self.assertEqual(len(m.validate_tables(tables(),[])),133)
    def test_wrong_count(self):
        with self.assertRaises(ValueError):m.validate_tables(tables()[:2],[])
    def test_descriptor(self):
        t=tables();t[2]['start']+=1
        with self.assertRaises(ValueError):m.validate_tables(t,[])
    def test_hex(self):
        t=tables();t[0]['hex']='zz'
        with self.assertRaises(ValueError):m.validate_tables(t,[])
    def test_length(self):
        t=tables();t[1]['hex']='00'
        with self.assertRaises(ValueError):m.validate_tables(t,[])
    def test_hash(self):
        t=tables();t[1]['identity']['sha256']='a'*64
        with self.assertRaises(ValueError):m.validate_tables(t,[])
    def test_code_overlap(self):
        with self.assertRaises(ValueError):m.validate_tables(tables(),[{'address':m.TABLES[0]['start'],'size':2}])
    def test_data_overlap(self):
        with self.assertRaises(ValueError):m.validate_tables(tables(),[],[(m.TABLES[1]['start'],1)])
    def test_data_disjoint(self):self.assertEqual(len(m.validate_tables(tables(),[],[(0x08008bb4,84)])),133)
    def test_short_rom(self):
        with self.assertRaises(ValueError):m.collect_tables(bytes(128),[])
    def test_wrong_rom_type(self):
        with self.assertRaises(ValueError):m.collect_tables(bytearray(8),[])
    def test_collect_exact(self):
        t=tables();raw=bytearray(m.TABLES[1]['start']-m.previous.ROM_BASE+76)
        for row in t:
            at=row['start']-m.previous.ROM_BASE;raw[at:at+row['length']]=bytes.fromhex(row['hex'])
        self.assertEqual(m.collect_tables(bytes(raw),[]),t)


class CallbackTests(unittest.TestCase):
    def test_fourteen(self):self.assertEqual(len(m.callback_candidates(tables(),[])),14)
    def test_indices(self):self.assertEqual([r['index']for r in m.callback_candidates(tables(),[])],list(range(14)))
    def test_addresses(self):self.assertEqual([r['table_address']for r in m.callback_candidates(tables(),[])],list(range(m.TABLES[0]['start'],m.TABLES[0]['start']+56,4)))
    def test_thumb_word(self):self.assertEqual(m.callback_candidates(tables(),[])[0]['effective_thumb_entry'],0x08008d01)
    def test_null_not_followed(self):self.assertFalse(m.callback_candidates(tables([0]*14),[])[0]['eligible_thumb_candidate'])
    def test_arm_not_rewritten(self):self.assertIsNone(m.callback_candidates(tables([0x08008d00]*14),[])[0]['effective_thumb_entry'])
    def test_nonrom_not_followed(self):self.assertFalse(m.callback_candidates(tables([0x02000001]*14),[])[0]['eligible_thumb_candidate'])
    def test_operand_rejected(self):
        with self.assertRaises(ValueError):m.callback_candidates(tables([0x08008d03]*14),[{'address':0x08008d00,'size':4}])
    def test_saved_entry_reused(self):self.assertTrue(m.callback_candidates(tables(),[{'address':0x08008d00,'size':4}])[0]['eligible_thumb_candidate'])
    def test_literal_rejected(self):
        with self.assertRaises(ValueError):m.callback_candidates(tables(),[{'address':0x08001000,'size':2,'literal_address':0x08008d00}])
    def test_table_target_rejected(self):
        with self.assertRaises(ValueError):m.callback_candidates(tables([m.TABLES[0]['start']|1]*14),[])
    def test_other_table_target_rejected(self):
        with self.assertRaises(ValueError):m.callback_candidates(tables(),[],[(0x08008d00,4)])


if __name__=='__main__':unittest.main()
