#!/usr/bin/env python3
"""505番道路のミルシティ南接続のSave52原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save52_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE505-SAVE52'
OUT=ROOT/'.local/pr16-story-save52-record'

CODE={'scripts/pr16_story_save52_accept.py','scripts/pr16_story_save52_record.py','tests/test_pr16_story_save52_accept.py',a.VISUAL,'.github/workflows/pr16-story-save52-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE52_JA.md' and a.CP=='content/modernization/pr16_story_save52_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save52_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37146098901,'5803a1894ce67270c32e923ececf539d589ee653',111270247423,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save52_measure.',18)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==112 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save51全112member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save51/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==67 and len(z.namelist())==68 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save52member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==52 and visual['reviewed_screens']==dict(progress=list(range(50)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save52画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save52画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE52_ORIGINAL=str(original),PR16_SAVE51_INPUT=str(assets/'input.srm'),PR16_SAVE52_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save52_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==39 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 39 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'39成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save51-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save52 artifact11282311020のstory-fast.srm（131088bytes/SHA256 f3fc9b1d3121b049900defb5c2f031a0b397a10b34fa3464d51f355a87833028）だけから再開。505の未戦闘ペアを視界過大近似の外側で迂回、20歩+南connectionを戦闘0で通過しミルシティmap3/2の28,0南/高度3へ到着。通常Save52/独立Continue全SaveRTC一致を限定受入。party全600byte/HP/PP/Bag/17040円/RP0/badge1/story4071=9/4072=1不変。オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・PP全0、他2体技ID全0。正常回復が最優先。保存済みtown collision/map/warpsから回復施設のowner・必要経路高度・必要eventだけ読取し、通常入口/会話/回復を目指す。最初の新story/event/未通過境界/新建物/実回復で保存、必須story省略なし。town新接続flag2194とaux4021=63→84/4022=0→1/40AE=91→80、およびcold RAMledger差のowner未解明を保持し次の限定調査で確認。progress ledger3c7c0390…は不変、cold def3a8d7…は別hash、全Save一致と混同しない。43最終Flash一時一致counter51→44counter52再差分→45成功/安定→49field。原本94+cold13入力52画面/18controller39受入/67memberを無影響再走0。doubletarget分離native未実証、旧失敗・Save50raw6/実PP2/partybyte41・旧ledger差は保持。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。ROM/host補充/故意全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用。一般CI既知source不一致/action_requiredを全成功にしない。'
    extra={'scripts/pr16_story_save52_inspect.py','.github/workflows/pr16-story-save52-inspect.yml'}
    inspected=inherited.terminal(37146312453,'88ce4ba2005e7ceb76b814525a38048d054e70b0',111270883481,['success']*8)
    _,z=a.transport.archive(11281269881,37146312453,dict(size=1519,sha256='0e320e1d6be1ff2bab31299bf63dcdbaf39e5b2b82303d9f409b8f9735fd0e4b'),'88ce4ba2005e7ceb76b814525a38048d054e70b0')
    with z:need(z.namelist()==['inspection.json']and z.read('inspection.json')==(ROOT/a.m.PREP).read_bytes(),'2体属性の原本byte完全一致')
    write(evidence/'inspection-terminal.json',inspected);paths.add(a.EVIDENCE+'/inspection-terminal.json')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
        artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save52_accepted=True,
        normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,route505_south_connection_accepted=True,double_target_separation_native_exercised=False,
        visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE|extra),evidence_bindings=h.d.bindings(paths),new_controller_tests=18,new_acceptance_tests=39,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 505番道路のペア迂回・ミルシティ到着・Save52限定受入

`{result['status']}`。31,24南から20歩/4方向転換で未戦闘ペアを迂回し、28,39から南connection1回でミルシティ（map3/2）28,0南へ。戦闘0、通常Save52/独立Continue全SaveRTC一致を受入。回復施設/正常回復は未完。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全67member、52画面、94+cold13入力。18新controller原log継承、39新受入/拒否試験。native2/record0/旧入力再走0/ROM変更0。

## ペア回避と通常南接続

read-only run37146312453/job111270883481でlocal3/8のobject属性16byteのみ追加読取。2体とも高度3、movement8、移動範囲x/y=1、trainer type/range=1。movement8の未証明の意味に依存せず、移動範囲内の全位置・全方向視界を過大近似して避ける。既存terrain/map/scriptsは再採取0。

0〜24で32列経由の20歩、草地4tileを通るが遭遇0。25で画面にミルシティ表示、map3/2・28,0南へ。未戦闘ペアを倒した扱いにせず、必須storyを省略していない。

## 全保存とcold RAMの差

party全600byte/全員HP/PP/全Bag/所持品/PC/S61E/17040円/RP0/badge1/story4071=9/4072=1は不変。新接続後の保存差はphysicalflag2194=0→1、var4021=63→84/4022=0→1/40AE=91→80。これらのruntime ownerは未解明。

progress RAMledgerは全50観測で同一だが、coldでは別hashとなる。全Save/RTC一致とは分離して保持する。cold差のowner解明、全国図鑑受入や全story受入を主張しない。

26〜30通常menu cursor0→4、31確認、32上書き。33〜42部分write、43は最終Flash一時一致でもcounter51、44counter52で再差分・書込中文言、45〜48成功文言、49field。cold0/1は同位置。42sector checksum、旧Save51bank57344byte保全、7025byte/1743差分範囲。

オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・全PP0。他2体は技ID全0。回復が最優先。今回戦闘0のため、新ダブルtarget分離や未確認技枠のnative実証は追加0。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8')
    need(h.d.bindings(protected)==protected,'旧受入正本/入力は不変')
    state['story_save51']['record_completion']=prior_done
    stage79=h.d.inputs.api('actions/runs/37146098795');need(stage79['status']=='completed'and stage79['conclusion']=='success'and stage79['head_sha']=='5803a1894ce67270c32e923ececf539d589ee653','Save51記録source Stage79終端')
    state['story_save51']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save52']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[3,2],xy=[28,0],facing=1,elevation=3,rp=0,money=17040,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[294,294],lead_pp=[11,10,15,14],mewtwo_hp=[50,354],mewtwo_pp=[0]*4,normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,trainer_victories=0,route505_south_connection_accepted=True,cold_ram_ledger_differs=True,cold_ram_ledger_change_owner_resolved=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='ペア回避20歩+ミルシティ南接続/Save52限定受入。戦闘0、正常回復未完。cold RAM差を全Save一致と分離。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='505のペア迂回20歩とミルシティ接続、Save52測定source。正常回復未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_NORMAL_RECOVERY_IN_MIRU_CITY_FROM_SAVE52',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save52_accept.py','scripts/pr16_story_save52_measure.py',a.EVIDENCE+'/inspection.json',a.m.PREP],stop_rule_ja='Save52/ミルシティ28,0南から必要な回復施設owner/経路高度/eventだけ静的確認し通常入力。最初の新story/event/未通過境界/新建物/実回復で保存。cold RAM差・新接続flag/varsは未解明として保持。必須story省略・host補充なし。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='505の未戦闘ペアを避け20歩+南接続、ミルシティ28,0南でSave52/独立Continueを限定受入。HP/PP不変、通常回復未完。'
    state['do_not_repeat'].append('Save52の94/cold13入力52画面・18controller39受入を無影響再走しない。20歩+ミルシティ接続、戦闘0。party/HP/PP不変。新接続flag2194/vars3件とcold RAMledger差owner未解明。43一時Flash一致→44counter/再差分→45成功→49field。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE|extra)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 505番道路ペア迂回・ミルシティ接続・Save52
- Version: story-miru-city-save52-v1
- Status: DONE（20歩/南接続/保存/独立Continue限定受入。回復未完）
- Summary: 31,24→20歩→28,39→ミルシティmap3/2の28,0南。戦闘0/HP/PP不変、17040円。オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・PP全0。
- Files changed: Save52 inspect/measure/18新controller・39新受入拒否/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、94/cold13入力52画面67member。18controller原log継承、新39受入、record native0。ダブルtarget分離native未実証を保持。
- Evidence: party全600byte不変。新接続physicalflag2194、vars4021/4022/40AEとcold RAMledger差owner未解明。33〜42/44部分write、43一時最終hash一致counter51→44counter52再差分→45成功→49field。42checksum/旧bank57344byte/7025byte1743範囲/cold全SaveRTC一致。
- Reuse: 保存済terrain/map/scripts再採取0。未読2object属性16byteだけread-only採取し原本zip全byte結合。移動範囲/全方向視界を過大近似してペアを回避、草地4cellで遭遇0。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actionsのみ。既存ROM/runtime/input非再配布。旧失敗・未解明差保持。一般CI既知source不一致/action_requiredは全成功としない。merge/release/baseline変更0。
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

