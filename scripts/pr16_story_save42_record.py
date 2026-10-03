#!/usr/bin/env python3
"""504橋下/階段/橋上のSave42原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save42_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE504-SAVE42'
OUT=ROOT/'.local/pr16-story-save42-record'

CODE={'scripts/pr16_story_save42_accept.py','scripts/pr16_story_save42_record.py','tests/test_pr16_story_save42_accept.py',a.VISUAL,'.github/workflows/pr16-story-save42-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE42_JA.md' and a.CP=='content/modernization/pr16_story_save42_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save42_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37131494568,'75d5b04934121c7213db4760f4ece87078524a45',111227343260,['success']*11)
    failed_record_done=inherited.terminal(37132651122,'2e66e9ad0c2c21c856e042d186a2fe0671fac868',111230669206,['success','success','success','failure','skipped','skipped','skipped','skipped','success','success','success'])
    second_record_done=inherited.terminal(37132813539,'a5dedfd0b2dbbc6777a25f2b84744b85733d1a9d',111231147495,['success','success','success','failure','skipped','skipped','skipped','skipped','success','success','success'])
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save42_measure.',16)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==59 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save41全59member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save41/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==72 and len(z.namelist())==73 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save42member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==57 and visual['reviewed_screens']==dict(progress=list(range(55)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save42画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save42画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    # 30試験は失敗run内で全件成功済み。誤ったsubstring guardだけを訂正し、試験再走0。
    for name in ['scripts/pr16_story_save42_accept.py','tests/test_pr16_story_save42_accept.py',a.VISUAL]:
        need(h.d.git('show','a5dedfd0b2dbbc6777a25f2b84744b85733d1a9d:'+name)==(ROOT/name).read_bytes(),'成功試験source不変 '+name)
    _,z=a.transport.archive(11277088734,37132813539,dict(size=705,sha256='6e56acca0cad2d6024c9d3601543b02ed45006cc184406d7c6202d8a83aba986'),'a5dedfd0b2dbbc6777a25f2b84744b85733d1a9d')
    with z:
        need(set(z.namelist())=={'unit.stdout.txt','unit.stderr.txt'},'二回目record試験原本2memberだけ')
        unit_stdout=z.read('unit.stdout.txt');unit_stderr=z.read('unit.stderr.txt')
    need(not unit_stdout and len(unit_stderr)==3133 and len(unit_stderr.splitlines())==35,'全試験原本のsize/行数')
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(len(test_lines)==30 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 30 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'30成功行と正確なunittest終端')
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save41-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'first-record-failure.json',dict(terminal=failed_record_done,native_processes=0,acceptance_tests_run=0,tracked_writes=0,reason_ja='新parserのGUIDE定数が旧Save41を指したため、専用宛先guardがartifact取得/受入試験/正本書込前に拒否。Save42専用宛先へ訂正し原本から記録。'))
    write(evidence/'second-record-failure.json',dict(terminal=second_record_done,artifact_id=11277088734,native_processes=0,accepted_tests_passed=30,replayed_tests=0,tracked_writes=0,reason_ja='30試験は全件ok/OK。成功した試験名underpass_falsely_skippedに含まれるskippedへsubstring guardが誤反応した。成功原本を不変で継承し、正確なunittest終端/全行okだけで照合。元run結論failureを保持。'))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save42 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map3/44（504番道路）・47,13西/橋上elevation4・party4/RP0・13796円・badge1・story4071=9/4072=1、HP320/354・PP[1,5,0,0]。'
      '橋下48,11から南通路、54,16→54,15階段→54,14上段、橋上49,13→48,13→47,13を通常通過し、Save42/独立Continueを限定受入。戦闘0。'
      '旧48,11→47,11は未通過のまま、今回再試行0。橋下/橋上の異なる高さを同じ経路にしない。'
      '次候補は47,13→46,13→46,12から上段を西へ。保存地形の42,12/37,13/34,13→33,13→31,13→30,10→26,10→26,11階段→26,12下段を候補とし、最初の新戦闘/event・未通過境界または通常回復地点で保存。'
      '保存済1440地形/既存ownerを再利用し、未知scriptだけ追加調査。PPはslot1残5/slot0残1を基準に通常技入力、host補充しない。'
      '今回103/cold13入力・57画面・16controller/30受入試験を無影響再走しない。30〜34実menu0→4、49は最終Flash一時一致/書込中、50counter42で再変化、51成功文言/安定全Flash→54field。'
      '今回全Save/RTC/cold RAM ledger一致。Save39旧cold RAM差owner未解明、Save40保存後parser failureの回収、Save41初回record guard failureを保持。'
      '残件: 通常story、正規全国図鑑解禁、分離progression自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。'
      'trainer352未受入、HM05所持だけ・未習得/未使用。全story/一般CI全成功/製品release未完。clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save42_accepted=True,underpass_south_accepted=True,stairs_accepted=True,upper_bridge_west_crossing_accepted=True,earlier_unpassed_edge_retried=False,cave_crossing_complete=True,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=16,new_acceptance_tests=30,successful_native_processes=2,record_native_processes=0,first_record_failure_run=37132651122,second_record_failure_run=37132813539,acceptance_test_source_run=37132813539,acceptance_tests_executed_in_record=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 504橋下・階段・橋上・Save42 限定受入

`{result['status']}`。Save41の橋下48,11から南へ抜け、54,15の階段で上段へ。橋上48,13から47,13西へ通常通過、Save42/独立Continueを限定受入。21歩/8方向転換、戦闘0。旧48,11→47,11は未通過のままで再試行0。全story・全国図鑑・自然成長は未完。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全72member/57画面/103+cold13入力。新16controller成功logを継承、二回目record run37132813539の新30原本受入/拒否試験成功logを継承、記録時試験再実行0、native2/record0。ROM/fixture/compile/既受入再走0。

party600byte/HP320/PP[1,5,0,0]/全Bag/HM05/13796円/PC/S61E/legacy flag/story4071=9/4072=1・badge1不変。補助var4021=75→96/4022=0→1だけでruntime owner未解明。42sector checksum/旧Save41bank57344byte/6871byte1715範囲/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400を保持。

30〜34の通常menu cursor0→4を実画像確認。37〜48と50は13部分write。49は最終Flashと一時一致するが書込中/counter41であり完了とはしない。50でcounter42/Flash再変化、51〜53成功文言/安定全Flash、54field。cold0/1も橋上47,13西。全57画面を確認。進行最終/cold ledger `{a.LEDGER}` は一致するがSave39旧差owner未解明を維持。

初回record run37132651122はGUIDE定数の旧Save41宛先を専用guardがartifact取得/受入試験/正本書込前に拒否。native0/試験0/正本書込0。Save42宛先へ訂正し、失敗終端を保持して記録。第二record run37132813539は30試験全成功後、成功した試験名のskippedへ粗いsubstring判定が誤反応。原試験log/705byte artifact11277088734を不変継承し、成功行と正確な終端を検査する。旧run結論はfailureのまま、試験/nativeを再走しない。

保存地形1440cell/11nodeの再採取0。橋tileのelevation15は進入した高さを保持し、54,15のelevation0階段から上段へ進める候補を今回の通常通過で限定裏付けた。すべての橋/階段の一般的到達保証にはしない。22vertexの今回候補全部を通過、以西は次の未受入区間。

## 次のcheckpointをActionsへ送る前のローカル確認

1. 新counterを1つ定め、ASTで全Pythonの構文と定数を照合する。importするmeasure/accept、CP/JSON、GUIDE/MD、EVIDENCE、VISUAL、OUT、workflow名、CODE列挙、test名が同じ新counterであること。文字列一括置換の小文字/大文字漏れを個別に検出する。
2. 環境変数は受入試験が読む新counterのORIGINAL/ROMと、実入力である親counterのINPUTの3名をrecord側定義と集合比較する。親artifact/run/source/save SHA、Save counter、bank世代、manifest件数を実原本と照合し、親を新counterへ一括置換しない。
3. 送信予定tree/staged pathsの全一覧を表示し、意図した新規text pathだけか、既存受入source/旧GUIDE/旧checkpointとの交差が0か確認する。CP/GUIDE/EVIDENCE専用宛先guardと既存private/source guardは弱めず保持する。
4. 新試験名/件数と成功原logの一致を確認する。unittestの成否はreturncodeと全成功行/正確な終端で判定し、試験名内のskipped等へのsubstring判定を使わない。既に成功した試験を記録器だけの失敗で再走しない。失敗runはそのまま保存し、以後は原本再利用で回収する。

本Save42のGUIDE旧名漏れと試験名substring誤判定は両方とも履歴へ保持した。次workerは上の4点をpush前に済ませ、既存の専用宛先/private/source guardを引き続き使用する。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save41']['record_completion']=prior_done
    state['story_save42']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[3,44],xy=[47,13],facing=3,rp=0,money=13796,badge_count=1,story_vars={'4071':9,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,underpass_south_accepted=True,stairs_accepted=True,upper_bridge_west_crossing_accepted=True,earlier_unpassed_edge=[[48,11],[47,11]],earlier_unpassed_edge_retried=False,route504_story_event_accepted=True,expanded_flag4370_accepted=True,cave_crossing_complete=True,story_flag4367_accepted=True,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='504橋下→南通路→階段→橋上/Save42を限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='504橋下から階段・橋上の通常通過・Save42測定source。全国図鑑/自然成長/全story未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stage79=h.d.inputs.api('actions/runs/37131494597')
    need(stage79['status']=='completed' and stage79['conclusion']=='success' and stage79['head_sha']=='75d5b04934121c7213db4760f4ece87078524a45','Save41記録source Stage79終端')
    state['story_save41']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['next_action'].update(id='STORY_ROUTE504_WEST_FROM_SAVE42',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save42_accept.py','content/modernization/pr16_story_save40_preparation.json','content/modernization/pr16_story_acceleration_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save42の47,13橋上から西46,13→46,12へ。保存済地形で上段を西へ進む候補だけを選び、最初の新戦闘/event・未通過境界または通常回復地点で限定保存。旧48,11→47,11を再試行せず、既受入を無影響再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='504番道路47,13西・橋下から階段/橋上通過・Save42独立Continue受入。戦闘0/13796円/HP320/PP[1,5,0,0]。全国図鑑/自然成長/全storyは未完。'
    state['do_not_repeat'].append('Save42の103/cold13入力57画面/16controller30受入を無影響再走しない。橋下→54,15階段→上段→橋上48,13→西47,13を通過。旧48,11→47,11は未通過のまま再試行0。30〜34実menu0→4、49最終Flash一時一致/50counter42再変化→51成功/安定→54field。全SaveRTC/cold ledger一致。静的1440地形再採取0。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 504橋下・階段・橋上・Save42
- Version: story-route504-save42-v1
- Status: DONE（橋下/階段/橋上通過/保存Continue限定受入）
- Summary: Save41の48,11から南へ抜け、54,15階段から上段へ。橋上48,13を経て47,13まで21歩/8方向転換。旧失敗辺の再試行0、戦闘0、全国図鑑/自然成長/全story未完。
- Files changed: Save42 controller/16新規試験/30原本受入拒否試験/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: 測定run{a.RUN}/job{a.JOB}全8step成功、103/cold13入力/57画面/72member。16controller原log継承、第二record run37132813539の新30受入成功原本を継承、今回試験再実行0/record native0。party600byte/HP320/PP[1,5,0,0]/Bag/13796円/PC/S61E/legacyflags/story不変。補助4021=75→96/4022=0→1はowner未解明。42checksum/旧bank57344byte/6871byte1715範囲/cold全SaveRTC一致。
- Evidence: 30〜34実menu0→4、37〜48/50部分write、49最終Flash一時一致で書込中、50counter42/再変化、51成功文言/安定Flash→54field。今回cold RAMledger一致、Save39旧差owner未解明を保持。Save41 record37131494568/Stage79run37131494597の全success終端反映。保存済地形再採取0、旧accepted試験/native再実行0。
- History: 第二record37132813539は30試験全成功後に試験名underpass_falsely_skippedへのsubstring誤反応。成功原ログ/artifact11277088734を不変継承し再試験0。初回record37132651122は旧Save41を指すGUIDE定数を専用宛先guardが事前拒否。native0/受入試験0/正本書込0。失敗終端を保持し、Save42宛先へ訂正。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actions入力のみ。既存ROM/runtime/input Save41再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
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

