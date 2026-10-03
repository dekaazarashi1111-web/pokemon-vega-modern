#!/usr/bin/env python3
"""Save29保存原本の受入と同branch記録。native/既受入試験の再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save29_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h
BASE=a.SOURCE
TASK='USER-20261003-CAVE-WEST-SAVE29'
OUT=ROOT/'.local/pr16-story-save29-record'
CODE={'scripts/pr16_story_save29_accept.py','scripts/pr16_story_save29_record.py','tests/test_pr16_story_save29_accept.py',a.VISUAL,'.github/workflows/pr16-story-save29-record.yml'}

def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not (ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    OUT.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37117631601,'3900c985f1901d9e0a674cc6254b2b6af2923bd0',111187403209,['success']*10)
    receipts=[]
    for job,needle,count in [(111189214812,'test_pr16_story_save29_measure.',16),(a.JOB,'test_pr16_story_save29_owner.',4)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        tests=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and needle in v]
        need(len(tests)==count and any('Ran '+str(count)+' tests in ' in v for v in log) and any(v.endswith(' OK')for v in log),'新controller/変更ownerの成功原本')
        receipts.append(dict(job=job,tests=count,test_lines=tests,replays=0))
    failed=h.d.inputs.api('actions/runs/37118280803');failedjob=h.d.inputs.api('actions/jobs/111189214812')
    need(failed['head_sha']=='4fe06a3b1a7a09279c591fe4619e6328c8f55ac4' and failed['status']=='completed' and failed['conclusion']=='failure' and [x['conclusion']for x in failedjob['steps']]==['success','success','success','failure','skipped','success','success','success'],'native0旧失敗は失敗のまま保持')
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==36 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save28全原本')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'Save28と同一ROM固定')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==55 and len(z.namelist())==56 and set(z.namelist())==set(manifest)|{'manifest.json'},'全55member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..' not in n.split('/') for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba') or n=='runner' or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==39 and visual['reviewed_screens']==dict(progress=list(range(37)),**{'continue':[0,1]}) and visual['save_success_wording_observed'] is True,'全39画面目視')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視全byte '+n)
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全39画面anchor完全')
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    os.environ.update(PR16_SAVE29_ORIGINAL=str(original),PR16_SAVE28_INPUT=str(assets/'input.srm'),PR16_SAVE29_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save29_accept.py','-v'],capture_output=True,timeout=120)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==20 and b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr,'新20受入/拒否試験のみ')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save28-record-terminal.json','preflight-failure.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0' not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',dict(passed_tests=20,receipts=receipts,replayed_tests=0));write(evidence/'failed-preflight-terminal.json',dict(run=h.d.run_summary(failed),job=failedjob,native_processes=0))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save29 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
          'map1/73・17,4西・party4/RP0・12712円・badge1・story4071=6/4072=1。西高台の通常移動、野生ディグダ♂Lv8の通常1勝、Save29/独立Continueは完了。'
          '次は17,4から西4歩で13,4、南の正規岩階段13,5→13,6へ進み、低地/橋からcoord11〜16,14のownerへ向かう。'
          'root0x08214656はsetflag4367/var4071=7の正規owner。先頭0x69・末尾0x6b/endを実byte観測。flag4367は未設定で8,10枝は未解禁。'
          'ミュウツーHP324/PP[1,14,0,4]、オノノクスHP294/PP[15,10,15,20]。火炎放射PP0を使わず、host回復/flag/var解禁は禁止。trainer352/353は未対戦。'
          '既存ROM/runnerはSave24 artifact11263343138、runtime11263910704をhash固定してActions入力のみ再利用。新公開artifactは新save/画面/textだけ。'
          '88/cold13入力・39画面・16controller+4owner/新20受入試験、Save1〜28は無影響再走しない。初回native0失敗を保持。'
          '13,5岩階段/洞窟走破/HM05原因/全国図鑑/自然成長進化/全storyは未完。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
        artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
        record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save29_accepted=True,teleport_accepted=False,
        visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
        prior_controller_tests=20,controller_test_split=[16,4],failed_preflight_run=37118280803,new_acceptance_tests=20,record_native_processes=0,next_goal_ja=goal,
        release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 洞窟西高台・Save29 限定受入

`{result['status']}`。Save28の27,7南から西高台を通り17,4西へ。野生ディグダ♂Lv8をれいとうビーム1回で倒し、通常Save29/独立Continueを受入。13,5岩階段、trainer352/353、西側story解禁は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / 232451bytes / SHA256 `{a.ARCHIVE['sha256']}`。全55member、88/cold13入力、39画面を照合。遭遇遷移16、戦闘17〜27、勝利/解錠28、保存成功文言35、安定field36。warmのfield:false残留はcallback/lockで区別し、cold0/1ではtrue。

Save29 `{a.OUTPUT['sha256']}` / 131088bytes。party600byte差分はれいとうビームPP5→4のみ。HP/EXP/種族/4技/道具/OT、Bag/HM05、12712円、全trainer/story flagsを保持。補助var4021だけ68→81、runtime ownerは未解決。旧Save28bank57344bytes、PC/S61E全payload、42stock checksums/S61E CRC、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1/badge1。全Save/RTCはcoldと同一、6949byte/1760範囲差分。

正規owner0x08214656のsetflag4367/setvar4071=7を照合。末尾opcodeは0x6b。初回run37118280803は0x6dと推測したpreflightがnative0で失敗した原本を保持。変更4owner試験を追加し、旧16controllerは再走0。今回新20受入/拒否試験、record native0、旧ゲーム受入再走0、ROM/compile/fixture0。Save28記録run37117631601全10step終端を固定JSONへ反映。一般CI全成功/releaseは主張しない。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save28']['record_completion']=prior_done
    state['story_save29']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
        story_fast_save=a.OUTPUT,map=[1,73],xy=[17,4],facing=3,rp=0,money=12712,badge_count=1,story_vars={'4071':6,'4072':1},
        hm05_owned=True,hm05_taught_or_used=False,teleport_accepted=False,cave_crossing_complete=False,
        record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='西高台17,4/野生1勝とSave29/独立Continueを限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='西高台17,4/野生1勝/Save29測定source。西岩階段/全story/製品SHAではない。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_CAVE_WEST_STAIRS_FROM_SAVE29',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save29_measure.py','content/modernization/pr16_story_cave_route_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save29の17,4西から先だけ。受入済み西高台/野生/保存を再走しない。13,5階段やstory解禁を未観測で受入へ昇格しない。host解禁禁止。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='西高台17,4西へ進み、野生ディグダ♂Lv8を通常1勝。Save29/独立Continue受入。12712円/party4/RP0/badge1、残PP[1,14,0,4]。13,5岩階段とstory owner/洞窟走破は未完。'
    state['do_not_repeat'].append('Save29の88/cold13入力・39画面・16controller+4owner/新20受入試験を無影響再走しない。全55memberとnative0 preflight失敗を保持。岩階段/flag4367解禁/8,10枝へ昇格しない。')

    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 西高台17,4への進行とSave29
- Version: story-cave-west-save29-v1
- Status: DONE（西高台/野生1勝/保存限定。西岩階段/story解禁/洞窟走破は未完）
- Summary: Save28から27,7→18,7→18,4→17,4西へ通常移動。ディグダ♂Lv8をれいとうビーム1回で撃破し通常Save29/独立Continue。火炎放射PP0を使わない。
- Files changed: Save29 controller/owner4試験/20受入試験/record workflow、checkpointとtext証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、88/cold13入力・39画面・全55member。party差分PP5→4、Bag/flags/PC/S61E/全国図鑑保持、var4021のみ68→81、42checksum。前回16controllerと変更owner4を原本再利用、新20受入のみ。record native0/ROM変更0/旧ゲーム再走0。
- Failure: run37118280803はowner終端opcodeを0x6dと推測したpreflightのnative0失敗。実setflag/setvar operandを限定照合し、末尾0x6bを観測。失敗原本を保持。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushし全text読戻し。
- Network: 同repo GitHub/Actions原本のみ。既存ROM/runtime/input Save28を再配布しない。一般CI旧capacity source不一致保持、merge/release/baseline変更0。
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
