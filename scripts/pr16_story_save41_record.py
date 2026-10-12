#!/usr/bin/env python3
"""504西段差/橋下のSave41原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save41_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE504-SAVE41'
OUT=ROOT/'.local/pr16-story-save41-record'

CODE={'scripts/pr16_story_save41_accept.py','scripts/pr16_story_save41_record.py','tests/test_pr16_story_save41_accept.py',a.VISUAL,'.github/workflows/pr16-story-save41-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE41_JA.md' and a.CP=='content/modernization/pr16_story_save41_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save41_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37130202320,'9ba845434ef1ed765eac2a57e71337bbb9d5e1c7',111223633347,['success']*11)
    failed_record_done=inherited.terminal(37131369405,'c0e24078cef9de77e1dc961fe3b4188d67a7f68a',111226984760,['success','success','success','failure','skipped','skipped','skipped','skipped','success','success','success'])
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save41_measure.',14)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==99 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save40全99member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save40/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==59 and len(z.namelist())==60 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save41member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==44 and visual['reviewed_screens']==dict(progress=list(range(42)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save41画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save41画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE41_ORIGINAL=str(original),PR16_SAVE40_INPUT=str(assets/'input.srm'),PR16_SAVE41_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save41_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==26 and b'\nOK\n'in unit.stderr and b'skipped'not in unit.stderr,'新Save41受入/拒否試験')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save40-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'first-record-failure.json',dict(terminal=failed_record_done,native_processes=0,acceptance_tests_run=0,reason_ja='GUIDE宛先が旧Save40のままだったため、専用宛先guardがartifact取得/書込/受入試験より前に拒否。新Save41専用pathに訂正し旧正本を保全。'))
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save41 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map3/44（504番道路）・48,11西・party4/RP0・13796円・badge1・story4071=9/4072=1、HP320/354・PP[1,5,0,0]。'
      '西段差58,10→56,10と橋下48,11までの通常移動、Save41/独立Continueを限定受入。戦闘0。48,11→47,11は3回未通過で反復しない。'
      '保存地形では48,11/12/13がelevation15の橋下、47,11は4であり単純BFSの高さ無視が誤候補だった。'
      '次は南48,12→48,13→48,14→48,15→49,15→50,15→50,16→51,16→52,16→53,16→54,16→54,15の階段behavior42/elevation0候補。'
      '54,14の上段elevation4や以西は静的候補で、実通過を先取りしない。橋の15は現在高度を保持し、階段0で高度を切り替える地形モデル候補を使う。'
      '全1440地形/既存ownerは原本を再利用。最初の新戦闘/event・未通過境界または通常回復地点で保存、PPをhost補充しない。'
      '77/cold13入力・44画面・14controller/26受入試験は無影響に再走しない。実menu cursor17〜21の0→4、36counter41は部分write、37成功文言/安定全Flash→41field。'
      '今回の進行最終/cold RAM ledgerと全Save/RTCは一致。Save39の旧cold RAM差owner未解明を保持。Save40の元parser failureは保存後回収済みで改作/再走しない。'
      '残件: 通常story、正規全国図鑑解禁、分離progression自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。'
      'trainer352未受入、HM05所持だけ・未習得/未使用。全story/一般CI全成功/製品release未完。clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save41_accepted=True,west_ledge_accepted=True,bridge_west_edge_passed=False,cave_crossing_complete=True,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=14,new_acceptance_tests=26,successful_native_processes=2,record_native_processes=0,first_record_failure_run=37131369405,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 504西段差と橋下・Save41 限定受入

`{result['status']}`。Save40の60,10から西へ進み、58,10→56,10の西段差を通常入力で通過し48,11の橋下に到達。48,11→47,11は3回未通過として保存し反復しない。通常Save41/独立Continueを限定受入。新戦闘0、正規story4071=9/4370は前Save40の受入を継承。全story・全国図鑑・自然成長は未完。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全59member/44画面/77+cold13入力。新14controllerの成功logを継承、新26原本受入/拒否試験、native2/record0。ROM/fixture/compile/既受入再走0。測定receiptを独立episode解析前に保存する構成へ改め、前回の保存後parser failureでreceiptが欠けた問題を避けた。旧parserや旧受入条件は変更していない。初回record run37131369405はGUIDE宛先の旧名を専用宛先guardが事前拒否し、native/受入試験/正本書込0。新Save41宛先へ訂正して原本から記録。

party600byte/HP320/PP[1,5,0,0]/全Bag/HM05/13796円/PC/S61E/legacy flag/story4071=9/4072=1・badge1不変。補助var4021=63→75/4022=3→0だけでruntime ownerは未解明。42sector checksum/旧Save40bank57344byte/6866byte1695範囲/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400を保持。

17〜21の通常menu cursor0→4を実画像確認。24〜36は13部分write、36counter41でもFlash未確定、37〜40成功文言/安定全Flash、41field復帰。cold0/1は同じ橋下48,11西。進行最終/cold ledger `{a.LEDGER}` は一致するがSave39の旧cold差owner未解明は維持。

保存地形1440cell/11nodeの再採取0。静的57vertexの候補のうち13vertexだけを通過し、次の47,11へは通れなかった。橋下elevation15と橋上elevation4を単純な隣接だけで接続するBFSはlive到達保証にならない。次候補は南の橋下を抜けて54,15階段へ。地形比較を実通過と同一視しない。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save40']['record_completion']=prior_done
    state['story_save41']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[3,44],xy=[48,11],facing=3,rp=0,money=13796,badge_count=1,story_vars={'4071':9,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,west_ledge_accepted=True,unpassed_edge=[[48,11],[47,11]],bridge_west_edge_passed=False,route504_story_event_accepted=True,expanded_flag4370_accepted=True,cave_crossing_complete=True,story_flag4367_accepted=True,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='504西段差通過/橋下の西辺未通過/Save41を限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='504西段差通過と橋下の西辺未通過・Save41測定source。全国図鑑/自然成長/全story未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stage79=h.d.inputs.api('actions/runs/37130202316')
    need(stage79['status']=='completed' and stage79['conclusion']=='success' and stage79['head_sha']=='9ba845434ef1ed765eac2a57e71337bbb9d5e1c7','Save40記録source Stage79終端')
    state['story_save40']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['next_action'].update(id='STORY_ROUTE504_UNDERPASS_FROM_SAVE41',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save41_accept.py','content/modernization/pr16_story_save40_preparation.json','content/modernization/pr16_story_acceleration_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save41の48,11から橋下を南へ。西47,11の未通過を反復しない。48,12/13→48,14/15→54,16→54,15階段が静的候補。最初の新戦闘/event・未通過境界または通常回復地点で限定保存。既受入を無影響再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='504番道路48,11西・西段差通過/橋下西辺未通過・Save41独立Continue受入。戦闘0/13796円/HP320/PP[1,5,0,0]。全国図鑑/自然成長/全storyは未完。'
    state['do_not_repeat'].append('Save41の77/cold13入力44画面/14controller26受入を無影響再走しない。58,10→56,10西段差は通過、48,11→47,11は3回未通過。17〜21実menu0→4、36counter41部分write→37成功/安定→41field。全SaveRTC/cold ledger一致。静的1440地形再採取0。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 504西段差・橋下・Save41
- Version: story-route504-save41-v1
- Status: DONE（西段差通過/橋下西辺未通過/保存Continue限定受入）
- Summary: Save40の60,10から58,10→56,10の西段差を通過し48,11橋下へ。西47,11は3回未通過で有限停止。戦闘0、全国図鑑/自然成長/全story未完。
- Files changed: Save41 controller/14変更試験/26原本受入拒否試験/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: 測定run{a.RUN}/job{a.JOB}全8step成功、77/cold13入力/44画面/59member。14controller原log継承、新26受入だけ実行、record native0。party600byte/HP320/PP[1,5,0,0]/Bag/13796円/PC/S61E/legacyflags/story不変。補助4021=63→75/4022=3→0はowner未解明。42checksum/旧bank57344byte/6866byte1695範囲/cold全SaveRTC一致。
- History: 初回record37131369405はGUIDEの旧Save40宛先を専用guardがartifact取得/書込/受入試験前に拒否。native0/受入試験0/正本書込0。新宛先へ訂正し失敗終端を保持。
- Evidence: 17〜21実menu0→4、24〜36部分write、36counter41、37成功文言/安定Flash→41field。今回cold RAMledger一致、Save39旧差owner未解明を保持。Save40 record37130202320/Stage79run37130202316の全success終端反映。保存済地形再採取0、旧accepted試験/native再実行0。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actions入力のみ。既存ROM/runtime/input Save40再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
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

