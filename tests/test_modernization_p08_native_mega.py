"""Original-backed mutation tests; no synthetic result is an emulator run."""
import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('m5_evidence', Path(__file__).resolve().parents[1] / 'scripts/check_modernization_p08_native_mega.py')
e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e)


class OriginalEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = e.regular(e.ROOT, e.DIRECTORY + '/original.zip')
        cls.actions = e.load(e.regular(e.ROOT, e.DIRECTORY + '/actions.json'))
        cls.files = e.unpack(cls.raw)

    def test_original_and_scoped_acceptance(self):
        report = e.check()
        self.assertEqual(report['accepted_original_processes'], 42)
        self.assertEqual(report['accepted_original_core_instances'], 48)
        self.assertIs(report['release_ready'], False)
        self.assertEqual(report['new_emulator_runs_during_integration'], 0)

    def test_original_zip_bytes_are_pinned(self):
        for bad in (self.raw[:-1], self.raw + b'X', b'not a zip'):
            with self.assertRaises(ValueError):
                e.unpack(bad)

    def test_wrong_actions_identity_or_conclusion(self):
        for key, value in self.actions.items():
            if key == 'steps':
                continue
            bad = dict(self.actions)
            bad[key] = False if type(value) is int else 'wrong'
            with self.subTest(key=key), self.assertRaises(ValueError):
                e.validate_actions(bad)

    def test_required_execution_steps(self):
        for index in range(len(e.STEPS)):
            bad = copy.deepcopy(self.actions)
            bad['steps'][index]['conclusion'] = 'failure'
            with self.assertRaises(ValueError):
                e.validate_actions(bad)
        bad = copy.deepcopy(self.actions)
        bad['steps'].append(bad['steps'][0])
        with self.assertRaises(ValueError):
            e.validate_actions(bad)

    def test_exit_head_and_toolchain(self):
        for key, value in (('native-exit-code.txt', b'false\n'), ('native-exit-code.txt', b'-11\n'),
                           ('tested-head.txt', b'wrong\n'), ('toolchain.stdout', b'14.2.0'),
                           ('fixed-toolchain.log', b'PASS'), ('compile.stderr', b'warning'),
                           ('job.stderr.log', b'traceback')):
            bad = dict(self.files, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                e.validate_payload(bad)

    def test_counter_and_release_overclaims(self):
        for key, value in (('fresh_process_runs', 41), ('cache_reuse', 1), ('core_instances', 42),
                           ('full_p05_acceptance', True), ('release_ready', True),
                           ('natural_capture_or_facility_entry', True), ('candidate_stage', 81)):
            bad = dict(self.files)
            obj = e.load(bad['result.json'])
            obj[key] = value
            bad['result.json'] = bad['job.stdout.json'] = e.stable(obj)
            with self.subTest(key=key), self.assertRaises(ValueError):
                e.validate_payload(bad)

    def test_original_case_not_summary_alone(self):
        bad = dict(self.files)
        obj = e.load(bad['dragonize--active.stdout'])
        obj['cold_save_all_100_party_bytes_equal'] = False
        bad['dragonize--active.stdout'] = e.stable(obj)
        with self.assertRaises(ValueError):
            e.validate_payload(bad)

    def test_source_binding_and_live_source(self):
        bad = dict(self.files)
        bad['sources/' + e.runtime.SOURCE] += b'\n'
        with self.assertRaises(ValueError):
            e.validate_payload(bad)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
            e.validate_payload(self.files, Path(tmp))

    def test_guard_negative_cannot_be_missing(self):
        for guard in e.runtime.GUARDS:
            bad = dict(self.files)
            bad['guard-' + guard + '.stderr'] = b''
            with self.assertRaises(ValueError):
                e.validate_payload(bad)

    def test_case_coverage_and_job_report_match(self):
        for filename in ('result.json', 'job.stdout.json'):
            bad = dict(self.files)
            obj = e.load(bad[filename])
            obj['cases'].pop()
            bad[filename] = e.stable(obj)
            with self.assertRaises(ValueError):
                e.validate_payload(bad)

    def test_readonly_check(self):
        names = (e.DIRECTORY + '/original.zip', e.DIRECTORY + '/actions.json', e.REPORT)
        before = {n: ((e.ROOT/n).read_bytes(), (e.ROOT/n).stat().st_mtime_ns) for n in names}
        e.check()
        self.assertEqual(before, {n: ((e.ROOT/n).read_bytes(), (e.ROOT/n).stat().st_mtime_ns) for n in names})

    def test_existing_evidence_not_overwritten(self):
        before = (e.ROOT/e.REPORT).read_bytes()
        with self.assertRaises(ValueError):
            e.import_evidence(self.raw, self.actions)
        self.assertEqual(before, (e.ROOT/e.REPORT).read_bytes())

    def test_symlink_and_parent_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'link').symlink_to(e.ROOT/e.REPORT)
            for name in ('link', '../escape', '/absolute', 'a//b'):
                with self.assertRaises(ValueError):
                    e.regular(root, name)

    def test_duplicate_json(self):
        with self.assertRaises(ValueError):
            e.load(b'{"status":"PASS","status":"FAIL"}')


if __name__ == '__main__':
    unittest.main()
