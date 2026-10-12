#!/usr/bin/env python3
"""505番道路への通常南接続のSave49原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save49_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-SOUTH-SAVE49'
OUT=ROOT/'.local/pr16-story-save49-record'

CODE={'scripts/pr16_story_save49_accept.py','scripts/pr16_story_save49_record.py','tests/test_pr16_story_save49_accept.py',a.VISUAL,'.github/workflows/pr16-story-save49-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE49_JA.md' and a.CP=='content/modernization/pr16_story_save49_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save49_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37141095775,'eb38b4ea9b668e2c8121dfd47860a9d4d456e58c',111255517151,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save49_measure.',12)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==134 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save48全134member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save48/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==44 and len(z.namelist())==45 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save49member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==29 and visual['reviewed_screens']==dict(progress=list(range(27)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save49画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save49画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE49_ORIGINAL=str(original),PR16_SAVE48_INPUT=str(assets/'input.srm'),PR16_SAVE49_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save49_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==34 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 34 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'34成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save48-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save49 artifact11280742739のstory-fast.srm（21374dbfbc9e38f0febf16304706b7f3b14feacf204d5956bd622dcf941b1a04、131088bytes）だけから再開。504南端17,19から通常南1入力で505番道路map3/23・33,0南/高度3へ接続、通常Save49/独立Continue全SaveRTC一致を限定受入。party4/RP0/15224円/badge1/story4071=9/4072=1、party600byte/HP/PP/Bag/legacy flags/PC/S61E不変。オノノクスPP[11,10,15,20]、ミュウツーHP314/354・全PP0で通常回復未完。次は既存map3/23 collision_gridの北端26〜33通路と南connection→map3/2を再利用し、33,0以南の新しい高度/ownerだけ追加読取して通常回復地点を目指す。最初の新戦闘/event/未通過境界/接続または正常回復地点で保存。未観測経路や回復を受入にしない。新classify/残PP選択はSave48の実装を継承、今回戦闘0で追加native実証0。20最終Flash一時一致でもcounter48/書込中、21counter49で再差分、22成功文言/安定Flash→26field。aux4021=108→109/4022=3→4はowner未解決、全RAMledger不変/最終cold一致。旧Save48途中ledger差/Save47raw used0誤陰性/Save46party2byte/Save39cold差/Save44並替差と旧失敗を保持。47+cold13入力/29画面/12controller34受入は無影響再走0。正規全国図鑑/全story/自然EXP・技習得・進化/LuckyEgg/12case/Lv100soak/研究施設自然到達未完。ROM/host補充/故意全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用、新artifactは新save/画面/textだけ。一般CI既知qol_production.c不一致とfinalHEAD action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save49_accepted=True,north_detour_complete=True,south_connection_accepted=True,pp_recovery_accepted=False,healing_site_reached=False,normal_recovery_required=True,repaired_classifier_native_exercised=False,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),new_controller_tests=12,new_acceptance_tests=34,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f"# 505番道路への通常南接続・Save49 限定受入\n\n`{result['status']}`。504番道路17,19南から1歩で505番道路map3/23・33,0南へ。戦闘/eventなし。通常Save49/独立Continueを限定受入。回復施設・ミュウツーPP回復は未完。\n\nsource `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全44member/29画面/47+cold13入力。12新controller成功原log継承、新34原本受入/拒否だけ。native2/record0/旧受入再走0/ROM変更0。\n\n## 保存・全境界\n\n0は504、1は505へ初接続。2〜6通常menu実cursor0→4、7保存確認、8上書き確認。9〜21書込中13種類。20最終Flash一時一致でもcounter48、21counter49で再差分。22〜25成功文言/安定Flash、26field。cold0/1は33,0南で全SaveRTC一致。42checksum/旧Save48bank57344byte/6894byte1700範囲。\n\nparty全600byte・HP/PP/EXP/Bag/15224円/全legacy flag/PC/S61E/story4071=9/4072=1・badge1不変。オノノクスHP294/294・PP[11,10,15,20]、ミュウツーHP314/354・PP0。親Save48の新パネル判定と残PP選択を継承。戦闘なしのため新判定/slot3選択のnative実証は追加0。Save47でのslot0実使用4回だけを継承し、原used0誤陰性を改作しない。\n\n補助var4021=108→109/4022=3→4のowner未解決、全RAM ledger `{a.LEDGER}` 不変/最終cold一致。Save48途中ledger差/Save46party2byte/Save39cold差/Save44並替差のowner未解明と旧失敗履歴を保持。\n\n保存済みmap3/23 map viewとmap3/44地形1440cellを再利用。新規追加読取は接続先33,0の1cellだけ、高度3/衝突0/behavior33。南接続は通常入力で確認済みだが33,0以南は未受入。\n\n## 次checkpoint送信前の確認\n\nAST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名、親artifact/run/source/SHA/counter/bank/member、ORIGINAL/ROM/親INPUT環境変数集合、送信tree/staged一覧、専用宛先/private/source guardと正確なunittest終端を照合。成功試験を記録器だけの失敗で再走しない。\n\n次: {goal}\n",encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save48']['record_completion']=prior_done
    stage79=h.d.inputs.api('actions/runs/37141095577')
    need(stage79['status']=='completed'and stage79['conclusion']=='success'and stage79['head_sha']=='eb38b4ea9b668e2c8121dfd47860a9d4d456e58c','Save48記録source Stage79終端')
    state['story_save48']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save49']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,map=[3,23],xy=[33,0],facing=1,elevation=3,rp=0,money=15224,badge_count=1,story_vars={'4071':9,'4072':1},lead_species=850,lead_hp=[294,294],lead_pp=[11,10,15,20],mewtwo_hp=[314,354],mewtwo_pp=[0,0,0,0],normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,haxorus_move_ui_native_accepted=True,haxorus_all_four_slots_native_accepted=False,raw_save47_controller_false_negative_preserved=True,repaired_classifier_native_exercised=False,cave_crossing_complete=True,north_detour_complete=True,south_connection_accepted=True,trainer_victories=0,physical_flag_deltas=[],party_byte_deltas=[],party_unchanged=True,ram_ledger_unchanged=True,ram_ledger_change_owner_resolved=False,hm05_owned=True,hm05_taught_or_used=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='Save48から通常南1接続で505番道路33,0へ、Save49を限定受入。通常回復は未完。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='505番道路への新南接続と33,0/Save49測定source。戦闘0・party/PP不変。回復未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_RECOVERY_ON_ROUTE505_FROM_SAVE49',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save49_accept.py','scripts/pr16_story_save49_measure.py','content/modernization/pr16_story_save44_evidence/inspection.json'],stop_rule_ja='Save49/map3/23の33,0南から先だけ。既存地形資料を使い必要な高度/ownerだけ追加読取。最初の新戦闘/event/未通過境界/接続または正常回復地点で保存。回復未完。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='通常南1接続で505番道路33,0南へ到達しSave49独立Continueを限定受入。回復は未完。'
    state['do_not_repeat'].append('Save49の47/cold13入力29画面・12controller34受入を無影響再走しない。504から505へ南1接続で33,0南、戦闘0/party/ledger不変。20Flash一時一致/counter48→21counter49再差分→22成功/安定→26field。回復と新classifierのbattle実証は未完。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 505番道路への通常南接続・Save49
- Version: story-south-connection-save49-v1
- Status: DONE（505接続/保存/独立Continue限定受入、通常回復未完）
- Summary: 504南端17,19から南1入力で505/map3/23・33,0南、戦闘0。party600byte/HP/PP/全Bag/15224円/全legacy flags/PC/S61E/全RAMledger不変。親Save48のパネル判定と実PP選択を継承、battle native実証追加0。
- Files changed: Save49 controller/12新試験/34原本受入拒否試験/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、47/cold13入力/29画面/44member。12controller原log継承、新34受入、record native0。aux4021=108→109/4022=3→4はowner未解決。
- Evidence: 9〜21書込中13種類。20最終Flash一時一致/counter48→21counter49再差分→22成功/安定→26field。42checksum/旧bank57344byte/6894byte1700範囲/cold全SaveRTC一致。Save48 record37141095775/Stage79run37141095577終端同期。旧失敗/旧party・ledger差owner未解明保持。新接続先1cellだけ追加読取。
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

