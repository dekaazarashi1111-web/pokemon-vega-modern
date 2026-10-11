#!/usr/bin/env python3
"""Ranger接近Save99の原本を独立受入し固定引継ぎ/両ログを同期。native0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT),str(ROOT/'tests')]
import pr16_story_save99_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-RANGER-SAVE99';OUT=ROOT/'.local/pr16-story-save99-record'
CODE={'scripts/pr16_story_save99_accept.py','scripts/pr16_story_save99_record.py','tests/test_pr16_story_save99_accept.py',a.VISUAL,'content/modernization/pr16_story_save99_next_route.json','.github/workflows/pr16-story-save99-record.yml'}
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
    raw=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode();log=raw.splitlines();lines=[v.split('Z ',1)[-1]for v in log if' ... 'in v and'test_pr16_story_save99_measure.'in v]
    need(len(lines)==40 and all(v.endswith(' ... ok')for v in lines)and any('Ran 40 tests'in v for v in log),'新40controllerの成功原本行だけ再読')
    import test_pr16_story_save99_measure as tests
    need(unittest.defaultTestLoader.loadTestsFromModule(tests).countTestCases()==40,'40caseはloadだけ、再走0')
    return dict(final_cases=40,executions=40,passed_executions=40,failed_executions=0,unchanged_success_reruns=0,job=a.JOB,test_lines=lines)

def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists()and not(ROOT/a.CP).exists(),'新記録1回だけ')
    need(a.GUIDE=='docs/PR16_STORY_SAVE99_JA.md'and a.CP=='content/modernization/pr16_story_save99_checkpoint.json','今回専用宛先')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need({a.GUIDE,a.CP}.isdisjoint(protected)and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入は不変')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37196489863,'3060cd081007374a6ced4f7d1394ee10901ee576',111419360155,['success']*11)
    controller=controller_receipt()
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        mf=json.loads(z.read('manifest.json'));need(len(mf)==84 and set(z.namelist())==set(mf)|{'manifest.json'},'親Save98全84member')
        for n,b in mf.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save98/不変ROM')
    original=OUT/'original';meta,manifest=unpack_verified(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE,original,119)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==104 and visual['reviewed_screens']==dict(progress=list(range(102)),**{'continue':[0,1]})and visual['save_success_wording_observed']is True,'全104原画目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'原画 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE99_ORIGINAL=str(original),PR16_SAVE98_INPUT=str(assets/'input.srm'),PR16_SAVE99_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save99_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    lines=[v for v in unit.stderr.decode().splitlines()if v.startswith('test_')]
    need(unit.returncode==0 and not unit.stdout and len(lines)==67 and all(v.endswith(' ... ok')for v in lines)and re.search(rb'\nRan 67 tests in [0-9.]+s\n\nOK\n\Z',unit.stderr),'67成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for p in sorted(original.rglob('*')):
        if not p.is_file()or p.suffix not in{'.json','.txt'}:continue
        raw=p.read_bytes();raw.decode();need(b'\0'not in raw,'tracked textのみ');dest=evidence/p.relative_to(original);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr);write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'controller-test-receipt.json',controller);write(evidence/'next-route.json',a.next_route());write(evidence/'save98-record-terminal.json',prior_done)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    rule=a.next_route()['transition_preflight_rule_ja']
    goal='Save99 artifact11301562515のstory-fast.srm（131088bytes/SHA256 18de364bd911a9470965cf571e10aab899e8f4236bcaef327586e965b3a02b6b）だけから再開。505番道路3/23・18,28西。61歩/15旋回・ROCK_STAIRS2か所・通常Save99/独立Continueを限定受入。草地を通ったが戦闘0、wild controllerはnative未使用。主人公のRanger正面隣接は未達。実画面のRangerは20,28、cold120frame後20,29へ動く。静的18,27へ北Aを盲送しない。次は実NPC位置・正面隣接を画面またはread-only object観測で確定して通常A。4382=true/4380=falseの固定scriptは4072=2/4352clear/町3,2へのwarp5,16。これは未測定、回復台詞は別分岐なのでHP/PP回復を仮定しない。最初の新field→通常Save100/独立Continueで止める。接近61歩/町/博物館/封書/受付再走なし。HP277/294/PP3,9,8,2/ミュウツー全HP/PP/23114円/4061=1/紙274=0/4382/4383/バッジ2/全party600byte/PC/S61E保持。4021=(30+61)%128=91/4022=(0+61)%5=1、次friendship周期まで37歩。今回RAM53差分と過去RAM42/2056等のowner未解明は残す。104画面/197+cold13入力、96counter99は途中hash/保存中、97最終hash/成功文言、101clearfield。cold間376pixelはRanger移動、全SaveRTC一致と全pixel一致を混同しない。40新controller/67新受入、成功native2/失敗0/記録native0/旧成功再走0。Save98記録run37196489863の全11stepを終端同期。旧失敗原本不変、ROM/runtime非再配布、ROM変更/host補充/merge/release/baseline変更0。全国図鑑/自然成長進化/全story/release未受入。一般CI既知qol_production.c不一致を全成功にしない。'+rule
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save99_accepted=True,ranger_approach_accepted=True,ranger_interaction_accepted=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=40,controller_executions=40,new_acceptance_tests=67,successful_native_processes=2,prior_failed_native_processes=0,record_native_processes=0,next_goal_ja=goal,transition_preflight_rule_ja=rule,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f'''# Ranger接近・Save99限定受入

`{result['status']}`。Save98から新61歩/15旋回で505番道路18,28西まで接近。通常Save99と独立Continue。会話/新戦闘/warpは0。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。119member/104画面/197+cold13入力。40controller/67新受入。成功native2/失敗0/記録native0/旧成功再走0。

## ROCK_STAIRSと歩行owner

behavior0x2aは固定上流/ROMのROCK_STAIRS。0x8059d1cの判定、0x805b368の北=現在tile/南=1tile南、0x805b348の通常歩行slow分岐をbinding。warp/一方向ledgeではない。32,15→32,14→32,13を北入力、22,19→22,20→22,21を南入力で実通過。全tile単位/15旋回、blocked0/自動歩行0。

歩数4021は30→91、4022は0→1。61歩でfriendship周期128には届かず、status0の4体は毒ダメージなし。party600byte全保持、HP277/294とPP3,9,8,2保持。次friendship周期まで37歩。RAMledgerは観測53で変化しowner未解明、以後/coldは保持。過去RAM42/physical2056等は未解決のまま。

## 保存・動的Ranger

77〜81menu0→4、82/83確認、84〜96保存中。96counter99でも途中hash、97最終hash/成功文言、101clearfield。全SaveRTC131088byte/PC/S61E/旧bank57344byte保持、7160byte/1788範囲/42checksum。

最終画面の主人公18,28西に対しRangerは2tile東の20,28。cold0も20,28、無入力120frame後cold1は20,29。位置は16px/tileの実画面比較で確認し、RAMobject配列は未採取。progress/cold0差132px、progress/cold1差410px、cold間差376pxは矩形145,67〜158,102のNPCだけ。全pixel一致ではない。静的初期18,27への北Aや回復を仮定しない。

## 次

{goal}
'''
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本不変')
    state['story_save98']['record_completion']=prior_done
    state['story_save99']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[3,23],xy=[18,28],facing=3,rp=0,money=23114,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],ranger_approach_accepted=True,ranger_interaction_accepted=False,museum_admission_var4061=1,letter_handoff_accepted=True,paper_quantity=0,paper_flag4383=True,paper_flag4382=True,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_route=a.EVIDENCE+'/next-route.json',next_goal_ja=goal,transition_preflight_rule_ja=rule)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='Ranger接近61歩/15旋回/ROCK_STAIRS2か所のSave99。動的NPCを正面隣接と混同しない。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='Ranger接近Save99/505番道路18,28西。61歩15旋回/104画面197+cold13入力。戦闘0/全party600byte/HP277/PP3,9,8,2/23114円保持。Rangerは20,28→20,29で動く、正面隣接/会話未達。ROCK_STAIRSを静的/実歩行照合。4021=91/4022=1、次周期37歩。RAM53/過去42/2056未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stop='Save99から動的Rangerの実位置/正面隣接を確認してから通常A。最初の新fieldでSave100/独立Continue。静的18,27への北Aを盲送しない。会話分岐で回復を仮定しない。接近61歩は再走しない。'+rule
    state['next_action'].update(id='STORY_DYNAMIC_RANGER_FROM_SAVE99',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save99_accept.py','scripts/pr16_story_save99_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,'content/modernization/pr16_story_save99_next_route.json'],stop_rule_ja=stop)
    state['do_not_repeat'].append('Save99の197/cold13入力104画面119member、61歩15旋回/ROCK_STAIRS2か所、40controller/67新受入を無影響再走しない。会話未達で動的Rangerの位置を次回確認。ROM/runtime非再配布。'+rule)
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='Save99/505番道路18,28西。61歩/15旋回/ROCK_STAIRS2か所を通過、戦闘0/全party保持。Ranger20,28→20,29の動きを実画面確認、正面隣接/会話未達。次周期37歩/RAM53未解明。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'''
## {stamp}
- Version: PR16-STORY-SAVE99
- Timestamp: {stamp}
- Task: {TASK} / Ranger接近とSave99
- Status: DONE（61歩接近/保存/Continue限定、Ranger正面隣接/会話未完）
- Summary: 新61歩/15旋回・ROCK_STAIRS2か所で505番道路18,28西。戦闘0、通常Save99/Continue。全party600byte/HP277/PP3,9,8,2/23114円/4061/4382/4383保持。
- Files changed: Save99 measure/controller/preparation/独立受入67/visual/record/checkpoint/text証拠/次dynamic plan、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、40新controller/67新受入。197+cold13入力/104画面/119member/native2/失敗0/記録native0/旧成功再走0。7160byte1788範囲/42checksum/全SaveRTC/PC/S61E/旧bank保持。
- Evidence: 96counter99は部分hash/保存中、97最終hash/成功文言、101clearfield。Ranger20,28→cold120frame後20,29。progress/cold132/410px、cold間376pxはNPC矩形内だけ。主人公位置は同一だが全pixel一致ではない。
- Owner: behavior0x2a=ROCK_STAIRSの0x8059d1c/0x805b368/0x805b348を固定ROMbinding。南北の減速歩行でwarp/一方向ledgeではない。4021=30+61→91/4022=0+61→1、次friendship周期37歩。RAM53と過去42/2056等は未解明のまま。
- Terminal sync: Save98記録run37196489863/job111419360155の全11step成功を同期。旧失敗原本は改作なし。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repoGitHub/Actions、source-lock固定pret/pokefirered c75f3523のmetatile定数/predicate/player avatar。ROM/runtime非再配布、ROM変更/host補充/merge/release/baseline変更0。一般CI既知不一致を全成功にしない。
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

