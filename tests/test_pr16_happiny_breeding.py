"""Synthetic fail-closed tests; never substitutes for native daycare evidence."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_happiny_breeding as m
# Synthetic PP values isolate the validator; actual execution reads hash-fixed ROM.
PP={0:0,1:35,539:10,461:5,464:10,357:10,204:20,343:25,549:15}

class HappinyBreedingTests(unittest.TestCase):
    def record(self,api,name):
        value=api.expected_result(name)
        value.update(generation_steps=511,hatch_clock_start=22,hatch_steps=41*256-23,
                     hatch_callback_frames=528,hatch_state_mask=(1<<6)|(1<<10),total_frames=450000,
                     witness={key:(i+1)*100 for i,key in enumerate(api.WITNESS)})
        return value

    def test_five_new_cases_preserve_independent_incense_and_no_incense_results(self):
        api=m.configure(PP)
        self.assertEqual(len(api.CASES),5)
        for name in api.CASES:
            value=self.record(api,name)
            self.assertEqual(api.validate_result(json.dumps(value).encode(),name,0),value)
        self.assertEqual(api.expected_result('three-retained-full')['moves'],[539,461,464,357])
        self.assertEqual(api.expected_result('no-incense-chansey')['child_species'],365)
        self.assertEqual(api.expected_result('no-incense-chansey')['moves'],[204,343,539,549])
        self.assertEqual(api.expected_result('mother-incense-first')['mother_item'],862)
        self.assertEqual(api.expected_result('father-incense-middle')['father_item'],862)
        self.assertEqual(len(m.prior.load().CASES),8)
        self.assertEqual(m.prior.load().expected_result('both-parents')['initial_egg_cycles'],10)

    def test_all_physical_stages_and_exact_forty_cycle_walk_required(self):
        api=m.configure(PP);name='three-retained-full'
        for key in api.WITNESS:
            bad=self.record(api,name);bad['witness'][key]=0
            with self.subTest(key=key),self.assertRaises(ValueError):api.validate_result(json.dumps(bad).encode(),name,0)
        for steps in (2793,0,41*256-24,41*256-22):
            bad=self.record(api,name);bad['hatch_steps']=steps
            with self.assertRaises(ValueError):api.validate_result(json.dumps(bad).encode(),name,0)

    def test_identity_species_pp_incense_cores_guards_and_scoped_flags_fail_closed(self):
        api=m.configure(PP);name='mother-incense-first';good=self.record(api,name)
        for key,value in [('rom_sha256','0'*64),('child_species',24),('child_species',365),
                          ('initial_egg_cycles',10),('mother_item',648),('mother_item',0),
                          ('moves',[1,539,0,0]),('pp',[35,10,0,0]),('ordinary_deposit',False),
                          ('ordinary_claim',False),('native_hatch',False),('egg_and_hatched_save_reload',False),
                          ('fresh_cores',1),('host_write_barriers',0),('parent_queue_byte_identity',False),
                          ('total_save_counter_delta',2),('release_ready',True),('warnings_errors',1)]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                api.validate_result(json.dumps(good|{key:value}).encode(),name,0)
        for code in (1,None,False,0.0):
            with self.assertRaises(ValueError):api.validate_result(json.dumps(good).encode(),name,code)

    def test_no_incense_cannot_be_relabelled_as_a_baby_success(self):
        api=m.configure(PP);name='no-incense-chansey';bad=self.record(api,name)
        bad['child_species']=364;bad['moves']=[539,461,464,357]
        with self.assertRaises(ValueError):api.validate_result(json.dumps(bad).encode(),name,0)
        bad=self.record(api,name);bad['father_item']=862
        with self.assertRaises(ValueError):api.validate_result(json.dumps(bad).encode(),name,0)

    def test_exact_source_rows_not_new_adoption_or_duplicates(self):
        rows=[dict(form_key='',move_id=move,move_key='MOVE_KEY_VEGA_'+str(move),route='egg',
                   source_class='CURRENT_PRESERVED',source_csv_line=line,source_member='egg_moves_final.csv',
                   source_parameters={'order':order},species_id=364,species_key='SPECIES_KEY_HAPPINY')
              for move,line,order in m.SOURCE_ROWS]
        self.assertEqual(m.source_rows({m.repaired.layer.LAYER:rows}),rows)
        for key,value in [('source_csv_line',3853),('source_class','NEW_ADOPTION'),('species_id',365),('move_id',462)]:
            bad=deepcopy(rows);bad[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.source_rows({m.repaired.layer.LAYER:bad})
        with self.assertRaises(ValueError):m.source_rows({m.repaired.layer.LAYER:rows+rows[:1]})

    def test_bounded_controller_projection_does_not_remove_save_or_write_guards(self):
        text=m.controller_source()
        self.assertIn(m.repaired.ROM_SHA,text)
        self.assertIn('No injected scripts/specials/steps/egg flags below',text)
        self.assertIn('z<12288U && !b_hatched',text)
        self.assertIn('initial_cycles==40U',text)
        self.assertIn('b_snapshot_check(c,&egg)',text);self.assertIn('b_snapshot_check(c,&hatched)',text)
        self.assertIn('b_native_hatch_saves==1U',text)
        self.assertNotIn('b_data(c,B_CHILD,11U)==24U',text)
        with patch.object(m.prior,'PARENT_C_SHA','0'*64),self.assertRaises(ValueError):m.controller_source()
        with patch.object(m.prior,'PARENT_SHA','0'*64),self.assertRaises(ValueError):m.validator_source()

    def test_bad_json_extra_fields_duplicate_keys_and_boolean_counters_rejected(self):
        api=m.configure(PP);name='incense-no-eligible';good=self.record(api,name)
        for raw in (json.dumps(good|{'unexpected':1}).encode(),b'{}',b'{"status":"PASS","status":"PASS"}',
                    json.dumps(good|{'generation_steps':True}).encode()):
            with self.assertRaises(ValueError):api.validate_result(raw,name,0)

if __name__=='__main__':unittest.main()
