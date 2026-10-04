#!/usr/bin/env python3
"""第6ディグダ配置変更・Save84原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save84_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-GYM-SIXTH-DIGLETT-SAVE84'
OUT=ROOT/'.local/pr16-story-save84-record'

CODE={'scripts/pr16_story_save84_accept.py','scripts/pr16_story_save84_record.py','tests/test_pr16_story_save84_accept.py',a.VISUAL,'content/modernization/pr16_story_save84_next_route.json','.github/workflows/pr16-story-save84-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE84_JA.md' and a.CP=='content/modernization/pr16_story_save84_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save84_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37178063036,'c8d4175bb8dc16c0208256a13edecba1265c29f2',111364757292,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save84_measure.' in v]
    need(len(lines)==31 and any('Ran 31 tests'in v for v in log)and any(v.endswith(' OK')for v in log),'新controller31の原logを継承・再走しない')
    test_receipts=[dict(job=a.JOB,passed_tests=31,executed_tests=31,failed_tests=0,test_lines=lines,replayed_passed_tests=0)]
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==85 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save83全85member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save83/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==49 and len(z.namelist())==50 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save84member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==34 and visual['reviewed_screens']==dict(progress=list(range(32)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save84画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save84画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE84_ORIGINAL=str(original),PR16_SAVE83_INPUT=str(assets/'input.srm'),PR16_SAVE84_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save84_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==59 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 59 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'59成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save83-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save84 artifact11294830074のstory-fast.srm（131088bytes/SHA256 882a52243dfb4d0faf4fa7d1e828197cf198b135c07c7698b3cfaaede360b8ac）だけから再開。ミルジム10/16・11,3西。第6local11の通常Aで4374set/remove8・4376clear/add10、local11保持。次は南4/西5の9歩6,7へ、南のlocal10/6,8へ通常A。4374trueの新branchで4372set/remove5・4374clear/add8。旧Save81の4375true branchとは別の第7相互作用。最初の新event後通常保存、予期しないNPC/境界は縮小停止。第7保存後の第8local10候補は4372trueから4373/4377set/remove6/11・4372clear/add5でleader前経路を開く静的予測、今回未入力。旧switch/勝利trainer132/160再走0。HP287/294・PP4,10,12,2、Bag20664円・紙274一個/PC保持、S61Eは4374/4376だけ。60+cold13入力34画面49member/native2、新controller31/新受入59。26最終hashでも保存中/counter83→27counter84/成功→31field。全SaveRTC/field全pixel/今回RAM全保持。aux4021:115→119/4022:0→4と過去RAM差分runtime owner未解明。紙consumer博物館2階local2はbadge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save84_accepted=True,sixth_diglett_event_accepted=True,trainer160_previously_accepted=True,gym_puzzle_completed=False,required_badge_flag=2083,required_badge_present=False,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=31,controller_executions=31,controller_failed_executions=0,controller_repaired_cases=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=59,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# ミルジム第6ディグダ配置変更・Save84限定受入

`{result['status']}`。Save83のジム10/16・11,7東から新北4歩11,3、西のlocal11/10,3へ通常A。4374 set/remove8、4376 clear/add10を保存byteと限定39命令ownerで照合。local11自体は残る。通常Save84/独立Continue、新戦闘0。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。49member/34画面/60+cold13入力。新controller31/新受入59。native2/record0/旧成功再走0/ROM変更0。

## 通常配置変更と保存境界

0開始11,7東→1北旋回→2〜5北4歩11,3→6西旋回→7話しかけた台詞→8配置変更文言→9field。local8は画面外、local10は下端のため全変更objectの直接視認は主張しない。保存flagsと固定ownerを照合し、local11は画面に残る。

10〜14menu0→4、15確認/16上書き、17〜26保存中。26は最終hashでもcounter83、27でcounter84/成功文言、31field。全party600byte/HP287/294・PP4,10,12,2/EXP/持物/控え保持。全Bag・20664円・紙274一個保持、physical trainer132/160含む全flags保持、PC保持。S61E payload2byteで4374 set/4376 clear、CRC確認。42checksum/7162byte1849範囲、旧Save83bank57344byte保持。

progress31/cold0/1全pixelと全SaveRTC一致、今回progress/coldRAM台帳全保持。aux4021:115→119/4022:0→4と過去RAM差分runtime ownerは未解明のまま。

## 次

[第7local10の新branchと限定39命令owner](../content/modernization/pr16_story_save84_next_route.json)。南4/西5の9歩6,7、南向きA。4374trueから4372set/remove5・4374clear/add8。旧第5local10の4375true branchは再走しない。

保存後の別stateで同じlocal10へ第8入力すれば4373/4377set/remove6/11・4372clear/add5となり、東側からleader前へ進む静的候補を見つけた。未入力であり、ジム攻略/leader到達・勝利へ昇格しない。毎回通常保存と新stateを照合する。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save83']['record_completion']=prior_done
    state['story_save84']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[10,16],xy=[11,3],facing=3,rp=0,money=20664,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[287,294],lead_pp=[4,10,12,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],sixth_diglett_event_accepted=True,trainer160_previously_accepted=True,gym_puzzle_completed=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='第6ディグダ配置変更とSave84。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='新北4歩/第6local11配置変更、Save84/11,3西。全SaveRTC/field全pixel/party/RAM保持。S61E4374set/4376clear、aux4021/4022と過去差分owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_GYM_SEVENTH_LOCAL10_FROM_SAVE84',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save84_accept.py','scripts/pr16_story_save84_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save84_preparation.json','content/modernization/pr16_story_save84_next_route.json'],stop_rule_ja='Save84/11,3西から南4/西5で6,7。南のlocal10へ通常A、4374trueの新branchだけ。最初の新event後通常保存、予期しないNPC/境界は縮小停止。旧4375truebranch/勝利trainer132/160再走0。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='第6local11配置変更、Save84/11,3西。4374set/4376clear。PP4,10,12,2/HP287/紙保持。次は南4/西5で第7local10の4374truebranch。'
    state['do_not_repeat'].append('Save84の60/cold13入力34画面49member/31controller/59受入を無影響再走しない。第6local11で4374set/4376clear、26最終hashでも保存中→27counter84/成功→31field。全SaveRTC/全pixel/party/今回RAM保持、aux4021/4022と過去差分owner未解明。次は第7local10の4374truebranch。旧第5の4375truebranch再走0。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / ミルジム第6ディグダ配置変更・Save84
- Version: story-gym-sixth-diglett-save84-v1
- Status: DONE（第6配置変更/通常保存/独立Continue限定）
- Summary: 新北4歩、西向きlocal11へ通常A。4374set/remove8・4376clear/add10、local11保持。11,3西Save84。全party600byte/HP287/PP4,10,12,2、Bag20664円/紙/PC保持。
- Files changed: Save84 preparation/measure/31controller/59受入/record/checkpoint/text証拠/次第7local10 owner、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。60+cold13入力34画面49member。新controller31原log継承/新受入59。record native0/compile0/旧成功再走0。
- Evidence: 17〜26保存中、26最終hashでもcounter83→27counter84/成功→31field。全SaveRTC/field全pixel/今回RAM保持。42checksum/7162byte1849範囲。aux4021:115→119/4022:0→4と過去差分runtime owner未解明、紙引渡し/ジム攻略未受入。
- Discovery: 保存済gym graphの第7local10限定39命令を再利用。4374trueで4372set/remove5・4374clear/add8。さらに別stateの第8で4377set/remove11となる静的候補だけ記録。旧第5local10とは分岐条件が違う。Save83記録run37178063036全11step終端を同期。
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







