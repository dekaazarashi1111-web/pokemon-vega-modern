#!/usr/bin/env python3
"""ミルシティの通常回復Save54原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save54_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-HEAL-SAVE54'
OUT=ROOT/'.local/pr16-story-save54-record'

CODE={'scripts/pr16_story_save54_accept.py','scripts/pr16_story_save54_record.py','tests/test_pr16_story_save54_accept.py',a.VISUAL,'.github/workflows/pr16-story-save54-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE54_JA.md' and a.CP=='content/modernization/pr16_story_save54_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save54_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37148761559,'8fa4d19c42eb0771a41b0d0f89b673f4e51ab8de',111278022912,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save54_measure.',21)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==75 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save53全75member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save53/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==54 and len(z.namelist())==55 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save54member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==39 and visual['reviewed_screens']==dict(progress=list(range(37)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save54画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save54画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE54_ORIGINAL=str(original),PR16_SAVE53_INPUT=str(assets/'input.srm'),PR16_SAVE54_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save54_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==43 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 43 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'43成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save53-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save54 artifact11283366654のstory-fast.srm（131088bytes/SHA256 bfdd4fb964fd8a3b526b919921b2400e3c1f44c02011208b03f0507606a496ad）だけから再開。ポケモンセンター1F map6/5・7,4北。通常4歩/受付「あずける」/HP・PP全回復/Save54/独立Continueを限定受入。オノノクスHP294/294・PP[15,10,15,20]、ミュウツーHP354/354・PP[10,20,15,10]、空技のミュウ/ビーダルも全HP。party600byte差分は回復8byteだけ。Bag/17040円/RP0/badge1/story4071=9/4072=1/全flags/PC/S61E不変。回復を再実行せず、保存済室内mapとtown ownerから出口→ミルシティの次必須storyを限定調査し通常入力で進める。最初の新event/戦闘/未通過境界で通常保存、必須story省略なし。aux4021=110→114/4022=2→1と回復後RAM台帳3aef553d4f2dba8f52868966ed63e2e315f111535d017321afe1c0df1a7bd384のowner未解明、旧Save52 cold差ownerも未解明。Save54 progress/coldは同一。Save54counter32は書込中、成功33→field36。66+cold13入力39画面21controller43受入54memberを無影響再走0。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完、doubletarget分離native未実証。既存ROM/runtime/input非再配布、host補充/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。'
    extra={'scripts/pr16_story_save54_inspect.py','.github/workflows/pr16-story-save54-inspect.yml'}
    terminal=inherited.terminal(37149252523,'bdba440a5a434288595b2bcb33b5896ff72be796',111279440130,['success']*8)
    _,z=a.transport.archive(11282394004,37149252523,dict(size=1598,sha256='937c9fcc8e7d81b42cdcb25096e88c23b20a8810ce0dbf111f7e6ad574684f56'),'bdba440a5a434288595b2bcb33b5896ff72be796')
    with z:need(z.namelist()==['inspection.json']and z.read('inspection.json')==(ROOT/a.m.PREP).read_bytes(),'5cells静的原本全byte')
    name=a.EVIDENCE+'/inspection-terminal.json';write(ROOT/name,terminal);paths.add(name)
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save54_accepted=True,normal_recovery_required=False,pp_recovery_accepted=True,normal_recovery_accepted=True,healing_site_reached=True,healer_conversation_started=True,healing_ram_ledger_owner_resolved=False,double_target_separation_native_exercised=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE|extra),evidence_bindings=h.d.bindings(paths),new_controller_tests=21,new_acceptance_tests=43,successful_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# ミルシティ通常受付のHP・PP全回復・Save54限定受入

`{result['status']}`。Save53から室内を北へ4歩、受付前7,4へ移動。カウンター越しに通常A、実画面「あずける」を選択し通常回復、Save54と独立Continue全SaveRTC一致を受入。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。54member/39画面/66+cold13入力、21controller原log/43新受入拒否試験。native2/record0/旧入力再走0/ROM変更0。

## 回復の独立照合

観測5で挨拶、6で「あずける／やめる」、7で預け、8で回復後party、9で挨拶終了、10で操作可能field。既読受付local3(7,2)のscript135790449→shared135872070→135872156、命令135872182のspecial0に対応。host補充なし。

オノノクスHP294/294、PP[11,10,15,14]→[15,10,15,20]。ミュウツーHP50→354/354、PP[0,0,0,0]→[10,20,15,10]。ミュウ342/342、ビーダル300/300、技は空のまま。全600partybyteの差分8byteだけを許可し、残592byteは不変。現候補ROMのpointer0x1cc/stride12/PPoffset4から8技の最大PPを照合。PPbonus0、全員HPとstatusを独立確認。

## 保存境界と未解明範囲

11〜15通常menu、16確認、17上書き。18〜32部分write、32counter54へ先行、33〜35成功文言、36field。cold0/1同位置。Bag/17040円/RP0/badge1/story4071=9/4072=1/全flags/PC/S61E/respawn不変。aux4021=110→114/4022=2→1。旧bank57344byte保全、42checksum、6936byte/1739範囲、全SaveRTC一致。

観測10でRAM台帳がdef3a8d7…から3aef553d…へ変化しcoldまで保持。回復との時間的対応はあるがowner未解明。保存済S61E payloadは不変。旧Save52 cold差/aux ownerも未解明のまま保持。台帳全不変と主張しない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save53']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37148761522');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='8fa4d19c42eb0771a41b0d0f89b673f4e51ab8de','旧Stage79終端')
    state['story_save53']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save54']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[6,5],xy=[7,4],facing=2,rp=0,money=17040,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[294,294],lead_pp=[15,10,15,20],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,normal_recovery_accepted=True,healing_site_reached=True,healer_conversation_started=True,healing_ram_ledger_owner_resolved=False,trainer_victories=0,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='通常受付でHP・PP全回復/Save54。RAM台帳差ownerは未解明。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='通常受付でHP・PP全回復/Save54。次はミルシティ必須story。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MIRU_CONTINUATION_FROM_HEALED_SAVE54',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save54_accept.py','scripts/pr16_story_save54_measure.py',a.EVIDENCE+'/inspection.json','content/modernization/pr16_story_save53_owner.json'],stop_rule_ja='Save54回復済から、保存済map/ownerを使い出口→ミルシティ必須storyを限定確認。最初の新event/戦闘/未通過境界で通常保存。回復再走/host補充なし。RAM台帳差owner未解明を保持。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='通常受付で全HP/PP回復しSave54。map6/5・7,4北。次はミルシティ必須story。'
    state['do_not_repeat'].append('Save54の66/cold13入力39画面・21controller43受入を無影響再走しない。室内4歩/通常受付/回復、戦闘0。party回復8byteのみ。RAM台帳は会話終了で変化しowner未解明、保存S61E不変。旧Save52 cold差ownerも未解明。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE|extra)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / ミルシティ通常受付の全回復・Save54
- Version: story-miru-normal-heal-save54-v1
- Status: DONE（通常回復/保存/独立Continue限定）
- Summary: 室内4歩で受付前7,4北。「あずける」の通常入力でHP/PP全回復。ミュウツーHP50→354/354・PP全0→[10,20,15,10]、オノノクスPP[15,10,15,20]。party差分8byteのみ。
- Files changed: Save54 inspect/measure/21controller/43受入/record、5cell静的原本、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功、66+cold13入力39画面54member、21controller原logと43新受入拒否。record native0/compile0/旧再走0。
- Evidence: 現候補move tableで最大PP照合。18〜32部分write、32counter先行→33成功→36field。Bag/17040円/RP0/PC/S61E/全国図鑑/全flags保持。aux2件、42checksum/旧bank57344byte/6936byte1739範囲/cold全SaveRTC一致。会話終了でRAM台帳差、owner未解明を明示。
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

