#!/usr/bin/env python3
"""完了済み503電話/Save21原本のみを記録。nativeと受入62試験を再走しない。"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save21_accept as m
import pr16_story_save21_measure as measure
import pr16_story_after_maori_measure as transport
import pr16_research_story_route_actions as h
import pr16_story_gym_record as log_gate
SOURCE='b58a6356c9b100a9180a9af955d25e1c6be48d0c'
RUN=36662466133
JOB=109719980409
CONFIG=m.DEV+'/record-input.json'
SELF='scripts/pr16_story_save21_record.py'
TEST='tests/test_pr16_story_save21_record.py'
WF='.github/workflows/pr16-story-save21-record.yml'
CODE={SELF,TEST,WF,CONFIG}
EVIDENCE='content/modernization/pr16_story_save21_evidence'
OUT=ROOT/'.local/pr16-story-save21-record'
PUBLIC=OUT/'public'
STEPS=['Set up job','Run actions/checkout@v4','Scoped source guard before native',
       'New Route503 phone Save21 interval and independent Continue only','Lightweight task graph',
       'Run actions/upload-artifact@v4','Post Run actions/checkout@v4','Complete job']
COUNTS=dict(source_head=SOURCE,run_id=RUN,new_tests=62,development_native_processes=2,
    development_native_failures=0,formal_native_processes=2,accepted_case_reruns=0,
    accepted_test_reruns=0,compiles=0,development_cold_prefix_preserved=True,development_cold_menu_end_accepted=False)
TEXT=('verification.json','measurement.json','manifest.json','parent.json','unit.stdout.txt','unit.stderr.txt',
      'progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json',
      'continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json',
      'progress-development.stdout.txt','progress-development.commands.txt',
      'continue-development.stdout.txt','continue-development.commands.txt')


def terminal(run,jobs):
    required=dict(id=RUN,head_sha=SOURCE,head_branch=m.source.BRANCH,path=measure.WF,
                  status='completed',conclusion='success',run_attempt=1)
    m.need(all(type(run.get(k)) is type(v) and run[k]==v for k,v in required.items()),'完了済み正式run初回だけ')
    m.need(type(jobs.get('total_count')) is int and jobs['total_count']==1 and len(jobs.get('jobs',[]))==1,'全jobページ')
    job=jobs['jobs'][0];required=dict(id=JOB,run_id=RUN,name='continuation',status='completed',conclusion='success')
    m.need(all(type(job.get(k)) is type(v) and job[k]==v for k,v in required.items()),'正式job identity/終端')
    m.need([x.get('name') for x in job.get('steps',[])]==STEPS and
           all(x.get('status')=='completed' and x.get('conclusion')=='success' for x in job['steps']),
           'upload/postを含む全8step成功')
    return dict(run=h.d.run_summary(run),job=job)


def counts(data):
    m.need(all(type(data.get(k)) is type(v) and data[k]==v for k,v in COUNTS.items()),'実行会計を再解釈しない')


def members(folder,expected):
    manifest=m.load((folder/'manifest.json').read_bytes())
    names={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    m.need(type(expected) is int and len(manifest)==expected and names==set(manifest)|{'manifest.json'},'全member集合')
    for name,binding in manifest.items():m.need(m.identity((folder/name).read_bytes())==binding,'全member byte '+name)
    return manifest


def goal(artifact):
    return (f'story-fastの唯一の開始点はartifact{artifact}のstory-fast.srm（Save21、131088bytes、'
        f'SHA256 {m.OUTPUT_SAVE["sha256"]}）。503番道路map3/21・24,17西・party4/RP0、6256円・badge1、'
        'var4071=6/4072=1。ミュウツーHP349/354・サイコブレイクPP5、他3体HP満タン。'
        'トシヒデ1勝/240円・電話会話/自動移動・通常Save21/独立Continueは完了。'
        'HM05所持、通常UIで4体とも非適合表示・ミュウ選択拒否。習得/使用/原因解決は未完。'
        '同じ拒否入力を繰り返さず、必要時は固定ROMの互換性判定ownerを限定照合し、自然取得条件を満たす'
        '承認済みfield-utility分離fixtureの適用条件を読む。基準外の習得を盲追加しない。'
        '現在地から通常storyの未完区間だけをSave/cold境界で進める。181/cold33入力・62試験・'
        'Save1〜20/旧BP/P08は無影響に再走しない。分離progression原本Axew Lv37/EXP68589と'
        'NationalDex magic0・grant ownerを保全し、flag/var注入で解禁しない。正規全国図鑑解禁、'
        '自然育成/進化、Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。')


def record():
    from pr16_learnset_compact_record import publish_resume
    os.chdir(ROOT);h.d.current();state=h.source_check()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/m.CP).exists() and not (ROOT/EVIDENCE).exists(),'未記録の初回だけ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    c=h.d.read(ROOT/CONFIG)
    m.need(set(c['record_source_bindings'])=={SELF,TEST} and h.d.bindings(c['record_source_bindings'])==c['record_source_bindings'],'ローカル検証済み記録source全byte')
    m.need(c['task']==m.TASK and c['source_head']==SOURCE and c['run_id']==RUN and c['job_id']==JOB,'固定測定identity')
    done=terminal(h.d.inputs.api(f'actions/runs/{RUN}'),h.d.inputs.api(f'actions/runs/{RUN}/jobs?per_page=100'))
    meta,z=transport.archive(c['artifact_id'],RUN,c['archive'],SOURCE)
    m.need(meta['name']=='pr16-story-save21-checkpoint','正式artifact名')
    folder=OUT/'original';folder.mkdir(parents=True)
    with z:z.extractall(folder)
    members(folder,c['manifest_members'])
    measured=h.d.read(folder/'measurement.json');counts(measured)
    m.need(set(measured['source_bindings'])==measure.CODE,'全測定source集合')
    for path,binding in measured['source_bindings'].items():
        m.need(m.identity((ROOT/path).read_bytes())==binding and m.identity(h.d.git('show',SOURCE+':'+path))==binding,
               '測定source変更を自動追認しない '+path)
    log_gate.unit_original((folder/'unit.stdout.txt').read_bytes(),(folder/'unit.stderr.txt').read_bytes(),62)
    result,ledger=m.verify(folder);result=json.loads(json.dumps(result))
    m.need(result==measured['result']==h.d.read(folder/'verification.json') and
           m.identity((folder/'verification.json').read_bytes())==c['verification'],'全oracle値と原本')
    m.need(ledger==h.d.read(folder/'save-byte-ledger.json') and ledger['changed_bytes']==6988 and len(ledger['ranges'])==1783 and
           m.identity((folder/'save-byte-ledger.json').read_bytes())==measured['save_byte_ledger'],'全差分ledger')
    screen=(folder/'continue/screen-0005.ppm').read_bytes()
    m.need(m.identity(screen)==c['final_cold_screen'],'追加cold終端の目視原本全byte')
    m.screen_bytes(screen,dict(sha256=c['final_cold_screen']['sha256']))
    log_gate.unit_original((OUT/'preflight/unit.stdout.txt').read_bytes(),(OUT/'preflight/unit.stderr.txt').read_bytes(),12)
    evidence=ROOT/EVIDENCE;evidence.mkdir()
    for name in TEXT:
        raw=(folder/name).read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'tracked textだけ')
        path=evidence/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    for suffix in ('stdout','stderr'):
        (evidence/f'record-unit.{suffix}.txt').write_bytes((OUT/f'preflight/unit.{suffix}.txt').read_bytes())
    checks=h.d.inputs.api('actions/runs?head_sha='+SOURCE+'&per_page=100')
    m.need(checks['total_count']==len(checks['workflow_runs']),'測定HEAD Actions全ページ')
    observed=[h.d.run_summary(r) for r in checks['workflow_runs']]
    done.update(artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},
        measured_head_checks=observed,general_ci_all_success_claimed=False,
        record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        record_native_processes=0,record_accepted_test_reruns=0,record_new_tests=12,record_compiles=0)
    prior_run=h.d.inputs.api('actions/runs/36573749814')
    prior_jobs=h.d.inputs.api('actions/runs/36573749814/jobs?per_page=100')
    m.need(prior_run['head_sha']=='556e4b2150df292af3ab90d8e88db9e41a759dfc' and
        prior_run['path']=='.github/workflows/pr16-story-hm05-record.yml' and
        prior_run['status']=='completed' and prior_run['conclusion']=='success' and prior_run['run_attempt']==1 and
        prior_jobs['total_count']==len(prior_jobs['jobs'])==1 and prior_jobs['jobs'][0]['id']==109423933171 and
        len(prior_jobs['jobs'][0]['steps'])==11 and all(s['status']=='completed' and s['conclusion']=='success'
        for s in prior_jobs['jobs'][0]['steps']),'旧Save20記録のpush/upload/post完了を別APIで照合')
    done['inherited_save20_record_completion']=dict(run=h.d.run_summary(prior_run),
        job=prior_jobs['jobs'][0],reflected_head='e517baa451b613283ca87bc05304bed42b75ded9',new_native_processes=0)
    h.d.write(evidence/'terminal.json',done)
    h.d.write(evidence/'visual-review.json',dict(source_head=SOURCE,run_id=RUN,
        anchors=h.d.read(ROOT/m.DEV/'expected.json')['visual_review'],additional_final_cold_screen=c['final_cold_screen'],
        total_reviewed_anchors=39,notes_ja='HM05通常非適合4体/ミュウ拒否、503番道路、トシヒデ戦/240円、電話会話/自動移動、書込途中、cold party HP349/354・6256円/badge1、追加cold5の操作可能fieldを目視。保存成功文言frame、HM05習得/使用・原因解決は主張しない。'))
    paths={p.relative_to(ROOT).as_posix() for p in evidence.rglob('*') if p.is_file()};next_goal=goal(meta['id'])
    checkpoint=dict(schema_version=1,task=m.TASK,status=result['status'],source_head=SOURCE,run_id=RUN,job_id=JOB,
        actions_completion_confirmed=True,actions_conclusion='success',artifact=done['artifact'],verification=result,
        save21_accepted=True,source_bindings=measured['source_bindings'],evidence_bindings=h.d.bindings(paths),
        record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        save_byte_ledger=dict(binding=measured['save_byte_ledger'],changed_bytes=6988,ranges=1783,artifact_only=True),
        next_goal_ja=next_goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    h.d.write(ROOT/m.CP,checkpoint)
    guide=f'''# 503番道路の電話イベント・Save21 限定受入

`{result['status']}`。支援story-fastのSave20後だけを進め、トシヒデ通常1勝、電話イベント/自動移動、通常Save21と独立Continueを受入。HM05は通常UIで拒否を確認しただけで、習得/使用・原因修正を合格にしない。自然育成/進化、全国図鑑、研究施設自然到達、全storyは未受入。

## 完了原本と実行会計

測定source `{SOURCE}`、run `{RUN}`、job `{JOB}`、upload/postを含む全8step成功。artifact `{meta['id']}`、{c['archive']['size']}bytes、SHA256 `{c['archive']['sha256']}`、期限 `{meta['expires_at']}`。全{c['manifest_members']}member/61画面を全byte検証。開発38anchorと正式pixelを結び、追加cold5を目視して計39anchor。

181/cold33入力、16528/cold2760frames。開発2・正式2native成功、compile/ROM変更/旧受入case再走0。新62試験を開発と正式で別124件へ水増ししない。記録は原本読取のみでnative/受入62試験再走0、別の記録拒否12試験。開発coldはcard後menuで終了し未受入。正式coldは原本prefixを全保持した後に待機/B/待機を追加し、observe5でfield=true/lock0を確認した。

## 通常操作で確定した範囲

HM05ケース→4体とも「おぼえられない」→ミュウ選択で相性拒否→field復帰。観測5/7/8/10とparty全byte不変を結合。ミュウ/ビーダルの4技/PPは空のまま。表示だけから互換性判定の原因を断定せず、基準外の習得や移動用fixtureを追加していない。HM05取得自体はSave20の既受入原本を継承する。

アヤメ南側から503番道路へ。map3/21 object3・13,12の通常trainer101トシヒデに1勝、賞金240円で6016→6256円。観測19で戦闘開始、24は同戦闘内の交代menuを取消、35で勝利、37で賞金、38でfield復帰。残るbattle_flags12/outcome1を追加勝利と数えない。野生勝利/離脱/捕獲/敗北/通常回復0、rematch1027は未実行。

map3/21 coord表のx21〜24/y17・var4071=5を実ROM headerから照合。今回の到達はx23のrootだけで、電話会話「ニューアイランド」「メア」等と自動移動を観測40〜47に結合した。var4071=6更新owner、非表示flag4366のownerを2nodes/診断0で照合。他3coordの実到達や全storyの完了を証明しない。

## Save差分と安全境界

Save21 `{m.OUTPUT_SAVE['sha256']}`、131088bytesを独立Continue後も全保持。map3/21・24,17西、party4/RP0、6256円・badge1・var4071=6/4072=1。ミュウツーHP349/354、サイコブレイクPP10→5。他3体HP満タン。600partybytes中HP/PP各1byteと2体EV欄各1byteだけ変化し、EXP/種族/Lv100/4技/装備は不変。これは自然育成/進化/全EV因果ケースの受入ではない。

通常ケースを開いた際にmachines先頭2slotがTM15/HM05→HM05/TM15へ整列した。全item/countと他Bag slotは不変。ローカル検証は当初の「Bag全slot不変」という誤仮定を拒否し、この具体的な順序交換だけを許可した。nativeを再実行して都合のよい結果を採り直していない。

全Save差分6988bytes/1783範囲。旧Save20 bank57344bytes、boxed PC、未使用party200bytes保持。ROM宣言checksum42件、S61E CRC/反転値を検証。legacy差分はtrainer physical1381のみ、変数4021=24→92/4022=0→2/4071=5→6だけ。S61E payloadのoffset257:1→65は拡張flag4366/index2062のbit6。NationalDex magic0/var404e0/flag840=0と分離progression/grant owner不変。全差分hex/ROM/Save/画像はartifactのみ。tracked text原本は `{EVIDENCE}`。

電話中7枚だけSave y20とlive y17の同期遅れを、正確なframe/座標/callback/hash/lock付きで区別した。旧判定器は変更せず、会話中をfield到達にしない。47で座標一致/解錠。51/52は書込途中、53/54でcounter21/Flash/field安定。保存成功文言frameは採取していない。

## 既存結果・CIとの切分け

旧Save20記録run36573749814/source556e4b21はpush/upload/postを含む全11step成功、反映HEAD e517baa4を別APIで照合した。旧受入Save1〜20/旧BP/P08/自然成長原本を再走しない。一般CIのP03 capacity既知source不一致とaction_requiredは専用成功と別scope。全CI成功、PR merge、release、active baseline切替は主張しない。

## 次の唯一の開始点

{next_goal}

記録source `{os.environ['GITHUB_SHA']}`、run `{os.environ['GITHUB_RUN_ID']}`。記録自身のpush/uploadは自己予測せず、別API・record-head.txt・record.zipで読戻し確認する。
'''
    (ROOT/m.GUIDE).write_text(guide,encoding='utf-8')
    m.need(h.d.bindings(protected)==protected,'旧受入source/evidence不変')
    state.setdefault('observed_head_history',[]).append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],
        checks=state['observed_head_checks'],reason_ja='Save20の先の503電話イベント/Save21だけを新規測定して記録。'))
    state['observed_head']=SOURCE
    state['observed_head_semantics']='503電話イベント・トシヒデ1勝・Save21測定source。HM05拒否を観測したが習得/使用/原因修正は未受入。記録commit/自然育成/全story/active baselineではない。'
    state['observed_head_checks']=dict(scope_head=SOURCE,runs=observed,reason_ja='専用runの全8step完了と全Save/画面を照合。一般CIは別scopeで全成功を主張しない。')
    now=datetime.datetime.now(datetime.timezone.utc);state['observed_date_jst']=now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['story_save21']=dict(status=result['status'],checkpoint=m.CP,guide=m.GUIDE,run_id=RUN,artifact_id=meta['id'],
        story_fast_save=m.OUTPUT_SAVE,map=[3,21],xy=[24,17],facing=3,badge_count=1,money=6256,rp=0,
        story_vars={'4071':6,'4072':1},hm05_owned=True,hm05_taught_or_used=False,hm05_attempt_rejected=True,
        hm05_root_cause_resolved=False,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=next_goal,release_ready=False)
    state['story_hm05']['record_completion']=done['inherited_save20_record_completion']
    state['next_action'].update(id='STORY_AFTER_ROUTE503_PHONE_SAVE21',goal_ja=next_goal,
        read_paths=[m.GUIDE,m.CP,'docs/PR16_NATIONAL_DEX_OWNER_JA.md','content/modernization/pr16_national_dex_owner_checkpoint.json',
                    'content/modernization/pr16_story_acceleration_checkpoint.json',m.DEV+'/expected.json',SELF],
        stop_rule_ja='Save21より先だけを通常story/Save/cold境界で区切る。181/cold33入力・62試験・Save1〜20/旧BP/P08は無影響に再走しない。HM05同一拒否入力の重複・互換性の盲修正・全国図鑑flag/var注入解禁は禁止。')
    state['bp']['next_step']=next_goal
    state['bp']['current_stop']='支援story-fastでHM05通常拒否・トシヒデ1勝/240円・503電話/自動移動・Save21/独立Continueを限定受入。map3/21・24,17西・party4/RP0・6256円・badge1。HM05未習得/未使用・原因未解決。NationalDex magic0保全。'
    state['do_not_repeat'].append(f'Save21 run{RUN}の181/cold33入力・62試験・HM05拒否観測/トシヒデ1勝/電話イベント/保存Continueは記録済み。無影響の再走禁止。Save20以前も不変。')
    owned={m.CP,m.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|measure.CODE|{'.github/workflows/pr16-story-save21-source.yml'})-{h.d.STATE,h.d.DOC,*h.d.LOGS}))
    publish_resume(state);stamp=now.isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {m.TASK} / 503電話イベント・Save21新区間
- Version: story-route503-save21-v1
- Status: DONE（支援story新区間限定。HM05習得/使用/原因修正・自然育成/全国図鑑/全story未完）
- Summary: Save20→HM05通常拒否→トシヒデ1勝/240円→電話/自動移動→Save21/cold。全61画面/39目視anchor/全差分6988bytes・1783範囲。HMケース順序交換と会話中座標同期遅れ7枚を限定判定し、途中Save/menuを合格にしない。
- Files changed: 新oracle/62拒否試験・測定器・開発text原本・記録器/12拒否試験・専用workflow・checkpoint/guide/text証跡、固定再開MD/JSON、両ログ。ROM/save/全差分hexはartifactのみ。
- Verify: run{RUN}/job{JOB}全8step成功、artifact{meta['id']}、181/cold33入力、Save/RTC全131088bytes保持。checksum42件/S61E CRC/旧bank/PC/全item個数。開発native2/正式native2、記録native0・受入試験再走0・compile0。新記録12試験/scoped final-index/private/resume/task graph/diff通過後のみcommit。一般CI全成功は主張しない。
- Commit: 測定{SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。小分けWIPを同branchへ逐次反映し、完了記録は非force pushと全text読戻し。
- Network: GitHub connector/固定Actions artifactだけ。開始HEAD e517baa451b613283ca87bc05304bed42b75ded9・source転送run36659873782・旧Save20記録run36573749814全11step成功を照合。旧BP/P08/Save1〜20/progression/grant owner/active baseline/source-lock不変。PR16未merge、releaseなし。旧P03 capacity failureは別scopeとして保持。
- Next: {next_goal}
'''
    for name in h.d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write(entry)
    PUBLIC.mkdir(parents=True,exist_ok=True);h.d.write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
    h.d.write(PUBLIC/'receipt.json',dict(status='RECORD_PREPARED_FROM_COMPLETED_SAVE21',terminal=done,owned=sorted(owned),
        manifest_members=c['manifest_members'],record_native_processes=0,record_accepted_test_reruns=0))


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT)
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard()
    h.d.git('diff','--cached','--check')


def snapshot():
    with zipfile.ZipFile(PUBLIC/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in h.d.read(OUT/'owned.json'):
            raw=h.d.git('show','HEAD:'+name);m.need(raw==(ROOT/name).read_bytes(),'commit済み全text読戻し '+name);z.writestr(name,raw)
        z.writestr('record-head.txt',h.d.git('rev-parse','HEAD'))
    (PUBLIC/'record-head.txt').write_bytes(h.d.git('rev-parse','HEAD'))


if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot)
    m.need(len(sys.argv)==2 and sys.argv[1] in actions,'record|guard|snapshot');actions[sys.argv[1]]()
