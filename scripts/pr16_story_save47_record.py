#!/usr/bin/env python3
"""北迂回/ジュネ勝利のSave47原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save47_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE504-SAVE47'
OUT=ROOT/'.local/pr16-story-save47-record'

CODE={'scripts/pr16_story_save47_accept.py','scripts/pr16_story_save47_record.py','tests/test_pr16_story_save47_accept.py',a.VISUAL,'.github/workflows/pr16-story-save47-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE47_JA.md' and a.CP=='content/modernization/pr16_story_save47_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save47_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37137814123,'59f7774d76df9c093c06f7e54cfa11d2b74246e4',111245821131,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save47_measure.',12)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==75 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save46全75member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save46/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==105 and len(z.namelist())==106 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save47member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==90 and visual['reviewed_screens']==dict(progress=list(range(88)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save47画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save47画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE47_ORIGINAL=str(original),PR16_SAVE46_INPUT=str(assets/'input.srm'),PR16_SAVE47_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save47_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==44 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 44 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'44成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save46-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save47 artifact11279895650のstory-fast.srm（0ffabf8d049f74edaabdaf32a54872a267d9ea4c04f02845612295a9f30c6431、131088bytes）だけから再開。map3/44・11,5東/下段3・party4/RP0・15224円・badge1・story4071=9/4072=1。3,12から北迂回19歩/8方向転換→だいすきクラブのジュネ4体に勝利、通常Save47/cold同一。オノノクスHP294/294・PP[11,10,15,20]、ミュウツーHP314/354・全PP0で回復未完。初の実技UI35/42/49/57はslot0ドラゴンクローPP15/14/13/12、36/43/50/58通常使用、party全600byteの差は52=15→11だけ。原controllerはPPlabel矩形がタイプ/物理アイコン化した実UIをotherと誤陰性、raw used[0,0,0,0]を改作せず実4回と区別。次のcontrollerは新pr16_story_save47_accept.classify_panel（技名/種族/PP数値非依存のパネル上枠+実cursor、原90画面の4技/3交代を照合済）を使い、selectは親実PP[11,10,15,20]で上限を再束縛する。旧PPlabel/used0/古いPP15のclosureを流用しない。native4slot選択/他技使用は未受入。以後は11,5→12,5→13,5→13,4→14,4→14,3→18,3→18,4から東へ、34,13下段→34,16→25,17→25,15→17,15→17,19の保存地形迂回候補の未通過続きだけ。最初の新戦闘/event/未通過境界または正常回復地点で次Save。南接続map3/23→3/2は候補、回復施設未同定。今回170+cold13入力/90画面/12controller44受入を無影響再走しない。71〜82部分write、83counter47/最終Flash→84成功文言→87field。physicalflag1402だけ0→1、賞金960円、Bag/HP/EXP/PC/S61E/story不変。auxvar4021=22→40/4022=1→0とRAMledger31/51差のowner未解決、最終/cold一致。Save46 party2byte/途中ledger、Save39旧cold差/Save44並替差と旧失敗を保持。正規全国図鑑/通常story/自然EXP・技習得・進化/LuckyEgg/12case/Lv100soak/研究施設自然到達未完。一般CIqol_production.c source不一致とfinalHEAD action_requiredは全成功としない。ROM/host補充/故意の全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用、新artifactは新save/画面/textだけ。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save47_accepted=True,north_detour_partial_accepted=True,pp_recovery_accepted=False,healing_site_reached=False,normal_recovery_required=True,haxorus_move_ui_native_accepted=True,haxorus_all_four_slots_native_accepted=False,raw_controller_false_negative_preserved=True,repaired_classifier_offline_only=True,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),new_controller_tests=12,new_acceptance_tests=44,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f"# 北迂回・ジュネ勝利・Save47 限定受入\n\n`{result['status']}`。504番道路3,12西から11,5東へ下段19歩/8方向転換。だいすきクラブのジュネの4体に通常勝利し、Save47/独立Continueを限定受入。回復施設・ミュウツーPP回復は未完。\n\nsource `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全105member/90画面/170+cold13入力。12新controller成功原log継承、新44原本受入/拒否だけ。native2/record0/旧受入再走0/ROM変更0。\n\n## オノノクスの初実技UIと原controllerの誤陰性\n\n全90原画を確認。35/42/49/57はドラゴンクローslot0、PP15/14/13/12、36/43/50/58実使用。ココガラ/アクタシ/ビッパ/ファマー4体を撃破、60勝利文言、62賞金960円、63field。HP294/294、最終PP[11,10,15,20]。ミュウツーHP314/354・PP0。party差は600byte中52=15→11だけ、599byte不変。\n\n旧PP_LABELの矩形は現行UIのタイプ/物理アイコンを含み、4技画面ともotherへ誤分類した。原receiptのused[0,0,0,0]とkeep_current3件を改作せず保持。有限通常A入力がslot0を実使用したことをraw画面/4段階party hash/保存PP差で独立検証し、controller集計の0を採用しない。\n\n`classify_panel` は技名/種族/PP数値に依存しないパネル上枠と実cursorを用い、原88進行画面で実技4/交代3だけ検知する。新44試験にsynthetic4cursor/曖昧拒否/全実画像を含む。nativeでの4slot選択や他技使用を受入れたとはしない。次はこの判定を使い、PP上限を親[11,10,15,20]へ束縛。既存measurement sourceは不変。\n\n## 保存・境界\n\n64〜68通常menu cursor0→4、71〜82部分Flash12種類、83counter47/安定Flash/文言遷移、84〜86成功文言、87field。cold0/1は11,5東で全SaveRTC一致。42checksum/旧Save46bank57344byte/6902byte1708範囲。\n\nphysicalflag1402のみ0→1、14264→15224円、全Bag/HP/EXP/PC/S61E/story4071=9/4072=1・badge1不変。trainer数値IDは本checkpointでscript owner独立照合していない。補助var4021=22→40/4022=1→0、RAM ledger31/51差のowner未解決、最終/cold `{a.LEDGER}` 一致。Save46旧party2byte/途中ledger、Save39旧cold差/Save44並替差のowner未解明と旧失敗履歴を保持。\n\n地形1440cell/既存owner再採取0。88vertex候補のうち20vertex/19歩で最初の新trainer戦へ区切った。残りの到達/回復は未証明。\n\n## 次checkpoint送信前の確認\n\nAST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名、親artifact/run/source/SHA/counter/bank/member、ORIGINAL/ROM/親INPUT環境変数集合、送信tree/staged一覧、専用宛先/private/source guardと正確なunittest終端を照合。成功試験を記録器だけの失敗で再走しない。\n\n次: {goal}\n",encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save46']['record_completion']=prior_done
    stage79=h.d.inputs.api('actions/runs/37137814075')
    need(stage79['status']=='completed'and stage79['conclusion']=='success'and stage79['head_sha']=='59f7774d76df9c093c06f7e54cfa11d2b74246e4','Save46記録source Stage79終端')
    state['story_save46']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save47']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,map=[3,44],xy=[11,5],facing=4,elevation=3,rp=0,money=15224,badge_count=1,story_vars={'4071':9,'4072':1},lead_species=850,lead_hp=[294,294],lead_pp=[11,10,15,20],mewtwo_hp=[314,354],mewtwo_pp=[0,0,0,0],normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,haxorus_move_ui_native_accepted=True,haxorus_all_four_slots_native_accepted=False,raw_controller_false_negative_preserved=True,repaired_classifier_offline_only=True,cave_crossing_complete=True,north_detour_partial_accepted=True,trainer_name_ja='だいすきクラブのジュネ',trainer_victories=1,physical_flag_deltas=result['boundary']['physical_flag_deltas'],party_byte_deltas=result['boundary']['party_byte_deltas'],party_change_owner_resolved=True,ram_ledger_change_owner_resolved=False,hm05_owned=True,hm05_taught_or_used=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='北迂回/ジュネ通常勝利/初オノノクス実技UI/Save47を限定受入。controller誤陰性原本と回復未完を保持。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='504の北迂回19歩→ジュネ4体に勝利/Save47測定source。実技slot0PP15→11、原controller used0誤陰性を改作しない。回復未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_NORMAL_RECOVERY_TRAVEL_FROM_SAVE47',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save47_accept.py','scripts/pr16_story_save47_measure.py','content/modernization/pr16_story_save44_evidence/inspection.json','content/modernization/pr16_story_save40_preparation.json'],stop_rule_ja='Save47の11,5から先の北迂回残りだけ。新パネル+実cursor判定/親PP11を使用、最初の新戦闘/event/未通過境界で保存。回復未完、原used0誤陰性/ledger差owner未解決を保持。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='504番道路11,5東/下段へ19歩→ジュネ通常勝利、初オノノクス実技slot0とSave47独立Continueを限定受入。原controller used0誤陰性を保持。回復未完。'
    state['do_not_repeat'].append('Save47の170/cold13入力90画面・12controller44受入を無影響再走しない。北迂回19歩/8turn、ジュネ4体勝利、960円、slot0ドラゴンクロー4回/PP15→11。原controller used0は誤陰性で改作しない。71〜82部分write、83counter47/安定Flash→84成功文言→87field。実技UI4画面検証済、4slot native/回復は未受入。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 北迂回・ジュネ勝利・Save47
- Version: story-north-june-save47-v1
- Status: DONE（新trainer通常勝利/実技UI/保存/独立Continue限定受入、回復未完）
- Summary: 3,12西→11,5東へ19歩/8方向転換、ジュネ4体勝利、賞金960円。オノノクスHP294/294・実ドラゴンクロー4回/PP15→11、ミュウツーPP0。原controller used0誤陰性を改作せず、全原画/PP1byteから独立受入。後継用パネル+実cursor判定を新44試験で原画検証、native4slot選択未受入。
- Files changed: Save47 controller/12新試験/44原本受入拒否試験/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、170/cold13入力/90画面/105member。12controller原log継承、新44受入、record native0。全Bag/HP/EXP/PC/S61E不変、14264→15224円、physicalflag1402だけ0→1。aux4021=22→40/4022=1→0と途中ledger差owner未解決。
- Evidence: 71〜82部分write、83counter47/安定Flash→84成功文言→87field。42checksum/旧bank57344byte/6902byte1708範囲/cold全SaveRTC一致。Save46 record37137814123/Stage79run37137814075終端反映。旧失敗/Save46party2byte等owner未解明保持。地形1440再採取0。
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

