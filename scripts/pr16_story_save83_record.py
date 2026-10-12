#!/usr/bin/env python3
"""trainer160通常勝利・Save83原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save83_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-GYM-TRAINER160-SAVE83'
OUT=ROOT/'.local/pr16-story-save83-record'

CODE={'scripts/pr16_story_save83_accept.py','scripts/pr16_story_save83_record.py','tests/test_pr16_story_save83_accept.py',a.VISUAL,'content/modernization/pr16_story_save83_next_route.json','.github/workflows/pr16-story-save83-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE83_JA.md' and a.CP=='content/modernization/pr16_story_save83_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save83_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37177151335,'b63c6e1f383406ec4e1b1f35d9b8504fa82335fc',111362051771,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save83_measure.' in v]
    need(len(lines)==31 and any('Ran 31 tests'in v for v in log)and any(v.endswith(' OK')for v in log),'新controller31の原logを継承・再走しない')
    test_receipts=[dict(job=a.JOB,passed_tests=31,executed_tests=31,failed_tests=0,test_lines=lines,replayed_passed_tests=0)]
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==78 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save82全78member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save82/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==85 and len(z.namelist())==86 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save83member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==70 and visual['reviewed_screens']==dict(progress=list(range(68)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save83画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save83画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE83_ORIGINAL=str(original),PR16_SAVE82_INPUT=str(assets/'input.srm'),PR16_SAVE83_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save83_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==67 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 67 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'67成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save82-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save83 artifact11293763616のstory-fast.srm（131088bytes/SHA256 157a945e7bdb3287b519c235ef95c12ddcefb14a62d479cf3a5f753e4f009523）だけから再開。ミルジム10/16・11,7東。新東5歩でlocal3/trainer160トラジに通常1勝、敵4体/賞金384円/physical1440set。次は新北4歩11,3、西のlocal11/10,3へ旋回して通常A。4376=true分岐は4374set/remove8・4376clear/add10、local11自体は残る。最初の新event/battle後通常保存、予期しない境界は縮小停止。旧5switch/勝利trainer132/160再走0。HP287/294・PP4,10,12,2、Bag20664円・紙274一個/PC/S61E保持。132+cold13入力70画面85member/native2、新controller31/新受入67。62counter83でも保存中/部分write→63最終hash/成功→67field。全SaveRTC/field全pixel/coldRAM保持。今回RAM17/38変化・aux4021:111→115と過去RAM差分のruntime owner未解明。紙consumer博物館2階local2はbadge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save83_accepted=True,trainer160_victory_accepted=True,gym_puzzle_completed=False,required_badge_flag=2083,required_badge_present=False,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=31,controller_executions=31,controller_failed_executions=0,controller_repaired_cases=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=67,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# ミルジムtrainer160通常1勝・Save83限定受入

`{result['status']}`。Save82のジム10/16・6,7北から新東5歩11,7でlocal3/trainer160視線発火。たんぱんこぞうトラジの4体を通常撃破し384円獲得、physical1440だけset。通常Save83/独立Continue。残り北4歩/第6switchは未入力。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。85member/70画面/132+cold13入力。新controller31/新受入67。native2/record0/旧成功再走0/ROM変更0。

## 通常戦闘と保存境界

0開始6,7北→1東旋回→2〜6東5歩11,7視線、7/8NPC南隣からの台詞。9〜44新戦闘。ライノス♀Lv22、レクオレ♂Lv23、ファイマー♂Lv23、リーティン♂Lv24。ドラゴンクロー2回/かわらわり2回/交代取消3。23でHP288→287、42勝利/44賞金384円。PP予約は選択ごと最大3PPで、2回後にslot2へ切替。実消費は保存party byteから別途確認。

45field、46〜50menu0→4、51確認/52上書き、53〜62保存中。62counter83でも部分write、63最終hashと成功文言、67field。全party597byte保持、PP6→4/14→12・HP288→287の3byteだけ。全EXP/持物/控え保持。全Bag保持と20280→20664円。physical1440だけ、PC/S61E/紙274一個/flag4383保持。42checksum/7168byte1847範囲、旧Save82bank57344byte保持。

progress45/67/cold0/1全pixelと全SaveRTC一致。progressRAM17/38変化・aux4021:111→115はruntime owner未解明。coldRAMは保存直前と同一で120frame後も保持。過去RAM差分owner解明とは別。local3元位置11,9/trainer160は静的ownerと勝利bitで照合し、南隣11,8は画面上の位置。runtime object IDの確定とは区別。

## 次

[第6local11への残り新北4歩と限定39命令owner](../content/modernization/pr16_story_save83_next_route.json)。4372/4373/4374/4375=false、4376=trueから4374set/remove8・4376clear/add10。local11自体は残る。今回は未入力のため静的予測のままであり、ジム突破には昇格しない。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save82']['record_completion']=prior_done
    state['story_save83']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[10,16],xy=[11,7],facing=4,rp=0,money=20664,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[287,294],lead_pp=[4,10,12,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],trainer160_victory_accepted=True,gym_puzzle_completed=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='trainer160新勝利とSave83。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='新東5歩からtrainer160トラジ1勝/賞金384円、Save83/11,7東。全SaveRTC/field全pixel/紙/S61E保持。PP2byteとHP1byteだけ、RAM17/38とaux4021 owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_GYM_SIXTH_DIGLETT_FROM_SAVE83',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save83_accept.py','scripts/pr16_story_save83_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save83_preparation.json','content/modernization/pr16_story_save83_next_route.json'],stop_rule_ja='Save83/11,7東から新北4歩11,3。西のlocal11へ通常A。最初の新event/battle後通常保存。予期しない境界は縮小停止。旧switch/trainer132/160再走0。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='trainer160トラジに新1勝、Save83/11,7東。PP4,10,12,2/HP287/紙/S61E保持。次は新北4歩で第6local11。'
    state['do_not_repeat'].append('Save83の132/cold13入力70画面85member/31controller/67受入を無影響再走しない。trainer160新1勝384円/1440set。62counter83でも保存中→63最終hash/成功→67field。全SaveRTC/全pixel/紙/S61E保持、PP2byteとHP1byteだけ。今回/過去RAM差分owner未解明。次は新北4歩と第6local11。旧gym graph再採取0。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / ミルジムtrainer160通常勝利・Save83
- Version: story-gym-trainer160-save83-v1
- Status: DONE（trainer160新1勝/通常保存/独立Continue限定）
- Summary: 新東5歩でlocal3トラジ視線発火。敵4体/通常1勝384円/physical1440set。11,7東Save83、全party597byte保持、PP6→4・14→12/HP288→287だけ、Bag20664円/紙/PC/S61E保持。
- Files changed: Save83 preparation/measure/31controller/67受入/record/checkpoint/text証拠/次第6local11 owner、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。132+cold13入力70画面85member。新controller31原log継承/新受入67。record native0/compile0/旧成功再走0。
- Evidence: 53〜62保存中、62counter83でも部分write→63最終hash/成功→67field。全SaveRTC/field全pixel/coldRAM保持。42checksum/7168byte1847範囲。今回RAM17/38とaux4021/過去差分runtime owner未解明、紙引渡し/ジム攻略未受入。
- Discovery: 保存済gym graphの第6local11限定39命令を再利用。4376true分岐は4374set/remove8・4376clear/add10。次は残り新北4歩11,3へ。全map再scan0。Save82記録run37177151335全11step終端を同期。
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







