#!/usr/bin/env python3
"""館内の北迂回13歩・プレッシャー野生1勝Save61原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save61_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MANSION-NORTH-DETOUR-SAVE61'
OUT=ROOT/'.local/pr16-story-save61-record'

CODE={'scripts/pr16_story_save61_accept.py','scripts/pr16_story_save61_record.py','tests/test_pr16_story_save61_accept.py',a.VISUAL,'.github/workflows/pr16-story-save61-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE61_JA.md' and a.CP=='content/modernization/pr16_story_save61_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save61_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37158672170,'7e495ef303475b948b6cf0f913e0ead8176d9fa9',111307297182,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save61_measure.',27)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==59 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save60全59member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save60/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==72 and len(z.namelist())==73 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save61member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==57 and visual['reviewed_screens']==dict(progress=list(range(55)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save61画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save61画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE61_ORIGINAL=str(original),PR16_SAVE60_INPUT=str(assets/'input.srm'),PR16_SAVE61_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save61_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==55 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 55 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'55成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save60-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save61 artifact11286499716のstory-fast.srm（131088bytes/SHA256 4bb9bb7761d2983164e0aa48687d0dae1ed893248b312af4f9ee36dbd873a092）だけから再開。map1/59・25,6東。新北迂回13歩とハクタクン♂Lv9野生1勝を限定受入。旧14,6→15,6不通辺は再走せず、14,5→15,5→16,5→16,6で通過。つばめがえし1コマンド/実PP11→9を区別し、相手プレッシャーpopup/文言と整合。HP288/294・PP15,10,15,9、ミュウツー全HP/PP、party残り599byte/Bag/17904円/RP0/badge1/story4071=9/4072=1保持。次は保存済未通過接尾辞25,6→26,6→27,6→28,6→28,7→28,8→28,9→28,10→29,10→30,10（behavior108階段）からmap1/60warp2へ。最初の新event/戦闘/不通境界で保存。上階/紙未到達、紙ownerはmap1/60背景16,28/item274/flag4383。27新controller/55新受入、101+cold13入力57画面72member/native2。49counter61でも部分write、50成功→54field。全SaveRTC/field画面同一。RAM台帳は観測25の技menuで変化しowner未解明。旧offset41/2056/aux4021/4022/404d/40ac未解明保持。Flash未使用/未習得、がくしゅうそうち未装備。旧迂回/戦闘/保存や旧20,24着地点不発を無影響再走しない。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save61_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,normal_recovery_repeated=False,double_target_separation_native_exercised=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=27,controller_executions=27,unchanged_controller_cases_replayed=0,new_acceptance_tests=55,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 館の北迂回13歩・プレッシャー野生1勝・Save61限定受入

`{result['status']}`。Save60の14,6東から北側へ迂回し、25,6東まで新13歩。旧14,6→15,6への東不通入力は再走しない。新野生ハクタクン♂Lv9に1勝し通常保存・独立Continue。上階/有効階段/像の紙は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。72member/57画面/101+cold13入力。新controller27case、55新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## 迂回とプレッシャーの限定観測

0〜17で14,6→14,5→15,5→16,5→16,6→24,6。向き変更4回、3で東向き後4も14,5を維持し5で15,5へ通過。近傍NPCが移動するがruntime identityや旧不通の因果を断定しない。18で25,6へ進み野生遷移、19暗転、20導入。21ハクタクン♂Lv9、22オノノクス♀Lv100/HP288/294、23プレッシャーpopupと「プレッシャーを はなっている！」。25slot0→26slot2→27slot3つばめがえしPP11、28撃破。選択は1コマンド、相手確定0、実保存PPは11→9で2消費。観測した能力表示と整合するが全技/特性一般検証には昇格しない。

29field、30〜34menu0→4、35確認/36上書き、37〜49保存中。49counter61でも部分write、50〜53成功文言、54field。progress29/54/cold0/cold1の全画面byte一致、全SaveRTCも一致。勝利残留flags4/outcome1とwire field=falseを追加戦闘や未復帰扱いしない。

## 限定差分と未完

party600bytes中slot3 PPの1byteだけ変化し残り599byte保持。HP288/294・PP15,10,15,9、ミュウツー全HP/PP、EXP/held item・全Bag/17904円/RP0・全legacy flags・PC/S61E全payload・旧Save60bank57344byte保持。42checksum、6974byte/1716範囲。aux4021=76→89、RAM台帳は観測25の技menuで変化、runtime owner未解明。過去のRAM台帳/offset41/2056/aux/40ac未解明を保持。

次は25,6から未通過9歩の階段接尾辞。有効階段/上階/紙は未到達、旧20,24着地点不発も再走しない。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。一般CI既知不一致/action_requiredを成功にしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save60']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37158672102');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='7e495ef303475b948b6cf0f913e0ead8176d9fa9','旧Stage79終端')
    state['story_save60']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save61']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,59],xy=[25,6],facing=4,rp=0,money=17904,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[15,10,15,9],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,trainer_victories=0,wild_victories=1,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='新北迂回13歩/プレッシャー野生1勝/Save61。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='館の北迂回13歩/25,6東/ハクタクン野生1勝/Save61。プレッシャー表示・選択1/実PP2。上階/紙未到達。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_STAIR_SUFFIX_FROM_SAVE61',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save61_accept.py','scripts/pr16_story_save61_measure.py',a.EVIDENCE+'/inspection.json','content/modernization/pr16_story_save57_preparation.json','content/modernization/pr16_story_save56_preparation.json'],stop_rule_ja='Save61の25,6東から階段30,10へ未通過接尾辞。最初の新event/戦闘/未通過境界で保存。旧北迂回/野生1勝は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='こころのやかた北迂回13歩・野生ハクタクン1勝でSave61。25,6東、プレッシャー表示/PP11→9。上階/像の紙未到達。'
    state['do_not_repeat'].append('Save61の101/cold13入力57画面72member/27controller/55受入を無影響再走しない。北迂回13歩/野生1勝/選択1と実PP2を区別。49counter61部分write→50成功→54field、全SaveRTC/field画面同一。RAM台帳観測25変化/aux4021owner未解明。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 館の北迂回13歩とプレッシャー野生1勝Save61
- Version: story-mansion-north-detour-save61-v1
- Status: DONE（新13歩/野生1勝/保存/独立Continue限定）
- Summary: Save60東不通から通常北迂回13歩、25,6東。ハクタクン♂Lv9新野生1勝、プレッシャー表示とつばめがえし選択1/実PP11→9を区別。party残り599byte/HP288/294/Bag/17904円/RP0保持。上階/有効階段/紙未到達。
- Files changed: Save61 measure/27controller/55受入/record、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。101+cold13入力57画面72member。新27controller原log継承/55新受入拒否試験。record native0/compile0/既受入再走0。
- Evidence: 49counter61部分write→50成功→54field。全SaveRTC/field画面同一。RAM台帳は25技menuで変化、aux4021=76→89owner未解明。旧bank57344byte/42checksum/6974byte1716範囲。NPC同定/旧不通因果は未確定。
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



