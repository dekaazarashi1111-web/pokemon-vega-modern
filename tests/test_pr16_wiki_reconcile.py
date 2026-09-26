"""記録確定の拒否境界だけを試験。受入済みWiki/native suiteを再実行しない。"""
from __future__ import annotations
import copy
import io
from pathlib import Path
import sys
import unittest
import urllib.request
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from pr16_candidate_wiki_inputs import stable, digest
from pr16_wiki_reconcile import RUNS, REPO, BRANCH, TASK, PROOF_FILES, ZERO_KEYS, SafeRedirect, validate_run, proof_files, validate_proof, validate_child

EXPECTED = RUNS[-1]
CANDIDATE = {'sha256': 'a'*64, 'size': 33554432, 'crc32': 'CC068B4A'}


def files_fixture():
    run, head, child, tests, _ = EXPECTED
    build = dict(status='PASS', command='build', candidate=CANDIDATE, files=1, bytes=2, tree_sha256='b'*64,
                 internal_links=0, output='docs/wiki/fixture', counts={}, record_counts={}, check_writes=0)
    receipt = {k: v for k, v in build.items() if k not in ('command', 'check_writes')}
    receipt.update(source_head=head, verification_run=run, issue18_complete=False,
                   unit={'tests': tests, 'errors': 0, 'failures': 0, 'skips': 0})
    proof = dict(status='PASS_WIKI_BUILD_CHECK', two_process_builds_identical=True,
                 actual_check_unchanged_bytes_and_mtimes=True, stage61_unchanged=True,
                 active_baseline_changed=False, issue18_complete=False, **{k: 0 for k in ZERO_KEYS})
    return {'build-11.json': stable(build), 'build-29.json': stable(build),
            'check.stdout.json': stable(dict(build, command='check')), 'check.stderr.txt': b'',
            'cli-check.json': stable(proof), 'acceptance.json': stable(receipt),
            'followup-unit.txt': f'\nRan {tests} tests in 0.001s\n\nOK\n'.encode(), 'reflected-head.txt': (child+'\n').encode()}


def remote_fixture():
    run, head, _child, _tests, _scope = EXPECTED
    metadata = dict(id=run, head_sha=head, head_branch=BRANCH, repository={'full_name': REPO}, event='push',
                    path='.github/workflows/pr16-candidate-wiki.yml', status='completed', conclusion='success')
    steps = [dict(name=n, status='completed', conclusion='success') for n in ('同branchへ非force push', 'Run actions/upload-artifact@v4')]
    jobs = dict(total_count=1, jobs=[dict(run_id=run, head_sha=head, name='wiki', status='completed', conclusion='success', steps=steps)])
    artifacts = dict(total_count=1, artifacts=[dict(id=1, name='pr16-candidate-wiki-cli', expired=False, digest='sha256:'+'c'*64,
                    workflow_run=dict(id=run, head_sha=head, head_branch=BRANCH))])
    return metadata, jobs, artifacts


class ReconcileTests(unittest.TestCase):
    def check_proof(self, files=None): return validate_proof(files or files_fixture(), EXPECTED, CANDIDATE)
    def mutate(self, name, key, value):
        import json
        files=files_fixture(); row=json.loads(files[name]); row[key]=value; files[name]=stable(row)
        with self.assertRaises(ValueError):self.check_proof(files)
    def zip_bytes(self, files):
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as archive:
            for name,value in files.items():archive.writestr(name,value)
        return raw.getvalue()
    def test_proof_valid(self):self.assertEqual(self.check_proof()['tests'],26)
    def test_remote_completed(self):self.assertEqual(validate_run(*remote_fixture(),EXPECTED)['id'],1)
    def test_in_progress_not_success(self):
        run,jobs,arts=remote_fixture();run['status']='in_progress'
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_failed_run(self):
        run,jobs,arts=remote_fixture();run['conclusion']='failure'
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_wrong_source(self):
        run,jobs,arts=remote_fixture();run['head_sha']='d'*40
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_wrong_branch(self):
        run,jobs,arts=remote_fixture();run['head_branch']='main'
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_other_repository(self):
        run,jobs,arts=remote_fixture();run['repository']['full_name']='other/repo'
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_other_workflow(self):
        run,jobs,arts=remote_fixture();run['path']='.github/workflows/other.yml'
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_job_pagination_not_ignored(self):
        run,jobs,arts=remote_fixture();jobs['total_count']=2
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_skipped_step_rejected(self):
        run,jobs,arts=remote_fixture();jobs['jobs'][0]['steps'][0]['conclusion']='skipped'
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_push_step_missing(self):
        run,jobs,arts=remote_fixture();jobs['jobs'][0]['steps']=jobs['jobs'][0]['steps'][1:]
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_expired_artifact(self):
        run,jobs,arts=remote_fixture();arts['artifacts'][0]['expired']=True
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_duplicate_artifact(self):
        run,jobs,arts=remote_fixture();arts['artifacts']*=2;arts['total_count']=2
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_artifact_wrong_run(self):
        run,jobs,arts=remote_fixture();arts['artifacts'][0]['workflow_run']['id']=7
        with self.assertRaises(ValueError):validate_run(run,jobs,arts,EXPECTED)
    def test_zip_digest_checked(self):
        raw=self.zip_bytes(files_fixture())
        with self.assertRaises(ValueError):proof_files(raw,'0'*64)
    def test_zip_roundtrip(self):
        files=files_fixture();raw=self.zip_bytes(files);self.assertEqual(proof_files(raw,digest(raw)),files)
    def test_zip_path_traversal(self):
        files=files_fixture();files['../x']=b'x';raw=self.zip_bytes(files)
        with self.assertRaises(ValueError):proof_files(raw,digest(raw))
    def test_zip_missing_original(self):
        files=files_fixture();files.pop('reflected-head.txt');raw=self.zip_bytes(files)
        with self.assertRaises(ValueError):proof_files(raw,digest(raw))
    def test_zip_nul_rejected(self):
        files=files_fixture();files['check.stderr.txt']=b'\0';raw=self.zip_bytes(files)
        with self.assertRaises(ValueError):proof_files(raw,digest(raw))
    def test_seed_difference(self):self.mutate('build-29.json','files',2)
    def test_tree_mismatch(self):self.mutate('check.stdout.json','tree_sha256','c'*64)
    def test_candidate_mismatch(self):self.mutate('acceptance.json','candidate',dict(CANDIDATE,crc32='00000000'))
    def test_check_writes_rejected(self):self.mutate('check.stdout.json','check_writes',1)
    def test_native_repetition_rejected(self):self.mutate('cli-check.json','accepted_native_reruns',1)
    def test_bool_zero_rejected(self):self.mutate('cli-check.json','new_native_runs',False)
    def test_issue18_promotion_rejected(self):self.mutate('acceptance.json','issue18_complete',True)
    def test_wrong_unit_count(self):
        files=files_fixture();files['followup-unit.txt']=b'\nRan 25 tests in 0.001s\n\nOK\n'
        with self.assertRaises(ValueError):self.check_proof(files)
    def test_fail_then_ok_not_a_single_run(self):
        files=files_fixture();files['followup-unit.txt']*=2
        with self.assertRaises(ValueError):self.check_proof(files)
    def test_reflected_commit_mismatch(self):
        files=files_fixture();files['reflected-head.txt']=b'bad\n'
        with self.assertRaises(ValueError):self.check_proof(files)
    def test_child_parent_checked(self):
        commit=dict(sha=EXPECTED[2],parents=[{'sha':EXPECTED[1]}],message=TASK+': 完了')
        validate_child(commit,EXPECTED);commit['parents'][0]['sha']='f'*40
        with self.assertRaises(ValueError):validate_child(commit,EXPECTED)
    def test_merge_child_not_linear(self):
        commit=dict(sha=EXPECTED[2],parents=[{'sha':EXPECTED[1]},{'sha':'d'*40}],message=TASK+': 完了')
        with self.assertRaises(ValueError):validate_child(commit,EXPECTED)
    def test_redirect_removes_authorization(self):
        request=urllib.request.Request('https://api.github.com/repos/a/b',headers={'Authorization':'Bearer test-only'})
        redirect=SafeRedirect().redirect_request(request,None,302,'Found',{},'https://example.test/blob')
        self.assertFalse(redirect.has_header('Authorization'))
    def test_insecure_redirect_rejected(self):
        request=urllib.request.Request('https://api.github.com/repos/a/b')
        with self.assertRaises(ValueError):SafeRedirect().redirect_request(request,None,302,'Found',{},'http://example.test/blob')
    def test_four_slices_counted_once(self):
        self.assertEqual(sum(r[3] for r in RUNS),110);self.assertEqual(len({r[0] for r in RUNS}),4)

if __name__=='__main__':unittest.main()
