#!/usr/bin/env python3
"""博物館退出Save97を原本から独立受入し、固定引継ぎ/両ログを更新。native0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT),str(ROOT/'tests')]
import pr16_story_save97_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-MUSEUM-EXIT-SAVE97';OUT=ROOT/'.local/pr16-story-save97-record'
CODE={'scripts/pr16_story_save97_accept.py','scripts/pr16_story_save97_record.py','tests/test_pr16_story_save97_accept.py',a.VISUAL,'content/modernization/pr16_story_save97_next_route.json','.github/workflows/pr16-story-save97-record.yml'}
FAIL_RUN,FAIL_JOB,FAIL_SOURCE,FAIL_ART=37193632724,111410836072,'c404c3b02f51e3d27029aebe9f8ad4e24ce4d6d3',11299424063
FAIL_ARCHIVE=dict(size=91504,sha256='dd8d4d38b4ec884591a441fda96b688025a1edb6e067889a86e3777cba5cc7cd')
def unpack_verified(artifact,run,archive,source,target,count):
    meta,z=a.transport.archive(artifact,run,archive,source);target.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==count and set(z.namelist())==set(manifest)|{'manifest.json'},'全manifest member')
        need(all(Path(n).suffix in{'.srm','.ppm','.txt','.json'}and not n.startswith('/')and'..'not in n.split('/')for n in z.namelist()),'新save/画面/textのみ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'全member '+n)
        z.extractall(target)
    return meta,manifest

def controller_receipt():
    rows=[]
    for job,executed,failed in [(111410610357,46,1),(FAIL_JOB,1,0),(a.JOB,22,0)]:
        raw=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode();log=raw.splitlines();lines=[v.split('Z ',1)[-1]for v in log if' ... 'in v and'test_pr16_story_save97_measure.'in v]
        need(len(lines)==executed and sum(v.endswith(' ... ok')for v in lines)==executed-failed and sum(v.endswith(' ... FAIL')for v in lines)==failed,'新controllerの原本行だけ再読')
        need(any('Ran '+str(executed)+' test'in v for v in log),'unit件数終端')
        rows.append(dict(job=job,executed=executed,passed=executed-failed,failed=failed,test_lines=lines))
    import test_pr16_story_save97_measure as tests
    need(unittest.defaultTestLoader.loadTestsFromModule(tests).countTestCases()==48,'最終controller48case。loadのみ再走0')
    return dict(final_cases=48,executions=69,passed_executions=68,failed_executions=1,unchanged_success_reruns=0,phases=rows,scope_ja='初回46(45成功1fixture失敗)、失敗1だけ修正成功、behavior修正影響22成功。旧no_stair caseはsouth_arrowへ置換。無影響成功caseの再実行なし。')

def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists()and not(ROOT/a.CP).exists(),'新記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need({a.GUIDE,a.CP}.isdisjoint(protected)and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入を書き換えない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37193064130,'2923268a967ed11823210fa044cfdf085d944ba1',111409138080,['success']*11)
    failed_terminal=inherited.terminal(FAIL_RUN,FAIL_SOURCE,FAIL_JOB,['success','success','success','failure','skipped','success','success','success'])
    controller=controller_receipt()
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        mf=json.loads(z.read('manifest.json'));need(len(mf)==62 and set(z.namelist())==set(mf)|{'manifest.json'},'親Save96全62member')
        for n,b in mf.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save96/不変ROM')
    original=OUT/'original';meta,manifest=unpack_verified(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE,original,61)
    failed=OUT/'failed-exit';failedmeta,failedmanifest=unpack_verified(FAIL_ART,FAIL_RUN,FAIL_ARCHIVE,FAIL_SOURCE,failed,31)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==46 and visual['reviewed_screens']==dict(progress=list(range(44)),**{'continue':[0,1]})and visual['save_success_wording_observed']is True,'全46原画目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'原画 '+n)
    need(visual['failed_exit_review']['reviewed_progress_screens']==list(range(24)),'失敗24画面も観測')
    result=a.verify(original,before,rom);failure=a.failed_exit(failed)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE97_ORIGINAL=str(original),PR16_SAVE96_INPUT=str(assets/'input.srm'),PR16_SAVE97_ROM=str(assets/'candidate.gba'),PR16_SAVE97_FAILED=str(failed))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save97_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    lines=[v for v in unit.stderr.decode().splitlines()if v.startswith('test_')]
    need(unit.returncode==0 and not unit.stdout and len(lines)==77 and all(v.endswith(' ... ok')for v in lines)and re.search(rb'\nRan 77 tests in [0-9.]+s\n\nOK\n\Z',unit.stderr),'77成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for folder,prefix in [(original,''),(failed,'failed-exit/')]:
        for p in sorted(folder.rglob('*')):
            if not p.is_file()or p.suffix not in{'.json','.txt'}:continue
            raw=p.read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ');dest=evidence/(prefix+p.relative_to(folder).as_posix());dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr);write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'failed-exit-terminal.json',failed_terminal);write(evidence/'failed-exit-verification.json',failure)
    write(evidence/'controller-test-receipt.json',controller);write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    rule=a.next_route()['transition_preflight_rule_ja']
    goal='Save97 artifact11300361541のstory-fast.srm（131088bytes/SHA256 4871ba79e718ea8dc8bc701394846ce1b393cd41a5961564ed4d670437a52139）だけから再開。博物館退出後の町3/2・19,26南。新13歩/3旋回、14,9の0x65南矢印で退出、町warp19,25から自動南1歩を実測し通常Save97/独立Continue受入。次は保存next-routeの町北端28,0まで35歩、通常北入力でmap3/23へのconnectionを越え最初のfieldだけ保存。Ranger local9/18,27はさらに後続、4382setを条件に4072=2/4352clear/町warpへ進む静的ownerを保存したが未実行。封書会話/受付/階段/退出成功区間を再走しない。紙274=0/4382/4383/4380未完/4061=1/23114円/バッジ2/全party600byte/HP277/294/PP3,9,8,2保持。観測5でRAM台帳変更、physical2056clear、aux4021:109→122/4022:1→4と過去owner未解明。46画面80+cold13入力、38counter97でも保存中/途中hash→39成功文言/安定最終hash→43clearfield。cold差分752pixelは左端NPC/花animation内、全SaveRTC/PC/S61E/旧bank保持。controller最終48case/69実行68成功1失敗、新受入77。成功native2/退出失敗native1/記録native0。最初のfixture失敗と13,9通常床非発火の失敗原本は保持。Save96のimport連鎖154module/入口上限1500修復は不変、受入済み72再走0。全国図鑑/自然成長進化/全story/release未受入。ROM/runtime非再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。'+rule
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save97_accepted=True,museum_exit_accepted=True,letter_handoff_accepted=True,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=48,controller_executions=69,controller_passed_executions=68,controller_failed_executions=1,unchanged_controller_cases_replayed=0,new_acceptance_tests=77,successful_native_processes=2,prior_failed_native_processes=1,prior_pre_native_failed_attempts=1,total_native_processes=3,record_native_processes=0,failed_exit_artifact={k:failedmeta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},failed_exit_verification=failure,next_goal_ja=goal,transition_preflight_rule_ja=rule,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f'''# 博物館退出・Save97限定受入

`{result['status']}`。封書引渡し後のSave96から新13歩/3旋回。14,9の赤い南矢印へ追加南入力して町3/2・19,26南へ初退出、最初のfieldで通常Save97と独立Continueを受入。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。61member/46画面/80+cold13入力。controller最終48case/69実行68成功1失敗、新受入77。成功native2/退出失敗native1/記録native0/ROM変更0/旧受入再走0。

## 失敗と復旧

初回controller46件中45成功、1件はoff-warp変異fixtureに正当な1歩前の座標を使った誤検査。fixtureだけ訂正し1件成功、既成功45再走0。その後nativeは親static計画の13,9で南8回でも非発火し有限停止。run37193632724/artifact11299424063、58入力24画面、通常保存0、Save96全131088byte保持。失敗は削除・成功換算しない。

固定ROMでは13,9/15,9は普通床0x08、14,9だけ0x65南矢印。warp-table登録だけでは発火しない。固定上流c75f3523のTryArrowWarpと方向predicateも確認。修正影響22検査だけ通し、未受入退出区間から回復。入力原本・旧受入sourceは不変。

## 保存・保持・目視

0〜16は13歩/旋回3、17で町19,26南。18〜22menu0→4、23/24確認、25〜38保存中、38counter97でも途中hash。39で成功文言/安定最終hash、43でoverlayなしclearfield。hash/counter単独の完了主張なし。

43→cold0/1は778/626pixel、cold間752pixel差。左端NPC矩形x0..15/y83..102と花animation x64..143/y137..159だけ。全画面一致とはしない。SaveRTC全131088byte/PC/S61E/旧Save96bank57344byte保持。差分7043byte1752範囲、42checksum。

全party600byte/HP277/294/PP3,9,8,2/23114円/紙274=0/4382/4383/4061=1/バッジ2保持。4380未完。RAM台帳は観測5旋回で変化し、その後/cold保持。physical2056:1→0、aux4021:109→122/4022:1→4のruntime owner未解明。過去ownerを解決済みにしない。Save96のfresh import失敗・154moduleと有限1500修復を保持し、旧72受入の再走0。

## 次の境界

[町北35歩とnorth connection](../content/modernization/pr16_story_save97_next_route.json)。町28,0から北入力、map3/23・28,39が静的候補。座標/自動歩行はnative未確認。最初のfieldだけ保存。Ranger local9/18,27は後続。静的scriptは4382を条件に4072=2/4352clear/町warpだが、会話もstory進行もまだ未受入。

{rule}

{goal}
'''
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本不変')
    state['story_save96']['record_completion']=prior_done
    state['story_save97']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[3,2],xy=[19,26],facing=1,rp=0,money=23114,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],museum_exit_accepted=True,museum_admission_var4061=1,letter_handoff_accepted=True,paper_quantity=0,paper_flag4383=True,paper_flag4382=True,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal,failed_exit=failure,transition_preflight_rule_ja=rule)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='博物館退出13歩/0x65南矢印とSave97。誤static出口失敗を保持して限定回復。旧成功再走0。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='博物館退出Save97/町3/2・19,26南。13歩/3旋回/南矢印/自動南1歩。46画面80+cold13入力。38counter97保存中→39成功→43clearfield。全party/23114円/4382/4383/4061保持。RAM観測5/2056clear/aux2varsと過去owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stop='Save97/町19,26南から北端28,0まで35歩、通常北入力でmap3/23の最初fieldだけ保存。Ranger会話は後続。未知NPC/戦闘/eventで縮小停止。封書/受付/階段/退出成功区間再走なし。'+rule
    state['next_action'].update(id='STORY_ROUTE505_FROM_SAVE97',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save97_accept.py','scripts/pr16_story_save97_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,'content/modernization/pr16_story_save97_exit_recovery.json','content/modernization/pr16_story_save97_next_route.json'],stop_rule_ja=stop)
    state['do_not_repeat'].append('Save97の80/cold13入力46画面61member、新13歩/3旋回/0x65南矢印/町自動南1歩、controller最終48case(69実行68成功1失敗)/新受入77を無影響再走しない。初回controllerfixture失敗、通常床13,9の失敗native1/58入力24画面/Save96保持を歴史保存。次は町北35歩の新区間。'+rule)
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='博物館退出Save97/町3/2・19,26南。全party/HP277/PP3,9,8,2/紙274=0/4382/4383/23114円/4061保持。RAM観測5/2056clear/aux2varsと過去owner未解明。次は町北35歩。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'''
## {stamp}
- Version: PR16-STORY-SAVE97
- Timestamp: {stamp}
- Task: {TASK} / 博物館退出とSave97
- Status: DONE（退出/保存/独立Continue限定、505道路接続とRangerは未到達）
- Summary: 固定ROMの0x65/14,9南矢印を解決し新13歩/3旋回で退出、町19,26南で通常Save97/Continue。全party600byte/HP277/PP3,9,8,2/バッジ2/23114円/4061/4382/4383/PC/S61E保持。
- Files changed: Save97 measure/preparation/controller/失敗原本と復旧/受入77/record/checkpoint/text証拠/次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。80+cold13入力46画面61member。controller最終48/69実行68成功1失敗、新受入77。成功native2/失敗native1/記録native0/compile0/旧成功再走0。
- Evidence: 初回controllerfixture1失敗を1件だけ修正。旧static13,9は0x08で58入力24画面の失敗native、Save96全保持。0x65/14,9へ修正し影響22成功。38counter97でも保存中/途中hash→39成功文言/最終hash→43clearfield。cold差分752pxはNPC/花animationだけ。42checksum/7043byte1752範囲/全SaveRTC/旧bank保持。
- Discovery: RAM観測5、physical2056clear、aux4021:109→122/4022:1→4と過去runtime owner未解明。Save96記録run37193064130全11step終端同期。154module/有限上限1500修復と旧72受入不変。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repoGitHub/Actions、source-lock固定pret/pokefirered c75f3523のmetatile/field_control_avatar。入力ROM/runtime非再配布、ROM変更/merge/release/baseline変更0。一般CI既知不一致を全成功にしない。
- Rule: {rule}
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
