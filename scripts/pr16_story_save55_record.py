#!/usr/bin/env python3
"""ミルシティのレンジャー戦と通常贈与Save55原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save55_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MIRU-SAVE55'
OUT=ROOT/'.local/pr16-story-save55-record'

CODE={'scripts/pr16_story_save55_accept.py','scripts/pr16_story_save55_record.py','tests/test_pr16_story_save55_accept.py',a.VISUAL,'.github/workflows/pr16-story-save55-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE55_JA.md' and a.CP=='content/modernization/pr16_story_save55_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save55_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37150128228,'1e4551b4da705a01da77fd53f109a182cf316c8a',111282060951,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save55_measure.',21)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==54 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save54全54member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save54/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==154 and len(z.namelist())==155 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save55member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==139 and visual['reviewed_screens']==dict(progress=list(range(137)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save55画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save55画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE55_ORIGINAL=str(original),PR16_SAVE54_INPUT=str(assets/'input.srm'),PR16_SAVE55_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save55_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==47 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 47 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'47成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save54-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save55 artifact11284146293のstory-fast.srm（131088bytes/SHA256 f9f9638a49aa4b0f0553c3bfcbaeb736f49d4ae42e5b5ca2509c8aaad9f515a2）だけから再開。map3/2・16,20南、こころのやかた前。通常出口/市内30歩、レンジャー331の6体へ1勝/864円/がくしゅうそうち182を1個通常取得、離脱flag4381、Save55/独立Continue全SaveRTC一致を限定受入。オノノクス288/294・PP[15,10,15,14]、ミュウツー354/354・PP[10,20,15,10]、所持金17904円/RP0/badge1/story4071=9/4072=1。次はNPC実台詞「こころのやかた奥のどうぞうの裏の紙」を調べる必須導線。保存済town warp15,19→map1/59・warp1から、未読室内owner/必要地形だけ調査し通常入力で入館・最初の新event/戦闘/未通過境界を保存する。任意TM21民家map39/0をgymと誤認しない。がくしゅうそうちは取得のみ、装備/自然成長受入なし。RAM台帳4差分/仲間offset41三件/aux2件と40ac=16のowner未解明を保持。最終/cold台帳77ccaa1d7ceee4a641d1094ab5b8f5caf44668ea125287542f3e2bed65a80e57。Save55counter131は部分write、132安定でも保存中→133成功→136field。268+cold13入力139画面21controller47受入154memberを無影響再走0。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完、doubletarget分離native未実証。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。'
    extra={'scripts/pr16_story_save55_inspect.py','.github/workflows/pr16-story-save55-inspect.yml'}
    terminal=inherited.terminal(37150727892,'f4f43a2672e5427988118267f46faac0b4623711',111283898658,['success']*8)
    _,z=a.transport.archive(11283612866,37150727892,dict(size=9344,sha256='6bbf996e215d5054beba363c75fc38278519f67d34024ffe51072e039d58e778'),'f4f43a2672e5427988118267f46faac0b4623711')
    with z:need(z.namelist()==['inspection.json']and z.read('inspection.json')==(ROOT/a.m.PREP).read_bytes(),'45node/38cell静的原本全byte')
    name=a.EVIDENCE+'/inspection-terminal.json';write(ROOT/name,terminal);paths.add(name)
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save55_accepted=True,ranger_battle_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,normal_recovery_repeated=False,heart_mansion_entered=False,double_target_separation_native_exercised=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE|extra),evidence_bindings=h.d.bindings(paths),new_controller_tests=21,new_acceptance_tests=47,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# ミルシティ通常レンジャー戦・がくしゅうそうち・Save55限定受入

`{result['status']}`。回復済Save54からPC出口4歩/warp、市内26歩でレンジャー東隣16,20。通常Aの会話から6体撃破し、864円・がくしゅうそうち1個・像の裏の紙を調べる依頼・NPC離脱・Save55と独立Continueを受入。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。154member/139画面/268+cold13入力、21controller原log/47新受入拒否試験。native2/record0/旧再走0/ROM変更0。

## 必須ownerと実戦

未読45node/38cell/1mapだけ採取、既読scriptを復元して再decodeしない。静的candidateの暫定gym欄map39/0はTM21民家と判明し、必須導線から除外。未入館。実際はtown local10(15,20)/script149023660、保存starter4031=0→trainer331、同候補のphysical1611。new setflag4381をS61E payload259のbit5から独立照合。

観測36〜45の会話→46戦闘開始。つばめがえし6回選択/実PP20→14、5回交代拒否。ダブルtarget確定0。オノノクスHP294→293→288/294。ミュウツー354/354と全PP保持。94勝利/96報酬864円/102〜103がくしゅうそうち/104〜111像の裏の紙の依頼/112NPC離脱とfield。主力Lv100によるstory短縮であり自然育成・難易度受入ではない。

## 保存と限定差分

113〜117通常menu0→4、118確認/119上書き、120〜131部分write。131counter55でも部分write、132最終Flashでも保存中、133〜135成功文言、136field。cold0/1は全SaveRTC同一、勝利残留を追加勝利にしない。

party5byte差分だけ。PP6/HP6と仲間offset41三件。歩行時の3byteとRAM台帳41/63/83/103のownerは未解明。Bagは空items先頭へ182を1個追加だけ、17040→17904円。legacy1611とexpanded4381だけ。vars4021=114→16/4022=1→0/40ac=0→16はruntime owner未解明。story4071=9/4072=1、badge1、全国図鑑未解禁。旧bank57344byte、PC全byte、S61E CRC/残payload保持。42checksum、6999byte/1764範囲。

がくしゅうそうちは装備していない。回復を繰り返していない。こころのやかた入館・像の調査は次工程。旧Save52 cold差/Save54回復台帳owner未解明も保持。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save54']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37150128114');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='1e4551b4da705a01da77fd53f109a182cf316c8a','旧Stage79終端')
    state['story_save54']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save55']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[3,2],xy=[16,20],facing=1,rp=0,money=17904,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[15,10,15,14],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=False,trainer_victories=1,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='回復済から必須レンジャー1勝/通常贈与/Save55。像の裏の紙へ。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='通常レンジャー1勝/がくしゅうそうち/Save55。次はこころのやかた奥の像の裏。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_HEART_MANSION_FROM_RANGER_SAVE55',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save55_accept.py','scripts/pr16_story_save55_measure.py',a.EVIDENCE+'/inspection.json','content/modernization/pr16_story_save55_preparation.json','content/modernization/pr16_story_save53_owner.json'],stop_rule_ja='Save55のみ。こころのやかた奥の像の裏の紙という実台詞の必須導線を省略しない。未読室内ownerを限定調査し、通常入館→最初の新event/戦闘/未通過境界で保存。レンジャー戦/回復の再走なし。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='レンジャー6体へ1勝、がくしゅうそうち取得しSave55。map3/2・16,20南。次は像の裏の紙。'
    state['do_not_repeat'].append('Save55の268/cold13入力139画面・21controller47受入を無影響再走しない。レンジャー331の6体/864円/がくしゅうそうち/flag4381。131counterは部分write、132安定でも保存中→133成功→136field。RAM台帳差とoffset41三件/aux40acのowner未解明。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE|extra)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 通常レンジャー戦・贈与・Save55
- Version: story-miru-ranger-save55-v1
- Status: DONE（新必須1勝/贈与/保存/独立Continue限定）
- Summary: 回復再走なしで通常出口/30歩。trainer331の6体へ1勝、864円とがくしゅうそうち1個、像の裏の紙の依頼、離脱flag4381。オノノクス288/294・PP[15,10,15,14]。ミュウツー全HP/PP保持。
- Files changed: Save55 inspect/measure/21controller/47受入/record、45node38cell静的原本、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、268+cold13入力139画面154member、21controller原logと47新受入拒否。record native0/compile0/旧再走0。
- Evidence: 全party9phase独立照合/保存5byte差分。131counter部分write→132安定/保存中→133成功→136field。items182を1個追加だけ、17904円/RP0、PC/S61E他payload不変。aux3件owner未解明、42checksum/旧bank57344byte/6999byte1764範囲/cold全SaveRTC一致。TM21民家map39/0を必須gymとして扱わない。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actionsのみ。既存ROM/runtime/input非再配布。一般CI既知不一致/action_requiredは全成功にしない。merge/release/baseline変更0。
- Next: {goal}
"""
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

