#!/usr/bin/env python3
"""館内の新10歩・動的通行境界Save60原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save60_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MANSION-DYNAMIC-EDGE-SAVE60'
OUT=ROOT/'.local/pr16-story-save60-record'

CODE={'scripts/pr16_story_save60_accept.py','scripts/pr16_story_save60_record.py','tests/test_pr16_story_save60_accept.py',a.VISUAL,'.github/workflows/pr16-story-save60-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE60_JA.md' and a.CP=='content/modernization/pr16_story_save60_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save60_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37157553408,'0aed5c751d11ffd57c205742a5b5249e893572fa',111304018725,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save60_measure.',26)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==69 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save59全69member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save59/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==59 and len(z.namelist())==60 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save60member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==44 and visual['reviewed_screens']==dict(progress=list(range(42)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save60画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save60画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE60_ORIGINAL=str(original),PR16_SAVE59_INPUT=str(assets/'input.srm'),PR16_SAVE60_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save60_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==51 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 51 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'51成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save59-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save60 artifact11286820207のstory-fast.srm（131088bytes/SHA256 40d65e6b41a49a59d295667ea30a88496da25c641ac8896059ed4d1fce196b0f）だけから再開。map1/59・14,6東。新10歩を限定受入、15,6への東入力3回は不通で停止。新戦闘0、全party600byte/HP288/294・PP15,10,15,11・ミュウツー全HP/PP・Bag/17904円/RP0/badge1/story4071=9/4072=1/RAM台帳保持。近傍移動NPCを実画面で観測、local6初期14,4/script141180503は静的候補でruntime同定/不通因果は未確定。次はcold画面の東隣NPCへの通常A会話を有限入力で確認するか、保存済通行可床14,5→15,5→16,5→16,6へ最小北迂回して未通過接尾辞を進める。目標はbehavior108階段30,10→map1/60warp2。最初の新event/戦闘/不通境界で保存。旧14,6→15,6東3回や旧20,24着地点不発を盲目的に再走しない。上階/紙未到達、紙ownerはmap1/60背景16,28/item274/flag4383と静的照合済み。26新controller/51新受入、75+cold13入力44画面59member/native2を無影響再走0。35で最終Flash一致でもcounter59/保存中、36counter60でも部分write、37成功→41field。全SaveRTC同一、progress/cold画面は近傍NPC211pixel/bbox129,58,143,80だけ異なり全画面同一としない。旧RAM/offset41/2056/aux4021/4022/404d/40ac未解明保持。Flash未使用/未習得、がくしゅうそうち未装備。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save60_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,normal_recovery_repeated=False,double_target_separation_native_exercised=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=26,controller_executions=26,unchanged_controller_cases_replayed=0,new_acceptance_tests=51,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 館の北廊下10歩・動的通行境界・Save60限定受入

`{result['status']}`。Save59の5,7北から北1/東9の通常10歩で14,6東へ。15,6への東入力3回で移動せず、最初の未通過境界として保存・独立Continue。新戦闘0、全party600bytesとHP288/294・PP[15,10,15,11]保持。上階/有効階段/像の紙は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。59member/44画面/75+cold13入力。新controller26case、51新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## 通常入力・保存・動的境界

0〜11暗所10歩と北→東の向き、12〜14の東入力3回は14,6を維持。静的15,6のcollision0/elevation3/behavior8を通過保証と混同しない。右隣のNPCが画面11〜14で移動、cold0/1では東隣。保存済map1/59のlocal6初期14,4/script141180503は候補にすぎず、runtime local ID/不通因果は未同定。

15〜19通常menu0→4、20確認/21上書き、22〜36保存中。35のFlashは一時的に最終hashと一致するがcounter59/保存中文字。36counter60でも再び部分write、37〜40成功文言、41field。progress14/41とcold0/1は各core内で同一。進行41対cold1の画面差は近傍NPC211pixel、bbox[129,58,143,80]だけ。プレイヤー/床/暗所と全SaveRTCは一致するが、全field同一とは主張しない。

## 限定差分と未完

全party600bytes/HP/PP/EXP/held item・全Bag/17904円/RP0・全legacy flags・PC/S61E全payload・旧Save59bank57344byte保持。42checksum、6959byte/1713範囲。aux4021=66→76のruntime owner未解明。RAM台帳は全観測でSave59と同一。過去のRAM台帳/offset41/2056/aux/40ac未解明を解決済みにしない。

15,6に向かう同じ東入力を盲目的に再生せず、新しい通常会話または最小北迂回で動的境界を越える。最初の新event/戦闘/境界で保存。有効階段/上階/紙は未到達、旧20,24着地点不発も再走しない。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。一般CI既知不一致/action_requiredを成功にしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save59']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37157553396');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='0aed5c751d11ffd57c205742a5b5249e893572fa','旧Stage79終端')
    state['story_save59']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save60']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,59],xy=[14,6],facing=4,rp=0,money=17904,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[15,10,15,11],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,trainer_victories=0,wild_victories=0,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='新10歩/動的通行境界/戦闘0/Save60。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='館の北廊下10歩/14,6東の動的境界/Save60。15,6東3回不通と近傍NPC移動を観測。上階/紙未到達。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_DYNAMIC_NPC_EDGE_FROM_SAVE60',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save60_accept.py','scripts/pr16_story_save60_measure.py',a.EVIDENCE+'/inspection.json','content/modernization/pr16_story_save57_preparation.json','content/modernization/pr16_story_save56_preparation.json'],stop_rule_ja='Save60の14,6東から新しい通常会話または最小北迂回。東3回不通を無条件再走せず、最初の新event/戦闘/未通過境界で保存。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='こころのやかた北廊下10歩でSave60。14,6東、不通15,6と近傍NPC移動。上階/像の紙未到達。'
    state['do_not_repeat'].append('Save60の75/cold13入力44画面59member/26controller/51受入を無影響再走しない。新10歩/新戦闘0/全party不変。15,6東3回は不通、同じ入力の盲目的再生をしない。35最終hash一致だが保存中→36counter部分write→37成功→41field。coldのNPC211pixel差/aux4021owner未解明。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 館の北廊下10歩と動的通行境界Save60
- Version: story-mansion-dynamic-edge-save60-v1
- Status: DONE（新10歩/不通境界/保存/独立Continue限定）
- Summary: Save59接尾辞10歩、14,6東。東15,6へ3回不通で停止、新戦闘0。全party600bytes/HP288/294/PP15,10,15,11/Bag/17904円/RP0/RAM台帳保持。上階/有効階段/紙未到達。
- Files changed: Save60 measure/26controller/51受入/record、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。75+cold13入力44画面59member。新26controller原log継承/51新受入拒否試験。record native0/compile0/既受入再走0。
- Evidence: 35最終Flash一致でもcounter59保存中、36counter60部分write→37成功→41field。全SaveRTC同一、cold画面差は周囲NPC211pixel/bbox129,58,143,80。local6静的候補だがruntime同定/不通因果は未確定。aux4021=66→76owner未解明。旧bank57344byte/42checksum/6959byte1713範囲。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actionsのみ。既存ROM/runtime/input非再配布。一般CI既知不一致/action_requiredは全成功にしない。merge/release/baseline変更0。
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



