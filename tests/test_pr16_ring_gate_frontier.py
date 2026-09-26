"""追加4rootの保存pending結合と復元前source固定。旧採取/contractは実行しない。"""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_gate_frontier as f


def analysis():
    return {'pending_direct_callees':list(f.CALLEES),'pending_effective_targets':list(f.EFFECTIVE),
        'pending_data_ranges':[],'pending_continuations':[],'saved_node_count':1935,
        'specific_create_caller_index_lt16_proven':True,'all_live_task_lists_acyclic_proven':False,
        'all_live_string_buffers_large_enough_proven':False,'ring_acquisition_accepted':False,'release_ready':False}


class PlanTests(unittest.TestCase):
    def test_four_exact_roots(self):self.assertEqual(f.plan(analysis()),[0x08002e4d,0x08002e79,0x08003eed,0x090970dd])
    def bad(self,k,v):
        a=analysis();a[k]=v
        with self.assertRaises(ValueError):f.plan(a)
    def test_missing_callee(self):self.bad('pending_direct_callees',list(f.CALLEES[:-1]))
    def test_duplicate_callee(self):self.bad('pending_direct_callees',[*f.CALLEES,f.CALLEES[0]])
    def test_changed_target(self):self.bad('pending_effective_targets',[0x090970df])
    def test_even_target(self):self.bad('pending_effective_targets',[0x090970dc])
    def test_extra_data(self):self.bad('pending_data_ranges',[{'start':0x083dd210,'length':32}])
    def test_extra_continuation(self):self.bad('pending_continuations',[0x08002d15])
    def test_changed_node_count(self):self.bad('saved_node_count',1936)
    def test_lost_specific_caller_proof(self):self.bad('specific_create_caller_index_lt16_proven',False)
    def test_no_live_task_promotion(self):self.bad('all_live_task_lists_acyclic_proven',True)
    def test_no_live_buffer_promotion(self):self.bad('all_live_string_buffers_large_enough_proven',True)
    def test_no_ring_promotion(self):self.bad('ring_acquisition_accepted',True)
    def test_no_release_promotion(self):self.bad('release_ready',True)
    def test_zero_is_not_false(self):self.bad('release_ready',0)
    def test_immutable_input(self):
        a=analysis();f.plan(a);self.assertEqual(a,analysis())
    def test_preflight_source_binding(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp);(p/'source').write_bytes(b'ok')
            r=f.preflight(p,('source',),analysis(),7)
            self.assertEqual(r['source_bindings'],{'source':f.identity(b'ok')});self.assertEqual(r['roots'],f.plan(analysis()))
    def test_missing_source(self):
        with tempfile.TemporaryDirectory()as tmp:
            with self.assertRaises(FileNotFoundError):f.preflight(Path(tmp),('missing',),analysis(),7)
    def test_empty_sources(self):
        with self.assertRaises(ValueError):f.preflight(Path('.'),(),analysis(),7)


if __name__=='__main__':unittest.main()
