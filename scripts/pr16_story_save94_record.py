#!/usr/bin/env python3
"""博物館2階到着・Save94原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import ast,datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save94_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-MUSEUM-SECOND-FLOOR-SAVE94'
OUT=ROOT/'.local/pr16-story-save94-record'

CODE={'scripts/pr16_story_save94_accept.py','scripts/pr16_story_save94_record.py','tests/test_pr16_story_save94_accept.py',a.VISUAL,'content/modernization/pr16_story_save94_next_route.json','.github/workflows/pr16-story-save94-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE94_JA.md' and a.CP=='content/modernization/pr16_story_save94_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save94_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37188979265,'ec3ca6e32007baa25d7b31b4c6829eac86caa949',111396971729,['success']*11)
    first_done=inherited.terminal(37189414997,'199e5b04dfcfe50a2692d4bd4a887d1e9a4dee44',111398292378,['success','success','failure','skipped','skipped','failure','success','success'])
    failed_done=inherited.terminal(37189493180,'dbb451ca07ef9746b437c4558582eecf6e054903',111398525799,['success','success','success','failure','skipped','success','success','success'])
    test_receipts=[]
    for job,total,passed,failed in [(111398292378,39,38,1),(111398525799,1,1,0),(a.JOB,3,3,0)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines();lines=[v.split('Z ',1)[-1]for v in log if ' ... 'in v and 'test_pr16_story_save94_measure.'in v]
        need(len(lines)==total and sum(v.endswith(' ... ok')for v in lines)==passed and sum(v.endswith(' ... FAIL')for v in lines)==failed,'初回38成功1失敗/修正1/東方向影響3の原log継承')
        need(any(('Ran '+str(total)+' test')in v for v in log),'unittest実行数')
        need(any(v.endswith('FAILED (failures=1)')for v in log)if failed else any(v.endswith(' OK')for v in log),'成功/失敗の正確な終端')
        test_receipts.append(dict(job=job,passed_tests=passed,executed_tests=total,failed_tests=failed,test_lines=lines,replayed_unchanged_passed_tests=0))
    _,failed_zip=a.transport.archive(11297508918,37189493180,dict(size=55924,sha256='25919cf20ac2c77d19934fe5723c536b63495293e2d200ee45ee447852b21b20'),'dbb451ca07ef9746b437c4558582eecf6e054903')
    failed_text={}
    with failed_zip:
        fm=json.loads(failed_zip.read('manifest.json'));need(len(fm)==20 and set(failed_zip.namelist())==set(fm)|{'manifest.json'},'階段南方向失敗全20member')
        for n,b in fm.items():need(identity(failed_zip.read(n))==b,'失敗member '+n)
        f=json.loads(failed_zip.read('failure.json'));e=json.loads(failed_zip.read('progress/execution.json'))
        need(f['native_processes']==1 and f['message']=='階段warp以外は追加入力しない'and e['initial_save']==e['final_save']==a.m.a.OUTPUT and e['observations']==13 and e['native_end']['inputs']==36,'失敗native1/通常保存0/全Save93保持')
        failed_text={n:failed_zip.read(n)for n in failed_zip.namelist()if Path(n).suffix in('.txt','.json')}
    history=dict(pre_native=dict(terminal=first_done,native_processes=0,artifact_missing=True,reason_ja='親route原本11998byteに対して作業materializationが末尾改行を1byte追加。元sourceへ書かずbindingと期待長だけ修正。38成功を再走しない。'),native=dict(terminal=failed_done,artifact=11297508918,archive=dict(size=55924,sha256='25919cf20ac2c77d19934fe5723c536b63495293e2d200ee45ee447852b21b20'),failure=f,execution=e,accepted=False,ordinary_saves=0,reason_ja='8,8は方向階段0x6C。旧南入力は1階8,9へ移動して停止。固定上流方向predicateへ照合し東入力へ修正。元runはfailure保持。'),controller_executions=43,controller_passed_executions=42,controller_failed_executions=1,final_controller_cases=41,changed_controller_cases_retested=2,unchanged_success_reruns=0)
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==52 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save93全52member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save93/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==56 and len(z.namelist())==57 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save94member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==41 and visual['reviewed_screens']==dict(progress=list(range(39)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save94画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save94画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE94_ORIGINAL=str(original),PR16_SAVE93_INPUT=str(assets/'input.srm'),PR16_SAVE94_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save94_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==67 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 67 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'67成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save93-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'failure-history.json',history)
    for name,raw in failed_text.items():
        dest=evidence/'failed-native'/name;dest.parent.mkdir(parents=True,exist_ok=True);raw.decode();need(b'\0'not in raw,'失敗原本textだけ');dest.write_bytes(raw)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save94 artifact11298740300のstory-fast.srm（131088bytes/SHA256 a306d040197e63d32a3a3d3380041af66c05ec17b8dbe52225320dad4046bb4f）だけから再開。西6南3/旋回2、階段8,8の東入力で2階6/1・11,8東へ到着。追加自動歩行なし。通常Save94/独立Continueを完了。次は新13歩でlocal2の北隣4,8へ、南向き会話で紙274一個の引渡しと4382setを最初の新境界として保存。505道路レンジャーは後続。受付/階段/旧成功を再走しない。23114円/4061=1/バッジ2/紙274一個/4383/未引渡し4382/未完4380/全party600byte/HP277/294/PP3,9,8,2保持。新RAM差分は1階8,7の観測10、physical2056:1→0、4001:2→0/4021:74→83/4022:1→0はowner未解明。過去Save93受付4001/4061のowner解決とは別。全41画面70+cold13入力、成功native2/初回未保存失敗native1/初回pre-native失敗1。controller最終41case、実行43=初回38成功1失敗+修正1成功+東方向影響3成功。新受入67、旧成功無影響再走0。20〜34保存中/34counter94途中hash、35成功文言/最終hash→38unlock。38画像には成功overlay残留、coldのfieldを別確認。cold263pixel差分はNPC矩形66,19〜94,38、全画面一致は未主張。全SaveRTC一致/S61E/PC保持。紙引渡し/全国図鑑/自然成長進化/全story/release未受入。入力ROM/runtime非再配布・host補充・ROM変更・merge/release/baseline変更0。一般CI既知qol_production.c不一致を全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save94_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=0,museum_admission_var4061=1,museum_second_floor_accepted=True,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,required_badge_flag=2083,required_badge_present=True,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=41,controller_executions=43,controller_passed_executions=42,controller_failed_executions=1,controller_repaired_cases=2,unchanged_controller_cases_replayed=0,new_acceptance_tests=67,successful_native_processes=2,prior_failed_native_processes=1,prior_pre_native_failed_attempts=1,total_native_processes=3,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 博物館2階・Save94限定受入

`{result['status']}`。Save93の支払済み1階14,5東から西6南3/旋回2、8,8で東入力を1回だけ行い、2階6/1・11,8東へ到着。追加自動歩行なし。通常Save94と独立Continueを受入。紙274一個・23114円/4061=1・バッジ2・全party600byte/HP277/PP3,9,8,2保持。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。56member/41画面/70+cold13入力。controller最終41case。43実行=初回38成功1失敗+修正1成功+東方向影響3成功。新独立受入67。成功native2/未保存失敗native1/pre-native失敗1/記録native0/旧成功無影響再走0。

## 診断履歴

run37189414997は親routeの末尾1byteを誤って加えたbindingで1検査だけ失敗、native0。原本11998byteへ修正し当該1検査だけ通過。run37189493180は13画面36入力/native1、方向階段8,8を南入力して1階8,9へ進み安全停止。Save93/RTC全保持。固定ROMのbehavior0x6Cとsource-lockのpret/pokefirered commit c75f352304d529f6ba92d4f74b9cf8b5c3810788にあるIsDirectionalStairWarpMetatileBehaviorを照合し、東入力だけへ修正。旧failure結論は保持。成功prefix0〜11を失敗原本と別に改作しない。

## 保存・表示・差分

13〜17menu0→4、18/19確認、20〜34保存中。34counter94でも途中hashと保存中文字、35最終hash/成功文言、38unlock field telemetry。ただし38画像にはcard/成功文言が残留。cold0/1のfield表示を別確認し、全画面一致とは主張しない。progress→cold差分19884/19904pixelはcard/成功文言の矩形内、cold間263pixelはNPC矩形x66..94/y19..38内。主人公・他地形は同一。全131088byteSaveRTCはcold/120frame後も一致。

全party/HP/PP/Bag/紙/所持金/受付4061/S61E/PC保持。42checksum/7062byte1772範囲、旧Save93bank57344byte保持。1階8,7の観測10でRAM ledger変化。physical2056:1→0、4001:2→0/4021:74→83/4022:1→0と今回RAMのruntime ownerは未解明。前回受付の4001/4061 ownerと混同しない。過去Save92/91/89/87等の未解明ownerも保持。

## 次

[local2への新13歩と紙引渡しowner](../content/modernization/pr16_story_save94_next_route.json)。2階11,8東から4,8へ、南向きに4,9のlocal2へ通常会話。バッジ2083と紙274を確認後、removeitem274x1/setflag4382の実命令がある。未実行の引渡しはまだ受入しない。NPCのruntime位置は初期座標と別に扱い、未知障害・会話・戦闘で縮小停止。505道路レンジャーはさらに後続。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save93']['record_completion']=prior_done
    state['story_save94']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[6,1],xy=[11,8],facing=4,rp=0,money=23114,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=0,museum_admission_var4061=1,museum_second_floor_accepted=True,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='新9歩と方向階段東入力、博物館2階Save94/独立Continue。初回pre-native1/未保存native1のfailure保持。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='博物館2階Save94/6/1・11,8東。新9歩/旋回2/東入力warp1、41画面。追加自動歩行なし。全party/紙/23114円/4061保持。RAM観測10/physical2056/3varsと過去owner未解明。35保存成功、38unlock画像overlay残留/coldNPC差分を限定記録。紙引渡し未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_LETTER_HANDOFF_FROM_SAVE94',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save94_accept.py','scripts/pr16_story_save94_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,'content/modernization/pr16_story_save94_next_route.json'],stop_rule_ja='Save94/2階11,8東から新13歩でlocal2北隣4,8へ。通常南向き会話、紙274消費/4382set後の最初のfieldだけ保存。505レンジャーは後続。未知NPC/境界/会話/戦闘で縮小停止。受付/階段を再走しない。')
    state['do_not_repeat'].append('Save94の70/cold13入力41画面56member、controller最終41case/43実行42成功1失敗、受入67を無影響再走しない。西6南3+東方向階段、6/1・11,8東。34counter途中hash、35成功/最終hash、38unlockだが画像にoverlay残留。coldNPC263pixel差分を全画面一致にしない。RAM観測10/2056/3varsと過去owner未解明。初回pre-native1/未保存native1はfailure保持。次はlocal2紙引渡し。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='博物館2階Save94/6/1・11,8東。23114円/4061=1/party/紙/HP277/PP3,9,8,2保持。RAM観測10/2056/3varsは未解明。次は新13歩でlocal2の紙引渡し。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    entry=f"""
## {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Version: PR16-STORY-SAVE94
- Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Task: {TASK} / 博物館2階とSave94
- Status: DONE（新9歩/方向階段/通常保存/独立Continue限定、紙引渡し未完）
- Summary: 西6南3/旋回2、階段8,8東入力で2階6/1・11,8東Save94。自動追加歩行なし。party600byte/HP277/PP3,9,8,2/紙/バッジ2/23114円/4061=1/S61E/PC保持。
- Files changed: Save94 preparation/measure/controller最終41case/受入67/record/checkpoint/text証拠/失敗履歴/次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。70+cold13入力41画面56member。controller43実行42成功1失敗、旧成功無影響再走0/新受入67。記録native0/compile0。
- Evidence: 20〜34保存中/34counter94途中hash、35最終hash成功文言、38unlockでも画像overlay残留。coldNPC263pixel矩形差分/全SaveRTC一致、全画面一致とは主張せず。42checksum/7062byte1772範囲。
- Discovery: 初回39controller中1失敗は親末尾byte誤binding、native0。修正1成功後の南方向階段失敗は36入力13画面/native1/Save93全保持。固定0x6C方向階段の東入力へ修正し影響3成功。今回RAM観測10/2056clear/3vars、過去owner未解明。Save93記録run37188979265全11step終端同期。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repoGitHub/Actions、検索語site:github.com/pret/pokefirered MB_UP_RIGHT_STAIR_WARP 0x6C。一次資料https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/field_control_avatar.c とsrc/metatile_behavior.c。source-lockへ固定して方向predicateを参照、ROM変更なし。入力ROM/runtime非再配布/merge/release/baseline変更0。一般CI既知不一致を全成功にしない。
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









