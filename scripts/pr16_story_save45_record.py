#!/usr/bin/env python3
"""504西上段/下り階段のSave45原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save45_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE504-SAVE45'
OUT=ROOT/'.local/pr16-story-save45-record'

CODE={'scripts/pr16_story_save45_accept.py','scripts/pr16_story_save45_record.py','tests/test_pr16_story_save45_accept.py',a.VISUAL,'.github/workflows/pr16-story-save45-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE45_JA.md' and a.CP=='content/modernization/pr16_story_save45_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save45_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37135792701,'9665b1cbb327431fa1b7830f92fbe6de6b212884',111239944417,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save45_measure.',20)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==60 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save44全60member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save44/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==70 and len(z.namelist())==71 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save45member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==55 and visual['reviewed_screens']==dict(progress=list(range(53)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save45画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save45画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE45_ORIGINAL=str(original),PR16_SAVE44_INPUT=str(assets/'input.srm'),PR16_SAVE45_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save45_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==32 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 32 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'32成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save44-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save45 artifact11278563389のstory-fast.srm（e356f82361d9c0cccf984a7113b91324d42d6c3c15acf22b42a4fea3ce21927d、131088bytes）だけから再開。map3/44・26,12南/下段elevation3・party4/RP0・14264円・badge1・story4071=9/4072=1。西上段39,12から26,10→26,11下り階段→26,12下段を通常通過、19歩/7方向転換/戦闘0。全party600byte不変。先頭オノノクスHP294/294・PP[15,10,15,20]、2番目ミュウツーHP314/354・PP[0,0,0,0]のまま。道具/きのみ空、回復地点はまだ未到達。次は保存済み1440地形から26,12→25,12→24,12→23,12→22,12→22,11→22,10→9,10方面の下段西通路を有限候補にする。最初の新戦闘/event/未通過境界で通常Save。先頭オノノクスの新classifierは共通PPラベル/arrowに変更し20controller試験済みだが今回戦闘0で実技UIは未観測。新戦闘では実cursorと技名/残PPを画面と保存partyから照合。旧ミュウツー技名依存classifierやPP0入力loopを使わない。南側map3/23→3/2は静的接続候補であり回復施設の位置/到達は未受入。host補充/ROM編集/故意の全滅なし。98+cold13入力・55画面・20controller32受入試験を無影響再走しない。46最終Flashでもcounter44/書込中、47counter45、48成功文言→52field。全SaveRTC/cold RAM ledger一致、補助var4021=104→123/4022=0→4のowner未解明。Save44並替RAM ledger差、Save39旧差、Save40/41/42失敗回収履歴を保持。通常story/正規全国図鑑/自然EXP・技習得・進化/Lucky Egg/12ケース/Lv100soak/研究施設自然到達未完。全story/一般CI全成功/製品release未完。cleanROM二重生成/BPS固定/merge/release/baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save45_accepted=True,west_descent_stairs_accepted=True,pp_recovery_accepted=False,healing_site_reached=False,normal_recovery_required=True,haxorus_move_ui_native_accepted=False,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),new_controller_tests=20,new_acceptance_tests=32,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 西上段・下り階段・Save45 限定受入

`{result['status']}`。504番道路39,12西の上段から西へ進み、26,10→26,11の下り階段→26,12下段へ。19歩/7方向転換・戦闘0、通常Save45と独立Continueを限定受入。回復地点到達とPP回復は未完。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全70member/55画面/98+cold13入力。20controller成功原logを継承、新32原本受入/拒否試験だけ。native2/record0/旧受入再走0/ROM変更0。

先頭オノノクスHP294/294・PP[15,10,15,20]、2番目ミュウツーHP314/354・PP[0,0,0,0]、全party600byte不変。費用/道具消費0。バッグの道具/きのみは空のまま。控えの既存PPを回復済みと混同しない。

0〜26通常西進と階段を通過。27〜31通常menu cursor0→4。34〜45部分write12状態。46最終Flashに一致するがcounter44/書込み中、47counter45もまだ書込み文言。48〜51成功文言、52field。cold0/1は26,12南の下段。全55画面を目視。

全Bag/14264円/legacy flags/PC/S61E/story4071=9/4072=1/badge1不変。補助var4021=104→123/4022=0→4はruntime owner未解明。42sector checksum/旧Save44bank57344byte/6890byte1706範囲/cold全SaveRTC一致。全観測RAM ledger `{a.LEDGER}` も不変。Save44の並替時変化とSave39旧cold差owner未解明を保持。

保存済504地形1440cell/既存owner再採取0。高度4から階段0を経て下段3へ通常通過した範囲だけを受入。共通PPラベル/arrowの新classifierは20controller試験を通過したが、今回は戦闘0で実オノノクス技UI未観測。次の新戦闘で独立照合する。

## 次checkpoint送信前の確認

新counterのAST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名を照合。新counter ORIGINAL/ROMと親counter INPUTのenv集合、親artifact/run/source/save SHA/counter/bank世代/全member数を確認。送信treeとstaged一覧を明示し旧正本と交差0。専用宛先/private/source guardを維持。unittestはreturncode/全成功行/正確な終端で判定し、試験名skippedへのsubstring判定を禁止。成功試験は記録器だけの失敗で再走しない。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save44']['record_completion']=prior_done
    stage79=h.d.inputs.api('actions/runs/37135792451')
    need(stage79['status']=='completed'and stage79['conclusion']=='success'and stage79['head_sha']=='9665b1cbb327431fa1b7830f92fbe6de6b212884','Save44記録source Stage79終端')
    state['story_save44']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save45']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,map=[3,44],xy=[26,12],facing=1,elevation=3,rp=0,money=14264,badge_count=1,story_vars={'4071':9,'4072':1},lead_species=850,lead_hp=[294,294],lead_pp=[15,10,15,20],mewtwo_hp=[314,354],mewtwo_pp=[0,0,0,0],normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,haxorus_move_ui_native_accepted=False,cave_crossing_complete=True,upper_west_crossing_accepted=True,west_descent_stairs_accepted=True,hm05_owned=True,hm05_taught_or_used=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='西上段/下り階段Save45を限定受入。戦闘0/PP回復未完。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='504の39,12上段から26,12下段まで通常通過/Save45測定source。戦闘0、PP回復/回復地点未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_NORMAL_RECOVERY_TRAVEL_FROM_SAVE45',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save45_accept.py','scripts/pr16_story_save45_measure.py','content/modernization/pr16_story_save44_evidence/inspection.json','content/modernization/pr16_story_save40_preparation.json'],stop_rule_ja='先頭オノノクスで下段西通路の新しい区間だけ。最初の新戦闘/event/未通過境界で保存。回復未完、実技UI未観測を保持し、旧PP0選択loop/host補充/故意の全滅なし。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='504番道路26,12南/下段へ通常通過・Save45独立Continue受入。19歩/7方向転換/戦闘0。回復地点・ミュウツーPP回復未完。'
    state['do_not_repeat'].append('Save45の98/cold13入力55画面・20controller32受入を無影響再走しない。19歩/7方向転換・26,11下り階段/26,12下段、戦闘0。party/Bag/14264円不変。46最終Flashはcounter44/書込中、47counter45→48成功文言→52field。全SaveRTC/全RAM ledger一致。新オノノクス実技UI未観測、PP回復未完。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 西上段・下り階段・Save45
- Version: story-west-descent-save45-v1
- Status: DONE（西上段/下り階段/保存Continue限定受入。PP回復未完）
- Summary: 39,12上段から26,10→26,11階段→26,12下段へ。19歩/7方向転換、戦闘0、全party600byte不変。先頭オノノクス既存PP[15,10,15,20]、ミュウツーPP0を保持。
- Files changed: Save45 controller/20試験/32原本受入拒否試験/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、98/cold13入力/55画面/70member。20controller原log継承、新32受入、record native0。Bag/14264円/legacy flags/PC/S61E不変、4021=104→123/4022=0→4 owner未解明。42checksum/旧bank57344byte/6890byte1706範囲/cold全SaveRTC一致。
- Evidence: 34〜45部分write、46最終Flashでもcounter44、47counter45/書込中、48成功文言→52field。全RAM ledger一致。Save44 record37135792701/Stage79run37135792451終端反映。旧失敗履歴/Save39差/Save44並替差owner未解明を保持。地形1440再採取0。新classifierは単体のみ、実オノノクス技UIは未観測。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actionsのみ。既存ROM/runtime/input非再配布。一般CI既知source不一致保持、merge/release/baseline変更0。
- Next: {goal}
'''
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

