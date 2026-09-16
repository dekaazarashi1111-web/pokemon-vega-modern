"""Synthetic validator regressions. These are not emulator success evidence."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_modernization_p03_relearner_e2e as subject

GOOD_PROCESS = {'schema_version': 1, 'returncode': 0, 'timed_out': False, 'spawn_error': None}


def fixture(c):
    r = deepcopy(subject.expected_result(c))
    w = {k: 0 for k in subject.WITNESS}
    w.update(bag=10, mode_menu=20, mode_choice=30, field=1000)
    a = c['action']
    if a == 8:
        w['denied'] = 60
        if c['denial_text'] in (0x092D06C6, 0x092D0688):
            w['party'] = 40
    else:
        w.update(party=40, list=50)
        if a < 4:
            w['ask'] = 60
        if a in (0, 3):
            w.update(delete_ask=70, summary=80, selection=90)
        if a == 0:
            w.update(replaced=100, learned=110)
        elif a == 1:
            w['learned'] = 70
        elif a in (2, 3, 4):
            w['giveup'] = 120
    r['witness'] = w
    return r


class Results(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = subject.vectors()

    def check(self, value, case=0, process=None, stderr=b''):
        return subject.validate_result(json.dumps(value).encode(), self.cases[case], process or deepcopy(GOOD_PROCESS), stderr)

    def reject(self, mutate, case=0):
        r = fixture(self.cases[case]); mutate(r)
        with self.assertRaises(ValueError):
            self.check(r, case)

    def test_all_46_synthetic_contracts(self):
        for i, c in enumerate(self.cases):
            with self.subTest(name=c['name']):
                self.check(fixture(c), i)

    def test_boolean_exit_zero_rejected(self):
        with self.assertRaises(ValueError):
            self.check(fixture(self.cases[0]), process=GOOD_PROCESS | {'returncode': False})

    def test_nonzero_exit_rejected(self):
        for code in (-11, 1, 2, 9, None, '0', 0.0):
            with self.subTest(code=code), self.assertRaises(ValueError):
                self.check(fixture(self.cases[0]), process=GOOD_PROCESS | {'returncode': code})

    def test_timeout_overrides_pass_output(self):
        with self.assertRaises(ValueError):
            self.check(fixture(self.cases[0]), process=GOOD_PROCESS | {'timed_out': True})

    def test_spawn_failure_overrides_pass_output(self):
        with self.assertRaises(ValueError):
            self.check(fixture(self.cases[0]), process=GOOD_PROCESS | {'spawn_error': 'missing executable'})

    def test_duplicate_json_rejected(self):
        r = json.dumps(fixture(self.cases[0]))
        raw = ('{"status":"PASS",' + r[1:]).encode()
        with self.assertRaises(ValueError):
            subject.validate_result(raw, self.cases[0], GOOD_PROCESS)

    def test_malformed_json_rejected(self):
        for raw in (b'', b'PASS', b'{}{}', b'null', b'[]', b'{"nan":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                subject.validate_result(raw, self.cases[0], GOOD_PROCESS)

    def test_missing_result_key(self):
        self.reject(lambda r: r.pop('mode_reset'))

    def test_extra_result_key(self):
        self.reject(lambda r: r.update(unrelated=True))

    def test_incorrect_scope(self):
        self.reject(lambda r: r.update(scope='P03_ARCHIVE_NATIVE_UI_SAVE_RELOAD'))

    def test_wrong_rom(self):
        self.reject(lambda r: r.update(rom_sha256='0' * 64))

    def test_wrong_case(self):
        self.reject(lambda r: r.update(case='another-case'))

    def test_float_and_boolean_frame_rejected(self):
        for v in (False, True, 1.0, -1, 24001, '1'):
            with self.subTest(value=v):
                self.reject(lambda r: r['witness'].update(bag=v))

    def test_boolean_integer_fields_rejected(self):
        self.reject(lambda r: r.update(mirror_herb_after=False))
        self.reject(lambda r: r['pp_before'].__setitem__(0, True))
        self.reject(lambda r: r.update(warnings_errors=False))

    def test_unclassified_emulator_warning(self):
        with self.assertRaises(ValueError):
            self.check(fixture(self.cases[0]), stderr=b'mGBA[GBA][0x04] Illegal opcode')

    def test_missing_write_barrier(self):
        self.reject(lambda r: r.update(host_write_barriers=2))

    def test_cold_continue_required(self):
        self.reject(lambda r: r.update(fresh_core_normal_continue=False))

    def test_complete_mon_identity_required(self):
        self.reject(lambda r: r.update(party_mon_bytes_preserved=80))

    def test_rtc_flash_must_be_preserved(self):
        self.reject(lambda r: r.update(rtc_flash_bytes_preserved=65536))

    def test_selected_slot_ppups_cleared(self):
        self.reject(lambda r: r.update(pp_bonuses_after=r['pp_bonuses_before']))

    def test_other_slot_ppups_retained(self):
        self.reject(lambda r: r.update(pp_bonuses_after=0))

    def test_herb_not_consumed(self):
        self.reject(lambda r: r.update(mirror_herb_after=0), 36)

    def test_no_release_promotion(self):
        self.reject(lambda r: r.update(release_ready=True))
        self.reject(lambda r: r.update(full_p03_acceptance=True))

    def test_wrong_pp_rejected(self):
        self.reject(lambda r: r['pp_after'].__setitem__(0, 45))

    def test_other_move_changed_rejected(self):
        self.reject(lambda r: r['moves_after'].__setitem__(3, 535))

    def test_mode_must_reset(self):
        self.reject(lambda r: r.update(mode_reset=False))

    def test_wrong_mgba_version(self):
        self.reject(lambda r: r.update(mgba_version='0.10.3'))

    def test_missing_input_or_wrong_order(self):
        for key in ('bag', 'mode_menu', 'mode_choice', 'party', 'list', 'ask', 'delete_ask', 'summary', 'selection', 'replaced', 'learned', 'field'):
            with self.subTest(key=key):
                self.reject(lambda r: r['witness'].__setitem__(key, 0))
        self.reject(lambda r: r['witness'].update(replaced=80))
        self.reject(lambda r: r['witness'].update(bag=1001))

    def test_denied_entry_cannot_enter_party(self):
        self.reject(lambda r: r['witness'].update(party=40), 41)

    def test_selected_mon_gate_must_enter_party(self):
        self.reject(lambda r: r['witness'].update(party=0), 44)

    def test_denied_gate_must_observe_exact_message(self):
        self.reject(lambda r: r['witness'].update(denied=0), 44)
        self.reject(lambda r: r.update(denial_text=0x092D06A5), 44)

    def test_denied_gate_cannot_open_teach_ui(self):
        for key in ('list', 'ask', 'summary', 'learned'):
            with self.subTest(key=key):
                self.reject(lambda r: r['witness'].__setitem__(key, 50), 44)

    def test_empty_slot_cannot_claim_summary(self):
        self.reject(lambda r: r['witness'].update(summary=80), 4)

    def test_cancel_cannot_claim_learning(self):
        self.reject(lambda r: r['witness'].update(learned=130), 9)

    def test_cancel_requires_giveup(self):
        self.reject(lambda r: r['witness'].update(giveup=0), 9)

    def test_witness_schema_exact(self):
        self.reject(lambda r: r['witness'].pop('denied'))
        self.reject(lambda r: r['witness'].update(mystery=5))

    def test_nested_typed_comparison(self):
        self.assertFalse(subject.same_typed({'x': [False]}, {'x': [0]}))


class Vectors(unittest.TestCase):
    def test_reviewed_vectors_and_header(self):
        c = subject.vectors(); h = subject.header(c)
        self.assertEqual(h.count('"normal-replace-0"'), 1)
        self.assertIn('"egg-needs-empty"', h)
        self.assertEqual(len(c), 46)

    def test_duplicate_name(self):
        c = deepcopy(subject.vectors()); c[1]['name'] = c[0]['name']
        with self.assertRaises(ValueError): subject.validate_vectors(c)

    def test_unsafe_name(self):
        for name in ('../../x', 'a.b', '"};evil', 'x\n'):
            c = deepcopy(subject.vectors()); c[0]['name'] = name
            with self.subTest(name=name), self.assertRaises(ValueError): subject.validate_vectors(c)

    def test_boolean_numeric_vector(self):
        c = deepcopy(subject.vectors()); c[0]['dh'] = False
        with self.assertRaises(ValueError): subject.validate_vectors(c)

    def test_duplicate_and_known_candidates(self):
        for candidate in ([535, 535], [33]):
            c = deepcopy(subject.vectors()); c[0]['candidates'] = candidate
            with self.subTest(candidate=candidate), self.assertRaises(ValueError): subject.validate_vectors(c)

    def test_wrong_ppup_transaction(self):
        c = deepcopy(subject.vectors()); c[0]['pp_bonuses_after'] = 0
        with self.assertRaises(ValueError): subject.validate_vectors(c)

    def test_wrong_gate_policy(self):
        c = deepcopy(subject.vectors()); c[44]['denial_text'] = 0x092D06A5
        with self.assertRaises(ValueError): subject.validate_vectors(c)

    def test_capacity_overflow(self):
        c = deepcopy(subject.vectors()); c[0]['candidates'] = list(range(200, 241))
        with self.assertRaises(ValueError): subject.validate_vectors(c)


class Operational(unittest.TestCase):
    def test_stale_pass_removed(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as tmp:
            d = Path(tmp); (d / 'result.json').write_text('{"status":"PASS"}')
            subject.prepare_output(d)
            self.assertFalse((d / 'result.json').exists())

    def test_local_root_forbidden(self):
        with self.assertRaises(ValueError): subject.prepare_output(ROOT / '.local')

    def test_outside_output_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError): subject.prepare_output(Path(tmp))

    def test_symlink_ancestor_forbidden(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as tmp:
            d = Path(tmp); (d / 'real').mkdir(); (d / 'alias').symlink_to(d / 'real', target_is_directory=True)
            with self.assertRaises(ValueError): subject.prepare_output(d / 'alias' / 'out')

    def test_symlink_result_forbidden(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as tmp:
            d = Path(tmp); (d / 'target').write_text('keep'); (d / 'result.json').symlink_to(d / 'target')
            with self.assertRaises(ValueError): subject.prepare_output(d)
            self.assertEqual((d / 'target').read_text(), 'keep')

    def test_timeout_raw_output_and_outcome_preserved(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as tmp:
            d = Path(tmp)
            e = subprocess.TimeoutExpired(['runner'], 1, output=b'partial', stderr=b'diagnostic')
            with patch.object(subject.previous.subprocess, 'run', side_effect=e):
                out, err, p = subject.capture(['runner'], d / 'timed-out', 1)
            self.assertEqual(out, b'partial'); self.assertEqual(err, b'diagnostic'); self.assertTrue(p['timed_out'])
            self.assertEqual((d / 'timed-out.stdout').read_bytes(), b'partial')
            self.assertTrue((d / 'timed-out.process.json').exists())

    def test_missing_executable_preserved(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as tmp:
            d = Path(tmp)
            with patch.object(subject.previous.subprocess, 'run', side_effect=FileNotFoundError('not present')):
                out, err, p = subject.capture(['runner'], d / 'missing', 1)
            self.assertEqual(out, b''); self.assertIn('not present', p['spawn_error'])
            self.assertTrue((d / 'missing.process.json').exists())

    def test_dot_prefix_cannot_clobber_other_case_logs(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as tmp, self.assertRaises(ValueError):
            subject.capture(['runner'], Path(tmp) / 'case.1', 1)

    def test_nonfixed_default_cannot_claim_pinned_acceptance(self):
        text = (ROOT / subject.SELF).read_text()
        self.assertIn("else 'LOCAL_DIAGNOSTIC'", text)
        self.assertIn("'full_p03_acceptance': False", text)

    def test_runner_never_derives_candidates_via_provider(self):
        text = (ROOT / subject.SOURCE).read_text()
        self.assertNotIn('a_candidates(', text)
        self.assertIn('v->candidates', text)
        self.assertIn('memcmp(party,restored,100)', text)

    def test_workflow_runs_real_binary_and_does_not_promote_baseline(self):
        text = (ROOT / subject.WORKFLOW).read_text()
        self.assertIn('--require-fixed-toolchain', text)
        self.assertIn('git diff --exit-code', text)
        self.assertNotIn('contents: write', text)
        self.assertNotIn('git push', text)


if __name__ == '__main__':
    unittest.main()
