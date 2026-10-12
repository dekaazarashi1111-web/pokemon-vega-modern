#!/usr/bin/env python3
"""504正規eventのSave40原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save40_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE504-SAVE40'
OUT=ROOT/'.local/pr16-story-save40-record'

CODE={'scripts/pr16_story_save40_accept.py','scripts/pr16_story_save40_record.py','tests/test_pr16_story_save40_accept.py',a.VISUAL,'.github/workflows/pr16-story-save40-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE40_JA.md' and a.CP=='content/modernization/pr16_story_save40_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save40_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success','success','success','failure','skipped','success','success','success'])
    prior_done=inherited.terminal(37128753593,'d953deff3152a853a860771af92004af8fa6df66',111219392908,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save40_measure.',13)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==55 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save39全55member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save39/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==99 and len(z.namelist())==100 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save40member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==83 and visual['reviewed_screens']==dict(progress=list(range(81)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save40画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save40画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE40_ORIGINAL=str(original),PR16_SAVE39_INPUT=str(assets/'input.srm'),PR16_SAVE40_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save40_accept.py','-v'],capture_output=True,timeout=120,env=env)
    (receipts/'unit.stdout.txt').write_bytes(unit.stdout);(receipts/'unit.stderr.txt').write_bytes(unit.stderr)
    need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==32 and b'\nOK\n'in unit.stderr and b'skipped'not in unit.stderr,'新Save40受入/拒否試験')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['failure.json','manifest.json','save39-record-terminal.json','inspection-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit.stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal=(f'Save40 artifact{a.ARTIFACT}のstory-fast.srm（{a.OUTPUT["sha256"]}、131088bytes）だけから再開。'
      'map3/44（504番道路）・60,10西・party4/RP0・13796円・badge1・story4071=9/4072=1、HP320/354・PP[1,5,0,0]。'
      '通常24歩から座標60,10のモスギス/D・H団人物の追跡eventを完了し、正規flag4370・4071=9、Save40/独立Continueを限定受入。戦闘0。'
      '次は西59,10→58,10→56,10の西段差候補から504を先へ。保存済behavior57は西向き段差の比較定義だが現候補の実通過は未受入。'
      '全1440地形/11node東側ownerは保存済原本を再利用し、無影響再採取しない。最初の新戦闘/eventまたは通常回復地点で保存、PPをhost補充しない。'
      '本runの156/cold13入力・83画面・13controller/32受入試験は再走しない。元run37129549744のfailureは正常保存/Continue後に旧洞窟専用parserがeventカメラ座標を拒否したもの。artifact全99memberを改作せず保持しnative再走0で回収。'
      '30〜55のカメラ座標は主人公live60,10と区別、56field復帰。通常Saveは各行menu cursor0→4を画像検証。75counter40は部分write、76成功文言/安定全Flash→80field。'
      '今回の進行最終/cold RAM ledgerと全Save/RTCは一致。ただしSave39の旧cold RAM差ownerは未解明。'
      'Save36の保存後parser回収、Save37/39の一時Flash一致、Save38のtrainer103と未受入再戦1029、Save39初回TrainerCard未保存を保持。'
      '残件: 通常story、正規全国図鑑解禁、分離progression自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。trainer352未受入、HM05所持だけ・未習得/未使用。'
      '全story/一般CI全成功/製品release未完。clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save40_accepted=True,route504_story_event_accepted=True,story4071=9,expanded_flag4370_accepted=True,cave_crossing_complete=True,
      static_inspection=dict(source='5d6e0d7ee13b5023d500012de56066cd01527751',run_id=37129298036,job_id=111221019996,artifact_id=11276262018,archive=dict(size=9610,sha256='41955775baf6663987a31b6f23c19e968f7797cfe1392efd7bb6bc627517896b'),new_terrain_cells=1440,new_script_nodes=11,native_processes=0),
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),
      new_controller_tests=13,new_acceptance_tests=32,successful_native_processes=2,record_native_processes=0,original_measurement_conclusion='failure',original_failure_is_post_save_trace_only=True,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 504番道路の正規event・Save40 限定受入

`{result['status']}`。Save39の71,9から通常24歩で60,10の座標eventへ入り、モスギスとD・H団人物の会話/追跡演出を完了。正規scriptでstory4071=8→9、拡張flag4370をセット。60,10西の通常Save40/独立Continueまで限定受入。戦闘0。全story・全国図鑑・自然成長は未完。

測定source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` はfailureを保持。156/cold13入力の両nativeは正常終端し、保存/Continue後に旧Save35洞窟専用trace parserが今回のカメラ座標差を拒否した。保存原本を改作せず、今回専用独立parserと原本32受入/拒否試験で回収。追加native0。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`、全99member/83画面。

新13controllerは元jobの成功logを継承。静的run37129298036の全8step成功、地形1440マス/11node（5root/4unique）/168命令・診断0を採取。既存map view/既受入gameplayの再走0、ROM/fixture/compile0。次作業は保存済地形を再利用する。

party600byte/HP320/PP[1,5,0,0]/全Bag/HM05/13796円/PC/legacy flag不変。S61Eはbyte258=3→7（flag4370のみ）とCRC正常、旧4367〜4369保持。正規story4071=8→9、補助4021=40→63/4022=0→3のownerは未解明。42sector checksum/旧Save39bank57344byte/6931byte1698範囲/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400・4072=1/badge1を保持。

30〜55はeventカメラ座標で、主人公live60,10を維持し56で操作へ復帰。カメラの48,8等を主人公の移動/warpにしない。57〜61は実menu cursor0→4、64〜75は12部分write、75counter40でもFlashは未確定、76〜79成功文言/安定全Flash、80field。cold0/1も60,10西。進行最終/cold ledger `{a.LEDGER}` は一致するが、前Save39で生じた旧cold差のownerを解明したとはしない。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save39']['record_completion']=prior_done
    state['story_save40']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[3,44],xy=[60,10],facing=3,rp=0,money=13796,badge_count=1,story_vars={'4071':9,'4072':1},
      hm05_owned=True,hm05_taught_or_used=False,route504_story_event_accepted=True,expanded_flag4370_accepted=True,cave_crossing_complete=True,story_flag4367_accepted=True,
      original_measurement_conclusion='failure',original_failure_is_post_save_trace_only=True,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='504の正規追跡event/Save40原本をnative再走0で限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='504正規event/Save40測定source。native成功後の旧parser failureを保持し原本限定回収。全国図鑑/自然成長/全story未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    stage79=h.d.inputs.api('actions/runs/37128753577')
    need(stage79['status']=='completed' and stage79['conclusion']=='success' and stage79['head_sha']=='d953deff3152a853a860771af92004af8fa6df66','Save39記録source Stage79終端')
    state['story_save39']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['next_action'].update(id='STORY_ROUTE504_WEST_FROM_SAVE40',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save40_accept.py','content/modernization/pr16_story_save40_preparation.json','content/modernization/pr16_story_acceleration_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save40の60,10から西へ。59,10→58,10→56,10の段差は静的候補。最初の新戦闘/eventまたは通常回復地点で限定保存。menu cursor実画像検証、カメラとlive座標を区別、既受入を無影響再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='504番道路60,10西・正規追跡event/story4071=9/flag4370/Save40独立Continue受入。戦闘0/13796円/HP320/PP[1,5,0,0]。全国図鑑/自然成長/全storyは未完。'
    state['do_not_repeat'].append('Save40の156/cold13入力83画面/13controller32受入を無影響再走しない。元run37129549744は保存Continue完了後の旧parser failureを保持しnative0で回収。30〜55はカメラ/live差を限定解釈、75counter40でも部分write→76成功/安定→80field。静的1440地形/11node再採取0。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 504追跡event・Save40
- Version: story-route504-save40-v1
- Status: DONE（正規story event/保存Continue限定受入）
- Summary: Save39から通常24歩で504の60,10座標event。モスギス/D・H団人物の会話追跡を完了、4071=8→9/flag4370。戦闘0、全国図鑑/自然成長/全story未完。
- Files changed: Save40 controller/13変更試験/32原本受入拒否試験/record workflow、静的地形1440/東側11node原本、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: 測定run{a.RUN}/job{a.JOB}は保存Continue後の旧洞窟専用parser failureを保持。両native正常終端/156/cold13入力/83画面/99memberを新独立parserで回収。13controller原log継承、新32受入試験だけ実行、追加native0。party600byte/HP320/PP[1,5,0,0]/Bag/13796円/PC/legacyflags不変。S61E byte258=3→7/CRC検証、story4071=9、補助4021=40→63/4022=0→3はowner未解明。42checksum/旧bank57344byte/6931byte1698範囲/cold全SaveRTC一致。
- Evidence: event30〜55カメラ/live差を区別→56field。57〜61実menu0→4、64〜75部分write、75counter40、76成功文言/安定Flash→80field。今回cold RAMledger一致、Save39旧差のowner未解明を保持。Save39 record37128753593/Stage79run37128753577のsuccess終端反映。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actions入力のみ。段差比較定義 https://raw.githubusercontent.com/pret/pokefirered/master/include/constants/metatile_behaviors.h の0x39=westを参照、現候補の通過は未受入。既存ROM/runtime/input Save39再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
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

