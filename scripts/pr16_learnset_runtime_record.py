#!/usr/bin/env python3
"""2入口の完了証拠を検証・保存する。原本/host/ARM/nativeを再実行しない。"""
from __future__ import annotations
from collections import Counter
import datetime
import fnmatch
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
START = 'ba4a6367c5179372d06138fef02f0aa29588d0e2'
RUN = 35704908254
TASK = 'USER-20260922-LEARNSET-RUNTIME'
BRANCH = 'codex/modernization-followup-20260908'
BASE = 'content/modernization/'
CHECKPOINT = BASE + 'pr16_learnset_runtime_checkpoint.json'
EVIDENCE = BASE + 'pr16_learnset_runtime_evidence'
STATE = BASE + 'pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
GUIDE = 'docs/PR16_LEARNSET_RUNTIME_JA.md'
CODE = {'scripts/pr16_learnset_runtime_record.py', 'tests/test_pr16_learnset_runtime_record.py',
        '.github/workflows/pr16-learnset-runtime-record.yml'}
PROOF = ('build11.txt', 'build29.txt', 'disassembly.txt', 'entrypoints.jsonl', 'host-audit.json',
         'native-compile.txt', 'link.json', 'native11.json', 'native11.txt', 'native29.json',
         'native29.txt', 'pr16_learnset_samples.h', 'receipt.json', 'reuse.json', 'task-graph.txt',
         'tracked-diff.txt', 'unit.txt', 'verification.json')
ARTIFACTS = {
    'pr16-learnset-runtime-proof': (10683662881, 153816, '17c4f5c18321b06229b878955ddf941c9c80d0a424cabd7c962d3b4727613889'),
    'pr16-learnset-runtime-data': (10683907559, 120487, 'd7f66cae03f6d228e49dd6dbb3caea8760063e9a771ace0d13e009cfef402c9e'),
    'pr16-learnset-runtime-link-checkpoint': (10684072168, 253286, '2f27b292935c1ca65090fe9f8693d32ecac8b7b8b64ad2731a70cca1e4950863'),
}
OWNED = {CHECKPOINT, STATE, DOC, GUIDE, 'design/run_log.md', 'design/version_log.md'}
OWNED |= {EVIDENCE + '/' + name for name in PROOF}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def unpack(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        need(len(archive.infolist()) == len(PROOF) and set(archive.namelist()) == set(PROOF), 'proof集合/重複不一致')
        files = {}
        for info in archive.infolist():
            need(not info.is_dir() and info.external_attr >> 28 != 0xA and info.file_size <= 1000000, 'proof種類/容量違反')
            value = archive.read(info.filename)
            value.decode('utf-8')
            need(b'\0' not in value, 'binary証拠をtrackedへ入れない')
            files[info.filename] = value
        return files


def validate(files):
    need(set(files) == set(PROOF), 'proof集合不一致')
    v = json.loads(files['verification.json'])
    need(v['status'] == 'PASS_TWO_GAME_ENTRYPOINTS_ARM_LINK_AND_DIRECT_ROM_PROBES'
         and v['source_head'] == START and v['run_id'] == RUN, '成功run/HEAD不一致')
    need(v['scope'] == 'TWO_ENTRYPOINT_DIRECT_CALL_NOT_GAMEPLAY_E2E', '直接callを実操作へ昇格しない')
    need(set(v['proof_files']) == set(PROOF) - {'verification.json'}, 'proof内側集合不一致')
    for name, expected in v['proof_files'].items():
        need(identity(files[name]) == expected, 'proof内側hash不一致: ' + name)
    for key in ('accepted_native_reruns', 'accepted_payload_regenerations', 'accepted_source_regenerations',
                'focused_tests_executed', 'host_queries_executed', 'new_arm_compiles', 'new_arm_links', 'old_arm_compiles'):
        need(type(v[key]) is int and v[key] == 0, '再実行計数違反: ' + key)
    for key in ('issue19_complete', 'release_ready', 'active_baseline_changed', 'saved_four_moves_rewritten',
                'conditional_consumers_connected', 'initial_moves_connected', 'natural_level_up_connected',
                'physical_archive_supply_verified', 'global_table_roots_changed'):
        need(v[key] is False, '未検証scopeの昇格: ' + key)
    for key in ('input_byte_mtime_unchanged', 'tracked_tree_unchanged', 'independent_candidate_hashes_match'):
        need(v[key] is True, '不変/独立証拠不一致: ' + key)
    need(v['native_probe_processes'] == 2 and v['native_probe_calls'] == 3382
         and v['focused_tests'] == 19 and v['inherited_arm_links'] == 2
         and v['inherited_arm_compiles'] == 8 and v['inherited_arm_evidence_run'] == 35703851133,
         '実行/継承計数不一致')
    link = json.loads(files['link.json'])
    need(link['candidate'] == v['candidate'] and link['parent'] == v['parent_candidate']
         and link['status'] == 'LINKED_TWO_ENTRYPOINTS_NOT_GAMEPLAY_ACCEPTANCE'
         and len(link['hooks']) == v['rom_hook_count'] == 2
         and link['outside_declared_ranges'] == 0 and link['allocation']['summaries']['overlap_count'] == 0,
         '配置/pointer/候補の証拠不一致')
    host = json.loads(files['host-audit.json'])
    need(host == v['host_audit'] and host['status'] == 'PASS_PLACED_C_AGAINST_ACCEPTED_SPANS'
         and host['owners'] == 1671 and host['learning_owners'] == 1483
         and host['identity_only_preserved'] == 188 and host['archive_moves_granted'] == 0,
         'host継承証拠不一致')
    need(files['unit.txt'].count(b' ... ok\n') == 19 and b'\nOK\n' in files['unit.txt'], '19試験原本不一致')
    for name in ('native11.json', 'native29.json'):
        n = json.loads(files[name])
        need(n['status'] == 'PASS_TWO_LINKED_ROM_ENTRYPOINTS'
             and n['scope'] == 'HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E'
             and n['candidate_sha256'] == v['candidate']['sha256'] and n['calls'] == 1691 and n['samples'] == 13,
             'native原本scope/計数不一致')
        for key in ('existing_mon_bytes_unchanged', 'new_code_pc_seen_for_every_call', 'output_canaries_unchanged'):
            need(n[key] is True, 'native不変条件不一致')
    return v


def record():
    sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_payload_verify import completed_run, current_pr
    from pr16_resume import render, pending_ids
    head = git('rev-parse', 'HEAD').decode().strip()
    current_pr(head)
    need(not (ROOT / CHECKPOINT).exists() and not (ROOT / EVIDENCE).exists(), '重複記録禁止')
    done = completed_run(RUN, START, '.github/workflows/pr16-learnset-runtime.yml', 'runtime-boundary')
    listing = fetch(f'actions/runs/{RUN}/artifacts?per_page=100')
    need(listing['total_count'] == len(listing['artifacts']) == 3, 'artifactページ/件数不一致')
    artifacts = {a['name']: a for a in listing['artifacts']}
    need(set(artifacts) == set(ARTIFACTS), 'artifact集合不一致')
    for name, (number, size, digest) in ARTIFACTS.items():
        a = artifacts[name]
        need((a['id'], a['size_in_bytes'], a['digest']) == (number, size, 'sha256:' + digest)
             and not a['expired'] and a['workflow_run']['id'] == RUN
             and a['workflow_run']['head_sha'] == START, 'artifact binding不一致')
    number, size, digest = ARTIFACTS['pr16-learnset-runtime-proof']
    raw = fetch(f'actions/artifacts/{number}/zip', binary=True)
    need(identity(raw) == {'size': size, 'sha256': digest}, '外側ZIP不一致')
    files = unpack(raw)
    v = validate(files)
    for name, expected in v['code_bindings'].items():
        need(identity((ROOT / name).read_bytes()) == expected, '受入source変更: ' + name)
    failed = []
    for number in (35703376221, 35703851133, 35704666433):
        r = fetch(f'actions/runs/{number}')
        need(r['status'] == 'completed' and r['conclusion'] == 'failure', '過去failureを成功へ改作しない')
        failed.append({k: r[k] for k in ('id', 'head_sha', 'status', 'conclusion')})
    all_runs = fetch(f'actions/runs?head_sha={START}&per_page=100')
    need(all_runs['total_count'] == len(all_runs['workflow_runs']), 'Actions未取得ページ')
    observed = [{k: r[k] for k in ('id', 'name', 'head_sha', 'path', 'event', 'status', 'conclusion')}
                for r in all_runs['workflow_runs']]
    state = json.loads((ROOT / STATE).read_text())
    backlog = json.loads((ROOT / (BASE + 'p08_remaining_work.json')).read_text())
    bp = json.loads((ROOT / (BASE + 'pr16_bp_chooser_checkpoint.json')).read_text())
    need(pending_ids(backlog) == (state['remaining_physical_gap_ids'], state['remaining_p08_gate_ids'])
         and bp['accepted_case_count'] == 3 and not state['release_ready']
         and not state['active_baseline_changed'] and not state['pr_merged'], '正式受入/残件境界不一致')
    checkpoint = {'task': TASK, 'status': 'ACCEPTED_TWO_ENTRYPOINTS_DIRECT_ROM_PROBES_GAMEPLAY_PENDING',
        'source_head': START, 'run_id': RUN, 'completed_actions': done, 'other_actions_observed': observed,
        'preserved_failed_runs': failed, 'artifacts': artifacts, 'verification': v,
        'proof_bindings': {name: identity(value) for name, value in files.items()},
        'candidate': v['candidate'], 'candidate_crc32': json.loads(files['link.json'])['candidate_crc32'],
        'record_source_head': head, 'gameplay_e2e_accepted': False, 'issue19_complete': False,
        'release_ready': False, 'active_baseline_changed': False}
    dest = ROOT / EVIDENCE
    dest.mkdir()
    for name, value in files.items():
        (dest / name).write_bytes(value)
    (ROOT / CHECKPOINT).write_bytes(encode(checkpoint))
    state['learnset_runtime'] = {'path': CHECKPOINT, 'status': checkpoint['status'], 'source_head': START,
        'run_id': RUN, 'candidate': v['candidate'], 'gameplay_e2e_accepted': False, 'issue19_complete': False}
    state.setdefault('observed_head_history', []).append({'head': state['observed_head'],
        'semantics': state['observed_head_semantics'], 'checks': state['observed_head_checks'],
        'reason_ja': '2入口の直接ROM検証を保存。親payload/正式nativeの受入範囲は変更しない。'})
    state['observed_head'] = START
    state['observed_head_semantics'] = '2入口の直接ROM call成功入力HEAD。通常操作E2E/Issue19全完了/記録commitではない。'
    state['observed_head_checks'] = {'scope_head': START, 'runs': [done],
        'reason_ja': 'run35704908254成功。保存ARMから2process/3382直接ROM callを受入。19試験/host/独立2linkは既存証拠を継承し再実行0。通常操作E2E・残consumerは未受入。'}
    state['observed_date_jst'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    goal = 'Issue19: aabd52a0の保存配置と親/Eternal payloadを再利用し、初期4技・自然level-up・進化/思い出し等の条件consumerを明示ownerへ接続。別候補Wikiと影響nativeを生成し、通常操作E2Eを受入する。2入口直接callは再実行しない。'
    state['next_action'] = dict(state['next_action'], id='LEARNSET_REMAINING_GAME_CONSUMERS', goal_ja=goal,
        read_paths=[GUIDE, CHECKPOINT, 'scripts/pr16_learnset_runtime_link.py', 'tools/pr16_learnset_runtime.py',
                    'src/modernization/pr16_learnset_game.c', 'src/modernization/pr16_learnset_runtime.c',
                    'docs/PR16_LEARNSET_PAYLOADS_JA.md'],
        stop_rule_ja='188保全枠を空表/旧表fallbackにしない。条件経路・archive12件の実供給を未検証で付与しない。保存4技/旧Wikiは不変。直接callを通常操作へ昇格せず、merge/release/baseline切替は行わない。')
    state['bp']['next_step'] = goal
    state['bp']['current_stop'] = '2入口GetLevelUpMovesBySpecies/CanMonLearnTMHMを新ROM aabd52a0へ接続。配置/全差分rollbackと13代表owner×2process/3382直接callを受入。188保全枠/保存個体不変。初期4技・自然level-up・条件consumer・通常操作E2E/別Wikiは未完。'
    state['do_not_repeat'].append('run35704908254の2入口直接ROM call3382件/2processを再実行しない。19host試験/全owner queryはrun35703376221、独立ARM8compile/2linkはrun35703851133の成功部分を継承。過去3failureは保持。保存aabd52a0/固定link artifactから再開。')
    state['logs_synchronized'] = True
    (ROOT / STATE).write_bytes(encode(state))
    (ROOT / DOC).write_text(render(state), encoding='utf-8')
    guide = '# Issue19: ゲームconsumer接続\n\n' + state['bp']['current_stop'] + '\n\n## 受入境界\n'
    guide += 'run35704908254 / HEAD `' + START + '`。候補SHA-256 `' + v['candidate']['sha256'] + '`、33554432 bytes、CRC32 47902B58。\n\n'
    guide += '通常操作E2Eではない。host fixtureから2関数を直接呼ぶROM診断であり、自然な習得/保存/Continueを証明しない。既存4技を書き換えず、archive追加供給は0。\n\n'
    guide += '19試験・1671 owner・213888 machine queryの成功原本、独立2ARM配置を継承。回復runでhost/ARMを重複実行しない。過去failureは改作しない。詳細は `'+ CHECKPOINT + '` と `' + EVIDENCE + '/verification.json`。\n\n## 次工程\n' + goal + '\n'
    (ROOT / GUIDE).write_text(guide, encoding='utf-8')
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 2入口ROM接続の完了証拠保存\n- Version: learnset-runtime-two-entrypoints-v1\n- Status: DONE（2入口直接call限定。通常操作/残consumerは未完）\n- Summary: 新ROM aabd52a0、2hook、全差分rollback/配置容量・13代表owner・2process/3382callを保存。19試験/host/ARMは継承し再実行0。\n- Files changed: runtime記録器/拒否試験/限定Actions、証拠/checkpoint、専用guide、固定再開MD/JSON、両ログ。\n- Verify: run35704908254 SUCCESS、ZIP/全member/source hash照合、新記録拒否試験・resume check・task graph・final index guard PASS後のみcommit。通常操作E2Eは未受入。\n- Commit: 本記録を含む同branch非force commit。自己SHAはgit logで照合。\n- Network: GitHub完了run/artifact再利用。新規ROM生成/host/ARM/native再実行0。過去3failureを保持。\n'
    for name in ('design/run_log.md', 'design/version_log.md'):
        with (ROOT / name).open('a', encoding='utf-8') as stream:
            stream.write(log)
    print(json.dumps({'status': checkpoint['status'], 'run_id': RUN, 'new_native_runs': 0}, ensure_ascii=False))


def guard():
    sys.path.insert(0, str(ROOT / 'scripts'))
    import guard_private_files as private
    subprocess.run(['git', 'merge-base', '--is-ancestor', START, 'HEAD'], cwd=ROOT, check=True)
    paths = set(git('diff', '--cached', '--name-only', '-z', START).decode().strip('\0').split('\0'))
    need(paths == OWNED | CODE, 'final index変更集合不一致: ' + str(paths ^ (OWNED | CODE)))
    for name in sorted(paths):
        raw = git('show', ':' + name)
        raw.decode('utf-8')
        need(b'\0' not in raw, 'tracked binary禁止')
        prior = subprocess.run(['git', 'show', START + ':' + name], cwd=ROOT, capture_output=True).stdout
        def violations(value):
            lines = value.decode('utf-8', errors='replace').splitlines()
            return Counter(lines[n - 1] for n in private.document_user_path_lines(value))
        need(not violations(raw) - violations(prior), '新規private path: ' + name)
        if name.startswith('design/'):
            need(raw.startswith(prior), 'ログappend-only違反')
    print(json.dumps({'status': 'PASS_SCOPED_FINAL_INDEX', 'paths': len(paths), 'new_private_violations': 0,
                      'full_historical_guard_pass_claimed': False}))


def snapshot():
    """後続実装の限定sourceをAPI往復せず取得する。private入力/binaryは含めない。"""
    patterns = ['scripts/pr16_learnset*.py', 'tools/pr16_learnset*.py', 'tests/test_pr16_learnset*.py',
                'src/modernization/pr16_learnset*', 'docs/PR16_LEARNSET*.md',
                'content/modernization/pr16_learnset*checkpoint.json',
                'content/modernization/pr16_learnset*inputs.json', '.github/workflows/pr16-learnset*.yml']
    exact = {STATE, DOC, 'AGENTS.md', 'scripts/pr16_resume.py', 'scripts/pr16_wiki_reconcile.py',
             'scripts/pr16_saved_recipe.py', 'tools/build_battle_core.py', 'tools/build_species_expansion.py',
             'tools/rom_allocator.py', 'tools/mgba_pr16_learnset_runtime.c', BASE + 'p08_remaining_work.json'}
    paths = [p for p in git('ls-files', '-z').decode().split('\0') if p and
             (p in exact or any(fnmatch.fnmatch(p, pattern) for pattern in patterns))]
    out = ROOT / '.local/pr16-learnset-runtime-record/context.zip'
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = {'source_head': git('rev-parse', 'HEAD').decode().strip(), 'files': {}}
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(paths):
            raw = git('show', 'HEAD:' + name)
            raw.decode('utf-8')
            need(b'\0' not in raw, 'source binary禁止')
            archive.writestr(name, raw)
            manifest['files'][name] = identity(raw)
        archive.writestr('context-manifest.json', encode(manifest))
    print(json.dumps({'files': len(paths), 'zip': identity(out.read_bytes())}))


if __name__ == '__main__':
    if sys.argv[1:] == ['record']:
        record()
    elif sys.argv[1:] == ['guard']:
        guard()
    elif sys.argv[1:] == ['paths']:
        print('\n'.join(sorted(OWNED)))
    elif sys.argv[1:] == ['snapshot']:
        snapshot()
    else:
        raise SystemExit('usage: pr16_learnset_runtime_record.py record|guard|paths|snapshot')
