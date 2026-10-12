#!/usr/bin/env python3
"""完了済み裁定artifactだけを記録する。原本採取・生成・nativeは再実行しない。"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.pr16_vega_original_baseline import TASK, identity, require, stable
from pr16_vega_original_verify import capture_artifact
from pr16_resume import STATE, DOC, render
from pr16_wiki_reconcile import fetch

REQUEST = '.github/pr16-vega-adjudication-record.json'
PHASE = 'vega-source-adjudication-20260922'
CHECKPOINT = 'content/modernization/pr16_vega_adjudication_checkpoint.json'
OUTPUT = 'content/modernization/pr16_vega_adjudication'
EVIDENCE = 'content/modernization/pr16_vega_breeding_evidence'
GUIDE = 'docs/PR16_VEGA_SOURCE_ADJUDICATION_JA.md'
OUTPUTS = {'source_collisions.json','adopted_vega_original_baseline.jsonl','nondirect_egg.jsonl','breeding_families.json','receipt.json'}
PROOFS = {'original-breeding.json','consumer-disassembly.txt','source-actions.json','verify.json','unit.txt',
          'audit-actions.json','collision-unit.txt','collision-actions.json','recording-unit.txt'}
CODE = ('tools/pr16_vega_adjudication.py','tools/pr16_vega_breeding.py','tests/test_pr16_vega_adjudication.py',
        'tests/test_pr16_vega_breeding.py','scripts/pr16_vega_breeding_collect.py',
        '.github/workflows/pr16-vega-adjudication.yml','.github/workflows/pr16-vega-breeding-source.yml',
        '.github/workflows/pr16-vega-breeding-audit.yml')
REPAIRS = {
 'CHATGPT_RESUME.md': ({'size':6124,'sha256':'8d027f0c3f5e65b756c2ce3455d01b33bb0101f21b3dce7ddc0143c13ac0cc79'},
                     {'size':7485,'sha256':'dedd8ac7713cd742582d52be81e2e12ec311028e071639cc905f90a41be0b230'}),
 'docs/PR16_VEGA_ORIGINAL_AUDIT_JA.md': ({'size':3157,'sha256':'b455278ce23cd9c7e33283bbb5d3636a18a2d816411596f6809eccfd20888083'},
                     {'size':4410,'sha256':'b9ee1dd32da36d9fe3d04aa1663afa0f2e6cc37aef491437dd2443a5870fb2d4'})}


def check_log(log, count):
    require(re.findall(r'^Ran (\d+) tests? in ',log,re.M) == [str(count)] and re.search(r'\nOK\s*$',log), '試験原本未成功')


def validate_report(report, request, log):
    require(report['status'] == 'PASS_SOURCE_ADJUDICATION_ONLY', '検証scope不一致')
    require(report['verification_head'] == request['source_head'] and report['verification_run_id'] == request['run_id'], '検証HEAD/run不一致')
    require(report['focused_tests'] == 13, '試験数不一致')
    check_log(log,13)
    for key in ('two_process_outputs_identical','readonly_byte_mtime_unchanged'):
        require(report[key] is True, '検証未成功')
    for key in ('rom_changes','new_native_runs','accepted_native_reruns','official_baseline_reruns','wiki_pages_fetched'):
        require(type(report[key]) is int and report[key] == 0, '既受入/原本境界違反')
    for key in ('runtime_applied','issue19_complete','release_ready'):
        require(report[key] is False, '全体完了への昇格禁止')
    require(set(report['files']) == OUTPUTS, '出力集合不一致')
    require(report['reused_collision_tests'] == {'run_id':35621880869,'head':'c8af78b793c554d43230cddeab5ce33ae515a742','tests':5}, '衝突試験の再利用原本不一致')


def validate_summary(summary):
    expected = {'species':92,'rows':2394,'pre_evolution_egg_rows':2394,'receiver_direct_egg_rows_added':0,
                'shared_egg_rows_added':0,'reference_only_rows':0,'unresolved_rows':0,'original_consumer_species_checked':411}
    require(all(type(summary.get(k)) is int and summary[k] == v for k,v in expected.items()), '裁定coverage不一致')
    require(summary['note_scopes'] == {'HATCH_BASE_REFERENCE':2336,'SAME_FAMILY_INTERMEDIATE_REFERENCE':57,'NO_BREEDING_NOTE':1}, '親注記分類不一致')
    for key in ('runtime_applied','physical_donor_chain_verified','issue19_complete','release_ready'):
        require(summary[key] is False, '静的照合から実機受入への昇格禁止')


def repaired_binding(name, previous, raw):
    old, new = REPAIRS[name]
    require(previous == old and identity(raw) == new, '開始時文書hash修復のscope外')
    return new


def synchronize(state, checkpoint):
    require('learnset_vega_adjudication' not in state, '記録済み工程の重複は禁止')
    require(not state['pr_merged'] and not state['active_baseline_changed'] and not state['release_ready'], '受入境界変更あり')
    result = copy.deepcopy(state)
    goal = 'Issue19: 裁定済み公式1299件/Vega181種/空owner overlayを入力にruntime全consumer用の後継表と旧候補差分を実装する。Side Change非採用の明示disposition、方法/条件/順序、原作孵化種のeggを保持し、影響範囲だけ後継ROM・Wiki・nativeで検証する。'
    result['next_action'] = {'id':'LEARNSET_RUNTIME_BASELINE_APPLICATION','goal_ja':goal,
        'read_paths':[GUIDE,CHECKPOINT,OUTPUT+'/receipt.json','content/modernization/pr16_learnset_baseline_checkpoint.json',
                      'content/modernization/pr16_learnset_baseline_evidence/receipt.json',
                      'docs/PR16_LEARNSET_BASELINE_RESET_JA.md','config/move_port.json'],
        'stop_rule_ja':'原本裁定は完了。runtime実装・全consumer/Side Change除外/後継Wiki/影響nativeは未完。旧CURRENT_PRESERVED/PRESERVE_V3等を検証済み新baselineと混同しない。Issue19/18全体・merge/releaseへ昇格しない。',
        'host_write_policy_ja':'凍結ROM/ZIP/save、旧Wiki・候補・受入原本は不変。非直接egg2394行を進化後のdirect/shared eggへ複製しない。親個体の自然入手/全交配の実機証明は今回のscope外。'}
    result['bp']['next_step'] = goal
    result['bp']['current_stop'] = '所有者決定の原本衝突3群5行と非直接egg92種2394行の裁定を完了。原作411種の孵化探索順・直接egg表に静的照合。新13試験と独立2生成/純読取PASS、衝突5試験は受入原本を再利用。直接9923行・元Wiki行を保持し、runtime反映0。'
    result.setdefault('observed_head_history',[]).append({'head':state['observed_head'],'semantics':state['observed_head_semantics'],
        'reason_ja':'原本採取から裁定済み後継証拠へ再開点を更新。旧受入scopeは変更しない。'})
    result['observed_head'] = checkpoint['verification_head']
    result['observed_head_semantics'] = 'Vega原本衝突/非直接egg裁定の完了Actions入力HEAD。branch最新HEADとは別。現在HEADはremoteから取得し、反映commitはgit logで確認する。'
    result['observed_date_jst'] = '2026-09-22'
    result['observed_head_checks'].setdefault('reason_history_ja',[]).append(state['observed_head_checks']['reason_ja'])
    result['observed_head_checks']['reason_ja'] = '裁定run35623180576の13試験/2生成/純読取PASS。衝突run35621880869の5試験を再利用。既存native/checksは元scopeのまま。'
    result['learnset_vega_adjudication'] = checkpoint
    result['do_not_repeat'] = [x for x in result['do_not_repeat'] if not x.startswith('Vega181種: 採取run35612400716')]
    result['do_not_repeat'].append('Vega181種: 原本9923行/182ページ/43試験、衝突5行/5試験、非直接egg2394行/13試験は保存証拠を再利用。原本採取・公式1299件の再生成・入力不変の単独再検証をしない。3群/92種を未裁定へ戻さず、次はruntime全consumer。')
    result['remaining_sequence_ja'] = '公式原本隔離済み → Vega原本採取/方法別隔離監査済み → 衝突3群5行/非直接egg92種2394行の裁定済み → Side Change非採用等のruntime明示処理 → 後継ROM・Wiki/影響native → Issue18限定監査 → 別承認のrelease。'
    result['logs_synchronized'] = True
    return result


def record():
    request = json.loads((ROOT/REQUEST).read_bytes())
    require(request['task'] == TASK, '記録task不一致')
    pr = fetch('pulls/16')
    require(pr['state'] == 'open' and pr['draft'] is True and not pr['merged'] and pr['head']['sha'] == os.environ['GITHUB_SHA'], 'PR/remote HEAD不一致')
    proof = ROOT/'.local/pr16-vega-adjudication-record/input'
    actions = capture_artifact(request['verification'],proof)
    report = json.loads((proof/'verify.json').read_bytes())
    validate_report(report,request['verification'],(proof/'unit.txt').read_text())
    subprocess.run(['git','diff','--exit-code',request['verification']['source_head'],'--',*CODE],cwd=ROOT,check=True)
    copied = {}
    require(set(request['expected_outputs']) == OUTPUTS, '期待出力集合不一致')
    for name in OUTPUTS:
        raw = (proof/'generated'/name).read_bytes()
        require(identity(raw) == report['files'][name] == request['expected_outputs'][name], '出力原本hash不一致: '+name)
        copied[name] = raw
    receipt = json.loads(copied['receipt.json'])
    validate_summary(receipt['summary'])
    for name, bound in receipt['code'].items():
        require(identity((ROOT/name).read_bytes()) == bound, '生成器identity不一致')
    require(receipt['outputs'] == {n:report['files'][n] for n in OUTPUTS-{'receipt.json'}}, 'receipt出力不一致')
    from tools import pr16_vega_breeding as breeding
    breeding.original_guard(ROOT)  # hash/sizeのみ。原本再採取・生成・13試験を呼ばない。
    require(identity((proof/'source/original-breeding.json').read_bytes())['sha256'] == breeding.SOURCE_SHA, '進化孵化原本不一致')
    original = json.loads((proof/'source/original-breeding.json').read_bytes())
    require(identity((proof/'source/consumer-disassembly.txt').read_bytes()) == original['disassembly_identity'], 'consumer証拠不一致')
    previous = ROOT/'.local/pr16-vega-adjudication-record/collision'
    collision_actions = capture_artifact(request['collision'],previous)
    check_log((previous/'unit.txt').read_text(),5)
    for name in ('source_collisions.json','adopted_vega_original_baseline.jsonl'):
        require((previous/'generated'/name).read_bytes() == copied[name], '受入衝突出力との不一致')
    proofs = {name:(proof/'source'/name).read_bytes() for name in ('original-breeding.json','consumer-disassembly.txt','source-actions.json')}
    proofs.update({name:(proof/name).read_bytes() for name in ('verify.json','unit.txt')})
    proofs['audit-actions.json'] = stable(actions)
    proofs['collision-actions.json'] = stable(collision_actions)
    proofs['collision-unit.txt'] = (previous/'unit.txt').read_bytes()
    proofs['recording-unit.txt'] = (ROOT/'.local/pr16-vega-adjudication-record/recording-unit.txt').read_bytes()
    check_log(proofs['recording-unit.txt'].decode(),12)
    checkpoint = dict(report,phase=PHASE,task=TASK,status='ACCEPTED_SOURCE_ADJUDICATION_ONLY_RUNTIME_PENDING',
        recording_tests=12,recording_run_id=int(os.environ['GITHUB_RUN_ID']),recording_source_head=os.environ['GITHUB_SHA'],checkpoint_path=CHECKPOINT,evidence_dir=EVIDENCE,output_dir=OUTPUT,
        artifact=actions['artifact'],job_id=actions['job']['id'],summary=receipt['summary'],
        source_conflict_groups_resolved=3,source_conflict_rows_adjudicated=5,unselected_wiki_rows=3,
        owner_overlay_rows_added=0,source_conflicts_original_unchanged=True,
        physical_donor_chain_verified=False,proof_bindings={n:identity(raw) for n,raw in proofs.items()})
    state = json.loads((ROOT/STATE).read_bytes())
    result = synchronize(state,checkpoint)
    for name in (OUTPUT,EVIDENCE,CHECKPOINT,GUIDE):
        require(not (ROOT/name).exists(), '記録先の重複は禁止: '+name)
    for name,(old,new) in REPAIRS.items():
        raw = (ROOT/name).read_bytes()
        result['source_bindings'][name] = repaired_binding(name,result['source_bindings'][name],raw)
        require(subprocess.check_output(['git','show','df0526687af875a6bc589cb8931a6d083b44aa08:'+name],cwd=ROOT) == raw, '開始HEADの本文から変更あり')
        result.setdefault('source_binding_repairs',[]).append({'path':name,'previous':old,'current':new,'content_changed':False,
            'reason_ja':'開始HEAD df052668の所有者決定追記に旧bindingが未追随。本文byte一致を確認しmetadataのみ同期。'})
    for directory, files in ((OUTPUT,copied),(EVIDENCE,proofs)):
        (ROOT/directory).mkdir()
        for name, raw in files.items():
            raw.decode('utf-8');require(b'\0' not in raw,'binary記録禁止')
            (ROOT/directory/name).write_bytes(raw)
    (ROOT/CHECKPOINT).write_bytes(stable(checkpoint))
    guide = f'''# Issue19 Vega原本の裁定完了とruntime再開点

工程 `{PHASE}`。正本は `{CHECKPOINT}`。原本採取の旧checkpointは履歴のまま保持し、本書と固定引継ぎの次工程を優先する。

## 完了した実装

所有者決定 `VEGA_ORIGINAL_SOURCE_PRIORITY_20260921` により固定ROMを採用。リーテイルのLv32リーフブレード/Lv46こうごうせい、ディザソルのTutorギガスパーク/バグノイズ、ゴートンのLv18かみつく、計3群5行を別台帳へ記録。不採用Wiki3行とWiki側にないTutor2行の根拠、元順序/offset/版/hashを残す。raw `source_conflicts.json` は改変しない。

`{OUTPUT}/adopted_vega_original_baseline.jsonl` は181種9923行の原作methodをそのまま保持したsource裁定済みprojectionであり、runtime入力への接続は未実施。

非直接egg92種2394行はすべて原作進化前の孵化種direct eggに存在し、`PRE_EVOLUTION_EGG` に分類。受取種へのdirect egg追加0、shared egg追加0、未解決0。元Wiki行・親注記7571件はそのまま保存。注記の分類は孵化種参照2336行/中間種参照57行/注記なし1行（カミギリー・よこどり）。注記欠落を補作しない。種名だけの注記も交配矢印へ変造しない。

原作進化表412枠/225非zero slot（target0の原文も保持）、egg147種3867行を不足範囲だけ追加採取。GetEggSpeciesのspecies1..411/5slot/first-match/最大5遡行、GetEggMovesのmarker/走査上限/50技容量に保存bytesを照合。独立走査と逆引き経路を全411種で比較した。GetEggMoves自身は孵化種へ変換しないため、進化後の種に直接eggを複製してはいけない。

## 証明の境界

これは原作表・固定consumer bytesの静的照合であり、親個体の自然入手、全交配手順、進化後の技保持のnative実行証明ではない。実機受入済みと表示しない。owner overlay追加0、ROM/ARM/new native変更0。公式1299件/118524経路、旧候補・Wiki・native原本を変更しない。Side Change非採用を維持し、効果/AI/新技は追加しない。

## 検証済み証拠と再実行防止

衝突5試験はrun35621880869（c8af78b7）の成功原本を再利用。欠落範囲だけの採取run35622433529（3da7acfe）、裁定13試験run35623180576（04b8ea96）、hash seed17/53の独立2生成、実CLI純読取byte/mtime不変、ローカルとActionsの全5出力一致を記録。記録器12境界試験とresume/最終index guardは今回の変更影響だけを検査する。完了artifactのID/digest/HEAD/job/全stepは証拠JSONへ保存。期限後もtrackedの全typed出力/consumer証拠/試験ログから再開できる。

入力変更のない受入済み5/13/43試験、182ページ採取、公式原本生成、nativeを反復しない。変更時の純読取入口は `python3 -B tools/pr16_vega_breeding.py check`。生成は明示 `generate` のみで、checkは修復しない。

## 次の未完作業

公式1299件と裁定済みVega181種と空owner overlayをruntime全consumerへ接続する後継生成器、既存候補との差分台帳、後継ROM/Wiki/影響nativeが次の区切り。raw方法別順序・条件・原本TM/TR番号とruntime slotの区別、原作孵化種direct eggを守る。旧CURRENT_PRESERVED/PRESERVE_V3/schemaV4等の履歴を新baseline受入根拠にしない。Side Change159経路/103種は証拠から削除せずactive除外を明示。除外だけで成立するなら補充不要、所有者が条件付きで許可したlevel-up仮技が必要な時だけstable key/IDを現行manifestで解決しcrosswalkを残す。Issue19全体/Issue18/merge/release/active baseline変更は未完・未承認のまま。
'''
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    binding_paths = (*CODE,REQUEST,CHECKPOINT,GUIDE,'scripts/pr16_vega_adjudication_record.py',
        'tests/test_pr16_vega_adjudication_record.py','.github/workflows/pr16-vega-adjudication-record.yml',
        *(OUTPUT+'/'+n for n in copied),*(EVIDENCE+'/'+n for n in proofs))
    for name in binding_paths: result['source_bindings'][name] = identity((ROOT/name).read_bytes())
    (ROOT/STATE).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/DOC).write_text(render(result),encoding='utf-8')
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry = f'''\n\n## {now} — Vega原本衝突・非直接egg裁定完了
- Task: {TASK}
- Version: {PHASE}
- Status: DONE（source裁定の区切り。runtime適用0、Issue19全体未完）
- Summary: 所有者ROM優先の3群5行を別台帳で裁定。92種2394行を原作孵化種direct eggへ結合。原本9923行・Wiki行/親注記保持、direct/shared追加0、未解決0、owner overlay追加0。
- Files changed: 裁定器2本/試験/不足範囲採取器/限定Actions、裁定5出力/9証拠、後継checkpoint/guide、固定引継ぎMD/JSON、両ログ。元source_conflicts/旧checkpoint/公式/native受入原本は不変。
- Verify: collision5試験run35621880869を再利用、新13試験run35623180576、独立2生成(seed17/53)・純読取byte/mtime不変・ローカル/Actions全出力一致。記録12試験、pr16_resume.py check、diff/changed-final-index guard。採取/native/公式生成の再実行なし。
- Commit: 本記録を含むcommit。検証HEAD=04b8ea96ac7244fd0940e9f9075026198869cdf4。開始HEAD=df0526687af875a6bc589cb8931a6d083b44aa08。途中c8af78b7/3da7acfe/04b8ea96を同branchへ非force反映。
- Network: GitHub connector/Actions。欠落進化/孵化範囲の採取run35622433529のみ追加。完了Actions/全step/artifact digest照合、182ページ再取得0。記録run={os.environ.get('GITHUB_RUN_ID')}。
- Repair: 開始HEADから未同期のCHATGPT_RESUME/旧Vega監査guideのbinding2件を本文byte不変確認後metadataだけ同期。新しい再開点は固定MD/JSONから後継guideへ。旧歴史は削除しない。
- Boundary: 原作411種の静的consumer照合であり自然交配/native受入ではない。Side Change効果/AI追加0、ROM/ARM/active baseline変更0、PR16 draft/openのまま、merge/releaseなし。次はruntime全consumer/後継ROM・Wiki/影響native。
'''
    for name in ('design/run_log.md','design/version_log.md'):
        require(PHASE not in (ROOT/name).read_text(), 'ログ二重追記禁止')
        with (ROOT/name).open('a',encoding='utf-8') as f: f.write(entry)
    print(json.dumps({'status':checkpoint['status'],'next_action':result['next_action']['id'],'outputs':len(copied),'proofs':len(proofs)}))


def guard(base):
    import guard_private_files as private
    require(re.fullmatch('[0-9a-f]{40}',base), 'base不正')
    git = lambda *args: subprocess.check_output(['git',*args],cwd=ROOT)
    paths = [p for p in git('diff','--cached','--name-only','-z',base).decode().split('\0') if p]
    allowed = {STATE,DOC,CHECKPOINT,GUIDE,'design/run_log.md','design/version_log.md'} | {OUTPUT+'/'+n for n in OUTPUTS} | {EVIDENCE+'/'+n for n in PROOFS}
    require(set(paths) == allowed, '記録path集合が過不足')
    for name in paths:
        raw = git('show',':'+name);raw.decode('utf-8');require(b'\0' not in raw,'binary stage禁止')
        before = subprocess.run(['git','show',base+':'+name],cwd=ROOT,capture_output=True).stdout
        def bad(data):
            lines = data.decode('utf-8',errors='replace').splitlines()
            return Counter(lines[n-1] for n in private.document_user_path_lines(data))
        require(not bad(raw)-bad(before), '新規private path違反: '+name)
        if name in ('design/run_log.md','design/version_log.md'): require(raw.startswith(before),'append-only違反')
    print(json.dumps({'status':'PASS_CHANGED_FINAL_INDEX','paths':len(paths),'new_violations':0,'full_historical_guard_pass_claimed':False}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['record','guard']);parser.add_argument('--base');args=parser.parse_args()
    if args.command == 'record': record()
    else: guard(args.base)
