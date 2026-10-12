#!/usr/bin/env python3
"""Record the completed Save18 original; zero cores, compiles or accepted-test reruns."""
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
import pr16_story_ayame_accept as m
RUN=36522150353
JOB=109257152262
SOURCE='2577d253823bdca94bf3dfac0a67dea9776a6d8a'
ARTIFACT=11012768108
ARCHIVE=dict(size=18101058,sha256='4e7a2e5d25dbf01284fdd992327971b7a0d84df2e86022ea6cefc685b2dd064b')
SELF='scripts/pr16_story_ayame_record.py'
WF='.github/workflows/pr16-story-ayame-record.yml'
TEST='tests/test_pr16_story_ayame_record.py'
OUT=ROOT/'.local/pr16-story-ayame-record'
PUBLIC=OUT/'public'
EVIDENCE='content/modernization/pr16_story_ayame_gate_evidence'
STEPS=['Set up job','Run actions/checkout@v4','New Save18 interval and independent Continue only',
       'Lightweight task graph','Run actions/upload-artifact@v4','Post Run actions/checkout@v4','Complete job']
TEXT=('verification.json','measurement.json','manifest.json','parent.json','failure-receipt.json',
      'unit-chain.stdout.txt','unit-chain.stderr.txt','unit-accept.stdout.txt','unit-accept.stderr.txt',
      'progress/commands.txt','progress/stdout.txt','progress/stderr.txt',
      'continue/commands.txt','continue/stdout.txt','continue/stderr.txt','failed-development-progress.stdout.txt')
RECORD_TEXT=('record-unit.stdout.txt','record-unit.stderr.txt')
GOAL=('story-fastの唯一の開始点はartifact11012768108のstory-fast.srm（Save18、131088bytes、'
      'SHA256 dc1f690f0616affc61b6d45632924e4c81995c91c7c1939994f37bbe8527432d）。'
      'アヤメPC map5/4・7,4・北向き・party4全回復/RP0から、通常出口→入場可能になったアヤメジムの未完storyを進める。'
      'ジムリーダー勝利/バッジはまだ未受入。旧未保存WIPのHM05はこのSaveには無く、必要時は通常会話で取得する。'
      '新381/cold23入力・55試験・旧BP/P08/Save1〜17を無影響に再走しない。'
      '分離progression原本Axew Lv37/EXP68589、NationalDex magic0とownerを保全し、flag/var注入で解禁しない。'
      '正規全国図鑑解禁、自然育成/進化、Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。')


def completed(run,jobs):
    m.need(run.get('id') == RUN and run.get('head_sha') == SOURCE and run.get('head_branch') == m.source.BRANCH and
        run.get('path') == '.github/workflows/pr16-story-ayame.yml' and run.get('status') == 'completed' and
        run.get('conclusion') == 'success' and type(run.get('run_attempt')) is int and run['run_attempt'] == 1,
        'exact completed measurement run')
    m.need(type(jobs.get('total_count')) is int and jobs['total_count'] == 1 and len(jobs.get('jobs',[])) == 1,'complete job page')
    job=jobs['jobs'][0]
    m.need(job.get('id') == JOB and job.get('run_id') == RUN and job.get('name') == 'continuation' and
        job.get('status') == 'completed' and job.get('conclusion') == 'success','exact completed measurement job')
    m.need([s.get('name') for s in job.get('steps',[])] == STEPS and
        all(s.get('status') == 'completed' and s.get('conclusion') == 'success' for s in job['steps']),
        'all seven steps including upload and post')
    return dict(run={k:run[k] for k in ('id','head_sha','head_branch','path','status','conclusion','run_attempt')},job=job)


def artifact_meta(meta):
    m.need(meta.get('id') == ARTIFACT and meta.get('name') == 'pr16-story-ayame-checkpoint' and
        meta.get('size_in_bytes') == ARCHIVE['size'] and meta.get('digest') == 'sha256:'+ARCHIVE['sha256'] and
        meta.get('expired') is False and meta.get('workflow_run',{}).get('id') == RUN and
        meta['workflow_run'].get('head_sha') == SOURCE,'fixed unexpired artifact and source')


def record():
    import pr16_research_story_route_actions as h
    import pr16_story_ayame_measure as measure
    from pr16_learnset_compact_record import publish_resume
    os.chdir(ROOT);h.d.current();state=h.source_check()
    m.need(os.environ['GITHUB_RUN_ATTEMPT'] == '1' and not (ROOT/m.CP).exists() and not (ROOT/EVIDENCE).exists(),
        'first record only; no duplicate accepted checkpoint')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    terminal=completed(h.d.inputs.api(f'actions/runs/{RUN}'),h.d.inputs.api(f'actions/runs/{RUN}/jobs?per_page=100'))
    meta=h.d.inputs.api(f'actions/artifacts/{ARTIFACT}');artifact_meta(meta)
    raw=h.d.inputs.api(f'actions/artifacts/{ARTIFACT}/zip',True)
    m.need(m.identity(raw) == ARCHIVE,'whole original archive')
    folder=OUT/'original';folder.mkdir(parents=True)
    with h.safe_zip(raw,80000000) as z:
        manifest=json.loads(z.read('manifest.json'))
        m.need(len(manifest) == 170 and set(z.namelist()) == set(manifest)|{'manifest.json'},'all170 original members')
        for name,binding in manifest.items():m.need(m.identity(z.read(name)) == binding,'original member '+name)
        z.extractall(folder)
    measured=json.loads((folder/'measurement.json').read_bytes())
    for key,value in dict(run_id=RUN,source_head=SOURCE,new_tests=55,formal_native_processes=2,
                         development_native_processes=4,development_failed_native=2,accepted_case_reruns=0,
                         accepted_test_reruns=0,compiles=0).items():
        m.need(measured.get(key) == value,'original execution count '+key)
    for path,binding in measured['source_bindings'].items():
        m.need(m.identity((ROOT/path).read_bytes()) == binding and m.identity(h.d.git('show',SOURCE+':'+path)) == binding,
               'unchanged measured source '+path)
    v,ledger=m.verify(folder);v=json.loads(json.dumps(v))
    m.need(v == measured['result'] == json.loads((folder/'verification.json').read_bytes()),'read-only oracle equality')
    m.need(ledger == json.loads((folder/'save-byte-ledger.json').read_bytes()) and
        m.identity((folder/'save-byte-ledger.json').read_bytes()) == measured['save_byte_ledger'],'full diff original')
    for kind,count in (('chain',25),('accept',30)):
        unit=(folder/f'unit-{kind}.stderr.txt').read_bytes()
        m.need(not (folder/f'unit-{kind}.stdout.txt').read_bytes() and unit.count(b' ... ok\n') == count and
            b'\nOK\n' in unit and b'FAILED' not in unit and b'skipped' not in unit,'reuse successful test original '+kind)
    record_stdout=(OUT/'preflight/unit.stdout.txt').read_bytes()
    record_stderr=(OUT/'preflight/unit.stderr.txt').read_bytes()
    m.need(not record_stdout and record_stderr.count(b' ... ok\n') == 24 and b'\nOK\n' in record_stderr and
        b'FAILED' not in record_stderr and b'skipped' not in record_stderr,'24 new record gate tests')
    evidence=ROOT/EVIDENCE;evidence.mkdir()
    (evidence/RECORD_TEXT[0]).write_bytes(record_stdout);(evidence/RECORD_TEXT[1]).write_bytes(record_stderr)
    for name in TEXT:
        data=(folder/name).read_bytes();data.decode('utf-8');m.need(b'\0' not in data,'text only')
        target=evidence/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    checks=h.d.inputs.api('actions/runs?head_sha='+SOURCE+'&per_page=100')
    m.need(checks['total_count'] == len(checks['workflow_runs']),'complete measured-head Actions page')
    latest=[h.d.run_summary(r) for r in checks['workflow_runs']]
    terminal.update(record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        record_native_processes=0,record_accepted_test_reruns=0,record_compiles=0,record_new_tests=24,
        artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},
        measured_head_actions=latest,general_ci_all_success_claimed=False)
    h.d.write(evidence/'terminal.json',terminal)
    checkpoint=dict(schema_version=1,task=m.TASK,status='PASS_AYAME_CHAIN_GYM_ENTRY_SAVE18_SCOPED',source_head=SOURCE,
        run_id=RUN,job_id=JOB,actions_completion_confirmed=True,actions_conclusion='success',
        record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        artifact=terminal['artifact'],verification=v,save18_accepted=True,
        chain_helper_flag_scope='verification.save_acceptance_claimed=false is the chain-only helper; Save18 is accepted separately by completion, structural bytes, independent Continue and completed Actions.',
        save_byte_ledger=dict(binding=measured['save_byte_ledger'],changed_bytes=ledger['changed_bytes'],ranges=len(ledger['ranges']),artifact_only=True),
        source_bindings=measured['source_bindings'],evidence_bindings=h.d.bindings({EVIDENCE+'/'+n for n in TEXT+RECORD_TEXT+('terminal.json',)}),
        next_goal_ja=GOAL,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    h.d.write(ROOT/m.CP,checkpoint)
    guide=f'''# アヤメ前提3連戦・ジム入場・Save18 限定受入

`PASS_AYAME_CHAIN_GYM_ENTRY_SAVE18_SCOPED`。固定Save17から通常ジム前会話、カチヌキ3兄弟の3連勝、ジム前NPCの退去、実ジムmap6/2入場、PC通常回復・Save18・独立Continue・手持ちUIまで完了。ジムリーダー/バッジ、自然育成/進化/自然難易度/全国図鑑/研究施設自然到達/全storyは未受入。

## 原本・実測

測定source `{SOURCE}`、run `{RUN}`、job `{JOB}` 全7step completed/success。artifact `{ARTIFACT}`、{ARCHIVE['size']}bytes、SHA256 `{ARCHIVE['sha256']}`、期限 `{meta['expires_at']}`。全170member hashと全Save差分6731bytes/1740範囲を再構成照合。ROM/Save/全145画像/全差分はartifactのみ。tracked text原本は `{EVIDENCE}`。

381/cold23入力、36244/cold1714frames。全145画像hash/形式検証、開発時の30pixelレビューanchorを正式同一画像に結合。キミカ200円・コウタ176円・カナコ192円、所持金3372→3940。BATTLE開始37/62/86、勝利55/78/109、field復帰58/81/112、連戦全体解錠115。中間lock1を許容し、交代UI46・KO・残留outcome1を別勝利に数えない。初回の条件未成立の上階訪問も元の入力どおり保持。

map22/1の通常条件eventはvar0x4071=2から発火し、root138585288がtrainer1/1200/1203を参照、終了時stage3を書込む。別のobject会話trainer557/558/559と混同しない。ジムobject1の通常scriptでflag4355をsetし、実際の入場観測123を照合。元ROMの変更やflag注入なし。

## 保存境界・保持

観測138はcounter17/lock1の書込中、139はcounter18/lock0の完了。成功文言frameそのものは未採取。独立Continueではcounter18・party4・RP0・全回復の手持ちUIとfieldを確認し、Save/RTC全131088bytes保持。前Save17 bank57344bytes、PC sections5〜12とchunk13 boxed payload2000bytes、unused party200bytes、Bag5pocketを保持。party変更は歩行友情2bytesだけ。chunk13+0x7d0のS61E拡張recordはCRC32/反転値を検証し、payload offset256の3→11（gym flag4355 bit3）だけが変化。他expanded flags/vars/ball/coinsは保持。一般sector checksum全体を追加受入したものではない。

chain helperのsave_acceptance_claimed=falseは連戦だけではSaveを受入しない意味で原本に残す。別completion/byte/cold/Actions gateを全通過したSave18の受入はcheckpoint最上位のsave18_accepted=true。

## 失敗と実行会計

開発harnessを保存途中で早期quitした1processと、その部分Saveから古いSave17へfallbackした診断cold1processは失敗として保持。未受入新区間だけを1回再実行し、全失敗観測prefix95617bytesを一致させた上で600frame待機を追加した。失敗stdout95806bytesは正式prefix+既知終端から元hash一致でlossless再構成したtextを保存。失敗を成功扱いにしない。開発native4（失敗2+成功2）、正式native2、記録native/compile/受入試験再実行0。新規55試験は開発/Actionsで同じ55件、110別件ではない。

旧未保存WIP c0e9970のHM05受領/野生逃走は今回のSaveに含まれず、Bagは不変。旧317/cold22入力・34/19試験・BP/P08/Save1〜17の明示再走0。PR CIの既存P03 capacity failure/action_requiredを専用成功へ合算しない。PR16 draft/open/未merge、release=false、active baseline/source-lock・分離progression原本・全国図鑑owner不変。

## 次の唯一のstory-fast開始点

{GOAL}

記録workflow source `{os.environ['GITHUB_SHA']}`、run `{os.environ['GITHUB_RUN_ID']}` のpush/upload終端は自己予測しない。別API照合し、artifactのrecord-head.txtとrecord.zipで全text読戻しを確定する。
'''
    (ROOT/m.GUIDE).write_text(guide,encoding='utf-8')
    m.need(h.d.bindings(protected) == protected,'prior accepted sources unchanged')
    state.setdefault('observed_head_history',[]).append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],
        checks=state['observed_head_checks'],reason_ja='旧受入を保持し、三兄弟3連勝・ジム入場・通常回復Save18の別scopeを追加。'))
    state['observed_head']=SOURCE
    state['observed_head_semantics']='三兄弟3連勝・ジム入場・回復Save18測定source。ジムリーダー/自然育成/進化/全story、記録commit、active baselineではない。'
    state['observed_head_checks']=dict(scope_head=SOURCE,runs=latest,reason_ja='専用run36522150353/job109257152262全7stepと170memberを照合。既存CI失敗は別scope。記録workflow自身の終端は別API照合。')
    now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    state['observed_date_jst']=now.date().isoformat()
    state['story_ayame_gate']=dict(status=checkpoint['status'],checkpoint=m.CP,guide=m.GUIDE,run_id=RUN,artifact_id=ARTIFACT,
        story_fast_save=m.OUTPUT_SAVE,map=[5,4],xy=[7,4],facing=2,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=GOAL,release_ready=False)
    state['next_action'].update(id='STORY_AFTER_AYAME_GYM_ENTRY_SAVE18',goal_ja=GOAL,
        read_paths=[m.GUIDE,m.CP,'docs/PR16_NATIONAL_DEX_OWNER_JA.md','content/modernization/pr16_national_dex_owner_checkpoint.json',
                    'content/modernization/pr16_story_acceleration_checkpoint.json',m.DEV+'/expected.json',SELF],
        stop_rule_ja='Save18から先の通常storyだけを自然Save/cold境界で区切る。新381/cold23・55試験・旧BP/P08/Save1〜17を再走しない。書込み途中counter更新だけで保存完了としない。異常時は失敗証跡を保全。')
    state['bp']['next_step']=GOAL
    state['bp']['current_stop']='支援story-fastで三兄弟3連勝・通常ジム入場・PC全回復Save18・独立Continueを限定受入。全Save/RTC131088bytes保持。map5/4・7,4北・party4/RP0。ジムリーダー/バッジ未完、NationalDex magic0維持。次はartifact11012768108から先だけ。'
    owned={m.CP,m.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|{EVIDENCE+'/'+n for n in TEXT+RECORD_TEXT+('terminal.json',)}
    bound=(owned|measure.CODE|{SELF,WF,TEST})-{h.d.STATE,h.d.DOC,*h.d.LOGS}
    state['source_bindings'].update(h.d.bindings(bound));publish_resume(state)
    stamp=now.isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {m.TASK} / アヤメ前提3連戦・ジム入場・Save18
- Version: story-ayame-save18-v1
- Status: DONE（支援story新区間限定。ジムリーダー/自然育成/進化/全story未完）
- Summary: Save17→通常条件会話・三兄弟3勝→ジム入場→PC回復・Save18・独立Continue。賞金568、Bag不変、旧WIPのHM05は未継承。連戦lock/交代UI/残留outcomeと保存途中を別判定。S61E tailをboxed payloadと分離しCRC/gym bitだけの変化を照合。
- Files changed: 新規連戦/保存/S61E oracle・55試験・入力計画/失敗receipt、測定/記録workflow、checkpoint/guide/text証跡、固定再開MD/JSON、両ログ。ROM/Save/全差分hex/画像はartifactのみ。
- Verify: run{RUN}/job{JOB}全7step成功、artifact{ARTIFACT}全170member、145画像/30pixel anchor、381/cold23入力、全Save差分6731bytes/1740範囲、cold全131088bytes、前bank57344bytes/boxed PC/Bag保持。新55試験原本再利用、記録時は新しい終端gate24試験のみ。開発native4（失敗2）/正式2、記録native0/受入再走0/compile0。scoped final-index/private path/resume/task graph/diff後のみcommit。既存CI全成功とは主張しない。
- Commit: WIP d75466777ae1、測定source{SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。同branch非force push・全text読戻し。
- Network: 固定GitHub HEAD/run/artifact。旧受入/BP/P08/progression/全国図鑑owner/active baseline/source-lock不変。PR16未merge、releaseなし。
- Next: {GOAL}
'''
    for path in h.d.LOGS:
        with (ROOT/path).open('a',encoding='utf-8') as stream:stream.write(entry)
    PUBLIC.mkdir(parents=True,exist_ok=True)
    h.d.write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
    h.d.write(PUBLIC/'receipt.json',dict(status='RECORD_PREPARED_FROM_COMPLETED_ORIGINAL',terminal=terminal,owned=sorted(owned),
        verified_members=170,record_native_processes=0,record_accepted_test_reruns=0))


def guard():
    import pr16_research_story_route_actions as h
    import pr16_resume
    import pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT)
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


def snapshot():
    import pr16_research_story_route_actions as h
    with zipfile.ZipFile(PUBLIC/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in h.d.read(OUT/'owned.json'):
            data=h.d.git('show','HEAD:'+name);m.need(data == (ROOT/name).read_bytes(),'committed text readback '+name)
            z.writestr(name,data)
        z.writestr('record-head.txt',h.d.git('rev-parse','HEAD'))
    (PUBLIC/'record-head.txt').write_bytes(h.d.git('rev-parse','HEAD'))


if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot)
    m.need(len(sys.argv) == 2 and sys.argv[1] in actions,'record|guard|snapshot');actions[sys.argv[1]]()
