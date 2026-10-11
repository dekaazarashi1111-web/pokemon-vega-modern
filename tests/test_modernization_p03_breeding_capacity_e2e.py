"""容量境界の成功契約・失敗時の原本保存・通常入力境界を検証する。"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_modernization_p03_breeding_capacity_e2e as suite


def valid(case='pc-first'):
    result = suite.expected_result(case)
    result.update(generation_steps=1789, total_steps=2315, total_frames=99615)
    result['witness'] = dict(zip(suite.WITNESS,
        [452, 759, 1299, 67606, 86558, 88436, 89712, 91078, 92540, 94962, 95731, 97193, 99615]))
    return result


def raw(result):
    return json.dumps(result).encode()


class ResultContract(unittest.TestCase):
    def assert_rejected(self, result, code=0):
        with self.assertRaises((ValueError, UnicodeError)):
            suite.validate_result(raw(result), result.get('case', 'pc-first'), code)

    def test_three_distinct_capacity_oracles(self):
        for case in suite.CASES:
            with self.subTest(case=case):
                value = valid(case)
                self.assertEqual(suite.validate_result(raw(value), case, 0), value)
        self.assertEqual(suite.expected_result('pc-last')['pc_destination'], 419)
        self.assertEqual(suite.expected_result('pc-full')['pc_deliveries'], 0)
        self.assertEqual(suite.expected_result('pc-full')['remaining_eggs'], 3)

    def test_unknown_case_rejected(self):
        with self.assertRaises(ValueError):
            suite.expected_result('pc-middle')

    def test_pass_stdout_never_hides_nonzero_or_signal(self):
        for code in (1, 2, -11, -15, 127):
            with self.subTest(code=code):
                self.assert_rejected(valid(), code)

    def test_false_float_and_absent_exit_are_not_zero(self):
        for code in (False, 0.0, None, '0'):
            with self.subTest(code=code):
                self.assert_rejected(valid(), code)

    def test_every_fixed_field_is_enforced(self):
        for key, old in suite.expected_result('pc-first').items():
            value = valid()
            value[key] = not old if type(old) is bool else old+1 if type(old) is int else old+'-changed'
            with self.subTest(field=key):
                # Hold requested case constant so changing result.case is detected.
                with self.assertRaises(ValueError):
                    suite.validate_result(raw(value), 'pc-first', 0)

    def test_no_implicit_boolean_integer_conversion(self):
        for key, old in suite.expected_result('pc-first').items():
            if type(old) in (int, bool):
                value = valid(); value[key] = int(old) if type(old) is bool else bool(old)
                with self.subTest(field=key):
                    self.assert_rejected(value)

    def test_no_missing_or_extra_result_fields(self):
        value = valid(); value.pop('fifo_byte_identity'); self.assert_rejected(value)
        value = valid(); value['assume_pass'] = True; self.assert_rejected(value)

    def test_every_witness_required(self):
        for key in suite.WITNESS:
            value = valid(); del value['witness'][key]
            with self.subTest(field=key):
                self.assert_rejected(value)

    def test_all_sequence_transitions_must_advance(self):
        for first, second in zip(suite.WITNESS, suite.WITNESS[1:]):
            value = valid(); value['witness'][second] = value['witness'][first]
            with self.subTest(transition=(first, second)):
                self.assert_rejected(value)

    def test_witness_type_and_bounds(self):
        for bad in (False, 1.0, None, -1, 0, 99616, '10'):
            value = valid(); value['witness']['first_claim'] = bad
            with self.subTest(value=bad):
                self.assert_rejected(value)

    def test_final_reload_is_last_observation(self):
        value = valid(); value['total_frames'] += 1; self.assert_rejected(value)

    def test_generation_is_bounded_physical_walking(self):
        for bad in (False, 0, -1, 8193, 700001, 1789.0, '1789'):
            value = valid(); value['generation_steps'] = bad
            with self.subTest(value=bad):
                self.assert_rejected(value)

    def test_overflow_and_route_steps_not_omitted(self):
        for steps in (1789, 2300, 2314, 2316, True):
            value = valid(); value['total_steps'] = steps
            with self.subTest(steps=steps):
                self.assert_rejected(value)

    def test_duplicate_keys_and_multiple_json_results_rejected(self):
        value = raw(valid())
        for payload in (value+value, value.replace(b'"status": "PASS"', b'"status":"FAIL","status":"PASS"')):
            with self.subTest(payload=payload[:80]):
                with self.assertRaises(ValueError):
                    suite.validate_result(payload, 'pc-first', 0)

    def test_bad_json_unicode_and_nonfinite_rejected(self):
        for payload in (b'\xff', b'{', b'NaN', b'null', b'[]', raw(valid()).replace(b'1789', b'Infinity')):
            with self.subTest(payload=payload[:80]):
                with self.assertRaises((ValueError, UnicodeError)):
                    suite.validate_result(payload, 'pc-first', 0)

    def test_full_pc_does_not_consume_third_egg(self):
        value = valid('pc-full'); value['remaining_eggs'] = 2; self.assert_rejected(value)
        value = valid('pc-full'); value['queue_head'] = 3; self.assert_rejected(value)

    def test_pc_search_last_slot_not_first_slot(self):
        value = valid('pc-last'); value['pc_destination'] = 0; self.assert_rejected(value)


class NativeBoundary(unittest.TestCase):
    def test_embedded_entrypoint_unique(self):
        self.assertEqual(suite.embed('int main(int argc,char **argv){}', 'old_main'),
                         'int old_main(int argc,char **argv){}')
        for source in ('int other(){}', 'int main(){} int main(){}'):
            with self.assertRaises(ValueError):
                suite.embed(source, 'old_main')

    def test_no_host_write_or_rom_call_after_fixture_barrier(self):
        source = (ROOT / suite.SOURCE).read_text()
        start = source.index('/* 以下ではhost書込')
        measured = source[start:]
        for forbidden in ('call_preserving(', 'call_rom_args(', 'write8(', 'write16(',
                          'write32(', 'set_mon_data', 'a_restore(', 'restore_cpu_state('):
            self.assertNotIn(forbidden, measured)
        self.assertIn('a_guard(c);', measured)
        self.assertIn('a_guard(c);a_require(bc_continue(c)', source)
        self.assertIn('i<420U', measured)
        self.assertIn('sizeof(s->pc)', source)
        self.assertIn('bc_queue_after(c,queue,delivered)', measured)

    def test_all_seven_real_guard_probes_required(self):
        self.assertEqual(suite.GUARDS, ('bus8', 'bus16', 'bus32', 'raw8', 'raw16', 'raw32', 'register'))
        process = {'returncode': 1, 'timed_out': False, 'spawn_error': None}
        suite.validate_guard(b'', b'P03 archive: host write after observation barrier\n', process)
        for change in ({'returncode': 0}, {'returncode': False}, {'returncode': -11},
                       {'timed_out': True}, {'spawn_error': 'not found'}):
            invalid = {**process, **change}
            with self.subTest(process=invalid):
                with self.assertRaises(ValueError):
                    suite.validate_guard(b'', b'P03 archive: host write after observation barrier\n', invalid)
        with self.assertRaises(ValueError):
            suite.validate_guard(b'PASS', b'P03 archive: host write after observation barrier\n', process)
        with self.assertRaises(ValueError):
            suite.validate_guard(b'', b'unrelated failure\n', process)

    def test_workflow_never_enables_diagnostic_acceptance(self):
        source = (ROOT / suite.WORKFLOW).read_text()
        self.assertIn('ubuntu-24.04', source)
        self.assertIn('infra/setup_github_actions.sh --install', source)
        self.assertIn('run_modernization_stage82_github_domain.py prepare', source)
        self.assertNotIn('--diagnostic', source)
        self.assertNotIn('continue-on-error', source)


class OutputAndProcess(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='capacity-tests-', dir=ROOT / '.local')
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_stale_pass_and_logs_are_removed(self):
        for name in ('result.json', 'result.json.tmp', 'pc-first.stdout', 'pc-last.stderr',
                     'pc-full.process.json', 'guard-bus8.stdout', 'compile.stderr'):
            (self.directory / name).write_text('old PASS')
        suite.prepare_output(self.directory)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_invalid_jobs_invalidate_prior_pass(self):
        for jobs in (0, 4, False, 1.0):
            (self.directory / 'result.json').write_text('old PASS')
            with self.subTest(jobs=jobs), self.assertRaises(ValueError):
                suite.run(self.directory, self.directory / 'absent.gba', jobs, True)
            self.assertFalse((self.directory / 'result.json').exists())

    def test_missing_rom_invalidate_prior_pass(self):
        (self.directory / 'result.json').write_text('old PASS')
        with self.assertRaises(ValueError):
            suite.run(self.directory, self.directory / 'absent.gba', 1, True)
        self.assertFalse((self.directory / 'result.json').exists())

    def test_wrong_hash_rejected_before_compile(self):
        rom = self.directory / 'wrong.gba'; rom.write_bytes(b'not the fixed candidate')
        with self.assertRaises(ValueError), patch.object(suite.common, 'capture') as capture:
            suite.run(self.directory / 'output', rom, 1, True)
        capture.assert_not_called()

    def test_fixed_mode_requires_actual_toolchain_success(self):
        (self.directory / 'result.json').write_text('old PASS')
        with patch.dict('os.environ', {k: '' for k in ('CPPFLAGS', 'CFLAGS', 'LDFLAGS', 'LD_LIBRARY_PATH')}):
            with patch.object(suite.common, 'capture', return_value=(b'', b'mismatch',
                              {'returncode': 1, 'timed_out': False, 'spawn_error': None})):
                with self.assertRaises(ValueError):
                    suite.run(self.directory, self.directory / 'absent.gba')
        self.assertFalse((self.directory / 'result.json').exists())

    def test_custom_flags_cannot_be_called_fixed_acceptance(self):
        with patch.dict('os.environ', {'CFLAGS': '-O0'}):
            with self.assertRaises(ValueError):
                suite.run(self.directory, self.directory / 'absent.gba')

    def test_output_cannot_be_local_root_or_escape(self):
        for path in (ROOT / '.local', ROOT / 'outside-capacity-output', ROOT / '.local/../outside-capacity-output'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                suite.prepare_output(path)

    def test_symlink_ancestor_and_product_rejected_without_touching_target(self):
        target = self.directory / 'target'; target.mkdir()
        link = self.directory / 'link'; link.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            suite.prepare_output(link / 'nested')
        protected = self.directory / 'protected.txt'; protected.write_text('must survive')
        result = self.directory / 'result.json'; result.symlink_to(protected)
        with self.assertRaises(ValueError):
            suite.prepare_output(self.directory)
        self.assertEqual(protected.read_text(), 'must survive')

    def test_input_snapshot_checks_mtime_as_well_as_hash(self):
        path = self.directory / 'input'; path.write_bytes(b'original')
        before = suite.snapshot(path)
        import os
        os.utime(path, ns=(path.stat().st_atime_ns, before['mtime_ns']+1))
        after = suite.snapshot(path)
        self.assertEqual(before['sha256'], after['sha256'])
        self.assertNotEqual(before, after)

    def test_actual_process_pass_then_signal_is_not_success(self):
        command = [sys.executable, '-c', 'import os,signal;print("PASS",flush=True);os.kill(os.getpid(),signal.SIGTERM)']
        out, err, process = suite.common.capture(command, self.directory / 'signal', 10)
        self.assertEqual(out, b'PASS\n')
        self.assertEqual(suite.common.require_exited(process), -15)
        with self.assertRaises(ValueError):
            suite.validate_result(raw(valid()), 'pc-first', process['returncode'])

    def test_actual_timeout_keeps_partial_non_utf8_logs(self):
        command = [sys.executable, '-c', 'import os,time;os.write(1,b"partial\\xff");os.write(2,b"error\\xfe");time.sleep(10)']
        out, err, process = suite.common.capture(command, self.directory / 'timeout', 2.0)
        self.assertTrue(process['timed_out'])
        self.assertEqual(out, b'partial\xff'); self.assertEqual(err, b'error\xfe')
        self.assertEqual((self.directory / 'timeout.stdout').read_bytes(), out)
        self.assertEqual((self.directory / 'timeout.stderr').read_bytes(), err)
        with self.assertRaises(ValueError):
            suite.common.require_exited(process)

    def test_actual_spawn_failure_is_retained(self):
        out, err, process = suite.common.capture([str(self.directory / 'not-executable')], self.directory / 'spawn', 1)
        self.assertIsNone(process['returncode']); self.assertIsNotNone(process['spawn_error'])
        self.assertTrue((self.directory / 'spawn.process.json').is_file())

    def test_atomic_result_has_no_partial_staging_file(self):
        suite.write_result(self.directory, {'status': 'PASS', 'diagnostic': True})
        self.assertEqual(json.loads((self.directory / 'result.json').read_text())['status'], 'PASS')
        self.assertFalse((self.directory / 'result.json.tmp').exists())

    def test_real_cli_unknown_argument_is_two(self):
        process = subprocess.run([sys.executable, str(ROOT / suite.SELF), '--not-a-valid-option'],
                                 capture_output=True, check=False)
        self.assertEqual(process.returncode, 2)
        self.assertNotIn(b'"status": "PASS"', process.stdout)


if __name__ == '__main__':
    unittest.main()
