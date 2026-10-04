#!/usr/bin/env python3
"""第3ディグダ配置変更・Save79原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save79_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-GYM-THIRD-DIGLETT-SAVE79'
OUT=ROOT/'.local/pr16-story-save79-record'

CODE={'scripts/pr16_story_save79_accept.py','scripts/pr16_story_save79_record.py','tests/test_pr16_story_save79_accept.py',a.VISUAL,'content/modernization/pr16_story_save79_next_route.json','.github/workflows/pr16-story-save79-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE79_JA.md' and a.CP=='content/modernization/pr16_story_save79_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save79_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37173950277,'b56cfab419023fc22085cc76c3f946b8edfdc86f',111352536771,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save79_measure.',29)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==49 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save78全49member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save78/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==50 and len(z.namelist())==51 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save79member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==35 and visual['reviewed_screens']==dict(progress=list(range(33)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save79画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save79画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE79_ORIGINAL=str(original),PR16_SAVE78_INPUT=str(assets/'input.srm'),PR16_SAVE79_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save79_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==56 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 56 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'56成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save78-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save79 artifact11292333576のstory-fast.srm（131088bytes/SHA256 88040caadde36a1cbad95bb8e558650089d868d742bba16809a3a32f8ae7553b）だけから再開。ミルジム10/16・9,13北。local8通常Aで4372/4374 set・4375 clear、local5/8消失・local9再出現を全画面/保存ownerで受入。次は保存next-routeの9,12→9,11→3,11→3,9へ新10歩、西旋回→local9/2,9へA。4372/4374=true分岐は4375 set/remove9・4372 clear/add5・4374 clear/add8。最初の新event/battle後通常保存。全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持、S61E payload258:135→87の3flagだけ。62+cold13入力35画面50member/native2、29新controller/56新受入。27最終hashでもcounter78/保存中→28counter79/成功文言→32field。全SaveRTC/field全pixel/今回RAM台帳60276271保持。aux4021:92→97のowner未解明、過去Save77 cold/Save78 progress RAM差分ownerも未解明。紙consumerは博物館2階local2・badge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャーは未完。全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達も未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save79_accepted=True,third_diglett_event_accepted=True,gym_puzzle_completed=False,required_badge_flag=2083,required_badge_present=False,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=29,controller_executions=29,unchanged_controller_cases_replayed=0,new_acceptance_tests=56,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 第3ディグダ配置変更・Save79限定受入

`{result['status']}`。Save78のジム10/16・4,13北から東5歩、東/北2旋回、local8/9,12への通常A。台詞2本とlocal5/8消失・local9再出現、4372/4374 set・4375 clearを確認。9,13北で通常Save79/独立Continue。新戦闘0、ジム突破は未受入。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。50member/35画面/62+cold13入力。新controller29/新受入56。native2/record0/旧成功再走0/ROM変更0。

## 第3ownerと観測

保存済gym graphの43命令/2台詞を再利用。4372/4373=false・4375=true・4376=false分岐はset4372/remove5・set4374/remove8・clear4375/add9。全域再scanなし。0開始、1東旋回、2〜6東5歩、7北旋回、8「めのまえのディグダにはなしかけた」、9「ディグダのはいちがへんかした」、10field。7/10原画で3個体の配置差を確認。11〜15通常menu0→4、16確認/17上書き、18〜27保存中、27最終hash先行、28counter79/成功文言、28〜31成功、32field。27のhashだけで完了としない。

全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持。physical flags全保持、S61E payload258:135→87の3flagだけ。aux4021:92→97のruntime ownerは未解明。42checksum/7068byte1804範囲、旧Save78bank57344byte保持。

全SaveRTCとprogress32/cold0/cold1全pixel一致。今回全progress/coldのRAM台帳60276271保持。Save77 cold/Save78 progressなど過去RAM差分ownerは未解明のまま。後続開始定数はSave79のcold0と一致する。

## 次

[local9への新10歩とowner](../content/modernization/pr16_story_save79_next_route.json)。local5/6/8の旧入力は再走しない。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save78']['record_completion']=prior_done
    state['story_save79']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[10,16],xy=[9,13],facing=2,rp=0,money=19416,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],third_diglett_event_accepted=True,gym_puzzle_completed=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='第3ディグダ通常配置変更とSave79。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='第3local8で4372/4374 set・4375 clear、Save79/9,13北。全SaveRTC/field全pixel/今回RAM台帳保持。過去RAMとaux4021 owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_GYM_FOURTH_DIGLETT_FROM_SAVE79',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save79_accept.py','scripts/pr16_story_save79_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save79_preparation.json','content/modernization/pr16_story_save79_next_route.json'],stop_rule_ja='Save79/ジム9,13北だけから開始。9,12→9,11→3,11→3,9の新10歩、西旋回→local9へA。最初の新境界で通常保存。local5/6/8の旧入力再走0。badge/紙引渡しを捏造しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='第3local8でlocal5/8除去・local9復帰、Save79/9,13北。全party/紙/今回RAM保持。次はlocal9。'
    state['do_not_repeat'].append('Save79の62/cold13入力35画面50member/29controller/56受入を無影響再走しない。local8で4372/4374 set・4375 clear、紙/全party保持。27最終hashはcounter78/保存中→28counter79/成功→32field。全SaveRTC/全pixel/今回RAM台帳保持。過去RAM差分owner未解明。次はlocal9へ新10歩。旧gym graph再採取0。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 第3ディグダ配置変更・Save79
- Version: story-gym-third-diglett-save79-v1
- Status: DONE（第3配置変更/通常保存/独立Continue限定）
- Summary: 東5歩・東/北2旋回とlocal8通常A。4372/4374 setでlocal5/8消失、4375 clearでlocal9復帰を固定owner/原画で照合。9,13北のSave79。全party600byte/HP288/PP9,10,15,2/Bag19416円/紙/PC保持。
- Files changed: Save79 preparation/measure/29controller/56受入/record/checkpoint/text証拠/次local9 owner、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。62+cold13入力35画面50member。新controller29原log継承/新受入56。record native0/compile0/旧成功再走0。
- Evidence: 18〜27保存中→27最終hash/counter78→28counter79/成功文言→32field。全SaveRTC/field全pixel/今回RAM台帳保持。42checksum/7068byte1804範囲。S61E3flagsだけ。aux4021と過去RAM差分owner未解明、紙引渡し/ジム攻略未受入。
- Discovery: 保存済gym graphの第3限定43命令/2台詞を再利用。次local9の4372/4374=true分岐と新10歩を保存。全map再scan0。Save78記録run37173950277全11step終端を同期。
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




