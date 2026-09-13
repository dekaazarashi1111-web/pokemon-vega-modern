"""P06既決2件の狭い採用契約と、実ROM観測を誤って成功にしない回帰試験。"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
import run_modernization_p06_decided_e2e as run
import modernization_p06_decided_adjustments as recipe

class ResultTests(unittest.TestCase):
    def setUp(self):
        # Local native log is a parser template only; unittest is not a fresh ROM run.
        self.raw=(ROOT/'tests/fixtures/p06_decided_native_template.json').read_bytes()
        self.row=json.loads(self.raw)
    def test_original_observation(self):
        self.assertEqual(run.validate(self.raw,(373,0,0),0)['final_stats'][1],44)
    def test_exit_bool_is_not_zero(self):
        with self.assertRaises(ValueError):run.validate(self.raw,(373,0,0),False)
    def test_nonzero_exit(self):
        for code in (-9,1,2):
            with self.subTest(code=code),self.assertRaises(ValueError):run.validate(self.raw,(373,0,0),code)
    def test_reject_each_fixed_field_change(self):
        keys='schema_version status scope parent_sha256 candidate_sha256 species slot mode ability_before ability_loaded ability_final initial_level final_level save_counter_delta normal_save_menu fresh_core_count cross_rom_100_bytes_equal candidate_cold_100_bytes_equal slot_preserved host_write_barriers native_creation_is_fixture ability_read_uses_native_abi full_p06_acceptance release_ready warnings_errors'.split()
        for k in keys:
            row=copy.deepcopy(self.row)
            row[k]=(not row[k]) if type(row[k]) is bool else (row[k]+1 if type(row[k]) is int else row[k]+'x')
            with self.subTest(field=k),self.assertRaises(ValueError):run.validate(json.dumps(row).encode(),(373,0,0),0)
    def test_false_numeric_fields(self):
        for key in ('schema_version','slot','mode','personality','bag_party_frame','level_up_frame','field_frame'):
            row=copy.deepcopy(self.row);row[key]=False
            with self.subTest(key=key),self.assertRaises(ValueError):run.validate(json.dumps(row).encode(),(373,0,0),0)
    def test_stats_formula_rejects_unapplied_attack(self):
        row=copy.deepcopy(self.row);row['final_stats'][1]=70
        with self.assertRaises(ValueError):run.validate(json.dumps(row).encode(),(373,0,0),0)
    def test_each_stat_array_rejects_bool(self):
        for key in ('ivs','evs','initial_stats','loaded_stats','final_stats'):
            row=copy.deepcopy(self.row);row[key][0]=False
            with self.subTest(key=key),self.assertRaises(ValueError):run.validate(json.dumps(row).encode(),(373,0,0),0)
    def test_cold_cache_is_not_magically_recalculated(self):
        row=copy.deepcopy(self.row);row['loaded_stats']=row['final_stats']
        with self.assertRaises(ValueError):run.validate(json.dumps(row).encode(),(373,0,0),0)
    def test_missing_schema_field(self):
        row=copy.deepcopy(self.row);del row['slot_preserved']
        with self.assertRaises(ValueError):run.validate(json.dumps(row).encode(),(373,0,0),0)
    def test_unknown_schema_field(self):
        row=copy.deepcopy(self.row);row['made_up_pass']=True
        with self.assertRaises(ValueError):run.validate(json.dumps(row).encode(),(373,0,0),0)
    def test_duplicate_json_key(self):
        raw=self.raw.strip()[:-1]+b',"slot":0}'
        with self.assertRaises(ValueError):run.validate(raw,(373,0,0),0)
    def test_two_json_documents(self):
        with self.assertRaises(ValueError):run.validate(self.raw+self.raw,(373,0,0),0)
    def test_nonfinite(self):
        raw=self.raw.replace(b'2229930865',b'NaN')
        with self.assertRaises(ValueError):run.validate(raw,(373,0,0),0)
    def test_phase_order(self):
        for key in ('bag_party_frame','level_up_frame','field_frame'):
            row=copy.deepcopy(self.row);row[key]=0
            with self.subTest(key=key),self.assertRaises(ValueError):run.validate(json.dumps(row).encode(),(373,0,0),0)
        row=copy.deepcopy(self.row);row['level_up_frame']=row['bag_party_frame']
        with self.assertRaises(ValueError):run.validate(json.dumps(row).encode(),(373,0,0),0)
    def test_mon_snapshot_change(self):
        for offset in (0,32,44,52,68,84,88,90):
            row=copy.deepcopy(self.row);b=bytearray.fromhex(row['after_mon_hex']);b[offset]^=1;row['after_mon_hex']=b.hex()
            with self.subTest(offset=offset),self.assertRaises(ValueError):run.validate(json.dumps(row).encode(),(373,0,0),0)
    def test_snapshot_not_hex(self):
        row=copy.deepcopy(self.row);row['after_mon_hex']='z'*200
        with self.assertRaises(ValueError):run.validate(json.dumps(row).encode(),(373,0,0),0)
    def test_native_migration_has_all_case_pairs(self):
        self.assertEqual(len(run.CASES),8);self.assertEqual(len(set(run.CASES)),8)
    def test_unknown_case(self):
        with self.assertRaises(ValueError):run.validate(self.raw,(373,2,0),0)

class SpecTests(unittest.TestCase):
    def test_recovered_decisions_are_exactly_two(self):
        c=recipe.specification();self.assertEqual(c['adoption']['adopted_delta_count'],2)
        self.assertTrue(c['adoption']['runtime_patch_authorized'])
        self.assertFalse(c['policy']['release_ready'])
    def test_original_checkpoint_stays_zero(self):
        c=recipe.specification();p=ROOT/c['historical_contract']['path'];history=json.loads(p.read_text())
        self.assertEqual(history['adoption']['adopted_delta_count'],0)
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),c['historical_contract']['sha256'])
    def test_parent_not_patched_without_exact_identity(self):
        for data in (b'',bytes(1024),bytearray(1024)):
            with self.subTest(size=len(data)),self.assertRaises(ValueError):recipe.build(data)
    def test_more_adjustments_cannot_be_inferred(self):
        original=recipe.strict_json;value=recipe.specification();value['adoption']['records'].append(copy.deepcopy(value['adoption']['records'][0]))
        with patch.object(recipe,'strict_json',return_value=value),self.assertRaises(ValueError):recipe.specification()
    def test_change_hidden_slot_is_not_adopted(self):
        value=recipe.specification();value['adoption']['records'][0]['changes'][1]['field']='ability.hidden'
        with patch.object(recipe,'strict_json',return_value=value),self.assertRaises(ValueError):recipe.specification()
    def test_different_attack_not_adopted(self):
        value=recipe.specification();value['adoption']['records'][1]['changes'][0]['after']=44
        with patch.object(recipe,'strict_json',return_value=value),self.assertRaises(ValueError):recipe.specification()
    def test_other_form_not_adopted(self):
        value=recipe.specification();value['adoption']['records'][0]['form_key']='FORM_KEY_MEGA'
        with patch.object(recipe,'strict_json',return_value=value),self.assertRaises(ValueError):recipe.specification()
    def test_no_authorization(self):
        value=recipe.specification();value['adoption']['runtime_patch_authorized']=False
        with patch.object(recipe,'strict_json',return_value=value),self.assertRaises(ValueError):recipe.specification()
    def test_source_tampering(self):
        real=recipe.safe_read
        def bad(root,name):
            b=real(root,name)
            return b+b'\n' if name.startswith('design/imported/') else b
        with patch.object(recipe,'safe_read',side_effect=bad),self.assertRaises(ValueError):recipe.specification()
    def test_duplicate_spec_json(self):
        with self.assertRaises(ValueError):recipe.strict_json(b'{"a":1,"a":2}')
    def test_safe_path_rejects_escape(self):
        for name in ('../README.md','/etc/passwd'):
            with self.subTest(name=name),self.assertRaises(ValueError):recipe.safe_read(ROOT,name)
    def test_embed_unique_only(self):
        s='int main(int argc,char**argv){return 0;}'
        self.assertEqual(run.embed(s,'old_main'),'int old_main(int argc,char**argv){return 0;}')
        for invalid in ('',s+s):
            with self.assertRaises(ValueError):run.embed(invalid,'old_main')
    def test_output_cleanup_is_scoped(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.local') as t:
            p=Path(t);(p/'result.json').write_text('old PASS');(p/'job.stdout.json').write_text('workflow')
            run.output_dir(p)
            self.assertFalse((p/'result.json').exists());self.assertEqual((p/'job.stdout.json').read_text(),'workflow')
    def test_timeout_cannot_pass(self):
        with self.assertRaises(ValueError):run.capture_api.require_exited({'timed_out':True,'spawn_error':None,'returncode':0})
    def test_spawn_failure_cannot_pass(self):
        with self.assertRaises(ValueError):run.capture_api.require_exited({'timed_out':False,'spawn_error':'missing','returncode':0})
    def test_unchanged_other_stats_formula(self):
        self.assertEqual(run.stats(220,48,False,0,[0]*6,[0]*6),run.stats(220,48,True,0,[0]*6,[0]*6))
        before=run.stats(373,48,False,0,[0]*6,[0]*6);after=run.stats(373,48,True,0,[0]*6,[0]*6)
        self.assertEqual([i for i,(a,b) in enumerate(zip(before,after)) if a!=b],[1])

if __name__=='__main__':unittest.main()
