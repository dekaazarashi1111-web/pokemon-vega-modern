#!/usr/bin/env python3
"""町北connection Save98を原本から独立受入し固定引継ぎ/両ログを記録。native0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT),str(ROOT/'tests')]
import pr16_story_save98_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-ROUTE505-SAVE98';OUT=ROOT/'.local/pr16-story-save98-record'
CODE={'scripts/pr16_story_save98_accept.py','scripts/pr16_story_save98_record.py','tests/test_pr16_story_save98_accept.py',a.VISUAL,a.OWNER,'content/modernization/pr16_story_save98_next_route.json','.github/workflows/pr16-story-save98-record.yml'}
FAIL_RUN,FAIL_JOB,FAIL_SOURCE,FAIL_ART=37195233466,111415610355,'c8312b3a0d7ddacb42825f9a60140612bce34eb3',11301280087
FAIL_ARCHIVE=json.loads((ROOT/a.m.RECOVERY).read_bytes())['archive']
PREFLIGHT_RUN,PREFLIGHT_JOB,PREFLIGHT_SOURCE,PREFLIGHT_ART=37195440238,111416217704,'cc0cf58afb9824b60d81b80249ad9f6b91232b18',11301235609
PREFLIGHT_ARCHIVE=json.loads((ROOT/'content/modernization/pr16_story_save98_preflight_failure.json').read_bytes())['archive']
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
    rows=[]
    for job,executed in[(FAIL_JOB,42),(PREFLIGHT_JOB,16),(a.JOB,1)]:
        raw=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode();log=raw.splitlines();lines=[v.split('Z ',1)[-1]for v in log if' ... 'in v and'test_pr16_story_save98_measure.'in v]
        need(len(lines)==executed and all(v.endswith(' ... ok')for v in lines),'新controllerの成功原本行のみ再読')
        need(any('Ran '+str(executed)+' test'in v for v in log),'unit終端')
        rows.append(dict(job=job,executed=executed,passed=executed,failed=0,test_lines=lines))
    import test_pr16_story_save98_measure as tests
    need(unittest.defaultTestLoader.loadTestsFromModule(tests).countTestCases()==46,'最終controller46case。loadのみ再走0')
    return dict(final_cases=46,executions=59,passed_executions=59,failed_executions=0,unchanged_success_reruns=0,phases=rows,scope_ja='初回42成功。party位相変更の影響13と新3を16成功。bytes型契約修復で新1のみ成功。native失敗1とpre-native失敗1を保存。')

def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists()and not(ROOT/a.CP).exists(),'新記録1回だけ')
    need(a.GUIDE=='docs/PR16_STORY_SAVE98_JA.md'and a.CP=='content/modernization/pr16_story_save98_checkpoint.json','今回専用宛先固定')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need({a.GUIDE,a.CP}.isdisjoint(protected)and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入を書き換えない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37194679580,'783714626e892c2b4e11305007da811755554814',111413969510,['success']*11)
    failed_terminal=inherited.terminal(FAIL_RUN,FAIL_SOURCE,FAIL_JOB,['success','success','success','failure','skipped','success','success','success'])
    preflight_terminal=inherited.terminal(PREFLIGHT_RUN,PREFLIGHT_SOURCE,PREFLIGHT_JOB,['success','success','success','failure','skipped','success','success','success'])
    controller=controller_receipt()
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        mf=json.loads(z.read('manifest.json'));need(len(mf)==61 and set(z.namelist())==set(mf)|{'manifest.json'},'親Save97全61member')
        for n,b in mf.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save97/不変ROM')
    original=OUT/'original';meta,manifest=unpack_verified(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE,original,84)
    failed=OUT/'failed-approach';failedmeta,failedmanifest=unpack_verified(FAIL_ART,FAIL_RUN,FAIL_ARCHIVE,FAIL_SOURCE,failed,16)
    preflight=OUT/'failed-preflight';premeta,premf=unpack_verified(PREFLIGHT_ART,PREFLIGHT_RUN,PREFLIGHT_ARCHIVE,PREFLIGHT_SOURCE,preflight,2)
    pf=json.loads((preflight/'failure.json').read_bytes());need(pf['native_processes']==0 and pf['message']=='bytes required','型契約失敗native0')
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==69 and visual['reviewed_screens']==dict(progress=list(range(67)),**{'continue':[0,1]})and visual['save_success_wording_observed']is True,'全69原画目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'原画 '+n)
    need(visual['failed_approach_review']['reviewed_progress_screens']==list(range(9)),'失敗9画面も観測')
    result=a.verify(original,before,rom);failure=a.failed_approach(failed)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE98_ORIGINAL=str(original),PR16_SAVE97_INPUT=str(assets/'input.srm'),PR16_SAVE98_ROM=str(assets/'candidate.gba'),PR16_SAVE98_FAILED=str(failed))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save98_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    lines=[v for v in unit.stderr.decode().splitlines()if v.startswith('test_')]
    need(unit.returncode==0 and not unit.stdout and len(lines)==79 and all(v.endswith(' ... ok')for v in lines)and re.search(rb'\nRan 79 tests in [0-9.]+s\n\nOK\n\Z',unit.stderr),'79成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for folder,prefix in[(original,''),(failed,'failed-approach/'),(preflight,'failed-preflight/')]:
        for p in sorted(folder.rglob('*')):
            if not p.is_file()or p.suffix not in{'.json','.txt'}:continue
            raw=p.read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ');dest=evidence/(prefix+p.relative_to(folder).as_posix());dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr);write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'failed-approach-terminal.json',failed_terminal);write(evidence/'failed-approach-verification.json',failure);write(evidence/'failed-preflight-terminal.json',preflight_terminal)
    write(evidence/'controller-test-receipt.json',controller);write(evidence/'next-route.json',a.next_route());write(evidence/'walk-owner.json',h.d.read(ROOT/a.OWNER))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    rule=a.next_route()['transition_preflight_rule_ja']
    goal='Save98 artifact11300996343のstory-fast.srm（131088bytes/SHA256 af8190f911ef0e182b22860531c8d0f1a160a57556600a16044edcfca8553cec）だけから再開。505番道路3/23・28,39北。町北35歩/6旋回/通常北connection1歩、通常Save98/独立Continueを限定受入。次はRangerの静的初期位置18,27へ向かう61歩候補。未戦闘pair1113/physical1282は未勝利、local3/8の移動範囲と全方向視界過大近似を避ける。1054/1055のphysical1406/1407は勝利済み。最初の草32,31は12歩目、未知wild/trainer/NPC eventで縮小停止。Rangerはmovement2/range2で動くため、18,28での北Aを盲目的に送らず実object/画面を確認する。会話は後続。段差32,14/22,20はbehavior42/高度0で別途preflight。町/博物館/封書/受付の成功区間再走なし。HP277/294/PP3,9,8,2/ミュウツー全HP/PP/23114円/4061/紙274=0/4382/4383/バッジ2/PC/S61E保持。party600byteの597保持、raw41/141/241各+1を通常saveで確認。固定ROMの歩行friendship event5/field32→raw41と4021mod128/4022mod5を解決、122+36→30、4+36→0。個々の乱数branchのPC trace未採取。過去offset41/歩数変数の原本は保持し本証拠へ参照、全過去実行を再traceしたとしない。RAM観測42とphysical2056等は別の未解明。現counter30、次friendship周期まで98歩。69画面128+cold13入力、62counter98/最終hash/空白→63成功文言→66clearfield。progress/cold雪6粒128pixel差、cold間全pixel一致。初回partyguard失敗1/native1/Save97保持とpreflight型失敗1/native0を保存。controller最終46/59実行成功、新受入79、成功native2/失敗native1/記録native0/旧成功再走0。全国図鑑/自然成長進化/全story/release未受入。ROM/runtime非再配布、ROM変更/host補充/merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。'+rule
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save98_accepted=True,town_north_connection_accepted=True,letter_handoff_accepted=True,visual_review=a.VISUAL,walk_owner=a.OWNER,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=46,controller_executions=59,controller_passed_executions=59,controller_failed_executions=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=79,successful_native_processes=2,prior_failed_native_processes=1,prior_pre_native_failed_attempts=1,total_native_processes=3,record_native_processes=0,failed_approach_artifact={k:failedmeta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},failed_approach_verification=failure,next_goal_ja=goal,transition_preflight_rule_ja=rule,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f'''# 町北connection・Save98限定受入

`{result['status']}`。Save97から町の新35歩/6旋回、北端28,0で通常北入力、505番道路3/23・28,39北の最初fieldでSave98/独立Continue。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。84member/69画面/128+cold13入力。controller最終46case/59実行成功、新受入79。成功native2/失敗native1/preflight失敗1/記録native0/旧受入再走0。

## 境界と保存

固定ROMの両側behavior0x21=SAND、衝突0、相互direction2/1、offset0。warp/矢印/方向階段ではない。観測41が北端画面、42で505番道路へ通常connection。自動追加入力なし。43〜47menu0→4、48/49確認、50〜61保存中。62counter98/最終hashでも文言は空白、63成功文言、66clearfield。

66→cold0/1は128pixel差で雪粒子6矩形だけ。cold0/1間は全pixel一致。全SaveRTC131088byte/PC/S61E/旧Save97bank57344byte保持。全save差分7074byte1780範囲/42checksum。

## 歩行ownerの限定解決

[固定ROM証拠](../{a.OWNER})。0x806cf40は4021を+1&127、0時に6体へevent5/AdjustFriendship。0x806cf90は4022を+1 mod5。0x8042db8はfield32のfriendshipを読み書きし、Get/Set handler0x803f74a/0x803fea4はsubstruct0+9、この候補の順序固定substruct0=mon+32なのでraw41。固定上流のVAR_HAPPINESS_STEP_COUNTER/VAR_POISON_STEP_COUNTERと一致。

Save97のcounter122から6歩目（観測8）でraw41/141/241が48→49/13→14/111→112。通常保存の600byte差も同じ3byteだけ、597byte保持。総36歩で4021=(122+36)%128=30、4022=(4+36)%5=0。HP/PP/EXP/持物保持。4体目raw341=65保持。共通機構はsourceと固定ROMとsave算術で照合したが、個別乱数分岐のPC traceは未採取。過去原本を書き換えず、同fieldの意味だけを後続証拠として参照する。過去全実行を再traceした主張はしない。RAM観測42/physical2056等の別ownerは未解明。

## 失敗履歴

run37195233466/job111415610355は初回42controller成功後、6歩目のparty hash guardでnative停止。artifact11301280087、9画面28入力、通常save0、Save97全byte保持。診断600byteの上記3byteだけのpreimage SHAが一致し、位置/位相限定で復旧した。

run37195440238/job111416217704は影響16controller成功後、診断bytearrayをbytes-only identityへ渡してpre-native停止。artifact11301235609、native0。identity guardは緩めずbytesへ確定、新契約1caseだけ検査。これらを成功へ換算しない。

## 次

[61歩の静的候補](../content/modernization/pr16_story_save98_next_route.json)。未戦闘pairの視界過大近似を避け、既勝利1054/1055は再戦しない。12歩目32,31から草地がある。Ranger local9はmovement2/range2で動く。未知event/野生戦で縮小停止し、会話は実object/画面確認後の別区間。高度0/behavior42の段差もpreflightする。現happiness30で次周期まで98歩。

{goal}
'''
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本不変')
    state['story_save97']['record_completion']=prior_done
    state['story_save98']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[3,23],xy=[28,39],facing=2,rp=0,money=23114,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],town_north_connection_accepted=True,museum_admission_var4061=1,letter_handoff_accepted=True,paper_quantity=0,paper_flag4383=True,paper_flag4382=True,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',walk_owner=a.OWNER,next_goal_ja=goal,failed_approach=failure,transition_preflight_rule_ja=rule)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='町北35歩と通常北connectionのSave98。歩行friendship/4021/4022共通ownerを固定ROMで解決し旧原本は保持。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='町北connection Save98/505番道路3/23・28,39北。69画面128+cold13入力。597partybyte保持/歩行friendship3byte+1、HP/PP/23114円/4061/4382/4383保持。4021/4022共通歩数owner解決、個別乱数PCtrace未採取。RAM観測42/2056等未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stop='Save98からRangerへ61歩静的候補、未戦闘pairを避け最初の未知NPC/戦闘/eventで縮小停止。12歩目32,31から草、Ranger位置は動く。会話/warpは後続。町35歩/博物館/封書/受付再走なし。'+rule
    state['next_action'].update(id='STORY_RANGER_APPROACH_FROM_SAVE98',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,a.OWNER,'scripts/pr16_story_save98_accept.py','scripts/pr16_story_save98_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,a.m.RECOVERY,'content/modernization/pr16_story_save98_next_route.json'],stop_rule_ja=stop)
    state['do_not_repeat'].append('Save98の128/cold13入力69画面84member、新35歩/6旋回/通常北connection、controller最終46case/59成功、新受入79を無影響再走しない。partyguard失敗1/9画面/Save97保持とpreflight型失敗1/native0を保存。歩行friendship/4021/4022共通機構はSave98 walk_ownerを参照。旧原本は保持。'+rule)
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='Save98/505番道路3/23・28,39北。HP277/PP3,9,8,2/23114円/4382/4383/4061保持。friendship3byteと4021/4022共通歩数owner解決、個々の乱数PCtrace未採取、RAM42/2056未解明。次Rangerへの草/段差/動的NPC。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'''
## {stamp}
- Version: PR16-STORY-SAVE98
- Timestamp: {stamp}
- Task: {TASK} / 町北connectionとSave98
- Status: DONE（505番道路最初field/保存/独立Continue限定、Ranger会話は未到達）
- Summary: 新35歩/6旋回/通常北connectionで505番道路28,39北。通常Save98/Continue。HP277/PP3,9,8,2/23114円/4061/4382/4383/PC/S61E保持。
- Files changed: Save98 measure/controller/失敗原本/位置限定復旧/受入79/record/checkpoint/text証拠/歩行owner/次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。128+cold13入力69画面84member。controller最終46case/59成功、新受入79。成功native2/失敗native1/preflight失敗1/記録native0/compile0/旧成功再走0。
- Evidence: 北端41→道路42。62counter98/最終hash/文言空白→63成功文言→66clearfield。progress/cold差128pxは雪6粒、cold間全pixel一致。42checksum/7074byte1780範囲/全SaveRTC/旧bank保持。
- Owner: 固定ROM0x806cf40の4021mod128/event5、0x806cf90の4022mod5、0x8042db8のfriendship field32、getter0x803f74a/setter0x803fea4→raw41。600byte中597保持、41/141/241各+1を通常save照合。122+36→30/4+36→0。個別乱数PCtraceなし、過去原本改作なし。RAM42/2056等は未解明。
- Recovery: 初回42検査成功後partyguardでSave97無変更停止。影響16検査成功後bytearray型契約でnative0停止。bytes確定/新1検査だけ修復。失敗原本を保持。Save97記録run37194679580の全11stepを同期。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repoGitHub/Actions、source-lock固定pret/pokefirered c75f3523のfield/pokemon/constants、PyPI capstone5.0.6の読取専用Thumb診断。入力ROM/runtime非再配布、ROM変更/merge/release/baseline変更0。一般CI既知不一致を全成功にしない。
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

