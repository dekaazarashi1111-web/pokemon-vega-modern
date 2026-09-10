"""Mutations of actual Actions originals; tests do not execute an emulator."""
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import record_modernization_p03_relearner as subject


class OriginalEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = ROOT / subject.DIRECTORY
        cls.data = (d / 'original.zip').read_bytes()
        cls.run = subject.strict_json((d / 'actions-run.json').read_bytes())
        cls.jobs = subject.strict_json((d / 'actions-jobs.json').read_bytes())
        cls.artifact = subject.strict_json((d / 'actions-artifact.json').read_bytes())
        cls.files = subject.archive_members(cls.data)
        cls.report = subject.strict_json(cls.files['result.json'])

    def check(self, data=None, run=None, jobs=None, artifact=None):
        return subject.verify(self.data if data is None else data,
                              self.run if run is None else run,
                              self.jobs if jobs is None else jobs,
                              self.artifact if artifact is None else artifact)

    def mutate_files(self, change):
        files = self.files.copy()
        change(files)
        b = io.BytesIO()
        with zipfile.ZipFile(b, 'w', zipfile.ZIP_DEFLATED) as z:
            for n, content in files.items():
                z.writestr(n, content)
        data = b.getvalue()
        # Refresh outer digest to test inner checks independently, not to claim authenticity.
        artifact = deepcopy(self.artifact)
        artifact.update(digest='sha256:' + subject.identity(data)['sha256'], size_in_bytes=len(data))
        with self.assertRaises((ValueError, KeyError, TypeError)):
            self.check(data=data, artifact=artifact)

    def mutate_report(self, change):
        def apply(files):
            r = subject.strict_json(files['result.json']); change(r)
            files['result.json'] = json.dumps(r).encode()
        self.mutate_files(apply)

    def test_original_all_46_and_no_promotion(self):
        r = self.check()
        self.assertEqual(r['accepted_original_processes'], 46)
        self.assertEqual(r['accepted_original_core_instances'], 92)
        self.assertEqual(r['new_emulator_runs_during_integration'], 0)
        self.assertIs(r['release_ready'], False)

    def test_run_identity_fail_closed(self):
        for k, v in [('id', True), ('head_sha', '0' * 40), ('head_branch', 'main'),
                     ('conclusion', 'failure'), ('status', 'in_progress'), ('event', 'workflow_dispatch'),
                     ('run_attempt', 2), ('path', '.github/workflows/ci.yml')]:
            with self.subTest(field=k), self.assertRaises(ValueError):
                self.check(run=self.run | {k: v})

    def test_foreign_repository(self):
        r = deepcopy(self.run); r['repository']['full_name'] = 'other/project'
        with self.assertRaises(ValueError): self.check(run=r)

    def test_archive_digest_size_and_run(self):
        for k, v in [('digest', 'sha256:' + '0' * 64), ('size_in_bytes', True), ('name', 'other')]:
            with self.subTest(field=k), self.assertRaises(ValueError):
                self.check(artifact=self.artifact | {k: v})
        a = deepcopy(self.artifact); a['workflow_run']['head_sha'] = '0' * 40
        with self.assertRaises(ValueError): self.check(artifact=a)

    def test_missing_or_failed_job(self):
        j = deepcopy(self.jobs); j['jobs'][0]['conclusion'] = 'failure'
        with self.assertRaises(ValueError): self.check(jobs=j)
        with self.assertRaises(ValueError): self.check(jobs={'jobs': [], 'total_count': 0})

    def test_skipped_required_step(self):
        j = deepcopy(self.jobs); j['jobs'][0]['steps'][2]['conclusion'] = 'skipped'
        with self.assertRaises(ValueError): self.check(jobs=j)

    def test_missing_member(self):
        self.mutate_files(lambda f: f.pop('normal-replace-0.stdout'))

    def test_unsafe_and_private_members(self):
        for name in ('../result.json', '/result.json', 'private.gba', 'save.srm', 'nested/result.json'):
            with self.subTest(name=name): self.mutate_files(lambda f: f.update({name: b'bad'}))

    def test_duplicate_member(self):
        b = io.BytesIO()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(b, 'w') as z:
                z.writestr('result.json', '{}'); z.writestr('result.json', '{}')
        with self.assertRaises(ValueError): subject.archive_members(b.getvalue())

    def test_symlink_member(self):
        b = io.BytesIO(); i = zipfile.ZipInfo('result.json'); i.external_attr = 0o120777 << 16
        with zipfile.ZipFile(b, 'w') as z: z.writestr(i, 'target')
        with self.assertRaises(ValueError): subject.archive_members(b.getvalue())

    def test_wrong_original_checkout(self):
        self.mutate_files(lambda f: f.update({'tested-head.txt': b'0' * 40}))

    def test_local_results_cannot_be_fixed_acceptance(self):
        self.mutate_report(lambda r: r.update(evidence_kind='LOCAL_DIAGNOSTIC'))

    def test_phase_promotion_and_fake_counts(self):
        for k, v in [('release_ready', True), ('full_p03_acceptance', True), ('full_p05_acceptance', True),
                     ('candidate_stage', 83), ('fresh_successful_mgba_processes', 45),
                     ('fresh_core_instances', 46), ('cache_reuse', False), ('product_rom_modified', True)]:
            with self.subTest(field=k): self.mutate_report(lambda r: r.update({k: v}))

    def test_missing_source_binding(self):
        self.mutate_report(lambda r: r['source_bindings'].pop(subject.suite.SOURCE))

    def test_changed_source_binding(self):
        self.mutate_report(lambda r: r['source_bindings'][subject.suite.SOURCE].update(sha256='0' * 64))

    def test_compiler_cannot_be_relabelled(self):
        self.mutate_report(lambda r: r.update(compiler='cc (Ubuntu) 13.3.0'))

    def test_missing_failed_toolchain_probe(self):
        for name in ('compile', 'fixed-toolchain', 'compiler-version'):
            with self.subTest(name=name):
                self.mutate_files(lambda f: f.update({name + '.process.json': b'{"returncode":false,"timed_out":false,"spawn_error":null}'}))

    def test_missing_case_and_duplicate_case(self):
        self.mutate_report(lambda r: r['cases'].pop())
        self.mutate_report(lambda r: r['cases'].__setitem__(1, deepcopy(r['cases'][0])))

    def test_summary_cannot_replace_raw_output(self):
        self.mutate_report(lambda r: r['cases'][0]['result'].update(pp_after=[1, 1, 1, 1]))

    def test_no_cold_continue_or_barrier(self):
        for key, value in [('fresh_core_normal_continue', False), ('host_write_barriers', 0)]:
            with self.subTest(key=key):
                def change(f):
                    r = subject.strict_json(f['normal-replace-0.stdout']); r[key] = value
                    f['normal-replace-0.stdout'] = json.dumps(r).encode()
                self.mutate_files(change)

    def test_guard_summary_and_real_rejection(self):
        self.mutate_report(lambda r: r['host_write_guard_checks'].pop())
        self.mutate_files(lambda f: f.update({'guard-bus8.stderr': b''}))

    def test_driver_incomplete_and_regression_failure(self):
        self.mutate_files(lambda f: f.update({'job.stderr.log': b'PASS normal-replace-0\n'}))
        self.mutate_files(lambda f: f.update({'regression.log': b'Ran 56 tests\nFAILED\n'}))

    def test_duplicate_json_and_output_hash(self):
        self.mutate_files(lambda f: f.update({'result.json': b'{"status":"FAIL",' + f['result.json'].lstrip()[1:]}))
        self.mutate_report(lambda r: r['cases'][0]['stdout'].update(sha256='0' * 64))

    def test_check_is_read_only(self):
        d = ROOT / subject.DIRECTORY
        before = {p.name: (subject.identity(p.read_bytes()), p.stat().st_mtime_ns) for p in d.iterdir()}
        subject.build()
        after = {p.name: (subject.identity(p.read_bytes()), p.stat().st_mtime_ns) for p in d.iterdir()}
        self.assertEqual(before, after)

if __name__ == '__main__': unittest.main()
