#!/usr/bin/env python3
"""戻り転送と野生戦のSave36原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save36_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-CAVE-TRAINER360-EVENT-SAVE36'
OUT=ROOT/'.local/pr16-story-save36-record'

CODE={'scripts/pr16_story_save36_accept.py','scripts/pr16_story_save36_record.py','tests/test_pr16_story_save36_accept.py',a.VISUAL,'.github/workflows/pr16-story-save36-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE36_JA.md' and a.CP=='content/modernization/pr16_story_save36_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save36_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success','success','success','failure','skipped','success','success','success'])
    prior_done=inherited.terminal(37125070319,'091d51ca2184ab1befb931ec804232a824e90eb1',111208592840,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    tests=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save36_event_entry.' in v]
    need(len(tests)==4 and any('Ran 4 tests in 'in v for v in log) and any(v.endswith(' OK')for v in log),'変更4event-entry controller試験原本')
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==77 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save35全77member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save35/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==130 and len(z.namelist())==131 and set(z.namelist())==set(manifest)|{'manifest.json'},'全130member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==114 and visual['reviewed_screens']==dict(progress=list(range(112)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全114画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全114画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE36_ORIGINAL=str(original),PR16_SAVE35_INPUT=str(assets/'input.srm'),PR16_SAVE36_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save36_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==34 and b'\nOK\n'in unit.stderr and b'skipped'not in unit.stderr,'新34受入/拒否試験')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['failure.json','manifest.json','save35-record-terminal.json','failed-original.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'record-preflight-failure.json',inherited.terminal(37125775957,'dc8a90c62bf675887503b7cca4c6a22505e8e251',111210655527,['success','success','success','failure','skipped','skipped','skipped','skipped','success','success','success']))
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',dict(job=a.JOB,passed_tests=4,test_lines=tests,replayed_tests=0))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save36 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map1/73・6,13南・party4/RP0・13576円・badge1・story4071=8/4072=1・flag4367/4368/4369=1。西岩階段/動的8,5/7,5event/trainer360の通常勝利/Save36・独立Continueまで限定受入。'
      'ミュウツーHP320/354・PP[1,8,0,0]。はどうだん4選択で5PP消費、最後のポリゴンのプレッシャーを区別。4体撃破/448円報酬。host回復/PP/flag/var注入禁止。'
      '次は6,13→6,14→6,15→6,16→6,17→6,18→6,19→5,19→4,19の出口候補。map1/38のwarp1は6,4、出口warp0は4,6→map3/21。実exitは未受入。flag4368/4369による敵NPC非表示は正規eventで保存。'
      '本原本227/cold13入力・114画面・全130memberを再生しない。run37125324369はnative2正常/保存完了後に旧Save21専用trace座標例外でfailure。失敗結論を保持し、新scoped parser/34受入で原本だけを回収。旧parser/旧受入は変更0。'
      '先行run37125164118は50入力20画面/native1・未保存のevent座標先行停止、旧13controller成功step継承/変更4controllerも原log継承。record native0・合計開発native3。'
      '107全Flash/108〜110保存成功文言/111field復帰/cold全SaveRTC一致。補助var4021=7→19のruntime owner未解決。'
      'trainer352、洞窟出口、正規全国図鑑、分離progression自然成長/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達、全story、releaseは未完。洞窟出口を越えたら到達milestoneと残件を報告し全ゲーム完了とはしない。既存ROM/runtime/inputはActionsだけ、新公開artifactは新save/画面/textのみ。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save36_accepted=True,west_stair_accepted=True,dynamic8_5_native_arrival=True,trainer360_accepted=True,measurement_conclusion="failure",
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=4,inherited_controller_tests=13,new_acceptance_tests=34,prior_failed_native_processes=1,total_development_native_processes=3,record_native_processes=0,record_preflight_failure=dict(run_id=37125775957,reason="GUIDE専用pathの旧Save35名残",native_processes=0,acceptance_tests_run=0),next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 西側通路・trainer360 event・Save36 限定受入

`{result['status']}`。Save35から西岩階段13,5を下り、開いた8,5から7,5の正規eventに到達。協力質問に「はい」、trainer360のD・H団したっぱ4体に勝利し、敵NPC非表示/同行者退出後6,13南でSave36/独立Continueへ区切った。洞窟出口/全国図鑑は未受入。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` / artifact `{a.ARTIFACT}`。archive {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。測定runの結論failureを保持。native2は正常終了して227/cold13入力・114画面・全130member、新Saveとcoldの全SaveRTC同一を保存済みだった。最後の旧Save21専用parserがevent中の保存座標/live座標差を拒否した。新scoped parserと34受入/拒否試験だけで回収し、成功した入力の再走0、旧parser/旧受入source変更0。

19〜91はcamera/自動移動/戦闘中の保存xy先行を観測。操作可能fieldへ一般化しない。45〜80でドガースLv11/ブロロンLv14/リーフィアLv13/ポリゴンLv12を撃破し、交代3回拒否。はどうだん4選択、最後のポリゴンがプレッシャーを放つ73、実PP13→8。HP320/354は不変。80に448円報酬。92でevent後field復帰。107は全Flash完了・画面書込み中、108〜110で保存成功文言、111でfield復帰。cold0/1同じ6,13南。

party600byteはPP欄1byteだけ、全Bag/HM05・旧Save35bank57344byte・PC維持。通常賞金13128→13576円、physical trainer1640/外部360 flag、story4071=7→8、S61E payload258の0→3（flag4368/4369）、補助var4021=7→19。補助var runtime owner未解決。42sector checksum/S61E CRC/6990byte1798範囲差分を照合。全国図鑑magic0/404e0/flag8400・badge1・4072=1保持。

先行run37125164118（2c0bb3de）は50入力20画面/native1・新保存なし。7,5event開始でsave7,10/live7,5を歩行検査が拒否し、旧13controller成功stepを保持して今回4controllerへ変更。その後の今回native2は成功した保存原本を回収するだけで再走しない。合計開発native3。旧地形920cells/6node event owner/map-load3node14命令は再採取0。ROM/compile/fixture0。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save35']['record_completion']=prior_done
    state['story_save36']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[1,73],xy=[6,13],facing=1,rp=0,money=13576,badge_count=1,story_vars={'4071':8,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,west_stair_accepted=True,dynamic8_5_native_arrival=True,trainer360_accepted=True,original_measurement_conclusion="failure",story_flag4367_accepted=True,cave_crossing_complete=False,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='西側通路/正規event/trainer360/Save36を保存後parser失敗原本から回収。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='西側通路/7,5event/trainer360/Save36の保存完了source。runは保存後parser failureのまま原本回収。洞窟出口/全story未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stage79=h.d.inputs.api('actions/runs/37125070374')
    need(stage79['status']=='completed' and stage79['conclusion']=='success' and stage79['head_sha']=='091d51ca2184ab1befb931ec804232a824e90eb1','前回Stage79終端')
    state['story_save35']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['next_action'].update(id='STORY_CAVE_EXIT_FROM_SAVE36',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save36_accept.py',a.m.TERRAIN,'content/modernization/pr16_story_acceleration_checkpoint.json'],stop_rule_ja='Save36の6,13南から出口4,19→map1/38へ通常入力。227/cold13成功入力/旧受入の無影響再走禁止。洞窟出口と全story完了を区別。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='西階段/動的8,5/7,5event/trainer360勝利/Save36・独立Continue受入。6,13南・13576円・HP320/PP[1,8,0,0]。洞窟出口未完。保存後parser failureは原本のまま。'
    state['do_not_repeat'].append('Save36の227/cold13入力・114画面・13+4controller/34受入を無影響再走しない。run37125324369はnative正常保存後trace failureを保持し原本だけ回収。先行未保存native1と合計native3。4選択/Pressure実5PP消費、正規event4071=8/flag4368/4369だけ。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 西階段・開通通路・trainer360 event・Save36
- Version: story-cave-trainer360-event-save36-v1
- Status: DONE（西側event/Save36限定受入。洞窟出口未完）
- Summary: 13,5西階段/動的8,5/7,5正規event→trainer360の4体撃破/448円報酬/敵NPC非表示/同行者退出→6,13南でSave36。HP320不変、はどうだん4選択/Pressureで実5PP消費、残PP[1,8,0,0]。
- Files changed: Save36 controller/13+4変更試験/新scoped trace parser/34受入拒否試験/record workflow、checkpoint/text原本、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}はnative2正常・227/cold13入力/114画面/130member/Save36完了後の旧parser座標例外でfailure。旧結論を保持して原本だけ独立受入、入力再走0。107全Flash/108〜110保存成功文言/111field復帰/cold全SaveRTC一致、42checksum/旧bank57344byte/S61E CRC/6990byte1798範囲。party差分PP1byte、Bag/PC保持、13576円、trainer physical1640/4071=8/flag4368/4369正規更新。補助var4021owner未解決。
- History: 記録run37125775957はGUIDE名残の宛先checkで停止（native0/受入試験0）。正しいSave36宛先に限定訂正し旧failureを保持。先行run37125164118は50入力20画面/native1・未保存のevent座標先行停止を保持。旧13controller/変更4controllerの成功stepを原log再利用、受入34件だけ追加。合計開発native3、record native0、旧受入再走/ROM変更/compile/fixture0。保存済920cells/6node owner/map-load原本再採取0。Save35記録とStage79終端を反映。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actions原本のみ。既存ROM/runtime/input Save35再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
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
