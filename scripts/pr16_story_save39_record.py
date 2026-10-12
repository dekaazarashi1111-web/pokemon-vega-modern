#!/usr/bin/env python3
"""504東端のSave39原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save39_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE504-SAVE39'
OUT=ROOT/'.local/pr16-story-save39-record'

CODE={'scripts/pr16_story_save39_accept.py','scripts/pr16_story_save39_record.py','tests/test_pr16_story_save39_accept.py',a.VISUAL,'.github/workflows/pr16-story-save39-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE39_JA.md' and a.CP=='content/modernization/pr16_story_save39_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save39_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37127976842,'da0ef846e31c2dc787ce15d18bd7a22c8d619720',111217116055,['success']*11)
    test_receipts=[]
    for job,suite,count in [(111217684192,'test_pr16_story_save39_measure.',11),(a.JOB,'test_pr16_story_save39_menu.',4)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==81 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save38全81member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save38/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==55 and len(z.namelist())==56 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save39member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==39 and visual['reviewed_screens']==dict(progress=list(range(37)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save39画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save39画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE39_ORIGINAL=str(original),PR16_SAVE38_INPUT=str(assets/'input.srm'),PR16_SAVE39_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save39_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==26 and b'\nOK\n'in unit.stderr and b'skipped'not in unit.stderr,'新Save39受入/拒否試験')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save38-record-terminal.json','first-failed-original.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save39 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map3/44（504番道路）・71,9西・party4/RP0・13796円・badge1・story4071=8/4072=1、HP320/354・PP[1,5,0,0]。'
      '503西端→504東端の通常connectionとSave39/独立Continueを限定受入、戦闘0。洞窟走破milestoneは前Save38で完了、全storyは未完。'
      '次は保存済72×20の504地形から先へ。70,9はcollision壁なので左を反復しない。71,9→71,10→70,10→69,10→68,10→67,10→66,10→65,10→64,10が静的候補。'
      '未読のelevation/behaviorと必要なownerだけ限定照合し、最初の新戦闘/新eventまたは通常回復地点で保存。PPをhost補充しない。'
      'Save39で改善した実画像menu_index/レポートcursor0→4確認を継承し、固定down4短間隔へ戻さない。'
      '67/cold13入力39画面/15controller26受入を無影響再走しない。初回90入力/56画面はTrainerCardに入り未保存で停止、原本artifact11275619886を保持。'
      '30Flash一時一致/counter38→31再差分/counter39→32安定/成功文言→36fieldを区別。cold RAM ledgerは進行時と異なりowner未解決、全Save/RTCは一致。'
      'Save36の227入力後parser失敗回復、Save37の24→25→26の区別、Save38のNPC103初戦/賞金220円/再戦1029未受入を保持。'
      '残件: 通常story、正規全国図鑑解禁、分離progression自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。'
      'trainer352未受入、HM05所持だけ・未習得/未使用。全story/一般CI全成功/製品release未完。clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save39_accepted=True,west_connection_accepted=True,route504_reached=True,cave_crossing_complete=True,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=15,new_acceptance_tests=26,prior_failed_native_processes=1,total_development_native_processes=3,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 503西端から504東端・Save39 限定受入

`{result['status']}`。Save38の503番道路9,76から西へ進み、通常connectionでmap3/44（504番道路）・71,9西に到達。通常Save39/独立Continueまで限定受入。新戦闘0。洞窟走破は前Save38で達成済みであり、全story・全国図鑑・自然成長は未完。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全55member、67/cold13入力、39画面。新15controller（初回11/画像menu4）は原log継承、新26原本受入/拒否試験、成功native2/未保存停止1/記録native0。ROM/fixture/compile/既受入再走0。map3/44の保存済72×20地形viewを再採取せず利用。

party600byte/HP320/PP[1,5,0,0]/全Bag/HM05/13796円/PC/S61E/全legacy flag/story4071=8/4072=1・badge1不変。補助var4021=30→40だけ、runtime owner未解決。42sector checksum/旧Save38bank57344byte/6785byte1672範囲/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400保持。

12〜16で通常menuのcursor0→4を画像確認。19〜29は部分write、30はcounter38のまま最終Flashと一時一致、31でcounter39/再差分、32〜35は成功文言/安定Flash、36field復帰。cold0/1は同じ504東端に復帰。進行RAM ledger `{a.LEDGER}` とcold `{a.COLD_LEDGER}` は異なる。owner未解決のまま保持し、全RAM不変とは主張しない。全Save/RTCはbyte一致。

初回run37128174890は504到達後に固定down4入力の1回が反映されずTrainerCardへ入った。90入力/56画面/native1、Save38全byte不変の未保存原本artifact11275619886を保持。通常menuを各行の実画像cursorで検証してからレポートだけに決定する修正を入れ、変更影響区間だけ再測定した。受入済みSave38以前は再走していない。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save38']['record_completion']=prior_done
    state['story_save39']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[3,44],xy=[71,9],facing=3,rp=0,money=13796,badge_count=1,story_vars={'4071':8,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,west_connection_accepted=True,route504_reached=True,cave_crossing_complete=True,story_flag4367_accepted=True,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='503西端から504東端の通常接続/Save39を限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='503西端→504東端・Save39測定source。全国図鑑/自然成長/全story未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stage79=h.d.inputs.api('actions/runs/37127976735')
    need(stage79['status']=='completed' and stage79['conclusion']=='success' and stage79['head_sha']=='da0ef846e31c2dc787ce15d18bd7a22c8d619720','Save38記録source Stage79終端')
    state['story_save38']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['next_action'].update(id='STORY_ROUTE504_EAST_FROM_SAVE39',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save39_measure.py','content/modernization/pr16_story_save39_preparation.json','content/modernization/pr16_story_acceleration_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save39の504東端から先へ。次候補71,9→71,10→64,10、左70,9の壁を反復しない。最初の新戦闘/eventまたは通常回復地点で限定保存。実画像menu cursor検証を継承、既受入を無影響再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='503西端→map3/44（504番道路）・71,9西/Save39・独立Continue受入。戦闘0/13796円/HP320/PP[1,5,0,0]。全国図鑑/自然成長/全storyは未完。'
    state['do_not_repeat'].append('Save39の67/cold13入力39画面/15controller26受入を無影響再走しない。30Flash一時一致→31再差分→32安定/成功文言→36fieldを区別。cold RAM ledger差はowner未解決、全SaveRTC一致。通常Saveは毎行menu cursor0→4を画像検証。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 503西端から504東端・Save39
- Version: story-route504-save39-v1
- Status: DONE（通常map接続/保存Continue限定受入）
- Summary: 503番道路9,76から西へ通常進行、504番道路map3/44・71,9西へ到達。戦闘0。全国図鑑/自然成長/全storyは未完。
- Files changed: Save39 controller/15変更試験/26受入拒否試験/record workflow、checkpoint/text原本、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、67/cold13入力/39画面/55member/成功native2。15controllerは原log継承、新26受入だけ実行、record native0。party600byte/HP320/PP[1,5,0,0]/Bag/13796円/PC/S61E/legacyflags/story不変。補助var4021=30→40だけ、owner未解決。42checksum/旧bank57344byte/6785byte1672範囲/cold全SaveRTC一致。30一時全Flash一致→31再差分→32成功文言/安定→36field。cold RAM ledger差はowner未解決として明示。
- History: 初回run37128174890は504到達後の固定down4の欠落でTrainerCardへ入り停止（90入力/56画面/native1/未保存/Save38全byte不変）。artifact11275619886保持。menu cursorを毎入力画像確認する修正の影響区間だけ検証。Save38 record37127976842/Stage79run37127976735のsuccess終端を反映。既受入ゲーム再走0、ROM/compile/fixture0、504地形再採取0。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actions原本のみ。既存ROM/runtime/input Save38再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
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
