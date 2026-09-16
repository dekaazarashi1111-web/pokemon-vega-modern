"""Run the adopted Stage81 acceptance CLI without mocked evidence or product execution.

Exit 0 means the evidence is consistent; exit 1 means release remains blocked;
exit 2 is a validation/usage error and must not masquerade as the release gate.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = 'scripts/check_modernization_p08_current_acceptance.py'
SNAPSHOT = 'content/modernization/p08_current_acceptance.json'
DOMAINS = ['p02', 'mega_shop', 'floette', 'p03', 'p04_mega_runtime', 'battle_policy', 'p05']
CANDIDATE_SHA = '521624a5e6065bd969b7c3143044f1d96491b8af05a0231827ba2e709d04d579'


def identity(path):
    target = ROOT / path
    target.resolve().relative_to(ROOT.resolve())
    data = target.read_bytes()
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'mtime_ns': target.stat().st_mtime_ns}


class Stage81AcceptanceCLITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot_bytes = (ROOT / SNAPSHOT).read_bytes()
        cls.snapshot = json.loads(cls.snapshot_bytes)
        paths = set(cls.snapshot['source_bindings']) | {
            SNAPSHOT, SCRIPT, 'config/active_play_baseline.json',
            'content/modernization/stage79_cumulative_mgba_runtime_gate.json',
            'content/modernization/p08_integration_matrix.json',
            'content/modernization/p08_runtime_handoff.json',
            'content/modernization/p08_release_handoff.json',
        }
        cls.before = {p: identity(p) for p in sorted(paths)}
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        cls.commands = {}
        for name, args in (
            ('check', ['--check']),
            ('release-gate', ['--check', '--require-release-ready']),
            ('conflicting-modes', ['--check', '--write']),
            ('unknown-option', ['--not-an-acceptance-option']),
        ):
            command = [sys.executable, str(ROOT / SCRIPT), *args]
            cls.commands[name] = subprocess.run(
                command, cwd=ROOT, env=env, capture_output=True, timeout=120, check=False)
        cls.after = {p: identity(p) for p in sorted(paths)}
        # Optional CI observations, not a success record. unittest owns pass/fail.
        destination = os.environ.get('STAGE81_CLI_EVIDENCE_DIRECTORY')
        if destination:
            output = Path(destination)
            if not output.is_absolute():
                output = ROOT / output
            output.resolve().relative_to((ROOT / '.local').resolve())
            output.mkdir(parents=True, exist_ok=True)
            rows = {}
            for name, result in cls.commands.items():
                (output / (name + '.stdout')).write_bytes(result.stdout)
                (output / (name + '.stderr')).write_bytes(result.stderr)
                rows[name] = {
                    'argv': result.args, 'returncode': result.returncode,
                    'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
                    'stderr_sha256': hashlib.sha256(result.stderr).hexdigest(),
                }
            checkout = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                      capture_output=True, text=True, check=True).stdout.strip()
            observation = {
                'schema_version': 1, 'scope': 'REAL_ACCEPTANCE_CLI_NOT_NEW_MGBA',
                'checkout_sha': checkout,
                'event_source_head_sha': os.environ.get('STAGE81_SOURCE_HEAD'),
                'snapshot_sha256': hashlib.sha256(cls.snapshot_bytes).hexdigest(),
                'fresh_mgba_process_runs': 0,
                'commands': rows, 'inputs_unchanged': cls.before == cls.after,
                'before': cls.before, 'after': cls.after,
            }
            (output / 'observations.json').write_text(
                json.dumps(observation, ensure_ascii=False, sort_keys=True, indent=2) + '\n')

    def test_real_check_succeeds_and_matches_committed_snapshot_exactly(self):
        result = self.commands['check']
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        self.assertEqual(result.stderr, b'')
        self.assertEqual(result.stdout, self.snapshot_bytes)

    def test_real_release_gate_is_one_not_validation_error_or_success(self):
        result = self.commands['release-gate']
        self.assertEqual(result.returncode, 1, result.stderr.decode(errors='replace'))
        self.assertEqual(result.stderr, b'')
        self.assertEqual(result.stdout, self.snapshot_bytes)
        self.assertEqual(result.stdout, self.commands['check'].stdout)

    def test_exact_adopted_stage81_identity(self):
        report = self.snapshot
        self.assertIs(type(report['candidate_stage']), int)
        self.assertEqual(report['candidate_stage'], 81)
        self.assertEqual(report['candidate_rom']['sha256'], CANDIDATE_SHA)
        self.assertIs(type(report['candidate_rom']['size']), int)
        self.assertEqual(report['candidate_rom']['size'], 33554432)
        self.assertEqual(report['native_pp_acceptance']['candidate_rom'], report['candidate_rom'])

    def test_all_seven_domains_belong_to_the_native_pp_layer(self):
        report = self.snapshot
        self.assertEqual(report['satisfied_runtime_domains'], DOMAINS)
        rows = report['native_pp_acceptance']['domains']
        self.assertEqual([row['id'] for row in rows], DOMAINS)
        self.assertTrue(all(row['status'] == 'PASS' for row in rows))
        self.assertEqual(report['runtime_evidence_source'], report['native_pp_acceptance']['source'])

    def test_original_runs_are_not_recounted_as_this_cli_execution(self):
        native = self.snapshot['native_pp_acceptance']
        expected = {'original_matrix_fresh_process_runs': 7, 'original_matrix_cache_reuse': 0,
                    'fresh_process_runs_this_validation': 0}
        for key, value in expected.items():
            self.assertIs(type(native[key]), int)
            self.assertEqual(native[key], value)
        p03 = native['p03_fullslots']
        for key, value in {'accepted_candidate_runs': 8, 'negative_control_runs': 2,
                           'original_fresh_process_runs': 10, 'original_cache_reuse': 0}.items():
            self.assertIs(type(p03[key]), int)
            self.assertEqual(p03[key], value)
        self.assertIs(self.snapshot['heavy_execution_performed'], False)

    def test_stage80_representatives_remain_historical_not_stage81_runs(self):
        self.assertEqual(self.snapshot['representative_e2e_scope'],
                         'STAGE80_HISTORY_NOT_RECOUNTED_AS_STAGE81')
        self.assertEqual(self.snapshot['native_pp_acceptance']['prior_stage80_evidence_scope'],
                         'RETAINED_HISTORY_NOT_RECOUNTED_AS_STAGE81_EXECUTIONS')
        self.assertIs(self.snapshot['historical_stage77']['modified'], False)

    def test_product_release_and_uncovered_paths_stay_blocked(self):
        report = self.snapshot
        self.assertEqual(report['validation_status'], 'PASS')
        self.assertEqual(report['acceptance_status'], 'BLOCKED')
        self.assertEqual(report['active_baseline_stage'], 62)
        for key in ('release_ready', 'phase_completion_promoted', 'active_baseline_changed'):
            self.assertIs(report[key], False)
        for value in report['native_pp_acceptance']['claims'].values():
            self.assertIs(value, False)
        blockers = {row['id'] for row in report['current_blockers']}
        self.assertTrue({'P03_BREEDING_E2E_PENDING', 'P03_FULL_ACCEPTANCE_PENDING',
                         'P05_FULL_ACCEPTANCE_PENDING', 'P06_SPECIES_ADJUSTMENT_NOT_ADOPTED',
                         'P07_CROSS_DISTRIBUTION_NOT_ADOPTED',
                         'P08_FINAL_ACCEPTANCE_AND_RELEASE_DECISION_PENDING'} <= blockers)

    def test_real_cli_preserves_all_bound_inputs_bytes_and_mtimes(self):
        self.assertEqual(self.before, self.after)
        self.assertEqual(self.before, {p: identity(p) for p in self.before})

    def test_conflicting_write_and_check_is_usage_error_not_release_block(self):
        result = self.commands['conflicting-modes']
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'not allowed with argument', result.stderr)

    def test_unknown_option_is_usage_error_not_release_block(self):
        result = self.commands['unknown-option']
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'unrecognized arguments', result.stderr)


if __name__ == '__main__':
    unittest.main()
