#!/usr/bin/env python3
"""Save24の保存原本を記録。失敗2件と旧静的候補を保ち、nativeを再走しない。"""
from __future__ import annotations
import ast
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save24_accept as a
import pr16_research_story_route_actions as h
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
BASE=a.SOURCE
TASK=a.d.TASK
OUT=ROOT/'.local/pr16-story-save24-record'
PUBLIC=OUT/'public'
CODE={'scripts/pr16_story_save24_accept.py','scripts/pr16_story_save24_record.py',
      'tests/test_pr16_story_save24_accept.py',a.VISUAL,'.github/workflows/pr16-story-save24-record.yml'}
TEXT=['measurement.json','parent.json','manifest.json','terrain.json','failed-attempt-receipt.json',
      'progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json',
      'continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json',
      'failed-attempt/failure.json','failed-attempt/manifest.json','failed-attempt/progress/commands.txt',
      'failed-attempt/progress/stdout.txt','failed-attempt/progress/execution.json']


def terminal(run_id,head,job_id,conclusions):
    run=h.d.inputs.api('actions/runs/'+str(run_id));jobs=h.d.inputs.api('actions/runs/'+str(run_id)+'/jobs?per_page=100')
    need(run['head_sha']==head and run['head_branch']=='codex/modernization-followup-20260908' and
         run['status']=='completed' and run['run_attempt']==1 and jobs['total_count']==len(jobs['jobs'])==1,
         '外部APIで完了identity')
    j=jobs['jobs'][0]
    need(j['id']==job_id and j['status']=='completed' and [x['conclusion'] for x in j['steps']]==conclusions and
         all(x['status']=='completed' for x in j['steps']),'全step終端を確認')
    expected='failure' if 'failure' in conclusions else 'success'
    need(run['conclusion']==j['conclusion']==expected,'過去failureをsuccessへ改作しない')
    return dict(run=h.d.run_summary(run),job=j)


def prior_preflight():
    head='45ccca9b8e123b7bd33af73a448cc39a919daf69'
    done=terminal(37093437062,head,111118427413,['success','success','success','failure','skipped','success','success','success'])
    meta,z=a.d.m.transport.archive(11263278045,37093437062,
        dict(size=17404809,sha256='f60140ed82ae147003c8e99c50bff3ce85d3640510158c63b5550e0e936c0553'),head)
    with z:
        failure=json.loads(z.read('failure.json'))
        need(failure['source_head']==head and failure['run_id']==37093437062 and failure['native_processes']==0 and
             failure['exception_type']=='ValueError' and not any(n.startswith('progress/') for n in z.namelist()),
             '砂床whitelist事前検査のみ・native0')
    # 同じwalk/save controllerの12試験は成功stepから再利用し、地形追加7件とは分離。
    old=h.d.git('show',head+':scripts/pr16_story_save24_detour.py').decode()
    new=(ROOT/'scripts/pr16_story_save24_detour.py').read_text()
    def functions(source):
        return {n.name:ast.get_source_segment(source,n) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
    of,nf=functions(old),functions(new)
    need(all(of[k]==nf[k] for k in ('walk','save')),'旧12試験のcontrollerは不変')
    need(h.d.git('show',head+':tests/test_pr16_story_save24_detour.py')==
         (ROOT/'tests/test_pr16_story_save24_detour.py').read_bytes(),'旧12試験source不変')
    return dict(terminal=done,artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},
        failure=failure,new_native_processes=0,reused_controller_tests=12,replayed_tests=0,
        resolution_ja='既通行の砂床0x2bを許可地形へ追加。新7地形試験だけ実行。旧12controller試験と入力は繰り返さない。')


def unit_receipt(job_id,count):
    raw=h.d.inputs.api('actions/jobs/'+str(job_id)+'/logs',True)
    lines=raw.decode('utf-8').splitlines()
    tests=[x.split('Z ',1)[-1] for x in lines if ' ... ok' in x and 'test_pr16_story_save24' in x]
    need(len(tests)==count and any('Ran '+str(count)+' tests in ' in x for x in lines) and
         any(x.endswith(' OK') for x in lines),'既成功試験の正確なログ会計')
    return dict(job_id=job_id,passed_tests=count,replayed_tests=0,test_lines=tests)


def record():
    os.chdir(ROOT);h.d.current()
    need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not (ROOT/a.CP).exists(),'新規記録1回')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    for name in a.d.CODE|a.d.m.CODE:
        need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定sources全byte不変 '+name)
    PUBLIC.mkdir(parents=True)
    done=terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    route_done=terminal(37092347183,'d9435a2d4af239ba25e262722bd52d8814a6bf86',111115153621,['success']*11)
    preflight=prior_preflight()
    tests_prior=[unit_receipt(111117037718,32),unit_receipt(111118427413,12),unit_receipt(a.JOB,7)]
    meta,z=a.d.m.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==47 and set(z.namelist())==set(manifest)|{'manifest.json'},'全47member原本')
        for name,binding in manifest.items():need(identity(z.read(name))==binding,'全member '+name)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['measurement_source']==a.SOURCE and visual['run_id']==a.RUN and visual['artifact_id']==a.ARTIFACT and
         visual['reviewed_screens']==dict(progress=list(range(20)),**{'continue':[0,1]}) and
         visual['total_screens_reviewed']==22 and visual['save_success_wording_observed'] is False and
         visual['teleport_accepted'] is False,'22画面目視と未観測境界')
    for name,digest in visual['screen_anchors'].items():need(identity((original/name).read_bytes())['sha256']==digest,'目視anchorの全byte')
    result,ledger=a.verify(original)
    os.environ['PR16_SAVE24_ORIGINAL']=str(original)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save24_accept.py','-v'],
                        capture_output=True,timeout=120)
    (PUBLIC/'unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==24 and b'\nOK\n' in unit.stderr and
         b'skipped' not in unit.stderr,'新24受入/拒否試験だけ')
    write(PUBLIC/'save-byte-ledger.json',ledger)
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in TEXT:
        raw=(original/name).read_bytes();raw.decode('utf-8');need(b'\0' not in raw,'tracked textのみ')
        p=evidence/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    for name in ('unit.stdout.txt','unit.stderr.txt'):(evidence/name).write_bytes((PUBLIC/name).read_bytes())
    write(evidence/'verification.json',result);write(evidence/'visual-review.json',visual)
    write(evidence/'terminal.json',done);write(evidence/'preflight-failure.json',preflight)
    write(evidence/'controller-test-receipts.json',tests_prior)
    write(evidence/'cave-route-terminal.json',route_done)
    evidence_paths={p.relative_to(ROOT).as_posix() for p in evidence.rglob('*') if p.is_file()}
    artifacts={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')}
    goal=(f'Save24 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
        'map1/73・31,4南・party4/RP0・12296円・badge1・var4071=6/4072=1。'
        '次は東側通路を南へ通常入力で進み、NPC/野生戦は通常UIで対処し次のSave/独立Continue境界へ。'
        '27,4→27,5は高さ3→4/北側進入不可なので旧11歩候補を再試行しない。'
        '岩階段23,14へ回り込む候補は未実測、19,14のcoordはflag4367で27,7/8,10へ分岐する。'
        '静的座標ownerは再利用し、敵trainer/script/進路と手持ちPPを保存候補から照合して入力を計画する。'
        '当回56/cold13入力・32+12+7/新24試験・Save1〜23/旧BP/P08は無影響に再走しない。'
        'teleport/洞窟走破/HM05原因/全国図鑑/自然成長進化/全storyは未完。hostによるstory/flag/var解禁禁止。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
        artifact=artifacts,measurement_conclusion='success',record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        save24_accepted=True,teleport_accepted=False,verification=result,visual_review=a.VISUAL,
        source_bindings=h.d.bindings(CODE|a.d.CODE|a.d.m.CODE),evidence_bindings=h.d.bindings(evidence_paths),
        save_byte_ledger=dict(binding=identity((PUBLIC/'save-byte-ledger.json').read_bytes()),changed_bytes=6937,ranges=1754,artifact_only=True),
        prior_wall_failure=dict(run_id=37092974275,artifact_id=11263731555,native_processes=1,ordinary_saves=0,conclusion='failure'),
        prior_preflight_failure=dict(run_id=37093437062,artifact_id=11263278045,native_processes=0,conclusion='failure'),
        new_measurement_native_processes=2,record_native_processes=0,original_controller_tests=[32,12,7],new_acceptance_tests=24,
        next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f'''# 洞窟東通路31,4・Save24 限定受入

`{result['status']}`。Save23から東11歩/南1歩で31,4南へ進み、通常Save24と独立Continueを受入。新戦闘0、teleport/洞窟走破は未達。

## 実測と原本

source `{a.SOURCE}`、run `{a.RUN}`、job `{a.JOB}` は全8step completed/success。artifact `{a.ARTIFACT}`、17559812bytes、archive SHA256 `{a.ARCHIVE['sha256']}`。47member全byte、進行56入力2782frames/cold13入力1510frames、22画面を検査。保存成功文言だけのanchorは採取しておらず、通常Save UI→安定field/counter24→独立Continueでの全Save/RTC保持を根拠にする。

Save24 SHA256 `{a.OUTPUT['sha256']}`、131088bytes。全party600bytes、Bag/HM05、12296円、旧Save23 bank57344bytes、PC/S61E、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1は不変。全stock checksum42/S61E CRCを確認。補助flags差分0、4021:26→38/4022:1→3だけ。6937byte/1754範囲の差分hexはartifactのみ。

## 失敗は保全し、静的候補を可達性へ昇格しない

run37092974275/source85e1e7d2/artifact11263731555はfailure。36入力1870frames・native1で27,4南まで進み、27,5への3試行が同位置。Save23全byte不変、Save24未作成。旧11歩候補は高さ3→4かつ北側進入不可behavior0x32を無視していた。ROM修正は不要と判断し同方向を反復しない。失敗で未保存のため当回は唯一のSave23から再開し、受入済み区間の再実行とはしない。

run37093437062/source45ccca9b/artifact11263278045は砂床0x2bをfloor whitelistに含め忘れた事前検査failure、native0。walk/save sourceと12試験は不変で成功原本を再利用し、7地形試験だけ追加。前段32/12/7試験も当記録で再実行0、新24受入/拒否試験のみ。古い4root/5node静的監査と全11step成功も継承。

地形名照合の一次資料: https://github.com/pret/pokefirered/blob/master/include/constants/metatile_behaviors.h 。固定ROMで0x2b砂床/0x32北側不可/0x2a岩階段を照合。ROMの同定とnative停止を根拠にし、参照資料だけでVega全体の挙動を保証しない。

## 次の未完工程

{goal}

record source `{os.environ['GITHUB_SHA']}` / run `{os.environ['GITHUB_RUN_ID']}`。record自身のpush/upload/postは後続外部APIで確認。merge/release/active baseline変更なし。
'''
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8')
    need(h.d.bindings(protected)==protected,'受入済み原本/候補/基準保全')
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],
        checks=state['observed_head_checks'],reason_ja='洞窟東通路の新Save24と独立Continue限定受入。旧failureは保全。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='Save24東通路31,4の通常Save/独立Continue測定source。teleport/洞窟走破/製品SHAではない。'
    h.observe_checks(state,a.SOURCE)
    state['story_save24']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,
        artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,map=[1,73],xy=[31,4],facing=1,money=12296,badge_count=1,rp=0,
        story_vars={'4071':6,'4072':1},hm05_owned=True,hm05_taught_or_used=False,teleport_accepted=False,
        cave_crossing_complete=False,measurement_conclusion='success',record_native_processes=0,
        record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['story_cave_route']['record_completion']=route_done
    state['story_cave_route']['runtime_rejected_direct_route']=dict(run_id=37092974275,blocked_edge=[[27,4],[27,5]],
        reason_ja='collision-only候補が高さ3→4/北側進入不可を含んだ。静的script ownerは不変。',new_checkpoint=a.CP)
    state['pending_runs'].append(dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress'))
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_CAVE_EAST_FROM_SAVE24',goal_ja=goal,
        read_paths=[a.GUIDE,a.CP,a.EVIDENCE+'/terrain.json','docs/PR16_STORY_CAVE_ROUTE_JA.md',
            'scripts/pr16_story_save24_accept.py','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],
        stop_rule_ja='Save24から先だけ。旧11歩の壁を反復せず、静的ownerをruntimeへ昇格しない。全国図鑑/story flag注入は禁止。')
    state['bp']['next_step']=goal
    state['bp']['current_stop']='洞窟東通路map1/73・31,4南へ通常進行、Save24/独立Continueを受入。party4/RP0・12296円・badge1。旧11歩は高さ境界で停止、失敗2件を保全。teleport/洞窟走破/全国図鑑/自然成長/全story未完。'
    state['do_not_repeat'].append('Save24の56/cold13入力・32+12+7/新24試験は原本を継承。27,4→27,5の壁3試行と旧11歩候補を反復せず、31,4から先だけ。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|evidence_paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.d.CODE|a.d.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}))
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 洞窟東通路31,4・Save24の通常保存継続
- Version: story-cave-east-save24-v1
- Status: DONE（東通路/Save24限定。teleport/洞窟走破/全story未完）
- Summary: collision-only11歩候補の27,4→27,5で高さ3→4/北側不可の停止を観測。失敗原本を保持し、同じ方向を反復せず東通路31,4へ12歩進行。通常Save24/独立Continueを受入、ROM変更0。
- Files changed: 新入力controller/地形限定検査/受入oracle/記録workflow、Save24 checkpoint/guide/text原本、固定再開MD/JSON、両ログ。
- Verify: run37092974275 native1/Save不変で壁停止、run37093437062 native0の砂床事前検査failureを保持。run{a.RUN}/job{a.JOB}全8step成功、native2・56/cold13入力・22画面・Save131088/party600bytes/Bag/12296円/旧bank/PC/S61E/全国図鑑保持。32+12+7controller試験原本再利用、新24受入試験のみ。記録native0/旧受入再走0/compile0。保存完了文言は未採取、安定field/counter24とcold全byteで限定受入。
- Commit: WIP85e1e7d2/45ccca9b/d9835626、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped final index/resume/task graph/diff確認後、同branch非force push、全text読戻し。
- Network: GitHub connector/固定Actions原本のみ。地形一次照合 https://github.com/pret/pokefirered/blob/master/include/constants/metatile_behaviors.h 。一般CI旧capacity source不一致/action_requiredは成功へ読み替えず、旧受入を緩めない。merge/release/active baseline変更0。
- Next: {goal}
'''
    for name in h.d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(entry)
    h.d.write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned));write(PUBLIC/'receipt.json',cp)


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT)
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard();h.d.git('diff','--cached','--check')


def snapshot():
    with zipfile.ZipFile(PUBLIC/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in h.d.read(OUT/'owned.json'):
            raw=h.d.git('show','HEAD:'+name);need(raw==(ROOT/name).read_bytes(),'全text読戻し');z.writestr(name,raw)
        z.writestr('record-head.txt',h.d.git('rev-parse','HEAD'))
    (PUBLIC/'record-head.txt').write_bytes(h.d.git('rev-parse','HEAD'))


if __name__=='__main__':
    operations=dict(record=record,guard=guard,snapshot=snapshot)
    need(len(sys.argv)==2 and sys.argv[1] in operations,'record|guard|snapshot');operations[sys.argv[1]]()
