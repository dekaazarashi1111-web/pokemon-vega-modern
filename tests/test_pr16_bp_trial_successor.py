"""Source-only tests for the new four-byte successor and its distinct receipt."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_bp_trial_successor as layer
import pr16_bp_trial_native as native

class EdgeTests(unittest.TestCase):
    def test_exact_pointer_only_and_original_immutable(self):
        original=b'head'+layer.BEFORE+b'tail'
        changed=layer.replace_edge(original,4,layer.BEFORE,layer.AFTER)
        self.assertEqual(changed,b'head'+layer.AFTER+b'tail')
        self.assertEqual(original,b'head'+layer.BEFORE+b'tail')
        self.assertEqual(sum(a!=b for a,b in zip(original,changed)),3)
    def test_reapplication_rejected(self):
        with self.assertRaises(ValueError):layer.replace_edge(layer.AFTER,0,layer.BEFORE,layer.AFTER)
    def test_wrong_preimage_rejected(self):
        with self.assertRaises(ValueError):layer.replace_edge(b'xxxx',0,layer.BEFORE,layer.AFTER)
    def test_bool_offset_rejected(self):
        with self.assertRaises(ValueError):layer.replace_edge(layer.BEFORE,False,layer.BEFORE,layer.AFTER)
    def test_negative_offset_rejected(self):
        with self.assertRaises(ValueError):layer.replace_edge(layer.BEFORE,-1,layer.BEFORE,layer.AFTER)
    def test_truncation_rejected(self):
        with self.assertRaises(ValueError):layer.replace_edge(layer.BEFORE[:3],0,layer.BEFORE,layer.AFTER)
    def test_resize_rejected(self):
        with self.assertRaises(ValueError):layer.replace_edge(layer.BEFORE,0,layer.BEFORE,b'a')
    def test_mutable_input_rejected(self):
        with self.assertRaises(ValueError):layer.replace_edge(bytearray(layer.BEFORE),0,layer.BEFORE,layer.AFTER)
    def test_noop_rejected(self):
        with self.assertRaises(ValueError):layer.replace_edge(layer.BEFORE,0,layer.BEFORE,layer.BEFORE)
    def test_nonparent_rom_rejected(self):
        with self.assertRaises(ValueError):layer.build(b'',{})
    def test_allocation_only_owner_rebound(self):
        before=b'aaaa'+layer.BEFORE+b'bbbb';after=layer.replace_edge(before,4,layer.BEFORE,layer.AFTER)
        rows=[dict(sequence=i,start=a,end_exclusive=b,size=b-a,content_sha256=layer.identity(before[a:b])['sha256']) for i,(a,b) in enumerate(((0,4),(4,8),(8,12)))]
        original=dict(summaries=dict(overlap_count=0),allocations=rows);saved=copy.deepcopy(original)
        with patch.object(layer,'OFFSET',4):result=layer.allocations(before,after,original)
        self.assertEqual(original,saved);self.assertEqual(result['allocations'][0],rows[0]);self.assertEqual(result['allocations'][2],rows[2])
        self.assertNotEqual(result['allocations'][1]['content_sha256'],rows[1]['content_sha256'])
    def test_missing_owner_rejected(self):
        plan=dict(summaries=dict(overlap_count=0),allocations=[])
        with self.assertRaises(ValueError):layer.allocations(b'aa',b'aa',plan)

class ReceiptTests(unittest.TestCase):
    def sample(self):
        row=native.expected();row.update(save_counter_before=2,save_counter_before_manual=2,save_counter_after=3,total_frames=90,
            witness={key:10*(i+1) for i,key in enumerate(native.control.TRACE)})
        return row
    def validate(self,row):
        return native.validate(json.dumps(row).encode(),b'BP_CTRL label=fixture \nBP_CTRL label=returned \n',0)
    def test_distinct_successor_contract(self):
        row=self.validate(self.sample());self.assertEqual(row['candidate_sha256'],layer.SHA)
        self.assertFalse(row['physical_bp_earning_accepted']);self.assertFalse(row['p05_native_bp_gap_closed'])
    def test_parent_rom_rejected(self):
        row=self.sample();row['candidate_sha256']=layer.route.SHA
        with self.assertRaises(ValueError):self.validate(row)
    def test_legacy_scope_rejected(self):
        row=self.sample();row['scope']=native.control.SCOPE
        with self.assertRaises(ValueError):self.validate(row)
    def test_missing_fresh_core_rejected(self):
        row=self.sample();row['fresh_cores']=1
        with self.assertRaises(ValueError):self.validate(row)
    def test_save_counter_rejected(self):
        row=self.sample();row['save_counter_after']=2
        with self.assertRaises(ValueError):self.validate(row)
    def test_missing_lifecycle_rejected(self):
        row=self.sample();row['witness']['rentals']=0
        with self.assertRaises(ValueError):self.validate(row)
    def test_bool_frames_rejected(self):
        row=self.sample();row['total_frames']=True
        with self.assertRaises(ValueError):self.validate(row)
    def test_unearned_bp_claim_rejected(self):
        row=self.sample();row['physical_bp_earning_accepted']=True
        with self.assertRaises(ValueError):self.validate(row)
    def test_nonzero_process_rejected(self):
        with self.assertRaises(ValueError):native.validate(json.dumps(self.sample()).encode(),b'',1)
    def test_barrier_count_rejected(self):
        row=self.sample();row['host_write_barriers']=6
        with self.assertRaises(ValueError):self.validate(row)
    def test_ambiguous_source_transform_rejected(self):
        with self.assertRaises(ValueError):native.transform('old old','old','new')
    def test_prior_source_pin_retained(self):
        self.assertEqual(layer.identity((ROOT/native.control.SOURCE).read_bytes())['sha256'],native.C_SOURCE_SHA)
        self.assertEqual(layer.identity((ROOT/native.control.SELF).read_bytes())['sha256'],native.PY_SOURCE_SHA)
