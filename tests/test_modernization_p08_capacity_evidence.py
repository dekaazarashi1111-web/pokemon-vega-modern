"""Mutate real capacity Actions originals; these checks do not run mGBA."""
from __future__ import annotations
import copy
import io
import json
import os
from pathlib import Path
import stat
import sys
import unittest
import warnings
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import record_modernization_p03_capacity as r


class OriginalEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(os.environ.get('P03_CAPACITY_ORIGINAL', str(ROOT / r.EVIDENCE / 'original.zip')))
        cls.raw = path.read_bytes()
        cls.members = r.unpack(cls.raw)

    def setUp(self):
        self.files = self.members.copy()

    def report(self):
        return json.loads(self.files['runtime/result.json'])

    def set_report(self, report):
        self.files['runtime/result.json'] = json.dumps(report).encode()

    def bad(self):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            r.payload(self.files)

    def test_exact_fixed_original_passes(self):
        result = r.payload(self.files)
        self.assertEqual(result['acceptance_environment'], 'FIXED_TOOLCHAIN')
        self.assertEqual([x['case'] for x in result['cases']], ['pc-first', 'pc-last', 'pc-full'])
        self.assertEqual(result['fresh_cores'], 9)

    def test_local_diagnostic_is_never_accepted(self):
        result = self.report(); result['acceptance_environment'] = 'LOCAL_DIAGNOSTIC'
        self.set_report(result); self.bad()

    def test_all_aggregate_fixed_fields_are_enforced(self):
        keys = ('schema_version', 'status', 'scope', 'fixed_toolchain_verified', 'rom', 'seed',
                'fresh_processes', 'fresh_cores', 'cache_reuse', 'protected_inputs',
                'input_hash_and_mtime_unchanged', 'full_p03_acceptance', 'release_ready')
        for key in keys:
            self.files = self.members.copy(); result = self.report(); result[key] = None
            with self.subTest(key=key):
                self.set_report(result); self.bad()

    def test_false_is_not_zero(self):
        result = self.report(); result['cache_reuse'] = False
        self.set_report(result); self.bad()
        self.assertFalse(r.same({'exit': 0}, {'exit': False}))

    def test_wrong_checkout_rejected(self):
        self.files['source-head.txt'] = b'0'*40 + b'\n'; self.bad()

    def test_extra_or_missing_member_rejected(self):
        self.files['unrelated.txt'] = b'noise'; self.bad()
        self.files = self.members.copy(); del self.files['runtime/pc-full.stderr']; self.bad()

    def test_changed_source_hash_rejected(self):
        result = self.report(); result['sources'][r.suite.SOURCE]['sha256'] = '0'*64
        self.set_report(result); self.bad()

    def test_missing_source_dependency_rejected(self):
        result = self.report(); result['sources'].pop(r.suite.SOURCE)
        self.set_report(result); self.bad()

    def test_nonzero_compile_exit_rejected(self):
        name = 'runtime/compile.process.json'; proc = json.loads(self.files[name]); proc['returncode'] = 1
        self.files[name] = json.dumps(proc).encode(); self.bad()

    def test_compile_diagnostic_rejected(self):
        self.files['runtime/compile.stderr'] = b'warning: suspicious instruction\n'; self.bad()

    def test_compiler_identity_mismatch_rejected(self):
        self.files['runtime/host-toolchain.stdout'] = b'cc (different compiler) 14.2.0\n'; self.bad()

    def test_toolchain_success_alone_is_insufficient(self):
        self.files['runtime/fixed-toolchain.stdout'] = b'GitHub Actions toolchain: PASS\n'; self.bad()

    def test_incomplete_regression_rejected(self):
        self.files['regression.txt'] = b'\nRan 34 tests in 0.1s\n\nOK\n'; self.bad()

    def test_altered_compile_flags_rejected(self):
        result = self.report(); result['compile_command'].insert(1, '-DASSUME_PASS')
        self.set_report(result); self.bad()

    def test_case_order_and_count_enforced(self):
        result = self.report(); result['cases'].reverse(); self.set_report(result); self.bad()
        self.files = self.members.copy(); result = self.report(); result['cases'].pop()
        self.set_report(result); self.bad()

    def test_case_receipt_signal_timeout_and_false_rejected(self):
        name = 'runtime/pc-first.process.json'
        for change in ({'returncode': -11}, {'returncode': False}, {'timed_out': True}, {'spawn_error': 'missing'}):
            self.files = self.members.copy(); proc = json.loads(self.files[name]); proc.update(change)
            self.files[name] = json.dumps(proc).encode()
            with self.subTest(change=change):
                self.bad()

    def test_case_stdout_must_be_original_bytes(self):
        self.files['runtime/pc-last.stdout'] += b' '; self.bad()

    def test_both_raw_and_aggregate_cannot_invent_a_consumed_egg(self):
        result = self.report(); name = 'runtime/pc-full.stdout'
        value = json.loads(self.files[name]); value['remaining_eggs'] = 2
        self.files[name] = json.dumps(value).encode(); result['cases'][2]['result'] = value
        result['cases'][2]['stdout_sha256'] = r.identity(self.files[name])['sha256']
        self.set_report(result); self.bad()

    def test_both_raw_and_hash_cannot_hide_missing_restart(self):
        result = self.report(); name = 'runtime/pc-first.stderr'
        self.files[name] = self.files[name].replace(b'capacity old core destroyed; fresh core ordinary Continue', b'omitted')
        result['cases'][0]['stderr_sha256'] = r.identity(self.files[name])['sha256']
        self.set_report(result); self.bad()

    def test_guard_missing_or_reordered_rejected(self):
        result = self.report(); result['guards'].pop(); self.set_report(result); self.bad()
        self.files = self.members.copy(); result = self.report(); result['guards'].reverse()
        self.set_report(result); self.bad()

    def test_duplicate_json_key_rejected(self):
        data = self.files['runtime/result.json']
        self.files['runtime/result.json'] = data.replace(b'"status": "PASS"', b'"status":"FAIL","status":"PASS"', 1)
        self.bad()

    def test_summary_does_not_promote_product_or_count_a_replay(self):
        value = r.summary(r.payload(self.files))
        self.assertIs(value['full_p03_acceptance'], False)
        self.assertIs(value['release_ready'], False)
        self.assertEqual(value['new_mgba_processes_during_integration'], 0)
        self.assertIs(value['active_stage62_baseline_changed'], False)
        self.assertIs(value['parent_and_pc_fixture_only'], True)

    def test_action_identity_failure_and_skipped_steps_rejected(self):
        # Synthetic metadata for validator unit tests, not a runtime or source of acceptance.
        run = {'id': r.RUN, 'head_sha': r.HEAD, 'head_branch': r.BRANCH, 'path': r.suite.WORKFLOW,
               'repository': {'full_name': r.REPO}, 'event': 'push', 'run_attempt': 1,
               'status': 'completed', 'conclusion': 'success'}
        job = {'name': 'capacity', 'run_id': r.RUN, 'head_sha': r.HEAD, 'status': 'completed',
               'conclusion': 'success', 'steps': [{'name': x, 'status': 'completed', 'conclusion': 'success'} for x in r.STEPS]}
        item = {'name': r.ARTIFACT, 'id': 1, 'expired': False, 'size_in_bytes': len(self.raw),
                'digest': 'sha256:' + r.identity(self.raw)['sha256'],
                'workflow_run': {'id': r.RUN, 'head_sha': r.HEAD},
                'archive_download_url': f'https://api.github.com/repos/{r.REPO}/actions/artifacts/1/zip'}
        r.actions(run, [job], item, self.raw)
        for key, bad in (('id', False), ('conclusion', 'failure'), ('head_sha', '0'*40),
                         ('run_attempt', 2), ('event', 'workflow_dispatch'), ('head_branch', 'main')):
            changed = copy.deepcopy(run); changed[key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.actions(changed, [job], item, self.raw)
        changed = copy.deepcopy(job); changed['steps'][2]['conclusion'] = 'skipped'
        with self.assertRaises(ValueError):
            r.actions(run, [changed], item, self.raw)
        changed = copy.deepcopy(item); changed['digest'] = 'sha256:' + '0'*64
        with self.assertRaises(ValueError):
            r.actions(run, [job], changed, self.raw)

    def test_zip_duplicates_traversal_and_symlinks_rejected(self):
        for kind in ('duplicate', 'traversal', 'symlink'):
            buffer = io.BytesIO()
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                with zipfile.ZipFile(buffer, 'w') as archive:
                    if kind == 'duplicate':
                        archive.writestr('same', b'1'); archive.writestr('same', b'2')
                    elif kind == 'traversal':
                        archive.writestr('../outside', b'bad')
                    else:
                        info = zipfile.ZipInfo('link'); info.create_system = 3
                        info.external_attr = (stat.S_IFLNK | 0o777) << 16
                        archive.writestr(info, b'../outside')
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                r.unpack(buffer.getvalue())

    def test_noncanonical_paths_rejected(self):
        for name in ('/absolute', '../outside', 'x/../z', './name', 'x//y', 'a\\b', '.', ''):
            with self.subTest(name=name), self.assertRaises(ValueError):
                r.relative(name)


if __name__ == '__main__':
    unittest.main()
