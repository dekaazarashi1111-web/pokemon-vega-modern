#!/usr/bin/env python3
"""ミルジム退出・Save91原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import ast,datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save91_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261004-GYM-EXIT-SAVE91'
OUT=ROOT/'.local/pr16-story-save91-record'

CODE={'scripts/pr16_story_save91_accept.py','scripts/pr16_story_save91_record.py','tests/test_pr16_story_save91_accept.py',a.VISUAL,'content/modernization/pr16_story_save91_exit_owner.json','content/modernization/pr16_story_save91_next_route.json','.github/workflows/pr16-story-save91-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE91_JA.md' and a.CP=='content/modernization/pr16_story_save91_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save91_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37185228993,'bdf57adffdbff7d35b78ae97c38e551fb3608e7e',111385654447,['success']*11)
    first_done=inherited.terminal(37185746332,'38c2c0f931d3c8c17e0ded5eb8192501d8857145',111387159162,['success','success','success','failure','skipped','success','success','success'])
    test_receipts=[]
    for job,pattern,count in [(111387159162,'test_pr16_story_save91_measure.',33),(a.JOB,'test_pr16_story_save91_preparation.',2)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines();lines=[v.split('Z ',1)[-1]for v in log if ' ... ok'in v and pattern in v]
        need(len(lines)==count and any('Ran '+str(count)+' tests'in v for v in log)and any(v.endswith(' OK')for v in log),'controller33/binding2の原log継承・再走0')
        test_receipts.append(dict(job=job,passed_tests=count,executed_tests=count,failed_tests=0,test_lines=lines,replayed_passed_tests=0))
    first_source='38c2c0f931d3c8c17e0ded5eb8192501d8857145'
    need(h.d.git('show',first_source+':tests/test_pr16_story_save91_measure.py')==(ROOT/'tests/test_pr16_story_save91_measure.py').read_bytes(),'元33controller source不変')
    previous=ast.parse(h.d.git('show',first_source+':scripts/pr16_story_save91_measure.py'));current=ast.parse((ROOT/'scripts/pr16_story_save91_measure.py').read_bytes())
    for name in ['direction','idle','start','scope','progress','save','menu_index','menu_index_from_digests']:
        old=next(n for n in previous.body if isinstance(n,ast.FunctionDef)and n.name==name);new=next(n for n in current.body if isinstance(n,ast.FunctionDef)and n.name==name);need(ast.dump(old)==ast.dump(new),'controller無影響 '+name)
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==43 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save90全43member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save90/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==55 and len(z.namelist())==56 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save91member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==39 and visual['reviewed_screens']==dict(progress=list(range(37)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save91画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save91画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE91_ORIGINAL=str(original),PR16_SAVE90_INPUT=str(assets/'input.srm'),PR16_SAVE91_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save91_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==63 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 63 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'63成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','failed-attempt.json','save90-record-terminal.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done);write(evidence/'pre-native-failure-terminal.json',first_done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    write(evidence/'next-route.json',a.next_route())
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save91 artifact11295979806のstory-fast.srm（131088bytes/SHA256 e61573b32ff8f319ee36fe0d4e29981a4d213ea764078bd290bf92fed622278b）だけから再開。ジム退出の新10歩/旋回2/warp1を完了、ミルシティ3/2・20,11南。町type3map-scriptが4372〜4378をclearし今回4372/4374/4378が1→0。バッジ2/leader417勝利/TM37/紙274一個/23164円、全party600byte/HP277/294/PP3,9,8,2・今回RAM保持。次は南11東3南4西4北1の新23歩で博物館入口19,25へ。最初のmap6/0到着後だけ保存。静的target14,9/自動北1歩14,8はnative未確認。2階local2への紙引渡しは別区間で未完。旧switch/leader/勝利trainer再走0、未知NPC/境界/戦闘は縮小停止。全39画面/69+cold13入力/native2/原33controller継承+新binding2/新受入63。初回LF参照hash誤差はnative前失敗/入力0を保持。21〜29部分hash、30/31最終hashでも保存中文字/counter90、32counter91空欄→33成功文言→36field。全SaveRTC一致。NPC/花animationで全pixel異なるが主人公/ジム背景9216pixel一致。physical2056clearと4021/40aa/40ac/40ad/40aeの5vars、過去Save89RAM14/Save87raw41/RAM等runtime owner未解明。紙引渡し/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達/全story未受入。がくしゅうそうち未装備/Flash未使用、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更0。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。'
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save91_accepted=True,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,required_badge_flag=2083,required_badge_present=True,paper_consumed_or_delivered=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE),evidence_bindings=h.d.bindings(paths),controller_cases=35,controller_executions=35,controller_failed_executions=0,controller_repaired_cases=0,unchanged_controller_cases_replayed=0,new_acceptance_tests=63,successful_native_processes=2,prior_failed_native_processes=0,prior_pre_native_failed_attempts=1,total_native_processes=2,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# ミルジム退出・Save91限定受入

`{result['status']}`。Save90/9,11南から新10歩・旋回2・warp1。12で退出warp6,18、13でミルシティ3/2の20,11南へ到着。直後の通常Save91/独立Continueを受入。leader417勝利・バッジ2・TM37・紙274一個・23164円を保持。紙引渡しは未実行。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。55member/39画面/69+cold13入力。初回33controller成功後、親route参照copyの末尾LF1byteをexact hashが拒否しnative0/入力0。repo原本17553byteに訂正、新binding2検査成功。原33を再走せず継承し新受入63。native2/記録native0/旧受入再走0/ROM変更0。

## 保存と差分

14〜18menu0→4、19/20確認、21〜29部分hash/保存中。30/31は最終hashでも保存中文字/counter90。32counter91/台詞空欄、33〜35成功文言、36field。全131088byteSaveRTC一致。hashやcounterだけを保存完了としない。町NPC/花animationでfield/cold全pixelは異なる。主人公とジム背景の9216pixelは全一致。

全party600byte/HP277/294/PP3,9,8,2/Bag/紙/23164円/PC/今回RAM保持。町header→type3 map-script0x08214ee8の9命令を固定ROMで照合し、4372〜4378 clearとflyflag/endを同定。今回S61E payload258:87→7/259:164→160は4372/4374/4378clearだけ。42checksum、全Save7185byte/1833範囲、旧Save90bank57344byte保持。

physical2056:1→0（入場Save76は0→1）、legacy4021:39→49・40aa:2049→0・40ac:16→0・40ad:4→0・40ae:15→80を台帳化。これらruntime ownerと過去Save89RAM14/Save87raw41/RAM/補助変数ownerは未解明。今回保持やジムreset owner同定を他のowner解決へ昇格しない。

## 次

[博物館入口の新23歩](../content/modernization/pr16_story_save91_next_route.json)。南11東3南4西4北1で町19,25入口。最初の博物館1階map6/0へ到着直後保存。静的warp14,9/自動北1歩14,8はnative未確認。博物館2階local2への紙引渡しは別区間。

{goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save90']['record_completion']=prior_done
    state['story_save91']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[3,2],xy=[20,11],facing=1,rp=0,money=23164,badge_count=2,story_vars={'4071':9,'4072':1},lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,letter_consumer_resolved=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_quantity=1,paper_flag4383=True,paper_consumed_or_delivered=False,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),static_route_plan=a.EVIDENCE+'/next-route.json',next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='新10歩/旋回2/warp1でジム退出、Save91通常保存/独立Continue。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='ジム退出の新10歩/旋回2/warp1。Save91/ミルシティ3/2・20,11南、39画面。party/HP277/PP3,9,8,2/紙/23164円/今回RAM保持。町type3で4372〜4378clear。physical2056/5varsと過去raw41/RAM/aux差分owner未解明。紙引渡し未完。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MUSEUM_ENTRY_FROM_SAVE91',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save91_accept.py','scripts/pr16_story_save91_measure.py',a.EVIDENCE+'/inspection.json',a.EVIDENCE+'/next-route.json',a.m.PREP,'content/modernization/pr16_story_save91_exit_owner.json','content/modernization/pr16_story_save91_next_route.json'],stop_rule_ja='Save91/20,11南から南11東3南4西4北1の新23歩で博物館19,25入口。最初のmap6/0到着後だけ保存。2階local2紙引渡しは別区間。旧ジム再走0、未知NPC/境界/戦闘は縮小停止。')
    state['do_not_repeat'].append('Save91の69/cold13入力39画面55member/原33controller+binding2/63受入を無影響再走しない。初回pre-native hash失敗はnative0。新10歩/旋回2/warp1。町type3でジム4372〜4378clear。30/31最終hash保存中、32counter91空欄→33成功文言→36field。全SaveRTC/party600byte/今回RAM/9216pixel保持、全pixelはNPC花animationで異なる。physical2056/5varsと過去raw41/RAM/aux差分owner未解明。次は博物館入口の新23歩。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['bp']['next_step']=goal;state['bp']['current_stop']='ジム退出からSave91/ミルシティ3/2・20,11南。新10歩/旋回2/warp1、町type3でジム4372〜4378clear。party/紙/HP277/PP3,9,8,2/今回RAM保持。次は博物館入口へ新23歩。紙引渡し未完。'
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    entry=f"""
## {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Version: PR16-STORY-SAVE91
- Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- Task: {TASK} / ミルジム退出とSave91
- Status: DONE（新退出warp/通常保存/独立Continue限定）
- Summary: 新10歩/旋回2/warp1、ミルシティ3/2・20,11南Save91。party600byte/HP277/PP3,9,8,2/Bag/紙/バッジ2/23164円/今回RAM保持。町type3の9命令が4372〜4378clear。紙引渡し未完。
- Files changed: Save91 preparation/measure/原33controller+binding2/63受入/record/checkpoint/text証拠/退出owner/次route、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。69+cold13入力39画面55member。初回run37185746332は末尾LF参照hashのpre-native失敗、native0/入力0。原33controller不変AST/原log継承+新binding2、新受入63。record native0/compile0/旧成功再走0。
- Evidence: 21〜29部分hash、30/31最終hashでも保存中字/counter90、32counter91/空欄→33成功文言→36field。全SaveRTC/party/今回RAM保持。NPC/花animationのため全pixel不一致、主人公/ジム9216pixel一致。42checksum/7185byte1833範囲。
- Discovery: 町header→type3map-script0x08214ee8/9命令の4372〜4378clear。physical2056clearと4021/40aa/40ac/40ad/40aeの5変数、過去Save89RAM/Save87raw41等runtime owner未解明。次は南11東3南4西4北1の新23歩で博物館入口。Save90記録run37185228993全11step終端を同期。
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









