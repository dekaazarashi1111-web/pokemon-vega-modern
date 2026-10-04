#!/usr/bin/env python3
"""第9ディグダ配置変更・Save88原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save88_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-GYM-NINTH-DIGLETT-SAVE88'
OUT=ROOT/'.local/pr16-story-save88-record'

CODE={'scripts/pr16_story_save88_accept.py','scripts/pr16_story_save88_record.py','tests/test_pr16_story_save88_accept.py',a.VISUAL,'content/modernization/pr16_story_save88_next_route.json','.github/workflows/pr16-story-save88-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE88_JA.md' and a.CP=='content/modernization/pr16_story_save88_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save88_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37182197160,'c55ce7d2fd862ef185dfb8ef5b91512e3b03c6f7',111376842542,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save88_measure.' in v]
    need(len(lines)==33 and any('Ran 33 tests'in v for v in log)and any(v.endswith(' OK')for v in log),'新controller33の原logを継承・再走しない')
    test_receipts=[dict(job=a.JOB,passed_tests=33,executed_tests=33,failed_tests=0,test_lines=lines,replayed_passed_tests=0)]
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==127 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save87全127member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save87/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==60 and len(z.namelist())==61 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save88member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==45 and visual['reviewed_screens']==dict(progress=list(range(43)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save88画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save88画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE88_ORIGINAL=str(original),PR16_SAVE87_INPUT=str(assets/'input.srm'),PR16_SAVE88_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save88_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==62 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 62 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'62成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save87-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save88 artifact11295552942のstory-fast.srm（131088bytes/SHA256 a99af1391ac7bd9a05cffa8487d868aff2c6e31a48aea2a27c1c2a90ebeb1b0c）だけから再開。ミルジム10/16・6,7南、退出用第9local10の4373truebranch完了。4373/4377clear・4376set、local10除去/local6/11復帰。バッジ2/leader417勝利/紙274一個/TM37/23164円、HP277/294・PP3,9,8,2を保持。次は南2/西3/南2/東6の新13歩で9,11、南旋回してlocal8/9,12へ通常A。未入力4376truebranchで4375set/4376clear、local9除去/local10復帰の退出用第10switch。最初の新event後保存。次の第11local8とジム退出/博物館2階local2への紙引渡しは未完、旧switch/leader/勝利trainerは再走しない。未知NPC/境界は縮小停止。全45画面/82+cold13入力/native2/新controller33/新受入62、旧受入再走0。37最終Flashhashでもcounter87→38counter88/一時別hash/保存中→39最終hash/成功文言→42field、cold全pixel/全SaveRTC一致。今回全party600byte/RAM保持。補助4021/4022、旧Save87のraw41系列/RAM4段階/補助varsと過去差分runtime owner未解明。紙引渡し/退出/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達/全story未受入。がくしゅうそうち未装備/Flash未使用、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更0。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save88_accepted=True,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=False,required_badge_flag=2083,required_badge_present=True,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=33,controller_executions=33,controller_failed_executions=0,controller_repaired_cases=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=62,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# ミルジム退出用第9ディグダ・Save88限定受入

`{result['status']}`。Save87の7,3西から東4/南4/西5の新13歩、4旋回で6,7南。local10の未入力4373truebranchを通常Aで実行し、4373/4377clear・4376set、local10除去/local6/11復帰。通常Save88/独立Continue。leader417勝利・バッジ2・TM37・紙・23164円を保持。ジム退出と紙引渡しは未入力。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。60member/45画面/82+cold13入力。新controller33/新受入62、native2/記録native0/旧受入再走0/ROM変更0。

## 保存と差分

0〜16移動/旋回、17南旋回、18撫でた台詞、19配置変更文言、20field。21〜25menu0→4、26/27確認、28〜38保存中。37は最終Flashhashでもcounter87。38でcounter88へ変化するが、一時別hashかつ保存中。39〜41は最終hash/成功文言、42field/cold0/1の全pixel一致。全131088byteSaveRTC一致。

全party600byte/HP277/294/PP3,9,8,2と今回RAM台帳を保持。全Bag/紙274一個/23164円/PC/legacy flags/通常story変数を保持。S61E差分258:39→7・259:166→165は4373/4377clear・4376setだけ。補助vars4021:13→26、4022:0→3のruntime ownerは未解明。40AC=16/バッジ2保持。42checksum、全Save7192byte/1843範囲、旧Save87bank57344byte保持。

過去Save87のraw41系列4byte・RAM4段階・補助6vars、Save85などの過去差分runtime ownerは解決扱いしない。第9switchは新stateでの相互作用であり、既受入の旧3branchを再生したものではない。

## 次

[退出用local8新分岐](../content/modernization/pr16_story_save88_next_route.json)。南2/西3/南2/東6の新13歩で9,11、南へ通常A。4376trueの第10switchは未入力。静的39命令6nodeから4375set・4376clear、local9除去/local10復帰を予測。最初の新event後保存。次の第11local8と退出/博物館封書引渡しは未受入。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save87']['record_completion']=prior_done
    state['story_save88']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[10,16],xy=[6,7],facing=1,rp=0,money=23164,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='退出用第9switchを新13歩から入力、Save88通常保存/独立Continue。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='退出用第9local10の未入力4373truebranch。Save88/6,7南、13歩4旋回・45画面、バッジ2/HP277/PP3,9,8,2/紙/23164円と全party/RAM保持。退出/紙引渡しは次。aux4021/4022と過去差分owner未解明。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_GYM_EXIT_TENTH_DIGLETT_FROM_SAVE88',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save88_accept.py','scripts/pr16_story_save88_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,'content/modernization/pr16_story_save88_next_route.json'],stop_rule_ja='Save88/6,7南から南2/西3/南2/東6で9,11、南旋回してlocal8/9,12へ通常A。退出用の未入力4376true分岐だけ、最初の新event後保存。旧switch/leader/勝利trainer再走0、未知NPC/境界は縮小停止。')
    state['do_not_repeat'].append('Save88の82/cold13入力45画面60member/33controller/62受入を無影響再走しない。退出用第9local10で4373/4377clear・4376set。37最終hash/counter87→38counter88/一時別hash/保存中→39成功文言→42field。全SaveRTC/全pixel/party600byte/今回RAM保持。aux4021/4022と旧Save87/raw41系列/RAM/過去差分owner未解明。次は退出用local8の未入力4376true分岐。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='退出用第9switchからSave88/6,7南。13歩4旋回、全party/RAM/紙/HP277/PP3,9,8,2保持。次はlocal8新分岐。退出/紙引渡し未完。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    entry=f"""
## {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Version: PR16-STORY-SAVE88
- Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Task: {TASK} / ミルジム退出用第9switchとSave88
- Status: DONE（第9配置変更/通常保存/独立Continue限定）
- Summary: 東4/南4/西5の新13歩4旋回、local10の4373truebranchへ通常A。4373/4377clear・4376set、local10除去/local6/11復帰。6,7南Save88、全party600byte/HP277/PP3,9,8,2/RAM/Bag/23164円/紙/バッジ2を保持。
- Files changed: Save88 preparation/measure/33controller/62受入/record/checkpoint/text証拠/第10switch次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。82+cold13入力45画面60member。新controller33原log継承/新受入62。record native0/compile0/旧成功再走0。
- Evidence: 37最終Flashhash/counter87→38counter88/一時別hash/保存中→39最終hash/成功文言→42field。全SaveRTC/field全pixel/party/RAM保持。42checksum/7192byte1843範囲。補助4021/4022と過去raw41系列/RAM/aux差分runtime owner未解明。退出/紙引渡し未受入。
- Discovery: 次の新stateはlocal8/9,12の4376truebranch、静的39命令6node。南2/西3/南2/東6の新13歩で9,11へ。Save87記録run37182197160全11step終端を同期。
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







