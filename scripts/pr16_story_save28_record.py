#!/usr/bin/env python3
"""Save28保存原本の受入と同branch記録。native/既受入試験の再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save28_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h
BASE=a.SOURCE
TASK='USER-20261003-CAVE-COORD-TELEPORT-SAVE28'
OUT=ROOT/'.local/pr16-story-save28-record'
CODE={'scripts/pr16_story_save28_accept.py','scripts/pr16_story_save28_record.py','tests/test_pr16_story_save28_accept.py',a.VISUAL,'.github/workflows/pr16-story-save28-record.yml'}

def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not (ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    OUT.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37116490265,'dacc10021fcb1a2d76e318113871b5e698878023',111184208479,['success']*10)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    tests=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save28_' in v]
    need(len(tests)==16 and any('Ran 16 tests in ' in v for v in log) and any(v.endswith(' OK')for v in log),'修正影響16controller成功原本')
    failed_runs=[]
    for run,source,job in [(37116752441,'02266ff46e26bca0a2a40ed784c45a9b2ca03fe6',111184942745),(37116959565,'f202f9f7779efa8e5b278c58ef21514025410b73',111185510454)]:
        oldrun=h.d.inputs.api('actions/runs/'+str(run));oldjob=h.d.inputs.api('actions/jobs/'+str(job))
        need(oldrun['head_sha']==source and oldrun['status']=='completed' and oldrun['conclusion']=='failure' and oldjob['conclusion']=='failure','native0失敗runの終端')
        need([x['conclusion']for x in oldjob['steps']]==['success','success','success','failure','skipped','success','success','success'],'失敗段階保持')
        failed_runs.append(dict(run=h.d.run_summary(oldrun),job=oldjob,native_processes=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==52 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save27全原本')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'Save27と同一ROM固定')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==36 and len(z.namelist())==37 and set(z.namelist())==set(manifest)|{'manifest.json'},'全36member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..' not in n.split('/') for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba') or n=='runner' or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==17 and visual['reviewed_screens']==dict(progress=list(range(15)),**{'continue':[0,1]}) and visual['save_success_wording_observed'] is True,'全17画面目視')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視全byte '+n)
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全17画面anchor完全')
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    os.environ.update(PR16_SAVE28_ORIGINAL=str(original),PR16_SAVE27_INPUT=str(assets/'input.srm'),PR16_SAVE28_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save28_accept.py','-v'],capture_output=True,timeout=120)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==20 and b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr,'新20受入/拒否試験のみ')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save27-record-terminal.json','coord-owner.json','coord-operands.json','preflight-failure.json','preflight-failure-2.json','preflight-misaligned-operands.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0' not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'failed-preflight-terminals.json',failed_runs)
    write(evidence/'controller-test-receipt.json',dict(job_id=a.JOB,passed_tests=16,development_controller_rechecks=16,reason_ja='実script先頭lockの位置修正でsynthetic原本とdecoderが変わったため16件を再検査。旧ゲーム受入suiteは再走0。',prior_development_test_counts=[12,4],test_lines=tests))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save28 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
          'map1/73・27,7南・party4/RP0・12712円・badge1・story4071=6/4072=1。19,14→27,7の正規teleport（flag4367=0）、Save28/独立Continueは完了。'
          '次は27,7高台から西側の正規通路/橋/coord11〜16,14（var4071=6）とflag4367のstory ownerを追い、新しい通常入力を進める。'
          '8,10行きはflag4367=1の未解禁枝。27,7へのteleport成功を洞窟走破へ昇格せず、19,14を無目的に周回しない。trainer352/353も未対戦。'
          'ミュウツーPP[1,14,0,5]/HP324、オノノクスPP[15,10,15,20]/HP294。火炎放射PP0を使わず、host回復/flag/var解禁は禁止。'
          '既存ROM/runnerはSave24 artifact11263343138、runtime11263910704をhash固定してActions入力のみ再利用。新公開artifactは新save/画面/textだけ。'
          '40/cold13入力・17画面・20新受入試験とSave1〜27は無影響再走しない。旧preflight2回はnative0失敗のまま保持。洞窟走破/HM05原因/全国図鑑/自然成長進化/全storyは未完。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
        artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
        record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save28_accepted=True,teleport_accepted=True,
        visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
        prior_controller_tests=16,development_controller_rechecks=16,failed_preflight_runs=failed_runs,new_acceptance_tests=20,record_native_processes=0,next_goal_ja=goal,
        release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 洞窟正規teleport・Save28 限定受入

`{result['status']}`。Save27の19,13で南を向き19,14へ。flag4367=0の正規scriptで27,7へteleportし通常Save28/独立Continueを受入。8,10行き・trainer352/353・洞窟走破は未受入。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / 127600bytes / SHA256 `{a.ARCHIVE['sha256']}`。全36member、40/cold13入力、17画面を照合。trigger2、暗転3、到着4、解錠6、保存成功文言13、安定field14。戦闘0。warm ledger hashは保存最終解錠14で更新しcoldと一致、途中値と混同しない。

Save28 `{a.OUTPUT['sha256']}` / 131088bytes。party600bytes/PP[1,14,0,5]、Bag/HM05、所持金12712、全trainer/story flags・vars、PC/S61E全payload不変。旧Save27bank57344bytes、42stock checksums/S61E CRC、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1/badge1。全Save/RTCはcoldと同一、6916byte/1743範囲差分。

実root0x08214661は先頭lock→checkflag4367→goto_if1。未設定側27,7・設定側8,10を独立ROM byteで照合。開発計測器の先頭lock漏れでrun37116752441/37116959565は各native0で停止、失敗原本を保持。最初の12+追加4試験と修正影響16再検査を区別し、今回は新20受入/拒否試験だけ。record native0、旧ゲーム受入再走0、ROM/compile/fixture0。一般CI全成功/releaseは主張しない。

条件比較の補助参照: https://raw.githubusercontent.com/pret/pokefirered/master/src/scrcmd.c （ScrCmd_checkflag・ScrCmd_goto_if・sScriptConditionTable）。実Vega候補のbyteと保存flagを受入の正本にする。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save27']['record_completion']=prior_done
    state['story_save28']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
        story_fast_save=a.OUTPUT,map=[1,73],xy=[27,7],facing=1,rp=0,money=12712,badge_count=1,story_vars={'4071':6,'4072':1},
        hm05_owned=True,hm05_taught_or_used=False,teleport_accepted=True,cave_crossing_complete=False,
        record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='正規19,14→27,7teleportとSave28/独立Continueを限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='19,14→27,7正規teleport/Save28測定source。8,10枝/洞窟走破/全story/製品SHAではない。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_CAVE_WEST_OWNER_FROM_SAVE28',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save28_measure.py','content/modernization/pr16_story_cave_route_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save28の27,7南から先だけ。19,14→27,7teleport/保存を無影響再走しない。8,10枝/洞窟走破を未観測で受入へ昇格しない。host解禁禁止。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='19,14→27,7の正規teleportとSave28/独立Continue受入。27,7南、12712円/party4/RP0/badge1、残PP[1,14,0,5]。flag4367=0のため8,10枝/西側story owner/洞窟走破は未完。'
    state['do_not_repeat'].append('Save28の40/cold13入力・17画面・新20受入試験を無影響再走しない。全36memberとnative0 preflight失敗2回を保持。19,14→27,7の一方向だけを受入。8,10枝/洞窟走破へ昇格しない。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 正規teleportとSave28
- Version: story-cave-coordinate-save28-v1
- Status: DONE（19,14→27,7/保存限定。8,10枝/洞窟走破/全story未完）
- Summary: Save27から南1tileの正規coordを踏み27,7南へteleport。通常Save28/独立Continue。戦闘0、party/PP/Bag/flags/vars不変。
- Files changed: Save28専用controller/20受入試験/record workflow、checkpointとtext証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、40/cold13入力・17画面・全36member。party600bytes、旧bank/PC/S61E/全国図鑑/全flagsとvars保持、42checksum。開発12+4試験と先頭lock修正影響16再検査を区別。新20受入試験だけ。record native0/ROM変更0/旧ゲーム受入再走0。
- Failure: run37116752441/37116959565はnative0の失敗原本。condition一般化だけでは解決しなかった。実operand観測で先頭lockの読み位置漏れを特定し修正。失敗を成功へ改作しない。
- Commit: 測定1cc88ec7、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push、全text読戻し。
- Network: 同repo GitHub/Actions原本。補助参照 https://raw.githubusercontent.com/pret/pokefirered/master/src/scrcmd.c のcheckflag/goto_if条件表。実ROM/saveが正本。既存ROM/runtime/input Save27を再配布しない。一般CI旧capacity source不一致保持、merge/release/baseline変更0。
- Next: {goal}
'''
    for name in h.d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8')as f:f.write(entry)
    write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))

def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard();h.d.git('diff','--cached','--check')
def snapshot():
    for n in h.d.read(OUT/'owned.json'):need(h.d.git('show','HEAD:'+n)==(ROOT/n).read_bytes(),'全text読戻し '+n)
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+h.d.git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot);need(len(sys.argv)==2 and sys.argv[1]in actions,'record|guard|snapshot');actions[sys.argv[1]]()
