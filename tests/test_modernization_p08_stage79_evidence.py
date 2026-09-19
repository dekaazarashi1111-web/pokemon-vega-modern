"""Fail-closed regression tests for the additive P08 cumulative runtime evidence."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import modernization_p08_stage79_evidence as evidence


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.source = {'run_id': 123, 'head_sha': 'a' * 40, 'run_attempt': 1}
        self.run = {'id': 123, 'head_sha': 'a' * 40, 'run_attempt': 1,
                    'repository': {'full_name': evidence.REPOSITORY},
                    'head_repository': {'full_name': evidence.REPOSITORY},
                    'head_branch': evidence.BRANCH, 'path': evidence.WORKFLOW,
                    'status': 'completed', 'conclusion': 'success'}
        names = ['plan', 'merge', *[f'domain ({d})' for d in evidence.DOMAINS]]
        self.jobs = {'total_count': 9, 'jobs': [
            {'name': name, 'run_id': 123, 'head_sha': 'a' * 40, 'status': 'completed',
             'conclusion': 'success', 'steps': [{'name': 'domainをmGBAで実行', 'conclusion': 'success'}]}
            for name in names]}
        names = ['stage79-plan', 'stage79-cumulative-result', *[f'stage79-domain-{d}' for d in evidence.DOMAINS]]
        self.artifacts = {'total_count': 9, 'artifacts': [
            {'name': name, 'workflow_run': {'id': 123, 'head_sha': 'a' * 40}, 'digest': 'sha256:' + 'b' * 64}
            for name in names]}

    def validate(self):
        evidence.validate_provenance(self.source, self.run, self.jobs, self.artifacts)

    def test_exact_completed_provenance_passes(self):
        self.validate()

    def test_failed_incomplete_or_wrong_source_run_is_rejected(self):
        for key, value in [('id', 456), ('head_sha', 'b' * 40), ('run_attempt', 2),
                           ('status', 'in_progress'), ('conclusion', 'failure'),
                           ('head_branch', 'main'), ('path', '.github/workflows/ci.yml')]:
            with self.subTest(key=key):
                before = self.run[key]
                self.run[key] = value
                with self.assertRaises(evidence.EvidenceError):
                    self.validate()
                self.run[key] = before

    def test_fork_provenance_is_rejected(self):
        self.run['head_repository']['full_name'] = 'other/repo'
        with self.assertRaises(evidence.EvidenceError):
            self.validate()

    def test_missing_and_duplicate_domain_jobs_are_rejected(self):
        self.jobs['jobs'][-1] = deepcopy(self.jobs['jobs'][-2])
        with self.assertRaises(evidence.EvidenceError):
            self.validate()

    def test_pass_stdout_cannot_override_failed_action_job(self):
        self.jobs['jobs'][-1]['conclusion'] = 'failure'
        with self.assertRaises(evidence.EvidenceError):
            self.validate()

    def test_initial_adoption_requires_executed_not_skipped_domains(self):
        self.jobs['jobs'][-1]['steps'][0]['conclusion'] = 'skipped'
        with self.assertRaises(evidence.EvidenceError):
            self.validate()

    def test_artifact_from_other_head_is_rejected(self):
        self.artifacts['artifacts'][0]['workflow_run']['head_sha'] = 'c' * 40
        with self.assertRaises(evidence.EvidenceError):
            self.validate()

    def test_missing_artifact_digest_is_rejected(self):
        self.artifacts['artifacts'][0]['digest'] = ''
        with self.assertRaises(evidence.EvidenceError):
            self.validate()


class RawResultTests(unittest.TestCase):
    def setUp(self):
        self.result = {'status': 'PASS', 'measured': True}
        self.stderr = b'raw log\xff'
        self.record = {'id': 'p02', 'status': 'PASS', 'plan_fingerprint': 'f',
                       'runner_result': self.result, 'stderr_sha256': evidence.sha(self.stderr)}
        self.summary = {'id': 'p02', 'status': 'DOMAIN_PASS', 'mGBA_process_runs': 1, 'plan_fingerprint': 'f'}
        self.stdout = evidence.stable(self.result)

    def validate(self):
        evidence.validate_domain_files('p02', self.record, self.stdout, self.stderr, self.summary, 'f')

    def test_exact_raw_result_and_binary_stderr_pass(self):
        self.validate()

    def test_forged_or_truncated_stdout_is_rejected(self):
        for raw in [b'{', b'\xff', b'{"status":"PASS"}']:
            self.stdout = raw
            with self.assertRaises(evidence.EvidenceError):
                self.validate()

    def test_stderr_tampering_is_rejected(self):
        self.stderr += b'changed'
        with self.assertRaises(evidence.EvidenceError):
            self.validate()

    def test_stale_fingerprint_is_rejected(self):
        self.record['plan_fingerprint'] = 'old'
        with self.assertRaises(evidence.EvidenceError):
            self.validate()

    def test_helper_failure_cannot_be_relabelled_as_success(self):
        self.summary['status'] = 'ERROR'
        with self.assertRaises(evidence.EvidenceError):
            self.validate()


class FileAndBindingTests(unittest.TestCase):
    def test_exact_file_hash_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'result').write_bytes(b'original')
            identity = {'size': 8, 'sha256': evidence.sha(b'original')}
            self.assertEqual(evidence.checked_bytes(root, 'result', identity), b'original')
            (root / 'result').write_bytes(b'changed!')
            with self.assertRaises(evidence.EvidenceError):
                evidence.checked_bytes(root, 'result', identity)

    def test_traversal_absolute_and_symlink_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'real').write_text('test')
            (root / 'link').symlink_to(root / 'real')
            for path in ['../real', '/etc/passwd', 'link', 'missing']:
                with self.assertRaises(evidence.EvidenceError):
                    evidence.regular(root, path)

    def test_unregistered_historical_outputs_are_not_auto_adopted(self):
        with tempfile.TemporaryDirectory() as directory:
            original = {'p08.json': b'{"release_ready":false}\n'}
            self.assertEqual(evidence.attach_outputs(original, Path(directory)), original)

    def test_registered_missing_evidence_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / evidence.CONFIG).parent.mkdir()
            (root / evidence.CONFIG).write_text('{}')
            with patch.object(evidence, 'build_extension', side_effect=evidence.EvidenceError('missing')):
                with self.assertRaises(evidence.EvidenceError):
                    evidence.attach_outputs({'p08.json': b'{}'}, root)

    def test_binding_covers_historical_document_and_runtime_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / evidence.CONFIG).parent.mkdir()
            (root / evidence.CONFIG).write_text('{}')
            original = {'p08.json': evidence.stable({'release_ready': False, 'candidate_stage': 77})}
            with patch.object(evidence, 'build_extension', return_value={'run_id': 1, 'claims': evidence.CLAIMS}):
                first = evidence.attach_outputs(original, root)
            with patch.object(evidence, 'build_extension', return_value={'run_id': 2, 'claims': evidence.CLAIMS}):
                second = evidence.attach_outputs(original, root)
            a, b = json.loads(first['p08.json']), json.loads(second['p08.json'])
            self.assertFalse(a['release_ready'])
            self.assertEqual(a['candidate_stage'], 77)
            self.assertEqual(a['cumulative_evidence_binding']['historical_document_sha256'], evidence.sha(original['p08.json']))
            self.assertNotEqual(a['cumulative_evidence_binding']['sha256'], b['cumulative_evidence_binding']['sha256'])

    def test_p08_release_promotion_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / evidence.CONFIG).parent.mkdir()
            (root / evidence.CONFIG).write_text('{}')
            with patch.object(evidence, 'build_extension', return_value={'claims': evidence.CLAIMS}):
                with self.assertRaises(evidence.EvidenceError):
                    evidence.attach_outputs({'p08.json': b'{"release_ready":true}'}, root)

    def test_manifest_requires_all_four_files_for_each_domain(self):
        files = evidence.expected_files()
        self.assertEqual(len(files), 35)
        for domain in evidence.DOMAINS:
            for name in evidence.DOMAIN_FILES:
                self.assertIn(f'domains/{domain}/{name}', files)


if __name__ == '__main__':
    unittest.main()
