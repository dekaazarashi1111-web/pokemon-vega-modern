#!/usr/bin/env python3
"""505番道路の高台東側経路とワタミ戦のSave51原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save51_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-ROUTE505-SAVE51'
OUT=ROOT/'.local/pr16-story-save51-record'

CODE={'scripts/pr16_story_save51_accept.py','scripts/pr16_story_save51_record.py','tests/test_pr16_story_save51_accept.py',a.VISUAL,'.github/workflows/pr16-story-save51-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE51_JA.md' and a.CP=='content/modernization/pr16_story_save51_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save51_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37144605978,'384ecdce0ab7aad6925c8a8a1ad01adab4c17f93',111265850823,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save51_measure.',22)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==168 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save50全168member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save50/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==112 and len(z.namelist())==113 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save51member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==97 and visual['reviewed_screens']==dict(progress=list(range(95)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save51画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save51画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE51_ORIGINAL=str(original),PR16_SAVE50_INPUT=str(assets/'input.srm'),PR16_SAVE51_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save51_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==44 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 44 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'44成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save50-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save51 artifact11281768926のstory-fast.srm（131088bytes/SHA256 8661346e2de9bc73fc61d5a63af5bd6acd10008486b54c66c9459820a5447d65）だけから再開。505番道路22,18→新27歩/高台東階段→31,24南/高度3でワタミのsingle戦1勝、通常Save51/独立Continue全SaveRTC一致を限定受入。party4/RP0/17040円/badge1/story4071=9/4072=1。オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・PP全0、他2体技ID全0。正常回復が最優先。保存済みroute index84から残20歩と南connection→map3/2の28,0が候補。28,27/29,27の未戦闘trainerの視界を避けられるか、保存済みterrain/graphと必要な未読object属性だけで確認してから進む。最初の新戦闘/event/未通過境界/接続/実回復で保存。新controllerは選択とtargetを分離しSave50実PPへ再束縛、今回はsingleなので選択4/target0/実PP4だけをnative確認、次回実PP14へ再束縛。ダブルtarget分離native未実証。42/63RAMledgerとaux4021=37→63のowner未解明。90安定Flash/counter51→91成功文言→94fieldを分離。原本184+cold13入力97画面/22controller44受入/112memberを無影響再走0。旧Save50 raw6/実PP2・partybyte41/旧ledger差、旧失敗を保持。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。ROM/host補充/故意全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用。一般CI既知source不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,
        artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save51_accepted=True,
        normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,route505_south_connection_accepted=False,double_target_separation_native_exercised=False,
        visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),new_controller_tests=22,new_acceptance_tests=44,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 505番道路の高台東階段・ワタミ戦・Save51限定受入

`{result['status']}`。22,18北から新27歩/8方向転換、高度4の東側を横断して32,14階段で高度3へ、31,24南でスキーヤーのワタミとsingle戦1勝。通常Save51/独立Continueだけを受入。南接続/正常回復は未完。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。全112member、97画面、184+cold13入力。新22controller原log継承、44新受入/拒否試験。native2/record0/旧入力再走0/ROM変更0。

## 通常入力と戦闘

35〜37は接近会話、38〜69はワタミ戦、ココガラ/イシズマイ/ビッパ/クヌギダマの4体。67勝利、69賞金1400円、70field。15640→17040円。trainer1055は同ROM remapでphysicalflag1407、保存差はその1bitだけ。

44/45/46は技cursor0→2→3。46/52/58/64でつばめがえしを選択、49/55/61の交代確認はBで拒否。新controllerは選択コマンド4と相手確定0を分離し、保存byte55=18→14から実PP4を独立確認。ダブルtarget分離のnative実証は今回は0、全4技のnative受入でもない。旧Save50のraw used6/実PP2は原本のまま保持。

オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・全PP0。他2体は技ID全0。今回のparty差は1byteだけ、全員HPを保持。正常回復は未完。

## 全保存境界

全Bag/所持品/PC/S61E/badge1/story4071=9/4072=1は不変。RAMledger42/63とaux4021=37→63はruntime owner未解明、cold最終ledgerは一致。旧Save50の歩行byte41など未解明差も保持。

71〜75通常menu cursor0→4、76確認、77上書き、78〜89は12種類の部分write。90安定Flash/counter51でも成功文言なし、91〜93成功文言、94field。cold0/1は31,24南で全SaveRTC一致。42sector checksum、旧Save50bank57344byte保全、6944byte/1717差分範囲。

## 再利用と次区間

Save50で保存した未通過47歩候補、terrain/map/scriptsをそのまま再利用。追加読取0、既受入57歩の再走0。今回新27歩を通過し、南接続前まで候補残20歩。28,27/29,27の未戦闘trainer付近を通るため、視界を避けられる安全な候補があるか必要な属性だけ確認して回復を優先する。必須storyは省略しない。

全国図鑑/自然EXP・技習得・進化/全story/研究施設自然到達/releaseは未完。一般CI既知source不一致とaction_requiredを全green扱いしない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8')
    need(h.d.bindings(protected)==protected,'旧受入正本/入力は不変')
    state['story_save50']['record_completion']=prior_done
    stage79=h.d.inputs.api('actions/runs/37144605824');need(stage79['status']=='completed'and stage79['conclusion']=='success'and stage79['head_sha']=='384ecdce0ab7aad6925c8a8a1ad01adab4c17f93','Save50記録source Stage79終端')
    state['story_save50']['stage79_completion']={k:stage79[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save51']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[3,23],xy=[31,24],facing=1,elevation=3,rp=0,money=17040,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[294,294],lead_pp=[11,10,15,14],mewtwo_hp=[50,354],mewtwo_pp=[0]*4,normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=False,trainer_victories=1,route505_south_connection_accepted=False,double_target_separation_native_exercised=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='通常27歩/ワタミsingle戦/Save51限定受入。正常回復未完、target分離はsingleでnative未実証。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='505の高台東階段と通常27歩、ワタミ戦とSave51測定source。正常回復未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_RECOVERY_ON_ROUTE505_FROM_SAVE51',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save51_accept.py','scripts/pr16_story_save51_measure.py',a.EVIDENCE+'/inspection.json','content/modernization/pr16_story_save50_preparation.json','content/modernization/pr16_story_save50_west_preparation.json'],stop_rule_ja='Save51/31,24南から保存済み候補残20歩と南connection。未戦闘trainerの視界を避ける静的候補を先に確認。必須story省略なし、最初の新戦闘/event/未通過境界/接続/実回復で保存。実PP14へ再束縛。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='通常27歩/高台東階段とワタミ戦1勝、505番道路31,24南でSave51/独立Continueを限定受入。ミュウツーHP50/全PP0、回復未完。'
    state['do_not_repeat'].append('Save51の184/cold13入力97画面・22controller44受入を無影響再走しない。27歩/ワタミ1勝/Save51、選択4/target0/実PP4。ダブルtarget分離native未実証。RAMledger42/63とaux4021owner未解明。90安定/counter→91成功→94field。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f'''
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 505番道路の高台東階段・ワタミ戦・Save51
- Version: story-route505-save51-v1
- Status: DONE（新27歩/通常single戦1勝/保存/独立Continue限定受入。回復未完）
- Summary: 22,18→31,24南/高度3。通常賞金1400円で17040円。オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・PP全0、全員HP不変。
- Files changed: Save51 measure/22新controller・44新受入拒否/record workflow、checkpoint/text証跡、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、184/cold13入力97画面112member。22controller原log継承、新44受入、record native0。選択4/target0/実PP4を別検証、ダブルtarget分離native未実証。
- Evidence: party差byte55の1byteだけ。physicalflag1407、aux4021=37→63とRAMledger42/63 owner未解明。78〜89部分write、90安定Flash/counter51→91成功→94field。42checksum/旧bank57344byte/6944byte1717範囲/cold全SaveRTC一致。
- Reuse: Save50のterrain/map/scriptsと候補を再利用、追加静的読取0/旧native再走0。残20歩と南connectionは未踏。未戦闘trainer視界の回避可能性を確認し通常回復を優先。
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

