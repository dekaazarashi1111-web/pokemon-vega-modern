#!/usr/bin/env python3
"""第11ディグダ配置変更・Save90原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save90_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-GYM-ELEVENTH-DIGLETT-SAVE90'
OUT=ROOT/'.local/pr16-story-save90-record'

CODE={'scripts/pr16_story_save90_accept.py','scripts/pr16_story_save90_record.py','tests/test_pr16_story_save90_accept.py',a.VISUAL,'content/modernization/pr16_story_save90_next_route.json','.github/workflows/pr16-story-save90-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE90_JA.md' and a.CP=='content/modernization/pr16_story_save90_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save90_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37184239129,'b58101da60846f3cb56b896dd3a744fdb5857845',111382754941,['success']*11)
    log=h.d.inputs.api('actions/jobs/'+str(a.JOB)+'/logs',True).decode().splitlines()
    lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and 'test_pr16_story_save90_measure.' in v]
    need(len(lines)==31 and any('Ran 31 tests'in v for v in log)and any(v.endswith(' OK')for v in log),'新controller31の原logを継承・再走しない')
    test_receipts=[dict(job=a.JOB,passed_tests=31,executed_tests=31,failed_tests=0,test_lines=lines,replayed_passed_tests=0)]
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==60 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save89全60member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save89/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==43 and len(z.namelist())==44 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save90member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==28 and visual['reviewed_screens']==dict(progress=list(range(26)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save90画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save90画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE90_ORIGINAL=str(original),PR16_SAVE89_INPUT=str(assets/'input.srm'),PR16_SAVE90_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save90_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==62 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 62 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'62成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save89-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save90 artifact11296466834のstory-fast.srm（131088bytes/SHA256 5ac6f0f42f6f0cb43e984e34eb6fe5d17667abb29a3b465934e03cd708f20d47）だけから再開。ミルジム10/16・9,11南、退出用第11local8の4375truebranch完了。4372/4374set・4375clear、local5/8除去/local9復帰。移動/旋回0。バッジ2/leader417勝利/紙274一個/TM37/23164円、全party600byte/HP277/294/PP3,9,8,2・今回RAM/legacy vars保持。次は南2西3南5の新10歩で6,18退出warpへ。local8/5へ再対話せず最初の外map3/2へ出た直後だけ保存。静的到着warp20,10/南出口20,11はnative未確認。ジム退出/博物館2階local2への紙引渡し未完。旧switch/leader/勝利trainer再走0、未知NPC/境界/戦闘は縮小停止。全28画面/48+cold13入力/native2/新controller31/新受入62、旧受入再走0。11〜19部分hash、20最終hashでも保存中文字/counter89、21counter90/空欄、22成功文言、25field/cold全pixel/全SaveRTC一致。今回RAMは保持、過去Save89RAM14/補助4021/4022、Save87raw41系列/RAM4段階/補助vars等のruntime owner未解明。紙引渡し/退出/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達/全story未受入。がくしゅうそうち未装備/Flash未使用、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更0。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save90_accepted=True,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=False,required_badge_flag=2083,required_badge_present=True,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=31,controller_executions=31,controller_failed_executions=0,controller_repaired_cases=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=62,successful_native_processes=2,prior_failed_native_processes=0,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# ミルジム退出用第11ディグダ・Save90限定受入

`{result['status']}`。Save89/9,11南から移動/旋回0、local8の未入力4375truebranchへ通常A。4372/4374set・4375clear、local5/8除去/local9復帰。通常Save90/独立Continue。leader417勝利・バッジ2・TM37・紙・23164円を保持。退出側は開いたが、ジム外へ出る入力と紙引渡しは未実行。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。43member/28画面/48+cold13入力。新controller31/新受入62、native2/記録native0/旧受入再走0/ROM変更0。

## 保存と差分

0field、1撫でた台詞、2配置変更文言、3field。4〜8menu0→4、9/10確認、11〜19部分hash/保存中。20は最終hashでも保存中文字/counter89。21counter90/台詞空欄、22〜24成功文言、25field/cold0/1全pixel一致。全131088byteSaveRTC一致。hashやcounterだけを保存完了としない。

全party600byte/HP277/294/PP3,9,8,2/Bag/紙274一個/23164円/PC/legacy flags/全legacy変数保持。S61E差分258:135→87は4372/4374set・4375clearだけ。今回RAMはprogress/cold全て25e14aa8を保持。42checksum、全Save7194byte/1844範囲、旧Save89bank57344byte保持。

過去Save89RAM14とaux4021/4022、Save87raw41系列4byte/RAM4段階/補助6varsなどのruntime ownerは未解明のまま。今回保持を過去owner解決へ昇格しない。親route参照はrepo原本のexact byte identityで照合。

## 次

[ジム退出の新10歩](../content/modernization/pr16_story_save90_next_route.json)。南2西3南5で6,18退出warp。local8/5除去済みで再対話しない。静的targetは町3/2のwarp2/20,10、南出口step20,11はnative未確認。最初の外mapへ出た直後保存。博物館2階local2への紙引渡しは別区間。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save89']['record_completion']=prior_done
    state['story_save90']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[10,16],xy=[9,11],facing=1,rp=0,money=23164,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=False,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='退出用第11switchを移動0で入力、Save90通常保存/独立Continue。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='退出用第11local8の4375truebranchを移動0で入力。Save90/9,11南、28画面、local5/8除去/local9復帰。party/HP277/PP3,9,8,2/紙/23164円/今回RAM保持。過去raw41/RAM/aux差分owner未解明。退出/紙引渡し未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_GYM_EXIT_FROM_SAVE90',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save90_accept.py','scripts/pr16_story_save90_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,'content/modernization/pr16_story_save90_next_route.json'],stop_rule_ja='Save90/9,11南から南2西3南5で6,18退出warpへ。最初の外map3/2へ出た後だけ保存。除去済local8/5や旧leader/trainer再走0、未知NPC/境界/戦闘は縮小停止。')
    state['do_not_repeat'].append('Save90の48/cold13入力28画面43member/31controller/62受入を無影響再走しない。第11local8で4372/4374set・4375clear。11〜19部分hash、20最終hashでも保存中/counter89、21counter90空欄→22成功文言→25field。全SaveRTC/全pixel/party600byte/今回RAM/全legacy変数保持。過去Save89RAM14やraw41/aux差分owner未解明。次はジム退出の新10歩。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='第11switchからSave90/9,11南。移動0、local5/8除去で退出側が開いた。party/紙/HP277/PP3,9,8,2/今回RAM保持。次は退出warpまで新10歩。退出/紙引渡し未完。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    entry=f"""
## {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Version: PR16-STORY-SAVE90
- Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Task: {TASK} / ミルジム退出用第11switchとSave90
- Status: DONE（第11配置変更/通常保存/独立Continue限定）
- Summary: 移動/旋回0、local8の4375truebranchへ通常A。4372/4374set・4375clear、local5/8除去/local9復帰。9,11南Save90、party600byte/HP277/PP3,9,8,2/Bag/紙/バッジ2/23164円/今回RAM保持。
- Files changed: Save90 preparation/measure/31controller/62受入/record/checkpoint/text証拠/退出次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。48+cold13入力28画面43member。新controller31原log継承/新受入62。record native0/compile0/旧成功再走0。
- Evidence: 11〜19部分hash、20最終hashでも保存中字/counter89、21counter90/空欄→22成功文言→25field。全SaveRTC/field全pixel/party保持。今回RAM/legacy vars保持。42checksum/7194byte1844範囲。過去Save89RAM14/aux4021/4022やSave87raw41/RAM他のruntime owner未解明。
- Discovery: 次は南2西3南5の新10歩から6,18退出warp→町3/2。静的28byte範囲bindingで道とwarpを固定。Save89記録run37184239129全11step終端を同期。退出/紙引渡し未受入。
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








