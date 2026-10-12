#!/usr/bin/env python3
"""戻り転送と野生戦のSave38原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save38_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE503-SAVE38'
OUT=ROOT/'.local/pr16-story-save38-record'

CODE={'scripts/pr16_story_save38_accept.py','scripts/pr16_story_save38_record.py','tests/test_pr16_story_save38_accept.py',a.VISUAL,'.github/workflows/pr16-story-save38-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE38_JA.md' and a.CP=='content/modernization/pr16_story_save38_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save38_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37126518059,'db7fbddd8929cf457be95b19d22be5831d22d2eb',111212777875,['success']*11)
    test_receipts=[]
    for job,suite,count in [(111214539355,'test_pr16_story_save38_measure.',10),(111215039388,'test_pr16_story_save38_door.',3),(a.JOB,'test_pr16_story_save38_event.',3)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==48 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save37全48member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save37/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==81 and len(z.namelist())==81+1 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save38member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==62 and visual['reviewed_screens']==dict(progress=list(range(60)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save38画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save38画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE38_ORIGINAL=str(original),PR16_SAVE37_INPUT=str(assets/'input.srm'),PR16_SAVE38_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save38_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==28 and b'\nOK\n'in unit.stderr and b'skipped'not in unit.stderr,'新Save38受入/拒否試験')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save37-record-terminal.json','first-failed-original.json','second-failed-original.json','preflight-failure.json','controller-receipts.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save38 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map3/21・9,76南・party4/RP0・13796円・badge1・story4071=8/4072=1、HP320/354・PP[1,5,0,0]。'
      '洞窟本区画→南出口部屋→外503番道路の通常接続とSave38/独立Continueを限定受入。洞窟走破milestone完了。出口trainer103（じゅくがえり・モトナリ）のココガラLv7/ポッポLv11/ビッパLv9に3手で勝利、賞金220円。全storyは未完。'
      '次は保存済503番道路南部viewから西側のmap3/44接続を通常進行し、最初の新event/新戦闘または回復地点で限定checkpoint。必要な未読隣接mapだけ採取。'
      'host回復/PP/flag/var注入は禁止。既受入の西側event・trainer360・洞窟本区画・Save38入力は無影響再走しない。'
      'Save38初回は矢印tile4,6で追加南入力がなく待機停止。未保存原本/失敗を保持し、変更影響区間だけ回復した。'
      'Save36の227完走入力後parser失敗回復とSave37の24一時Flash一致→25再差分→26安定→30fieldを保持。'
      '残件: 通常story継続、正規全国図鑑解禁、分離progressionの自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。'
      'trainer352未受入。HM05は所持だけ・未習得/未使用。全story/一般CI全成功/製品releaseは未完。'
      'clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save38_accepted=True,cave_interior_crossing_complete=True,outside_route503_reached=True,cave_crossing_complete=True,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=16,new_acceptance_tests=28,prior_failed_native_processes=2,total_development_native_processes=4,preflight_failed_native_processes=0,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 洞窟南出口から503番道路・Save38 限定受入

`{result['status']}`。Save37の南出口部屋6,4から6,5→5,5→4,5→4,6へ歩き、出口矢印から南へ追加通常入力して屋外map3/21・9,76南へ到達。出口trainer103に正規勝利・賞金220円の後、通常Save38/独立Continueまで限定受入。洞窟本区画・南出口部屋・外503番道路の接続milestoneは完了。全story・全国図鑑・自然成長は未完。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全81member、122/cold13入力、62画面。新16controller（初回10/矢印修正3/NPC修正3）は原log継承、新28原本受入/拒否試験、成功native2/未保存停止2/記録native0。ROM/fixture/compile/既受入再走0。失敗原本で採取したmap3/21を再採取せず再利用。NPC10のscript graph6nodeを新規採取し、trainer103初戦/1029再戦を分離。measurementのnew_script_nodes=0は継承値の誤記であり、保存graph6nodeを正としてcheckpointで明示訂正。原本は改作しない。

party600byte差分はPP8→5の1byteだけ、HP320/354保持。Bag/HM05/PC/S61E不変、13576→13796円（賞金220円）。legacyflag1383=0→1（trainer103）と2056=1→0、補助var4021=26→30/4022=2→0/40ae=79→91、補助runtime owner未解決。story4071=8/4072=1・badge1・全国図鑑magic0/404e0/flag8400保持。42sector checksum/旧bank57344byte/6840byte1710範囲/cold全SaveRTC一致。

43〜54は書込中12画面/11Flash状態（53/54同じ）。55でcounter38/安定全Flashだが台詞移行中、56〜58保存成功文言、59field復帰。Save37の24一時一致→25再差分→26安定とは異なる。

初回run37127113183は出口矢印tile4,6で待機上限となった。Save37全byte不変/未保存の原本artifact11275422186を保持。待機を増やす代わりに実画面の下矢印から通常南入力1回を追加し、変更影響区間だけ検証した。第二native run37127420854は屋外到達したがNPC会話で未保存停止、artifact11275593672を保持。会話/戦闘を含む影響区間だけ修正。中間run37127280308はguardの変更集合基準不一致でnative0。既受入Save37以前は再走していない。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save37']['record_completion']=prior_done
    state['story_save38']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[3,21],xy=[9,76],facing=1,rp=0,money=13796,badge_count=1,story_vars={'4071':8,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,cave_interior_crossing_complete=True,outside_route503_reached=True,cave_crossing_complete=True,story_flag4367_accepted=True,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='南出口部屋から屋外503番道路の通常接続/Save38を限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='南出口部屋→屋外503番道路・Save38測定source。洞窟走破接続完了、全国図鑑/自然成長/全story未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stage79=h.d.inputs.api('actions/runs/37126518074')
    need(stage79['status']=='completed' and stage79['conclusion']=='success' and stage79['head_sha']=='db7fbddd8929cf457be95b19d22be5831d22d2eb','Save37記録source Stage79終端')
    state['story_save37']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['next_action'].update(id='STORY_ROUTE503_SOUTH_FROM_SAVE38',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save38_measure.py','content/modernization/pr16_story_save38_preparation.json','content/modernization/pr16_story_acceleration_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save38屋外503番道路南部から通常接続へ。最初の新event/新戦闘または回復地点で限定保存。洞窟走破と全story完了を区別。既受入を無影響再走せず正規UIのみ。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='南出口部屋→屋外map3/21・9,76南/Save38・独立Continue受入。洞窟走破milestone完了。13796円・HP320/PP[1,5,0,0]。全国図鑑/自然成長/全storyは未完。'
    state['do_not_repeat'].append('Save38の122/cold13入力・62画面・16controller/28受入を無影響再走しない。初回矢印出口待機停止の未保存原本を保持。外503番道路の通常接続は受入、全story未完。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 洞窟南出口から屋外503番道路・Save38
- Version: story-route503-save38-v1
- Status: DONE（通常屋外接続/保存Continue限定受入）
- Summary: 南出口部屋の矢印tileから通常南入力で屋外map3/21・9,76南へ到達。洞窟走破milestone完了。全国図鑑/自然成長/全storyは未完。
- Files changed: Save38 controller/16変更試験/28受入拒否試験/record workflow、checkpoint/text原本、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、122/cold13入力/62画面/81member/成功native2。16controllerは原log継承、新28受入だけ実行、record native0。party600byte差分はPP8→5の1byteだけ、HP320/354保持。Bag/HM05/PC/S61E不変、13576→13796円（賞金220円）。legacyflag1383=0→1（trainer103）と2056=1→0、補助var4021=26→30/4022=2→0/40ae=79→91、補助runtime owner未解決。story4071=8/4072=1・badge1・全国図鑑magic0/404e0/flag8400保持。42sector checksum/旧bank57344byte/6840byte1710範囲/cold全SaveRTC一致。 43〜54は書込中12画面/11Flash状態（53/54同じ）。55でcounter38/安定全Flashだが台詞移行中、56〜58保存成功文言、59field復帰。Save37の24一時一致→25再差分→26安定とは異なる。
- History: 初回run37127113183は出口矢印tileで待機停止（native1/Save37全byte不変/未保存）。artifact11275422186を保全。第二native run37127420854/artifact11275593672は屋外NPC会話待ちで未保存停止（native1）、中間run37127280308はguard基準修正前のnative0失敗。通常南入力および新会話/戦闘の変更影響区間だけ検証。Save37記録run37126518059/Stage79run37126518074のsuccess終端を反映。旧失敗・Save36 parser回復・Save37一時Flash一致の区別を保持、既受入ゲーム再走0、ROM/compile/fixture0。503番道路view再採取0。新NPC owner6nodes/診断0を採取。測定new_script_nodes=0は6への訂正をcheckpointへ記録し原本は保持。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actions原本のみ。既存ROM/runtime/input Save37再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
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
