"""Negative contract tests; fabricated unit vectors are not emulator evidence."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_evolution_fullslots as m
PROCESS = {'schema_version': 1, 'returncode': 0, 'timed_out': False, 'spawn_error': None}

class EvolutionFullSlotsTests(unittest.TestCase):
    def record(self, api, case):
        v = api.expected(case)
        v['witness'] = dict(bag_party=10, level=20, evo_begin=30, evo_update=40,
                            dialog=50, summary=60, selection=70,
                            stop=80 if case[-1] == 3 else 0, downs=1, field=100)
        return v

    def test_frozen_projection_and_new_cases(self):
        text = m.controller_source()
        self.assertIn('read32(c,task)==0x080CF9F9U', text)
        self.assertIn('read16(c,task+22)==(stop?11:5)', text)
        self.assertIn('read16(c,task+24)==(stop?0:10)', text)
        self.assertNotIn('write', m.OBSERVER)
        self.assertNotIn('call_preserving', m.OBSERVER)
        self.assertNotIn('taillow-level-', text)
        self.assertIn('a_guard(c);a_require(a_save(c)', text)
        self.assertIn('!memcmp(learned,cold,100)', text)
        for case in m.CASES:
            self.assertIn(case[0], text)

    def test_both_cases_keep_exact_slots_pp_and_evolved_species(self):
        api = m.module()
        for case in m.CASES:
            v = self.record(api, case)
            self.assertEqual(api.validate(json.dumps(v).encode(), case, PROCESS), v)
        accepted = api.expected(m.CASES[0])
        canceled = api.expected(m.CASES[1])
        self.assertEqual(accepted['moves_after'], [33,366,45,52])
        self.assertEqual(accepted['pp_after'], [7,20,9,10])
        self.assertEqual(accepted['pp_bonuses_after'], 225)
        self.assertEqual(canceled['moves_after'], [33,81,45,52])
        self.assertEqual(canceled['pp_bonuses_after'], 229)
        self.assertEqual(canceled['species_after'], 13)

    def test_prompt_cannot_precede_evolution_or_skip_summary_cancel(self):
        api = m.module()
        for case in m.CASES:
            for key,value in [('dialog',25),('summary',0),('selection',0),('evo_update',0),('field',70)]:
                bad = self.record(api, case);bad['witness'][key] = value
                with self.subTest(case=case[0],key=key), self.assertRaises(ValueError):
                    api.validate(json.dumps(bad).encode(), case, PROCESS)
        bad = self.record(api,m.CASES[1]);bad['witness']['stop'] = 0
        with self.assertRaises(ValueError):api.validate(json.dumps(bad).encode(),m.CASES[1],PROCESS)

    def test_process_save_identity_and_guards_fail_closed(self):
        api = m.module();case=m.CASES[0];v=self.record(api,case)
        for key,value in [('rom_sha256','0'*64),('cold_continue',False),('normal_save_menu',False),
                          ('fresh_cores',1),('host_write_barriers',2),('save_counter_delta',0),
                          ('pp_after',[7,8,9,10]),('party_mon_bytes_preserved',99)]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                api.validate(json.dumps(v|{key:value}).encode(),case,PROCESS)
        for process in (PROCESS|{'returncode':1},PROCESS|{'timed_out':True}):
            with self.assertRaises(ValueError):api.validate(json.dumps(v).encode(),case,process)
        with self.assertRaises(ValueError):api.validate(json.dumps(v).encode(),case,PROCESS,b'mGBA[warn]')

    def test_controller_drift_is_rejected(self):
        with patch.object(m,'PARENT_C_SHA','0'*64),self.assertRaises(ValueError):m.controller_source()
        with self.assertRaises(ValueError):m.replace_once('a a','a','b')

if __name__=='__main__':unittest.main()
