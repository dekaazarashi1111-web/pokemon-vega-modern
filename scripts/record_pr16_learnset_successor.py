#!/usr/bin/env python3
"""後継表の完了Actionsを受け、記録だけを同branchへ送る。生成/旧試験は呼ばない。"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import pr16_learnset_successor as s
from pr16_resume import STATE, DOC, render

TASK = 'USER-20260921-LEARNSET-BASELINE-RESET'
START = 'd3eaab712e79b0692f1cad51653ba40f1357da6a'
REQUEST = '.github/pr16-learnset-successor-record.json'
CHECKPOINT = s.BASE + 'pr16_learnset_successor_checkpoint.json'
EVIDENCE = s.BASE + 'pr16_learnset_successor_evidence'
GUIDE = 'docs/PR16_LEARNSET_SUCCESSOR_JA.md'
PROOFS = {'verify.json','receipt.json','unit.txt','compact-review.json','source-actions.json',
          'verification-actions.json','table-artifact.json','recording-unit.txt'}
CODE = ('tools/pr16_learnset_successor.py','tests/test_pr16_learnset_successor.py',
        'scripts/pr16_learnset_successor_verify.py','.github/pr16-learnset-successor-local.json',
        '.github/workflows/pr16-learnset-successor.yml')
OWNED = {STATE,DOC,CHECKPOINT,GUIDE,'design/run_log.md','design/version_log.md'} | {EVIDENCE+'/'+n for n in PROOFS}
ALL_CHANGED = OWNED | set(CODE) | {REQUEST,'scripts/record_pr16_learnset_successor.py',
              'tests/test_pr16_learnset_successor_record.py','.github/workflows/pr16-learnset-successor-record.yml'}


def raw_identity(raw: bytes) -> dict:
    return {'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw)}


def check_log(log: str, count: int) -> None:
    s.require(re.findall(r'^Ran (\d+) tests? in ',log,re.M) == [str(count)] and re.search(r'\nOK\s*$',log), '試験証拠未成功')


def validate_report(report: dict, receipt: dict, request: dict, log: str) -> None:
    s.require(report['status'] == 'PASS_SUCCESSOR_TABLES_ONLY', 'scope不一致')
    s.require(report['source_head'] == request['source_head'] and report['run_id'] == request['run_id'], 'HEAD/run不一致')
    s.require(report['focused_tests'] == 39, '新試験数不一致')
    check_log(log,39)
    for key in ('two_process_outputs_identical','readonly_byte_mtime_unchanged',
                'independent_source_row_audit','local_and_actions_output_identical'):
        s.require(report[key] is True, '未完了証拠: '+key)
    for key in ('rom_changes','new_native_runs','accepted_native_reruns','official_baseline_reruns','vega_source_reruns'):
        s.require(type(report[key]) is int and report[key] == 0, 'scope外実行: '+key)
    for source in (report,receipt):
        for key in ('runtime_applied','issue19_complete','release_ready'):
            s.require(source[key] is False, 'runtime/全体完了への昇格禁止')
    s.require(receipt['selected_routes'] == 128288 and report['source_rows_accounted'] == 128447, '原本全数不一致')
    s.require(receipt['official_species'] == 1299 and receipt['vega_species'] == 181, '対象集合不一致')
    s.require(receipt['side_change_excluded'] == 159 and receipt['side_change_species'] == 103
              and receipt['active_side_change'] == receipt['placeholder_rows'] == receipt['owner_overlay_rows'] == 0, '除外/補充境界違反')
    s.require(receipt['vega_nondirect_egg_rows'] == 2394 and receipt['hatch_baseline_membership_gaps'] == 531
              and receipt['vega_nondirect_direct_grants'] == receipt['vega_nondirect_shared_grants'] == 0, '孵化境界違反')
    s.require(report['files'] == receipt['files'] and set(receipt['consumers']) == set(s.CONSUMERS), '出力/consumer集合不一致')


def validate_archive(raw: bytes, artifact: dict, receipt: dict) -> None:
    s.require(raw_identity(raw) == {'size':artifact['size_in_bytes'],'sha256':artifact['digest'].removeprefix('sha256:')}, '表artifact byte不一致')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        s.require(len(names) == len(set(names)) and set(names) == set(receipt['files']) | {'receipt.json'}, '表出力集合不一致')
        s.require(sum(i.file_size for i in archive.infolist()) < 400000000, '表展開上限超過')
        for info in archive.infolist():
            path=PurePosixPath(info.filename)
            s.require(not path.is_absolute() and '..' not in path.parts and '\\' not in info.filename
                      and not stat.S_ISLNK(info.external_attr >> 16), '表artifactの危険path')
            if info.filename == 'receipt.json':
                s.require(archive.read(info) == s.encode(receipt), '表receipt原本不一致')
                continue
            digest=hashlib.sha256();size=0
            with archive.open(info) as stream:
                for block in iter(lambda:stream.read(1048576),b''):
                    digest.update(block);size+=len(block)
            s.require({'size':size,'sha256':digest.hexdigest()} == receipt['files'][info.filename], '表file hash不一致')


def synchronize(state: dict, checkpoint: dict) -> dict:
    s.require('learnset_successor_tables' not in state, '同じ工程の重複記録禁止')
    s.require(not state['pr_merged'] and not state['active_baseline_changed'] and not state['release_ready'], '受入境界不一致')
    result=copy.deepcopy(state)
    goal='Issue19: 検証済み後継9consumer表を再利用し、未選択191枠のSpecies/Form bindingと原作孵化先の新egg差分531行を明示処理してbinary consumer adapterへ接続する。その後に後継ROM・別Wiki・変更影響nativeを限定検証する。'
    result['next_action']={'id':'LEARNSET_SUCCESSOR_BINARY_ADAPTERS','goal_ja':goal,
        'read_paths':[GUIDE,CHECKPOINT,EVIDENCE+'/receipt.json',EVIDENCE+'/compact-review.json',
                      'tools/pr16_learnset_successor.py','docs/PR16_LEARNSET_BASELINE_RESET_JA.md','config/move_port.json'],
        'stop_rule_ja':'後継表・差分の工程は完了、ROM適用は未完。191枠を旧表fallback/一括削除せず、531行をdirect/shared eggへ無断補充しない。原本裁定を未完へ戻さない。Issue19/18完了・merge/releaseへ昇格しない。',
        'host_write_policy_ja':'受入済み公式/Vega原本・旧候補Wiki・ROM/saveは不変。生成物は後継artifactを再利用。consumer接続で影響する最小範囲のみ再検証する。'}
    result['bp']['next_step']=goal
    result['bp']['current_stop']='後継9consumer表128288経路/Side Change除外159行と旧候補1671枠との差分を39新試験・独立2生成・純読取・原本128447行独立監査で検証。孵化参照2394行は保持、direct/shared追加0。新孵化表のmembership差531行を別台帳化。ROM適用0。'
    result.setdefault('observed_head_history',[]).append({'head':state['observed_head'],'semantics':state['observed_head_semantics'],
        'reason_ja':'source裁定受入を保持したまま、後継consumer表の完了証拠へ再開点を更新。'})
    result['observed_head']=checkpoint['source_head']
    result['observed_head_semantics']='後継consumer表検証の完了Actions入力HEAD。branch最新HEADではない。現在HEADはremoteから取得し、記録commitはgit logで確認する。'
    result['observed_date_jst']='2026-09-22'
    result['observed_head_checks'].setdefault('reason_history_ja',[]).append(state['observed_head_checks']['reason_ja'])
    result['observed_head_checks']['reason_ja']=f"後継表run{checkpoint['run_id']}の新39試験、2生成、純読取、全128447原本行保存、ローカル/Actions13出力一致。旧native/原本採取・公式生成を再実行していない。"
    result['learnset_successor_tables']=checkpoint
    result['do_not_repeat'].append('後継9consumer表v1: 128288採用/159明示除外、39新試験、独立2生成・純読取・原本128447行独立監査は保存済み。入力/生成器が同じなら再生成/単独再試験しない。未完は191枠binding/孵化531差分/binary接続と後継ROM・Wiki・影響native。')
    result['remaining_sequence_ja']='原本隔離/裁定済み → 後継9consumer表・旧候補差分検証済み → 未選択Species/Form/孵化差分の明示binding → binary consumer接続 → 後継ROM・別Wiki/影響native → Issue18限定監査 → 別承認release。'
    result['logs_synchronized']=True
    return result


def record() -> None:
    from pr16_vega_original_verify import capture_artifact
    from pr16_wiki_reconcile import fetch
    request=s.read_json(ROOT/REQUEST)
    s.require(request['task'] == TASK, 'task不一致')
    pr=fetch('pulls/16')
    s.require(pr['state']=='open' and pr['draft'] is True and not pr['merged']
              and pr['head']['ref']=='codex/modernization-followup-20260908'
              and pr['head']['sha']==os.environ['GITHUB_SHA'], 'PR/remote HEAD不一致')
    location=ROOT/'.local/pr16-learnset-successor-record/proof'
    actions=capture_artifact(request['verification'],location)
    s.require({p.name for p in location.iterdir()} == PROOFS-{'verification-actions.json','table-artifact.json','recording-unit.txt'}, '小型証拠集合不一致')
    report=s.read_json(location/'verify.json');receipt=s.read_json(location/'receipt.json')
    validate_report(report,receipt,request['verification'],(location/'unit.txt').read_text())
    subprocess.run(['git','diff','--exit-code',report['source_head'],'--',*CODE],cwd=ROOT,check=True)
    for name, ident in report['code'].items():s.bound(ROOT/name,ident)
    for name, ident in receipt['inputs'].items():
        if name not in ('official_baseline.jsonl','official_index.json','owner_approved_overlay.json'):
            s.bound(ROOT/name,ident)
    table=fetch(f"actions/artifacts/{request['tables']['id']}")
    s.require(table['digest']=='sha256:'+request['tables']['sha256'] and table['name']=='pr16-learnset-successor-tables'
              and table['expired'] is False and table['workflow_run']['id']==report['run_id']
              and table['workflow_run']['head_sha']==report['source_head'], '全表artifact binding不一致')
    validate_archive(fetch(f"actions/artifacts/{table['id']}/zip",binary=True),table,receipt)
    review=s.read_json(location/'compact-review.json')
    s.require(len(review['unselected_species'])==191 and len(review['hatch_baseline_membership_gaps'])==531
              and len(review['candidate_diff_summary'])==1671 and review['source_rows_accounted']==128447, '後継差分台帳coverage不一致')
    proofs={p.name:p.read_bytes() for p in location.iterdir()}
    proofs['verification-actions.json']=s.encode(actions)
    proofs['table-artifact.json']=s.encode({k:table[k] for k in ('id','name','digest','size_in_bytes','expires_at','workflow_run')})
    proofs['recording-unit.txt']=(ROOT/'.local/pr16-learnset-successor-record/unit.txt').read_bytes()
    check_log(proofs['recording-unit.txt'].decode(),10)
    checkpoint=dict(report,phase=s.PHASE,status='ACCEPTED_SUCCESSOR_TABLES_ONLY_RUNTIME_PENDING',
        checkpoint_path=CHECKPOINT,evidence_dir=EVIDENCE,task=TASK,
        artifact=actions['artifact'],table_artifact=json.loads(proofs['table-artifact.json']),
        recording_tests=10,recording_run_id=int(os.environ['GITHUB_RUN_ID']),recording_source_head=os.environ['GITHUB_SHA'],
        summary={k:v for k,v in receipt.items() if k not in ('inputs','files','comparison')},
        comparison=receipt['comparison'],proof_bindings={k:raw_identity(v) for k,v in proofs.items()})
    state=s.read_json(ROOT/STATE)
    result=synchronize(state,checkpoint)
    for name in (EVIDENCE,CHECKPOINT,GUIDE):s.require(not (ROOT/name).exists(),'記録先重複: '+name)
    (ROOT/EVIDENCE).mkdir()
    for name,raw in proofs.items():
        raw.decode('utf-8');s.require(b'\0' not in raw,'binary記録禁止')
        (ROOT/EVIDENCE/name).write_bytes(raw)
    (ROOT/CHECKPOINT).write_bytes(s.encode(checkpoint))
    guide=f'''# Issue19 後継learnset表の完了境界とbinary接続再開点

正本は `{CHECKPOINT}`。工程 `{s.PHASE}` は表生成・差分・検証まで完了。実ROMへの接続や実機受入の完了ではない。

## 完了した実装

`tools/pr16_learnset_successor.py` は裁定済み公式1299件118524行、Vega181種9923行、空owner overlayだけを採用し、9consumerを分離する。全128447原本行の方法・条件・順序・ID・form・provenanceを保存し、Side Change159行/103種を別の明示除外台帳へ移す。採用128288行、新技・代替技0。原作TM/TR番号を現在候補のslotと混同せず、現在候補のmachine128/tutor64 slotをmove単位で逆引きする。候補slotがある33321行も互換bitを勝手に付与せず、archive接続が必要な28188行と区別する。

旧候補1671枠の全行を差分へ対応づけた。直接習得のmembership共通88863、旧表のみ11692、新表のみ3872、level列の変更346種。これは方法・条件の完全同値や自然供給の証明ではなく、削除/追加の実ROM適用を表す数でもない。条件付きegg、進化前持越し、姿変更、legacy preservationは直接技へ平坦化しない。

Vega非直接egg2394行は原作の孵化種表へ結合し、直接/shared付与0。公式孵化種に結びつく655行のうち、新しい孵化先direct eggのmembershipにない531行を明示。原本裁定を変更せず、後継adapterが扱うcross-source差分として残す。これは全習得経路で取得不能という判定ではない。

## 検証と再利用

Actions run `{report['run_id']}` / HEAD `{report['source_head']}`。新39試験、seed17/53の独立2生成、check前後のbyte/mtime不変、原本128447行の独立全行監査、ローカル/Actions全13出力一致。生成物はartifact `{table['id']}`、digest `{table['digest']}` に保存。受入済み公式生成/182Wiki再採取/旧native再実行0。約310MiBの全表はtrackedへ複製せず、小型receipt・proof・差分台帳だけを本工程のevidenceへ保存する。

入力/生成器が不変なら、checkpointのartifactを取得してreceiptのSHA/sizeを照合するだけで再開する。期限切れ等で回復が必要なときだけ理由を記録し、固定公式artifactまたは原本ZIPと裁定済みVega入力から再生成する。CLIは `python3 -B tools/pr16_learnset_successor.py generate --official <受入済みoutputs> --output <repository>/.local/<新規出力>`。`check` は同じ引数で純読取。既存出力の上書き、symlink、.local外出力は禁止。

## 次の未完作業

`compact-review.json` の未選択191枠（canonical141/拡張50）に対するSpecies/Form binding、原作孵化先531差分の扱いを原本/所有者方針から明示する。非選択は「全削除」や「旧表fallback」を意味しない。キャタピー旧P03補正も公式1299へ暗黙混入させない。孵化差分を進化後direct/shared eggやowner overlayへ自動追加しない。

その明示bindingを使って既存binary consumerへ接続し、level-up/初期生成/思い出し/進化/持越し/TM・Tutor・archive/egg・shared egg/姿条件の影響範囲を確認する。後継ROMは別候補として生成、旧Wikiを保持した別snapshotと変更影響nativeだけを追加する。既存原本裁定・全nativeの反復は不要。

ROM/ARM/active play baseline変更0、Issue19/18全体未完、PR16 draft/open維持、merge/releaseなし。固定入口CHATGPT_RESUMEには変動進捗を重複記載せず、固定引継ぎMD/JSONを次工程へ同期した。
'''
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    for name in [GUIDE,CHECKPOINT,*[EVIDENCE+'/'+n for n in PROOFS]]:
        result['source_bindings'][name]=s.identity(ROOT/name)
    (ROOT/STATE).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/DOC).write_text(render(result),encoding='utf-8')
    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'''\n\n## {timestamp} — 後継9consumer表・旧候補差分の検証記録
- Timestamp: {timestamp}
- Task: {TASK} / 後継表をbinary接続の直前まで確定
- Version: {s.PHASE}
- Status: DONE（後継表工程。実ROM適用/Issue19全体は未完）
- Summary: 1299公式+181Vegaの128447原本行を全数保存し、128288採用/159明示除外へ分離。孵化2394行のdirect/shared追加0。未選択191枠と孵化先新egg差分531行を台帳化。旧候補/Wikiは不変。
- Files changed: 後継生成器/39試験/独立検証器/限定Actions、記録器/10試験、checkpoint/8証拠/guide、固定引継ぎMD/JSON、両ログ。全13大規模出力はartifact保管。
- Verify: 新39試験、2生成(seed17/53)、純読取byte/mtime不変、128447行独立監査、ローカル/Actions13出力一致（run{report['run_id']}）。記録10試験、pr16_resume.py check、diff/開始HEADからのchanged-final-index guard。原本採取/公式生成/旧native再実行0。
- Commit: 本記録を含むcommit。開始HEAD={START}。検証HEAD={report['source_head']}。途中の実装・試験を同branchへWIP非force反映。
- Network: GitHub connector/Actions。受入公式artifact10641504482を再利用。後継proof/table artifactの完了run/job/全step/digest/全fileを照合。外部Wiki再取得0。
- Boundary: consumer表は実ROM接続済みと表示しない。孵化差分を無断補充せず、旧表をfallbackにも一括削除にも使わない。active baseline/merge/release変更0。
'''
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write(entry)
    print(json.dumps({'status':'RECORDED_TABLES_ONLY','run_id':report['run_id'],'next_action':result['next_action']['id']}))


def guard(base: str) -> None:
    import guard_private_files as private
    s.require(base==START,'開始HEADの変更は禁止')
    git=lambda *args:subprocess.check_output(['git',*args],cwd=ROOT)
    subprocess.run(['git','merge-base','--is-ancestor',base,'HEAD'],cwd=ROOT,check=True)
    paths={p for p in git('diff','--cached','--name-only','-z',base).decode().split('\0') if p}
    s.require(paths==ALL_CHANGED,'変更path集合が過不足: '+str(sorted(paths^ALL_CHANGED)))
    for name in sorted(paths):
        raw=git('show',':'+name);raw.decode('utf-8');s.require(b'\0' not in raw,'binary stage禁止')
        before=subprocess.run(['git','show',base+':'+name],cwd=ROOT,capture_output=True).stdout
        def bad(data):
            lines=data.decode('utf-8',errors='replace').splitlines()
            return Counter(lines[n-1] for n in private.document_user_path_lines(data))
        s.require(not bad(raw)-bad(before),'新規private path違反: '+name)
        if name in ('design/run_log.md','design/version_log.md'):s.require(raw.startswith(before),'append-only違反')
    print(json.dumps({'status':'PASS_CHANGED_FINAL_INDEX','paths':len(paths),'new_violations':0,
                      'full_historical_guard_pass_claimed':False}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('record','guard'))
    parser.add_argument('--base',default=START);args=parser.parse_args()
    record() if args.command=='record' else guard(args.base)
