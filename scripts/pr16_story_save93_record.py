#!/usr/bin/env python3
"""博物館50円受付・Save93原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import ast,datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save93_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-MUSEUM-ADMISSION-SAVE93'
OUT=ROOT/'.local/pr16-story-save93-record'

CODE={'scripts/pr16_story_save93_accept.py','scripts/pr16_story_save93_record.py','tests/test_pr16_story_save93_accept.py',a.VISUAL,'content/modernization/pr16_story_save93_next_route.json','.github/workflows/pr16-story-save93-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE93_JA.md' and a.CP=='content/modernization/pr16_story_save93_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save93_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37187614083,'82f22a40ecc60f5f26468531d10ca25b0db3ee7c',111392808208,['success']*11)
    first_done=inherited.terminal(37188126911,'6a02e79f4b88685e8de8199edde4b335cb6a30e9',111394391365,['success','success','success','failure','skipped','success','success','success'])
    test_receipts=[]
    for job,module,count in [(111394391365,'test_pr16_story_save93_measure',38),(a.JOB,'test_pr16_story_save93_admission',15)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines();lines=[v.split('Z ',1)[-1]for v in log if ' ... ok'in v and module+'.'in v]
        need(len(lines)==count and any(f'Ran {count} tests'in v for v in log)and any(v.endswith(' OK')for v in log),'初回38/影響15controller原log・再走0')
        test_receipts.append(dict(job=job,passed_tests=count,executed_tests=count,failed_tests=0,test_lines=lines,replayed_passed_tests=0))
    first_source='6a02e79f4b88685e8de8199edde4b335cb6a30e9'
    historical_code={'scripts/pr16_story_save93_measure.py','tests/test_pr16_story_save93_measure.py','content/modernization/pr16_story_save93_preparation.json'}
    for name in historical_code:need(h.d.git('show',first_source+':'+name)==(ROOT/name).read_bytes(),'初回計画source原本保持 '+name)
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==70 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save92全70member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save92/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==52 and len(z.namelist())==53 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save93member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==36 and visual['reviewed_screens']==dict(progress=list(range(34)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save93画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save93画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE93_ORIGINAL=str(original),PR16_SAVE92_INPUT=str(assets/'input.srm'),PR16_SAVE93_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save93_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==63 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 63 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'63成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','failed-attempt.json','save92-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'failed-first-terminal.json',first_done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save93 artifact11298425525のstory-fast.srm（131088bytes/SHA256 93cdaccd2cd5cb969a9d4bc78187b25b62fd0f9b05924f2c2bd0ad26ed73d255）だけから再開。博物館1階6/0・14,5東、通常50円受付/Save93/独立Continueを完了。所持金23114円、var4061=1。次は西6南3の新9歩で階段8,8へ、最初の2階6/1到着直後だけ保存。到着はwarp11,8と通行可能な隣接11,7/11,9/12,8のいずれか、実到着/自動歩行未確認。旧北4歩/受付を再走しない。local2への紙引渡しは後続別区間。紙274一個/4383/未引渡し4382/バッジ2/全party600byte/HP277/294/PP3,9,8,2保持。今回全RAM/legacy flags/S61E/PC保持。4001:0→2と4061:0→1は受付ROM ownerと一致、4021:71→74/4022:3→1のowner未解明。過去Save92RAM観測5/2056/3vars、Save91の5vars/Save89RAM14/Save87raw41等は未解明のまま。全36画面/60+cold13入力、成功native2と初回未保存失敗native1。原38controllerと新影響15、新受入63、旧成功再走0。28最終hash先行でも保存中/counter92→29counter93別hash→30成功文言/最終hash→33field。全SaveRTC/全38400pixel一致。2階/紙引渡し/全国図鑑/自然成長進化/全story/release未受入。入力ROM/runtime非再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save93_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=50,museum_admission_var4061=1,museum_second_floor_accepted=False,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,required_badge_flag=2083,required_badge_present=True,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE|historical_code),evidence_bindings=h.d.bindings(paths),controller_cases=53,controller_executions=53,controller_failed_executions=0,controller_repaired_cases=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=63,successful_native_processes=2,prior_failed_native_processes=1,prior_pre_native_failed_attempts=0,total_native_processes=3,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 博物館50円受付・Save93限定受入

`{result['status']}`。Save92/14,9北から新北4歩、14,5で自動受付。4で50円説明/東向き、5は実はいcursor、6で50円受領/23114円、7field。到着直後の通常Save93/独立Continueを受入。バッジ2・紙274一個・全party600byte/HP277/PP3,9,8,2を保持。2階到達/紙引渡しは未実行。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。52member/36画面/60+cold13入力。原controller38を再走せず保持、新影響controller15、新独立受入63。成功native2/初回未保存失敗native1/記録native0/旧受入再走0/ROM変更0。

## 未知受付での初回安全停止

初回run37188126911/job111394391365/artifact11298047173はfailureのまま保持。最初の北4歩、14,5のcoord event/var4061=0による受付を計画が未登録だった。20入力5画面/native1、通常保存0、全Save92/RTC保持。ROM-rootedのcoord3件と今回root7node/56命令を照合し、新しい50円受付だけに縮小。原script/test/preparationは改作せず、別admission controllerを作成。旧受入区間の再走ではない。

## 保存と差分

8〜12menu0→4、13/14確認、15〜29保存中。28は最終hashが一度現れてもcounter92/保存中文字。29counter93で別hash、30成功文言と最終hash→33field。全131088byteSaveRTCと全38400pixelが独立Continue/120frame後も一致。hash/counter単独で完了としない。

全party600byte/HP277/294/PP3,9,8,2/Bag/紙/PC/S61E/今回全RAM/legacy flags保持。所持金23164→23114、受付scriptのremove-money50と一致。4001:0→2はcoord位置分岐、4061:0→1は受付完了の実命令へbinding。4021:71→74/4022:3→1はowner未解明。42checksum、全Save7046byte/1785範囲、旧Save92bank57344byte保持。過去Save92のRAM/2056/3vars、Save91/89/87等の未解明差分は今回不変と混同しない。

## 次

[支払済み状態から2階への新9歩](../content/modernization/pr16_story_save93_next_route.json)。14,5東から西6南3で階段8,8へ。12/13/14,5のcoordは4061==0条件、現在1なので受付を再入力しない。最初の2階6/1到着後だけ保存。実到着/自動歩行は未確認。local2紙引渡しはさらに別区間。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save92']['record_completion']=prior_done
    state['story_save93']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[6,0],xy=[14,5],facing=4,rp=0,money=23114,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=50,museum_admission_var4061=1,museum_second_floor_accepted=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='新北4歩/50円受付とSave93。未知coordの初回未保存失敗を保持、影響scopeのみ修正。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='博物館50円受付Save93/6/0・14,5東。23114円/4061=1、36画面、全party/HP277/PP3,9,8,2/紙/バッジ2/今回RAM保持。4001/4061 owner一致、4021/4022と過去RAM/raw41/2056等未解明。次は2階9歩、紙引渡し未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MUSEUM_SECOND_FLOOR_FROM_SAVE93',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save93_accept.py','scripts/pr16_story_save93_admission_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,'content/modernization/pr16_story_save93_next_route.json'],stop_rule_ja='Save93/1階14,5東から西6南3の新9歩、4061=1確認。最初の2階6/1到着後だけ保存。旧北4歩/50円受付再走0。local2紙引渡しは後続別区間。未知NPC/境界/戦闘は縮小停止。')
    state['do_not_repeat'].append('Save93の60/cold13入力36画面52member/原38controller+新影響15/受入63を無影響再走しない。50円受付/4061=1/23114円、全party/今回RAM/S61E/legacyflags保持。28最終hash先行、29counter別hash、30成功→33field。初回未保存失敗native1をfailureのまま保持。4001/4061 owner一致、4021/4022と過去差分owner未解明。次は2階への新9歩。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='博物館50円受付Save93/6/0・14,5東。23114円/4061=1、party/紙/HP277/PP3,9,8,2/今回RAM保持。次は西6南3の新9歩で2階。紙引渡しは後続。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE|historical_code)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    entry=f"""
## {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Version: PR16-STORY-SAVE93
- Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Task: {TASK} / 博物館50円受付とSave93
- Status: DONE（50円受付/通常保存/独立Continue限定。2階は未完）
- Summary: 新北4歩/受付scriptの東向き、1階6/0・14,5東Save93。23164→23114円、4061=1。party600byte/HP277/PP3,9,8,2/Bag/紙/バッジ2/S61E/今回RAM/legacyflags保持。
- Files changed: 旧13歩計画/失敗原本を保持、新admission controller/owner/受入63/record/checkpoint/text証拠/次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。60+cold13入力36画面52member。原38controller+新影響15を原log継承、新受入63。記録native0/compile0/旧成功再走0。
- Evidence: 15〜29保存中。28最終hash先行でもcounter92/保存中文字、29counter93別hash→30成功/最終hash→33field。全SaveRTC/party/S61E/38400pixel保持。42checksum/7046byte1785範囲。
- Discovery: 初回run37188126911は14,5未知coordで安全停止、native1/20入力5画面/Save92全保持。ROM rootの50円受付と4061条件を同定。4001:0→2/4061:0→1のowner一致、4021/4022と過去Save92/91/89/87差分owner未解明。Save92記録run37187614083全11step終端同期。
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









