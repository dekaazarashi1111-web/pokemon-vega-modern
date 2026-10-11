"""Diplomaだけのproducer/厳密4JSON公開境界。旧suite・ROM再構成・nativeは呼ばない。"""
import copy
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
import pr16_dex_hof_diploma_validation as v


class DiplomaPublicBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof_raw = (ROOT / v.DEVELOPMENT_PROOF).read_bytes()
        cls.proof = v.read_text(cls.proof_raw)
        cls.count = v.development()['unit_tests']
        cls.bindings = v.bindings()
        cls.context = dict(source_head='1' * 40, run_id=123456789,
                           expected_bindings=cls.bindings, test_count=cls.count)
        with mock.patch('subprocess.Popen', side_effect=AssertionError('外部processは禁止')), \
             mock.patch.object(v.field, 'compose', side_effect=AssertionError('旧/現consumerを再実行しない')), \
             mock.patch.object(v.chain.d, 'inventory', side_effect=AssertionError('ROM全scanは禁止')):
            cls.parent = v.chain.parent(*[(ROOT / path).read_bytes() for path in v.chain.PARENT_INPUTS])
            region = v.chain.d.TypedRegion(v.field.HIT, v.field.HIT + 4, v.field.KIND, v.field.evidence_template())
            cls.delta = v.chain.canonical(v.chain.build(cls.parent, [region], cls.proof))
        cls.report = v.measured_report(cls.proof, cls.delta, **cls.context)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / 'public'
        self.generated = io.StringIO()
        v.write_output(self.directory, self.report, self.delta, log=self.generated)

    def write(self, name, value):
        (self.directory / name).write_bytes(v.json_bytes(value))

    def validate(self, log=None):
        return v.validate_output(self.directory, self.parent, **self.context,
                                 log=io.StringIO() if log is None else log)

    def reject(self):
        with self.assertRaises((ValueError, UnicodeError, OSError, KeyError, TypeError)):
            self.validate()

    def pad(self, name, size):
        path = self.directory / name
        raw = path.read_bytes()
        self.assertLessEqual(len(raw), size)
        path.write_bytes(raw[:-1] + b' ' * (size - len(raw)) + b'\n')

    def test_valid_real_four_file_write_readback(self):
        self.assertTrue(v.validate_report(self.report, self.delta, self.parent, **self.context))
        self.assertEqual(set(self.validate()), v.FILES)
        self.assertTrue(v.exact(v.read_text((self.directory / 'measurement.json').read_bytes()), self.report))

    def test_independent_development_not_actual_measurement(self):
        self.assertIs(v.development()['current_rom_measured'], False)
        self.assertEqual(v.identity(self.proof_raw), self.report['development_proof_identity'])
        self.assertIs(v.provenance(self.report)['independent_development_fixture']['is_current_rom_measurement'], False)
        with self.assertRaises(ValueError):
            v.validate_report(v.development(), self.delta, self.parent, **self.context)
        with self.assertRaises(ValueError):
            v.validate_report(dict(self.report, measurement_origin='independent_development_fixture'),
                              self.delta, self.parent, **self.context)

    def test_actual_producer_to_normalized_report_and_four_files(self):
        from test_pr16_dex_hof_diploma_asset import fixture
        asset = v.sources.diploma_asset(v.sources.load_sources())['consumed']
        with mock.patch('subprocess.Popen', side_effect=AssertionError('外部processは禁止')), \
             mock.patch.object(v.chain.d, 'inventory', side_effect=AssertionError('ROM全scanは禁止')):
            regions, raw_proof = v.field._regions(fixture(asset=asset), self.parent)
        self.assertEqual(raw_proof['hit'], 0x083DCAED)
        self.assertEqual(raw_proof['consumer']['phase_steps'], self.proof['consumer']['phase_steps'])
        self.assertEqual(v.identity(v.chain.canonical(raw_proof)), v.identity(self.proof_raw))
        before = copy.deepcopy(raw_proof)
        delta = v.chain.canonical(v.chain.build(self.parent, regions, raw_proof))
        report = v.measured_report(raw_proof, delta, **self.context)
        self.assertEqual(raw_proof, before)
        self.assertTrue(v.exact(report['scope_proof'], self.proof))
        self.assertTrue(v.validate_report(report, delta, self.parent, **self.context))
        directory = Path(self.tmp.name) / 'actual-public'
        generated = v.write_output(directory, report, delta, log=io.StringIO())
        validated = v.validate_output(directory, self.parent, **self.context, log=io.StringIO())
        self.assertEqual(generated, validated)
        self.assertTrue(v.exact(v.read_text((directory / 'measurement.json').read_bytes()), report))
        self.assertTrue(all(row['size'] < v.MAX_FILE_BYTES for row in generated.values()))

    def test_internal_tuple_normalization_does_not_weaken_public_exact(self):
        raw = copy.deepcopy(self.proof)
        raw['consumer']['calls'] = tuple(raw['consumer']['calls'])
        report = v.measured_report(raw, self.delta, **self.context)
        self.assertIs(type(raw['consumer']['calls']), tuple)
        self.assertIs(type(report['scope_proof']['consumer']['calls']), list)
        self.assertTrue(v.validate_report(report, self.delta, self.parent, **self.context))
        report['scope_proof']['consumer']['calls'] = tuple(report['scope_proof']['consumer']['calls'])
        with self.assertRaises(ValueError):
            v.validate_report(report, self.delta, self.parent, **self.context)
        self.assertFalse(v.exact((1, 2), [1, 2]))

    def test_estimated_output_fits_with_explicit_headroom(self):
        # 実runnerと同じindent=2/UTF8/LFを使い、旧750k事故を再発させない。
        sizes = {name: (self.directory / name).stat().st_size for name in v.FILES}
        self.assertTrue(all(0 < size <= 1_350_000 for size in sizes.values()), sizes)
        self.assertEqual(v.MAX_FILE_BYTES, 1_500_000)

    def test_old_750k_and_770711_boundaries_are_accepted(self):
        original = (self.directory / 'tests.json').read_bytes()
        for size in (749999, 750000, 750001, 770711):
            with self.subTest(size=size):
                (self.directory / 'tests.json').write_bytes(original)
                self.pad('tests.json', size)
                self.assertEqual(self.validate()['tests.json']['size'], size)

    def test_1500000_inclusive_boundary(self):
        self.pad('measurement.json', 1_500_000)
        self.assertEqual(self.validate()['measurement.json']['size'], 1_500_000)

    def test_each_file_above_limit_is_rejected(self):
        for name in sorted(v.FILES):
            raw = (self.directory / name).read_bytes()
            with self.subTest(name=name):
                self.pad(name, 1_500_001)
                self.reject()
            (self.directory / name).write_bytes(raw)

    def test_closed_files_missing_extra(self):
        for name in sorted(v.FILES):
            path = self.directory / name
            raw = path.read_bytes()
            path.unlink()
            with self.subTest(missing=name):
                self.reject()
            path.write_bytes(raw)
        (self.directory / 'extra.json').write_bytes(b'{}\n')
        self.reject()

    def test_directory_and_nonregular_output_refused(self):
        path = self.directory / 'tests.json'
        raw = path.read_bytes()
        path.unlink()
        path.mkdir()
        self.reject()
        path.rmdir()
        path.write_bytes(raw)
        (self.directory / 'nested').mkdir()
        self.reject()

    def test_file_symlink_refused(self):
        path = self.directory / 'tests.json'
        target = self.directory.parent / 'actual.json'
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
        self.reject()

    def test_directory_ancestor_symlinks_refused(self):
        alias = self.directory.parent / 'alias'
        alias.symlink_to(self.directory, target_is_directory=True)
        original = self.directory
        self.directory = alias
        self.reject()
        ancestor = original.parent / 'ancestor'
        ancestor.symlink_to(original.parent, target_is_directory=True)
        self.directory = ancestor / 'public'
        self.reject()

    def test_writer_refuses_existing_or_symlink_directory(self):
        with self.assertRaises(FileExistsError):
            v.write_output(self.directory, self.report, self.delta, log=io.StringIO())
        alias = self.directory.parent / 'alias'
        alias.symlink_to(self.directory, target_is_directory=True)
        with self.assertRaises(ValueError):
            v.write_output(alias, self.report, self.delta, log=io.StringIO())

    def test_empty_utf8_lf_cr_nul_boundaries(self):
        path = self.directory / 'tests.json'
        raw = path.read_bytes()
        for bad in (b'', raw.rstrip(b'\n'), raw + b'\r\n', raw + b'\0\n', b'\xff\n'):
            with self.subTest(raw=bad[:16]):
                path.write_bytes(bad)
                self.reject()

    def test_duplicate_keys_nonfinite_json_refused(self):
        for raw in (b'{"a":1,"a":1}\n', b'{"x":{"a":1,"a":2}}\n',
                    b'{"a":1.0}\n', b'{"a":1e0}\n',
                    b'{"a":NaN}\n', b'{"a":Infinity}\n', b'{"a":-Infinity}\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                v.read_text(raw)

    def test_report_missing_extra_wrong_status_refused(self):
        for key in self.report:
            bad = dict(self.report)
            bad.pop(key)
            with self.subTest(missing=key), self.assertRaises(ValueError):
                v.validate_report(bad, self.delta, self.parent, **self.context)
        for key, value in [('raw_hex', 'private'), ('status', 'PASS_OLD_SCOPE')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.validate_report(dict(self.report, **{key: value}), self.delta, self.parent, **self.context)

    def test_integer_bool_float_aliases_refused(self):
        for key, value in self.report.items():
            if type(value) is int:
                for alias in (bool(value), float(value)):
                    with self.subTest(key=key, alias=alias), self.assertRaises(ValueError):
                        v.validate_report(dict(self.report, **{key: alias}), self.delta, self.parent, **self.context)
        for key in ('candidate', 'delta_identity', 'development_identity', 'development_proof_identity'):
            bad = copy.deepcopy(self.report)
            bad[key]['size'] = float(bad[key]['size'])
            with self.subTest(nested=key), self.assertRaises(ValueError):
                v.validate_report(bad, self.delta, self.parent, **self.context)

    def test_safety_claims_and_bool_integer_aliases_refused(self):
        for key, value in self.report.items():
            if type(value) is bool:
                for bad_value in (not value, int(value)):
                    with self.subTest(key=key, value=bad_value), self.assertRaises(ValueError):
                        v.validate_report(dict(self.report, **{key: bad_value}), self.delta, self.parent, **self.context)

    def test_changed_or_unapproved_proof_refused(self):
        for key, value in [('raw_hex', 'private'), ('newly_classified', 2), ('donor_eligible', True)]:
            bad = copy.deepcopy(self.report)
            bad['scope_proof'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.validate_report(bad, self.delta, self.parent, **self.context)
        bad = copy.deepcopy(self.report)
        bad['scope_proof']['consumer']['phase_steps'][0] += 1
        with self.assertRaises(ValueError):
            v.validate_report(bad, self.delta, self.parent, **self.context)

    def test_changed_delta_with_recomputed_hash_refused(self):
        original = v.read_text(self.delta)
        for key, value in [('classified', 784), ('newly_classified', True), ('donor_eligible', True),
                           ('proof', dict(original['proof'], extra='private'))]:
            bad = copy.deepcopy(original)
            bad[key] = value
            bad['proof_identity'] = v.identity(v.chain.canonical(bad['proof']))
            raw = v.chain.canonical(bad)
            report = dict(self.report, delta_identity=v.identity(raw))
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.validate_report(report, raw, self.parent, **self.context)

    def test_wrong_run_head_and_counts_refused(self):
        for key, value in [('source_head', '2' * 40), ('run_id', 987), ('unit_tests', self.count + 1),
                           ('inherited_classified', 780), ('inherited_unclassified', 94), ('old_scope_test_reruns', 165)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.validate_report(dict(self.report, **{key: value}), self.delta, self.parent, **self.context)
        for key, value in [('source_head', 'bad'), ('run_id', True), ('run_id', 0),
                           ('test_count', 0), ('test_count', self.count + 1)]:
            with self.subTest(context=key), self.assertRaises(ValueError):
                v.measured_report(self.proof, self.delta, **dict(self.context, **{key: value}))

    def test_source_bindings_missing_extra_mutated_refused(self):
        for bindings in ({}, {**self.bindings, 'extra': v.identity(b'x')}):
            with self.assertRaises(ValueError):
                v.measured_report(self.proof, self.delta, **dict(self.context, expected_bindings=bindings))
        for path in sorted(v.SOURCE_CODE):
            bindings = copy.deepcopy(self.bindings)
            bindings[path]['sha256'] = '0' * 64
            with self.subTest(path=path), self.assertRaises(ValueError):
                v.measured_report(self.proof, self.delta, **dict(self.context, expected_bindings=bindings))

    def test_public_source_and_binding_type_mutations_refused(self):
        for key in ('source_bindings', 'public_source_bindings'):
            bad = copy.deepcopy(self.report)
            next(iter(bad[key].values()))['size'] += 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.validate_report(bad, self.delta, self.parent, **self.context)
        bindings = copy.deepcopy(self.bindings)
        next(iter(bindings.values()))['size'] = True
        with self.assertRaises(ValueError):
            v.measured_report(self.proof, self.delta, **dict(self.context, expected_bindings=bindings))

    def test_closed_summary_with_strict_counter_types(self):
        for key, value in [('tests', self.count + 1), ('failures', False), ('errors', 1),
                           ('skipped', 1), ('old_scope_test_reruns', 27), ('unapproved', 'private')]:
            with self.subTest(key=key):
                self.write('tests.json', dict(v.test_summary(self.count), **{key: value}))
                self.reject()

    def test_closed_provenance_and_no_fixture_promotion(self):
        original = v.provenance(self.report)
        mutations = [(['current_measurement', 'current_rom_reconstructions'], 0),
                     (['current_measurement', 'delta_identity', 'sha256'], '0' * 64),
                     (['inherited_frontier', 'classified'], 780),
                     (['inherited_frontier', 'saved_input_count'], 55),
                     (['inherited_frontier', 'reference_stages'], 28),
                     (['inherited_frontier', 'restored_parent_identity', 'sha256'], '0' * 64),
                     (['independent_development_fixture', 'is_current_rom_measurement'], True),
                     (['formal_save_changed'], True), (['donor_eligible'], True), (['unapproved'], 'private')]
        for keys, value in mutations:
            bad = copy.deepcopy(original)
            target = bad
            for key in keys[:-1]:
                target = target[key]
            target[keys[-1]] = value
            with self.subTest(keys=keys):
                self.write('provenance.json', bad)
                self.reject()

    def test_generated_identities_are_logged_before_any_validator(self):
        rows = [json.loads(line) for line in self.generated.getvalue().splitlines()]
        self.assertEqual([row['file'] for row in rows], sorted(v.FILES))
        for row in rows:
            self.assertEqual(row, dict(status='GENERATED_DIPLOMA_FILE_IDENTITY', file=row['file'],
                                      **v.identity((self.directory / row['file']).read_bytes())))
        self.write('tests.json', dict(v.test_summary(self.count), errors=1))
        log = io.StringIO()
        with self.assertRaises(ValueError):
            self.validate(log=log)
        self.assertEqual(log.getvalue(), '')
        self.assertEqual(len(rows), 4)

    def test_validated_identities_are_logged_before_publication(self):
        log = io.StringIO()
        identities = self.validate(log=log)
        rows = [json.loads(line) for line in log.getvalue().splitlines()]
        self.assertEqual([row['file'] for row in rows], sorted(v.FILES))
        for row in rows:
            self.assertEqual(row, dict(status='PASS_DIPLOMA_PUBLIC_FILE', file=row['file'],
                                      **identities[row['file']]))

    def test_frontier_and_no_runtime_or_donor_claims(self):
        self.assertEqual((self.report['inherited_classified'], self.report['inherited_unclassified']), (782, 92))
        self.assertEqual((self.report['classified'], self.report['unclassified'], self.report['newly_classified']), (783, 91, 1))
        self.assertEqual((self.report['current_rom_reconstructions'], self.report['current_owner_count'], self.report['saved_hit_count']), (1, 115, 874))
        self.assertEqual(self.report['current_saved_hits_rebound'], 874)
        self.assertEqual([self.report[key] for key in ('inherited_saved_inputs', 'inherited_reference_stages',
                         'inherited_changes', 'inherited_witnesses')], [57, 29, 163, 153])
        inherited = v.provenance(self.report)['inherited_frontier']
        self.assertEqual(len(inherited['saved_input_identities']), 57)
        self.assertEqual(inherited['restored_parent_identity'], v.chain.PARENT_AUDIT_ID)
        self.assertEqual(self.report['old_scope_test_reruns'], 0)
        self.assertEqual(self.report['native_processes'], 0)
        self.assertEqual(self.report['donor_safe_bytes'], 0)
        self.assertIs(v.provenance(self.report)['actual_runtime_execution_observed'], False)


class DevelopmentBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.proof_raw = (ROOT / v.DEVELOPMENT_PROOF).read_bytes()
        self.dev = dict(status='PASS_INDEPENDENT_DIPLOMA_ASSET_DEVELOPMENT',
            candidate=copy.deepcopy(v.field.CANDIDATE), scope_proof_identity=v.identity(self.proof_raw),
            unit_tests=101, current_rom_measured=False, formal_classified=782, formal_unclassified=92,
            proposed_new_types=1, old_scope_test_reruns=0, native_processes=0, donor_safe_bytes=0,
            formal_rom_changed=False, formal_save_changed=False,
            source_head_before_development='1' * 40, scope_ja='公開PNGから生成した独立fixture。現ROM実測ではない。')
        (self.root / v.DEV).parent.mkdir(parents=True)
        (self.root / v.DEVELOPMENT_PROOF).write_bytes(self.proof_raw)
        self.save(self.dev)
        patcher = mock.patch.object(v, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def save(self, value):
        (self.root / v.DEV).write_bytes(v.json_bytes(value))

    def test_closed_independent_development(self):
        self.assertTrue(v.exact(v.development(), self.dev))
        self.assertEqual(set(self.dev), v.DEVELOPMENT_FIELDS)

    def test_development_unknown_and_missing_fields(self):
        for key in self.dev:
            bad = dict(self.dev)
            del bad[key]
            self.save(bad)
            with self.subTest(missing=key), self.assertRaises(ValueError):
                v.development()
        self.save(dict(self.dev, extra='private'))
        with self.assertRaises(ValueError):
            v.development()

    def test_development_cannot_promote_measurement_or_frontier(self):
        for key, value in [('current_rom_measured', True), ('formal_classified', 783),
                           ('formal_unclassified', 91), ('proposed_new_types', 2),
                           ('native_processes', 1), ('old_scope_test_reruns', 1),
                           ('donor_safe_bytes', 4), ('formal_rom_changed', True),
                           ('formal_save_changed', True), ('status', 'PASS_CURRENT_ROOTED_DIPLOMA_MINIMUM_TYPE')]:
            self.save(dict(self.dev, **{key: value}))
            with self.subTest(key=key), self.assertRaises(ValueError):
                v.development()

    def test_development_bool_integer_float_aliases(self):
        for key, value in self.dev.items():
            if type(value) not in (int, bool):
                continue
            for alias in ([bool(value), float(value)] if type(value) is int else [int(value), float(value)]):
                self.save(dict(self.dev, **{key: alias}))
                with self.subTest(key=key, alias=alias), self.assertRaises(ValueError):
                    v.development()
        for value in (0, -1, '101'):
            self.save(dict(self.dev, unit_tests=value))
            with self.subTest(count=value), self.assertRaises(ValueError):
                v.development()

    def test_development_hash_and_noncanonical_proof(self):
        self.save(dict(self.dev, scope_proof_identity=dict(size=len(self.proof_raw), sha256='0' * 64)))
        with self.assertRaises(ValueError):
            v.development()
        raw = v.json_bytes(v.read_text(self.proof_raw))
        self.assertNotEqual(raw, self.proof_raw)
        (self.root / v.DEVELOPMENT_PROOF).write_bytes(raw)
        self.save(dict(self.dev, scope_proof_identity=v.identity(raw)))
        with self.assertRaises(ValueError):
            v.development()

    def test_development_source_head_and_text_types(self):
        for key, value in [('source_head_before_development', 'invalid'),
                           ('source_head_before_development', 1), ('scope_ja', ''),
                           ('scope_ja', 'nul\0text'), ('scope_ja', 'line\ntext'),
                           ('scope_ja', ['unexpected']), ('scope_ja', '長' * 2001)]:
            self.save(dict(self.dev, **{key: value}))
            with self.subTest(key=key, value=str(value)[:12]), self.assertRaises(ValueError):
                v.development()

    def test_input_symlinks_and_ancestor_symlinks_refused(self):
        original = self.root / v.DEV
        source = self.root / 'real.json'
        source.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(source)
        with self.assertRaises(ValueError):
            v.development()
        original.unlink()
        original.write_bytes(source.read_bytes())
        alias = self.root / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with mock.patch.object(v, 'ROOT', alias), self.assertRaises(ValueError):
            v.development()

    def test_input_bound_and_regular_file_checked_before_read(self):
        original = self.root / v.DEV
        original.write_bytes(b' ' * (v.MAX_FILE_BYTES + 1))
        with mock.patch.object(Path, 'read_bytes', side_effect=AssertionError('過大入力は読まない')), \
             self.assertRaises(ValueError):
            v.development()
        original.unlink()
        original.mkdir()
        with self.assertRaises(ValueError):
            v.development()

    def test_identity_and_exact_types_are_closed(self):
        self.assertFalse(v.exact(1, True))
        self.assertFalse(v.exact(0, False))
        self.assertFalse(v.exact(1, 1.0))
        self.assertFalse(v.exact([1], (1,)))
        class ListAlias(list):
            pass
        self.assertFalse(v.exact(ListAlias([1]), [1]))
        for value in ({}, dict(size=True, sha256='0' * 64), dict(size=1.0, sha256='0' * 64),
                      dict(size=1, sha256='A' * 64), dict(size=0, sha256='0' * 64),
                      dict(size=1, sha256='0' * 64, extra=False)):
            with self.subTest(identity=value):
                self.assertFalse(v.valid_identity(value))


if __name__ == '__main__':
    unittest.main()
