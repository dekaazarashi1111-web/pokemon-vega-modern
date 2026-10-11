"""今回3data表/dispatch対象の境界のみ。旧ABI/nativeなし。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_dependency_frontier as m


def tables(words=None):
    words=words or [0x08008b80+i*2 for i in range(6)]
    result=[]
    for i,desc in enumerate(m.TABLES):
        raw=b''.join(w.to_bytes(4,'little') for w in words) if i==0 else bytes(desc['length'])
        result.append(dict(desc,hex=raw.hex(),identity=m.identity(raw)))
    return result


def prior():
    return {'pending_direct_callees':list(m.CALLEES),'pending_data_ranges':list(m.TABLES),
        'pending_continuations':[],'ring_acquisition_accepted':False,'release_ready':False}


class DataTests(unittest.TestCase):
    def test_plan_exact(self):self.assertEqual(m.data_plan(prior()),m.TABLES)
    def test_plan_copy(self):
        x=m.data_plan(prior());x[0]['start']=1;self.assertNotEqual(x,m.TABLES)
    def test_callee_drift(self):
        p=prior();p['pending_direct_callees'].pop()
        with self.assertRaises(ValueError):m.data_plan(p)
    def test_table_drift(self):
        p=copy.deepcopy(prior());p['pending_data_ranges'][0]['length']=28
        with self.assertRaises(ValueError):m.data_plan(p)
    def test_continuation_drift(self):
        p=prior();p['pending_continuations']=[1]
        with self.assertRaises(ValueError):m.data_plan(p)
    def test_no_promotion(self):
        p=prior();p['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):m.data_plan(p)
    def test_data_total_440(self):self.assertEqual(len(m.validate_tables(tables(),[])),440)
    def test_three_tables_required(self):
        with self.assertRaises(ValueError):m.validate_tables(tables()[:2],[])
    def test_descriptor_required(self):
        rows=tables();rows[0]['stride']=8
        with self.assertRaises(ValueError):m.validate_tables(rows,[])
    def test_payload_length(self):
        rows=tables();rows[0]['hex']='00'
        with self.assertRaises(ValueError):m.validate_tables(rows,[])
    def test_payload_identity(self):
        rows=tables();rows[0]['identity']['sha256']='a'*64
        with self.assertRaises(ValueError):m.validate_tables(rows,[])
    def test_code_data_disjoint(self):
        with self.assertRaises(ValueError):m.validate_tables(tables(),[{'address':m.TABLES[1]['start'],'size':2}])
    def test_dispatch_six_controls(self):
        rows=m.dispatch_targets(tables(),[]);self.assertEqual([r['control_byte'] for r in rows],list(range(250,256)))
    def test_even_mov_pc_target(self):self.assertEqual(m.dispatch_targets(tables(),[])[0]['effective_thumb_entry'],0x08008b81)
    def test_odd_mov_pc_target(self):self.assertEqual(m.dispatch_targets(tables([0x08008b81]*6),[])[0]['effective_thumb_entry'],0x08008b81)
    def test_zero_dispatch_rejected(self):
        with self.assertRaises(ValueError):m.dispatch_targets(tables([0]*6),[])
    def test_outside_rom_rejected(self):
        with self.assertRaises(ValueError):m.dispatch_targets(tables([m.ROM_END]*6),[])
    def test_table_self_target_rejected(self):
        with self.assertRaises(ValueError):m.dispatch_targets(tables([m.TABLES[0]['start']]*6),[])
    def test_operand_target_rejected(self):
        with self.assertRaises(ValueError):m.dispatch_targets(tables([0x08008b82]*6),[{'address':0x08008b80,'size':4}])
    def test_saved_entry_reused(self):
        self.assertEqual(len(m.dispatch_targets(tables([0x08008b80]*6),[{'address':0x08008b80,'size':4}])),6)
    def test_literal_target_rejected(self):
        with self.assertRaises(ValueError):m.dispatch_targets(tables(),[{'address':0x08001000,'size':2,'literal_address':0x08008b80}])
    def test_short_rom_rejected(self):
        with self.assertRaises(ValueError):m.collect_tables(bytes(128),[])

if __name__=='__main__':unittest.main()
