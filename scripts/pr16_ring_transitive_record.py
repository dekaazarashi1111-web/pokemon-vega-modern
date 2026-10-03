#!/usr/bin/env python3
"""成功したRing第一段だけを記録。ROM/native再実行や未検証closureの追認なし。"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_resume as resume
import pr16_ring_transitive_owner as owner
import pr16_ring_compiled_record as previous

BASE = '6638194aac8d3bc8d866e29f6110191fdbe52339'
SELF = 'scripts/pr16_ring_transitive_record.py'
TEST = 'tests/test_pr16_ring_transitive_record.py'
WORKFLOW = '.github/workflows/pr16-ring-transitive-record.yml'
OUT = ROOT / '.local/pr16-ring-transitive-record'
OUTPUTS = (owner.REPORT, resume.STATE, resume.DOC, resume.BACKLOG, *previous.LOGS)
ALLOWED = set(OUTPUTS + (SELF, TEST, WORKFLOW, owner.SELF, owner.TEST, owner.WORKFLOW))
AUDIT = {'size': 29240, 'sha256': '5f3863a9e5cb65bbf709cdc6e945b1f85adf8c80f078291a9642ae4164bad3b5'}
HEAD = '41debb1dc1ac3c8fddefe7fa97898e7ecd2943b7'
RUN, JOB, ARTIFACT = 34960361700, 104352222046, 10392663831
DIGEST = 'a3ae8cbfc1ce80a7883c152950f8ccfd939fe8ca33defc007b785f77a5619a5d'
GAP = previous.GAP
NEXT = ('成功済みcallstd4と6 native入口の証拠を再実行せず再利用し、'
        'FlagSet 0x0806DE75→0x093775C5、SaveFinalize 0x092D28D9→0x093BDD7Dの'
        'patch先と、記録された未解決callee/標準script engine handlerだけを限定追跡する。'
        'callstd4のscript層はmessage/wait/returnだがengine副作用やRing giver不存在は未証明。'
        '通常取得ownerが未実装と確認できた場合だけ正規story取引を実装し、条件不足・取消・'
        '二重取得・容量不足、通常取得、装備実戦、Save/fresh Continueを検証する。')
need = owner.need


def validate_receipt(value, root=ROOT):
    audit = copy.deepcopy(value)
    verification = audit.pop('verification')
    audit.pop('actions_observed_before_record')
    need(owner.identity(owner.stable(audit)) == AUDIT, 'successful audit bytes differ')
    need(audit['source_head'] == HEAD and audit['task'] == owner.TASK, 'wrong audit source')
    for name,binding in audit['source_bindings'].items():
        need(owner.identity(resume.safe_path(root,name).read_bytes()) == binding, 'stale source: '+name)
    need(verification['run'] == {'id':RUN,'head_sha':HEAD,'status':'completed','conclusion':'success'}, 'wrong run')
    need(verification['job'] == {'id':JOB,'run_id':RUN,'status':'completed','conclusion':'success'}, 'wrong job')
    need(verification['artifact'] == {'id':ARTIFACT,'run_id':RUN,'head_sha':HEAD,'sha256':DIGEST,'size':42421}, 'wrong artifact')
    need(verification['focused_tests'] == {'tests_run':34,'successful':True,'failures':0,'errors':0,'skips':0}, 'wrong tests')
    return value


def project(state, backlog, report):
    s,b = copy.deepcopy(state),copy.deepcopy(backlog)
    need({k:s['candidate'].get(k) for k in owner.prior.CANDIDATE} == owner.prior.CANDIDATE, 'candidate changed')
    need(s['bp']['spending_accepted'] is True and s['latest_native_run']==34946969126, 'BP acceptance changed')
    need(not s['candidate']['final_product_sha_fixed'] and not s['candidate']['full_candidate_regression_complete'], 'release promotion')
    need(GAP in s['remaining_physical_gap_ids'], 'Ring already closed')
    row = next(r for r in b['remaining_conditions'] if r['id']=='NATURAL_CAPTURE_GEAR')
    need(GAP in row['remaining_supply_gap_ids'] and row['selected_supply_entrypoints'][GAP] is None, 'Ring owner changed')
    row['ring_transitive_owner'] = owner.REPORT
    s['ring_transitive_owner'] = {'path':owner.REPORT,'run_id':RUN,'source_head':HEAD,
        'classification':report['classification'],'ring_acquisition_accepted':False}
    stop = ('Ring未解決callee第一段を実装・検証。callstd4は0x08192DA5の8 bytes '
            '6700000000666d03（message0→waitmessage→waitbuttonpress→return）。'
            'Flag/QOL/Save/Trainer/ScriptContextの6入口を有限byte監査した。'
            'FlagSetとSaveFinalizeはpatch済み入口で、sourceだけを見て無副作用と判断してはならない。'
            'QOLDispatchのDAYCARE分岐は入力74/79では非到達だがQOL_FEATURE全体は未除外。'
            'Ring通常取得・全runtime owner不存在は未証明。BP受入run34946969126は不変。')
    s['bp']['current_stop'] = s['source_change_review_ja'] = stop
    s['bp']['next_step'] = s['next_action']['goal_ja'] = NEXT
    s['next_action']['read_paths'] = [owner.REPORT,owner.prior.REPORT,owner.SELF,owner.TEST,
        'overlays/event_design/event_design.c','overlays/qol_production/qol_production.c']
    s['observed_head'] = HEAD
    s['observed_head_semantics'] = '限定byte監査を実行したsource HEAD。最終記録commitはremote refで別途確認する。'
    s['observed_head_checks']['reason_ja'] = ('限定run34960361700/job104352222046はsuccess、34 tests PASS。'
        'Actions全件greenではない。観測した他runはreceiptのactions_observed_before_recordに保存し、failure/action_requiredを成功へ読み替えない。')
    s['session_execution_summary'] = {'new_emulator_processes':0,'rom_changes':0,
        'accepted_standalone_replays':0,'candidate_reconstructions':1,
        'scope_ja':'限定監査1回。記録時再build/nativeなし。追加closureは書込み未反映・未受入であり成果に含めない。通常pushの自動CIは別枠。'}
    note = 'run34960361700の34 tests/callstd4/6入口はsource不変なら再実行しない。patch先の未観測実体と未解決辺だけを進める。BP受入原本は不変。'
    if note not in s['do_not_repeat']:s['do_not_repeat'].append(note)
    return s,b


def check():
    value=validate_receipt(resume.load(ROOT,owner.REPORT))
    state=resume.validate(ROOT);backlog=resume.load(ROOT,resume.BACKLOG)
    need(project(state,backlog,value)==(state,backlog),'record projection differs')
    return value


def prepare(path):
    value=validate_receipt(json.loads(path.read_bytes()))
    need(not (ROOT/owner.REPORT).exists(),'already recorded; do not duplicate')
    state,backlog=project(resume.validate(ROOT),resume.load(ROOT,resume.BACKLOG),value)
    (ROOT/owner.REPORT).write_bytes(owner.stable(value))
    for name in (owner.SELF,owner.TEST,owner.WORKFLOW,owner.REPORT,SELF,TEST,WORKFLOW):
        state['source_bindings'][name]=owner.identity((ROOT/name).read_bytes())
    (ROOT/resume.BACKLOG).write_bytes(owner.stable(backlog))
    (ROOT/resume.STATE).write_bytes(owner.stable(state))
    (ROOT/resume.DOC).write_text(resume.render(state),encoding='utf-8')
    check()


def logs():
    check();tests=json.loads((OUT/'tests.json').read_bytes())
    need(tests['successful'] and tests['tests_run']>0,'record tests failed')
    stamp=datetime.now(timezone.utc).isoformat()
    entry=(f'\n\n## {stamp} — {owner.TASK}\n- Timestamp: {stamp}\n- Task: {owner.TASK}\n'
        '- Status: DONE / 未解決callee第一段の実装・検証・記録。Ring通常取得は未完。\n'
        '- Version: PR16 Ring transitive owner first layer\n'
        '- Summary: callstd4の8 bytesと6 native入口を有限CFG化。未知opcode/不正Thumb/範囲外/重複命令を拒否。間接分岐・memory writeを無副作用やgiver不存在へ昇格しない。FlagSet→0x093775C5、SaveFinalize→0x093BDD7Dのpatched入口を特定。\n'
        f'- Verify: run{RUN}/job{JOB} success、34 tests PASS。記録・固定resume {tests["tests_run"]} tests PASS。read-only resume/task graph/diffと差分guardをcommit前必須gateとする。\n'
        f'- Evidence: {owner.REPORT}; source HEAD={HEAD}; artifact{ARTIFACT}; SHA256={DIGEST}。\n'
        '- Preserved: candidate ceddbe91/CRC3EB17B36、受入BP原本・checkpoint・compiled owner不変。限定候補再構築1、native0、受入済みnative再実行0、ROM変更0。自動push CIは別枠。追加closureコードは書込みブロックで未反映・未受入。\n'
        '- Files changed: 限定監査/helper/tests/workflows、receipt、固定引継ぎMD/JSON、P08 Ring参照、両ログ。\n'
        '- Commit: この記録を含む同branchへの非force commit。自己SHAはremote ref/recorded-resultで確認。\n'
        '- Network: GitHub connector/Actions。ROM/save/private入力の追加なし。既存full guard違反は保持し、前後出力完全一致と追加違反0を要求。全Actions green/merge/release/baseline切替は主張しない。\n'
        '- Next: '+NEXT+'\n')
    for name in previous.LOGS:
        p=ROOT/name;need(owner.TASK not in p.read_text(),'log already recorded')
        with p.open('a',encoding='utf-8') as f:f.write(entry)
    check()


def guard():
    # Use the unchanged repository guard implementation and exact baseline comparison.
    previous.BASE,previous.OUT,previous.ALLOWED=BASE,OUT,ALLOWED
    previous.guard()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','check','logs','guard'))
    p.add_argument('--receipt',type=Path);a=p.parse_args()
    if a.command=='prepare':need(a.receipt is not None,'receipt required');prepare(a.receipt)
    elif a.command=='check':check();print('PASS_TRANSITIVE_FIRST_LAYER_RECORD_NOT_NATIVE_ACCEPTANCE')
    elif a.command=='logs':logs()
    else:guard()
