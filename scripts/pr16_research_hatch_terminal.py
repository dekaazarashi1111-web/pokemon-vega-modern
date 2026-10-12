#!/usr/bin/env python3
"""Close the 5+10 research-hatch cohort from saved evidence; no emulation."""
from __future__ import annotations
import datetime
import os
from pathlib import Path
import re
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
import pr16_research_hatch_proof as p
SELF = 'scripts/pr16_research_hatch_terminal.py'
TEST = 'tests/test_pr16_research_hatch_terminal.py'
WF = '.github/workflows/pr16-research-hatch-terminal-20260925.yml'
CODE = {SELF, TEST, WF}
WORK = ROOT/'.local/pr16-research-hatch-terminal'
OUT = WORK/'proof'
SHOTS = WORK/'screens'
CRITICAL = {
    'plan': ('新matrix境界unitだけ、旧32/復元30を再実行しない',
             '復元Actions終端・成果commitを照合し未成功だけを選ぶ'),
    'collect': ('worker別原本を照合し成功分だけ固定引継ぎ・両ログへ記録',
                '引継ぎ整合・task graph・最終index限定guard',
                '集約jobだけ同branch非force commit/push・remote照合'),
}
NATIVE_STEP = '原本個体fixtureから1件だけ実歩行・孵化・Save・fresh Continue'


def cohort(v, names, inherited):
    p.need(len(names) == len(set(names)) == 15 and len(inherited) == len(set(inherited)) == 5, 'cohort domain')
    p.need(set(v['accepted']) == set(names) and set(inherited) <= set(names), 'exact 15 accepted')
    p.need(v['status'] == 'PASS_RESEARCH_HATCH_SCOPED' and not v['failures'] and not v['pending_cases'] and not v['unresolved_worker_attempts'], 'no unfinished case')
    for key in ('actions_completion_confirmed', 'issue19_complete', 'release_ready', 'active_baseline_changed'):
        p.need(v[key] is False, 'scope not promoted '+key)
    for key in ('accepted_case_reruns', 'gift_reruns', 'arm_compiles', 'rom_changes', 'wiki_generations'):
        p.need(type(v[key]) is int and v[key] == 0, 'no rerun '+key)
    p.need(v['native_processes'] == v['host_compiles'] == 10 and v['new_unit_tests'] == 23, 'matrix counters')
    pending = set(names)-set(inherited)
    p.need(set(v['matrix']['worker_artifacts']) == pending, 'ten worker origins')
    for name, row in v['accepted'].items():
        p.need(row['result']['status'] == 'PASS' and row['contract'] == v['contracts'][name], 'accepted contract '+name)
        if name in pending:
            p.need(row['source_head'] == v['source_head'] and row['run_id'] == v['run_id'], 'matrix origin '+name)
    return sorted(pending)


def terminal_jobs(payload, expected, head, run_id):
    jobs = payload['jobs']
    p.need(payload['total_count'] == len(jobs) == len(expected) == 12, 'complete 12-job terminal page')
    p.need(len({j['name'] for j in jobs}) == 12 and {j['name'] for j in jobs} == set(expected), 'exact unique job names')
    result = []
    for job in jobs:
        name = job['name']
        p.need(job['run_id'] == run_id and job['head_sha'] == head and job['status'] == 'completed' and job['conclusion'] == 'success', 'terminal job '+name)
        steps = job['steps']
        p.need(steps and len({s['number'] for s in steps}) == len(steps), 'unique steps '+name)
        p.need(all(s['status'] == 'completed' and s['conclusion'] in ('success', 'skipped') for s in steps), 'all terminal steps '+name)
        critical = CRITICAL.get(name, (NATIVE_STEP,))
        for label in critical:
            matches = [s for s in steps if s['name'] == label]
            p.need(len(matches) == 1 and matches[0]['conclusion'] == 'success', 'critical step executed '+name+'/'+label)
        result.append({k: job[k] for k in ('id', 'name', 'run_id', 'head_sha', 'status', 'conclusion')})
    return result


def checked_file(relative, binding=None):
    rel = Path(relative)
    p.need(not rel.is_absolute() and '..' not in rel.parts, 'repository-relative evidence')
    path = ROOT/rel
    p.need(path.is_file() and not path.is_symlink(), 'regular evidence '+relative)
    raw = path.read_bytes()
    if binding is not None:
        p.need(p.identity(raw) == binding, 'unchanged file '+relative)
    return raw


def execute():
    import pr16_research_hatch as r
    import pr16_research_hatch_matrix as m
    import pr16_research_hatch_recover as recovery
    import pr16_natural_supply as s
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    from common import redact_user_paths
    head = current()
    v = r.load(ROOT/r.CP)
    names = cohort(v, r.NAMES, recovery.CASES)
    p.need(v['candidate'] == m.CANDIDATE, 'unchanged candidate')
    err = (OUT/'terminal-unit.stderr.txt').read_bytes()
    count = re.search(rb'Ran (\d+) tests? in ', err)
    p.need(count and b'\nOK\n' in err, 'new terminal boundary unit PASS')
    new_units = int(count[1])
    rid, source = v['run_id'], v['source_head']
    run = fetch('actions/runs/'+str(rid))
    p.need(run['head_sha'] == source and run['status'] == 'completed' and run['conclusion'] == 'success' and run['path'] == m.WF and run['run_attempt'] == 1, 'completed matrix run')
    expected_jobs = ['plan', 'collect']+['hatch / '+name for name in names]
    p.need(set(expected_jobs) == set(v['matrix']['expected_jobs']), 'saved job inventory')
    jobs = terminal_jobs(fetch('actions/runs/'+str(rid)+'/jobs?per_page=100'), expected_jobs, source, rid)
    for path, binding in {**v['source_bindings'], **v['protected_bindings'], **v['compiled_sources']}.items():
        checked_file(path, binding)
    for name, binding in v['public_evidence_bindings'].items():
        checked_file(v['evidence_path']+'/'+name, binding)
    matrix = v['matrix']
    aggregate_raw = checked_file(matrix['receipt_path'], matrix['receipt_binding'])
    aggregate = m.decode(aggregate_raw)
    p.need(aggregate['worker_artifacts'] == matrix['worker_artifacts'] and aggregate['plan'] == matrix['plan'] and aggregate['successful_workers'] == 10 and not aggregate['failures'], 'saved aggregate')
    listing = m.artifacts(rid)
    expected_artifacts = {m.UNIT_NAME, m.PROOF_NAME}|{'pr16-rh-'+name+'-'+kind for name in names for kind in ('proof', 'screens')}
    p.need(len(listing) == 22 and {a['name'] for a in listing} == expected_artifacts, 'complete 22-artifact inventory')
    summary_expected = {'aggregate.json': p.identity(aggregate_raw),
                        'verification.json': p.identity(checked_file(v['evidence_path']+'/verification.json')),
                        'reflected-head.txt': None}
    summary, summary_meta = m.artifact(listing, m.PROOF_NAME, summary_expected, rid, source)
    reflected = summary['reflected-head.txt']
    p.need(re.fullmatch(b'[0-9a-f]{40}\n', reflected), 'matrix reflected SHA')
    reflected_sha = p.reflected(reflected, source, fetch('git/commits/'+reflected.decode().strip()))
    subprocess.run(['git', 'merge-base', '--is-ancestor', reflected_sha, head], check=True)
    base_raw = subprocess.run(['git', 'show', source+':'+r.CP], check=True, stdout=subprocess.PIPE).stdout
    p.need(p.identity(base_raw) == matrix['plan']['input_checkpoint'], 'exact measured input checkpoint')
    base = m.decode(base_raw)
    p.need(set(base['accepted']) == set(recovery.CASES) and all(v['accepted'][n] == base['accepted'][n] for n in recovery.CASES), 'five inherited cases unchanged')
    recovery_receipt = m.recovery_terminal(base, head)
    p.need(recovery_receipt == matrix['plan']['recovery_terminal'], 'recovery provenance unchanged')
    unit, unit_meta = m.artifact(listing, m.UNIT_NAME, dict.fromkeys(('plan.json', 'matrix-unit.stdout.txt', 'matrix-unit.stderr.txt')), rid, source)
    p.need(unit_meta == matrix['unit_artifact'] and m.decode(unit['plan.json']) == matrix['plan'], 'matrix unit/plan artifact')
    for name, binding in matrix['plan']['unit_bindings'].items():
        p.need(p.identity(unit[name]) == binding, 'saved matrix unit byte identity')
    def public_equal(folder, files):
        for name, raw in files.items():
            text = raw.decode('utf-8')
            safe = '\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
            p.need(safe.encode() == checked_file(folder+'/'+name), 'artifact/public evidence '+name)
    public_equal(v['evidence_path']+'/unit', unit)
    SHOTS.mkdir(parents=True, exist_ok=True)
    frames = {}
    for name in names:
        saved = matrix['worker_artifacts'][name]
        files, meta = m.artifact(listing, 'pr16-rh-'+name+'-proof', saved['raw_bindings'], rid, source)
        p.need(meta == saved['proof'], 'pinned worker artifact '+name)
        worker = m.decode(files['verification.json'])
        p.need(m.merge_one(base, worker, name, source, rid, matrix['plan']['input_checkpoint']) == v['accepted'][name], 'original worker acceptance '+name)
        public_equal(v['evidence_path']+'/'+name, files)
        images, image_meta = m.artifact(listing, 'pr16-rh-'+name+'-screens', {f: row['identity'] for f, row in saved['frames'].items()}, rid, source)
        p.need(image_meta == saved['screens'], 'pinned worker screens '+name)
        for filename, raw in images.items():
            observed = p.frame(raw)
            p.need(observed == saved['frames'][filename] and observed['nonblank'], 'unchanged rendered frame')
            frames[filename] = dict(observed, run_id=rid)
            (SHOTS/filename).write_bytes(raw)
    old_run = fetch('actions/runs/'+str(recovery.RUN))
    p.need(old_run['head_sha'] == recovery.SOURCE and old_run['status'] == 'completed' and old_run['conclusion'] == 'cancelled' and old_run['path'] == m.WF, 'original cancelled run retained')
    old_listing = m.artifacts(recovery.RUN)
    p.need(len(old_listing) == 2, 'original artifact inventory')
    old_names = recovery.BASE_NAMES|{n+suffix for n in recovery.CASES for suffix in ('.process.json', '.stdout.txt', '.stderr.txt')}
    old_files, old_meta = m.artifact(old_listing, recovery.PROOF['name'], dict.fromkeys(old_names), recovery.RUN, recovery.SOURCE)
    p.need(old_meta == recovery.PROOF and p.identity(old_files['verification.json']) == base['recovery']['raw_verification_binding'], 'original interrupted proof identity')
    original = m.decode(old_files['verification.json'])
    p.need(original['status'] == 'RUNNING' and 'proof_bindings' not in original and 'screenshots' not in original and original['accepted'] == base['accepted'], 'interrupted raw not rewritten')
    public_equal(r.EVIDENCE+'/'+str(recovery.RUN), old_files)
    recovered = m.decode(checked_file(base['recovery']['path'], base['recovery']['binding']))
    old_images, old_image_meta = m.artifact(old_listing, recovery.SCREENS['name'], {n: row['identity'] for n, row in recovered['frames'].items()}, recovery.RUN, recovery.SOURCE)
    p.need(old_image_meta == recovery.SCREENS and len(old_images) == 10, 'original 10 frames')
    for name, raw in old_images.items():
        observed = p.frame(raw)
        p.need(observed == recovered['frames'][name] and observed['nonblank'] and name not in frames, 'original frame identity')
        frames[name] = dict(observed, run_id=recovery.RUN)
        (SHOTS/name).write_bytes(raw)
    p.need(len(frames) == 30, '15 paired lifecycle frames')
    terminal_actions = [{k: old_run[k] for k in ('id', 'head_sha', 'path', 'status', 'conclusion')},
                        dict(id=recovery_receipt['run_id'], head_sha=recovery_receipt['source_head'],
                             path=recovery.WF, status='completed', conclusion='success'),
                        {k: run[k] for k in ('id', 'head_sha', 'path', 'status', 'conclusion')}]
    receipt = dict(schema_version=1, task=r.TASK, status='PASS_RESEARCH_HATCH_15_TERMINAL',
                   source_head=head, run_id=int(os.environ['GITHUB_RUN_ID']), candidate=v['candidate'],
                   accepted_cases=list(r.NAMES), inherited_native_cases=5, matrix_native_cases=10,
                   matrix_artifacts=matrix['worker_artifacts'], matrix_proof=summary_meta,
                   matrix_reflected_head=reflected_sha, matrix_jobs=jobs, terminal_actions=terminal_actions,
                   recovery=recovery_receipt, original_proof=old_meta, original_screens=old_image_meta, frames=frames,
                   new_unit_tests=new_units, old_unit_tests=0, new_native_processes=0, host_compiles=0,
                   arm_compiles=0, rom_changes=0, accepted_case_reruns=0, gift_reruns=0,
                   original_cancelled_run_promoted=False, original_post_loop_input_mtime_check_completed=False,
                   original_unrecorded_inflight_attempt_not_ruled_out=True,
                   continuous_gift_save_claimed=False, pokemon_identity_visual_acceptance=False,
                   issue19_complete=False, release_ready=False, active_baseline_changed=False,
                   unit_bindings={n: p.identity((OUT/n).read_bytes()) for n in ('terminal-unit.stdout.txt', 'terminal-unit.stderr.txt')})
    dest = ROOT/r.EVIDENCE/os.environ['GITHUB_RUN_ID']
    p.need(not dest.exists(), 'no terminal evidence overwrite');dest.mkdir(parents=True)
    r.write(dest/'terminal.json', receipt);r.write(OUT/'terminal.json', receipt)
    for name in ('terminal-unit.stdout.txt', 'terminal-unit.stderr.txt'):
        (dest/name).write_bytes((OUT/name).read_bytes())
    v.update(actions_completion_confirmed=True, terminal_actions=terminal_actions,
             completed_by_source=head, completed_by_run=int(os.environ['GITHUB_RUN_ID']))
    v['terminal_evidence'] = dict(path=(dest/'terminal.json').relative_to(ROOT).as_posix(),
                                  binding=p.identity((dest/'terminal.json').read_bytes()), accepted_cases=15,
                                  new_native_processes=0, new_unit_tests=new_units, old_unit_tests=0)
    r.write(ROOT/r.CP, v)
    log_paths = ('design/run_log.md', 'design/version_log.md')
    prefixes = {path: (ROOT/path).read_bytes() for path in log_paths}
    r.CODE |= m.CODE|CODE
    r.publish(v, completion=True)
    for path, prefix in prefixes.items():
        after = (ROOT/path).read_bytes();p.need(after.startswith(prefix), 'append-only log')
        tail = after[len(prefix):].decode().replace('専用時native/unit/compile0', f'専用時native/旧unit/compile0・新terminal unit{new_units}')
        tail = tail.replace('新unit23、host10、native10', '原実測matrix runのunit23、host10、native10')
        tail = tail.replace('新driver/C/unit/限定Actions', '既設C不変・新terminal driver/unit/限定Actions')
        (ROOT/path).write_bytes(prefix+tail.encode())
    guide = (ROOT/r.GUIDE).read_text().replace('今回新unit23、host compile10、native10', '原実測matrix runの新unit23、host compile10、native10')
    guide += '\n## 15件の終端確定\n\n保存原本の5件と独立worker10件を限定受入。元run36138860612のcancelled/RUNNING/push skippedは改称していない。元runの終了時seed mtime検査完了や未保存の進行中caseの不存在は主張しない。成功した復元runとmatrix全12job・22artifact・全member・成果commitの直接親/祖先を照合した。終端専用runは新境界unitのみで、native/旧32・30・23unit/host/ARM/ROM変更/受入済み再実行0。\n\n30画面は保存原本hashと非黒画面を確認。form/技UIの視覚受入、元saveから連続した配布→孵化、ストーリー到達は主張しない。元配布17件と研究孵化15件は変更影響がない限り再実行しない。\n'
    reads = {
        'overlays/stage59_wild_identity_npc_regression_repair/stage59_wild_identity_npc_regression_repair.c': [35, 86],
        'overlays/research_economy_v1/research_economy_v1.c': [1640, 1678],
        'overlays/move_distribution_v4/move_distribution_v4.c': [128, 160],
        'overlays/qol_production/qol_production.c': [2667, 2808],
        'config/research_economy_v1.json': [70, 104],
    }
    guide += '\n## 次の特殊野生調査を重複しないための引継ぎ\n\nソース調査のみ・native受入0・ROM変更0。Stage59のidentity正規化はreset_wild_moves=0。一方、研究経済adapterはFN_MOVE_FISHING/FN_MOVE_HIDDENへ委譲し、V4 adapterはQOL生成後にApplyWildInitialMovesを呼ぶ。QOL apply_research_profileはCreateMon後にタマゴ技を第4枠へ置く。外側のStage59だけ、または旧V4だけを根拠に不具合/保持を確定しない。次は候補ROMの実hook/delegateと生成→特殊技設定→再初期化順を限定観測する。正確な読取範囲とsource hashは固定状態JSONのlearnset_special_wild_next_probe/read_ranges・source_bindingsに保存。\n\n1281 identity-only/自動fallback禁止、Issue19全体未完、release_ready=false、PR未merge、active baseline不変。\n'
    (ROOT/r.GUIDE).write_text(guide)
    state = r.load(ROOT/s.m.STATE)
    state['learnset_research_hatch'].update(terminal_evidence=v['terminal_evidence'], recovery=v['recovery'],
                                          matrix=dict(receipt_path=matrix['receipt_path'], receipt_binding=matrix['receipt_binding']))
    state['learnset_special_wild_next_probe'] = dict(status='UNACCEPTED_SOURCE_TRACE_ONLY', source_head=head,
        candidate=v['candidate'], native_cases=0, rom_changes=0, read_ranges=reads,
        caution_ja='候補内の実接続先と特殊技後の再初期化順を限定観測。Stage59 reset=0/旧V4だけで保持/不具合を決めず、既受入15孵化/17配布/旧野生を再実行しない。')
    for path in CODE|{r.CP, r.GUIDE}|set(reads):
        state['source_bindings'][path] = p.identity((ROOT/path).read_bytes())
    state['next_action']['read_paths'] = [r.GUIDE, r.CP, SELF, v['terminal_evidence']['path']]
    publish_resume(state)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    note = f'\n## {now}\n- Timestamp: {now}\n- Task: {r.TASK}\n- Version: research-hatch-terminal-5-plus-10-v1\n- Status: DONE（15孵化限定、Issue19/release未完）\n- Summary: 5件の中断原本復元+10独立workerを終端確定。32初期unit/30復元unit/23matrix unitは各変更範囲で一度だけ、終端は新unit{new_units}のみ。\n- Files changed: terminal driver/unit/Actions、terminal原本、checkpoint/guide、固定引継ぎMD/JSON、両ログ。\n- Verify: 12job/22matrix artifact/成果commit直接親・祖先/15raw origin/30画面hashを照合。終端新native/旧unit/host/ARM/ROM変更0。原runのcancelledは保存。resume/task graph/final-index scoped guardをcommit前実行。\n- Commit: 同branch非force push・remote照合。source={head}。成果SHAはterminal-proof/reflected-head.txt。\n- Network: 固定GitHub原本のみ。ROM/saveは非追跡。特殊野生はソース調査のみで実接続先未受入。merge/release/baseline切替なし。\n'
    for path in log_paths:
        with (ROOT/path).open('a') as f:f.write(note)
    print('PASS: research hatch 15/15 terminal; native/old-unit/compile reruns=0')


if __name__ == '__main__':
    execute()
