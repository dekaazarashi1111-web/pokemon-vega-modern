#!/usr/bin/env python3
"""初期技/通常level-upの完了済み証拠を保存。host/ARM/nativeの再実行なし。"""
from __future__ import annotations
import datetime
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from pr16_learnset_runtime_record import need, identity, encode, git
BASELINE = 'fc7f87fb6d6dd3559b89b9cb1a667831bbcc9717'
TASK = 'USER-20260922-LEARNSET-PROGRESS'
PREFIX = 'content/modernization/'
INPUTS = PREFIX+'pr16_learnset_progress_record_inputs.json'
CP = PREFIX+'pr16_learnset_progress_checkpoint.json'
EVIDENCE = PREFIX+'pr16_learnset_progress_evidence'
STATE = PREFIX+'pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
GUIDE = 'docs/PR16_LEARNSET_PROGRESS_JA.md'
CODE = {'src/modernization/pr16_learnset_progress.h', 'src/modernization/pr16_learnset_progress.c',
        'src/modernization/pr16_learnset_progress_game.c', 'tests/fixtures/pr16_learnset_progress_bindings.h',
        'tests/fixtures/pr16_learnset_progress_fixture.c', 'tests/test_pr16_learnset_progress.py',
        'scripts/pr16_learnset_progress_verify.py', 'scripts/pr16_learnset_progress_reuse.py',
        'scripts/pr16_learnset_progress_abi.py', 'tools/mgba_pr16_learnset_progress.c',
        '.github/workflows/pr16-learnset-progress.yml', INPUTS,
        'scripts/pr16_learnset_progress_record.py', 'tests/test_pr16_learnset_progress_record.py',
        '.github/workflows/pr16-learnset-progress-record.yml'}


def inputs():
    return json.loads((ROOT/INPUTS).read_bytes())


def owned():
    return {CP, STATE, DOC, GUIDE, 'design/run_log.md', 'design/version_log.md'} | {
        EVIDENCE+'/'+name for name in inputs()['proof_files']}


def unpack(raw, bindings):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        need(len(archive.infolist()) == len(bindings) and set(archive.namelist()) == set(bindings), '証拠ZIP集合/重複違反')
        files = {}
        for info in archive.infolist():
            need(not info.is_dir() and info.external_attr >> 28 != 0xA and info.file_size <= 1000000, '証拠種類/容量違反')
            value = archive.read(info.filename)
            value.decode('utf-8')
            need(b'\0' not in value and '/' not in info.filename and '\\' not in info.filename, 'binary/階層を持つ証拠禁止')
            need(identity(value) == bindings[info.filename], '外側member hash不一致')
            files[info.filename] = value
        return files


def validate(files, expected):
    need(set(files) == set(expected['proof_files']), '証拠集合不一致')
    for name, binding in expected['proof_files'].items():
        need(identity(files[name]) == binding, '固定証拠改変: '+name)
    v = json.loads(files['verification.json'])
    need(v['status'] == 'PASS_INITIAL_AND_NATURAL_ROM_PROBES' and v['source_head'] == expected['source_head']
         and v['run_id'] == expected['run_id'], '完了HEAD/run/scope不一致')
    need(v['scope'] == 'HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E', '実操作E2Eへ昇格しない')
    need(v['candidate'] == expected['candidate'] and v['candidate']['size'] == 33554432, '候補ROM不一致')
    need(set(v['proof_files']) == set(files)-{'verification.json'}, '内側proof集合不一致')
    for name, binding in v['proof_files'].items():
        need(identity(files[name]) == binding, '内側member hash不一致')
    for key in ('conditional_consumers_connected', 'gameplay_e2e_accepted', 'release_ready', 'active_baseline_changed', 'issue19_complete'):
        need(v[key] is False, '未検証条件経路/実操作/リリースの昇格: '+key)
    for key in ('initial_and_natural_connected', 'p03_evolution_dispatch_unchanged', 'prior_two_entrypoints_unchanged',
                'independent_candidate_hashes_match', 'input_byte_mtime_unchanged', 'tracked_tree_unchanged'):
        need(v[key] is True, '接続/不変証拠不一致: '+key)
    for key in ('accepted_native_reruns', 'accepted_payload_regenerations', 'accepted_source_regenerations',
                'old_arm_compiles', 'focused_tests_executed', 'host_queries_executed'):
        need(type(v[key]) is int and v[key] == 0, '再実行境界違反: '+key)
    need(v['focused_tests'] == 30 and v['inherited_host_run'] == 35709388462
         and v['native_processes'] == 2, '新規/継承計数不一致')
    for key, value in expected['execution_counts'].items():
        need(v[key] == value, '実行計数不一致: '+key)
    host = json.loads(files['host-audit.json'])
    need(host == v['host_audit'] and host['owners'] == 1483 and host['levels'] == 100
         and host['queries'] == 318186 and host['identity_only_excluded'] == 188
         and host['input_image_unchanged'] is True, 'host全owner証拠不一致')
    need(files['unit.txt'].count(b' ... ok\n') == 30 and b'\nOK\n' in files['unit.txt'], '30試験原本不一致')
    inherited = json.loads(files['inherited-host.json'])
    need(inherited['run_id'] == 35709388462 and inherited['run_conclusion'] == 'failure'
         and inherited['focused_tests_executed'] == inherited['host_queries_executed'] == 0, '過去failure/継承境界不一致')
    link = json.loads(files['link.json'])
    need(link['candidate'] == v['candidate'] and link['outside_declared_ranges'] == 0
         and link['p03_evolution_dispatch_unchanged'] and link['prior_image_unchanged']
         and link['allocation']['summaries']['overlap_count'] == 0, '配置/保全境界不一致')
    need([h['offset'] for h in link['hooks']] == [0x3E14C, 0x11145F0, 0x1377728], '3入口範囲不一致')
    need(link['bundle']['size'] <= 4096 and link['code_end']-link['code_start'] == link['bundle']['size'], 'code配置容量違反')
    for i, name in enumerate(('native11.json', 'native29.json')):
        n = json.loads(files[name])
        need(n == v['native_results'][i] and n == expected['native_results'][i]
             and n['status'] == v['status'] and n['scope'] == v['scope']
             and n['candidate_sha256'] == v['candidate']['sha256'] and n['samples'] == 9, 'native原本不一致')
        for key in ('new_code_pc_seen_for_every_call', 'stored_four_moves_unchanged', 'real_initial_pp_checked'):
            need(n[key] is True, 'native不変条件違反')
    return v


def record():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_payload_verify import completed_run, current_pr
    from pr16_resume import render, pending_ids
    config = inputs()
    head = git('rev-parse', 'HEAD').decode().strip()
    current_pr(head)
    need(not (ROOT/CP).exists() and not (ROOT/EVIDENCE).exists(), '完了記録の重複禁止')
    done = completed_run(config['run_id'], config['source_head'], '.github/workflows/pr16-learnset-progress.yml', 'progress-boundary')
    listing = fetch(f"actions/runs/{config['run_id']}/artifacts?per_page=100")
    need(listing['total_count'] == len(listing['artifacts']), 'artifactページ不足')
    artifacts = {row['name']: row for row in listing['artifacts']}
    need(set(artifacts) == set(config['artifacts']), 'artifact集合不一致')
    for name, binding in config['artifacts'].items():
        a = artifacts[name]
        need((a['id'], a['size_in_bytes'], a['digest']) == (binding['id'], binding['size'], 'sha256:'+binding['sha256'])
             and not a['expired'] and a['workflow_run']['head_sha'] == config['source_head']
             and a['workflow_run']['id'] == config['run_id'], 'artifact/source結合不一致')
    binding = config['artifacts']['pr16-learnset-progress-proof']
    raw = fetch(f"actions/artifacts/{binding['id']}/zip", binary=True)
    need(identity(raw) == {k: binding[k] for k in ('size', 'sha256')}, '証拠ZIP hash不一致')
    files = unpack(raw, config['proof_files'])
    v = validate(files, config)
    for name, binding in v['code_bindings'].items():
        need(identity((ROOT/name).read_bytes()) == binding, '完了source変更: '+name)
    failures = []
    for number in config['preserved_failed_runs']:
        run = fetch(f'actions/runs/{number}')
        need(run['status'] == 'completed' and run['conclusion'] == 'failure', '過去failure改作禁止')
        failures.append({k: run[k] for k in ('id', 'head_sha', 'status', 'conclusion')})
    state = json.loads((ROOT/STATE).read_bytes())
    backlog = json.loads((ROOT/(PREFIX+'p08_remaining_work.json')).read_bytes())
    bp = json.loads((ROOT/(PREFIX+'pr16_bp_chooser_checkpoint.json')).read_bytes())
    need(pending_ids(backlog) == (state['remaining_physical_gap_ids'], state['remaining_p08_gate_ids'])
         and bp['accepted_case_count'] == 3 and not state['pr_merged'] and not state['release_ready']
         and not state['active_baseline_changed'], '正式native/P08/基準境界不一致')
    checkpoint = {'task': TASK, 'status': 'ACCEPTED_INITIAL_AND_NATURAL_DIRECT_ROM_PROBES_GAMEPLAY_PENDING',
        'source_head': config['source_head'], 'run_id': config['run_id'], 'record_source_head': head,
        'candidate': v['candidate'], 'candidate_crc32': v['candidate_crc32'], 'completed_actions': done,
        'artifacts': artifacts, 'proof_bindings': config['proof_files'], 'verification': v,
        'preserved_failed_runs': failures, 'gameplay_e2e_accepted': False, 'issue19_complete': False,
        'active_baseline_changed': False, 'release_ready': False}
    (ROOT/EVIDENCE).mkdir()
    for name, value in files.items():
        (ROOT/EVIDENCE/name).write_bytes(value)
    (ROOT/CP).write_bytes(encode(checkpoint))
    state['learnset_progress'] = {k: checkpoint[k] for k in ('status', 'source_head', 'run_id', 'candidate', 'gameplay_e2e_accepted', 'issue19_complete')}
    state['learnset_progress']['path'] = CP
    state.setdefault('observed_head_history', []).append({'head': state['observed_head'], 'semantics': state['observed_head_semantics'],
        'checks': state['observed_head_checks'], 'reason_ja': '初期技と通常level-upの限定受入を追加。旧2入口/正式BP/P08受入は不変。'})
    state['observed_head'] = config['source_head']
    state['observed_head_semantics'] = '初期技/通常level-upの直接ROM probe成功入力HEAD。記録commit/通常操作E2E/Issue19全完了ではない。'
    state['observed_head_checks'] = {'scope_head': config['source_head'], 'runs': [done],
        'reason_ja': '初期技/通常level-up接続と2独立配置・2native processを受入。30試験/318186照合はrun35709388462を継承し再実行0。通常操作/条件consumerは未受入。'}
    state['observed_date_jst'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    goal = 'Issue19: 保存済み初期技/通常level-up候補とPLR1/payloadを再利用し、進化・思い出し・egg/shared-egg・tutor等の条件consumerを個別に明示ownerへ接続。新候補Wikiを別pathへ生成し、Bag/戦闘/習得選択/Save/Continueの影響実操作E2Eを受入する。今回の直接ROM probeや30host試験を重複しない。'
    state['next_action'] = dict(state['next_action'], id='LEARNSET_CONDITIONAL_CONSUMERS_AND_GAMEPLAY', goal_ja=goal,
        read_paths=[GUIDE, CP, 'scripts/pr16_learnset_progress_verify.py', 'src/modernization/pr16_learnset_progress_game.c',
                    'scripts/pr16_evolution_learning_repair.py', 'docs/PR16_LEARNSET_PAYLOADS_JA.md'],
        stop_rule_ja='進化LR分岐/P03受入と保存4技/188保全枠を維持。条件経路を通常levelへ混ぜずarchive12件を実供給済みにしない。旧Wiki/基準ROMは変更しない。直接callを通常操作へ昇格せず、merge/releaseは行わない。')
    state['bp']['next_step'] = goal
    state['bp']['current_stop'] = '旧2入口に加え初期技/通常level-upを新候補'+v['candidate']['sha256'][:8]+'へ接続。3hook/全差分rollback/P03進化dispatch不変・30試験/全1483owner×100level/318186照合・9代表条件×2processの直接ROM probeを受入。条件consumer/新Wiki/通常操作E2Eは未完。'
    state['do_not_repeat'].append('初期技/通常level-up: run'+str(config['run_id'])+'の2process直接ROM probeと独立配置を再実行しない。30試験/318186 host照合はrun35709388462の成功部分を継承。途中失敗runは保持し、保存candidate/bundle/linkから再開。')
    state['logs_synchronized'] = True
    (ROOT/STATE).write_bytes(encode(state))
    (ROOT/DOC).write_text(render(state), encoding='utf-8')
    (ROOT/GUIDE).write_text('# Issue19: 初期技と通常level-up\n\n'+state['bp']['current_stop']+'\n\n## 完了境界\n\n'
        +'候補SHA-256 `'+v['candidate']['sha256']+'`、33554432 bytes、CRC32 `'+v['candidate_crc32']+'`。成功Actions `'+str(config['run_id'])+'`、入力HEAD `'+config['source_head']+'`。\n\n'
        +'初期技は該当level以下の末尾4行を既存GiveMoveToBoxMonへ渡す。既存の非空4技は変更しない。通常習得は同levelの複数行を順に通知し、満杯/既習得の戻り値とPPを維持する。進化専用/思い出し等の行を通常levelへ混ぜない。\n\n'
        +'真の初期技入口0x0803E14Cと別CFRU初期関数0x091145F0、通常QoL delegate0x09377728の3か所を接続。0x0803E174は関数途中でありC ABI入口ではない。P03進化dispatchと2つの進化LR分岐はbyte不変。旧2入口/PLR1/root/save構造は不変。\n\n'
        +'9代表条件でCreateMon・実PP・初期2入口・通常2入口・満杯通知・重複後継続・非学習owner保全を検証。ただしhost fixtureからの直接ROM callであり、野生遭遇/Bag/戦闘/習得画面/Save/Continueの実操作受入ではない。固定CFRU source configのrandomizer無効確認は全ビルドmacroの網羅検証ではない。\n\n'
        +'30host試験と318186照合は失敗run35709388462の成功部分を継承。ABI/配置検査失敗を成功へ改作しない。証拠/checkpointのhashとsource bindingから再開し、受入済みhost/ARM/nativeを重複しない。\n\n## 次工程\n\n'+goal+'\n', encoding='utf-8')
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = '\n## '+stamp+'\n- Timestamp: '+stamp+'\n- Task: '+TASK+' / 初期技・通常level-upのROM consumer接続\n'
    log += '- Version: learnset-progress-v1\n- Status: DONE（初期技/通常level-up直接ROM probe限定。条件経路/通常操作E2Eは未完）\n'
    log += '- Summary: 新候補'+v['candidate']['sha256'][:8]+'、3hook、P03進化分岐/旧PLR1/保存4技を保全。9代表条件×2native process、実PP/満杯/重複後継続を確認。\n'
    log += '- Files changed: 新C/typed fixture/30境界試験、配置・診断・継承・native検証器、限定Actions、証拠/checkpoint/guide、固定引継ぎMD/JSON、両ログ。\n'
    log += '- Verify: run'+str(config['run_id'])+' SUCCESS。30試験/318186照合は成功証拠継承。新記録拒否試験・resume check・task graph・diff --check・final index guard PASS後のみcommit。\n'
    log += '- Commit: 本記録を含む同branch非force commit。自己SHAはgit logで照合。\n'
    log += '- Network: GitHub固定run/artifact、CFRU-JP@e24a16feのBPRJ.ld/src/config.hをhash照合。原本収集/旧accepted native/hostの再実行0。ABI/offset失敗履歴はcheckpointに保持。\n'
    for path in ('design/run_log.md', 'design/version_log.md'):
        with (ROOT/path).open('a', encoding='utf-8') as stream:
            stream.write(log)
    print(json.dumps({'status': checkpoint['status'], 'candidate': v['candidate'], 'run_id': config['run_id'], 'new_native_runs': 0}))


def guard():
    import pr16_learnset_runtime_record as scoped
    scoped.START, scoped.CODE, scoped.OWNED = BASELINE, CODE, owned()
    scoped.guard()
    subprocess.run(['git', 'diff', '--cached', '--check', BASELINE], cwd=ROOT, check=True)


if __name__ == '__main__':
    if sys.argv[1:] == ['record']:
        record()
    elif sys.argv[1:] == ['guard']:
        guard()
    elif sys.argv[1:] == ['paths']:
        print('\n'.join(sorted(owned())))
    else:
        raise SystemExit('usage: pr16_learnset_progress_record.py record|guard|paths')
