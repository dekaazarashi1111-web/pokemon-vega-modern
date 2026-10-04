#!/usr/bin/env python3
"""封書引渡し・Save95原本を独立受入し固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save95_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-LETTER-HANDOFF-SAVE95'
OUT=ROOT/'.local/pr16-story-save95-record'
CODE={'scripts/pr16_story_save95_accept.py','scripts/pr16_story_save95_record.py','tests/test_pr16_story_save95_accept.py',a.VISUAL,'content/modernization/pr16_story_save95_next_route.json','.github/workflows/pr16-story-save95-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists()and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE95_JA.md'and a.CP=='content/modernization/pr16_story_save95_checkpoint.json'and a.EVIDENCE=='content/modernization/pr16_story_save95_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected)and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37190224812,'037236ba10f1e531eeade211f69e6732734d2ae4',111400657915,['success']*11)
    failed_done=inherited.terminal(37190678835,'fd9ce64230317b5607967c68445dcb109dcbfd4e',111402001558,['success','success','success','failure','skipped','success','success','success'])
    test_receipts=[]
    for job,total in [(111402001558,39),(a.JOB,9)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines();lines=[v.split('Z ',1)[-1]for v in log if' ... 'in v and'test_pr16_story_save95_measure.'in v]
        need(len(lines)==total and all(v.endswith(' ... ok')for v in lines)and any(('Ran '+str(total)+' tests')in v for v in log)and any(v.endswith(' OK')for v in log),'初回39と変更影響9の原log成功終端')
        test_receipts.append(dict(job=job,passed_tests=total,executed_tests=total,failed_tests=0,test_lines=lines,replayed_unchanged_passed_tests=0))
    _,z=a.transport.archive(11299056405,37190678835,dict(size=85226,sha256='bd9a735b967bf13fbed0fbafef931b132d81db3293d91b564571e34bb7d47666'),'fd9ce64230317b5607967c68445dcb109dcbfd4e')
    with z:
        fm=json.loads(z.read('manifest.json'));need(len(fm)==28 and set(z.namelist())==set(fm)|{'manifest.json'},'失敗原本全28member')
        for n,b in fm.items():need(identity(z.read(n))==b,'失敗member '+n)
        f=json.loads(z.read('failure.json'));e=json.loads(z.read('progress/execution.json'))
        need(f['native_processes']==1 and f['message']=='最初のlocal2会話を観測'and e['initial_save']==e['final_save']==a.m.a.OUTPUT and e['observations']==21 and e['native_end']['inputs']==52,'失敗native1/保存0/Save94全保持')
        failed_text={n:z.read(n)for n in z.namelist()if Path(n).suffix in('.txt','.json')}
    history=dict(native=dict(terminal=failed_done,artifact=11299056405,archive=dict(size=85226,sha256='bd9a735b967bf13fbed0fbafef931b132d81db3293d91b564571e34bb7d47666'),failure=f,execution=e,accepted=False,ordinary_saves=0,reason_ja='local2はROM movement type5左右移動。初期4,9を会話時座標と誤仮定し初Aで会話なし、安全停止。原画128内部pixelの左右spriteを正面で2回連続確認する待機へ限定修正。初回failure結論は保持。'),controller_executions=48,controller_passed_executions=48,controller_failed_executions=0,final_controller_cases=46,changed_controller_cases_retested=2,unchanged_success_reruns=0)
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==56 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save94全56member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save94/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==81 and len(z.namelist())==82 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save95member')
        need(all(Path(n).suffix in{'.srm','.ppm','.txt','.json'}and not n.startswith('/')and'..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==66 and visual['reviewed_screens']==dict(progress=list(range(64)),**{'continue':[0,1]})and visual['save_success_wording_observed']is True,'全66原画目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE95_ORIGINAL=str(original),PR16_SAVE94_INPUT=str(assets/'input.srm'),PR16_SAVE95_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save95_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    lines=[v for v in unit.stderr.decode().splitlines()if v.startswith('test_')]
    need(unit.returncode==0 and not unit.stdout and len(lines)==69 and all(v.endswith(' ... ok')for v in lines)and re.search(rb'\nRan 69 tests in [0-9.]+s\n\nOK\n\Z',unit.stderr),'69成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in['measurement.json','manifest.json','save94-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ');dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr);write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'failure-history.json',history)
    for name,raw in failed_text.items():
        dest=evidence/'failed-native'/name;dest.parent.mkdir(parents=True,exist_ok=True);raw.decode();need(b'\0'not in raw,'失敗textだけ');dest.write_bytes(raw)
    write(evidence/'controller-test-receipt.json',test_receipts);write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save95 artifact11298657664のstory-fast.srm（131088bytes/SHA256 7a23bd41f4c9131b3abc4dee4d9efd974ca9e9a681bf78cc835f4c0e3e240fa4）だけから再開。博物館2階6/1・4,8南で封書274を一個引渡し、4382setを通常保存/独立Continueで受入。新13歩/5旋回/障害待ち1、local2の左右移動を原画128pixelで2回確認してから会話、90frame待機/全15dialog。次は新復路13歩で11,8の0x6F方向階段へ、西入力で1階へ初下降し最初のfieldを保存。封書会話/50円受付/旧入館を再走しない。505道路レンジャーは退出後。23114円/4061=1/バッジ2/4383/未完4380/全party600byte/HP277/294/PP3,9,8,2保持。今回RAM差分は会話32、aux4021:83→96/4022:0→3 owner未解明、過去ownerも未解明のまま。66画面118+cold13入力。59counter95でも途中hash/保存中、60成功文言/最終hash→63clearfield。cold間1023pixel差分は3人NPCだけ、全画面一致とは主張しない。全SaveRTC/PC保持、S61Eは4382bitだけset。初回失敗native1/52入力21画面/Save94全保持、通常保存0。controller39+影響9=48成功実行/最終46case、影響ある旧2だけ再検査、無影響再走0。新独立受入69/成功native2/記録native0。全国図鑑/自然成長進化/全story/release未受入。ROM/runtime非再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save95_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=0,museum_admission_var4061=1,museum_second_floor_accepted=True,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,required_badge_flag=2083,required_badge_present=True,paper_consumed_or_delivered=True,letter_handoff_accepted=True,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=46,controller_executions=48,controller_passed_executions=48,controller_failed_executions=0,controller_repaired_cases=2,unchanged_controller_cases_replayed=0,new_acceptance_tests=69,successful_native_processes=2,prior_failed_native_processes=1,prior_pre_native_failed_attempts=0,total_native_processes=3,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 封書引渡し・Save95限定受入

`{result['status']}`。Save94の博物館2階11,8東から新13歩/5旋回/一時通行待ち1、4,8南でlocal2へ封書274一個を通常引渡し。Bag slot4は274x1→空、S61E payload259は160→224で4382だけset。4383とバッジ2/全party600byte/HP277/PP3,9,8,2/23114円/4061=1/PC保持。通常Save95と独立Continueを受入。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。81member/66画面/118+cold13入力。controller最終46case、39+影響9=48成功実行。初回39のうち変更影響2だけ再検査/無影響成功再走0。新独立受入69。成功native2/未保存失敗native1/記録native0。

## 移動NPCと失敗履歴

run37190678835は21画面52入力/native1/通常保存0/Save94全保持。local2は初期座標4,9から左右へ歩くmovement type5で、最初A時は5,9にいた。元failure結論と全原画を保持。固定ROMのobject24byteとsource-lockのmovement enumを照合し、失敗原画19の内部128pixelを抽出、左右向きspriteのいずれかが正面4,9へ来るまで決定しない待機へ限定修正。成功19/20は未到着、21/22で連続確認し、90frame待機後23で会話開始。RAM座標書換えやNPC固定はしない。

## 会話・保存・境界

23「それはだいじなふうしょ」から37まで全15dialog。506前のダグトリオと505道路レンジャーへの案内を確認。38で最初fieldへ復帰して保存。39〜43menu0→4、44/45確認、46〜59保存中。59counter95でも部分hash/保存中文字、60最終hash/成功文言、63overlayなしfield。cold0/1も4,8南field。全131088byteSaveRTCはcold/120frame後保持。

63→cold0/1は744/920pixel、cold間1023pixel差。全差分はNPC3人の矩形x48..63/y45..70、x101..132/y83..102、x193..206/y1..38内のみ。主人公/地形は保持するが全画面一致は主張しない。Save差分7064byte1772範囲、42checksum、旧Save94bank57344byte保持。

RAM台帳は会話中32で変化しowner未解明。physical全保持、aux4021:83→96/4022:0→3 owner未解明。紙消費/4382のscript ownerとは別。過去Save94のRAM10/2056/3vars、Save93/92/91/89/87等も未解明のまま。全国図鑑/自然成長進化/全story/releaseは未受入。

## 次

[新復路13歩と下降階段](../content/modernization/pr16_story_save95_next_route.json)。4,8南から11,8へ新復路、0x6Fの西入力で1階へ初下降し最初fieldで保存。次の到達は静的候補だけで未受入。封書会話/受付/旧入館を繰り返さず、館退出後に505道路レンジャーへ進む。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save94']['record_completion']=prior_done
    state['story_save95']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[6,1],xy=[4,8],facing=1,rp=0,money=23114,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=0,museum_admission_var4061=1,museum_second_floor_accepted=True,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_quantity=0,paper_flag4383=True,paper_flag4382=True,paper_consumed_or_delivered=True,letter_handoff_accepted=True,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='新13歩と移動NPCへの通常封書引渡し、Save95/独立Continue。未保存失敗native1はfailure保持。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='封書引渡しSave95/6/1・4,8南。274一個消費/4382set、party600byte/23114円/4383/4061保持。新13歩/旋回5/全66画面。59counter部分hash→60成功→63clearfield。coldNPC3人の差分を限定記録、全SaveRTC保持。RAM32/aux2vars/過去owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MUSEUM_RETURN_STAIRS_FROM_SAVE95',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save95_accept.py','scripts/pr16_story_save95_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,'content/modernization/pr16_story_save95_next_route.json'],stop_rule_ja='Save95/2階4,8南から新復路13歩で11,8の0x6F階段へ。西入力で1階へ初下降し最初のfieldで保存。封書会話/受付/旧入館の再走なし。未知NPC/障害/eventで縮小停止。505道路レンジャーは退出後。')
    state['do_not_repeat'].append('Save95の118/cold13入力66画面81member、controller39+影響9=48成功実行/最終46case、受入69を無影響再走しない。新13歩/旋回5/障害待ち1、移動local2をsprite128pixelで2回確認して封書274消費/4382set。59counter途中hash保存中→60成功最終hash→63clearfield。cold3人NPC1023pixel差/全SaveRTC保持。RAM32/aux2varsと過去owner未解明。初回未保存native1/Save94全保持はfailure。次は新復路13歩と西方向下降。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='封書引渡しSave95/6/1・4,8南。274消費/4382set、23114円/4061/全party/HP277/PP3,9,8,2保持。RAM32/aux2varsと過去owner未解明。次は新復路13歩/西入力下降。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    entry=f"""
## {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Version: PR16-STORY-SAVE95
- Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Task: {TASK} / 封書引渡しとSave95
- Status: DONE（新13歩/通常引渡し/保存/独立Continue限定、505レンジャー未到達）
- Summary: 2階4,8南からlocal2へ封書274x1引渡し/4382set。全party600byte/HP277/PP3,9,8,2/バッジ2/23114円/4061/4383/PC保持。
- Files changed: Save95 measure/controller最終46case/実画面predicate/受入69/record/checkpoint/text証拠/失敗履歴/次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。118+cold13入力66画面81member。controller48成功実行/影響2再検査/無影響再走0、新受入69。成功native2/失敗native1/記録native0/compile0。
- Evidence: 46〜59保存中/59counter部分hash、60成功文言/最終hash、63clearfield。coldNPC3人1023pixel差/全SaveRTC保持。全42checksum/7064byte1772範囲/旧bank保持。
- Discovery: 初回native1/21画面52入力、local2の初期座標をruntime座標と誤仮定して会話なし停止。全Save94保持。ROM movement5/原画128pixelを照合し90frame待機/連続2回確認後会話。RAM32/aux2varsと過去owner未解明。Save94記録run37190224812全11step終端同期。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repoGitHub/Actions。source-lockのpret/pokefirered commit c75f352304d529f6ba92d4f74b9cf8b5c3810788: include/constants/event_object_movement.h、src/field_control_avatar.c#L923-L943、include/constants/metatile_behaviors.h。movement5左右移動と0x6F西方向predicateの一次source参照。入力ROM/runtime非再配布、ROM変更/merge/release/baseline変更0。一般CI既知不一致は全成功にしない。
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
