#!/usr/bin/env python3
"""保存済み4入口の独立受入。native/ARM/host compileを実行しない。"""
import datetime
import io
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_connection_oracle as o
import pr16_research_connection_actions as a
import pr16_research_lifecycle_actions as d
START='b168a81f04a4804cba7c6f6ac9b954375a5fff95'
SELF='scripts/pr16_research_connection_accept.py'
WF='.github/workflows/pr16-research-connection-accept-20260927.yml'
ORACLE='scripts/pr16_research_connection_oracle.py'
TEST='tests/test_pr16_research_connection_oracle.py'
CODE={SELF,WF,ORACLE,TEST}
RECEIPT='content/modernization/pr16_research_connection_acceptance.json'
EVIDENCE='content/modernization/pr16_research_connection_acceptance'
OUT=ROOT/'.local/pr16-research-connection-accept'
PUBLIC=OUT/'public'
SPECS=((36284847516,10920635514,169242,'4cb370e24507813119ee999e0057cfde750a477d23bf16da5d8f7d4c4cd955eb',59,3847143,'ed1f8051c9e3ac80b3d4034553d80fe4d2172e8a'),(36285051878,10919907386,21980,'28ab30edeec1448f4e31f7478ffb604038e25b9e75d3ebbfbbf8db6c7ba4a0ef',14,592822,'51f4ce7eae44ebb5ed6c192bf088b3ebbf030ed1'))

def archive(number,size,digest,count,total,run_id):
    meta=d.inputs.api('actions/artifacts/'+str(number))
    o.need(meta['id']==number and not meta['expired'] and meta['size_in_bytes']==size and meta['digest']=='sha256:'+digest and meta['workflow_run']['id']==run_id,'固定artifactのAPI identity')
    raw=d.inputs.api('actions/artifacts/'+str(number)+'/zip',True)
    o.need(o.identity(raw)=={'size':size,'sha256':digest},'固定artifact ZIP bytes')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        o.need(len(z.infolist())==len(set(z.namelist()))==count and sum(v.file_size for v in z.infolist())==total,'ZIP集合/容量')
        result={}
        for info in z.infolist():
            p=PurePosixPath(info.filename)
            o.need(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename and not info.is_dir() and info.external_attr>>28!=10,'regular relative artifact member')
            result[info.filename]=z.read(info)
    return result,{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run')}

def record():
    os.chdir(ROOT);d.current();o.need(not Path(RECEIPT).exists(),'受入済み工程を再実行しない')
    PUBLIC.mkdir(parents=True)
    cp=d.read(a.CP);o.need(cp['accepted_native_cases']==[] and cp['ecology_followup']['run_id']==36285051878,'未受入checkpoint')
    o.need(d.bindings(set(cp['source_bindings']))==cp['source_bindings'],'実測source不変')
    oldproof={str(p) for p in Path(a.BASE).rglob('*') if p.is_file()}
    protected=d.bindings(a.PROTECTED|oldproof|set(cp['source_bindings'])|{'.github/workflows/pr16-research-ecology-guide-20260927.yml'})
    code=d.bindings(CODE);runs=[];zips={};metas={}
    for rid,aid,size,digest,count,total,head in SPECS:
        run=d.inputs.api('actions/runs/'+str(rid))
        o.need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==head and run['head_branch']=='codex/modernization-followup-20260908' and run['run_attempt']==1,'元実測の終端成功/HEAD')
        rows,meta=archive(aid,size,digest,count,total,rid)
        o.need(meta['workflow_run']['head_sha']==head,'artifact source HEAD')
        runs.append(d.run_summary(run));zips[rid]=rows;metas[rid]=meta
        manifest=d.read(Path(a.BASE)/str(rid)/'manifest.json')
        prefix='.local/pr16-research-connection/public/' if rid==36284847516 else ''
        for path,identity in manifest.items():
            relative=str(Path(path).relative_to(Path(a.BASE)/str(rid)))
            o.need(o.identity(Path(path).read_bytes())==identity and rows[prefix+relative]==Path(path).read_bytes(),'artifactとtracked原本の一致: '+relative)
    failed=d.inputs.api('actions/runs/36284738523')
    o.need(failed['status']=='completed' and failed['conclusion']=='failure','起動前tuple失敗を維持')
    rows,data_meta=archive(10898510128,17366330,'7d3de78d4e852583eb35551076021630c1343aa623e91fe1529d73f4cf1471ed',3,33685811,36218655601)
    seed=rows['seed.srm'];o.need(o.identity(seed)=={'size':131072,'sha256':'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'},'固定seed')
    fixture,fixture_receipt=o.photo.fixture(seed);o.need(o.identity(fixture)==o.FIXTURE,'固定zero RP fixture')
    (OUT/'fixture.srm').write_bytes(fixture)
    results={};screens={}
    for case in o.COMMANDS:
        rid=36285051878 if case=='ecology' else 36284847516
        directory=Path(a.BASE)/str(rid)
        member='' if case=='ecology' else '.local/pr16-research-connection/public/'+case+'/'
        if case!='ecology':directory/=case
        measured=d.read(directory/'measurement.json')
        o.need(measured['returncode']==0 and measured['stderr']==o.identity(b''),'元processのclean完走')
        for name,binding in measured['screens'].items():
            raw=zips[rid][member+name]
            o.need(o.identity(raw)==binding and raw.startswith(b'P6\n240 160\n255\n') and len(raw)==115215,'実画面PPMの完全一致')
            screens[case+'/'+name]=dict(artifact_id=metas[rid]['id'],member=member+name,identity=binding)
        raw=(directory/'stdout.txt').read_bytes();commands=(directory/'commands.txt').read_bytes()
        o.need(o.identity(raw)==measured['stdout'] and o.identity(commands)==measured['commands'],'実測入力/出力identity')
        results[case]=o.validate(raw,case,commands,fixture,measured['screens'])
    o.need(len(screens)==33 and sum(len(v['dialogues']) for v in results.values())==12,'レビュー対象33画面/12静的文言')
    review=dict(schema_version=1,status='PASS_REVIEWED_STATIC_WORDING_AND_PHYSICAL_MENU_SCOPED',method_ja='本会話でダウンロードした固定2artifactの全33 native PPMを拡大して視認。OCRではなく原寸情報を保つ画像表示。member/hashをActionsで再照合し、コードが画面を見たとは主張しない。',artifacts=list(metas.values()),screens=screens,reviewed_screen_count=33,reviewed_dialogue_count=12,readability_ja='受付5文言、ショップ導入とRP0/19件の初期一覧、釣り/ゲーム/生態の各説明と上限2文言を確認。対象の文字化け/説明文切れを認めない。',finding=dict(id='RESEARCH_COUNTER_NUMERIC_VIEW_MISSING',status='OPEN_IMPLEMENTATION_REQUIRED',screen='lab/counter_balance.ppm',identity=screens['lab/counter_balance.ppm']['identity'],actual_ja='ポイントを／かくにんします。という固定文だけで数値残高とrankは未表示。',expected_ja='canonical modelのSTANDARD_LISTによる残高/活動説明/rank。ショップRP0を受付数値UIの代替受入にしない。'),whole_game_visual_quality_accepted=False,natural_story_progress_accepted=False,naturally_earned_spending_accepted=False,review_scope_ja='受付/ショップの物理接続と静的文言のみ。全map/全活動/標準listの全操作/自然稼得支出/画面全体の無欠陥は主張しない。')
    d.write(PUBLIC/'visual-review.json',review)
    d.write(PUBLIC/'oracle.json',results)
    os.environ['PR16_CONNECTION_FIXTURE']=str((OUT/'fixture.srm').relative_to(ROOT))
    suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_pr16_research_connection_oracle')
    count=suite.countTestCases();o.need(count>100,'新規テスト集合をロード')
    p=subprocess.run([sys.executable,'-B','-m','unittest','tests.test_pr16_research_connection_oracle','-v'],capture_output=True,timeout=120)
    (PUBLIC/'unit.stdout.txt').write_bytes(p.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(p.stderr)
    unit=dict(returncode=p.returncode,expected_tests=count,passed_tests=p.stderr.count(b' ... ok\n'),stdout=o.identity(p.stdout),stderr=o.identity(p.stderr),module='tests.test_pr16_research_connection_oracle',test_runs=1,native_processes=0,host_compiles=0,arm_compiles=0)
    d.write(PUBLIC/'unit.json',unit)
    o.need(p.returncode==0 and unit['passed_tests']==count and not p.stdout,'新規oracle陽性/改変拒否の全件PASS')
    o.need(d.bindings(set(protected))==protected and d.bindings(CODE)==code,'原本/source不変')
    evidence={}
    for path in sorted(PUBLIC.iterdir()):
        raw=path.read_bytes();raw.decode('utf-8');o.need(b'\0' not in raw,'tracked UTF8 only')
        dest=Path(EVIDENCE)/path.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);evidence[str(dest)]=o.identity(raw)
    d.write(Path(EVIDENCE)/'manifest.json',evidence)
    receipt=dict(schema_version=1,task='USER-20260927-RESEARCH-CONNECTION',status='PASS_PHYSICAL_DOOR_AND_STATIC_GUIDE_SCOPED',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=code,protected_bindings=protected,measurement_runs=runs,previous_failure=d.run_summary(failed),artifacts=list(metas.values()),seed_artifact=data_meta,fixture=fixture_receipt,fixture_identity=o.FIXTURE,candidate=cp['candidate'],accepted_cases=list(results),oracle=EVIDENCE+'/oracle.json',visual_review=EVIDENCE+'/visual-review.json',tests=unit,evidence_manifest=EVIDENCE+'/manifest.json',native_processes=0,host_compiles=0,arm_compiles=0,accepted_case_reruns=0,rom_changes=0,release_ready=False,active_baseline_changed=False,counter_numeric_display_accepted=False,natural_story_progress_accepted=False,naturally_earned_spending_accepted=False,own_actions_completion_confirmed=False)
    d.write(RECEIPT,receipt)
    cp['measurement_status_preserved']=cp['status'];cp['status']=receipt['status'];cp['accepted_native_cases']=list(results);cp['acceptance']=dict(path=RECEIPT,status=receipt['status'],source_head=os.environ['GITHUB_SHA'],run_id=receipt['run_id'])
    cp['ecology_followup']['independent_oracle_accepted']=True;cp['ecology_followup']['terminal_run']=runs[1]
    cp['not_accepted']=['counter-numeric-balance','counter-rank-standard-list','natural-story-progress','naturally-earned-spending','all-activities','all-maps','whole-game-visual-quality']
    d.write(a.CP,cp)
    goal='物理4入口/受付静的5文言/初期ショップ開閉/釣り・ゲーム・生態の静的ガイドは原本と独立oracleで限定受入済み。次は受付の数値残高・rank/標準listを実装し変更影響だけ検証、その後自然稼得RP→ショップ支出と通常進行の接続を実測。旧稼得/今回4入口を無変更再実行しない。'
    with Path(a.GUIDE).open('a',encoding='utf-8') as f:
        f.write('\n## 独立受入確定\n\n'+goal+'\n\n受入 `'+RECEIPT+'`。新規oracle '+str(count)+'件PASS、全owner64byte/入力/fixture/画面/JSON型/虚偽scope昇格の拒否を含む。元33画面・12静的文言を視認しartifact/member/hash固定。今回native/compile/ARMは0。研究室は屋外→受付→ショップ初期19件/取消→屋外。釣り/ゲーム/生態は入口→案内→会話終了までで、屋外帰還は主張しない。\n\n旧生態未観測、旧tuple事前失敗、ローカル原本消失を保持。受付の数値残高/rankは未表示のためOPEN。屋外fixture到達をストーリー通しの自然到達へ、ショップRP0表示を自然稼得RP支出へ昇格しない。\n')
    state=d.read(d.STATE);state['research_connection'].update(status=receipt['status'],acceptance=cp['acceptance'],accepted_native_cases=list(results),ecology_followup=cp['ecology_followup'])
    state['bp']['current_stop']=receipt['status'];state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_COUNTER_NUMERIC_VIEW_AND_NATURAL_SPENDING_NEXT',goal_ja=goal,read_paths=[a.GUIDE,a.CP,RECEIPT,EVIDENCE+'/visual-review.json','content/research_economy_v1/canonical_model.json','overlays/research_economy_v1/research_economy_v1.c'],stop_rule_ja='静的入口4件と旧稼得nativeは無変更再実行しない。数値表示・rank・自然RP支出は別受入。受入原本/基準不変、merge/release禁止。')
    state['do_not_repeat'].insert(0,'研究接続4入口は'+RECEIPT+'で限定受入済み。原本/33画面/独立oracleを再利用し、未表示の受付数値/rankと自然RP支出の変更影響だけ実測。全活動/通常ストーリーへ昇格禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='保存済み実測4入口の独立受入code HEAD。元実測2run終端success確認済み。自己記録runと一般CIは別管理。'
    observed=d.inputs.api('actions/runs?head_sha='+os.environ['GITHUB_SHA']+'&per_page=50')
    o.need(observed['total_count']<=50,'現在HEAD Actions完全性')
    head_runs=[d.run_summary(r) for r in observed['workflow_runs']]
    state['observed_head_checks']={'scope_head':os.environ['GITHUB_SHA'],'runs':head_runs,'measurement_runs':runs,'reason_ja':'元2run成功・保存原本の独立oracleと33画面限定受入。旧失敗は不変。自己記録run終端や全CI/全体private guard成功はまだ主張しない。'}
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in head_runs if r['status'] in ('queued','in_progress')]
    for path in CODE|{RECEIPT,a.CP,a.GUIDE}:state['source_bindings'][path]=o.identity(Path(path).read_bytes())
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {now}\n- Timestamp: {now}\n- Task: USER-20260927-RESEARCH-CONNECTION / 4物理入口と静的案内の独立受入\n- Version: research-connection-accepted-v1\n- Status: DONE（物理入口と静的案内の限定範囲）\n- Summary: 研究室の屋外→受付→初期ショップ/取消→屋外、釣り/ゲーム/生態の入口→案内→終了を受入。受付の数値残高/rank/標準list、自然稼得RP支出、通常ストーリー到達は未完として次へ。旧失敗・生態未観測・消失原本は保持。\n- Files changed: 独立oracle/改変拒否test/記録script/workflow、受入/画面レビュー/検査原本、checkpoint/guide、固定引継ぎMD/JSON、両ログ。\n- Verify: 新規oracle {count}件PASS、33実画面/12静的文言の視認と固定artifact照合、2048byte ledger独立再計算。新native/host compile/ARM/ROM変更/受入済み再実行0。元Actions36284847516/36285051878 success、現在HEAD一般CIは別記。resume/task graph/最終index scoped guard。全体guard成功は主張しない。\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branchへの非force記録、自己SHAはgit log。\n- Network: GitHub固定artifact/PR/Actionsのみ。merge/release/baseline変更なし。\n'
    for path in d.LOGS:
        with Path(path).open('a',encoding='utf-8') as f:f.write(log)
    owned=set(evidence)|{EVIDENCE+'/manifest.json',RECEIPT,a.CP,a.GUIDE,d.STATE,d.DOC}|d.LOGS
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_resume,pr16_learnset_runtime_record as g
    pr16_resume.validate(ROOT);g.START=START;g.CODE=CODE;g.OWNED=owned;g.guard()
    o.need(d.bindings(set(protected))==protected,'最終原本不変')
    subprocess.run(['git','diff','--cached','--check'],check=True)
    print('PASS_SCOPED_CONNECTION_ACCEPTANCE tests='+str(count)+' native=0 compile=0',flush=True)

if __name__=='__main__':record()
