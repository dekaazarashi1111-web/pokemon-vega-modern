#!/usr/bin/env python3
"""Vega原作採取/監査の完了原本を記録する。採取・生成・nativeは再実行しない。"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.pr16_vega_original_baseline import TASK, identity, require, stable
from pr16_vega_original_verify import capture_artifact
from pr16_resume import STATE, DOC, render

REQUEST = '.github/pr16-vega-original-record.json'
CHECKPOINT = 'content/modernization/pr16_vega_original_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_vega_original_evidence'
GUIDE = 'docs/PR16_VEGA_ORIGINAL_AUDIT_JA.md'
PHASE = 'vega-original-capture-method-audit-20260921'
CODE = ('tools/pr16_vega_original_baseline.py', 'tools/pr16_vega_original_audit.py',
        'scripts/pr16_vega_original_collect.py', 'scripts/pr16_vega_original_verify.py',
        'tests/test_pr16_vega_original_baseline.py', 'tests/test_pr16_vega_original_archive.py',
        'tests/test_pr16_vega_original_audit.py', '.github/pr16-vega-original-audit.json',
        '.github/workflows/pr16-vega-original-baseline.yml', '.github/workflows/pr16-vega-original-audit.yml')
OUTPUTS = {'summary.json','source_lock.json','layout.json','roster.json','vega_original_baseline.jsonl',
           'wiki_methods.jsonl','source_conflicts.json','wiki_nondirect_egg.json','explicit_empty.json','receipt.json'}
PROOFS = {'verify.json','unit.txt','capture-unit.txt','capture-actions.json','audit-actions.json','recording-unit.txt'}


def validate_report(report, request, log):
    require(report['status'] == 'PASS_SOURCE_CAPTURE_AND_METHOD_AUDIT_ONLY' and report['task'] == TASK, '検証scope不一致')
    require(report['verification_head'] == request['source_head'] and report['verification_run_id'] == request['run_id'], '検証HEAD/run不一致')
    require(report['species'] == 181 and report['wiki_pages'] == 182 and report['total_direct_rows'] == 9923, '原本coverage不一致')
    require(report['method_rows'] == {'egg':1790,'level_up':3044,'machine':3549,'tutor':1540}, '方法別coverage不一致')
    require(report['source_conflict_groups'] == 3 and report['wiki_nondirect_egg_species'] == 92
            and report['wiki_nondirect_egg_routes'] == 2394, '差分台帳scope不一致')
    require(report['unknown_moves'] == 0 and report['dex_mismatches'] == 0 and report['focused_tests'] == 43, '未解決identity/試験欠落')
    for name in ('two_process_outputs_identical','readonly_byte_mtime_unchanged','tracked_tree_unchanged','local_and_actions_outputs_identical'):
        require(report[name] is True, '検証未成功: ' + name)
    for name in ('rom_changes','new_native_runs','accepted_native_reruns','official_baseline_reruns','owner_overlay_rows'):
        require(type(report[name]) is int and report[name] == 0, '既受入/原本境界違反')
    for name in ('adoption_ready','issue19_complete','release_ready','side_change_implementation_added'):
        require(report[name] is False, '採用/全体完了への昇格禁止')
    require(re.findall(r'^Ran (\d+) tests? in ', log, re.M) == ['43'] and re.search(r'\nOK\s*$', log), '43試験原本未成功')
    require(set(report['files']) == OUTPUTS, '検証出力集合不一致')


def synchronize(state, checkpoint):
    require('learnset_vega_original' not in state, '記録済み工程の重複は禁止')
    result = copy.deepcopy(state)
    goal = 'Issue19: 保存済みVega原本の3群5行の衝突（リーテイル/ゴートン/ディザソル）を根拠付きで裁定し、92種2394行の進化前等経由eggを原作進化/孵化consumerと照合する。原本の再採取・公式1299件の再生成はしない。'
    result['next_action'] = {'id':'LEARNSET_VEGA_SOURCE_ADJUDICATION','goal_ja':goal,
        'read_paths':[GUIDE,CHECKPOINT,EVIDENCE+'/source_conflicts.json',EVIDENCE+'/wiki_nondirect_egg.json',
                      EVIDENCE+'/source_lock.json','config/move_port.json','docs/PR16_LEARNSET_BASELINE_RESET_JA.md'],
        'stop_rule_ja':'原本衝突の採用判断を未解決のままruntimeへ進めない。Side Changeは所有者決定に従い非採用。旧Wiki/候補ROM/受入原本を保持。Issue19全体は未完。',
        'host_write_policy_ja':'凍結ROM/ZIP/saveは読み取り専用。原本観測9923行とWikiの進化前等経由行は別layer。owner overlayを増やさない。'}
    result['bp']['next_step'] = goal
    result['bp']['current_stop'] = 'Vega181種の原本採取・方法別隔離監査を完了。182ページ/直接9923行、43試験、Actions独立2生成/純読取一致。3群5行の原本衝突と92種2394行の非直接eggを別台帳へ保持し、runtime採用は停止。'
    result.setdefault('observed_head_history', []).append({'head':state['observed_head'],'semantics':state['observed_head_semantics'],
        'reason_ja':'Vega原本監査の完了検証HEADを表示。公式原本/旧Wiki/nativeの各受入HEADは変更しない。'})
    result['observed_head'] = checkpoint['verification_head']
    result['observed_head_semantics'] = 'Vega原本隔離監査の完了Actions入力HEAD。branch最新HEAD/native受入HEADとは別。反映commitはgit log、原本runはlearnset_vega_originalを参照。'
    result['observed_head_checks'].setdefault('reason_history_ja', []).append(state['observed_head_checks']['reason_ja'])
    result['observed_head_checks']['reason_ja'] = '過去native/checksは元scopeのまま保持。新規43試験・独立2生成・純読取はlearnset_vega_originalの完了原本。採用判定とIssue19全体は未完。'
    result['learnset_vega_original'] = checkpoint
    result['do_not_repeat'].append('Vega181種: 採取run35612400716の182ページと固定ROM観測を再利用。コード/原本hash不変なら43試験/二重生成を反復しない。次は3群5行の衝突と92種の原作進化/孵化意味だけ。')
    result['remaining_sequence_ja'] = '公式原本隔離済み → Vega原本採取/方法別隔離監査済み → 原本衝突3群/非直接egg92種の裁定 → Side Change非採用を含むengine例外 → runtime全consumer/後継ROM・Wiki/影響native → Issue18限定監査 → 別承認のrelease。'
    result['logs_synchronized'] = True
    return result


def record():
    request = json.loads((ROOT / REQUEST).read_bytes())
    require(request['task'] == TASK, '記録task不一致')
    verification = request['verification']
    proof = ROOT / '.local/pr16-vega-original-record/input'
    actions = capture_artifact(verification, proof)
    report = json.loads((proof / 'verify.json').read_bytes())
    validate_report(report, verification, (proof / 'unit.txt').read_text())
    subprocess.run(['git','diff','--exit-code',verification['source_head'],'--',*CODE], cwd=ROOT, check=True)
    expected = json.loads((ROOT / '.github/pr16-vega-original-audit.json').read_bytes())['expected_outputs']
    copied = {}
    for name, bound in report['files'].items():
        raw = (proof / 'outputs' / name).read_bytes()
        require(identity(raw) == bound, '出力原本hash不一致: ' + name)
        if name != 'receipt.json':
            require(bound == expected[name], '固定期待出力不一致')
        copied[name] = raw
    receipt = json.loads(copied['receipt.json'])
    for name, bound in receipt['source_identity'].items():
        require(identity((ROOT / name).read_bytes()) == bound, '生成器identity不一致')
    for name in ('verify.json','unit.txt','capture-unit.txt','capture-actions.json'):
        copied[name] = (proof / name).read_bytes()
    recording_log = (ROOT / '.local/pr16-vega-original-record/recording-unit.txt').read_bytes()
    require(re.findall(rb'^Ran (\d+) tests? in ', recording_log, re.M) == [b'10'] and re.search(rb'\nOK\s*$', recording_log), '記録10試験原本未成功')
    copied['recording-unit.txt'] = recording_log
    copied['audit-actions.json'] = stable(actions)
    checkpoint = dict(report, phase=PHASE, evidence_dir=EVIDENCE, status='ACCEPTED_CAPTURE_AND_METHOD_AUDIT_ONLY_ADOPTION_BLOCKED',
                      recording_tests=10, artifact=actions['artifact'], job=actions['job']['id'],
                      proof_bindings={n:identity(raw) for n,raw in copied.items()})
    state = json.loads((ROOT / STATE).read_bytes())
    require(not state['pr_merged'] and not state['active_baseline_changed'], '受入境界変更あり')
    result = synchronize(state, checkpoint)
    destination = ROOT / EVIDENCE
    require(not destination.exists() and not (ROOT / CHECKPOINT).exists(), '記録先を上書きしない')
    destination.mkdir()
    for name, raw in copied.items():
        raw.decode('utf-8'); require(b'\0' not in raw, 'binary記録禁止')
        (destination / name).write_bytes(raw)
    (ROOT / CHECKPOINT).write_bytes(stable(checkpoint))
    guide = f'''# Issue19 Vega原本の採取・方法別隔離監査

工程ID: `{PHASE}`。正本は `{CHECKPOINT}`。これは原本観測と比較の完了であり、Vega baselineのruntime採用・Issue19全体完了ではない。

## 完了した範囲

固定Vega ROM `f600fb3faa565bd335ea75114f9233f9a4fe97c12cfed145e0a7b48784d0c9d5`（16,777,216 bytes）とWiki図鑑入口＋181個別ページをrun `35612400716` で一度だけ採取。全181種のdexNo・Species ID・key一致、未知技0。ページの取得時刻・表示更新版・SHA/size、原作tableのoffset/順序を保持。

直接原本はlevel-up 3044、TM/HM 3549、Tutor 1540、egg 1790、計9923行。TM/HM 58slot/stride8とTutor15slot/stride2は全種照合・予約bit・境界・別stride対照を記録。別表記くらいつく/ねらいうちと同名ID1/511は既存configの固定crosswalkで解決し、IDの追加や置換はしていない。

`vega_original_baseline.jsonl` は凍結ROM観測であり全件HELD。`wiki_methods.jsonl` はWiki原文由来の別layer。進化前等経由の92種2394行は `wiki_nondirect_egg.json` に隔離。直接eggが存在する68種はWikiと一致するが、進化前経由を当該種の直接習得へ複製しない。

## 次の未完作業（採用停止条件）

`source_conflicts.json` の3群5行を根拠付きで裁定する。リーテイルはLv32（原作リーフブレード/Wikiはかいこうせん）とLv46（原作こうごうせい/Wikiじこさいせい）、ゴートンはかみつくの習得レベル（原作18/Wiki20）、ディザソルは原作のTutorギガスパーク/バグノイズがWikiにない。固定ROM優先という出典階層だけで衝突を消したことにせず、版差・誤記根拠または明示判断を台帳へ記録する。次に92種の非直接eggを原作の進化/孵化consumerと照合する。新規採取が必要な場合も欠落している原作進化/孵化範囲だけに限定し、182ページ全体や公式原本を取り直さない。

Side Changeは所有者決定どおり非採用。効果・AI・教え技等を追加しない。削除だけで成立するなら代替不要。今回owner overlay追加0、既存Move ID/効果/歴史は不変。

## 検証と再開

検証run `{verification['run_id']}`、HEAD `{verification['source_head']}` の43試験と独立2生成（hash seed11/29）、実CLI純読取checkでbyte/mtime不変、ローカル期待値一致を完了原本から記録。記録器10境界試験も実施。`{EVIDENCE}` の16証拠とcheckpoint proof_bindingsを参照。採取/検証のActions artifactは30日保存であり、expiryを過ぎて元HTMLが必要なら既存artifact/保存元の有無を先に確認する。trackedのtyped原本・台帳・hashは失わない。

公式1299件/118524経路、旧候補ROM、受入済みnative、旧Wikiは不変。新native/ARM build/ROM変更0、merge/release/active baseline変更なし。受入済み範囲の入力hash不変なら再検証しない。
'''
    require(not (ROOT / GUIDE).exists(), 'guide重複')
    (ROOT / GUIDE).write_text(guide)
    with (ROOT / 'CHATGPT_RESUME.md').open('a') as f:
        f.write('\n\n## Vega181種の原本採取・隔離監査checkpoint\n\n'+f'`{GUIDE}` と `{CHECKPOINT}` を参照。原本9923行/全182ページ/43試験は完了。次工程は3群5行の原本衝突と92種の非直接egg裁定。baseline採用/Issue19全体は未完。保存原本から再開し、公式隔離やWiki全件採取を繰り返さない。\n')
    binding_paths = (*CODE,REQUEST,CHECKPOINT,GUIDE,'CHATGPT_RESUME.md',
                     'scripts/pr16_vega_original_record.py','tests/test_pr16_vega_original_record.py',
                     '.github/workflows/pr16-vega-original-record.yml',*(EVIDENCE+'/'+n for n in copied))
    for name in binding_paths:
        result['source_bindings'][name] = identity((ROOT / name).read_bytes())
    (ROOT / STATE).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (ROOT / DOC).write_text(render(result))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry = f'''\n\n## {now} — Vega原作採取・方法別隔離監査完了
- Task: {TASK}
- Version: {PHASE}
- Status: DONE（原本観測/監査の区切りのみ。採用BLOCKED、Issue19全体未完）
- Summary: 181種/182ページ/直接9923行を分離。dex/key差分0・未知move0。3群5行の原本衝突と92種2394行の非直接eggを全件台帳へ。固定crosswalkのみ使用しowner overlay追加0。
- Files changed: 原作専用reader/採取器/方法別監査器/43試験/限定Actions、typed原本/差分/完了証拠、専用guide/checkpoint、固定入口と引継ぎMD/JSON、両ログ。
- Verify: 43境界試験・Actions独立2生成/実CLI純読取byte-mtime不変・ローカル期待hash一致。記録10境界試験、resume/task-graph/diff/changed-final-index guard。既受入official/native再実行0。
- Commit: 本記録を含むcommit。検証HEAD={verification['source_head']}。採取HEAD=9a5cb4172571bfed953c54155c030ef73c845542。
- Network: GitHub connector/Actions。採取run35612400716、検証run{verification['run_id']}、両完了job/全step/artifact digestを照合。Wiki採取1回（https://w.atwiki.jp/altair1/pages/19.html とsource_lockの181個別URL）、後続比較は保存原本のみ。
- Boundary: 原本衝突の片側を推測で採用しない。Side Change非採用を維持。ROM/ARM/native変更0、旧Wiki・候補・active baseline不変、merge/releaseなし。
'''
    for name in ('design/run_log.md','design/version_log.md'):
        require(PHASE not in (ROOT / name).read_text(), 'ログ二重追記禁止')
        with (ROOT / name).open('a') as f: f.write(entry)
    print(json.dumps({'status':checkpoint['status'],'proofs':len(copied),'next_action':result['next_action']['id']},sort_keys=True))


def guard(base):
    import guard_private_files as private
    require(re.fullmatch('[0-9a-f]{40}',base), 'base不正')
    git = lambda *a: subprocess.check_output(['git',*a],cwd=ROOT)
    paths = [p for p in git('diff','--cached','--name-only','-z',base).decode().split('\0') if p]
    allowed = {STATE,DOC,CHECKPOINT,GUIDE,'CHATGPT_RESUME.md','design/run_log.md','design/version_log.md'} | {EVIDENCE+'/'+n for n in OUTPUTS|PROOFS}
    require(set(paths) == allowed, '記録path集合が過不足')
    for name in paths:
        data = git('show',':'+name); data.decode('utf-8'); require(b'\0' not in data,'binary stage禁止')
        before = subprocess.run(['git','show',base+':'+name],cwd=ROOT,capture_output=True).stdout
        def bad(raw):
            lines = raw.decode('utf-8',errors='replace').splitlines()
            return Counter(lines[n-1] for n in private.document_user_path_lines(raw))
        require(not bad(data)-bad(before),'新規private path違反: '+name)
        if name in ('design/run_log.md','design/version_log.md'):
            require(data.startswith(before),'append-only違反')
    print(json.dumps({'status':'PASS_CHANGED_FINAL_INDEX','paths':len(paths),'new_violations':0,'full_historical_guard_pass_claimed':False}))

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['record','guard']);p.add_argument('--base');a=p.parse_args()
    if a.command=='record': record()
    else: guard(a.base)
