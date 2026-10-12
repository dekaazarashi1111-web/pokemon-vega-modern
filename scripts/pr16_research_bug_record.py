#!/usr/bin/env python3
"""虫取りActions原本を一度だけ受入記録する。native/compileの再実行はしない。"""
from __future__ import annotations
import datetime
import io
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_bug as b
import pr16_research_lifecycle_actions as d
from pr16_learnset_compact_record import publish_resume
need,identity=b.need,b.identity
TASK='USER-20260927-RESEARCH-ACTIVITIES'
START='60afcc675a8230eec6299910f76bd69c95dc9357'
HEAD='5412cee1d3cbde3d818a17fa6bf53d1096fc6c2c'
RUN=36261672837
ARTIFACT=10912851229
ZIP={'size':61494,'sha256':'dc637a82e536a2c3f8453b5e74c806f36e7d75e14dc05e863c7609729bdd0846'}
WF='.github/workflows/pr16-research-activities-20260927.yml'
SELF='scripts/pr16_research_bug_record.py'
MODEL='scripts/pr16_research_bug.py'
TEST='tests/test_pr16_research_bug.py'
CAPTURE='scripts/pr16_research_bug_capture.py'
RAW='content/modernization/pr16_research_bug_measurement.json'
CP='content/modernization/pr16_research_bug_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_BUG_JA.md'
BASE='content/modernization/pr16_research_bug_evidence/36261672837'
UNIT=BASE+'/unit.json'
OWN={WF,SELF,CAPTURE,MODEL,TEST}
OUT=Path('.local/pr16-research-bug-record')
PUBLIC=OUT/'public'
GOAL='次は残る4活動（釣り・生態・ゲームコーナー・採掘）の実RP稼得、通常進行からResearch受付/ショップ接続、残るnative文言。保存view修復26dac23cを専用recipeで復元する。写真と虫取りの受入原本は変更影響なしに再実行しない。虫取りは実NPC/0→8RP/取消/条件不足/同日重複拒否/取引保存/独立Continue/4文言まで。開始party・進行・warpはfixtureで、自然到達・全活動・全map・releaseは未受入。'


def put(name,value):d.write(PUBLIC/name,value)


def amend_missing_fixture_reference():
    old=b"RAW = 'content/modernization/pr16_research_bug_local_measurement.json'"
    new=("RAW = '"+RAW+"'").encode()
    source=Path(MODEL).read_bytes();need(source==d.git('show',HEAD+':'+MODEL) and source.count(old)==1,'exact old RAW literal')
    Path(MODEL).write_bytes(source.replace(old,new));b.RAW=RAW
    tests=Path(TEST).read_text();need(tests.encode()==d.git('show',HEAD+':'+TEST),'unchanged original tests')
    before="""    def test_initial_harness_failure_not_accepted(self):
        failure=self.raw['harness_failure'];self.assertEqual(failure['execution']['returncode'],1)
        with self.assertRaises(ValueError):b.validate(failure['stdout'].encode(),b.CASES[0])
"""
    after="""    def test_missing_historical_measurement_is_not_fabricated(self):
        prior=self.raw['previous_unpersisted_local_evidence']
        self.assertIs(prior['available'],False)
        self.assertIsNone(prior['execution_counts'])
        self.assertNotIn('harness_failure',self.raw)
        for case in b.CASES:
            self.assertEqual(self.raw['cases'][case]['execution'],{'returncode':0,'timeout':False})
"""
    count_old="self.assertEqual(self.raw['counts']['failed_native_processes'],1)"
    need(tests.count(before)==1 and tests.count(count_old)==1,'two exact provenance expectations')
    tests=tests.replace(before,after).replace(count_old,"self.assertEqual(self.raw['counts']['failed_native_processes'],0)")
    Path(TEST).write_text(tests)
    return {'reason_ja':'失われた旧ローカルJSONの初回失敗1件を創作しない。新Actions実測2成功/0失敗と過去件数unknownを区別。oracleと生成Cは不変。',
            'model_before':identity(source),'model_after':identity(Path(MODEL).read_bytes()),
            'model_only_replacement':{'before':old.decode(),'after':new.decode()},
            'tests_before':identity(d.git('show',HEAD+':'+TEST)),'tests_after':identity(Path(TEST).read_bytes()),
            'test_changes':['欠落した過去failureの参照を、欠落/件数unknown/新2成功の検査へ置換','現在Actionsのfailed_native_processesを1から0へ訂正'],
            'native_reexecutions':0,'accepted_test_reexecutions':0}


def record():
    os.chdir(ROOT);d.current();need(not Path(CP).exists() and not PUBLIC.exists(),'already recorded; do not repeat')
    PUBLIC.mkdir(parents=True)
    run=d.inputs.api('actions/runs/'+str(RUN));jobs=d.inputs.api('actions/runs/'+str(RUN)+'/jobs?per_page=100')
    need(run['head_sha']==HEAD and run['path']==WF and run['run_attempt']==1 and run['status']=='completed' and run['conclusion']=='success','exact successful original Actions')
    need(jobs['total_count']==len(jobs['jobs'])==1 and all(j['conclusion']=='success' and j['status']=='completed' and all(s['conclusion']=='success' for s in j['steps']) for j in jobs['jobs']),'all original steps finished')
    meta=d.inputs.api('actions/artifacts/'+str(ARTIFACT))
    need(meta['name']=='pr16-research-bug-measurement' and meta['digest']=='sha256:'+ZIP['sha256'] and meta['size_in_bytes']==ZIP['size'] and not meta['expired'] and meta['workflow_run']['head_sha']==HEAD and meta['workflow_run']['id']==RUN,'exact original artifact metadata')
    rawzip=d.inputs.api('actions/artifacts/'+str(ARTIFACT)+'/zip',True);need(identity(rawzip)==ZIP,'original artifact bytes')
    with zipfile.ZipFile(io.BytesIO(rawzip)) as z:
        members=z.infolist();need(len(members)==13 and len(set(z.namelist()))==13,'one JSON and twelve physical images')
        raw=z.read('public/measurement.json');m=b.load(raw)
        expected={'public/measurement.json'}|{case+'/'+name for case,v in m['cases'].items() for name in v['screens']}
        need(set(z.namelist())==expected and all(e.external_attr>>28!=10 and not e.is_dir() and e.file_size<=500000 for e in members),'closed bounded regular artifact members')
        for case,v in m['cases'].items():
            for name,ib in v['screens'].items():
                image=z.read(case+'/'+name)
                need(image.startswith(b'P6\n240 160\n255\n') and identity(image)==ib and len(image)==115215,'visually reviewed exact screen')
    need(m['source_head']==HEAD and m['run_id']==RUN and m['candidate']==b.CANDIDATE and m['status']=='PASS_NATIVE_PENDING_VISUAL_AND_UNIT' and not m['failures'],'original scoped native success')
    need(m['environment']=='GitHub Actions; new measurement, not recovered local evidence' and m['previous_unpersisted_local_evidence']['execution_counts'] is None,'honest provenance')
    need(m['counts']==dict(rom_changes=0,arm_compiles=0,host_compiles=1,native_processes=2,accepted_case_reruns=0,accepted_native_processes=2,failed_native_processes=0),'complete current execution counts')
    need(m['compile']['returncode']==0 and not m['compile']['stdout'] and not m['compile']['stderr'],'strict recorded compile')
    need(set(m['cases'])==set(b.CASES),'closed original cases')
    for p,bi in m['source_bindings'].items():
        need(identity(d.git('show',HEAD+':'+p))==bi,'original source bytes '+p)
        if p!=WF:need(identity(Path(p).read_bytes())==bi,'unchanged measured source '+p)
    need(d.bindings(m['protected_bindings'])==m['protected_bindings'],'original protected evidence unchanged')
    parent=d.read('content/modernization/pr16_research_map_view_checkpoint.json')
    inherited={p:bi for p,bi in parent['source_bindings'].items() if p!='.github/workflows/pr16-research-photo-visual-20260927.yml'}
    need(d.bindings(inherited)==inherited and parent['actions_completion_confirmed'] and parent['status']=='PASS_MAP_VIEW_REPAIR_SCOPED','exact accepted parent source excluding terminal-only workflow')
    results={}
    for case,v in m['cases'].items():
        need(v['execution']==dict(returncode=0,timeout=False) and not v['stderr'] and identity(v['stdout'].encode())==v['stdout_identity'] and identity(b'')==v['stderr_identity'],'recorded numeric exit/stdout/stderr')
        need(v['generated_source']==m['compile']['generated_source'],'identical compiled program')
        results[case]=b.validate(v['stdout'].encode(),case)
        need(results[case]==v['validated'],'immutable independently checked native report')
    tracked=d.git('ls-files').decode().splitlines()
    need(not [p for p in tracked if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','content','docs','design')],'nested rules require review')
    protected=d.bindings(set(m['protected_bindings'])|set(parent['protected_bindings'])|{p for p in tracked if p.startswith(('content/modernization/pr16_research_photo_evidence/','content/modernization/pr16_research_map_view_evidence/'))})
    Path(RAW).write_bytes(raw)
    amendments=amend_missing_fixture_reference()
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_bug.py','-v'],capture_output=True,timeout=120)
    (PUBLIC/'unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(unit.stderr)
    count=(unit.stdout+unit.stderr).count(b' ... ok\n')
    u=dict(returncode=unit.returncode,passed=count,failures=0 if unit.returncode==0 else None,
           source_bindings=d.bindings({MODEL,TEST,b.C}),native_processes=0,compiles=0,
           stdout=identity(unit.stdout),stderr=identity(unit.stderr))
    put('unit.json',u)
    need(unit.returncode==0 and count==51,'new 51 scoped tests (not historical reruns)')
    put('source-adjudication.json',amendments)
    put('terminal.json',dict(run=d.run_summary(run),jobs=jobs['jobs'],artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run')}))
    visual=dict(status='PASS',method='ChatGPT vision of all twelve PPMs in original artifact; pixel hashes matched before review',
        images={case:v['screens'] for case,v in m['cases'].items()},unique_dialogues=4,
        text_ja=['むしポケモンを みせてくれる？','むしポケモンが てもちにいない。','かんさつかんりょう。8ポイントだよ。','きょうのむしは きろくずみだよ。'],
        finding_ja='森林・花・道・人物・台詞枠が正常。独立Continueでも森林地形を保持。青い反復背景なし。四文言は欠字/切詰めなし。全map/自然到達の受入ではない。')
    put('visual.json',visual)
    put('reconciliation.json',dict(status='PASS_BUG_ACTIONS_SOURCE_AND_EVIDENCE',original=identity(raw),candidate=m['candidate'],accepted_cases=results,
        counts=m['counts'],new_scoped_tests=51,record_native_runs=0,record_compiles=0,source_adjudication=amendments,
        guard_reuse_ja='既受入の7API書込拒否は同一helper/生成依存から継承。今回barrier後は実キーと読取のみ。',
        parent_inheritance_exclusion='.github/workflows/pr16-research-photo-visual-20260927.yml'))
    manifest={}
    for p in sorted(PUBLIC.iterdir()):
        value=p.read_bytes();value.decode('utf-8');need(p.suffix in ('.json','.txt') and b'\0' not in value and len(value)<2000000,'public UTF8 only')
        dest=Path(BASE)/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(value);manifest[str(dest)]=identity(value)
    d.write(BASE+'/manifest.json',manifest)
    cp=dict(schema_version=1,task=TASK,status='PASS_BUG_REAL_EARNING_SCOPED',source_head=HEAD,run_id=RUN,record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']),
        candidate=b.CANDIDATE,recipe=b.view.RECIPE,measurement=RAW,manifest=BASE+'/manifest.json',terminal=BASE+'/terminal.json',unit=UNIT,
        bug_accepted=True,actions_completion_confirmed=True,accepted_cases=list(b.CASES),failed_cases=[],fresh_cores=3,
        counts=dict(m['counts'],new_scoped_tests=51),source_bindings=d.bindings(set(m['source_bindings'])|{SELF}),protected_bindings=protected,
        visual=BASE+'/visual.json',source_adjudication=BASE+'/source-adjudication.json',all_activities_accepted=False,natural_arrival_accepted=False,
        shop_connection_accepted=False,all_dialogue_native_display_accepted=False,all_maps_accepted=False,release_ready=False,active_baseline_changed=False,
        prior_unpersisted_measurement=m['previous_unpersisted_local_evidence'],record_execution=dict(native_processes=0,compiles=0,new_unit_processes=1))
    d.write(CP,cp)
    guide=f'''# PR16 虫取りの実RP稼得

{cp['status']}

## 実装・限定受入

候補 `{b.CANDIDATE['sha256']}` / 33554432 bytes。保存view修復後候補のbyte変更なし、ARM compile/link0。
実map97/0、local11、(43,6)、record0x09413854、script0x093C048Cを現ROMから同定。species39は現ROMのtype6/6（むし）、species1は12/12。全国図鑑番号から推測しない。

実NPCへ通常キーで話し、条件不足はresult3/RP0/Flash不変。むしありの取消はRP0/Flash不変、承諾で0→8RP、日内8/生涯8/claim1/取引ID2、counter2→4。直後の同日重複、独立coreの通常Continue、再度の重複はresult4/残高8/counter4/Flash不変。全party600bytes・Bag・ledger2048bytes・他owner・checksumを確認。取引自身の保存2回、手動Save0、警告0、観測barrier後host書込み0。

開始party/進行/warpはfixtureで、自然捕獲・自然到達の受入ではない。写真の旧候補や受入済みmap-view検査を再実行せず、元ROM/seed/旧証拠を保全。

## 原本と実行数

Actions run `{RUN}` / source `{HEAD}`、数値returncode0を持つ2process/3fresh cores、host compile1、native失敗0。四文言と12PPMを目視し森林/花/道/人物/台詞枠・cold地形を確認。虫なし・確認・8ポイント・日内記録済みを区別。

原本 `{RAW}` はartifact10912851229のmeasurement.jsonをbyte不変で保存。外側ZIP sha256 `{ZIP['sha256']}`。`{BASE}/terminal.json` が全step成功を確認。`{UNIT}` は新規51テスト（全64owner byte変異/順序/欠落/型/過大主張拒否を含む）。原本照合・記録時native/compile再実行0。

60afcc67にあった旧ローカルJSON参照は未保存だった。過去の失敗1件やstdoutは復元できたと主張せず、過去件数unknownを保持。参照先を今回のActions原本へ変更し、2テストの由来期待だけを訂正。独立oracle/生成C/ROMは不変。`{BASE}/source-adjudication.json` に旧/新source hashを記録。

## 次工程・禁止

{GOAL}

全体CIには既存P03 capacity source pin問題等があり、本限定PASSを全CI成功へ昇格しない。最新結果は固定引継ぎのobserved_head_checks。PR draft/open・未mergeを維持、release/baseline切替なし。
'''
    Path(GUIDE).write_text(guide)
    state=d.read(d.STATE)
    old_checks=state['observed_head_checks'];old_ids={r['id'] for r in old_checks['runs'] if r['status']!='completed'}
    prior_checks=[d.run_summary(d.inputs.api('actions/runs/'+str(i))) for i in sorted(old_ids)]
    listing=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=24')['workflow_runs']
    checks={'prior_incomplete_now_observed':prior_checks,'latest_runs':[d.run_summary(r) for r in listing]}
    d.write(BASE+'/checks.json',checks);manifest[BASE+'/checks.json']=identity(Path(BASE+'/checks.json').read_bytes());d.write(BASE+'/manifest.json',manifest)
    state['research_bug']={k:cp[k] for k in ('status','source_head','run_id','candidate','actions_completion_confirmed','bug_accepted','accepted_cases','fresh_cores','counts')}
    state['research_bug'].update(path=CP,measurement=RAW,guide=GUIDE)
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=GOAL
    state['next_action']=dict(state['next_action'],id='RESEARCH_REMAINING_FOUR_AND_NATURAL_CONNECTION_NEXT',goal_ja=GOAL,
        read_paths=[GUIDE,CP,b.view.RECIPE,'content/research_economy_v1/canonical_model.json','overlays/research_economy_v1/research_economy_v1.c','docs/PR16_RESEARCH_CATALOG_JA.md','content/modernization/pr16_research_catalog_checkpoint.json','docs/PR16_RESEARCH_NEW_GAME_JA.md'],
        stop_rule_ja='写真/虫取り/保存view受入・元ROM/seed/旧証拠を不変に保つ。自然到達/全活動/全mapへの過大主張、無変更再実行、merge/release/baseline変更は禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='虫取りActions実測5412cee1/run36261672837の受入記録source。自己commit SHAはgit log参照。'
    state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],runs=checks['latest_runs'],reconciliation=BASE+'/checks.json',
        reason_ja='虫取りrun36261672837は全step成功。旧引継ぎの実行中6runも現在結果を照合。一般CIと本限定受入を分離し、P03既存source pin failure/承認待ちを全CI成功へ昇格しない。記録workflowの最終結果はremote HEADとActionsで確認。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in listing if r['status'] in ('queued','in_progress')]
    for path in OWN|{b.C,RAW,CP,GUIDE}:state['source_bindings'][path]=identity(Path(path).read_bytes())
    note='虫取りrun36261672837/26dac23cは実NPC0→8RP・取消・条件不足・重複拒否・取引保存2・独立Continue・4文言を受入。新規51検査、2process/3cores、ROM/ARM0。旧ローカル未保存原本の件数はunknown。無変更再実行禁止、自然到達/全活動へ昇格しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat();state['logs_synchronized']=True
    publish_resume(state)
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 虫取り実RP稼得の未保存WIPを完了\n- Version: research-bug-v1\n- Status: DONE（虫取り限定scope）\n- Summary: 実NPCから0→8RP、取消/条件不足/同日重複拒否、取引保存2/独立Continue、4文言12画像を受入。旧ローカル原本欠落はunknownとして新Actions原本と分離。残る4活動/自然到達/受付ショップ接続は未受入。\n- Files changed: 虫取りrunner/oracle/51検査/回収・記録Actions/UTF8原本/checkpoint/guide、固定引継ぎMD・JSON、両ログ。\n- Verify: run36261672837全step成功、2native/3cores/host1/ARM0/ROM変更0、失敗0。今回新51tests PASS。記録native/compile再実行0、旧受入再実行0。source/hash/12画像/ledger2048/party600/Bag/Flashを照合。commit前resume/task graph/scoped index guard必須。\n- Commit: WIP64f9894・5412cee、測定source={HEAD}、記録source='+os.environ['GITHUB_SHA']+'、自己SHAはgit log参照、同branch非force push。\n- Network: GitHub live HEAD/PR/Actions/固定artifactだけ。旧実行中runを現在結果へ照合。一般CIは限定受入と分離。ROM/save非tracked、merge/release/baseline不変。\n'
    for path in sorted(d.LOGS):
        with Path(path).open('a') as f:f.write(log)
    owned=set(manifest)|{BASE+'/manifest.json',RAW,CP,GUIDE,MODEL,TEST,d.STATE,d.DOC}|d.LOGS
    d.write(OUT/'owned.json',sorted(owned));put('summary.json',dict(status=cp['status'],original_run=RUN,source_head=HEAD,record_source_head=os.environ['GITHUB_SHA'],unit=u,record_native_runs=0))


def guard():
    cp=d.read(CP);need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'accepted evidence preserved')
    owned=set(d.read(OUT/'owned.json'));subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    changed=set(d.git('diff','--cached','--name-only',START).decode().splitlines())
    need(changed<=owned|OWN,'all task commits remain in explicit scope')
    g.START=START;g.CODE=changed-owned;g.OWNED=owned;g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)
    put('guard.json',dict(status='PASS_SCOPED_FINAL_INDEX',source_head=os.environ['GITHUB_SHA'],from_task_head=START,changed_paths=sorted(changed),new_private_violations=0,full_historical_guard_pass_claimed=False))


if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('record | guard')
