"""保存Diploma成功4原本のreceipt専用拒否試験。新168/旧suite/consumerは再走しない。"""
import copy
import fnmatch
import io
import json
import zipfile
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_dex_hof_asset_receipt as v


class ReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        v._pins_ready()
        cls.receipt = v.validation.read_text((ROOT / v.CP).read_bytes())
        cls.files = {name: (ROOT / v.EVIDENCE / name).read_bytes() for name in v.FILES}
        cls.frontier = v.validation.read_text((ROOT / v.FRONTIER).read_bytes())
        # 全57保存原本の認証・復元は1回だけ。同じ親を各receipt拒否試験へ渡す。
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
        # 試験内だけ全envelopeと派生identityを再seal。正式原本には書かない。
        values = {key: v.validation.read_text(raw) for key, raw in self.files.items()}
        change(values[name])
        files = dict(self.files)
        files[name] = v.chain.canonical(values[name])
        if name == 'reference-chain.json':
            values['measurement.json']['delta_identity'] = v.identity(files[name])
            files['measurement.json'] = v.chain.canonical(values['measurement.json'])
        if name in {'reference-chain.json', 'measurement.json'}:
            current = values['provenance.json']['current_measurement']
            current['delta_identity'] = copy.deepcopy(values['measurement.json']['delta_identity'])
            current['measurement_canonical_identity'] = v.identity(
                v.chain.canonical(values['measurement.json']))
            files['provenance.json'] = v.chain.canonical(values['provenance.json'])
        pins = {key: v.identity(raw) for key, raw in files.items()}
        receipt = copy.deepcopy(self.receipt)
        receipt['evidence_bindings'] = {v.EVIDENCE + '/' + key: value for key, value in pins.items()}
        for key in v.LOG_FIELDS:
            receipt[key] = copy.deepcopy(pins)
        mirrors = {'measurement.json': 'measurement_identity', 'reference-chain.json': 'delta_identity',
                   'tests.json': 'tests_identity', 'provenance.json': 'provenance_identity'}
        for filename, mirror in mirrors.items():
            receipt[mirror] = copy.deepcopy(pins[filename])
        with mock.patch.object(v, 'FILES', pins), self.assertRaises((ValueError, KeyError, TypeError)):
            self.check(receipt=receipt, files=files)

    def test_successful_783_91_receipt(self):
        result = self.check()
        self.assertEqual((result['classified'], result['unclassified']), (783, 91))
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
        for index in range(9):
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
        for key, value in [('newly_classified', True), ('native_processes', False), ('classified', 783.0),
                           ('unit_tests', 152), ('old_scope_test_reruns', 1),
                           ('current_rom_reconstructions', 0), ('source_file_count', 13),
                           ('inherited_parent_inputs', 55), ('inherited_namespaces', 28),
                           ('inherited_changes', 162), ('inherited_witnesses', 152), ('donor_safe_bytes', 4),
                           ('public_source_file_count', 12), ('accepted_namespaces', 29),
                           ('accepted_changes', 163), ('accepted_witnesses', 153)]:
            with self.subTest(key=key):
                self.reject(lambda r: r.update({key: value}))

    def test_safety_and_original_output_claims_remain_false(self):
        for key, value in v.COUNTERS.items():
            if value is not False:
                continue
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
                for status in ('GENERATED_DIPLOMA_FILE_IDENTITY',
                               'PASS_DIPLOMA_PUBLIC_FILE', 'PASS_DIPLOMA_PUBLIC_FILE')
                for name in sorted(v.FILES)]

    def parse_fixture(self, rows):
        raw = ''.join('2026-10-08T02:30:00.0000000Z ' + json.dumps(row) + '\n' for row in rows).encode()
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

    def test_frontier_exactly91_rows(self):
        frontier = copy.deepcopy(self.frontier)
        frontier['rows'].pop()
        frontier['total'] = 90
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
                       lambda m: m.update(actual_bios_cpu_executed=True),
                       lambda m: m.update(actual_screen_rendered=True),
                       lambda m: m.update(conditional_finite_type_only=False),
                       lambda m: m.update(unit_tests=True)):
            self.semantic_reject('measurement.json', change)

    def test_semantic_provenance_fixture_and_current_measurement(self):
        for change in (lambda p: p['independent_development_fixture'].update(is_current_rom_measurement=True),
                       lambda p: p['current_measurement'].update(run_id=v.RUN - 1),
                       lambda p: p['inherited_frontier'].update(old_scope_test_reruns=1),
                       lambda p: p.update(actual_runtime_execution_observed=True),
                       lambda p: p.update(extra='raw')):
            self.semantic_reject('provenance.json', change)

    def test_semantic_new168_original_tests(self):
        for key, value in [('tests', 165), ('old_scope_test_reruns', 1),
                           ('failures', False), ('errors', 1), ('skipped', 1), ('extra', 'raw')]:
            self.semantic_reject('tests.json', lambda t: t.update({key: value}))

    def test_semantic_delta_rejects_unapproved_change_and_claim(self):
        for change in (lambda d: d.update(classified=784), lambda d: d.update(donor_eligible=True),
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
        full[v.chain.INHERITED_NAMES[-1]]['proof']['unapproved'] = True
        with mock.patch.object(v.chain, 'materialize', return_value=full), self.assertRaises(ValueError):
            self.check()

    def test_no_measurement_or_old_suite_and_parent_unchanged(self):
        before = v.identity(v.chain.canonical(self.parent))
        with mock.patch.object(v.field, 'compose', side_effect=AssertionError('consumer再測定禁止')), \
             mock.patch.object(v.field, 'regions', side_effect=AssertionError('ROM測定禁止')), \
             mock.patch.object(v.validation.sources, 'load_sources', side_effect=AssertionError('公開source再取得禁止')), \
             mock.patch.object(v.validation.sources, 'diploma_asset', side_effect=AssertionError('asset再生成禁止')), \
             mock.patch('subprocess.run', side_effect=AssertionError('native/旧suite再走禁止')):
            self.assertEqual(self.check()['measurement_replays'], 0)
        self.assertEqual(v.identity(v.chain.canonical(self.parent)), before)

    def test_all_counter_and_flag_alias_types_are_rejected(self):
        for key, value in v.COUNTERS.items():
            alias = int(value) if type(value) is bool else float(value)
            with self.subTest(key=key):
                self.reject(lambda r: r.update({key: alias}))

    def test_all13_public_source_bindings_are_fixed(self):
        report = v.validation.read_text(self.files['measurement.json'])
        self.assertEqual(len(report['public_source_bindings']), 13)
        for source in sorted(report['public_source_bindings']):
            with self.subTest(source=source):
                self.semantic_reject('measurement.json',
                    lambda m: m['public_source_bindings'][source].update(sha256='0' * 64))
        self.semantic_reject('measurement.json', lambda m: m['public_source_bindings'].pop(source))
        self.semantic_reject('measurement.json', lambda m: m['public_source_bindings'].update(raw='00'))

    def test_raw_bytehex_and_untrusted_schema_are_rejected_after_reseal(self):
        for name in self.files:
            for key, value in (('raw_bytes', [1, 2, 3]), ('bytehex', '00010203'),
                               ('untrusted_schema', {'allowed': True})):
                with self.subTest(file=name, key=key):
                    self.semantic_reject(name, lambda value_: value_.update({key: value}))
        for change in (lambda d: d['proof'].update(raw_bytes=[1]),
                       lambda d: d['witnesses'][0]['evidence'].update(bytehex='00010203'),
                       lambda d: d['changes'][0].update(untrusted_schema='pass'),
                       lambda d: d.update(hits=copy.deepcopy(self.parent['hits']))):
            self.semantic_reject('reference-chain.json', change)

    def test_semantic_diploma_boundary_claims_cannot_be_promoted(self):
        for flag, value in v.field.CLAIMS.items():
            changed = not value
            with self.subTest(flag=flag):
                self.semantic_reject('measurement.json',
                    lambda m: m['scope_proof'].update({flag: changed}))
        for change in (lambda d: d['changes'][0].update(size=5),
                       lambda d: d['changes'][0].update(accepted=1),
                       lambda d: d['changes'][0].update(witness_ids=[False]),
                       lambda d: d['witnesses'][0].update(address=v.field.HIT - 1),
                       lambda d: d['witnesses'].append(copy.deepcopy(d['witnesses'][0]))):
            self.semantic_reject('reference-chain.json', change)

    def test_materialized_new_namespace_and_totals_are_exact(self):
        for change in (lambda f: f.update(extra_namespace={}),
                       lambda f: f[v.chain.NAMESPACE]['changes'].clear(),
                       lambda f: f[v.chain.NAMESPACE]['witnesses'].clear()):
            full = copy.deepcopy(self.full)
            change(full)
            with mock.patch.object(v.chain, 'materialize', return_value=full), self.assertRaises(ValueError):
                self.check()

    def test_old_unknown_original_is_bound_by_parent_checkpoint(self):
        read_bytes = Path.read_bytes
        def altered(path):
            raw = read_bytes(path)
            return raw + b' ' if path == ROOT / v.OLD_FRONTIER else raw
        with mock.patch.object(Path, 'read_bytes', altered), self.assertRaises(ValueError):
            self.check()

    def test_log_duplicate_keys_float_aliases_and_malformed_extra_are_rejected(self):
        lines = [json.dumps(row) for row in self.log_fixture()]
        status = '"status": "PASS_DIPLOMA_PUBLIC_FILE"'
        for replacement in (lines[-1].replace(status, status + ', ' + status),
                            lines[-1].replace('"size": ', '"size": 1e0, "unused": ')):
            raw = ('\n'.join(lines[:-1] + [replacement]) + '\n').encode()
            with mock.patch.object(v, 'JOB_LOG_ID', v.identity(raw)), self.assertRaises(ValueError):
                v.verify_job_log(raw)
        raw = ('\n'.join(lines) + '\n{"status":"PASS_DIPLOMA_PUBLIC_FILE",broken\n').encode()
        with mock.patch.object(v, 'JOB_LOG_ID', v.identity(raw)), self.assertRaises(ValueError):
            v.verify_job_log(raw)

    def zip_fixture(self, rows):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, raw in rows:
                archive.writestr(name, raw)
        raw = stream.getvalue()
        pin = v.identity(raw)
        with mock.patch.object(v, 'ZIP_SIZE', pin['size']), mock.patch.object(v, 'ZIP_SHA', pin['sha256']):
            return v.verify_artifact_zip(raw)

    def test_zip_binds_exact_acquired4_originals(self):
        self.assertEqual(self.zip_fixture(list(self.files.items())), self.files)
        with self.assertRaises(ValueError):
            v.verify_artifact_zip(b'not the acquired zip')

    def test_zip_rejects_extra_missing_renamed_and_modified_original(self):
        rows = list(self.files.items())
        altered = [(name, raw + b' ') if name == rows[0][0] else (name, raw) for name, raw in rows]
        renamed = [('raw/' + name, raw) for name, raw in rows]
        for changed in (rows + [('raw.bin', b'private')], rows[:-1], renamed, altered):
            with self.assertRaises(ValueError):
                self.zip_fixture(changed)

    def test_zip_rejects_symlink_original(self):
        rows = list(self.files.items())
        entry = zipfile.ZipInfo(rows[0][0])
        entry.external_attr = 0o120777 << 16
        with self.assertRaises(ValueError):
            self.zip_fixture([(entry, rows[0][1]), *rows[1:]])

    def test_main_rejects_extra_raw_file_in_evidence_directory(self):
        iterdir = Path.iterdir
        def extra(path):
            children = list(iterdir(path))
            return iter(children + [path / 'raw.bin']) if path == ROOT / v.EVIDENCE else iter(children)
        with mock.patch.object(Path, 'iterdir', extra), self.assertRaises(ValueError):
            v.main()

    def test_main_rejects_symlink_original_or_ancestor(self):
        is_symlink = Path.is_symlink
        for selected in (ROOT / v.EVIDENCE, ROOT / v.EVIDENCE / 'measurement.json'):
            def substituted(path):
                return path == selected or is_symlink(path)
            with self.subTest(path=selected), mock.patch.object(Path, 'is_symlink', substituted), \
                 self.assertRaises(ValueError):
                v.main()

    def test_receipt_does_not_trigger_frozen_measurement_workflows(self):
        patterns = ('scripts/pr16_dex_hof_diploma_*.py', 'tests/test_pr16_dex_hof_diploma_*.py',
                    'scripts/pr16_dex_hof_jp_minigame_*.py', 'tests/test_pr16_dex_hof_jp_minigame_*.py',
                    'scripts/pr16_dex_hof_jp_item_*.py', 'tests/test_pr16_dex_hof_jp_item_*.py',
                    'scripts/pr16_dex_hof_item_recovery*.py', 'tests/test_pr16_dex_hof_item_recovery*.py',
                    'scripts/pr16_dex_hof_credits_*.py', 'tests/test_pr16_dex_hof_credits_*.py')
        for path in ('scripts/pr16_dex_hof_asset_receipt.py', 'tests/test_pr16_dex_hof_asset_receipt.py'):
            self.assertFalse(any(fnmatch.fnmatch(path, pattern) for pattern in patterns))


if __name__ == '__main__':
    unittest.main()
