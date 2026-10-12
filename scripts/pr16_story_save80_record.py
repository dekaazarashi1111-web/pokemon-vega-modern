#!/usr/bin/env python3
"""第4ディグダ配置変更・Save80原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save80_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-GYM-FOURTH-DIGLETT-SAVE80'
OUT=ROOT/'.local/pr16-story-save80-record'

CODE={'scripts/pr16_story_save80_accept.py','scripts/pr16_story_save80_record.py','tests/test_pr16_story_save80_accept.py',a.VISUAL,'content/modernization/pr16_story_save80_next_route.json','.github/workflows/pr16-story-save80-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE80_JA.md' and a.CP=='content/modernization/pr16_story_save80_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save80_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37174510738,'21176a3cb8b045c944214fdee13494a785a46c55',111354226537,['success']*11)
    first_done=inherited.terminal(37174805490,'b744cf8cfeab4eb62ec0806e448c8e55cd141127',111355112045,['success','success','failure','skipped','skipped','failure','success','success'])
    test_receipts=[]
    for job,count,total,ending in [(111355112045,30,31,'FAILED (failures=1)'),(a.JOB,1,1,'OK')]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save80_measure.' in v]
        need(len(lines)==count and any(f'Ran {total} test'in v for v in log)and any(v.endswith(' '+ending)for v in log),'controller原logを成功30+修正1に分離')
        if job==111355112045:need(any('test_unexpected_early_event_stops' in v and ' ... FAIL' in v for v in log),'失敗1件を保持')
        test_receipts.append(dict(job=job,passed_tests=count,executed_tests=total,failed_tests=total-count,test_lines=lines,replayed_passed_tests=0))
    old_test=h.d.git('show','b744cf8cfeab4eb62ec0806e448c8e55cd141127:tests/test_pr16_story_save80_measure.py')
    need(old_test.replace(b"('new_event',[9,12],4)",b"('new_event',[9,12],6)")==(ROOT/'tests/test_pr16_story_save80_measure.py').read_bytes(),'変更影響は失敗テスト期待値だけ。30成功再走0')
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==50 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save79全50member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save79/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==56 and len(z.namelist())==57 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save80member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==41 and visual['reviewed_screens']==dict(progress=list(range(39)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save80画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save80画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE80_ORIGINAL=str(original),PR16_SAVE79_INPUT=str(assets/'input.srm'),PR16_SAVE80_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save80_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==56 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 56 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'56成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save79-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'failed-controller-terminal.json',dict(terminal=first_done,native_processes=0,accepted=False,reason_ja='テスト側早期event期待4入力が誤り。実際6入力を正とし失敗1件だけ再検証。成功30件再走0。'))
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save80 artifact11292349565のstory-fast.srm（131088bytes/SHA256 6083038273bdf89de7563800c91a215c861552e7fc4da71af7c4a3c3237580dc）だけから再開。ミルジム10/16・3,9西。local9通常Aで4375 set・4372/4374 clear、local9消失・local5/8復帰を保存ownerで受入。local5全体は画面下端で見えない。次は保存next-routeの東3歩で6,9、北旋回→local10/6,8へA。4372/4373/4374=false・4375=true分岐は4376 set/remove10・4375 clear/add9。最初の新event/battle後通常保存。全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持、S61E payload258:87→135の3flagだけ。74+cold13入力41画面56member/native2、新controller31（初回30成功/1失敗、修正1のみ成功。計32実行）/56新受入。34counter80でも保存中/最終hash未達→35最終hash/成功文言→38field。全SaveRTC/field全pixel一致。progress19menuでRAM台帳60276271→e9f829d5、以後/cold保持。今回/過去RAMとaux4021:97→107のowner未解明。紙consumerは博物館2階local2・badge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save80_accepted=True,fourth_diglett_event_accepted=True,gym_puzzle_completed=False,required_badge_flag=2083,required_badge_present=False,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=31,controller_executions=32,controller_failed_executions=1,controller_repaired_cases=1,unchanged_controller_cases_replayed=0,new_acceptance_tests=56,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 第4ディグダ配置変更・Save80限定受入

`{result['status']}`。Save79のジム10/16・9,13北から北2/西6/北2の新10歩、西/北/西3旋回、local9/2,9への通常A。台詞2本とlocal9消失・local5/8再出現、4375 set・4372/4374 clearを確認。3,9西で通常Save80/独立Continue。新戦闘0、ジム突破は未受入。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。56member/41画面/74+cold13入力。新controller31/新受入56。初回run37174805490は30成功/1失敗でnative未起動、期待入力数4→6を訂正して失敗1件だけ成功。計32実行、成功30件再走0。native2/record0/旧成功再走0/ROM変更0。

## 第4ownerと観測

保存済gym graphの47命令/2台詞を再利用。4372/4374=true分岐はset4375/remove9・clear4372/add5・clear4374/add8。全域再scanなし。0開始、1〜2北2歩、3西旋回、4〜9西6歩、10北旋回、11〜12北2歩、13西旋回。14話しかけた台詞、15配置変更、16field。local9除去/local8復帰は13/16原画、local5は下端で頭部のみなので全体目視を主張せず保存flagとownerで照合。17〜21通常menu0→4、22確認/23上書き、24〜34保存中、34counter80でも最終hash未達、35最終hash/成功文言、38field。counterだけで完了としない。

全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持。physical flags全保持、S61E payload258:87→135の3flagだけ。aux4021:97→107のruntime ownerは未解明。42checksum/7132byte1831範囲、旧Save79bank57344byte保持。

全SaveRTCとprogress38/cold0/cold1全pixel一致。progress19menu中のRAM台帳60276271→e9f829d5を明示、以後/coldでは保持。今回/過去RAM差分owner未解明。後続開始定数はSave80のcold0と一致。

## 次

[local10への新東3歩とowner](../content/modernization/pr16_story_save80_next_route.json)。local5/6/8/9の旧入力は再走しない。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save79']['record_completion']=prior_done
    state['story_save80']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[10,16],xy=[3,9],facing=3,rp=0,money=19416,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],fourth_diglett_event_accepted=True,gym_puzzle_completed=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='第4ディグダ通常配置変更とSave80。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='第4local9で4375 set・4372/4374 clear、Save80/3,9西。全SaveRTC/field全pixel保持。menu19のRAM差分/aux4021 owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_GYM_FIFTH_DIGLETT_FROM_SAVE80',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save80_accept.py','scripts/pr16_story_save80_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save80_preparation.json','content/modernization/pr16_story_save80_next_route.json'],stop_rule_ja='Save80/ジム3,9西だけから開始。東旋回/新東3歩で6,9、北旋回→local10へA。最初の新境界で通常保存。local5/6/8/9の旧入力再走0。badge/紙引渡しを捏造しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='第4local9除去・local5/8復帰、Save80/3,9西。全party/紙保持。次はlocal10。menu19のRAM台帳差分owner未解明。'
    state['do_not_repeat'].append('Save80の74/cold13入力41画面56member/31controller計32実行/56受入を無影響再走しない。local9で4375 set・4372/4374 clear。34counter80でも保存中/未finalhash→35最終hash/成功→38field。全SaveRTC/全pixel/全party保持。menu19RAM台帳差分owner未解明。初回native0/30成功1失敗→失敗1件だけ再検証、既成功30再走0。次はlocal10へ新東3歩。旧gym graph再採取0。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 第4ディグダ配置変更・Save80
- Version: story-gym-fourth-diglett-save80-v1
- Status: DONE（第4配置変更/通常保存/独立Continue限定）
- Summary: 新10歩・西/北/西3旋回とlocal9通常A。4375 set/local9消失、4372/4374 clear/local5/8復帰を固定owner/保存flagで照合。local5は画面下端で一部だけ、全体目視を主張しない。3,9西のSave80、全party600byte/HP288/PP9,10,15,2/Bag19416円/紙/PC保持。
- Files changed: Save80 preparation/measure/31controller/56受入/record/checkpoint/text証拠/次local10 owner、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。74+cold13入力41画面56member。新controller31（初回30成功/1失敗→修正1のみ成功、計32実行）原log継承/新受入56。record native0/compile0/旧成功再走0。
- Evidence: 24〜34保存中→34counter80/未finalhash→35最終hash/成功文言→38field。全SaveRTC/field全pixel/party保持。42checksum/7132byte1831範囲。S61E3flagsだけ。progress19menu RAM台帳60276271→e9f829d5、以後/cold保持。今回/過去RAMとaux4021 owner未解明、紙引渡し/ジム攻略未受入。
- Discovery: 保存済gym graphの第4限定47命令/2台詞を再利用。次local10の4372/4373/4374=false・4375=true分岐と新東3歩を保存。全map再scan0。Save79記録run37174510738全11step終端を同期。
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




