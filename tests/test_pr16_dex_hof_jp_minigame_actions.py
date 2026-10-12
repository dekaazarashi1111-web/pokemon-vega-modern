"""新minigameの実producer/包装/実4file読戻しと閉じたActions公開境界の反証。"""
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
import pr16_dex_hof_jp_minigame_actions as actions
import pr16_dex_hof_jp_minigame_validation as v


class ActionsBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        location = ROOT / '.local/jp-minigame-sources'
        if not location.exists():
            location = actions.OUT / 'sources'
        cls.sources = actions.source_preflight(location)

    def test_fixed_source_set_and_full_identity(self):
        self.assertEqual(set(self.sources), set(v.field.source_manifest()))
        self.assertTrue(v.field.sources_bind(self.sources))

    def test_each_source_mutation_is_rejected(self):
        for name in self.sources:
            bad = dict(self.sources)
            bad[name] += b'\n'
            with self.subTest(source=name), self.assertRaises(ValueError):
                v.field.sources_bind(bad)

    def test_missing_extra_source_is_rejected(self):
        for bad in ({}, {**self.sources, 'extra': b''}):
            with self.assertRaises(ValueError):
                v.field.sources_bind(bad)

    def test_manifest_is_independent_and_exact(self):
        self.assertTrue(v.exact(v.read_text((ROOT / v.MANIFEST).read_bytes()), v.field.source_manifest()))
        self.assertEqual(v.field.source_manifest()['pret-party_menu.c']['commit'],
                         'c75f352304d529f6ba92d4f74b9cf8b5c3810788')

    def test_source_preflight_symlink_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            alias = root / 'alias'
            alias.symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                actions.source_preflight(alias / 'sources')

    def test_publication_contract(self):
        result = actions.publication.contract(ROOT, actions.WF, actions.PUBLIC, actions.ARTIFACT, actions.SELF)
        self.assertEqual(result['artifact'], 'pr16-jp-minigame-text-only')

    def test_readonly_workflow_and_success_only_upload(self):
        value = (ROOT / actions.WF).read_text()
        for marker in ('contents: read', 'actions: read', 'pull-requests: read',
                       'persist-credentials: false', "github.run_attempt == 1",
                       "if: ${{ always() && steps.publication_guard.outcome == 'success' }}",
                       'MINIGAME_MEASUREMENT_OUTCOME: ${{ steps.measurement.outcome }}'):
            self.assertIn(marker, value)
        for marker in ('contents: write', 'actions: write', 'pull-requests: write',
                       'pull_request_target', 'git push', 'upload-artifact@v3'):
            self.assertNotIn(marker, value)
        self.assertEqual(value.count('uses: actions/upload-artifact@v4'), 1)

    def test_new_suite_only_and_one_reconstruction(self):
        self.assertEqual(actions.SUITES, ('roots', 'text', 'chain', 'actions'))
        source = (ROOT / actions.SELF).read_text()
        self.assertEqual(source.count('reconstruct.reconstruct()'), 1)
        for marker in ('test_pr16_dex_hof_jp_item_', 'test_pr16_dex_hof_item_recovery_',
                       'test_pr16_dex_hof_item_receipt', 'donor.audit(', 'native.run('):
            self.assertNotIn(marker, source)

    def test_all_branch_first_run(self):
        row = dict(id=123, head_sha='1' * 40, head_branch=actions.BRANCH, run_attempt=1)
        actions.validate_history(dict(total_count=1, workflow_runs=[row]), 123, '1' * 40)
        source = (ROOT / actions.SELF).read_text()
        self.assertIn("Path(WF).name + '/runs?per_page=100'", source)
        self.assertNotIn('/runs?branch=', source)

    def test_prior_hidden_or_other_branch_run_refused(self):
        row = dict(id=123, head_sha='1' * 40, head_branch=actions.BRANCH, run_attempt=1)
        histories = [dict(total_count=0, workflow_runs=[]),
                     dict(total_count=2, workflow_runs=[row]),
                     dict(total_count=2, workflow_runs=[row, dict(row, id=124, head_branch='other')]),
                     dict(total_count=True, workflow_runs=[row]),
                     dict(total_count=1, workflow_runs=[dict(row, run_attempt=2)]),
                     dict(total_count=1, workflow_runs=[dict(row, id=True)]),
                     dict(total_count=1, workflow_runs=[dict(row, head_sha='2' * 40)]),
                     dict(total_count=1, workflow_runs=[dict(row, head_branch='other')])]
        for history in histories:
            with self.subTest(history=history), self.assertRaises(ValueError):
                actions.validate_history(history, 123, '1' * 40)

    def test_failed_measurement_cannot_export(self):
        for outcome in ('failure', 'skipped', 'cancelled', ''):
            with self.subTest(outcome=outcome), mock.patch.dict(os.environ, {'MINIGAME_MEASUREMENT_OUTCOME': outcome}), \
                 mock.patch.object(actions, 'validate_guard') as guard, \
                 mock.patch.object(v, 'validate_output') as publish, self.assertRaises(ValueError):
                actions.export()
            guard.assert_not_called()
            publish.assert_not_called()

    def test_private_failure_diagnostics_not_public(self):
        source = (ROOT / actions.SELF).read_text()
        self.assertIn("OUT / 'private-failure.txt'", source)
        self.assertNotIn("PUBLIC / 'failure.json'", source)
        self.assertEqual(v.FILES, {'measurement.json', 'reference-chain.json', 'tests.json', 'provenance.json'})

    def test_all_fourteen_sources_are_bound(self):
        self.assertEqual(len(v.SOURCE_CODE), 14)
        self.assertEqual(actions.CODE, v.SOURCE_CODE)
        self.assertEqual(set(v.bindings()), v.SOURCE_CODE)
        self.assertIn('scripts/pr16_dex_hof_jp_minigame_validation.py', v.SOURCE_CODE)
        self.assertIn(v.DEVELOPMENT_PROOF, v.SOURCE_CODE)


class MinigamePublicBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof_raw = (ROOT / v.DEVELOPMENT_PROOF).read_bytes()
        cls.proof = v.read_text(cls.proof_raw)
        cls.count = v.development()['unit_tests']
        cls.bindings = v.bindings()
        cls.context = dict(source_head='1' * 40, run_id=123456789,
                           expected_bindings=cls.bindings, test_count=cls.count)
        with mock.patch('subprocess.Popen', side_effect=AssertionError('外部processは禁止')), \
             mock.patch.object(v.field, 'compose_selected', side_effect=AssertionError('旧/現consumerを再実行しない')), \
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

    def test_actual_producer_to_normalized_report_and_four_files(self):
        from test_pr16_dex_hof_jp_minigame_text import fixture
        with mock.patch('subprocess.Popen', side_effect=AssertionError('外部processは禁止')), \
             mock.patch.object(v.chain.d, 'inventory', side_effect=AssertionError('ROM全scanは禁止')):
            regions, raw_proof = v.field._regions(fixture(), self.parent)
        self.assertEqual([row['lane'] for row in raw_proof['cases']], ['entry', 'cancel'])
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
        raw['cases'] = tuple(raw['cases'])
        report = v.measured_report(raw, self.delta, **self.context)
        self.assertIs(type(raw['cases']), tuple)
        self.assertIs(type(report['scope_proof']['cases']), list)
        self.assertTrue(v.validate_report(report, self.delta, self.parent, **self.context))
        report['scope_proof']['cases'] = tuple(report['scope_proof']['cases'])
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
        bad['scope_proof']['cases'][0]['text_read_bytes'] += 1
        with self.assertRaises(ValueError):
            v.validate_report(bad, self.delta, self.parent, **self.context)

    def test_changed_delta_with_recomputed_hash_refused(self):
        original = v.read_text(self.delta)
        for key, value in [('classified', 783), ('newly_classified', True), ('donor_eligible', True),
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
            self.assertEqual(row, dict(status='GENERATED_MINIGAME_FILE_IDENTITY', file=row['file'],
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
            self.assertEqual(row, dict(status='PASS_MINIGAME_PUBLIC_FILE', file=row['file'],
                                      **identities[row['file']]))

    def test_frontier_and_no_runtime_or_donor_claims(self):
        self.assertEqual((self.report['inherited_classified'], self.report['inherited_unclassified']), (781, 93))
        self.assertEqual((self.report['classified'], self.report['unclassified'], self.report['newly_classified']), (782, 92, 1))
        self.assertEqual((self.report['current_rom_reconstructions'], self.report['current_owner_count'], self.report['saved_hit_count']), (1, 115, 874))
        self.assertEqual(self.report['old_scope_test_reruns'], 0)
        self.assertEqual(self.report['native_processes'], 0)
        self.assertEqual(self.report['donor_safe_bytes'], 0)
        self.assertIs(v.provenance(self.report)['actual_runtime_execution_observed'], False)


if __name__ == '__main__':
    unittest.main()
