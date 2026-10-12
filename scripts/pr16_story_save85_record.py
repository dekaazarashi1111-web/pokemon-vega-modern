#!/usr/bin/env python3
"""第7ディグダ配置変更・Save85原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save85_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-GYM-SEVENTH-DIGLETT-SAVE85'
OUT=ROOT/'.local/pr16-story-save85-record'

CODE={'scripts/pr16_story_save85_accept.py','scripts/pr16_story_save85_record.py','tests/test_pr16_story_save85_accept.py',a.VISUAL,'content/modernization/pr16_story_save85_next_route.json','.github/workflows/pr16-story-save85-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE85_JA.md' and a.CP=='content/modernization/pr16_story_save85_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save85_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37178978418,'41855abed8f2655553b26d00ae9d9ba4db1d7ea8',111367470748,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save85_measure.' in v]
    need(len(lines)==31 and any('Ran 31 tests'in v for v in log)and any(v.endswith(' OK')for v in log),'新controller31の原logを継承・再走しない')
    test_receipts=[dict(job=a.JOB,passed_tests=31,executed_tests=31,failed_tests=0,test_lines=lines,replayed_passed_tests=0)]
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==49 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save84全49member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save84/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==55 and len(z.namelist())==56 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save85member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==40 and visual['reviewed_screens']==dict(progress=list(range(38)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save85画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save85画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE85_ORIGINAL=str(original),PR16_SAVE84_INPUT=str(assets/'input.srm'),PR16_SAVE85_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save85_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==63 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 63 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'63成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save84-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save85 artifact11294671228のstory-fast.srm（131088bytes/SHA256 0001f6a52812526ea52a9f2bcca8055e934379830214a8507867b10e3c2e00e0）だけから再開。ミルジム10/16・6,7南。第7local10の4374true branchで4372set/remove5・4374clear/add8、local10保持。次は移動せず南のlocal10/6,8へ通常A。4372trueの未入力第8branchで4373/4377set/remove6/11・4372clear/add5を予測。最初の新event後通常保存し、別stateとして独立Continue。第8後の東5/北4/西4の13歩leader前7,3は静的候補のみ、今回未入力。旧第5/第7branch、勝利trainer132/160再走0。HP287/294・PP4,10,12,2/Bag20664円・紙274一個/PC保持。party598/600byte保持、raw241:108→109と341:61→62が進行観測11で変化、RAM台帳も11で変化。これら/aux4021:119→0・4022:4→3と過去差分runtime ownerは未解明。72+cold13入力40画面55member/native2、新controller31/新受入63。33counter85でも保存中/部分hash→34最終hash/成功→37field。全SaveRTC/field全pixel/coldRAM保持。紙consumer博物館2階local2はbadge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save85_accepted=True,seventh_diglett_event_accepted=True,trainer160_previously_accepted=True,gym_puzzle_completed=False,required_badge_flag=2083,required_badge_present=False,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=31,controller_executions=31,controller_failed_executions=0,controller_repaired_cases=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=63,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# ミルジム第7ディグダ配置変更・Save85限定受入

`{result['status']}`。Save84のジム10/16・11,3西から新南4/西5歩6,7へ。南のlocal10/6,8に通常A、4374trueの未入力branchで4372 set/remove5・4374 clear/add8。local10自体は残る。通常Save85/独立Continue、新戦闘0。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。55member/40画面/72+cold13入力。新controller31/新受入63。native2/record0/旧成功再走0/ROM変更0。

## 通常配置変更と保存境界

0開始11,3西→1南旋回→2〜5南4歩→6西旋回→7〜11西5歩6,7→12南旋回→13話しかけた台詞→14配置変更文言→15field。local10保持。local5除去/local8復帰を保存flagsと限定39命令ownerで照合し、全変更object画面内とは主張しない。

16〜20menu0→4、21確認/22上書き、23〜33保存中。33でcounter85だが部分hash/保存中、34で最終hashと成功文言、37field。partyは598/600byte保持、raw241:108→109/341:61→62（控え2体のraw offset41）が観測11で変化、RAM台帳も同時変化。runtime ownerは未解明。主力HP287/294・PP4,10,12,2/EXP/持物/全Bag・20664円・紙274一個・PC・physical flags保持。S61E payload258:71→23で4372 set/4374 clear、CRC確認。42checksum/7171byte1847範囲、旧Save84bank57344byte保持。

progress37/cold0/1全pixelと全SaveRTC一致、cold RAM台帳保持。aux4021:119→0/4022:4→3と過去RAM差分runtime ownerは未解明のまま。party/RAMの全保持とは記録しない。

## 次

[第8local10の未入力4372true branchと限定43命令owner](../content/modernization/pr16_story_save85_next_route.json)。移動せず同じ南向きAで4373/4377set/remove6/11・4372clear/add5。別stateの新eventとして通常保存する。

その保存後にleader前7,3へ東5/北4/西4の13歩を進む静的候補がある。第8/leader到達・勝利/ジム攻略は未入力・未受入。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save84']['record_completion']=prior_done
    state['story_save85']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[10,16],xy=[6,7],facing=1,rp=0,money=20664,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[287,294],lead_pp=[4,10,12,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],seventh_diglett_event_accepted=True,trainer160_previously_accepted=True,gym_puzzle_completed=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='第7ディグダ配置変更とSave85。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='新南4/西5歩/第7local10配置変更、Save85/6,7南。4372set/4374clear、全SaveRTC/field全pixel/coldRAM保持。party2byte/RAM観測11変化とaux4021/4022、過去差分owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_GYM_EIGHTH_LOCAL10_FROM_SAVE85',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save85_accept.py','scripts/pr16_story_save85_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save85_preparation.json','content/modernization/pr16_story_save85_next_route.json'],stop_rule_ja='Save85/6,7南から移動せずlocal10へ通常A、4372trueの第8新branchだけ。最初の新event後通常保存。旧第5/第7branch/勝利trainer132/160再走0。leader経路は第8保存後に再評価。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='第7local10の4374true branch、Save85/6,7南。4372set/4374clear。HP287/PP4,10,12,2/紙保持、party2byte/RAM差分owner未解明。次は同位置の第8local10/4372true branch。'
    state['do_not_repeat'].append('Save85の72/cold13入力40画面55member/31controller/63受入を無影響再走しない。第7local10で4372set/4374clear。33counter85でも保存中→34最終hash/成功→37field。全SaveRTC/全pixel/coldRAM保持。party598byte保持/2byteと観測11RAM、aux4021/4022、過去差分owner未解明。次は同位置第8local10の4372truebranch。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / ミルジム第7ディグダ配置変更・Save85
- Version: story-gym-seventh-diglett-save85-v1
- Status: DONE（第7配置変更/通常保存/独立Continue限定）
- Summary: 新南4/西5歩、南向きlocal10へ通常A。4372set/remove5・4374clear/add8、local10保持。6,7南Save85。HP287/PP4,10,12,2、Bag20664円/紙/PC保持。party598byte保持/2byte変化は別記。
- Files changed: Save85 preparation/measure/31controller/63受入/record/checkpoint/text証拠/次第8local10 owner、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。72+cold13入力40画面55member。新controller31原log継承/新受入63。record native0/compile0/旧成功再走0。
- Evidence: 23〜33保存中、33counter85でも部分hash→34最終hash/成功→37field。全SaveRTC/field全pixel/coldRAM保持。42checksum/7171byte1847範囲。raw241:108→109/341:61→62・観測11RAM、aux4021:119→0/4022:4→3と過去差分runtime owner未解明。紙引渡し/ジム攻略未受入。
- Discovery: 保存済gym graphの第8local10限定43命令を再利用。4372trueで4373/4377set/remove6/11・4372clear/add5を予測。leader前13歩は静的候補のみ。Save84記録run37178978418全11step終端を同期。
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







