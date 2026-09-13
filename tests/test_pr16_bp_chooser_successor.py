"""Focused source/negative receipt tests, not emulator or physical acceptance."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_bp_chooser_successor as layer
import pr16_bp_chooser_native as native

class OperandTests(unittest.TestCase):
    def test_one_byte_only(self):
        original=b'head'+layer.BEFORE+b'tail'
        changed=layer.replace_operand(original,4,layer.BEFORE,layer.AFTER)
        self.assertEqual(changed,b'head'+layer.AFTER+b'tail')
        self.assertEqual(original,b'head'+layer.BEFORE+b'tail')
        self.assertEqual(sum(a!=b for a,b in zip(original,changed)),1)
    def test_wrong_preimage(self):
        with self.assertRaises(ValueError):layer.replace_operand(b'xx',0,layer.BEFORE,layer.AFTER)
    def test_reapplication(self):
        with self.assertRaises(ValueError):layer.replace_operand(layer.AFTER,0,layer.BEFORE,layer.AFTER)
    def test_bool_offset(self):
        with self.assertRaises(ValueError):layer.replace_operand(layer.BEFORE,False,layer.BEFORE,layer.AFTER)
    def test_negative_offset(self):
        with self.assertRaises(ValueError):layer.replace_operand(layer.BEFORE,-1,layer.BEFORE,layer.AFTER)
    def test_truncation(self):
        with self.assertRaises(ValueError):layer.replace_operand(b'\x2f',0,layer.BEFORE,layer.AFTER)
    def test_resize(self):
        with self.assertRaises(ValueError):layer.replace_operand(layer.BEFORE,0,layer.BEFORE,b'\x29')
    def test_mutable(self):
        with self.assertRaises(ValueError):layer.replace_operand(bytearray(layer.BEFORE),0,layer.BEFORE,layer.AFTER)
    def test_noop(self):
        with self.assertRaises(ValueError):layer.replace_operand(layer.BEFORE,0,layer.BEFORE,layer.BEFORE)
    def test_nonparent(self):
        with self.assertRaises(ValueError):layer.binding(b'')
    def test_owner_hash_only(self):
        a=b'aaaa'+layer.BEFORE+b'bbbb';b=layer.replace_operand(a,4,layer.BEFORE,layer.AFTER)
        rows=[dict(sequence=i,start=x,end_exclusive=y,size=y-x,content_sha256=layer.identity(a[x:y])['sha256']) for i,(x,y) in enumerate(((0,4),(4,6),(6,10)))]
        plan=dict(summaries=dict(overlap_count=0),allocations=rows);saved=copy.deepcopy(plan)
        with patch.object(layer,'OFFSET',4):out=layer.allocations(a,b,plan)
        self.assertEqual(plan,saved);self.assertEqual(out['allocations'][0],rows[0]);self.assertEqual(out['allocations'][2],rows[2])
        self.assertNotEqual(out['allocations'][1]['content_sha256'],rows[1]['content_sha256'])
    def test_no_owner(self):
        with self.assertRaises(ValueError):layer.allocations(b'aa',b'aa',dict(summaries=dict(overlap_count=0),allocations=[]))

class ReceiptTests(unittest.TestCase):
    SHA='0'*64
    def sample(self):
        row=native.expected(self.SHA);row.update(save_counter_before=2,save_counter_before_manual=2,save_counter_after=3,total_frames=90,witness={k:10*(i+1) for i,k in enumerate(native.control.TRACE)})
        return row
    def validate(self,row):return native.validate(json.dumps(row).encode(),b'BP_CTRL label=fixture \nBP_CTRL label=returned \n',0,self.SHA)
    def test_distinct_output(self):
        row=self.validate(self.sample());self.assertEqual(row['candidate_sha256'],self.SHA)
        self.assertFalse(row['physical_bp_earning_accepted']);self.assertFalse(row['p05_native_bp_gap_closed'])
    def test_predecessor_not_output(self):
        for sha in (layer.PARENT_SHA,layer.parent_layer.route.SHA):
            with self.assertRaises(ValueError):native.expected(sha)
    def test_unbound_output(self):
        row=self.sample();row['candidate_sha256']='1'*64
        with self.assertRaises(ValueError):self.validate(row)
    def test_legacy_scope(self):
        row=self.sample();row['scope']=native.control.SCOPE
        with self.assertRaises(ValueError):self.validate(row)
    def test_missing_cold_core(self):
        row=self.sample();row['fresh_cores']=1
        with self.assertRaises(ValueError):self.validate(row)
    def test_save_counter(self):
        row=self.sample();row['save_counter_after']=2
        with self.assertRaises(ValueError):self.validate(row)
    def test_missing_lifecycle(self):
        row=self.sample();row['witness']['rentals']=0
        with self.assertRaises(ValueError):self.validate(row)
    def test_bool_frames(self):
        row=self.sample();row['total_frames']=True
        with self.assertRaises(ValueError):self.validate(row)
    def test_unearned_claim(self):
        row=self.sample();row['physical_bp_earning_accepted']=True
        with self.assertRaises(ValueError):self.validate(row)
    def test_nonzero_exit(self):
        with self.assertRaises(ValueError):native.validate(json.dumps(self.sample()).encode(),b'',1,self.SHA)
    def test_barrier_count(self):
        row=self.sample();row['host_write_barriers']=6
        with self.assertRaises(ValueError):self.validate(row)
    def test_prior_source_pins(self):
        self.assertEqual(layer.identity((ROOT/native.control.SOURCE).read_bytes())['sha256'],native.C_SOURCE_SHA)
        self.assertEqual(layer.identity((ROOT/native.control.SELF).read_bytes())['sha256'],native.PY_SOURCE_SHA)
    def test_ambiguous_transform(self):
        with self.assertRaises(ValueError):native.transform('old old','old','new')
    def test_timeout_unchanged(self):
        text=(ROOT/native.SELF).read_text();self.assertIn('],out/CASE,900)',text)
        self.assertNotIn('continue-on-error',text)

if __name__=='__main__':unittest.main()
