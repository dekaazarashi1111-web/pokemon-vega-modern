#!/usr/bin/env python3
"""戻り転送と野生戦のSave37原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save37_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-CAVE-EXIT-SAVE37'
OUT=ROOT/'.local/pr16-story-save37-record'

CODE={'scripts/pr16_story_save37_accept.py','scripts/pr16_story_save37_record.py','tests/test_pr16_story_save37_accept.py',a.VISUAL,'.github/workflows/pr16-story-save37-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE37_JA.md' and a.CP=='content/modernization/pr16_story_save37_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save37_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37125940788,'a194033c4599fd27746c5f5d4f29c99287eef165',111211121386,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    tests=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save37_measure.' in v]
    need(len(tests)==12 and any('Ran 12 tests in 'in v for v in log) and any(v.endswith(' OK')for v in log),'変更12exit controller試験原本')
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==130 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save36全130member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save36/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==48 and len(z.namelist())==49 and set(z.namelist())==set(manifest)|{'manifest.json'},'全48member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==33 and visual['reviewed_screens']==dict(progress=list(range(31)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全33画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全33画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE37_ORIGINAL=str(original),PR16_SAVE36_INPUT=str(assets/'input.srm'),PR16_SAVE37_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save37_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==26 and b'\nOK\n'in unit.stderr and b'skipped'not in unit.stderr,'新26受入/拒否試験')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save36-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'record-preflight-failure.json',inherited.terminal(37126331827,'8728140fd123b5fa5faabfd9cd49debdfb91dca7',111212235538,['success','success','success','failure','skipped','skipped','skipped','skipped','success','success','success']))
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',dict(job=a.JOB,passed_tests=12,test_lines=tests,replayed_tests=0))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save37 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map1/38・6,4西・party4/RP0・13576円・badge1・story4071=8/4072=1、ミュウツーHP320/354・PP[1,8,0,0]。'
      'Save36の正規event/trainer360完了地点から洞窟本区画4,19→南出口部屋1/38へ通常warpし、Save37/独立Continueを限定受入。本区画走破のmilestoneは完了。外の503番道路への接続/全storyはまだ未受入。'
      '次は部屋6,4→6,5→5,5→4,5→4,6の通常出口候補。保存済map1/38 warp0は4,6→map3/21 warp1。必要なら既存のmap3/21 warp1保存ownerを照合し、未保存のtargetだけ限定採取する。'
      'host回復/PP/flag/var注入は禁止。受入済の西側event・trainer360・洞窟本区画・今回63/cold13入力33画面/12controller26受入を無影響再走しない。'
      'party600byte/Bag/13576円/PC/S61E/story値は不変、補助flag2056=0→1とvar4021=19→26/4022=0→2/404d=20→21だけ。runtime owner未解決。24のFlash一時一致/counter36を保存完了にせず、25のhash再差分、26〜29成功文言/安定全Flash、30field復帰/cold全SaveRTC一致を区別。'
      '残件は出口部屋→外の通常接続とその先のstory、正規全国図鑑解禁、分離progressionの自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。trainer352は未受入だがこの正規出口経路を通るための追加勝利へ捏造せず、未実施のまま保持。'
      'HM05は所持のみで未習得/未使用、同じ拒否入力を反復しない。全story/一般CI全成功/製品releaseは未完。clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断の境界を保持。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save37_accepted=True,cave_interior_exit_accepted=True,cave_interior_crossing_complete=True,outside_route503_reached=False,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=12,new_acceptance_tests=26,record_preflight_failure=dict(run_id=37126331827,native_processes=0,acceptance_tests_run=0,reason="全legacy不変仮定が補助flag2056で停止"),prior_failed_native_processes=0,total_development_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 洞窟本区画南出口・Save37 限定受入

`{result['status']}`。Save36の6,13から南へ通常歩行し、4,19のwarpでmap1/38・6,4西の南出口部屋へ到達。通常Save37/独立Continueまで限定受入。西側開通/正規event/trainer360を含む本区画走破のmilestoneは完了した。出口部屋から外の503番道路への接続と全storyは未受入のまま保持する。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全48member、63/cold13入力、33画面。新12controllerと26原本受入/拒否試験、native2/記録native0。ROM/fixture/compile/既受入再走0。地形920cells/出口warp/接続部屋viewは保存原本再利用。

戦闘0・party600byte/HP320/PP[1,8,0,0]/全Bag/HM05/13576円/PC/S61E/story4071=8/4072=1・badge1不変。補助flag2056=0→1とvar4021=19→26/4022=0→2/404d=20→21のruntime ownerは未解決。42sector checksum/旧Save36bank57344byte/6917byte1753範囲差分/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400保持。

13〜23は部分write、24は書込中画面/counter36のまま最終Flash hashと一時一致し、25では再び異なる。単一hash一致を保存完了としない。26〜29でcounter37・安定全Flashと保存成功文言、30でfield復帰。独立Continue0/1も同じ南出口部屋。全sector checksum/全SaveRTC比較と画面の異なる意味を保つ。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save36']['record_completion']=prior_done
    state['story_save37']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[1,38],xy=[6,4],facing=3,rp=0,money=13576,badge_count=1,story_vars={'4071':8,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,cave_interior_exit_accepted=True,cave_interior_crossing_complete=True,outside_route503_reached=False,story_flag4367_accepted=True,cave_crossing_complete=False,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='洞窟本区画から南出口部屋への通常接続/Save37を限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='洞窟本区画南出口→map1/38・6,4/Save37測定source。本区画走破完了、出口部屋から外/全国図鑑/全story未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stage79=h.d.inputs.api('actions/runs/37125940822')
    need(stage79['status']=='completed' and stage79['conclusion']=='success' and stage79['head_sha']=='a194033c4599fd27746c5f5d4f29c99287eef165','Save36記録source Stage79終端')
    state['story_save36']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['next_action'].update(id='STORY_OUTSIDE_SOUTH_EXIT_ROOM_FROM_SAVE37',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save37_measure.py',a.m.TERRAIN,'content/modernization/pr16_story_acceleration_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save37南出口部屋から外の通常接続へ。本区画走破と全story完了を区別して到達milestone/残件を報告。既受入を無影響再走せず正規UIのみ。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='洞窟本区画南出口→map1/38・6,4西/Save37・独立Continue受入。本区画走破のmilestone完了。13576円・HP320/PP[1,8,0,0]。出口部屋から外/全国図鑑/自然成長/全storyは未完。'
    state['do_not_repeat'].append('Save37の63/cold13入力・33画面・12controller/26受入を無影響再走しない。24Flash一時一致/counter36→25再差分→26安定/成功文言→30fieldを区別。本区画南出口は受入、外503接続/全story未完。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 洞窟本区画南出口・Save37
- Version: story-cave-south-exit-room-save37-v1
- Status: DONE（本区画南出口/通常保存Continue限定受入）
- Summary: Save36の正規event後6,13から南へ進み4,19→map1/38・6,4西の出口部屋へ到達。西側開通/event/trainer360を含む本区画走破のmilestoneを完了。外の503番道路/全国図鑑/自然成長/全storyは未完。
- Files changed: Save37 controller/12変更試験/26受入拒否試験/record workflow、checkpoint/text原本、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、63/cold13入力/33画面/48member/native2。新12controllerは原log継承、新26受入だけ実行、record native0。party600byte/Bag/13576円/PC/S61E/story不変、補助flag2056=0→1、HP320/PP[1,8,0,0]。補助var3件owner未解決。42checksum/旧bank57344byte/6917byte1753範囲/cold全SaveRTC一致。24の一時全Flash一致を完了とせず、25再差分/26〜29成功文言/30fieldを区別。
- History: 記録run37126331827は全legacy不変仮定が補助flag2056の0→1で停止（native0/受入試験0）。同flagだけを新oracleで限定照合しruntime owner未解決/旧failureを保持。Save36記録run37125940788/Stage79 run37125940822のsuccess終端を反映。旧失敗原本は保持、既受入ゲーム再走0、ROM/compile/fixture0。保存済920cells/warp接続再採取0。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actions原本のみ。既存ROM/runtime/input Save36再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
- Next: {goal}
'''
    for name in h.d.LOGS:
        with(ROOT/name).open('a',encoding='utf-8')as f:f.write(entry)
    write(OUT/'owned.json',sorted(owned));h.d.git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    h.d.current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(h.d.read(OUT/'owned.json'));g.guard();h.d.git('diff','--cached','--check')
def snapshot():
    for n in h.d.read(OUT/'owned.json'):need(h.d.git('show','HEAD:'+n)==(ROOT/n).read_bytes(),'全text読戻し '+n)
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+h.d.git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot);need(len(sys.argv)==2 and sys.argv[1]in actions,'record|guard|snapshot');actions[sys.argv[1]]()
