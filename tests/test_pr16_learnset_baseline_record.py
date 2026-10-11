"""Issue19の記録境界のみ。受入済み39試験・生成・nativeは呼び出さない。"""
import copy
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_learnset_baseline_record as r


def binding():
    return dict(run_id=1, source_head='1' * 40, artifact_id=2, artifact_sha256='2' * 64)


def actions():
    q = binding()
    run = dict(id=1, head_sha=q['source_head'], head_branch=r.BRANCH,
        repository={'full_name': r.REPO}, event='push',
        path='.github/workflows/pr16-learnset-baseline.yml', status='completed', conclusion='success')
    job = dict(id=3, run_id=1, head_sha=q['source_head'], name='baseline-verify',
        status='completed', conclusion='success',
        steps=[dict(name='Run actions/upload-artifact@v4', status='completed', conclusion='success')])
    artifact = dict(id=2, name='pr16-learnset-baseline-verified', digest='sha256:' + q['artifact_sha256'],
        expired=False, workflow_run=dict(id=1, head_sha=q['source_head'], head_branch=r.BRANCH))
    return run, dict(total_count=1, jobs=[job]), dict(total_count=1, artifacts=[artifact]), q


def documents():
    q = binding()
    report = dict(status='PASS_OFFICIAL_SOURCE_ISOLATION', task=r.TASK,
        source_head=q['source_head'], run_id=1, focused_tests=39,
        two_process_builds_identical=True, readonly_check_byte_mtime_unchanged=True,
        tracked_tree_unchanged=True, local_and_actions_output_identical=True,
        rom_changes=0, new_native_runs=0, accepted_native_reruns=0,
        issue19_complete=False, release_ready=False)
    receipt = dict(official_records=1299, official_routes=118524, route_kinds=dict(r.KINDS),
        source_semantic_differences=0, vega_pending_species=181, vega_baseline_rows_imported=0,
        owner_overlay_rows=0, p07_historical_rows_preserved=1572,
        activation_gate={'ready': False}, rom_changed=False, release_ready=False,
        spec_only_routes=159, spec_only_species=103)
    return report, receipt, q


def fake_archive(extra=None):
    report, receipt, request = documents()
    outputs = {n: b'{}\n' for n in r.COPIED if n != 'receipt.json'}
    outputs.update({'official_baseline.jsonl': b'{"test":1}\n', 'historical_layers.json': b'{"test":2}\n'})
    ident = lambda v: dict(size=len(v), sha256=r.sha(v))
    receipt['outputs'] = {k: ident(v) for k, v in outputs.items()}
    receipt_bytes = r.stable_json(receipt)
    outputs['receipt.json'] = receipt_bytes
    report['files'] = {k: ident(v) for k, v in outputs.items()}
    proof = {n: receipt_bytes for n in ('build11.json', 'build29.json', 'check.json')}
    proof.update({'verify.json': r.stable_json(report), 'unit.log': b'Ran 39 tests in 0.1s\n\nOK\n'})
    proof.update({'outputs/' + k: v for k, v in outputs.items()})
    if extra:
        proof.update(extra)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
        for key, data in proof.items(): z.writestr(key, data)
    raw = stream.getvalue()
    request['artifact_sha256'] = r.sha(raw)
    return raw, request


class RecordingBoundaries(unittest.TestCase):
    def test_completed_original_is_accepted(self):
        args = actions()
        self.assertEqual(r.validate_run(*args)['id'], 2)

    def test_wrong_source_identity_rejected(self):
        for key, value in [('head_sha', 'f' * 40), ('head_branch', 'main'), ('event', 'pull_request'),
                           ('path', 'other.yml'), ('repository', {'full_name': 'other/repo'})]:
            with self.subTest(key=key):
                run, jobs, arts, request = actions(); run[key] = value
                with self.assertRaises(ValueError): r.validate_run(run, jobs, arts, request)

    def test_incomplete_failed_or_skipped_run_rejected(self):
        for kind in ('run_pending', 'run_failed', 'step_skipped', 'job_pending', 'missing_upload'):
            with self.subTest(kind=kind):
                run, jobs, arts, request = actions(); job = jobs['jobs'][0]
                if kind == 'run_pending': run['status'] = 'in_progress'
                if kind == 'run_failed': run['conclusion'] = 'failure'
                if kind == 'step_skipped': job['steps'][0]['conclusion'] = 'skipped'
                if kind == 'job_pending': job['status'] = 'in_progress'
                if kind == 'missing_upload': job['steps'][0]['name'] = 'read'
                with self.assertRaises(ValueError): r.validate_run(run, jobs, arts, request)

    def test_artifact_identity_expiry_and_pagination_rejected(self):
        for kind in ('digest', 'expired', 'head', 'job_page', 'artifact_page', 'duplicate'):
            with self.subTest(kind=kind):
                run, jobs, arts, request = actions(); a = arts['artifacts'][0]
                if kind == 'digest': a['digest'] = 'sha256:' + '3' * 64
                if kind == 'expired': a['expired'] = True
                if kind == 'head': a['workflow_run']['head_sha'] = '4' * 40
                if kind == 'job_page': jobs['total_count'] = 2
                if kind == 'artifact_page': arts['total_count'] = 2
                if kind == 'duplicate': arts['artifacts'].append(copy.deepcopy(a)); arts['total_count'] = 2
                with self.assertRaises(ValueError): r.validate_run(run, jobs, arts, request)

    def test_source_only_report_cannot_be_native_or_release(self):
        for key, value in [('rom_changes', 1), ('new_native_runs', 1), ('accepted_native_reruns', False),
                           ('issue19_complete', True), ('readonly_check_byte_mtime_unchanged', False),
                           ('release_ready', True), ('focused_tests', 38)]:
            with self.subTest(key=key):
                report, receipt, request = documents(); report[key] = value
                with self.assertRaises(ValueError): r.validate_report(report, receipt, request)

    def test_receipt_coverage_and_layer_leak_rejected(self):
        for key, value in [('official_records', 1300), ('official_routes', 118528),
                           ('source_semantic_differences', 1), ('vega_pending_species', 206),
                           ('owner_overlay_rows', 1), ('vega_baseline_rows_imported', 181),
                           ('spec_only_routes', 0), ('p07_historical_rows_preserved', 0)]:
            with self.subTest(key=key):
                report, receipt, request = documents(); receipt[key] = value
                with self.assertRaises(ValueError): r.validate_report(report, receipt, request)

    def test_all_proof_outputs_validated_and_compact_only_retained(self):
        raw, request = fake_archive()
        kept = r.read_proof(raw, request)
        self.assertEqual(len(kept), 10)
        self.assertNotIn('outputs/official_baseline.jsonl', kept)
        self.assertNotIn('outputs/historical_layers.json', kept)

    def test_corruption_source_route_and_check_mismatch_rejected(self):
        for extra in ({'outputs/official_baseline.jsonl': b'{"test":3}\n'},
                      {'check.json': b'{}\n'}, {'unit.log': b'Ran 39 tests in 0.1s\n\nFAILED\n'}):
            with self.subTest(extra=extra):
                raw, request = fake_archive(extra)
                with self.assertRaises(ValueError): r.read_proof(raw, request)
        raw, request = fake_archive(); request['artifact_sha256'] = '0' * 64
        with self.assertRaises(ValueError): r.read_proof(raw, request)

    def test_archive_path_traversal_rejected(self):
        for path in ('../outside.json', '/outside.json', 'a\\b.json'):
            with self.subTest(path=path):
                raw, request = fake_archive({path: b'{}'})
                with self.assertRaises(ValueError): r.read_proof(raw, request)

    def test_synchronization_preserves_candidate_wiki_and_native(self):
        original = json.loads((ROOT / r.STATE).read_bytes())
        original.pop('learnset_baseline', None)
        before = copy.deepcopy(original)
        changed = r.synchronize(original, dict(source_head='1' * 40, run_id=1))
        self.assertEqual(original, before)
        for key in ('candidate', 'candidate_wiki', 'current_p08_candidate', 'latest_native_run',
                    'latest_native_tested_head', 'last_accepted_native_run', 'release_ready'):
            self.assertEqual(changed[key], before[key])
        self.assertEqual(changed['bp']['next_step'], changed['next_action']['goal_ja'])

    def test_duplicate_recording_is_rejected(self):
        with self.assertRaises(ValueError): r.synchronize({'learnset_baseline': {}}, {})

    def test_recording_log_requires_exact_twelve_successes(self):
        r.validate_recording_log(b'Ran 12 tests in 0.1s\n\nOK\n')
        for text in (b'Ran 11 tests in 0.1s\n\nOK\n', b'Ran 12 tests in 0.1s\n\nFAILED\n',
                     b'Ran 12 tests in 0.1s\n\nOK (skipped=1)\n', b''):
            with self.assertRaises(ValueError): r.validate_recording_log(text)


if __name__ == '__main__': unittest.main()
