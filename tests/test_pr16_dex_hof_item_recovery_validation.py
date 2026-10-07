"""独立開発fixtureだけで回復の公開境界を検証。旧165試験・consumer/ROM生成は再走しない。"""
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
import pr16_dex_hof_item_recovery_validation as v


class RecoveryValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 開発fixtureであり、元runの失われたmeasurement原本とは主張しない。
        cls.proof_raw = (ROOT / v.DEVELOPMENT_PROOF).read_bytes()
        cls.proof = v.read_text(cls.proof_raw)
        with mock.patch('subprocess.Popen', side_effect=AssertionError('外部processは禁止')), \
             mock.patch.object(v.field, 'compose_selected', side_effect=AssertionError('consumer再実行は禁止')), \
             mock.patch.object(v.chain.d, 'inventory', side_effect=AssertionError('ROM全scanは禁止')):
            cls.parent = v.chain.parent(*[(ROOT / path).read_bytes() for path in v.chain.PARENT_INPUTS])
            # 型witnessの構築のみ。ROM・疎ROM・旧consumerの実行は行わない。
            region = v.chain.d.TypedRegion(v.field.HIT, v.field.HIT + 4, v.field.KIND,
                                            v.field.evidence_template())
            cls.delta = v.chain.canonical(v.chain.build(cls.parent, [region], cls.proof))
        cls.count = 24
        cls.bindings = {path: v.identity(('independent export fixture: ' + path).encode())
                        for path in sorted(v.SOURCE_CODE)}
        cls.bindings[v.DEV] = copy.deepcopy(v.DEV_IDENTITY)
        cls.bindings[v.DEVELOPMENT_PROOF] = copy.deepcopy(v.SCOPE_PROOF_IDENTITY)
        cls.context = dict(source_head='1' * 40, run_id=123456789,
                           expected_bindings=cls.bindings, recovery_test_count=cls.count)
        cls.log_identity = v.identity(b'independent synthetic source job log fixture\n')
        cls.report = v.measured_report(cls.proof, cls.delta, **cls.context)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / 'public'
        self.directory.mkdir()
        self.write('measurement.json', self.report)
        (self.directory / 'reference-chain.json').write_bytes(self.delta)
        self.write('tests.json', v.test_summary(self.count))
        self.write('provenance.json', v.provenance(self.report, inherited_log_identity=self.log_identity))

    def write(self, name, value):
        (self.directory / name).write_bytes(v.chain.canonical(value))

    def validate(self, **kwargs):
        return v.validate_output(self.directory, self.parent, **self.context,
                                 inherited_log_identity=self.log_identity,
                                 log=kwargs.pop('log', io.StringIO()), **kwargs)

    def reject(self):
        with self.assertRaises((ValueError, UnicodeError, OSError)):
            self.validate()

    def pad(self, name, size):
        path = self.directory / name
        raw = path.read_bytes()
        self.assertLessEqual(len(raw), size)
        path.write_bytes(raw[:-1] + b' ' * (size - len(raw)) + b'\n')

    def test_development_fixture_identity_is_not_lost_original(self):
        self.assertEqual(v.identity(self.proof_raw), v.SCOPE_PROOF_IDENTITY)
        self.assertEqual(v._development()['scope_proof_identity'], v.identity(self.proof_raw))
        p = v.provenance(self.report, inherited_log_identity=self.log_identity)
        self.assertIs(p['independent_development_fixture']['is_current_rom_measurement'], False)
        self.assertIs(p['independent_development_fixture']['is_lost_output_original'], False)
        self.assertIs(p['original_failed_run']['original_output_hashes_available'], False)
        self.assertIs(p['original_failed_run']['original_output_size_logged'], False)
        self.assertNotIn('measurement_output_bytes', p['original_failed_run'])
        self.assertEqual(p['independent_development_fixture']['reconstructed_measurement_size'], 770711)
        self.assertIs(p['independent_development_fixture']['original_size_logged'], False)

    def test_valid_report_and_all_four_texts(self):
        self.assertTrue(v.validate_report(self.report, self.delta, self.parent, **self.context))
        self.assertEqual(set(self.validate()), v.FILES)
        self.assertEqual(len(v.SOURCE_CODE), 20)
        self.assertEqual(len(v.INHERITED_CODE), 14)

    def test_770711_bytes_no_longer_fails_export(self):
        self.pad('measurement.json', 770711)
        identities = self.validate()
        self.assertEqual(identities['measurement.json']['size'], 770711)

    def test_750000_old_boundary_has_no_special_rejection(self):
        for size in (749999, 750000, 750001):
            with self.subTest(size=size):
                self.write('measurement.json', self.report)
                self.pad('measurement.json', size)
                self.assertEqual(self.validate()['measurement.json']['size'], size)

    def test_1500000_bytes_inclusive_maximum(self):
        self.pad('measurement.json', 1_500_000)
        self.assertEqual(self.validate()['measurement.json']['size'], 1_500_000)

    def test_each_file_over_1500000_is_rejected(self):
        for name in sorted(v.FILES):
            with self.subTest(name=name):
                old = (self.directory / name).read_bytes()
                self.pad(name, 1_500_001)
                self.reject()
                (self.directory / name).write_bytes(old)

    def test_closed_four_file_set_missing_and_extra(self):
        for name in sorted(v.FILES):
            path = self.directory / name
            original = path.read_bytes()
            path.unlink()
            with self.subTest(missing=name):
                self.reject()
            path.write_bytes(original)
        extra = self.directory / 'unapproved.json'
        extra.write_bytes(b'{}\n')
        self.reject()

    def test_nonregular_file_and_extra_directory_rejected(self):
        path = self.directory / 'tests.json'
        original = path.read_bytes()
        path.unlink()
        path.mkdir()
        self.reject()
        path.rmdir()
        path.write_bytes(original)
        (self.directory / 'nested').mkdir()
        self.reject()

    def test_file_symlink_is_rejected(self):
        path = self.directory / 'tests.json'
        target = self.directory.parent / 'tests-source.json'
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
        self.reject()

    def test_directory_and_ancestor_symlinks_are_rejected(self):
        alias = self.directory.parent / 'alias'
        alias.symlink_to(self.directory, target_is_directory=True)
        old = self.directory
        self.directory = alias
        self.reject()
        self.directory = old
        ancestor = self.directory.parent / 'ancestor'
        ancestor.symlink_to(self.directory.parent, target_is_directory=True)
        self.directory = ancestor / 'public'
        self.reject()

    def test_utf8_lf_nul_and_empty_boundaries(self):
        path = self.directory / 'tests.json'
        original = path.read_bytes()
        for raw in (b'', original.rstrip(b'\n'), original + b'\r\n', original + b'\0\n', b'\xff\n'):
            with self.subTest(raw=raw[:12]):
                path.write_bytes(raw)
                self.reject()

    def test_duplicate_keys_and_nonfinite_json_rejected(self):
        for raw in (b'{"a":1,"a":1}\n', b'{"x":{"a":1,"a":1}}\n',
                    b'{"a":NaN}\n', b'{"a":Infinity}\n', b'{"a":-Infinity}\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                v.read_text(raw)

    def test_report_missing_extra_and_old_schema_rejected(self):
        for key in self.report:
            bad = dict(self.report)
            bad.pop(key)
            with self.subTest(missing=key), self.assertRaises(ValueError):
                v.validate_report(bad, self.delta, self.parent, **self.context)
        for key, value in [('raw', 'unapproved'), ('unit_tests', 165),
                           ('status', 'PASS_CURRENT_ROOTED_ITEM_EXCHANGE_MAIL_MINIMUM_TYPE')]:
            bad = dict(self.report, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.validate_report(bad, self.delta, self.parent, **self.context)

    def test_report_integer_bool_and_float_aliases_rejected(self):
        for key, value in self.report.items():
            if type(value) is not int:
                continue
            for alias in (bool(value), float(value)):
                bad = dict(self.report, **{key: alias})
                with self.subTest(key=key, alias=alias), self.assertRaises(ValueError):
                    v.validate_report(bad, self.delta, self.parent, **self.context)
        for key in ('candidate', 'delta_identity', 'development_identity'):
            bad = copy.deepcopy(self.report)
            bad[key]['size'] = float(bad[key]['size'])
            with self.subTest(nested=key), self.assertRaises(ValueError):
                v.validate_report(bad, self.delta, self.parent, **self.context)

    def test_boolean_flags_and_safety_claims_rejected(self):
        for key, value in self.report.items():
            if type(value) is not bool:
                continue
            for bad_value in (not value, int(value)):
                bad = dict(self.report, **{key: bad_value})
                with self.subTest(key=key), self.assertRaises(ValueError):
                    v.validate_report(bad, self.delta, self.parent, **self.context)

    def test_changed_scope_proof_cannot_self_approve(self):
        bad = copy.deepcopy(self.report)
        bad['scope_proof']['cases'][0]['text_read_bytes'] += 1
        with self.assertRaises(ValueError):
            v.validate_report(bad, self.delta, self.parent, **self.context)
        bad = copy.deepcopy(self.report)
        bad['scope_proof']['unapproved'] = 'private'
        with self.assertRaises(ValueError):
            v.validate_report(bad, self.delta, self.parent, **self.context)

    def test_changed_chain_and_recomputed_identity_rejected(self):
        original = json.loads(self.delta)
        mutations = [('proof', dict(original['proof'], unapproved=False)), ('classified', 782),
                     ('newly_classified', True), ('donor_eligible', True)]
        for key, value in mutations:
            delta = copy.deepcopy(original)
            delta[key] = value
            delta['proof_identity'] = v.identity(v.chain.canonical(delta['proof']))
            raw = v.chain.canonical(delta)
            report = dict(self.report, delta_identity=v.identity(raw))
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.validate_report(report, raw, self.parent, **self.context)

    def test_current_run_and_inherited_source_identity_rejected(self):
        for key, value in [('source_head', '2' * 40), ('run_id', 987),
                           ('inherited_source_head', '3' * 40), ('inherited_measurement_run', 1),
                           ('inherited_scope_tests', 164), ('old_scope_test_reruns', 165)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.validate_report(dict(self.report, **{key: value}), self.delta, self.parent, **self.context)
        for key, value in [('source_head', v.INHERITED_SOURCE_HEAD), ('run_id', v.INHERITED_MEASUREMENT_RUN),
                           ('source_head', 'not-a-head'), ('run_id', True), ('recovery_test_count', 0)]:
            context = dict(self.context, **{key: value})
            with self.subTest(context=key), self.assertRaises(ValueError):
                v.measured_report(self.proof, self.delta, **context)

    def test_source_binding_unknown_missing_and_typed_mutations(self):
        for bindings in ({}, {**self.bindings, 'unknown.py': v.identity(b'x')}):
            with self.assertRaises(ValueError):
                v.measured_report(self.proof, self.delta, **dict(self.context, expected_bindings=bindings))
        for path in (v.DEV, v.DEVELOPMENT_PROOF):
            bindings = copy.deepcopy(self.bindings)
            bindings[path]['sha256'] = '0' * 64
            with self.subTest(path=path), self.assertRaises(ValueError):
                v.measured_report(self.proof, self.delta, **dict(self.context, expected_bindings=bindings))
        for key in ('source_bindings', 'public_source_bindings'):
            bad = copy.deepcopy(self.report)
            next(iter(bad[key].values()))['size'] += 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.validate_report(bad, self.delta, self.parent, **self.context)
        bad = copy.deepcopy(self.bindings)
        next(iter(bad.values()))['size'] = True
        with self.assertRaises(ValueError):
            v.measured_report(self.proof, self.delta, **dict(self.context, expected_bindings=bad))

    def test_closed_test_summary_and_bool_alias(self):
        summary = v.test_summary(self.count)
        for key, value in [('recovery_test_count', self.count + 1), ('failures', False),
                           ('old_scope_test_reruns', 165), ('unapproved', 1)]:
            with self.subTest(key=key):
                self.write('tests.json', dict(summary, **{key: value}))
                self.reject()

    def test_provenance_closed_and_original_failure_not_rewritten(self):
        original = v.provenance(self.report, inherited_log_identity=self.log_identity)
        mutations = [(['original_failed_run', 'run_conclusion'], 'success'),
                     (['original_failed_run', 'artifact_count'], False),
                     (['original_failed_run', 'original_output_hashes_available'], True),
                     (['original_failed_run', 'job_log_identity', 'sha256'], '0' * 64),
                     (['inherited_scope', 'source_files_unchanged'], 13),
                     (['current_remeasurement', 'current_rom_reconstructions'], 0),
                     (['reconstructed_text_is_original'], True), (['unapproved'], 'private')]
        for keys, value in mutations:
            bad = copy.deepcopy(original)
            target = bad
            for key in keys[:-1]:
                target = target[key]
            target[keys[-1]] = value
            with self.subTest(keys=keys):
                self.write('provenance.json', bad)
                self.reject()

    def test_failed_validation_never_prints_public_hashes(self):
        log = io.StringIO()
        self.write('tests.json', dict(v.test_summary(self.count), errors=1))
        with self.assertRaises(ValueError):
            self.validate(log=log)
        self.assertEqual(log.getvalue(), '')

    def test_every_success_file_hash_is_logged_before_upload(self):
        log = io.StringIO()
        identities = self.validate(log=log)
        lines = [json.loads(line) for line in log.getvalue().splitlines()]
        self.assertEqual(len(lines), 4)
        self.assertEqual([row['file'] for row in lines], sorted(v.FILES))
        for row in lines:
            self.assertEqual(row, dict(status='PASS_JP_ITEM_RECOVERY_PUBLIC_FILE', file=row['file'],
                                       **v.identity((self.directory / row['file']).read_bytes())))
            self.assertEqual(identities[row['file']], {key: row[key] for key in ('size', 'sha256')})

    def test_cumulative_work_and_formal_frontier_are_kept_separate(self):
        self.assertEqual((self.report['current_rom_reconstructions'],
                          self.report['cumulative_scope_rom_reconstructions'],
                          self.report['consumer_remeasurements']), (1, 2, 2))
        self.assertEqual((self.report['classified'], self.report['unclassified'],
                          self.report['newly_classified']), (781, 93, 1))
        self.assertEqual((self.report['formal_classified_before_recovery'],
                          self.report['formal_unclassified_before_recovery']), (780, 94))
        self.assertEqual(self.report['recovery_test_count'], self.count)
        self.assertEqual(self.report['inherited_scope_tests'], 165)
        self.assertEqual(self.report['old_scope_test_reruns'], 0)
        self.assertEqual(self.report['native_processes'], 0)
        self.assertEqual(self.report['donor_safe_bytes'], 0)


if __name__ == '__main__':
    unittest.main()
