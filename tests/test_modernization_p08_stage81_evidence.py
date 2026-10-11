"""Strict original-evidence, layered acceptance and wrong-success regressions."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from unittest import mock
import unittest

from tools import modernization_p08_stage81_evidence as e
from scripts import integrate_modernization_p08_stage81_evidence as importer


class Stage81EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        e.base.require((e.ROOT / e.CONFIG).is_file(), 'explicit Stage81 adoption required for integration tests')
        cls.actual = e.build_extension()
        cls.actions = {s: json.loads((e.ROOT / e.DIRECTORY / ('actions-' + s + '.json')).read_bytes())
                       for s in ('stage81', 'p03')}
        cls.archives = {n: (e.ROOT / e.DIRECTORY / n / 'source.zip').read_bytes() for n in e.ARCHIVES}
        cls.payload = e.unpack(cls.archives['p03-fullslots-e2e'], 'p03-fullslots-e2e')

    def test_exact_stage81_product_and_declared_limits(self):
        self.assertEqual(self.actual['candidate_stage'], 81)
        self.assertEqual(self.actual['candidate_rom']['sha256'], e.adapter.SHA)
        self.assertEqual(self.actual['domain_count'], 7)
        self.assertEqual(self.actual['original_matrix_fresh_process_runs'], 7)
        self.assertEqual(self.actual['original_matrix_cache_reuse'], 0)
        self.assertEqual(self.actual['fresh_process_runs_this_validation'], 0)
        self.assertEqual(self.actual['p03_fullslots']['accepted_candidate_runs'], 8)
        self.assertEqual(self.actual['p03_fullslots']['negative_control_runs'], 2)
        self.assertTrue(all(v is False for v in self.actual['claims'].values()))

    def test_all_pinned_original_zips_are_verified(self):
        for name, raw in self.archives.items():
            self.assertEqual(set(e.unpack(raw, name)), e.members(name))

    def test_all_original_actions_are_successful(self):
        for suite, actions in self.actions.items():
            e.validate_actions(actions, suite)

    def test_exact_eight_cases_and_two_pp_failure_controls(self):
        report = e.validate_p03(self.payload)
        self.assertEqual([r['mode'] for r in report['cases']], list(e.p03.MODES))
        self.assertEqual(len(report['pre_repair_controls']), 2)

    def test_false_and_zero_differ(self):
        for value in (False, 0.0, '0', None):
            with self.assertRaises(e.base.EvidenceError): e.exact(value, 0, 'typed exit')

    def test_attachment_preserves_every_prior_field(self):
        path = 'content/modernization/p08_runtime_handoff.json'
        document = json.loads((e.ROOT / path).read_bytes())
        original = e.strip(document)
        with mock.patch.object(e, 'build_extension', return_value=self.actual):
            result = e.attach_outputs({path: e.base.stable(original)})
            self.assertEqual(result, e.attach_outputs(result))
        attached = json.loads(result[path])
        self.assertEqual(e.strip(attached), original)
        e.validate_document(attached, self.actual)

    def test_source_and_gate_checks_are_read_only(self):
        paths = [e.CONFIG, *self.actual['source_bindings'], e.adapter.GATE]
        before = {p: ((e.ROOT / p).stat().st_mtime_ns, e.identity((e.ROOT / p).read_bytes())) for p in paths}
        self.assertEqual(e.build_extension(), self.actual)
        self.assertEqual(before, {p: ((e.ROOT / p).stat().st_mtime_ns, e.identity((e.ROOT / p).read_bytes())) for p in paths})

    def test_unregistered_layer_is_rejected(self):
        with self.assertRaises(e.base.EvidenceError):
            e.validate_document({'current_native_pp_acceptance': self.actual}, None)

    def test_historical_fixture_is_not_auto_adopted(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = {'old.json': b'{}'}
            self.assertEqual(e.attach_outputs(raw, Path(directory)), raw)

    def test_prior_document_mutation_is_rejected(self):
        document = json.loads((e.ROOT / 'content/modernization/p08_runtime_handoff.json').read_bytes())
        document['release_ready'] = True
        with self.assertRaises(e.base.EvidenceError): e.validate_document(document, self.actual)

    def test_new_layer_mutation_is_rejected(self):
        document = json.loads((e.ROOT / 'content/modernization/p08_runtime_handoff.json').read_bytes())
        document['current_native_pp_acceptance']['p03_fullslots']['full_p03_acceptance'] = True
        with self.assertRaises(e.base.EvidenceError): e.validate_document(document, self.actual)

    def test_registered_source_mutation_is_rejected(self):
        original = e.base.regular
        target = e.p03.WORKFLOW
        def changed(root, path):
            return original(root, path) + (b' ' if path == target else b'')
        with mock.patch.object(e.base, 'regular', side_effect=changed), self.assertRaises(e.base.EvidenceError):
            e.build_extension()

    def test_importer_rejects_missing_archive_before_writes(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(e.base.EvidenceError):
            importer.import_verified({}, self.actions, Path(directory))
        self.assertTrue(self.archives)

    def test_importer_symlink_parent_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'alias').symlink_to(e.ROOT, target_is_directory=True)
            with self.assertRaises(e.base.EvidenceError): importer.write('alias/no-write', b'x', root)

    def test_gate_read_override_is_restored_after_failure(self):
        engine = e.adapter.load_engine()
        original = engine._read_json_path
        with self.assertRaises((RuntimeError, e.base.EvidenceError)):
            e.validate_gate(engine, {}, Path(e.adapter.CONFIG))
        self.assertIs(engine._read_json_path, original)


def action_test(name, mutate):
    def test(self):
        for suite in self.actions:
            actions = deepcopy(self.actions[suite]); mutate(actions)
            with self.subTest(suite=suite), self.assertRaises((e.base.EvidenceError, KeyError, TypeError)):
                e.validate_actions(actions, suite)
    setattr(Stage81EvidenceTests, 'test_actions_reject_' + name, test)


for name, mutation in {
    'failed_run': lambda a: a['run'].update(conclusion='failure'),
    'unfinished_run': lambda a: a['run'].update(status='in_progress'),
    'wrong_head': lambda a: a['run'].update(head_sha='0'*40),
    'wrong_repository': lambda a: a['run'].update(repository='other/fork'),
    'boolean_attempt': lambda a: a['run'].update(run_attempt=True),
    'missing_job': lambda a: a['jobs'].pop(),
    'duplicate_job': lambda a: a['jobs'].append(a['jobs'][0]),
    'wrong_job_head': lambda a: a['jobs'][0].update(head_sha='0'*40),
    'failed_job': lambda a: a['jobs'][0].update(conclusion='failure'),
    'skipped_required_step': lambda a: next(s for s in a['jobs'][0]['steps'] if s['name'] in ('Fixed toolchain','Regression tests for exact candidate and unchanged contracts')).update(conclusion='skipped'),
    'missing_artifact': lambda a: a['artifacts'].pop(),
    'wrong_artifact_digest': lambda a: a['artifacts'][0].update(digest='sha256:'+'0'*64),
    'wrong_artifact_head': lambda a: a['artifacts'][0].update(head_sha='0'*40),
    'missing_toolchain': lambda a: a['sources'].pop(e.TOOLCHAIN[0]),
}.items():
    action_test(name, mutation)

for name, mutation in {
    'false_exit': lambda r: r['cases'][0]['process'].update(returncode=False),
    'signal_exit': lambda r: r['cases'][0]['process'].update(returncode=-11),
    'timed_out': lambda r: r['cases'][0]['process'].update(timed_out=True),
    'missing_case': lambda r: r['cases'].pop(),
    'duplicated_case': lambda r: r['cases'].append(r['cases'][0]),
    'missing_negative_control': lambda r: r['pre_repair_controls'].pop(),
    'false_cache_count': lambda r: r.update(cached_results_reused=False),
    'full_acceptance_claim': lambda r: r.update(full_p03_acceptance=True),
    'release_claim': lambda r: r.update(release_ready=True),
    'other_rom': lambda r: r['candidate_build']['candidate'].update(sha256='0'*64),
    'parent_crash': lambda r: r['pre_repair_controls'][0]['process'].update(returncode=-11),
    'raw_stream_tampering': lambda r: r['cases'][0]['stdout'].update(sha256='0'*64),
}.items():
    def test(self, mutate=mutation):
        files = dict(self.payload); report = e.p03.strict_json(files['result.json']); mutate(report)
        files['result.json'] = files['job.stdout.json'] = e.base.stable(report)
        with self.assertRaises((e.base.EvidenceError, RuntimeError, ValueError, KeyError)):
            e.validate_p03(files)
    setattr(Stage81EvidenceTests, 'test_p03_reject_' + name, test)

for name in e.ARCHIVES:
    def test(self, name=name):
        data = bytearray(self.archives[name]); data[len(data)//2] ^= 1
        with self.assertRaises(e.base.EvidenceError): e.unpack(bytes(data), name)
    setattr(Stage81EvidenceTests, 'test_corrupt_zip_' + name.replace('-', '_'), test)



class DownloadRedirectTests(unittest.TestCase):
    def test_artifact_redirect_never_forwards_github_authorization(self):
        name = next(iter(e.ARCHIVES))
        payload = b'exact-archive-bytes'

        def open_request(request, timeout):
            self.assertEqual(timeout, 60)
            self.assertEqual(request.get_header('Authorization'), 'Bearer unit-test-token')
            redirected = importer.urllib.request.HTTPRedirectHandler().redirect_request(
                request, None, 302, 'Found', {},
                'https://example.blob.core.windows.net/artifacts/source.zip?sig=unit-test')
            self.assertIsNone(redirected.get_header('Authorization'))
            response = mock.MagicMock()
            response.__enter__.return_value.read.return_value = payload
            return response

        with mock.patch.dict(importer.os.environ, {'GH_TOKEN': 'unit-test-token'}), \
                mock.patch.object(importer.urllib.request, 'urlopen', side_effect=open_request), \
                mock.patch.object(importer.evidence, 'unpack') as unpack:
            self.assertEqual(importer.download(name), payload)
            unpack.assert_called_once_with(payload, name)


if __name__ == '__main__': unittest.main()
