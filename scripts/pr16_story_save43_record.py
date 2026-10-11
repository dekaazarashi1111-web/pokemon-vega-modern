#!/usr/bin/env python3
"""504上段西進/trainer114のSave43原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save43_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE504-SAVE43'
OUT=ROOT/'.local/pr16-story-save43-record'

CODE={'scripts/pr16_story_save43_accept.py','scripts/pr16_story_save43_record.py','tests/test_pr16_story_save43_accept.py',a.VISUAL,'.github/workflows/pr16-story-save43-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE43_JA.md' and a.CP=='content/modernization/pr16_story_save43_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save43_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37133099941,'c1c8764ad436d7f34d72aba1dea90a1002dfac48',111231993053,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save43_measure.',16)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==72 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save42全72member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save42/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==105 and len(z.namelist())==106 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save43member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==90 and visual['reviewed_screens']==dict(progress=list(range(88)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save43画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save43画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE43_ORIGINAL=str(original),PR16_SAVE42_INPUT=str(assets/'input.srm'),PR16_SAVE43_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save43_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==34 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 34 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'34成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save42-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save43 artifact11277619007のstory-fast.srm（80d9c9387937173a62283f1164cb6ff035ebd39eaa38f78a779da92691ae788f、131088bytes）だけから再開。map3/44・39,12西/上段elevation4・party4/RP0・14264円・badge1・story4071=9/4072=1。主力HP314/354、全PP[0,0,0,0]。trainer114ショウダイの4体へ通常勝利し468円/physicalflag1394だけを追加、Save43/独立Continueを限定受入。次は通常戦闘へ進む前に既存Bagと通常回復地点を確認する。既存のPP回復用品があれば通常BagUIで使用し、なければ静的地形とtrainer視線を照合し通常回復地点へ向かう有限候補を作る。host補充、負けによる回復の暗黙選択、全PP0の旧技選択loopはしない。回復後の未完候補は39,12→38,12→37,12→37,13から西上段、26,10→26,11→26,12の下り階段。今回39,12以西/下り階段は未到達。保存済1440地形/既存ownerを再利用し未知scriptだけ調べる。170/cold13入力・90画面・16controller/34受入試験を無影響再走しない。64〜68実menu0→4、71〜82部分write、83counter43/安定Flash/文言空白→84成功文言→87field。全Save/RTC/cold RAM ledger一致。Save39旧cold RAM差owner未解明、Save40保存後parser回収、Save41/42のrecord失敗履歴を保持。通常story/正規全国図鑑/分離progression自然EXP・技習得・進化/Lucky Egg/12ケース/Lv100soak/研究施設自然到達は未完。trainer352未受入、HM05所持だけ。全story/一般CI全成功/製品release未完。clean-ROM二重生成/BPS固定、merge/release/baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
      artifact={k:meta[k]for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
      record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save43_accepted=True,trainer114_accepted=True,upper_west_partial_accepted=True,west_descent_stairs_accepted=False,normal_recovery_required=True,
      visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),new_controller_tests=16,new_acceptance_tests=34,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    (ROOT/a.GUIDE).write_text(f'''# 504上段西進・trainer114・Save43 限定受入

`{result['status']}`。Save42橋上47,13から西上段39,12へ進み、やまおとこのショウダイ（trainer114）へ通常勝利。イシズマイLv10/ダンゴロLv11/ワンリキーLv13/コジオLv12の4体。通常Save43/独立Continueを限定受入。38,12以西と26,11下り階段は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}` 全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全105member/90画面/170+cold13入力。16controller成功logを継承し、新34原本受入/拒否試験だけを実行。native2/record0/旧受入再走0/ROM変更0。

実技cursor20/25/32/41/48ではどうだん5回、56でサイコブレイク1回。29/45/52の交代拒否3回。がんじょうを最初の2体で、ダンゴロのオレンのみを画像確認。主力party全600byte差分はoffset52:1→0/53:5→0/86:64→58だけ。HP320→315→314/354、全PP[0,0,0,0]。保存親から全8中間partyを独立再構成。通常報酬468円で13796→14264、physicalflag1394=trainer114だけ追加。保存map local3 script154581891から未知ownerのみ照合する。

Bag/HM05/PC/S61E/story4071=9/4072=1/badge1不変。補助var4021=96→104/4022=1→0はruntime owner未解明。42sector checksum/旧Save42bank57344byte/6881byte1710範囲/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400保持。RAM ledger全観測を固定し、進行最終/cold `{a.LEDGER}` は一致。Save39旧差owner未解明は保持。

64〜68通常menu実cursor0→4。71〜82部分write12状態、83counter43/安定全Flashだが文言は空白、84〜86成功文言、87field。cold0/1は39,12西。保存完了をcounter単独や途中hashだけで主張しない。全90画面を目視。

## 次checkpoint送信前の確認

新counterのPython AST、measure/accept import、CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名を大小文字別に照合。受入試験の新counter ORIGINAL/ROMと親counter INPUTのenv集合をrecord側と比較。親artifact/run/source/全save SHA/counter/bank世代/manifest件数を原本で確認。送信treeと最終staged一覧を明示し旧正本との交差0を確認。専用宛先/private/source guardを維持。unittestはreturncode・全成功行・正確な終端で判定し、試験名skippedへのsubstring判定を禁止。記録器だけが失敗した場合は成功原logを継承し再試験しない。旧Save42の2回の記録失敗と30成功試験回収は旧正本のまま保全。

次: {goal}
''',encoding='utf-8')
    need(h.d.bindings(protected)==protected,'既存受入正本/入力不変')
    state['story_save42']['record_completion']=prior_done
    stage79=h.d.inputs.api('actions/runs/37133099890')
    need(stage79['status']=='completed'and stage79['conclusion']=='success'and stage79['head_sha']=='c1c8764ad436d7f34d72aba1dea90a1002dfac48','Save42記録source Stage79終端')
    state['story_save42']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save43']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,
      story_fast_save=a.OUTPUT,map=[3,44],xy=[39,12],facing=3,rp=0,money=14264,badge_count=1,story_vars={'4071':9,'4072':1},hp=[314,354],pp=[0,0,0,0],normal_recovery_required=True,
      hm05_owned=True,hm05_taught_or_used=False,upper_west_partial_accepted=True,west_descent_stairs_accepted=False,trainer114_accepted=True,trainer114_reward=468,physical_trainer_bit=1394,route504_story_event_accepted=True,expanded_flag4370_accepted=True,cave_crossing_complete=True,story_flag4367_accepted=True,
      record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='504西上段trainer114勝利/Save43を限定受入。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='504上段39,12でtrainer114通常勝利/Save43測定source。PP0/通常回復優先。全国図鑑/自然成長/全story未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_NORMAL_PP_RECOVERY_FROM_SAVE43',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save43_accept.py','content/modernization/pr16_story_save40_preparation.json','content/modernization/pr16_story_acceleration_checkpoint.json','docs/PR16_NATIONAL_DEX_OWNER_JA.md'],stop_rule_ja='Save43主力PP全0のため次戦闘の前に通常回復を優先。既存Bag/通常回復先を確認し、通常UIでの回復と保存を有限checkpointにする。host補充や旧入力反復をしない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='504番道路39,12西/上段trainer114勝利・Save43独立Continue受入。14264円/HP314/PP[0,0,0,0]、次は通常回復。全国図鑑/自然成長/全story未完。'
    state['do_not_repeat'].append('Save43の170/cold13入力90画面/16controller34受入を無影響再走しない。39,12でtrainer114の4体へ1勝/468円/flag1394のみ。全PP0、次は通常回復優先。64〜68実menu0→4、71〜82部分write→83counter43/安定Flash/空白→84成功文言→87field。全SaveRTC/cold ledger一致。38,12以西/下り階段未到達。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''\n## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 504上段西進・trainer114・Save43
- Version: story-route504-save43-v1
- Status: DONE（上段一部/新trainer1勝/保存Continue限定受入）
- Summary: 47,13橋上から39,12西上段へ。ショウダイtrainer114の4体へ勝利、通常報酬468円。PP全0で次は通常回復。下り階段/全story/全国図鑑/自然成長未完。
- Files changed: Save43 controller/16新規試験/34原本受入拒否試験/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: 測定run{a.RUN}/job{a.JOB}全8step成功、170/cold13入力/90画面/105member。16controller原log継承、新34受入だけ実行、record native0。全8中間partyを親から独立再構成。全party差分3byte/HP320→314/PP全0。Bag/PC/S61E/story不変、13796→14264円/flag1394のみ。補助4021/4022 owner未解明。42checksum/旧bank57344byte/6881byte1710範囲/cold全SaveRTC一致。
- Evidence: 64〜68実menu0→4、71〜82部分write、83counter43/安定Flash/文言空白→84成功文言→87field。Save42 record37133099941/Stage79run37133099890終端success反映。Save39旧cold RAM差owner未解明、Save40/41/42失敗回収履歴を保持。静的地形再採取0、未知trainer114 ownerだけ追加照合。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actions入力のみ。既存ROM/runtime/input Save42再配布0。一般CI既知source不一致を保持、merge/release/baseline変更0。
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

