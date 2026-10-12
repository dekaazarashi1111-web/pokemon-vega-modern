#!/usr/bin/env python3
"""完了済みSave19を全byte照合して記録する。emulator/旧受入試験の再走は行わない。"""
from __future__ import annotations
import datetime
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_gym_accept as m
RUN,JOB,ARTIFACT=36559147649,109375512907,11028517527
SOURCE='e9c9a55c59705490cd49f834fb8586c41bb1861b'
ARCHIVE=dict(size=18664867,sha256='d93e36abb202788962f1ddd866189d1a72443efa51102a4b66a197ec0549156a')
SELF='scripts/pr16_story_gym_record.py'
WF='.github/workflows/pr16-story-gym-closeout.yml'
TEST='tests/test_pr16_story_gym_record.py'
OUT=ROOT/'.local/pr16-story-gym-closeout'
PUBLIC=OUT/'public'
EVIDENCE='content/modernization/pr16_story_gym_evidence'
STEPS=['Set up job','Run actions/checkout@v4','New Save19 gym interval and independent Continue only',
       'Lightweight task graph','Run actions/upload-artifact@v4','Post Run actions/checkout@v4','Complete job']
TEXT=('verification.json','measurement.json','manifest.json','parent.json','unit.stdout.txt','unit.stderr.txt',
      'progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json',
      'continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json')
COUNTS=dict(run_id=RUN,source_head=SOURCE,new_tests=73,development_native_processes=2,
    development_native_failures=0,prior_unaccepted_lost_wip_native_processes=1,formal_native_processes=2,
    accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,recovery_prefix_verified=True,
    prior_hash_only_wip_accepted=False)
GOAL=('story-fastの唯一の開始点はartifact11028517527のstory-fast.srm（Save19、131088bytes、'
      'SHA256 dd7adddc09555c2232299075bba657e9e7261ad3b868d9cabb5f0edccc8ed06d）。'
      'アヤメPC map5/4・7,4北・party4全回復/RP0、badge1・var4071=5/4072=1から通常storyの未完区間だけを進める。'
      'ハヤカ/アマナ2勝・通常報酬・モスギス会話・Save19/coldは完了。HM05は未所持で必要なら通常会話で取得する。'
      '新464/cold34入力・73試験・旧BP/P08/Save1〜18は無影響に再走しない。'
      '分離progression原本Axew Lv37/EXP68589とNationalDex magic0・grant ownerを保全しflag/var注入で解禁しない。'
      '正規全国図鑑解禁、自然育成/進化、Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。')


def completed(run,jobs):
    m.need(run.get('id') == RUN and run.get('head_sha') == SOURCE and run.get('head_branch') == m.source.BRANCH and
        run.get('path') == '.github/workflows/pr16-story-gym.yml' and run.get('status') == 'completed' and
        run.get('conclusion') == 'success' and type(run.get('run_attempt')) is int and run['run_attempt'] == 1,
        '正式測定runのidentity/成功/初回だけ')
    m.need(type(jobs.get('total_count')) is int and jobs['total_count'] == 1 and len(jobs.get('jobs',[])) == 1,'全jobページ')
    job=jobs['jobs'][0]
    m.need(job.get('id') == JOB and job.get('run_id') == RUN and job.get('name') == 'continuation' and
        job.get('status') == 'completed' and job.get('conclusion') == 'success','正式測定job')
    m.need([s.get('name') for s in job.get('steps',[])] == STEPS and
        all(s.get('status') == 'completed' and s.get('conclusion') == 'success' for s in job['steps']),
        'upload/postを含む全7step成功')
    return dict(run={k:run[k] for k in ('id','head_sha','head_branch','path','status','conclusion','run_attempt')},job=job)


def artifact_meta(meta):
    m.need(meta.get('id') == ARTIFACT and meta.get('name') == 'pr16-story-gym-checkpoint' and
        meta.get('size_in_bytes') == ARCHIVE['size'] and meta.get('digest') == 'sha256:'+ARCHIVE['sha256'] and
        meta.get('expired') is False and meta.get('workflow_run',{}).get('id') == RUN and
        meta['workflow_run'].get('head_sha') == SOURCE,'固定artifactの全identity')


def counts(measured):
    for key,value in COUNTS.items():
        m.need(type(measured.get(key)) is type(value) and measured[key] == value,'元の実行会計 '+key)


def unit_original(stdout,stderr,count):
    # テスト名のskipped/FAILEDを結果と混同せず、件数付きの終端を固定する。
    footer=rb'\n-{10,}\nRan '+str(count).encode()+rb' tests? in [0-9]+(?:\.[0-9]+)?s\n\nOK\n\Z'
    m.need(type(stdout) is bytes and type(stderr) is bytes and type(count) is int and count > 0 and
           not stdout and stderr.count(b' ... ok\n') == count and re.search(footer,stderr) is not None,
           '成功した試験原本の件数/終端だけ')


def verify_original(folder):
    folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_bytes())
    names={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    m.need(len(manifest) == 264 and names == set(manifest)|{'manifest.json'},'全264memberの集合')
    for name,binding in manifest.items():m.need(m.identity((folder/name).read_bytes()) == binding,'全byte '+name)
    measured=json.loads((folder/'measurement.json').read_bytes());counts(measured)
    unit_original((folder/'unit.stdout.txt').read_bytes(),(folder/'unit.stderr.txt').read_bytes(),73)
    v,ledger=m.verify(folder);v=json.loads(json.dumps(v))
    m.need(v == measured['result'] == json.loads((folder/'verification.json').read_bytes()),'保存済み受入oracle全値')
    m.need(ledger == json.loads((folder/'save-byte-ledger.json').read_bytes()) and
        m.identity((folder/'save-byte-ledger.json').read_bytes()) == measured['save_byte_ledger'],'全差分ledger原本')
    return measured,v,ledger


def record():
    import pr16_research_story_route_actions as h
    import pr16_story_gym_measure as measure
    from pr16_learnset_compact_record import publish_resume
    os.chdir(ROOT);h.d.current();state=h.source_check()
    m.need(os.environ['GITHUB_RUN_ATTEMPT'] == '1' and not (ROOT/m.CP).exists() and not (ROOT/EVIDENCE).exists(),
        '初回記録だけ。受入済みの再走禁止')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    terminal=completed(h.d.inputs.api(f'actions/runs/{RUN}'),h.d.inputs.api(f'actions/runs/{RUN}/jobs?per_page=100'))
    meta=h.d.inputs.api(f'actions/artifacts/{ARTIFACT}');artifact_meta(meta)
    raw=h.d.inputs.api(f'actions/artifacts/{ARTIFACT}/zip',True)
    m.need(m.identity(raw) == ARCHIVE,'外側ZIP全byte')
    folder=OUT/'original';folder.mkdir(parents=True)
    with h.safe_zip(raw,100000000) as z:z.extractall(folder)
    measured,v,ledger=verify_original(folder)
    for path,binding in measured['source_bindings'].items():
        m.need(m.identity((ROOT/path).read_bytes()) == binding and m.identity(h.d.git('show',SOURCE+':'+path)) == binding,
               '測定sourceを改変しない '+path)
    unit_original((OUT/'preflight/unit.stdout.txt').read_bytes(),(OUT/'preflight/unit.stderr.txt').read_bytes(),32)
    evidence=ROOT/EVIDENCE;evidence.mkdir()
    for name in TEXT:
        data=(folder/name).read_bytes();data.decode('utf-8');m.need(b'\0' not in data,'textだけ')
        p=evidence/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    for suffix in ('stdout','stderr'):
        (evidence/f'record-unit.{suffix}.txt').write_bytes((OUT/f'preflight/unit.{suffix}.txt').read_bytes())
    checks=h.d.inputs.api('actions/runs?head_sha='+SOURCE+'&per_page=100')
    m.need(checks['total_count'] == len(checks['workflow_runs']),'測定HEADの全Actionsページ')
    latest=[h.d.run_summary(r) for r in checks['workflow_runs']]
    terminal.update(record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        record_native_processes=0,record_accepted_test_reruns=0,record_compiles=0,record_new_tests=32,
        artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},
        measured_head_actions=latest,general_ci_all_success_claimed=False)
    terminal['preserved_failed_record']={'run_id':36567145293,'job_id':109401758947,'source_head':'d614c2adc22dc616ee48cf0489870a010487b789','conclusion':'failure','native_processes':0,'tracked_changes_pushed':False,'reason_ja':'成功ログ内のtest名skippedを誤拒否し、pipefail未指定で記録/guardの終了値が隠れた。commitは変更なしで失敗。footer判定とbash pipefailで修正。'}
    h.d.write(evidence/'terminal.json',terminal)
    review=dict(reviewed_at_utc='2026-09-29',scope='保存済み正式PPMの35anchorを目視。新しい画面生成なし。',
        anchors=json.loads((ROOT/m.DEV/'expected.json').read_text())['visual_review'],
        notes_ja='ハヤカ336円、窓switch、アマナ勝利/エリナバッジ/1500円、わざメモリー/せいたいレーダー/TM15、モスギス、PC回復、保存途中、cold全回復/5776円/badge1を確認。保存成功文言frameの採取は主張しない。')
    h.d.write(evidence/'visual-review.json',review)
    evidence_paths={p.relative_to(ROOT).as_posix() for p in evidence.rglob('*') if p.is_file()}
    checkpoint=dict(schema_version=1,task=m.TASK,status='PASS_AYAME_GYM_BADGE1_SAVE19_SCOPED',source_head=SOURCE,
        run_id=RUN,job_id=JOB,actions_completion_confirmed=True,actions_conclusion='success',
        record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        artifact=terminal['artifact'],verification=v,save19_accepted=True,
        save_byte_ledger=dict(binding=measured['save_byte_ledger'],changed_bytes=ledger['changed_bytes'],ranges=len(ledger['ranges']),artifact_only=True),
        source_bindings=measured['source_bindings'],evidence_bindings=h.d.bindings(evidence_paths),
        next_goal_ja=GOAL,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    h.d.write(ROOT/m.CP,checkpoint)
    guide=f'''# アヤメジム・バッジ1・Save19 限定受入

`{checkpoint['status']}`。支援story-fastで通常ハヤカ/アマナ2勝、窓のスイッチ、バッジ1、報酬、町のモスギス会話、PC通常回復、Save19と独立Continueを受入。自然難易度・自然育成/進化・全国図鑑・研究施設自然到達・全storyは未受入。

## 原本と検証

測定source `{SOURCE}`、run `{RUN}`、job `{JOB}`、upload/postを含む全7step成功。artifact `{ARTIFACT}`、{ARCHIVE['size']}bytes、SHA256 `{ARCHIVE['sha256']}`、期限 `{meta['expires_at']}`。全264memberと243画像を全byte検証し、35anchorを目視照合。全Save差分6817bytes/1718範囲と保存済みoracle全値が一致。ROM/Save/画像/全差分hexはartifactのみ、tracked text原本は `{EVIDENCE}`。

464/cold34入力、57403/cold2492frames。2戦の開始/勝利/復帰/解錠は16/49/52/52と92/141/152/162。交代UIと残留outcomeを別勝利に数えない。通常賞金336+1500円で3940→5776円。key items347/348/364、TM15=303を追加。他pocket不変。364の個別ownerは未同定のまま、HM05所持は主張しない。通常badge flag2080、trainer physical bits1422/1694、var4071=3→5/4072=0→1をROM rootと保存差分で照合した。

## 保存境界と未受入範囲

観測227/228は書込み途中、229/230はcounter19/field解錠。成功文言frame自体は未採取。独立Continueでmap5/4・7,4北・party4全回復/RP0・5776円・badge1、Save/RTC全131088bytes保持。前bank57344bytes、boxed PC、未使用party200bytesを保持。partyは歩行友情4bytesのみ、EXP/Lv100/種族不変。ROM宣言payload checksum42件と別S61E CRC/反転値、S61E payload差分3bytesを検証。NationalDex magic0/var404e0/flag840=0、分離progression原本とgrant owner不変。

旧hash-only WIP1processは未受入のまま保持。開発成功2process・正式成功2process、同じ73試験を146別件に数えない。記録時は新しい32拒否試験のみ、受入73試験/native/compile/ROM変更/旧区間再走0。一般CIのP03 capacity failureを専用run成功で隠さない。PR16 draft/open/未merge、release/active baseline切替なし。

## 次の唯一の開始点

{GOAL}

記録source `{os.environ['GITHUB_SHA']}`、run `{os.environ['GITHUB_RUN_ID']}`。記録workflow自身のpush/upload成功は自己予測せず、別APIとrecord-head.txt/record.zipで読戻し確認する。
'''
    (ROOT/m.GUIDE).write_text(guide,encoding='utf-8')
    m.need(h.d.bindings(protected) == protected,'旧受入source/evidence不変')
    state.setdefault('observed_head_history',[]).append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],
        checks=state['observed_head_checks'],reason_ja='受入済みSave18の先で完了したSave19を無再走回収。旧受入は不変。'))
    state['observed_head']=SOURCE
    state['observed_head_semantics']='アヤメジム2勝・badge1・通常報酬/回復Save19測定source。記録commit/自然育成/全story/active baselineではない。'
    state['observed_head_checks']=dict(scope_head=SOURCE,runs=latest,reason_ja='専用run36559147649/job109375512907全7stepと264memberを照合。一般CIの既存failureは別scope。')
    now=datetime.datetime.now(datetime.timezone.utc);state['observed_date_jst']=now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['story_gym']=dict(status=checkpoint['status'],checkpoint=m.CP,guide=m.GUIDE,run_id=RUN,artifact_id=ARTIFACT,
        story_fast_save=m.OUTPUT_SAVE,map=[5,4],xy=[7,4],facing=2,badge_count=1,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=GOAL,release_ready=False)
    state['next_action'].update(id='STORY_AFTER_AYAME_GYM_SAVE19',goal_ja=GOAL,
        read_paths=[m.GUIDE,m.CP,'docs/PR16_NATIONAL_DEX_OWNER_JA.md','content/modernization/pr16_national_dex_owner_checkpoint.json',
                    'content/modernization/pr16_story_acceleration_checkpoint.json',m.DEV+'/expected.json',SELF],
        stop_rule_ja='Save19より先の未完storyだけを自然Save/cold境界で区切る。464/cold34・73試験・旧BP/P08/Save1〜18は再走しない。全国図鑑の注入解禁/保存途中での成功判定は禁止。')
    state['bp']['next_step']=GOAL
    state['bp']['current_stop']='支援story-fastのアヤメジム2勝・badge1・通常報酬/モスギス会話・PC全回復Save19・独立Continueを限定受入。map5/4・7,4北・party4/RP0。NationalDex magic0維持。次はartifact11028517527から先だけ。'
    state['do_not_repeat'].append('Save19 run36559147649の464/cold34入力・73試験・2勝/badge1/通常報酬/回復保存Continueは受入済み。無影響の再走禁止。Save18以前も不変。')
    owned={m.CP,m.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|evidence_paths
    state['source_bindings'].update(h.d.bindings((owned|measure.CODE|{SELF,WF,TEST})-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=now.isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {m.TASK} / アヤメジム・badge1・Save19完了原本の無再走回収
- Version: story-gym-save19-v1
- Status: DONE（支援story新区間限定。自然育成/進化/全国図鑑/全story未完）
- Summary: Save18→通常ジム2勝・窓switch・badge1・報酬・モスギス会話→PC回復Save19/cold。再開MDのSave18停止と完了Actionsの不一致を解消。全264member/243画面/35目視anchor/全Save差分6817bytes・1718範囲を照合。
- Files changed: gym記録器・32拒否試験・closeout workflow、checkpoint/guide/text証跡、固定再開MD/JSON、両ログ。ROM/Save/画像/全差分hexはartifactのみ。
- Verify: run{RUN}/job{JOB}全7step成功、artifact{ARTIFACT}、464/cold34入力、cold全131088bytes、payload checksum42件/S61E CRC、旧bank/PC/Bag境界。記録native/compile/受入73試験再走0。新32試験とscoped final-index/private/resume/task graph/diff通過後のみcommit。一般CI全成功は主張しない。
- Commit: 測定{SOURCE}、回収WIP50b87e638b96、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。同branch非force pushと全text読戻し。
- Network: 固定GitHub run/artifactの再利用だけ。旧BP/P08/progression/grant owner/active baseline/source-lock不変。PR16未merge、releaseなし。
- Next: {GOAL}
'''
    for path in h.d.LOGS:
        with (ROOT/path).open('a',encoding='utf-8') as stream:stream.write(entry)
    PUBLIC.mkdir(parents=True,exist_ok=True);h.d.write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
    h.d.write(PUBLIC/'receipt.json',dict(status='RECORD_PREPARED_FROM_COMPLETED_SAVE19',terminal=terminal,owned=sorted(owned),
        verified_members=264,record_native_processes=0,record_accepted_test_reruns=0))


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
            data=h.d.git('show','HEAD:'+name);m.need(data == (ROOT/name).read_bytes(),'commit済みtext読戻し '+name);z.writestr(name,data)
        z.writestr('record-head.txt',h.d.git('rev-parse','HEAD'))
    (PUBLIC/'record-head.txt').write_bytes(h.d.git('rev-parse','HEAD'))


if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot)
    m.need(len(sys.argv) == 2 and sys.argv[1] in actions,'record|guard|snapshot');actions[sys.argv[1]]()
