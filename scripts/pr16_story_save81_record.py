#!/usr/bin/env python3
"""第5ディグダ配置変更・Save81原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save81_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-GYM-FIFTH-DIGLETT-SAVE81'
OUT=ROOT/'.local/pr16-story-save81-record'

CODE={'scripts/pr16_story_save81_accept.py','scripts/pr16_story_save81_record.py','tests/test_pr16_story_save81_accept.py',a.VISUAL,'content/modernization/pr16_story_save81_next_route.json','.github/workflows/pr16-story-save81-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE81_JA.md' and a.CP=='content/modernization/pr16_story_save81_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save81_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37175134666,'9f3ce0e818136d0e7175708d4913250d8dfcf955',111356083695,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save81_measure.' in v]
    need(len(lines)==31 and any('Ran 31 tests'in v for v in log)and any(v.endswith(' OK')for v in log),'新controller31の原logを継承・再走しない')
    test_receipts=[dict(job=a.JOB,passed_tests=31,executed_tests=31,failed_tests=0,test_lines=lines,replayed_passed_tests=0)]
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==56 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save80全56member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save80/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==48 and len(z.namelist())==49 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save81member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==33 and visual['reviewed_screens']==dict(progress=list(range(31)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save81画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save81画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE81_ORIGINAL=str(original),PR16_SAVE80_INPUT=str(assets/'input.srm'),PR16_SAVE81_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save81_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==56 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 56 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'56成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save80-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save81 artifact11293356282のstory-fast.srm（131088bytes/SHA256 3beb00ee134983ae76b2e41bdc9d5cdbf76e2d031d3f42d3a07fadb164a07633）だけから再開。ミルジム10/16・6,9北。第5local10通常Aで4376 set/remove10・4375 clear/add9を受入。次は開いたlocal10跡6,8を通って新北2歩6,7へ。local1/3,7のtrainer132・視線距離3・movement10の新event候補で、最初の新戦闘/新境界の後だけ通常保存。発火しなければ6,7で縮小停止し画面確認。旧switchの入力再走0。全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持、S61E2flagsだけ。58+cold13入力33画面48member/native2、新controller31/新受入56。25最終hashでも保存中/counter80→26counter81/成功文言→30field。全SaveRTC/field全pixel/RAM台帳保持。過去Save77/78/80等RAM差分と今回aux4021:107→110・4022:4→2のruntime owner未解明。紙consumerは博物館2階local2・badge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save81_accepted=True,fifth_diglett_event_accepted=True,gym_puzzle_completed=False,required_badge_flag=2083,required_badge_present=False,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=31,controller_executions=31,controller_failed_executions=0,controller_repaired_cases=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=56,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 第5ディグダ配置変更・Save81限定受入

`{result['status']}`。Save80のジム10/16・3,9西から新東3歩、東/北2旋回、local10/6,8への通常A。台詞2本、local10消失/local9復帰、4376 set・4375 clearを確認。6,9北で通常Save81/独立Continue。新戦闘0、ジム突破は未受入。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。48member/33画面/58+cold13入力。新controller31/新受入56。native2/record0/旧成功再走0/ROM変更0。

## 第5ownerと観測

保存済gym graphの39命令/2台詞を再利用。4372/4373/4374=false・4375=true分岐はset4376/remove10・clear4375/add9。全域再scanなし。0開始、1東旋回、2〜4東3歩、5北旋回、6話しかけた台詞、7配置変更、8field。local10除去/local9復帰は5/8原画と保存flagで照合。9〜13menu0→4、14確認/15上書き、16〜25保存中、25最終hashでもcounter80/保存中文言、26counter81/成功文言、30field。最終hashだけで完了としない。

全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持。physical flags全保持、S61E payload258:135→7・259:164→165の2flagsだけ。aux4021:107→110・4022:4→2のruntime ownerは未解明。42checksum/7126byte1827範囲、旧Save80bank57344byte保持。

全SaveRTCとprogress30/cold0/cold1全pixel一致。今回はprogress/coldの全RAM台帳も保持。過去Save77/78/80等RAM差分owner解明とは区別。後続開始定数はSave81のcold0と一致。

## 次

[local1/trainer132への新北2歩とowner](../content/modernization/pr16_story_save81_next_route.json)。開いたlocal10跡から6,7へ。local1/3,7の視線距離3を静的確認した新event候補であり、native戦闘は未受入。第6ディグダを無目的に押さない。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save80']['record_completion']=prior_done
    state['story_save81']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[10,16],xy=[6,9],facing=2,rp=0,money=19416,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],fifth_diglett_event_accepted=True,gym_puzzle_completed=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='第5ディグダ通常配置変更とSave81。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='第5local10で4376 set・4375 clear、Save81/6,9北。全SaveRTC/field全pixel/RAM台帳保持。過去RAM差分/今回aux4021・4022 owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_GYM_TRAINER132_FROM_SAVE81',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save81_accept.py','scripts/pr16_story_save81_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save81_preparation.json','content/modernization/pr16_story_save81_next_route.json'],stop_rule_ja='Save81/6,9北だけから新北2歩6,7。最初の新event/battle後通常保存。視線発火しなければ6,7で縮小停止/目視。旧switch入力再走0。badge/紙引渡しを捏造しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='第5local10除去/local9復帰、Save81/6,9北。全party/紙/RAM保持。次は新北2歩でlocal1/trainer132視線候補。'
    state['do_not_repeat'].append('Save81の58/cold13入力33画面48member/31controller/56受入を無影響再走しない。local10で4376 set・4375 clear。25最終hashでも保存中/counter80→26counter81/成功→30field。全SaveRTC/全pixel/全party/RAM保持。過去RAM差分ownerは未解明。次は北2歩6,7のlocal1/trainer132視線候補。旧gym graph再採取0。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 第5ディグダ配置変更・Save81
- Version: story-gym-fifth-diglett-save81-v1
- Status: DONE（第5配置変更/通常保存/独立Continue限定）
- Summary: 新東3歩・東/北2旋回とlocal10通常A。4376 set/local10消失、4375 clear/local9復帰を原画/保存flag/固定ownerで照合。6,9北のSave81、全party600byte/HP288/PP9,10,15,2/Bag19416円/紙/PC保持。
- Files changed: Save81 preparation/measure/31controller/56受入/record/checkpoint/text証拠/次trainer132 owner、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。58+cold13入力33画面48member。新controller31原log継承/新受入56。record native0/compile0/旧成功再走0。
- Evidence: 16〜25保存中→25最終hash/counter80→26counter81/成功文言→30field。全SaveRTC/field全pixel/party/RAM保持。42checksum/7126byte1827範囲。S61E2flagsだけ。過去RAM差分とaux4021/4022 runtime owner未解明、紙引渡し/ジム攻略未受入。
- Discovery: 保存済gym graphの第5限定39命令/2台詞を再利用。次は開いたlocal10跡から北2歩6,7のlocal1/trainer132視線候補。全map再scan0。Save80記録run37175134666全11step終端を同期。
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





