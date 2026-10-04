#!/usr/bin/env python3
"""上階南側14歩・野生バーニン1勝Save71原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save71_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-MANSION-UPPER-SOUTH-WILD-SAVE71'
OUT=ROOT/'.local/pr16-story-save71-record'

CODE={'scripts/pr16_story_save71_accept.py','scripts/pr16_story_save71_record.py','tests/test_pr16_story_save71_accept.py',a.VISUAL,'.github/workflows/pr16-story-save71-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE71_JA.md' and a.CP=='content/modernization/pr16_story_save71_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save71_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37165819639,'4d7d8a4f690aadfd933e5f03ca991b7355b791a4',111328367226,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save71_measure.',29)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==60 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save70全60member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save70/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==68 and len(z.namelist())==69 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save71member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==53 and visual['reviewed_screens']==dict(progress=list(range(51)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save71画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save71画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE71_ORIGINAL=str(original),PR16_SAVE70_INPUT=str(assets/'input.srm'),PR16_SAVE71_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save71_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==62 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 62 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'62成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save70-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save71 artifact11289573274のstory-fast.srm（131088bytes/SHA256 87f67074b6d470df8260e15d2bd58566f949a6297318a1e7a9ee3d9b80cbb6fd）だけから再開。上階33,29東から新14歩/転換2、23,31で野生バーニン♂Lv13をドラゴンクロー1回で撃破し通常Save71/独立Continueを限定受入。HP288/294保持・PP9,10,15,2、全party599byte/Bag19416円/PC/S61E保持、RP0/badge1/story4071=9/4072=1。legacy flag差分0、aux4021:29→43/4022:4→0のowner未解明、全RAM台帳不変。次は同map1/60・23,31西から残り未通過11歩23,31→17,31→17,27→紙側16,27。初の新event/戦闘/不通境界、または紙側到着で通常保存。紙/像16,28/item274/flag4383は静的ownerのみ、取得未完。29新controller/62新受入、93+cold13入力53画面68member/native2、旧成功再走0。44は最終hash先行一致だが保存中、45counter71でも部分write→46成功→50field。勝利残留flags4/outcome1/wire field:falseを追加勝利や未復帰にしない。全SaveRTC/field4画面全pixel一致。旧offset41/2056/aux/40acのruntime owner未解明を保持。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save71_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,southeast_stair_previously_accepted=True,normal_recovery_repeated=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=29,controller_executions=29,unchanged_controller_cases_replayed=0,new_acceptance_tests=62,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 上階南側・野生バーニンSave71限定受入

`{result['status']}`。Save70の上階33,29東から南側の新14歩/転換2で23,31へ。野生バーニン♂Lv13に遭遇、ドラゴンクロー1回で撃破し通常保存・独立Continue。紙側は未到達。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。68member/53画面/93+cold13入力。新controller29/新受入62。native2/record0/旧成功再走0/ROM変更0。

## 初遭遇・通常保存・独立Continue

0〜16上階南側新14歩/転換2。16野生導入、17一時黒画面、18〜24戦闘、22ドラゴンクロー選択、23技使用/partyPP更新、24撃破、25通常field。勝利flags4/outcome1とwire field:falseが残っても、callback/lock/画面でfield復帰を確認する。

26〜30menu0→4、31確認/32上書き、33〜45保存中。44のFlashは最終hashと同一だが未完、45は再び部分write/counter71。46〜49成功文言、50field。progress25/50/cold0/cold1全画面byte一致、全SaveRTC一致。

## 保存境界・次の未通過区間

party600byte中599byte保持、差分offset52 PP10→9だけ。HP288/294・PP9,10,15,2/Bag19416円/PC/S61E/旧Save70bank57344byte保持。legacy flag差分0、aux4021:29→43/4022:4→0のowner未解明、全RAM台帳不変。42checksum/6877byte1684範囲。

[次の未通過11歩](../{a.EVIDENCE}/next-route.json)は23,31→17,31→17,27→紙側16,27。紙/像16,28のitem274・flag4383は静的ownerだけで取得未完。旧14歩/野生戦/階段を再走しない。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save70']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37165819478');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='4d7d8a4f690aadfd933e5f03ca991b7355b791a4','旧Stage79終端')
    state['story_save70']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save71']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,60],xy=[23,31],facing=3,rp=0,money=19416,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,southeast_stair_previously_accepted=True,inert_warp8_activation=False,trainer_victories=0,wild_victories=1,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='上階新14歩/野生バーニン1勝/Save71。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='上階南側14歩で野生バーニン1勝、23,31西でSave71。HP288/294保持・PP9,10,15,2。次は紙側まで残り11歩。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_UPPER_SOUTH_PAPER_APPROACH_FROM_SAVE71',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save71_accept.py','scripts/pr16_story_save71_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save62_evidence/route-plan.json','content/modernization/pr16_story_save57_preparation.json'],stop_rule_ja='Save71上階23,31西から残り未通過11歩で紙側16,27へ。初の新event/戦闘/不通境界、または紙側へ初到着したら通常保存。PP9,10,15,2、host補充なし。旧14歩/野生戦/南東階段/保存は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='上階南側新14歩で野生バーニン1勝、23,31西でSave71。HP288/294保持・PP9,10,15,2/19416円。次は紙側まで残り未通過11歩。'
    state['do_not_repeat'].append('Save71の93/cold13入力53画面68member/29controller/62受入を無影響再走しない。上階南側新14歩/転換2/野生バーニン♂Lv13新1勝。23,31西/HP288保持/PP9,10,15,2/Bag19416円保持。legacy flag不変/aux2変数owner未解明/RAM台帳不変。44最終hashでも保存中→45counter71/部分write→46成功→50field。全SaveRTC/field4画像一致、勝利残留/wire falseを追加勝利や未復帰にしない。紙未到達。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 上階南側14歩・野生バーニン1勝Save71
- Version: story-mansion-upper-south-wild-save71-v1
- Status: DONE（新14歩/野生1勝/通常保存/独立Continue限定）
- Summary: 上階33,29東から南側新14歩/転換2、23,31で野生バーニン♂Lv13をドラゴンクロー1回で撃破。party599byte・HP288/294保持、PP9,10,15,2/Bag19416円/PC/S61E保持。legacy flag0差分/aux2変数owner未解明/RAM台帳不変。
- Files changed: Save71 measure/29controller/62受入/record/checkpoint/text証拠/残り11歩候補、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。93+cold13入力53画面68member。新controller29原log継承/新受入62。record native0/compile0/旧成功再走0。
- Evidence: 44最終hashでも保存中→45counter71/部分write→46成功→50field。全SaveRTC/field4画面全pixel一致。勝利残留/wire falseを別扱い。42checksum/6877byte1684範囲。紙未到達。
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




