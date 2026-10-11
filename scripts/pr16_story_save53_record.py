#!/usr/bin/env python3
"""505番道路のミルシティ南接続のSave53原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save53_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MIRU-SAVE53'
OUT=ROOT/'.local/pr16-story-save53-record'

CODE={'scripts/pr16_story_save53_accept.py','scripts/pr16_story_save53_record.py','tests/test_pr16_story_save53_accept.py',a.VISUAL,'.github/workflows/pr16-story-save53-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE53_JA.md' and a.CP=='content/modernization/pr16_story_save53_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save53_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37147254753,'9e4b701087c609141774a6a746b96bdc1aeede66',111273645819,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save53_measure.',20)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==67 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save52全67member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save52/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==75 and len(z.namelist())==76 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save53member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==60 and visual['reviewed_screens']==dict(progress=list(range(58)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save53画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save53画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE53_ORIGINAL=str(original),PR16_SAVE52_INPUT=str(assets/'input.srm'),PR16_SAVE53_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save53_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==39 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 39 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'39成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save52-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save53 artifact11283178064のstory-fast.srm（131088bytes/SHA256 e22287b3ef44b53029d855aca7cac243f567af75fce21d557f28294c7f4c9a13）からのみ再開。ミルシティのポケモンセンター1F map6/5・7,8北。通常26歩/入口/Save53/独立Continueを限定受入。party600byte/Bag/17040円/RP0/badge1/story4071=9/4072=1不変。オノノクスHP294/294・PP[11,10,15,14]、ミュウツーHP50/354・PP全0で正常回復が最優先。施設map/warps/owner graphは保存済み。受付local3の7,2、script135790449→135872070→135872156→special0を同一候補で確認。必要な室内経路高度だけ読み、カウンター越しの通常会話/回復へ進む。最初の新event/未通過境界/実回復で通常保存、必須story省略なし。Save52のflag2194 ownerはtown load script136400616の命令136400637/setworldmapflag。既受入の原本を書換えず後継解決として記録。今回var4021=84→110/4022=1→2と旧cold RAM差のowner未解明を保持。今回progress/cold ledgerはdef3a8d727dc95294ed0908fa68914b62022587e25ef55d2fe352a942c1ec502で同一。Save53成功54→field57、counter53だけでは完了判定しない。108+cold13入力60画面20controller39受入75memberを無影響再走0。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完、doubletarget分離native未実証。既存ROM/runtime/input非再配布、host補充/故意全滅/merge/release/baseline切替なし。一般CI既知source不一致/action_requiredを全成功にしない。'
    extra={'scripts/pr16_story_save53_inspect.py','.github/workflows/pr16-story-save53-inspect.yml','scripts/pr16_story_save53_owner.py','.github/workflows/pr16-story-save53-owner.yml','content/modernization/pr16_story_save53_preparation.json'}
    specs=[(37147799280,'cb5100a3a7b88b017b49908779e2a87344911c3a',111275230755,11283217077,dict(size=7794,sha256='aee22c54ec74f952dacd4057e86af9ab621e6fd8431af0dd8a78dbc8a19d5839'),'content/modernization/pr16_story_save53_preparation.json'),(37147984676,'94462ddced1f8a4b21afab8ce49f170bb93d09cf',111275763489,11282334060,dict(size=7871,sha256='b8bec3e6cd087cacc6cdc9fb8446ec9ec754b3c476d25c3cf0c22978b5aaf61f'),a.m.PREP)]
    for run,source,job,aid,archive,path in specs:
        terminal=inherited.terminal(run,source,job,['success']*8);_,z=a.transport.archive(aid,run,archive,source)
        with z:need(z.namelist()==['inspection.json']and z.read('inspection.json')==(ROOT/path).read_bytes(),'owner静的原本全byte一致')
        name=a.EVIDENCE+'/inspection-'+str(run)+'-terminal.json';write(ROOT/name,terminal);paths.add(name)
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save53_accepted=True,normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=True,healer_conversation_started=False,town_flag2194_owner_resolved=True,double_target_separation_native_exercised=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE|extra),evidence_bindings=h.d.bindings(paths),new_controller_tests=20,new_acceptance_tests=39,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# ミルシティ回復施設への通常到達・Save53限定受入

`{result['status']}`。ミルシティ28,0南から26歩/3方向転換で38,16へ。通常door38,15からポケモンセンター1F map6/5の7,8北へ入り、Save53と独立Continue全SaveRTC一致を受入。受付との会話と回復は未完。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。75member/60画面/108+cold13入力、20controller原log/39新受入拒否試験。native2/record0/旧入力再走0/ROM変更0。

## Ownerの限定確認

保存済town mapを再利用。最初の候補6/0は回復specialがなく除外。後続6/5でrespawn3、受付local3(7,2)のscript135790449からshared135872070/135872156、命令135872182のspecial0へ到達するgraphを固定。同候補の既存母親heal special0と一致し、画面にもポケモンセンターが表示された。ただし会話/実回復は次。

旧Save52のflag2194はtown load script136400616の命令136400637/setworldmapflagで解決。旧原本の未解明記述は改作せず、後継調査として扱う。aux varsと旧cold RAM差は未解明。

## 保存境界

31で室内field。32〜36通常menu、37確認、38上書き。39〜53は部分write、53でcounter53へ先行、54〜56成功文言、57field。cold0/1同位置。全party600byte/HP/PP/Bag/17040円/RP0/badge1/story4071=9/4072=1/PC/S61E不変。flags変化0、aux4021=84→110/4022=1→2。respawnは[3,1,255,0,16,0,13,0]から[3,2,255,0,38,0,16,0]へ通常更新。旧Save52 bank57344byte保全、42checksum、6989byte/1765範囲。今回progress/cold ledgerはSave52 cold値def3a8d7…から不変。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save52']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37147254700');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='9e4b701087c609141774a6a746b96bdc1aeede66','旧Stage79終端')
    state['story_save52']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save52']['later_flag2194_owner_resolution']=dict(checkpoint=a.CP,script=136400616,instruction=136400637,command='setworldmapflag',original_evidence_unchanged=True)
    state['story_save53']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[6,5],xy=[7,8],facing=2,rp=0,money=17040,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[294,294],lead_pp=[11,10,15,14],mewtwo_hp=[50,354],mewtwo_pp=[0]*4,normal_recovery_required=True,pp_recovery_accepted=False,healing_site_reached=True,healer_conversation_started=False,trainer_victories=0,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='ポケモンセンターへの通常入館Save53。回復まだ、旧flag2194 ownerだけ後継解決。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='ミルシティ26歩/通常入館Save53。回復は未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_NORMAL_HEALER_CONVERSATION_FROM_SAVE53',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save53_accept.py','scripts/pr16_story_save53_measure.py',a.EVIDENCE+'/inspection.json',a.m.PREP],stop_rule_ja='Save53室内7,8北から必要な経路だけ静的確認し、受付local3との通常会話/回復へ。最初の新event/未通過境界/実回復で通常保存。旧cold RAM差/aux owner未解明を保持、host補充なし。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='ミルシティ回復施設map6/5の7,8北、Save53。HP/PP不変、受付会話/回復が次。'
    state['do_not_repeat'].append('Save53の108/cold13入力60画面・20controller39受入を無影響再走しない。26歩/通常入館、戦闘0。全party不変。今回RAM台帳不変、旧Save52 cold差ownerは未解明のまま。新flag0/aux2件、respawn通常更新。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE|extra)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / ミルシティ回復施設の通常到達・Save53
- Version: story-miru-healing-building-save53-v1
- Status: DONE（通常入館/保存/独立Continue限定。回復未完）
- Summary: town26歩/3方向転換、通常door38,15からmap6/5の7,8北。受付local3のheal special0静的owner確認。全party/HP/PP不変。旧flag2194だけsetworldmapflag ownerを後継解決。
- Files changed: Save53 inspect/owner/measure/20controller/39受入/record、静的原本2、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、108+cold13入力60画面75member、20controller原logと39新受入拒否。record native0/compile0/旧再走0。
- Evidence: 39〜53部分write、53counter先行→54成功→57field。party600byte/Bag/17040円/RP0/PC/S61E/全国図鑑未解禁保持、flags0/aux2件、通常respawn更新。42checksum/旧bank57344byte/6989byte1765範囲/cold全SaveRTC一致。今回RAM不変、旧差owner未解明。
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

