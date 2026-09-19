"""Synthetic contract tests; never counted as emulator executions."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SPEC = importlib.util.spec_from_file_location('m5_runner', Path(__file__).resolve().parents[1] / 'scripts/run_modernization_p05_mega_lifecycle_e2e.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def valid(case='dragonize', mode='active'):
    base, initial, mega, ability, _ = m.CASES[case]
    active = mode == 'active'
    row = dict(schema_version=1, status='OBSERVED', scope=m.SCOPE, rom_sha256=m.ROM_SHA,
               case=case, mode=mode, initial_species=base, initial_ability=initial,
               final_species=mega if active else base, final_ability=ability if active else initial,
               eligible=mode in ('active', 'no-toggle', 'cancel-toggle'), cold_core_count=2 if active else 1,
               cold_save_all_100_party_bytes_equal=active, host_write_guard=True,
               player_ability_injected=False, natural_capture_or_facility_entry=False,
               full_p05_acceptance=False, release_ready=False, warnings_errors=0)
    row.update({k: 0 for k in m.NUMBERS})
    row.update(initial_hp=64, player_hp=64, enemy_hp=1000, player_pp=19, enemy_pp=19,
               spent_frame=100, end_frame=200, return_frame=202, last_key_frame=190)
    if mode != 'no-toggle':
        row.update(toggle_first=10, toggle_last=20 if mode == 'cancel-toggle' else 10,
                   toggle_count=2 if mode == 'cancel-toggle' else 1)
    if active:
        row.update(mega_frame=50, flee_frame=450, flee_outcome=4, run_presses=1,
                   reverted_species=base, save_counter_before=2, save_counter_after=3)
    if case in ('dragonize', 'mega_sol', 'piercing_drill') and active or case == 'fire_mane':
        row['enemy_hp'] = 995
    if case == 'spicy_spray':
        row.update(player_hp=54, enemy_hp=938 if active else 1000, enemy_status=16 if active else 0)
    return row


class Contract(unittest.TestCase):
    def check(self, row, code=0):
        return m.validate_case(json.dumps(row).encode(), row['case'], row['mode'], code)

    def reject(self, row, **changes):
        row = dict(row, **changes)
        with self.assertRaises(ValueError):
            self.check(row)

    def test_complete_matrix(self):
        rows = [valid(*pair) for pair in m.PAIRS]
        m.validate_matrix(rows)
        self.assertEqual(len(rows), 42)
        self.assertEqual(sum(r['cold_core_count'] for r in rows), 48)

    def test_exit_codes_are_strict(self):
        for code in (False, True, 0.0, None, '0', -11, -15, 1, 2):
            with self.subTest(code=code), self.assertRaises(ValueError):
                self.check(valid(), code)

    def test_missing_duplicate_extra_conditions(self):
        rows = [valid(*pair) for pair in m.PAIRS]
        for bad in (rows[:-1], rows + [rows[0]], rows[:-1] + [rows[0]]):
            with self.assertRaises(ValueError):
                m.validate_matrix(bad)

    def test_duplicate_json_and_trailing_data(self):
        raw = json.dumps(valid()).encode()
        for bad in (raw[:-1] + b',"status":"OBSERVED"}', raw + raw, b'[]', b'null', b'NaN', b'{'):
            with self.subTest(raw=bad[:20]), self.assertRaises(ValueError):
                m.validate_case(bad, 'dragonize', 'active', 0)

    def test_unknown_schema(self):
        obj = valid()
        self.reject(obj, unknown=True)
        del obj['mega_frame']
        with self.assertRaises(ValueError):
            self.check(obj)

    def test_input_assignment_turn_order(self):
        for changes in (dict(toggle_first=0), dict(toggle_last=100), dict(mega_frame=10),
                        dict(mega_frame=100), dict(end_frame=100), dict(return_frame=200),
                        dict(last_key_frame=202), dict(return_frame=16000)):
            self.reject(valid(), **changes)

    def test_native_ability_not_injection(self):
        for changes in (dict(initial_ability=312), dict(final_ability=67), dict(final_species=503),
                        dict(player_ability_injected=True), dict(host_write_guard=False)):
            self.reject(valid(), **changes)

    def test_failed_or_non_native_lifecycle(self):
        for changes in (dict(reverted_species=1638), dict(flee_outcome=1), dict(flee_frame=0),
                        dict(run_presses=0), dict(save_counter_after=2), dict(save_counter_after=4),
                        dict(cold_save_all_100_party_bytes_equal=False), dict(cold_core_count=1)):
            self.reject(valid(), **changes)

    def test_control_cannot_evolve_or_claim_save(self):
        for mode in m.MODES[1:]:
            for changes in (dict(mega_frame=20), dict(final_ability=312), dict(reverted_species=503),
                            dict(cold_save_all_100_party_bytes_equal=True), dict(save_counter_after=1)):
                self.reject(valid('dragonize', mode), **changes)

    def test_cancel_requires_two_distinct_edges(self):
        for changes in (dict(toggle_count=1), dict(toggle_last=10), dict(toggle_first=20)):
            self.reject(valid('dragonize', 'cancel-toggle'), **changes)

    def test_single_turn_not_multiple_turns(self):
        for field in ('player_pp', 'enemy_pp'):
            for pp in (18, 20):
                self.reject(valid(), **{field: pp})

    def test_effect_controls(self):
        for case in ('dragonize', 'mega_sol', 'piercing_drill'):
            self.reject(valid(case), enemy_hp=1000)
            self.reject(valid(case, 'no-stone'), enemy_hp=995)
        self.reject(valid('spicy_spray'), enemy_status=0)
        self.reject(valid('spicy_spray', 'no-stone'), enemy_status=16)
        self.reject(valid('eelevate_ground'), player_hp=54)

    def test_embed_changes_only_unique_entry(self):
        source = 'int main(int argc, char **argv) {return 0;}'
        self.assertEqual(m.embed(source, 'prior'), source.replace('main', 'prior'))
        for source in ('nothing', source + source):
            with self.assertRaises(ValueError):
                m.embed(source, 'prior')

    def test_stale_pass_removed_before_preflight_failure(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(m, 'ROOT', Path(tmp)):
            out = Path(tmp) / '.local/run'
            out.mkdir(parents=True)
            (out / 'result.json').write_text('old PASS')
            with self.assertRaises(ValueError):
                m.run(out)
            self.assertFalse((out / 'result.json').exists())

    def test_output_bounds(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(m, 'ROOT', Path(tmp)):
            root = Path(tmp)
            for path in (root, root / '.local'):
                with self.assertRaises(ValueError):
                    m.prepare_output(path)
            (root / '.local').mkdir(exist_ok=True)
            (root / '.local/link').symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                m.prepare_output(root / '.local/link')

    def test_timeout_keeps_partial_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            error = subprocess.TimeoutExpired(['fake'], 1, output=b'partial\xff', stderr=b'error\xfe')
            with mock.patch.object(m.subprocess, 'run', side_effect=error), self.assertRaises(subprocess.TimeoutExpired):
                m.capture(['fake'], out, 'failed', 1)
            self.assertEqual((out / 'failed.stdout').read_bytes(), b'partial\xff')
            self.assertEqual((out / 'failed.stderr').read_bytes(), b'error\xfe')

    def test_real_child_signal_rejects_printed_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = 'import os,signal;print("PASS",flush=True);os.kill(os.getpid(),signal.SIGTERM)'
            result = m.capture([sys.executable, '-c', code], Path(tmp), 'child', 5)
            self.assertEqual(result.returncode, -15)
            with self.assertRaises(ValueError):
                m.validate_case(result.stdout, 'dragonize', 'active', result.returncode)


for field, value in valid().items():
    if type(value) not in (int, bool):
        continue
    def test(self, field=field, value=value):
        self.reject(valid(), **{field: False if type(value) is int else int(value)})
    setattr(Contract, 'test_strict_type_' + field, test)

if __name__ == '__main__':
    unittest.main()
