#!/usr/bin/env python3
"""NPC北迂回新13歩・野生オタクン1勝Save67原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save67_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MANSION-HOLE-APPROACH-SAVE67'
OUT=ROOT/'.local/pr16-story-save67-record'

CODE={'scripts/pr16_story_save67_accept.py','scripts/pr16_story_save67_record.py','tests/test_pr16_story_save67_accept.py',a.VISUAL,'.github/workflows/pr16-story-save67-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE67_JA.md' and a.CP=='content/modernization/pr16_story_save67_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save67_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37163116203,'48fd554eb7f6b4adae8b2d56b751df38439cfa1b',111320488487,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save67_measure.',27)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==70 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save66全70member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save66/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==68 and len(z.namelist())==69 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save67member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==53 and visual['reviewed_screens']==dict(progress=list(range(51)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save67画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save67画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE67_ORIGINAL=str(original),PR16_SAVE66_INPUT=str(assets/'input.srm'),PR16_SAVE67_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save67_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==56 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 56 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'56成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save66-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save67 artifact11288432849のstory-fast.srm（131088bytes/SHA256 a4543c8c8d1b47668159adc71a0aff60f2bcf58ac91139d50d6eb201bd9677f5）だけから再開。上階接尾辞新14歩/転換2、map1/60・31,20南でオタクン♂Lv9に新野生1勝。ドラゴンクロー1選択/実PP14→13、通常Save67/独立Continue、HP288/294・PP13,10,15,2。次は南へ穴31,21まで未通過1歩、落下が起きれば入口階map1/59・31,22で保存。初の新event/戦闘/不通境界で通常保存し、穴下階接続を判定。穴→南東階段30,29→上階33,29→紙側16,27は未実測。歩行中観測4で4体のoffset41/141/241/341が+1、PP1と合わせ5byte変化、残595byte保持。offset41と観測3のRAM台帳変化のruntime owner未解明。Bag/19104円/RP0/badge1/story4071=9/4072=1/全flags/PC保持、aux4021:124→10だけowner未解明。27新controller/56新受入、93+cold13入力53画面68member/native2。45counter67部分write→46成功→50field、全SaveRTC/field全pixel同一。Flash未使用/がくしゅうそうち未装備、つばめがえし2温存。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。旧成功無影響再走/host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save67_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,normal_recovery_repeated=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=27,controller_executions=27,unchanged_controller_cases_replayed=0,new_acceptance_tests=56,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 上階の穴手前まで新14歩・野生オタクン1勝・Save67限定受入

`{result['status']}`。Save66から上階の未通過14歩/転換2。31,20南の穴手前でオタクン♂Lv9に新1勝、通常保存・独立Continue。穴へあと1歩、落下と紙は未受入。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。68member/53画面/93+cold13入力。新controller27/新受入56。native2/record0/旧成功再走0/ROM変更0。

## 新経路・戦闘・保存

0〜16で上階25,12→25,16→31,16→31,20、14歩/転換2。17暗転、18導入、19オタクン♂Lv9、22ドラゴンクロー選択、23使用、24撃破、25field。PP14→13、つばめがえし2温存。

26〜30menu0→4、31確認/32上書き、33〜45保存中。45counter67でも部分write、46〜49成功文言、50field。progress25/50/cold0/cold1全画面byte一致、全SaveRTC一致。

## 変化したbyteと保持境界

party offset41/141/241/341は観測4から各+1、runtime owner未解明。保存byteから中間party hashを独立再構成し、23でPP52:14→13だけを追加。合計5byte差分、残595byte/HP288/294/ミュウツーHP・PP/EXP/持物保持。RAM台帳は観測3で変化、owner未解明。Bag/19104円/RP0/全flags/PC/S61E/旧Save66bank57344byte保持、aux4021:124→10だけ。42checksum/6866byte1681範囲。

[次の未通過1歩](../{a.EVIDENCE}/next-route.json)は31,20→穴31,21。落下先候補は入口階31,22、その先の南東階段/紙側は未実測。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未受入。一般CI既知不一致/action_requiredを成功にしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save66']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37163116147');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='48fd554eb7f6b4adae8b2d56b751df38439cfa1b','旧Stage79終端')
    state['story_save66']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save67']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,60],xy=[31,20],facing=1,rp=0,money=19104,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[13,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,inert_warp8_activation=False,trainer_victories=0,wild_victories=1,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='上階新14歩/穴手前オタクン野生1勝/Save67。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='上階新14歩/転換2とオタクン野生1勝。DragonClaw PP14→13、上階31,20南でSave67。穴まで残1歩、落下/紙未受入。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_HOLE_FINAL_EDGE_FROM_SAVE67',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save67_accept.py','scripts/pr16_story_save67_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save62_evidence/route-plan.json','content/modernization/pr16_story_save57_preparation.json'],stop_rule_ja='Save67上階31,20南から穴31,21へ未通過1歩。落下先31,22で保存、初の新event/戦闘/不通境界で停止。実PP13,10,15,2。旧経路/野生戦/保存は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='上階の新14歩/転換2、オタクン♂Lv9野生1勝でSave67。31,20南、穴まであと1歩。PP13,10,15,2。'
    state['do_not_repeat'].append('Save67の93/cold13入力53画面68member/27controller/56受入を無影響再走しない。上階新14歩/転換2/オタクン1勝/DragonClaw実PP1。party4体offset41+1とRAM観測3変化owner未解明。45counter67部分write→46成功→50field。全SaveRTC/field画像一致。穴まで1歩、落下/紙未受入。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 上階の穴手前へ新14歩・オタクン1勝Save67
- Version: story-mansion-hole-approach-save67-v1
- Status: DONE（新14歩/野生1勝/通常保存/独立Continue限定）
- Summary: 上階31,20南、穴まで残1歩。オタクン♂Lv9、DragonClaw実PP14→13、つばめがえし2保持。観測4から4体offset41+1/RAM観測3変化のowner未解明、party残595byte/HP288/294/Bag19104円/RP0/全flags/PC保持。
- Files changed: Save67 measure/27controller/56受入/record/checkpoint/text証拠/次1歩、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。93+cold13入力53画面68member。新controller27原log継承/新受入56。record native0/compile0/旧受入再走0。
- Evidence: 45counter67部分write→46成功→50field。全SaveRTC/field全pixel一致、aux4021:124→10 owner未解明。42checksum/6866byte1681範囲。穴落下/紙未到達。
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



