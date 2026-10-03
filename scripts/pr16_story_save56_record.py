#!/usr/bin/env python3
"""館の入口から新廊下のSave56原本を受入し、固定再開正本へ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save56_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
h=a.m.h;BASE=a.SOURCE;TASK='USER-20261003-MANSION-SAVE56'
OUT=ROOT/'.local/pr16-story-save56-record'

CODE={'scripts/pr16_story_save56_accept.py','scripts/pr16_story_save56_record.py','tests/test_pr16_story_save56_accept.py',a.VISUAL,'.github/workflows/pr16-story-save56-record.yml'}
def record():
    os.chdir(ROOT);h.d.current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/a.CP).exists(),'新規記録1回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    need(a.GUIDE=='docs/PR16_STORY_SAVE56_JA.md' and a.CP=='content/modernization/pr16_story_save56_checkpoint.json' and a.EVIDENCE=='content/modernization/pr16_story_save56_evidence','今回専用宛先')
    need({a.GUIDE,a.CP}.isdisjoint(protected) and not any(p.startswith(a.EVIDENCE+'/')for p in protected),'旧受入へ書かない')
    OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    for name in a.m.CODE:need(h.d.git('show',a.SOURCE+':'+name)==(ROOT/name).read_bytes(),'測定source不変 '+name)
    done=inherited.terminal(a.RUN,a.SOURCE,a.JOB,['success']*8)
    prior_done=inherited.terminal(37152018112,'3238addb62097be451dbc10e653dba5946070312',111287669292,['success']*11)
    test_receipts=[]
    for job,suite,count in [(111289893097,'test_pr16_story_save56_measure.',22),(a.JOB,'test_pr16_story_save56_measure.',3)]:
        log=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        lines=[v.split('Z ',1)[-1]for v in log if ' ... ok' in v and suite in v]
        need(len(lines)==count and any(f'Ran {count} tests in 'in v for v in log)and any(v.endswith(' OK')for v in log),'controller原log継承')
        test_receipts.append(dict(job=job,passed_tests=count,test_lines=lines,replayed_tests=0))
    _,z=a.transport.archive(a.m.a.ARTIFACT,a.m.a.RUN,a.m.a.ARCHIVE,a.m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==154 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save55全154member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'親member '+n)
        before=z.read('story-fast.srm')
    old=a.m.m.a
    _,z=a.transport.archive(old.ARTIFACT,old.RUN,old.ARCHIVE,old.SOURCE)
    with z:rom=z.read('candidate.gba')
    need(identity(before)==a.m.a.OUTPUT and identity(rom)==a.shared.plan.CANDIDATE,'正式Save55/同一ROM')
    meta,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE);original=OUT/'original';original.mkdir()
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==57 and len(z.namelist())==58 and set(z.namelist())==set(manifest)|{'manifest.json'},'全Save56member')
        need(all(Path(n).suffix in {'.srm','.ppm','.txt','.json'} and not n.startswith('/') and '..'not in n.split('/')for n in z.namelist()),'新save/画面/textだけ')
        need(not any(n.endswith('.gba')or n=='runner'or n.startswith(('runtime/','private-inputs/'))for n in z.namelist()),'既存ROM/runtime非再配布')
        for n,b in manifest.items():need(identity(z.read(n))==b,'新member全byte '+n)
        z.extractall(original)
    visual=h.d.read(ROOT/a.VISUAL)
    need(visual['run_id']==a.RUN and visual['measurement_source']==a.SOURCE and visual['total_screens_reviewed']==41 and visual['reviewed_screens']==dict(progress=list(range(39)),**{'continue':[0,1]}) and visual['save_success_wording_observed']is True,'全Save56画面目視')
    need(set(visual['screen_anchors'])=={n for n in manifest if n.endswith('.ppm')},'全Save56画面anchor')
    for n,digest in visual['screen_anchors'].items():need(identity((original/n).read_bytes())['sha256']==digest,'目視原本 '+n)
    result=a.verify(original,before,rom)
    assets=OUT/'private-inputs';assets.mkdir();(assets/'input.srm').write_bytes(before);(assets/'candidate.gba').write_bytes(rom)
    env=dict(os.environ,PR16_SAVE56_ORIGINAL=str(original),PR16_SAVE55_INPUT=str(assets/'input.srm'),PR16_SAVE56_ROM=str(assets/'candidate.gba'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_save56_accept.py','-v'],capture_output=True,timeout=120,env=env)
    unit_stdout,unit_stderr=unit.stdout,unit.stderr
    (receipts/'unit.stdout.txt').write_bytes(unit_stdout);(receipts/'unit.stderr.txt').write_bytes(unit_stderr)
    test_lines=[line for line in unit_stderr.decode().splitlines()if line.startswith('test_')]
    need(unit.returncode==0 and not unit_stdout and len(test_lines)==46 and all(line.endswith(' ... ok')for line in test_lines)and re.search(rb'\nRan 46 tests in [0-9.]+s\n\nOK\n\Z',unit_stderr),'46成功行と正確なunittest終端')
    evidence=ROOT/a.EVIDENCE;evidence.mkdir()
    for name in ['measurement.json','manifest.json','save55-record-terminal.json','prior-entry-failure.json','inspection.json','progress/commands.txt','progress/stdout.txt','progress/stderr.txt','progress/execution.json','continue/commands.txt','continue/stdout.txt','continue/stderr.txt','continue/execution.json']:
        raw=(original/name).read_bytes();raw.decode();need(b'\0'not in raw,'tracked textだけ')
        dest=evidence/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    (evidence/'unit.stderr.txt').write_bytes(unit_stderr)
    write(evidence/'verification.json',result);write(evidence/'terminal.json',done)
    write(evidence/'controller-test-receipt.json',test_receipts)
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()}
    goal='Save56 artifact11284293358のstory-fast.srm（131088bytes/SHA256 cf11b02c2152e238bf0f56fd2dadc3b30038ea6c45b105ca616ad4dc2ce93386）だけから再開。map1/59・20,25北、こころのやかた入口階の未読階層手前。通常入館2歩/warpと館内8歩/戦闘0/Save56/独立Continueを限定受入。party600byteとHP288/294・PP[15,10,15,14]、ミュウツー全HP/PP、Bag/17904円/RP0/badge1/story4071=9/4072=1保持。次は北20,24の既読warp8→map1/60・warp5。未読map1/60と必要owner/最小地形を限定調査し、NPC依頼「奥のどうぞうの裏の紙」を目標に最初の新event/戦闘/未通過境界まで通常入力で進める。紙は未調査、Flash未使用/未習得、がくしゅうそうち未装備。2056flagのruntime ownerとaux4021/4022/404d未解明、2221は館map3 script setworldmapflag照合。過去RAM台帳/仲間offset41/40ac=16のowner未解明も保持。Save56のRAM台帳は全観測/cold77ccaa1d7ceee4a641d1094ab5b8f5caf44668ea125287542f3e2bed65a80e57。32/33最終似hashでも旧counter55/保存中→34counter56でhash再変化→35成功→38fieldを区別。70+cold13入力41画面57member/46新受入を無影響再走しない。初回20,32推測は実20,33で未保存停止した21入力6画面/native1を原本保持し、3影響試験だけ訂正。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CIの既知不一致とaction_requiredを全成功にしない。'
    extra={'scripts/pr16_story_save56_inspect.py','.github/workflows/pr16-story-save56-inspect.yml'}
    terminal=inherited.terminal(37152496844,'90d1ea03a0b5c244aaa871f8b71d574239966256',111289069800,['success']*8)
    _,z=a.transport.archive(11284517014,37152496844,dict(size=13556,sha256='57795ef62eb5de09f19d06a7f48a0386655774683268b3db17af4678b14abdd8'),'90d1ea03a0b5c244aaa871f8b71d574239966256')
    with z:need(z.namelist()==['inspection.json']and z.read('inspection.json')==(ROOT/a.m.PREP).read_bytes(),'17node/1330cell静的原本全byte')
    name=a.EVIDENCE+'/inspection-terminal.json';write(ROOT/name,terminal);paths.add(name)
    failed=json.loads((original/'prior-entry-failure.json').read_bytes());need(failed['terminal']['run']['conclusion']=='failure','失敗を成功へ改作しない')
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=a.SOURCE,run_id=a.RUN,job_id=a.JOB,artifact={k:meta[k]for k in('id','name','size_in_bytes','digest','workflow_run','expires_at')},verification=result,record_source=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),save56_accepted=True,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,normal_recovery_repeated=False,double_target_separation_native_exercised=False,visual_review=a.VISUAL,source_bindings=h.d.bindings(CODE|a.m.CODE|extra),evidence_bindings=h.d.bindings(paths),controller_cases=23,controller_executions=25,unchanged_controller_cases_replayed=0,new_acceptance_tests=46,successful_native_processes=2,prior_failed_native_processes=1,total_native_processes=3,prior_failure=failed,record_native_processes=0,next_goal_ja=goal,release_ready=False,active_baseline_changed=False,general_ci_all_success_claimed=False)
    write(ROOT/a.CP,cp)
    guide=f"""# こころのやかた通常入館・新廊下・Save56限定受入

`{result['status']}`。Save55の16,20南から通常西1歩/北doorへ1歩、暗い館map1/59の20,33へ入館。通常北8歩で20,25北。次階層warp20,24へ踏み込まずSave56と独立Continueを受入。戦闘/会話/新item/Flash0、像の裏の紙は未調査。

source `{a.SOURCE}` / run `{a.RUN}` / job `{a.JOB}`全8step成功。artifact `{a.ARTIFACT}` / {a.ARCHIVE['size']}bytes / SHA256 `{a.ARCHIVE['sha256']}`。57member/41画面/70+cold13入力。controller23case（初回22、影響2+新規1の計25実行。未影響20件は原log継承）、46新受入拒否試験。成功native2/失敗native1/record0/旧受入再走0/ROM変更0。

## 実測入口での訂正

初回run37152779196/source5bad5bee97dc0059e901984c7f35d936e65c0351/job111289893097/artifact11285040773は、warp後に1歩自動で進むという推測20,32をguardが拒否。実際は20,33出口arrowの上でfield復帰。21入力/6画面/native1、Save55全byte不変、未保存。原本を改作せずartifact全13memberと終了receiptを照合し、実観測から1tileだけ訂正。受入済み回復・レンジャー区間は再生していない。

## 画面と保存

0〜3town/向き、4warp transition、5入館、6〜13新廊下。14〜18menu0→4、19確認/20上書き、21〜34保存中。32/33は最終Flash hashと同じでもcounter55かつ保存中、34はcounter56でも一度別hash。35〜37成功文言、38field。hash一致やcounterだけで完了としない。cold0/1は120frame後も全SaveRTC・暗所の人物/可視範囲を含む画面byteがprogress38と一致。

## 限定差分

party600byte/HP/PP/全Bag/17904円/RP0を保持。legacy2056と2221だけ新set。2221は館map-script3のsetworldmapflag（142978050）と照合。2056runtime ownerは未解明。4021=16→25/4022=0→4/404d=21→44のownerも未解明。story4071=9/4072=1、40ac=16、badge1/全国図鑑未解禁。PC/S61E全payloadと旧Save55bank57344byte保持、42checksum/6874byte1708範囲。

未読17node/1330cell/1mapの静的採取はnative到達と分離。任意TM21民家へ入らず、がくしゅうそうちを装備せず、回復せず。紙が入口階の既読会話/背景eventにないことだけを確認し、次は隣接階の必要箇所へ。

次: {goal}
"""
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8');need(h.d.bindings(protected)==protected,'旧正本/入力不変')
    state['story_save55']['record_completion']=prior_done
    stage=h.d.inputs.api('actions/runs/37152018257');need(stage['status']=='completed'and stage['conclusion']=='success'and stage['head_sha']=='3238addb62097be451dbc10e653dba5946070312','旧Stage79終端')
    state['story_save55']['stage79_completion']={k:stage[k]for k in('id','head_sha','status','conclusion','html_url')}
    state['story_save56']=dict(status=result['status'],checkpoint=a.CP,guide=a.GUIDE,run_id=a.RUN,job_id=a.JOB,artifact_id=a.ARTIFACT,story_fast_save=a.OUTPUT,verification=result,map=[1,59],xy=[20,25],facing=2,rp=0,money=17904,badge_count=1,story_vars={'4071':9,'4072':1},lead_hp=[288,294],lead_pp=[15,10,15,14],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_required=False,pp_recovery_accepted=True,exp_share_equipped_or_growth_accepted=False,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,trainer_victories=0,wild_victories=0,record_native_processes=0,record_run_id=int(os.environ['GITHUB_RUN_ID']),prior_failed_entry=failed,next_goal_ja=goal)
    state['observed_head_history'].append(dict(head=state['observed_head'],semantics=state['observed_head_semantics'],checks=state['observed_head_checks'],reason_ja='通常入館と新廊下8歩/未読階層手前Save56。'))
    state['observed_head']=a.SOURCE;state['observed_head_semantics']='こころのやかた入館/新廊下Save56。次は未読階層から像の裏の紙へ。';h.observe_checks(state,a.SOURCE)
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')];state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['next_action'].update(id='STORY_MANSION_INNER_FLOOR_FROM_SAVE56',goal_ja=goal,read_paths=[a.GUIDE,a.CP,a.VISUAL,'scripts/pr16_story_save56_accept.py','scripts/pr16_story_save56_measure.py',a.EVIDENCE+'/inspection.json','content/modernization/pr16_story_save56_preparation.json'],stop_rule_ja='Save56だけから、北20,24warp→未読map1/60・warp5の必要ownerを限定調査して通常進行。紙未調査を完了扱いしない。最初の新event/戦闘/未通過境界で保存し、既受入区間は再走しない。')
    state['bp']['next_step']=goal;state['bp']['current_stop']='こころのやかたへ通常入館、新廊下8歩でSave56。map1/59・20,25北。次は未読階層から像の裏の紙へ。'
    state['do_not_repeat'].append('Save56の70/cold13入力41画面57member/46受入を無影響再走しない。入館初回20,32推測は実20,33で停止21入力6画面、影響3試験だけ訂正。32/33最終似hashでも34再変化→35成功→38field。2056/aux3varと過去RAM/offset41のowner未解明。')
    owned={a.CP,a.GUIDE,h.d.STATE,h.d.DOC,*h.d.LOGS}|paths
    state['source_bindings'].update(h.d.bindings((owned|CODE|a.m.CODE|extra)-{h.d.STATE,h.d.DOC,*h.d.LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry=f"""
## {stamp}
- Timestamp: {stamp}
- Task: {TASK} / こころのやかた新廊下とSave56
- Version: story-heart-mansion-entry-save56-v1
- Status: DONE（通常入館/新廊下/保存/独立Continue限定）
- Summary: Save55からtown2歩/warpと新廊下8歩。20,25北、次warp20,24の未読階層手前。戦闘0/紙未調査/Flash0。party/HP/PP/Bag/17904円/RP0を保持。
- Files changed: Save56 inspect/measure/23controller/46受入/record、17node1330cell静的原本、checkpoint/text証拠、固定再開MD/JSON、両ログ。
- Verify: run{a.RUN}/job{a.JOB}全8step成功。70+cold13入力41画面57member。controller22原log+影響3件、46新受入拒否試験。record native0/compile0/既受入再走0。
- Prior failure: run37152779196/job111289893097の21入力6画面/native1は入口20,32推測をguardが拒否、実20,33で未保存停止。原本artifact11285040773と全Save55不変を保持。
- Evidence: party600byte/PC/S61E保持、2221map-script owner照合、2056/aux3var owner未解明。32/33最終似hashでも34再変化→35成功→38field。旧bank57344byte、42checksum/6874byte1708範囲/cold全SaveRTC・全fieldframe一致。
- Commit: 測定source={a.SOURCE}、記録source={os.environ['GITHUB_SHA']}・run={os.environ['GITHUB_RUN_ID']}。scoped guard/task graph/resume後に同branch非force pushと全text読戻し。
- Network: 同repo GitHub/Actionsのみ。既存ROM/runtime/input非再配布。一般CIの既知不一致/action_requiredは全成功にしない。merge/release/baseline変更0。
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

