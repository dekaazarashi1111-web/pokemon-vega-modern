#!/usr/bin/env python3
"""上階の新14歩・野生バーニン1勝Save64原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save64_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MANSION-UPPER-WILD-SAVE64'
OUT=ROOT/'.local/pr16-story-save64-record'

CODE={'scripts/pr16_story_save64_accept.py','scripts/pr16_story_save64_record.py','tests/test_pr16_story_save64_accept.py',a.VISUAL,'.github/workflows/pr16-story-save64-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE64_JA.md' and a.CP=='content/modernization/pr16_story_save64_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save64_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37161192971,'f6f411e7bb102591b1afe2d014385a20efb05197',111314792272,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save64_measure.',27)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==56 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save63全56member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save63/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==69 and len(z.namelist())==70 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save64member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==54 and visual['reviewed_screens']==dict(progress=list(range(52)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save64画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save64画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE64_ORIGINAL=str(original),PR16_SAVE63_INPUT=str(assets/'input.srm'),PR16_SAVE64_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save64_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==53 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 53 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'53成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save63-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-neighbor.json',a.next_neighbor())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save64 artifact11286858775のstory-fast.srm（131088bytes/SHA256 7cab241382223fc8ddbd2d659f8c29619c5b9b0ff5fd6d24e9269b4f366833d0）だけから再開。上階map1/60・26,6西。上階新14歩/転換2、バーニン♂Lv11に野生1勝、つばめがえし1選択/実PP6→5、通常Save64・独立Continue済み。HP288/294・PP15,10,15,5、party残り599byte/Bag/18744円/RP0/badge1/story4071=9/4072=1/PC保持。西隣25,6には実画面NPC。保存済map1/60 local7・script154587024はtrainerbattle155だがruntime identityは未捕捉。次は西向きのままAを1回だけ押し、新会話/新戦闘/不応答を区別して最初の境界で保存。通行を無理に3回反復しない。応答受入後は未通過26歩の静的接尾辞26,6→25,6→24,6→23,6→23,11→25,11→25,16→31,16→穴31,21が候補。穴/南東階段/紙未到達。27新controller/53新受入、95+cold13入力54画面69member/native2。46counter64部分write、47成功→51field。全SaveRTC/field画面同一。勝利残留wire fieldfalse/flags4/outcome1を未復帰や追加勝利にしない。全RAM台帳/flags保持、aux4021:97→111/4022:3→0のruntime owner未解明。旧offset41/2056/aux404d/40ac未解明保持。Flash未使用/がくしゅうそうち未装備。旧経路/野生戦/保存は無影響再走しない。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save64_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,inert_warp8_activation=False,normal_recovery_repeated=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=27,controller_executions=27,unchanged_controller_cases_replayed=0,new_acceptance_tests=53,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 上階の野生バーニン1勝・Save64限定受入

`{result['status']}`。Save63から上階を新14歩・北/西への転換2、26,6西でバーニン♂Lv11と遭遇。つばめがえし1回で新1勝、通常保存・独立Continue。trainer戦0、穴と像の紙は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。69member/54画面/95+cold13入力。新controller27case、53新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## 新野生戦と保存

0開始、1〜16で新14歩/転換2。16transition、17全暗転、18導入、19野生バーニン♂Lv11。22〜24実技cursor0→2→3、24つばめがえし、25撃破/実PP6→5、26field。勝利後はwire field=false/flags4/outcome1が残るがcallback field/lock0、通常menu・保存と独立Continueを確認。追加勝利にはしない。

27〜31menu0→4、32確認/33上書き、34〜46保存中。46counter64でも部分write、47〜50成功文言、51field。progress26/51/cold0/cold1全画面byte一致、全SaveRTC一致。

## 保存差分・次の隣接NPC

party600byte中PP55の6→5だけ、残り599byte/HP288/294・ミュウツー全HP/PP・EXP/持物・全Bag/18744円/RP0・全legacy flags・PC/S61E全payload・旧Save63bank57344byte保持。aux4021:97→111/4022:3→0のruntime ownerは未解明。全RAM台帳不変。42checksum/6899byte1681範囲。

[隣接NPC候補](../{a.EVIDENCE}/next-neighbor.json): 実画面の西隣25,6にNPC。保存済map1/60 local7/script154587024のtrainerbattle155命令を照合した。runtime object IDは未捕捉。次は西向きからA1回だけで会話/戦闘を観測し、最初の新境界で保存する。残りの上階静的候補は26歩。穴31,21→入口31,22→南東階段→紙側の接続は未実測。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。一般CI既知不一致/action_requiredを成功にしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save63']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37161192800');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='f6f411e7bb102591b1afe2d014385a20efb05197','旧Stage79終端')
    state['story_save63']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save64']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,60],xy=[26,6],facing=3,rp=0,money=18744,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[15,10,15,5],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,inert_warp8_activation=False,trainer_victories=0,wild_victories=1,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_neighbor=a.EVIDENCE+'/next-neighbor.json',static_route_plan='content/modernization/pr16_story_save62_evidence/route-plan.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='上階新14歩/野生バーニン1勝/Save64。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='上階新14歩/バーニン♂Lv11新1勝/Save64。26,6西、PP6→5。穴/紙未到達、隣接NPCは次の新境界。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_ADJACENT_NPC_FROM_SAVE64',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save64_accept.py','scripts/pr16_story_save64_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-neighbor.json','content/modernization/pr16_story_save62_evidence/route-plan.json','content/modernization/pr16_story_save57_preparation.json'],stop_rule_ja='Save64上階26,6西から隣接NPCへA1回。最初の新会話/戦闘/不応答で保存。次の未通過接尾辞は26歩。旧上階14歩/野生戦/保存は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='上階新14歩と野生バーニン1勝でSave64。26,6西、PP6→5。西隣NPCへ通常A1回が次の境界。穴/紙未到達。'
    state['do_not_repeat'].append('Save64の95/cold13入力54画面69member/27controller/53受入を無影響再走しない。上階新14歩/転換2/野生バーニン1勝/実PP1。46counter64部分write→47成功→51field、全SaveRTC/field画面一致。勝利残留fieldfalse/flags4/outcome1を未復帰や追加勝利にしない。隣接trainer155はstatic候補、穴/紙未到達。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 上階新14歩と野生バーニン1勝Save64
- Version: story-mansion-upper-wild-save64-v1
- Status: DONE（上階新14歩/野生1勝/保存/独立Continue限定）
- Summary: 上階32,10から14歩/転換2で26,6西。野生バーニン♂Lv11をつばめがえし1回/実PP6→5で撃破。party残り599byte/HP288/294/Bag/18744円/RP0保持。trainer戦0・穴/紙未到達。
- Files changed: Save64 measure/27controller/53受入/record、checkpoint/text証拠/隣接NPC候補、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。95+cold13入力54画面69member。新27controller原log継承/53新受入拒否試験。record native0/compile0/既受入再走0。
- Evidence: 46counter64部分write→47成功→51field。全SaveRTC/field画面一致。RAM台帳/全flags保持。aux4021:97→111・4022:3→0 owner未解明。旧bank57344byte/42checksum/6899byte1681範囲。残留fieldfalse/flags4/outcome1の意味を保持。西隣25,6のstatic trainer155候補へ次はA1回。
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



