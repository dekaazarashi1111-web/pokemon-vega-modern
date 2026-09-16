#!/usr/bin/env python3
"""Revalidate three pinned originals into five cases; no emulator or ROM rebuild.

Raw failed runs and their per-case flags are immutable. The aggregate is a new
claim over selected successful processes on ONE candidate, not a rewritten run.
Only --retain-new/--apply write; default --check is side-effect-free. Git index
and HEAD read-back are required by the checkpoint workflow before/after push.
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import zipfile

import pr16_fixed_form_acceptance as fixed
from pr16_fixed_form_originals import scan

ROOT = Path(__file__).resolve().parents[1]
BASE = 'content/modernization/pr16_fixed_form_acceptance_evidence'
ACCEPTANCE = 'content/modernization/pr16_fixed_form_acceptance.json'
RECEIPT = 'content/modernization/pr16_fixed_form_acceptance_receipt.json'
P08 = 'content/modernization/p08_remaining_work.json'
SELF = 'scripts/pr16_fixed_form_closeout.py'
TEST = 'tests/test_pr16_fixed_form_closeout.py'
WORKFLOW = '.github/workflows/pr16-fixed-form-closeout.yml'
DOC = 'docs/PR16_FIXED_FORM_CLOSEOUT_20260912_JA.md'
GAP = 'P03_FIXED_FORM_TRANSITION_PHYSICAL'
REPOSITORY = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
CANDIDATE = dict(size=33554432, sha256=fixed.SHA)
AUXILIARY = dict(iron_head=405, photon_geyser=733)
# run, job, artifact, exact tested HEAD, original size/SHA256, conclusion, cases
PINS = (
    (34694218218, 103554787890, 10297554037, 'a9ec7ab9d93d8013139698242802826278aaf667', 802643, '45fbc581ec17cf7e0504d2c8d3150072e44a9099e4deed04da759d8b3a6328c7', 'failure', ('necrozma-decline-unchanged',)),
    (34695512247, 103558198010, 10298208423, '952b9fb2e2ee8b5951214eda7a7847c4ca1092d5', 854855, '0d31881c45e05e9aa4b3c122663ce3bfd7605ff4287299a602c48232dc893cc8', 'success', ('zacian-crowned-battle-roundtrip', 'zamazenta-crowned-battle-roundtrip')),
    (34698120000, 103565021381, 10299506555, 'a552361a250ff1a01afb4f328c5bfef8a329775e', 1055169, '3a2b3faa1ef98e2ddfde2ca1ef32bbcdc90e92469e53b6016d9700a286344c64', 'success', ('necrozma-dusk-mane-four-slot-roundtrip', 'necrozma-dawn-wings-four-slot-roundtrip')),
)
need, identity, stable = fixed.need, fixed.identity, fixed.stable


def load(raw: bytes):
    # Metadata can exceed the native stdout's deliberately small 64 KiB cap.
    need(type(raw) is bytes and len(raw) <= 4_000_000, 'unbounded metadata')
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'duplicate metadata key')
            out[key] = value
        return out
    def reject(_):
        raise ValueError('nonfinite metadata number')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=reject)


def process(row: dict, code: int) -> None:
    want = dict(schema_version=1, returncode=code, spawn_error=None, timed_out=False)
    need(type(row) is dict and set(row) == set(want), 'invalid process envelope')
    need(all(type(row[k]) is type(v) and row[k] == v for k, v in want.items()), 'process did not finish as required')


def actions_valid(data: dict, pin: tuple) -> None:
    run_id, job_id, artifact_id, head, size, digest, conclusion, _ = pin
    run, artifact, jobs = data['run'], data['artifact'], data['jobs']['jobs']
    need(run['id'] == run_id and run['head_sha'] == head and run['head_branch'] == BRANCH, 'Actions run/head differs')
    need(run['status'] == 'completed' and run['conclusion'] == conclusion and run['run_attempt'] == 1, 'Actions outcome differs')
    need(len(jobs) == 1 and jobs[0]['id'] == job_id and jobs[0]['run_id'] == run_id, 'Actions job differs')
    need(jobs[0]['status'] == 'completed' and jobs[0]['conclusion'] == conclusion, 'Actions job outcome differs')
    need(artifact['id'] == artifact_id and artifact['size_in_bytes'] == size and artifact['digest'] == 'sha256:' + digest, 'Actions artifact differs')
    need(artifact['workflow_run']['id'] == run_id and artifact['workflow_run']['head_sha'] == head, 'artifact is from another run/head')


def archive_valid(raw: bytes, pin: tuple, root: Path | None = None) -> tuple[list, dict]:
    run, job, artifact, head, size, digest, conclusion, selected = pin
    need(identity(raw) == dict(size=size, sha256=digest), 'original ZIP differs')
    prefix = 'pr16-fixed-form-acceptance/'
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        scan(z)
        receipt = load(z.read(prefix + 'receipt.json'))
        report = load(z.read(prefix + 'result.json'))
        need(receipt['tested_head'] == head, 'receipt tested HEAD differs')
        need(receipt['candidate'] == report['candidate'] == CANDIDATE, 'candidate differs')
        need(report['auxiliary_moves'] == AUXILIARY, 'move oracle differs')
        for key in ('native_acceptance_claimed', 'p03_fixed_form_gap_closed', 'release_ready'):
            need(receipt[key] is False and report[key] is False, 'raw partial run was promoted')
        need({n[len(prefix):] for n in z.namelist() if n.startswith(prefix)} == set(receipt['members']) | {'receipt.json'}, 'receipt member set differs')
        for name, binding in receipt['members'].items():
            need(identity(z.read(prefix + name)) == binding, 'receipt member digest differs: ' + name)
        process(load(z.read(prefix + 'compile.process.json')), 0)
        need(report['guard_checks'] == list(fixed.GUARDS), 'write barrier coverage differs')
        for guard in fixed.GUARDS:
            process(load(z.read(prefix + 'guard-' + guard + '.process.json')), 1)
            need(z.read(prefix + 'guard-' + guard + '.stdout') == b'', 'guard emitted acceptance output')
            need(z.read(prefix + 'guard-' + guard + '.stderr') == b'P03 archive: host write after observation barrier\n', 'guard did not reject a post-observation write')
        source_bindings = report['sources']
        with zipfile.ZipFile(io.BytesIO(z.read(prefix + 'sources.zip'))) as sources:
            need(set(sources.namelist()) == set(source_bindings), 'source inventory differs')
            for name, binding in source_bindings.items():
                need(identity(sources.read(name)) == binding, 'source digest differs: ' + name)
                if root is not None:
                    tracked = subprocess.check_output(['git', 'show', head + ':' + name], cwd=root)
                    need(identity(tracked) == binding, 'source is not bound to exact Git HEAD: ' + name)
        need([row['name'] for row in report['results']] == list(selected), 'selected successful case set differs')
        if conclusion == 'success':
            need(report['failures'] == [] and report['actual_new_processes'] == len(selected), 'successful run contains failures or different process count')
        else:
            # Only the originally successful FORM cancellation is inherited.
            need(run == 34694218218 and report['status'] == 'FAIL' and len(report['failures']) == 4 and report['actual_new_processes'] == 5, 'historical failed run was relabelled')
        rows = []
        for row in report['results']:
            name = row['name']
            envelope = load(z.read(prefix + name + '.process.json'))
            process(envelope, 0)
            need(envelope == row['process'], 'process file/report differs')
            actual = fixed.validate(z.read(prefix + name + '.stdout'), z.read(prefix + name + '.stderr'), name, envelope['returncode'], AUXILIARY)
            need(actual == row['result'], 'stdout/report differs')
            rows.append(dict(name=name, process=envelope, result=actual, evidence_run_id=run))
        record = dict(run_id=run, job_id=job, artifact_id=artifact, tested_head=head,
                      actions_conclusion=conclusion, original=dict(path=f'{BASE}/{run}/original.zip', size=size, sha256=digest),
                      original_result=identity(z.read(prefix + 'result.json')),
                      original_receipt=identity(z.read(prefix + 'receipt.json')),
                      source_zip=identity(z.read(prefix + 'sources.zip')),
                      actual_processes_in_original_run=report['actual_new_processes'],
                      failures_in_original_run=len(report['failures']), selected_successful_cases=list(selected))
        return rows, record


def aggregate(root: Path, surface: str | None) -> tuple[dict, dict]:
    rows, records = [], []
    for pin in PINS:
        base = root / BASE / str(pin[0])
        file = base / 'original.zip'
        need(not any(p.is_symlink() for p in (file, *file.parents)), 'symlink evidence path')
        raw = file.read_bytes()
        if surface:
            ref = ':' if surface == 'index' else 'HEAD:'
            need(subprocess.check_output(['git', 'show', ref + str(file.relative_to(root))], cwd=root) == raw, 'original not retained in Git ' + surface)
        actions = (base / 'actions.json').read_bytes()
        actions_valid(load(actions), pin)
        accepted, record = archive_valid(raw, pin, root)
        record['actions'] = dict(path=str((base / 'actions.json').relative_to(root)), **identity(actions))
        rows.extend(accepted)
        records.append(record)
    need(len(rows) == 5 and len({r['name'] for r in rows}) == 5, 'missing or duplicate acceptance case')
    rows.sort(key=lambda r: list(fixed.CASES).index(r['name']))
    # This is five inherited successful processes, NOT five new executions and
    # NOT a claim that the old run's four failures disappeared.
    envelopes = [{k: r[k] for k in ('name', 'process', 'result')} for r in rows]
    need(fixed.complete(envelopes, [], list(fixed.GUARDS), len(envelopes), AUXILIARY), 'five-case aggregate rejected')
    report = dict(schema_version=2, status='PASS_FIVE_CASE_NATIVE_ACCEPTANCE_PENDING_P08_TRANSFER',
                  accepted_case_count=5, accepted_cases=rows, remaining_case_ids=[],
                  candidate=CANDIDATE, candidate_crc32='BFB089F9',
                  native_acceptance_claimed=True, p03_fixed_form_gap_closed=True,
                  full_p03_acceptance=False, release_ready=False, active_baseline_changed=False,
                  new_emulator_runs_during_aggregation=0, actual_new_processes_this_run=0,
                  successful_original_processes=5, successful_original_fresh_cores=11,
                  evidence_run_ids=[p[0] for p in PINS],
                  current_successful_run_id=PINS[-1][0], current_successful_tested_head=PINS[-1][3],
                  total_attempted_processes_in_selected_originals=sum(r['actual_processes_in_original_run'] for r in records),
                  historical_failures_retained=True, all_attempt_history_is_exhaustive=False,
                  cancellation_scope='Native FORM service 245/246 cancellation; not a claim about N-item cancellation or ineligible fusion',
                  fusion_entry='Native N-Solarizer697/N-Lunarizer698, partner and four-slot selection; not FORM service selection',
                  fixture_boundary='Starting progress/map/party/items are fixtures; only input after the host-write barrier',
                  normal_supply_accepted=False,
                  next_action='P05 native ring/BP/policy supply, Circus admission, then exact-final-candidate P08 transfer; do not repeat these five successful cases without a changed relevant input')
    bindings = {p: identity((root / p).read_bytes()) for p in (SELF, TEST, WORKFLOW, fixed.SELF, fixed.SOURCE, fixed.CONTROLLER, fixed.CONTRACT, 'scripts/pr16_fixed_form_originals.py')}
    receipt = dict(schema_version=3, status=report['status'], candidate=CANDIDATE,
                   acceptance=dict(path=ACCEPTANCE, **identity(stable(report))),
                   originals=records, source_bindings=bindings,
                   native_acceptance_claimed=True, p03_fixed_form_gap_closed=True,
                   full_p03_acceptance=False, release_ready=False,
                   new_emulator_runs_during_aggregation=0,
                   retained_originals_must_match_git_index_and_head=True)
    return report, receipt


def update_p08(data: dict) -> dict:
    rows = [r for r in data['remaining_conditions'] if r['id'] == 'EVOLUTION_FORM_OTHER_EGG']
    need(len(rows) == 1, 'P03 P08 condition is ambiguous')
    row = rows[0]
    need(row['remaining_physical_gap_ids'] in ([GAP], []), 'P03 scope changed')
    need('P03_GENERIC_FORM_CHANGE_CARRY_PHYSICAL' in row['accepted_physical_gap_ids'], 'generic FORM acceptance disappeared')
    row.update(status='PASS_SCOPED_CANDIDATE_PENDING_P08_TRANSFER',
               coverage_inventory_complete=True, physical_acceptance_complete=True, complete=True,
               remaining_physical_gap_ids=[], accepted_candidate_sha256=fixed.SHA,
               fixed_form_success_evidence=ACCEPTANCE,
               successor_transfer_condition_id='FINAL_NATIVE_ACCEPTANCE',
               reason_ja='generic FORM/Rotom成功を保持。fixed-formは同一e630f7f候補の独立5成功プロセスを原本照合して受入。残るのはP08最終候補への変更影響移送であり、P03固有physical gapは0。',
               resume='Keep all five original cases and their distinct native entry owners. Re-run only if P08 change-impact review requires it; do not invent Photon Geyser auto-restoration.')
    row['accepted_physical_gap_ids'] = sorted(set(row['accepted_physical_gap_ids']) | {GAP})
    data['fixed_form_checkpoint'] = dict(acceptance=ACCEPTANCE, receipt=RECEIPT, candidate=CANDIDATE,
                                        accepted_cases=5, new_emulator_runs=0, physical_gap_closed=True,
                                        final_candidate_transfer_complete=False)
    need(data['full_p03_acceptance'] is False and data['release_ready'] is False and data['active_baseline_changed'] is False, 'release/baseline scope changed')
    return data


def retain_new(root: Path) -> None:
    need(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY, 'unexpected retention repository')
    pin = PINS[-1]
    base = root / BASE / str(pin[0])
    original, meta = base / 'original.zip', base / 'actions.json'
    if original.exists() and meta.exists():
        archive_valid(original.read_bytes(), pin, root)
        actions_valid(load(meta.read_bytes()), pin)
        return
    need(not original.exists() and not meta.exists(), 'partial retention requires reconciliation, not overwrite')
    def api(suffix):
        return subprocess.check_output(['gh', 'api', 'repos/' + REPOSITORY + '/' + suffix], timeout=120)
    run = load(api(f'actions/runs/{pin[0]}'))
    jobs = load(api(f'actions/runs/{pin[0]}/jobs'))
    artifact = load(api(f'actions/artifacts/{pin[2]}'))
    metadata = dict(run=run, jobs=jobs, artifact=artifact)
    actions_valid(metadata, pin)
    need(artifact['expired'] is False, 'unretained original has expired')
    raw = api(f'actions/artifacts/{pin[2]}/zip')
    archive_valid(raw, pin, root)
    base.mkdir(parents=True, exist_ok=True)
    with original.open('xb') as out:
        out.write(raw)
    with meta.open('xb') as out:
        out.write(stable(dict(metadata, download=identity(raw))))


def apply(root: Path) -> None:
    report, receipt = aggregate(root, None)
    for name in (ACCEPTANCE, RECEIPT):
        backup = root / BASE / str(PINS[-1][0]) / ('previous_' + Path(name).name)
        if not backup.exists():
            with backup.open('xb') as out:
                out.write((root / name).read_bytes())
    (root / ACCEPTANCE).write_bytes(stable(report))
    (root / RECEIPT).write_bytes(stable(receipt))
    (root / P08).write_bytes(stable(update_p08(load((root / P08).read_bytes()))))
    note = ('\n\n## USER-MODERNIZATION: fixed-form five-case closeout / 2026-09-12\n\n'
            '既存HEAD a552361aのnative run34698120000がNecrozma2ケースで成功していたため再実行せず回収。'
            'Nアイテム→相方→実4枠選択→専用技→Save/新コアContinue→解除/技枠圧縮→相方100bytes一致→実Pokemonメニュー→2回目Save/新コアContinueを原本照合。'
            'FORM取消run34694218218とCrowned2ケースrun34695512247を合わせ5成功process/11cores。'
            '原本失敗4件は削除・成功への再分類をしない。新規emulator実行0。'
            'ZIP/receipt/source/Actions/process/write-barrierを照合し、Git index/HEADの原本byte一致を別検査。'
            'P03固定フォームphysical gapだけ閉鎖。P05供給3件/Circus/P08最終SHA移送/clean-ROM配布は未完。'
            'full_p03_acceptance/release_ready/active_baseline_changed=false。詳細: ' + DOC + '\n')
    for name in ('design/run_log.md', 'design/version_log.md'):
        file = root / name
        old = file.read_text()
        if '## USER-MODERNIZATION: fixed-form five-case closeout / 2026-09-12' not in old:
            with file.open('a') as out:
                out.write(note)


def check(root: Path, surface: str) -> dict:
    report, receipt = aggregate(root, surface)
    need((root / ACCEPTANCE).read_bytes() == stable(report), 'canonical acceptance differs')
    need((root / RECEIPT).read_bytes() == stable(receipt), 'canonical receipt differs')
    p08 = (root / P08).read_bytes()
    need(p08 == stable(update_p08(load(p08))), 'P08 fixed-form state differs')
    return dict(status='PASS_FIVE_CASE_CLOSEOUT', checked_git_surface=surface, accepted_cases=5,
                successful_original_fresh_cores=11, new_emulator_runs=0,
                p03_fixed_form_gap_closed=True, full_p03_acceptance=False, release_ready=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--retain-new', action='store_true')
    modes.add_argument('--apply', action='store_true')
    modes.add_argument('--check', action='store_true')
    parser.add_argument('--surface', choices=('index', 'head'), default='head')
    args = parser.parse_args()
    if args.retain_new:
        retain_new(ROOT)
    elif args.apply:
        apply(ROOT)
    else:
        print(stable(check(ROOT, args.surface)).decode(), end='')
