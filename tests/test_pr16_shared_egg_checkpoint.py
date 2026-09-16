"""Retained raw evidence tests; never new emulator success counts."""
from copy import deepcopy
from pathlib import Path
import io
import sys
import unittest
from unittest.mock import patch
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_shared_egg_checkpoint as m


class SharedCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = m.prior.archive((ROOT / m.DIRECTORY / str(m.RECORD[0]) / 'original.zip').read_bytes())

    def changed(self, path, **changes):
        value = deepcopy(m.prior.load(self.files[path])); value.update(changes)
        return self.files | {path: m.prior.stable(value)}

    def test_exact_raw_originals_and_selected_scope(self):
        value = m.verify_files(self.files)
        self.assertEqual((value['new_native_processes'], value['fresh_cores'], value['unit_tests']), (16, 32, 12))
        self.assertEqual([r['species'] for r in value['receivers']], [605, 549])
        self.assertTrue(value['shared_only_selected_receiver_routes_accepted'])
        for key in ('all_shared_egg_routes_accepted', 'natural_acquisition_accepted', 'full_p03_acceptance', 'full_p07_acceptance', 'release_ready'):
            self.assertIs(value[key], False)

    def test_actions_requires_exact_success_head_attempt_and_artifact(self):
        run, aid, size, sha, head, wf, name, _ = m.RECORD
        good = dict(run_id=run, artifact_id=aid, size=size, sha256=sha, artifact_name=name,
                    head_sha=head, head_branch=m.prior.BRANCH, run_attempt=1,
                    path='.github/workflows/' + wf + '.yml', status='completed', conclusion='success',
                    jobs=[dict(run_id=run, head_sha=head, status='completed', conclusion='success',
                               steps=[dict(status='completed', conclusion='success')])])
        m.prior.metadata(good, m.RECORD)
        for key, value in [('head_sha', '0'*40), ('run_attempt', 2), ('conclusion', 'failure'), ('artifact_id', 0)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.prior.metadata(good | {key: value}, m.RECORD)

    def test_exact_tested_head_is_required(self):
        with self.assertRaises(ValueError):
            m.verify_files(self.files | {m.RECORD[7] + 'tested-head.txt': b'0000000000000000000000000000000000000000\n'})

    def test_outer_scope_cannot_be_promoted_or_old_runs_relabelled(self):
        path = 'pr16-shared-egg-routes/result.json'
        for key, value in [('full_p03_acceptance', True), ('full_p07_acceptance', True), ('release_ready', True),
                           ('successful_fresh_cores', 33), ('actual_new_processes', 15), ('old_runs_relabelled', 1),
                           ('scope', 'P07_INTEGRATED_NATIVE_MEMORY_SAVE')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.verify_files(self.changed(path, **{key: value}))

    def test_missing_fresh_continue_cannot_pass(self):
        path = 'pr16-shared-egg-routes/native/shared-605-empty.stdout'
        with self.assertRaises(ValueError):
            m.verify_files(self.changed(path, fresh_core_normal_continue=False))

    def test_boolean_zero_exit_and_timeout_are_not_success(self):
        path = 'pr16-shared-egg-routes/native/shared-605-empty.process.json'
        for fields in ({'returncode': False}, {'returncode': 1}, {'timed_out': True}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                m.verify_files(self.changed(path, **fields))

    def test_cancel_must_leave_moves_and_pp_unchanged(self):
        path = 'pr16-shared-egg-routes/native/shared-605-summary-cancel.stdout'
        value = m.prior.load(self.files[path])
        changed = list(value['pp_after']); changed[0] += 1
        with self.assertRaises(ValueError):
            m.verify_files(self.changed(path, pp_after=changed))

    def test_target_cannot_be_relabelled_as_a_legacy_move(self):
        path = 'pr16-shared-egg-routes/oracle.json'
        value = m.prior.load(self.files[path]); value['selected_receivers'][0]['legacy'].append(23)
        oracle = m.prior.stable(value)
        report_path = 'pr16-shared-egg-routes/result.json'
        report = m.prior.load(self.files[report_path]); report['oracle'] = m.prior.identity(oracle)
        with self.assertRaises(ValueError):
            m.verify_files(self.files | {path: oracle, report_path: m.prior.stable(report)})

    def test_missing_case_is_rejected_even_after_report_hash_recomputed(self):
        path = 'pr16-shared-egg-routes/native/result.json'
        value = m.prior.load(self.files[path]); value['cases'].pop(); native = m.prior.stable(value)
        report_path = 'pr16-shared-egg-routes/result.json'
        report = m.prior.load(self.files[report_path]); report['native_report'] = m.prior.identity(native)
        with self.assertRaises(ValueError):
            m.verify_files(self.files | {path: native, report_path: m.prior.stable(report)})

    def test_physical_host_write_guard_must_really_fail(self):
        path = 'pr16-shared-egg-routes/native/guard-bus8.stderr'
        with self.assertRaises(ValueError):
            m.verify_files(self.files | {path: b'PASS\n'})

    def test_rom_save_and_unsafe_archive_members_are_rejected(self):
        for name in ('capture.sav', 'candidate.gba', '../result.json'):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w') as z:
                z.writestr(name, b'not an accepted artifact')
            with self.subTest(name=name), self.assertRaises(ValueError):
                m.prior.archive(buf.getvalue())

    def test_projection_idempotently_preserves_prior_successes_and_remaining_gates(self):
        previous = dict(final_integration={'source_path': m.prior.RECEIPT}, physical_route_checkpoint={'new_native_processes': 15, 'new_native_cores': 40},
            full_p03_acceptance=False, full_p05_acceptance=False, full_p07_acceptance=False, full_p06_acceptance=True,
            p06_adoption={'full_phase_accepted': True}, release_ready=False, repository_policy={'visibility': 'public'},
            archive_economy={'cost': 0}, remaining_conditions=[{'id': 'EVOLUTION_FORM_OTHER_EGG', 'physical_route_success_evidence': 'preserved'},
            {'id': 'PHYSICAL_CIRCUS_ADMISSION', 'resume': 'unchanged'}])
        before = deepcopy(previous); receipt = {'synthetic_unit_only': True}
        with patch.object(m, 'build', return_value=receipt), patch.object(m.prior, 'read', return_value=m.prior.stable(receipt)):
            after = m.project(previous); twice = m.project(after)
        self.assertEqual(previous, before); self.assertEqual(after, twice)
        for key in ('physical_route_checkpoint', 'p06_adoption', 'repository_policy', 'archive_economy', 'full_p03_acceptance', 'full_p05_acceptance', 'full_p07_acceptance', 'full_p06_acceptance', 'release_ready'):
            self.assertEqual(after[key], before[key])
        self.assertEqual(after['remaining_conditions'][1], before['remaining_conditions'][1])
        self.assertEqual(after['remaining_conditions'][0]['physical_route_success_evidence'], 'preserved')
        self.assertEqual(len(after['remaining_conditions']), 2)

if __name__ == '__main__':
    unittest.main()
