#!/usr/bin/env python3
"""戻り転送と野生戦のSave35原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save35_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-CAVE-RETURN-WILD-SAVE35'
OUT=ROOT/'.local/pr16-story-save35-record'

CODE={'scripts/pr16_story_save35_accept.py','scripts/pr16_story_save35_record.py','tests/test_pr16_story_save35_accept.py',a.VISUAL,'.github/workflows/pr16-story-save35-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE35_JA.md' and a.CP=='content/modernization/pr16_story_save35_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save35_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37123931026,'a4c565b152c26e00e5a68b381a9a564a389a45f9',111205330968,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    tests=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save35_transition_wait.' in v]
    need(len(tests)==5 and any('Ran 5 tests in 'in v for v in log) and any(v.endswith(' OK')for v in log),'変更5wait-only controller試験原本')
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==35 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save34全35member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save34/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==77 and len(z.namelist())==78 and set(z.namelist())==set(manifest)|{'manifest.json'},'全77member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==60 and visual['reviewed_screens']==dict(progress=list(range(58)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全60画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全60画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE35_ORIGINAL=str(original),PR16_SAVE34_INPUT=str(assets/'input.srm'),PR16_SAVE35_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save35_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==26 and b'\nOK\n'in unit.stderr and b'skipped'not in unit.stderr,'新26受入/拒否試験')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save34-record-terminal.json','failed-original.json','second-failed-original.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',dict(job=a.JOB,passed_tests=5,test_lines=tests,replayed_tests=0))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save35 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map1/73・16,5西・party4/RP0・13128円・badge1・story4071=7/4072=1・flag4367=1。戻り転送8,10→27,7と野生バルキー1勝、通常Save35/独立Continueまで限定受入。'
      'ミュウツーHP320/354・PP[1,13,0,0]。はどうだん選択2回のうち初回はひるみ、実PP消費1。host回復/PP/flag/var注入禁止。'
      '次は16,5→16,4→15,4→14,4→13,4→13,5西岩階段→13,6→12,6→11,6→10,6→9,6→8,6→8,5→7,5候補。失敗辺9,7→9,6は反復せず、戻り転送の今回完了prefixも再走しない。'
      '保存済920cells/map-load3node14命令/7,5event6nodeを再採取しない。8,5はflag4367により開く静的ownerを継承するが、西階段/実8,5/7,5event/trainer360は未受入。'
      '本成功115/cold13入力・60画面・全77member、旧controller19+4成功step継承/新5wait-only/新26受入。失敗run37124366728の56入力24画面、37124554654の57入力25画面はいずれも未保存native1で保持。'
      'party offset41/241の各+1と補助var4021=119→7/4022=1→0のruntime ownerは未解決で、自然成長受入へ昇格しない。'
      '保存成功文言54〜56/全Flash完成54/field復帰57/cold全SaveRTC一致。trainer352/360、洞窟出口4,19→map1/38、全国図鑑、自然成長進化、全storyは未完。既存ROM/runtime/inputはActionsだけ、新公開artifactは新save/画面/textのみ。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save35_accepted=True,return_teleport_accepted=True,west_stair_accepted=False,dynamic8_5_native_arrival=False,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=5,inherited_controller_tests=23,new_acceptance_tests=26,prior_failed_native_processes=2,total_development_native_processes=4,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 戻り転送・野生戦・Save35 限定受入

`{result['status']}`。Save34から8,10→27,7の戻り転送を通常入力で通り、16,5で野生バルキー♂Lv6に通常勝利。西階段手前で通常Save35/独立Continueへ区切った。西階段/8,5/7,5eventへ到達したとは主張しない。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全77member、115/cold13入力、60画面。23/24のfield移行/黒画面初期化は無入力で有限待機。25〜37で野生戦、32でひるんだため、はどうだんの2選択と実PP消費1を区別する。HP322→320、PP14→13。38でfield callback/lock0へ復帰し、wire field:falseは残留戦闘値によるため追加戦闘/未復帰としない。

42〜53は部分Flash write12状態、53はcounter35先行、54で全Flash完成と保存成功文言。54〜56の成功文言を目視確認、57でfield復帰。全Save/RTC独立Continue一致と42sector checksumを別途検証。旧Save34bank57344bytes・全Bag/HM05/13128円/PC/S61E・全legacy/storyflags/badge1維持。party差分4byteのうちoffset41/241の+1はruntime owner未解決、補助var4021=119→7/4022=1→0も別記する。自然成長を受入にしない。

最初のrun37124366728（f98a120a）は56入力/24画面/native1、次のrun37124554654（f1f7817a）は57入力/25画面/native1。両者とも野生戦開始callbackの検査器停止・Flash未変更・新保存なし。失敗の原本を保持した上で有限no-input待機だけを修正し、未受入区間をSave34から回復した。成功測定native2、合計開発native4。旧19controller/4transition成功stepは再実行せず、最新5wait-onlyと26独立受入/拒否試験を追加。ROM/compile/fixture/既受入ゲーム再走0。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save34']['record_completion']=prior_done
    state['story_save35']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[1,73],xy=[16,5],facing=3,rp=0,money=13128,badge_count=1,story_vars={'4071':7,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,return_teleport_accepted=True,west_stair_accepted=False,dynamic8_5_native_arrival=False,story_flag4367_accepted=True,cave_crossing_complete=False,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='戻り転送/野生1勝/Save35・独立Continueを限定受入。失敗2runを保持。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='戻り転送/野生バルキー1勝/16,5でSave35測定source。西階段/8,5/7,5event/洞窟出口/全story未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stage79=h.d.inputs.api('actions/runs/37123931149')
    need(stage79['status']=='completed' and stage79['conclusion']=='success' and stage79['head_sha']=='a4c565b152c26e00e5a68b381a9a564a389a45f9','前回pending Stage79の終端照合')
    state['story_save34']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['next_action'].update(id='STORY_CAVE_WEST_STAIRS_FROM_SAVE35',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save35_measure.py',a.m.PREP,a.m.TERRAIN],stop_rule_ja='Save35の16,5西から未完の西階段/動的8,5/7,5eventへ通常入力で進む。受入済戻り転送/野生戦を反復しない。PP[1,13,0,0]。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='戻り転送/野生1勝/Save35・独立Continue受入。16,5西・HP320/PP[1,13,0,0]。西階段/8,5/7,5eventは未完。'
    state['do_not_repeat'].append('Save35の115/cold13入力・60画面・28controller総数/新26受入を無影響再走しない。失敗2run合計native2と成功native2を分離。はどうだん選択2/ひるみ1/実PP消費1。西階段/8,5未到達。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 戻り転送・野生バルキー・Save35
- Version: story-cave-return-wild-save35-v1
- Status: DONE（戻り転送/野生1勝/通常保存Continue限定受入）
- Summary: 8,10→27,7を通常転送、16,5で野生バルキー勝利。ひるみ1/はどうだん選択2/実PP消費1を区別しHP320/PP[1,13,0,0]。西階段/8,5/event未到達。
- Files changed: Save35 controller/追加wait-only検査/受入26試験/record workflow、checkpoint/text原本、固定再開MD/JSON、両ログ。
- Verify: 測定run{a.RUN}/job{a.JOB}全8step成功、115/cold13入力/60画面/77member。部分write42〜53/counter35先行53、全Flash/成功文言54〜56/field復帰57。旧bank57344byte/42checksum/6941byte1770範囲差分/cold全SaveRTC一致。party4byte差分のoffset41/241+1と補助var2件のowner未解決。全Bag/13128円/PC/S61E/flag/badge不変。旧19+4controllerは成功step再利用、新5wait-onlyと26受入/拒否のみ。record native0。
- History: run37124366728は56入力24画面/native1、37124554654は57入力25画面/native1で未保存停止。両原本/失敗を保持し、no-input有限待機へ変更してSave34の未受入区間だけ回復。合計native4、受入済ゲーム再走0、ROM変更/fixture/compile0。Save34記録run37123931026とStage79 run37123931149のsuccess終端反映。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushし全text読戻し。
- Network: 同repo GitHub/Actions原本のみ。既存ROM/runtime/input Save34再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
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
