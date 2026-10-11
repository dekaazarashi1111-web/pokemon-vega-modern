#!/usr/bin/env python3
"""像のだいじなふうしょ取得Save73原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save73_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-MANSION-STATUE-LETTER-SAVE73'
OUT=ROOT/'.local/pr16-story-save73-record'

CODE={'scripts/pr16_story_save73_accept.py','scripts/pr16_story_save73_record.py','tests/test_pr16_story_save73_accept.py',a.VISUAL,'.github/workflows/pr16-story-save73-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE73_JA.md' and a.CP=='content/modernization/pr16_story_save73_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save73_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37167376758,'1a42d3433d5a1382c50cc305c88613328186b5d2',111333037803,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save73_measure.',32)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==58 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save72全58member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save72/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==47 and len(z.namelist())==48 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save73member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==32 and visual['reviewed_screens']==dict(progress=list(range(30)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save73画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save73画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE73_ORIGINAL=str(original),PR16_SAVE72_INPUT=str(assets/'input.srm'),PR16_SAVE73_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save73_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==62 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 62 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'62成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save72-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save73 artifact11290362029のstory-fast.srm（131088bytes/SHA256 1790277ae4ff1fbb3242a3e58578dfbc66aa98b9e274e42d9811ffb438eb22bb）だけから再開。上階map1/60・16,27南。通常南向き1回→像を初めて調べ、実画面でだいじなふうしょ取得、key_items slot4にitem274が0→1、expanded4383が0→1。通常Save73/独立Continueを限定受入。新戦闘/歩行0、全party600byte・HP288/294・PP9,10,15,2/他Bag・19416円/PC保持、legacy全flags/vars/RAM台帳保持、S61E payload259が32→160だけでCRC正常。次は紙取得後の新復路9歩、16,27→17,27→17,26→17,25→18,25→18,24→18,23→19,23→20,23→20,24の上階hole behavior102/warp5から下階map1/59・warp8/20,24へ通常南入力で降りる候補。最初の新戦闘/event/下降境界で保存する。下階warp8は旧不発着地点、上階holeとは別。像取得や旧routeを成功caseとして再走しない。32新controller/62新受入、53+cold13入力32画面47member/native2、旧成功再走0。24最終Flash一時一致→25counter73も保存中→26成功→29field。全SaveRTC/field5画像全pixel一致。紙の使用/引渡し・hole下降/館退出は未受入。旧offset41/2056/aux/40acのruntime owner未解明、Flash未使用/がくしゅうそうち未装備、全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save73_accepted=True,heart_mansion_entered=True,statue_paper_observed=True,paper_obtained=True,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,paper_side_reached=True,statue_visual_observed=True,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,southeast_stair_previously_accepted=True,normal_recovery_repeated=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=32,controller_executions=32,unchanged_controller_cases_replayed=0,new_acceptance_tests=62,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 像のだいじなふうしょ取得Save73限定受入

`{result['status']}`。Save72の上階16,27西から南へ向き、ミュウツーの像を初めて調べた。画面で「だいじなふうしょ」を大切なものポケットへ入れ、通常保存・独立Continue。新戦闘/歩行0。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。47member/32画面/53+cold13入力。新controller32/新受入62。native2/record0/旧成功再走0/ROM変更0。

## 取得・通常保存

0西→1南、2像を調べた、3だいじなふうしょ取得表示、4解錠。key_items slot4 (0,0)→(274,1)、全他Bag/19416円保持。像script149012422のadditem274/setflag4383と、S61E payload259:32→160/CRCを独立照合。全legacy flags/vars/RAM台帳と全party600byte/HP288/294・PP9,10,15,2/PCを保持。

5〜9menu0→4、10確認/11上書き。12〜25保存中、24で最終Flashに一時一致しても25に再変化、counter73も25では保存中。26〜28成功文言、29field。progress1/4/29/cold0/cold1全画面byte一致、全SaveRTC一致。42checksum/6849byte1672範囲、旧Save72bank57344byte保持。

## 次の新しい復路

[静的9歩hole下降候補](../{a.EVIDENCE}/next-route.json)。16,27から上階20,24のbehavior102/warp5へ行き、下階map1/59のwarp8/20,24へ降りる候補。下階で不発だった着地点へ同じ入力を繰り返す話ではない。実下降/館退出/紙使用・引渡しは未受入。最初の新戦闘/event/下降で停止・保存する。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save72']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37167376719');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='1a42d3433d5a1382c50cc305c88613328186b5d2','旧Stage79終端')
    state['story_save72']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save73']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,60],xy=[16,27],facing=1,rp=0,money=19416,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=True,paper_obtained=True,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,paper_side_reached=True,statue_visual_observed=True,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,southeast_stair_previously_accepted=True,inert_warp8_activation=False,trainer_victories=0,wild_victories=0,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='像の初回ふうしょ取得/Save73。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='像を初めて調べ、だいじなふうしょ274とflag4383を通常取得しSave73。全party・HP・PP保持。次は紙取得後の新9歩/hole下降候補。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_POST_LETTER_HOLE_DESCENT_FROM_SAVE73',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save73_accept.py','scripts/pr16_story_save73_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save62_evidence/route-plan.json','content/modernization/pr16_story_save57_preparation.json'],stop_rule_ja='Save73上階16,27南から紙取得後の新復路9歩/上階20,24のhole102→下階1/59の20,24候補だけ。最初の新戦闘/event/下降で通常保存。紙274/flag4383保持、PP9,10,15,2、host補充なし。像の取得event/受入済み入力を再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='像を初めて調べ、だいじなふうしょ274/flag4383を取得しSave73。上階16,27南、全party・HP288/PP9,10,15,2保持。次は紙取得後の新9歩/hole下降候補。'
    state['do_not_repeat'].append('Save73の53/cold13入力32画面47member/32controller/62受入を無影響再走しない。像の紙274/flag4383は取得済み。新戦闘/歩行0、全party/他Bag/19416円/PC/legacy flags-vars/RAM台帳保持。24一時最終hash→25counterも保存中→26成功→29field。全SaveRTC/field5画像一致。次は新しい復路/hole下降だけ。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 像のだいじなふうしょ取得Save73
- Version: story-mansion-statue-letter-save73-v1
- Status: DONE（紙取得/通常保存/独立Continue限定）
- Summary: 上階16,27西→南、像の初回eventでだいじなふうしょ274を通常取得。key_items slot4 0→1、expanded4383 0→1、S61E payload259:32→160/CRC正常。全party600byte/HP288/PP9,10,15,2/他Bag/19416円/PC/legacy全flags-vars/RAM台帳保持。
- Files changed: Save73 measure/32controller/62受入/record/checkpoint/text証拠/新9歩hole下降静的候補、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。53+cold13入力32画面47member。新controller32原log継承/新受入62。record native0/compile0/旧成功再走0。
- Evidence: 24最終Flash一時一致→25counter73も保存中→26成功→29field。全SaveRTC/field5画像全pixel一致、42checksum/6849byte1672範囲。紙使用/引渡し・hole下降/館退出は未受入。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force push/全text読戻し。
- Network: 同repo GitHub/Actionsだけ。既存ROM/runtime/input非再配布。一般CI既知不一致/action_requiredを全成功にしない。merge/release/baseline変更0。
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




