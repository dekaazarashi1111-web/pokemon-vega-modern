#!/usr/bin/env python3
"""博物館入場・Save92原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import ast,datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save92_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-MUSEUM-ENTRY-SAVE92'
OUT=ROOT/'.local/pr16-story-save92-record'

CODE={'scripts/pr16_story_save92_accept.py','scripts/pr16_story_save92_record.py','tests/test_pr16_story_save92_accept.py',a.VISUAL,'content/modernization/pr16_story_save92_next_route.json','.github/workflows/pr16-story-save92-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE92_JA.md' and a.CP=='content/modernization/pr16_story_save92_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save92_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37186524023,'636f5f15f23a7bdc2b3400675f40286434e256b4',111389491487,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines();lines=[v.split('Z ',1)[-1]for v in log if ' ... ok'in v and 'test_pr16_story_save92_measure.'in v]
    need(len(lines)==36 and any('Ran 36 tests'in v for v in log)and any(v.endswith(' OK')for v in log),'controller36の原log継承・再走0')
    test_receipts=[dict(job=a.JOB,passed_tests=36,executed_tests=36,failed_tests=0,test_lines=lines,replayed_passed_tests=0)]
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==55 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save91全55member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save91/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==70 and len(z.namelist())==71 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save92member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==55 and visual['reviewed_screens']==dict(progress=list(range(53)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save92画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save92画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE92_ORIGINAL=str(original),PR16_SAVE91_INPUT=str(assets/'input.srm'),PR16_SAVE92_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save92_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==63 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 63 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'63成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save91-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save92 artifact11297164221のstory-fast.srm（131088bytes/SHA256 79864ff24d80a3b1cee73166bffb95f5795e2450f54582bad67ac6c024e2f9bf）だけから再開。新23歩/旋回3/warp1で博物館1階6/0・14,9北、通常保存/独立Continueを完了。自動北1歩は起きず14,9が実到着。次は北4西6南3の新13歩で階段8,8へ、最初の2階6/1到着直後だけ保存。静的target11,8/自動歩行はnative未確認。2階local2への紙引渡しはさらに別区間。紙274一個/4383/未引渡し4382/バッジ2/23164円/全party600byte/HP277/294/PP3,9,8,2保持。町20,16の観測5でprogress RAM差分、coldは新ledger保持。physical2056:0→1とlegacy4021:49→71/4022:1→3/404d:33→7のowner未解明。過去Save91の5vars/Save89RAM14/Save87raw41等も未解明のまま。全55画面/98+cold13入力/native2/新controller36/新受入63、旧受入再走0。35〜47保存中、46/47途中同hashでもcounter91/保存中文字、48最終hash/counter92/成功文言→52field。全SaveRTC/全38400pixel一致、S61E全payload保持。がくしゅうそうち未装備、Flash未使用、紙引渡し/全国図鑑/自然成長進化/全story/release未受入。入力ROM/runtime再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save92_accepted=True,museum_entry_accepted=True,museum_second_floor_accepted=False,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,required_badge_flag=2083,required_badge_present=True,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=36,controller_executions=36,controller_failed_executions=0,controller_repaired_cases=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=63,successful_native_processes=2,prior_failed_native_processes=0,prior_pre_native_failed_attempts=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 博物館入場・Save92限定受入

`{result['status']}`。Save91/20,11南から新23歩・旋回3・warp1。26で町19,25の入口遷移、27で博物館1階6/0・14,9北へ到着。自動北1歩は起きない。到着直後の通常Save92/独立Continueを受入。バッジ2・紙274一個・23164円、全party600byte/HP277/PP3,9,8,2を保持。2階到達/紙引渡しは未実行。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。70member/55画面/98+cold13入力。controller36と独立受入63。native2/記録native0/旧受入再走0/ROM変更0。

## 保存と差分

28〜32menu0→4、33/34確認、35〜47保存中。46/47は同じ途中hashでもcounter91/保存中文字。48最終hash/counter92/成功文言、52field。全131088byteSaveRTCと全38400pixelが独立Continue/120frame後も一致。安定hash/counter単独で完了としない。

全party600byte/HP277/294/PP3,9,8,2/Bag/紙/23164円/PC/S61E全payload保持。42checksum、全Save7105byte/1806範囲、旧Save91bank57344byte保持。町20,16の観測5でprogress RAM ledger差分が発生。coldは新ledger保持。physical2056:0→1、legacy4021:49→71/4022:1→3/404d:33→7。このruntime ownerと過去Save91の5vars/Save89RAM14/Save87raw41/RAM等のownerは未解明。現在差分を過去ownerの解決と混同しない。

## 次

[2階への新13歩](../content/modernization/pr16_story_save92_next_route.json)。14,9北から北4西6南3で階段8,8へ、最初の2階map6/1到着後だけ保存。静的target11,8/自動歩行はnative未確認。local2への封書引渡しはさらに後続の別区間。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save91']['record_completion']=prior_done
    state['story_save92']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[6,0],xy=[14,9],facing=2,rp=0,money=23164,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,museum_entry_accepted=True,museum_second_floor_accepted=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='新23歩/旋回3/warp1で博物館入場、Save92通常保存/独立Continue。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='博物館入場の新23歩/旋回3/warp1。Save92/6/0・14,9北、55画面。自動北1歩なし。party/HP277/PP3,9,8,2/紙/バッジ2/23164円保持。町20,16のRAM差分とphysical2056/3vars、過去raw41/RAM/auxのowner未解明。2階/紙引渡し未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MUSEUM_SECOND_FLOOR_FROM_SAVE92',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save92_accept.py','scripts/pr16_story_save92_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,'content/modernization/pr16_story_save92_next_route.json'],stop_rule_ja='Save92/博物館1階14,9北から北4西6南3の新13歩で階段8,8へ。最初のmap6/1到着後だけ保存。local2紙引渡しは後続別区間。未知NPC/境界/戦闘は縮小停止。旧23歩/ジム再走0。')
    state['do_not_repeat'].append('Save92の98/cold13入力55画面70member/controller36/受入63を無影響再走しない。新23歩/旋回3/warp1、6/0・14,9北で自動北1歩なし。35〜47保存中/46,47途中同hash、48最終hashと成功文言、52field。全SaveRTC/party600byte/S61E/全38400pixel保持。町20,16観測5のRAM差分とphysical2056/3vars、過去raw41/RAM等owner未解明。次は2階への新13歩。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='博物館入場Save92/6/0・14,9北。新23歩/旋回3/warp1、自動北1歩なし。party/紙/HP277/PP3,9,8,2保持。町20,16のRAM差分と2056/3varsのowner未解明。次は2階への新13歩、紙引渡しは後続。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    entry=f"""
## {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Version: PR16-STORY-SAVE92
- Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Task: {TASK} / 博物館入場とSave92
- Status: DONE（新入場warp/通常保存/独立Continue限定）
- Summary: 新23歩/旋回3/warp1、博物館6/0・14,9北Save92。自動北1歩なし。party600byte/HP277/PP3,9,8,2/Bag/紙/バッジ2/23164円/S61E保持。2階/紙引渡し未完。
- Files changed: Save92 preparation/measure/controller36/受入63/record/checkpoint/text証拠/次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。98+cold13入力55画面70member。controller36原logを継承、新受入63。record native0/compile0/旧成功再走0。
- Evidence: 35〜47部分hash/保存中、46/47途中同hash/counter91。48最終hash/counter92/成功文言→52field。全SaveRTC/party/S61E/38400pixel保持。42checksum/7105byte1806範囲。
- Discovery: 町20,16観測5でprogress RAM差分。coldは新ledger保持。physical2056:0→1と4021/4022/404dの3変数、過去Save91vars/Save89RAM/Save87raw41等runtime owner未解明。次は北4西6南3の新13歩で2階階段。Save91記録run37186524023全11step終端を同期。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repo GitHub/Actionsだけ。既存ROM/runtime/input非再配布。一般CI既知不一致を全成功にしない。merge/release/baseline変更0。
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









