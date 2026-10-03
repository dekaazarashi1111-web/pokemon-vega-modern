#!/usr/bin/env python3
"""独立窓/純粋入力/枠タイル修正後だけ実測。以前の失敗を保存して判定を緩めない。"""
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_standard_list_actions as a
import pr16_research_counter_accept as archive
import pr16_research_lifecycle_actions as d
import pr16_research_standard_list as s
BUILD_RUN=36312100158
WORKFLOW_HEAD='597673e7f4163a063593a1157a8f51a4236c3cdd'
BUILD_HEAD='ad9b61026eeec84431c43d5cdd493e421ce3cc83'
BUILD_ART=10929104210
BUILD_BIND={'size':11806,'sha256':'a60e9d87322801b0eca921b0d249fad417a140e5bdf48f05f05fa025e568f267'}
CANDIDATE={'size':33554432,'sha256':'59ac6688576238f00dac88cccec1a42415f6f0e4f3f07d60411f6d3059bf61e6'}
SELF='scripts/pr16_research_standard_list_ui_actions.py'
OLD=[('content/modernization/pr16_research_standard_list_checkpoint.json',36311122801,'a06f61d9ed78061d59f2b7cb681efdfe55d3daaa'),
     ('content/modernization/pr16_research_standard_list_thumb_checkpoint.json',36311562940,'995e87e0e38c167f52c1ed2feeca6324fe6e017b')]
a.CP='content/modernization/pr16_research_standard_list_ui_checkpoint.json'
a.RECIPE='content/modernization/pr16_research_standard_list_ui_recipe.json'
a.BASE='content/modernization/pr16_research_standard_list_ui_evidence'
a.OUT=ROOT/'.local/pr16-standard-list-ui-native';a.PUBLIC=a.OUT/'public'
a.CODE|={SELF,'tests/test_pr16_research_standard_list_thumb.py','scripts/pr16_research_standard_list_thumb_actions.py',
         'content/modernization/pr16_research_standard_list_ui_edits.json'}
a.PROTECTED|={p for p,_,_ in OLD}|{p.replace('_checkpoint.json','_recipe.json') for p,_,_ in OLD}
a.BUILD_RUN=BUILD_RUN;a.BUILD_HEAD=BUILD_HEAD;a.BUILD_ART=BUILD_ART;a.BUILD_BIND=BUILD_BIND
a.oracle.CANDIDATE=CANDIDATE


def build_reuse():
    run=d.inputs.api('actions/runs/'+str(BUILD_RUN))
    s.need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==WORKFLOW_HEAD,'UI correction build terminal')
    data,meta=archive.archive(BUILD_ART,BUILD_BIND['size'],BUILD_BIND['sha256'],15,34805,BUILD_RUN)
    build=a.oracle.load(data['build.json']);receipt=a.oracle.load(data['source-commit.json'])
    s.need(build['source_head']==receipt['source_head']==BUILD_HEAD and build['workflow_head']==receipt['workflow_head']==WORKFLOW_HEAD
           and build['run_id']==BUILD_RUN and receipt['non_force_push_confirmed'] is True,'build from exact non-force source checkpoint')
    for name,b in build['source_bindings'].items():s.need(s.identity((ROOT/name).read_bytes())==b,'unchanged UI source '+name)
    s.need(s.audit_thumb_symbols(data['arm/menu.elf'])==build['thumb_symbols'] and len(build['thumb_symbols'])==18,'18 actual Thumb function symbols')
    for label,count in [('host',18),('thumb',8)]:
        s.need(data[label+'.stderr.txt'].count(b' ... ok\n')==count and b'\nOK\n' in data[label+'.stderr.txt']
               and not data[label+'.stdout.txt'],'saved affected tests '+label)
    previous=[]
    for path,rid,head in OLD:
        prior=d.inputs.api('actions/runs/'+str(rid));cp=d.read(ROOT/path)
        s.need(prior['status']=='completed' and prior['conclusion']=='failure' and prior['head_sha']==head
               and cp['run_id']==rid and cp['standard_list_accepted'] is False,'unaccepted native failure remains immutable')
        previous.append({'run':d.run_summary(prior),'checkpoint':path,'binding':s.identity((ROOT/path).read_bytes())})
    for name,b in data.items():
        if Path(name).suffix not in ('.json','.txt','.S','.ld','.h'):continue
        dest=a.PUBLIC/'build'/name
        if dest.suffix in ('.S','.ld','.h'):dest=dest.with_suffix(dest.suffix+'.txt')
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
    d.write(a.PUBLIC/'build-reuse.json',dict(run=d.run_summary(run),artifact=meta,archive=BUILD_BIND,
        source_head=BUILD_HEAD,reused_arm_compiles=1,reused_host_tests=18,reused_thumb_tests=8,
        reused_event_tests=14,event_test_run=36310534280,new_arm_compiles=0,new_host_test_executions=0,
        original_native_failures=previous,oracle_weakened=False))
    return bytes.fromhex(build['code_hex']),build


def record():
    a.record()
    cp=d.read(ROOT/a.CP);recipe=d.read(ROOT/a.RECIPE)
    cp.update(supersedes_failed_checkpoints=[p for p,_,_ in OLD],failed_original_native_runs=[rid for _,rid,_ in OLD],
              candidate_binding_source=SELF,reused_event_tests=14,reused_event_test_run=36310534280,
              ui_repairs=['pure input does not delete shared yes/no dialogue window','separate 0x280 pixel tiles and 0x214 user frame tiles','18 typed Thumb delegates'],
              strict_oracle_unchanged=True)
    cp['reused_build'].update(source_head=BUILD_HEAD,workflow_head=WORKFLOW_HEAD,tests=26,host_tests=18,thumb_tests=8,thumb_delegate_count=18)
    d.write(ROOT/a.CP,cp)
    text=f'''# PR16 受付STANDARD_LIST\n\nTask: `{a.TASK}`\n\n## 現在地\n\n`{cp['status']}`。source `{cp['source_head']}` / run `{cp['run_id']}`。正本は `{a.CP}` と `{a.RECIPE}`。自己run終端と22実画面の視認前に正式受入へ昇格しない。\n\n## 実装\n\n固定c3971e83の後処理層。受付local4 script pointerと未参照FF領域0x09F4A800/2048byteだけを変更。新候補 `{CANDIDATE['sha256']}`。独立Thumbコード{recipe['build']['code']['size']}byte、イベント212byte、実差分{recipe['changed_bytes']}byte、全ROM rollback一致。既存数値script/text、canonical、研究owner/volatile不変、新EWRAM0。\n\n「ポイントとランク」「ポイントのあつめかた」「おわる」、B取消、両機能からlistへ戻る、3訪問の入力と資源解放を検査。全てstock task/window/menu APIを使い、taskだけが自分のwindowを一度解放。window pixelsは0x280..0x2f7、選択したユーザ枠は0x214..0x21c。ELFの18 delegateはSTT_FUNC/Thumbで型付けする。\n\n## 過去の不具合と変更影響\n\nrun36310336114の暗黙memcpyリンク失敗、run36311122801の誤ったARM/Thumb veneer、run36311562940の会話窓消失と枠破損を原本のまま保持。後者のnative終了0/警告0だけでは受入できなかった。0x08110BF9は純粋入力でなくshared yes/no windowも削除するwrapperだったため、0x08110539へ接続を修正。0x080F89CDが返す0x214は枠タイルであり、文字タイルの確保に流用しない。元の厳格window再訪/解放oracleは変更していない。\n\n既存canonical overlayにも同じ入力/枠APIの使用があるため、次の自然稼得RP→shop支出ではその実ウィンドウ所有関係を先に確認する。本タスクでは旧shopや受入済み数値境界のコード・結果を改作しない。\n\n## 検証\n\nrun{BUILD_RUN}の変更影響host18件・ELF8件・ARM生成を再利用。イベント14件は完全不変を照合してrun36310534280を再利用。今回の新nativeは起動前0RP fixture、屋外prefix以降key入力だけ。3訪問、機能2行、B取消2回、終了行1回、22画面。新oracle27件を同じ原本に対して陽性前提付きで検査する。実績件数/失敗はcheckpointと原本が優先。旧数値2境界/旧4入口/旧稼得/BP/P08受入ケースの再実行0。\n\n## 次の独立境界\n\nこのlistの22画面とrun終端を照合後、自然稼得RP→ショップ支出と通常ストーリー進行へ進む。今回はRP注入なしだが初期map/party/progressionはfixtureであり、自然到達・自然稼得支出は未受入。merge/release/baseline変更は禁止。\n'''
    (ROOT/a.GUIDE).write_text(text,encoding='utf-8')
    state=d.read(ROOT/d.STATE)
    for path in (a.CP,a.GUIDE):state['source_bindings'][path]=s.identity((ROOT/path).read_bytes())
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    note=f'\n- UI repair scope correction: 共通recordのARM/30試験表記を最新実績で限定訂正。ARMとhost18/ELF8はrun{BUILD_RUN}、不変event14はrun36310534280を再利用。現在候補{CANDIDATE["sha256"]}、code{recipe["build"]["code"]["size"]}byte/差分{recipe["changed_bytes"]}byte。旧2native failureは保持。純粋入力/独立pixelタイル/ユーザ枠ロードだけの変更影響を今回のnativeで検査し、厳格oracleは緩和しない。視認・自己run終端の未確認を成功としない。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a',encoding='utf-8') as stream:stream.write(note)


def guard():
    d.current()
    import pr16_resume
    import pr16_learnset_runtime_record as g
    pr16_resume.validate(ROOT)
    history=set(d.git('diff','--name-only',a.START,os.environ['GITHUB_SHA']).decode().splitlines())
    g.START=a.START;g.CODE=a.CODE|history;g.OWNED=set(d.read(a.OUT/'owned.json'));g.guard()
    s.need(d.bindings(a.PROTECTED)==d.read(ROOT/a.CP)['protected_bindings'],'old accepted/failure evidence immutable')
    subprocess.run(['git','diff','--cached','--check'],check=True)


a.build_reuse=build_reuse
if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['measure']:
        try:a.measure()
        except Exception as exc:
            if a.PUBLIC.exists():d.write(a.PUBLIC/'error.json',dict(type=type(exc).__name__,reason=str(exc),counts=a.COUNTS))
            raise
    elif sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(d.read(a.OUT/'owned.json')))
    else:raise SystemExit('measure|record|guard|paths')
