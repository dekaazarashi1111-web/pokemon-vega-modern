#!/usr/bin/env python3
"""Keep a pinned native execution, including failures; never close a gap here.

This is an explicit evidence-write command, not emulator execution. The caller
must add the scanned original.zip EXACT path with git add -f, then call git_check
on INDEX and HEAD. Merely copying an ignored ZIP is not durable retention.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

import pr16_fixed_form_acceptance as fixed
import pr16_fixed_form_originals as originals

ROOT = Path(__file__).resolve().parents[1]
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
PREFIX = 'pr16-fixed-form-acceptance/'
need = fixed.need
identity = originals.identity


def strict(raw: bytes) -> dict:
    need(type(raw) is bytes and len(raw) <= 4000000, 'invalid JSON evidence input')
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'duplicate JSON evidence key: ' + key)
            out[key] = value
        return out
    def reject(value):
        raise ValueError('nonfinite JSON: ' + value)
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs, parse_constant=reject)


def pin_check(pin: dict) -> None:
    need(type(pin) is dict and set(pin) == {'run_id', 'job_id', 'artifact_id', 'head', 'size', 'sha256', 'cases', 'conclusion'}, 'invalid pin schema')
    for key in ('run_id', 'job_id', 'artifact_id', 'size'):
        need(type(pin[key]) is int and pin[key] > 0, 'invalid pin integer: ' + key)
    need(pin['size'] <= 32000000, 'oversized evidence ZIP')
    for key, count in (('head', 40), ('sha256', 64)):
        need(type(pin[key]) is str and re.fullmatch('[0-9a-f]{' + str(count) + '}', pin[key]) is not None, 'invalid pin digest: ' + key)
    fixed.selected_cases(pin['cases'])
    need(pin['conclusion'] in ('success', 'failure'), 'invalid native conclusion')


def process(raw: bytes, expected_code: int) -> dict:
    row = strict(raw)
    want = dict(schema_version=1, returncode=expected_code, spawn_error=None, timed_out=False)
    need(type(row) is dict and set(row) == set(want), 'process schema differs')
    need(all(type(row[k]) is type(v) and row[k] == v for k, v in want.items()), 'process did not exit as pinned')
    return row


def validate(raw: bytes, pin: dict, *, source_reader=None) -> tuple[dict, dict]:
    pin_check(pin)
    need(identity(raw) == {k: pin[k] for k in ('size', 'sha256')}, 'outer ZIP identity differs')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        originals.scan(archive)
        report = strict(archive.read(PREFIX + 'result.json'))
        receipt = strict(archive.read(PREFIX + 'receipt.json'))
        need(receipt['tested_head'] == pin['head'], 'tested HEAD differs')
        for claim in ('p03_fixed_form_gap_closed', 'release_ready'):
            need(receipt[claim] is False and report[claim] is False, 'execution claims unsupported promotion')
        need(report['full_p03_acceptance'] is False and report['old_runs_relabelled'] == 0, 'execution inflated old evidence')
        for name, bound in receipt['members'].items():
            need(identity(archive.read(PREFIX + name)) == bound, 'receipt member differs: ' + name)
        need(report['candidate'] == dict(size=33554432, sha256=fixed.SHA), 'candidate identity differs')
        need(report['requested_cases'] == pin['cases'] and report['actual_new_processes'] == len(pin['cases']), 'case request/process count differs')
        need(report['guard_checks'] == list(fixed.GUARDS), 'seven native write guards missing')
        process(archive.read(PREFIX + 'compile.process.json'), 0)
        for guard in fixed.GUARDS:
            process(archive.read(PREFIX + 'guard-' + guard + '.process.json'), 1)
            need(archive.read(PREFIX + 'guard-' + guard + '.stdout') == b'', 'write-guard stdout differs')
            need(archive.read(PREFIX + 'guard-' + guard + '.stderr') == b'P03 archive: host write after observation barrier\n', 'write-guard failure is not the host barrier')
        successes = report['results']
        failures = report['failures']
        need(type(successes) is list and type(failures) is list, 'invalid results/failures')
        names = [r['name'] for r in successes + failures]
        need(len(names) == len(set(names)) == len(pin['cases']) and set(names) == set(pin['cases']), 'run omitted or duplicated a case')
        for row in successes:
            name = row['name']
            need(process(archive.read(PREFIX + name + '.process.json'), 0) == row['process'], 'result/process binding differs')
            result = fixed.validate(archive.read(PREFIX + name + '.stdout'), archive.read(PREFIX + name + '.stderr'), name, 0, report['auxiliary_moves'])
            need(row['result'] == result, 'accepted payload differs from raw stdout')
        for row in failures:
            name = row['name']
            need(process(archive.read(PREFIX + name + '.process.json'), 1) == row['process'], 'failed process binding differs')
            need(type(row['error']) is str and row['error'], 'failure reason missing')
            text = archive.read(PREFIX + name + '.stderr').decode('utf-8')
            need('P03 archive:' in text, 'failed controller has no retained error')
        expected = 'failure' if failures else 'success'
        need(expected == pin['conclusion'], 'Actions conclusion and raw results disagree')
        need(report['status'] == ('FAIL' if failures else 'PASS_SCOPED_PENDING_FIVE_CASES' if len(names) < 5 else 'PASS_NATIVE_PENDING_DURABLE_RECEIPT'), 'execution status differs')
        with zipfile.ZipFile(io.BytesIO(archive.read(PREFIX + 'sources.zip'))) as sources:
            need(set(sources.namelist()) == set(report['sources']), 'source set differs')
            for name, bound in report['sources'].items():
                data = sources.read(name)
                need(identity(data) == bound, 'source digest differs: ' + name)
                if source_reader is not None:
                    need(source_reader(pin['head'], name) == data, 'tested commit source differs: ' + name)
        return report, receipt


def git_check(record: dict, surface: str = 'INDEX') -> None:
    need(surface in ('INDEX', 'HEAD'), 'unexpected Git surface')
    original = record['original']
    path = original['path']
    prefix = ':' if surface == 'INDEX' else 'HEAD:'
    data = subprocess.check_output(['git', 'show', prefix + path], cwd=ROOT)
    need(identity(data) == {k: original[k] for k in ('size', 'sha256')}, 'original is missing/different in Git ' + surface)


def retain(pin: dict, note: str) -> dict:
    pin_check(pin)
    need(os.environ.get('GITHUB_REPOSITORY') == REPO, 'unexpected retention repository')
    need(type(note) is str and note.strip(), 'retention note missing')
    dest = ROOT / originals.BASE / str(pin['run_id'])
    need(not dest.exists() and not any(p.is_symlink() for p in (dest, *dest.parents)), 'retention is create-only, without symlinks')
    def api(path):
        return subprocess.check_output(['gh', 'api', f'repos/{REPO}/' + path], timeout=90)
    run = strict(api(f'actions/runs/{pin["run_id"]}'))
    jobs = strict(api(f'actions/runs/{pin["run_id"]}/jobs'))
    artifact = strict(api(f'actions/artifacts/{pin["artifact_id"]}'))
    need(run['id'] == pin['run_id'] and run['head_sha'] == pin['head'] and run['run_attempt'] == 1 and run['status'] == 'completed' and run['conclusion'] == pin['conclusion'], 'live run differs')
    need(len(jobs['jobs']) == 1 and jobs['jobs'][0]['id'] == pin['job_id'] and jobs['jobs'][0]['conclusion'] == pin['conclusion'], 'live job differs')
    need(artifact['id'] == pin['artifact_id'] and artifact['workflow_run']['head_sha'] == pin['head'] and artifact['workflow_run']['id'] == pin['run_id'] and artifact['digest'] == 'sha256:' + pin['sha256'] and artifact['expired'] is False, 'live artifact differs')
    raw = api(f'actions/artifacts/{pin["artifact_id"]}/zip')
    def source_reader(head, name):
        return subprocess.check_output(['git', 'show', head + ':' + name], cwd=ROOT)
    report, receipt = validate(raw, pin, source_reader=source_reader)
    record = dict(schema_version=1, status='RETAINED_NATIVE_EXECUTION_NOT_GAP_CLOSEOUT', pin=pin, note=note, result=report, inner_receipt=receipt, original=dict(path=(dest / 'original.zip').relative_to(ROOT).as_posix(), **identity(raw)), new_emulator_runs_during_retention=0, p03_fixed_form_gap_closed=False, release_ready=False)
    dest.mkdir(parents=True)
    (dest / 'original.zip').write_bytes(raw)
    (dest / 'actions.json').write_bytes(fixed.stable(dict(schema_version=1, run=run, jobs=jobs, artifact=artifact, download=identity(raw))))
    (dest / 'checkpoint.json').write_bytes(fixed.stable(record))
    return record
