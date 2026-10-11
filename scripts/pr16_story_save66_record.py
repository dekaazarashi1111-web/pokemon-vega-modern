#!/usr/bin/env python3
"""NPC北迂回新13歩・野生オタクン1勝Save66原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save66_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MANSION-NORTH-DETOUR-SAVE66'
OUT=ROOT/'.local/pr16-story-save66-record'

CODE={'scripts/pr16_story_save66_accept.py','scripts/pr16_story_save66_record.py','tests/test_pr16_story_save66_accept.py',a.VISUAL,'.github/workflows/pr16-story-save66-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE66_JA.md' and a.CP=='content/modernization/pr16_story_save66_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save66_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37162209164,'cab051cd8556e87b2a360207d36c92d47de2bf25',111317801126,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save66_measure.',27)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==70 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save65全70member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save65/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==70 and len(z.namelist())==71 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save66member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==55 and visual['reviewed_screens']==dict(progress=list(range(53)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save66画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save66画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE66_ORIGINAL=str(original),PR16_SAVE65_INPUT=str(assets/'input.srm'),PR16_SAVE66_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save66_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==55 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 55 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'55成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save65-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save66 artifact11288387069のstory-fast.srm（131088bytes/SHA256 5c415ce0cac66346d10309f6ec7b783fade9cdfb5902a5bf2c19845c930d50a5）だけから再開。NPC25,6を北迂回する新13歩/転換5、上階map1/60・25,12南でオタクン♂Lv10に野生1勝。ドラゴンクロー1選択/実PP15→14、通常Save66/独立Continue。HP288/294・PP14,10,15,2でつばめがえし2は温存、party残り599byte/Bag/19104円/RP0/badge1/story4071=9/4072=1/全flags/PC保持。次は保存済経路の未通過15歩:25,12→25,16→31,16→穴31,21。最初の新event/戦闘/不通境界で通常保存。穴→入口31,22/南東階段30,29→上階33,29→紙側16,27は未実測。選択コマンドと実PPを分け、通常技のみ/host補充なし。27新controller/55新受入、97+cold13入力55画面70member/native2/旧受入再走0。46Flash最終hash一致でも保存中、47counter66で再変化、48成功→52field。全SaveRTC/field画面同一。aux4021:111→124のruntime owner未解明、RAM台帳不変。旧offset41/2056/aux/40acの未解明は保持。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、回復再走/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save66_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,normal_recovery_repeated=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=27,controller_executions=27,unchanged_controller_cases_replayed=0,new_acceptance_tests=55,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# NPC北迂回の新13歩・野生オタクン1勝・Save66限定受入

`{result['status']}`。Save65からNPC25,6を北迂回、新13歩/転換5。上階25,12南でオタクン♂Lv10に新1勝、通常保存・独立Continue。穴・紙は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。70member/55画面/97+cold13入力。新controller27case/新受入55case。native2/record0/旧受入再走0/ROM変更0。

## 新歩行・野生戦

0〜18でNPC北迂回から新13歩/方向転換5。19暗転、20導入、21オタクン♂Lv10を拡大画面で確認。24ドラゴンクロー選択、25使用、26撃破、27通常field。選択1と実PP15→14を別確認、つばめがえし2は温存。保守的3PP/コマンド予約を実消費数として扱わない。

## 保存完了判定

28〜32menu0→4、33確認/34上書き、35〜47保存中。46のFlash hashが最終値でも保存画面は途中、47counter66でhash再変化、48〜51成功文言、52field。hash一致やcounterだけで完了にしない。progress27/52/cold0/cold1全画面byte一致、全SaveRTC一致。

## 保存境界

party600byteのoffset52だけ15→14、残り599byte/HP288/294/ミュウツー全HP/PP/EXP/持物/Bag/19104円/RP0/全flags/PC/S61E payload/旧Save65bank57344byte保持。aux4021:111→124だけ、runtime owner未解明。RAM台帳不変、42checksum/6860byte1673範囲。Flash未使用/がくしゅうそうち未装備。

[次の静的15歩](../{a.EVIDENCE}/next-route.json)は25,12→25,16→31,16→穴31,21。穴・下階着地点・南東階段・紙側接続は未受入。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。一般CI不一致/action_requiredを全成功にしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save65']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37162209156');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='cab051cd8556e87b2a360207d36c92d47de2bf25','旧Stage79終端')
    state['story_save65']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save66']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,60],xy=[25,12],facing=1,rp=0,money=19104,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[14,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,inert_warp8_activation=False,trainer_victories=0,wild_victories=1,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='NPC北迂回新13歩/オタクン野生1勝/Save66。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='NPCを北迂回する新13歩/転換5とオタクン野生1勝。DragonClaw PP15→14、上階25,12南でSave66。穴/紙未到達。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_UPPER_SUFFIX_FROM_SAVE66',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save66_accept.py','scripts/pr16_story_save66_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save62_evidence/route-plan.json','content/modernization/pr16_story_save57_preparation.json'],stop_rule_ja='Save66上階25,12南から未通過15歩候補で穴31,21へ。最初の新event/戦闘/不通境界で保存。実PP14,10,15,2を守りhost補充なし。北迂回/野生戦/保存は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='NPC北迂回を新13歩/転換5、オタクン♂Lv10野生1勝でSave66。上階25,12南、PP14,10,15,2。次は穴への未通過15歩。'
    state['do_not_repeat'].append('Save66の97/cold13入力55画面70member/27controller/55受入を無影響再走しない。NPC北迂回新13歩/転換5/オタクン1勝/DragonClaw実PP1、つばめがえし残2。46最終hash一致でも保存中→47counter66で再変化→48成功→52field。全SaveRTC/field画像一致。残り15歩/穴/紙未受入。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / NPC北迂回新13歩・オタクン1勝Save66
- Version: story-mansion-north-detour-save66-v1
- Status: DONE（新13歩/野生1勝/通常保存/独立Continue限定）
- Summary: 上階25,12南、NPC北迂回新13歩/転換5。オタクン♂Lv10、DragonClaw実PP15→14、つばめがえし2温存。party残599byte/HP288/294/Bag19104円/RP0/全flags/PC保持。
- Files changed: Save66 measure/27controller/55受入/record/checkpoint/text証拠/次15歩、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。97+cold13入力55画面70member。新controller27原log継承/新受入55。record native0/compile0/旧受入再走0。
- Evidence: 46最終hash一致でも保存中、47counter66で再変化、48成功→52field。全SaveRTC/field全pixel一致。aux4021:111→124 owner未解明、RAM台帳保持。42checksum/6860byte1673範囲。穴/紙未到達。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repo GitHub/Actionsだけ、ROM/runtime/input非再配布。一般CI既知不一致/action_requiredを全成功にしない。merge/release/baseline変更0。
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



