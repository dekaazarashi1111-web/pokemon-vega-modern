#!/usr/bin/env python3
"""完了済みHM05/Save20原本のみを記録。nativeと受入60試験を再走しない。"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_hm05_accept as m
import pr16_story_hm05_measure as measure
import pr16_story_after_maori_measure as transport
import pr16_research_story_route_actions as h
import pr16_story_gym_record as log_gate
SOURCE='b47f2d1720b200a7eb01888691e1e489c3df215e'
RUN=36572961114
JOB=109421243251
CONFIG=m.DEV+'/record-input.json'
SELF='scripts/pr16_story_hm05_record.py'
TEST='tests/test_pr16_story_hm05_record.py'
WF='.github/workflows/pr16-story-hm05-record.yml'
CODE={SELF,TEST,WF,CONFIG}
EVIDENCE='content/modernization/pr16_story_hm05_evidence'
OUT=ROOT/'.local/pr16-story-hm05-record'
PUBLIC=OUT/'public'
STEPS=['Set up job','Run actions/checkout@v4','Scoped source guard before native',
       'New HM05 Save20 interval and independent Continue only','Lightweight task graph',
       'Run actions/upload-artifact@v4','Post Run actions/checkout@v4','Complete job']
COUNTS=dict(source_head=SOURCE,run_id=RUN,new_tests=60,development_native_processes=2,
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
    return (f'story-fastの唯一の開始点はartifact{artifact}のstory-fast.srm（Save20、131088bytes、'
        f'SHA256 {m.OUTPUT_SAVE["sha256"]}）。アヤメPC map5/4・7,4北・party4全回復/RP0、'
        '6016円・badge1・var4071=5/4072=1、HM05フラッシュ所持から通常storyの未完区間だけを進める。'
        'HM05は未習得/未使用。通常NPC取得、新トレーナー2勝、野生2離脱、PC回復/Save20/coldは完了。'
        '248/cold59入力・60試験・Save1〜19/旧BP/P08は無影響に再走しない。'
        '分離progression原本Axew Lv37/EXP68589とNationalDex magic0・grant ownerを保全し、flag/var注入で解禁しない。'
        '正規全国図鑑解禁、自然育成/進化、Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。')


def record():
    from pr16_learnset_compact_record import publish_resume
    os.chdir(ROOT);h.d.current();state=h.source_check()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/m.CP).exists() and not (ROOT/EVIDENCE).exists(),'未記録の初回だけ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    c=h.d.read(ROOT/CONFIG)
    m.need(c['task']==m.TASK and c['source_head']==SOURCE and c['run_id']==RUN and c['job_id']==JOB,'固定測定identity')
    done=terminal(h.d.inputs.api(f'actions/runs/{RUN}'),h.d.inputs.api(f'actions/runs/{RUN}/jobs?per_page=100'))
    meta,z=transport.archive(c['artifact_id'],RUN,c['archive'],SOURCE)
    m.need(meta['name']=='pr16-story-hm05-checkpoint','正式artifact名')
    folder=OUT/'original';folder.mkdir(parents=True)
    with z:z.extractall(folder)
    members(folder,c['manifest_members'])
    measured=h.d.read(folder/'measurement.json');counts(measured)
    m.need(set(measured['source_bindings'])==measure.CODE,'全測定source集合')
    for path,binding in measured['source_bindings'].items():
        m.need(m.identity((ROOT/path).read_bytes())==binding and m.identity(h.d.git('show',SOURCE+':'+path))==binding,
               '測定source変更を自動追認しない '+path)
    log_gate.unit_original((folder/'unit.stdout.txt').read_bytes(),(folder/'unit.stderr.txt').read_bytes(),60)
    result,ledger=m.verify(folder);result=json.loads(json.dumps(result))
    m.need(result==measured['result']==h.d.read(folder/'verification.json') and
           m.identity((folder/'verification.json').read_bytes())==c['verification'],'全oracle値と原本')
    m.need(ledger==h.d.read(folder/'save-byte-ledger.json') and ledger['changed_bytes']==6783 and len(ledger['ranges'])==1784 and
           m.identity((folder/'save-byte-ledger.json').read_bytes())==measured['save_byte_ledger'],'全差分ledger')
    screen=(folder/'continue/screen-0010.ppm').read_bytes()
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
    h.d.write(evidence/'terminal.json',done)
    h.d.write(evidence/'visual-review.json',dict(source_head=SOURCE,run_id=RUN,
        anchors=h.d.read(ROOT/m.DEV/'expected.json')['visual_review'],additional_final_cold_screen=c['final_cold_screen'],
        total_reviewed_anchors=36,notes_ja='通常HM05取得とcase所持、128+112円、2野生離脱、回復、書込途中、cold全回復/6016円/badge1、追加cold10のPC fieldを目視。保存成功文言frame、HM05習得/使用は主張しない。'))
    paths={p.relative_to(ROOT).as_posix() for p in evidence.rglob('*') if p.is_file()};next_goal=goal(meta['id'])
    checkpoint=dict(schema_version=1,task=m.TASK,status=result['status'],source_head=SOURCE,run_id=RUN,job_id=JOB,
        actions_completion_confirmed=True,actions_conclusion='success',artifact=done['artifact'],verification=result,
        save20_accepted=True,source_bindings=measured['source_bindings'],evidence_bindings=h.d.bindings(paths),
        record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        save_byte_ledger=dict(binding=measured['save_byte_ledger'],changed_bytes=6783,ranges=1784,artifact_only=True),
        next_goal_ja=next_goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    h.d.write(ROOT/m.CP,checkpoint)
    guide=f'''# HM05通常取得・Save20 限定受入

`{result['status']}`。支援story-fastの未完区間のみ。Save19からRoute502の通常NPC会話でHM05「フラッシュ」取得、新トレーナー2勝、野生2離脱、PC通常回復、Save20と独立Continueを受入。HM05習得/使用、自然育成/進化、全国図鑑、研究施設自然到達、全storyは未受入。

## 完了原本

測定source `{SOURCE}`、run `{RUN}`、job `{JOB}`、upload/postを含む全8step成功。artifact `{meta['id']}`、{c['archive']['size']}bytes、SHA256 `{c['archive']['sha256']}`、期限 `{meta['expires_at']}`。全{c['manifest_members']}member/82画面を全byte検証。開発35anchorを正式pixelに結び、追加cold10を目視して合計36anchor。記録は完了原本の読取だけでnative/受入60試験再走/compile0。

248/cold59入力、23900/cold3690frames。ノゾミ128円・タツヤ112円の2勝で5776→6016円。戦闘は12→19→22と25→30→32、野生フロン/スバメは42→45→46と49→50→51で通常離脱。捕獲/野生勝利/敗北0。HM05はmap3/20 object5・7,4のROM checkitem/checkitemspace/additem343と通常会話35〜40を照合。trainer91/116とphysical bits1371/1396を照合し、未実行rematch分岐を合格にしない。

## 保存・回復・境界

Save20 `{m.OUTPUT_SAVE['sha256']}`、131088bytesを独立Continue後も全保持。PC map5/4・7,4北・party4全回復/RP0・badge1・6016円・HM05所持。Bag全slotはmachines slot1の(0,0)→(343,1)以外不変。手持ち600bytes中友情2bytesとEV欄2bytesのみ変化、EXP/種族/Lv100不変。これはEV因果全ケースや自然育成の受入ではない。

全Save差分6783bytes/1784範囲を照合。旧Save19 bank57344bytes、boxed PC、未使用party200bytes保持。ROM宣言payload checksum42件、S61E CRC/反転値を検証しS61E payload不変。legacy変数4021=46→24/4022=3→0以外不変。NationalDex magic0/var404e0/flag840=0、story4071=5/4072=1、分離progression/grant owner不変。全差分hex/ROM/Save/画像はartifactだけ、tracked text原本は `{EVIDENCE}`。

load中1枚の転送先Save座標/転送元live座標不一致だけを種別付きで許可し、field到達にはしない。旧判定器は不変。観測64〜68は書込途中、69/70でcounter20/Flash安定/通常callback/lock0。warm終端の旧field補助述語falseを改竄せず記録。保存成功文言frameは未採取。開発coldはcard/menu終了で未受入、正式coldはその原本prefixを全保持し、追加待機/B/待機後のobserve10でfield=true/lock0を確認した。開発2・正式2native成功。60試験を開発と正式の計120別件に水増ししない。

## 既存結果との切分け

Save19のジム2勝/エルナトバッジ/通常報酬/Save19受入はd2a97721で記録済み。旧視覚注釈の「エリナ」は「エルナト」の誤字で、旧raw画面/flag2080/受入値は変更していない。旧一般CI run36559155007はP03 capacityで `tested source changed: overlays/qol_production/qol_production.c`、25試験中2ERROR。旧原本とのsource一致規約は緩めず専用Actions成功と区別する。一般CI全成功/PR merge/release/active baseline切替は主張しない。

## 次の唯一の開始点

{next_goal}

記録source `{os.environ['GITHUB_SHA']}`、run `{os.environ['GITHUB_RUN_ID']}`。記録自身のpush/upload成功は自己予測せず、別API・record-head.txt・record.zipで読戻し確認する。
'''
    (ROOT/m.GUIDE).write_text(guide,encoding='utf-8')
    m.need(h.d.bindings(protected)==protected,'旧受入source/evidence不変')
    state.setdefault('observed_head_history',[]).append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],
        checks=state['observed_head_checks'],reason_ja='受入済みSave19の先の通常HM05取得/Save20を新規測定して記録。'))
    state['observed_head']=SOURCE
    state['observed_head_semantics']='HM05通常取得・新2勝/野生2離脱・PC回復Save20測定source。記録commit/自然育成/全story/active baselineではない。'
    state['observed_head_checks']=dict(scope_head=SOURCE,runs=observed,reason_ja='専用runの全8step完了原本と全Save/画面を照合。一般CIは別scope。')
    now=datetime.datetime.now(datetime.timezone.utc);state['observed_date_jst']=now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['story_hm05']=dict(status=result['status'],checkpoint=m.CP,guide=m.GUIDE,run_id=RUN,artifact_id=meta['id'],
        story_fast_save=m.OUTPUT_SAVE,map=[5,4],xy=[7,4],facing=2,badge_count=1,hm05_owned=True,hm05_taught_or_used=False,
        record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=next_goal,release_ready=False)
    state['next_action'].update(id='STORY_AFTER_HM05_SAVE20',goal_ja=next_goal,
        read_paths=[m.GUIDE,m.CP,'docs/PR16_NATIONAL_DEX_OWNER_JA.md','content/modernization/pr16_national_dex_owner_checkpoint.json',
                    'content/modernization/pr16_story_acceleration_checkpoint.json',m.DEV+'/expected.json',SELF],
        stop_rule_ja='Save20より先だけを通常story/Save/cold境界で区切る。248/cold59入力・60試験・Save1〜19/旧BP/P08は無影響に再走しない。全国図鑑の注入解禁は禁止。')
    state['bp']['next_step']=next_goal
    state['bp']['current_stop']='支援story-fastで通常HM05取得・新trainer2勝/野生2離脱・PC全回復Save20/独立Continueを限定受入。map5/4・7,4北・party4/RP0・6016円・badge1。HM05未習得/未使用。NationalDex magic0保全。'
    state['do_not_repeat'].append(f'Save20 run{RUN}の248/cold59入力・60試験・通常HM05/2勝/2離脱/PC回復/保存Continueは受入済み。無影響の再走禁止。Save19以前も不変。')
    owned={m.CP,m.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|measure.CODE|{m.DEV+'/start.json'})-{h.d.STATE,h.d.DOC,*h.d.LOGS}))
    publish_resume(state);stamp=now.isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {m.TASK} / HM05通常取得・Save20新区間
- Version: story-hm05-save20-v1
- Status: DONE（支援story新区間限定。HM05習得/使用・自然育成/全国図鑑/全story未完）
- Summary: Save19→通常trainer2勝/240円・HM05取得・野生2離脱→PC通常回復Save20/cold。全82画面/36目視anchor/全差分6783bytes・1784範囲を照合。
- Files changed: 専用oracle/60拒否試験・測定器・開発text原本・記録器/12拒否試験・workflow・checkpoint/guide/text証跡、固定再開MD/JSON、両ログ。private binary/全差分hexはartifactのみ。
- Verify: run{RUN}/job{JOB}全8step成功、artifact{meta['id']}、248/cold59入力、Save/RTC全131088bytes保持。payload checksum42件/S61E CRC/旧bank/PC/Bag境界。開発native2/正式native2、記録native0・受入試験再走0・compile0。新記録12試験/scoped final-index/private/resume/task graph/diff通過後のみcommit。一般CI全成功は主張しない。
- Commit: 測定{SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。同branch非force pushと全text読戻し。
- Network: 固定GitHub artifactを再利用。旧BP/P08/Save1〜19/progression/grant owner/active baseline/source-lock不変。PR16未merge、releaseなし。旧P03 capacity source不一致failureは別scopeとして保持。
- Next: {next_goal}
'''
    for name in h.d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write(entry)
    PUBLIC.mkdir(parents=True,exist_ok=True);h.d.write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
    h.d.write(PUBLIC/'receipt.json',dict(status='RECORD_PREPARED_FROM_COMPLETED_SAVE20',terminal=done,owned=sorted(owned),
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
