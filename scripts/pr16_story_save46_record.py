#!/usr/bin/env python3
"""504西上段/下り階段のSave46原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save46_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE504-SAVE46'
OUT=ROOT/'.local/pr16-story-save46-record'

CODE={'scripts/pr16_story_save46_accept.py','scripts/pr16_story_save46_record.py','tests/test_pr16_story_save46_accept.py',a.VISUAL,'.github/workflows/pr16-story-save46-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE46_JA.md' and a.CP=='content/modernization/pr16_story_save46_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save46_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37136570224,'62d8270a81f2255b35e35a1aa35245321f282dbe',111242199106,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save46_measure.',12)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==70 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save45全70member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save45/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==75 and len(z.namelist())==76 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save46member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==60 and visual['reviewed_screens']==dict(progress=list(range(58)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save46画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save46画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE46_ORIGINAL=str(original),PR16_SAVE45_INPUT=str(assets/'input.srm'),PR16_SAVE46_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save46_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==36 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 36 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'36成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save45-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save46 artifact11278684880のstory-fast.srm（d4a2e1f06ecbb1dee1bd54bda6962c1993b51711a09607954fe7b67d1c568e47、131088bytes）だけから再開。map3/44・3,12西/下段elevation3・party4/RP0・14264円・badge1・story4071=9/4072=1。26,12から下段西通路27歩/5方向転換/戦闘0で到達。先頭オノノクスHP294/294・PP[15,10,15,20]、ミュウツーHP314/354・PP0、回復施設/回復未完。party全600byteのうち141=7→8/241=105→106の2byteだけ通常歩行観測7で変化、HP/PP/EXP等598byte不変。なつき度候補だがowner未解決、自然成長受入とはしない。RAM ledgerは観測13で変わり最終/cold一致、owner未解決。次は3,12から北3,11→3,10→3,9→2,9→2,5→6,5→6,6→10,6方面の未通過下段通路を有限候補にする。静的地形だけでは南端17,19へ直進できず北迂回候補、実到達ではない。南map3/23→3/2は接続候補で回復施設未同定。最初の新戦闘/event/未通過境界で通常Save、PPラベル/実cursorの既受入classifierを継承し初のオノノクス実技UIを原画像/残PPと照合。旧ミュウツー技名依存/PP0選択loop/host補充/ROM変更/故意の全滅なし。109+cold13入力・60画面・12controller36受入を無影響再走しない。40〜52部分Flash、51/52同hashも書込み中、53counter46/最終Flash→54成功文言→57field。全SaveRTC/cold一致、補助var4021=123→22/4022=4→1 owner未解明。Save39旧差/Save44並替差と旧失敗回収履歴を保持。通常story/正規全国図鑑/自然EXP・技習得・進化/Lucky Egg/12ケース/Lv100soak/研究施設自然到達未完。一般CIqol_production.c source不一致とfinalHEAD action_requiredを過大主張せず保持。全story/一般CI全成功/製品release未完、cleanROM二重生成/BPS固定/merge/release/baseline切替は別途判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save46_accepted=True,lower_west_crossing_accepted=True,pp_recovery_accepted=False,healing_site_reached=False,normal_recovery_required=True,haxorus_move_ui_native_accepted=False,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),new_controller_tests=12,new_acceptance_tests=36,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f"# 下段西通路・Save46 限定受入\n\n`{result['status']}`。504番道路26,12南から3,12西へ、下段を27歩/5方向転換・戦闘0で通常通過。通常Save46/独立Continueを限定受入。回復施設到達・ミュウツーPP回復・オノノクス実技UIは未完。\n\nsource `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全75member/60画面/109+cold13入力。12新controller成功原log継承、新36原本受入拒否試験のみ。native2/record0/旧受入再走0/ROM変更0。\n\n先頭オノノクスHP294/294・PP[15,10,15,20]、2番目ミュウツーHP314/354・全PP0。party600byte中、141=7→8/241=105→106の2byteだけ通常歩行観測7で変化。なつき度候補だがowner未解決で、全party不変/自然成長受入とはしない。598byteは不変、HP/PP/EXP等に差なし。Bag/14264円/費用0・道具消費0。\n\n0〜32通常下段西進、33〜37menu実cursor0→4。40〜52部分Flash13観測/12種類。51/52同hashでも最終値ではなく書込み中。53counter46/最終Flash/文言遷移、54〜56成功文言、57field。cold0/1は3,12西で一致。全60原画を目視。\n\nlegacy flags/PC/S61E/story4071=9/4072=1/badge1不変。補助var4021=123→22/4022=4→1 owner未解明。42checksum/旧Save45bank57344byte/6892byte1708範囲/cold全SaveRTC一致。RAM ledgerは観測13で変化、最終/cold `{a.LEDGER}` 一致。party2byte差/途中ledgerのowner未解決を明示し、Save39旧cold差/Save44並替差のowner未解明も保持。\n\n保存済504地形1440cell/既存owner再採取0。全28vertexのelevation3だけを通常通過。既受入共通PPラベル/実cursor classifierはそのまま継承し、無影響20試験再走0。実オノノクス技UIは未観測のまま。\n\n## 次checkpoint送信前の確認\n\nAST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名、親artifact/run/source/save SHA/counter/bank/全member数、環境変数は新counter ORIGINAL/ROMと親counter INPUTの集合を照合。送信tree/staged一覧と旧正本の交差0、専用宛先/private/source guard、全成功行と正確なunittest終端を維持。記録器だけの失敗なら成功試験/nativeを再走しない。\n\n次: {goal}\n",encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save45']['record_completion']=prior_done
    stage79=h.d.inputs.api('actions/runs/37136570130')
    need(stage79['status']=='completed'and stage79['conclusion']=='success'and stage79['head_sha']=='62d8270a81f2255b35e35a1aa35245321f282dbe','Save45記録source Stage79終端')
    state['story_save45']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save46']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,map=[3,44],xy=[3,12],facing=3,elevation=3,rp=0,money=14264,badge_count=1,story_vars={'4071':9,'4072':1},lead_species=850,lead_hp=[294,294],lead_pp=[15,10,15,20],mewtwo_hp=[314,354],mewtwo_pp=[0,0,0,0],normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,haxorus_move_ui_native_accepted=False,cave_crossing_complete=True,lower_west_crossing_accepted=True,party_byte_deltas=result['boundary']['party_byte_deltas'],party_change_owner_resolved=False,ram_ledger_change_owner_resolved=False,hm05_owned=True,hm05_taught_or_used=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='下段西通路Save46を限定受入。戦闘0/PP回復未完。party2byteと途中RAM ledger差を保持。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='504の26,12下段から3,12西へ通常通過/Save46測定source。戦闘0、PP回復/回復地点未完。party2byteと途中RAM ledger差のowner未解決。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_NORMAL_RECOVERY_TRAVEL_FROM_SAVE46',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save46_accept.py','scripts/pr16_story_save46_measure.py','content/modernization/pr16_story_save44_evidence/inspection.json','content/modernization/pr16_story_save40_preparation.json'],stop_rule_ja='Save46から未通過北側迂回候補だけ。最初の新戦闘/event/未通過境界で通常Save。回復未完/実技UI未観測/party2byteとledgerのowner未解決を保持、旧PP0 loop/host補充/故意の全滅なし。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='504番道路3,12西/下段へ27歩・Save46独立Continue受入。戦闘0/回復未完。party2byteと途中RAM ledger差のowner未解決。'
    state['do_not_repeat'].append('Save46の109/cold13入力60画面・12controller36受入を無影響再走しない。27歩/5方向転換/戦闘0。HP/PP/Bag/14264円不変だがparty141=7→8/241=105→106と途中RAM ledger差を保持。40〜52部分write、53counter46/最終Flash→54成功文言→57field。回復/オノノクス実技UI未完。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 下段西通路・Save46
- Version: story-lower-west-save46-v1
- Status: DONE（下段西通路/通常保存/独立Continue限定受入、回復未完）
- Summary: 26,12南から3,12西へ27歩/5方向転換、戦闘0。HP/PP不変、party141=7→8/241=105→106の2byte変化、owner未解決。最終/cold ledger一致、途中変化owner未解決。回復/オノノクス実技UI未完。
- Files changed: Save46 controller/12新試験/36原本受入拒否試験/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、109/cold13入力/60画面/75member。12controller原log継承、新36受入、record native0。Bag/14264円/legacy flags/PC/S61E不変。4021=123→22/4022=4→1 owner未解明。42checksum/旧bank57344byte/6892byte1708範囲/cold全SaveRTC一致。
- Evidence: 40〜52部分write、53counter46/最終Flash→54成功文言→57field。Save45 record37136570224/Stage79run37136570130終端反映、旧失敗履歴/旧owner未解明保持。地形1440再採取0/旧20classifier試験再走0。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actionsのみ。既存ROM/runtime/input非再配布。一般CI既知source不一致/finalHEAD action_requiredを保持、merge/release/baseline変更0。
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

