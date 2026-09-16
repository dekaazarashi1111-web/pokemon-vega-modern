"""11文字列の有限採取境界。旧contract/nativeは起動しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_text_frontier as m


def analysis():
    return {'pending_direct_callees':list(m.CALLEES),'pending_effective_targets':list(m.EFFECTIVE),
        'pending_data_ranges':m.text_plan(),'pending_continuations':[],
        'saved_node_count':1859,'ring_acquisition_accepted':False,'release_ready':False}


def texts():
    return [dict(d,hex=(b'\x11'*(d['length']-1)+b'\xff').hex(),
        identity=m.identity(b'\x11'*(d['length']-1)+b'\xff'))for d in m.text_plan()]


class PlanTests(unittest.TestCase):
    def test_exact(self):self.assertEqual(m.data_plan(analysis()),m.text_plan())
    def test_copy(self):
        a=analysis();p=m.data_plan(a);p[0]['length']=0;self.assertEqual(a,analysis())
    def test_callee(self):
        a=analysis();a['pending_direct_callees']=[]
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_effective(self):
        a=analysis();a['pending_effective_targets']=[0x08002d17]
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_ranges(self):
        a=analysis();a['pending_data_ranges'][0]['length']+=1
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_continuation(self):
        a=analysis();a['pending_continuations']=[0x08000001]
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_nodes(self):
        a=analysis();a['saved_node_count']=1860
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_acceptance(self):
        a=analysis();a['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_release(self):
        a=analysis();a['release_ready']=True
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_false_not_zero(self):
        a=analysis();a['release_ready']=0
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_missing(self):
        a=analysis();del a['pending_continuations']
        with self.assertRaises(ValueError):m.data_plan(a)
    def test_no_extra_scan(self):self.assertEqual(sum(d['length']for d in m.text_plan()),83)


class DataTests(unittest.TestCase):
    def test_exact(self):self.assertEqual(len(m.validate_texts(texts(),[])),83)
    def test_count(self):
        with self.assertRaises(ValueError):m.validate_texts(texts()[:-1],[])
    def test_order(self):
        with self.assertRaises(ValueError):m.validate_texts(texts()[::-1],[])
    def test_descriptor(self):
        t=texts();t[0]['start']+=1
        with self.assertRaises(ValueError):m.validate_texts(t,[])
    def test_bool_length(self):
        t=texts();t[0]['length']=True
        with self.assertRaises(ValueError):m.validate_texts(t,[])
    def test_hex(self):
        t=texts();t[0]['hex']='zz'
        with self.assertRaises(ValueError):m.validate_texts(t,[])
    def test_length(self):
        t=texts();t[0]['hex']='00'
        with self.assertRaises(ValueError):m.validate_texts(t,[])
    def test_digest(self):
        t=texts();t[0]['identity']['sha256']='0'*64
        with self.assertRaises(ValueError):m.validate_texts(t,[])
    def test_code_overlap(self):
        with self.assertRaises(ValueError):m.validate_texts(texts(),[{'address':m.TEXT_POINTERS[0],'size':2}])
    def test_literal_overlap(self):
        with self.assertRaises(ValueError):m.validate_texts(texts(),[{'address':0x08000000,'size':2,'literal_address':m.TEXT_POINTERS[0]}])
    def test_data_overlap(self):
        with self.assertRaises(ValueError):m.validate_texts(texts(),[],[(m.TEXT_POINTERS[-1]+31,1)])
    def test_disjoint(self):self.assertEqual(len(m.validate_texts(texts(),[],[(0x08001000,4)])),83)
    def test_range_type(self):
        with self.assertRaises(ValueError):m.validate_texts(texts(),[],[(0x08001000,False)])
    def test_short_input(self):
        with self.assertRaises(ValueError):m.collect_texts(bytes(64),[])
    def test_wrong_input(self):
        with self.assertRaises(ValueError):m.collect_texts(bytearray(64),[])
    def test_collect(self):
        raw=bytearray(m.TEXT_POINTERS[-1]-m.ROM_BASE+32)
        for t in texts():raw[t['start']-m.ROM_BASE:t['start']-m.ROM_BASE+t['length']]=bytes.fromhex(t['hex'])
        self.assertEqual(m.collect_texts(bytes(raw),[]),texts())
    def test_terminated(self):self.assertTrue(all(r['first_ff_offset']is not None for r in m.terminators(texts())))
    def test_no_terminator_stays_unproven(self):
        t=texts();raw=b'\x01'*t[-1]['length'];t[-1].update(hex=raw.hex(),identity=m.identity(raw))
        self.assertIsNone(m.terminators(t)[-1]['bounded_prefix_hex'])
    def test_first_ff_only(self):
        t=texts();raw=b'\xff'*t[0]['length'];t[0].update(hex=raw.hex(),identity=m.identity(raw))
        self.assertEqual(m.terminators(t)[0]['bounded_prefix_hex'],'ff')
    def test_no_runtime_promotion(self):self.assertTrue(all(r['all_runtime_buffer_bounds_proven']is False for r in m.terminators(texts())))


if __name__=='__main__':unittest.main()
