#!/usr/bin/env python3
"""505番道路の通常迂回とセナラナ戦のSave50原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save50_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE505-SAVE50'
OUT=ROOT/'.local/pr16-story-save50-record'

CODE={'scripts/pr16_story_save50_accept.py','scripts/pr16_story_save50_record.py','tests/test_pr16_story_save50_accept.py',a.VISUAL,'.github/workflows/pr16-story-save50-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE50_JA.md' and a.CP=='content/modernization/pr16_story_save50_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save50_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37142517526,'76ba6c8ff45c9f1f0943a7e2741bef643d279f81',111259715046,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save50_measure.',20)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==44 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save49全44member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save49/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==168 and len(z.namelist())==169 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save50member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==153 and visual['reviewed_screens']==dict(progress=list(range(151)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save50画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save50画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE50_ORIGINAL=str(original),PR16_SAVE49_INPUT=str(assets/'input.srm'),PR16_SAVE50_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save50_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==44 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 44 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'44成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save49-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save50 artifact11281112264のstory-fast.srm（131088bytes/SHA256 b586055a74bd6b826d7ea8150e25954a9452718ad5b46e4926f0d01f9088022e）だけから再開。505番道路33,0→西側迂回57歩→22,18北/高度4でセナラナのダブル戦1勝、通常Save50/独立Continue全SaveRTC一致を限定受入。party4/RP0/15640円/badge1/story4071=9/4072=1。オノノクスHP294/294・PP[11,10,15,18]、ミュウツーHP50/354・PP全0、ミュウHP342/342とメタモンHP300/300はいずれも技4枠0。PP持ちは1体だけで、並替だけで2体にはできない。次は保存済み候補routeのindex57から残47歩を使い、任意戦を避けて南connection→map3/2の28,0/正常回復を優先。最初の新戦闘/event/未通過境界/接続または実回復で保存。戦闘前にはダブル戦の技選択/相手確定を別計数し、現在PPへ再束縛する。今回raw used6は選択3+target3で実PP消費2、3回目は相方が先に倒して未実行。ミュウツーのわるあがき3回反動264HPを回復扱いしない。新classifierはslot0/2/3表示とslot3実使用2だけをnative確認、slot1/全4技は未完。歩行中party byte41=43→44と途中RAMledger4差・aux4021=109→37/4022=4→0はowner未解明。146安定Flash/counter50→147成功文言→150fieldを分離。原本296+cold13入力153画面/20controller44受入/168memberを無影響再走0。旧失敗と旧party/ledger不明差を保持。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。ROM/host補充/故意全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用。一般CI既知qol_production.c source不一致/finalHEAD action_requiredを全成功にしない。'
    extra={'scripts/pr16_story_save50_inspect.py','scripts/pr16_story_save50_inspect_west.py','.github/workflows/pr16-story-save50-inspect.yml','.github/workflows/pr16-story-save50-inspect-west.yml',a.m.PREP,a.m.WEST}
    inspections=[]
    for run,source,job in [(37143096088,'fce28e7eadbca614e689175afd56b17d2d8fe2f1',111261408572),(37143284932,'a6e21c85944b1e613ae1bc63553dea1352ce6574',111261971903)]:
        inspections.append(inherited.terminal(run,source,job,['success']*8))
    write(evidence/'inspection-terminals.json',inspections);paths.add(a.EVIDENCE+'/inspection-terminals.json')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
        artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save50_accepted=True,
        normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,route505_south_connection_accepted=False,double_target_miscount_preserved=True,
        visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE|extra),evidence_bindings=h.d.bindings(paths),new_controller_tests=20,new_acceptance_tests=44,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 505番道路の通常迂回・セナラナ戦・Save50限定受入

`{result['status']}`。33,0から西側へ57歩/18方向転換、22,20階段を通過して高度4の22,18北へ。センパイとコウハイのセナとラナのダブル戦1勝と通常Save50/独立Continueだけを受入。南接続/正常回復は未完。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全168member、153画面、296+cold13入力。20新controller原log継承、44新受入/拒否試験。native2/record0/旧入力再走0/ROM変更0。

## ダブル戦と通常入力の限界

79〜125でココガラ/タマンチュラ/クヌギダマ/ビッパと戦い、122勝利、125賞金416円、126field。party4/RP0、15224→15640円。trainer1054は同候補remapでphysicalflag1406へ対応し、保存差はその1bitだけ。

実技panelは86/87/88でcursor0→2→3。89/103/117は相手確定のため同じpanelが残る。raw controllerのused6を改作せず、選択3+target3と実PP消費2に分離する。つばめがえしは2回、PP20→18。3回目はミュウツーが先に最後の相手を倒し未実行。slot1/全4技native受入ではない。次の戦闘前にtargetを別計数し、Save50の実PPへ再束縛する。

ミュウツーは全PP0。通常わるあがき3回、反動でHP314→226→138→50。オノノクスHP294/294・PP[11,10,15,18]。ミュウHP342/342、メタモンHP300/300は技欄4つ0。PP持ち2体への単なる並替では解決しない。回復は未完、任意戦を避けて実回復を優先する。

## 全保存境界

party差はbyte41=43→44（24の歩行中、runtime owner未解明）、byte55=20→18（PP2）、186/187=58,1→50,0（HP314→50）。party phase全6hashを原本へ結合。全Bag/所持品/PC/S61E/badge1/story4071=9/4072=1は不変。aux4021=109→37/4022=4→0とRAMledger39/85/106/126のownerは未解明。最終coldでは全RAMledgerも一致。

127〜131通常menu cursor0→4、132確認、133上書き、134〜145は12種類の書込中Flash。146安定Flash/counter50でも成功文言はまだ未表示、147〜149成功文言、150field。cold0/1は22,18北で全SaveRTC一致。42sector checksum、旧Save49bank57344byte保全、6948byte/1728差分範囲。

## 再利用と未踏範囲

Save49の1cellとSave44の505collision viewを再利用。read-only run37143096088で未読東側322cell/13script、run37143284932で西8〜20行187cell/12script、診断0。東側のみ/西20行まででは南へ通じる候補なし。今回さらに21行12cellと南接続先1cell/map3/2を追加読取して104歩の候補を得た。実通過は先頭57歩だけ、残47歩と南connectionは未受入。新しいread-only原本から再開し、再採取しない。

旧Save47誤陰性/Save48途中ledger/Save46party2byte/Save39cold/Save44並替差と旧失敗を保持。正規全国図鑑/自然EXP・技習得・進化/全story/研究施設自然到達/releaseは未完。一般CI既知source不一致とaction_requiredを全green扱いしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8')
    need(h.d.bindings(protected)==protected,'旧受入正本/入力は不変')
    state['story_save49']['record_completion']=prior_done
    stage79=h.d.inputs.api('actions/runs/37142517457');need(stage79['status']=='completed'and stage79['conclusion']=='success'and stage79['head_sha']=='76ba6c8ff45c9f1f0943a7e2741bef643d279f81','Save49記録source Stage79終端')
    state['story_save49']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save50']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[3,23],xy=[22,18],facing=2,elevation=4,rp=0,money=15640,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[294,294],lead_pp=[11,10,15,18],mewtwo_hp=[50,354],mewtwo_pp=[0]*4,normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,trainer_victories=1,route505_south_connection_accepted=False,double_target_miscount_preserved=True,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='通常57歩/セナラナのダブル戦/Save50限定受入。回復未完、target計数と実PP消費を分離。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='505の通常迂回57歩、セナラナのダブル戦とSave50測定source。正常回復未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_RECOVERY_ON_ROUTE505_FROM_SAVE50',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save50_accept.py','scripts/pr16_story_save50_measure.py',a.EVIDENCE+'/inspection.json',a.m.PREP,a.m.WEST],stop_rule_ja='Save50/22,18北から残47歩の保存候補だけ。任意戦を避けて通常回復を優先。次battle前にtarget二重計数を分離し実PPへ束縛。最初の新戦闘/event/未通過境界/接続/実回復で保存。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='通常57歩とセナラナのダブル戦1勝、505番道路22,18北でSave50/独立Continueを限定受入。ミュウツーHP50/全PP0、回復未完。'
    state['do_not_repeat'].append('Save50の296/cold13入力153画面・20controller44受入を無影響再走しない。57歩/セナラナ1勝/Save50、raw used6は実PP2+選択targetの限界を保持。party byte41/ledger owner未解明、反動HP314→50を回復としない。146安定/counter→147成功→150field。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE|extra)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 505番道路の通常迂回・セナラナ戦・Save50
- Version: story-route505-save50-v1
- Status: DONE（新57歩/ダブル戦1勝/保存/独立Continue限定受入。回復未完）
- Summary: 33,0→22,18北/高度4。通常賞金416円で15640円。ミュウツーPP0のわるあがき3回、反動264でHP50/354。オノノクスHP294/294・PP[11,10,15,18]。PP持ち2体への並替だけでは解決しない。
- Files changed: Save50 inspect東/西原本・measure/20新試験・44新受入拒否/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、296/cold13入力153画面168member。20controller原log継承、新44受入、record native0。raw used6は選択3+target3で実PP消費2、3回目未実行。元測定を改作しない。
- Evidence: party差41/55/186/187の4byte、歩行byte41owner未解明。physicalflag1406のみ。aux4021/4022とRAMledger4差owner未解明。134〜145部分write、146安定Flash/counter50→147成功→150field。42checksum/旧bank57344byte/6948byte1728範囲/cold全SaveRTC一致。
- Read-only: 東322cell/13script、西187cell/12scriptを新規採取し診断0。追加21行12cell+接続先1cell/map3/2のみ。保存collision/旧native不変。104歩候補の実57歩だけ受入、残47歩/南connection未踏。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actionsのみ。既存ROM/runtime/input非再配布。旧失敗・未解明差を保持。一般CI既知source不一致/finalHEAD action_requiredは全成功としない。merge/release/baseline変更0。
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

