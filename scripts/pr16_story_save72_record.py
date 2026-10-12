#!/usr/bin/env python3
"""上階残り11歩・像北隣初到着Save72原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save72_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-MANSION-PAPER-SIDE-SAVE72'
OUT=ROOT/'.local/pr16-story-save72-record'

CODE={'scripts/pr16_story_save72_accept.py','scripts/pr16_story_save72_record.py','tests/test_pr16_story_save72_accept.py',a.VISUAL,'.github/workflows/pr16-story-save72-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE72_JA.md' and a.CP=='content/modernization/pr16_story_save72_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save72_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37166790901,'74abc6a55dc2bae04c8ed2955b51b254374f3ce1',111331240970,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save72_measure.',29)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==68 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save71全68member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save71/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==58 and len(z.namelist())==59 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save72member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==43 and visual['reviewed_screens']==dict(progress=list(range(41)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save72画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save72画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE72_ORIGINAL=str(original),PR16_SAVE71_INPUT=str(assets/'input.srm'),PR16_SAVE72_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save72_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==55 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 55 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'55成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save71-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save72 artifact11289800679のstory-fast.srm（131088bytes/SHA256 851c87f8a8006eaecdcb6ea28ee9f097fbcab4ba0c7f5b626afb6edbec40fa49）だけから再開。上階23,31西から残り新11歩/転換2で像北隣16,27西へ初到着、通常Save72/独立Continueを限定受入。新戦闘0、全party600byte・HP288/294・PP9,10,15,2/Bag19416円/PC/S61E保持、RP0/badge1/story4071=9/4072=1。legacy flag差分0、aux4021:43→54/4022:0→1とRAM台帳10変化のowner未解明。次は同map1/60・16,27西から通常南入力で向き1を確認して像16,28をAで調べる最初の新eventだけ。保存済background script149012422、compare800C=1/checkflag4383/checkspace274/additem274/setflag4383を静的照合、紙（item274だいじなふうしょ）の取得は未実測。通常dialog完了/取得/最初の新event境界で保存し、実Bag/expanded flag/画面/独立Continueで確認。29新controller/55新受入、73+cold13入力43画面58member/native2、旧成功再走0。35counter72も部分write→36成功→40field。全SaveRTC/像側field4画面全pixel一致。旧offset41/2056/aux/40acのruntime owner未解明を保持。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save72_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,paper_side_reached=True,statue_visual_observed=True,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,southeast_stair_previously_accepted=True,normal_recovery_repeated=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=29,controller_executions=29,unchanged_controller_cases_replayed=0,new_acceptance_tests=55,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 像北隣への初到着Save72限定受入

`{result['status']}`。Save71の上階23,31西から、残りの新11歩/転換2で像北隣16,27西へ初到着し通常保存・独立Continue。像は画面に見えるが紙を調べる操作は未実行。新戦闘0。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。58member/43画面/73+cold13入力。新controller29/新受入55。native2/record0/旧成功再走0/ROM変更0。

## 像北隣・通常保存

0〜13新11歩/転換2で像北隣16,27西へ。14〜18menu0→4、19確認/20上書き、21〜35保存中。35counter72でも部分write、36〜39成功文言、40field。progress13/40/cold0/cold1全画面byte一致、全SaveRTC一致。

全party600byte/HP288/294・PP9,10,15,2/Bag19416円/PC/S61E/旧Save71bank57344byte保持。legacy flag差分0、aux4021:43→54/4022:0→1とRAM台帳10変化のowner未解明。42checksum/6843byte1666範囲。

## 次の像イベント

[次の静的操作候補](../{a.EVIDENCE}/next-route.json)。16,27西から通常南入力で向き1を確認し、南隣16,28の像をAで調べる。保存済background script149012422、compare800C=1/checkflag4383/checkspace274/additem274/setflag4383を照合。紙/item274「だいじなふうしょ」の取得、台詞、Bag/flag保存は未実測で、今回の到着受入へ含めない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save71']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37166790727');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='74abc6a55dc2bae04c8ed2955b51b254374f3ce1','旧Stage79終端')
    state['story_save71']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save72']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,60],xy=[16,27],facing=3,rp=0,money=19416,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,paper_side_reached=True,statue_visual_observed=True,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,southeast_stair_previously_accepted=True,inert_warp8_activation=False,trainer_victories=0,wild_victories=0,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='新11歩/像北隣初到着/Save72。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='上階残り11歩で像北隣16,27西へ初到着しSave72。新戦闘0/全party・HP・PP保持。次は南を向き像の紙を調べる最初のevent。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_STATUE_PAPER_INTERACTION_FROM_SAVE72',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save72_accept.py','scripts/pr16_story_save72_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save62_evidence/route-plan.json','content/modernization/pr16_story_save57_preparation.json'],stop_rule_ja='Save72上階16,27西から通常南入力で向き1を確認し、南隣16,28の像をAで調べる新eventだけ。dialog/取得/最初の新event境界で通常保存。紙/item274/flag4383は未取得として実画面と保存値で確認。PP9,10,15,2、host補充なし。旧11歩/野生戦/階段/保存は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='上階残り11歩で像北隣16,27西へ初到着しSave72。新戦闘0/HP288/294・PP9,10,15,2/19416円保持。次は南を向き像の紙を調べる新event。'
    state['do_not_repeat'].append('Save72の73/cold13入力43画面58member/29controller/55受入を無影響再走しない。残り新11歩/転換2で像北隣16,27西に初到着、新戦闘0/全party600byte・HP288/PP9,10,15,2/Bag19416円保持。legacy flag不変/aux2変数/RAM10変化owner未解明。35counter72も部分write→36成功→40field。全SaveRTC/像側field4画像一致。像は見えるが紙を調べる操作/取得未完。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 上階残り11歩・像北隣初到着Save72
- Version: story-mansion-paper-side-save72-v1
- Status: DONE（新11歩/像北隣初到着/通常保存/独立Continue限定）
- Summary: 上階23,31西から残り新11歩/転換2、像北隣16,27西へ初到着。新戦闘0/全party600byte・HP288/294・PP9,10,15,2/Bag19416円/PC/S61E保持。legacy flag0差分/aux2変数とRAM10変化owner未解明。
- Files changed: Save72 measure/29controller/55受入/record/checkpoint/text証拠/像event静的操作候補、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。73+cold13入力43画面58member。新controller29原log継承/新受入55。record native0/compile0/旧成功再走0。
- Evidence: 35counter72も部分write→36成功→40field。全SaveRTC/像側field4画面全pixel一致。42checksum/6843byte1666範囲。紙の取得は未完。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repo GitHub/Actionsだけ。既存ROM/runtime/input非再配布。一般CI既知不一致/action_requiredを全成功にしない。merge/release/baseline変更0。
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




