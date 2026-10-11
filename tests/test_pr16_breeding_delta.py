"""Synthetic negatives only; actual daycare/hatch evidence is a separate job."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_breeding_delta as m
PP={0:0,39:30,84:30,175:15,273:10,344:15,440:20}
# 440:20 is a synthetic PP value, not a claim about ROM content. Native runs
# obtain it independently from hash-fixed parent and candidate physical tables.

class BreedingDeltaTests(unittest.TestCase):
    def record(self,api,name):
        v=api.expected_result(name)
        v.update(generation_steps=509,hatch_clock_start=22,hatch_steps=2793,
                 hatch_callback_frames=528,hatch_state_mask=(1<<6)|(1<<10),total_frames=200000,
                 witness={key:(i+1)*100 for i,key in enumerate(api.WITNESS)})
        return v

    def test_five_new_vectors_and_parent_validator_unchanged(self):
        api=m.configure(PP)
        self.assertEqual(len(api.CASES),5)
        for name in api.CASES:
            v=self.record(api,name)
            self.assertEqual(api.validate_result(json.dumps(v).encode(),name,0),v)
        self.assertEqual(api.expected_result('vega-lightball-full')['moves'],[175,440,273,344])
        self.assertEqual(api.expected_result('vega-both')['moves'],[39,84,440,0])
        self.assertEqual(api.expected_result('no-eligible-control')['moves'],[39,84,0,0])
        self.assertEqual(len(m.load().CASES),8)

    def test_every_observed_physical_stage_must_be_ordered(self):
        api=m.configure(PP);name='vega-father'
        for key in api.WITNESS:
            bad=self.record(api,name);bad['witness'][key]=0
            with self.subTest(key=key),self.assertRaises(ValueError):api.validate_result(json.dumps(bad).encode(),name,0)
        bad=self.record(api,name);bad['hatch_steps']-=1
        with self.assertRaises(ValueError):api.validate_result(json.dumps(bad).encode(),name,0)

    def test_identity_inheritance_cold_cores_and_guards_fail_closed(self):
        api=m.configure(PP);name='vega-mother';good=self.record(api,name)
        for key,value in [('rom_sha256','0'*64),('moves',[39,84,0,0]),('pp',[30,30,0,0]),
                          ('ordinary_deposit',False),('ordinary_claim',False),('native_hatch',False),
                          ('egg_and_hatched_save_reload',False),('fresh_cores',1),('host_write_barriers',0),
                          ('parent_queue_byte_identity',False),('total_save_counter_delta',2)]:
            with self.subTest(key=key),self.assertRaises(ValueError):api.validate_result(json.dumps(good|{key:value}).encode(),name,0)
        for code in (1,None,False,0.0):
            with self.assertRaises(ValueError):api.validate_result(json.dumps(good).encode(),name,code)

    def test_conditional_lightball_and_duplicate_not_generalized(self):
        api=m.configure(PP)
        for name in ('vega-lightball-full','vega-both'):
            bad=self.record(api,name);bad['moves']=[39,84,440,440]
            with self.assertRaises(ValueError):api.validate_result(json.dumps(bad).encode(),name,0)
        bad=self.record(api,'vega-lightball-full');bad['father_item']=0
        with self.assertRaises(ValueError):api.validate_result(json.dumps(bad).encode(),'vega-lightball-full',0)

    def test_exact_source_position_preservation_not_new_adoption(self):
        row={'form_key':'','move_id':440,'move_key':'MOVE_KEY_VEGA_440','route':'egg',
             'source_class':'CURRENT_PRESERVED','source_csv_line':273,'source_member':'egg_moves_final.csv',
             'source_parameters':{'order':'20'},'species_id':24,'species_key':'SPECIES_KEY_PICHU'}
        self.assertEqual(m.source_row({m.repaired.layer.LAYER:[row]}),row)
        for key,value in [('move_id',441),('source_csv_line',274),('source_class','NEW_ADOPTION'),('species_id',25)]:
            with self.subTest(key=key),self.assertRaises(ValueError):m.source_row({m.repaired.layer.LAYER:[row|{key:value}]})
        with self.assertRaises(ValueError):m.source_row({m.repaired.layer.LAYER:[row,row]})

    def test_bounded_projection_keeps_controller_and_saves(self):
        text=m.controller_source()
        self.assertIn(m.repaired.ROM_SHA,text)
        self.assertIn('No injected scripts/specials/steps/egg flags below',text)
        self.assertIn('b_trace.hatch_reloaded',text)
        self.assertIn('b_native_hatch_saves==1U',text)
        self.assertIn('b_snapshot_check(c,&egg)',text)
        self.assertIn('b_snapshot_check(c,&hatched)',text)
        with patch.object(m,'PARENT_C_SHA','0'*64),self.assertRaises(ValueError):m.controller_source()
        with self.assertRaises(ValueError):m.replace_once('a a','a','b')

if __name__=='__main__':unittest.main()
