#!/usr/bin/env python3
"""紙保持の新南9歩・館退出Save75原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save75_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-MANSION-EXIT-SAVE75'
OUT=ROOT/'.local/pr16-story-save75-record'

CODE={'scripts/pr16_story_save75_accept.py','scripts/pr16_story_save75_record.py','tests/test_pr16_story_save75_accept.py',a.VISUAL,'.github/workflows/pr16-story-save75-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE75_JA.md' and a.CP=='content/modernization/pr16_story_save75_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save75_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37169376902,'386d8366f85ed44bbdbea1f1ad3892f7890b4c4f',111339017542,['success']*11)
    test_receipts=[]
    for job,suite,count in [(a.JOB,'test_pr16_story_save75_measure.',31)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==61 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save74全61member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save74/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==51 and len(z.namelist())==52 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save75member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==36 and visual['reviewed_screens']==dict(progress=list(range(34)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save75画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save75画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE75_ORIGINAL=str(original),PR16_SAVE74_INPUT=str(assets/'input.srm'),PR16_SAVE75_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save75_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==63 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 63 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'63成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save74-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save75 artifact11290759615のstory-fast.srm（131088bytes/SHA256 6554c5f872f710b4dbef5a2db06fbf3d2b91ab3a2984008be53c7ce1ecf4ffb2）だけから再開。入口階20,24から新南9歩/出口追加南1入力で館退出、ミルシティmap3/2・15,20南への自動南1歩と通常Save75/独立Continueを受入。紙274一個/flag4383・全party600byte/HP288/294・PP9,10,15,2/Bag19416円/PC/S61E保持。次は保存済script graph/tableからitem274/flag4383のcheck/remove/clearとstory4071=9/4072=1の後続入口を限定照合し、未読consumerだけ同一候補ROMで読む。受取人/次目的地を推測せず、正規イベントownerと歩行経路を固定してからSave75以降の最初の新戦闘/event/退出境界へ進み通常保存する。旧像取得/館内/退出は再走しない。31新controller/63新受入、63+cold13入力36画面51member/native2。27/28部分hash安定→29counter75/最終Flashでも文言未完→30成功→33field。全SaveRTC一致、町のNPC/水面は画面差あり、player/館外観112x89crop全pixel一致。physical2056:1→0/aux4021:62→71/4022:4→3/40ac:16→0、RAM台帳は7/20,31で変化、owner未解明。紙使用/引渡し、全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。Flash未使用/がくしゅうそうち未装備。host補充/ROM変更/既存ROMruntimeinput再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save75_accepted=True,heart_mansion_entered=True,statue_paper_observed=True,paper_obtained=True,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,paper_side_reached=True,statue_visual_observed=True,unread_floor_entered=True,hole_descent_observed=False,hole_descent_previously_accepted=True,mansion_exit_observed=True,automatic_town_south_step_observed=True,southeast_stair_observed=False,southeast_stair_previously_accepted=True,normal_recovery_repeated=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=31,controller_executions=31,unchanged_controller_cases_replayed=0,new_acceptance_tests=63,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# 紙保持の新南9歩・館退出Save75限定受入

`{result['status']}`。Save74の入口階20,24南から新南9歩/20,33出口で追加南1入力。ミルシティmap3/2・warp7/15,19から自動南1歩で15,20に到着し通常Save75と独立Continue。新戦闘0、紙274/flag4383保持。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。51member/36画面/63+cold13入力。新controller31/新受入63。native2/record0/旧成功再走0/ROM変更0。

## 実退出・通常保存

9入口階20,33は下向き矢印の出口field。追加南入力1回で10ミルシティ15,20南/町名banner。町に着いてからの方向入力0。全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙一個/PC/S61Eを保持。physical2056:1→0、aux4021:62→71/4022:4→3/40ac:16→0。RAM台帳は7/20,31で変化。各runtime owner未解明。

11〜15menu0→4、16確認/17上書き。18〜28保存中、27/28は部分hashが同一、29counter75/最終Flashでも文言未完、30〜32成功文言、33field。全SaveRTC一致、42checksum/7003byte1728範囲、旧Save74bank57344byte保持。

町のNPC/水面animationによりprogress33/cold0/cold1の全画面は異なる。player/館外観112x89cropは全pixel一致。全画面一致へ昇格しない。

## 次の正規イベントownerを限定照合

[次の照合条件](../{a.EVIDENCE}/next-route.json)。紙274/flag4383の消費・後続入口を保存済scriptから照合し、未読範囲だけ同一候補で読む。受取人や歩行先は未同定。館内/退出の無変更再走を避け、owner固定後の新しい区間へ進む。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save74']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37169376833');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='386d8366f85ed44bbdbea1f1ad3892f7890b4c4f','旧Stage79終端')
    state['story_save74']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save75']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[3,2],xy=[15,20],facing=1,rp=0,money=19416,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=True,paper_obtained=True,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,paper_side_reached=True,statue_visual_observed=True,unread_floor_entered=True,hole_descent_observed=False,hole_descent_previously_accepted=True,mansion_exit_observed=True,automatic_town_south_step_observed=True,southeast_stair_observed=False,southeast_stair_previously_accepted=True,inert_warp8_activation=False,trainer_victories=0,wild_victories=0,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='紙保持の新南9歩/館退出/Save75。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='紙保持の新南9歩/館退出でミルシティ15,20南へSave75。全party/HP/PP保持。次は紙の後続consumerを限定照合。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_POST_LETTER_CONSUMER_INSPECTION_FROM_SAVE75',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save75_accept.py','scripts/pr16_story_save75_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json','content/modernization/pr16_story_save62_evidence/route-plan.json','content/modernization/pr16_story_save57_preparation.json'],stop_rule_ja='Save75町15,20南だけから再開。紙274/flag4383と後続story入口を限定照合してから新native経路を決める。受取人/次目的地を推測しない。最初の新境界で通常保存。紙/PP保持、host補充なし。旧像/館内/退出は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='紙保持の新南9歩/館退出でSave75。ミルシティ15,20南、全party/HP288/PP9,10,15,2保持。次は紙の後続consumerを限定照合。'
    state['do_not_repeat'].append('Save75の63/cold13入力36画面51member/31controller/63受入を無影響再走しない。新南9歩+出口南1入力、ミルシティ15,20自動南1歩。新戦闘0、全party/Bag19416円/PC/S61E/紙274/flag4383保持。2056解除/aux2変数/40ac解除/RAM7変化owner未解明。27/28部分hash安定→29counter/最終hashも文言未完→30成功→33field。全SaveRTC/player建物crop一致、NPC/水面差あり。次は紙の後続consumer限定照合。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / 紙保持の新南9歩・館退出Save75
- Version: story-mansion-exit-save75-v1
- Status: DONE（新南9歩/館退出/保存/独立Continue限定）
- Summary: 入口階20,24南から新南9歩/20,33出口追加南1入力、ミルシティ15,20へ自動南1歩。紙274一個/flag4383・全party600byte/HP288/PP9,10,15,2/Bag19416円/PC/S61E保持。2056解除/aux4021/4022/40ac解除/RAM観測7変化はowner未解明。
- Files changed: Save75 measure/31controller/63受入/record/checkpoint/text証拠/次consumer照合条件、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。63+cold13入力36画面51member。新controller31原log継承/新受入63。record native0/compile0/旧成功再走0。
- Evidence: 27/28部分hash安定→29counter75/最終Flashも文言未完→30成功→33field。全SaveRTC/player建物112x89crop一致、NPC/水面animationは画面差あり。42checksum/7003byte1728範囲。紙の使用/引渡し・次目的地未受入。
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




