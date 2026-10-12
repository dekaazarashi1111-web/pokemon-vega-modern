#!/usr/bin/env python3
"""館内の新1歩・コレクター210新1勝Save62原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save62_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MANSION-COLLECTOR210-SAVE62'
OUT=ROOT/'.local/pr16-story-save62-record'

CODE={'scripts/pr16_story_save62_accept.py','scripts/pr16_story_save62_record.py','tests/test_pr16_story_save62_accept.py',a.VISUAL,'.github/workflows/pr16-story-save62-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE62_JA.md' and a.CP=='content/modernization/pr16_story_save62_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save62_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37159642405,'39d198614105804285f070ac94f63a7867a9f0a6',111310230045,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save62_measure.',27)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==72 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save61全72member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save61/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==71 and len(z.namelist())==72 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save62member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==56 and visual['reviewed_screens']==dict(progress=list(range(54)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save62画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save62画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE62_ORIGINAL=str(original),PR16_SAVE61_INPUT=str(assets/'input.srm'),PR16_SAVE62_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save62_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==58 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 58 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'58成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save61-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'route-plan.json',a.route_plan())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save62 artifact11286961947のstory-fast.srm（131088bytes/SHA256 6526b5a8cf179800096fda0721f2e1770818170c83e9b76da39957166d86e356）だけから再開。map1/59・26,6東。Save61から新1歩でヒサテル/コレクター210の新1勝、敵3体・つばめがえし3選択/実PP9→6・交代拒否2回・賞金840円、physical1490=0→1を限定受入。HP288/294・PP15,10,15,6、ミュウツー全HP/PP、party残り599byte/Bag/RP0/badge1/story4071=9/4072=1/全legacy vars保持、所持金18744。次は未通過8歩26,6→27,6→28,6→28,7→28,8→28,9→28,10→29,10→30,10（behavior108階段）からmap1/60warp2へ。最初の新event/戦闘/不通境界で保存。上階/紙未到達。紙までの静的候補は専用route-plan.jsonの89tile+3層間接続（92edges）。上階32,10側から紙16,28側へ直接歩けず、上階31,21のbehavior102穴→入口階31,22→入口階30,29の階段→上階33,29→紙背面16,27が候補。穴/階段/動的通行は未実測、旧20,24着地点不発は再走しない。27新controller/58新受入、101+cold13入力56画面71member/native2。48counter62でも部分write、49成功→53field。全SaveRTC/field画面同一。RAM台帳は観測17の2体目撃破で変化しowner未解明。旧offset41/2056/aux4021/4022/404d/40ac未解明保持。Flash未使用/未習得、がくしゅうそうち未装備。旧迂回/野生戦/本trainer戦/保存を無影響再走しない。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save62_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,normal_recovery_repeated=False,double_target_separation_native_exercised=False,visual_review=a.VISUAL,static_route_plan=a.EVIDENCE+'/route-plan.json',source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=27,controller_executions=27,unchanged_controller_cases_replayed=0,new_acceptance_tests=58,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 館のコレクター210新1勝・Save62限定受入

`{result['status']}`。Save61の25,6東から新1歩で26,6東へ進み、ヒサテルに発見され新trainer戦。敵3体を倒して1勝、通常保存・独立Continue。上階/有効階段/像の紙は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。71member/56画面/101+cold13入力。新controller27case、58新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## コレクター新1勝と保存

0開始、1新1歩/接近、2勧誘台詞、3導入、4ポケモンコレクターのヒサテル。5イシズマイ♂Lv11、15ビッパ♂Lv12、21コフキムシ♀Lv14。10/16/22でslot3つばめがえし選択、実PP9→8→7→6。13/19の交代確認を2回拒否し先頭維持。25勝利、26降参台詞、27実賞金840円、28field。3体撃破を3勝とせずtrainer1勝だけ。

29〜33menu0→4、34確認/35上書き、36〜48保存中。48counter62でも部分write、49〜52成功文言、53field。progress28/53/cold0/cold1の全画面byte一致、全SaveRTCも一致。今回trainer戦後はwire field=trueへ戻る。残留flags12/outcome1を追加勝利にしない。

## 差分・静的owner・次の経路

party600bytes中slot3 PPの1byteだけ変化し残り599byte保持。保存partyからPP8/7/6各段階の全600byte hashも独立再構成。HP288/294・PP15,10,15,6、ミュウツー全HP/PP、EXP/held item・全Bag/RP0・全legacy vars・PC/S61E全payload・旧Save61bank57344byte保持。所持金17904→18744。legacy flag唯一の差分はphysical1490=0→1。保存済map1/59 local9/初期26,4/script154591088のtrainerbattle210命令と固定remap210+0x500→1490をROM byte照合。ただしruntime object IDの直接捕捉とは主張しない。

42checksum、6975byte/1716範囲。RAM台帳は観測17の2体目撃破で変化しruntime owner未解明。過去のRAM台帳/offset41/2056/aux/40ac未解明を保持。

保存済み二階層の静的床/warp ownerから、[紙までの静的候補](../{a.EVIDENCE}/route-plan.json)を新規整理。26,6から89tile移動+3層間接続の92edges。上階32,10の領域は紙16,28側と非連結で、上階31,21のbehavior102穴→入口階31,22→入口階30,29階段→上階33,29の南側領域→紙背面16,27が候補。新ROM採取0、動的NPC/戦闘/穴作動/階段作動は未受入。まず未通過8歩の北東階段30,10へ進み最初の新境界で保存する。

全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。一般CI既知不一致/action_requiredを成功にしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save61']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37159642381');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='39d198614105804285f070ac94f63a7867a9f0a6','旧Stage79終端')
    state['story_save61']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save62']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,59],xy=[26,6],facing=4,rp=0,money=18744,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[15,10,15,6],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,trainer_victories=1,wild_victories=0,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/route-plan.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='新1歩/コレクター210新1勝/賞金840/Save62。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='館の新1歩/26,6東/コレクターヒサテル新1勝/Save62。敵3体・PP3消費・840円・flag1490。上階/紙未到達。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_STAIR_SUFFIX_FROM_SAVE62',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save62_accept.py','scripts/pr16_story_save62_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/route-plan.json','content/modernization/pr16_story_save57_preparation.json','content/modernization/pr16_story_save56_preparation.json'],stop_rule_ja='Save62の26,6東から階段30,10へ未通過8歩。最初の新event/戦闘/未通過境界で保存。紙へは別領域間の3接続候補を使い、旧受入区間/着地点不発は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='こころのやかたヒサテル新1勝でSave62。26,6東、PP9→6/賞金840円。紙への二階層3接続を静的整理、上階/紙未到達。'
    state['do_not_repeat'].append('Save62の101/cold13入力56画面71member/27controller/58受入を無影響再走しない。新1歩/コレクター210新1勝/敵3体/PP3/840円/1490bitだけ。48counter62部分write→49成功→53field、全SaveRTC/field画面同一。RAM台帳観測17変化owner未解明。静的92edgeをnative受入にしない。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 館のコレクター210新1勝Save62と紙までの静的経路
- Version: story-mansion-collector210-save62-v1
- Status: DONE（新1歩/trainer1勝/保存/独立Continue限定、紙routeは静的候補）
- Summary: Save61接尾辞新1歩、26,6東。ヒサテル敵3体に新1勝、つばめがえし3選択/実PP9→6、交代拒否2回、賞金840円/physical1490。party残り599byte/HP288/294/Bag/RP0/全vars保持。上階/紙未到達。
- Files changed: Save62 measure/27controller/58受入/record、checkpoint/text証拠/route-plan、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。101+cold13入力56画面71member。新27controller原log継承/58新受入拒否試験。record native0/compile0/既受入再走0。
- Evidence: 48counter62部分write→49成功→53field。全SaveRTC/field画面同一。RAM台帳17変化owner未解明。旧bank57344byte/42checksum/6975byte1716範囲。保存済local9 scriptのtrainer210とremap1490照合。上階北東→穴31,21→入口南東階段30,29→上階南側/紙背面16,27の89tile+3warpは静的候補でnative未受入。
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



