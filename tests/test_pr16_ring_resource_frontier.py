"""未読8calleeの厳密planと保存code/data境界を検証。旧ABI/nativeは実行しない。"""
from pathlib import Path
import copy
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_resource_frontier as f


def analysis():
    return {'pending_direct_callees':list(f.CALLEES),'pending_effective_targets':[],
        'pending_data_ranges':[],'pending_continuations':[],
        'known_callees_awaiting_caller_contracts':[],'saved_node_count':2457,
        'synthetic_selector_returns_proven':True,'selector_callee_arguments_bound':True,
        'all_live_slot_bounds_proven':False,'all_dispatch_returns_proven':False,
        'all_live_frames_proven':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False}


def node(at=0x080011e4,size=2,code='00b5'):
    return {'address':at,'size':size,'hex':code,'kind':'ordinary'}


class PlanTests(unittest.TestCase):
    def bad(self,key,value):
        a=analysis();a[key]=value
        with self.assertRaises(ValueError):f.plan(a)
    def test_exact_eight(self):self.assertEqual(f.plan(analysis()),list(f.CALLEES))
    def test_missing(self):self.bad('pending_direct_callees',list(f.CALLEES[:-1]))
    def test_duplicate(self):self.bad('pending_direct_callees',[*f.CALLEES,f.CALLEES[0]])
    def test_extra(self):self.bad('pending_direct_callees',[*f.CALLEES,0x081138f9])
    def test_reordered(self):self.bad('pending_direct_callees',list(reversed(f.CALLEES)))
    def test_even(self):self.bad('pending_direct_callees',[f.CALLEES[0]&~1,*f.CALLEES[1:]])
    def test_effective(self):self.bad('pending_effective_targets',[0x08000001])
    def test_data(self):self.bad('pending_data_ranges',[{'start':0x08000000,'length':4}])
    def test_continuation(self):self.bad('pending_continuations',[0x08000001])
    def test_known_pending(self):self.bad('known_callees_awaiting_caller_contracts',[0x081138f9])
    def test_node_count(self):self.bad('saved_node_count',2456)
    def test_selector_proof(self):self.bad('synthetic_selector_returns_proven',False)
    def test_arguments(self):self.bad('selector_callee_arguments_bound',False)
    def test_ring(self):self.bad('ring_acquisition_accepted',True)
    def test_release(self):self.bad('release_ready',True)
    def test_bool_strict(self):self.bad('release_ready',0)
    def test_frame(self):self.bad('all_live_frames_proven',True)
    def test_slot(self):self.bad('all_live_slot_bounds_proven',True)
    def test_returns(self):self.bad('all_dispatch_returns_proven',True)
    def test_allocation(self):self.bad('caller_pointer_size_limit_proven',True)
    def test_no_mutation(self):
        a=analysis();old=copy.deepcopy(a);f.plan(a);self.assertEqual(a,old)
    def test_bad_type(self):
        with self.assertRaises(ValueError):f.plan([])
    def test_missing_key(self):
        a=analysis();del a['release_ready']
        with self.assertRaises(ValueError):f.plan(a)
    def test_preflight(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp);(p/'input').write_bytes(b'ok')
            r=f.preflight(p,('input',),analysis(),7)
            self.assertEqual(r['source_bindings']['input'],f.identity(b'ok'));self.assertEqual(r['saved_nodes'],2457)
    def test_bad_run(self):
        with self.assertRaises(ValueError):f.preflight(Path('.'),('input',),analysis(),True)
    def test_empty_paths(self):
        with self.assertRaises(ValueError):f.preflight(Path('.'),(),analysis(),7)
    def test_missing_source(self):
        with tempfile.TemporaryDirectory()as tmp:
            with self.assertRaises(FileNotFoundError):f.preflight(Path(tmp),('absent',),analysis(),7)


class BoundaryTests(unittest.TestCase):
    def test_data_union(self):self.assertEqual(f.data_bytes([(0x08000000,4),(0x08000002,4)]),set(range(0x08000000,0x08000006)))
    def test_negative_data(self):
        with self.assertRaises(ValueError):f.data_bytes([(0x08000000,-1)])
    def test_outside_data(self):
        with self.assertRaises(ValueError):f.data_bytes([(0x09ffffff,2)])
    def test_large_data(self):
        with self.assertRaises(ValueError):f.data_bytes([(0x08000000,65537)])
    def test_no_overlap(self):self.assertEqual(f.validate_new([node()],[],set()),2)
    def test_saved_overlap(self):
        with self.assertRaises(ValueError):f.validate_new([node()],[node()],set())
    def test_saved_operand(self):
        with self.assertRaises(ValueError):f.validate_new([node()],[node(0x080011e2,4,'00f000f8')],set())
    def test_data_operand(self):
        with self.assertRaises(ValueError):f.validate_new([node()],[],{0x080011e5})
    def test_duplicate(self):
        with self.assertRaises(ValueError):f.validate_new([node(),node()],[],set())
    def test_odd(self):
        with self.assertRaises(ValueError):f.validate_new([node(0x080011e5)],[],set())
    def test_bad_width(self):
        with self.assertRaises(ValueError):f.validate_new([node(size=3,code='000000')],[],set())
    def test_bad_hex_width(self):
        with self.assertRaises(ValueError):f.validate_new([node(code='00')],[],set())
    def test_outside_node(self):
        with self.assertRaises(ValueError):f.validate_new([node(0x02000000)],[],set())


if __name__=='__main__':unittest.main()
