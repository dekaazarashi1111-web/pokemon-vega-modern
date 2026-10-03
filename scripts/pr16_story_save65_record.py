#!/usr/bin/env python3
"""上階のA1回会話・りかけい155新1勝Save65原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save65_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MANSION-TRAINER155-SAVE65'
OUT=ROOT/'.local/pr16-story-save65-record'

CODE={'scripts/pr16_story_save65_accept.py','scripts/pr16_story_save65_record.py','tests/test_pr16_story_save65_accept.py',a.VISUAL,'.github/workflows/pr16-story-save65-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE65_JA.md' and a.CP=='content/modernization/pr16_story_save65_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save65_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37161576580,'7201d8628d7f1b51d714724c701f861623a676d1',111315928828,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save65_measure.',27)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==69 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save64全69member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save64/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==70 and len(z.namelist())==71 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save65member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==55 and visual['reviewed_screens']==dict(progress=list(range(53)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save65画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save65画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE65_ORIGINAL=str(original),PR16_SAVE64_INPUT=str(assets/'input.srm'),PR16_SAVE65_ROM=str(assets/'candidate.gba'))
    failed_source='2d67f3472934b600a6f9e18d624c58c6f93da384'
    # 初回56成功はそのまま継承。誤ってcold開始行をmutationした2caseだけ訂正する。
    previous=h.d.git('show',failed_source+':tests/test_pr16_story_save65_accept.py').decode()
    expected=previous.replace("'event_lock':('progress',0,'lock',0)","'event_lock':('progress',1,'lock',0)").replace("'event_field':('progress',0,'field',True)","'event_field':('progress',1,'field',True)")
    need((ROOT/'tests/test_pr16_story_save65_accept.py').read_text()==expected and expected!=previous,'変更影響は観測index0→1の2mutationだけ')
    need(h.d.git('show',failed_source+':scripts/pr16_story_save65_accept.py')==(ROOT/'scripts/pr16_story_save65_accept.py').read_bytes(),'受入oracle本体不変')
    prior_run=h.d.inputs.api('actions/runs/37161916477');need(prior_run['head_sha']==failed_source and prior_run['status']=='completed'and prior_run['conclusion']=='failure','最初の記録failureを保持')
    _,prior_zip=a.transport.archive(11287926896,37161916477,dict(size=1234,sha256='311b08f403503e6edbb8edcfaa95333dc1e7245fde5161d25c990c58368dd5de'),failed_source)
    with prior_zip:
        need(set(prior_zip.namelist())=={'unit.stdout.txt','unit.stderr.txt'}and not prior_zip.read('unit.stdout.txt'),'初回unit原本2member')
        prior_stderr=prior_zip.read('unit.stderr.txt')
    old_lines=[v for v in prior_stderr.decode().splitlines()if v.startswith('test_')]
    names=['test_reject_event_field','test_reject_event_lock']
    need(len(old_lines)==58 and sum(v.endswith(' ... ok')for v in old_lines)==56 and sorted(v.split(' ',1)[0]for v in old_lines if v.endswith(' ... FAIL'))==names and re.search(rb'\nRan 58 tests in [0-9.]+s\n\nFAILED \(failures=2\)\n\Z',prior_stderr),'初回56成功/2誤mutationの正確な終端')
    env['PYTHONPATH']=str(ROOT/'tests')
    unit=subprocess.run([sys.executable,'-B','-m','unittest',*['test_pr16_story_save65_accept.Acceptance.'+n for n in names],'-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==2 and all(line.endswith(' ... ok')for line in test_lines)and sorted(v.split(' ',1)[0]for v in test_lines)==names and re.search(rb'\nRan 2 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'訂正2caseだけ成功。初回成功56case再走0')
    recovery=dict(prior_run_id=37161916477,prior_job_id=111316948030,prior_source=failed_source,prior_conclusion='failure',prior_artifact_id=11287926896,prior_successful_tests=56,prior_failed_mutations=names,corrected_case_executions=2,reused_successful_cases=56,replayed_successful_cases=0,unique_accepted_tests=58,total_executions=60,unit_code_change_ja='会話の観測indexだけ0→1。oracle変更0。native再走0。')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save64-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    (evidence/'prior-unit.stderr.txt').write_bytes(prior_stderr)
    write(evidence/'acceptance-recovery.json',recovery)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save65 artifact11287846702のstory-fast.srm（131088bytes/SHA256 c3d67760ba4c452c48abddbf423ea9bd5a052e38227fee85e47e299a60a45dda）だけから再開。上階map1/60・26,6西。A1回で隣接カケル/りかけい155に新1勝、敵3体・つばめがえし3選択/実PP5→2・交代拒否2・賞金360円/physical1435を限定受入。歩行0、通常Save65/独立Continue。HP288/294・PP15,10,15,2、party残り599byte/Bag/RP0/badge1/story4071=9/4072=1/全legacy vars/PC保持、19104円。次はNPC25,6を避ける保存済静的28歩候補:26,6→26,5→25,5→24,5→23,5→23,6→23,11→25,11→25,16→31,16→穴31,21。最初の新event/戦闘/不通境界で保存。穴→入口31,22/南東階段→紙側は未実測。つばめがえし残2PP、host補充なし、残量に応じて通常技を選ぶ。27新controller/58新受入（56継承+訂正2、計60実行、成功例再走0）、99+cold13入力55画面70member/native2。47counter65部分write、48成功→52field、全SaveRTC/field画面同一。RAM台帳6/27変化のruntime owner未解明。旧offset41/2056/aux/40ac未解明保持。Flash未使用/がくしゅうそうち未装備。既受入階段/経路/野生戦/隣接会話trainer戦/保存は無影響再走しない。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save65_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,inert_warp8_activation=False,normal_recovery_repeated=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=27,controller_executions=27,unchanged_controller_cases_replayed=0,new_acceptance_tests=58,acceptance_test_executions=60,acceptance_recovery=recovery,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 上階の隣接カケル1勝・Save65限定受入

`{result['status']}`。Save64の26,6西からA1回で西隣NPCと会話。りかけいのおとこカケル（trainer155）に新1勝、通常保存・独立Continue。歩行0、穴と像の紙は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。70member/55画面/99+cold13入力。新controller27case、58新受入拒否試験（初回56成功・誤mutation2件、観測indexを訂正して2件だけ成功。成功56件の再走0、計60実行）。native2/record0/旧受入再走0/ROM変更0。

## 会話・trainer戦と保存

0開始、1会話「ひとりごとのじゃましないでよ」、2導入、3りかけいのおとこのカケル。4コイキング♀Lv12、13ウパー♀Lv14、19クヌギダマ♂Lv15。9/15/21つばめがえし選択、実PP5→4→3→2、12/18交代拒否。24勝利、25降参台詞、26賞金360円、27field。敵3体撃破はtrainer1勝だけ。

28〜32menu0→4、33確認/34上書き、35〜47保存中。47counter65でも部分write、48〜51成功文言、52field。progress27/52/cold0/cold1全画面byte一致、全SaveRTC一致。

## 保存差分と次の新経路

party600byte中PP55の5→2だけ、残り599byte/HP288/294・ミュウツー全HP/PP・EXP/持物・全Bag/RP0・全legacy vars・PC/S61E全payload・旧Save64bank57344byte保持。所持金18744→19104、physical1435:0→1だけ。保存済local7のtrainer155命令と固定remap155+0x500→1435をROM byte照合。ただしruntime object IDは直接捕捉していない。RAM台帳は6と27で変化、owner未解明。42checksum/6856byte1665範囲。

[次の静的経路](../{a.EVIDENCE}/next-route.json)はNPC占有25,6を除いた28歩。26,6から北へ26,5→25,5→24,5→23,5→23,6と未通過床を進み、穴31,21へ向かう。旧候補のNPC tileを無理に反復しない。実通行/穴/南東階段/紙側接続は未受入。つばめがえし残2PP、通常技の残量を守りhost補充しない。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。一般CI既知不一致/action_requiredを成功にしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save64']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37161576570');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='7201d8628d7f1b51d714724c701f861623a676d1','旧Stage79終端')
    state['story_save64']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save65']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,60],xy=[26,6],facing=3,rp=0,money=19104,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[15,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,inert_warp8_activation=False,trainer_victories=1,wild_victories=0,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),acceptance_recovery=recovery,static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='A1回隣接会話/りかけいカケル新1勝/Save65。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='上階26,6西からA1回会話/カケル155新1勝/Save65。歩行0/PP5→2/360円・1435bit。穴/紙未到達。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_NPC_AVOIDING_ROUTE_FROM_SAVE65',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save65_accept.py','scripts/pr16_story_save65_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save62_evidence/route-plan.json','content/modernization/pr16_story_save57_preparation.json'],stop_rule_ja='Save65上階26,6西から北迂回5歩でNPC25,6を避け、穴31,21まで未通過28歩候補。最初の新event/戦闘/不通境界で保存。つばめがえし残2PP、host補充なし。旧会話/戦闘/保存は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='西隣のカケルへA1回会話し新1勝でSave65。26,6西、PP5→2/賞金360円。次はNPCを避ける未通過北迂回から穴へ。'
    state['do_not_repeat'].append('Save65の99/cold13入力55画面70member/27controller/58受入を無影響再走しない。A1回/歩行0/りかけい155新1勝/実PP3/360円/1435bit。47counter65部分write→48成功→52field、全SaveRTC/field画面一致。RAM台帳6/27変化owner未解明。北迂回28歩は静的候補、穴/紙未到達。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 隣接カケル新1勝Save65
- Version: story-mansion-adjacent-trainer155-save65-v1
- Status: DONE（A1回会話/trainer1勝/保存/独立Continue限定。初回記録failureは維持）
- Summary: 上階26,6西からA1回。りかけいカケル155/敵3体に新1勝、PP5→2、交代拒否2、賞金360円/1435bit。歩行0/HP288/294/party残り599byte/Bag/RP0/全vars保持、19104円。
- Files changed: Save65 measure/27controller/58受入/record、checkpoint/text証拠/北迂回静的経路、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。99+cold13入力55画面70member。新27controller原log継承/58新受入拒否試験（初回56成功・誤mutation2件、観測indexを訂正して2件だけ成功。成功56件の再走0、計60実行）。record native0/compile0/既受入再走0。
- Evidence: 47counter65部分write→48成功→52field。全SaveRTC/field画面一致。RAM台帳6/27変化owner未解明。旧bank57344byte/42checksum/6856byte1665範囲。静的trainer155命令と1435remap照合。次の28歩はNPC25,6を除外した未通過北迂回、穴/紙は未実測。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actionsのみ。既存ROM/runtime/input非再配布。一般CI既知不一致/action_requiredは全成功にしない。merge/release/baseline変更0。
- Next: {goal}
"""
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



