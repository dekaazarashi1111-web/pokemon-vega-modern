#!/usr/bin/env python3
"""leader417通常勝利・Save87原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save87_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-GYM-LEADER-SAVE87'
OUT=ROOT/'.local/pr16-story-save87-record'

CODE={'scripts/pr16_story_save87_accept.py','scripts/pr16_story_save87_record.py','tests/test_pr16_story_save87_accept.py',a.VISUAL,a.ACTIVE,'content/modernization/pr16_story_save87_next_route.json','.github/workflows/pr16-story-save87-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE87_JA.md' and a.CP=='content/modernization/pr16_story_save87_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save87_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37180497747,'f5a5285c6818281aaedd70ee61a9c29a8d918230',111371933768,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save87_measure.' in v]
    need(len(lines)==37 and any('Ran 37 tests'in v for v in log)and any(v.endswith(' OK')for v in log),'新controller37の原logを継承・再走しない')
    test_receipts=[dict(job=a.JOB,passed_tests=37,executed_tests=37,failed_tests=0,test_lines=lines,replayed_passed_tests=0)]
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==43 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save86全43member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save86/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==127 and len(z.namelist())==128 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save87member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==112 and visual['reviewed_screens']==dict(progress=list(range(110)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save87画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save87画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE87_ORIGINAL=str(original),PR16_SAVE86_INPUT=str(assets/'input.srm'),PR16_SAVE87_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save87_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==65 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 65 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'65成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save86-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save87 artifact11294659819のstory-fast.srm（131088bytes/SHA256 9c49fdef23b321415e82bffe0b239b5acff9cb4356e7cc3aea1a9aa25027028c）だけから再開。ミルジム10/16・7,3西、leader417新1勝・バッジ2個/0x823・TM37item325一個を通常取得。HP277/294、PP3,9,8,2、所持金23164円、紙274一個保持。次は東4/南4/西5の13歩で6,7、南旋回してlocal10/6,8へ通常A。未入力4373true分岐で4373/4377clear・4376set、local6/11復帰/local10除去の退出用第9switch。最初の新event後保存。旧3branch/switch/勝利trainerの再走0、未知NPC/境界は縮小停止。退出は静的にはlocal8まで13歩と2相互作用、出口へ10歩が続くが未測定。第9switch→退出→博物館2階local2へ封書引渡し→505レンジャー。leader実6体/実技6使用を全112画面とactive table0x09329070・24consumerで照合。測定前の残存原本3体誤認はactive_trainer.jsonで訂正、原本を改作せず再走0。216+cold13入力/127member/native2、新controller37/新受入65。105counter87/最終hashでもtext空白、106成功文言、109field/cold全pixel/全SaveRTC一致。party8byte差分のうちPP3/HP1以外のraw41/141/241/341、RAM22/43/63/85と補助vars6件・旧Save85/過去差分runtime owner未解明。紙引渡し/退出/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達/全story未受入。がくしゅうそうち未装備、Flash未使用、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更0。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save87_accepted=True,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=False,required_badge_flag=2083,required_badge_present=True,paper_consumed_or_delivered=False,active_trainer_correction=a.ACTIVE,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=37,controller_executions=37,controller_failed_executions=0,controller_repaired_cases=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=65,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# ミルジムleader417勝利・バッジ/TM37・Save87限定受入

`{result['status']}`。Save86の6,7南から東5/北4/西4の新13歩で7,3西。leaderナギナタの6体に1勝、アルネブバッジ/バッジ2個・TM37どろばくだんitem325一個・賞金2500円を通常取得。Save87/独立Continue。退出と紙引渡しは未入力。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。127member/112画面/216+cold13入力。新controller37/新受入65、native2/記録native0/旧受入再走0/ROM変更0。

## 実編成と測定前原本の訂正

測定前の[preparation](../content/modernization/pr16_story_save87_preparation.json)はVega残存table0x081FDFD8の3体を読んだ。現consumerではなかった。[active trainer訂正](../content/modernization/pr16_story_save87_active_trainer.json)で、現ROMの24consumer pointer→table0x09329070→trainer417/party0x09352320の6体を確認し、全画面に照合した。過去原本は改作せず、native再走もしない。

実出現順はサイホーンLv23/エビワラーLv23/モグリューLv24/アオガラスLv24/ダグトリオLv25/ファイマーLv25。tableの最後2枠と実選出順は異なる。ドラゴンクロー1/かわらわり4/じしん1、交代取消5。PP予算8選択内の6選択、実PP消費6。HP287→282→277/294、PP4,10,12,2→3,9,8,2。つばめがえし2を保持。

## 保存境界

74勝利、77/78バッジ、81賞金、83TM収納、84〜86説明、87field。88〜92menu0→4、93/94確認、95〜104部分保存。105counter87/最終hashでもtext空白、106〜108成功文言、109field/cold0/1全pixel一致。全131088byteSaveRTC一致。

party592byte保持、差分8byte=実PP3/HP1/raw41系列4。raw41/141/241/341のownerは未解明、全party8段階hashは保存byteから独立再構成。全BagはTM枠2の325一個追加のみ、所持金20664→23164円、紙274一個/PC/S61E/通常story変数を保持。physical flags158clear/659,1203,1545,1697,2083setはsourceの勝利/報酬/旧trainer265自動setへ照合。新戦闘はleader1勝だけ。

補助vars4021,4022,40AA,40AC,40AD,40AEとRAM22/43/63/85のruntime owner未解明。過去差分も解決扱いしない。42checksum、全Save7194byte/1842範囲、旧Save86bank57344byte保持。

## 次

[退出用local10新分岐](../content/modernization/pr16_story_save87_next_route.json)。東4/南4/西5で6,7、南へ通常A。4373trueの第9switchは未入力。静的47命令7nodeから4373/4377clear・4376set、local6/11復帰/local10除去を予測。旧3branchと区別し最初の新event後保存。ジム退出/博物館の封書引渡しは未受入。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save86']['record_completion']=prior_done
    state['story_save87']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[10,16],xy=[7,3],facing=3,rp=0,money=23164,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,active_trainer_correction=a.ACTIVE,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='leader417の6体へ1勝/バッジ/TM37/Save87。残存原本3体は現consumerと異なることを訂正。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='新13歩からナギナタ6体へ1勝。Save87/7,3西、バッジ2/TM37/賞金2500円。active table/24consumer/画面を照合。退出と紙引渡しは次。raw41系列とRAM/補助vars・過去差分owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_GYM_EXIT_NINTH_DIGLETT_FROM_SAVE87',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,a.ACTIVE,'scripts/pr16_story_save87_accept.py','scripts/pr16_story_save87_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save87_preparation.json','content/modernization/pr16_story_save87_next_route.json'],stop_rule_ja='Save87/7,3西から東4/南4/西5で6,7、南旋回してlocal10/6,8へ通常A。退出用の未入力4373true分岐だけ、最初の新event後保存。旧switchの3branch/旧勝利再走0。未知NPC/境界は縮小停止。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='ナギナタ6体に1勝、Save87/7,3西。バッジ2/TM37/23164円、HP277/PP3,9,8,2。次は退出用local10の未入力4373true分岐。残存3体preparationはactive6体へ訂正。退出/紙引渡し未完。'
    state['do_not_repeat'].append('Save87の216/cold13入力112画面127member/37controller/65受入を無影響再走しない。leader417の実6体に1勝/バッジ2083/TM37/賞金2500円。原本残存3体preparationはactive_trainer.jsonの24consumer/後継6体で訂正し、旧原本は保持。105counterと最終hash/text空白→106成功→109field、全SaveRTC/全pixel保持。raw41系列/RAM/auxvarsと旧差分owner未解明。次は退出用local10の未入力4373true分岐。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / ミルジムleader417通常勝利・Save87
- Version: story-gym-leader-save87-v1
- Status: DONE（leader1勝/バッジ/TM37/通常保存/独立Continue限定）
- Summary: 新13歩/3旋回、7,3西でナギナタ6体へ1勝。アルネブバッジ/バッジ2、TM37item325一個、賞金2500円。HP277/294・PP3,9,8,2・23164円・紙274保持。
- Files changed: Save87 preparation/measure/37controller/65受入/record/checkpoint/全text証拠/active consumer訂正/退出次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。216+cold13入力112画面127member。controller37原log継承/新受入65。record native0/compile0/旧成功再走0。
- Evidence: 全6体画面/技6使用/交代取消5。105counter87/最終hashでもtext空白→106成功→109field。全SaveRTC/field全pixel/PC/S61E/紙保持。party8byte差分、raw41系列4byte/RAM4段階/auxvars6件と旧差分owner未解明。42checksum/7194byte1842範囲。
- Correction: 測定前の3体はVega残存table、現consumerではなかった。測定後に24consumer→table0x09329070→party0x09352320の6体を確定。native原本/preparationは改作せず、再走0。最後2体のtable順と実AI選出順を分離。今後は現consumerから読む。
- Discovery: バッジ後もswitch配置は不変。退出用local10の未入力4373truebranch/47命令7nodeを固定。次は東4/南4/西5で6,7へ、第9相互作用後保存。Save86記録run37180497747全11step終端を同期。
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







