#!/usr/bin/env python3
"""入口階新11歩・trainer165新1勝Save69原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save69_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-MANSION-LOWER-TRAINER165-SAVE69'
OUT=ROOT/'.local/pr16-story-save69-record'

CODE={'scripts/pr16_story_save69_accept.py','scripts/pr16_story_save69_record.py','tests/test_pr16_story_save69_accept.py',a.VISUAL,'.github/workflows/pr16-story-save69-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE69_JA.md' and a.CP=='content/modernization/pr16_story_save69_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save69_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37164209682,'cfb8205205bf0c4ca2f829ea62d35434d70b1523',111323694182,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save69_measure.',27)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==44 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save68全44member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save68/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==84 and len(z.namelist())==85 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save69member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==69 and visual['reviewed_screens']==dict(progress=list(range(67)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save69画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save69画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE69_ORIGINAL=str(original),PR16_SAVE68_INPUT=str(assets/'input.srm'),PR16_SAVE69_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save69_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==62 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 62 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'62成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save68-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save69 artifact11289196478のstory-fast.srm（131088bytes/SHA256 9f17464ffd3b805b2d7b493298abbc1830b905b1cf0cef009feb5aa19e3c64a2）だけから再開。入口階31,22→26,28の新11歩でりかけいのおとこリオン/trainer165に通常1勝、ココガラLv10・ビッパLv12・ファマーLv13をDragonClaw3回、交代取消2/賞金312円。通常Save69/独立Continueを限定受入。HP288/294、PP10,10,15,2、money19416、RP0/badge1/story4071=9/4072=1。party600byte中slot0PP1byteだけ、physical1445:0→1、aux4021:10→20、全Bag/PC/S61E保持。RAM台帳は5/31で変化、owner未解明。戦後/Save後/cold全field画面同一、南隣NPC26,29が見えるため直進を避ける。次は新9歩候補26,28→25,28→25,30→27,30→27,29→南東階段30,29、上階33,29または自動東1歩34,29へ初到着したら通常保存。初の新event/戦闘/不通境界で停止。南東階段/紙側16,27は未実測。27新controller/62新受入、127+cold13入力69画面84member/native2、旧成功再走0。61counter69でも部分write/保存中、62成功→66field、全SaveRTC一致。旧offset41/2056/aux/40acのruntime owner未解明を保持。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save69_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,normal_recovery_repeated=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=27,controller_executions=27,unchanged_controller_cases_replayed=0,new_acceptance_tests=62,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 入口階新11歩・リオン戦Save69限定受入

`{result['status']}`。Save68の入口階31,22南から新11歩/方向転換2で26,28へ到達。接近してきたりかけいのおとこリオン/trainer165に通常1勝し、通常保存・独立Continue。南東階段は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。84member/69画面/127+cold13入力。新controller27/新受入62。native2/record0/旧成功再走0/ROM変更0。

## 新規trainer戦・通常保存

0〜13新11歩と転換2、13NPC発見/14接近会話。15〜40新trainer1戦、ココガラLv10♀・ビッパLv12♀・ファマーLv13♂。DragonClaw3回、交代取消2、38勝利/40賞金312円/41field。敵3体や勝利残留を追加勝利にしない。

42〜46menu0→4、47確認/48上書き、49〜61保存中。61counter69でも部分writeで未完、62〜65成功文言、66field。progress41/66/cold0/cold1全画面byte一致、全SaveRTC一致。

## 保存境界・南隣NPC迂回

party600byte中slot0PP13→10の1byteだけ。HP288/294、PP10,10,15,2、全Bag/PC/S61E/旧Save68bank57344byte保持。money19104→19416、physical1445:0→1、aux4021:10→20だけ。static local10/script trainer165/remapと勝利bitを照合。runtime object ID、RAM台帳5/31変化やauxのownerは未解明。42checksum/6913byte1702範囲。

[次の未通過9歩](../{a.EVIDENCE}/next-route.json)は南隣NPC26,29を避けて26,28→25,28→25,30→27,30→27,29→階段30,29。南隣NPCの像は独立Continueでも一致。static local10元位置26,31とruntime IDの同定は混同しない。上階33,29と紙16,27は未実測。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save68']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37164209720');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='cfb8205205bf0c4ca2f829ea62d35434d70b1523','旧Stage79終端')
    state['story_save68']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save69']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,59],xy=[26,28],facing=1,rp=0,money=19416,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[10,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,inert_warp8_activation=False,trainer_victories=1,wild_victories=0,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='入口階新11歩/リオン1勝/Save69。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='入口階新11歩で26,28へ。リオン/trainer165に1勝、DragonClaw3回/賞金312円/Save69。南隣NPCを迂回して南東階段へ。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_LOWER_NPC_DETOUR_FROM_SAVE69',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save69_accept.py','scripts/pr16_story_save69_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save62_evidence/route-plan.json','content/modernization/pr16_story_save57_preparation.json'],stop_rule_ja='Save69入口階26,28南から南隣NPC26,29を避けて未通過9歩で南東階段30,29へ。初の新event/戦闘/不通境界、または上階33,29/自動東1tile34,29へ初到着したら通常保存。PP10,10,15,2、host補充なし。旧11歩/リオン戦/保存は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='入口階新11歩で26,28へ、リオン/trainer165に1勝しSave69。HP288/294・PP10,10,15,2/19416円。次は南隣NPCを避ける未通過9歩で南東階段へ。'
    state['do_not_repeat'].append('Save69の127/cold13入力69画面84member/27controller/62受入を無影響再走しない。入口階新11歩/転換2/リオンtrainer165に1勝、DragonClaw3回/交代取消2/賞金312円。slot0PPだけ13→10、physical1445/aux4021差。RAM5/31owner未解明。61counter69も部分write→62成功→66field。全SaveRTC/全field画像一致。南隣NPC迂回/南東階段/紙未受入。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 入口階新11歩・リオンtrainer165新1勝Save69
- Version: story-mansion-lower-trainer165-save69-v1
- Status: DONE（新trainer1勝/通常保存/独立Continue限定）
- Summary: 入口階31,22→26,28の新11歩/転換2。リオン/trainer165に1勝、DragonClaw3回/交代取消2/賞金312円。HP288/294、PP10,10,15,2、19416円。全party600byte中PP1byteのみ、physical1445/aux4021差。RAM5/31owner未解明。
- Files changed: Save69 measure/27controller/62受入/record/checkpoint/text証拠/NPC迂回9歩候補、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。127+cold13入力69画面84member。新controller27原log継承/新受入62。record native0/compile0/旧成功再走0。
- Evidence: 61counter69も部分write/保存中→62成功→66field。戦後/Save後/cold全field全pixel一致、全SaveRTC一致。42checksum/6913byte1702範囲。南隣NPCが残るため直進を避ける。南東階段/紙未到達。
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




