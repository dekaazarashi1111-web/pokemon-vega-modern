"""Synthetic metadata/archive negatives; none are counted as mGBA executions."""
from __future__ import annotations
import copy
import io
from pathlib import Path
import stat
import sys
import unittest
from unittest import mock
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import record_modernization_p03_breeding as r


def provenance():
    data = b'original ZIP identity fixture'
    run = {'id': r.SOURCE_RUN, 'head_sha': r.TESTED_HEAD, 'head_branch': r.BRANCH,
           'path': r.breeding.WORKFLOW, 'repository': {'full_name': r.REPO},
           'status': 'completed', 'conclusion': 'success', 'event': 'push', 'run_attempt': 1}
    jobs = [{'run_id': r.SOURCE_RUN, 'head_sha': r.TESTED_HEAD, 'name': 'breeding',
             'status': 'completed', 'conclusion': 'success',
             'steps': [{'name': name, 'status': 'completed', 'conclusion': 'success'}
                       for name in r.REQUIRED_STEPS]}]
    artifact = {'id': 101, 'name': r.ARTIFACT, 'expired': False, 'size_in_bytes': len(data),
                'digest': 'sha256:' + r.digest(data)['sha256'],
                'workflow_run': {'id': r.SOURCE_RUN, 'head_sha': r.TESTED_HEAD},
                'archive_download_url': 'https://api.github.com/repos/' + r.REPO + '/actions/artifacts/101/zip'}
    return run, jobs, artifact, data


def archive(entries):
    output = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with zipfile.ZipFile(output, 'w') as z:
            for name, data in entries:
                z.writestr(name, data)
    return output.getvalue()


class BreedingEvidenceTests(unittest.TestCase):
    def test_deep_integer_and_boolean_types(self):
        self.assertTrue(r.same({'a': [0, False]}, {'a': [0, False]}))
        self.assertFalse(r.same({'a': {'returncode': False}}, {'a': {'returncode': 0}}))
        self.assertFalse(r.same({'a': [False]}, {'a': [0]}))
        self.assertFalse(r.same({'a': 1}, {'a': 1.0}))

    def test_complete_source_actions_metadata(self):
        r.validate_actions(*provenance())

    def test_rejects_failed_incomplete_or_wrong_source_run(self):
        for key, value in [('id', 123), ('head_sha', '0'*40), ('head_branch', 'main'),
                           ('path', '.github/workflows/ci.yml'), ('status', 'in_progress'),
                           ('conclusion', 'failure'), ('conclusion', None),
                           ('event', 'workflow_dispatch'), ('run_attempt', True), ('run_attempt', 2)]:
            values = list(provenance()); values[0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                r.validate_actions(*values)

    def test_rejects_other_repository(self):
        values=list(provenance()); values[0]['repository']['full_name']='other/repo'
        with self.assertRaises(ValueError):r.validate_actions(*values)

    def test_rejects_missing_duplicate_or_failed_jobs(self):
        for jobs in ([], provenance()[1]*2):
            values=list(provenance()); values[1]=jobs
            with self.assertRaises(ValueError):r.validate_actions(*values)
        for key, value in [('run_id', 1), ('head_sha', '0'*40), ('conclusion', 'failure'),
                           ('status', 'in_progress'), ('name', 'other')]:
            values=list(provenance());values[1][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.validate_actions(*values)

    def test_rejects_missing_duplicate_skipped_native_steps(self):
        for index in range(len(r.REQUIRED_STEPS)):
            for mutation in ('missing', 'duplicate', 'skipped', 'failed'):
                values=list(provenance());steps=values[1][0]['steps']
                if mutation=='missing':del steps[index]
                elif mutation=='duplicate':steps.append(steps[index].copy())
                else:steps[index]['conclusion']='skipped' if mutation=='skipped' else 'failure'
                with self.subTest(index=index,mutation=mutation),self.assertRaises(ValueError):
                    r.validate_actions(*values)

    def test_rejects_changed_zip_size_digest_or_artifact(self):
        for key,value in [('name','other'),('expired',True),('size_in_bytes',0),
                          ('digest','sha256:'+'0'*64),('id',False),
                          ('archive_download_url','https://example.com/stolen')]:
            values=list(provenance());values[2][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.validate_actions(*values)
        values=list(provenance());values[3]+=b'changed'
        with self.assertRaises(ValueError):r.validate_actions(*values)

    def test_rejects_mixed_artifact_source(self):
        for key,value in [('id',123),('head_sha','0'*40)]:
            values=list(provenance());values[2]['workflow_run'][key]=value
            with self.assertRaises(ValueError):r.validate_actions(*values)

    def test_normal_process_receipt_is_exact_not_truthy(self):
        original={'schema_version':1,'returncode':0,'timed_out':False,'spawn_error':None}
        self.assertEqual(r.process(original,0),0)
        for key,value in [('schema_version',True),('returncode',False),('returncode',-11),
                          ('returncode',1),('timed_out',True),('timed_out',0),('spawn_error','timeout')]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                r.process(original|{key:value},0)
        with self.assertRaises(ValueError):r.process(original|{'extra':True},0)

    def test_archive_round_trip_bytes(self):
        self.assertEqual(r.archive_members(archive([('runtime/',b''),('runtime/a',b'\xff\0')])),
                         {'runtime/a':b'\xff\0'})

    def test_rejects_archive_traversal_aliases_and_duplicate_members(self):
        for name in ('../escape','/escape','a/../escape','a\\escape','a//escape','./escape'):
            with self.subTest(name=name),self.assertRaises(ValueError):
                r.archive_members(archive([(name,b'bad')]))
        with self.assertRaises(ValueError):r.archive_members(archive([('same',b'a'),('same',b'b')]))

    def test_rejects_archive_symlinks(self):
        item=zipfile.ZipInfo('link');item.create_system=3;item.external_attr=(stat.S_IFLNK|0o777)<<16
        with self.assertRaises(ValueError):r.archive_members(archive([(item,b'../../secret')]))

    def test_rejects_unbounded_member_count(self):
        with self.assertRaises(ValueError):
            r.archive_members(archive([(str(i),b'') for i in range(201)]))

    def test_source_closure_requires_runner_dependencies_and_baseline(self):
        required=r.required_sources()
        for source in (r.breeding.SOURCE,r.breeding.SELF,r.breeding.TEST,r.breeding.WORKFLOW,
                       'config/active_play_baseline.json','infra/toolchain_manifest.json',
                       'tools/mgba_battle_core_smoke.c','overlays/acquisition_runtime/acquisition_engine_adapter_rom.c'):
            self.assertIn(source,required)

    def test_rejects_missing_original_payload_before_acceptance(self):
        with self.assertRaises(KeyError):r.validate_payload({})
        with self.assertRaises(ValueError):r.validate_payload({'source-head.txt':b'other\n'})

    def test_summary_cannot_claim_full_breeding_or_new_integration_executions(self):
        summary=r.summary({'candidate':{'size':33554432,'sha256':r.breeding.repair.CANDIDATE_SHA}})
        self.assertEqual(summary['fresh_mgba_processes_in_original'],8)
        self.assertEqual(summary['fresh_core_instances_in_original'],24)
        self.assertEqual(summary['new_mgba_processes_during_integration'],0)
        self.assertEqual(summary['physical_breeding_cases'],list(r.breeding.CASES))
        for key in ('all_breeding_paths_accepted','full_p03_acceptance','release_ready','active_stage62_baseline_changed'):
            self.assertIs(summary[key],False)
        self.assertTrue(summary['closed_conditions']);self.assertTrue(summary['remaining_conditions'])


if __name__=='__main__':unittest.main()
