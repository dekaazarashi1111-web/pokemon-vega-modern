#!/usr/bin/env python3
"""Record completed Maori evidence; never starts a core, compiles, or repeats tests."""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_fast_maori as m
import pr16_research_story_route_actions as h
from pr16_learnset_compact_record import publish_resume
SELF='scripts/pr16_story_fast_maori_record.py'
WF='.github/workflows/pr16-story-fast-maori-record.yml'
TEST='tests/test_pr16_story_fast_maori_record.py'
RUN=36504040292
SOURCE='383ce0f49f4761f6db875e1a2f0a89692d2966e8'
ARTIFACT=11006311891
ARCHIVE=dict(size=17717828,sha256='304cae07573563abfb93e4bd7f1bfd5bc7e8348b374380fa487ffe20fd382d1d')
STATE=h.d.STATE
DOC=h.d.DOC
OUT=ROOT/'.local/pr16-story-fast-maori-record'
PUBLIC=OUT/'public'
EVIDENCE='content/modernization/pr16_story_fast_maori_evidence'
GOAL='マオリ通常勝利・story-fast Save16・独立Continueは受入済み。次はartifact11006311891のstory-fast.srm（map3/19、53,10、北向き）から先へ進む。176/cold20入力とSave1〜14・分離smokeを再生しない。progression.srmは元の戦闘前Axew Lv37/EXP68589を保持。全国図鑑の正規解禁ownerと進化gateを照合し、自然解禁境界または影響台帳付きsource修正/後継候補へ進む。flag注入で進化成功扱いしない。Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。'
TEXT=('verification.json','measurement.json','manifest.json','unit.stdout.txt','unit.stderr.txt',
      'progress/stdout.txt','progress/stderr.txt','continue/stdout.txt','continue/stderr.txt')


def put(path,value):h.d.write(path,value)


def completed(run,jobs):
    m.need(type(run) is dict and run.get('id')==RUN and run.get('head_sha')==SOURCE and
           run.get('head_branch')=='codex/modernization-followup-20260908' and
           run.get('path')=='.github/workflows/pr16-story-fast-maori.yml' and
           run.get('status')=='completed' and run.get('conclusion')=='success' and
           type(run.get('run_attempt')) is int and run['run_attempt']==1,'exact successful native terminal')
    m.need(type(jobs) is dict and jobs.get('total_count')==1 and len(jobs.get('jobs',[]))==1,'complete single job page')
    job=jobs['jobs'][0]
    names=['Set up job','Run actions/checkout@v4','Fixed resume integrity without native acceptance replay',
           'New Maori176 and independent cold20 only','Lightweight task graph','Run actions/upload-artifact@v4',
           'Post Run actions/checkout@v4','Complete job']
    m.need(job.get('id')==109201289995 and job.get('run_id')==RUN and job.get('name')=='measurement' and
           job.get('status')=='completed' and job.get('conclusion')=='success','completed measurement job')
    m.need([s.get('name') for s in job.get('steps',[])]==names and all(s.get('status')=='completed' and
           s.get('conclusion')=='success' for s in job['steps']),'all steps including upload/post complete')
    return dict(run=h.d.run_summary(run),job={k:job[k] for k in ('id','run_id','name','status','conclusion','steps')})


def artifact_meta(meta):
    m.need(meta.get('id')==ARTIFACT and meta.get('size_in_bytes')==ARCHIVE['size'] and
           meta.get('digest')=='sha256:'+ARCHIVE['sha256'] and meta.get('expired') is False and
           meta.get('name')=='pr16-story-fast-maori-checkpoint' and
           meta.get('workflow_run',{}).get('id')==RUN and meta['workflow_run'].get('head_sha')==SOURCE,
           'immutable artifact metadata, not another successful run')


def record():
    os.chdir(ROOT);h.d.current();state=h.source_check()
    m.need(not (ROOT/m.CP).exists() and not (ROOT/EVIDENCE).exists(),'do not duplicate accepted record')
    before=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    terminal=completed(h.d.inputs.api(f'actions/runs/{RUN}'),h.d.inputs.api(f'actions/runs/{RUN}/jobs?per_page=100'))
    meta=h.d.inputs.api(f'actions/artifacts/{ARTIFACT}');artifact_meta(meta)
    raw=h.d.inputs.api(f'actions/artifacts/{ARTIFACT}/zip',True)
    m.need(m.identity(raw)==ARCHIVE,'exact outer archive bytes')
    folder=OUT/'original';folder.mkdir(parents=True)
    with h.safe_zip(raw,60000000) as z:
        manifest=json.loads(z.read('manifest.json'))
        m.need(len(manifest)==73 and set(z.namelist())==set(manifest)|{'manifest.json'},'complete 73-file artifact manifest')
        for name,binding in manifest.items():m.need(m.identity(z.read(name))==binding,'original evidence '+name)
        z.extractall(folder)
    measured=json.loads((folder/'measurement.json').read_bytes())
    m.need(measured['run_id']==RUN and measured['source_head']==SOURCE and measured['focused_tests']==44 and
           measured['formal_native_processes']==measured['development_native_processes']==2 and
           measured['accepted_case_reruns']==0,'original execution accounting')
    for path,binding in measured['source_bindings'].items():
        m.need(m.identity((ROOT/path).read_bytes())==binding and m.identity(h.d.git('show',SOURCE+':'+path))==binding,
               'unmodified measured source '+path)
    v,ledger=m.verify(folder)
    m.need(v==measured['result']==json.loads((folder/'verification.json').read_bytes()),'read-only oracle agrees with original')
    m.need(ledger==json.loads((folder/'save-byte-ledger.json').read_bytes()) and
           m.identity((folder/'save-byte-ledger.json').read_bytes())==measured['save_byte_ledger'],'complete original byte ledger')
    unit=(folder/'unit.stderr.txt').read_bytes()
    m.need(not (folder/'unit.stdout.txt').read_bytes() and unit.count(b' ... ok\n')==44 and b'\nOK\n' in unit and
           b'skipped' not in unit and b'FAILED' not in unit,'44 original tests; do not rerun')
    evidence=ROOT/EVIDENCE;evidence.mkdir()
    for name in TEXT:
        data=(folder/name).read_bytes();data.decode('utf-8');m.need(b'\0' not in data,'text evidence only')
        target=evidence/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    terminal.update(record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        record_native_processes=0,record_accepted_test_reruns=0,record_compiles=0,
        formal_artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','expires_at','workflow_run')})
    put(evidence/'terminal.json',terminal)
    review=json.loads((ROOT/m.DEV/'measurement.json').read_text())['review']
    checkpoint=dict(schema_version=1,task=m.TASK,status='PASS_STORY_FAST_MAORI_SAVE16_SCOPED',
        source_head=SOURCE,run_id=RUN,actions_completion_confirmed=True,actions_conclusion='success',
        record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        terminal_evidence=EVIDENCE+'/terminal.json',artifact=terminal['formal_artifact'],verification=v,
        save_byte_ledger=dict(binding=measured['save_byte_ledger'],changed_bytes=ledger['changed_bytes'],
            ranges=len(ledger['ranges']),artifact_only=True),visual_review=review,
        source_bindings=measured['source_bindings'],evidence_bindings=h.d.bindings({EVIDENCE+'/'+n for n in TEXT+('terminal.json',)}),
        next_goal_ja=GOAL,record_native_processes=0,record_accepted_case_reruns=0,
        general_ci_all_success_claimed=False,release_ready=False,active_baseline_changed=False)
    put(ROOT/m.CP,checkpoint)
    guide=f'''# story-fast マオリ勝利・Save16の限定受入

## 完了した範囲

`PASS_STORY_FAST_MAORI_SAVE16_SCOPED`。自己OT Lv100支援partyで、通常の道路移動からじゅくがえりマオリに1勝し、通常Save counter15→16、独立Continueと戦闘後会話まで完了した。自然入手・自然育成・自然難易度・進化・全storyの受入ではない。

マオリのパモ♀Lv4、パピモッチ♀Lv6、コフキムシ♂Lv8にサイコブレイク3回。賞金160円、所持金2776→2936。途中の野生エネコ♀Lv2は通常逃走1回であり勝利ではない。捕獲・敗北0。相手ひんし32は勝利終端ではなく、outcome33→field36で1勝だけを計上する。fieldに残るflags12/outcome1を再戦と数えない。

## 固定原本と検証

測定source `{SOURCE}`、run `{RUN}`、job `109201289995` は全8step completed/success。artifact `{ARTIFACT}` (`pr16-story-fast-maori-checkpoint`) は{ARCHIVE['size']}bytes、SHA-256 `{ARCHIVE['sha256']}`、期限2026-12-28。73 member hashとmanifestを照合。ROM/save/runner/48画像/全Save byte差分はartifactだけに保管し、tracked textは `{EVIDENCE}` に限定する。

ROMは33554432bytes、SHA-256 `{m.CANDIDATE['sha256']}`。旧Wiki候補46487d98…ではない。開発2process、正式2process（progress176入力15106frames、cold20入力1848frames）。7 host-write barrier、host書込/fixture呼出/警告0。開発44試験・正式44試験は同じ新規44件を別環境で実行した数であり、88別件とは数えない。記録時の追加native/compile/受入試験再実行は0。

全600partybytesではPP offset52の9→6と徒歩友情 offset141の35→36だけが変化。species/EXP/Lv100/status、未使用party200bytes、全5Bag pocket、PC sector5〜13と預けた元2匹は保持。前回保存bank57344bytes不変。全Save差分6418bytes/1757範囲を再構成一致し、byte台帳185286bytesのSHA-256は `{measured['save_byte_ledger']['sha256']}`。一般sector checksum対応全体は主張しない。

## 次回の唯一のstory-fast開始点

同artifactの `story-fast.srm`（`cold.srm`も全byte同一）は131088bytes、SHA-256 `{m.OUTPUT_SAVE['sha256']}`、counter16。保存位置map3/19（501番道路）、座標53,10、北向き。独立Continueで全Save/RTC131088bytes、party600bytes、研究ledger/RP0を保持。マオリ再会話は戦闘後台詞となり再戦しない。

Save成功文そのもののframeは未取得。obs41は書込中、42がcounter16/field復帰であり、この区別と独立Continueで保存を証明する。obs14は逃走後の全暗転frameで、成功画面ではない。48画像は直接pixel目視し、同一hashの正式原本へ結び付けた。画像名だけで文言を創作しない。

## 未完と禁止事項

{GOAL}

元の非支援Save14と分離済みprogression原本は保全した。全国図鑑magic0のままで、Axew進化成功へ読み替えない。最新の成長・進化・Lucky Egg受入状態は分離checkpointを参照。旧BP/P08/一般CIのfailure・action_requiredは本scope成功へ統合せず、Stage62 active baseline、source-lock、原本、PR draft/open/未merge、release=falseを維持する。

記録workflow自身のpush/upload終端は自己予測せず、別API照合で確認する。記録commitはbranch履歴と記録artifactの `record-head.txt` が正本。
'''
    (ROOT/m.GUIDE).write_text(guide,encoding='utf-8')
    state.setdefault('observed_head_history',[]).append(dict(head=state['observed_head'],
        semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='Save14の非支援受入を保持し、別laneのマオリSave16限定受入を追加。'))
    state['observed_head']=SOURCE
    state['observed_head_semantics']='自己OT Lv100 story-fastのマオリ勝利・Save16測定source HEAD。非支援Save14、進化成功、記録commit、active baselineではない。'
    state['observed_head_checks']=dict(scope_head=SOURCE,runs=[terminal['run']],
        reason_ja='専用run36504040292/job109201289995の全8stepと73memberを照合済み。一般CI全成功は主張せず既存failure/action_requiredを保持。記録workflow自身の終端は別照合。')
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['story_fast_maori']={k:checkpoint[k] for k in ('status','source_head','run_id','actions_completion_confirmed','actions_conclusion','record_source_head','record_run_id')}
    state['story_fast_maori'].update(path=m.CP,guide=m.GUIDE,output_save=m.OUTPUT_SAVE,artifact_id=ARTIFACT,natural_growth_accepted=False,evolution_accepted=False)
    state['next_action'].update(id='STORY_FAST_AFTER_MAORI_AND_NATIONAL_DEX_GATE',goal_ja=GOAL,
        read_paths=[m.GUIDE,m.CP,'docs/PR16_STORY_ACCELERATION_CHECKPOINT_JA.md',
        'content/modernization/pr16_story_acceleration_completion.json','content/modernization/pr16_story_acceleration_checkpoint.json',
        'docs/PR16_STORY_ACCELERATED_ACCEPTANCE_PLAN_JA.md','content/modernization/pr16_story_acceleration_plan.json',
        'tools/mgba_pr16_story_acceleration.c'])
    state['bp']['next_step']=GOAL
    state['bp']['current_stop']='story-fastはマオリ通常勝利後Save16、map3/19（53,10）、131088bytes保存/独立Continue一致。非支援laneはSave14のまま。progressionは全国図鑑gateで進化未受入。正式BP/P08受入は不変。'
    owned={m.CP,m.GUIDE,STATE,DOC,*h.d.LOGS}|{EVIDENCE+'/'+n for n in TEXT+('terminal.json',)}
    code={SELF,WF,TEST,*measured['source_bindings']}
    m.need(h.d.bindings(before)==before,'no accepted file changed before publishing')
    for p in (owned|code)-{STATE,DOC,*h.d.LOGS}:state['source_bindings'][p]=m.identity((ROOT/p).read_bytes())
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {m.TASK} / マオリ通常勝利・Save16・独立Continue
- Version: story-fast-maori-v1
- Status: DONE（支援story進行限定、自然育成/進化/全storyは未完）
- Summary: 新story-fast176/cold20入力でtrainer1勝・逃走1回・賞金160・counter15→16。全party差分2bytes、前bank57344bytes/PC/Bag保持、独立Continue全131088bytes一致、再会話再戦0。Save成功文frameは未取得と明記。
- Files changed: 新検証器/44試験/入力/正式測定/記録器、公開text/checkpoint/guide、固定引継ぎMD/JSON、両ログ。ROM/save/画像/全差分hexはartifactのみ。
- Verify: completed native run{RUN}/job109201289995全8step成功、artifact{ARTIFACT}全73member hash、48目視画像原本、全Save差分6418bytes/1757範囲再構成PASS。開発44/正式44は同じ新44件。開発native2/正式2、記録native0/test再実行0、compile/ROM変更/既受入native再実行0。resume/task graph/最終scoped index/diff後のみcommit。一般CI全成功は主張しない。
- Commit: WIP92da857/3d07192、検証器a35eb96、測定source{SOURCE}。記録source={os.environ['GITHUB_SHA']}; record run={os.environ['GITHUB_RUN_ID']}、同branch非force pushと全text読戻し。
- Network: GitHub固定HEAD/run/artifactのみ。原本Save14/分離progression/Stage62基準/source-lock/正式BP/P08不変、PR未merge・releaseなし。
- Next: {GOAL}
'''
    for p in h.d.LOGS:
        with (ROOT/p).open('a',encoding='utf-8') as f:f.write(entry)
    PUBLIC.mkdir(parents=True)
    put(OUT/'owned.json',sorted(owned))
    h.d.git('add','--',*sorted(owned))
    put(PUBLIC/'receipt.json',dict(status='RECORD_PREPARED_FROM_COMPLETED_ORIGINAL',terminal=terminal,
        owned=sorted(owned),verified_members=73,record_native_processes=0,record_test_reruns=0))


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT)
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


def snapshot():
    with zipfile.ZipFile(PUBLIC/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in h.d.read(OUT/'owned.json'):
            data=h.d.git('show','HEAD:'+name);m.need(data==(ROOT/name).read_bytes(),'commit text readback '+name)
            z.writestr(name,data)
        z.writestr('record-head.txt',h.d.git('rev-parse','HEAD'))
    (PUBLIC/'record-head.txt').write_bytes(h.d.git('rev-parse','HEAD'))

if __name__=='__main__':
    commands=dict(record=record,guard=guard,snapshot=snapshot)
    if len(sys.argv)!=2 or sys.argv[1] not in commands:raise SystemExit('record|guard|snapshot')
    commands[sys.argv[1]]()
