"""Synthetic parser/observer contracts only; fixtures are never runtime evidence."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_ring_caller_snapshot as a


def fixture():
    snap=a.compose.fixture()
    snap.pop('normal_mapping_stable');snap.pop('synchronous')
    entry={'kind':'entry','ordinal':1,'step':1,'raw_pc':a.ENTRY+2,'cpsr':63,
           'r0':560,'r4':42,'snapshot':snap,'record_readable':True,'flag_readable':True,
           'memory_control':0x0D000020,'ime':1,'ie':1,'dma_enable':0}
    path=[{'kind':'pc','ordinal':1,'offset':0,'pc':a.ENTRY,'sp':snap['sp'],'cpsr':63},
          {'kind':'pc','ordinal':1,'offset':1,'pc':a.ENTRY+2,'sp':snap['sp']-44,'cpsr':63}]
    exit={'kind':'exit','ordinal':1,'returned':True,'steps':2,
          'raw_pc':(snap['lr']&~1)+2,'cpsr':63,'sp':snap['sp'],'r0':0,'r4':42,
          'minimum_sp':snap['sp']-44,'saved_lr_word':snap['lr'],'saved_r4_word':42,
          'record_word_after':0x248230,'flag_byte_after':0x25,'counter_after':1,
          'pending_id_after':560,'cpu_mode_stable':True,'memory_control_stable':True,
          'dma_disabled_at_step_boundaries':True,'call_log_problems':0}
    summary={'kind':'summary','hits':1,'search_steps':2,'search_limit':a.SEARCH_LIMIT,
             'unobserved_title_frames':0,'host_memory_writes':0,'host_register_writes':0,
             'host_function_calls':0,'savestate_loads':0,'ring_acquisition_accepted':False,'log_problems':0}
    return [entry,*path,exit,summary]


def raw(rows):return ('\n'.join(json.dumps(r) for r in rows)+'\n').encode()


class SnapshotTests(unittest.TestCase):
    def setUp(self):self.rows=fixture()
    def result(self):return a.validate_trace(raw(self.rows))
    def reject_call(self):
        result=self.result();self.assertEqual(result['bound_calls'],0)
        self.assertEqual(len(result['rejected_calls']),1)
    def test_fixture_is_never_runtime_evidence(self):
        r=self.result();self.assertEqual(r['bound_calls'],1)
        self.assertFalse(r['runtime_provenance_bound']);self.assertEqual(r['new_emulator_processes'],0)
        self.assertFalse(r['bindings'][0]['runtime_provenance_bound'])
        self.assertNotIn('actual_return_observed',r['bindings'][0])
    def test_assumptions_stay_explicit(self):
        b=self.result()['bindings'][0]
        self.assertEqual(b['conditional_assumptions_not_discharged'],['normal_mapping_stable','synchronous'])
        self.assertFalse(b['allocated_storage_extent_proven']);self.assertFalse(b['synchrony_proven'])
    def test_no_hit_is_not_absence_proof(self):
        r=self.rows[-1];r['hits']=0
        value=a.validate_trace(raw([r]));self.assertEqual(value['bound_calls'],0)
        self.assertFalse(value['all_runtime_owners_excluded'])
    def test_pc_pipeline_boundary(self):
        self.assertEqual(a.instruction(a.ENTRY+2,63),a.ENTRY)
        self.assertEqual(a.instruction(0x08000004,31),0x08000000)
    def test_pc_odd_rejected(self):
        with self.assertRaises(ValueError):a.instruction(a.ENTRY+1,63)
    def test_pc_underflow_rejected(self):
        with self.assertRaises(ValueError):a.instruction(0,63)
    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError):a.strict(b'{"x":1,"x":2}')
    def test_json_nan(self):
        with self.assertRaises(ValueError):a.strict(b'{"x":NaN}')
    def test_oversize(self):
        with self.assertRaises(ValueError):a.strict(b' '* (a.MAX_TRACE_BYTES+1))
    def test_embedded_nul(self):
        with self.assertRaises(ValueError):a.strict(b'\0')
    def test_missing_summary(self):
        with self.assertRaises(ValueError):a.validate_trace(raw(self.rows[:-1]))
    def test_mismatched_hit_count(self):
        self.rows[-1]['hits']=2
        with self.assertRaises(ValueError):self.result()
    def test_bool_count_not_integer(self):
        self.rows[-1]['hits']=True
        with self.assertRaises(ValueError):self.result()
    def test_host_write_rejected(self):
        self.rows[-1]['host_memory_writes']=1
        with self.assertRaises(ValueError):self.result()
    def test_host_register_rejected(self):
        self.rows[-1]['host_register_writes']=1
        with self.assertRaises(ValueError):self.result()
    def test_host_function_rejected(self):
        self.rows[-1]['host_function_calls']=1
        with self.assertRaises(ValueError):self.result()
    def test_savestate_rejected(self):
        self.rows[-1]['savestate_loads']=1
        with self.assertRaises(ValueError):self.result()
    def test_no_acceptance_upgrade(self):
        self.rows[-1]['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):self.result()
    def test_injected_conditions_rejected(self):
        self.rows[0]['snapshot']['synchronous']=True;self.reject_call()
    def test_wrong_entry_rejected(self):self.rows[0]['raw_pc']+=2;self.reject_call()
    def test_wrong_isa_rejected(self):self.rows[0]['cpsr']=31;self.reject_call()
    def test_wrong_id_rejected(self):self.rows[0]['r0']=561;self.reject_call()
    def test_wrong_return_rejected(self):self.rows[-2]['raw_pc']+=2;self.reject_call()
    def test_unobserved_return_rejected(self):self.rows[-2]['returned']=False;self.reject_call()
    def test_wrong_sp_rejected(self):self.rows[-2]['sp']-=4;self.reject_call()
    def test_wrong_r4_rejected(self):self.rows[-2]['r4']=43;self.reject_call()
    def test_wrong_saved_lr_rejected(self):self.rows[-2]['saved_lr_word']+=2;self.reject_call()
    def test_wrong_saved_r4_rejected(self):self.rows[-2]['saved_r4_word']+=1;self.reject_call()
    def test_wrong_flag_rejected(self):self.rows[-2]['flag_byte_after']^=1;self.reject_call()
    def test_wrong_record_rejected(self):self.rows[-2]['record_word_after']^=1;self.reject_call()
    def test_wrong_counter_rejected(self):self.rows[-2]['counter_after']=0;self.reject_call()
    def test_wrong_pending_id_rejected(self):self.rows[-2]['pending_id_after']=0;self.reject_call()
    def test_mode_change_cannot_be_hidden(self):self.rows[2]['cpsr']=0x32;self.reject_call()
    def test_sp_min_cannot_be_fabricated(self):self.rows[-2]['minimum_sp']-=4;self.reject_call()
    def test_wrong_order_rejected(self):self.rows[2]['offset']=0;self.reject_call()
    def test_frame_alias_rejected(self):
        self.rows[0]['snapshot']['record_base']=self.rows[0]['snapshot']['sp']-40;self.reject_call()
    def test_unreadable_flag_rejected(self):self.rows[0]['flag_readable']=False;self.reject_call()
    def test_unreadable_record_rejected(self):self.rows[0]['record_readable']=False;self.reject_call()
    def test_hardware_sampling_is_not_synchrony_proof(self):
        self.rows[-2]['dma_disabled_at_step_boundaries']=False
        b=self.result()['bindings'][0];self.assertFalse(b['synchrony_proven'])
    def test_parser_does_not_mutate_caller_snapshot(self):
        before=copy.deepcopy(self.rows);self.result();self.assertEqual(self.rows,before)
    def test_warning_inside_call_rejected(self):self.rows[-2]['call_log_problems']=1;self.reject_call()
    def test_missing_warning_accounting_rejected(self):del self.rows[-2]['call_log_problems'];self.reject_call()
    def test_unobserved_reset_prefix_rejected(self):
        self.rows[-1]['unobserved_title_frames']=1200
        with self.assertRaises(ValueError):self.result()
    def test_c_logger_stays_off_trace_channel(self):
        text=(ROOT/a.SOURCE).read_text()
        self.assertIn('mLogSetDefaultLogger(&logger)',text)
        self.assertIn('vfprintf(stderr,format,args)',text)
    def test_read_only_c_driver(self):a.source_policy((ROOT/a.SOURCE).read_text())
    def test_write_surface_guard(self):
        with self.assertRaises(ValueError):a.source_policy((ROOT/a.SOURCE).read_text()+'c->writeRegister(c);')

if __name__=='__main__':unittest.main()
