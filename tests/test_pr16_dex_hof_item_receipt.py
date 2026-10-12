"""保存成功原本の新receipt拒否試験。旧165/回復27試験とfinite consumerは再走しない。"""
import copy
import fnmatch
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_dex_hof_item_receipt as v


class ReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        v._pins_ready()
        cls.receipt = v.validation.read_text((ROOT / v.CP).read_bytes())
        cls.files = {name: (ROOT / v.EVIDENCE / name).read_bytes() for name in v.FILES}
        cls.frontier = v.validation.read_text((ROOT / v.FRONTIER).read_bytes())
        # 旧53原本の認証・復元はこの1回だけ。以下は同じ親をmockで再利用する。
        cls.parent = v.chain.parent(*[(ROOT / path).read_bytes() for path in v.chain.PARENT_INPUTS])
        delta = v.chain.read_measured(cls.files['reference-chain.json'], v.FILES['reference-chain.json'], cls.parent)
        cls.full = v.chain.materialize(cls.parent, delta)

    def check(self, receipt=None, files=None, frontier=None):
        with mock.patch.object(v.chain, 'parent', return_value=self.parent):
            return v.validate(self.receipt if receipt is None else receipt,
                              self.files if files is None else files,
                              self.frontier if frontier is None else frontier)

    def reject(self, change):
        receipt = copy.deepcopy(self.receipt)
        change(receipt)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            self.check(receipt=receipt)

    def semantic_reject(self, name, change):
        # 暗号的封筒を試験内だけ再束縛しても、意味的閉schemaで改作を拒否する。
        value = v.validation.read_text(self.files[name])
        change(value)
        files = dict(self.files)
        files[name] = v.chain.canonical(value)
        pins = copy.deepcopy(v.FILES)
        pins[name] = v.identity(files[name])
        receipt = copy.deepcopy(self.receipt)
        receipt['evidence_bindings'][v.EVIDENCE + '/' + name] = pins[name]
        mirrors = {'measurement.json': 'measurement_identity', 'reference-chain.json': 'delta_identity',
                   'tests.json': 'tests_identity', 'provenance.json': 'provenance_identity'}
        receipt[mirrors[name]] = pins[name]
        with mock.patch.object(v, 'FILES', pins), self.assertRaises((ValueError, KeyError, TypeError)):
            self.check(receipt=receipt, files=files)

    def test_successful_781_93_receipt(self):
        result = self.check()
        self.assertEqual((result['classified'], result['unclassified']), (781, 93))
        self.assertEqual((result['measurement_replays'], result['old_scope_test_reruns']), (0, 0))

    def test_unacquired_identities_fail_closed(self):
        for key in ('ARTIFACT_ID', 'ZIP_SIZE', 'ZIP_SHA', 'INHERITED_LOG_ID', 'PRIOR_RECOVERY_LOG_ID'):
            with self.subTest(key=key), mock.patch.object(v, key, None), self.assertRaises(ValueError):
                self.check()
        with mock.patch.object(v, 'FILES', {name: None for name in v.FILES}), self.assertRaises(ValueError):
            self.check()

    def test_every_original_byte_identity(self):
        for name in self.files:
            files = dict(self.files)
            files[name] += b' '
            with self.subTest(file=name), self.assertRaises(ValueError):
                self.check(files=files)

    def test_missing_extra_original(self):
        for files in ({**self.files, 'rom.bin': b''},
                      {key: value for key, value in self.files.items() if key != 'provenance.json'}):
            with self.assertRaises(ValueError):
                self.check(files=files)

    def test_receipt_schema_and_mirror_identity(self):
        self.reject(lambda r: r.update(extra='unapproved'))
        self.reject(lambda r: r.pop('original_failed_run'))
        for key in ('measurement_identity', 'delta_identity', 'tests_identity',
                    'provenance_identity', 'unknown_identity'):
            with self.subTest(key=key):
                self.reject(lambda r: r[key].update(size=0))

    def test_source_run_attempt_and_guide(self):
        for key, value in [('source_head', v.validation.INHERITED_SOURCE_HEAD), ('run_id', v.RUN + 1),
                           ('run_attempt', 2), ('conclusion', 'failure'), ('guide', v.CP),
                           ('previous_checkpoint', v.CP)]:
            with self.subTest(key=key):
                self.reject(lambda r: r.update({key: value}))

    def test_every_job_step_success_and_order(self):
        for index in range(10):
            with self.subTest(step=index):
                self.reject(lambda r: r['job']['steps'][index].update(conclusion='skipped'))
        self.reject(lambda r: r['job']['steps'].reverse())
        self.reject(lambda r: r['job']['steps'].pop())

    def test_job_identity_and_schema(self):
        for key, value in [('id', v.JOB + 1), ('id', float(v.JOB)), ('status', 'in_progress'),
                           ('run_id', v.validation.INHERITED_MEASUREMENT_RUN), ('extra', 'unapproved')]:
            with self.subTest(key=key):
                self.reject(lambda r: r['job'].update({key: value}))

    def test_artifact_outer_identity(self):
        for key, value in [('id', v.ARTIFACT_ID + 1), ('size_in_bytes', v.ZIP_SIZE + 1),
                           ('digest', 'sha256:' + '0' * 64), ('expired', True), ('extra', 'raw')]:
            with self.subTest(key=key):
                self.reject(lambda r: r['artifact'].update({key: value}))

    def test_artifact_source_branch_urls_and_types(self):
        for key, value in [('head_sha', v.validation.INHERITED_SOURCE_HEAD), ('head_branch', 'main'),
                           ('id', float(v.RUN)), ('repository_id', 1), ('extra', 'raw')]:
            with self.subTest(key=key):
                self.reject(lambda r: r['artifact']['workflow_run'].update({key: value}))
        for key, value in [('url', 'https://example.invalid'), ('archive_download_url', 'file:///raw'),
                           ('created_at', 'unknown'), ('expired', 0)]:
            with self.subTest(key=key):
                self.reject(lambda r: r['artifact'].update({key: value}))

    def test_counter_bool_float_aliases_and_replay_claims(self):
        for key, value in [('newly_classified', True), ('native_processes', False), ('classified', 781.0),
                           ('inherited_scope_tests', 192), ('recovery_test_count', 165),
                           ('old_scope_test_reruns', 1), ('cumulative_scope_rom_reconstructions', 2),
                           ('consumer_remeasurements', 0), ('donor_safe_bytes', 4)]:
            with self.subTest(key=key):
                self.reject(lambda r: r.update({key: value}))

    def test_safety_and_original_output_claims_remain_false(self):
        for key in ('donor_eligible', 'donor_leased', 'formal_rom_changed', 'formal_save_changed',
                    'original_failed_run_rewritten', 'reconstructed_text_promoted_as_original'):
            with self.subTest(key=key):
                self.reject(lambda r: r.update({key: True}))

    def test_original_failure_snapshot_preserved(self):
        for key, value in [('run_conclusion', 'success'), ('artifact_count', 1),
                           ('original_output_hashes_available', True), ('scope_tests', 192),
                           ('measurement_step_outcome', 'failure'), ('export_step_outcome', 'success')]:
            with self.subTest(key=key):
                self.reject(lambda r: r['original_failed_run'].update({key: value}))
        for key, value in [('run_conclusion', 'success'), ('measurement_step', 'success'),
                           ('original_artifact_missing', False), ('successful_measurement_claimed', True),
                           ('scope_proof_original_available', True), ('current_rom_reconstructions', 0)]:
            with self.subTest(prior_recovery_key=key):
                self.reject(lambda r: r['prior_failed_recovery'].update({key: value}))

    def test_frontier_exactly93_rows(self):
        frontier = copy.deepcopy(self.frontier)
        frontier['rows'].pop()
        frontier['total'] = 92
        with self.assertRaises(ValueError):
            self.check(frontier=frontier)

    def test_frontier_all_fields_order_and_safety_retained(self):
        for change in (lambda f: f['rows'][0]['hit'].update(accepted=True),
                       lambda f: f['rows'].reverse(), lambda f: f.update(donor_eligible=True),
                       lambda f: f.update(owner_unknown=False), lambda f: f.update(extra='raw')):
            frontier = copy.deepcopy(self.frontier)
            change(frontier)
            with self.assertRaises(ValueError):
                self.check(frontier=frontier)

    def test_semantic_report_source_and_counters(self):
        for change in (lambda m: m.update(classified=780),
                       lambda m: m.update(reconstructed_text_promoted_as_original=True),
                       lambda m: m['source_bindings'][v.validation.DEV].update(size=1)):
            self.semantic_reject('measurement.json', change)

    def test_semantic_provenance_and_lost_hashes(self):
        for change in (lambda p: p['original_failed_run'].update(original_output_hashes_available=True),
                       lambda p: p['inherited_scope'].update(reruns=1),
                       lambda p: p['prior_failed_recovery'].update(successful_measurement_claimed=True),
                       lambda p: p['current_remeasurement'].update(cumulative_scope_rom_reconstructions=2),
                       lambda p: p['independent_development_fixture'].update(is_lost_output_original=True),
                       lambda p: p['current_remeasurement'].update(origin='recovered_original_output'),
                       lambda p: p.update(extra='raw')):
            self.semantic_reject('provenance.json', change)

    def test_semantic_new27_and_inherited165_tests(self):
        for key, value in [('recovery_test_count', 165), ('inherited_scope_tests', 27),
                           ('old_scope_test_reruns', 1), ('failures', False), ('errors', 1)]:
            self.semantic_reject('tests.json', lambda t: t.update({key: value}))

    def test_other873_inventory_rows_retained(self):
        full = copy.deepcopy(self.full)
        row = next(hit for hit in full['hits'] if hit['address'] != v.field.HIT and hit['accepted'])
        row['reason'] = 'unapproved rewrite'
        with mock.patch.object(v.chain, 'materialize', return_value=full), self.assertRaises(ValueError):
            self.check()

    def test_prior_source_bindings_retained(self):
        full = copy.deepcopy(self.full)
        full[v.chain.previous.NAMESPACE]['proof']['unapproved'] = True
        with mock.patch.object(v.chain, 'materialize', return_value=full), self.assertRaises(ValueError):
            self.check()

    def test_no_measurement_or_old_suite_and_parent_unchanged(self):
        before = v.identity(v.chain.canonical(self.parent))
        with mock.patch.object(v.field, 'compose_selected', side_effect=AssertionError('再測定禁止')), \
             mock.patch.object(v.field, 'regions', side_effect=AssertionError('ROM測定禁止')):
            self.assertEqual(self.check()['measurement_replays'], 0)
        self.assertEqual(v.identity(v.chain.canonical(self.parent)), before)

    def test_receipt_does_not_trigger_either_measurement_workflow(self):
        patterns = ('scripts/pr16_dex_hof_jp_item_*.py', 'tests/test_pr16_dex_hof_jp_item_*.py',
                    'scripts/pr16_dex_hof_item_recovery*.py', 'tests/test_pr16_dex_hof_item_recovery*.py')
        for path in ('scripts/pr16_dex_hof_item_receipt.py', 'tests/test_pr16_dex_hof_item_receipt.py'):
            self.assertFalse(any(fnmatch.fnmatch(path, pattern) for pattern in patterns))


if __name__ == '__main__':
    unittest.main()
