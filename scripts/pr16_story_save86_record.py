#!/usr/bin/env python3
"""第8ディグダ配置変更・Save86原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save86_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-GYM-EIGHTH-DIGLETT-SAVE86'
OUT=ROOT/'.local/pr16-story-save86-record'

CODE={'scripts/pr16_story_save86_accept.py','scripts/pr16_story_save86_record.py','tests/test_pr16_story_save86_accept.py',a.VISUAL,'content/modernization/pr16_story_save86_next_route.json','.github/workflows/pr16-story-save86-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE86_JA.md' and a.CP=='content/modernization/pr16_story_save86_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save86_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37179886417,'6757a9443d1fdd106fea64075d3498257297170e',111370126817,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save86_measure.' in v]
    need(len(lines)==31 and any('Ran 31 tests'in v for v in log)and any(v.endswith(' OK')for v in log),'新controller31の原logを継承・再走しない')
    test_receipts=[dict(job=a.JOB,passed_tests=31,executed_tests=31,failed_tests=0,test_lines=lines,replayed_passed_tests=0)]
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==55 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save85全55member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save85/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==43 and len(z.namelist())==44 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save86member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==28 and visual['reviewed_screens']==dict(progress=list(range(26)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save86画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save86画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE86_ORIGINAL=str(original),PR16_SAVE85_INPUT=str(assets/'input.srm'),PR16_SAVE86_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save86_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==59 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 59 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'59成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save85-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save86 artifact11294997639のstory-fast.srm（131088bytes/SHA256 d1ea60da2a4b4ea00fa6a6d70fde1c9be74b5c92fd90fc780b47737761041715）だけから再開。ミルジム10/16・6,7南。第8local10の4372true branchで4373/4377set/remove6/11・4372clear/add5、local10保持。次は東5/北4/西4の新13歩で7,3西へ、西のleader local7/6,3へ通常A。static trainer417/type1、badge0x823 setのsourceを118命令17nodeで固定。leaderの原本party/技/physical remapとPP方針は先に確認し、最初の新event/戦闘後通常保存。予期しないNPC/境界は縮小停止。leader経路/到達/勝利は未入力、ジム攻略未受入。旧switch/勝利trainer132/160再走0。HP287/294・PP4,10,12,2、控えMewtwo354/354・PP10,20,15,10、Bag20664円・紙274一個/PC保持。今回party600byte/全SaveRTC/field全pixel/progressとcoldRAM/全legacyvars保持。旧Save85 raw241/341各+1・観測11RAM、aux4021:119→0・4022:4→3と過去差分runtime ownerは未解明。48+cold13入力28画面43member/native2、新controller31/新受入59。20最終hashでもcounter85/保存中→21counter86/text空白→22成功文言→25field。紙consumer博物館2階local2はbadge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save86_accepted=True,eighth_diglett_event_accepted=True,trainer160_previously_accepted=True,gym_puzzle_completed=False,required_badge_flag=2083,required_badge_present=False,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=31,controller_executions=31,controller_failed_executions=0,controller_repaired_cases=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=59,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# ミルジム第8ディグダ配置変更・Save86限定受入

`{result['status']}`。Save85のジム10/16・6,7南から移動も旋回もせずlocal10/6,8へ通常A。4372trueの未入力branchで4373/4377 set/remove6/11・4372 clear/add5。local10自体は残る。通常Save86/独立Continue、新戦闘0。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。43member/28画面/48+cold13入力。新controller31/新受入59。native2/record0/旧成功再走0/ROM変更0。

## 通常配置変更と保存境界

0開始6,7南→1話しかけた台詞→2配置変更文言→3field。移動/旋回0。local10保持、右上local11/10,3が消えleader側の通路が開く見た目を確認。local6除去/local5復帰も保存flagsと限定43命令ownerで照合し、全変更object画面内とは主張しない。

4〜8menu0→4、9確認/10上書き、11〜20保存中。20で最終hashでもcounter85、21counter86でtext欄空白、22〜24成功文言、25field。今回party600byte/HP287/294・PP4,10,12,2/EXP/持物/全Bag・20664円・紙274一個・PC・physical flags/全legacy vars保持。S61E payload258:23→39/259:164→166で4373/4377 set・4372 clear、CRC確認。42checksum/7161byte1847範囲、旧Save85bank57344byte保持。

progress25/cold0/1全pixelと全SaveRTC一致、今回progress/cold RAM台帳保持。旧Save85 party raw241/341各+1と観測11RAM、aux4021/4022、過去差分のruntime ownerは未解明のまま。

## 次

[leader前13歩とlocal7の118命令17node](../content/modernization/pr16_story_save86_next_route.json)。6,7から東5/北4/西4で7,3西へ。西のleader6,3へ通常A。固定sourceのtrainer417/type1とbadge0x823 set命令を確認。原本party/技/physical remap/PP方針は次に確認する。

この13歩とleader到達・勝利は未入力。local11除去からの静的通行可能予測を、ジム攻略の受入にしない。最初の新event/戦闘後保存、未知NPC/境界は縮小停止。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save85']['record_completion']=prior_done
    state['story_save86']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[10,16],xy=[6,7],facing=1,rp=0,money=20664,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[287,294],lead_pp=[4,10,12,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],eighth_diglett_event_accepted=True,trainer160_previously_accepted=True,gym_puzzle_completed=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='第8ディグダ配置変更とSave86。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='第8local10を移動/旋回0で通常A、Save86/6,7南。4373/4377set/4372clear、local11除去。今回全party/SaveRTC/field全pixel/RAM保持。leader13歩は静的候補、旧Save85/過去差分owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_GYM_LEADER_FROM_SAVE86',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save86_accept.py','scripts/pr16_story_save86_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save86_preparation.json','content/modernization/pr16_story_save86_next_route.json'],stop_rule_ja='Save86/6,7南から東5/北4/西4で7,3西、leader local7/6,3へ通常A。trainer417の原本party/技/physical remap/PP方針を先に確認。最初の新event/戦闘後通常保存。未知NPC/境界は縮小停止。旧switch/勝利trainer132/160再走0。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='第8local10の4372true branch、Save86/6,7南。4373/4377set/4372clear、local11除去。全party/RAM保持。次は新13歩でleader前7,3西、通常A。leader到達/勝利は未入力。'
    state['do_not_repeat'].append('Save86の48/cold13入力28画面43member/31controller/59受入を無影響再走しない。第8local10で4373/4377set/4372clear、local11除去。20最終hash/21counterとtext空白/22成功/25field。全SaveRTC/全pixel/今回party600byteとRAM保持。旧Save85と過去差分owner未解明。次はleader前13歩/新A、trainer417/type1は静的確認のみ。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / ミルジム第8ディグダ配置変更・Save86
- Version: story-gym-eighth-diglett-save86-v1
- Status: DONE（第8配置変更/通常保存/独立Continue限定）
- Summary: 移動/旋回0、南向きlocal10へ通常A。4373/4377set/remove6/11・4372clear/add5、local10保持。6,7南Save86。今回全party600byte/HP287/PP4,10,12,2、Bag20664円/紙/PC/legacyvars/RAM保持。
- Files changed: Save86 preparation/measure/31controller/59受入/record/checkpoint/text証拠/leader次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。48+cold13入力28画面43member。新controller31原log継承/新受入59。record native0/compile0/旧成功再走0。
- Evidence: 11〜20保存中、20最終hash/counter85→21counter86/text空白→22成功文言→25field。全SaveRTC/field全pixel/今回party/RAM保持。42checksum/7161byte1847範囲。旧Save85 party2byte/RAMとaux4021/4022、過去差分runtime owner未解明。紙引渡し/leader/ジム攻略未受入。
- Discovery: local11が消えleader側通路が開いた画面。次は東5/北4/西4の新13歩7,3西。保存済gym graphからleader local7の118命令17nodeを再利用、trainer417/type1とbadge0x823 set命令だけ静的確認。party/技/physical remap/PP方針とnativeは次工程。Save85記録run37179886417全11step終端を同期。
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







