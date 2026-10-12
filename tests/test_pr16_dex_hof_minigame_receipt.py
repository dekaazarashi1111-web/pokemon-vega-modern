"""保存成功4原本のreceipt専用拒否試験。新152/旧152/165/27/22とconsumerは再走しない。"""
import copy
import fnmatch
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_dex_hof_minigame_receipt as v


class ReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        v._pins_ready()
        cls.receipt = v.validation.read_text((ROOT / v.CP).read_bytes())
        cls.files = {name: (ROOT / v.EVIDENCE / name).read_bytes() for name in v.FILES}
        cls.frontier = v.validation.read_text((ROOT / v.FRONTIER).read_bytes())
        # 全55保存原本の認証・復元は1回だけ。同じ親を各receipt拒否試験へ渡す。
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
        # 暗号封筒のpinを試験内だけ再束縛しても、source側閉schemaで改作を拒否する。
        value = v.validation.read_text(self.files[name])
        change(value)
        files = dict(self.files)
        files[name] = v.chain.canonical(value)
        pins = copy.deepcopy(v.FILES)
        pins[name] = v.identity(files[name])
        receipt = copy.deepcopy(self.receipt)
        receipt['evidence_bindings'][v.EVIDENCE + '/' + name] = pins[name]
        for key in v.LOG_FIELDS:
            receipt[key][name] = pins[name]
        mirrors = {'measurement.json': 'measurement_identity', 'reference-chain.json': 'delta_identity',
                   'tests.json': 'tests_identity', 'provenance.json': 'provenance_identity'}
        receipt[mirrors[name]] = pins[name]
        with mock.patch.object(v, 'FILES', pins), self.assertRaises((ValueError, KeyError, TypeError)):
            self.check(receipt=receipt, files=files)

    def test_successful_782_92_receipt(self):
        result = self.check()
        self.assertEqual((result['classified'], result['unclassified']), (782, 92))
        self.assertEqual((result['measurement_replays'], result['old_scope_test_reruns']), (0, 0))

    def test_unacquired_identities_fail_closed(self):
        for key in ('ARTIFACT_ID', 'ZIP_SIZE', 'ZIP_SHA', 'JOB_LOG_ID', 'ARTIFACT_TIMES'):
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
        self.reject(lambda r: r.pop('published_file_identities'))
        for key in ('measurement_identity', 'delta_identity', 'tests_identity',
                    'provenance_identity', 'unknown_identity'):
            with self.subTest(key=key):
                self.reject(lambda r: r[key].update(size=0))

    def test_source_run_attempt_and_guide(self):
        for key, value in [('source_head', '0' * 40), ('run_id', v.RUN + 1),
                           ('run_attempt', 2), ('conclusion', 'failure'), ('guide', v.CP),
                           ('previous_checkpoint', v.CP), ('next_ja', ' ')]:
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
                           ('run_id', v.RUN - 1), ('extra', 'unapproved')]:
            with self.subTest(key=key):
                self.reject(lambda r: r['job'].update({key: value}))

    def test_artifact_outer_identity(self):
        for key, value in [('id', v.ARTIFACT_ID + 1), ('size_in_bytes', v.ZIP_SIZE + 1),
                           ('digest', 'sha256:' + '0' * 64), ('expired', True), ('extra', 'raw')]:
            with self.subTest(key=key):
                self.reject(lambda r: r['artifact'].update({key: value}))

    def test_artifact_source_branch_urls_and_types(self):
        for key, value in [('head_sha', '0' * 40), ('head_branch', 'main'),
                           ('id', float(v.RUN)), ('repository_id', 1), ('extra', 'raw')]:
            with self.subTest(key=key):
                self.reject(lambda r: r['artifact']['workflow_run'].update({key: value}))
        for key, value in [('url', 'https://example.invalid'), ('archive_download_url', 'file:///raw'),
                           ('created_at', '2026-10-08T00:00:00Z'), ('expired', 0)]:
            with self.subTest(key=key):
                self.reject(lambda r: r['artifact'].update({key: value}))

    def test_counter_bool_float_aliases_and_replay_claims(self):
        for key, value in [('newly_classified', True), ('native_processes', False), ('classified', 782.0),
                           ('unit_tests', 165), ('old_scope_test_reruns', 1),
                           ('current_rom_reconstructions', 0), ('source_file_count', 13),
                           ('inherited_parent_inputs', 53), ('inherited_namespaces', 27),
                           ('inherited_changes', 161), ('inherited_witnesses', 151), ('donor_safe_bytes', 4)]:
            with self.subTest(key=key):
                self.reject(lambda r: r.update({key: value}))

    def test_safety_and_original_output_claims_remain_false(self):
        for key in ('donor_eligible', 'donor_leased', 'formal_rom_changed', 'formal_save_changed',
                    'release_ready', 'actual_runtime_execution_observed',
                    'reconstructed_text_promoted_as_original'):
            with self.subTest(key=key):
                self.reject(lambda r: r.update({key: True}))

    def test_all_three_log_phases_match_original_bytes(self):
        self.reject(lambda r: r['job_log_identity'].update(sha256='0' * 64))
        for key in v.LOG_FIELDS:
            for name in v.FILES:
                with self.subTest(phase=key, name=name):
                    self.reject(lambda r: r[key][name].update(size=1))
            self.reject(lambda r: r[key].update(extra={'size': 1, 'sha256': '0' * 64}))

    @staticmethod
    def log_fixture():
        # parser試験専用の疑似log。実測原本/正式checkpointへ保存・昇格しない。
        return [dict(status=status, file=name, **v.FILES[name])
                for status in ('GENERATED_MINIGAME_FILE_IDENTITY',
                               'PASS_MINIGAME_PUBLIC_FILE', 'PASS_MINIGAME_PUBLIC_FILE')
                for name in sorted(v.FILES)]

    def parse_fixture(self, rows):
        raw = ''.join('2026-10-08T01:30:00.0000000Z ' + json.dumps(row) + '\n' for row in rows).encode()
        with mock.patch.object(v, 'JOB_LOG_ID', v.identity(raw)):
            return v.verify_job_log(raw)

    def test_log_parser_retains_generation_validation_publication(self):
        result = self.parse_fixture(self.log_fixture())
        for key in v.LOG_FIELDS:
            self.assertEqual(result[key], v.FILES)
        with self.assertRaises(ValueError):
            v.verify_job_log(b'not the acquired job log\n')

    def test_log_parser_rejects_missing_extra_reordered_record(self):
        rows = self.log_fixture()
        for changed in (rows[:-1], rows + [rows[-1]], list(reversed(rows)), rows[4:]):
            with self.assertRaises(ValueError):
                self.parse_fixture(changed)

    def test_log_parser_rejects_hash_type_and_schema_corruption(self):
        for change in (lambda row: row.update(size=True), lambda row: row.update(sha256='0' * 64),
                       lambda row: row.update(extra='unapproved'), lambda row: row.update(file='rom.bin')):
            rows = self.log_fixture()
            change(rows[-1])
            with self.assertRaises(ValueError):
                self.parse_fixture(rows)

    def test_frontier_exactly92_rows(self):
        frontier = copy.deepcopy(self.frontier)
        frontier['rows'].pop()
        frontier['total'] = 91
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

    def test_semantic_report_schema_source_and_counters(self):
        for change in (lambda m: m.update(classified=781), lambda m: m.update(extra='unapproved'),
                       lambda m: m.update(measurement_origin='independent_development_fixture'),
                       lambda m: m['source_bindings'][v.validation.DEV].update(size=1),
                       lambda m: m['source_bindings'].pop(v.validation.WF)):
            self.semantic_reject('measurement.json', change)

    def test_each_of14_frozen_source_byte_changes_is_rejected(self):
        read_bytes = Path.read_bytes
        for source in sorted(v.validation.SOURCE_CODE):
            selected = ROOT / source
            def changed(path):
                raw = read_bytes(path)
                return raw + b'\n' if path == selected else raw
            with self.subTest(source=source), mock.patch.object(Path, 'read_bytes', changed), \
                 self.assertRaises(ValueError):
                self.check()

    def test_semantic_report_safety_and_proof_type(self):
        for change in (lambda m: m.update(formal_rom_changed=True),
                       lambda m: m['scope_proof'].update(actual_runtime_execution_observed=True),
                       lambda m: m.update(unit_tests=True)):
            self.semantic_reject('measurement.json', change)

    def test_semantic_provenance_fixture_and_current_measurement(self):
        for change in (lambda p: p['independent_development_fixture'].update(is_current_rom_measurement=True),
                       lambda p: p['current_measurement'].update(run_id=v.RUN - 1),
                       lambda p: p['inherited_frontier'].update(old_scope_test_reruns=1),
                       lambda p: p.update(actual_runtime_execution_observed=True),
                       lambda p: p.update(extra='raw')):
            self.semantic_reject('provenance.json', change)

    def test_semantic_new152_original_tests(self):
        for key, value in [('tests', 165), ('old_scope_test_reruns', 1),
                           ('failures', False), ('errors', 1), ('skipped', 1), ('extra', 'raw')]:
            self.semantic_reject('tests.json', lambda t: t.update({key: value}))

    def test_semantic_delta_rejects_unapproved_change_and_claim(self):
        for change in (lambda d: d.update(classified=783), lambda d: d.update(donor_eligible=True),
                       lambda d: d['changes'][0].update(address=v.field.HIT + 4),
                       lambda d: d['witnesses'][0].update(size=8)):
            self.semantic_reject('reference-chain.json', change)

    def test_other873_inventory_rows_retained(self):
        full = copy.deepcopy(self.full)
        row = next(hit for hit in full['hits'] if hit['address'] != v.field.HIT and hit['accepted'])
        row['reason'] = 'unapproved rewrite'
        with mock.patch.object(v.chain, 'materialize', return_value=full), self.assertRaises(ValueError):
            self.check()

    def test_prior_source_bindings_and_namespaces_retained(self):
        full = copy.deepcopy(self.full)
        full[v.chain.previous.NAMESPACE]['proof']['unapproved'] = True
        with mock.patch.object(v.chain, 'materialize', return_value=full), self.assertRaises(ValueError):
            self.check()

    def test_no_measurement_or_old_suite_and_parent_unchanged(self):
        before = v.identity(v.chain.canonical(self.parent))
        with mock.patch.object(v.field, 'compose_selected', side_effect=AssertionError('consumer再測定禁止')), \
             mock.patch.object(v.field, 'regions', side_effect=AssertionError('ROM測定禁止')):
            self.assertEqual(self.check()['measurement_replays'], 0)
        self.assertEqual(v.identity(v.chain.canonical(self.parent)), before)

    def test_receipt_does_not_trigger_frozen_measurement_workflows(self):
        patterns = ('scripts/pr16_dex_hof_jp_minigame_*.py', 'tests/test_pr16_dex_hof_jp_minigame_*.py',
                    'scripts/pr16_dex_hof_jp_item_*.py', 'tests/test_pr16_dex_hof_jp_item_*.py',
                    'scripts/pr16_dex_hof_item_recovery*.py', 'tests/test_pr16_dex_hof_item_recovery*.py')
        for path in ('scripts/pr16_dex_hof_minigame_receipt.py', 'tests/test_pr16_dex_hof_minigame_receipt.py'):
            self.assertFalse(any(fnmatch.fnmatch(path, pattern) for pattern in patterns))


if __name__ == '__main__':
    unittest.main()
