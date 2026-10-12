#!/usr/bin/env python3
"""博物館初下降Save96原本を独立受入し固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import ast,datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save96_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-MUSEUM-DESCENT-SAVE96'
OUT=ROOT/'.local/pr16-story-save96-record'
CODE={'scripts/pr16_story_save96_accept.py','scripts/pr16_story_save96_record.py','tests/test_pr16_story_save96_accept.py',a.VISUAL,'content/modernization/pr16_story_save96_next_route.json','.github/workflows/pr16-story-save96-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists()and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE96_JA.md'and a.CP=='content/modernization/pr16_story_save96_checkpoint.json'and a.EVIDENCE=='content/modernization/pr16_story_save96_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected)and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37191567861,'e08e19c43f067d2f659b8e3acc64eb4ab4b64c47',111404656251,['success']*11)
    failed_record=inherited.terminal(37192785450,'ebf7b33c307d028354d35bddc0f9e2bf030a86d1',111408313462,['success','success','success','failure','skipped','skipped','skipped','skipped','success','success','success'])
    _,z=a.transport.archive(11300145384,37192785450,dict(size=2280,sha256='d2a64d5219f9b132240fa9ce213e1a4942a74159800e463ce864d046bdb5f8c4'),'ebf7b33c307d028354d35bddc0f9e2bf030a86d1')
    with z:
        need(set(z.namelist())=={'unit.stderr.txt','unit.stdout.txt'}and not z.read('unit.stdout.txt'),'失敗記録2member')
        prior_error=z.read('unit.stderr.txt').decode();need('RecursionError: maximum recursion depth exceeded'in prior_error and 'Ran 1 test in 0.000s'in prior_error and 'FAILED (errors=1)'in prior_error,'fresh unittest import失敗、71実試験未実行')
        chain=[Path(p).name for p in re.findall(r'  File "([^"\n]+)", line [0-9]+, in <module>',prior_error)if '/scripts/'in p]
        expected=[n for k in range(96,24,-1)for n in ['pr16_story_save'+str(k)+'_accept.py','pr16_story_save'+str(k)+('_admission_measure.py'if k==93 else'_measure.py')]]+['pr16_story_save24_accept.py','pr16_story_save24_detour.py','pr16_story_save24_measure.py','pr16_story_save23_accept.py','pr16_story_save23_measure.py','pr16_story_after_maori_measure.py','pr16_research_story_route_actions.py','pr16_research_story_actions.py','pr16_research_lifecycle_actions.py','pr16_research_bag_actions.py']
        need(chain==expected and len(chain)==len(set(chain))==154,'観測import鎖は96→25の単調履歴と既知tail154個。循環/未知edgeなし')
        for src,dst in zip(chain,chain[1:]):
            tree=ast.parse((ROOT/'scripts'/src).read_bytes());imports={v.name for n in ast.walk(tree)if isinstance(n,ast.Import)for v in n.names}|{n.module for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)}
            need(dst[:-3]in imports,'observed直接importを実tracked sourceで照合 '+src)
        failure_receipt=dict(terminal=failed_record,artifact=11300145384,archive=dict(size=2280,sha256='d2a64d5219f9b132240fa9ce213e1a4942a74159800e463ce864d046bdb5f8c4'),members={n:identity(z.read(n))for n in z.namelist()},observed_import_chain=chain,observed_unique_modules=154,observed_import_cycle=False,all_observed_edges_source_verified=True,entrypoint_recursion_limit=1500,later_maintenance_ja='checkpoint履歴のimport依存整理は別作業。今回旧moduleの変更/全依存refactorなし。',loader_failures=1,acceptance_cases_executed=0,acceptance_cases_never_run=71,native_processes=0,source_parser_positive_completed=True,cause='RecursionError: maximum recursion depth exceeded',repair_ja='不変な過去154固有module連鎖のfresh unittest importが既定1000に達した。この新受入入口だけ有限1500へ引上げ。旧module/ROM/native原本は不変。新上限1試験を追加し72caseを初実行。')
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines();lines=[v.split('Z ',1)[-1]for v in log if' ... 'in v and'test_pr16_story_save96_measure.'in v]
    need(len(lines)==40 and all(v.endswith(' ... ok')for v in lines)and any('Ran 40 tests'in v for v in log)and any(v.endswith(' OK')for v in log),'新controller40の成功行/終端だけ再読')
    controller=dict(job=a.JOB,passed_tests=40,executed_tests=40,failed_tests=0,test_lines=lines,replayed_unchanged_passed_tests=0)
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==81 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save95全81member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save95/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==62 and len(z.namelist())==63 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save96member')
        need(all(Path(n).suffix in{'.srm','.ppm','.txt','.json'}and not n.startswith('/')and'..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==47 and visual['reviewed_screens']==dict(progress=list(range(45)),**{'continue':[0,1]})and visual['save_success_wording_observed']is True,'全47原画目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE96_ORIGINAL=str(original),PR16_SAVE95_INPUT=str(assets/'input.srm'),PR16_SAVE96_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save96_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    lines=[v for v in unit.stderr.decode().splitlines()if v.startswith('test_')]
    need(unit.returncode==0 and not unit.stdout and len(lines)==72 and all(v.endswith(' ... ok')for v in lines)and re.search(rb'\nRan 72 tests in [0-9.]+s\n\nOK\n\Z',unit.stderr),'72成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in['measurement.json','manifest.json','save95-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ');dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr);write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'failed-record.json',failure_receipt)
    write(evidence/'controller-test-receipt.json',controller);write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save96 artifact11299780050のstory-fast.srm（131088bytes/SHA256 1f1d30d7f8261ff8b03f0bf290aaa61d052709b6a0a1c259da13f16895cd4b81）だけから再開。封書引渡し後の新復路13歩/5旋回、西入力で博物館1階6/0・8,8西へ初下降しSave96/独立Continueを受入。次は新復路12歩で出口13,9、最初の町3/2 fieldを保存。町19,25/19,26は静的候補、自動歩行は未確認。受付4061=1のため12/13/14,5の条件4061==0は非発火。封書会話/50円受付/階段/旧入館を再走せず、505道路レンジャーは退出後。紙274=0/4382/4383/未完4380/23114円/バッジ2/全party600byte/HP277/294/PP3,9,8,2保持。今回全RAM台帳保持だがphysical2056:0→1とaux4021:96→109/4022:3→1のruntime owner未解明、過去ownerも未解明。47画面83+cold13入力。39は最終flash hashと一時一致でも保存中/counter95、40別hash/counter96、41成功文言/安定finalhash、44clearfield。cold間142pixel差はNPC1人矩形内、全画面一致とはしない。全SaveRTC/PC/S61E/旧bank保持。controller40/新独立受入72、native2/記録native0/実測失敗0。記録初回はimport再帰上限によるloader1失敗/71実試験未実行、入口1500と新1検査で72case初実行。全国図鑑/自然成長進化/全story/release未受入。ROM/runtime非再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save96_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=0,museum_admission_var4061=1,museum_second_floor_accepted=True,museum_return_first_floor_accepted=True,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,required_badge_flag=2083,required_badge_present=True,paper_consumed_or_delivered=True,letter_handoff_accepted=True,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),record_loader_failed_attempts=1,acceptance_successful_cases=72,acceptance_failed_loader_cases=1,acceptance_case_replays=0,controller_cases=40,controller_executions=40,controller_passed_executions=40,controller_failed_executions=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=72,successful_native_processes=2,prior_failed_native_processes=0,prior_pre_native_failed_attempts=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 博物館初下降・Save96限定受入

`{result['status']}`。封書引渡し後のSave95から、新復路13歩/5旋回で2階11,8へ。西入力で1階6/0・8,8西へ初下降し、最初のfieldで通常Save96、独立Continueを受入。受付/封書会話の再走なし。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。62member/47画面/83+cold13入力。controller40、新独立受入72、成功native2/失敗0/記録native0/ROM変更0/旧受入再走0。

## 記録側のimport修復

初回記録run37192785450/job111408313462はfresh unittest importでRecursionError。71実試験は未実行、loader失敗1、native追加0、正本書込み/commitなし。失敗receipt artifact11300145384を全byte保持し終端もfailureのまま。今回の新受入入口だけで過去module読取用の有限再帰上限1500を設定、上限1検査を追加し72caseを初実行する。旧source/controller/nativeを再走しない。

## 保存境界と全画面

0〜18は13歩/旋回5、19で初下降、20〜24menu0→4、25/26確認、27〜40保存中。39は最終flash hashに一時一致してもcounter95/保存中。40ではcounter96と別hash、41で成功文言と安定finalhash、44でoverlayなしclearfield。hash単独/counter単独の完了判定にしない。

44→cold0/1は202/60pixel、cold間142pixel差。全差分は上端NPC1人の矩形x18..29/y0..22内だけ。主人公/地形保持だが全画面一致とは主張しない。SaveRTC全131088byte、PC/S61E/旧Save95bank57344byte保持。差分7019byte1748範囲、42checksum。

全party600byte/HP277/294/PP3,9,8,2/23114円/紙274=0/4382/4383/4061=1/バッジ2保持。4380未完。今回全RAM台帳保持だがphysical2056:0→1、aux4021:96→109/4022:3→1のruntime owner未解明。過去Save95/94等のownerも未解明のまま。全国図鑑/自然成長進化/全story/releaseは未受入。

## 次

[新復路12歩と博物館退出](../content/modernization/pr16_story_save96_next_route.json)。1階8,8西から13,9の出口へ。13,5受付coordは4061==0だけなので支払済み値1を維持。最初の町fieldで保存。19,25/19,26は静的候補で自動歩行未確認。505道路レンジャーは退出後。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save95']['record_completion']=prior_done
    state['story_save96']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[6,0],xy=[8,8],facing=3,rp=0,money=23114,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=0,museum_admission_var4061=1,museum_second_floor_accepted=True,museum_return_first_floor_accepted=True,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_quantity=0,paper_flag4383=True,paper_flag4382=True,paper_consumed_or_delivered=True,letter_handoff_accepted=True,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='封書引渡し後の新13歩、西入力初下降とSave96/独立Continue。旧受入再走0。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='初下降Save96/6/0・8,8西。新13歩/5旋回/西階段/47画面。39一時finalhash→40別hash/counter96→41成功→44clearfield。全party/23114円/紙引渡し/4382/4383/4061/全RAM台帳保持。physical2056set/aux2vars/過去owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MUSEUM_EXIT_FROM_SAVE96',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save96_accept.py','scripts/pr16_story_save96_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,'content/modernization/pr16_story_save96_next_route.json'],stop_rule_ja='Save96/1階8,8西から新復路12歩で13,9出口へ。最初の町fieldを保存。封書会話/受付/階段/旧入館再走なし。4061=1/23114円保持、未知NPC/障害/eventで縮小停止。505道路レンジャーは退出後。')
    state['do_not_repeat'].append('Save96の83/cold13入力47画面62member、新復路13歩/5旋回/西初下降、controller40/独立受入72を無影響再走しない。39一時finalhash保存中/counter95→40別hash/counter96→41成功最終hash→44clearfield。coldNPC1人142pixel差/全SaveRTC保持。今回RAM保持でもphysical2056set/aux2varsと過去owner未解明。次は新復路12歩で博物館退出。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='博物館初下降Save96/6/0・8,8西。紙274=0/4382/4383/23114円/4061/全party/HP277/PP3,9,8,2保持。今回RAM保持、physical2056set/aux2varsと過去owner未解明。次は新復路12歩で退出。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    entry=f"""
## {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Version: PR16-STORY-SAVE96
- Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Task: {TASK} / 博物館初下降とSave96
- Status: DONE（新13歩/西方向下降/保存/独立Continue限定、博物館退出/505レンジャー未到達）
- Summary: 2階4,8南から新復路13歩/5旋回、11,8西入力で1階8,8西へ初下降。全party600byte/HP277/PP3,9,8,2/バッジ2/23114円/4061/4382/4383/PC/S61E保持。
- Files changed: Save96 preparation/measure/controller40/受入72/record/checkpoint/text証拠/次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。83+cold13入力47画面62member。controller40、新受入72。成功native2/失敗0/記録native0/compile0/旧成功再走0。
- Evidence: 27〜40保存中/39一時finalhashでもcounter95、40別hash/counter96、41成功文言/安定finalhash、44clearfield。coldNPC1人142pixel差/全SaveRTC保持。42checksum/7019byte1748範囲/旧bank保持。
- Discovery: 初回記録のfresh unittest importが既定再帰1000へ到達、loader1失敗/71実試験未実行/native0。新受入入口だけ1500を設定、上限1試験を追加し72case初実行。失敗原本artifact11300145384/終端failure保持。今回全RAM台帳保持だがphysical2056:0→1/aux4021:96→109/4022:3→1のruntime owner未解明。過去owner未解明。Save95記録run37191567861全11step終端同期。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repoGitHub/Actions。継承source-lockの0x6F西方向predicateを保持。入力ROM/runtime非再配布、ROM変更/merge/release/baseline変更0。一般CI既知不一致は全成功にしない。
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
