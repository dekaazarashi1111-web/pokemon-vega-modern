#!/usr/bin/env python3
"""北迂回の残68歩と南端到達のSave48原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save48_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE504-SAVE48'
OUT=ROOT/'.local/pr16-story-save48-record'

CODE={'scripts/pr16_story_save48_accept.py','scripts/pr16_story_save48_record.py','tests/test_pr16_story_save48_accept.py',a.VISUAL,'.github/workflows/pr16-story-save48-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE48_JA.md' and a.CP=='content/modernization/pr16_story_save48_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save48_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37138998824,'cd72e53291d03339df72007ada3c7463b962d10d',111249329799,['success']*11)
    handoff_done=inherited.terminal(37139239163,'dfbec07def05ffdc0c0acd57386cbb9f4b5eb8cc',111250043959,['success']*10)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save48_measure.',18)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==105 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save47全105member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save47/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==134 and len(z.namelist())==135 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save48member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==118 and visual['reviewed_screens']==dict(progress=list(range(116)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save48画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save48画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE48_ORIGINAL=str(original),PR16_SAVE47_INPUT=str(assets/'input.srm'),PR16_SAVE48_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save48_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==34 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 34 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'34成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save47-record-terminal.json','save47-handoff-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save48 artifact11279239942のstory-fast.srm（3095edcc45f08ff64cabe7a07c54098ec4b82f8ed874d6e103fafe9f7a2fb02f、131088bytes）だけから再開。map3/44・17,19南/下段3・party4/RP0・15224円・badge1・story4071=9/4072=1。Save47の右隣NPCを避け、11,5→11,4→12,4→13,4から北迂回残68歩/21turnを戦闘0で完走、通常Save48と独立Continue全SaveRTC一致。全party600byte/PP/HP/Bag/所持金/legacy flags/PC/S61E不変。オノノクスPP[11,10,15,20]、ミュウツーHP314/354・全PP0で回復未完。次は保存済map3/44高さ20/南connection offset-16→map3/23を参照し、17,19から南境界を越える新通常入力だけ。想定接続先33,0は静的候補で未受入。既存map3/23読取資料の北端通路26〜33と南connection→map3/2を使い、必要な新しい高度/ownerだけ追加照合。最初の新接続/戦闘/event/未通過境界または正常回復地点で保存。通常回復のHP/PPと原画が確認できるまで回復完了としない。新パネル判定a.classify_panelを継承、selectは実PP[11,10,15,20]に束縛。今回戦闘0で新判定/slot3選択のnative実証は追加0、Save47のslot0だけ受入済。97〜110部分write、110counter48でも未完、111成功文言/安定Flash→115field。aux4021=40→108/4022=0→3、RAMledger18/82差owner未解決、最終cold一致。Save47のraw used0誤陰性、Save46party2byte、Save39cold差/Save44並替差と旧失敗を保持。224+cold13入力/118画面/18controller34受入は無影響再走0。正規全国図鑑/通常story/自然EXP・技習得・進化/LuckyEgg/12case/Lv100soak/研究施設自然到達未完。ROM/host補充/故意全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用、新artifactは新save/画面/textだけ。一般CI既知qol_production.c不一致とfinalHEAD action_requiredは全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save48_accepted=True,north_detour_complete=True,south_connection_accepted=False,pp_recovery_accepted=False,healing_site_reached=False,normal_recovery_required=True,repaired_classifier_native_exercised=False,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),new_controller_tests=18,new_acceptance_tests=34,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f"# 北迂回の残68歩・南端・Save48 限定受入\n\n`{result['status']}`。504番道路11,5東から17,19南へ68歩/21方向転換。ジュネが残る右隣12,5を11,4→12,4→13,4で避け、北迂回を完走した。戦闘/eventなし。Save48/独立Continueを限定受入。南接続・回復施設・ミュウツーPP回復は未完。\n\nsource `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全134member/118画面/224+cold13入力。18新controller成功原log継承、新34原本受入/拒否だけ。native2/record0/旧受入再走0/ROM変更0。\n\n## 保存・全境界\n\n0〜89通常移動、90〜94通常menu実cursor0→4、95保存確認、96上書き確認。97〜110部分Flash14種類、110counter48はまだ部分write。111〜114成功文言/安定Flash、115field。cold0/1は17,19南で全SaveRTC一致。42checksum/旧Save47bank57344byte/6894byte1708範囲。\n\nparty全600byte・HP/PP/EXP/Bag/15224円/全legacy flag/PC/S61E/story4071=9/4072=1・badge1不変。オノノクスHP294/294・PP[11,10,15,20]、ミュウツーHP314/354・PP0。新パネル判定/残PP束縛controllerは18新試験で照合したが戦闘なしのため新判定/slot3選択のnative実証は追加0。Save47でのslot0実使用4回だけを継承し、原used0誤陰性を改作しない。\n\n補助var4021=40→108/4022=0→3、RAM ledger18/82差のowner未解決、最終/cold `{a.LEDGER}` 一致。Save46party2byte/途中ledger、Save39cold差/Save44並替差のowner未解明と旧失敗履歴を保持。\n\n地形1440cell/既存owner再採取0。69vertex候補を全通過したが、map3/23南接続はまだ未受入。保存済み72×20地形の17,19南端から南connection offset-16の想定33,0へ新規入力で続ける。想定座標を実到達へ昇格しない。\n\n## 次checkpoint送信前の確認\n\nAST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名、親artifact/run/source/SHA/counter/bank/member、ORIGINAL/ROM/親INPUT環境変数集合、送信tree/staged一覧、専用宛先/private/source guardと正確なunittest終端を照合。成功試験を記録器だけの失敗で再走しない。\n\n次: {goal}\n",encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save47']['record_completion']=prior_done
    state['story_save47']['handoff_completion']=handoff_done
    stage79=h.d.inputs.api('actions/runs/37139239131')
    need(stage79['status']=='completed'and stage79['conclusion']=='success'and stage79['head_sha']=='dfbec07def05ffdc0c0acd57386cbb9f4b5eb8cc','Save47同期source Stage79終端')
    state['story_save47']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save48']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,map=[3,44],xy=[17,19],facing=1,elevation=3,rp=0,money=15224,badge_count=1,story_vars={'4071':9,'4072':1},lead_species=850,lead_hp=[294,294],lead_pp=[11,10,15,20],mewtwo_hp=[314,354],mewtwo_pp=[0,0,0,0],normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,haxorus_move_ui_native_accepted=True,haxorus_all_four_slots_native_accepted=False,raw_save47_controller_false_negative_preserved=True,repaired_classifier_native_exercised=False,cave_crossing_complete=True,north_detour_complete=True,south_connection_accepted=False,trainer_victories=0,physical_flag_deltas=[],party_byte_deltas=[],party_unchanged=True,ram_ledger_change_owner_resolved=False,hm05_owned=True,hm05_taught_or_used=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='Save47から北迂回の残68歩/南端到達/Save48を限定受入。南接続/回復は未完。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='504北迂回の残68歩と南端17,19/Save48測定source。戦闘0・party/PP不変。回復未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_SOUTH_CONNECTION_FROM_SAVE48',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save48_accept.py','scripts/pr16_story_save48_measure.py','content/modernization/pr16_story_save44_evidence/inspection.json','content/modernization/pr16_story_save40_preparation.json'],stop_rule_ja='Save48/17,19南から南connectionの未通過入力だけ。最初の新接続/戦闘/event/未通過境界または通常回復地点で保存。回復未完。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='504北迂回残68歩を戦闘0で完走し南端17,19南/Save48独立Continueを限定受入。南接続/回復は未完。'
    state['do_not_repeat'].append('Save48の224/cold13入力118画面・18controller34受入を無影響再走しない。北迂回68歩/21turnで17,19南、戦闘0/party不変。97〜110部分write、110counter48は未完→111成功/安定→115field。南接続/回復と新classifierのbattle実証は未完。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 北迂回の残68歩・南端・Save48
- Version: story-north-detour-save48-v1
- Status: DONE（北迂回完走/保存/独立Continue限定受入、南接続と回復未完）
- Summary: 右隣NPC12,5を北へ避け11,5東→17,19南へ68歩/21方向転換、戦闘0。party600byte/HP/PP/全Bag/15224円/全legacy flags/PC/S61E不変。新パネル判定と親残PP[11,10,15,20]束縛の18新controller試験。戦闘なしのため新UI/slot3のnative実証は追加0。
- Files changed: Save48 controller/18新試験/34原本受入拒否試験/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、224/cold13入力/118画面/134member。18controller原log継承、新34受入、record native0。aux4021=40→108/4022=0→3とledger18/82差owner未解決。
- Evidence: 97〜110部分write、110counter48は部分write→111成功/安定Flash→115field。42checksum/旧bank57344byte/6894byte1708範囲/cold全SaveRTC一致。Save47 record37138998824/同期37139239163/Stage79run37139239131終端反映。旧失敗/Save47raw used0誤陰性/旧party差等owner未解明保持。地形1440再採取0。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actionsのみ。既存ROM/runtime/input非再配布。一般CI既知source不一致/finalHEAD action_requiredは全成功としない。merge/release/baseline変更0。
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

