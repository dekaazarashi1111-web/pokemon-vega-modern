#!/usr/bin/env python3
"""成功したpatch/handler限定監査を固定引継ぎへ記録。再build/nativeなし。"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_patch_owner as owner

BASE = 'd95bb137a4a8332da7b7ce2e97640e198524342e'
HEAD = '03ca035d5617b4d381845189e15838b5ba495a7d'
RUN, JOB, ARTIFACT = 34964225479, 104364767602, 10394980742
DIGEST = 'abfd6019728f39df7ce64f8dce8b2c0a49fadfdec2670f7005a3ef8dd117b879'
ZIP_SIZE = 46664
AUDIT = {'size': 120846, 'sha256': 'dbfe69964b34de5bf87d4a829928b572a4c9d1e53fcd4c489339e27fe15f013e'}
SELF = 'scripts/pr16_ring_patch_record.py'
TEST = 'tests/test_pr16_ring_patch_record.py'
WORKFLOW = '.github/workflows/pr16-ring-patch-record.yml'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
BACKLOG = 'content/modernization/p08_remaining_work.json'
LOGS = ('design/run_log.md', 'design/version_log.md')
OUTPUTS = (owner.REPORT, STATE, DOC, BACKLOG, *LOGS)
ALLOWED = set((*OUTPUTS, SELF, TEST, WORKFLOW, owner.SELF, owner.TEST, owner.WORKFLOW))
OUT = ROOT / '.local/pr16-ring-patch-record'
GAP = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
NEXT = ('成功run34964225479の24 graph/366命令、callstd4/旧6入口を再実行せず、'
        '保存済みgraphから15間接辺を戻り番地とR3 trampolineにABI/dataflowで分類する。'
        '特にQOL_FEATURE→0x09376F45、FlagSet→0x09377615、0x093789F3→0x0806DE7Dを確認し、'
        '18未読targetは必要なrootだけ追加採取する。全owner未除外のままRing story giftを新設しない。'
        '通常取得ownerの未実装を確認できた場合だけ正規story取引を実装し、条件不足・取消・二重取得・'
        '容量不足、通常取得、装備実戦、Save/fresh Continueを検証する。')
need = owner.need


def validate_metadata(value):
    audit = copy.deepcopy(value)
    v = audit.pop('verification')
    audit.pop('actions_observed_before_record')
    need(owner.identity(owner.stable(audit)) == AUDIT, 'successful audit bytes differ')
    need(audit['source_head'] == HEAD and audit['task'] == owner.TASK, 'wrong audit source')
    need(v['run'] == {'id': RUN, 'head_sha': HEAD, 'status': 'completed', 'conclusion': 'success'}, 'wrong run')
    need(v['job'] == {'id': JOB, 'run_id': RUN, 'status': 'completed', 'conclusion': 'success'}, 'wrong job')
    need(v['artifact'] == {'id': ARTIFACT, 'run_id': RUN, 'head_sha': HEAD, 'sha256': DIGEST, 'size': ZIP_SIZE}, 'wrong artifact')
    need(v['focused_tests'] == {'tests_run': 18, 'successful': True, 'failures': 0, 'errors': 0, 'skips': 0}, 'wrong tests')
    need(audit['primary_roots_decoded'] is True, 'primary roots incomplete')
    return value


def validate_receipt(value):
    validate_metadata(value)
    for name, binding in value['source_bindings'].items():
        need(owner.identity(owner.safe(ROOT, name).read_bytes()) == binding, 'stale audit source: ' + name)
    import pr16_ring_transitive_record as old_record
    import pr16_ring_transitive_owner as old_owner
    old_record.validate_receipt(json.loads(owner.safe(ROOT, owner.PRIOR).read_bytes()))
    old_owner.reuse(json.loads(owner.safe(ROOT, old_owner.prior.REPORT).read_bytes()))
    return value


def project(state, backlog, report):
    s, b = copy.deepcopy(state), copy.deepcopy(backlog)
    need(all(s['candidate'][k] == v for k, v in report['candidate'].items()), 'candidate changed')
    need(s['bp']['spending_accepted'] is True and s['latest_native_run'] == 34946969126, 'BP acceptance changed')
    need(not s['candidate']['final_product_sha_fixed'] and not s['candidate']['full_candidate_regression_complete'], 'release promotion')
    need(GAP in s['remaining_physical_gap_ids'], 'Ring already closed')
    row = next(r for r in b['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    need(GAP in row['remaining_supply_gap_ids'] and row['selected_supply_entrypoints'][GAP] is None, 'Ring owner changed')
    row['ring_patch_owner'] = owner.REPORT
    s['ring_patch_owner'] = {'path': owner.REPORT, 'run_id': RUN, 'source_head': HEAD,
        'classification': report['classification'], 'new_graphs': 24, 'instructions': 366,
        'unread_targets': 18, 'unresolved_indirect_edges': 15, 'ring_acquisition_accepted': False}
    stop = ('Ring patch先・標準handlerの限定追跡を実装・検証。FlagSet→0x093775C5と'
            'SaveFinalize→0x093BDD7D、callstd4 handler 03/66/67/6Dをcandidate byteで照合。'
            '新規24 graph/366命令・56 memory-write siteを記録し、decoder停止0。'
            '18未読target（22辺）と15間接辺は未解決のまま保存。'
            'Ring通常取得・全runtime owner不存在は未証明。正式BP受入run34946969126は不変。')
    s['bp']['current_stop'] = s['source_change_review_ja'] = stop
    s['bp']['next_step'] = s['next_action']['goal_ja'] = NEXT
    s['next_action']['read_paths'] = [owner.REPORT, owner.SELF, owner.PRIOR,
        'overlays/save_migration/save_migration.c', 'overlays/qol_production/qol_production.c']
    s['observed_head'] = HEAD
    s['observed_head_semantics'] = 'patch先・標準handler限定byte監査のsource HEAD。最終記録commitはremote refで確認する。'
    s['observed_head_checks']['reason_ja'] = ('限定run34964225479/job104364767602はsuccess、18 tests PASS。'
        'これは全Actions greenやrelease受入ではない。自動P03 run34964225326のfailure、開始HEADのaction_requiredを保持し、最新snapshotをreceiptへ保存。')
    s['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'accepted_standalone_replays': 0, 'candidate_reconstructions': 1,
        'scope_ja': '新規patch/handler/callee有限追跡1回。既存入口/compiled/callstd監査・BP native再実行0。記録時再build0。通常pushの自動CIは別枠。'}
    note = 'run34964225479の18 tests・24 graph/366命令は同一source/candidateなら再実行しない。残る18target/15間接辺だけを進める。Ring通常取得受入や全owner不存在へ読み替えない。'
    if note not in s['do_not_repeat']:
        s['do_not_repeat'].append(note)
    return s, b


def check():
    import pr16_resume as resume
    report = validate_receipt(resume.load(ROOT, owner.REPORT))
    state = resume.validate(ROOT)
    backlog = resume.load(ROOT, BACKLOG)
    need(project(state, backlog, report) == (state, backlog), 'record projection differs')
    return report


def prepare(path):
    import pr16_resume as resume
    report = validate_receipt(json.loads(path.read_bytes()))
    need(not (ROOT / owner.REPORT).exists(), 'already recorded; do not duplicate')
    state, backlog = project(resume.validate(ROOT), resume.load(ROOT, BACKLOG), report)
    (ROOT / owner.REPORT).write_bytes(owner.stable(report))
    for name in (owner.SELF, owner.TEST, owner.WORKFLOW, owner.REPORT, SELF, TEST, WORKFLOW):
        state['source_bindings'][name] = owner.identity((ROOT / name).read_bytes())
    (ROOT / BACKLOG).write_bytes(owner.stable(backlog))
    (ROOT / STATE).write_bytes(owner.stable(state))
    (ROOT / DOC).write_text(resume.render(state), encoding='utf-8')
    check()


def logs():
    check()
    tests = json.loads((OUT / 'tests.json').read_bytes())
    need(tests['successful'] and tests['tests_run'] > 0 and tests['skips'] == 0, 'record tests failed')
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {owner.TASK}\n- Timestamp: {stamp}\n- Task: {owner.TASK}\n'
        '- Status: DONE / patch先・標準handler有限追跡の実装・検証・記録。Ring通常取得は未受入。\n'
        '- Version: PR16 Ring patch/handler bounded frontier\n'
        '- Summary: 既存6入口/callstd4を再走査せず、両patch先と4標準handler、記録済みcalleeから24 graph/366命令を検証。56 memory-write siteを保持。未知命令を推測せず、18未読targetと15間接辺を未解決として出力する。\n'
        f'- Verify: 新規18 tests PASS、run{RUN}/job{JOB} success。記録/固定resume {tests["tests_run"]} tests PASS。task graph、read-only check、最終index差分guard、diffをcommit必須gateとする。\n'
        f'- Evidence: {owner.REPORT}; source HEAD={HEAD}; artifact{ARTIFACT}; SHA256={DIGEST}。\n'
        '- Preserved: candidate ceddbe91/CRC3EB17B36とBP checkpoint/原本は不変。候補再構築1、native0、受入済み単独再実行0、ROM変更0。P03自動CI failure/action_requiredを成功に読み替えない。\n'
        '- Files changed: 新規監査/記録helper・tests・workflows、receipt、固定引継ぎMD/JSON、P08 Ring参照、両ログ。\n'
        '- Commit: この記録を含む同branchへの非force commit。自己SHAはremote refとrecorded-resultで照合。\n'
        '- Network: GitHub connector/Actions。containerの直接Git取得はDNS失敗のため使用せず、権限不足とは扱わない。ROM/save/private入力の新規追跡なし。既存全体guardの違反は保持し前後完全一致・追加違反0を要求。merge/release/baseline切替なし。\n'
        '- Next: ' + NEXT + '\n')
    for name in LOGS:
        p = ROOT / name
        need(owner.TASK not in p.read_text(encoding='utf-8'), 'completion log already exists')
        with p.open('a', encoding='utf-8') as stream:
            stream.write(entry)
    check()


def guard():
    import pr16_ring_compiled_record as previous
    previous.BASE, previous.OUT, previous.ALLOWED = BASE, OUT, ALLOWED
    previous.guard()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('prepare', 'check', 'logs', 'guard'))
    p.add_argument('--receipt', type=Path)
    a = p.parse_args()
    if a.command == 'prepare':
        need(a.receipt is not None, 'receipt required'); prepare(a.receipt)
    elif a.command == 'check':
        check(); print('PASS_PATCH_HANDLER_RECORD_NOT_NATIVE_ACCEPTANCE')
    elif a.command == 'logs':
        logs()
    else:
        guard()
