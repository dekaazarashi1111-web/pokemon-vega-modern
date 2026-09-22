#!/usr/bin/env python3
"""保存された供給ARMリンクを照合・記録する。旧生成/受入試験は呼ばない。"""
from __future__ import annotations
import datetime
import fnmatch
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
START = 'abc3218f56f4bab6e97991cbfe8923b422d90f21'
TASK = 'USER-20260922-LEARNSET-SUPPLY-ABI'
PREFIX = 'content/modernization/'
INPUTS = PREFIX + 'pr16_learnset_supply_link_record_inputs.json'
CP = PREFIX + 'pr16_learnset_supply_link_checkpoint.json'
EVIDENCE = PREFIX + 'pr16_learnset_supply_link_evidence'
STATE = PREFIX + 'pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
GUIDE = 'docs/PR16_LEARNSET_SUPPLY_JA.md'
WORK = ROOT / '.local/pr16-learnset-supply-link-record'
CODE = {INPUTS, 'scripts/pr16_learnset_supply_link_record.py',
        'tests/test_pr16_learnset_supply_link_record.py',
        'scripts/pr16_learnset_supply_link_actions.py',
        'tests/test_pr16_learnset_supply_link_actions.py',
        '.github/workflows/pr16-learnset-supply-link-record.yml'}
FALSE_FLAGS = ('physical_supply_verified', 'gameplay_e2e_accepted', 'issue19_complete',
               'active_baseline_changed', 'release_ready')
ZERO_COUNTS = ('accepted_tests_rerun', 'accepted_native_reruns', 'accepted_payload_regenerations',
               'old_arm_compiles', 'new_native_processes', 'new_tests')
HOOKS = {'Pr16_GameCanLearnTutor': 0x1110228, 'Pr16_GameSupplyRelearner': 0x11141D4,
         'Pr16_GameSupplySelectedRowCount': 0x1539D78, 'Pr16_GameSupplySelectedPageHasMoves': 0x153A23C}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def load(path):
    return json.loads(path.read_bytes())


def inputs():
    return load(ROOT / INPUTS)


def owned():
    return {CP, STATE, DOC, GUIDE, 'design/run_log.md', 'design/version_log.md'} | {
        EVIDENCE + '/' + name for name in inputs()['proof_files']}


def validate(files, config):
    need(set(files) == set(config['proof_files']), '証拠集合不一致')
    for name, binding in config['proof_files'].items():
        raw = files[name]
        raw.decode('utf-8')
        need(b'\0' not in raw and identity(raw) == binding, '証拠hash/text不一致: ' + name)
    v = json.loads(files['verification.json'])
    need(v['status'] == 'PASS_NEW_SUPPLY_ARM_LINK' and
         v['scope'] == 'REAL_ROM_LINK_NOT_NATIVE_OR_GAMEPLAY_ACCEPTANCE', 'リンクを実操作へ昇格しない')
    need(v['source_head'] == config['source_head'] == START and v['run_id'] == config['run_id'] == 35732715452
         and v['task'] == TASK, 'run/source不一致')
    need(v['candidate'] == config['candidate'] and v['candidate_crc32'] == '9A91E7FB', '候補不一致')
    need(set(v['proof_files']) == set(files) - {'verification.json'}, '内側証拠集合不一致')
    for name, binding in v['proof_files'].items():
        need(identity(files[name]) == binding, '内側証拠hash不一致')
    for name in FALSE_FLAGS:
        need(v[name] is False, '未受入範囲の昇格: ' + name)
    for name in ZERO_COUNTS:
        need(type(v[name]) is int and v[name] == 0, '再実行/未観測計数違反: ' + name)
    for name, value in {'new_arm_compiles': 8, 'new_arm_links': 2, 'inherited_scoped_tests': 14}.items():
        need(type(v[name]) is int and v[name] == value, '継承/実行計数不一致')
    need(v['independent_candidate_match'] is True, '独立2生成一致欠落')
    failed = v['failed_predecessor']
    need(failed['run_id'] == 35731723699 and failed['conclusion'] == 'failure'
         and failed['source_head'] == '1bb993d81ba08e5633e79cd67992a1326b4607da'
         and failed['new_native_processes'] == 0, '失敗原本の改作禁止')
    inherited = json.loads(files['inherited-unit.json'])
    need(inherited['run_id'] == failed['run_id'] and inherited['source_head'] == failed['source_head']
         and inherited['whole_run_conclusion'] == 'failure' and inherited['scoped_tests_passed'] == 14
         and inherited['tests_rerun'] == 0, '14試験の出典不一致')
    need(files['unit.txt'].count(b' ... ok\n') == 14 and b'Ran 14 tests' in files['unit.txt']
         and files['unit.txt'].rstrip().endswith(b'OK') and not files['tracked-diff.txt'], '成功部分原本不一致')
    link = json.loads(files['link.json'])
    need(link['status'] == 'LINKED_PLA1_TUTOR_AND_ARCHIVE' and link['candidate'] == v['candidate']
         and link['candidate_crc32'] == v['candidate_crc32'] and link['parent'] == config['parent_candidate'], 'link候補/親不一致')
    need(len(link['hooks']) == 4 and {p['symbol']: p['offset'] for p in link['hooks']} == HOOKS, '4hook集合不一致')
    need(len(link['segments']) == 2 and {s['file'] for s in link['segments']} == {'archive-image.bin', 'supply.bin'}, 'segment集合不一致')
    spans = []
    for p in link['hooks']:
        need(len(bytes.fromhex(p['before'])) == len(bytes.fromhex(p['after'])) == 8
             and p['target'] & 1 and link['code_start'] <= p['target'] - 1 < link['code_end'], 'hook byte/target不一致')
        spans.append((p['offset'], p['offset'] + 8))
    for seg in link['segments']:
        need(seg['end_exclusive'] - seg['start'] == seg['size'] > 0
             and v['data_files'][seg['file']] == {'size': seg['size'], 'sha256': seg['sha256']}, 'segment容量/hash不一致')
        spans.append((seg['start'], seg['end_exclusive']))
    spans.sort()
    need(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), '変更領域重複')
    need(link['outside_declared_ranges'] == 0 and link['parent_compact_segments_unchanged'] is True
         and link['special_body_unchanged'] is True and link['rom_hooks_installed'] is True, '親/特殊body保全欠落')
    need(link['code_end'] - link['code_start'] == 2784 and link['special_tutor_ids'] == list(range(152, 161))
         and set(link['page_count_callers']) == {'Prepare', 'Open', 'Commit'}
         and all(len(v_) == 1 for v_ in link['page_count_callers'].values()), '特殊Tutor/page caller不一致')
    for name in ('gameplay_e2e_accepted', 'physical_supply_verified', 'issue19_complete', 'release_ready'):
        need(link[name] is False, 'link未受入の昇格禁止')
    need(v['data_files']['archive-image.bin'] == config['image'], 'PLA1不変性違反')
    return v


def record():
    from pr16_learnset_floette_verify import download
    from pr16_learnset_payload_verify import current_pr
    from pr16_learnset_supply_link_actions import completed_run
    from pr16_learnset_compact_record import publish_resume
    from pr16_resume import pending_ids
    config = inputs()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    current_pr(head)
    need(not (ROOT / CP).exists() and not (ROOT / EVIDENCE).exists(), '同じ受入記録の重複禁止')
    done = completed_run(config['run_id'], config['source_head'], '.github/workflows/pr16-learnset-supply-link-followup.yml', 'supply-link-followup')
    download(config['artifacts']['proof'], config['source_head'], WORK / 'proof', config['proof_files'])
    files = {n: (WORK / 'proof' / n).read_bytes() for n in config['proof_files']}
    v = validate(files, config)
    download(config['artifacts']['data'], config['source_head'], WORK / 'data', v['data_files'])
    need((WORK / 'data/link.json').read_bytes() == files['link.json'], 'data/proof不一致')
    for name, binding in v['code_bindings'].items():
        need(identity((ROOT / name).read_bytes()) == binding, '受入source変更: ' + name)
    parent = load(ROOT / (PREFIX + 'pr16_learnset_compact_checkpoint.json'))
    host = load(ROOT / (PREFIX + 'pr16_learnset_supply_checkpoint.json'))
    need(parent['candidate'] == config['parent_candidate'] and host['image'] == config['image'], '既受入入力不一致')
    state = load(ROOT / STATE)
    backlog = load(ROOT / (PREFIX + 'p08_remaining_work.json'))
    bp = load(ROOT / (PREFIX + 'pr16_bp_chooser_checkpoint.json'))
    need(pending_ids(backlog) == (state['remaining_physical_gap_ids'], state['remaining_p08_gate_ids'])
         and bp['accepted_case_count'] == 3 and not state['pr_merged']
         and not state['release_ready'] and not state['active_baseline_changed'], '正式BP/P08境界不一致')
    checkpoint = {'task': TASK, 'status': 'ACCEPTED_ROM_SUPPLY_LINK_NATIVE_PENDING',
        'source_head': config['source_head'], 'run_id': config['run_id'], 'record_source_head': head,
        'completed_actions': done, 'artifacts': config['artifacts'], 'proof_bindings': config['proof_files'],
        'candidate': v['candidate'], 'candidate_crc32': v['candidate_crc32'], 'parent_candidate': config['parent_candidate'],
        'image': config['image'], 'verification': v, 'data_files': v['data_files'],
        'rom_hooks_installed': True, 'game_tutor_connected': True, 'archive_rebound': True,
        'connection_scope': 'ROM_BYTE_LINK_ONLY_NOT_NATIVE_ACCEPTANCE',
        'record_failed_predecessor': {'run_id': 35734221410, 'source_head': '4617ce06c04effcc7aa45b8bf5b30eab6a7f527f',
            'conclusion': 'failure', 'reason': 'failure-only upload step was skipped; over-strict all-success checker rejected before record',
            'new_tests': 0, 'new_native_processes': 0, 'pushed': False}, **{n: False for n in FALSE_FLAGS}}
    (ROOT / EVIDENCE).mkdir()
    for name, raw in files.items():
        (ROOT / EVIDENCE / name).write_bytes(raw)
    (ROOT / CP).write_bytes(encode(checkpoint))
    state['learnset_supply_link'] = {k: checkpoint[k] for k in
        ('status', 'source_head', 'run_id', 'candidate', 'candidate_crc32', 'rom_hooks_installed', 'connection_scope', *FALSE_FLAGS)}
    state['learnset_supply_link']['path'] = CP
    state.setdefault('observed_head_history', []).append({'head': state['observed_head'],
        'semantics': state['observed_head_semantics'], 'checks': state['observed_head_checks'],
        'reason_ja': '保存済み供給ARMリンクの成功を反映。PLA1 host/PLC2/P08の受入原本は不変。'})
    state['observed_head'] = config['source_head']
    state['observed_head_semantics'] = '供給ARM独立2link成功の入力HEAD。通常操作・native・記録commitの受入ではない。'
    state['observed_head_checks'] = {'scope_head': config['source_head'], 'runs': [done],
        'reason_ja': '未反映run35732715452を照合。14試験は失敗runの成功部分を継承。今回記録でARM/native/既受入試験再実行0。'}
    state['observed_date_jst'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    goal = 'Issue19: 保存候補ec5992aaと供給ARM/PLA1/link.jsonをhash検証で復元し、新しい4hookの実ROM ABI・Tutor特殊条件・raw40行ページ選択を検証する。既受入ARM/PLA1生成/14試験/旧4入口probeを再実行しない。次に別候補Wikiと変更影響のBag/戦闘/習得選択/Save/Continueへ進む。'
    state['next_action'] = dict(state['next_action'], id='LEARNSET_SUPPLY_NATIVE_AND_GAMEPLAY', goal_ja=goal,
        read_paths=[GUIDE, CP, 'src/modernization/pr16_learnset_supply_native.c',
                    'scripts/pr16_learnset_supply_link.py', 'docs/PR16_LEARNSET_COMPACT_JA.md',
                    PREFIX + 'pr16_learnset_compact_checkpoint.json'])
    state['bp']['next_step'] = goal
    state['bp']['current_stop'] = 'run35732715452の新供給ARM2784 bytes・PLA1 21383 bytes・4hookを候補ec5992aaへ配置し独立2生成一致を確認。特殊Tutor152..160 bodyとPLC2保存segmentは不変。14試験は初回失敗runの成功部分を継承。新native/通常操作/新Wikiは未完。'
    state['do_not_repeat'].append('供給ARM: run35732715452/abc3218f56f4の8compile/2linkと候補ec5992aaの同値性は受入済み。保存supply.bin/PLA1/link.jsonを再利用し、旧ARM/PLA1/初回14試験を再実行しない。run35731723699のmemset未解決failureは成功へ改作しない。')
    state['logs_synchronized'] = True
    publish_resume(state)
    prior = (ROOT / GUIDE).read_text(encoding='utf-8')
    guide = '# Issue19: Tutor/追加archive consumer（実ROM配置受入済み）\n\n' + state['bp']['current_stop'] + '\n\n'
    guide += '候補SHA-256 `' + v['candidate']['sha256'] + '` / 33554432 bytes / CRC32 `9A91E7FB`。正本 `' + CP + '`。\n\n'
    guide += '固定PLC2親から保存byteを適用した候補であり、clean-ROM最終2生成や通常操作の受入ではない。新ARM8compile/2linkは完了runの値。今回の記録では再実行0。初回記録run35734221410は失敗時artifactのskipを誤拒否してpush前に停止し、failureのまま保持。保存4技/PP、通常level/P03進化LR、正式BP/P08、旧Wiki、baselineを変更しない。\n\n## 次工程\n\n' + goal + '\n\n## 前段階の記録（履歴）\n\n' + prior
    (ROOT / GUIDE).write_text(guide, encoding='utf-8')
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 未反映供給ARMリンクの受入・固定再開点更新\n- Version: learnset-supply-rom-link-v1\n- Status: DONE（ROM配置限定。実操作/新Wikiは未完）\n- Summary: run35732715452の保存証拠を照合。ec5992aa/4hook/ARM2784 bytes/PLA1 21383 bytes/独立2候補一致。初回14試験を継承、失敗履歴を保持。\n- Files changed: 専用record/拒否試験/入力binding/Actions、link証拠/checkpoint、固定再開MD/JSON、供給guide、両ログ。\n- Verify: 外側ZIP・全member/source hash・親checkpoint/BP/P08一致、新規記録拒否試験、resume/task graph/final index限定guard PASS後のみcommit。旧受入/native/ARM再実行0。全履歴guardのPASSは主張しない。\n- Commit: 本記録を含む同branch非force commit。自己SHAはgit logで照合。\n- Network: GitHub既存Actions/artifactだけ。原本再採取/merge/release/baseline切替なし。\n'
    for name in ('design/run_log.md', 'design/version_log.md'):
        with (ROOT / name).open('a', encoding='utf-8') as stream:
            stream.write(log)
    print(json.dumps({'status': checkpoint['status'], 'run_id': config['run_id'], 'accepted_reruns': 0}))


def guard():
    import pr16_learnset_runtime_record as scoped
    scoped.START, scoped.CODE, scoped.OWNED = START, CODE, owned()
    scoped.guard()
    subprocess.run(['git', 'diff', '--cached', '--check', START], cwd=ROOT, check=True)


def snapshot():
    patterns = ['scripts/pr16_learnset*.py', 'tools/pr16_learnset*.py', 'tests/test_pr16_learnset*.py',
        'tests/fixtures/pr16_learnset*', 'src/modernization/pr16_learnset*', 'tools/mgba_pr16_learnset*.c',
        'docs/PR16_LEARNSET*.md', 'content/modernization/pr16_learnset*checkpoint.json',
        'content/modernization/pr16_learnset*inputs.json', '.github/workflows/pr16-learnset*.yml']
    exact = {STATE, DOC, 'AGENTS.md', 'README.md', 'design/agent_context_map.md', 'design/current_state.md',
        'scripts/pr16_resume.py', 'scripts/pr16_wiki_reconcile.py', 'scripts/pr16_saved_recipe.py',
        'tools/rom_allocator.py', 'infra/toolchain_manifest.json', 'config/active_play_baseline.json',
        'design/active_play_baseline.md', PREFIX + 'p08_remaining_work.json', PREFIX + 'pr16_bp_chooser_checkpoint.json'}
    paths = [p for p in subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
             if p and (p in exact or any(fnmatch.fnmatch(p, pat) for pat in patterns))]
    WORK.mkdir(parents=True, exist_ok=True)
    manifest = {'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(), 'files': {}}
    with zipfile.ZipFile(WORK / 'context.zip', 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(paths):
            raw = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT)
            raw.decode('utf-8')
            need(b'\0' not in raw, 'snapshot binary禁止')
            z.writestr(name, raw)
            manifest['files'][name] = identity(raw)
        z.writestr('context-manifest.json', encode(manifest))
    print(json.dumps({'files': len(paths), 'source_head': manifest['source_head'], 'zip': identity((WORK / 'context.zip').read_bytes())}))


if __name__ == '__main__':
    actions = {'record': record, 'guard': guard, 'snapshot': snapshot, 'paths': lambda: print('\n'.join(sorted(owned())))}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        raise SystemExit('usage: pr16_learnset_supply_link_record.py record|guard|snapshot|paths')
    actions[sys.argv[1]]()
