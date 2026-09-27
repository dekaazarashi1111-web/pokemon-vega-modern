#!/usr/bin/env python3
"""新しい数値受付2境界だけを実測・記録。旧受入matrixとARM compilerは呼ばない。"""
import datetime
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_counter_numeric as patch
import pr16_research_counter_probe as probe
import pr16_research_counter_oracle as oracle
import pr16_research_connection_actions as parent
import pr16_research_lifecycle_actions as d

TASK='USER-20260927-RESEARCH-COUNTER'
SELF='scripts/pr16_research_counter_actions.py'
WF='.github/workflows/pr16-research-counter-numeric.yml'
CP='content/modernization/pr16_research_counter_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_COUNTER_JA.md'
BASE='content/modernization/pr16_research_counter_evidence'
TEST='tests/test_pr16_research_counter_numeric.py'
CODE={SELF,WF,TEST,'scripts/pr16_research_counter_numeric.py','scripts/pr16_research_counter_probe.py',
      'scripts/pr16_research_counter_oracle.py',probe.C}
PROTECTED=parent.PROTECTED|{'content/modernization/pr16_research_connection_checkpoint.json',
    'content/modernization/pr16_research_connection_acceptance.json','docs/PR16_RESEARCH_CONNECTION_JA.md'}
OUT=ROOT/'.local/pr16-research-counter';PUBLIC=OUT/'public'
COUNTS={'native_processes':0,'guard_processes':0,'host_compiles':0,'arm_compiles':0,'accepted_case_reruns':0}


def measure():
    os.chdir(ROOT);d.current();patch.need(not Path(CP).exists(),'recorded numeric matrix must not be rerun')
    PUBLIC.mkdir(parents=True)
    bound=d.bindings(CODE);protected=d.bindings(PROTECTED)
    d.write(PUBLIC/'invocation.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=bound,protected_bindings=protected))
    accepted=d.inputs.api('actions/runs/36285446907')
    patch.need(accepted['head_sha']=='c4da83fc8dd55c18281a02d1ba838728d7ee48c6' and accepted['status']=='completed' and accepted['conclusion']=='success','prior independent acceptance terminal')
    d.write(PUBLIC/'previous-acceptance.json',d.run_summary(accepted))
    parent.OUT=OUT/'parent';parent.PUBLIC=PUBLIC
    runtime,seed,predecessor,_,_=parent.restore()
    candidate,recipe=patch.apply(predecessor);d.write(PUBLIC/'recipe.json',recipe)
    # Extra rejection checks use copies only; no native processes or old builders.
    for address in (patch.TEXT,patch.SCRIPT,0x0806B684,0x08162CC4,0x09413B9C):
        bad=bytearray(predecessor);bad[address-0x08000000]^=1
        try: patch.audit(bytes(bad))
        except ValueError: pass
        else: raise ValueError('modified predecessor accepted')
    rom=OUT/'candidate.gba';rom.write_bytes(candidate)
    import pr16_research_lifecycle_v2 as gen
    gen.OUT=OUT/'generated';d.PUBLIC=PUBLIC
    generated=probe.generate(seed);source=OUT/'probe.c';source.write_bytes(generated)
    (PUBLIC/'generated.c.txt').write_bytes(generated)
    exe=OUT/'probe';command=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.','-I'+str(runtime/'include'),str(source),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    COUNTS['host_compiles']+=1
    compiled=subprocess.run(command,capture_output=True,timeout=150)
    (PUBLIC/'compile.stdout.txt').write_bytes(compiled.stdout);(PUBLIC/'compile.stderr.txt').write_bytes(compiled.stderr)
    d.write(PUBLIC/'compile.json',dict(returncode=compiled.returncode,source=patch.identity(generated),compiler=subprocess.check_output(['cc','--version']).decode(),command=[v.replace(str(ROOT)+'/', '') for v in command],stdout=patch.identity(compiled.stdout),stderr=patch.identity(compiled.stderr)))
    patch.need(compiled.returncode==0 and not compiled.stderr,'strict host compile')
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)]
    guards={}
    for method in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
        COUNTS['guard_processes']+=1
        proc=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=15)
        (PUBLIC/(method+'.stdout.txt')).write_bytes(proc.stdout);(PUBLIC/(method+'.stderr.txt')).write_bytes(proc.stderr)
        guards[method]=dict(returncode=proc.returncode,stdout=patch.identity(proc.stdout),stderr=patch.identity(proc.stderr))
        d.write(PUBLIC/'guards.json',guards)
        patch.need(proc.returncode==1 and not proc.stdout and proc.stderr==b'research-save-impact: host write after observation barrier\n','new executable host barrier '+method)
    results={};failures={}
    for index in (0,1):
        directory=PUBLIC/str(index);directory.mkdir()
        fixture,receipt=probe.fixture(seed,index);save=OUT/(str(index)+'.srm');save.write_bytes(fixture)
        commands=probe.commands();(directory/'commands.txt').write_bytes(commands)
        COUNTS['native_processes']+=1;start=time.monotonic()
        try:
            proc=subprocess.run(prefix+[str(rom),str(save),str(index)],input=commands,capture_output=True,cwd=directory,timeout=180)
            rc=proc.returncode;out,err=proc.stdout,proc.stderr;timed_out=False
        except subprocess.TimeoutExpired as exc:
            rc=None;out,err=exc.stdout or b'',exc.stderr or b'';timed_out=True
        (directory/'stdout.txt').write_bytes(out);(directory/'stderr.txt').write_bytes(err)
        screens={p.name:patch.identity(p.read_bytes()) for p in sorted(directory.glob('*.ppm'))}
        for p in directory.glob('*.ppm'):
            b=p.read_bytes();patch.need(len(b)==115215 and b.startswith(b'P6\n240 160\n255\n'),'bounded complete native PPM')
        measurement=dict(returncode=rc,timeout=timed_out,elapsed_seconds=round(time.monotonic()-start,3),stdout=patch.identity(out),stderr=patch.identity(err),commands=patch.identity(commands),screens=screens,fixture=receipt,save_after=patch.identity(save.read_bytes()))
        d.write(directory/'measurement.json',measurement)
        try:
            patch.need(rc==0 and not timed_out and not err,'clean native process')
            patch.need(save.read_bytes()==fixture,'fixture Flash remained unchanged')
            results[str(index)]=oracle.validate(out,index,commands,fixture,screens)
        except (ValueError,KeyError,TypeError) as exc: failures[str(index)]=dict(type=type(exc).__name__,reason=str(exc))
        d.write(PUBLIC/'oracle.json',dict(results=results,failures=failures))
    os.environ['PR16_COUNTER_EVIDENCE']=str(PUBLIC)
    suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_pr16_research_counter_numeric')
    count=suite.countTestCases()
    unit=subprocess.run([sys.executable,'-B','-m','unittest','tests.test_pr16_research_counter_numeric','-v'],capture_output=True,timeout=120)
    (PUBLIC/'unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(unit.stderr)
    passed=unit.stderr.count(b' ... ok\n')
    d.write(PUBLIC/'unit.json',dict(returncode=unit.returncode,expected_tests=count,passed_tests=passed,module=TEST,stdout=patch.identity(unit.stdout),stderr=patch.identity(unit.stderr)))
    patch.need(d.bindings(CODE)==bound and d.bindings(PROTECTED)==protected,'source/protected byte identity')
    patch.need(patch.identity(rom.read_bytes())==patch.CANDIDATE,'candidate immutable during observation')
    d.write(PUBLIC/'measurement.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=patch.CANDIDATE,results=results,failures=failures,tests=count,tests_passed=passed,visual_review_completed=False,counts=COUNTS))
    patch.need(not failures and unit.returncode==0 and passed==count==76 and not unit.stdout,'two numeric boundaries and all 76 new tests')


def record():
    os.chdir(ROOT);d.current();patch.need(not Path(CP).exists(),'immutable initial checkpoint')
    invocation=d.read(PUBLIC/'invocation.json');patch.need(invocation['source_head']==os.environ['GITHUB_SHA'],'bound measurement HEAD')
    patch.need(d.bindings(CODE)==invocation['source_bindings'] and d.bindings(PROTECTED)==invocation['protected_bindings'],'protected/code preserved')
    error=d.read(PUBLIC/'error.json') if (PUBLIC/'error.json').exists() else None
    measurement=d.read(PUBLIC/'measurement.json') if (PUBLIC/'measurement.json').exists() else {}
    directory=Path(BASE)/os.environ['GITHUB_RUN_ID'];patch.need(not directory.exists(),'immutable evidence directory')
    evidence={}
    for p in sorted(PUBLIC.rglob('*')):
        if not p.is_file() or p.suffix not in ('.json','.txt'): continue
        raw=p.read_bytes();raw.decode('utf-8');patch.need(b'\0' not in raw,'tracked UTF8 only')
        target=directory/p.relative_to(PUBLIC);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        evidence[str(target)]=patch.identity(raw)
    d.write(directory/'manifest.json',evidence)
    cp=dict(schema_version=1,task=TASK,status='STOPPED_COUNTER_MEASUREMENT' if error else 'MEASURED_COUNTER_NUMERIC_ORACLE_PASS_PENDING_VISUAL_REVIEW',
        source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=patch.CANDIDATE,parent=patch.PARENT,
        source_bindings=invocation['source_bindings'],protected_bindings=invocation['protected_bindings'],error=error,
        measurement=measurement,evidence_manifest=str(directory/'manifest.json'),evidence_directory=str(directory),
        actions_completion_confirmed=False,counter_numeric_display_accepted=False,counter_rank_number_accepted=False,
        standard_list_accepted=False,naturally_earned_spending_accepted=False,natural_story_progress_accepted=False,
        active_baseline_changed=False,release_ready=False,issue19_complete=False)
    d.write(CP,cp)
    goal=('数値受付の原本/独立oracleが保存済み。実画面とrun終端を確認して限定受入を確定し、その後標準list、自然稼得RP支出、通常進行の接続へ進む。' if not error else '数値受付の失敗原本を先に読む。計測済み成功部分を再実行せず、変更影響だけ修復する。')
    goal+=' 旧4入口/旧稼得/BP/P08は不変。新規9999RPは表示境界fixtureであり自然稼得ではない。'
    (ROOT/GUIDE).write_text('# PR16 受付の残高・rank数値表示\n\nTask: `'+TASK+'`\n\n'+goal+'\n\n## 実装境界\n\n親26dac23cから既存15byte文言と132byteイベント窓だけを変更。残高getter/ランクgetter→標準buffernumber→msgbox、成功resultを0へ戻し、cap4/保存失敗13/その他の分岐を保持。147byte宣言内88byte差分、全rollback一致、外部変更0、新ARM/新領域0。canonical modelは歴史正本のまま不変で、実際の後継文言は専用recipeが正本。STANDARD_LISTの実装とは区別する。\n\n## 検証境界\n\n0RP/rank1と9999RP/rank7を起動前の完全save fixtureで用意し、観測barrier後は物理keyのみ。変更された受付へ到達する屋外prefixだけを含み、旧4入口matrix/旧稼得を独立再実行しない。実値、数値buffer、展開文言、全owner64/ledger2048/Bag/party/Flash/counterと会話終了を照合。7方式のhost書込み拒否と厳格host compile。標準list/自然RP支出/通常ストーリー到達/全ゲーム品質は未受入。\n\n## 原本\n\ncheckpoint `'+CP+'` / source `'+cp['source_head']+'` / run `'+str(cp['run_id'])+'`。Actions終端や画面視認を自己確定しない。\n',encoding='utf-8')
    state=d.read(d.STATE);state['research_counter']=dict(path=CP,status=cp['status'],candidate=cp['candidate'],source_head=cp['source_head'],run_id=cp['run_id'])
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_COUNTER_VISUAL_REVIEW_AND_STANDARD_LIST_NEXT',goal_ja=goal,read_paths=[GUIDE,CP,SELF,'scripts/pr16_research_counter_numeric.py','scripts/pr16_research_counter_oracle.py'],stop_rule_ja='保存済み2境界/旧4入口/旧稼得を無変更再実行しない。受入前に原本/画面/Actions終端を照合。標準list・自然RP支出は別受入。merge/release/baseline切替禁止。')
    state['do_not_repeat'].insert(0,'数値受付の新規2境界は'+CP+'の原本を先に照合。画面未レビューを受入と呼ばない。同じcandidate/fixtureのnativeと旧4入口matrixを反復しない。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='数値受付の実測source HEAD。自己commit SHAはgit logで照合。旧BP/P08は歴史受入のまま。'
    runs=d.inputs.api('actions/runs?head_sha='+os.environ['GITHUB_SHA']+'&per_page=50')
    patch.need(runs['total_count']<=50,'current HEAD Actions completeness')
    state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],runs=[d.run_summary(r) for r in runs['workflow_runs']],reason_ja='新数値受付の原本を記録。自己run終端と一般CI全成功はまだ主張しない。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in runs['workflow_runs'] if r['status'] in ('queued','in_progress')]
    for p in CODE|{CP,GUIDE}: state['source_bindings'][p]=patch.identity((ROOT/p).read_bytes())
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 数値受付の限定実装・原本固定\n- Version: research-counter-numeric-measured-v1\n- Status: STOPPED（'+('失敗原本を保存' if error else '数値oracle成功、画面とActions終端の確認待ち')+f'）\n- Summary: 既存147byte内88byteの数値表示接続。0RP/rank1・9999RP/rank7だけを実測。標準list/自然RP支出は未完。\n- Files changed: 専用probe/oracle/新76検査/Actions、recipeとUTF8原本、専用MD/checkpoint、固定引継ぎMD/JSON、両ログ。\n- Verify: 計数と失敗有無は{CP}のmeasurement/errorを正本とする。新規2境界、guard7、host1、ARM0、既受入独立再実行0を計画し実数を保存。VMの値/分岐/原本改変拒否をnative件数に含めない。全体guard/全CI成功は主張しない。\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force記録。自己SHAはgit log。\n- Network: 固定GitHub artifactとActions/PR metadataのみ。ROM/saveはGit管理外。merge/release/baseline変更なし。\n'
    for p in d.LOGS:
        with (ROOT/p).open('a',encoding='utf-8') as f: f.write(log)
    owned=set(evidence)|{str(directory/'manifest.json'),CP,GUIDE,d.STATE,d.DOC}|d.LOGS
    d.write(OUT/'owned.json',sorted(owned))


def guard():
    os.chdir(ROOT);d.current()
    import pr16_resume
    import pr16_learnset_runtime_record as g
    pr16_resume.validate(ROOT)
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(d.read(OUT/'owned.json'));g.guard()
    patch.need(d.bindings(PROTECTED)==d.read(CP)['protected_bindings'],'protected inputs unchanged before commit')
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    if sys.argv[1:]==['measure']:
        try: measure()
        except Exception as exc:
            if PUBLIC.exists(): d.write(PUBLIC/'error.json',dict(type=type(exc).__name__,reason=str(exc),counts=COUNTS))
            raise
    elif sys.argv[1:]==['record']: record()
    elif sys.argv[1:]==['guard']: guard()
    elif sys.argv[1:]==['paths']: print('\n'.join(d.read(OUT/'owned.json')))
    else: raise SystemExit('measure|record|guard|paths')
