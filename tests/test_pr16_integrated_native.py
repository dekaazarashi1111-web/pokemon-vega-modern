"""Synthetic adapter checks only; no emulator success is fabricated here."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_integrated_native as m
import run_modernization_p03_relearner_e2e as historical
PROCESS={'schema_version':1,'returncode':0,'timed_out':False,'spawn_error':None}
class NativeBinding(unittest.TestCase):
    def test_old_validator_and_vectors_are_unchanged(self):
        api=m.validator()
        self.assertEqual(api.ROM_SHA,m.ROM_SHA)
        self.assertNotEqual(historical.ROM_SHA,m.ROM_SHA)
        self.assertEqual(len(historical.vectors()),46)
    def test_old_rom_success_cannot_pass_new_identity(self):
        api=m.validator();c=api.vectors()[0]
        value=api.expected_result(c)
        w={k:0 for k in api.WITNESS};w.update(bag=10,mode_menu=20,mode_choice=30,party=40,list=50,ask=60,delete_ask=70,summary=80,selection=90,replaced=100,learned=110,field=1000)
        value['witness']=w
        api.validate_result(json.dumps(value).encode(),c,PROCESS)
        for key,wrong in [('rom_sha256',historical.ROM_SHA),('normal_save_menu',False),('fresh_core_normal_continue',False),('save_counter_delta',0),('host_write_barriers',0)]:
            mutated=dict(value);mutated[key]=wrong
            with self.subTest(key=key),self.assertRaises(ValueError):api.validate_result(json.dumps(mutated).encode(),c,PROCESS)
        with self.assertRaises(ValueError):api.validate_result(json.dumps(value).encode(),c,PROCESS|{'timed_out':True})
    def test_cancel_retains_every_slot_pp_and_ppup(self):
        c=m.make_case(m.SPECS[2],[1,457],20)
        self.assertEqual(c['known'],c['after']);self.assertEqual(c['pp_before'],c['pp_after'])
        self.assertEqual(c['pp_bonuses_before'],c['pp_bonuses_after']);self.assertEqual(c['canonical_pp'],0)
    def test_empty_changes_only_first_empty_slot(self):
        c=m.make_case(m.SPECS[0],[1,457],20)
        self.assertEqual(c['after'],[33,81,457,0]);self.assertEqual(c['pp_after'],[7,8,20,0]);self.assertEqual(c['pp_bonuses_after'],197)
    def test_missing_target_or_capacity_cannot_be_skipped(self):
        for pool in ([1,2],list(range(400,470))):
            with self.assertRaises(ValueError):m.make_case(m.SPECS[0],pool,20)
    def test_reproduced_hook_offset_typo(self):
        self.assertEqual(m.layer.MEMORY_HOOK,0x091141D4-0x08000000)
        self.assertNotEqual(m.layer.MEMORY_HOOK,0x1141D4)
if __name__=='__main__':unittest.main()
