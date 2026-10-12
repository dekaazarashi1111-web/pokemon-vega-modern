#!/usr/bin/env python3
"""Save23の保存済みfailure原本を新oracleで限定受入し、入力を再実行せず記録する。"""
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
import pr16_story_save23_accept as a
import pr16_research_story_route_actions as h
import pr16_story_after_maori_measure as transport
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
TASK=a.measured.TASK
OUT=ROOT/'.local/pr16-story-save23-record'
PUBLIC=OUT/'public'
SELF='scripts/pr16_story_save23_record.py'
VISUAL='content/modernization/pr16_story_save23_visual_review.json'
CODE={SELF,VISUAL,'scripts/pr16_story_save23_accept.py','tests/test_pr16_story_save23_accept.py',
      '.github/workflows/pr16-story-save23-record.yml'}
TEXT=['failure.json','parent.json','manifest.json','progress/commands.txt','progress/stdout.txt',
      'progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt',
      'continue/stderr.txt','continue/execution.json']


def terminal():
    run=h.d.inputs.api(f'actions/runs/{a.RUN}');jobs=h.d.inputs.api(f'actions/runs/{a.RUN}/jobs?per_page=100')
    need(run['head_sha']==a.SOURCE and run['head_branch']==a.measured.plan.BRANCH and
         run['status']=='completed' and run['conclusion']=='failure' and run['run_attempt']==1,
         'original failed run stays failed')
    need(jobs['total_count']==len(jobs['jobs'])==1,'one complete job')
    j=jobs['jobs'][0]
    names=['Set up job','Run actions/checkout@v4','New controller tests and scoped source guard',
           'New interior warp Save23 and independent Continue only','Lightweight task graph',
           'Run actions/upload-artifact@v4','Post Run actions/checkout@v4','Complete job']
    conclusions=['success','success','success','failure','skipped','success','success','success']
    need(j['id']==a.JOB and j['status']=='completed' and j['conclusion']=='failure' and
         [s['name'] for s in j['steps']]==names and [s['conclusion'] for s in j['steps']]==conclusions and
         all(s['status']=='completed' for s in j['steps']),'exact terminal steps including retained failure and upload')
    return dict(run=h.d.run_summary(run),job=j)


def restore():
    meta,z=transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    original=OUT/'original';original.mkdir(parents=True)
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==34 and set(z.namelist())==set(manifest)|{'manifest.json'},'all34 original members')
        for name,binding in manifest.items():need(identity(z.read(name))==binding,'original byte '+name)
        z.extractall(original)
    review=h.d.read(ROOT/VISUAL)
    need(review['measurement_source']==a.SOURCE and review['run_id']==a.RUN and review['reviewed_anchors']==len(review['anchors'])==14,
         'source-bound visual review')
    for name,binding in review['anchors'].items():
        need(name in manifest and identity((original/name).read_bytes())==binding,'reviewed full screen '+name)
    return original,meta,review


def record():
    os.chdir(ROOT);h.d.current()
    need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not (ROOT/a.CP).exists() and
         not (ROOT/a.EVIDENCE).exists(),'new record once only')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    # Native計測器は失敗時の全byteを保持。新oracleを旧sourceへ遡及して適用したとは記録しない。
    for name in a.measured.CODE|a.measured.plan.CODE:
        need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'original measurement source unchanged '+name)
    done=terminal();original,meta,review=restore();PUBLIC.mkdir(parents=True)
    os.environ['PR16_SAVE23_ORIGINAL']=str(original)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save23_accept.py','-v'],
                        capture_output=True,timeout=120)
    (PUBLIC/'unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==24 and b'\nOK\n' in unit.stderr and
         b'skipped' not in unit.stderr,'24 new acceptance/negative tests only')
    result,ledger=a.verify(original)
    # 全Save差分hexはartifactだけ。tracked textにはsize/hash/件数のみ保存する。
    write(PUBLIC/'save-byte-ledger.json',ledger)
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in TEXT:
        raw=(original/name).read_bytes();raw.decode('utf-8');need(b'\0' not in raw,'tracked text only')
        p=evidence/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    for name in ('unit.stdout.txt','unit.stderr.txt'):(evidence/name).write_bytes((PUBLIC/name).read_bytes())
    write(evidence/'verification.json',result)
    write(evidence/'visual-review.json',review)
    # 完了済み静的採取はhash固定artifactからのみ継承。採取器も14試験も再実行しない。
    inspect_meta,z=transport.archive(11262023177,37090546571,
        dict(size=2859,sha256='00ae5d9406ddddd77e5e94ff9c90a640582c429fe94a13a0a0d8b9d3d50d2d52'),a.measured.BASE)
    with z:
        need(z.namelist()==['inspection.json'],'inspection text only')
        inspection=json.loads(z.read('inspection.json'))
    need(inspection['source_head']==a.measured.BASE and inspection['status']=='PASS_STATIC_CAVE_OPTIONS_NOT_NATIVE_ACCEPTANCE' and
         inspection['native_processes']==0,'static proof is not native acceptance')
    write(evidence/'inspection.json',inspection)
    write(evidence/'terminal.json',done)
    artifacts={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')}
    evidence_paths={p.relative_to(ROOT).as_posix() for p in evidence.rglob('*') if p.is_file()}
    next_goal=(f'story-fastの唯一の開始点はartifact{a.ARTIFACT}のstory-fast.srm（Save23、131088bytes、SHA256 {a.OUTPUT["sha256"]}）。'
        'ちえのどうくつ内部map1/73・20,3東・party4/RP0・12296円・badge1、var4071=6/4072=1。'
        '北入口からの階段warp・通常Save23・保存成功文言・独立Continueは限定受入済み。'
        '内部の先へ通常入力で進み、次のSave/cold境界で区切る。洞窟走破/南出口/新storyイベントは未完。'
        '45/cold13入力、静的14/入力17/原本受入24試験とSave1〜22/旧BP/P08は無影響に再走しない。'
        'run37090970832のfailureは保存後oracleの補助flag2056不変仮定が原因であり、成功へ改作しない。'
        '2056:1→0と補助var4021/4022の実観測差分だけを限定記録しruntime ownerは未解決。'
        'HM05は所持のみで未習得/未使用・原因未解決、同じ拒否入力を反復しない。'
        '全国図鑑magic0/grant ownerと分離progression原本Axewを保全し、flag/var注入で解禁しない。'
        '正規全国図鑑、自然成長/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達、全storyは未完。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
        artifact=artifacts,measurement_conclusion='failure',record_source=os.environ['GITHUB_SHA'],
        record_run_id=int(os.environ['GITHUB_RUN_ID']),save23_accepted=True,verification=result,
        source_bindings=h.d.bindings(CODE|a.measured.CODE|a.measured.plan.CODE),evidence_bindings=h.d.bindings(evidence_paths),
        save_byte_ledger=dict(binding=identity((PUBLIC/'save-byte-ledger.json').read_bytes()),changed_bytes=7000,ranges=1788,artifact_only=True),
        next_goal_ja=next_goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f'''# ちえのどうくつ内部warp・Save23 限定受入

`{result['status']}`。北入口map1/36から内部map1/73・20,3東への通常階段warp、通常Save23、独立Continueのみ。洞窟走破/南出口/新storyイベント、HM05、全国図鑑、自然成長/進化、全storyは未完。

## 原本と失敗の意味

測定source `{a.SOURCE}`、run `{a.RUN}`、job `{a.JOB}`、artifact `{a.ARTIFACT}`。archive全17499395bytesのSHA256 `{a.ARCHIVE['sha256']}`、全34member/17画面を照合。native2processは正常終了、45/cold13入力・3318/cold1510framesで保存まで完走。初回の最終oracleはflag2056を完全不変と仮定したためfailure。実際の差分2056:1→0とvars4021:23→26/4022:3→1だけを後続oracleで限定照合する。runtime ownerやflagの意味を推測せず未解決のまま保持する。旧runをsuccessへ改作せず、native/入力の再走0。

## 保存と画面の境界

Save23 `{a.OUTPUT['sha256']}`、131088bytes。全Save/RTCが独立Continue後も不変。全party600bytes、全Bag/HM05、12296円、旧Save22bank57344bytes、PC/S61E、全国図鑑magic0/var404e0/flag840=0、story4071=6/4072=1を保持。stock checksum42件とS61E CRC/反転値を照合。全差分7000bytes/1788範囲のhexはartifactだけ。

進行0/1/3/5/7〜14とcold0/1の14anchorを目視。進行7で内部到達、11/12は書込途中、13で「レポートに しっかり かきのこした！」、14で操作可能fieldへ戻る。cold2画面も同位置。新戦闘/捕獲/回復/育成/技習得0。静的14試験と入力controller17試験の原本は再実行せず、新しい原本受入/拒否24試験を追加。

## 再開

{next_goal}

記録source `{os.environ['GITHUB_SHA']}`、run `{os.environ['GITHUB_RUN_ID']}`。記録自身のpush/upload/post成功は次の外部APIで確認し、自己予測しない。一般CI全成功・release・merge・active baseline切替は主張しない。
'''
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8')
    need(h.d.bindings(protected)==protected,'all accepted source/evidence/progression/baseline unchanged')
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],
        checks=state['observed_head_checks'],reason_ja='Save22以降の洞窟内部warpとSave23だけを保存済み原本から限定受入。'))
    state['observed_head']=a.SOURCE
    state['observed_head_semantics']='Save23の階段warp・通常Save・独立Continue測定source。runは最終補助flag oracle failureを保持、後続原本検査で限定受入。全story/製品SHAではない。'
    runs=h.d.inputs.api('actions/runs?head_sha='+a.SOURCE+'&per_page=100')
    need(runs['total_count']==len(runs['workflow_runs']),'complete measurement HEAD runs')
    state['observed_head_checks']=dict(scope_head=a.SOURCE,runs=[h.d.run_summary(r) for r in runs['workflow_runs']],
        reason_ja='元測定failureを保持。専用後続検証と一般CIのscopeを分離。')
    old_pending=[]
    for pending in state['pending_runs']:
        run=h.d.inputs.api('actions/runs/'+str(pending['run_id']))
        need(run['head_sha']==pending['tested_head'] and run['status']=='completed','old pending identity and terminal')
        old_pending.append(h.d.run_summary(run))
    state['story_save23']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,artifact_id=a.ARTIFACT,
        story_fast_save=a.OUTPUT,map=[1,73],xy=[20,3],facing=4,money=12296,badge_count=1,rp=0,
        story_vars={'4071':6,'4072':1},hm05_owned=True,hm05_taught_or_used=False,hm05_root_cause_resolved=False,
        inner_cave_reached=True,cave_crossing_complete=False,original_run_conclusion='failure',record_native_processes=0,
        record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=next_goal,old_pending_reconciled=old_pending)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['story_save22']['record_completion']=inspection['prior_record']
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_AFTER_CHIE_INTERIOR_SAVE23',goal_ja=next_goal,read_paths=[a.GUIDE,a.CP,
        a.EVIDENCE+'/inspection.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md','content/modernization/pr16_story_acceleration_checkpoint.json',
        'scripts/pr16_story_save23_accept.py'],stop_rule_ja='Save23内部から先だけ。Save1〜22/今回の45+13入力/完了済み試験は無影響に再走しない。旧failureと補助owner未解決を保持。HM05盲修正/flag注入解禁は禁止。')
    state['bp']['next_step']=next_goal
    state['bp']['current_stop']='支援story-fastは洞窟内部map1/73・20,3東へ進行、通常Save23と独立Continueを限定受入。party4/RP0・12296円・badge1。旧oracle failureを保持し原本だけで回収。洞窟走破/全国図鑑/自然成長/全story未完。'
    state['do_not_repeat'].append('Save23の45/cold13入力・内部warp/保存/Continueは原本から限定受入。run37090970832 failureを保持しnative再走0で回収。静的14/入力17/原本24試験は無影響に反復しない。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|evidence_paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.measured.CODE|a.measured.plan.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}))
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 洞窟内部warp・Save23を保存済み原本から限定受入
- Version: story-cave-save23-v1
- Status: DONE（内部到達/Save23限定。洞窟走破・全story未完）
- Summary: Save22の唯一の親から4tile階段warp、map1/73・20,3東へ通常進行。45/cold13入力と保存成功文言、独立Continueを確認。初回補助flag2056不変仮定failureを保持し、2056:1→0と補助var2件だけを新oracleで限定照合。入力再走0。
- Files changed: 新規静的採取器14試験/入力controller17試験/原本受入24試験/記録器/専用workflow、Save23 checkpoint/guide/text原本、固定再開MD/JSON、両ログ。
- Verify: 測定run{a.RUN}/job{a.JOB}は最終oracle failureのまま、正常native2process・17画面・全34memberを回収。後続新24試験、全Save/RTC131088bytes、party600bytes、全Bag/12296円、checksum42件、S61E、旧bank/PC/全国図鑑/progression保全。7000差分bytes/1788範囲。記録native0・旧受入再走0・compile0。scoped final-index guard/resume/task graph/diff確認後のみcommit。一般CI全成功とはしない。
- Commit: WIP7061be32/171a6518、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。同branch非force push、全text読戻し。自己SHAはgit履歴で確認。
- Network: GitHub connectorと固定Actions artifactsのみ。全Save/ROM/画面/差分hexはartifactだけ。旧pending5件の完了も外部APIで照合。merge/release/active baseline/source-lock変更なし。
- Next: {next_goal}
'''
    for name in h.d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(entry)
    h.d.write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
    write(PUBLIC/'receipt.json',dict(status='PREPARED_SAVE23_SCOPED_RECORD',measurement_terminal=done,artifact=artifacts,
        new_acceptance_tests=24,measurement_native_processes=2,record_native_processes=0,old_native_reruns=0,
        verification=result,owned=sorted(owned)))


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT)
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard()
    h.d.git('diff','--cached','--check')


def snapshot():
    with zipfile.ZipFile(PUBLIC/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in h.d.read(OUT/'owned.json'):
            raw=h.d.git('show','HEAD:'+name);need(raw==(ROOT/name).read_bytes(),'all committed text readback '+name);z.writestr(name,raw)
        z.writestr('record-head.txt',h.d.git('rev-parse','HEAD'))
    (PUBLIC/'record-head.txt').write_bytes(h.d.git('rev-parse','HEAD'))


if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot)
    need(len(sys.argv)==2 and sys.argv[1] in actions,'record|guard|snapshot');actions[sys.argv[1]]()
