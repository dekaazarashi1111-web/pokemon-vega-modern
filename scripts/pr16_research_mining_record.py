#!/usr/bin/env python3
"""完了済み採掘Actions原本を記録。native/compile/unitを再実行しない。"""
from __future__ import annotations
import datetime
import io
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_mining as b
import pr16_research_lifecycle_actions as d
from pr16_learnset_compact_record import publish_resume
need,identity=b.need,b.identity
TASK='USER-20260927-RESEARCH-MINING'
START='8ec5a37666e07a12f1b31d8c5257324168d8fe4e'
HEAD='8fdda1bb5e4f559cf71120f17e7fc947116e8f69'
RUN=36267515706
ARTIFACT=10914865008
ZIP=dict(size=32149,sha256='4c8ef9850fec610641944b1b76f7673edee49169e00dbe75623989bca9381719')
WF='.github/workflows/pr16-research-mining-20260927.yml'
RECORD_WF='.github/workflows/pr16-research-mining-record-20260927.yml'
SELF='scripts/pr16_research_mining_record.py'
MODEL='scripts/pr16_research_mining.py'
TEST='tests/test_pr16_research_mining.py'
CAPTURE='scripts/pr16_research_mining_capture.py'
LOCAL='content/modernization/pr16_research_mining_local_development.json'
CP='content/modernization/pr16_research_mining_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_MINING_JA.md'
BASE='content/modernization/pr16_research_mining_evidence/36267515706'
OUT=Path('.local/pr16-research-mining-record');PUBLIC=OUT/'public'
CODE={WF,RECORD_WF,SELF,MODEL,TEST,CAPTURE,LOCAL,b.C}
GOAL='次は残る3活動（釣り・生態・ゲームコーナー）の実RP稼得、通常進行からResearch受付/ショップ接続、残るnative文言。修復候補26dac23cを専用recipeで復元し、写真/虫取り/採掘の受入済みケースは変更影響なしに再実行しない。採掘は標準いわくだきから0→10RP、条件不足/取消、取引保存2、独立Continue、別coreの階往復fixture後の日次上限、4文言まで。初期party/技/バッジ/進行/warpとcap再入場はfixture。RockSmashWildEncounterの自然終端・自然到達/再到達・全活動/全map/通常接続・releaseは未受入。'


def record():
    os.chdir(ROOT);d.current()
    need(not Path(CP).exists() and not PUBLIC.exists(),'one immutable acceptance, no repeated record')
    PUBLIC.mkdir(parents=True)
    run=d.inputs.api('actions/runs/'+str(RUN));jobs=d.inputs.api('actions/runs/'+str(RUN)+'/jobs?per_page=100')
    need(run['head_sha']==HEAD and run['path']==WF and run['status']=='completed' and run['conclusion']=='success' and run['run_attempt']==1,'complete source-fixed measurement run')
    need(jobs['total_count']==len(jobs['jobs'])==1 and jobs['jobs'][0]['conclusion']=='success' and all(s['conclusion']=='success' for s in jobs['jobs'][0]['steps']),'all measurement steps complete')
    meta=d.inputs.api('actions/artifacts/'+str(ARTIFACT))
    need(not meta['expired'] and meta['size_in_bytes']==ZIP['size'] and meta['digest']=='sha256:'+ZIP['sha256'] and meta['workflow_run']['id']==RUN and meta['workflow_run']['head_sha']==HEAD,'fixed measurement artifact metadata')
    archive=d.inputs.api('actions/artifacts/'+str(ARTIFACT)+'/zip',True);need(identity(archive)==ZIP,'exact outer ZIP')
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        members=z.infolist();need(len(members)==len(set(z.namelist()))==12 and sum(e.file_size for e in members)==1323325,'complete bounded archive')
        raw=z.read('public/measurement.json');m=b.load(raw)
        need(identity(raw)==dict(size=55960,sha256='ccb0c8411f111fb205313968233d3c3b47b8e4c543d0c1819daab87b8d4a792d'),'immutable original measurement')
        expected={'public/measurement.json'}|{case+'/'+name for case,v in m['cases'].items() for name in v['screens']}
        need(set(z.namelist())==expected and all(e.external_attr>>28!=10 and not e.is_dir() and e.file_size<=500000 for e in members),'closed regular artifact members')
        for case,v in m['cases'].items():
            for name,bi in v['screens'].items():
                image=z.read(case+'/'+name);need(image.startswith(b'P6\n240 160\n255\n') and identity(image)==bi and len(image)==115215,'complete reviewed pixels')
    need(m['source_head']==HEAD and m['run_id']==RUN and m['candidate']==b.CANDIDATE and m['status']=='PASS_MINING_MEASUREMENT_SCOPED' and not m['failures'],'original scoped success')
    need(m['counts']==dict(rom_changes=0,arm_compiles=0,host_compiles=1,native_processes=3,accepted_case_reruns=0,accepted_native_processes=3,failed_native_processes=0),'complete execution counts')
    need(m['compile']['returncode']==0 and not m['compile']['stdout'] and not m['compile']['stderr'],'strict recorded host compile')
    need(m['compile']['generated_source']==dict(size=66650,sha256='e878b1e3e050aa4ca5f03f5efefb1bfdd935e40360dc85e95f6a291069ef4c98'),'measured generated C')
    need(set(m['cases'])==set(b.CASES) and not m['visual_review_pending'] and not m['natural_arrival_accepted'] and not m['all_activities_accepted'] and not m['release_ready'],'three new cases; no expanded scope')
    for p,bi in m['source_bindings'].items():
        need(identity(d.git('show',HEAD+':'+p))==bi and identity(Path(p).read_bytes())==bi,'exact original/current source '+p)
    need(d.bindings(m['protected_bindings'])==m['protected_bindings'],'accepted evidence unchanged')
    parent=d.read('content/modernization/pr16_research_bug_checkpoint.json')
    need(d.bindings(parent['source_bindings'])==parent['source_bindings'] and parent['actions_completion_confirmed'],'accepted predecessor unchanged')
    results={}
    for case,v in m['cases'].items():
        need(v['execution']==dict(returncode=0,timeout=False) and not v['stderr'] and identity(v['stdout'].encode())==v['stdout_identity'] and identity(b'')==v['stderr_identity'],'numeric exit and complete stdout/stderr')
        need(v['generated_source']==m['compile']['generated_source'],'identical compiled program')
        results[case]=b.validate(v['stdout'].encode(),case)
        need(results[case]==v['validated'],'independent raw replay, not native rerun')
        need(v['screens']=={r['screen']:dict(size=115215,sha256=r['sha256']) for r in results[case]['screens']},'all eleven image bindings')
    u=m['unit'];need(u['returncode']==0 and u['passed']==64 and (u['stdout']+u['stderr']).count(' ... ok\n')==64 and u['native_processes']==u['compiles']==0,'source-pinned 64 tests; no rerun')
    local=d.read(LOCAL);need(local['native_processes']==8 and local['failed_native_processes']==5 and local['successful_native_processes']==3 and len(local['attempts'])==8,'development failures remain separate')
    tracked=d.git('ls-files').decode().splitlines()
    need(not [p for p in tracked if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','content','docs','design')],'nested rules require review')
    protected=d.bindings(set(m['protected_bindings'])|set(parent['protected_bindings'])|{p for p in tracked if p.startswith(('content/modernization/pr16_research_photo_evidence/','content/modernization/pr16_research_bug_evidence/','content/modernization/pr16_research_map_view_evidence/'))})
    Path(b.RAW).write_bytes(raw)
    d.write(PUBLIC/'terminal.json',dict(run=d.run_summary(run),jobs=jobs['jobs'],artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run')}))
    d.write(PUBLIC/'unit.json',dict(u,source_bindings=d.bindings({MODEL,TEST,b.C}),reexecutions=0))
    d.write(PUBLIC/'visual.json',dict(status='PASS_FOUR_DIALOGUES_SCOPED',method='ChatGPT vision of original local PPMs, then exact Actions PPM hashes',images={case:v['screens'] for case,v in m['cases'].items()},unique_dialogues=4,images_count=11,
        text_ja=['このいわを しらべますか？','いまはこのいわを こわせない。','こうせきのきろく。10ポイントだよ。','きょうのさいくつは おわっている。'],
        notes_ja='洞窟の暗い周囲・人物・岩・台詞枠を確認。四文言に欠字/切詰めなし。報酬/上限はwild tail前で止める。自然な再到達/全mapは未受入。'))
    prior_pending=[d.run_summary(d.inputs.api('actions/runs/'+str(r['run_id']))) for r in d.read(d.STATE)['pending_runs']]
    listing=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=20')['workflow_runs']
    checks=dict(prior_pending=prior_pending,runs=[d.run_summary(r) for r in listing])
    d.write(PUBLIC/'checks.json',checks)
    d.write(PUBLIC/'reconciliation.json',dict(status='PASS_MINING_ACTIONS_SOURCE_AND_EVIDENCE',source_head=HEAD,original=identity(raw),candidate=m['candidate'],accepted_cases=results,counts=m['counts'],new_scoped_tests=64,record_native_runs=0,record_compiles=0,record_unit_runs=0,local_history=LOCAL,
        scope_ja='RP稼得・実保存・cold Continue・fixture再入場後capまで。後続wild tailの正常復帰は未検証。'))
    manifest={}
    for p in sorted(PUBLIC.iterdir()):
        value=p.read_bytes();value.decode('utf-8');need(p.suffix in ('.json','.txt') and b'\0' not in value and len(value)<2000000,'public UTF8 only')
        dest=Path(BASE)/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(value);manifest[str(dest)]=identity(value)
    d.write(BASE+'/manifest.json',manifest)
    cp=dict(schema_version=1,task=TASK,status='PASS_MINING_REAL_EARNING_SCOPED',source_head=HEAD,run_id=RUN,
        record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),candidate=b.CANDIDATE,
        recipe=b.prior.view.RECIPE,measurement=b.RAW,manifest=BASE+'/manifest.json',terminal=BASE+'/terminal.json',unit=BASE+'/unit.json',visual=BASE+'/visual.json',local_development=LOCAL,
        mining_accepted=True,actions_completion_confirmed=True,accepted_cases=list(b.CASES),failed_cases=[],fresh_cores=5,counts=dict(m['counts'],new_scoped_tests=64),
        source_bindings=d.bindings(set(m['source_bindings'])|CODE),protected_bindings=protected,
        all_activities_accepted=False,natural_arrival_accepted=False,natural_reentry_accepted=False,wild_tail_accepted=False,
        shop_connection_accepted=False,all_dialogue_native_display_accepted=False,all_maps_accepted=False,release_ready=False,active_baseline_changed=False,
        record_execution=dict(native_processes=0,compiles=0,unit_processes=0),remaining_activities=['FISHING','ECOLOGY','GAME_CORNER'])
    d.write(CP,cp)
    Path(GUIDE).write_text(f'''# PR16 採掘の実RP稼得

{cp['status']} / {TASK}

## 実装・限定受入

候補 `{b.CANDIDATE['sha256']}` / 33554432bytesは不変。標準いわくだきのfield effect37→岩除去→実FieldMiningを物理Aで通す。map97/82、local12、(1,20)、event0x09413B40、record0x0941397C、script0x093C050C。現在のobject template数17とlive対象岩1を区別する。

バッジ不足・技不足・取消ではRP0/Flash不変。承諾で0→10RP、生涯10/日内mining10/claim2/取引ID2、保存counter2→4。取引自身の保存2回、手動Save0。全party600bytes・Bag・台帳2048bytes・他owner・checksumを検査。独立coreの通常Continueで残高10と全不変量を保持する。

岩消去は同mapのContinueでも保持される。日次上限は3番目のcoreの開始fixtureで隣接階97/81へstock warpして戻し、再度実岩を調べresult4/RP10/counter4/Flash不変を確認。自然な階往復とは区別する。報酬と上限文言で入力を止め、RockSmashWildEncounterの自然終端は未受入。初期party/技/バッジ/進行/warpもfixture。barrier後host書込み0、RP/resultの注入0。

## 原本・実行数・失敗履歴

Actions `{RUN}` / source `{HEAD}` は全step成功。新規3process/5fresh cores、host compile1、ARM0、ROM変更0、失敗0。新規64unit成功（64owner byte変異、全行欠落/追加、型・順序・不変量・過大主張拒否を含む）。11PPMの完全hashが目視済み四文言に一致。記録時unit/native/compile再実行0。

原本 `{b.RAW}` はartifact{ARTIFACT}のmeasurement.jsonをbyte不変保存。外側ZIP `{ZIP['sha256']}`。`{BASE}/terminal.json`、unit/visual/reconciliation/manifestを照合する。

ローカル開発は8process/成功3/失敗5。旧configの件数誤仮定1、CPU非保存のsetup1、過剰Aでwild tailへ進みparty変化2、Continue後の岩消去保持1を失敗として保存。途中失敗のstderr原文・stdout/source/measurement identity・compile/preflight履歴は `{LOCAL}`。途中stdout全文はcontainer原本でありGitに全文保存したとは主張しない。正式原本は上記Actions。成功に読み替えない。

## 次工程

{GOAL}

既存P03 capacity source pin等の一般CI失敗は限定PASSと分離する。最新照合は `{BASE}/checks.json`。PR draft/open・未merge、release/baseline切替なし。記録workflow自身の終端はrecord_run_idから確認し、自己実行中をsuccessにしない。
''')
    state=d.read(d.STATE)
    state['research_mining']={k:cp[k] for k in ('status','source_head','run_id','candidate','actions_completion_confirmed','mining_accepted','accepted_cases','fresh_cores','counts','record_run_id')}
    state['research_mining'].update(path=CP,measurement=b.RAW,guide=GUIDE)
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=GOAL
    state['next_action']=dict(state['next_action'],id='RESEARCH_REMAINING_THREE_AND_NATURAL_CONNECTION_NEXT',goal_ja=GOAL,
        read_paths=[GUIDE,CP,b.prior.view.RECIPE,'content/research_economy_v1/canonical_model.json','overlays/research_economy_v1/research_economy_v1.c','docs/PR16_RESEARCH_CATALOG_JA.md','content/modernization/pr16_research_catalog_checkpoint.json','docs/PR16_RESEARCH_NEW_GAME_JA.md'],
        stop_rule_ja='写真/虫取り/採掘/保存view・元ROM/seed/旧証拠を保全。採掘wild tail/自然再入場・全活動・全mapの過大主張禁止。無変更再実行、merge/release/baseline変更禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='採掘Actions run36267515706/source8fdda1bbの受入記録source。自己commit SHAはgit log参照。record_run_idの終端と非force pushをremoteで確認する。'
    state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],runs=checks['runs'],reconciliation=BASE+'/checks.json',
        reason_ja='採掘の実測・新64検査・context exportは全step成功。一般CIの既存失敗と分離。記録workflowの最終結果は実行中に自己確定せず、record_run_idとremote HEADで確認。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in listing if r['status'] in ('queued','in_progress')]
    for p in CODE|{b.RAW,CP,GUIDE}:state['source_bindings'][p]=identity(Path(p).read_bytes())
    note='採掘run36267515706/source8fdda1bb/26dac23cを限定受入。0→10RP・条件不足/取消・取引保存2・独立Continue・fixture再入場cap・4文言、3process/5cores/新64検査。無変更再実行禁止。wild tail/自然再到達/通常接続/全活動は未受入。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat();state['logs_synchronized']=True
    publish_resume(state)
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 採掘実RP稼得の限定受入\n- Version: research-mining-v1\n- Status: DONE（採掘限定scope）\n- Summary: 標準いわくだき0→10RP、条件不足/取消、保存2/独立Continue、fixture階往復後cap、4文言を受入。wild tail/自然到達/残3活動/受付ショップ接続は未受入。\n- Files changed: 採掘runner/oracle/64検査/測定・記録Actions、UTF8原本/失敗履歴/checkpoint/guide、固定引継ぎMD・JSON、両ログ。\n- Verify: run{RUN}全step成功、3native/5cores/host1/ARM0/ROM変更0、失敗0、新64tests PASS。local開発8中5失敗は別記。記録unit/native/compile再実行0。source/11画像/全ledger/party/Bag/Flash照合。commit前resume/task graph/scoped final-index guard必須。\n- Commit: WIP f12167c7/2640e5d9、測定source={HEAD}、記録source='+os.environ['GITHUB_SHA']+'、自己SHAはgit log参照、同branch非force push。\n- Network: GitHub HEAD/PR/完了Actions/固定artifactのみ。旧写真/虫取り/BP/P08/seed/baseline不変。一般CIと限定PASSを分離、merge/releaseなし。\n'
    for p in d.LOGS:
        with Path(p).open('a') as f:f.write(log)
    owned=set(manifest)|{BASE+'/manifest.json',b.RAW,CP,GUIDE,d.STATE,d.DOC}|d.LOGS
    d.write(OUT/'owned.json',sorted(owned));d.write(PUBLIC/'summary.json',dict(status=cp['status'],original_run=RUN,source_head=HEAD,record_source_head=os.environ['GITHUB_SHA'],unit_passed=64,record_native_runs=0,record_unit_runs=0))


def guard():
    cp=d.read(CP);need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'accepted protected evidence preserved')
    owned=set(d.read(OUT/'owned.json'));subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    changed=set(d.git('diff','--cached','--name-only',START).decode().splitlines());need(changed<=owned|CODE,'entire task in explicit scope')
    g.START=START;g.CODE=changed-owned;g.OWNED=owned;g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)
    d.write(PUBLIC/'guard.json',dict(status='PASS_SCOPED_FINAL_INDEX',source_head=os.environ['GITHUB_SHA'],from_task_head=START,changed_paths=sorted(changed),new_private_violations=0,full_historical_guard_pass_claimed=False))


if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('record | guard')
