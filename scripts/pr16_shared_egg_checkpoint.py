#!/usr/bin/env python3
"""Retain and revalidate sixteen new shared-only input/save originals.

This verifier starts no emulator. The historic parent adapter's generic report
scope is recorded, not interpreted as old P07 successes or a new phase closure.
"""
from copy import deepcopy
import argparse
import json
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_completion_checkpoint as prior
import pr16_shared_egg_routes as shared
need = prior.need
SELF = 'scripts/pr16_shared_egg_checkpoint.py'
RECEIPT = 'content/modernization/pr16_shared_egg_acceptance.json'
DIRECTORY = 'content/modernization/pr16_shared_egg_evidence'
RECORD = (34564143971, 10185434186, 115806,
          '1c272eaca2c44f177063633dcaec8957881b214a370979b52b4e84734488e55b',
          '00fb5ccf6009e1f87e5a83b60fda1fde35f157ac',
          'pr16-shared-egg-routes', 'pr16-shared-egg-acceptance', 'pr16-shared-evidence/')
EXPECTED_RECEIVERS = (605, 549)
EXPECTED_TARGETS = {605: (23, 603), 549: (34, 663)}


def fetch(root=ROOT):
    def api(path):
        return subprocess.check_output(['gh', 'api', 'repos/' + prior.REPO + '/' + path])
    def install(path, raw):
        target = root / path
        need(not any(p.is_symlink() for p in (target, *target.parents)), 'unsafe original destination')
        if target.exists():
            need(target.read_bytes() == raw, 'refuse original overwrite')
        else:
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
    run, aid, size, sha, head, _, _, _ = RECORD
    r = prior.load(api(f'actions/runs/{run}'))
    jobs = prior.load(api(f'actions/runs/{run}/jobs?per_page=100'))
    a = prior.load(api(f'actions/artifacts/{aid}'))
    prior.fields(a['workflow_run'], dict(id=run, head_sha=head))
    need(jobs['total_count'] == len(jobs['jobs']) and a['digest'] == 'sha256:' + sha, 'incomplete or changed Actions origin')
    meta = {k: r[k] for k in ('head_sha', 'head_branch', 'run_attempt', 'path', 'status', 'conclusion')}
    meta.update(run_id=r['id'], artifact_id=a['id'], artifact_name=a['name'], size=a['size_in_bytes'], sha256=sha,
                jobs=[{k: j[k] for k in ('id', 'name', 'run_id', 'head_sha', 'status', 'conclusion', 'steps')} for j in jobs['jobs']])
    prior.metadata(meta, RECORD)
    raw = api(f'actions/artifacts/{aid}/zip')
    need(prior.same(prior.identity(raw), dict(size=size, sha256=sha)), 'download identity differs')
    prior.archive(raw)
    directory = Path(DIRECTORY) / str(run)
    install(directory / 'original.zip', raw)
    install(directory / 'actions.json', prior.stable(meta))


def verify_files(files, root=ROOT):
    prefix = 'pr16-shared-egg-routes/'
    native_prefix = prefix + 'native/'
    need(files[RECORD[7] + 'tested-head.txt'] == (RECORD[4] + '\n').encode(), 'tested HEAD differs')
    report = prior.load(files[prefix + 'result.json'])
    prior.fields(report, dict(status='PASS', scope=shared.SCOPE, candidate=prior.CANDIDATE,
        actual_new_processes=16, successful_fresh_cores=32, accepted_receivers=list(EXPECTED_RECEIVERS),
        shared_only_selected_receiver_routes_accepted=True, old_runs_relabelled=0,
        full_p03_acceptance=False, full_p07_acceptance=False, release_ready=False, rom_changed=False,
        active_baseline_changed=False, parent_adapter_scope='P07_INTEGRATED_NATIVE_MEMORY_SAVE'))
    for key, name in (('oracle', 'oracle.json'), ('native_report', 'native/result.json')):
        need(prior.same(report[key], prior.identity(files[prefix + name])), 'shared linked original differs')
    audit = prior.load(files[prefix + 'oracle.json'])
    prior.fields(audit, dict(candidate=prior.CANDIDATE, audited_shared_receivers=943, audited_shared_rows=5023,
                            eligible_evolved_append_receivers=342, full_shared_consumer_native_acceptance=False))
    need(prior.same(audit['adopted_index'], prior.identity(prior.read(root, shared.INDEX))), 'adopted index differs')
    receivers = audit['selected_receivers']
    need([r['species'] for r in receivers] == list(EXPECTED_RECEIVERS), 'receiver identity/order differs')
    for receiver in receivers:
        need(receiver['form_key'] == '' and receiver['pre_evolution_carry'] > 0, 'not an adopted normal-form evolved receiver')
        selected = receiver['shared_only']
        need(selected == [m for m in receiver['shared'] if m not in receiver['legacy'] and m not in shared.KNOWN], 'not genuinely shared-only')
        need((selected[0], selected[-1]) == EXPECTED_TARGETS[receiver['species']], 'shared target identity differs')
        need(receiver['merged'] == shared.unique(receiver['legacy'] + receiver['shared']), 'shared union order differs')
    nat = shared.repaired.native_module(); api = nat.validator()
    input_audit = deepcopy(audit)
    input_audit['canonical_pp'] = {int(k): v for k, v in audit['canonical_pp'].items()}
    cases = shared.build_cases(input_audit, nat.make_case)
    need(prior.same(cases, prior.load(files[prefix + 'cases.json'])), 'cases were not independently reconstructed')
    vectors = prior.load(files[native_prefix + 'vectors.json'])
    need(prior.same(vectors, dict(cases=cases, oracle=audit)), 'executed vectors/oracle differ')
    native = prior.load(files[native_prefix + 'result.json'])
    prior.fields(native, dict(status='PASS', candidate=prior.CANDIDATE, failures=[], new_processes=16,
        successful_processes=16, successful_fresh_cores=32, old_runs_relabelled=0,
        full_p07_acceptance=False, release_ready=False, active_baseline_changed=False,
        scope='P07_INTEGRATED_NATIVE_MEMORY_SAVE', host_write_guard_checks=prior.GUARDS))
    need(prior.same(native['vectors'], prior.identity(files[native_prefix + 'vectors.json'])), 'native vector hash differs')
    need(len(native['cases']) == len(cases), 'raw native process count differs')
    rows = []
    for case, row in zip(cases, native['cases'], strict=True):
        p = native_prefix + case['name']
        process = prior.load(files[p + '.process.json'])
        value = api.validate_result(files[p + '.stdout'], case, process, files[p + '.stderr'])
        need(prior.same(row['result'], value) and prior.same(row['process'], process) and row['name'] == case['name'], 'raw native result/report differs')
        need(case['expected'] not in next(r['legacy'] for r in receivers if r['species'] == case['species']), 'legacy-only case relabelled')
        rows.append(dict(case=case['name'], species=case['species'], action=case['action'], slot=case['slot'],
                         target=case['expected'], fresh_cores=2, saved_mon_bytes=100))
    prior.guards(files, native_prefix)
    sources = prior.load(files[prefix + 'source-bindings.json'])
    need(prior.same(sources, report['sources']), 'shared source binding mirrors differ')
    for name, binding in {**native['source_bindings'], **sources}.items():
        need(prior.same(binding, prior.identity(prior.read(root, name))), 'tested source changed: ' + name)
    snapshot = prior.archive(files[RECORD[7] + 'sources.zip'])
    bindings = prior.load(files[RECORD[7] + 'source-bindings.json'])
    need(set(snapshot) == set(bindings), 'archived source membership differs')
    for name, binding in bindings.items():
        need(prior.same(prior.identity(snapshot[name]), binding), 'archived source hash differs')
    for name in (shared.SELF, shared.TEST, shared.WORKFLOW):
        need(snapshot[name] == prior.read(root, name), 'executed shared source changed')
    log = files[RECORD[7] + 'unit.log']
    need(b'Ran 12 tests' in log and log.endswith(b'OK\n'), 'shared unit completion differs')
    return dict(status='PASS', scope=shared.SCOPE, new_native_processes=16, fresh_cores=32,
                receivers=receivers, cases=rows, unit_tests=12,
                shared_only_selected_receiver_routes_accepted=True,
                all_shared_egg_routes_accepted=False, natural_acquisition_accepted=False,
                fixture_boundary=report['fixture_boundary'], old_runs_relabelled=0,
                full_p03_acceptance=False, full_p07_acceptance=False, release_ready=False)


def build(root=ROOT):
    run, aid, size, sha, head, _, _, _ = RECORD
    directory = Path(DIRECTORY) / str(run)
    prior.metadata(prior.load(prior.read(root, directory / 'actions.json')), RECORD)
    raw = prior.read(root, directory / 'original.zip')
    need(prior.same(prior.identity(raw), dict(size=size, sha256=sha)), 'retained original identity differs')
    result = verify_files(prior.archive(raw), root)
    return dict(schema_version=1, status='PASS', scope='RETAINED_SHARED_ONLY_PHYSICAL_SUBROUTES', candidate=prior.CANDIDATE,
                original=dict(run_id=run, artifact_id=aid, tested_head=head, path=str(directory / 'original.zip'), size=size, sha256=sha),
                acceptance=result, new_emulator_runs=0, historical_successes_preserved_not_relabelled=True,
                full_p03_acceptance=False, full_p07_acceptance=False, release_ready=False)


def project(previous, root=ROOT):
    receipt = build(root)
    need(prior.same(receipt, prior.load(prior.read(root, RECEIPT))), 'current shared receipt differs')
    out = deepcopy(previous)
    out['shared_egg_checkpoint'] = dict(source_path=RECEIPT, candidate=prior.CANDIDATE,
        accepted_receivers=list(EXPECTED_RECEIVERS), new_native_processes=16, new_native_cores=32,
        shared_only_selected_receiver_routes_accepted=True, full_shared_routes_accepted=False, release_ready=False)
    out['final_integration']['shared_egg_verified_native'] = RECEIPT
    for row in out['remaining_conditions']:
        if row['id'] == 'EVOLUTION_FORM_OTHER_EGG':
            row.update(reason_ja='ロトム実受付10件に加え、バクーダ・ドンファンの共有技追加16件（全4枠・取消・保存再開）を受入済み。残る採用済み経路と既存原本の対応を確定する',
                       shared_egg_success_evidence=RECEIPT,
                       resume=SELF + ' verifies the 16 shared-only receiver routes; retain Rotom/evolution/Pichu/Happiny successes and reconcile only residual consumers')
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--fetch', action='store_true'); p.add_argument('--write', action='store_true')
    args = p.parse_args()
    if args.fetch:
        fetch()
    value = build(); path = ROOT / RECEIPT
    if args.write:
        path.write_bytes(prior.stable(value))
    else:
        need(prior.same(value, prior.load(path.read_bytes())), 'stored shared acceptance differs')
    print(json.dumps(dict(status='PASS', retained_new_native_processes=16, retained_new_native_cores=32,
                          originals_verified=True, new_emulator_runs=0, full_p03_acceptance=False, release_ready=False)))

if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, zipfile.BadZipFile) as error:
        print(str(error), file=sys.stderr); raise SystemExit(1)
