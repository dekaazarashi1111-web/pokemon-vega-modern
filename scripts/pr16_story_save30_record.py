#!/usr/bin/env python3
"""Save30原本の独立受入・固定引継ぎ・同branch記録。native再走なし。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save30_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h
BASE=a.SOURCE
TASK='USER-20261003-CAVE-STAIRS-SAVE30'
OUT=ROOT/'.local/pr16-story-save30-record'
CODE={'scripts/pr16_story_save30_accept.py','scripts/pr16_story_save30_record.py','tests/test_pr16_story_save30_accept.py',a.VISUAL,'.github/workflows/pr16-story-save30-record.yml'}

def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not (ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE30_JA.md' and a.CP=='content/modernization/pr16_story_save30_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save30_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37119219773,'a5d169ffc645d574d8d2bd471555fc82a56b592f',111191908827,['success']*10)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    tests=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save30_measure.' in v]
    need(len(tests)==12 and any('Ran 12 tests in 'in v for v in log) and any(v.endswith(' OK')for v in log),'変更12controller試験原本')
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==55 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save29全55member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save29/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==33 and len(z.namelist())==34 and set(z.namelist())==set(manifest)|{'manifest.json'},'全33member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==18 and visual['reviewed_screens']==dict(progress=list(range(16)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全18画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全18画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE30_ORIGINAL=str(original),PR16_SAVE29_INPUT=str(assets/'input.srm'),PR16_SAVE30_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save30_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==20 and b'\nOK\n'in unit.stderr and b'skipped'not in unit.stderr,'新20受入/拒否試験')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save29-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',dict(job=a.JOB,passed_tests=12,test_lines=tests,replayed_tests=0))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save30 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map1/73・13,6南・party4/RP0・12712円・badge1・story4071=6/4072=1。正規岩階段13,5を通常通過し下層13,6のSave30/独立Continueを受入。'
      '次は下層から南のcoord11〜16,14へ進み、正規owner0x08214656によるflag4367/var4071=7を通常入力で観測する。'
      '保存済みlower_corridor_terrainでは13,6→13,7→14,7→14,8の南にbehavior59境界14,9がある。衝突bitだけで到達不能と断定せず、通常入力と画面で境界を確認する。'
      'ミュウツーHP324/PP[1,14,0,4]、オノノクスHP294/PP[15,10,15,20]は不変。今回戦闘0。火炎放射PP0を使わずhost回復/flag/var解禁は禁止。'
      '既存ROM/runnerはSave24 artifact11263343138、runtime11263910704をActions入力だけ再利用し、新公開artifactは新save/画面/textだけ。'
      '46/cold13入力・18画面・新12controller/20受入試験、Save1〜29は無影響再走しない。補助var4021=87/4022=1のruntime ownerは未解決。'
      'trainer352/353、story flag4367、洞窟走破、HM05原因、全国図鑑、自然成長進化、全storyは未完。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save30_accepted=True,west_stairs_accepted=True,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=12,new_acceptance_tests=20,record_native_processes=0,next_goal_ja=goal,
      release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 洞窟西岩階段・Save30 限定受入

`{result['status']}`。Save29の17,4西から13,4まで進み、13,5岩階段を通常通過し下層13,6南で通常Save30/独立Continueを受入。戦闘0、story解禁/洞窟走破は未完。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / 134841bytes / SHA256 `{a.ARCHIVE['sha256']}`。全33member、46/cold13入力、18画面を照合。南へ向き直り5、階段6、下層7、保存成功文言14、安定field15。独立Continue0/1でも同じ13,6南。

Save30 `{a.OUTPUT['sha256']}` / 131088bytes。party全600byte、HP/PP/EXP/種族/4技/道具/OT、Bag/HM05、12712円、全trainer/story flagsを保持。補助var4021だけ81→87、4022は0→1。これらのruntime ownerは未解決。旧Save29bank57344bytes、PC/S61E全payload、42stock checksums/S61E CRC、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1/badge1。全Save/RTCはcoldと同一、6941byte/1761範囲差分。

新12controller試験は測定runの原logを保持して再走0。新20受入/拒否試験は今回だけ実行し全stderrを保存。既存Save29の失敗原本と試験証拠を改作しない。record native0/ROM変更0/compile0/fixture0/既受入再走0。Save29記録run37119219773全10step終端を固定JSONへ反映。一般CI全成功/releaseは主張しない。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save29']['record_completion']=prior_done
    state['story_save30']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[1,73],xy=[13,6],facing=1,rp=0,money=12712,badge_count=1,story_vars={'4071':6,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,west_stairs_accepted=True,story_flag4367_accepted=False,cave_crossing_complete=False,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='西岩階段13,5通過/下層13,6のSave30を限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='西岩階段/下層13,6/Save30測定source。story解禁/全story/製品SHAではない。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_CAVE_SOUTH_OWNER_FROM_SAVE30',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save30_measure.py',a.EVIDENCE+'/inspection.json','content/modernization/pr16_story_cave_route_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save30の13,6南から先だけ。既受入岩階段を再走せず、未解禁flag4367/var4071の正規ownerへ。host解禁禁止。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='西岩階段13,5→下層13,6南を通常通過。Save30/独立Continue受入。12712円/party4/RP0/badge1、HP/PP不変。story flag4367/洞窟走破は未完。'
    state['do_not_repeat'].append('Save30の46/cold13入力・18画面・新12controller/20受入試験を無影響再走しない。全33memberと既存失敗原本を保持。flag4367/洞窟走破へ昇格しない。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 西岩階段の通常通過とSave30
- Version: story-cave-stairs-save30-v1
- Status: DONE（西岩階段/下層保存限定。story解禁/洞窟走破は未完）
- Summary: Save29の17,4→13,4→13,5岩階段→13,6南。通常Save30/独立Continue。今回戦闘0、HP/PP/party全600byte不変。
- Files changed: Save30 controller/12変更試験/20受入試験/record workflow、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、46/cold13入力・18画面・全33member。Bag/flags/PC/S61E/全国図鑑保持、var4021は81→87/4022は0→1、runtime owner未解決。42checksum/6941byte差分/全SaveRTC保持。新12controller原本を再利用、新20受入のみ実行してstderr全保存。record native0/ROM変更0/旧ゲーム再走0。
- History: Save29のnative0 preflight失敗/旧guide宛先guard/絶対pathprivateguard失敗は原本保持。既通過試験の証拠限界も変更しない。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushし全text読戻し。
- Network: 同repo GitHub/Actions原本だけ。既存ROM/runtime/input Save29の再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
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
