#!/usr/bin/env python3
"""館内の新野生1勝Save57原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save57_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MANSION-WILD-SAVE57'
OUT=ROOT/'.local/pr16-story-save57-record'

CODE={'scripts/pr16_story_save57_accept.py','scripts/pr16_story_save57_record.py','tests/test_pr16_story_save57_accept.py',a.VISUAL,'.github/workflows/pr16-story-save57-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE57_JA.md' and a.CP=='content/modernization/pr16_story_save57_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save57_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37153775936,'73261d17c77f56ad4e2fcc80a8cac30d9af21e6e',111292837644,['success']*11)
    test_receipts=[]
    for job,suite,count in [(111295266609,'test_pr16_story_save57_measure.',25),(a.JOB,'test_pr16_story_save57_measure.',3)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==57 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save56全57member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save56/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==69 and len(z.namelist())==70 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save57member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==53 and visual['reviewed_screens']==dict(progress=list(range(51)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save57画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save57画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE57_ORIGINAL=str(original),PR16_SAVE56_INPUT=str(assets/'input.srm'),PR16_SAVE57_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save57_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==51 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 51 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'51成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save56-record-terminal.json','prior-inert-warp-failure.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save57 artifact11284919827のstory-fast.srm（131088bytes/SHA256 082a6789ed90223995bd007efaa43337c8aca352d85f1a33068a6fae11b1b9ca）だけから再開。map1/59・19,13北。通常13歩と野生バーニンLv9へ1勝、つばめがえし1回/PP14→13、HP288/294・ミュウツー全HP/PP・Bag/17904円/RP0/badge1/story4071=9/4072=1保持、Save57/独立Continueを限定受入。上階/像の紙は未到達。旧次工程20,24のwarp8は床behavior8上の着地点であり、通常北入力では発火しない。未保存失敗16入力3画面/native1/Save56全byte不変を保持し、同じ北歩行を繰り返さない。次は保存済pr16_story_save57_measure.ROUTEの19,13からの接尾辞を使い、北19,12→西7,12→南7,16→西5,16→北5,6→東28,6→南28,10→東30,10のbehavior108階段warp5→map1/60warp2へ通常入力。最初の新event/戦闘/未通過境界で保存する。到着候補32,10/33,10は未測定。像の紙ownerはmap1/60背景16,28/script149012422・item274だいじなふうしょ/setflag4383と静的照合済みだが取得は未受入。次階層warp31,21→map1/59の31,22は逆向き着地点と区別。27controller計28実行と51新受入、93+cold13入力53画面69memberを無影響再走0。RAMledgerは観測3で939b183a3db45a9fedd87e87814bbb94e1cd42a8510dc3d3083d0ce96d9ff1d4へ変化しowner未解明、全coldSaveRTC/全暗所field画面同一。45counter57でも部分write、46成功→50field。旧RAM/offset41/2056/aux4021/4022/404d/40acのowner未解明を保持。Flash未使用/未習得、がくしゅうそうち未装備。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。'
    extra={'scripts/pr16_story_save57_inspect.py','.github/workflows/pr16-story-save57-inspect.yml'}
    terminal=inherited.terminal(37154213537,'66490428811ca668483bfa8cd4b7e514a3c37f9f',111294130125,['success']*8)
    _,z=a.transport.archive(11284793695,37154213537,dict(size=14013,sha256='a94d58afe9ba811e74e2a487fed85623fbcb8dc1249513aabd54cd657d8b4864'),'66490428811ca668483bfa8cd4b7e514a3c37f9f')
    with z:need(z.namelist()==['inspection.json']and z.read('inspection.json')==(ROOT/a.m.PREP).read_bytes(),'15node/1444cell静的原本全byte')
    name=a.EVIDENCE+'/inspection-terminal.json';write(ROOT/name,terminal);paths.add(name)
    failed=json.loads((original/'prior-inert-warp-failure.json').read_bytes());need(failed['terminal']['run']['conclusion']=='failure','失敗を成功へ改作しない')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save57_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,normal_recovery_repeated=False,double_target_separation_native_exercised=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE|extra),evidence_bindings=h.d.bindings(paths),controller_cases=27,controller_executions=28,unchanged_controller_cases_replayed=0,new_acceptance_tests=51,successful_native_processes=2,prior_failed_native_processes=1,total_native_processes=3,prior_failure=failed,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 館内通常13歩・野生1勝・Save57限定受入

`{result['status']}`。Save56から西1歩/北12歩、19,13でバーニン♀Lv9に遭遇。オノノクスLv100のつばめがえし1回で通常撃破し、Save57と独立Continue。HP288/294・PP[15,10,15,13]。上階/像/紙は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。69member/53画面/93+cold13入力。controller27case（初回25、影響1+新規2の計28実行、未影響24件原log継承）、51新受入拒否試験。成功native2/失敗native1/record0/旧受入再走0/ROM変更0。

## 着地点warpと発火床の訂正

旧引継ぎの20,24warp8はmap1/60側から戻る着地点。実床behavior8であり、通常北入力では発火しない。初回run37154589799/source79ad87e8223c84f0cb781667e54ab85a395fcddd/job111295266609/artifact11285188296は20,25→20,24→20,23の16入力3画面/native1でguard停止。全Save56不変・未保存。原本を改作せず、有効behavior108の30,10階段への別経路を実装した。同じ不発北歩行を繰り返さない。

新階層1/60は15node/1444cell/1mapだけ採取。像16,28/script149012422にitem274「だいじなふうしょ」/flag4383を静的確認。native未到達・未取得であり、その受入とは区別する。

## 野生戦と保存

0〜14暗所の通常移動、15野生遷移/16暗転/17battle。18バーニン♀Lv9、19オノノクスLv100。21slot0/22slot2/23slot3の実技UI、つばめがえしPP14、24撃破/実PP13。25callback field/lock0へ復帰。battle_flags4/outcome1とwire field:falseの残留を未復帰や追加勝利にしない。

26〜30通常menu0→4、31確認/32上書き、33〜45保存中。45counter57でも部分write、46〜49成功文言/安定Flash、50field。cold0/1の120frame後まで全SaveRTC/人物と床の暗所field全byte一致。

## 限定差分と未完

全party600bytesの差分はslot3 PPの1byteだけ。HP/EXP/held item/残partyを保持。全Bag/17904円/RP0、全legacy flags、PC/S61E全payloadと旧Save56bank57344byte保持。42checksum、7030byte/1731範囲。aux4021=25→38/4022=4→0のruntime owner未解明。RAMledgerは向きを北に変えた観測3で変化し、その後coldまで939b183a...を保持するがowner未解明。過去台帳/offset41/2056/aux/40ac未解明も保持。

全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。一般CIの既知不一致/action_requiredを成功にしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save56']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37153775959');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='73261d17c77f56ad4e2fcc80a8cac30d9af21e6e','旧Stage79終端')
    state['story_save56']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save57']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,59],xy=[19,13],facing=2,rp=0,money=17904,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[15,10,15,13],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,trainer_victories=0,wild_victories=1,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),prior_failed_inert_warp=failed,next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='着地点warp誤仮定を訂正。別経路13歩/野生1勝/Save57。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='館内13歩/新野生1勝/Save57。次は有効階段30,10への残り経路。上階/紙未到達。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_EFFECTIVE_STAIRS_FROM_SAVE57',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save57_accept.py','scripts/pr16_story_save57_measure.py',a.EVIDENCE+'/inspection.json','content/modernization/pr16_story_save57_preparation.json','content/modernization/pr16_story_save56_preparation.json'],stop_rule_ja='Save57だけから19,13以降の保存済ROUTE接尾辞へ。20,24の着地点を発火warpとして再走しない。有効階段30,10を目標に最初の新event/戦闘/未通過境界で保存。野生1勝/旧区間は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='こころのやかた入口階13歩/野生1勝でSave57。19,13北。着地点warp不発を訂正し、次は有効階段30,10への残り経路。'
    state['do_not_repeat'].append('Save57の93/cold13入力53画面69member/51受入を無影響再走しない。warp8の誤仮定は未保存16入力3画面/native1、影響3試験だけ訂正。野生1勝/PP14→13、45counter部分write→46成功→50field。紙/上階未到達、RAM台帳/aux owner未解明。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE|extra)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 館内の新野生1勝とSave57
- Version: story-mansion-wild-save57-v1
- Status: DONE（新13歩/野生1勝/保存/独立Continue限定）
- Summary: 有効階段への別経路13歩、バーニン♀Lv9へ1勝。HP288/294・つばめがえしPP14→13、全他party/Bag/17904円/RP0を保持。19,13北で保存、上階/紙未到達。
- Files changed: Save57 inspect/measure/27controller/51受入/record、15node1444cell静的原本、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。93+cold13入力53画面69member。controller25原log+影響3件、51新受入拒否試験。record native0/compile0/既受入再走0。
- Prior failure: run37154589799/job111295266609の16入力3画面/native1は床behavior8上の着地点warp8を発火すると誤仮定。未保存安全停止/Save56全byte不変、原本artifact11285188296保持。同じ北歩行を繰り返さずbehavior108階段経路に訂正。
- Evidence: party599byte/HP/EXP/持物/全Bag/legacy flags/PC/S61E保持、PP1消費だけ。45counter部分write→46成功→50field、全SaveRTC/暗所3画面一致。RAMledger観測3とaux2変数owner未解明。旧bank57344byte/42checksum/7030byte1731範囲。
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

